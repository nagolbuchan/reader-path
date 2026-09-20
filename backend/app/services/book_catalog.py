"""Run catalog + thin post-crew membership/uniqueness check."""

from __future__ import annotations

import re
import threading
import unicodedata
from typing import Dict, Iterable, List, Optional, Tuple

from app.core.config import settings
from app.models.course import BookReading, CoursePreview, ModuleItem
from app.services.book_sources.types import (
    BookRecord,
    amazon_url_for_isbn,
    isbn13_to_isbn10,
)

_lock = threading.Lock()
_active_catalog: Optional[Dict[str, BookRecord]] = None

MIN_READINGS_PER_MODULE = 6


def start_catalog(seed: Optional[Iterable[BookRecord]] = None) -> Dict[str, BookRecord]:
    catalog: Dict[str, BookRecord] = {}
    if seed:
        for book in seed:
            catalog[book.catalog_key] = book
    with _lock:
        global _active_catalog
        _active_catalog = catalog
    return catalog


def get_catalog() -> Dict[str, BookRecord]:
    with _lock:
        return dict(_active_catalog or {})


def record_books(books: Iterable[BookRecord]) -> None:
    with _lock:
        if _active_catalog is None:
            return
        for book in books:
            _active_catalog[book.catalog_key] = book


def clear_catalog() -> None:
    with _lock:
        global _active_catalog
        _active_catalog = None


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _identity_keys(book: BookRecord) -> set[str]:
    keys = {book.catalog_key}
    if book.google_books_id:
        keys.add(f"gb:{book.google_books_id}")
    return keys


def _match_record(
    reading: BookReading, catalog: Dict[str, BookRecord]
) -> Optional[BookRecord]:
    """Match by google_books_id, then isbn13, then exact normalized title."""
    if reading.google_books_id:
        for book in catalog.values():
            if book.google_books_id == reading.google_books_id:
                return book
    if reading.isbn13:
        for book in catalog.values():
            if book.isbn13 == reading.isbn13:
                return book

    title_n = _normalize(reading.title)
    if not title_n:
        return None
    for book in catalog.values():
        if _normalize(book.title) == title_n:
            return book
    return None


def _is_used(book: BookRecord, seen_ids: set[str]) -> bool:
    return bool(_identity_keys(book) & seen_ids)


def _mark_used(book: BookRecord, seen_ids: set[str]) -> None:
    seen_ids.update(_identity_keys(book))


def book_to_reading(
    book: BookRecord, summary: Optional[str] = None
) -> BookReading:
    isbn10 = book.isbn10 or isbn13_to_isbn10(book.isbn13)
    amazon_url = book.amazon_url or amazon_url_for_isbn(
        isbn10 or book.isbn13,
        tag=settings.AMAZON_ASSOCIATE_TAG or "",
    )
    return BookReading(
        title=book.title,
        authors=book.authors,
        link=book.link,
        summary=summary or book.description,
        google_books_id=book.google_books_id,
        open_library_id=book.open_library_id,
        loc_control_number=book.loc_control_number,
        isbn13=book.isbn13,
        isbn10=isbn10,
        amazon_url=amazon_url,
        published_year=book.published_year,
    )


def unused_catalog_readings(
    course: CoursePreview, catalog: Dict[str, BookRecord]
) -> List[BookReading]:
    """Return verified catalog books that are not assigned anywhere in the course."""
    seen_ids: set[str] = set()

    for module in course.modules:
        for reading in module.assigned_readings:
            match = _match_record(reading, catalog)
            if match:
                _mark_used(match, seen_ids)
                continue
            if reading.google_books_id:
                seen_ids.add(f"gb:{reading.google_books_id}")
            if reading.isbn13:
                seen_ids.add(f"isbn:{reading.isbn13}")

    return [
        book_to_reading(book)
        for book in catalog.values()
        if not _is_used(book, seen_ids)
    ]


def validate_course_readings(
    course: CoursePreview, catalog: Dict[str, BookRecord]
) -> Tuple[CoursePreview, List[str]]:
    """
    Keep only readings that match the Google Books–validated run catalog.

    Unverified and duplicate readings are dropped. Short modules are not
    padded from leftover catalog titles. Fails if a module cannot reach MIN
    unique verified readings.
    """
    if not catalog:
        raise ValueError(
            "No verified book catalog available. Cannot accept course readings."
        )

    repairs: List[str] = []
    seen_ids: set[str] = set()
    new_modules: List[ModuleItem] = []

    for module in course.modules:
        verified: List[BookReading] = []

        for reading in module.assigned_readings:
            match = _match_record(reading, catalog)

            if not match:
                repairs.append(
                    f"{module.module_title}: dropped unverified “{reading.title}”"
                )
                continue

            if _is_used(match, seen_ids):
                repairs.append(
                    f"{module.module_title}: dropped duplicate “{match.title}”"
                )
                continue

            _mark_used(match, seen_ids)
            verified.append(
                book_to_reading(
                    match, summary=reading.summary or match.description
                )
            )

        if len(verified) < MIN_READINGS_PER_MODULE:
            raise ValueError(
                f"Module “{module.module_title}” has fewer than "
                f"{MIN_READINGS_PER_MODULE} unique verified readings "
                f"(have {len(verified)}; not enough validated topic books). "
                + ("; ".join(repairs[-5:]) if repairs else "")
            )

        new_modules.append(
            module.model_copy(update={"assigned_readings": verified})
        )

    if repairs:
        # Avoid Windows console encode failures on arrows / curly quotes.
        safe = "; ".join(repairs[:20]).encode("ascii", "replace").decode("ascii")
        print("Reading repairs:", safe)

    return course.model_copy(update={"modules": new_modules}), repairs
