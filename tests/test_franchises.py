"""Franchise continuity: STL→LAR, OAK→LV, etc."""

from app.ingest.identity import (
    CURRENT_NFL_TEAMS,
    canonicalize_nfl_team,
    nfl_franchise_sql,
    nfl_team_name,
)


def test_franchise_aliases() -> None:
    assert canonicalize_nfl_team("STL") == "LAR"
    assert canonicalize_nfl_team("LA") == "LAR"
    assert canonicalize_nfl_team("OAK") == "LV"
    assert canonicalize_nfl_team("LVR") == "LV"
    assert canonicalize_nfl_team("SD") == "LAC"
    assert canonicalize_nfl_team("JAC") == "JAX"
    assert canonicalize_nfl_team("WSH") == "WAS"
    assert canonicalize_nfl_team("LAR") == "LAR"
    assert len(CURRENT_NFL_TEAMS) == 32


def test_franchise_sql_contains_aliases() -> None:
    sql = nfl_franchise_sql("home_team")
    assert "WHEN 'STL' THEN 'LAR'" in sql
    assert "WHEN 'OAK' THEN 'LV'" in sql
    assert sql.startswith("CASE home_team")


def test_display_names_use_current_city() -> None:
    assert "Rams" in nfl_team_name("STL")
    assert "Raiders" in nfl_team_name("OAK")
    assert "Chargers" in nfl_team_name("SD")
