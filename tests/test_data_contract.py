"""Data Contract v0.1: league, identity, Market 0 snapshots."""

from app.ingest.contract_checks import assert_core_contract
from app.ingest.identity import backfill_contract
from db.session import get_session_factory


def test_data_contract_backfill_and_checks() -> None:
    session = get_session_factory()()
    try:
        stats = backfill_contract(session)
        checks = assert_core_contract(session)
    finally:
        session.close()

    assert checks["games"] > 0
    assert checks["nfl_teams"] >= 32
    assert checks["gsis_players"] > 100
    assert checks["market0_spreads"] == checks["games_with_spread"]
    assert stats["market_rows"] >= checks["market0_spreads"]
