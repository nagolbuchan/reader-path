import asyncio
import json
import re
from typing import Any, Callable, Optional

from app.agents.crews.crew import ReaderPathCrew
from app.models.course import CoursePreview
from app.services.book_catalog import (
    clear_catalog,
    get_catalog,
    start_catalog,
    validate_course_readings,
)
from app.services.google_books import (
    GoogleBooksError,
    format_catalog_for_agent,
    search_volumes,
)
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


def _collect_books(topic: str, category: str):
    """Pre-fetch verified books; fail closed if the API is down or too thin."""
    collected = []
    seen = set()
    last_error: Optional[GoogleBooksError] = None

    for query in catalog_queries_for(topic, category):  # type: ignore[arg-type]
        try:
            books = search_volumes(query, max_results=40)
        except GoogleBooksError as exc:
            last_error = exc
            continue
        for book in books:
            if book.google_books_id in seen:
                continue
            seen.add(book.google_books_id)
            collected.append(book)

    if not collected and last_error:
        raise ValueError(str(last_error)) from last_error

    if len(collected) < 12:
        raise ValueError(
            "Could not find enough verified books on Google Books for this topic "
            f"(found {len(collected)}). Try a broader topic, or check API quota."
        )

    return collected


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

            progress("searching_books", "Searching Google Books")
            collected = await asyncio.to_thread(_collect_books, topic, category)
            catalog = start_catalog(collected)
            verified_books = format_catalog_for_agent(list(catalog.values())[:40])

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

            progress("validating_readings", "Validating readings")
            live_catalog = get_catalog() or catalog
            course, repairs = validate_course_readings(course, live_catalog)
            if repairs:
                print(
                    f"Applied {len(repairs)} reading repair(s) for topic={topic!r}"
                )
            course.topic = course.topic or topic
            course.category = category
            return course
        finally:
            clear_catalog()
