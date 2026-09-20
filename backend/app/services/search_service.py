import asyncio
import json
import re
import uuid
from typing import Any, Callable, List, Optional, Tuple

from app.agents.crews.crew import ReaderPathCrew
from app.models.course import CoursePreview
from app.services.book_catalog import (
    clear_catalog,
    get_catalog,
    start_catalog,
    unused_catalog_readings,
    validate_course_readings,
)
from app.services.book_cache import set_replacement_pool
from app.services.book_sources import library_of_congress as loc
from app.services.book_sources import open_library as ol
from app.services.book_sources.gutenberg import enrich_course_with_gutenberg
from app.services.book_sources.merge import format_catalog_for_agent, merge_records
from app.services.book_sources.resolve import resolve_candidates
from app.services.book_sources.tmu_sheets import (
    CandidateBook,
    fetch_tmu_candidates,
    filter_candidates_for_topic,
)
from app.services.book_sources.types import BookRecord
from app.services.book_sources.web_search import (
    SerperError,
    candidate_from_record,
    dedupe_candidates,
    search_web_candidates,
)
from app.services.crew_run_log import (
    CrewRunLogger,
    capture_verbose_trace,
    crew_tasks_log_path,
)
from app.services.history_order import order_history_course_chronologically
from app.services.topic_classifier import catalog_queries_for, classify_topic

ProgressCallback = Callable[[str, str], None]

_MAX_CANDIDATES_TO_VALIDATE = 80
_MIN_VALIDATED_CATALOG = 12


