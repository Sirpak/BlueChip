"""Multi-source matchup news for desk context (not a PURE model feature).

Sources (no paid key required):
- ESPN team news API (structured)
- Google News RSS (aggregates FOX, Yahoo, CBS, AP, team sites, etc.)

Optional later: NEWS_API_KEY / Bing for broader web search.
Ordering is heuristic keyword + recency — not a guarantee of predictive value.
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import quote_plus, urlparse

import httpx
import truststore

truststore.inject_into_ssl()

logger = logging.getLogger(__name__)

ESPN_NEWS_URL = "https://site.web.api.espn.com/apis/site/v2/sports/football/{sport}/news"
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
SPORTS = {"NFL": "nfl", "CFB": "college-football"}
CACHE_TTL = timedelta(minutes=15)

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, application/rss+xml, application/xml, text/xml, */*",
    "Referer": "https://www.espn.com/",
}

_BUCKET_PATTERNS: list[tuple[str, int, re.Pattern[str]]] = [
    (
        "availability",
        100,
        re.compile(
            r"\b(injur(?:y|ies)|questionable|doubtful|out for|ruled out|ir\b|pup\b|"
            r"suspended|inactive|status|qb\b|quarterback|starting|starter|"
            r"depth chart|transfer portal|waived|signed|traded)\b",
            re.I,
        ),
    ),
    (
        "analysis",
        70,
        re.compile(
            r"\b(preview|keys to|breakdown|film|matchup|spread|odds|pick(?:s)?|"
            r"prediction|power ranking|how .+ can win|what to watch|scouting|"
            r"betting|line move)\b",
            re.I,
        ),
    ),
    (
        "update",
        40,
        re.compile(
            r"\b(latest|update|intel|training camp|practice|report|roster|"
            r"cut.?down|final 53|news|buzz)\b",
            re.I,
        ),
    ),
]

_STOP = frozenset(
    {
        "the",
        "and",
        "for",
        "vs",
        "at",
        "of",
        "st",
        "state",
        "university",
        "football",
        "team",
    }
)

_cache: dict[str, tuple[datetime, Any]] = {}


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_rfc822(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError, IndexError):
        return None


def _bucket_and_boost(text: str) -> tuple[str, int]:
    for name, boost, pat in _BUCKET_PATTERNS:
        if pat.search(text):
            return name, boost
    return "general", 10


def _recency_boost(published: datetime | None, now: datetime) -> int:
    if published is None:
        return 0
    hours = max((now - published).total_seconds() / 3600.0, 0.0)
    if hours <= 24:
        return 35
    if hours <= 72:
        return 20
    if hours <= 168:
        return 10
    return 0


def _token_hits(blob: str, tokens: list[str]) -> int:
    return sum(1 for t in tokens if t and re.search(rf"\b{re.escape(t)}\b", blob, re.I))


def _headline_key(headline: str) -> str:
    # Strip trailing " - Publisher" for dedupe across Google vs ESPN.
    base = re.sub(r"\s+[-–|]\s+[^-–|]{2,40}$", "", headline.strip())
    return re.sub(r"\W+", " ", base.lower()).strip()


def _publisher_from_headline(headline: str, fallback: str | None = None) -> str:
    m = re.search(r"\s+[-–]\s+([^-–]{2,40})$", headline.strip())
    if m:
        return m.group(1).strip()
    return fallback or "web"


def _score_item(
    *,
    headline: str,
    description: str | None,
    published: datetime | None,
    now: datetime,
    tokens: list[str],
) -> tuple[str, int]:
    blob = f"{headline} {description or ''}"
    bucket, boost = _bucket_and_boost(blob)
    score = boost + _recency_boost(published, now)
    hits = _token_hits(blob, tokens)
    if hits:
        score += 25 * min(hits, 4)
        if bucket == "general":
            bucket = "matchup"
    return bucket, score


def _name_tokens(*parts: str | None) -> list[str]:
    out: list[str] = []
    for part in parts:
        if not part:
            continue
        for tok in re.split(r"\W+", part):
            if len(tok) > 2 and tok.lower() not in _STOP:
                out.append(tok)
    # Preserve order, unique case-insensitive
    seen: set[str] = set()
    uniq: list[str] = []
    for t in out:
        k = t.lower()
        if k in seen:
            continue
        seen.add(k)
        uniq.append(t)
    return uniq


def _fetch_json(url: str, *, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    try:
        with httpx.Client(headers=_BROWSER_HEADERS, follow_redirects=True, timeout=30.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except Exception:
        logger.exception("News JSON fetch failed %s", url)
        return None


def _fetch_bytes(url: str) -> bytes | None:
    try:
        with httpx.Client(headers=_BROWSER_HEADERS, follow_redirects=True, timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.content
    except Exception:
        logger.exception("News RSS fetch failed %s", url)
        return None


def fetch_espn_team_news(league: str, espn_team_id: str, *, limit: int = 12) -> list[dict[str, Any]]:
    league = league.upper()
    sport = SPORTS.get(league)
    if not sport or not espn_team_id:
        return []
    cache_key = f"espn:{league}:{espn_team_id}:{limit}"
    now = datetime.now(timezone.utc)
    hit = _cache.get(cache_key)
    if hit and now - hit[0] < CACHE_TTL:
        return hit[1]

    payload = _fetch_json(
        ESPN_NEWS_URL.format(sport=sport),
        params={"team": espn_team_id, "limit": limit},
    )
    articles = (payload or {}).get("articles") or []
    _cache[cache_key] = (now, articles)
    return articles


def fetch_google_news(query: str, *, limit: int = 20) -> list[dict[str, Any]]:
    cache_key = f"gnews:{query}:{limit}"
    now = datetime.now(timezone.utc)
    hit = _cache.get(cache_key)
    if hit and now - hit[0] < CACHE_TTL:
        return hit[1]

    url = GOOGLE_NEWS_RSS.format(query=quote_plus(query))
    raw = _fetch_bytes(url)
    if not raw:
        return []
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        logger.exception("Google News RSS parse failed")
        return []

    items: list[dict[str, Any]] = []
    for node in root.findall("./channel/item")[:limit]:
        title = (node.findtext("title") or "").strip()
        link = (node.findtext("link") or "").strip()
        if not title or not link:
            continue
        source_el = node.find("source")
        publisher = (source_el.text or "").strip() if source_el is not None else None
        items.append(
            {
                "headline": title,
                "description": (node.findtext("description") or "").strip() or None,
                "url": link,
                "published": node.findtext("pubDate"),
                "publisher": publisher or _publisher_from_headline(title),
            }
        )
    _cache[cache_key] = (now, items)
    return items


def _from_espn(
    article: dict[str, Any],
    *,
    team_side: str,
    team_abbr: str,
    now: datetime,
    tokens: list[str],
) -> dict[str, Any] | None:
    headline = (article.get("headline") or "").strip()
    if not headline:
        return None
    links = article.get("links") or {}
    url = ((links.get("web") or {}).get("href")) if isinstance(links, dict) else None
    if not url:
        return None
    description = (article.get("description") or "").strip() or None
    published = _parse_iso(article.get("published"))
    bucket, score = _score_item(
        headline=headline,
        description=description,
        published=published,
        now=now,
        tokens=tokens,
    )
    images = article.get("images") or []
    image_url = images[0].get("url") if images and isinstance(images[0], dict) else None
    return {
        "id": f"espn:{article.get('id') or url}",
        "headline": headline,
        "description": description,
        "url": str(url),
        "published": published.isoformat() if published else None,
        "source": "espn",
        "publisher": "ESPN",
        "team_side": team_side,
        "team_abbr": team_abbr,
        "bucket": bucket,
        "relevance_score": score,
        "image_url": image_url,
        "context_only": True,
    }


def _from_google(
    article: dict[str, Any],
    *,
    team_side: str,
    team_abbr: str,
    now: datetime,
    tokens: list[str],
) -> dict[str, Any] | None:
    headline = (article.get("headline") or "").strip()
    url = (article.get("url") or "").strip()
    if not headline or not url:
        return None
    description = article.get("description")
    # Strip HTML crumbs Google sometimes embeds in description.
    if description:
        description = re.sub(r"<[^>]+>", " ", description)
        description = re.sub(r"\s+", " ", description).strip() or None
    published = _parse_rfc822(article.get("published"))
    bucket, score = _score_item(
        headline=headline,
        description=description,
        published=published,
        now=now,
        tokens=tokens,
    )
    publisher = article.get("publisher") or _publisher_from_headline(headline, "Google News")
    return {
        "id": f"gnews:{_headline_key(headline)}:{urlparse(url).path[-24:]}",
        "headline": headline,
        "description": description,
        "url": url,
        "published": published.isoformat() if published else None,
        "source": "google_news",
        "publisher": publisher,
        "team_side": team_side,
        "team_abbr": team_abbr,
        "bucket": bucket,
        "relevance_score": score,
        "image_url": None,
        "context_only": True,
    }


def _league_query_bits(league: str) -> str:
    if league.upper() == "CFB":
        return '(college football OR NCAA OR FBS)'
    return "NFL"


def matchup_news(
    *,
    league: str,
    away_abbr: str,
    home_abbr: str,
    away_espn_id: str | None,
    home_espn_id: str | None,
    away_name: str | None = None,
    home_name: str | None = None,
    limit: int = 12,
) -> dict[str, Any]:
    """Fetch ESPN + Google News, dedupe, and rank for the matchup desk."""
    now = datetime.now(timezone.utc)
    tokens = _name_tokens(away_abbr, home_abbr, away_name, home_name)
    away_label = away_name or away_abbr
    home_label = home_name or home_abbr
    sport_q = _league_query_bits(league)

    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_headlines: set[str] = set()

    def _add(item: dict[str, Any] | None) -> None:
        if item is None:
            return
        hk = _headline_key(item["headline"])
        if item["id"] in seen_ids or (hk and hk in seen_headlines):
            return
        seen_ids.add(item["id"])
        if hk:
            seen_headlines.add(hk)
        rows.append(item)

    for side, abbr, espn_id in (
        ("away", away_abbr, away_espn_id),
        ("home", home_abbr, home_espn_id),
    ):
        if not espn_id:
            continue
        for raw in fetch_espn_team_news(league, espn_id, limit=10):
            _add(
                _from_espn(
                    raw,
                    team_side=side,
                    team_abbr=abbr,
                    now=now,
                    tokens=tokens,
                )
            )

    queries = [
        (
            "matchup",
            f'"{away_label}" "{home_label}" {sport_q} (preview OR injury OR odds OR matchup OR prediction)',
        ),
        ("away", f'"{away_label}" {sport_q} (injury OR preview OR roster OR QB OR odds)'),
        ("home", f'"{home_label}" {sport_q} (injury OR preview OR roster OR QB OR odds)'),
    ]
    for side, query in queries:
        team_abbr = away_abbr if side == "away" else home_abbr if side == "home" else "both"
        for raw in fetch_google_news(query, limit=12):
            _add(
                _from_google(
                    raw,
                    team_side=side if side != "matchup" else "both",
                    team_abbr=team_abbr,
                    now=now,
                    tokens=tokens,
                )
            )

    def _published_ts(value: str | None) -> float:
        if not value:
            return 0.0
        try:
            return datetime.fromisoformat(value).timestamp()
        except ValueError:
            return 0.0

    rows.sort(key=lambda r: (-int(r["relevance_score"]), -_published_ts(r.get("published"))))
    bucket_order = ("availability", "analysis", "matchup", "update", "general")
    by_bucket: dict[str, list[dict[str, Any]]] = {b: [] for b in bucket_order}
    for row in rows:
        by_bucket.setdefault(row["bucket"], []).append(row)

    sources = sorted({r["source"] for r in rows[:limit]})
    publishers = sorted({r["publisher"] for r in rows[:limit] if r.get("publisher")})

    return {
        "source": "+".join(sources) if sources else "none",
        "sources": sources,
        "publishers": publishers,
        "as_of": now.isoformat(),
        "disclaimer": (
            "CONTEXT only — multi-source desk news (ESPN + Google News aggregate), "
            "not a BCW-RIDGE PURE feature. Ordering is heuristic "
            "(availability / analysis / matchup / recency)."
        ),
        "articles": rows[:limit],
        "by_bucket": {k: v[:6] for k, v in by_bucket.items() if v},
        "count": len(rows[:limit]),
    }
