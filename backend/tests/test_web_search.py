"""Web-snippet parser emits untrusted CandidateBook records, not proof."""

from __future__ import annotations

from app.services.book_sources.tmu_sheets import CandidateBook
from app.services.book_sources.types import BookRecord
from app.services.book_sources.web_search import (
    candidates_from_serper_organic,
    extract_isbn,
    parse_web_result,
)


def test_parser_extracts_title_author_isbn_without_treating_snippet_as_proof() -> None:
    candidate = parse_web_result(
        title="Sapiens: A Brief History of Humankind - Wikipedia",
        snippet=(
            "Sapiens: A Brief History of Humankind is a book by Yuval Noah Harari "
            "published in 2014. ISBN 978-0062316097"
        ),
        url="https://en.wikipedia.org/wiki/Sapiens:_A_Brief_History_of_Humankind",
    )

    assert candidate is not None
    assert isinstance(candidate, CandidateBook)
    assert not isinstance(candidate, BookRecord)
    assert "Sapiens" in candidate.title
    assert "Wikipedia" not in candidate.title
    assert "Harari" in candidate.authors
    assert candidate.isbn13 == "9780062316097"
    assert (
        candidate.source_url
        == "https://en.wikipedia.org/wiki/Sapiens:_A_Brief_History_of_Humankind"
    )
    assert not hasattr(candidate, "google_books_id")


def test_extract_isbn_prefers_prefixed_isbn13() -> None:
    assert extract_isbn("See ISBN-13: 978-0-06-231609-7 for details") == "9780062316097"


def test_serper_organic_hits_stay_untrusted_candidates() -> None:
    organic = [
        {
            "title": "Meditations - Amazon.com",
            "snippet": "Meditations is a series of personal writings by Marcus Aurelius.",
            "link": "https://www.amazon.com/dp/0140449337",
        },
        {
            "title": "10 Best Stoicism Books",
            "snippet": "A blog list of recommendations.",
            "link": "https://example.com/best-stoicism",
        },
    ]
    candidates = candidates_from_serper_organic(organic)
    assert all(isinstance(c, CandidateBook) for c in candidates)
    assert all(not hasattr(c, "google_books_id") for c in candidates)
    assert candidates[0].title == "Meditations"
    assert "Marcus" in candidates[0].authors
