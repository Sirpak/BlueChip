"""Assemble BCW-SNAP-v0.1 rows. Rolling stats stop at the previous game."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

import pandas as pd
from sqlalchemy import delete
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from ml.features.constants import EWMA_ALPHA, FEATURE_VERSION, era_label
from ml.features.ratings import walk_ratings
from ml.features.team_games import aggregate_team_games
from app.ingest.identity import canonicalize_nfl_columns
from db.models import FeatureSnapshot

logger = logging.getLogger(__name__)

ROLL_COLS = [
    "off_epa",
    "def_epa",
    "pass_epa",
    "rush_epa",
    "pass_epa_allowed",
    "rush_epa_allowed",
    "success_off",
    "success_def",
    "explosive_off",
    "explosive_allowed",
    "early_down_epa",
    "int_rate",
]


def _sort_ts(df: pd.DataFrame) -> pd.Series:
    kick = pd.to_datetime(df["kickoff"], utc=True, errors="coerce")
    gdate = pd.to_datetime(df["game_date"], utc=True, errors="coerce") + pd.Timedelta(hours=17)
    return kick.fillna(gdate)


def add_prior_rolling(tg: pd.DataFrame, alpha: float = EWMA_ALPHA) -> pd.DataFrame:
    tg = tg.sort_values(["team", "sort_ts"], kind="mergesort").copy()
    tg["n_prior"] = tg.groupby("team", sort=False).cumcount()
    for col in ROLL_COLS:
        if col not in tg.columns:
            continue
        grp = tg.groupby("team", sort=False)[col]
        tg[f"{col}_ewma"] = grp.transform(lambda s: s.shift(1).ewm(alpha=alpha, adjust=False).mean())
        tg[f"{col}_last3"] = grp.transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
        tg[f"{col}_last5"] = grp.transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())
        tg[f"{col}_std"] = grp.transform(lambda s: s.shift(1).rolling(8, min_periods=3).std())
        seas = tg.groupby(["team", "season"], sort=False)[col]
        tg[f"{col}_s2d"] = seas.transform(lambda s: s.shift(1).expanding(min_periods=1).mean())
    return tg


def _side_frame(tg: pd.DataFrame, home: bool, prefix: str) -> pd.DataFrame:
    part = tg.loc[tg["is_home"] == home]
    data: dict[str, object] = {"game_id": part["game_id"].to_numpy()}
    for col in ROLL_COLS:
        ewma = f"{col}_ewma"
        if ewma in part.columns:
            data[f"{prefix}_{col}"] = part[ewma].to_numpy()
        for suffix in ("last3", "last5", "s2d", "std"):
            src = f"{col}_{suffix}"
            if src in part.columns:
                data[f"{prefix}_{src}"] = part[src].to_numpy()
    if "n_prior" in part.columns:
        data[f"{prefix}_n_prior"] = part["n_prior"].to_numpy()
    out = pd.DataFrame(data)
    return out.drop_duplicates("game_id", keep="first")


def load_games_frame(session: Session) -> pd.DataFrame:
    games = pd.read_sql(
        """
        SELECT game_id, season, week, season_type, game_date, kickoff,
               home_team, away_team, home_score, away_score, result,
               spread_line, home_rest, away_rest
        FROM games
        WHERE league = 'NFL'
        """,
        session.get_bind(),
        parse_dates=["kickoff", "game_date"],
    )
    games["sort_ts"] = _sort_ts(games)
    games["home_margin"] = games["result"]
    missing = games["home_margin"].isna()
    games.loc[missing, "home_margin"] = (
        games.loc[missing, "home_score"] - games.loc[missing, "away_score"]
    )
    games["home_win"] = (games["home_margin"] > 0).astype(float)
    games.loc[games["home_margin"].isna(), "home_win"] = pd.NA
    return canonicalize_nfl_columns(games, ["home_team", "away_team"])


def attach_schedule_to_team_games(tg: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    meta = games[
        ["game_id", "home_team", "away_team", "sort_ts", "season", "week", "season_type"]
    ]
    out = tg.merge(meta, on="game_id", how="inner")
    out = canonicalize_nfl_columns(out, ["team", "home_team", "away_team"])
    out["is_home"] = out["team"] == out["home_team"]
    out["opponent"] = out["away_team"].where(out["is_home"], out["home_team"])
    return out


def build_snapshot_frame(session: Session) -> pd.DataFrame:
    games = load_games_frame(session)
    tg = aggregate_team_games(session)
    if tg.empty:
        raise RuntimeError("No team-game EPA rows; ingest PBP first.")
    tg = attach_schedule_to_team_games(tg, games)
    tg = add_prior_rolling(tg)
    home = _side_frame(tg, True, "home")
    away = _side_frame(tg, False, "away")
    ratings = walk_ratings(games, tg)
    snap = games.merge(home, on="game_id", how="left").merge(away, on="game_id", how="left")
    snap = snap.merge(ratings, on="game_id", how="left")
    snap["success_rate_diff"] = snap["home_success_off"] - snap["away_success_off"]
    snap["explosive_play_diff"] = snap["home_explosive_off"] - snap["away_explosive_off"]
    snap["rest_diff"] = snap["home_rest"] - snap["away_rest"]
    snap["era"] = snap["season"].map(lambda s: era_label(int(s)))
    snap["feature_version"] = FEATURE_VERSION
    return snap


def _i(val: object) -> int | None:
    f = _f(val)
    return None if f is None else int(f)


def _f(val: object) -> float | None:
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    return float(val)


def snapshots_to_rows(snap: pd.DataFrame) -> list[dict]:
    now = datetime.now(timezone.utc)
    rows = []
    for rec in snap.to_dict(orient="records"):
        kickoff = rec.get("kickoff")
        if kickoff is not None and pd.notna(kickoff):
            kickoff = pd.Timestamp(kickoff).to_pydatetime()
            if kickoff.tzinfo is None:
                kickoff = kickoff.replace(tzinfo=timezone.utc)
            known_max = kickoff - timedelta(seconds=1)
        else:
            kickoff = None
            known_max = None
        extras = {
            k: _f(v)
            for k, v in rec.items()
            if isinstance(k, str)
            and k.endswith(("_last3", "_last5", "_s2d", "_std", "_n_prior"))
        }
        rows.append(
            {
                "game_id": rec["game_id"],
                "feature_version": FEATURE_VERSION,
                "prediction_at": kickoff,
                "known_at_max": known_max,
                "era": rec["era"],
                "season": int(rec["season"]),
                "week": int(rec["week"]),
                "home_team": rec["home_team"],
                "away_team": rec["away_team"],
                "home_rest": _i(rec.get("home_rest")),
                "away_rest": _i(rec.get("away_rest")),
                "rest_diff": _f(rec.get("rest_diff")),
                "elo_home": _f(rec.get("elo_home")),
                "elo_away": _f(rec.get("elo_away")),
                "elo_diff": _f(rec.get("elo_diff")),
                "elo_win_home": _f(rec.get("elo_win_home")),
                "srs_home": _f(rec.get("srs_home")),
                "srs_away": _f(rec.get("srs_away")),
                "srs_diff": _f(rec.get("srs_diff")),
                "srs_pred_margin": _f(rec.get("srs_pred_margin")),
                "hfa_prior": _f(rec.get("hfa_prior")),
                "adj_off_home": _f(rec.get("adj_off_home")),
                "adj_def_home": _f(rec.get("adj_def_home")),
                "adj_off_away": _f(rec.get("adj_off_away")),
                "adj_def_away": _f(rec.get("adj_def_away")),
                "adj_pred_margin": _f(rec.get("adj_pred_margin")),
                "home_off_epa": _f(rec.get("home_off_epa")),
                "away_off_epa": _f(rec.get("away_off_epa")),
                "home_def_epa": _f(rec.get("home_def_epa")),
                "away_def_epa": _f(rec.get("away_def_epa")),
                "home_pass_epa": _f(rec.get("home_pass_epa")),
                "away_pass_epa": _f(rec.get("away_pass_epa")),
                "home_rush_epa": _f(rec.get("home_rush_epa")),
                "away_rush_epa": _f(rec.get("away_rush_epa")),
                "home_pass_epa_allowed": _f(rec.get("home_pass_epa_allowed")),
                "away_pass_epa_allowed": _f(rec.get("away_pass_epa_allowed")),
                "home_rush_epa_allowed": _f(rec.get("home_rush_epa_allowed")),
                "away_rush_epa_allowed": _f(rec.get("away_rush_epa_allowed")),
                "success_rate_diff": _f(rec.get("success_rate_diff")),
                "explosive_play_diff": _f(rec.get("explosive_play_diff")),
                "home_margin": _f(rec.get("home_margin")),
                "home_win": _f(rec.get("home_win")),
                "market_spread": _f(rec.get("spread_line")),
                "extras_json": json.dumps(extras, separators=(",", ":")),
                "retrieved_at": now,
            }
        )
    return rows


def persist_snapshots(session: Session, rows: list[dict]) -> int:
    session.execute(delete(FeatureSnapshot).where(FeatureSnapshot.feature_version == FEATURE_VERSION))
    if not rows:
        session.commit()
        return 0
    n_cols = len(rows[0])
    batch = max(1, 900 // n_cols)
    for i in range(0, len(rows), batch):
        stmt = sqlite_insert(FeatureSnapshot).values(rows[i : i + batch])
        session.execute(stmt)
    session.commit()
    return len(rows)


def build_and_persist(session: Session) -> dict[str, int]:
    logger.info("Building %s snapshots", FEATURE_VERSION)
    snap = build_snapshot_frame(session)
    rows = snapshots_to_rows(snap)
    n = persist_snapshots(session, rows)
    logger.info("Wrote %s feature snapshots", n)
    return {"snapshots": n, "games": int(len(snap))}
