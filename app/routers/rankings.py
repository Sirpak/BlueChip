"""Team + rankings API (desk CONTEXT)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.deps import UserDep
from app.services import game_news, rankings
from db.session import get_session

router = APIRouter(tags=["rankings-teams"])


@router.get("/api/rankings")
def rankings_home(_user: UserDep, session: Session = Depends(get_session)) -> dict:
    return rankings.rankings_bundle(session)


@router.get("/api/rankings/ap-top25")
def ap_top25(_user: UserDep) -> dict:
    return rankings.ap_top25()


@router.get("/api/rankings/bcw-nfl")
def bcw_nfl(_user: UserDep, session: Session = Depends(get_session)) -> dict:
    return rankings.bcw_nfl_strength(session)


@router.get("/api/teams")
def team_directory(
    _user: UserDep,
    league: str = Query(..., pattern="^(NFL|CFB)$"),
) -> dict:
    return rankings.espn_team_directory(league)


@router.get("/api/teams/news")
def team_news(
    _user: UserDep,
    league: str = Query(..., pattern="^(NFL|CFB)$"),
    espn_id: str = Query(..., min_length=1, max_length=16),
    abbr: str = Query(default="TEAM", min_length=1, max_length=12),
    name: str | None = Query(default=None),
    limit: int = Query(default=12, ge=1, le=30),
) -> dict:
    """ESPN team-page news (same feed as /nfl/team/_/name/... and CFB team pages)."""
    directory = rankings.espn_team_directory(league)
    meta = next((t for t in directory["teams"] if t.get("espn_id") == str(espn_id)), None)
    team_url = (meta or {}).get("team_url")
    articles_raw = game_news.fetch_espn_team_news(league, espn_id, limit=limit)
    now = datetime.now(timezone.utc)
    tokens = game_news._name_tokens(abbr, name)
    rows: list[dict] = []
    seen: set[str] = set()

    for raw in articles_raw:
        item = game_news._from_espn(
            raw,
            team_side="team",
            team_abbr=abbr,
            now=now,
            tokens=tokens,
        )
        if item and item["id"] not in seen:
            item["team_url"] = team_url
            seen.add(item["id"])
            rows.append(item)

    label = name or abbr
    sport = "NFL" if league == "NFL" else "college football"
    for raw in game_news.fetch_google_news(
        f'"{label}" {sport} (injury OR preview OR roster OR QB OR odds)',
        limit=10,
    ):
        item = game_news._from_google(
            raw,
            team_side="team",
            team_abbr=abbr,
            now=now,
            tokens=tokens,
        )
        if item and item["id"] not in seen:
            item["team_url"] = team_url
            seen.add(item["id"])
            rows.append(item)

    def _ts(value: str | None) -> float:
        if not value:
            return 0.0
        try:
            return datetime.fromisoformat(value).timestamp()
        except ValueError:
            return 0.0

    rows.sort(key=lambda r: (-int(r["relevance_score"]), -_ts(r.get("published"))))
    return {
        "league": league,
        "espn_id": espn_id,
        "abbr": abbr,
        "name": name or (meta or {}).get("name"),
        "team_url": team_url,
        "logo_url": (meta or {}).get("logo_url"),
        "articles": rows[:limit],
        "count": len(rows[:limit]),
        "disclaimer": "CONTEXT only — ESPN team page + Google News aggregate. Not a PURE model feature.",
    }
