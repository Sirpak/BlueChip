"""Columns owned by nflverse schedules, not PBP collapse."""

SCHEDULE_OWNED_GAME_COLS = frozenset(
    {
        "kickoff",
        "occurred_at",
        "home_rest",
        "away_rest",
        "home_moneyline",
        "away_moneyline",
        "spread_home_odds",
        "spread_away_odds",
        "over_odds",
        "under_odds",
        "weekday",
        "gametime",
        "location",
        "neutral_site",
        "overtime",
        "div_game",
        "game_type",
        "stadium_name",
    }
)
