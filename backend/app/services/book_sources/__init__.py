"""Multi-source book providers (web discovery, Google Books validation, enrichment)."""

from app.services.book_sources.merge import format_catalog_for_agent, merge_records
from app.services.book_sources.types import BookRecord

__all__ = [
    "BookRecord",
    "format_catalog_for_agent",
    "merge_records",
]
