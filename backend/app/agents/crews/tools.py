# Option 1 (most common now)
from crewai.tools import tool

from app.services.book_catalog import record_books
from app.services.google_books import GoogleBooksError, format_catalog_for_agent, search_volumes


@tool
def ask_human(question: str) -> str:
    """
    If a user's topic is unclear, ask them a clarifying question to better understand what they want to learn.
    """
    print(f"\n\n[AGENT IS ASKING]: {question}")
    user_response = input("Your Answer: ")
    return f"The user said: {user_response}"


@tool("Google Books Topic Search Tool")
def search_books_by_topic(topic: str) -> str:
    """Searches Google Books for real books matching a topic. Returns only real, existing books with IDs."""
    try:
        books = search_volumes(topic, max_results=40)
    except GoogleBooksError as exc:
        # FATAL prefix — generation must abort if catalog stays empty
        return f"FATAL: {exc}"

    if not books:
        return f"No books found for topic: {topic}. Try a different sub-query."

    record_books(books)
    return format_catalog_for_agent(books)
