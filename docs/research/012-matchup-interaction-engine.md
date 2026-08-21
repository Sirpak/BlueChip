# 012 — Matchup interaction engine (next generation)

Locked framing 2026-08-20. Does **not** reopen [04](../roadmap/04-bcw-v0.1.md). Does **not** replace Ridge v0.1. Builds **after** Model Launch (freeze + one holdout pass + five gates).

Related: [010](010-snapshot-superset-vs-ridge.md) (play-style matchups mentioned as later “why” copy), [011](011-model-lab-reproductions.md) Stages C–E, [008](008-margin-probability-foundations.md).

## Question

Can BlueChip move from **team-level differences**

\[
x = \text{strength}_A - \text{strength}_B
\]

to **interaction features**

\[
x = f(\text{strength}_A,\ \text{weakness}_B,\ \text{usage}_A,\ \text{context})
\]

that improve OOS Brier / MAE / ATS-vs-close **and** produce slate “EDGE headlines” users understand?

## Principle

Football is matchup-driven. NFL Next Gen Stats models blocker–rusher graphs, pressure probability, and attribution; 2026 Bradley–Terry work rates ~153k blocker–rusher pairs with ridge regularization and double-team indicators. BlueChip should:

1. Keep **historical relationship data** (1999+) to estimate *how much* mismatches matter.
2. Keep **current strength data** (recent games / roster) to estimate *who* is strong today.
3. Apply relationships via a **Matchup Feature Engine** — a separate layer from PURE Ridge freeze.

## Three models (after Wave 1 Model Launch)

| Id | Form | Output |
|----|------|--------|
| `BCW-MATCHUP-LOGISTIC` | \(P(\text{home win})=\sigma(\beta_0+\beta^\top x_{\text{interact}})\) | win prob + interpretable \(\beta\) |
| `BCW-MATCHUP-LGBM` | trees on interaction DB | margin / win; learns nonlinear “elite rush × weak OL × slow QB” |
| `BCW-MATCHUP-DISTRIBUTION` | \(M\sim D(\mu,\sigma)\) with matchup-adjusted mean **and** width | win / cover / push / upset from one \(F_M\) |

These are **Stage C–D successors**, not v0.1. Ridge remains the published launch \(\mu\) until gates say otherwise.

## Matchup Feature Engine (the missing layer)

Today: Team A features, Team B features → difference.

Target:

```text
Team A strengths  ×  Team B weaknesses  →  MATCHUP FEATURES
```

Build order (measure historically; do not hand-code “+2 points”):

1. **Pass rush × OL × QB** (strongest public/research support)
2. **Run offense × front seven** (success / EPA / YCOE — not raw YPC)
3. **WR depth × coverage** (concentration + CB1 / double-team risk)
4. **QB mobility × rush style** (edge vs interior pressure)
5. **OL weak-link / Bradley–Terry** (research lab; tracking-dependent)
6. **Defensive weakness × opponent usage** \(\times\) efficiency

Example interaction test (not folklore):

\[
Y = \beta_0 + \beta_1\,\text{PressureMismatch} + \beta_2\,\text{QBPressureSkill}
  + \beta_3\,(\text{PressureMismatch}\times\text{QBPressureSkill}) + \varepsilon
\]

Retain only terms with stable walk-forward lift vs Market 0.

## Product surfaces (Research Preview OK before public %)

- **EDGE Headlines** on matchup pages (major / strong / negative)
- **Matchup Matrix** (pass, rush, protection, WR room, QB vs pressure, ST)
- Total matchup adjustment as a **labeled** additive — test OOS before feeding Ridge

## Data tiers

| Tier | Content | Status vs BlueChip |
|------|---------|-------------------|
| 1 | nflverse EPA, success, CPOE, air/YAC, sacks, scrambles, locations, IDs | **Have** (PBP + snapshots) |
| 2 | Rosters / starters / depth / injury `known_at` | **Not built** |
| 3 | Snap / route / pass-block / coverage participation | **Not built** |
| 4 | Pressure / PBWR / quick pressure / blocker–rusher | **Gap** — aggregate licensed metrics and/or Big Data Bowl research |
| 5 | Separation / coverage shell / double coverage | **Gap** — schema now, data later |
| 6 | QB context (TTT, clean vs pressure EPA, scramble EPA) | **Partial** via PBP; needs player windows |
| 7 | Individual OL continuity | **Not built** |
| 8 | Rush YBC/YAC / RYOE / box counts | **Partial** |
| 9 | CFB returning production / recruiting | **Blocked** until NFL gates + CFB ingest |

## What is *not* this note

- Do not dump interaction features into `BCW-RIDGE-v0.1` before freeze.
- Do not train pregame LightGBM before the sacred holdout pass ([011] Stage C).
- Do not treat weekly desk AI / strength proxies as the Matchup Engine.

## Wave split (locked product framing 2026-08-20)

Keep **W1 Model Launch** untouched (Ridge freeze / holdout / gates).

| Wave | Scope | Status |
|------|--------|--------|
| **W2A** | Matchup statistics from nflverse-class team EPA (pass/rush/overall/success + pressure proxy) | Code: `ml/matchup/edges.py` |
| **W2B** | Game Intelligence Package (cached evidence + events + AI brief; hash skip) | Code: `app/services/intelligence/` |
| **W3** | EDGE headlines UI + `BCW-MATCHUP-LOGISTIC` Research Preview + Level 1/2/3 pages | Code: brief UI + `ml/matchup/logistic.py` |

Fan product (EDGE + brief) can improve **before** advanced matchup models are published. Labels stay **MATCHUP SIGNAL** / Research Preview until walk-forward validation.

### Build / serve

```bash
python -m ml.pregame.weekly_publish --nfl 0 --cfb 0 --ai-top 0
python -m ml.matchup.build_intelligence --limit 20   # or omit limit for all weekly cards
```

Page views: `GET /api/intelligence/game` — **no LLM**.

## Implemented?

**Partial (W2A / W2B / W3 fan layer).** Capture 2026-08-20.

- Edges: `ml/matchup/edges.py`, profiles: `ml/matchup/profiles.py`
- Headlines + logistic: `ml/matchup/headlines.py`, `logistic.py`
- Packages: `app/services/intelligence/`, CLI `python -m ml.matchup.build_intelligence`
- API: `/api/intelligence/*` · UI: `GameIntelligenceBrief` on matchup Overview

Not done: walk-forward validation of matchup logistic, true pressure/PBWR, roster events, weather snapshots.

## Open questions (blocking Wave 2+)

1. Which Tier 4 pressure metrics are legally/reliably obtainable for production vs research-only (Big Data Bowl)?
2. Minimum viable interaction set from **nflverse alone** before roster/snap joins?
3. Does pass-rush mismatch beat opp-adj EPA diffs on 2009–2022 walk-forward Brier/MAE?
4. Should EDGE Headlines ship as Research Preview UI before any matchup model is published?
