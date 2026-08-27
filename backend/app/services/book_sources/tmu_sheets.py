"""Master's University textbook sheets as candidate sources (public CSV)."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from typing import List, Optional

import requests

from app.core.config import settings
from app.services.book_sources.types import normalize_isbn

TMU_DEFAULT_SHEETS = [
    # Undergrad
    "https://docs.google.com/spreadsheets/d/1qo8Ykw_87n9lyqkd-64c204eEmi_KvwWJQQGDGalQLk/export?format=csv&gid=0",
    # Graduate
    "https://docs.google.com/spreadsheets/d/1bk2fHXfwZzHa1Azf4rh_gwWQSKY9xLWQadH4ogSKGak/export?format=csv&gid=0",
]


@dataclass
class CandidateBook:
    title: str
    authors: str = ""
    isbn13: Optional[str] = None


def _sheet_urls() -> List[str]:
    raw = (settings.TMU_SHEET_CSV_URLS or "").strip()
    if raw:
        return [u.strip() for u in raw.split(",") if u.strip()]
    return list(TMU_DEFAULT_SHEETS)


def _pick_column(headers: List[str], *needles: str) -> Optional[int]:
    lower = [h.strip().lower() for h in headers]
    for needle in needles:
        for i, h in enumerate(lower):
            if needle in h:
                return i
    return None


def _parse_csv(text: str) -> List[CandidateBook]:
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return []
    headers = rows[0]
    title_i = _pick_column(headers, "title", "book", "textbook", "work")
    author_i = _pick_column(headers, "author", "authors")
    isbn_i = _pick_column(headers, "isbn")
    if title_i is None:
        # Fallback: first non-empty-looking text column
        title_i = 0

    candidates: List[CandidateBook] = []
    for row in rows[1:]:
        if title_i >= len(row):
            continue
        title = (row[title_i] or "").strip()
        if len(title) < 3:
            continue
        authors = ""
        if author_i is not None and author_i < len(row):
            authors = (row[author_i] or "").strip()
        isbn13 = None
        if isbn_i is not None and isbn_i < len(row):
            isbn13 = normalize_isbn(row[isbn_i] or "")
        candidates.append(CandidateBook(title=title, authors=authors, isbn13=isbn13))
    return candidates


def fetch_tmu_candidates() -> List[CandidateBook]:
    """Fetch TMU CSVs. Soft-fail per sheet (log and continue)."""
    out: List[CandidateBook] = []
    seen = set()
    for url in _sheet_urls():
        try:
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                print(f"TMU sheet fetch failed ({response.status_code}): {url}")
                continue
            batch = _parse_csv(response.text)
            print(f"TMU sheet loaded {len(batch)} rows from {url}")
            for c in batch:
                key = (c.isbn13 or "") + "|" + c.title.lower()
                if key in seen:
                    continue
                seen.add(key)
                out.append(c)
        except requests.RequestException as exc:
            print(f"TMU sheet fetch error: {exc} ({url})")
    return out


def filter_candidates_for_topic(
    candidates: List[CandidateBook], topic: str, limit: int = 40
) -> List[CandidateBook]:
    tokens = {t for t in re.split(r"[^a-z0-9]+", topic.lower()) if len(t) > 2}
    if not tokens:
        return candidates[:limit]

    scored = []
    for c in candidates:
        hay = f"{c.title} {c.authors}".lower()
        score = sum(1 for t in tokens if t in hay)
        if score > 0:
            scored.append((score, c))
    scored.sort(key=lambda x: -x[0])
    if scored:
        return [c for _, c in scored[:limit]]
    # If nothing overlaps, return a small sample so resolve still can help related curricula
    return candidates[: min(12, limit)]
