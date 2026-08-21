"""News headlines → structured events (W2B). Prefer facts + citations, not article republication."""

from __future__ import annotations

import re
from typing import Any


_INJURY = re.compile(
    r"\b(injur|questionable|doubtful|out for|ruled out|DNP|limited|ankle|knee|hamstring|"
    r"concussion|IR\b|inactive|miss(es|ed)? practice)\b",
    re.I,
)
_STARTER = re.compile(r"\b(start(ing|er)|named QB|depth chart|will start)\b", re.I)
_COACH = re.compile(r"\b(coach|coordinator|said|told reporters|press conference)\b", re.I)
_WEATHER = re.compile(r"\b(weather|wind|snow|rain|cold|forecast)\b", re.I)
_MARKET = re.compile(r"\b(line move|odds|spread|opened|now -?\d)\b", re.I)


def classify_headline(headline: str) -> str:
    if _INJURY.search(headline):
        return "injury"
    if _STARTER.search(headline):
        return "starter_change"
    if _WEATHER.search(headline):
        return "weather"
    if _MARKET.search(headline):
        return "market"
    if _COACH.search(headline):
        return "coach_comment"
    return "other"


def events_from_news(articles: list[dict[str, Any]], *, game_id: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for a in articles:
        headline = a.get("headline") or ""
        et = classify_headline(headline)
        events.append(
            {
                "game_id": game_id,
                "event_type": et,
                "headline": headline,
                "publisher": a.get("publisher") or a.get("source") or "web",
                "source_url": a.get("url"),
                "bucket": a.get("bucket"),
                "structured_fact": headline[:240],
                "confidence": 0.7 if et != "other" else 0.45,
                "tier": 2 if (a.get("publisher") or "").lower() in {"espn", "nfl.com"} else 3,
            }
        )
    return events
