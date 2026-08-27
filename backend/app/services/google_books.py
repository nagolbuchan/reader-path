"""Backward-compatible re-exports for Google Books helpers."""

from app.services.book_sources.google_books import (
    GoogleBooksError,
    resolve_by_isbn,
    search_volumes,
)
from app.services.book_sources.merge import format_catalog_for_agent
from app.services.book_sources.types import BookRecord

__all__ = [
    "BookRecord",
    "GoogleBooksError",
    "format_catalog_for_agent",
    "resolve_by_isbn",
    "search_volumes",
]
