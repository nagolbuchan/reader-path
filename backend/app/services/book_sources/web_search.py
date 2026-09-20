"""Serper-backed web discovery. Hits are untrusted candidates, never proof."""

from __future__ import annotations

import re
from typing import Iterable, List, Optional, Sequence

import requests

from app.core.config import settings
from app.services.book_sources.tmu_sheets import CandidateBook
from app.services.book_sources.types import BookRecord, normalize_isbn

SERPER_ENDPOINT = "https://google.serper.dev/search"

_SITE_SUFFIX = re.compile(
    r"\s*[-|–—:]\s*(?:Amazon(?:\.com)?|Goodreads|Wikipedia(?:, the free encyclopedia)?"
    r"|Google Books|WorldCat|Barnes & Noble|Audible|Publishers Weekly"
    r"|Bookshop(?:\.org)?|ThriftBooks|AbeBooks|Penguin Random House"
    r"|YouTube|Reddit|Facebook|Instagram).*$",
    re.I,
)
_ISBN_PREFIX_RE = re.compile(
    r"ISBN(?:-1[03])?[:\s]*([0-9Xx][0-9Xx\- ]{8,20})",
    re.I,
)
_ISBN13_RE = re.compile(r"97[89][\d\- ]{10,17}")
_AUTHOR_RE = re.compile(
    r"\b(?:written\s+by|authored\s+by|author[s]?\s*:|by)\s+"
    r"([A-Z][\w.'\-]+(?:\s+(?:and|&)\s+[A-Z][\w.'\-]+"
    r"|\s+[A-Z][\w.'\-]+){0,4})",
)


class SerperError(Exception):
    """Raised when Serper cannot be used (missing key, HTTP, transport)."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


def extract_isbn(text: str) -> Optional[str]:
    """Pull an ISBN from snippet text. Presence is a hint, not validation."""
    if not text:
        return None
    for match in _ISBN_PREFIX_RE.finditer(text):
        cleaned = normalize_isbn(match.group(1))
        if cleaned:
            return cleaned
    for match in _ISBN13_RE.finditer(text):
        cleaned = normalize_isbn(match.group(0))
        if cleaned and len(cleaned) == 13:
            return cleaned
    return None


def extract_author(text: str) -> str:
    if not text:
        return ""
    match = _AUTHOR_RE.search(text)
    if not match:
        return ""
    author = re.sub(r"\s+", " ", match.group(1)).strip(" ,.;:")
    # Avoid swallowing the rest of a sentence after a short name.
    parts = author.split()
    if len(parts) > 5:
        author = " ".join(parts[:5])
    return author


def parse_web_result(
    title: str, snippet: str = "", url: str = ""
) -> Optional[CandidateBook]:
    """
    Turn a search snippet into an untrusted CandidateBook.

    The snippet is never treated as proof that the book exists; callers must
    validate through Google Books before promoting the candidate.
    """
    raw_title = (title or "").strip()
    if not raw_title:
        return None
    cleaned_title = _SITE_SUFFIX.sub("", raw_title).strip()
    if len(cleaned_title) < 3:
        return None

    haystack = f"{raw_title} {snippet or ''}"
    isbn13 = extract_isbn(haystack)
    authors = extract_author(snippet or "") or extract_author(haystack)
    return CandidateBook(
        title=cleaned_title,
        authors=authors,
        isbn13=isbn13,
        source_url=(url or "").strip() or None,
    )


def candidates_from_serper_organic(organic: Sequence[dict]) -> List[CandidateBook]:
    """Parse Serper organic hits into untrusted candidates (no existence check)."""
    out: List[CandidateBook] = []
    seen: set[tuple[str, str]] = set()
    for hit in organic or []:
        candidate = parse_web_result(
            title=str(hit.get("title") or ""),
            snippet=str(hit.get("snippet") or ""),
            url=str(hit.get("link") or ""),
        )
        if not candidate:
            continue
        key = (candidate.isbn13 or "", candidate.title.lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(candidate)
    return out


def candidate_from_record(record: BookRecord) -> CandidateBook:
    """OL/LoC (or other) catalog hits are suggestions only until GB validates."""
    return CandidateBook(
        title=record.title,
        authors=record.authors or "",
        isbn13=record.isbn13,
        source_url=record.link or None,
    )


def web_queries_for(topic: str, category: str = "other") -> List[str]:
    t = (topic or "").strip()
    if not t:
        return []
    queries = [
        f"{t} book",
        f"{t} books ISBN",
        f"best books on {t}",
        f"{t} textbook",
    ]
    try:
        from app.services.topic_classifier import catalog_queries_for

        extras = catalog_queries_for(t, category)  # type: ignore[arg-type]
    except Exception:
        extras = []
    for extra in extras[1:3]:
        queries.append(f"{extra} book")
    seen: set[str] = set()
    unique: List[str] = []
    for q in queries:
        key = q.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(q)
    return unique[:5]


def serper_search(query: str, num: int = 10) -> List[dict]:
    """Return Serper organic hits. Untrusted; do not expose this to the LLM."""
    api_key = (settings.SERPER_API_KEY or "").strip()
    if not api_key:
        raise SerperError("SERPER_API_KEY is not configured")

    q = (query or "").strip()
    if not q:
        return []

    try:
        response = requests.post(
            SERPER_ENDPOINT,
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json",
            },
            json={"q": q, "num": min(max(num, 1), 20)},
            timeout=20,
        )
    except requests.RequestException as exc:
        raise SerperError(f"Serper request failed: {exc}") from exc

    if response.status_code in (401, 403):
        raise SerperError(
            "Serper API rejected the request (check SERPER_API_KEY).",
            status_code=response.status_code,
        )
    if response.status_code == 429:
        raise SerperError("Serper API rate limit reached.", status_code=429)
    if response.status_code != 200:
        raise SerperError(
            f"Serper API error {response.status_code}: {response.text[:300]}",
            status_code=response.status_code,
        )

    data = response.json() if response.content else {}
    organic = data.get("organic") or []
    return [hit for hit in organic if isinstance(hit, dict)]


def search_web_candidates(
    topic: str,
    category: str = "other",
    *,
    max_per_query: int = 10,
) -> List[CandidateBook]:
    """Discover untrusted book candidates on the open web via Serper."""
    collected: List[CandidateBook] = []
    seen: set[tuple[str, str]] = set()
    errors: List[str] = []

    for query in web_queries_for(topic, category):
        try:
            organic = serper_search(query, num=max_per_query)
        except SerperError as exc:
            errors.append(str(exc))
            continue
        for candidate in candidates_from_serper_organic(organic):
            key = (candidate.isbn13 or "", candidate.title.lower())
            if key in seen:
                continue
            seen.add(key)
            collected.append(candidate)

    if not collected and errors:
        raise SerperError(errors[0])
    return collected


def search_web_candidates_for_query(
    query: str, *, max_results: int = 10
) -> List[CandidateBook]:
    """Single-query web discovery for agent tools. Still untrusted."""
    organic = serper_search(query, num=max_results)
    return candidates_from_serper_organic(organic)


def dedupe_candidates(candidates: Iterable[CandidateBook]) -> List[CandidateBook]:
    out: List[CandidateBook] = []
    seen: set[tuple[str, str, str]] = set()
    for candidate in candidates:
        title = (candidate.title or "").strip().lower()
        if not title:
            continue
        key = (candidate.isbn13 or "", title, (candidate.authors or "").strip().lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(candidate)
    return out
