# Experiments

Notebooks and recorded runs. **Sacred holdout 2023–2025 is not a tuning set.** Open it once for BCW-v0.1 after the freeze in [04-bcw-v0.1.md](../roadmap/04-bcw-v0.1.md).

| Idea | Status |
|------|--------|
| `BCW-NFL-WP-XGB-v0.1` vs nflverse `wp` (2024 train / 2025 test, then LOSO) | Code ready; run from parquet |
| Start-year A–D: train 1999/2006/2009/2015–2022, **one** eval on 2023–2025 | Frozen design; run after snapshots |
| `nfl_margin_distribution.ipynb` — empirical \(P(M=k)\), key numbers 3/7/10/14 | Planned |
| Feature class ablation: PURE vs +CONTEXT vs +MARKET | After v0.1 freeze (not in launch features) |
| Forecast vs observed weather leakage check | After NWS ingest |

Each committed model run should have an `experiment_id`, git commit, train/valid/test ranges, `feature_version`, `market_features: true/false`, and metrics **with n and intervals**. v0.1 leaderboard: no ROI.

MLflow is optional later; the registry concept is required now (see data contract).
