"""Fail-closed course assembly: drop unverified/duplicates; no leftover padding."""

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
    assert all("padded with topic-sourced" not in r for r in repairs)


def test_duplicate_is_dropped_without_padding() -> None:
    catalog_books = [_record(i) for i in range(1, 8)]
    catalog = {b.catalog_key: b for b in catalog_books}

    readings = [_reading_from(b) for b in catalog_books[:5]]
    readings.append(_reading_from(catalog_books[0]))  # duplicate of book 1

    with pytest.raises(ValueError, match="fewer than 6 unique verified readings"):
        validate_course_readings(_course(readings), catalog)


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


def test_matches_by_google_books_id_despite_wrong_title() -> None:
    catalog_books = [_record(i) for i in range(1, 8)]
    catalog = {b.catalog_key: b for b in catalog_books}
    target = catalog_books[5]

    readings = [_reading_from(b) for b in catalog_books[:5]]
    readings.append(
        BookReading(
            title="Slightly Wrong Title",
            authors="Someone Else",
            link="https://example.com/wrong",
            google_books_id=target.google_books_id,
        )
    )

    course, repairs = validate_course_readings(_course(readings), catalog)
    titles = [r.title for r in course.modules[0].assigned_readings]
    ids = [r.google_books_id for r in course.modules[0].assigned_readings]

    assert target.title in titles
    assert "Slightly Wrong Title" not in titles
    assert target.google_books_id in ids
    assert all("padded with topic-sourced" not in r for r in repairs)


def test_rejects_substring_only_title_match() -> None:
    long_title = _record(7, title="The Complete History of Rome")
    catalog_books = [_record(i) for i in range(1, 7)] + [long_title]
    catalog = {b.catalog_key: b for b in catalog_books}

    readings = [_reading_from(b) for b in catalog_books[:6]]
    readings.append(
        BookReading(
            title="History of Rome",
            authors="Author 7",
            link="https://example.com/rome",
        )
    )

    course, repairs = validate_course_readings(_course(readings), catalog)
    titles = [r.title for r in course.modules[0].assigned_readings]

    assert "History of Rome" not in titles
    assert long_title.title not in titles
    assert len(titles) == 6
    assert any("dropped unverified" in r for r in repairs)
    assert all("padded with topic-sourced" not in r for r in repairs)
