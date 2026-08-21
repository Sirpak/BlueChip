"""Smoke tests for schema + ingest helpers."""

from datetime import date

import pandas as pd

from app.ingest.nflfastr import _games_from_pbp, _plays_from_pbp


def test_games_and_plays_from_minimal_pbp() -> None:
    df = pd.DataFrame(
        [
            {
                "play_id": 1,
                "game_id": "2024_01_KC_BAL",
                "season": 2024,
                "week": 1,
                "season_type": "REG",
                "game_date": "2024-09-05",
                "home_team": "BAL",
                "away_team": "KC",
                "posteam": "KC",
                "defteam": "BAL",
                "play_type": "pass",
                "epa": 0.5,
                "pass_attempt": 1,
                "rush_attempt": 0,
                "success": 1,
                "home_score": 0,
                "away_score": 7,
                "roof": "outdoor",
                "surface": "grass",
                "temp": 72.0,
                "wind": 5.0,
                "result": None,
                "total": None,
                "spread_line": -3.0,
                "total_line": 47.5,
            },
            {
                "play_id": 2,
                "game_id": "2024_01_KC_BAL",
                "season": 2024,
                "week": 1,
                "season_type": "REG",
                "game_date": "2024-09-05",
                "home_team": "BAL",
                "away_team": "KC",
                "posteam": "BAL",
                "defteam": "KC",
                "play_type": "run",
                "epa": -0.2,
                "pass_attempt": 0,
                "rush_attempt": 1,
                "success": 0,
                "home_score": 20,
                "away_score": 27,
                "roof": "outdoor",
                "surface": "grass",
                "temp": 72.0,
                "wind": 5.0,
                "result": -7,
                "total": 47,
                "spread_line": -3.0,
                "total_line": 47.5,
            },
        ]
    )

    games = _games_from_pbp(df)
    plays = _plays_from_pbp(df)

    assert len(games) == 1
    assert games[0]["game_id"] == "2024_01_KC_BAL"
    assert games[0]["home_score"] == 20
    assert games[0]["away_score"] == 27
    assert games[0]["result"] == -7
    assert games[0]["game_date"] == date(2024, 9, 5)

    assert len(plays) == 2
    assert plays[0]["pass_attempt"] is True
    assert plays[1]["rush_attempt"] is True
    assert plays[0]["play_id"] == "1"
