# 002 — NFL prediction models (a lab, not one classifier)

## Citation

Beal, R., Norman, T. J., & Ramchurn, S. D. work comparing **multiple ML classifiers** for NFL game-outcome prediction (on the order of ~1,280 games / five seasons; performance and situational features). See e.g. year-by-year comparison figure context on [ResearchGate](https://www.researchgate.net/figure/Year-by-Year-Comparison_fig1_348650836).

## Question

Does a single fancy classifier dominate simple ratings and logistic models out of sample, or should BlueChip keep a **model lab** (Elo, logistic, ridge, trees, market)?

## Dataset

Their: limited NFL seasons. Ours: nflverse PBP 1999–present; **train v0.1 on 2009+**.

## Model

They: nine classifiers, winner prediction.  
We: winner **and** margin **and** (later) \(P(M>x)\). Market always on the board.

## Features

Football performance + situational (not a single proprietary rating). Aligns with EPA diffs, rest, home — **estimated**, not hard-coded folklore.

## Train/test methodology

BlueChip: walk-forward by season, then week; no shuffled split. Sensitivity of start year 1999/2006/2009/2015/2018.

## Result

Classifier bake-offs show year-to-year variance; no substitute for a market baseline. Small game counts make headline accuracies fragile.

## Limitations

Winner accuracy ≠ betting value. Calibration and Brier are the relevant scores (see 004). 855 games (2023–25 only) is not their or our serious sample.

## What BlueChip will test

Full catalog and lab order: [011-model-lab-reproductions.md](011-model-lab-reproductions.md). Same snapshots, walk-forward, Market 0 on the board. Brier / log loss / MAE over winner-accuracy headlines. Classifier shootout is **Stage C**, after Ridge freeze.

## Implemented?

No. Stubs in `ml/pregame/`.

## Experiment ID

—
