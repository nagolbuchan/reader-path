from crewai.tools import tool

from app.services.book_catalog import record_books
from app.services.book_sources import google_books as gb
from app.services.book_sources import open_library as ol
from app.services.book_sources.merge import format_catalog_for_agent, merge_records


@tool
def ask_human(question: str) -> str:
    """
    If a user's topic is unclear, ask them a clarifying question to better understand what they want to learn.
    """
    print(f"\n\n[AGENT IS ASKING]: {question}")
    user_response = input("Your Answer: ")
    return f"The user said: {user_response}"


@tool("Verified Books Topic Search Tool")
def search_books_by_topic(topic: str) -> str:
    """
    Searches verified catalogs (Google Books + Open Library) for real books.
    Returns only real, existing books with stable IDs. Never invents titles.
    """
    collected = []
    errors = []

    try:
        collected.extend(gb.search_volumes(topic, max_results=40))
    except gb.GoogleBooksError as exc:
        errors.append(str(exc))

    try:
        collected.extend(ol.search_open_library(topic, max_results=40))
    except ol.OpenLibraryError as exc:
        errors.append(str(exc))

    if not collected:
        if errors:
            return f"FATAL: {' | '.join(errors)}"
        return f"No books found for topic: {topic}. Try a different sub-query."

    merged = list(merge_records(collected).values())
    record_books(merged)
    return format_catalog_for_agent(merged)
