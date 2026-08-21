# 003 — CFB prediction and spread difficulty

## Citation

CollegeFootballData / Rad Sports Analytics: [Using machine learning to predict game outcomes and spreads](https://blog.collegefootballdata.com/predicting-spreads-gbdt/). Historical experiment: large feature matrix (~17k games, hundreds of features), LightGBM/NGBoost. Reported test AUC ~0.87, ~76% winner accuracy; margin RMSE ~15.72; 2020 subset ~75% winners. **Spread harder than winner.**

## Question

Can CFB structured (recruiting, talent, returning production, rankings, opponent-adjusted stats) support a second BlueChip league using the **same engine** but different features?

## Dataset

CFBD games + recruiting + rankings + analytics + historical lines. NCAA.com only as validation. Ingest **after** NFL framework; key can exist now.

## Model

Gradient boosting (winner) and NGBoost-style probabilistic margin. We copy the idea (distribution over \(M\)), not their exact pipeline.

## Features

Location, recruiting, returning production, rankings, talent, pregame spreads (those last are **MARKET**, not PURE), historical team and opponent stats.

## Train/test methodology

The blog post’s split is theirs. We will walk-forward and hold out a sacred CFB window once ingest exists. Do not retune on that holdout.

## Result

Useful as a **blueprint**, not evidence a 2026 betting strategy is profitable. Confirms winner is easier than exact margin.

## Limitations

Feature count (700+) overfits easily. Pregame spread in the feature list makes it a market-aware model — we must flag `market_features=true`.

## What BlueChip will test

Same Model Lab on CFB **after** NFL v0.1. Separate PURE vs +MARKET. Compare CFBD historical close as Market 0.

## Implemented?

No (no CFB rows yet).

## Experiment ID

—
