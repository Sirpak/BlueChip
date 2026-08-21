# BlueChipWager phases (plan of record)

Locked 2026-08-18. Model exists **before** the AI wrapper. Later features sit on a leakage-safe foundation.

Freeze (holdout, gates, Ridge as published \(\mu\), no ROI, no v0.1 ensemble): [04-bcw-v0.1.md](04-bcw-v0.1.md). Money / Ask / MCP: [03-monetary.md](03-monetary.md). Snapshot vs Ridge: [010](../research/010-snapshot-superset-vs-ridge.md). Lab catalog: [011](../research/011-model-lab-reproductions.md). Checkboxes: [TODO.md](TODO.md).

Do **not** jump to LightGBM, RAG, CFB ingest, Stripe, or AWS because the desk looks like a product.

---

## Immediate path (now → first real prediction)

At **step 15**, BlueChip is a prediction product. Everything after is a layer on a number we can defend.

```
 1. 1999–2025 NFL PBP          ← done
 2. nflverse schedules         ← done
 3. Data Contract v0.1         ← schema/identity/Market 0 done; keep filling as years land
 4. Pregame snapshot builder   ← done (`BCW-SNAP-v0.1`, 7,276 rows)
 5. Mean + HFA                 ← done (on snapshots)
 6. Elo                        ← done (on snapshots)
 7. SRS                        ← done (on snapshots)
 8. Opponent-adjusted EPA      ← done (on snapshots)
 9. Logistic                   ← next
10. Ridge margin
11. Walk-forward 2009–2022
12. Freeze (features, α, λ, metrics)
13. Sacred 2023–2025 (once) + start-year A–D
14. BCW-RIDGE-v0.1
15. Put μ / P(cover) on the upcoming-games page
```

---

## Phase 0 — Current state

Have: FastAPI; Vite desk + Jinja `/legacy`; SQLite; nflverse PBP **1999–2025**; nflverse **schedules** (kickoff, rest, moneylines); ESPN slate; EPA/standings views; Stage 1 Stern/de-vig calculator; Data Contract identity + Market 0; WP trainer (metrics run still open); UI shells.

**Do not have:** a pregame model that emits a defensible number before kickoff and proves OOS performance.

That remains Priority #1.

---

## Phase 1 — Data foundation  `[~]`

Canonical NFL research DB. Every feature reconstructible as known before kickoff.

