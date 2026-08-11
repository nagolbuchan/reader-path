import json
import re
from typing import Any

from app.agents.crews.crew import ReaderPathCrew
from app.models.course import CoursePreview


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

    # CrewOutput-like objects
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


class CourseGenerationService:
    """Generate a course structure from a topic using CrewAI agents."""

    async def generate_course_from_topic(self, topic: str) -> CoursePreview:
        print("generate_course_from_topic called with topic:", topic)
        crew_instance = ReaderPathCrew()
        crew = crew_instance.reader_path_crew()
        result = await crew.kickoff_async(inputs={"topic": topic})
        course = parse_crew_course_result(result)
        if not course.topic:
            course.topic = topic
        return course
