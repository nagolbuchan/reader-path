"""Verified book catalog for a single generation run + reading validation."""

from __future__ import annotations

import re
import threading
import unicodedata
from typing import Dict, Iterable, List, Optional, Tuple

from app.models.course import BookReading, CoursePreview, ModuleItem
from app.services.google_books import BookRecord

_lock = threading.Lock()
_active_catalog: Optional[Dict[str, BookRecord]] = None


def start_catalog(seed: Optional[Iterable[BookRecord]] = None) -> Dict[str, BookRecord]:
    catalog: Dict[str, BookRecord] = {}
    if seed:
        for book in seed:
            catalog[book.google_books_id] = book
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
            _active_catalog[book.google_books_id] = book


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


def _match_record(
    reading: BookReading, catalog: Dict[str, BookRecord]
) -> Optional[BookRecord]:
    if reading.google_books_id and reading.google_books_id in catalog:
        return catalog[reading.google_books_id]

    title_n = _normalize(reading.title)
    authors_n = _normalize(reading.authors or "")
    if not title_n:
        return None

    for book in catalog.values():
        bt = _normalize(book.title)
        if title_n != bt and title_n not in bt and bt not in title_n:
            continue
        if authors_n:
            a_tokens = set(authors_n.split())
            b_tokens = set(_normalize(book.authors).split())
            if a_tokens and b_tokens and not (a_tokens & b_tokens):
                continue
        return book
    return None


def validate_course_readings(
    course: CoursePreview, catalog: Dict[str, BookRecord]
) -> Tuple[CoursePreview, List[str]]:
    """
    Enrich readings with catalog IDs/links. Fail closed on any unverified title.
    """
    if not catalog:
        raise ValueError(
            "No verified Google Books catalog available. Cannot accept course readings."
        )

    rejected: List[str] = []
    new_modules: List[ModuleItem] = []

    for module in course.modules:
        verified: List[BookReading] = []
        for reading in module.assigned_readings:
            match = _match_record(reading, catalog)
            if not match:
                rejected.append(
                    f"{module.module_title}: unverified “{reading.title}”"
                )
                continue
            verified.append(
                BookReading(
                    title=match.title,
                    authors=match.authors,
                    link=match.link,
                    summary=reading.summary or match.description,
                    google_books_id=match.google_books_id,
                )
            )

        if len(verified) < 4:
            raise ValueError(
                f"Module “{module.module_title}” has fewer than 4 verified readings."
            )

        new_modules.append(
            module.model_copy(update={"assigned_readings": verified})
        )

    if rejected:
        raise ValueError(
            "Rejected unverified books (not in Google Books catalog): "
            + "; ".join(rejected[:8])
        )

    return course.model_copy(update={"modules": new_modules}), rejected
