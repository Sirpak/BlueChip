"""Load leakage-safe snapshot frames for pregame models."""

from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session

from ml.features.constants import FEATURE_VERSION
from ml.pregame.feature_columns import DEV_SEASON_END, DEV_SEASON_START, add_derived_columns


def load_pregame_frame(
    session: Session,
    *,
    feature_version: str = FEATURE_VERSION,
    season_start: int = DEV_SEASON_START,
    season_end: int = DEV_SEASON_END,
    season_type: str = "REG",
) -> pd.DataFrame:
    """Snapshots joined to games for labels, market line, and season filters."""
    sql = """
        SELECT
            s.*,
            g.season_type,
            g.spread_line,
            g.kickoff
        FROM feature_snapshots s
        JOIN games g ON g.game_id = s.game_id
        WHERE s.feature_version = :feature_version
          AND g.league = 'NFL'
          AND g.season_type = :season_type
          AND s.season BETWEEN :season_start AND :season_end
        ORDER BY s.season, s.week, s.game_id
    """
    df = pd.read_sql(
        sql,
        session.get_bind(),
        params={
            "feature_version": feature_version,
            "season_type": season_type,
            "season_start": season_start,
            "season_end": season_end,
        },
    )
    if df["market_spread"].isna().all() and "spread_line" in df.columns:
        df["market_spread"] = pd.to_numeric(df["spread_line"], errors="coerce")
    return add_derived_columns(df)
