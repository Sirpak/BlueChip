"""nflfastR / nflverse play-by-play ingestion."""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
import truststore
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.ingest.game_fields import SCHEDULE_OWNED_GAME_COLS
from app.config import Settings, get_settings
from app.ingest.identity import canonicalize_nfl_team
from db.models import Game, Play

# Windows / corporate roots: use OS certificate store for TLS.
truststore.inject_into_ssl()

logger = logging.getLogger(__name__)

# Curated columns we persist from nflverse parquet
PBP_COLUMNS: list[str] = [
    "play_id",
    "game_id",
    "season",
    "week",
    "season_type",
    "game_date",
    "home_team",
    "away_team",
    "posteam",
    "defteam",
    "posteam_type",
    "play_type",
    "down",
    "ydstogo",
    "yardline_100",
    "qtr",
    "quarter_seconds_remaining",
    "half_seconds_remaining",
    "game_seconds_remaining",
    "yards_gained",
    "air_yards",
    "yards_after_catch",
    "epa",
    "ep",
    "wp",
    "wpa",
    "success",
    "pass_attempt",
    "rush_attempt",
    "complete_pass",
    "incomplete_pass",
    "interception",
    "touchdown",
    "first_down",
    "shotgun",
    "no_huddle",
    "special_teams_play",
    "score_differential",
    "home_score",
    "away_score",
    "passer_player_id",
    "passer_player_name",
    "rusher_player_id",
    "rusher_player_name",
    "desc",
    # game-level fields present on each play row
    "roof",
    "surface",
    "temp",
    "wind",
    "result",
    "total",
    "spread_line",
    "total_line",
]

BOOL_COLUMNS = {
    "success",
    "pass_attempt",
    "rush_attempt",
    "complete_pass",
    "incomplete_pass",
    "interception",
    "touchdown",
    "first_down",
    "shotgun",
    "no_huddle",
    "special_teams_play",
}

# SQLite default SQLITE_MAX_VARIABLE_NUMBER is 999.
# Batch size = floor(999 / n_columns) with a small safety margin.
def _batch_size(n_columns: int) -> int:
    return max(1, 900 // max(n_columns, 1))


def _to_python(value: Any) -> Any:
    """Convert pandas / numpy scalars to plain Python (None for NA)."""
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        try:
            value = value.item()
        except (ValueError, AttributeError):
            pass
    if isinstance(value, float) and pd.isna(value):
        return None
    return value


def _as_bool(value: Any) -> bool | None:
    value = _to_python(value)
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(int(value))
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "t", "yes"}:
            return True
        if lowered in {"0", "false", "f", "no", ""}:
            return False
    return bool(value)


def _as_date(value: Any) -> date | None:
    value = _to_python(value)
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    # pandas Timestamp
    if hasattr(value, "date"):
        return value.date()
    return None


