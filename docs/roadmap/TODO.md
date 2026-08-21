# To-do

Phases (plan of record): [02-phases.md](02-phases.md). Execute **1–15** before LightGBM / Ask / CFB / AWS. Decisions: [DECISIONS.md](DECISIONS.md). Freeze: [04-bcw-v0.1.md](04-bcw-v0.1.md). Money: [03-monetary.md](03-monetary.md).

Legend: `[ ]` open · `[~]` in progress · `[x]` done

---

## Done

- [x] Scaffold: FastAPI, SQLAlchemy, Alembic, SQLite
- [x] nflfastR loader, 2023–2025 PBP
- [x] Jinja dashboard + JSON
- [x] Vision / architecture / research notes in `docs/`
- [x] Data Contract v0.1 **spec**
- [x] Research foundation 008 (Stern, market-as-prior, EPA, key numbers)
- [x] Stage 1 market engine: `app/markets` + `/markets` + `/api/markets/price`
- [x] `ml/` lab layout: `reference/nflfastr`, `pregame/`, `live/`, `evaluation/`
- [x] BCW-NFL-WP-XGB-v0.1 feature engine + trainer (Python XGBoost; first metrics run still open)

---

## Now — two tracks (do not mix problems)

### A — Data Contract + NFL history (pregame path, before Elo)

Schema / identity (implement the spec)

- [x] `league` on every core table (default NFL)
- [x] `teams` + `team_external_ids`
- [x] `players` + `player_external_ids` (gsis from PBP)
- [x] Time/provenance fields as they appear (`known_at`, `retrieved_at`, `source`)
- [x] Promote `spread_line` → market snapshots: `market_source=nflverse_pfr`, `market_type=historical_close`

Data

- [x] Ingest nflverse PBP **1999–present** (cache parquet, upsert) — CLI: `python -m app.ingest --from-season 1999 --to-season 2025`
- [x] Ingest nflverse **schedules** (kickoff, rest, ML) — `python -m app.ingest --schedules --from-season 1999 --to-season 2025`
- [x] Data-quality asserts + tests
- [x] CI-oriented **leakage helpers** (even if feature engine is thin)

You (David)

- [ ] CFBD: `CFBD_API_KEY` is still missing from `.env`; one test request when it exists; **no CFB ingest**

### B — Live model lab (in-game WP/EP; can proceed from parquet now)

Does **not** open the pregame sacred holdout. Do not retune v0.1 features from WP metrics.

- [ ] Run `python -m ml.reference.nflfastr.wp_model --train-season 2023 --train-season 2024 --test-season 2025 --preset nflfastr_wp --save` and log experiment_id vs nflverse `wp`
- [ ] Same for `--preset bcw_v0.1`
- [ ] MARKET WP vs `vegas_wp` (`python -m ml.reference.nflfastr.vegas_wp_model`)
- [ ] EP multinomial trainer + EPA from our EP, not only nflverse `epa`
- [ ] Persist timeouts / `receive_2h_ko` on `plays` only if inference from SQLite is needed

Explicitly **not** now: LightGBM *pregame*, ESPN as canonical scores, NWS, Odds API, Docker, AWS, CFB rows.

---

## Then — Model Lab v0.1 (develop 2009–2022; holdout 2023–2025 once)

Freeze: [04-bcw-v0.1.md](04-bcw-v0.1.md) (reconfirmed 2026-08-18). Published number = **Ridge \(\mu\)** + Stern. No ensemble. No ROI.