def _extract_json_object(text: str) -> dict:
    """Pull a JSON object out of raw LLM / CrewAI text."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in crew output")
    return json.loads(text[start : end + 1])


def parse_crew_course_result(result: Any) -> CoursePreview:
    if isinstance(result, CoursePreview):
        return result

    if isinstance(result, dict):
        return CoursePreview.model_validate(result)

    if hasattr(result, "json_dict") and getattr(result, "json_dict"):
        return CoursePreview.model_validate(result.json_dict)

    raw = getattr(result, "raw", None)
    if raw is None:
        raw = getattr(result, "pydantic", None) or result

    if isinstance(raw, dict):
        return CoursePreview.model_validate(raw)

    if hasattr(raw, "model_dump"):
        return CoursePreview.model_validate(raw.model_dump())

    text = str(raw)
    data = _extract_json_object(text)
    return CoursePreview.model_validate(data)


def _catalog_suggestion_candidates(topic: str, category: str) -> List[CandidateBook]:
    """Open Library / LoC may suggest titles; they are not trusted until GB validates."""
    suggestions: List[CandidateBook] = []
    queries = catalog_queries_for(topic, category)[:2]  # type: ignore[arg-type]
    for query in queries:
        try:
            for rec in ol.search_open_library(query, max_results=15):
                suggestions.append(candidate_from_record(rec))
        except ol.OpenLibraryError as exc:
            print(f"Open Library suggestion pass skipped: {exc}")

        try:
            for rec in loc.search_loc(query, max_results=15):
                suggestions.append(candidate_from_record(rec))
        except loc.LocError as exc:
            print(f"Library of Congress suggestion pass skipped: {exc}")
    return suggestions


def _discover_candidates(
    topic: str, category: str
) -> Tuple[List[CandidateBook], List[str], List[str]]:
    """Untrusted discovery: web + TMU + optional OL/LoC suggestions."""
    collected: List[CandidateBook] = []
    errors: List[str] = []
    sources_used: List[str] = []

    try:
        web = search_web_candidates(topic, category)
        if web:
            sources_used.append("web")
            collected.extend(web)
            print(f"Web discovery found {len(web)} candidate(s) for topic={topic!r}")
    except SerperError as exc:
        errors.append(f"Serper: {exc}")
        print(f"Web discovery skipped: {exc}")

    try:
        tmu = filter_candidates_for_topic(fetch_tmu_candidates(), topic, limit=30)
        if tmu:
            sources_used.append("tmu_sheets")
            collected.extend(tmu)
            print(f"TMU sheets contributed {len(tmu)} candidate(s) for topic={topic!r}")
    except Exception as exc:
        print(f"TMU candidate pass skipped: {exc}")

    suggestions = _catalog_suggestion_candidates(topic, category)
    if suggestions:
        sources_used.append("catalog_suggestions")
        collected.extend(suggestions)
        print(
            f"OL/LoC contributed {len(suggestions)} untrusted suggestion(s) "
            f"for topic={topic!r}"
        )

    deduped = dedupe_candidates(collected)
    print(
        "Discovery sources:",
        sorted(set(sources_used)),
        f"unique candidates={len(deduped)}",
    )
    return deduped, errors, sources_used


def _validate_candidates(
    candidates: List[CandidateBook],
    errors: List[str],
) -> List[BookRecord]:
    """Promote candidates only after Google Books ISBN or strict-match validation."""
    to_validate = candidates[:_MAX_CANDIDATES_TO_VALIDATE]
    resolved = resolve_candidates(to_validate)
    merged = list(merge_records(resolved).values())
    print(f"Google Books validated {len(merged)} of {len(to_validate)} candidate(s)")

    if not merged:
        detail = "; ".join(errors[:3]) if errors else "no Google Books matches"
        raise ValueError(
            "Could not validate any real books via Google Books after web "
            f"discovery. ({detail})"
        )

    if len(merged) < _MIN_VALIDATED_CATALOG:
        raise ValueError(
            "Could not find enough verified books for this topic "
            f"(found {len(merged)}). Try a broader topic, or check API quota."
        )
    return merged


def _collect_books(topic: str, category: str) -> List[BookRecord]:
    """Discover untrusted candidates, then validate through Google Books."""
    candidates, errors, _sources = _discover_candidates(topic, category)
    return _validate_candidates(candidates, errors)


class CourseGenerationService:
    """Generate a course structure from a topic using CrewAI agents."""

    async def generate_course_from_topic(
        self,
        topic: str,
        on_progress: Optional[ProgressCallback] = None,
        run_id: Optional[str] = None,
    ) -> CoursePreview:
        def progress(key: str, label: str = "") -> None:
            if on_progress:
                on_progress(key, label)

        run_id = run_id or str(uuid.uuid4())
        run_log = CrewRunLogger(run_id=run_id, topic=topic)

        print("generate_course_from_topic called with topic:", topic)
        print(f"crew run log: {run_log.dir_path}")
        clear_catalog()

        try:
            progress("classifying_topic", "Classifying topic")
            category = await asyncio.to_thread(classify_topic, topic)
            run_log.category = category
            print("classified category:", category)

            progress("discovering_books", "Searching the web for books")
            candidates, discover_errors, _sources = await asyncio.to_thread(
                _discover_candidates, topic, category
            )

            progress("validating_books", "Validating books exist")
            collected = await asyncio.to_thread(
                _validate_candidates, candidates, discover_errors
            )
            catalog = start_catalog(collected)
            verified_books = format_catalog_for_agent(
                list(catalog.values())[:40],
                chronological=(category == "history"),
            )

            progress("building_modules", "Building course modules")
            crew_instance = ReaderPathCrew()
            crew_instance._output_log_file = str(crew_tasks_log_path(run_id))
            crew_instance._step_callback = run_log.append_step
            crew = crew_instance.reader_path_crew()

            with capture_verbose_trace(run_id) as trace_buf:
                result = await crew.kickoff_async(
                    inputs={
                        "topic": topic,
                        "category": category,
                        "verified_books": verified_books,
                    }
                )
            run_log.verbose_trace = trace_buf.getvalue()
            run_log.agent_raw_output = str(
                getattr(result, "raw", None) or result
            )

            course = parse_crew_course_result(result)
            run_log.course_from_agents = course.model_dump()

            progress("validating_readings", "Confirming assigned readings")
            live_catalog = get_catalog() or catalog
            course, repairs = validate_course_readings(course, live_catalog)
            run_log.repairs = list(repairs or [])
            if repairs:
                print(
                    f"Applied {len(repairs)} reading repair(s) for topic={topic!r}"
                )

            if category == "history":
                course = order_history_course_chronologically(course)

            course = await asyncio.to_thread(enrich_course_with_gutenberg, course)

            course.topic = course.topic or topic
            course.category = category

            pool = unused_catalog_readings(course, live_catalog)
            course.replacement_pool = pool
            set_replacement_pool(run_id, pool)

            run_log.final_course = course.model_dump()
            run_log.status = "complete"
            return course
        except Exception as exc:
            run_log.status = "failed"
            run_log.error = str(exc)
            raise
        finally:
            try:
                path = run_log.write()
                print(f"Wrote crew run log: {path}")
            except Exception as log_exc:
                print(f"Failed to write crew run log: {log_exc}")
            clear_catalog()
