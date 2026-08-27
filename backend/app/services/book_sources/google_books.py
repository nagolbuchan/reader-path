"""Google Books verified provider."""

from __future__ import annotations

from typing import List, Optional

import requests

from app.core.config import settings
from app.services.book_sources.types import BookRecord, normalize_isbn


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
        books.append(
            BookRecord(
                source="google_books",
                source_id=volume_id,
                title=title,
                authors=", ".join(authors_list),
                link=link,
                description=description,
                isbn13=_extract_isbn13(info),
                google_books_id=volume_id,
            )
        )
    return books


def resolve_by_isbn(isbn: str) -> Optional[BookRecord]:
    cleaned = normalize_isbn(isbn)
    if not cleaned:
        return None
    try:
        books = search_volumes(f"isbn:{cleaned}", max_results=5)
    except GoogleBooksError:
        return None
    for book in books:
        if book.isbn13 == cleaned or cleaned in (book.isbn13 or ""):
            return book
    return books[0] if books else None
