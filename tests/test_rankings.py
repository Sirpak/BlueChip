"""Rankings helpers (network mocked where needed)."""

from app.ingest.identity import CURRENT_NFL_TEAMS, canonicalize_nfl_team
from app.services import rankings


def test_zscores_centered() -> None:
    zs = rankings._zscores([10.0, 20.0, 30.0])
    assert abs(sum(zs)) < 1e-9
    assert zs[2] > zs[0]


def test_franchise_aliases_fold_to_current() -> None:
    assert canonicalize_nfl_team("STL") == "LAR"
    assert canonicalize_nfl_team("LA") == "LAR"
    assert canonicalize_nfl_team("OAK") == "LV"
    assert canonicalize_nfl_team("LVR") == "LV"
    assert canonicalize_nfl_team("SD") == "LAC"
    assert canonicalize_nfl_team("JAC") == "JAX"
    assert canonicalize_nfl_team("WSH") == "WAS"
    assert len(CURRENT_NFL_TEAMS) == 32


def test_bcw_strength_has_exactly_32_franchises() -> None:
    from db.session import get_session_factory

    session = get_session_factory()()
    try:
        payload = rankings.bcw_nfl_strength(session)
        assert payload["count"] == 32
        teams = [r["team"] for r in payload["rows"]]
        assert len(teams) == len(set(teams))
        assert set(teams) == CURRENT_NFL_TEAMS
        assert "STL" not in teams
        assert "OAK" not in teams
        assert "SD" not in teams
        assert payload["rows"][0]["rank"] == 1
        assert payload["rows"][0]["elo"] is not None
        assert payload["rows"][0]["name"]
    finally:
        session.close()


def test_ap_top25_live() -> None:
    payload = rankings.ap_top25()
    assert payload["count"] == 25
    assert payload["rows"][0]["rank"] == 1
    assert payload["rows"][0]["espn_id"]
