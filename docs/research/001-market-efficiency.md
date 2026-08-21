# 001 — Market efficiency (closing line as Model 0)

## Citation

- Kain, K. J., & Logan, T. D. related literature on betting markets as aggregators; NFL open vs close vs actual margin: [arXiv:1211.4000](https://arxiv.org/pdf/1211.4000) (2012).
- Cox, Schwartz, Van Ness, Van Ness. “The Predictive Power of College Football Spreads…” *Journal of Sports Economics* (2021). [Sage](https://journals.sagepub.com/doi/abs/10.1177/1527002520975837)
- On probabilistic decision-making in sports betting: [PMC10306238](https://pmc.ncbi.nlm.nih.gov/articles/PMC10306238/)

## Question

How much information about actual NFL/CFB outcomes is already in the **closing** spread (and, later, moneyline and total)? Is the book a hard benchmark (“Model 0”) rather than a number we merely beat?

## Dataset

NFL: nflverse/PFR closing `spread_line` (and totals/moneylines when present), 1999+.  
CFB: CFBD historical betting lines (after ingest).  
Live books: Odds API later — separate snapshots, not aliased as the same series.

## Model

None of ours. The **market** is the model: implied margin ≈ posted spread; implied win prob from moneyline after de-vig.

## Features

Market quotes only. Not mixed into PURE BlueChip feature sets. nflfastR `vegas_wp` is the same class of information — **benchmark, never a PURE feature**.

## Train/test methodology

Not applicable to the market itself. BlueChip walk-forward compares *our* OOS probabilities/margins to this close. v0.1: cover-vs-line when American price is missing.

## Result

Literature: closing lines are highly informative; some subset inefficiencies appear historically (especially CFB). Spreads explain a large share of variation in game margin in NFL samples. Results are **not** a license that a 2026 strategy is +EV.

## Limitations

- Historical `spread_line` without −110/−105 is not a precise EV study.
- Close ≠ open; CLV needs timestamps we do not yet have.
- Vig-adjusted “fair” 50/50 on −110/−110 is an assumption of symmetry.

## What BlueChip will test

1. MAE/RMSE of closing spread vs actual \(M\), by season and era (1999 vs 2009 vs 2018).  
2. Brier of a naive “cover 50% at the close” vs our models.  
3. Later: moneyline-implied \(P(\text{win})\) and total-implied scoring vs our distributions.  
4. Never label `nflverse_pfr` snapshots as `vegas_line`.

## Implemented?

Partial — `games.spread_line` ingested; Stage 1 conversions live in `app/markets`. Not yet first-class `MarketSnapshot` rows with `market_source=nflverse_pfr`.

## Experiment ID

—
