# 005 — Spread / margin modeling and key numbers

## Citation

Same CFBD GBDT post as 003 (margin RMSE vs classifier AUC). nflfastR `spread_line` as **closing** spread ([nflfastR data dictionary](https://www.nflfastr.com/articles/field_descriptions.html) — confirm `spread_line` / closing language in current docs). Discrete NFL scoring: 3, 6, 7, 10, 14.

## Question

Should the flagship object be \(P(\text{cover } x)\) from a distribution of \(M\), not a yes/no −7 classifier? How do pushes and key numbers change −6.5 vs −7?

## Dataset

NFL final scores; empirical \(P(M=k)\). Market: closing spread, prices when present.

## Model

v0.1: Ridge \(\hat\mu\). Next: Normal residual \(\mathcal{N}(\hat\mu,\hat\sigma)\). Later: NGBoost, quantile LGBM, discrete / simulation around key numbers. Cover: \(P(M>x)\); push \(P(M=x)\) for integer lines.

## Features

PURE football first. Do not retrain when the posted line moves −7 → −6.5; re-evaluate the CDF.

## Train/test methodology

Walk-forward. ATS treats pushes separately. No EV metric when `price_american` is null.

## Result

Margin is harder than winner (CFBD RMSE ~15.7 historically). Key-number mass means a continuous Normal is a **baseline**, not the last word.

## Limitations

Normal density on a discrete score difference mis-prices 7s. Apparent 1.6 pp edges may be noise (see 004).

## What BlueChip will test

v0.1: Ridge \(\hat\mu\) + Stern \(\sigma=13.5\). After freeze: Normal residual, NGBoost, empirical / t / BALE-inspired in `ml/research/distributions/` ([011](011-model-lab-reproductions.md), [PMC10929675](https://pmc.ncbi.nlm.nih.gov/articles/PMC10929675/), [PMC10306238](https://pmc.ncbi.nlm.nih.gov/articles/PMC10306238/)). Cover is \(1-F_M(s)\), not a binary classifier. Leaderboard: MAE/RMSE/CRPS + ATS with push counts. **No ROI.**

## Implemented?

Stage 1 normal + continuity in `app/markets/spread.py`. Ordered-logistic / empirical key numbers: no.

## Experiment ID

—
