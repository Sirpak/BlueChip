# BCW-v0.1 freeze

Locked 2026-08-17. **Reconfirmed 2026-08-18.** Change only by explicit override. This file is what keeps v0.1 a **research model**, not a moving target.

Index: [DECISIONS.md](DECISIONS.md) · [questions.md](questions.md) · [TODO.md](TODO.md)

---

## Three launches (do not bundle)

| Launch | Definition |
|--------|------------|
| **Model** | One upcoming NFL slate loads; BCW-v0.1 produces a pregame **home margin** for every eligible game; Stern/`app/markets` maps \(\mu\) → win/cover; predictions are **immutable and versioned**; the desk shows them next to the market with honest OOS validation. |
| **Product** | Auth, Stripe, Ask BlueChip with citations, usage limits; model outputs exposed as tools. [03-monetary.md](03-monetary.md). |
| **CFB** | Same contract + modeling framework on CFBD **after** the NFL pipeline is proven. |

Dependency — this belongs in the README too:

```
DATA → FEATURES → MODEL → PREDICTION STORE → RESEARCH DESK → ASK BLUECHIP
```

Not: `RAG → football opinions`.

```
BCW MODEL          produces numbers
BCW RESEARCH DESK  shows numbers, history, features, evidence
ASK BLUECHIP       interrogates the desk
```

**Model launch ≠ site is pretty.** Model launch is: slate in, versioned \(\mu\) out, Stern cover/win, desk next to market, honest validation.

---

## Years

| Role | Seasons |
|------|---------|
| Ingest | **1999–present** |
| Elo initialization / era / history | 1999–2008 is allowed |
| Primary development | **2009–2022** |
| Sacred holdout | **2023–2025** |

**Open 2023–2025 exactly once for BCW-v0.1**, after feature definitions, hyperparameters, calibration method, and evaluation metrics are frozen. Looking at holdout metrics and then changing features **voids the holdout**.

Walk-forward lives **inside** 2009–2022. Do not harvest 2023–2025 for α, Ridge λ, or feature ideas.

Start-year experiment (same frozen pipeline, **one** holdout pass):

```
A: train 1999–2022
B: train 2006–2022
C: train 2009–2022   ← default published window
D: train 2015–2022
```

Evaluate all four identically on 2023–2025. That decides whether twenty-five years helps or hurts.

Do **not** treat 1999+ as one football. Ingest all seasons; keep explicit **era** on snapshots (nflfastR does this because the sport changes). Era is a feature/split, not a silent mix.

---

## Sign convention (everywhere internally)

\[
M = \text{home\_score} - \text{away\_score}
\]

nflverse / Market 0: **`spread_line > 0` ⇒ home favored**; negative ⇒ away favored. ([nflfastR `spread_line`][nflfastr-pbp])

```python
actual_margin = home_score - away_score
model_margin  = predicted_home_margin
market_margin = spread_line
```

BUF −6.5 on the road:

```
spread_line        = -6.5
model_home_margin  = -8.1    # BUF by 8.1
disagreement       = -8.1 - (-6.5) = -1.6
```

That is **1.6 points stronger toward the away team** than the market.

Never mix “favorite margin” and “home margin” in storage or models. Convert only in the UI.

Cover (home spread \(x\), home-centric): cover if \(M > x\); push if \(M = x\) on an integer line.

---

## Leaderboard (v0.1)

**No simulated ROI, units, or bankroll charts.** No “+42 units.” Historical American prices are often missing; `spread_line` is the closing spread (PFR via nflverse), which is enough for ATS vs line, not EV. ([nflfastR][nflfastr-pbp]; [beginner’s guide][nflfastr-beginner])

Defendable columns:

| Model | Brier ↓ | Log loss ↓ | Margin MAE ↓ | RMSE ↓ | ATS | ATS % | N | interval |
|-------|--------:|-----------:|-------------:|-------:|----:|------:|--:|----------|
| Market 0 (close) | — | — | vs actual \(M\) | — | — | — | | |
| Home / mean baseline | | | | | | | | |
| Elo | | | | | | | | |
| Logistic | | | — | — | | | | |
| **Ridge margin (published)** | | | | | | | | |

Logistic has no margin MAE/RMSE. Market 0 is the close, not “Vegas.” Every cell has **n**. Subsets (e.g. road favorites of 6–7) must show **39**, not impersonate 4,000.

---

## Model stack

| Id | Role | Target |
|----|------|--------|
| 0 | Historical mean + home field | baseline |
| 1 | Elo | rating / home win (reference) |
| 2 | Logistic | `home_win` (reference) |
| 3 | **Ridge** | `home_margin` — **this is the published spread number** |
| 4 | BCW-v0.1 | **not an ensemble.** Name of the frozen ridge + Stern pipeline |

