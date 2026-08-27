"""Merge and format multi-source book catalogs."""

from __future__ import annotations

from typing import Dict, Iterable, List

from app.services.book_sources.types import BookRecord


def merge_records(books: Iterable[BookRecord]) -> Dict[str, BookRecord]:
    """
    Dedupe by ISBN-13, then google/ol id, then catalog_key.
    Prefer Google Books when merging the same ISBN.
    """
    by_key: Dict[str, BookRecord] = {}
    source_rank = {"google_books": 0, "open_library": 1}

    for book in books:
        keys = [book.catalog_key]
        if book.isbn13:
            keys.append(f"isbn:{book.isbn13}")
        if book.google_books_id:
            keys.append(f"gb:{book.google_books_id}")
        if book.open_library_id:
            keys.append(f"ol:{book.open_library_id}")

        existing = None
        existing_key = None
        for k in keys:
            if k in by_key:
                existing = by_key[k]
                existing_key = k
                break

        if existing is None:
            by_key[book.catalog_key] = book
            continue

        # Merge IDs onto the preferred record
        prefer_new = source_rank.get(book.source, 9) < source_rank.get(
            existing.source, 9
        )
        primary = book if prefer_new else existing
        secondary = existing if prefer_new else book
        merged = BookRecord(
            source=primary.source,
            source_id=primary.source_id,
            title=primary.title or secondary.title,
            authors=primary.authors or secondary.authors,
            link=primary.link or secondary.link,
            description=primary.description or secondary.description,
            isbn13=primary.isbn13 or secondary.isbn13,
            google_books_id=primary.google_books_id or secondary.google_books_id,
            open_library_id=primary.open_library_id or secondary.open_library_id,
            published_year=(
                min(y for y in (primary.published_year, secondary.published_year) if y)
                if (primary.published_year or secondary.published_year)
                else None
            ),
        )
        # Drop old key aliases pointing at existing
        for k, v in list(by_key.items()):
            if v is existing:
                del by_key[k]
        by_key[merged.catalog_key] = merged

    return by_key


def format_catalog_for_agent(
    books: List[BookRecord], *, chronological: bool = False
) -> str:
    ordered = list(books)
    if chronological:
        ordered.sort(key=lambda b: (b.published_year is None, b.published_year or 9999))

    blocks = []
    for b in ordered:
        lines = [
            f"Source: {b.source}",
            f"ID: {b.source_id}",
        ]
        if b.google_books_id:
            lines.append(f"GoogleBooksID: {b.google_books_id}")
        if b.open_library_id:
            lines.append(f"OpenLibraryID: {b.open_library_id}")
        if b.isbn13:
            lines.append(f"ISBN13: {b.isbn13}")
        if b.published_year:
            lines.append(f"Year: {b.published_year}")
        lines.extend(
            [
                f"Title: {b.title}",
                f"Authors: {b.authors}",
                f"Description: {b.description}",
                f"Link: {b.link}",
                "---",
            ]
        )
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)
