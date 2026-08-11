# Option 1 (most common now)
from crewai.tools import tool
import requests
import os


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
    """Searches Google Books for real books matching a topic. Returns only real, existing books."""
    api_key = os.getenv("GOOGLE_BOOKS_API_KEY")
    if not api_key:
        return "Error: GOOGLE_BOOKS_API_KEY is not set in environment variables."

    url = "https://www.googleapis.com/books/v1/volumes"

    params = {
        "q": topic,
        "maxResults": 12,
        "printType": "books",
        "orderBy": "relevance",
        "key": api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            return f"API Error: {response.status_code} - {response.text}"

        data = response.json()
        items = data.get("items", [])

        if not items:
            return f"No books found for topic: {topic}"

        books_summary = []
        for item in items:
            v_info = item.get("volumeInfo", {})
            title = v_info.get("title", "N/A")
            authors = v_info.get("authors", ["Unknown Author"])
            description = (
                v_info.get("description", "No description available.")[:280] + "..."
                if v_info.get("description")
                else "No description available."
            )
            preview_link = v_info.get("previewLink", "No preview available")

            books_summary.append(
                f"Title: {title}\n"
                f"Authors: {', '.join(authors)}\n"
                f"Description: {description}\n"
                f"Preview: {preview_link}\n"
                f"---"
            )

        return "\n\n".join(books_summary)

    except Exception as e:
        return f"Error searching Google Books: {str(e)}"
