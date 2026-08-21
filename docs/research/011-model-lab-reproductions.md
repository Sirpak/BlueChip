# 011 — Model lab: reproduce published methods, same BlueChip data

Locked 2026-08-18. Holdout, published Ridge \(\mu\), no ROI, no v0.1 ensemble: [04](../roadmap/04-bcw-v0.1.md). Snapshot vs Ridge: [010](010-snapshot-superset-vs-ridge.md). This note is the **catalog and lab order**, not a license to train twenty models at once.

## Citation

| # | Source | What we take |
|---|--------|----------------|
| 1 | ESPN, *How NFL FPI was developed* | EPA/play off + def + ST; opponent and trash-time adjustment; QB when backup; HFA. https://www.espn.com/nfl/story/_/id/13539941/how-espn-nfl-football-power-index-was-developed-implemented |
| 2 | ESPN, *FPI debuts* | Rest, altitude, travel as documented game factors. https://www.espn.com/nfl/story/_/id/13539793/espn-nfl-football-power-index-debuts |
| 3 | Palomino, Peypoch & Zhang, *Footballonomics* (arXiv:1601.04302) | Logistic + bootstrap; reported ~63% winner accuracy 2014–15. Pregame rolling features only. |
| 4 | Beal, Norman & Ramchurn, classifier comparison (~1,280 NFL games, 42 features/team) | Nine classifiers; published best ~67.5% Naive Bayes. Reproduce as a **shootout**, judge Brier/log loss not headline accuracy. https://www.researchgate.net/publication/348650836 |
| 5 | CFBD / Rad Sports, LightGBM + NGBoost on 17,662 CFB games | Chronological split (pre-2019 / 2019+); winner AUC ~0.87, ~76% acc; margin RMSE ~15.7. NFL uses a **smaller** feature set first. https://blog.collegefootballdata.com/predicting-spreads-gbdt/ |
| 6 | NFL margin as a random variable (PMC10929675) | Distribution / quantiles vs spread; Normal/t/empirical/BALE-inspired in `ml/research/distributions/`. |
| 7 | Moreland & Superdock, arXiv:1802.00527 | Elo-style ratings for **margins**, not only win/loss. |
| 8 | *A statistical theory of optimal decision-making in sports betting* (PMC10306238) | >5,000 NFL games; close captures ~**86%** of variation in **median** outcome. **Do not** treat spread betting as binary classification. Need \(F_M\). |
| 9 | *iWinRNFL* (arXiv:1704.00197) | Calibration; extra nonlinear complexity did not reliably beat a simple in-game logistic. Complicated ≠ better. |

PFR SRS glossary; Stern 1991 / 008 for \(P(M>x)\) from a Normal around \(\mu\).

## Question

On one leakage-safe BlueChip dataset (develop 2009–2022; holdout 2023–2025 once), which **published-style** models add incremental OOS information beyond Market 0 (nflverse_pfr close)?

There is **no magic algorithm**. Strong systems combine: (1) team-strength ratings, (2) opponent-adjusted efficiency, (3) a **distribution** of margin, (4) market benchmarking.

Research question is **not** “can ML predict football.” It is whether a named model + feature set beats (or even matches) a close that already explains most of the median.

## Principle (betting)

\[
M = \text{home} - \text{away},\qquad P(\text{cover } s) = 1 - F_M(s)
\]

Cover-yes/no classifiers are the wrong object. Winner accuracy is a reference metric only. Leaderboard: Brier, log loss, MAE/RMSE, ATS vs close, n, interval. **No ROI.**

## Lab stages (do not run C–E before A–B exist)

### Stage A — rating baselines (before Ridge freeze)

| Id | Form | Output |
|----|------|--------|
| `BCW-HFA` | historical mean + home | \(\mu\) |
| `BCW-ELO` | recursive rating | rating / \(P(\text{win})\) |
| `BCW-SRS` | iterative \(R_i = \overline{\text{PD}}_i + \mathrm{SOS}_i\); \(\hat\mu = R_h - R_a + \mathrm{HFA}\) | \(\mu\), SOS, raw PD |

SRS is hard to beat by accident and produces expected **margin**. Dashboard later: overall, SOS, raw PD, opponent-adjusted margin, expected neutral-field margin.

### Stage B — interpretable stats (before Ridge freeze)

