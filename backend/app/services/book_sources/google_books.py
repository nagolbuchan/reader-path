"""Google Books existence validator (not a primary discovery source)."""

from __future__ import annotations

from typing import List, Optional

import requests

from app.core.config import settings
from app.services.book_sources.types import (
    BookRecord,
    isbn13_to_isbn10,
    normalize_isbn,
    parse_year,
)


class GoogleBooksError(Exception):
    """Raised when Google Books cannot be used (auth, rate limit, transport)."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


def _extract_isbn13(info: dict) -> Optional[str]:
    for ident in info.get("industryIdentifiers") or []:
        if ident.get("type") == "ISBN_13":
            return normalize_isbn(ident.get("identifier") or "")
    for ident in info.get("industryIdentifiers") or []:
        if ident.get("type") == "ISBN_10":
            return normalize_isbn(ident.get("identifier") or "")
    return None


def _extract_isbn10(info: dict) -> Optional[str]:
    for ident in info.get("industryIdentifiers") or []:
        if ident.get("type") == "ISBN_10":
            return normalize_isbn(ident.get("identifier") or "")
    return None


def search_volumes(query: str, max_results: int = 40) -> List[BookRecord]:
    """
    Search Google Books. Raises GoogleBooksError on missing key, HTTP errors,
    or transport failures. Returns an empty list when the query has no hits.
    """
    api_key = settings.GOOGLE_BOOKS_API_KEY or ""
    if not api_key:
        raise GoogleBooksError("GOOGLE_BOOKS_API_KEY is not configured")

    params = {
        "q": query,
        "maxResults": min(max_results, 40),
        "printType": "books",
        "orderBy": "relevance",
        "key": api_key,
    }

    try:
        response = requests.get(
            "https://www.googleapis.com/books/v1/volumes",
            params=params,
            timeout=15,
        )
    except requests.RequestException as exc:
        raise GoogleBooksError(f"Google Books request failed: {exc}") from exc

    if response.status_code in (401, 403):
        raise GoogleBooksError(
            "Google Books API rejected the request (check API key / quota).",
            status_code=response.status_code,
        )
    if response.status_code == 429:
        raise GoogleBooksError(
            "Google Books API rate limit reached. Try again later.",
            status_code=429,
        )
    if response.status_code != 200:
        raise GoogleBooksError(
            f"Google Books API error {response.status_code}: {response.text[:300]}",
            status_code=response.status_code,
        )

    items = response.json().get("items") or []
    books: List[BookRecord] = []
    for item in items:
        volume_id = item.get("id") or ""
        info = item.get("volumeInfo") or {}
        title = (info.get("title") or "").strip()
        if not volume_id or not title:
            continue
        authors_list = info.get("authors") or ["Unknown Author"]
        description = info.get("description") or "No description available."
        if len(description) > 280:
            description = description[:280] + "..."
        link = (
            info.get("infoLink")
            or info.get("previewLink")
            or f"https://books.google.com/books?id={volume_id}"
        )
        isbn13 = _extract_isbn13(info)
        books.append(
            BookRecord(
                source="google_books",
                source_id=volume_id,
                title=title,
                authors=", ".join(authors_list),
                link=link,
                description=description,
                isbn13=isbn13,
                isbn10=_extract_isbn10(info) or isbn13_to_isbn10(isbn13),
                google_books_id=volume_id,
                published_year=parse_year(info.get("publishedDate")),
            )
        )
    return books


def _isbn_matches(cleaned: str, book: BookRecord) -> bool:
    book_ids = {
        i
        for i in (book.isbn13, book.isbn10, isbn13_to_isbn10(book.isbn13))
        if i
    }
    if cleaned in book_ids:
        return True
    if len(cleaned) == 13:
        as10 = isbn13_to_isbn10(cleaned)
        return bool(as10 and as10 in book_ids)
    return False


def resolve_by_isbn(isbn: str) -> Optional[BookRecord]:
    """Return a Google Books record only when the ISBN actually matches."""
    cleaned = normalize_isbn(isbn)
    if not cleaned:
        return None
    try:
        books = search_volumes(f"isbn:{cleaned}", max_results=5)
    except GoogleBooksError:
        return None
    for book in books:
        if _isbn_matches(cleaned, book):
            return book
    return None
