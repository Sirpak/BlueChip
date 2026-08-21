# 004 — Probability calibration vs classification accuracy

## Citation

Work on ML for sports betting arguing **calibration** (not raw accuracy) drives betting performance, e.g. [ScienceDirect article](https://www.sciencedirect.com/science/article/pii/S266682702400015X). Brier score as a proper scoring rule.

## Question

If Model A is 71% accurate but uncalibrated, and Model B is 69% accurate and calibrated, which should price bets? How do we show uncertainty around a 1.62 pp “edge”?

## Dataset

Any BlueChip prediction log with \(p\) and outcome \(y\).

## Model

Platt scaling, isotonic regression, reliability diagrams. Interval around \(p\) (bootstrap or calibration error).

## Features

n/a — post-processing of scores.

## Train/test methodology

Fit calibrators on **validation** walk-forward folds, never on the sacred holdout. Report Brier before/after.

## Result

Literature: selecting by calibration can change betting outcomes vs selecting by accuracy. Overconfidence is expensive: \((0.70-0)^2=0.49\).

## Limitations

Isotonic on small sports samples can overfit. Intervals will be wide; many “edges” will overlap break-even.

## What BlueChip will test

Reliability tables (50–52%, 52–54%, …). Do not publish a naked 56.2%. Bootstrap interval + n on every desk number. v0.1 leaderboard: Brier/logloss/ATS — **not** ROI ([04-bcw-v0.1.md](../roadmap/04-bcw-v0.1.md)).

## Implemented?

No.

## Experiment ID

—
