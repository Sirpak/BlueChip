"""Dashboard query smoke tests against the live SQLite ingest."""

from fastapi.testclient import TestClient

from app.main import app
from app.auth.seed import seed_dev_users
from app.services.dashboard import dashboard_payload
from db.session import get_session_factory


def test_dashboard_payload_has_2025_standings() -> None:
    session = get_session_factory()()
    try:
        payload = dashboard_payload(session)
    finally:
        session.close()

    assert payload["latest_season"] == 2025
    assert payload["totals"]["plays"] > 100_000
    teams = {row["team"] for row in payload["standings"]}
    assert "SEA" in teams
    assert len(payload["standings"]) == 32


def test_dashboard_pages_render(monkeypatch) -> None:
    session = get_session_factory()()
    try:
        seed_dev_users(session)
    finally:
        session.close()

    monkeypatch.setattr(
        "app.services.schedule.upcoming_window",
        lambda **_kwargs: {
            "as_of": "2026-08-17T00:00:00+00:00",
            "horizon_days": 28,
            "window_end": "2026-09-14T00:00:00+00:00",
            "source": "espn",
            "nfl": [],
            "cfb": [],
            "count": {"nfl": 0, "cfb": 0},
        },
    )
    client = TestClient(app)
    login = client.post("/api/auth/login", json={"username": "demo_pro", "password": "demoPro123"})
    assert login.status_code == 200

    home = client.get("/")
    assert home.status_code == 200
    assert b"BlueChipWager" in home.content

    games = client.get("/games")
    assert games.status_code == 200

    api = client.get("/api/dashboard")
    assert api.status_code == 200
    assert api.json()["latest_season"] == 2025

    ratings = client.get("/teams/SEA/ratings")
    assert ratings.status_code == 200
    assert ratings.json()["team"] == "SEA"

    desk = client.get("/legacy/markets")
    assert desk.status_code == 200
    assert b"Market desk" in desk.content

    priced = client.get("/api/markets/price", params={"home_spread": -7, "home_american": -110, "away_american": -110})
    assert priced.status_code == 200
    assert abs(priced.json()["break_even_home"] - 0.5238) < 1e-4


def test_brand_icons_served() -> None:
    client = TestClient(app)
    ico = client.get("/favicon.ico")
    assert ico.status_code == 200
    assert ico.content[:8] == b"\x89PNG\r\n\x1a\n"
    mark = client.get("/images/icon.png")
    assert mark.status_code == 200
    assert mark.content[:8] == b"\x89PNG\r\n\x1a\n"
    wordmark = client.get("/images/Logo_BlueChipWager.png")
    assert wordmark.status_code == 200
    glb = client.get("/models/wilson-football.glb")
    assert glb.status_code == 200
    assert glb.content[:4] == b"glTF"
