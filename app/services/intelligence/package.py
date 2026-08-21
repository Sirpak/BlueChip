"""W2B — Game Intelligence Package: build once, serve many page views."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.config import ROOT_DIR
from app.services import game_news, rankings
from app.services.intelligence.brief import write_brief
from app.services.intelligence.events import events_from_news
from app.services.weekly_desk import card_for_game, load_weekly
from db.session import get_session_factory
from ml.matchup.edges import (
    edges_from_profiles,
    edges_from_ranks,
    paths_to_win,
    total_adjustment,
    what_could_go_wrong,
)
from ml.matchup.headlines import headline_cards, slate_top_edges
from ml.matchup.logistic import score_edges
from ml.matchup.profiles import profiles_for_game

logger = logging.getLogger(__name__)

INTEL_DIR = ROOT_DIR / "data" / "intelligence"
INTEL_DIR.mkdir(parents=True, exist_ok=True)
INDEX_PATH = INTEL_DIR / "index.json"
PACKAGE_VERSION = "BCW-GIP-v0.1"


def _hash_payload(obj: Any) -> str:
    blob = json.dumps(obj, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:24]


def _package_path(game_id: str) -> Path:
    safe = game_id.replace(":", "_").replace("/", "_")
    return INTEL_DIR / f"{safe}.json"


def load_package(game_id: str) -> dict[str, Any] | None:
    path = _package_path(game_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_index() -> dict[str, Any]:
    if not INDEX_PATH.exists():
        return {"packages": {}, "updated_at": None}
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def _save_package(pkg: dict[str, Any]) -> None:
    path = _package_path(pkg["game_id"])
    path.write_text(json.dumps(pkg, indent=2), encoding="utf-8")
    idx = load_index()
    idx.setdefault("packages", {})[pkg["game_id"]] = {
        "game_id": pkg["game_id"],
        "matchup": pkg["game"].get("matchup"),
        "league": pkg["game"].get("league"),
        "lean_team": pkg.get("lean_team"),
        "top_edges": pkg.get("slate_edges"),
        "source_set_hash": pkg["source_set_hash"],
        "generated_at": pkg["generated_at"],
        "summary_short": pkg.get("summary_short"),
    }
    idx["updated_at"] = datetime.now(timezone.utc).isoformat()
    INDEX_PATH.write_text(json.dumps(idx, indent=2), encoding="utf-8")


def _ap_ranks() -> dict[str, int]:
    poll = rankings.ap_top25()
    out: dict[str, int] = {}
    for row in poll.get("rows") or []:
        if row.get("espn_id") and row.get("rank") is not None:
            out[f"id:{row['espn_id']}"] = int(row["rank"])
        if row.get("team"):
            out[str(row["team"]).upper()] = int(row["rank"])
    return out


def build_package_for_game(
    game: dict[str, Any],
    session: Session,
    *,
    use_llm: bool = True,
    force: bool = False,
) -> dict[str, Any]:
    game_id = game["game_id"]
    home = game["home_team"]
    away = game["away_team"]
    league = (game.get("league") or "NFL").upper()

    weekly = card_for_game(game_id) or {}
    projection = weekly.get("projection") or {}
    news_articles = weekly.get("news") or []
    if not news_articles:
        news_payload = game_news.matchup_news(
            league=league,
            away_abbr=away,
            home_abbr=home,
            away_espn_id=game.get("away_espn_id"),
            home_espn_id=game.get("home_espn_id"),
            away_name=game.get("away_name"),
            home_name=game.get("home_name"),
            limit=6,
        )
        news_articles = news_payload.get("articles") or []

    events = events_from_news(news_articles, game_id=game_id)

    if league == "NFL":
        home_p, away_p = profiles_for_game(session, home, away)
        edges = edges_from_profiles(home_team=home, away_team=away, home=home_p, away=away_p)
    else:
        ap = _ap_ranks()
        hr = ap.get(f"id:{game.get('home_espn_id')}") or ap.get(home.upper())
        ar = ap.get(f"id:{game.get('away_espn_id')}") or ap.get(away.upper())
        edges = edges_from_ranks(home_team=home, away_team=away, home_rank=hr, away_rank=ar)

    edge_dicts = [e.to_dict() for e in edges]
    headlines = headline_cards(edges)
    slate = slate_top_edges(edges)
    matchup_logistic = score_edges(edges)
    lean_side = matchup_logistic["lean"]
    lean_team = home if lean_side == "HOME" else away
    if projection.get("model_lean_team"):
        lean_team = projection["model_lean_team"]
    other = away if lean_team == home else home
    paths = paths_to_win(edges, home, away)
    risks = what_could_go_wrong(edges, lean_team, other)
    adj = total_adjustment(edges)

    evidence_core = {
        "game": {
            "game_id": game_id,
            "league": league,
            "matchup": game.get("matchup") or f"{away} @ {home}",
            "home_team": home,
            "away_team": away,
            "home_name": game.get("home_name"),
            "away_name": game.get("away_name"),
            "spread_label": game.get("spread_label") or weekly.get("spread_label"),
            "home_spread": game.get("home_spread") if game.get("home_spread") is not None else weekly.get("home_spread"),
            "total_line": game.get("total_line") or weekly.get("total_line"),
            "week": game.get("week") or weekly.get("week"),
        },
        "projection": projection,
        "matchup_edges": edge_dicts,
        "headline_cards": headlines,
        "matchup_logistic": matchup_logistic,
        "events": [
            {
                "event_type": e["event_type"],
                "structured_fact": e["structured_fact"],
                "source_url": e.get("source_url"),
                "publisher": e.get("publisher"),
                "confidence": e.get("confidence"),
            }
            for e in events
        ],
        "paths": paths,
        "risks": risks,
        "adjustment": adj,
        "lean_team": lean_team,
    }
    source_set_hash = _hash_payload(
        {
            "edges": edge_dicts,
            "events": evidence_core["events"],
            "projection": {
                "mu": projection.get("mu_home"),
                "lean": projection.get("model_lean_team"),
                "conf": projection.get("confidence_pct"),
            },
            "logistic": matchup_logistic.get("p_home_win"),
            "spread": evidence_core["game"].get("home_spread"),
        }
    )

    existing = load_package(game_id)
    if existing and existing.get("source_set_hash") == source_set_hash and not force:
        logger.info("Skip regenerate %s (hash unchanged)", game_id)
        return existing

    written = write_brief(evidence_core, use_llm=use_llm)
    now = datetime.now(timezone.utc).isoformat()
    pkg = {
        "game_id": game_id,
        "version": PACKAGE_VERSION,
        "created_at": existing.get("created_at") if existing else now,
        "generated_at": now,
        "information_cutoff": now,
        "source_set_hash": source_set_hash,
        "game": evidence_core["game"],
        "lean_team": lean_team,
        "projection": projection,
        "matchup_edges": edge_dicts,
        "headline_cards": headlines,
        "slate_edges": slate,
        "matchup_logistic": matchup_logistic,
        "paths": paths,
        "risks": risks,
        "adjustment": adj,
        "events": events,
        "news_citations": [
            {"headline": a.get("headline"), "url": a.get("url"), "publisher": a.get("publisher")}
            for a in news_articles[:8]
        ],
        "summary_short": written["summary_short"],
        "summary_full": written["summary_full"],
        "generation_model": written.get("model"),
        "generation_provider": written.get("provider"),
        "glossary": {
            "EPA/play": (
                "Expected Points Added estimates how much each play improves expected scoring position. "
                "Positive is good. A 5-yard gain on 3rd-and-3 is not treated like 5 yards on 3rd-and-20."
            ),
            "MATCHUP SIGNAL": (
                "A descriptive strength×weakness edge. Not a published win probability and not fed into "
                "BCW-RIDGE-v0.1 until validated walk-forward."
            ),
            "Research Preview": "BlueChip quantitative layer that has not cleared the five public ship gates.",
        },
        "levels": {
            "slate": {
                "lean": lean_team,
                "top_edges": slate,
                "market": evidence_core["game"].get("spread_label"),
                "mu": projection.get("mu_home"),
                "confidence_pct": projection.get("confidence_pct"),
            }
        },
    }
    _save_package(pkg)
    logger.info("Wrote intelligence package %s", game_id)
    return pkg


def build_from_weekly(*, use_llm: bool = True, limit: int | None = None, force: bool = False) -> dict[str, Any]:
    weekly = load_weekly()
    if not weekly or not weekly.get("cards"):
        return {"ok": False, "message": "Run weekly publish first", "built": 0}
    session = get_session_factory()()
    built = 0
    skipped = 0
    try:
        cards = weekly["cards"]
        if limit:
            cards = cards[:limit]
        for card in cards:
            game = {
                "game_id": card["game_id"],
                "league": card["league"],
                "home_team": card["home_team"],
                "away_team": card["away_team"],
                "home_name": card.get("home_name"),
                "away_name": card.get("away_name"),
                "home_espn_id": card.get("home_espn_id"),
                "away_espn_id": card.get("away_espn_id"),
                "matchup": card.get("matchup"),
                "spread_label": card.get("spread_label"),
                "home_spread": card.get("home_spread"),
                "total_line": card.get("total_line"),
                "week": card.get("week"),
            }
            before = load_package(card["game_id"])
            pkg = build_package_for_game(game, session, use_llm=use_llm, force=force)
            if before and before.get("source_set_hash") == pkg.get("source_set_hash") and not force:
                skipped += 1
            else:
                built += 1
    finally:
        session.close()
    return {
        "ok": True,
        "built": built,
        "skipped_unchanged": skipped,
        "total": built + skipped,
        "index": str(INDEX_PATH),
    }
