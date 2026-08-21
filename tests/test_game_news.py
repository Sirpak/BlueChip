"""Unit tests for matchup news ranking (no network)."""

from datetime import datetime, timedelta, timezone

from app.services import game_news


def test_availability_outranks_general() -> None:
    now = datetime.now(timezone.utc)
    injury = game_news._from_espn(
        {
            "id": 1,
            "headline": "Starting QB ruled out with ankle injury",
            "description": "Status update before kickoff",
            "published": now.isoformat().replace("+00:00", "Z"),
            "links": {"web": {"href": "https://www.espn.com/a"}},
        },
        team_side="home",
        team_abbr="KC",
        now=now,
        tokens=["BUF", "KC"],
    )
    fluff = game_news._from_espn(
        {
            "id": 2,
            "headline": "Fan fest photos from the stadium",
            "description": "Crowd shots",
            "published": (now - timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
            "links": {"web": {"href": "https://www.espn.com/b"}},
        },
        team_side="away",
        team_abbr="BUF",
        now=now,
        tokens=["BUF", "KC"],
    )
    assert injury is not None and fluff is not None
    assert injury["bucket"] == "availability"
    assert injury["relevance_score"] > fluff["relevance_score"]
    assert injury["publisher"] == "ESPN"


def test_google_item_keeps_publisher() -> None:
    now = datetime.now(timezone.utc)
    item = game_news._from_google(
        {
            "headline": "Bills QB questionable for Sunday - Yahoo Sports",
            "description": None,
            "url": "https://news.google.com/rss/articles/abc",
            "published": "Sat, 15 Aug 2026 22:49:00 GMT",
            "publisher": "Yahoo Sports",
        },
        team_side="away",
        team_abbr="BUF",
        now=now,
        tokens=["BUF", "Bills"],
    )
    assert item is not None
    assert item["source"] == "google_news"
    assert item["publisher"] == "Yahoo Sports"
    assert item["bucket"] == "availability"


def test_matchup_news_empty_without_feeds(monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setattr(game_news, "fetch_espn_team_news", lambda *a, **k: [])
    monkeypatch.setattr(game_news, "fetch_google_news", lambda *a, **k: [])
    payload = game_news.matchup_news(
        league="NFL",
        away_abbr="BUF",
        home_abbr="KC",
        away_espn_id=None,
        home_espn_id=None,
    )
    assert payload["count"] == 0
    assert payload["articles"] == []
    assert "CONTEXT" in payload["disclaimer"]
