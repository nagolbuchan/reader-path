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

MIN_READINGS_PER_MODULE = 4


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


def _is_used(book: BookRecord, seen_ids: set[str], seen_titles: set[str]) -> bool:
    title_key = _normalize(book.title)
    if book.google_books_id in seen_ids:
        return True
    if title_key and title_key in seen_titles:
        return True
    return False


def _next_unused(
    catalog: Dict[str, BookRecord], seen_ids: set[str], seen_titles: set[str]
) -> Optional[BookRecord]:
    for book in catalog.values():
        if not _is_used(book, seen_ids, seen_titles):
            return book
    return None


def _claim(
    book: BookRecord,
    seen_ids: set[str],
    seen_titles: set[str],
    summary: Optional[str] = None,
) -> BookReading:
    seen_ids.add(book.google_books_id)
    title_key = _normalize(book.title)
    if title_key:
        seen_titles.add(title_key)
    return BookReading(
        title=book.title,
        authors=book.authors,
        link=book.link,
        summary=summary or book.description,
        google_books_id=book.google_books_id,
    )


def validate_course_readings(
    course: CoursePreview, catalog: Dict[str, BookRecord]
) -> Tuple[CoursePreview, List[str]]:
    """
    Enrich readings with catalog IDs/links.

    Duplicates and unverified slots are repaired by pulling unused books from the
    verified catalog. Fails only if a module cannot reach 4 unique verified readings.
    """
    if not catalog:
        raise ValueError(
            "No verified Google Books catalog available. Cannot accept course readings."
        )

    repairs: List[str] = []
    seen_ids: set[str] = set()
    seen_titles: set[str] = set()
    new_modules: List[ModuleItem] = []

    for module in course.modules:
        verified: List[BookReading] = []

        for reading in module.assigned_readings:
            match = _match_record(reading, catalog)

            if not match:
                replacement = _next_unused(catalog, seen_ids, seen_titles)
                if not replacement:
                    repairs.append(
                        f"{module.module_title}: could not replace unverified "
                        f"“{reading.title}” (catalog exhausted)"
                    )
                    continue
                repairs.append(
                    f"{module.module_title}: replaced unverified “{reading.title}” "
                    f"→ “{replacement.title}”"
                )
                verified.append(_claim(replacement, seen_ids, seen_titles))
                continue

            if _is_used(match, seen_ids, seen_titles):
                replacement = _next_unused(catalog, seen_ids, seen_titles)
                if not replacement:
                    repairs.append(
                        f"{module.module_title}: could not replace duplicate "
                        f"“{match.title}” (catalog exhausted)"
                    )
                    continue
                repairs.append(
                    f"{module.module_title}: replaced duplicate “{match.title}” "
                    f"→ “{replacement.title}”"
                )
                verified.append(
                    _claim(
                        replacement,
                        seen_ids,
                        seen_titles,
                        summary=reading.summary,
                    )
                )
                continue

            verified.append(
                _claim(
                    match,
                    seen_ids,
                    seen_titles,
                    summary=reading.summary or match.description,
                )
            )

        while len(verified) < MIN_READINGS_PER_MODULE:
            filler = _next_unused(catalog, seen_ids, seen_titles)
            if not filler:
                break
            repairs.append(
                f"{module.module_title}: filled slot with “{filler.title}”"
            )
            verified.append(_claim(filler, seen_ids, seen_titles))

        if len(verified) < MIN_READINGS_PER_MODULE:
            raise ValueError(
                f"Module “{module.module_title}” has fewer than "
                f"{MIN_READINGS_PER_MODULE} unique verified readings after repair "
                f"(have {len(verified)}; catalog may be too small). "
                + ("; ".join(repairs[-5:]) if repairs else "")
            )

        new_modules.append(
            module.model_copy(update={"assigned_readings": verified})
        )

    if repairs:
        print("Reading repairs:", "; ".join(repairs[:20]))

    return course.model_copy(update={"modules": new_modules}), repairs
