"""Seed leagues, teams, players, and Market 0 snapshots from ingested PBP."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, text, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from db.models import Game, League, OddsSnapshot, Play, Player, PlayerExternalId, Team, TeamExternalId

logger = logging.getLogger(__name__)

NFL_NAMES: dict[str, str] = {
    "ARI": "Arizona Cardinals",
    "ATL": "Atlanta Falcons",
    "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills",
    "CAR": "Carolina Panthers",
    "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals",
    "CLE": "Cleveland Browns",
    "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos",
    "DET": "Detroit Lions",
    "GB": "Green Bay Packers",
    "HOU": "Houston Texans",
    "IND": "Indianapolis Colts",
    "JAX": "Jacksonville Jaguars",
    "JAC": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs",
    "LA": "Los Angeles Rams",
    "LAC": "Los Angeles Chargers",
    "LAR": "Los Angeles Rams",
    "LV": "Las Vegas Raiders",
    "LVR": "Las Vegas Raiders",
    "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings",
    "NE": "New England Patriots",
    "NO": "New Orleans Saints",
    "NYG": "New York Giants",
    "NYJ": "New York Jets",
    "OAK": "Las Vegas Raiders",
    "PHI": "Philadelphia Eagles",
    "PIT": "Pittsburgh Steelers",
    "SD": "Los Angeles Chargers",
    "SEA": "Seattle Seahawks",
    "SF": "San Francisco 49ers",
    "STL": "Los Angeles Rams",
    "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans",
    "WAS": "Washington Commanders",
    "WSH": "Washington Commanders",
}

# Historical / alternate abbreviations → current franchise id (32-team map).
# Relocations stay the same franchise: STL/LA→LAR, OAK→LV, SD→LAC, etc.
NFL_FRANCHISE_CANON: dict[str, str] = {
    "STL": "LAR",
    "LA": "LAR",
    "OAK": "LV",
    "LVR": "LV",
    "SD": "LAC",
    "JAC": "JAX",
    "WSH": "WAS",
}

CURRENT_NFL_TEAMS: frozenset[str] = frozenset(
    {
        "ARI",
        "ATL",
        "BAL",
        "BUF",
        "CAR",
        "CHI",
        "CIN",
        "CLE",
        "DAL",
        "DEN",
        "DET",
        "GB",
        "HOU",
        "IND",
        "JAX",
        "KC",
        "LAC",
        "LAR",
        "LV",
        "MIA",
        "MIN",
        "NE",
        "NO",
        "NYG",
        "NYJ",
        "PHI",
        "PIT",
        "SEA",
        "SF",
        "TB",
        "TEN",
        "WAS",
    }
)


def canonicalize_nfl_team(abbr: str | None) -> str | None:
    """Map any historical/alt abbr onto the current 32-team franchise code."""
    if not abbr:
        return None
    key = str(abbr).strip().upper()
    if key in {"", "NONE", "NAN", "NULL", "?"}:
        return None
    return NFL_FRANCHISE_CANON.get(key, key)


def nfl_team_name(abbr: str | None) -> str:
    if not abbr:
        return "—"
    canon = canonicalize_nfl_team(abbr) or abbr
    return NFL_NAMES.get(canon, NFL_NAMES.get(str(abbr).upper(), str(abbr)))


def nfl_franchise_sql(column: str) -> str:
    """SQL CASE that folds historical NFL abbrs into the current franchise."""
    parts = [f"CASE {column}"]
    for old, new in sorted(NFL_FRANCHISE_CANON.items()):
        parts.append(f"WHEN '{old}' THEN '{new}'")
    parts.append(f"ELSE {column}")
    parts.append("END")
    return " ".join(parts)


def canonicalize_nfl_columns(df: Any, columns: list[str]) -> Any:
    """In-place franchise fold for pandas DataFrames used in features/ingest."""
    import pandas as pd

    if df is None or getattr(df, "empty", True):
        return df
    out = df
    for col in columns:
        if col not in out.columns:
            continue
        out[col] = out[col].map(lambda v: canonicalize_nfl_team(v) if pd.notna(v) else v)
    return out



def _now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_leagues(session: Session) -> None:
    for league_id, name in (("NFL", "National Football League"), ("CFB", "NCAA Football")):
        existing = session.get(League, league_id)
        if existing is None:
            session.add(League(league_id=league_id, name=name))
    session.flush()


def seed_teams_from_games(session: Session) -> int:
    rows = session.execute(text("SELECT DISTINCT home_team AS abbr FROM games UNION SELECT DISTINCT away_team FROM games"))
    abbrs = sorted(
        {
            canonicalize_nfl_team(str(r[0]))
            for r in rows
            if r[0] and canonicalize_nfl_team(str(r[0])) in CURRENT_NFL_TEAMS
        }
    )
    existing = set(session.scalars(select(Team.abbreviation).where(Team.league == "NFL")))
    created = 0
    for abbr in abbrs:
        if abbr in existing:
            continue
        team = Team(
            league="NFL",
            abbreviation=abbr,
            name=nfl_team_name(abbr),
            source="nflverse",
            source_id=abbr,
        )
        session.add(team)
        session.flush()
        session.add(TeamExternalId(team_id=team.team_id, system="nflverse", external_id=abbr))
        existing.add(abbr)
        created += 1
    return created


def seed_players_from_plays(session: Session) -> int:
    q = text(
        """
        SELECT passer_player_id AS pid, passer_player_name AS pname FROM plays
        WHERE passer_player_id IS NOT NULL
        UNION
        SELECT rusher_player_id, rusher_player_name FROM plays
        WHERE rusher_player_id IS NOT NULL
        """
    )
    existing = set(
        session.scalars(select(PlayerExternalId.external_id).where(PlayerExternalId.system == "gsis"))
    )
    created = 0
    for pid, pname in session.execute(q):
        gsis = str(pid)
        if gsis in existing:
            continue
        name = str(pname or gsis)
        player = Player(
            league="NFL",
            canonical_name=name,
            source="nflverse",
            source_id=gsis,
        )
        session.add(player)
        session.flush()
        session.add(PlayerExternalId(player_id=player.player_id, system="gsis", external_id=gsis))
        existing.add(gsis)
        created += 1
    return created


def tag_games_and_plays(session: Session) -> None:
    now = _now()
    session.execute(
        update(Game).values(
            league="NFL",
            source="nflverse",
            source_id=Game.game_id,
            retrieved_at=now,
            occurred_at=Game.kickoff,
        )
    )
    session.execute(update(Play).values(league="NFL", source="nflverse"))


def seed_market_zero(session: Session) -> int:
    """Copy games.spread_line / total_line into tagged historical_close snapshots."""
    now = _now()
    games = session.execute(
        select(
            Game.game_id,
            Game.spread_line,
            Game.total_line,
            Game.kickoff,
            Game.game_date,
            Game.league,
            Game.home_moneyline,
            Game.away_moneyline,
            Game.spread_home_odds,
        )
    ).all()
    rows: list[dict[str, Any]] = []
    for (
        game_id,
        spread,
        total,
        kickoff,
        game_date,
        league,
        home_ml,
        away_ml,
        spread_home_odds,
    ) in games:
        known = kickoff
        if known is None and game_date is not None:
            known = datetime(game_date.year, game_date.month, game_date.day, tzinfo=timezone.utc)
        captured = known or now
        if spread is not None:
            rows.append(
                {
                    "league": league or "NFL",
                    "game_id": game_id,
                    "bookmaker": "nflverse_pfr",
                    "market_source": "nflverse_pfr",
                    "market_type": "historical_close",
                    "market": "spread",
                    "side": "home",
                    "point": float(spread),
                    "price_american": int(spread_home_odds) if spread_home_odds is not None else None,
                    "captured_at": captured,
                    "known_at": known,
                    "retrieved_at": now,
                    "source": "nflverse",
                    "is_closing": True,
                }
            )
        if total is not None:
            rows.append(
                {
                    "league": league or "NFL",
                    "game_id": game_id,
                    "bookmaker": "nflverse_pfr",
                    "market_source": "nflverse_pfr",
                    "market_type": "historical_close",
                    "market": "total",
                    "side": "over",
                    "point": float(total),
                    "price_american": None,
                    "captured_at": captured,
                    "known_at": known,
                    "retrieved_at": now,
                    "source": "nflverse",
                    "is_closing": True,
                }
            )
        if home_ml is not None:
            rows.append(
                {
                    "league": league or "NFL",
                    "game_id": game_id,
                    "bookmaker": "nflverse_pfr",
                    "market_source": "nflverse_pfr",
                    "market_type": "historical_close",
                    "market": "h2h",
                    "side": "home",
                    "point": None,
                    "price_american": int(home_ml),
                    "captured_at": captured,
                    "known_at": known,
                    "retrieved_at": now,
                    "source": "nflverse",
                    "is_closing": True,
                }
            )
        if away_ml is not None:
            rows.append(
                {
                    "league": league or "NFL",
                    "game_id": game_id,
                    "bookmaker": "nflverse_pfr",
                    "market_source": "nflverse_pfr",
                    "market_type": "historical_close",
                    "market": "h2h",
                    "side": "away",
                    "point": None,
                    "price_american": int(away_ml),
                    "captured_at": captured,
                    "known_at": known,
                    "retrieved_at": now,
                    "source": "nflverse",
                    "is_closing": True,
                }
            )
    if not rows:
        return 0
    update_cols = [
        "point",
        "price_american",
        "captured_at",
        "known_at",
        "retrieved_at",
        "is_closing",
        "bookmaker",
        "league",
        "source",
    ]
    n_cols = len(rows[0])
    batch_size = max(1, 900 // n_cols)
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        stmt = sqlite_insert(OddsSnapshot).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=["game_id", "market_source", "market_type", "market", "side"],
            set_={col: getattr(stmt.excluded, col) for col in update_cols},
        )
        session.execute(stmt)
    return len(rows)


def backfill_contract(session: Session) -> dict[str, int]:
    ensure_leagues(session)
    tag_games_and_plays(session)
    n_teams = seed_teams_from_games(session)
    n_players = seed_players_from_plays(session)
    n_markets = seed_market_zero(session)
    session.commit()
    logger.info(
        "Data contract backfill teams_new=%s players_new=%s market_rows=%s",
        n_teams,
        n_players,
        n_markets,
    )
    return {"teams_new": n_teams, "players_new": n_players, "market_rows": n_markets}
