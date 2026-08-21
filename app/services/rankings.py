"""Public polls + BCW strength rankings for the Teams desk (CONTEXT / Research Preview)."""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any
from xml.etree import ElementTree as ET
from urllib.parse import quote_plus

import httpx
import truststore
from sqlalchemy import text
from sqlalchemy.orm import Session

truststore.inject_into_ssl()

logger = logging.getLogger(__name__)

CFB_RANKINGS_URL = "https://site.web.api.espn.com/apis/site/v2/sports/football/college-football/rankings"
NFL_TEAMS_URL = "https://site.web.api.espn.com/apis/site/v2/sports/football/nfl/teams"
CFB_TEAMS_URL = "https://site.web.api.espn.com/apis/site/v2/sports/football/college-football/teams"
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
CACHE_TTL = timedelta(minutes=20)

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, application/rss+xml, application/xml, text/xml, */*",
    "Referer": "https://www.espn.com/",
}

_cache: dict[str, tuple[datetime, Any]] = {}


def _cached(key: str) -> Any | None:
    hit = _cache.get(key)
    if not hit:
        return None
    when, value = hit
    if datetime.now(timezone.utc) - when > CACHE_TTL:
        return None
    return value


def _store(key: str, value: Any) -> Any:
    _cache[key] = (datetime.now(timezone.utc), value)
    return value


def _get_json(url: str, *, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    try:
        with httpx.Client(headers=_BROWSER_HEADERS, follow_redirects=True, timeout=30.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except Exception:
        logger.exception("Rankings JSON fetch failed %s", url)
        return None


def _get_bytes(url: str) -> bytes | None:
    try:
        with httpx.Client(headers=_BROWSER_HEADERS, follow_redirects=True, timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.content
    except Exception:
        logger.exception("Rankings RSS fetch failed %s", url)
        return None


def _zscores(values: list[float | None]) -> list[float]:
    clean = [v for v in values if v is not None and math.isfinite(v)]
    if len(clean) < 2:
        return [0.0 for _ in values]
    mean = sum(clean) / len(clean)
    var = sum((v - mean) ** 2 for v in clean) / len(clean)
    std = math.sqrt(var) if var > 1e-12 else 1.0
    out: list[float] = []
    for v in values:
        if v is None or not math.isfinite(v):
            out.append(0.0)
        else:
            out.append((v - mean) / std)
    return out


def ap_top25() -> dict[str, Any]:
    """ESPN-hosted AP Top 25 (college football)."""
    key = "ap_top25"
    hit = _cached(key)
    if hit is not None:
        return hit

    payload = _get_json(CFB_RANKINGS_URL) or {}
    polls = payload.get("rankings") or []
    ap = next((p for p in polls if (p.get("type") or "").lower() == "ap"), None)
    if ap is None and polls:
        ap = polls[0]

    rows: list[dict[str, Any]] = []
    for entry in (ap or {}).get("ranks") or []:
        team = entry.get("team") or {}
        logos = team.get("logos") or []
        logo = None
        if logos and isinstance(logos[0], dict):
            logo = logos[0].get("href")
        rows.append(
            {
                "rank": entry.get("current"),
                "previous": entry.get("previous"),
                "team": team.get("abbreviation") or team.get("shortDisplayName"),
                "name": team.get("displayName") or team.get("nickname"),
                "espn_id": str(team.get("id")) if team.get("id") is not None else None,
                "record": entry.get("recordSummary"),
                "points": entry.get("points"),
                "first_place_votes": entry.get("firstPlaceVotes"),
                "trend": entry.get("trend"),
                "logo_url": logo,
                "team_url": (
                    f"https://www.espn.com/college-football/team/_/id/{team.get('id')}"
                    if team.get("id") is not None
                    else None
                ),
            }
        )

    season = (payload.get("latestSeason") or {}).get("year")
    week = (payload.get("latestWeek") or {}).get("number")
    result = {
        "league": "CFB",
        "poll": (ap or {}).get("name") or "AP Top 25",
        "poll_type": (ap or {}).get("type") or "ap",
        "season": season,
        "week": week,
        "as_of": datetime.now(timezone.utc).isoformat(),
        "source": "espn",
        "source_url": "https://www.espn.com/college-football/rankings",
        "rows": rows,
        "count": len(rows),
    }
    return _store(key, result)


def nfl_power_ranking_stories(*, limit: int = 8) -> dict[str, Any]:
    """Latest NFL power-ranking coverage (ESPN often ships this as a story, not a table API)."""
    key = f"nfl_pr_stories:{limit}"
    hit = _cached(key)
    if hit is not None:
        return hit

    queries = [
        '"NFL Power Rankings" (ESPN OR NFL.com OR CBS OR Yahoo)',
        '"NFL Future Power Rankings" ESPN',
    ]
    articles: list[dict[str, Any]] = []
    seen: set[str] = set()
    for query in queries:
        raw = _get_bytes(GOOGLE_NEWS_RSS.format(query=quote_plus(query)))
        if not raw:
            continue
        try:
            root = ET.fromstring(raw)
        except ET.ParseError:
            continue
        for node in root.findall("./channel/item"):
            title = (node.findtext("title") or "").strip()
            link = (node.findtext("link") or "").strip()
            if not title or not link or link in seen:
                continue
            if "power rank" not in title.lower():
                continue
            # Skip other sports accidentally caught
            low = title.lower()
            if any(x in low for x in ("wnba", "nba", "mlb", "nhl", "mls", "soccer")):
                continue
            seen.add(link)
            src = node.find("source")
            articles.append(
                {
                    "headline": title,
                    "url": link,
                    "published": node.findtext("pubDate"),
                    "publisher": (src.text if src is not None else None) or "web",
                }
            )
            if len(articles) >= limit:
                break
        if len(articles) >= limit:
            break

    result = {
        "league": "NFL",
        "as_of": datetime.now(timezone.utc).isoformat(),
        "note": (
            "ESPN does not expose a stable machine-readable weekly power-rankings table. "
            "We surface the latest power-ranking stories and pair them with BCW strength rankings."
        ),
        "articles": articles,
        "count": len(articles),
    }
    return _store(key, result)


def bcw_nfl_strength(session: Session, *, season_cap: int | None = None) -> dict[str, Any]:
    """Research Preview power list from snapshot Elo + SRS + net EPA (NFL only until CFB ingest).

    Historical abbrs (STL, OAK, SD, …) are folded into the current 32 franchises.
    """
    from app.ingest.identity import (
        CURRENT_NFL_TEAMS,
        canonicalize_nfl_team,
        nfl_team_name,
    )

    cap = season_cap
    if cap is None:
        cap = session.execute(
            text("SELECT MAX(season) FROM feature_snapshots WHERE feature_version = 'BCW-SNAP-v0.1'")
        ).scalar()
    if cap is None:
        return {
            "league": "NFL",
            "model": "BCW-STRENGTH-v0.x",
            "status": "empty",
            "rows": [],
            "count": 0,
            "disclaimer": "No feature snapshots available.",
        }

    # Partition by franchise, not raw historical abbr (STL/LAR, OAK/LV, SD/LAC, …).
    from app.ingest.identity import nfl_franchise_sql

    team_expr = nfl_franchise_sql("fs.home_team")
    rows_raw = session.execute(
        text(
            f"""
WITH canon AS (
  SELECT
    {team_expr} AS team,
    fs.elo_home AS elo,
    fs.srs_home AS srs,
    fs.home_off_epa AS off_epa,
    fs.home_def_epa AS def_epa,
    fs.season,
    fs.week
  FROM feature_snapshots fs
  JOIN games g ON g.game_id = fs.game_id
  WHERE fs.feature_version = 'BCW-SNAP-v0.1'
    AND g.season_type = 'REG'
    AND fs.season <= :cap
    AND fs.elo_home IS NOT NULL
),
joined AS (
  SELECT
    team, elo, srs, off_epa, def_epa, season, week,
    ROW_NUMBER() OVER (
      PARTITION BY team
      ORDER BY season DESC, week DESC
    ) AS rn
  FROM canon
)
SELECT team, elo, srs, off_epa, def_epa, season, week
FROM joined
WHERE rn = 1
"""
        ),
        {"cap": int(cap)},
    ).mappings().all()

    # Keep only the current 32 franchises (drop any unexpected codes).
    filtered = []
    for r in rows_raw:
        team = canonicalize_nfl_team(r["team"])
        if team not in CURRENT_NFL_TEAMS:
            continue
        filtered.append({**dict(r), "team": team})

    teams = [r["team"] for r in filtered]
    elo = [float(r["elo"]) if r["elo"] is not None else None for r in filtered]
    srs = [float(r["srs"]) if r["srs"] is not None else None for r in filtered]
    net = []
    for r in filtered:
        if r["off_epa"] is None or r["def_epa"] is None:
            net.append(None)
        else:
            net.append(float(r["off_epa"]) - float(r["def_epa"]))

    z_elo = _zscores(elo)
    z_srs = _zscores(srs)
    z_net = _zscores(net)
    scores = [0.55 * a + 0.25 * b + 0.20 * c for a, b, c in zip(z_elo, z_srs, z_net, strict=True)]

    ranked = sorted(
        zip(teams, scores, elo, srs, net, filtered, strict=True),
        key=lambda x: x[1],
        reverse=True,
    )
    out_rows: list[dict[str, Any]] = []
    for i, (team, score, e, s, n, raw) in enumerate(ranked, start=1):
        out_rows.append(
            {
                "rank": i,
                "team": team,
                "name": nfl_team_name(team),
                "strength": round(float(score), 3),
                "elo": round(float(e), 1) if e is not None else None,
                "srs": round(float(s), 2) if s is not None else None,
                "net_epa": round(float(n), 3) if n is not None else None,
                "as_of_season": raw["season"],
                "as_of_week": raw["week"],
            }
        )

    return {
        "league": "NFL",
        "model": "BCW-STRENGTH-v0.x",
        "status": "research_preview",
        "method": (
            "0.55·z(Elo) + 0.25·z(SRS) + 0.20·z(offEPA−defEPA) from latest REG snapshot ≤ season_cap; "
            "franchises canonicalized (STL/LA→LAR, OAK/LVR→LV, SD→LAC, JAC→JAX, WSH→WAS)"
        ),
        "season_cap": int(cap),
        "as_of": datetime.now(timezone.utc).isoformat(),
        "disclaimer": (
            "Research Preview carry-in ranking from leakage-safe snapshots — not a published betting list, "
            "not an ensemble, and not CFB (no CFB ingest yet). Analysis notes are separate from PURE Ridge freeze."
        ),
        "rows": out_rows,
        "count": len(out_rows),
    }


def espn_team_directory(league: str, *, limit: int = 400) -> dict[str, Any]:
    """NFL or CFB team directory with ESPN ids + team page URLs for news deep-links."""
    league = league.upper()
    key = f"teams:{league}:{limit}"
    hit = _cached(key)
    if hit is not None:
        return hit

    url = NFL_TEAMS_URL if league == "NFL" else CFB_TEAMS_URL
    params: dict[str, Any] = {"limit": limit}
    if league == "CFB":
        params["groups"] = 80  # FBS
    payload = _get_json(url, params=params) or {}
    teams: list[dict[str, Any]] = []
    try:
        raw_teams = payload["sports"][0]["leagues"][0]["teams"]
    except (KeyError, IndexError, TypeError):
        raw_teams = []

    for wrap in raw_teams:
        team = wrap.get("team") or wrap
        espn_id = team.get("id")
        slug = team.get("slug") or team.get("abbreviation")
        abbr = team.get("abbreviation")
        team_url = None
        for link in team.get("links") or []:
            if not isinstance(link, dict):
                continue
            if link.get("rel") == ["clubhouse"] or "team" in (link.get("href") or ""):
                if "/team/" in (link.get("href") or ""):
                    team_url = link.get("href")
                    break
        if team_url is None:
            if league == "NFL" and abbr:
                team_url = f"https://www.espn.com/nfl/team/_/name/{abbr.lower()}"
            elif espn_id is not None:
                team_url = f"https://www.espn.com/college-football/team/_/id/{espn_id}"
        logos = team.get("logos") or []
        logo = logos[0].get("href") if logos and isinstance(logos[0], dict) else None
        teams.append(
            {
                "espn_id": str(espn_id) if espn_id is not None else None,
                "abbr": abbr,
                "name": team.get("displayName"),
                "slug": slug,
                "logo_url": logo,
                "team_url": team_url,
                "league": league,
            }
        )

    teams.sort(key=lambda t: (t.get("name") or ""))
    result = {
        "league": league,
        "as_of": datetime.now(timezone.utc).isoformat(),
        "teams": teams,
        "count": len(teams),
    }
    return _store(key, result)


def rankings_bundle(session: Session) -> dict[str, Any]:
    return {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "ap_top25": ap_top25(),
        "nfl_power_ranking_stories": nfl_power_ranking_stories(),
        "bcw_nfl_strength": bcw_nfl_strength(session),
        "bcw_cfb_strength": {
            "league": "CFB",
            "status": "pending_cfb_ingest",
            "rows": [],
            "count": 0,
            "disclaimer": "BCW CFB strength rankings unlock after NFL gates pass and CFB ingest begins.",
        },
    }
