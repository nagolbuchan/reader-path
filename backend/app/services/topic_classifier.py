"""Classify a learning topic into ReaderPath curriculum categories."""

from __future__ import annotations

import json
import re
from typing import Literal, get_args

import httpx

from app.core.config import settings

TopicCategory = Literal[
    "history",
    "sciences",
    "trade_craft",
    "philosophy",
    "literature",
    "languages",
    "professional",
    "religion_theology",
    "other",
]

VALID_CATEGORIES = set(get_args(TopicCategory))

_SYSTEM = """You classify learning topics for a reading-course product.
Return ONLY valid JSON: {"category":"<one of the allowed values>","reason":"short"}

Allowed category values (exact strings):
- history
- sciences
- trade_craft
- philosophy
- literature
- languages
- professional
- religion_theology
- other

Rules:
- history: historical periods, civilizations, wars, cultures studied as history, primary-source eras
- sciences: natural sciences, engineering, math, CS/ML, medicine as science (NOT hands-on trades)
- trade_craft: applied trades and crafts (welding, carpentry, cooking, blacksmithing, machining, etc.)
- philosophy: philosophy, ethics, epistemology, political philosophy as philosophy
- literature: novels, poetry, drama, literary movements studied as literature
- languages: learning a language, linguistics, grammar, reading competence in a tongue
- professional: law, business practice, education practice, professional standards/case-based fields
- religion_theology: religion, theology, scripture study as faith/doctrine (not church history alone)
- other: soft skills, misc, or unclear topics that do not fit above
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
    if category not in VALID_CATEGORIES:
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
    if category == "trade_craft":
        return [
            t,
            f"{t} handbook",
            f"{t} manual",
            f"{t} techniques",
            f"history of {t}",
            f"{t} for beginners",
        ]
    if category == "philosophy":
        return [
            t,
            f"{t} primary texts",
            f"{t} philosophy",
            f"{t} anthology",
            f"{t} commentary",
        ]
    if category == "literature":
        return [
            t,
            f"{t} literature",
            f"{t} poems",
            f"{t} novels",
            f"{t} literary criticism",
            f"{t} anthology",
        ]
    if category == "languages":
        return [
            t,
            f"{t} grammar",
            f"{t} reader",
            f"{t} textbook",
            f"{t} vocabulary",
            f"learn {t}",
        ]
    if category == "professional":
        return [
            t,
            f"{t} handbook",
            f"{t} casebook",
            f"{t} practice",
            f"{t} standards",
            f"{t} textbook",
        ]
    if category == "religion_theology":
        return [
            t,
            f"{t} scripture",
            f"{t} theology",
            f"{t} commentary",
            f"{t} sacred texts",
            f"{t} introduction",
        ]
    return [t, f"{t} introduction", f"{t} guide", f"{t} essays"]
