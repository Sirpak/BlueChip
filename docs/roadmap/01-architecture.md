# Architecture (target)

NFL and CFB **share an engine** (ingest → features → models → market compare → API). They do **not** have to share weights, features, or one trained model.

Hosted **Ask BlueChip** and a later ChatGPT/MCP client must share the same `app/tools/` layer. The subscription is data + models + RAG; the chat UI is not the moat. Details: [03-monetary.md](03-monetary.md).

```
              BLUECHIPWAGER
                    │
         ┌──────────┴─────────┐
         │                    │
        NFL                  CFB
         │                    │
   NFL feature builder   CFB feature builder
         │                    │
         └──────────┬─────────┘
                    │
              Model Engine
         winner / margin / distribution
                    │
              Market Engine
         odds → de-vig → probabilities
                    │
              MODEL VS MARKET
```

---

## Data sources (planned)

Canonical NFL: **nflverse**. Canonical CFB: **CFBD** (key now, rows after NFL models). Historical NFL market: `nflverse_pfr` / `historical_close`. Live books: Odds API **later**. Weather: **NWS/NOAA**, forecast ≠ observation. ESPN: cached context + injuries, not canonical scores. Details: [architecture/ingest-pipeline.md](../architecture/ingest-pipeline.md).

**855 games (2023–2025 only) is not a serious ML sample.** Ingest 1999–present (in progress); develop **2009–2022**; hold out **2023–2025** once. [04-bcw-v0.1.md](04-bcw-v0.1.md). Execution order: [02-phases.md](02-phases.md).

Never put `vegas_wp` in a PURE model. Never name a column `vegas_line`.

---

## Feature philosophy

Build **pre-game snapshots**, never season-to-date stats that include the game being predicted.

Recency: EWMA, not a magic “last 5.”

\[
\text{EWMA}_t = \alpha x_t + (1-\alpha)\text{EWMA}_{t-1}
\]

Tune \(\alpha\) out of sample **on 2009–2022 only**. Opponent-adjust. Estimate rest/bye; do not hard-code folklore.

**NFL v0.1 (frozen):** home, rest, EPA EWMA off/def/pass/rush and allowed, success/explosive diffs, Elo. Rolling stats end at the previous game. **Not in v0.1:** injuries, weather, news, fancy QB. Full list: [04-bcw-v0.1.md](04-bcw-v0.1.md).

**CFB (later):** opponent-adjusted EPA, recruiting, talent, returning/transfer production, SOS, conference, havoc, etc. Wider talent ranges; more teams.

Matchup features, not only team-level diffs: `home_pass_off` vs `away_pass_def`, and so on.

`feature_snapshots` is the table that proves: *this prediction used only information available at 11:00 Sunday.* Leakage will fake a beautiful backtest.

Name the feature **class** on every snapshot: PURE football / environmental / availability / market (and combinations). PURE must not contain spread, moneyline, or `vegas_wp`.

---

## Model lab (not “the model”)

Two tracks. **Pregame** is the product. **Live** is in-game state value. nflfastR WP is live.

```
PREGAME (v0.1)                   LIVE
Mean + HFA                       BCW WP (PURE)
Elo (reference)                  BCW WP MARKET (spread_time)
Logistic (reference)             Expected Points
Ridge μ (published)              Live cover P (later)
LightGBM / ensemble              (after v0.1)
Market 0 (close)
```

Replication of nflfastR lives under `ml/reference/nflfastr/` as `BCW-nflfastR-replication-v1`. It is a benchmark. Level 1 = use nflverse `epa`/`wp` columns. Level 2 = Python XGBoost on the same features. Level 3 = our own WP/EP. We are building Level 2 now. `vegas_wp` is never a PURE feature.

| Id | Role | Split |
|----|------|-------|
| Market 0 | Closing line (pregame) | walk-forward |
| Elo / logistic / ridge | Pregame winner / E[M] | walk-forward |
| LightGBM / distribution | Pregame P(M > x) | walk-forward |
| `BCW-NFL-WP-XGB-v0.1` | In-game P(posteam wins) | leave-one-season-out |
| `BCW-NFL-WP-XGB-MARKET-v0.1` | In-game WP + decaying spread | leave-one-season-out |

### Training vs inference vs repricing

| Activity | When | Cost |
|----------|------|------|
| Train | New week/season, feature or model change | Occasional, heavier |
| Infer | New feature snapshot | Cheap (`model.pkl` + row) |
| Reprice | User changes −7 → −6.5 | Free if we have \((\mu, \sigma)\) |

---

## Market engine (`app/markets/` — when we get there)

Small library, not buried in a notebook:

- American odds → raw implied probability
- De-vig / normalize two-sided books
- EV, hold, break-even vs fair
- Line math (spread cover at \(x\), including .5)

Negative American:

\[
P_{\text{raw}} = \frac{|odds|}{|odds|+100}
\]

Positive:

\[
P_{\text{raw}} = \frac{100}{odds+100}
\]

Then \(P^{\text{fair}}_A = p_A / (p_A + p_B)\).

v0.1 NFL close: copy `spread_line` into snapshots with `market_source="nflverse_pfr"`, `market_type="historical_close"`. Missing American price → ATS vs line, not EV.

De-vig when two-sided prices exist. Negative American \(P_{\text{raw}} = |o|/(|o|+100)\); fair \(p_A/(p_A+p_B)\).

---

## Schema direction (incremental, not a rewrite)

Add when a layer needs it. Do not block Elo on a 20-table migration.

Already present: `games`, `plays`, `team_ratings`, `odds_snapshots`, `model_predictions`, `stadiums`.

Natural next tables: `leagues`, `teams`, `feature_snapshots`, `model_registry` / `model_runs`, `prediction_market_comparisons`, `backtest_results`, then `weather_snapshots` / `injury_snapshots`.

A `league` column on `games`/`plays` is enough until CFB lands. Full `teams` entity when two sources must join.

---

## UI (later than the math)

Per game: posted line + break-even + no-vig, BlueChip \(\mu\) / win / cover-\(x\) / both edges, model table, calibration/confidence, attribution (SHAP as illustration, not causation), and a **margin density** with book vs model means and \(P(M > \text{spread})\) shaded.

Nav target: Games · NFL · College · Models · Markets · Backtests · Research · Model Lab.

---

## AWS (after the models work locally)

No SageMaker, Kubernetes, or GPUs for this stack. LightGBM/Elo/logistic run on CPU.

Progression: Windows + SQLite **now** → Docker + Postgres locally → FastAPI on ECS/Lightsail, RDS Postgres, S3 artifacts, EventBridge-scheduled ECS tasks, CloudWatch.

Always-on: API + Jinja + queries. Ephemeral: ingest, features, train, weekly backtest.
