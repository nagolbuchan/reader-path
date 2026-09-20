"""Fail-closed course assembly: drop unverified/duplicates; no leftover swaps."""

from __future__ import annotations

import pytest

from app.models.course import BookReading, CoursePreview, ModuleItem
from app.services.book_catalog import validate_course_readings
from app.services.book_sources.types import BookRecord


def _record(n: int, title: str | None = None) -> BookRecord:
    title = title or f"Topic Book {n}"
    gb_id = f"gb{n}"
    return BookRecord(
        source="google_books",
        source_id=gb_id,
        title=title,
        authors=f"Author {n}",
        link=f"https://books.google.com/books?id={gb_id}",
        description="validated",
        isbn13=f"978000000000{n}" if n < 10 else None,
        google_books_id=gb_id,
    )


def _reading_from(record: BookRecord) -> BookReading:
    return BookReading(
        title=record.title,
        authors=record.authors,
        link=record.link,
        google_books_id=record.google_books_id,
        isbn13=record.isbn13,
    )


def _course(readings: list[BookReading]) -> CoursePreview:
    return CoursePreview(
        title="Test Course",
        description="desc",
        topic="stoicism",
        category="philosophy",
        modules=[
            ModuleItem(
                module_title="Foundations",
                learning_objectives=["learn"],
                assigned_readings=readings,
                assignments=[],
            )
        ],
    )


def test_unverified_reading_is_dropped_not_replaced_with_leftover() -> None:
    catalog_books = [_record(i) for i in range(1, 8)]
    catalog = {b.catalog_key: b for b in catalog_books}
    leftover = catalog_books[-1]

    readings = [_reading_from(b) for b in catalog_books[:6]]
    readings.append(
        BookReading(
            title="Quantum Baking for Cats",
            authors="Jane Fakeauthor",
            link="https://example.com/fake",
        )
    )

    course, repairs = validate_course_readings(_course(readings), catalog)
    titles = [r.title for r in course.modules[0].assigned_readings]

    assert "Quantum Baking for Cats" not in titles
    assert leftover.title not in titles
    assert len(titles) == 6
    assert any("dropped unverified" in r for r in repairs)
    assert all("replaced unverified" not in r for r in repairs)


def test_duplicate_is_dropped_and_module_padded_from_unused_topic_books() -> None:
    catalog_books = [_record(i) for i in range(1, 8)]
    catalog = {b.catalog_key: b for b in catalog_books}

    readings = [_reading_from(b) for b in catalog_books[:5]]
    readings.append(_reading_from(catalog_books[0]))  # duplicate of book 1

    course, repairs = validate_course_readings(_course(readings), catalog)
    titles = [r.title for r in course.modules[0].assigned_readings]

    assert len(titles) == 6
    assert len(set(titles)) == 6
    assert any("dropped duplicate" in r for r in repairs)
    assert any("padded with topic-sourced" in r for r in repairs)
    assert catalog_books[5].title in titles


def test_fails_if_module_cannot_reach_six_real_readings() -> None:
    catalog_books = [_record(i) for i in range(1, 5)]
    catalog = {b.catalog_key: b for b in catalog_books}
    readings = [_reading_from(b) for b in catalog_books]
    readings.append(
        BookReading(title="Hallucinated Title", authors="Nobody", link="https://x")
    )
    readings.append(
        BookReading(title="Another Fake", authors="Nobody", link="https://y")
    )

    with pytest.raises(ValueError, match="fewer than 6 unique verified readings"):
        validate_course_readings(_course(readings), catalog)
