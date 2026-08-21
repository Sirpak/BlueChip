"""Upcoming NFL/CFB slate for the next N days (ESPN scoreboard)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.ingest.sources.espn import (
    fetch_scoreboard,
    parse_kickoff,
    parse_scoreboard,
    scoreboard_meta,
)

logger = logging.getLogger(__name__)

HORIZON_DAYS = 28


def _advance_week(season_type: int, week: int) -> tuple[int, int]:
    if season_type == 1 and week >= 4:
        return 2, 1
    return season_type, week + 1


def weeks_ahead(season_type: int, week: int, count: int = 6) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    st, w = season_type, max(week - 1, 1)
    for _ in range(count):
        out.append((st, w))
        st, w = _advance_week(st, w)
    # unique preserve order
    seen: set[tuple[int, int]] = set()
    unique: list[tuple[int, int]] = []
    for pair in out:
        if pair not in seen:
            seen.add(pair)
            unique.append(pair)
    return unique


def _in_window(game: dict[str, Any], start: datetime, end: datetime) -> bool:
    kickoff = parse_kickoff(game.get("kickoff"))
    if kickoff is None:
        return False
    if kickoff.tzinfo is None:
        kickoff = kickoff.replace(tzinfo=timezone.utc)
    status = (game.get("status") or "").lower()
    if "final" in status or status in {"post", "status_final"}:
        return False
    return start <= kickoff <= end


def upcoming_for_league(league: str, *, horizon_days: int = HORIZON_DAYS, now: datetime | None = None) -> list[dict[str, Any]]:
    now = now or datetime.now(timezone.utc)
    start = now
    end = now + timedelta(days=horizon_days)
    try:
        current = fetch_scoreboard(league)
    except Exception:
        logger.exception("ESPN current scoreboard failed for %s", league)
        return []
    year, stype, week = scoreboard_meta(current)
    games: dict[str, dict[str, Any]] = {}
    for parsed in parse_scoreboard(current, league=league):
        games[parsed["game_id"]] = parsed
    for st, w in weeks_ahead(stype, week):
        try:
            payload = fetch_scoreboard(league, year=year, week=w, season_type=st)
        except Exception:
            logger.exception("ESPN scoreboard failed %s year=%s st=%s week=%s", league, year, st, w)
            continue
        for parsed in parse_scoreboard(payload, league=league):
            games[parsed["game_id"]] = parsed
    windowed = [g for g in games.values() if _in_window(g, start, end)]
    windowed.sort(key=lambda g: (g.get("kickoff") or "", g.get("game_id") or ""))
    return windowed


def upcoming_window(*, horizon_days: int = HORIZON_DAYS, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    nfl = upcoming_for_league("NFL", horizon_days=horizon_days, now=now)
    cfb = upcoming_for_league("CFB", horizon_days=horizon_days, now=now)
    return {
        "as_of": now.isoformat(),
        "horizon_days": horizon_days,
        "window_end": (now + timedelta(days=horizon_days)).isoformat(),
        "source": "espn",
        "nfl": nfl,
        "cfb": cfb,
        "count": {"nfl": len(nfl), "cfb": len(cfb)},
    }
