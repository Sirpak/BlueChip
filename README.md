# BlueChipWager

NFL + CFB football intelligence — research desk UI, FastAPI, data pipeline, models.

**Status:** Research Preview. Walk-forward on **2009–2022** only. Sacred holdout **2023–2025** is sealed. Public cover % is not published. Market 0 remains the benchmark.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e ".[dev]"

copy .env.example .env
alembic upgrade head
python -m app.seed_users

# Pull & upsert play-by-play (nflfastR / nflverse parquet)
python -m app.ingest --from-season 1999 --to-season 2025
python -m app.ingest --schedules --from-season 1999 --to-season 2025
python -m ml.features.build
python -m ml.pregame.experiments
```

## Run the desk

```bash
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

UI (Vite + Three.js) lives in `web/`. Production build is served by FastAPI from `web/dist`:

```bash
cd web
npm install
npm run build
```

Open http://127.0.0.1:8000 — landing, research desk, games. JSON: `/games/upcoming`, `/api/dashboard`, `/api/markets/price`, `/docs`.

Frontend hot reload (API on :8000):

```bash
cd web
npm run dev
```

Local demo accounts (from `.env.example` / seed): `demo_free`, `demo_pro`, `demo_research`, `admin`.

Old Jinja calculator: `/legacy/markets`. Standings ingest view: `/legacy`.

## Layout

| Path | Role |
|------|------|
| `app/` | FastAPI app, ingest CLI, services, auth/entitlements |
| `db/` | SQLAlchemy models + Alembic migrations |
| `data/` | Local SQLite DB + cached raw parquet (not committed) |
| `ml/` | Model lab: `reference/nflfastr`, `pregame/`, `live/`, `evaluation/` |
| `web/` | Product UI — Vite, React, Three.js |

## Docs

BlueChipWager is a **probabilistic research platform**, not a pick-em bot. North star, architecture, phases, monetary roadmap, v0.1 freeze, and to-do live under [`docs/`](docs/README.md).

**Stack:** data → features → model → prediction store → research desk → Ask BlueChip. The LLM interrogates the desk; it does not invent football opinions.

v0.1 freeze (holdout, gates, Ridge as the published number): [`docs/roadmap/04-bcw-v0.1.md`](docs/roadmap/04-bcw-v0.1.md). Pricing / MCP: [`docs/roadmap/03-monetary.md`](docs/roadmap/03-monetary.md).

**Now:** extend Ridge λ / EWMA α on 2009–2022 only, then freeze, then open 2023–2025 once. Path: [02-phases.md](docs/roadmap/02-phases.md). Do not jump to LightGBM, Ask production, or CFB ingest.
