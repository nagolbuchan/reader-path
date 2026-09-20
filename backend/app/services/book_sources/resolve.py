"""Validate untrusted candidates through Google Books (existence gate)."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import List, Optional

from app.services.book_sources import google_books as gb
from app.services.book_sources import library_of_congress as loc
from app.services.book_sources import open_library as ol
from app.services.book_sources.merge import merge_records
from app.services.book_sources.tmu_sheets import CandidateBook
from app.services.book_sources.types import BookRecord

STRICT_TITLE_RATIO = 0.92
_MIN_CORE_LEN = 6


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _core_title(text: str) -> str:
    raw = (text or "").strip()
    core = re.split(r"\s*[:–—]\s*", raw, maxsplit=1)[0]
    core = re.split(r"\s+-\s+", core, maxsplit=1)[0]
    return _normalize(core)


def _author_tokens(text: str) -> set[str]:
    stop = {"the", "and", "of", "by", "a", "an", "unknown", "author", "authors"}
    return {t for t in _normalize(text).split() if t not in stop and len(t) > 1}


def is_strict_match(candidate: CandidateBook, record: BookRecord) -> bool:
    """
    Accept only normalized title equality or high similarity, plus overlapping
    author tokens when the candidate names an author. Never first-hit.
    """
    cand_title = _normalize(candidate.title)
    rec_title = _normalize(record.title)
    if not cand_title or not rec_title:
        return False

    titles_equal = cand_title == rec_title
    high_sim = (
        SequenceMatcher(None, cand_title, rec_title).ratio() >= STRICT_TITLE_RATIO
    )
    cand_core = _core_title(candidate.title)
    rec_core = _core_title(record.title)
    cores_equal = (
        bool(cand_core)
        and cand_core == rec_core
        and len(cand_core) >= _MIN_CORE_LEN
    )
    if not (titles_equal or high_sim or cores_equal):
        return False

    cand_authors = _author_tokens(candidate.authors)
    rec_authors = _author_tokens(record.authors)
    if cand_authors and rec_authors and not (cand_authors & rec_authors):
        return False
    return True


def _enrich_with_catalog_ids(record: BookRecord) -> BookRecord:
    """Attach Open Library / LoC IDs after Google Books has proven the book."""
    extras: List[BookRecord] = []
    isbn = record.isbn13
    if isbn:
        try:
            ol_hit = ol.resolve_by_isbn(isbn)
        except ol.OpenLibraryError:
            ol_hit = None
        if ol_hit:
            extras.append(ol_hit)
        try:
            loc_hit = loc.resolve_by_isbn(isbn)
        except loc.LocError:
            loc_hit = None
        if loc_hit:
            extras.append(loc_hit)
    if not extras:
        return record
    merged = merge_records([record, *extras])
    return next(iter(merged.values()))


def _lookup_google_books_strict(candidate: CandidateBook) -> Optional[BookRecord]:
    query = candidate.title
    if candidate.authors:
        query = f"{candidate.title} {candidate.authors}"
    try:
        hits = gb.search_volumes(query, max_results=5)
    except gb.GoogleBooksError:
        return None
    for hit in hits:
        if is_strict_match(candidate, hit):
            return hit
    return None


def resolve_candidate(candidate: CandidateBook) -> Optional[BookRecord]:
    """
    Google Books is the authority. ISBN must match; otherwise only a strict
    title (+ author) match is accepted. No first-hit or ISBN fallthrough.
    """
    if not (candidate.title or "").strip() and not candidate.isbn13:
        return None

    record: Optional[BookRecord] = None
    if candidate.isbn13:
        record = gb.resolve_by_isbn(candidate.isbn13)
    if record is None and (candidate.title or "").strip():
        record = _lookup_google_books_strict(candidate)
    if record is None:
        return None
    if not record.google_books_id:
        return None
    return _enrich_with_catalog_ids(record)


def resolve_candidates(candidates: List[CandidateBook]) -> List[BookRecord]:
    resolved: List[BookRecord] = []
    # Prefer ISBN-bearing candidates — cheaper, stronger validation.
    ordered = sorted(
        candidates,
        key=lambda c: (0 if c.isbn13 else 1),
    )
    seen_keys: set[str] = set()
    for candidate in ordered:
        rec = resolve_candidate(candidate)
        if not rec:
            continue
        key = rec.catalog_key
        if key in seen_keys:
            continue
        seen_keys.add(key)
        resolved.append(rec)
    return resolved
