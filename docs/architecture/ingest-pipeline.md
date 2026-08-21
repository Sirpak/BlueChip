# Data sources and ingest

Hierarchy: **structured canonical data outranks HTML**. nflverse (NFL) and CFBD (CFB) are backbone. ESPN/NCAA/Sportradar are context, validation, or future feeds.

Respect each site’s terms, robots, rate limits, and copyright. Publicly viewable ≠ unrestricted bulk scrape or redistribution.

---

## Budget (v0.1)

| Purpose | Source | Cost |
|---------|--------|-----:|
| NFL PBP, schedules, EPA/WPA, historical close | nflverse | $0 |
| CFB structured data, recruiting, lines, advanced metrics | CFBD Academic or free; later Tier 2 | $0–$5 |
| Weather | NOAA/NWS | $0 |
| News/context | Public pages, carefully cached | $0 |
| Live NFL/CFB odds | Odds API **later, free first** | $0 then maybe $30 |
| Sportradar | Trial/eval only, not a dependency | $0 |

Target: **$0–5/month**. Only CFBD Tier 2 ($5) is an early paid “yes.” Odds API paid waits.

---

## Tier A — canonical

### NFL: nflverse

Keep as backbone. Expand PBP **1999–present**. Schedules include rest, closing spreads, (sometimes) spread odds, totals, moneylines, cross-provider IDs.

Also: EPA, WPA, CPOE, down/distance, air yards, YAC, QB IDs, roof/surface/temp/wind.

**`vegas_wp`:** benchmark only. Never a feature in PURE models.

Three implementation levels (see [009](../research/009-nflfastr-replication.md)):

1. Use nflverse `epa` / `wp` columns (dashboard today).
2. Train Python XGBoost on the published features (`ml/reference/nflfastr/`) from **parquet**.
3. Our own WP/EP (LightGBM, calibration) after Level 2 matches closely enough.

Do not rebuild the nflverse raw scraper. Parquet → BCW cache → BCW features → BCW models.

Historical market:

```text
market_source = "nflverse_pfr"
market_type   = "historical_close"
```

If `spread_line` exists but spread *price* does not: **ATS vs line**, not historical EV.

### CFB: CollegeFootballData

Primary college source (games, team/player stats, drives, weather, scoreboard, advanced box, rankings, recruiting, betting lines, advanced metrics). Roster turnover → recruiting/talent/returning production/conference/SOS matter more than in the NFL.

Ingest after NFL Model Lab works; **key now**, **rows later**. `league` on every core table today.

---

## Other sources

| Source | Role | v0.1 |
|--------|------|------|
| NOAA/NWS | Forecast + observed weather, separate tables | Design in contract; fetch later |
| NCAA.com | Validate CFB box / leaderboards | Not primary pipeline |
| Sportradar | Schema inspiration, possible future commercial PBP | No dependency |
| ESPN | **Context**: availability, kickoff, venue, broadcast, injury summaries | Fetch-once cache; nflverse/CFBD remain canonical for scores |
| The Odds API | Live open/current/close, multi-book | After models exist |
| Official NFL injury report | Should outrank ESPN when we ingest it | Later |

---

## ESPN / HTML pattern

Not “save a URL as a file.” **Immutable raw-source snapshot.**

```text
data/raw/espn/2026/nfl/2026-10-11/game_401772934/
  metadata.json
  source.html.gz
  parsed.json
  sha256.txt
```

`source_registry`: url, hash, first_seen, last_fetched, status, local_path, sha256, parser_version.

```text
if cached: return snapshot
download → save_raw → parse_local → normalize → validate → upsert
```

Never: URL → BeautifulSoup → model features.

News: keep URL, headline, published_at, entities, injury/starter signals, confidence — **not** full article bodies as app content.

---

## Pipeline shape (target)

```
FETCH → RAW SNAPSHOT → PARSE → NORMALIZE → VALIDATE → UPSERT
```

```
app/ingest/
  sources/     nflverse, cfbd, nws, odds_api, espn, ncaa
  fetch/       http, cache, manifest, checksum
  parse/       espn_game, espn_news, injury, depth_chart
  normalize/   teams, players, games, identifiers
```

Reconciliation: if nflverse score ≠ ESPN score → `DATA_CONFLICT`, do not silently overwrite.

Every feed gets asserts (`home != away`, spread bounds, ids, non-negative scores).
