# 010 — Snapshot superset vs BCW-RIDGE-v0.1 (FPI/SP+/SRS)

Locked 2026-08-18. Does **not** reopen [04-bcw-v0.1.md](../roadmap/04-bcw-v0.1.md). ESPN FPI / SP+ are **design references**, not data sources or Ridge features.

## Citation

- ESPN, *A Guide to NFL FPI* — EPA/play units (off/def/ST), rest, travel, altitude; rating in points vs average; season simulation. https://www.espn.com/blog/statsinfo/post/_/id/123048/a-guide-to-nfl-fpi
- ESPN, *How ESPN's NFL Football Power Index was developed* — EPA foundation, trash-time and opponent adjustment, QB when backup. https://www.espn.com/nfl/story/_/id/13539941/how-espn-nfl-football-power-index-was-developed-implemented
- ESPN Analytics (2022 FPI overhaul) — preseason FPI **untethered from betting markets**; predictive QB + non-QB ratings; run/pass unit ratings; pass rate over expected (PROE) in the game model. https://www.espn.com/nfl/story/_/id/33927352/nfl-season-projections-2022-win-loss-records-playoff-super-bowl-chances-football-power-index
- ESPN college FPI — offensive/defensive/ST components, opponent-adjusted EPA, Bayesian in-season update; preseason priors (returning talent, recruiting, coaching, QB experience) fade as games accumulate.
- Bill Connelly, SP+ — tempo- and opponent-adjusted efficiency; separate offense/defense/ST; preseason prior fades. Predictive, not just descriptive.
- Pro-Football-Reference Simple Rating System — point differential + strength of schedule; 0 = average; rating difference ≈ neutral-field spread. https://www.pro-football-reference.com/about/glossary.htm

Peer-reviewed EPA / market-as-prior: [008](008-margin-probability-foundations.md). Leakage clocks: [007](007-data-leakage.md).

## Question

Can BlueChip **store** a rich, leakage-safe pregame feature table (FPI/SP+-class families) while the **published** v0.1 model stays a small, explainable PURE Ridge?

## Distinction (locked)

> **Snapshot features available ≠ features used by BCW-v0.1.**

Collect many honest pregame columns. Train `BCW-RIDGE-v0.1` on the **frozen** 04 list only (~15–25 columns). Everything else is for **controlled ablations after** 1999+ ingest and time-safe snapshots exist. Looking at 2023–2025 and then stuffing FPI-ish inputs into Ridge **voids the holdout**.

Do **not** expand the frozen Ridge spec because ESPN FPI uses more inputs.

## Launch sequence

SRS and **opponent-adjusted EPA** run **before** Ridge freeze (lab order: [011](011-model-lab-reproductions.md)). Holdout and published Ridge \(\mu\) stay locked.

```
1999–present nflverse PBP
        ↓
nflverse schedules (rest / extra close fields)
        ↓
Data Contract identity + Market 0 (already in schema)
        ↓
Pregame snapshot builder (rich table, era, known_at)
        ↓
Develop 2009–2022 only
        ↓
HFA → Elo → SRS → opponent-adjusted EPA → logistic → Ridge μ
        ↓
Walk-forward inside 2009–2022
        ↓
Freeze (including raw vs adj EPA for Ridge — this window only)
        ↓
2023–2025 sacred holdout (once)
        ↓
BCW-RIDGE-v0.1
```

SRS is a **baseline model**, not an ensemble member. Opponent-adjusted EPA is a lab model **and** a candidate Ridge feature family decided on 2009–2022. LightGBM / NGBoost / Power Index (ST+QB+travel) wait until after freeze.

## First modeling question

How much do **HFA / Elo / SRS / opponent-adjusted EPA / logistic / small Ridge** add vs Market 0 on 2009–2022?

ST, QB, PROE, pace, travel, LightGBM, NGBoost are **after** that freeze ([011](011-model-lab-reproductions.md) stages C–D).

## Snapshot families (store; do not dump into Ridge)

Identity / time: `game_id`, league, season, week, kickoff, `known_at`, `feature_version`, **era**.

Ratings (computed, still pregame): Elo, **SRS**, diffs.

Offense / defense: off/def EPA/play, pass/rush EPA and allowed, success rates, early/late down EPA, dropback EPA.

Style: PROE, pace (seconds/snap, plays/game, neutral-situation pace).

Explosiveness: explosive pass/run rates and allowed (fixed yard threshold, versioned).

