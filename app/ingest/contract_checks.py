"""Data Contract v0.1 helpers: identity, Market 0 tags, basic leakage guards."""

from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from db.models import Game, OddsSnapshot, Play, PlayerExternalId, Team


def assert_core_contract(session: Session) -> dict[str, int]:
    """Raise if league/identity/Market 0 are missing. Safe on the live SQLite."""
    insp = inspect(session.get_bind())
    for table in ("leagues", "teams", "team_external_ids", "players", "player_external_ids"):
        if table not in insp.get_table_names():
            raise AssertionError(f"missing table {table}")

    game_cols = {c["name"] for c in insp.get_columns("games")}
    play_cols = {c["name"] for c in insp.get_columns("plays")}
    odds_cols = {c["name"] for c in insp.get_columns("odds_snapshots")}
    for col in ("league", "source", "source_id"):
        if col not in game_cols:
            raise AssertionError(f"games missing {col}")
    if "league" not in play_cols:
        raise AssertionError("plays missing league")
    for col in ("market_source", "market_type", "known_at"):
        if col not in odds_cols:
            raise AssertionError(f"odds_snapshots missing {col}")

    n_games = session.query(Game).count()
    n_unleagued = session.query(Game).filter(Game.league.is_(None)).count()
    if n_games and n_unleagued:
        raise AssertionError(f"{n_unleagued} games missing league")

    n_plays_unleagued = session.query(Play).filter(Play.league.is_(None)).count()
    if n_plays_unleagued:
        raise AssertionError(f"{n_plays_unleagued} plays missing league")

    n_teams = session.query(Team).filter(Team.league == "NFL").count()
    n_gsis = session.query(PlayerExternalId).filter(PlayerExternalId.system == "gsis").count()
    n_m0 = (
        session.query(OddsSnapshot)
        .filter(
            OddsSnapshot.market_source == "nflverse_pfr",
            OddsSnapshot.market_type == "historical_close",
            OddsSnapshot.market == "spread",
        )
        .count()
    )
    n_spread_games = session.query(Game).filter(Game.spread_line.isnot(None)).count()
    if n_spread_games and n_m0 == 0:
        raise AssertionError("spread_line present but no Market 0 snapshots")

    n_kickoff = session.query(Game).filter(Game.kickoff.is_not(None)).count()
    n_rest = session.query(Game).filter(Game.home_rest.is_not(None)).count()
    n_home_away = session.execute(text("SELECT COUNT(*) FROM games WHERE home_team = away_team")).scalar_one()
    if n_home_away:
        raise AssertionError(f"{n_home_away} games with home_team = away_team")

    # PURE leakage: vegas_wp must never live on plays (it is a market feature).
    play_col_names = {c["name"] for c in insp.get_columns("plays")}
    if "vegas_wp" in play_col_names:
        raise AssertionError("plays must not persist vegas_wp (MARKET leakage)")

    snap_stats = {"snapshots": 0, "known_at_ok": 0}
    if "feature_snapshots" in insp.get_table_names():
        from ml.features.leakage import assert_snapshot_leakage

        snap_stats = assert_snapshot_leakage(session)

    bad_spread = session.execute(
        text("SELECT COUNT(*) FROM odds_snapshots WHERE point IS NOT NULL AND (point <= -100 OR point >= 100)")
    ).scalar_one()
    if bad_spread:
        raise AssertionError(f"{bad_spread} market points outside (-100, 100)")

    return {
        "games": n_games,
        "nfl_teams": n_teams,
        "gsis_players": n_gsis,
        "market0_spreads": n_m0,
        "games_with_spread": n_spread_games,
        "games_with_kickoff": n_kickoff,
        "games_with_rest": n_rest,
        "feature_snapshots": snap_stats["snapshots"],
    }
