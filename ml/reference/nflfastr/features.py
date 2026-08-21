"""nflfastR-shaped WP / EP features.

Source of truth for formulas: nflfastR ``calculate_win_probability``
(https://github.com/nflverse/nflfastR/blob/master/R/ep_wp_calculators.R)
and Baldwin / open-source-football 2020-09-28.

``Diff_Time_Ratio`` in production R is

    score_differential / exp(-4 * elapsed_share)

which is algebraically the same as the blog form

    score_differential * exp(4 * elapsed_share)

``spread_time`` decays the pregame spread as the clock runs:

    posteam_spread * exp(-4 * elapsed_share)

``spread_line`` here is nflverse: **positive means the home team was favored**.
``posteam_spread`` is that line from the possession team's point of view.

We train from nflverse **parquet**, not the slim SQLite ``plays`` table
(timeouts / ``receive_2h_ko`` / ``vegas_wp`` are not in SQLite today).
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from app.ingest.nflfastr import download_pbp_parquet, parquet_path_for_season

GAME_SECONDS = 3600.0
DECAY = 4.0

# Columns read from parquet for WP replication (keep nflverse labels for compare).
WP_SOURCE_COLUMNS: tuple[str, ...] = (
    "game_id",
    "play_id",
    "season",
    "week",
    "season_type",
    "qtr",
    "home_team",
    "away_team",
    "posteam",
    "defteam",
    "play_type",
    "down",
    "ydstogo",
    "yardline_100",
    "half_seconds_remaining",
    "game_seconds_remaining",
    "score_differential",
    "result",
    "posteam_timeouts_remaining",
    "defteam_timeouts_remaining",
    "receive_2h_ko",
    "spread_line",
    "wp",
    "vegas_wp",
    "ep",
    "epa",
)

PURE_WP_FEATURES: list[str] = [
    "receive_2h_ko",
    "home",
    "half_seconds_remaining",
    "game_seconds_remaining",
    "diff_time_ratio",
    "score_differential",
    "down",
    "ydstogo",
    "yardline_100",
    "posteam_timeouts_remaining",
    "defteam_timeouts_remaining",
]

MARKET_WP_FEATURES: list[str] = PURE_WP_FEATURES + ["spread_time"]

LABEL_COL = "label"


def elapsed_share(game_seconds_remaining: np.ndarray | pd.Series) -> np.ndarray:
    gsr = np.asarray(game_seconds_remaining, dtype=float)
    return (GAME_SECONDS - gsr) / GAME_SECONDS


def diff_time_ratio(
    score_differential: np.ndarray | pd.Series,
    game_seconds_remaining: np.ndarray | pd.Series,
) -> np.ndarray:
    """Possession-team score diff scaled up as time elapses (nflfastR identity)."""
    share = elapsed_share(game_seconds_remaining)
    sd = np.asarray(score_differential, dtype=float)
    return sd / np.exp(-DECAY * share)


def spread_time(
    posteam_spread: np.ndarray | pd.Series,
    game_seconds_remaining: np.ndarray | pd.Series,
) -> np.ndarray:
    """Pregame spread from posteam view, decayed toward zero as the game progresses."""
    share = elapsed_share(game_seconds_remaining)
    spread = np.asarray(posteam_spread, dtype=float)
    return spread * np.exp(-DECAY * share)


def _engineer_receive_2h_ko(df: pd.DataFrame) -> pd.Series:
    """1 in the first half if posteam will receive the 2nd-half kickoff."""
    if "receive_2h_ko" in df.columns and df["receive_2h_ko"].notna().any():
        return pd.to_numeric(df["receive_2h_ko"], errors="coerce")

    opening_receiver = (
        df.loc[df["play_type"].astype(str) == "kickoff", ["game_id", "play_id", "posteam"]]
        .sort_values(["game_id", "play_id"])
        .groupby("game_id", as_index=True)["posteam"]
        .first()
    )
    recv = df["game_id"].map(opening_receiver)
    first_half = pd.to_numeric(df["qtr"], errors="coerce").fillna(99) <= 2
    return (first_half & (df["posteam"] != recv) & df["posteam"].notna()).astype(float)


def add_wp_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``home``, ``diff_time_ratio``, ``spread_time``, ``receive_2h_ko``, ``label``."""
    out = df.copy()
    posteam = out["posteam"]
    home_team = out["home_team"]
    out["home"] = (posteam == home_team).astype(float)
    out["posteam_is_home"] = out["home"]

    spread_line = pd.to_numeric(out.get("spread_line"), errors="coerce")
    out["posteam_spread"] = np.where(out["home"] == 1, spread_line, -spread_line)

    gsr = pd.to_numeric(out["game_seconds_remaining"], errors="coerce")
    sd = pd.to_numeric(out["score_differential"], errors="coerce")
    out["elapsed_share"] = elapsed_share(gsr)
    out["diff_time_ratio"] = diff_time_ratio(sd, gsr)
    out["spread_time"] = spread_time(out["posteam_spread"], gsr)
    out["receive_2h_ko"] = _engineer_receive_2h_ko(out)

    result = pd.to_numeric(out.get("result"), errors="coerce")
    posteam_won = np.where(
        result > 0,
        out["home"] == 1,
        np.where(result < 0, out["home"] == 0, np.nan),
    )
    out[LABEL_COL] = pd.Series(posteam_won, index=out.index).astype(float)
    return out


def wp_row_filter(df: pd.DataFrame) -> pd.Series:
    """Regulation, valid down/state, no ties — Baldwin / nflfastR training filter."""
    qtr = pd.to_numeric(df["qtr"], errors="coerce")
    result = pd.to_numeric(df["result"], errors="coerce")
    return (
        qtr.le(4)
        & result.notna()
        & (result != 0)
        & df["posteam"].notna()
        & pd.to_numeric(df["down"], errors="coerce").notna()
        & pd.to_numeric(df["game_seconds_remaining"], errors="coerce").notna()
        & pd.to_numeric(df["yardline_100"], errors="coerce").notna()
        & pd.to_numeric(df["score_differential"], errors="coerce").notna()
        & pd.to_numeric(df["posteam_timeouts_remaining"], errors="coerce").notna()
        & pd.to_numeric(df["defteam_timeouts_remaining"], errors="coerce").notna()
        & pd.to_numeric(df[LABEL_COL], errors="coerce").notna()
    )


def wp_training_frame(df: pd.DataFrame, *, market: bool = False) -> pd.DataFrame:
    """Feature-ready WP rows. ``market=True`` also requires ``spread_time``."""
    featured = add_wp_features(df)
    keep = wp_row_filter(featured)
    if market:
        keep = keep & pd.to_numeric(featured["spread_time"], errors="coerce").notna()
    cols = ["game_id", "play_id", "season", "qtr", LABEL_COL, "wp", "vegas_wp"]
    cols += MARKET_WP_FEATURES if market else PURE_WP_FEATURES
    existing = [c for c in cols if c in featured.columns]
    return featured.loc[keep, existing].copy()


def load_pbp_seasons(
    seasons: Iterable[int],
    *,
    force_download: bool = False,
    columns: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """Load cached (or downloaded) nflverse parquet with modeling columns intact."""
    wanted = list(columns or WP_SOURCE_COLUMNS)
    frames: list[pd.DataFrame] = []
    for season in seasons:
        path: Path = parquet_path_for_season(int(season))
        if not path.exists() or force_download:
            download_pbp_parquet(int(season), force=force_download)
        raw = pd.read_parquet(path)
        present = [c for c in wanted if c in raw.columns]
        frames.append(raw[present].copy())
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)
