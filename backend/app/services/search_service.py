import asyncio
import json
import re
from typing import Any, Callable, List, Optional

from app.agents.crews.crew import ReaderPathCrew
from app.models.course import CoursePreview
from app.services.book_catalog import (
    clear_catalog,
    get_catalog,
    start_catalog,
    validate_course_readings,
)
from app.services.book_sources import google_books as gb
from app.services.book_sources import open_library as ol
from app.services.book_sources.gutenberg import enrich_course_with_gutenberg
from app.services.book_sources.merge import format_catalog_for_agent, merge_records
from app.services.book_sources.resolve import resolve_candidates
from app.services.book_sources.tmu_sheets import (
    fetch_tmu_candidates,
    filter_candidates_for_topic,
)
from app.services.book_sources.types import BookRecord
from app.services.history_order import order_history_course_chronologically
from app.services.topic_classifier import catalog_queries_for, classify_topic

ProgressCallback = Callable[[str, str], None]


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


def _collect_books(topic: str, category: str) -> List[BookRecord]:
    """
    Seed verified catalog from Google Books + Open Library, then resolve
    TMU sheet candidates into the same catalog.
    """
    collected: List[BookRecord] = []
    errors: List[str] = []
    sources_used: List[str] = []

    for query in catalog_queries_for(topic, category):  # type: ignore[arg-type]
        try:
            books = gb.search_volumes(query, max_results=40)
            if books:
                sources_used.append("google_books")
                collected.extend(books)
        except gb.GoogleBooksError as exc:
            errors.append(f"Google Books: {exc}")

        try:
            books = ol.search_open_library(query, max_results=40)
            if books:
                sources_used.append("open_library")
                collected.extend(books)
        except ol.OpenLibraryError as exc:
            errors.append(f"Open Library: {exc}")

    # TMU curriculum candidates → resolve via GB/OL
    try:
        candidates = fetch_tmu_candidates()
        filtered = filter_candidates_for_topic(candidates, topic, limit=30)
        resolved = resolve_candidates(filtered)
        if resolved:
            sources_used.append("tmu_sheets")
            collected.extend(resolved)
            print(f"Resolved {len(resolved)} TMU candidate books for topic={topic!r}")
    except Exception as exc:
        print(f"TMU candidate pass skipped: {exc}")

    merged = list(merge_records(collected).values())
    print(
        "Catalog sources:",
        sorted(set(sources_used)),
        f"unique books={len(merged)}",
    )

    if not merged:
        detail = "; ".join(errors[:3]) if errors else "no results"
        raise ValueError(
            "Could not build a verified book catalog from Google Books / Open Library. "
            f"({detail})"
        )

    if len(merged) < 12:
        raise ValueError(
            "Could not find enough verified books for this topic "
            f"(found {len(merged)}). Try a broader topic, or check API quota."
        )

    return merged


class CourseGenerationService:
    """Generate a course structure from a topic using CrewAI agents."""

    async def generate_course_from_topic(
        self,
        topic: str,
        on_progress: Optional[ProgressCallback] = None,
    ) -> CoursePreview:
        def progress(key: str, label: str = "") -> None:
            if on_progress:
                on_progress(key, label)

        print("generate_course_from_topic called with topic:", topic)
        clear_catalog()

        try:
            progress("classifying_topic", "Classifying topic")
            category = await asyncio.to_thread(classify_topic, topic)
            print("classified category:", category)

            progress("searching_books", "Searching verified catalogs")
            collected = await asyncio.to_thread(_collect_books, topic, category)
            catalog = start_catalog(collected)
            verified_books = format_catalog_for_agent(
                list(catalog.values())[:40],
                chronological=(category == "history"),
            )

            progress("building_modules", "Building course modules")
            crew_instance = ReaderPathCrew()
            crew = crew_instance.reader_path_crew()
            result = await crew.kickoff_async(
                inputs={
                    "topic": topic,
                    "category": category,
                    "verified_books": verified_books,
                }
            )
            course = parse_crew_course_result(result)

            progress("validating_readings", "Validating & repairing readings")
            live_catalog = get_catalog() or catalog
            course, repairs = validate_course_readings(course, live_catalog)
            if repairs:
                print(
                    f"Applied {len(repairs)} reading repair(s) for topic={topic!r}"
                )

            if category == "history":
                course = order_history_course_chronologically(course)

            course = await asyncio.to_thread(enrich_course_with_gutenberg, course)

            course.topic = course.topic or topic
            course.category = category
            return course
        finally:
            clear_catalog()
