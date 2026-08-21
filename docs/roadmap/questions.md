# Questions and suggestions

The agent should still **ask** on keys, leakage, and touting. Locked answers: [DECISIONS.md](DECISIONS.md). v0.1 freeze: [04-bcw-v0.1.md](04-bcw-v0.1.md). Money: [03-monetary.md](03-monetary.md).

---

## Answered (2026-08-17; reconfirmed 2026-08-18)

| # | Decision |
|---|----------|
| NFL years | **Ingest 1999–present.** Develop **2009–2022**. Sacred holdout **2023–2025**, opened **once** after freeze. Start-year A–D on that pass. Era on snapshots. Do not treat 1999+ as one sport. |
| Odds API | **Do not pay yet.** Key later; free tier then if we need live snapshots. $30/mo waits. |
| CFBD | **Key now** (Academic `.edu` if eligible). One test call. **No CFB rows** until NFL gates pass. `league` from day one. |
| Market 0 | nflverse closing `spread_line` (`nflverse_pfr` / `historical_close`). ATS vs line when price missing. Never `vegas_line`. |
| Research git | **Commit notes.** `docs/research/` is part of the product. |
| Commercial | BlueChip-hosted AI, Pro **$14.99**; ChatGPT/MCP later; no consumer API keys. [03-monetary.md](03-monetary.md). |
| Home margin | **Yes, everywhere.** \(M =\) home − away. `spread_line > 0` ⇒ home favored. UI may flip; storage may not. |
| v0.1 leaderboard | Brier, log loss, MAE/RMSE, ATS vs close, ATS %, n, interval. **No ROI / units / bankroll / “+42 units.”** |
| Published model | **Ridge \(\mu\)** (`BCW-RIDGE-v0.1`) + Stern. Elo/logistic are references. **Not an ensemble.** |
| Ship gates | All five required before a public cover %: leakage, baseline, calibration buckets, uncertainty + `prediction_at`, n. [04-bcw-v0.1.md](04-bcw-v0.1.md). |
| Feature freeze | Home, rest, EPA EWMA off/def/pass/rush + allowed, success/explosive diffs, Elo. Rolling stats end at previous game. **Out:** injuries, weather, news, fancy QB, `vegas_wp`. |
| Launches | Model → Product → CFB. Data → features → model → store → desk → Ask. Not RAG-as-opinions. Model launch is a slate + versioned \(\mu\), not “the marketing site is done.” |

Plan of record: [02-phases.md](02-phases.md) (30 phases; execute 1–15 now). Model before Ask. Do not skip to LightGBM, CFB, Stripe, or AWS.

Snapshot table may store FPI/SP+-class families. **Before Ridge freeze:** HFA, Elo, SRS, opponent-adjusted EPA, logistic, then Ridge (raw vs adj EPA on 2009–2022). LightGBM / NGBoost / Power Index / ensemble after the holdout pass. [011](../research/011-model-lab-reproductions.md). Do not reopen holdout, ROI, or a v0.1 ensemble in [04](04-bcw-v0.1.md).

Still valid: Normal residuals before NGBoost; season walk-forward before weekly; SQLite until Model Lab works; no Docker/AWS yet; `vegas_wp` is not a PURE feature.

These items are **closed**. Do not re-ask them.

---

## Still open (answer anytime)

1. Paste `CFBD_API_KEY` into local `.env` when you have it (never commit). Academic vs free is your call; both are “get the key, don’t ingest.”
2. EWMA \(\alpha\) and Ridge \(\lambda\) — **only** on 2009–2022 walk-forward, after snapshots exist.

---

## When the agent should stop and ask

- Adding a paid API beyond CFBD Tier 2
- Using `vegas_wp` or close as a feature in a model labeled PURE
- **Opening 2023–2025** before features/hyperparams/calibration/metrics are frozen, or changing features after looking at it
- Adding injuries, weather, news, or QB-complexity to the **v0.1** feature freeze
- Making BCW-v0.1 an ensemble average
- Showing ROI, units, or a bankroll chart on the v0.1 leaderboard
- Publishing a naked cover % (no n, no interval, no model id)
- Silent overwrite on nflverse vs ESPN score conflict
- Live wager placement / tout copy
- AWS spend
- Making ChatGPT/MCP the only way to use BlueChip, or requiring a consumer OpenAI API key at signup
- Exposing GPT token counts or pricing as `OpenAI cost + margin`
- Leading the product as an “AI sports betting assistant”
