"""Parse ESPN scoreboard events without hitting the network."""

from app.ingest.sources.espn import format_spread_label, home_spread_from_odds, parse_event, parse_scoreboard


SAMPLE_EVENT = {
    "id": "401873400",
    "date": "2026-09-10T00:20Z",
    "week": {"number": 1},
    "season": {"year": 2026, "type": 2},
    "status": {"type": {"name": "STATUS_SCHEDULED"}},
    "competitions": [
        {
            "neutralSite": False,
            "competitors": [
                {
                    "homeAway": "home",
                    "team": {"abbreviation": "SEA", "displayName": "Seattle Seahawks"},
                },
                {
                    "homeAway": "away",
                    "team": {"abbreviation": "NE", "displayName": "New England Patriots"},
                },
            ],
            "odds": [
                {
                    "details": "SEA -3.5",
                    "overUnder": 44.5,
                    "spread": -3.5,
                    "provider": {"name": "DraftKings"},
                    "homeTeamOdds": {"favorite": True, "underdog": False},
                    "awayTeamOdds": {"favorite": False, "underdog": True},
                }
            ],
        }
    ],
}


def test_home_favorite_spread() -> None:
    spread = home_spread_from_odds(SAMPLE_EVENT["competitions"][0]["odds"][0])
    assert spread == -3.5
    assert format_spread_label("SEA", "NE", spread) == "SEA -3.5"


def test_parse_event_matchup() -> None:
    game = parse_event(
        SAMPLE_EVENT,
        league="NFL",
        fallback_week=1,
        fallback_season=2026,
        fallback_stype="REG",
    )
    assert game is not None
    assert game["matchup"] == "NE @ SEA"
    assert game["home_spread"] == -3.5
    assert game["spread_label"] == "SEA -3.5"
    assert game["total_line"] == 44.5
    assert game["round"] == "Week 1"
    assert game["source"] == "espn"


def test_parse_scoreboard_skips_empty() -> None:
    assert parse_scoreboard({"events": []}, league="NFL") == []