Do not invent an arbitrary average “to have a consensus.” Elo and logistic stay on the leaderboard. Stern maps \(\mu_{\text{margin}} \to P(\text{win}), P(\text{cover at } x)\).

Published artifact example:

```
BUF @ NE
MARKET          BUF -6.5   source tagged (nflverse_pfr close / ESPN live, never mixed)
BCW-v0.1        projected home margin -8.1  (BUF by 8.1)
Win probability 72.0%
Cover -6.5      56.2%
Break-even -110 52.38%
vs break-even   +3.82 pp
MODEL           BCW-RIDGE-v0.1
TRAINING        2009–2022
OOS EVAL        2023–2025  (opened once)
Prediction at   2026-09-20 10:04 ET
```

Never display `56.2%` as a physical constant. Show model id, prediction time, **n**, and a calibration/bootstrap range (e.g. roughly 52–59%). Simple bootstrap is enough for v0.1.

Desk copy when a cover % is allowed through the gates:

```
BCW cover probability
56.2%

Historical calibration range
approximately 52–59%

Model
BCW-v0.1

Prediction generated
Sun 10:04 AM
```

---

## Frozen PURE feature set (`feature_version` to name when coded)

Rolling stats **end at the team’s previous game**. No current-game EPA.

```
home (indicator / HFA)
home_rest_days, away_rest_days

home_off_epa, away_off_epa          trailing EWMA /play
home_def_epa, away_def_epa

home_pass_epa, away_pass_epa
home_pass_epa_allowed, away_pass_epa_allowed
home_rush_epa, away_rush_epa
home_rush_epa_allowed, away_rush_epa_allowed

success_rate_diff
explosive_play_diff

elo_home, elo_away, elo_diff
```

Matchup diffs, e.g.

\[
\text{EPA}_{\text{off,diff}} = \text{HomeOffEPA} - \text{AwayOffEPA},\quad
\text{EPA}_{\text{def,diff}} = \text{AwayDefEPA} - \text{HomeDefEPA}
\]

**Out of v0.1:** injuries, weather, ESPN news, recruiting, complex QB adjustments, `vegas_wp`, spread as a PURE feature.

Tune EWMA \(\alpha\) only on development years.

---

## Five ship gates (all required to publish a cover %)

> **BCW-v0.1 may publish a cover percentage only if the entire prediction pipeline is leakage-safe, has a frozen feature set, beats or at least adds measurable information beyond simple baselines out-of-sample, is acceptably calibrated, and reports uncertainty and sample size.**

Beating the **close** is the research goal, not a promise. The system must **show** whether it does. Do not require Elo, logistic, and Ridge all to beat Market 0.

1. **Data / leakage** — every feature for game \(g\) uses only records with `known_at < kickoff_g`. Automated tests, not honor. Banned in PURE: `vegas_wp` (nflfastR: incorporates pregame spread), current-game EPA. ([nflfastR WP][nflfastr-wp])
2. **Baseline** — Ridge beats “HFA + historical mean” on margin error (dev walk-forward). Logistic is compared to Elo and a home-win baseline. Market 0 stays on the board.
3. **Calibration** — bucket predicted cover (or win) vs observed frequency. Fit any calibrator on **development** folds only. A 58% that happens 52% of the time does not ship on accuracy.

   | Predicted cover | Observed cover frequency |
   |----------------|--------------------------|
   | 50–52% | ? |
   | 52–54% | ? |
   | 54–56% | ? |
   | 56–58% | ? |
   | 58–60% | ? |

4. **Uncertainty** — UI shows interval + model + `prediction_at`, not a naked 56.2%. First interval: simple bootstrap.
5. **Sample size** — every result has `n`.

---

## CFBD

Get the key **now**. Free tier 1,000 calls/month; Academic 3,000/month with a `.edu` address. ([CFBD tiers][cfbd-tiers]) Put `CFBD_API_KEY` in local `.env` only. **One test request**, document the provider, then **stop**. No CFB rows until the NFL lab passes these gates.

---

## Next engineering (boring, decisive)

Schema identity + Market 0 tags are in Alembic `0002_data_contract`. Snapshots are Alembic `0004_feature_snapshots` (`BCW-SNAP-v0.1`). Remaining: logistic then Ridge on **2009–2022**, freeze, then the sacred 2023–2025 pass.

---

[nflfastr-pbp]: https://nflfastr.com/reference/fast_scraper.html
[nflfastr-beginner]: https://www.nflfastr.com/articles/beginners_guide
[nflfastr-wp]: https://nflfastr.com/reference/calculate_win_probability.html
[cfbd-tiers]: https://collegefootballdata.com/api-tiers
