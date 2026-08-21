"""EDGE Headline Engine — rules over validated-looking stats. MATCHUP SIGNAL only."""

from __future__ import annotations

from typing import Any

from ml.matchup.edges import MatchupEdge


def headline_cards(edges: list[MatchupEdge], *, limit: int = 4) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for e in edges:
        if e.strength == "EVEN" and abs(e.mismatch_z) < 0.35:
            continue
        cards.append(
            {
                "marks": {"MAJOR": "+++", "STRONG": "++", "MILD": "+", "EVEN": "·", "NEGATIVE": "-"}.get(
                    e.strength, "·"
                ),
                "key": e.key,
                "title": e.title,
                "team": e.side_team,
                "strength": e.strength,
                "fan_line": e.fan_line,
                "mismatch_z": e.mismatch_z,
                "percentile_hint": _percentile_hint(e.mismatch_z),
                "label": e.label,
                "why": e.why,
                "home_stat": e.home_stat,
                "away_stat": e.away_stat,
            }
        )
        if len(cards) >= limit:
            break
    return cards


def _percentile_hint(z: float) -> str | None:
    az = abs(z)
    if az < 1.0:
        return None
    if az >= 1.96:
        return "More extreme than ~95% of similar unit mismatches in a normal sample."
    if az >= 1.65:
        return "More extreme than ~90% of similar unit mismatches in a normal sample."
    return "Clearly tilted versus a typical NFL/CFB unit matchup."


def slate_top_edges(edges: list[MatchupEdge], *, limit: int = 3) -> list[str]:
    lines: list[str] = []
    for e in edges[:limit]:
        if e.strength == "EVEN":
            continue
        mark = {"MAJOR": "+++", "STRONG": "++", "MILD": "+"}.get(e.strength, "+")
        lines.append(f"{mark} {e.side_team} {e.key.replace('_', ' ').title()}")
    return lines
