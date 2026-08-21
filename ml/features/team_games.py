"""Post-game team-game efficiency. Used only for *later* games' snapshots."""

from __future__ import annotations

import logging

import pandas as pd
from sqlalchemy.orm import Session

from ml.features.constants import EXPLOSIVE_PASS_YARDS, EXPLOSIVE_RUSH_YARDS
from app.ingest.identity import canonicalize_nfl_columns

logger = logging.getLogger(__name__)

PLAY_SQL = """
SELECT
    p.game_id,
    p.posteam,
    p.defteam,
    p.epa,
    p.success,
    p.pass_attempt,
    p.rush_attempt,
    p.yards_gained,
    p.down,
    p.interception,
    p.play_type
FROM plays p
WHERE p.posteam IS NOT NULL AND TRIM(p.posteam) != ''
"""


def _as_bool_s(s: pd.Series) -> pd.Series:
    return s.fillna(False).astype(bool)


def aggregate_team_games(session: Session) -> pd.DataFrame:
    """One row per (game_id, team) of *observed* EPA. Includes the current game."""
    logger.info("Aggregating team-game EPA from plays")
    plays = pd.read_sql(PLAY_SQL, session.get_bind())
    if plays.empty:
        return pd.DataFrame()
    plays = canonicalize_nfl_columns(plays, ["posteam", "defteam"])

    off_mask = _as_bool_s(plays["pass_attempt"]) | _as_bool_s(plays["rush_attempt"])
    off = plays.loc[off_mask].copy()
    off["is_pass"] = _as_bool_s(off["pass_attempt"])
    off["is_rush"] = _as_bool_s(off["rush_attempt"])
    off["success_f"] = _as_bool_s(off["success"]).astype(float)
    off["explosive"] = (
        (off["is_pass"] & (off["yards_gained"].fillna(0) >= EXPLOSIVE_PASS_YARDS))
        | (off["is_rush"] & (off["yards_gained"].fillna(0) >= EXPLOSIVE_RUSH_YARDS))
    ).astype(float)
    off["early"] = off["down"].isin([1, 2])
    off["int_f"] = _as_bool_s(off["interception"]).astype(float)

    pass_epa = (
        off.loc[off["is_pass"]].groupby(["game_id", "posteam"], sort=False)["epa"].mean().rename("pass_epa")
    )
    rush_epa = (
        off.loc[off["is_rush"]].groupby(["game_id", "posteam"], sort=False)["epa"].mean().rename("rush_epa")
    )
    early_epa = (
        off.loc[off["early"]].groupby(["game_id", "posteam"], sort=False)["epa"].mean().rename("early_down_epa")
    )
    off_basic = (
        off.groupby(["game_id", "posteam"], sort=False)
        .agg(
            off_epa=("epa", "mean"),
            n_plays=("epa", "size"),
            success_off=("success_f", "mean"),
            explosive_off=("explosive", "mean"),
            int_rate=("int_f", "mean"),
        )
        .reset_index()
        .rename(columns={"posteam": "team"})
    )
    off_g = off_basic.merge(pass_epa.reset_index().rename(columns={"posteam": "team"}), how="left")
    off_g = off_g.merge(rush_epa.reset_index().rename(columns={"posteam": "team"}), how="left")
    off_g = off_g.merge(early_epa.reset_index().rename(columns={"posteam": "team"}), how="left")

    def_pass = (
        off.loc[off["is_pass"]].groupby(["game_id", "defteam"], sort=False)["epa"].mean().rename("pass_epa_allowed")
    )
    def_rush = (
        off.loc[off["is_rush"]].groupby(["game_id", "defteam"], sort=False)["epa"].mean().rename("rush_epa_allowed")
    )
    def_basic = (
        off.groupby(["game_id", "defteam"], sort=False)
        .agg(
            def_epa=("epa", "mean"),
            success_def=("success_f", "mean"),
            explosive_allowed=("explosive", "mean"),
        )
        .reset_index()
        .rename(columns={"defteam": "team"})
    )
    def_g = def_basic.merge(def_pass.reset_index().rename(columns={"defteam": "team"}), how="left")
    def_g = def_g.merge(def_rush.reset_index().rename(columns={"defteam": "team"}), how="left")

    tg = off_g.merge(def_g, on=["game_id", "team"], how="outer")
    logger.info("Team-game rows=%s", len(tg))
    return tg
