"""Chronological ordering helpers for history courses."""

from __future__ import annotations

from typing import List

from app.models.course import BookReading, CoursePreview, ModuleItem


def _reading_year(reading: BookReading) -> int:
    return reading.published_year if reading.published_year is not None else 9999


def _module_earliest_year(module: ModuleItem) -> int:
    years = [r.published_year for r in module.assigned_readings if r.published_year]
    return min(years) if years else 9999


def order_history_course_chronologically(course: CoursePreview) -> CoursePreview:
    """
    For history courses: sort readings within each module earliest→latest,
    then sort modules by the earliest dated reading in each module.
    Primary-sources-only modules are kept toward the front when dates tie.
    """
    modules: List[ModuleItem] = []
    for module in course.modules:
        readings = sorted(module.assigned_readings, key=_reading_year)
        modules.append(module.model_copy(update={"assigned_readings": readings}))

    modules.sort(
        key=lambda m: (
            _module_earliest_year(m),
            0 if m.is_primary_sources_only else 1,
            m.module_title.lower(),
        )
    )
    return course.model_copy(update={"modules": modules})
