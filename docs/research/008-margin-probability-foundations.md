# 008 — Predictive modeling of NFL & CFB margins (research foundation)

Foundation write-up for BlueChipWager. Specific ML accuracies from student CS229/capstone work are **indicative**, not peer-reviewed gospel. Peer-reviewed anchors: Stern (1991), Glickman & Stern (1998), David et al. (2011), Lopez, Matthews & Baumer (2018).

## Citation

See sections below. Primary: Stern, *The American Statistician* 45(3); Glickman & Stern, *JASA* 93(441); Lopez, Matthews & Baumer, *AOAS* 12(4). Spread conversion: Sides, Harvill & Sides (2022) [arXiv:2212.08116](https://arxiv.org/abs/2212.08116). Line-as-Gaussian: [arXiv:1211.4000](https://arxiv.org/abs/1211.4000).

## Question

Given a projected (or market) margin, what is \(P(\text{win})\) and \(P(\text{cover } x)\), how does that compare to no-vig market probability, and which public features actually forecast **future** margin?

## Implemented?

**Partial — Stage 1 is in code.** `app/markets/`: American odds, multiplicative/additive/Shin de-vig, Stern \(\Phi(\cdot)\) with \(\sigma_{\text{NFL}}=13.5\), \(\sigma_{\text{CFB}}=15\), continuity correction, both edges. UI `/markets`, JSON `/api/markets/price`. Stages 2–5 are not implemented.

## Experiment ID

—

---

## TL;DR

- **The betting market is the hardest benchmark and the best feature.** Models rarely beat the closing spread OOS: NFL MAE ~10–12 pts vs the line ~10.5; ATS clusters ~50%, below 52.4% at −110. Architecture: **no-vig line as prior**, hunt narrow situational edges — do not try to out-predict the market from scratch.
- **Math is simple and established.** Margin ~ Normal around the spread, \(\sigma \approx 13.5\) NFL (Stern 13.86; PFR 13.45), \(\approx 14–16\) CFB (spread-centered). Convert ML → implied → de-vig; compare to model \(p\). Refine with key numbers 3 and 7.
- **Features: opponent-adjusted EPA/play**, not box-score totals. Success rate + CPOE stabilize; turnovers **regress hard**; HFA ~2 pts not 3 (and ~1 in 2020); **QB availability** is the largest situational swing (up to ~7 pts). Open data: nflfastR / cfbfastR / CFBD.

---

## Key findings

1. Margin → probability is solved in **Stern (1991)**. Favorite of \(p\) points: \(P(\text{win})=\Phi(p/13.86)\). College needs wider \(\sigma\).
2. **Discreteness:** ~15–18.7% of NFL games land on a 3-point margin, ~9–10% on 7. Ordered-logistic / empirical weights beat a plain normal near key numbers.
3. **NFL closes are efficient.** CFB is measurably softer (no mandatory injury reports, slower midweek, weaker small-program attention).
4. Opponent-adjusted **EPA differential** is the strongest public future-margin predictor (FPI-class).
5. Canonical ratings: **Elo** (FiveThirtyEight MOV + autocorrelation) and **Glickman–Stern state-space**.
6. **QB injuries** dominate situation (~7 pts for elites); market speed is the battleground.
7. **Do not treat spreads as binary cover classification.** Need \(F_M\) so \(P(\text{cover } s)=1-F_M(s)\). A 2002–2022 NFL analysis found the close captures ~86% of variation in the **median** outcome ([PMC10306238](https://pmc.ncbi.nlm.nih.gov/articles/PMC10306238/)). Lab catalog: [011](011-model-lab-reproductions.md).

---

## 1. Academic literature

**Stern (1991), “On the Probability of Winning a Football Game.”** 1981/83/84 NFL. Margin of victory for the favorite ~ Gaussian with mean = spread, \(\sigma=13.86\). \(P(\text{favorite of } p \text{ wins})=\Phi(p/13.86)\). Basis for PFR (\(\sigma\approx 13.45\), 1978–2012) and Winston/Mathletics.

**Glickman & Stern (1998), JASA.** Dynamic Bayesian state-space NFL scores; AR(1) team strength; week-to-week and season-to-season variance; team-varying HFA; MCMC. Reported to beat Vegas on the last 110 games of 1993. 2017 chapter updates. Template for a Bayesian BCW layer.

**Lopez, Matthews & Baumer (2018), AOAS.** (Third author **Benjamin Baumer**, not “Trueblood.”) Betting-ML implied strengths after Hosmer–Lemeshow supports market efficiency in four majors. NFL “RegParity” 0.70 neutral / 0.54 when best team is home. **Difficult to beat the market**; combining model+market (Manner 2015) only occasionally beat markets alone. Do not attribute Mauboussin’s “39% luck” figure to this paper.

**Warner (2010), Stanford CS229.** GP on 1,280 games/5 seasons. Margin error ~2% above Vegas; winners 64.36%; betting scheme **&lt;51% ATS** — beating the line ≫ picking winners.

**David, Pasteur, Ahmad & Janning (2011), JQAS.** ANN committees; ~62–68% winner accuracy; practical ceiling MAE **~10–12 NFL, ~12–14 CFB**.

**Sides, Harvill & Sides (2022), arXiv:2212.08116.** Directly: if the model says +7.9, do you bet −7? Stern’s two flaws: discreteness; a 5-point favorite does not hit exactly 5 at the same rate a 7-point favorite hits 7. Empirically weighted college \(\sigma\): ~21–22 raw score-diff, **~15 spread-centered**. Break-even 52.4% at −110; edge = cover% − break-even. Uses SP+ as μ input.

**Also:** arXiv:1211.4000 — line-difference ~ N(0, 13.588); 7-pt favorite wins ~69.6%. Szalkowski & Nelson (2012) 2,560 games 2002–11: home ATS 47%; home **underdogs** 53.5% (fragile). Bock (2016) turnovers: +TO margin teams win ~70% but TOs near-random. Wadsworth & Vera (2016) ATS ~ coin flip. Conrad (2024) sportsbook **total** RMSE 12.87; spread models weaker than total models.

---

## 2. Rating systems

**FiveThirtyEight NFL Elo (open):** \(R \leftarrow R + K \cdot M(z)\cdot A(x)\cdot(S-E)\), \(K=20\), \(M=\ln(|\text{margin}|+1)\), \(A=2.2/(2.2+0.001\cdot\text{elo_diff})\), \(E=1/(1+10^{-x/400})\). HFA ~65 Elo (~2.5 pts) historically; 1/3 seasonal reversion; 400 pts ≈ 10:1. Strong at ranks, weaker at precise probabilities. CFB Elo to 1869.

**ESPN FPI:** off/def/ST in EPA/play, points vs average on a neutral field. Preseason blends Vegas totals/ML, polls, prior efficiency, returning starters/recruiting, coach/QB changes; in-season Bayesian toward current EPA. QB injury, rest, travel, altitude. College FPI Brier worsened 0.207 (2014) → 0.235 (2022) — a calibration benchmark.

**Massey:** least squares \(X\mathbf{r}=\mathbf{y}\) on margins. **Sagarin:** Elo vs points predictor (points version forecasts better). **DVOA:** opponent- and situation-adjusted; paywalled; open EPA/success rate often match it. Raw **point differential** remains extremely predictive.

---

## 3. Engine math (Stage 1 — implemented)

Spread → win: \(P(\text{favorite of } p)=\Phi(p/\sigma)\), \(\sigma_{\text{NFL}}=13.5\). Example: \(\Phi(7/13.5)\approx 69.8\%\), fair ML \(\approx -231\).

Cover given model \(\mu\): \(P(M>x)=1-\Phi((x-\mu)/\sigma)\). Integer \(x\): continuity \(x\pm 0.5\); key numbers for later ordered-logistic (Stage 2).

American: \(p=|o|/(|o|+100)\) if \(o<0\) else \(100/(o+100)\). −110 → 52.38%.

De-vig: **multiplicative default**; additive; **Shin** optional (more margin on longshots). Edge vs fair = \(p_{\text{model}}-p_{\text{no-vig}}\). Edge vs break-even = \(p_{\text{model}}-p_{\text{price}}\). Report **both**.

Home spread convention: \(M=\text{home}-\text{away}\); `home_spread=-7` ⇒ \(E[M]\approx +7\); cover iff \(M>7\).

Key numbers: 3 (~15–18.7%), 7 (~9–10%), 6/10/14; XP moved to 33 yards in 2015 slightly cut 7s. Stage 2 must re-fit empirically.

---

## 4. Features (later engineering)

Opponent-adjusted **EPA/play differential** (strongest public). Success rate (floor). CPOE (sticky QB). EPA/dropback, QBR, ANY/A. **Turnovers: expected, not realized.** HFA as tunable **1.5–2.5**, team-specific; down-weight 2020. QB starter–backup up to **~7** pts. Rest/travel/short week/bye — estimate (Lopez). Pace: per-play, not per-game (more important in CFB). Wind for totals; special teams EPA; red zone **regress**.

Feature classes remain PURE / CONTEXT / AVAILABILITY / MARKET. `vegas_wp` is MARKET, never PURE.

---

## 5. ML from the literature

Ridge + opponent-adjusted efficiency + walk-forward = practical baseline. GP/Warner, ANN/David, GBM (Bock, Conrad), Bayesian state-space, Skellam/Poisson scores, **ordered logistic** for discrete \(M\). Metrics: **Brier and log loss**. Do not compare a win-% MAE of 0.05 to a margin MAE of 11 points.

---

## 6. Data

nflverse / `nfl_data_py`; CFBD / cfbfastR; PFR SRS + documented \(\sigma=13.45\); Big Data Bowl later; historical closes now from nflverse; Pinnacle later for sharp no-vig; Odds API later.

---

## 7. Efficiency — how we hunt edges

NFL close is hard after vig. Fragile exceptions: historical home underdogs; favorite–longshot ML bias; season-specific linear profits that die. **Structural opportunity: CFB** + **QB news speed** + small situational deviations from a **market-anchored** prior.

Only flag edges that clear vig **plus a safety margin** (Stage 5 starts at **3–4 pp no-vig**). Size later with fractional Kelly. **CLV** is the leading KPI. If walk-forward Brier cannot match the close, defer to the market. If CLV is negative on ~200+ bets, stop. Re-fit \(\sigma\) and key numbers if they drift (2015 XP, 2020 HFA).

---

## Staged build (this note’s recommendations)

| Stage | Work | Status |
|-------|------|--------|
| 1 | Odds, de-vig, Stern CDF, continuity, both edges | **Done** (`app/markets`) |
| 2 | Empirical / ordered-logistic \(M\) for key numbers | Not started |
| 3 | Opponent-adjusted EPA ridge + FTE-style Elo; Brier vs close | After data contract + 1999–present ingest |
| 4 | Situational **nudges** (QB, rest, weather, team HFA), not full re-preds | Later |
| 5 | Selective flags, Kelly, CLV; CFB + injury speed | Later |

Never random CV. If HFA or key-number frequencies shift, re-fit.

---

## Caveats

- Peer review on exact ATS edges is thin; CS229/capstone numbers are directional.
- Match metric scale to the target.
- \(\sigma\) is not constant (NFL SD ~12.7–15.2 by season; “lumpy” at 3/7). College \(\sigma\) depends on **spread-centered vs raw**.
- Historical biases decay. COVID HFA is noisy.
- Marketing blogs and unsourced XGBoost lore were excluded.

## What BlueChip will test

Validate Stage 1 against −110 → 52.38% and −7 → ~69.8% / −231 (unit tests). Later: empirical \(P(M=3), P(M=7)\) vs Normal; Brier of Stern-from-close as Model 0 vs any fundamental model; start-year sensitivity 1999+.
