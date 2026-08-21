"""ESPN scoreboard fetch + parse (schedule/odds context, not canonical PBP)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
import truststore

from app.config import get_settings

truststore.inject_into_ssl()

logger = logging.getLogger(__name__)

SCOREBOARD_URL = "https://site.web.api.espn.com/apis/site/v2/sports/football/{sport}/scoreboard"
SPORTS = {"NFL": "nfl", "CFB": "college-football"}
SEASON_TYPE = {1: "PRE", 2: "REG", 3: "POST"}
CACHE_TTL = timedelta(minutes=20)

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.espn.com/",
}


def _cache_dir() -> Path:
    path = get_settings().raw_data_dir / "espn" / "scoreboard"
    path.mkdir(parents=True, exist_ok=True)
    return path


def cache_path(league: str, year: int, season_type: int, week: int) -> Path:
    return _cache_dir() / f"{league.lower()}_{year}_st{season_type}_w{week}.json"


def _read_cache(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    age = datetime.now(timezone.utc) - datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    if age > CACHE_TTL:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def fetch_scoreboard(
    league: str,
    *,
    year: int | None = None,
    week: int | None = None,
    season_type: int | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """GET ESPN scoreboard JSON, cached under data/raw/espn/scoreboard/."""
    league = league.upper()
    sport = SPORTS[league]
    params: dict[str, Any] = {"limit": 300}
    if year is not None:
        params["year"] = year
    if week is not None:
        params["week"] = week
    if season_type is not None:
        params["seasontype"] = season_type
    if league == "CFB":
        params["groups"] = 80  # FBS

    path: Path | None = None
    if year is not None and week is not None and season_type is not None:
        path = cache_path(league, year, season_type, week)
        if not force:
            cached = _read_cache(path)
            if cached is not None:
                return cached

    url = SCOREBOARD_URL.format(sport=sport)
    logger.info("ESPN scoreboard %s %s", league, params)
    with httpx.Client(headers=_BROWSER_HEADERS, follow_redirects=True, timeout=45.0) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()
    if path is not None:
        path.write_text(json.dumps(payload), encoding="utf-8")
    return payload


def parse_kickoff(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _competitor(comp: dict[str, Any], side: str) -> dict[str, Any]:
    for row in comp.get("competitors") or []:
        if row.get("homeAway") == side:
            team = row.get("team") or {}
            return {
                "abbr": team.get("abbreviation") or row.get("abbreviation") or "?",
                "name": team.get("displayName") or row.get("displayName"),
                "score": row.get("score"),
            }
    return {"abbr": "?", "name": None, "score": None}


def home_spread_from_odds(odds: dict[str, Any]) -> float | None:
    """Betting convention: negative = home favored."""
    home = odds.get("homeTeamOdds") or {}
    raw = odds.get("spread")
    if raw is None:
        return None
    spread = float(raw)
    if home.get("favorite") is True:
        return -abs(spread)
    if home.get("underdog") is True or home.get("favorite") is False:
        return abs(spread)
    return spread


def format_spread_label(home_abbr: str, away_abbr: str, home_spread: float | None) -> str | None:
    if home_spread is None:
        return None
    if home_spread <= 0:
        return f"{home_abbr} {home_spread:+.1f}"
    return f"{away_abbr} {-home_spread:+.1f}"


def parse_event(event: dict[str, Any], *, league: str, fallback_week: int | None, fallback_season: int | None, fallback_stype: str) -> dict[str, Any] | None:
    comp = (event.get("competitions") or [None])[0]
    if not isinstance(comp, dict):
        return None
    home = _competitor(comp, "home")
    away = _competitor(comp, "away")
    kickoff = parse_kickoff(event.get("date") or comp.get("date"))
    status_type = ((event.get("status") or {}).get("type") or {})
    status_name = (status_type.get("name") or status_type.get("state") or "unknown").lower()
    odds_list = comp.get("odds") or []
    odds = odds_list[0] if odds_list else {}
    home_spread = home_spread_from_odds(odds) if odds else None
    total = odds.get("overUnder") if odds else None
    book = ((odds.get("provider") or {}).get("name") if odds else None)
    season_block = event.get("season") or {}
    week_block = event.get("week") or {}
    stype_num = season_block.get("type")
    season_type = SEASON_TYPE.get(int(stype_num), fallback_stype) if stype_num else fallback_stype
    week = week_block.get("number") or fallback_week
    season = season_block.get("year") or fallback_season
    neutral = bool(comp.get("neutralSite"))
    matchup = f"{away['abbr']} vs {home['abbr']}" if neutral else f"{away['abbr']} @ {home['abbr']}"
    return {
        "league": league,
        "game_id": f"espn:{event.get('id')}",
        "source_id": str(event.get("id")),
        "source": "espn",
        "kickoff": kickoff.isoformat() if kickoff else None,
        "game_date": kickoff.date().isoformat() if kickoff else None,
        "week": int(week) if week is not None else None,
        "season": int(season) if season is not None else None,
        "season_type": season_type,
        "away_team": away["abbr"],
        "home_team": home["abbr"],
        "away_name": away["name"],
        "home_name": home["name"],
        "neutral": neutral,
        "matchup": matchup,
        "home_spread": home_spread,
        "spread_label": format_spread_label(home["abbr"], away["abbr"], home_spread),
        "total_line": float(total) if total is not None else None,
        "book": book,
        "status": status_name,
        "round": _round_label(season_type, int(week) if week is not None else 0),
    }


def _round_label(season_type: str, week: int) -> str:
    if season_type == "PRE":
        return f"Pre {week}"
    if season_type == "POST":
        return f"Post {week}"
    return f"Week {week}"


def parse_scoreboard(payload: dict[str, Any], *, league: str) -> list[dict[str, Any]]:
    season_block = payload.get("season") or {}
    week_block = payload.get("week") or {}
    stype_num = season_block.get("type")
    fallback_stype = SEASON_TYPE.get(int(stype_num), "REG") if stype_num else "REG"
    games = []
    for event in payload.get("events") or []:
        parsed = parse_event(
            event,
            league=league,
            fallback_week=week_block.get("number"),
            fallback_season=season_block.get("year"),
            fallback_stype=fallback_stype,
        )
        if parsed:
            games.append(parsed)
    return games


def scoreboard_meta(payload: dict[str, Any]) -> tuple[int, int, int]:
    """Return (year, season_type, week) from a scoreboard payload."""
    season = payload.get("season") or {}
    week = payload.get("week") or {}
    year = int(season.get("year") or datetime.now(timezone.utc).year)
    stype = int(season.get("type") or 2)
    number = int(week.get("number") or 1)
    return year, stype, number
