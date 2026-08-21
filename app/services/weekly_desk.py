"""Weekly featured slate: model projections + free-model AI handicapper.

Publishes top NFL Week-1 and top CFB cards for the desk. Research Preview —
not the frozen BCW-RIDGE public cover %. CLI: ``python -m ml.pregame.weekly_publish``
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import truststore
from sqlalchemy.orm import Session

from app.config import ROOT_DIR, get_settings
from app.ingest.identity import canonicalize_nfl_team
from app.markets.american_odds import break_even_prob
from app.markets.spread import p_home_cover, p_home_win, sigma_for_league
from app.services import game_news, rankings
from app.services.schedule import upcoming_for_league
from app.ingest.sources.espn import fetch_scoreboard, parse_scoreboard
from db.session import get_session_factory

truststore.inject_into_ssl()
logger = logging.getLogger(__name__)

WEEKLY_DIR = ROOT_DIR / "data" / "weekly"
WEEKLY_PATH = WEEKLY_DIR / "BCW-WEEKLY-DESK.json"
MODEL_ID = "BCW-DESK-STRENGTH-v0.x"
AI_MODEL_OPENROUTER = "openai/gpt-oss-20b:free"
AI_MODEL_GEMINI = "gemini-flash-latest"
BREAK_EVEN_110 = break_even_prob(-110)


def _elo_map(session: Session) -> dict[str, dict[str, float | None]]:
    strength = rankings.bcw_nfl_strength(session)
    return {
        r["team"]: {
            "elo": r.get("elo"),
            "srs": r.get("srs"),
            "net_epa": r.get("net_epa"),
            "strength": r.get("strength"),
        }
        for r in strength.get("rows") or []
    }


def _ap_rank_map() -> dict[str, int]:
    poll = rankings.ap_top25()
    out: dict[str, int] = {}
    for row in poll.get("rows") or []:
        espn_id = row.get("espn_id")
        abbr = (row.get("team") or "").upper()
        rank = row.get("rank")
        if rank is None:
            continue
        if espn_id:
            out[f"id:{espn_id}"] = int(rank)
        if abbr:
            out[abbr] = int(rank)
    return out


def _project_nfl(game: dict[str, Any], ratings: dict[str, dict[str, float | None]]) -> dict[str, Any]:
    home = canonicalize_nfl_team(game.get("home_team")) or game.get("home_team")
    away = canonicalize_nfl_team(game.get("away_team")) or game.get("away_team")
    rh = ratings.get(home or "", {})
    ra = ratings.get(away or "", {})
    elo_h = float(rh.get("elo") or 1500.0)
    elo_a = float(ra.get("elo") or 1500.0)
    srs_h = float(rh.get("srs") or 0.0)
    srs_a = float(ra.get("srs") or 0.0)
    # Blend Elo margin (~25 Elo ≈ 1 pt) with SRS + modest HFA.
    mu_elo = (elo_h - elo_a) / 25.0 + 2.0
    mu_srs = (srs_h - srs_a) + 2.0
    mu = 0.65 * mu_elo + 0.35 * mu_srs
    return _pack_projection(game, mu=mu, league="NFL", method="0.65·Elo/25+HFA + 0.35·(SRS+HFA)")


def _project_cfb(game: dict[str, Any], ap: dict[str, int]) -> dict[str, Any]:
    home_spread = game.get("home_spread")
    home_rank = ap.get(f"id:{game.get('home_espn_id')}") or ap.get((game.get("home_team") or "").upper())
    away_rank = ap.get(f"id:{game.get('away_espn_id')}") or ap.get((game.get("away_team") or "").upper())
    # Rank gap → margin nudge (better/lower rank ⇒ more points). Cap ±14.
    adj = 0.0
    if home_rank and away_rank:
        adj = max(-14.0, min(14.0, (away_rank - home_rank) * 0.55))
    elif home_rank:
        adj = max(0.0, (26 - home_rank) * 0.25)
    elif away_rank:
        adj = -max(0.0, (26 - away_rank) * 0.25)
    if home_spread is not None:
        market_mu = -float(home_spread)
        # Pure AP edge over the number (not blended back to market).
        mu = market_mu + adj
        method = "Market line + AP rank edge (CFB; no CFB Elo yet)"
    else:
        mu = 2.5 + adj
        method = "HFA prior + AP rank edge (no market line)"
    return _pack_projection(game, mu=mu, league="CFB", method=method)


def lean_cover_prob(proj: dict[str, Any]) -> float:
    """P(recommended side covers) — used as numeric confidence."""
    side = proj.get("model_lean") or "HOME"
    p_cover = proj.get("p_home_cover")
    if p_cover is not None:
        return float(p_cover) if side == "HOME" else 1.0 - float(p_cover)
    p_win = float(proj.get("p_home_win") or 0.5)
    return p_win if side == "HOME" else 1.0 - p_win


def _pack_projection(game: dict[str, Any], *, mu: float, league: str, method: str) -> dict[str, Any]:
    sigma = sigma_for_league(league)
    home_spread = game.get("home_spread")
    p_win = p_home_win(mu, sigma)
    p_cover = None
    edge = None
    if home_spread is not None:
        p_cover = p_home_cover(mu, float(home_spread), sigma)
        edge = float(p_cover) - BREAK_EVEN_110
    side = "HOME" if (p_cover is not None and p_cover >= 0.5) else "AWAY"
    if p_cover is None:
        side = "HOME" if p_win >= 0.5 else "AWAY"
    pick_team = game["home_team"] if side == "HOME" else game["away_team"]
    proj = {
        "model_id": MODEL_ID,
        "method": method,
        "mu_home": round(float(mu), 2),
        "sigma": sigma,
        "p_home_win": round(float(p_win), 4),
        "p_home_cover": round(float(p_cover), 4) if p_cover is not None else None,
        "edge_vs_minus_110": round(float(edge), 4) if edge is not None else None,
        "model_lean": side,
        "model_lean_team": pick_team,
        "label": "Research Preview",
        "public_probability_published": False,
    }
    conf = lean_cover_prob(proj)
    proj["confidence_pct"] = round(conf * 100.0, 1)
    return proj


def _interest_score_nfl(game: dict[str, Any], ratings: dict[str, dict[str, float | None]]) -> float:
    home = canonicalize_nfl_team(game.get("home_team")) or ""
    away = canonicalize_nfl_team(game.get("away_team")) or ""
    sh = float((ratings.get(home) or {}).get("strength") or 0.0)
    sa = float((ratings.get(away) or {}).get("strength") or 0.0)
    spread = abs(float(game["home_spread"])) if game.get("home_spread") is not None else 7.0
    # Prefer strong teams + competitive lines.
    return (sh + sa) * 10.0 - spread + (3.0 if (game.get("total_line") or 0) >= 45 else 0.0)


def _interest_score_cfb(game: dict[str, Any], ap: dict[str, int]) -> float:
    hr = ap.get(f"id:{game.get('home_espn_id')}")
    ar = ap.get(f"id:{game.get('away_espn_id')}")
    score = 0.0
    if hr:
        score += max(0, 26 - hr) * 3
    if ar:
        score += max(0, 26 - ar) * 3
    if hr and ar:
        score += 25  # ranked vs ranked
    spread = abs(float(game["home_spread"])) if game.get("home_spread") is not None else 14.0
    return score - spread * 0.5


def select_nfl_week1(limit: int = 5) -> list[dict[str, Any]]:
    year = datetime.now(timezone.utc).year
    # Prefer upcoming window; fall back to forced Week 1 REG board.
    games = upcoming_for_league("NFL", horizon_days=45)
    week1 = [g for g in games if g.get("week") == 1 and (g.get("season_type") or "REG") == "REG"]
    if len(week1) < limit:
        try:
            payload = fetch_scoreboard("NFL", year=year, week=1, season_type=2)
            week1 = parse_scoreboard(payload, league="NFL")
        except Exception:
            logger.exception("Forced NFL week 1 fetch failed")
    return week1


def select_cfb_featured(limit: int = 5) -> list[dict[str, Any]]:
    games = upcoming_for_league("CFB", horizon_days=45)
    if len(games) < limit:
        try:
            payload = fetch_scoreboard("CFB")
            games = parse_scoreboard(payload, league="CFB")
        except Exception:
            logger.exception("CFB featured fetch failed")
    return games


def _news_digest(game: dict[str, Any], *, limit: int = 5) -> list[dict[str, str]]:
    payload = game_news.matchup_news(
        league=game["league"],
        away_abbr=game["away_team"],
        home_abbr=game["home_team"],
        away_espn_id=game.get("away_espn_id"),
        home_espn_id=game.get("home_espn_id"),
        away_name=game.get("away_name"),
        home_name=game.get("home_name"),
        limit=limit,
    )
    return [
        {
            "headline": a["headline"],
            "publisher": a.get("publisher") or a.get("source") or "web",
            "bucket": a.get("bucket") or "general",
            "url": a["url"],
        }
        for a in payload.get("articles") or []
    ]


def _chat_openrouter(prompt: str, api_key: str) -> str | None:
    try:
        with httpx.Client(timeout=60.0) as client:
            r = client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://bluechipwager.local",
                    "X-Title": "BlueChipWager Weekly Desk",
                },
                json={
                    "model": AI_MODEL_OPENROUTER,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a sharp but responsible sports handicapper and TV pundit. "
                                "Be specific, cite the model numbers and headlines provided, give a clear side "
                                "recommendation (home or away vs the spread), and end with a one-line confidence "
                                "(Low/Medium/High). Do not invent injuries. Keep under 220 words."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.5,
                    "max_tokens": 450,
                },
            )
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        logger.exception("OpenRouter analysis failed (%s)", type(exc).__name__)
        return None


def _chat_gemini(prompt: str, api_key: str) -> str | None:
    try:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{AI_MODEL_GEMINI}:generateContent"
        )
        with httpx.Client(timeout=60.0) as client:
            r = client.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": api_key,
                },
                json={
                    "contents": [
                        {
                            "parts": [
                                {
                                    "text": (
                                        "You are a sharp sports handicapper. "
                                        + prompt
                                        + "\nGive a clear bet recommendation vs the spread and Low/Medium/High confidence."
                                    )
                                }
                            ]
                        }
                    ],
                    "generationConfig": {"temperature": 0.5, "maxOutputTokens": 450},
                },
            )
            if r.status_code >= 400:
                logger.warning("Gemini HTTP %s: %s", r.status_code, r.text[:200])
                if r.status_code in {429, 503}:
                    time.sleep(2.5)
                    r = client.post(
                        url,
                        headers={
                            "Content-Type": "application/json",
                            "x-goog-api-key": api_key,
                        },
                        json={
                            "contents": [
                                {
                                    "parts": [
                                        {
                                            "text": (
                                                "You are a sharp sports handicapper. "
                                                + prompt
                                                + "\nGive a clear bet recommendation vs the spread and Low/Medium/High confidence."
                                            )
                                        }
                                    ]
                                }
                            ],
                            "generationConfig": {"temperature": 0.5, "maxOutputTokens": 450},
                        },
                    )
                    if r.status_code >= 400:
                        logger.warning("Gemini retry HTTP %s", r.status_code)
            r.raise_for_status()
            data = r.json()
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts).strip()
    except Exception as exc:
        logger.exception("Gemini analysis failed (%s)", type(exc).__name__)
        return None


def _fallback_analysis(game: dict[str, Any], proj: dict[str, Any], news: list[dict[str, str]]) -> str:
    spread = game.get("spread_label") or "pick'em"
    lean = proj["model_lean_team"]
    mu = proj["mu_home"]
    conf = proj.get("confidence_pct") or round(lean_cover_prob(proj) * 100.0, 1)
    p_cover = proj.get("p_home_cover")
    bullets = "; ".join(n["headline"] for n in news[:3]) or "No fresh headlines ranked yet."
    cover_txt = f"{p_cover:.0%} model home-cover" if p_cover is not None else f"{proj['p_home_win']:.0%} home win"
    return (
        f"{game['away_team']} at {game['home_team']} opens around {spread}. "
        f"Desk strength projects home margin μ={mu:+.1f} ({cover_txt}). "
        f"News desk highlights: {bullets}. "
        f"Bet recommendation: {lean} vs the spread. "
        f"Model confidence: {conf:.1f}% (P(lean covers)). "
        f"Research Preview opinion only — not a frozen public cover %."
    )


def analyze_game(
    game: dict[str, Any],
    proj: dict[str, Any],
    news: list[dict[str, str]],
    *,
    use_llm: bool = True,
) -> dict[str, Any]:
    conf_pct = float(proj.get("confidence_pct") or round(lean_cover_prob(proj) * 100.0, 1))
    settings = get_settings()
    prompt = (
        f"Matchup: {game.get('away_name')} ({game['away_team']}) at "
        f"{game.get('home_name')} ({game['home_team']}) — {game['league']}.\n"
        f"Market: {game.get('spread_label')} · total {game.get('total_line')}\n"
        f"Model μ (home margin): {proj['mu_home']:+.2f}\n"
        f"Model P(home win): {proj['p_home_win']:.1%}\n"
        f"Model P(home cover): {proj.get('p_home_cover')}\n"
        f"Model lean: {proj['model_lean_team']} at {conf_pct:.1f}% confidence\n"
        f"Headlines:\n"
        + "\n".join(f"- [{n['bucket']}] {n['headline']} ({n['publisher']})" for n in news)
        + "\nWrite the preview + betting recommendation. State the confidence as a percentage."
    )
    provider = "fallback"
    model = "desk-template"
    text = None
    if use_llm:
        if settings.google_studio_api_key:
            text = _chat_gemini(prompt, settings.google_studio_api_key)
            if text:
                provider = "google"
                model = AI_MODEL_GEMINI
        if text is None and settings.openrouter_api_key:
            text = _chat_openrouter(prompt, settings.openrouter_api_key)
            if text:
                provider = "openrouter"
                model = AI_MODEL_OPENROUTER
    if text is None:
        text = _fallback_analysis(game, proj, news)
    return {
        "provider": provider,
        "model": model,
        "analysis": text,
        "confidence": f"{conf_pct:.1f}%",
        "confidence_pct": conf_pct,
        "recommendation_team": proj["model_lean_team"],
        "recommendation_side": proj["model_lean"],
        "disclaimer": (
            "Desk opinion for entertainment and research. Not the frozen BCW-RIDGE public probability. "
            "Bet responsibly."
        ),
    }


def build_card(
    game: dict[str, Any],
    proj: dict[str, Any],
    news: list[dict[str, str]],
    analysis: dict[str, Any],
    *,
    featured: bool = False,
) -> dict[str, Any]:
    return {
        "game_id": game["game_id"],
        "league": game["league"],
        "week": game.get("week"),
        "season": game.get("season"),
        "season_type": game.get("season_type"),
        "kickoff": game.get("kickoff"),
        "away_team": game["away_team"],
        "home_team": game["home_team"],
        "away_name": game.get("away_name"),
        "home_name": game.get("home_name"),
        "away_espn_id": game.get("away_espn_id"),
        "home_espn_id": game.get("home_espn_id"),
        "matchup": game.get("matchup"),
        "spread_label": game.get("spread_label"),
        "home_spread": game.get("home_spread"),
        "total_line": game.get("total_line"),
        "book": game.get("book"),
        "featured": featured,
        "projection": proj,
        "news": news,
        "ai": analysis,
    }


def select_cfb_week1() -> list[dict[str, Any]]:
    games = upcoming_for_league("CFB", horizon_days=45)
    week1 = [g for g in games if g.get("week") == 1 and (g.get("season_type") or "REG") == "REG"]
    if len(week1) < 20:
        try:
            year = datetime.now(timezone.utc).year
            payload = fetch_scoreboard("CFB", year=year, week=1, season_type=2)
            week1 = parse_scoreboard(payload, league="CFB")
        except Exception:
            logger.exception("Forced CFB week 1 fetch failed")
    return week1


def publish_weekly(
    *,
    nfl_n: int = 0,
    cfb_n: int = 0,
    ai_top: int = 8,
) -> dict[str, Any]:
    """Publish Week 1 desks. ``nfl_n``/``cfb_n`` of 0 = all Week 1 games for that league."""
    session = get_session_factory()()
    try:
        ratings = _elo_map(session)
        ap = _ap_rank_map()
        nfl_pool = select_nfl_week1(limit=64)
        cfb_pool = select_cfb_week1()
        if nfl_n > 0:
            nfl_pool = sorted(nfl_pool, key=lambda g: _interest_score_nfl(g, ratings), reverse=True)[:nfl_n]
        if cfb_n > 0:
            cfb_pool = sorted(cfb_pool, key=lambda g: _interest_score_cfb(g, ap), reverse=True)[:cfb_n]

        drafted: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for game in nfl_pool:
            game = {**game, "league": "NFL"}
            drafted.append((game, _project_nfl(game, ratings)))
        for game in cfb_pool:
            game = {**game, "league": "CFB"}
            drafted.append((game, _project_cfb(game, ap)))
    finally:
        session.close()

    drafted.sort(key=lambda pair: lean_cover_prob(pair[1]), reverse=True)
    ai_ids = {g["game_id"] for g, _ in drafted[: max(0, ai_top)]}

    cards: list[dict[str, Any]] = []
    for game, proj in drafted:
        use_llm = game["game_id"] in ai_ids
        news = _news_digest(game) if use_llm else []
        analysis = analyze_game(game, proj, news, use_llm=use_llm)
        cards.append(build_card(game, proj, news, analysis, featured=use_llm))
        if use_llm:
            time.sleep(1.0)

    cards.sort(
        key=lambda c: (
            0 if c.get("home_spread") is None else 1,
            float(c["projection"].get("confidence_pct") or 0),
        ),
        reverse=True,
    )
    for i, card in enumerate(cards):
        card["confidence_rank"] = i + 1

    cfb_week1 = [
        c
        for c in cards
        if c["league"] == "CFB" and c.get("week") == 1 and c.get("home_spread") is not None
    ]
    cfb_week1.sort(key=lambda c: float(c["projection"].get("confidence_pct") or 0), reverse=True)
    nfl_week1 = [c for c in cards if c["league"] == "NFL" and c.get("week") == 1]
    best_cfb = cfb_week1[0] if cfb_week1 else None
    best_any = cards[0] if cards else None

    def _best_summary(card: dict[str, Any] | None) -> dict[str, Any] | None:
        if not card:
            return None
        return {
            "game_id": card["game_id"],
            "league": card["league"],
            "matchup": card["matchup"],
            "recommendation_team": card["ai"]["recommendation_team"],
            "confidence_pct": card["projection"]["confidence_pct"],
            "spread_label": card.get("spread_label"),
        }

    payload = {
        "published_at": datetime.now(timezone.utc).isoformat(),
        "title": "Week 1 desk — all CFB + NFL with confidence %",
        "model_id": MODEL_ID,
        "label": "Research Preview",
        "public_probability_published": False,
        "counts": {
            "nfl": len(nfl_week1) if nfl_n == 0 else len([c for c in cards if c["league"] == "NFL"]),
            "cfb": len(cfb_week1) if cfb_n == 0 else len([c for c in cards if c["league"] == "CFB"]),
            "total": len(cards),
            "ai_enriched": len(ai_ids),
        },
        "highest_confidence": _best_summary(best_any),
        "highest_confidence_cfb_week1": _best_summary(best_cfb),
        "cards": cards,
        "by_game_id": {c["game_id"]: c for c in cards},
    }
    WEEKLY_DIR.mkdir(parents=True, exist_ok=True)
    WEEKLY_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info(
        "Wrote weekly desk %s (%s cards; best CFB W1 %s @ %.1f%%)",
        WEEKLY_PATH,
        len(cards),
        (best_cfb or {}).get("matchup"),
        (best_cfb or {}).get("projection", {}).get("confidence_pct") or 0,
    )
    return payload


def load_weekly() -> dict[str, Any] | None:
    if not WEEKLY_PATH.exists():
        return None
    return json.loads(WEEKLY_PATH.read_text(encoding="utf-8"))


def card_for_game(game_id: str) -> dict[str, Any] | None:
    payload = load_weekly()
    if not payload:
        return None
    return (payload.get("by_game_id") or {}).get(game_id)
