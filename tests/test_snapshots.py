"""Pregame snapshot rolling, ratings walk, and known_at (no live DB required)."""

from datetime import datetime, timezone

import pandas as pd

from ml.features.ratings import fit_adj_epa, fit_srs, walk_ratings
from ml.features.snapshots import add_prior_rolling, snapshots_to_rows


def test_prior_rolling_excludes_current_game() -> None:
    ts = [
        datetime(2020, 9, 13, 17, tzinfo=timezone.utc),
        datetime(2020, 9, 20, 17, tzinfo=timezone.utc),
        datetime(2020, 9, 27, 17, tzinfo=timezone.utc),
    ]
    tg = pd.DataFrame(
        {
            "game_id": ["g1", "g2", "g3"],
            "team": ["BUF", "BUF", "BUF"],
            "season": [2020, 2020, 2020],
            "sort_ts": ts,
            "off_epa": [0.10, 0.90, -0.20],
            "is_home": [True, True, True],
        }
    )
    out = add_prior_rolling(tg)
    assert pd.isna(out.loc[out["game_id"] == "g1", "off_epa_ewma"].iloc[0])
    g2 = float(out.loc[out["game_id"] == "g2", "off_epa_ewma"].iloc[0])
    assert abs(g2 - 0.10) < 1e-9
    g3 = float(out.loc[out["game_id"] == "g3", "off_epa_ewma"].iloc[0])
    assert abs(g3 - 0.90) > 0.05


def test_elo_snapshot_is_pre_update() -> None:
    ts = [
        datetime(2020, 9, 13, 17, tzinfo=timezone.utc),
        datetime(2020, 9, 20, 17, tzinfo=timezone.utc),
    ]
    games = pd.DataFrame(
        {
            "game_id": ["g1", "g2"],
            "season": [2020, 2020],
            "week": [1, 2],
            "season_type": ["REG", "REG"],
            "game_date": [ts[0].date(), ts[1].date()],
            "sort_ts": ts,
            "home_team": ["BUF", "BUF"],
            "away_team": ["NYJ", "MIA"],
            "home_margin": [14.0, 3.0],
        }
    )
    ratings = walk_ratings(games, pd.DataFrame())
    assert abs(float(ratings.loc[0, "elo_home"]) - 1500.0) < 1e-9
    assert float(ratings.loc[1, "elo_home"]) > 1500.0
    assert abs(float(ratings.loc[0, "hfa_prior"]) - 2.0) < 1e-9


def test_srs_excludes_current_game_and_is_mean_centered() -> None:
    rows = [("BUF", "NYJ", 14.0), ("MIA", "BUF", -3.0)]
    srs = fit_srs(rows)
    assert abs(sum(srs.values())) < 1e-6
    assert srs["BUF"] > srs["NYJ"]

    ts = [
        datetime(2020, 9, 13, 17, tzinfo=timezone.utc),
        datetime(2020, 9, 20, 17, tzinfo=timezone.utc),
    ]
    games = pd.DataFrame(
        {
            "game_id": ["g1", "g2"],
            "season": [2020, 2020],
            "week": [1, 2],
            "season_type": ["REG", "REG"],
            "game_date": [ts[0].date(), ts[1].date()],
            "sort_ts": ts,
            "home_team": ["BUF", "BUF"],
            "away_team": ["NYJ", "MIA"],
            "home_margin": [14.0, 3.0],
        }
    )
    ratings = walk_ratings(games, pd.DataFrame())
    assert abs(float(ratings.loc[0, "srs_home"])) < 1e-9
    assert float(ratings.loc[1, "srs_home"]) > 0.0


def test_adj_epa_fits_offense_and_defense() -> None:
    teams = [f"T{i}" for i in range(8)]
    rows = []
    for week in range(6):
        for i, team in enumerate(teams):
            opp = teams[(i + 1 + week) % 8]
            off = 0.20 if i < 4 else -0.15
            rows.append(
                {
                    "game_id": f"w{week}_{team}",
                    "team": team,
                    "opponent": opp,
                    "off_epa": off,
                    "is_home": i % 2 == 0,
                }
            )
    off, deff = fit_adj_epa(pd.DataFrame(rows))
    assert off["T0"] > off["T7"]
    assert deff["T0"] != 0.0 or deff["T7"] != 0.0


def test_known_at_max_is_before_kickoff() -> None:
    kick = datetime(2020, 9, 13, 17, 0, tzinfo=timezone.utc)
    snap = pd.DataFrame(
        [
            {
                "game_id": "2020_01_NYJ_BUF",
                "season": 2020,
                "week": 1,
                "home_team": "BUF",
                "away_team": "NYJ",
                "era": "2016-2020",
                "kickoff": kick,
            }
        ]
    )
    row = snapshots_to_rows(snap)[0]
    assert row["prediction_at"] == kick
    assert row["known_at_max"] is not None
    assert row["known_at_max"] < row["prediction_at"]
    assert "vegas_wp" not in row
