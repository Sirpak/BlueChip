"""Matchup context endpoints (news, later injuries/weather)."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.auth.deps import UserDep
from app.services import game_news

router = APIRouter(prefix="/api/games", tags=["games-context"])


@router.get("/news")
def game_news_feed(
    _user: UserDep,
    league: str = Query(..., pattern="^(NFL|CFB)$"),
    away_team: str = Query(..., min_length=1, max_length=12),
    home_team: str = Query(..., min_length=1, max_length=12),
    away_espn_id: str | None = Query(default=None),
    home_espn_id: str | None = Query(default=None),
    away_name: str | None = Query(default=None),
    home_name: str | None = Query(default=None),
    limit: int = Query(default=12, ge=1, le=30),
) -> dict:
    return game_news.matchup_news(
        league=league,
        away_abbr=away_team,
        home_abbr=home_team,
        away_espn_id=away_espn_id,
        home_espn_id=home_espn_id,
        away_name=away_name,
        home_name=home_name,
        limit=limit,
    )