| Step | Status |
|------|--------|
| 1.1 PBP 1999–present | `[x]` 1999–2025 upserted (~9 min). Next: schedules. |
| 1.2 nflverse **schedules** (kickoff, rest, scores, spread/total/ML when present) | `[x]` `python -m app.ingest --schedules --from-season 1999 --to-season 2025`. PBP scores win on conflict (`ingest_conflicts`). |
| 1.3 Market 0 snapshots `nflverse_pfr` / `historical_close` | `[x]` for ingested seasons; re-backfill as years land. Close is **not** a PURE feature. ~86% of median-margin variation ([PMC10306238](https://pmc.ncbi.nlm.nih.gov/articles/PMC10306238/)). |
| 1.4 Data Contract entities | `[x]` league, team, player, game, play, odds_snapshots, **feature_snapshots**. `[ ]` Model, Experiment, Prediction, BacktestRun as first-class tables. |
| 1.5 `known_at < kickoff` | `[x]` `known_at_max = kickoff − 1s` on `BCW-SNAP-v0.1`; leakage tests |
| 1.6 External IDs | `[x]` team/player from PBP; `game_external_ids` from schedules (nflverse / espn / pfr / gsis) |
| 1.7 Quality gates | `[x]` contract_checks (home≠away, ids, duplicates, spread range). Conflicts: flag, don’t clobber. |

Spec: [v0.1-data-contract.md](../data-dictionary/v0.1-data-contract.md).

---

## Phase 2 — Pregame snapshot engine  `[x]`

`python -m ml.features.build` writes **7,276** `BCW-SNAP-v0.1` rows. One row per game using **only prior games**. No current-game EPA, no `vegas_wp`. Rolling EPA is `shift(1)` EWMA α=0.20 (not tuned on 2023–2025). Recency last-3 / last-5 / s2d / std live in `extras_json`. `market_spread` is a **target/benchmark** column, not a PURE input.

Ridge freeze still selects a subset on 2009–2022 only ([010](../research/010-snapshot-superset-vs-ridge.md)). Sacks are not in the curated `plays` columns yet.

---

## Phase 3 — Baseline lab  `[x]` columns / `[ ]` leaderboard

Written onto snapshots in the same walk: expanding REG `hfa_prior` (default 2.0 until n=80), Elo K=20 / HFA=55 / 25% season regression (pre-update), Massey-style mean-centered SRS. Development-window margin MAE (2009–2022, n=3,775): HFA **11.32**, SRS **11.18**. Everything else must still beat HFA on the real leaderboard (Brier / log loss / ATS vs close — not this smoke MAE).

---

## Phase 4 — Opponent-adjusted strength  `[x]`

Ridge \(\lambda=5\): \(\mathrm{off\_epa} \approx \mathrm{Off}_i + \mathrm{Def}_j + \mathrm{HFA}\cdot\mathrm{home}\). Refit when `game_date` changes (Thursday can inform Sunday). Off/def are **EPA/play**, not points — Ridge v0.1 maps them to \(\mu\). Later ST and QB. FPI is a design reference, not a feature ([ESPN FPI](https://www.espn.com/nfl/story/_/id/13539941/how-espn-nfl-football-power-index-was-developed-implemented)).

---

## Phase 5 — Logistic win  `[ ]`

`BCW-LOGISTIC-v0.1`: \(P(\text{home win})=\sigma(\beta_0+\beta^\top x)\). Pregame rolling \(x\): Elo/SRS/adj-EPA diffs, rest, home, success-rate. Brier, log loss, calibration — not a 63% headline ([arXiv:1601.04302](https://arxiv.org/abs/1601.04302)).

---

## Phase 6 — Launch model  `[ ]`

`BCW-RIDGE-v0.1`: \(M=\) home−away. Interpretable \(\beta_j x_j\). On 2009–2022 compare raw vs opponent-adjusted EPA; freeze **one** `feature_version`.

---

## Phase 7 — Probability conversion  `[x]` engine / `[ ]` wired to Ridge

Existing `app/markets` Stern layer. \(\mu \to P(\text{win}), P(\text{cover}), P(\text{push})\), interval. v0.1: validated \(\sigma\) or empirical residual — not a final uncertainty model.

---

## Phase 8 — Walk-forward  `[ ]`

Develop **2009–2022**, season folds (train through \(t-1\), predict \(t\)). No shuffle. Win: Brier, log loss, AUC, calibration. Margin: MAE, RMSE, residuals. Market: ATS vs close, n, interval. **No ROI.**

---

## Phase 9 — Sacred holdout  `[ ]`

After freeze of features / α / λ / design / metrics: open **2023–2025 once**. Start-year A–D on that same pass. Do not retune from holdout.

---

## Phase 10 — Five ship gates  `[ ]`

Leakage, baseline, calibration, uncertainty + `prediction_at` + model id, n. Public % only if all pass. Simple well-calibrated models can beat fancy ones ([arXiv:1704.00197](https://arxiv.org/abs/1704.00197)).

---

## Phase 11 — First real game page  `[ ]`  ← “real product”

Market vs Ridge \(\mu\), win/cover/break-even, model id, `prediction_at`, train/holdout windows. Comparison: Elo / SRS / logistic / Ridge (**show**, don’t average). Why: \(\beta_j x_j\).

---

## Phase 12 — Dashboard v1  `[ ]`

This week’s board, power ratings, model lab leaderboard, calibration charts, research page per `experiment_id` (math, years, market-in? Y/N, paper). UI shells exist; they bind to **versioned predictions**, not Stern+jitter.

---

## Phase 13 — LightGBM  `[ ]` after Ridge is established

`BCW-LGBM-WIN-v1` / `MARGIN-v1`. Smaller NFL \(X\) than CFBD’s 714. Same folds as Ridge. Keep Ridge in production if Brier/MAE/calibration don’t improve stably ([CFBD GBDT](https://blog.collegefootballdata.com/predicting-spreads-gbdt/)).

---

## Phase 14 — Probabilistic margin  `[ ]`

NGBoost, quantile LGBM, empirical residual, Student-t. \(M \sim D(\mu,\sigma,\ldots)\). Price any line without retraining. Distribution/quantiles, not median-only ([PMC10306238](https://pmc.ncbi.nlm.nih.gov/articles/PMC10306238/)).

---

## Phase 15 — Key numbers  `[ ]`

Mass at 3 / 6 / 7 / 10 / 14. Line-specific \(P(\text{cover}/\text{push}/\text{fail})\) especially −6.5 / −7 / −7.5.

---

## Phase 16 — QB  `[ ]`

Starter vs replacement; ablation PURE vs PURE+QB. Own `known_at`. Not v0.1 unless starter history is clean.

---

## Phase 17 — FPI-style context  `[ ]`

Rest, short week, bye, travel, timezone, altitude, seasonal. **Estimate**; do not hard-code ESPN point values.

---

## Phase 18 — Special teams  `[ ]`

FG / punt / kickoff / return EPA → OFF / DEF / ST / OVR power index.

---

## Phase 19 — Live WP/EP lab  `[~]` parallel, not the launch model

Python nflfastR-style EP/WP vs nflverse. First metrics run still open. Do not retune pregame v0.1 from WP.

---

## Phase 20 — CFB data  `[ ]` after NFL gates

CFBD. Same entities + recruiting, talent, returning production, rankings, QB experience, coach, FBS/FCS. Key may exist now; **no rows** until then.

---

## Phase 21 — CFB model lab  `[ ]`

Reuse Elo/SRS/logistic/Ridge/LGBM/NGBoost. Preseason prior that fades: \(R_t = w_t(\text{current})+(1-w_t)(\text{prior})\).

---

## Phase 22 — Live odds  `[ ]`

Odds API later. Open / current / T−24h / T−6h / T−1h / close. Movement, best price, consensus, CLV. Not v0.1.

---

## Phase 23 — Weather & availability  `[ ]`

NWS **forecast** ≠ observation. Official injuries, expected starters, depth. Timestamped.

---

## Phase 24 — News / research ingest  `[ ]`

Fetch-once → raw snapshot → parser → structured events. URL, `retrieved_at`, entities. RAG context later. Not full article bodies as product content.

---

## Phase 25 — Ask BlueChip  `[ ]`

Intent → SQL / model tools / vector / LLM → answer **+ citations**. GPT interrogates BlueChip; it does not invent \(\mu\). Canned Ask UI today is not this.

---

## Phase 26 — Subscription  `[ ]`

Free / Pro **$14.99** / Research **$29.99**. Meter credits, never tokens. [03-monetary.md](03-monetary.md).

---

## Phase 27 — ChatGPT / MCP  `[ ]`

Website stays independent. MCP is another client on the same tools.

---

## Phase 28 — AWS  `[ ]` after laptop product works

Route53 → CloudFront → FastAPI → RDS → S3. EventBridge → Fargate ingest/features/train/predict. No always-on GPU box, no Kubernetes.

---

## Phase 29 — Registry / ops  `[ ]`

`model_id`, versions, git, train window, `prediction_at`, cutoff, metrics, artifact URI. Drift: Brier/MAE/calibration/features/disagreement by week.

---

## Phase 30 — Season simulation  `[ ]`

Once game \(P(\text{win})\) is trustworthy: Monte Carlo expected wins, division/playoff/championship %.

---

## End state (five questions per game)

1. Who is stronger? Power rating.  
2. What is the number? Projected margin.  
3. Probability? Win / cover / push / \(F_M\).  
4. vs market? Close, break-even, no-vig, disagreement.  
5. Why? Components, not an LLM story.

Ask BlueChip is the conversational layer over that, last among the three launches: **Model → Product → CFB**.
