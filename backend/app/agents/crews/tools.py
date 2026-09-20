from crewai.tools import tool

from app.services.book_catalog import record_books
from app.services.book_sources import library_of_congress as loc
from app.services.book_sources import open_library as ol
from app.services.book_sources.merge import format_catalog_for_agent, merge_records
from app.services.book_sources.resolve import resolve_candidates
from app.services.book_sources.web_search import (
    SerperError,
    candidate_from_record,
    dedupe_candidates,
    search_web_candidates_for_query,
)


@tool
def ask_human(question: str) -> str:
    """
    If a user's topic is unclear, ask them a clarifying question to better understand what they want to learn.
    """
    print(f"\n\n[AGENT IS ASKING]: {question}")
    user_response = input("Your Answer: ")
    return f"The user said: {user_response}"


@tool("Discover and Validate Books Tool")
def search_and_validate_books(topic: str) -> str:
    """
    Search the open web for books on a topic, then keep only titles Google Books
    can verify as real. Returns validated catalog records (IDs, ISBN, links).
    Web snippets are untrusted and never returned unless they pass validation.
    """
    query = (topic or "").strip()
    if not query:
        return "No topic provided. Try a specific book-topic query."

    candidates = []
    errors = []

    try:
        candidates.extend(search_web_candidates_for_query(query, max_results=10))
    except SerperError as exc:
        errors.append(str(exc))

    try:
        for rec in ol.search_open_library(query, max_results=15):
            candidates.append(candidate_from_record(rec))
    except ol.OpenLibraryError as exc:
        errors.append(str(exc))

    try:
        for rec in loc.search_loc(query, max_results=10):
            candidates.append(candidate_from_record(rec))
    except loc.LocError as exc:
        errors.append(str(exc))

    unique = dedupe_candidates(candidates)
    if not unique:
        if errors:
            return (
                "No book candidates found, and discovery errors occurred: "
                + " | ".join(errors)
            )
        return (
            f"No book candidates found for {query!r}. Try a more specific sub-query."
        )

    validated = resolve_candidates(unique)
    if not validated:
        return (
            f"Found {len(unique)} web/catalog mention(s) for {query!r}, but none "
            "could be validated as real books in Google Books. Do not use those "
            "snippet titles. Try a different sub-query."
        )

    merged = list(merge_records(validated).values())
    record_books(merged)
    return format_catalog_for_agent(merged)
