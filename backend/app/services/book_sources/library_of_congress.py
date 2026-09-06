"""Library of Congress verified provider (public SRU — no API key)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import List, Optional
from xml.etree.ElementTree import Element

import requests

from app.services.book_sources.types import BookRecord, normalize_isbn, parse_year

SRU_BASE = "http://lx2.loc.gov:210/lcdb"
USER_AGENT = "ReaderPath/1.0 (course generation; educational)"

_DC_NS = "http://purl.org/dc/elements/1.1/"
_DC = {"dc": _DC_NS}
_SRW = {"srw": "http://www.loc.gov/zing/srw/"}


class LocError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


def _text(el: Optional[Element]) -> str:
    if el is None or el.text is None:
        return ""
    return el.text.strip()


def _all_texts(parent: Element, local_name: str) -> List[str]:
    """Collect text from DC elements regardless of prefix style."""
    values: List[str] = []
    for el in parent.findall(f"dc:{local_name}", _DC):
        t = _text(el)
        if t:
            values.append(t)
    if not values:
        for el in parent.findall(f"{{{_DC_NS}}}{local_name}"):
            t = _text(el)
            if t:
                values.append(t)
    return values


def _pick_isbn13(identifiers: List[str]) -> Optional[str]:
    for raw in identifiers:
        # Common forms: "ISBN 978..." or bare digits
        cleaned = normalize_isbn(raw)
        if cleaned and len(cleaned) == 13:
            return cleaned
    for raw in identifiers:
        cleaned = normalize_isbn(raw)
        if cleaned:
            return cleaned
    return None


def _pick_lccn(identifiers: List[str]) -> Optional[str]:
    for raw in identifiers:
        lower = raw.lower()
        if "lccn" in lower or "loc control" in lower:
            digits = re.sub(r"[^0-9a-zA-Z]", "", raw.split()[-1])
            if digits:
                return digits
        # Bare LCCN-like tokens (e.g. 2001023456)
        m = re.search(r"\b(\d{2,4}[\d\-]{4,12})\b", raw)
        if m and "isbn" not in lower:
            return re.sub(r"[^0-9a-zA-Z]", "", m.group(1))
    return None


def _loc_permalink(lccn: Optional[str], source_id: str) -> str:
    if lccn:
        return f"https://lccn.loc.gov/{lccn}"
    return f"https://catalog.loc.gov/vwebv/search?searchArg={source_id}&searchCode=GKEY%5E*&searchType=0"


def _record_from_dc(dc_root: Element, index: int) -> Optional[BookRecord]:
    titles = _all_texts(dc_root, "title")
    if not titles:
        return None
    title = titles[0].rstrip(" /")
    authors = ", ".join(_all_texts(dc_root, "creator")) or "Unknown Author"
    identifiers = _all_texts(dc_root, "identifier")
    descriptions = _all_texts(dc_root, "description")
    dates = _all_texts(dc_root, "date")

    isbn13 = _pick_isbn13(identifiers)
    lccn = _pick_lccn(identifiers)
    source_id = lccn or isbn13 or f"loc-{index}"
    description = descriptions[0] if descriptions else "No description available."
    if len(description) > 280:
        description = description[:280] + "..."
    year = None
    for d in dates:
        year = parse_year(d)
        if year:
            break

    return BookRecord(
        source="library_of_congress",
        source_id=source_id,
        title=title,
        authors=authors,
        link=_loc_permalink(lccn, source_id),
        description=description,
        isbn13=isbn13,
        loc_control_number=lccn,
        published_year=year,
    )


def _parse_sru_response(xml_text: str) -> List[BookRecord]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise LocError(f"LOC SRU XML parse failed: {exc}") from exc

    books: List[BookRecord] = []
    # Records may be under srw:records/srw:record or without namespace prefixes
    records = root.findall(".//{http://www.loc.gov/zing/srw/}record")
    if not records:
        records = root.findall(".//record")

    for i, record in enumerate(records):
        data = record.find("{http://www.loc.gov/zing/srw/}recordData")
        if data is None:
            data = record.find("recordData")
        if data is None:
            continue
        # DC root is often a direct child; sometimes wrapped
        dc = None
        for child in list(data):
            tag = child.tag
            if tag.endswith("dc") or tag == "dc" or "elements/1.1" in tag:
                dc = child
                break
            # Some responses put dc:* elements directly under recordData
            if tag.endswith("title") or tag.endswith("}title"):
                dc = data
                break
        if dc is None and list(data):
            dc = data
        if dc is None:
            continue
        book = _record_from_dc(dc, i)
        if book:
            books.append(book)
    return books


def _sru_search(cql: str, max_results: int) -> List[BookRecord]:
    params = {
        "operation": "searchRetrieve",
        "version": "1.1",
        "query": cql,
        "maximumRecords": str(min(max(1, max_results), 40)),
        "recordSchema": "dc",
        "startRecord": "1",
    }
    try:
        response = requests.get(
            SRU_BASE,
            params=params,
            timeout=25,
            headers={"User-Agent": USER_AGENT, "Accept": "application/xml"},
        )
    except requests.RequestException as exc:
        raise LocError(f"LOC SRU request failed: {exc}") from exc

    if response.status_code == 429:
        raise LocError("LOC SRU rate limit reached.", status_code=429)
    if response.status_code != 200:
        raise LocError(
            f"LOC SRU error {response.status_code}: {response.text[:300]}",
            status_code=response.status_code,
        )
    return _parse_sru_response(response.text)


def search_loc(query: str, max_results: int = 40) -> List[BookRecord]:
    """Keyword search against the LOC bibliographic catalog."""
    q = (query or "").strip()
    if not q:
        return []
    safe = q.replace('"', "")
    try:
        return _sru_search(safe, max_results=max_results)
    except LocError as first_err:
        try:
            return _sru_search(f'dc.title="{safe}"', max_results=max_results)
        except LocError:
            raise first_err from None


def resolve_by_isbn(isbn: str) -> Optional[BookRecord]:
    cleaned = normalize_isbn(isbn)
    if not cleaned:
        return None
    try:
        hits = _sru_search(f'bath.isbn="{cleaned}"', max_results=5)
    except LocError:
        return None
    for hit in hits:
        if hit.isbn13 == cleaned or not hit.isbn13:
            if not hit.isbn13:
                hit.isbn13 = cleaned
            return hit
    return hits[0] if hits else None
