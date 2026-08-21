# Product vision — probabilistic football research

BlueChipWager is **not** a “pick the winner” app. It is a **probabilistic football research platform**. NFL (then CFB) models estimate the **distribution of possible game outcomes**, and the platform compares those probabilities to sportsbook prices.

Identity: a **quantitative research terminal**, closer to Bloomberg than a tout. Not “lock of the day.” Commercial packaging is **Football Intelligence** (Perplexity for NFL + CFB), not “AI sports betting assistant.” Pricing, AI metering, and ChatGPT/MCP as a *secondary* client: [03-monetary.md](03-monetary.md).

Documents here are a compass, not mandatory work items. Better math or a thinner design wins.

---

## The question

> Given everything known before kickoff, what is the probability Team A wins by more than X points, and is that probability materially different from the probability implied by the market price?

That framing is the whole stack: statistics, distributions, feature engineering, time-series validation, calibration, ML, databases, APIs, and (later) AWS and model monitoring.

---

## Two probabilities inside a posted number

Example: **Rams −7 (−110)**

- **−7** is the handicap (spread).
- **−110** is the price (American odds).

Break-even probability at −110:

\[
P_{\text{break-even}} = \frac{110}{110 + 100} = 0.5238
\]

If the model says \(P(\text{Rams margin} > 7) = 54\%\):

\[
54\% - 52.38\% = 1.62\text{ pp edge vs break-even}
\]

That is **not** the sportsbook’s fair cover probability. If both sides are −110/−110:

\[
52.38\% + 52.38\% = 104.76\%
\]

The extra 4.76% is vig/overround. After de-vig, a symmetric −110/−110 market is about **50/50**.

BlueChip always reports **both**:

| Metric | Example |
|--------|--------:|
| Model cover probability | 54.0% |
| Market fair (no-vig) probability | 50.0% |
| Model vs market edge | +4.0 pp |
| Break-even probability | 52.38% |
| Edge vs break-even | +1.62 pp |

Sportsbooks are an extremely strong benchmark (NFL research finds spreads explain a large share of variation in actual margins). Beating winners is the wrong scoreboard; beating **calibrated probability vs the close** is the right one.

---

## Flagship model: distribution of margin

Do **not** make “Rams cover −7: yes/no” the primary model.

Define \(M = \text{home points} - \text{away points}\). Predict:

\[
M \sim \text{Distribution}(\mu, \sigma, \ldots)
\]

Then one fitted model answers any line without retraining:

- \(P(M > 0)\) — moneyline
- \(P(M > 3)\) — −3
- \(P(M > 6.5)\) — −6.5
- \(P(M > 7)\) — −7

Pushes: \(P(M = 7)\) on an integer −7. NFL margins are discrete; key numbers (3, 7, 10, 14) matter. A Normal is a baseline.

Do not treat 54% vs 52.38% as a real 1.62 pp edge without a calibration/bootstrap interval. ATS of 9/15 is not a finding.

Training is occasional. Inference is cheap. Repricing a line from −7 to −6.5 is just another CDF evaluation.

Point estimates (expected margin +2.3 vs the posted −7) are useful but incomplete without **uncertainty**.

---

## What “good” means

Winner accuracy is a vanity metric here. A 71% model that is overconfident can lose money to a 69% model that is calibrated.

**Primary metrics**

| Family | Metrics |
|--------|---------|
| Classification | Accuracy, AUC |
| Probability | **Brier**, log loss, calibration error |
| Margin | MAE, RMSE, **CRPS** |
| Betting (simulated) | ATS vs close (v0.1). ROI, CLV, bankroll **after** v0.1 — not on the launch leaderboard |
| Versus market | Model vs market probability error |

Brier for a binary outcome \(y \in \{0,1\}\) and forecast \(p\):

\[
\text{Brier} = (p - y)^2
\]

Confident and wrong is expensive. That is what we want the score to punish.

Walk-forward validation is **more important than LightGBM**. No shuffled `train_test_split`. Develop **2009–2022**; sacred holdout **2023–2025** opens once. Cover % ships only after the five gates in [04-bcw-v0.1.md](04-bcw-v0.1.md).

---

## Pure models vs market-aware models

**Pure (never see odds as features)**

- BCW-LOGISTIC-PURE
- BCW-ELO
- BCW-EPA
- BCW-MARGIN-PURE
- BCW-LGBM-PURE

**Market-aware (separate, labeled honestly)**

- BCW-MARKET-RESIDUAL — target is `actual_margin - market_spread` (“what doesn’t Vegas know?”)
- BCW-LGBM-MARKET
- BCW-ENSEMBLE-MARKET

Using Vegas as a feature is a valid model. It is **not** “we predict NFL at 74%.” Leaderboards always include **Market** as Model 0.

---

## Research that informs this (write-ups in `docs/research/`)

| Theme | Why it matters |
|-------|----------------|
| NFL ML classifiers (Beal, Norman, Ramchurn) | Many models, not “the LightGBM app” |
| CFBD LightGBM/NGBoost experiment | CFB blueprint; winner better than exact margin (AUC ~0.87, margin RMSE ~15.7 historically) |
| Closing line as a model | Market is Model 0, NFL and CFB |
| Calibration vs accuracy in sports betting ML | Choose models by probability quality |
| Lopez & Bliss on rest / bye after 2011 CBA | **Estimate** narratives; don’t hard-code `bye = +2.5` |

Citations and notes: [docs/research/README.md](../research/README.md).

---

## Interview / portfolio sentence (target)

> I built a multi-league football research platform in Python. It ingests NFL play-by-play and (later) college football data, constructs time-safe feature snapshots, and runs Elo, logistic regression, regularized margin regression, and gradient-boosted probabilistic models. Instead of classifying winners, it estimates a distribution over scoring margin so any spread can be priced. A market engine converts American odds to implied probabilities, removes vig, and compares calibrated forecasts to opening and closing lines. Models are evaluated with walk-forward validation (Brier, log loss, calibration, RMSE, CLV, simulated ROI) and every prediction is versioned to the information available before kickoff.

That is a different project from “I trained LightGBM on football games.”