- [x] Time-safe snapshots: **table is a superset** (`BCW-SNAP-v0.1`, 7,276 rows). [010](../research/010-snapshot-superset-vs-ridge.md). Rolling stats end at previous game. CLI: `python -m ml.features.build`
- [x] Automated leakage tests: `known_at_max < kickoff`, no current-game EPA in rolling, no `vegas_wp` in PURE
- [x] `BCW-HFA` — expanding REG home-margin mean on snapshots
- [x] `BCW-ELO` — hand-coded pre-update Elo on snapshots (1999–2008 initializes)
- [x] `BCW-SRS` — Massey linear SOS on snapshots; extra **baseline**, not an ensemble
- [x] `BCW-OPP-ADJ-EPA` — \(\mathrm{EPA} \approx \mathrm{Off}_i + \mathrm{Def}_j + \mathrm{HFA}\); prior opponent strength only
- [x] `BCW-LOGISTIC-v0.1` — `home_win`; pregame rolling features; walk-forward CLI
- [x] `BCW-RIDGE-v0.1` — published \(\mu\); raw vs adj EPA comparison on 2009–2022 (raw MAE 10.50 vs adj 10.58)
- [x] Season walk-forward **inside 2009–2022** — `python -m ml.pregame.walk_forward` → `data/walk_forward/BCW-WF-v0.1.json`
- [~] Leaderboard: Brier, log loss, MAE/RMSE, ATS vs close, ATS %, n, bootstrap intervals — vs Market 0 (dev search + `/api/models/leaderboard`)
- [~] Calibration buckets + Platt/isotonic inside walk-forward (desk chart still pending)
- [x] Immutable versioned predictions + `prediction_at` for `BCW-RIDGE-PURE` / `v0.1-candidate` (2009–2022 OOS)
- [ ] Start-year A–D (1999/2006/2009/2015–2022) — **one** 2023–2025 pass after freeze
- [~] Upcoming slate: market next to Research Preview Ridge μ (no public cover %). Bind snapshots to ESPN ids next.

Catalog: [011](../research/011-model-lab-reproductions.md). After freeze: LightGBM, NGBoost, \(F_M\), classifier shootout, Power Index, consensus.

**Next generation:** W2A matchup stats + W2B Game Intelligence Package + W3 EDGE/brief UI are **in code** ([012](../research/012-matchup-interaction-engine.md)). Still do **not** feed MATCHUP SIGNAL into Ridge freeze. Finish Wave 1 (Model Launch) in parallel.

---

## Sprint A — Product shell & auth ([05-project-aws-roadmap.md](05-project-aws-roadmap.md))

- [x] User sidebar (no API / Data / Health in public nav)
- [x] Pricing page + Developer access section
- [x] Model Lab + Research + Backtests shells (honest status)
- [x] Local auth (bcrypt, session cookie, demo/admin from `.env`)
- [x] Login page + profile menu + `/admin` shell
- [x] Role + plan entitlements (`FREE`/`PRO`/`RESEARCH`/`INTERNAL`), quotas, seed accounts
- [x] Admin pipeline / logs / experiments / predictions JSON pages
- [ ] Cognito / AWS / Stripe (Sprint F — after model gates)

---

- [ ] LightGBM
- [ ] Normal residual (then richer distributions); \(P(M>x)\), \(P(M=x)\) push
- [x] `app/markets/` American + de-vig + Stern (Stage 1)
- [ ] CFBD ingest (same IDs + `league=CFB`)
- [ ] NWS forecast vs observation
- [ ] Injuries / depth / `known_at`
- [ ] Odds API free snapshots
- [ ] Sacred holdout discipline documented in each `experiment_id`

---

## Parking lot / never required

- Hard-coded `bye = +2.5`
- Shuffled `train_test_split`
- Dumping full news articles into the model
- Silent score overwrite across sources
- Labeling nflverse close as `vegas`
- GPU / SageMaker / Kubernetes
- ChatGPT as the **primary** product or signup funnel
- Consumer BYO OpenAI API key at launch
- Showing customers GPT token counts
- Leading as “AI sports betting assistant”
- v0.1 ensemble “consensus” average
- ROI / units / bankroll on the v0.1 leaderboard
- Injuries, weather, news, or fancy QB in the **v0.1** feature freeze
