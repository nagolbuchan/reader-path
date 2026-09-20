"""Google Books existence gate: reject hallucinations, accept ISBN, strict match."""

from __future__ import annotations

import pytest

from app.services.book_sources import google_books as gb
from app.services.book_sources import library_of_congress as loc
from app.services.book_sources import open_library as ol
from app.services.book_sources.resolve import resolve_candidate
from app.services.book_sources.tmu_sheets import CandidateBook
from app.services.book_sources.types import BookRecord

SAPIENS_ISBN = "9780062316097"


def _gb_record(
    *,
    title: str,
    authors: str,
    google_books_id: str,
    isbn13: str | None = None,
) -> BookRecord:
    return BookRecord(
        source="google_books",
        source_id=google_books_id,
        title=title,
        authors=authors,
        link=f"https://books.google.com/books?id={google_books_id}",
        description="A real book.",
        isbn13=isbn13,
        google_books_id=google_books_id,
    )


@pytest.fixture(autouse=True)
def _no_network_enrichment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ol, "resolve_by_isbn", lambda isbn: None)
    monkeypatch.setattr(loc, "resolve_by_isbn", lambda isbn: None)


def test_hallucinated_title_author_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        gb,
        "search_volumes",
        lambda query, max_results=5: [
            _gb_record(
                title="Real Intro to Chemistry",
                authors="Someone Real",
                google_books_id="real1",
            )
        ],
    )
    monkeypatch.setattr(gb, "resolve_by_isbn", lambda isbn: None)

    result = resolve_candidate(
        CandidateBook(title="Quantum Baking for Cats", authors="Jane Fakeauthor")
    )
    assert result is None


def test_real_isbn_is_accepted_with_google_books_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    accepted = _gb_record(
        title="Sapiens: A Brief History of Humankind",
        authors="Yuval Noah Harari",
        google_books_id="sapiensGB",
        isbn13=SAPIENS_ISBN,
    )

    def fake_search(query: str, max_results: int = 5) -> list[BookRecord]:
        assert query.startswith("isbn:")
        return [accepted]

    monkeypatch.setattr(gb, "search_volumes", fake_search)

    via_resolver = gb.resolve_by_isbn(SAPIENS_ISBN)
    assert via_resolver is not None
    assert via_resolver.google_books_id == "sapiensGB"
    assert via_resolver.isbn13 == SAPIENS_ISBN

    via_candidate = resolve_candidate(
        CandidateBook(
            title="whatever the snippet said",
            authors="",
            isbn13=SAPIENS_ISBN,
        )
    )
    assert via_candidate is not None
    assert via_candidate.google_books_id == "sapiensGB"


def test_resolve_by_isbn_rejects_mismatched_first_hit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wrong = _gb_record(
        title="Some Other Book",
        authors="Other Author",
        google_books_id="nope",
        isbn13="9780000000002",
    )
    monkeypatch.setattr(gb, "search_volumes", lambda query, max_results=5: [wrong])
    assert gb.resolve_by_isbn(SAPIENS_ISBN) is None


def test_strict_match_rejects_near_miss_first_hit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    near_miss = _gb_record(
        title="Sapiens Graphic Novel",
        authors="Yuval Noah Harari",
        google_books_id="graphic",
        isbn13="9780547995069",
    )
    monkeypatch.setattr(gb, "search_volumes", lambda query, max_results=5: [near_miss])
    monkeypatch.setattr(gb, "resolve_by_isbn", lambda isbn: None)

    result = resolve_candidate(
        CandidateBook(
            title="Sapiens: A Brief History of Humankind",
            authors="Yuval Noah Harari",
        )
    )
    assert result is None


def test_strict_match_accepts_later_exact_hit_not_first(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    near_miss = _gb_record(
        title="Sapiens Graphic Novel",
        authors="Yuval Noah Harari",
        google_books_id="graphic",
    )
    exact = _gb_record(
        title="Sapiens: A Brief History of Humankind",
        authors="Yuval Noah Harari",
        google_books_id="sapiensGB",
        isbn13=SAPIENS_ISBN,
    )
    monkeypatch.setattr(
        gb, "search_volumes", lambda query, max_results=5: [near_miss, exact]
    )
    monkeypatch.setattr(gb, "resolve_by_isbn", lambda isbn: None)

    result = resolve_candidate(
        CandidateBook(
            title="Sapiens: A Brief History of Humankind",
            authors="Yuval Noah Harari",
        )
    )
    assert result is not None
    assert result.google_books_id == "sapiensGB"
