"""Pull latest team EPA profiles from feature snapshots (NFL) for matchup edges."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.ingest.identity import canonicalize_nfl_team
from ml.features.constants import FEATURE_VERSION


PROFILE_KEYS = (
    "off_epa",
    "def_epa",
    "pass_epa",
    "rush_epa",
    "pass_epa_allowed",
    "rush_epa_allowed",
    "success_off",
)


def latest_team_profiles(session: Session) -> dict[str, dict[str, float | None]]:
    """Most recent pregame snapshot side for each franchise (home row preferred)."""
    sql = text(
        """
        WITH ranked AS (
          SELECT
            home_team AS team,
            home_off_epa AS off_epa,
            home_def_epa AS def_epa,
            home_pass_epa AS pass_epa,
            home_rush_epa AS rush_epa,
            home_pass_epa_allowed AS pass_epa_allowed,
            home_rush_epa_allowed AS rush_epa_allowed,
            extras_json,
            season, week,
            ROW_NUMBER() OVER (PARTITION BY home_team ORDER BY season DESC, week DESC) AS rn
          FROM feature_snapshots
          WHERE feature_version = :fv
          UNION ALL
          SELECT
            away_team,
            away_off_epa, away_def_epa, away_pass_epa, away_rush_epa,
            away_pass_epa_allowed, away_rush_epa_allowed,
            extras_json, season, week,
            ROW_NUMBER() OVER (PARTITION BY away_team ORDER BY season DESC, week DESC) AS rn
          FROM feature_snapshots
          WHERE feature_version = :fv
        )
        SELECT * FROM ranked WHERE rn = 1
        """
    )
    rows = session.execute(sql, {"fv": FEATURE_VERSION}).mappings().all()
    out: dict[str, dict[str, float | None]] = {}
    for r in rows:
        team = canonicalize_nfl_team(r["team"]) or r["team"]
        # success_off may live in extras; leave None if missing
        out[team] = {
            "off_epa": r["off_epa"],
            "def_epa": r["def_epa"],
            "pass_epa": r["pass_epa"],
            "rush_epa": r["rush_epa"],
            "pass_epa_allowed": r["pass_epa_allowed"],
            "rush_epa_allowed": r["rush_epa_allowed"],
            "success_off": None,
        }
    return out


def profiles_for_game(
    session: Session, home: str, away: str
) -> tuple[dict[str, float | None], dict[str, float | None]]:
    all_p = latest_team_profiles(session)
    h = canonicalize_nfl_team(home) or home
    a = canonicalize_nfl_team(away) or away
    return all_p.get(h, {}), all_p.get(a, {})
