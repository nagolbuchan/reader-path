from crewai import tool
from typing import Optional

@tool
def ask_human(question: str) -> str:
    """
    If a user's topic is unclear, ask them a clarifying question to better understand what they want to learn.  For example, if the user's topic is 'Classical Greek',
    you might ask if they are interested in learning Classical Greek, or are they only interested in reading authentic texts from that time period?  
    Once you understand the user's needs, then give the librarian the refined topic to search for books
    """
    print(f"\n\n[AGENT IS ASKING]: {question}")
    user_response = input("Your Answer: ")
    return f"The user said: {user_response}"