"""nflverse schedules: kickoff, rest, historical prices, external ids.

PBP remains canonical for final scores. Conflicts are flagged, not clobbered.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import httpx
import pandas as pd
import truststore
from sqlalchemy import delete, select, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.ingest.game_fields import SCHEDULE_OWNED_GAME_COLS
from app.ingest.nflfastr import _as_bool, _as_date, _batch_size, _to_python
from db.models import Game, GameExternalId, IngestConflict

truststore.inject_into_ssl()

logger = logging.getLogger(__name__)

ET = ZoneInfo("America/New_York")

SCHEDULE_COLUMNS = [
    "game_id",
    "season",
    "game_type",
    "week",
    "gameday",
    "weekday",
    "gametime",
    "away_team",
    "away_score",
    "home_team",
    "home_score",
    "location",
    "result",
    "total",
    "overtime",
    "gsis",
    "pfr",
    "espn",
    "away_rest",
    "home_rest",
    "away_moneyline",
    "home_moneyline",
    "spread_line",
    "away_spread_odds",
    "home_spread_odds",
    "total_line",
    "under_odds",
    "over_odds",
    "div_game",
    "roof",
    "surface",
    "temp",
    "wind",
    "stadium",
]

SKIP_GAME_TYPES = {"PRE"}


def season_type_from_game_type(game_type: str | None) -> str:
    raw = (game_type or "REG").upper()
    if raw == "PRE":
        return "PRE"
    if raw == "REG":
        return "REG"
    return "POST"


def parse_kickoff(gameday: Any, gametime: Any) -> datetime | None:
    d = _as_date(gameday)
    if d is None:
        return None
    t = _to_python(gametime)
    if t is None:
        return None
    hour, minute = 0, 0
    if hasattr(t, "hour"):
        hour, minute = int(t.hour), int(t.minute)
    elif isinstance(t, str) and t.strip():
        parts = t.strip().split(":")
        try:
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
        except ValueError:
            return None
    else:
        return None
    return datetime(d.year, d.month, d.day, hour, minute, tzinfo=ET)


def _as_int(value: Any) -> int | None:
    value = _to_python(value)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> float | None:
    value = _to_python(value)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_str(value: Any) -> str | None:
    value = _to_python(value)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def schedules_parquet_path(settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    settings.raw_data_dir.mkdir(parents=True, exist_ok=True)
    return settings.raw_data_dir / "schedules.parquet"


def download_schedules_parquet(*, force: bool = False, settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    dest = schedules_parquet_path(settings)
    if dest.exists() and not force:
        logger.info("Using cached parquet %s", dest)
        return dest
    url = settings.nflverse_schedules_url
    logger.info("Downloading %s → %s", url, dest)
    with httpx.stream("GET", url, follow_redirects=True, timeout=180.0) as response:
        response.raise_for_status()
        with dest.open("wb") as fh:
            for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                fh.write(chunk)
    logger.info("Saved %s (%.1f MB)", dest, dest.stat().st_size / 1e6)
    return dest


def load_schedules_frame(
    *,
    from_season: int,
    to_season: int,
    force_download: bool = False,
) -> pd.DataFrame:
    path = download_schedules_parquet(force=force_download)
    df = pd.read_parquet(path)
    available = [c for c in SCHEDULE_COLUMNS if c in df.columns]
    missing = sorted(set(SCHEDULE_COLUMNS) - set(available))
    if missing:
        logger.warning("schedules parquet missing columns: %s", missing)
    df = df[available].copy()
    if "season" in df.columns:
        df = df[(df["season"] >= from_season) & (df["season"] <= to_season)]
    return df


def _flag(
    conflicts: list[dict[str, Any]],
    game_id: str,
    field: str,
    existing: Any,
    incoming: Any,
) -> None:
    conflicts.append(
        {
            "game_id": game_id,
            "field": field,
            "existing_value": None if existing is None else str(existing),
            "incoming_value": None if incoming is None else str(incoming),
            "kept": "existing",
            "source_existing": "nflverse_pbp",
            "source_incoming": "nflverse_schedules",
        }
    )


def _scores_conflict(existing: int | None, incoming: int | None) -> bool:
    return existing is not None and incoming is not None and int(existing) != int(incoming)


def row_from_schedule(record: dict[str, Any]) -> dict[str, Any] | None:
    game_id = _as_str(record.get("game_id"))
    home = _as_str(record.get("home_team"))
    away = _as_str(record.get("away_team"))
    season = _as_int(record.get("season"))
    week = _as_int(record.get("week"))
    if not game_id or not home or not away or season is None or week is None:
        return None
    if home == away:
        return None
    game_type = (_as_str(record.get("game_type")) or "REG").upper()
    kickoff = parse_kickoff(record.get("gameday"), record.get("gametime"))
    location = _as_str(record.get("location"))
    gametime = _as_str(record.get("gametime"))
    if gametime and len(gametime) > 16:
        gametime = gametime[:16]
    return {
        "game_id": game_id,
        "league": "NFL",
        "season": season,
        "week": week,
        "season_type": season_type_from_game_type(game_type),
        "game_type": game_type[:8],
        "game_date": _as_date(record.get("gameday")),
        "kickoff": kickoff,
        "occurred_at": kickoff,
        "home_team": home,
        "away_team": away,
        "home_score": _as_int(record.get("home_score")),
        "away_score": _as_int(record.get("away_score")),
        "result": _as_int(record.get("result")),
        "total": _as_int(record.get("total")),
        "spread_line": _as_float(record.get("spread_line")),
        "total_line": _as_float(record.get("total_line")),
        "roof": _as_str(record.get("roof")),
        "surface": _as_str(record.get("surface")),
        "temp": _as_float(record.get("temp")),
        "wind": _as_float(record.get("wind")),
        "weekday": _as_str(record.get("weekday")),
        "gametime": gametime,
        "location": location,
        "stadium_name": _as_str(record.get("stadium")),
        "home_rest": _as_int(record.get("home_rest")),
        "away_rest": _as_int(record.get("away_rest")),
        "home_moneyline": _as_int(record.get("home_moneyline")),
        "away_moneyline": _as_int(record.get("away_moneyline")),
        "spread_home_odds": _as_int(record.get("home_spread_odds")),
        "spread_away_odds": _as_int(record.get("away_spread_odds")),
        "over_odds": _as_int(record.get("over_odds")),
        "under_odds": _as_int(record.get("under_odds")),
        "overtime": _as_bool(record.get("overtime")),
        "div_game": _as_bool(record.get("div_game")),
        "neutral_site": True if location and location.lower() == "neutral" else False,
        "source": "nflverse",
        "source_id": game_id,
        "retrieved_at": datetime.now(timezone.utc),
        "_espn": _as_str(record.get("espn")),
        "_pfr": _as_str(record.get("pfr")),
        "_gsis": _as_str(record.get("gsis")),
    }


def apply_schedule_frame(session: Session, df: pd.DataFrame) -> dict[str, int]:
    """Merge schedule rows into games. Scores from PBP win on conflict."""
    if df.empty:
        return {"updated": 0, "inserted": 0, "conflicts": 0, "skipped_pre": 0}

    session.execute(delete(IngestConflict).where(IngestConflict.source_incoming == "nflverse_schedules"))

    existing = {
        row.game_id: row
        for row in session.execute(
            select(
                Game.game_id,
                Game.home_score,
                Game.away_score,
                Game.spread_line,
                Game.total_line,
                Game.result,
                Game.total,
            )
        ).all()
    }

    updates: list[dict[str, Any]] = []
    inserts: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    ext_rows: list[dict[str, Any]] = []
    skipped_pre = 0

    for record in df.to_dict(orient="records"):
        row = row_from_schedule(record)
        if row is None:
            continue
        game_type = row["game_type"]
        if game_type in SKIP_GAME_TYPES:
            skipped_pre += 1
            continue

        espn, pfr, gsis = row.pop("_espn"), row.pop("_pfr"), row.pop("_gsis")
        game_id = row["game_id"]
        ext_rows.append({"game_id": game_id, "system": "nflverse", "external_id": game_id})
        if espn:
            ext_rows.append({"game_id": game_id, "system": "espn", "external_id": espn})
        if pfr:
            ext_rows.append({"game_id": game_id, "system": "pfr", "external_id": pfr})
        if gsis:
            ext_rows.append({"game_id": game_id, "system": "gsis", "external_id": gsis})

        prior = existing.get(game_id)
        if prior is None:
            inserts.append(row)
            continue

        if _scores_conflict(prior.home_score, row["home_score"]):
            _flag(conflicts, game_id, "home_score", prior.home_score, row["home_score"])
            row["home_score"] = prior.home_score
        elif prior.home_score is not None:
            row["home_score"] = prior.home_score

        if _scores_conflict(prior.away_score, row["away_score"]):
            _flag(conflicts, game_id, "away_score", prior.away_score, row["away_score"])
            row["away_score"] = prior.away_score
        elif prior.away_score is not None:
            row["away_score"] = prior.away_score

        if prior.result is not None:
            row["result"] = prior.result
        if prior.total is not None:
            row["total"] = prior.total

        if (
            prior.spread_line is not None
            and row["spread_line"] is not None
            and abs(float(prior.spread_line) - float(row["spread_line"])) > 0.05
        ):
            _flag(conflicts, game_id, "spread_line", prior.spread_line, row["spread_line"])
            row["spread_line"] = prior.spread_line
        elif prior.spread_line is not None:
            row["spread_line"] = prior.spread_line

        if (
            prior.total_line is not None
            and row["total_line"] is not None
            and abs(float(prior.total_line) - float(row["total_line"])) > 0.05
        ):
            _flag(conflicts, game_id, "total_line", prior.total_line, row["total_line"])
            row["total_line"] = prior.total_line
        elif prior.total_line is not None:
            row["total_line"] = prior.total_line

        updates.append(row)

    if inserts:
        n_cols = len(inserts[0])
        batch_size = _batch_size(n_cols)
        for i in range(0, len(inserts), batch_size):
            stmt = sqlite_insert(Game).values(inserts[i : i + batch_size])
            stmt = stmt.on_conflict_do_nothing(index_elements=["game_id"])
            session.execute(stmt)

    if updates:
        session.execute(update(Game), updates)

    if ext_rows:
        n_cols = len(ext_rows[0])
        batch_size = _batch_size(n_cols)
        for i in range(0, len(ext_rows), batch_size):
            stmt = sqlite_insert(GameExternalId).values(ext_rows[i : i + batch_size])
            stmt = stmt.on_conflict_do_nothing()
            session.execute(stmt)

    if conflicts:
        session.execute(sqlite_insert(IngestConflict).values(conflicts))

    session.flush()
    logger.info(
        "Schedules merged updated=%s inserted=%s conflicts=%s skipped_pre=%s",
        len(updates),
        len(inserts),
        len(conflicts),
        skipped_pre,
    )
    return {
        "updated": len(updates),
        "inserted": len(inserts),
        "conflicts": len(conflicts),
        "skipped_pre": skipped_pre,
    }


def ingest_schedules(
    session: Session,
    *,
    from_season: int,
    to_season: int,
    force_download: bool = False,
) -> dict[str, int]:
    logger.info("Ingesting nflverse schedules %s–%s", from_season, to_season)
    df = load_schedules_frame(
        from_season=from_season,
        to_season=to_season,
        force_download=force_download,
    )
    stats = apply_schedule_frame(session, df)
    session.commit()
    from sqlalchemy import func

    stats["games_with_kickoff"] = int(
        session.scalar(select(func.count()).select_from(Game).where(Game.kickoff.is_not(None))) or 0
    )
    stats["games_with_rest"] = int(
        session.scalar(select(func.count()).select_from(Game).where(Game.home_rest.is_not(None))) or 0
    )
    return stats
