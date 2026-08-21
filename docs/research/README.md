# Research notes

Committed on purpose: BlueChip is a **research repo**. Each note uses the same skeleton (see [_TEMPLATE.md](_TEMPLATE.md)). They are starting points, **not** proof a 2026 betting strategy is +EV.

| Note | Topic | Implemented? |
|------|--------|----------------|
| [001-market-efficiency.md](001-market-efficiency.md) | Closing line as Model 0; never `vegas_line` | Partial (spread on `games`) |
| [002-nfl-prediction-models.md](002-nfl-prediction-models.md) | Model lab, not one classifier | No |
| [003-cfb-prediction-models.md](003-cfb-prediction-models.md) | CFBD GBDT; spread harder than winner | No |
| [004-calibration.md](004-calibration.md) | Brier, intervals around “edge” | No |
| [005-spread-modeling.md](005-spread-modeling.md) | \(P(M>x)\), pushes, key numbers | Stage 1 normal in code |
| [006-feature-research.md](006-feature-research.md) | Estimate rest/bye; EWMA; pre-game EPA | No (dashboard EPA leaks the game) |
| [007-data-leakage.md](007-data-leakage.md) | `known_at`, clocks, holdout hygiene | Spec only |
| [008-margin-probability-foundations.md](008-margin-probability-foundations.md) | Stern, de-vig, EPA, market-as-prior | **Stage 1 implemented** |
| [009-nflfastr-replication.md](009-nflfastr-replication.md) | Python EP/WP, not an R wrap; live ≠ pregame | Partial (WP trainer) |
| [010-snapshot-superset-vs-ridge.md](010-snapshot-superset-vs-ridge.md) | Snapshot may be rich; Ridge freeze stays small | Spec |
| [011-model-lab-reproductions.md](011-model-lab-reproductions.md) | Reproduce SRS / FPI-style EPA / logistic / LGBM / \(F_M\) on one dataset | Spec |
| [012-matchup-interaction-engine.md](012-matchup-interaction-engine.md) | Strength×weakness matchups; logistic / LGBM / \(F_M\); EDGE headlines | Spec only — **after** Model Launch |

Sources: [nflfastR](https://github.com/nflverse/nflfastR), [nflverse](https://github.com/nflverse), [CFBD API](https://api.collegefootballdata.com/getting-started).

When code lands, set `Implemented?` and `Experiment ID` and link the module.
