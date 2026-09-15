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
    isbn10: Optional[str] = None
    amazon_url: Optional[str] = None
    google_books_id: Optional[str] = None
    open_library_id: Optional[str] = None
    loc_control_number: Optional[str] = None
    published_year: Optional[int] = None

    @property
    def catalog_key(self) -> str:
        if self.isbn13:
            return f"isbn:{self.isbn13}"
        if self.google_books_id:
            return f"gb:{self.google_books_id}"
        if self.open_library_id:
            return f"ol:{self.open_library_id}"
        if self.loc_control_number:
            return f"loc:{self.loc_control_number}"
        return f"{self.source}:{self.source_id}"


def normalize_isbn(raw: str) -> Optional[str]:
    digits = "".join(c for c in (raw or "") if c.isdigit() or c.upper() == "X")
    if len(digits) == 10 or len(digits) == 13:
        return digits.upper()
    return None


def _isbn10_check_digit(body9: str) -> str:
    total = sum((10 - i) * int(body9[i]) for i in range(9))
    remainder = total % 11
    check = 11 - remainder
    if check == 10:
        return "X"
    if check == 11:
        return "0"
    return str(check)


def isbn13_to_isbn10(isbn: Optional[str]) -> Optional[str]:
    """Convert ISBN-13 (978…) to ISBN-10. 979 prefixes have no ISBN-10 equivalent."""
    cleaned = normalize_isbn(isbn or "")
    if not cleaned:
        return None
    if len(cleaned) == 10:
        return cleaned
    if len(cleaned) == 13 and cleaned.startswith("978"):
        body = cleaned[3:12]
        if body.isdigit() and len(body) == 9:
            return body + _isbn10_check_digit(body)
    return None


def amazon_url_for_isbn(isbn: Optional[str], tag: str = "") -> Optional[str]:
    """
    Stable Amazon URL from an ISBN. Prefer /dp/{isbn10} when a 978 ISBN-13
    (or native ISBN-10) is available; otherwise ISBN search. No ISBN → None.
    """
    cleaned = normalize_isbn(isbn or "")
    if not cleaned:
        return None
    isbn10 = isbn13_to_isbn10(cleaned)
    if isbn10:
        url = f"https://www.amazon.com/dp/{isbn10}"
    else:
        url = f"https://www.amazon.com/s?k={cleaned}"
    tag = (tag or "").strip()
    if tag:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}tag={tag}"
    return url


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
