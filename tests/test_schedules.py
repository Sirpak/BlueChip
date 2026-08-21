"""nflverse schedule merge: kickoff/rest; PBP scores win on conflict."""

from datetime import timezone

import pandas as pd
from sqlalchemy import delete, select

from app.ingest.schedules import apply_schedule_frame, parse_kickoff, season_type_from_game_type
from db.models import Game, GameExternalId, IngestConflict
from db.session import get_session_factory


def test_parse_kickoff_edt() -> None:
    ko = parse_kickoff("2024-09-08", "13:00")
    assert ko is not None
    assert ko.astimezone(timezone.utc).hour == 17


def test_season_type_mapping() -> None:
    assert season_type_from_game_type("REG") == "REG"
    assert season_type_from_game_type("WC") == "POST"
    assert season_type_from_game_type("SB") == "POST"
    assert season_type_from_game_type("PRE") == "PRE"


def test_schedule_keeps_pbp_score_on_conflict() -> None:
    session = get_session_factory()()
    game_id = "2099_01_ZZZ_YYY"
    try:
        session.merge(
            Game(
                game_id=game_id,
                league="NFL",
                season=2099,
                week=1,
                season_type="REG",
                home_team="ZZZ",
                away_team="YYY",
                home_score=31,
                away_score=17,
                result=14,
                total=48,
                spread_line=-3.5,
                source="nflverse",
                source_id=game_id,
            )
        )
        session.commit()
        df = pd.DataFrame(
            [
                {
                    "game_id": game_id,
                    "season": 2099,
                    "game_type": "REG",
                    "week": 1,
                    "gameday": "2099-09-10",
                    "weekday": "Friday",
                    "gametime": "20:15",
                    "home_team": "ZZZ",
                    "away_team": "YYY",
                    "home_score": 99,
                    "away_score": 0,
                    "location": "Home",
                    "result": 99,
                    "total": 99,
                    "overtime": 0,
                    "espn": "999001",
                    "pfr": "zzz2099",
                    "gsis": None,
                    "home_rest": 7,
                    "away_rest": 6,
                    "home_moneyline": -180,
                    "away_moneyline": 154,
                    "spread_line": -7.0,
                    "home_spread_odds": -110,
                    "away_spread_odds": -110,
                    "total_line": 44.5,
                    "over_odds": -110,
                    "under_odds": -110,
                    "div_game": 0,
                    "roof": "outdoors",
                    "surface": "grass",
                    "temp": 70,
                    "wind": 5,
                    "stadium": "Test Park",
                }
            ]
        )
        stats = apply_schedule_frame(session, df)
        session.commit()
        game = session.get(Game, game_id)
        assert game is not None
        assert game.home_score == 31
        assert game.away_score == 17
        assert game.spread_line == -3.5
        assert game.home_rest == 7
        assert game.away_rest == 6
        assert game.home_moneyline == -180
        assert game.kickoff is not None
        assert stats["conflicts"] >= 3
        n_flags = session.scalar(
            select(IngestConflict.id).where(IngestConflict.game_id == game_id).limit(1)
        )
        assert n_flags is not None
    finally:
        session.execute(delete(IngestConflict).where(IngestConflict.game_id == game_id))
        session.execute(delete(GameExternalId).where(GameExternalId.game_id == game_id))
        session.execute(delete(Game).where(Game.game_id == game_id))
        session.commit()
        session.close()
