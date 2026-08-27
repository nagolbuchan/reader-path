"""Open Library verified provider."""

from __future__ import annotations

from typing import List, Optional

import requests

from app.services.book_sources.types import BookRecord, normalize_isbn


class OpenLibraryError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


def search_open_library(query: str, max_results: int = 40) -> List[BookRecord]:
    params = {
        "q": query,
        "limit": min(max_results, 40),
        "fields": "key,title,author_name,isbn,first_sentence,edition_key",
    }
    try:
        response = requests.get(
            "https://openlibrary.org/search.json",
            params=params,
            timeout=20,
            headers={"User-Agent": "ReaderPath/1.0 (course generation)"},
        )
    except requests.RequestException as exc:
        raise OpenLibraryError(f"Open Library request failed: {exc}") from exc

    if response.status_code == 429:
        raise OpenLibraryError("Open Library rate limit reached.", status_code=429)
    if response.status_code != 200:
        raise OpenLibraryError(
            f"Open Library error {response.status_code}: {response.text[:300]}",
            status_code=response.status_code,
        )

    docs = response.json().get("docs") or []
    books: List[BookRecord] = []
    for doc in docs:
        key = (doc.get("key") or "").strip()  # e.g. /works/OL123W
        title = (doc.get("title") or "").strip()
        if not key or not title:
            continue
        olid = key.rstrip("/").split("/")[-1]
        authors = ", ".join(doc.get("author_name") or ["Unknown Author"])
        isbn13 = None
        for raw in doc.get("isbn") or []:
            isbn13 = normalize_isbn(str(raw))
            if isbn13 and len(isbn13) == 13:
                break
            if isbn13 and len(isbn13) == 10 and not isbn13:
                pass
        if not isbn13:
            for raw in doc.get("isbn") or []:
                isbn13 = normalize_isbn(str(raw))
                if isbn13:
                    break
        first = doc.get("first_sentence")
        if isinstance(first, list):
            description = first[0] if first else "No description available."
        elif isinstance(first, str):
            description = first
        else:
            description = "No description available."
        if len(description) > 280:
            description = description[:280] + "..."
        link = f"https://openlibrary.org{key}"
        books.append(
            BookRecord(
                source="open_library",
                source_id=olid,
                title=title,
                authors=authors,
                link=link,
                description=description,
                isbn13=isbn13,
                open_library_id=olid,
            )
        )
    return books


def resolve_by_isbn(isbn: str) -> Optional[BookRecord]:
    cleaned = normalize_isbn(isbn)
    if not cleaned:
        return None
    try:
        response = requests.get(
            f"https://openlibrary.org/isbn/{cleaned}.json",
            timeout=15,
            headers={"User-Agent": "ReaderPath/1.0 (course generation)"},
            allow_redirects=True,
        )
    except requests.RequestException:
        return None
    if response.status_code != 200:
        return None
    data = response.json()
    title = (data.get("title") or "").strip()
    if not title:
        return None
    key = data.get("key") or f"/books/{cleaned}"
    olid = key.rstrip("/").split("/")[-1]
    authors = "Unknown Author"
    # Authors often need extra fetches; keep simple
    desc = data.get("description")
    if isinstance(desc, dict):
        description = desc.get("value") or "No description available."
    elif isinstance(desc, str):
        description = desc
    else:
        description = "No description available."
    if len(description) > 280:
        description = description[:280] + "..."
    return BookRecord(
        source="open_library",
        source_id=olid,
        title=title,
        authors=authors,
        link=f"https://openlibrary.org{key}",
        description=description,
        isbn13=cleaned,
        open_library_id=olid,
    )
