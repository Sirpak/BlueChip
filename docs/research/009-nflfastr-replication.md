# 009 — Reproduce nflfastR EP/WP in Python (do not wrap R)

## Citation

Baldwin, B. *nflfastR EP, WP, CP, xYAC, and xPass models*. Open Source Football, 2020-09-28.  
https://opensourcefootball.com/posts/2020-09-28-nflfastr-ep-wp-and-cp-models/

nflfastR `calculate_win_probability` / `ep_wp_calculators.R`.  
https://github.com/nflverse/nflfastR

## Question

Can BlueChip independently implement the nflfastR **in-game** expected-points and win-probability models in Python (XGBoost + the published features) closely enough that `bcw_wp` tracks nflverse `wp`?

This is **not** “can we beat the closing spread.”

## Dataset

nflverse play-by-play **parquet** (full columns). SQLite `plays` is a curated subset and currently lacks timeouts / `receive_2h_ko` / `vegas_wp`. Do not scrape NFL.com to replicate nflverse.

Filter (Baldwin / nflfastR training): regulation (`qtr <= 4`), valid down and field position, no ties, possession team known.

Target: `label = 1` iff the possession team won the game.

## Model

Family: **`BCW-nflfastR-replication-v1`**. Benchmark, not the betting model.

| Id | Question | Market features |
|----|----------|-----------------|
| `BCW-NFL-WP-XGB-v0.1` | P(posteam wins \| game state) | No |
| `BCW-NFL-WP-XGB-MARKET-v0.1` | same + decaying pregame spread | `spread_time` only |
| EP (not trained yet) | next-score 7-class → EP | No |

Published WP (non-spread) hyperparams: `max_depth=4`, `eta=0.2`, `nrounds=65`.  
v0.1 BCW default: `max_depth=5`, `learning_rate=0.025`, `n_estimators=500` (same schedule as their EP write-up). Compare both via `--preset nflfastr_wp` / `bcw_v0.1`.

## Features

Engineered (nflfastR identities):

\[
\mathrm{elapsed\_share} = (3600 - \mathrm{game\_seconds\_remaining}) / 3600
\]

\[
\mathrm{diff\_time\_ratio} = \mathrm{score\_differential} \cdot e^{4 \cdot \mathrm{elapsed\_share}}
\]

\[
\mathrm{spread\_time} = \mathrm{posteam\_spread} \cdot e^{-4 \cdot \mathrm{elapsed\_share}}
\]

`spread_line` is nflverse (positive = home favored). `posteam_spread` flips that for the possession team. `spread_time` **shrinks** the book’s influence as the clock runs.

PURE WP: receive 2nd-half KO, home, half/game seconds, `diff_time_ratio`, score differential, down, ydstogo, `yardline_100`, both timeouts. MARKET adds `spread_time` only. Never use nflverse `vegas_wp` as a feature.

## Train/test methodology

**Replication:** leave-one-season-out (whole season in one fold — no splitting a drive across folds).

**Pregame betting models (later):** chronological walk-forward. Different problem, different split.

## Result

Code exists (`ml/reference/nflfastr/`). Held-out Brier vs nflverse `wp` is filled in when the first parquet train run is logged under `data/models/` (gitignored) and an `experiment_id`.

## Limitations

In-game WP ≠ pregame \(P(M > x)\). Matching nflfastR is validation of our pipeline, not an edge. LOSO is not a betting backtest. 2023–2025 only is a thin replication sample; extend PBP years.

## What BlueChip will test

1. Feature identities vs R (unit tests).
2. Train PURE WP; Brier / log loss / AUC / ECE vs labels; MAE vs nflverse `wp`.
3. Train MARKET WP; compare to `vegas_wp` (benchmark only).
4. Then EP multinomial + EPA.
5. Then stop cloning: `BCW-WP-LGBM-v1`, calibration layer.
6. Pregame: Elo → logistic → ridge → LightGBM margin on walk-forward.

## Implemented?

Partial. Feature engine, PURE/MARKET trainers, LOSO helper, EP value mapping. EP **training** not started. No logged experiment yet.

## Experiment ID

—
