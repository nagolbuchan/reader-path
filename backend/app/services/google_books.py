"""Google Books API client — structured results, fail-closed on API errors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import requests

from app.core.config import settings


class GoogleBooksError(Exception):
    """Raised when Google Books cannot be used (auth, rate limit, transport)."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class BookRecord:
    google_books_id: str
    title: str
    authors: str
    link: str
    description: str


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
                google_books_id=volume_id,
                title=title,
                authors=", ".join(authors_list),
                link=link,
                description=description,
            )
        )
    return books


def format_catalog_for_agent(books: List[BookRecord]) -> str:
    blocks = []
    for b in books:
        blocks.append(
            f"ID: {b.google_books_id}\n"
            f"Title: {b.title}\n"
            f"Authors: {b.authors}\n"
            f"Description: {b.description}\n"
            f"Link: {b.link}\n"
            f"---"
        )
    return "\n\n".join(blocks)
