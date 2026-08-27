"""Project Gutenberg enrichment — free ebook links for verified readings."""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

import requests

from app.models.course import CoursePreview


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def lookup_gutenberg_url(title: str, authors: str = "") -> Optional[str]:
    """
    Search Project Gutenberg via Gutendex. Return ebook URL only on a confident
    title match. Never invent links.
    """
    q = title.strip()
    if not q:
        return None
    try:
        response = requests.get(
            "https://gutendex.com/books/",
            params={"search": q},
            timeout=15,
            headers={"User-Agent": "ReaderPath/1.0"},
        )
    except requests.RequestException:
        return None
    if response.status_code != 200:
        return None

    results = response.json().get("results") or []
    title_n = _normalize(title)
    author_n = _normalize(authors)
    author_tokens = set(author_n.split()) if author_n else set()

    for item in results[:8]:
        item_title = _normalize(item.get("title") or "")
        if not item_title:
            continue
        title_ok = (
            item_title == title_n
            or title_n in item_title
            or item_title in title_n
        )
        if not title_ok:
            continue
        if author_tokens:
            names = " ".join(
                _normalize(a.get("name") or "") for a in (item.get("authors") or [])
            )
            name_tokens = set(names.split())
            if author_tokens and name_tokens and not (author_tokens & name_tokens):
                continue
        book_id = item.get("id")
        if not book_id:
            continue
        return f"https://www.gutenberg.org/ebooks/{book_id}"

    return None


def enrich_course_with_gutenberg(course: CoursePreview) -> CoursePreview:
    new_modules = []
    for module in course.modules:
        readings = []
        for reading in module.assigned_readings:
            if reading.gutenberg_url:
                readings.append(reading)
                continue
            url = lookup_gutenberg_url(reading.title, reading.authors or "")
            if url:
                readings.append(reading.model_copy(update={"gutenberg_url": url}))
            else:
                readings.append(reading)
        new_modules.append(
            module.model_copy(update={"assigned_readings": readings})
        )
    return course.model_copy(update={"modules": new_modules})
