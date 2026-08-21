# 006 — Feature research (rest, bye, EPA, recency)

## Citation

Lopez, M. J., & Bliss, T. (and related) work on **rest differentials**, Bayesian state-space structure, and betting-market information; bye-week effects shrinking or changing after the **2011 CBA**. EPA/CPOE ecosystem: nflfastR/nflverse.

## Question

Which situational stories survive estimation? Rest, bye, travel, QB change — **estimate**, don’t ship `bye_week = +2.5`.

## Dataset

nflverse rest fields, schedule, EPA from PBP. QB on/off from passer ids. Later: injury `known_at`.

## Model

Coefficients in logistic/ridge; later hierarchical/Bayesian if needed. EWMA:

\[\mathrm{EWMA}_t = \alpha x_t + (1-\alpha)\mathrm{EWMA}_{t-1}\]

Tune \(\alpha\) OOS (e.g. 0.10, 0.20, 0.35, 0.50).

## Features

PURE: EPA splits, success, explosive, CPOE, rest diff, home. CONTEXT: roof, travel (later). AVAILABILITY: QB start, injuries. Never **actual** NWS observation in a pregame snapshot.

## Train/test methodology

Pre-game snapshots only. Post-2011 bye as a split or interaction, not a constant.

## Result

Published rest/bye effects are smaller or messier than talk-radio. Measure on our walk-forward.

## Limitations

Confounding (good teams get byes). Injury timing is the leakage magnet (Sunday `OUT` in a Friday model).

## What BlueChip will test

**v0.1 freeze** (no injuries/weather/QB complexity): rest days, EPA EWMA splits (off/def/pass/rush and allowed), success and explosive diffs, Elo. Rolling stats stop at the previous game. Full list: [04-bcw-v0.1.md](../roadmap/04-bcw-v0.1.md).

Snapshot **table** may be richer; Ridge does not automatically get those columns. [010-snapshot-superset-vs-ridge.md](010-snapshot-superset-vs-ridge.md).

Later: rest-diff coefficient, EWMA α grid on **2009–2022 only**, SRS baseline, opponent-adjusted EPA **before Ridge freeze**, then QB / ST / LightGBM after. [011](011-model-lab-reproductions.md).

## Implemented?

Partial (spec). Dashboard EPA is **season-to-date including the game** — leakage if used for modeling. Real pre-game snapshots: no.

## Experiment ID

—