def parquet_path_for_season(season: int, settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    settings.raw_data_dir.mkdir(parents=True, exist_ok=True)
    return settings.raw_data_dir / f"play_by_play_{season}.parquet"


def download_pbp_parquet(
    season: int,
    *,
    force: bool = False,
    settings: Settings | None = None,
) -> Path:
    """Download nflverse PBP parquet to data/raw/ (cached unless force)."""
    settings = settings or get_settings()
    dest = parquet_path_for_season(season, settings)
    if dest.exists() and not force:
        logger.info("Using cached parquet %s", dest)
        return dest

    url = settings.nflverse_pbp_url.format(season=season)
    logger.info("Downloading %s → %s", url, dest)
    with httpx.stream(
        "GET",
        url,
        follow_redirects=True,
        timeout=180.0,
    ) as response:
        response.raise_for_status()
        with dest.open("wb") as fh:
            for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                fh.write(chunk)
    logger.info("Saved %s (%.1f MB)", dest, dest.stat().st_size / 1e6)
    return dest


def load_pbp_frame(season: int, *, force_download: bool = False) -> pd.DataFrame:
    path = download_pbp_parquet(season, force=force_download)
    df = pd.read_parquet(path)
    available = [c for c in PBP_COLUMNS if c in df.columns]
    missing = sorted(set(PBP_COLUMNS) - set(available))
    if missing:
        logger.warning("Season %s parquet missing columns: %s", season, missing)
    return df[available].copy()


def _games_from_pbp(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Collapse play rows into one game dict per game_id."""
    if df.empty:
        return []

    # Last non-null scores / lines within each game (plays are chronological)
    group_cols = ["game_id"]
    agg: dict[str, Any] = {
        "season": "first",
        "week": "first",
        "season_type": "first",
        "game_date": "first",
        "home_team": "first",
        "away_team": "first",
        "roof": "last",
        "surface": "last",
        "temp": "last",
        "wind": "last",
        "home_score": "last",
        "away_score": "last",
        "result": "last",
        "total": "last",
        "spread_line": "last",
        "total_line": "last",
    }
    # Only aggregate columns that exist
    agg = {k: v for k, v in agg.items() if k in df.columns}
    games_df = df.groupby(group_cols, sort=False).agg(agg).reset_index()

    rows: list[dict[str, Any]] = []
    for record in games_df.to_dict(orient="records"):
        home_score = _to_python(record.get("home_score"))
        away_score = _to_python(record.get("away_score"))
        result = _to_python(record.get("result"))
        total = _to_python(record.get("total"))
        if result is None and home_score is not None and away_score is not None:
            result = int(home_score) - int(away_score)
        if total is None and home_score is not None and away_score is not None:
            total = int(home_score) + int(away_score)

        rows.append(
            {
                "game_id": str(record["game_id"]),
                "league": "NFL",
                "season": int(record["season"]),
                "week": int(record["week"]),
                "season_type": str(record.get("season_type") or "REG"),
                "game_date": _as_date(record.get("game_date")),
                "kickoff": None,
                "home_team": canonicalize_nfl_team(str(record["home_team"])) or str(record["home_team"]),
                "away_team": canonicalize_nfl_team(str(record["away_team"])) or str(record["away_team"]),
                "home_score": int(home_score) if home_score is not None else None,
                "away_score": int(away_score) if away_score is not None else None,
                "roof": _to_python(record.get("roof")),
                "surface": _to_python(record.get("surface")),
                "temp": _to_python(record.get("temp")),
                "wind": _to_python(record.get("wind")),
                "result": int(result) if result is not None else None,
                "total": int(total) if total is not None else None,
                "spread_line": _to_python(record.get("spread_line")),
                "total_line": _to_python(record.get("total_line")),
                "source": "nflverse",
                "source_id": str(record["game_id"]),
                "retrieved_at": datetime.now(timezone.utc),
                "occurred_at": None,
            }
        )
    return rows


def _plays_from_pbp(df: pd.DataFrame) -> list[dict[str, Any]]:
    play_fields = [
        c
        for c in PBP_COLUMNS
        if c
        not in {
            "roof",
            "surface",
            "temp",
            "wind",
            "result",
            "total",
            "spread_line",
            "total_line",
        }
    ]
    rows: list[dict[str, Any]] = []
    for record in df.to_dict(orient="records"):
        row: dict[str, Any] = {}
        for col in play_fields:
            if col not in record:
                continue
            raw = record[col]
            if col in BOOL_COLUMNS:
                row[col] = _as_bool(raw)
            elif col == "game_date":
                row[col] = _as_date(raw)
            elif col in {"play_id", "game_id"}:
                val = _to_python(raw)
                row[col] = str(val) if val is not None else None
            elif col in {
                "passer_player_id",
                "passer_player_name",
                "rusher_player_id",
                "rusher_player_name",
                "desc",
                "posteam",
                "defteam",
                "posteam_type",
                "play_type",
                "season_type",
                "home_team",
                "away_team",
            }:
                val = _to_python(raw)
                if val is None:
                    row[col] = None
                elif col in {"posteam", "defteam", "home_team", "away_team"}:
                    row[col] = canonicalize_nfl_team(str(val)) or str(val)
                else:
                    row[col] = str(val)
            else:
                row[col] = _to_python(raw)

        if not row.get("game_id") or row.get("play_id") is None:
            continue
        row["league"] = "NFL"
        row["source"] = "nflverse"
        rows.append(row)
    return rows


def _upsert_games(session: Session, games: list[dict[str, Any]]) -> int:
    if not games:
        return 0
    update_cols = [
        c.name
        for c in Game.__table__.columns
        if c.name not in {"game_id", "created_at"} | SCHEDULE_OWNED_GAME_COLS
    ]
    n_cols = len(games[0])
    batch_size = _batch_size(n_cols)
    for i in range(0, len(games), batch_size):
        batch = games[i : i + batch_size]
        stmt = sqlite_insert(Game).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=["game_id"],
            set_={col: getattr(stmt.excluded, col) for col in update_cols},
        )
        session.execute(stmt)
    return len(games)


def _upsert_plays(session: Session, plays: list[dict[str, Any]]) -> int:
    if not plays:
        return 0
    update_cols = [
        c.name
        for c in Play.__table__.columns
        if c.name not in {"id", "game_id", "play_id", "created_at"}
    ]
    n_cols = len(plays[0])
    batch_size = _batch_size(n_cols)
    for i in range(0, len(plays), batch_size):
        batch = plays[i : i + batch_size]
        stmt = sqlite_insert(Play).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=["game_id", "play_id"],
            set_={col: getattr(stmt.excluded, col) for col in update_cols},
        )
        session.execute(stmt)
    return len(plays)


def ingest_season(
    session: Session,
    season: int,
    *,
    force_download: bool = False,
) -> dict[str, int]:
    """Download (if needed), normalize, and upsert one season of PBP into DB."""
    logger.info("Ingesting nflfastR season %s", season)
    df = load_pbp_frame(season, force_download=force_download)
    # Drop rows without game_id / play_id (kickoffs sometimes odd, but keep most)
    df = df.dropna(subset=["game_id", "play_id"])

    games = _games_from_pbp(df)
    plays = _plays_from_pbp(df)

    n_games = _upsert_games(session, games)
    n_plays = _upsert_plays(session, plays)
    session.commit()

    from sqlalchemy import func

    db_games = session.scalar(
        select(func.count()).select_from(Game).where(Game.season == season)
    )
    db_plays = session.scalar(
        select(func.count()).select_from(Play).where(Play.season == season)
    )

    logger.info(
        "Season %s upserted games=%s plays=%s | db now games=%s plays=%s",
        season,
        n_games,
        n_plays,
        db_games,
        db_plays,
    )
    return {
        "season": season,
        "games_upserted": n_games,
        "plays_upserted": n_plays,
        "games_in_db": int(db_games or 0),
        "plays_in_db": int(db_plays or 0),
    }