| Id | Form | Output |
|----|------|--------|
| `BCW-OPP-ADJ-EPA` | \(\mathrm{EPA}_{ij} \approx \mu + \mathrm{Off}_i + \mathrm{Def}_j + \mathrm{HFA} + \varepsilon\), Ridge shrinkage | off/def strength |
| `BCW-LOGISTIC-v0.1` | \(\sigma(\beta_0 + \beta^\top x)\), L2, **pregame rolling \(x\) only** | \(P(\text{home win})\) |
| `BCW-RIDGE-v0.1` | \(M \sim X\beta\), L2; published \(\mu\) + Stern | \(\mu\), \(\beta_j x_j\) “why” |

Logistic feature candidates (all known before kickoff): Elo diff, SRS diff, off/def EPA diffs (**prefer opponent-adjusted once that model exists**), success-rate diff, rest diff, home. Turnover-rate diff only if heavily regressed.

**Before freeze, on 2009–2022 only:** compare Ridge(raw EPA EWMA) vs Ridge(opponent-adjusted EPA). Freeze **one** PURE feature_version. Do not open 2023–2025 to decide.

FPI-style **Power Index** \( \mathrm{Off}-\mathrm{Def}+\mathrm{ST} \) + QB/rest/travel is a **later** named model (`BCW-POWER`), not a dump into Ridge v0.1. Estimate those additives; do not hard-code folklore points.

### Stage C — structured ML (after Ridge freeze + one holdout pass)

`BCW-LGBM-WIN`, `BCW-LGBM-MARGIN` — CFBD experiment on NFL snapshots, smaller \(X\) first. Chronological walk-forward. Then a **classifier shootout** (logistic, Gaussian NB, RF, SVM, kNN, tree, GBDT, XGB/LGBM) on the **same** folds. Care about Brier / log loss / AUC / calibration more than 67.5% headlines.

### Stage D — probability (after C or in parallel with C, still not v0.1)

`BCW-NGBOOST` (learned \(\mu,\sigma\)); empirical residual; Student-t; BALE-inspired in `ml/research/distributions/`. Metrics: log likelihood, CRPS, coverage, spread-probability calibration. `BCW-MARGIN-ELO` (Moreland–Superdock). Then \(P(\text{cover})\) from \(F_M\), not global \(\sigma=13.5\).

### Stage E — ensemble

`BCW-CONSENSUS` only after OOS predictions exist for A–D. **Not** the published v0.1 number. Desk may **show** disagreement (model matrix) without averaging into one tout.

## Immediate pipeline (overrides 010 “opp-adj after v0.1”)

Keep sacred holdout and Ridge as the **published** launch \(\mu\).

```
1999–present PBP + schedules
        ↓
time-safe snapshot superset
        ↓
BCW-HFA → BCW-ELO → BCW-SRS
        ↓
BCW-OPP-ADJ-EPA
        ↓
BCW-LOGISTIC-v0.1
        ↓
BCW-RIDGE-v0.1   (freeze after 2009–2022 walk-forward;
                  adj vs raw EPA decided here)
        ↓
FREEZE
        ↓
2023–2025 once
        ↓
then Stage C → D → E
```

## Product (after numbers exist; not a reason to skip ingest)

Power-ratings table (OVR / OFF / DEF / ST / Elo / SRS). Per-game **model matrix** (margin / win / cover vs market). Performance page by season with n. Calibration chart (mandatory once we show %). Ridge \(\beta_j x_j\); trees get SHAP later. Research page per `experiment_id` with paper link, train window, holdout, market-in? Y/N, status RESEARCH vs PUBLISHED.

Ask BlueChip later **retrieves** those explanations; it does not invent them.

## Dataset / methodology

Same snapshots, walk-forward inside 2009–2022, `known_at < kickoff`, no current-game EPA, no `vegas_wp` in PURE. Market 0 always on the board. CFB LightGBM numbers are **indicative**; NFL RMSE/AUC will differ.

## Result

—

## Limitations

FPI is not fully specified. Classifier papers use small \(n\) and winner accuracy. CFBD 714-feature LGBM is not the NFL v0.1 feature freeze. 86% of **median** variation ≠ 86% of ATS.

## What BlueChip will test

Stage A then B on snapshots, then freeze Ridge, then C–E. Each model an `experiment_id`.

## Implemented?

No (spec + stubs). `ml/pregame/elo.py`, `srs.py`, `opp_adj_epa.py`, `logistic.py`, `ridge_margin.py` raise until snapshots exist.

## Experiment ID

—
