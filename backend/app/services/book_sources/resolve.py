"""Resolve candidate titles/ISBNs into verified BookRecords."""

from __future__ import annotations

from typing import List, Optional

from app.services.book_sources import google_books as gb
from app.services.book_sources import open_library as ol
from app.services.book_sources.tmu_sheets import CandidateBook
from app.services.book_sources.types import BookRecord


def resolve_candidate(candidate: CandidateBook) -> Optional[BookRecord]:
    if candidate.isbn13:
        record = ol.resolve_by_isbn(candidate.isbn13)
        if record:
            return record
        record = gb.resolve_by_isbn(candidate.isbn13)
        if record:
            return record

    query = candidate.title
    if candidate.authors:
        query = f"{candidate.title} {candidate.authors}"

    try:
        ol_hits = ol.search_open_library(query, max_results=5)
    except ol.OpenLibraryError:
        ol_hits = []
    if ol_hits:
        return ol_hits[0]

    try:
        gb_hits = gb.search_volumes(query, max_results=5)
    except gb.GoogleBooksError:
        gb_hits = []
    if gb_hits:
        return gb_hits[0]
    return None


def resolve_candidates(candidates: List[CandidateBook]) -> List[BookRecord]:
    resolved: List[BookRecord] = []
    for c in candidates:
        rec = resolve_candidate(c)
        if rec:
            resolved.append(rec)
    return resolved
