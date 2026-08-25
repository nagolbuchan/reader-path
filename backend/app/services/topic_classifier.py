"""Classify a learning topic into history | sciences | other."""

from __future__ import annotations

import json
import re
from typing import Literal

import httpx

from app.core.config import settings

TopicCategory = Literal["history", "sciences", "other"]

_SYSTEM = """You classify learning topics for a reading-course product.
Return ONLY valid JSON: {"category":"history"|"sciences"|"other","reason":"short"}

Rules:
- history: historical periods, civilizations, wars, cultures studied as history, primary-source eras
- sciences: natural sciences, engineering, applied trades/skills (e.g. electrical engineering, welding, machine learning, chemistry, physics, biology, medicine as practice)
- other: philosophy, literature as art, religion as belief (not church history), soft skills, misc
"""


def classify_topic(topic: str) -> TopicCategory:
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured")

    payload = {
        "model": settings.OPENAI_MODEL or "gpt-4o-mini",
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": f"Topic: {topic}"},
        ],
    }
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
    if response.status_code != 200:
        raise ValueError(
            f"Topic classification failed ({response.status_code}): {response.text[:200]}"
        )

    raw = response.json()["choices"][0]["message"]["content"] or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(match.group(0)) if match else {}

    category = str(data.get("category", "other")).strip().lower()
    if category not in ("history", "sciences", "other"):
        return "other"
    return category  # type: ignore[return-value]


def catalog_queries_for(topic: str, category: TopicCategory) -> list[str]:
    """Multiple Google Books queries to seed a verified catalog."""
    t = topic.strip()
    if category == "history":
        return [
            t,
            f"{t} primary sources",
            f"{t} documentary history",
            f"{t} chronicles letters",
            f"{t} history sources",
        ]
    if category == "sciences":
        return [
            t,
            f"{t} textbook",
            f"history of {t}",
            f"{t} foundations",
            f"{t} handbook",
            f"{t} principles",
        ]
    return [t, f"{t} introduction", f"{t} guide", f"{t} essays"]