Negative plays: sack rates, turnover/INT/fumble rates (**regress**; high variance).

Special teams: punt / kickoff / FG / return EPA → `st_epa`.

Context: HFA, rest, short week, bye. Travel / altitude = later CONTEXT, not v0.1 Ridge.

Stability: EPA/margin/success σ (week-to-week). Useful later for **width** of \(M\), not v0.1 \(\mu\).

Targets (after the game only): home margin, home win, market close, covered.

Recency: persist enough to derive season-to-date, last-3, last-5, EWMA \(\alpha \in \{0.10,0.20,0.30,0.40\}\) — **tune \(\alpha\) on 2009–2022**; do not put all correlated versions into Ridge.

Garbage-time: flag `competitive_play` / `garbage_time`; ablation all-play EPA vs competitive EPA.

QB table (later, own `known_at`): starter id, EPA/dropback, CPOE, sack/INT, rolling windows. **Not v0.1 unless starter history is clean.** Team passing EPA is not a QB model.

Play-style matchups (later): pass-off vs pass-def, rush-off vs rush-def, then shotgun / early-down / short-yardage / red zone. “Why” copy, not launch Ridge.

## Ablation ladder (each `feature_version` / `experiment_id`)

**Before freeze (2009–2022):** HFA, Elo, SRS, opp-adj EPA, logistic, Ridge(raw EPA) vs Ridge(adj EPA).

**After v0.1 holdout pass:**

| Id | Adds |
|----|------|
| BCW-v0.2 | + QB |
| BCW-POWER | FPI-style Off−Def+ST + estimated rest/travel (not ESPN FPI as a feature) |
| BCW-v0.4 | + availability |
| BCW-v0.5 | + environmental (forecast, not observation) |
| BCW-MARKET-v1 | PURE + market (never labeled PURE) |
| Stage C–E | LightGBM, NGBoost, \(F_M\), consensus |

Do not add ESPN FPI, close/`vegas_wp`, injuries, weather, news, or LightGBM to anything labeled PURE or to Ridge **before** the freeze.

## Not before Ridge v0.1

ESPN FPI as a feature, close/`vegas_wp` in PURE, injuries, weather, news sentiment, coaching narratives, referees, social, “sharp money,” public %, LightGBM, CFB Bayesian preseason blend.

College FPI / SP+ prior-fade

\[
\text{Rating}_t = w_t(\text{current season}) + (1-w_t)(\text{preseason prior}),\quad w_t \uparrow
\]

is the **BCW-CFB** sketch after NFL gates. Not now. No CFB ingest.

## Product outputs (later UI; not a reason to expand Ridge)

Five questions: who is stronger (power rating) → what is the number (\(\mu\)) → probability (win/cover/push) → do models agree (dispersion, not a fake ensemble) → why (Ridge \(\beta_j x_j\)). PURE vs Market vs later hybrid, labeled. Similar-games and season Monte Carlo wait on \(P(\text{win})\) per game.

## Dataset

nflverse PBP **parquet** (full columns) + schedules for rest; SQLite identity / Market 0. Snapshot builder may read parquet so curated `plays` need not hold every FPI-class field on day one. Re-upsert extra play columns from cache when needed (`sack`, `cpoe`, `fumble_lost`, `xpass` / `pass_oe`, ST play types).

## Train/test methodology

Walk-forward **inside 2009–2022**. Holdout 2023–2025 once. Ablations compare OOS Brier / log loss / MAE / ATS vs close — **no ROI**. Automated `known_at < kickoff`; no current-game EPA; no `vegas_wp` in PURE.

## Result

—

## Limitations

FPI/SP+ methodology is public description, not a spec we can copy blindly. Iterative opponent adjustment is its own leakage surface (must use **prior** opponent strength only). Turnover and ST samples are noisy. Power-rating UI is not Model launch.

## What BlueChip will test

1. Ingest 1999–present + schedules.
2. Snapshot table **superset** + `feature_version` that **selects** the 04 list for Ridge.
3. HFA, Elo, **SRS**, **opponent-adjusted EPA**, logistic, Ridge (raw vs adj EPA on 2009–2022).
4. After freeze + one holdout pass: LightGBM, NGBoost, \(F_M\), Power Index, then the rest of [011](011-model-lab-reproductions.md).

## Implemented?

No (spec). Schema identity + Market 0 exist; `feature_snapshots` empty.

## Experiment ID

—
