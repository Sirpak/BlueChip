"""PURE v0.1 feature columns for logistic and Ridge (BCW-SNAP-v0.1).

Home margin convention: M = home − away. nflverse ``spread_line > 0`` ⇒ home favored.
"""

from __future__ import annotations

import pandas as pd

MODEL_LOGISTIC = "BCW-LOGISTIC-v0.1"
MODEL_RIDGE = "BCW-RIDGE-v0.1"

DEV_SEASON_START = 2009
DEV_SEASON_END = 2022

BASE_FEATURES: tuple[str, ...] = (
    "elo_diff",
    "srs_diff",
    "rest_diff",
    "success_rate_diff",
    "explosive_play_diff",
)

RAW_EPA_FEATURES: tuple[str, ...] = BASE_FEATURES + ("off_epa_diff", "def_epa_diff")
ADJ_EPA_FEATURES: tuple[str, ...] = BASE_FEATURES + ("adj_off_diff", "adj_def_diff")

COMPUTED_COLUMNS = (
    "off_epa_diff",
    "def_epa_diff",
    "adj_off_diff",
    "adj_def_diff",
    "pass_epa_diff",
    "rush_epa_diff",
    "pass_epa_allowed_diff",
)


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Team-strength diffs used by raw vs opponent-adjusted Ridge variants."""
    out = df.copy()
    if {"home_off_epa", "away_off_epa"}.issubset(out.columns):
        out["off_epa_diff"] = out["home_off_epa"] - out["away_off_epa"]
    if {"home_def_epa", "away_off_epa"}.issubset(out.columns):
        out["def_epa_diff"] = out["away_off_epa"] - out["home_def_epa"]
    if {"adj_off_home", "adj_off_away"}.issubset(out.columns):
        out["adj_off_diff"] = out["adj_off_home"] - out["adj_off_away"]
    if {"adj_def_home", "adj_def_away"}.issubset(out.columns):
        out["adj_def_diff"] = out["adj_def_away"] - out["adj_def_home"]
    if {"home_pass_epa", "away_pass_epa"}.issubset(out.columns):
        out["pass_epa_diff"] = out["home_pass_epa"] - out["away_pass_epa"]
    if {"home_rush_epa", "away_rush_epa"}.issubset(out.columns):
        out["rush_epa_diff"] = out["home_rush_epa"] - out["away_rush_epa"]
    if {"home_pass_epa_allowed", "away_pass_epa_allowed"}.issubset(out.columns):
        out["pass_epa_allowed_diff"] = out["away_pass_epa_allowed"] - out["home_pass_epa_allowed"]
    return out


def feature_matrix(df: pd.DataFrame, columns: tuple[str, ...]) -> tuple[pd.DataFrame, pd.Series]:
    """Return X (with intercept) and a boolean mask of complete rows."""
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise KeyError(f"missing feature columns: {missing}")
    block = df[list(columns)].apply(pd.to_numeric, errors="coerce")
    mask = block.notna().all(axis=1)
    x = block.loc[mask].copy()
    x.insert(0, "intercept", 1.0)
    return x, mask
