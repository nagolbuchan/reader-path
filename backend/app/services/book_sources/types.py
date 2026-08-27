"""Shared book record types for multi-source catalogs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class BookRecord:
    source: str  # google_books | open_library | …
    source_id: str
    title: str
    authors: str
    link: str
    description: str
    isbn13: Optional[str] = None
    google_books_id: Optional[str] = None
    open_library_id: Optional[str] = None
    published_year: Optional[int] = None

    @property
    def catalog_key(self) -> str:
        if self.isbn13:
            return f"isbn:{self.isbn13}"
        if self.google_books_id:
            return f"gb:{self.google_books_id}"
        if self.open_library_id:
            return f"ol:{self.open_library_id}"
        return f"{self.source}:{self.source_id}"


def normalize_isbn(raw: str) -> Optional[str]:
    digits = "".join(c for c in (raw or "") if c.isdigit() or c.upper() == "X")
    if len(digits) == 10 or len(digits) == 13:
        return digits.upper()
    return None


def parse_year(raw: object) -> Optional[int]:
    if raw is None:
        return None
    if isinstance(raw, int):
        return raw if 100 <= raw <= 2100 else None
    text = str(raw).strip()
    if not text:
        return None
    match = re.search(r"(?<!\d)([1-9]\d{2,3})(?!\d)", text)
    if not match:
        return None
    year = int(match.group(1))
    return year if 100 <= year <= 2100 else None
