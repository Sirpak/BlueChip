# BlueChipWager / Project — Developer & AWS Implementation Roadmap

Locked 2026-08-18. Product freeze: [04-bcw-v0.1.md](04-bcw-v0.1.md). Phases: [02-phases.md](02-phases.md). Checkboxes: [TODO.md](TODO.md).

This is the implementation plan from the current state to a launchable product. Priorities: **finish the model foundation, clean up the user-facing product, separate admin functionality, add authentication, then deploy to AWS using serverless/on-demand infrastructure** (no idle ECS web servers).

---

## 1. Product navigation — user vs admin

### User-facing sidebar

Overview · Games · Ask BlueChip · Models · Markets · Teams · Backtests · Research · Pricing · Settings

### Remove from normal users

- API, Data, Health from public nav
- API access → Pricing / Research tier (Developer access section)
- Health, ingestion, DB status, model jobs, logs → **Administrator app only** (`/admin`)

**Status (2026-08-18):** User sidebar shipped in React desk. Pricing replaces API. Health/Data removed from nav. Admin shell next.

---

## 2. Models page — Model Lab

Production featured card (BCW-RIDGE-v0.1), reference models with status badges, detail pages (math, features, methodology, papers). **No fake metrics** before walk-forward. No train/retrain/promote for users.

**Status:** Model Lab + detail routes shipped. Ridge = In development until ship gates. Metrics empty until leaderboard.

---

## 3. Research page

BlueChip studies + external research + “How BlueChip uses this” + Data sources + Developer access footer. Later: RAG corpus.

**Status:** Shipped (categories expandable).

---

## 4. Backtests page

Walk-forward methodology, filters, metrics matrix. No ROI/units at launch.

**Status:** Shell shipped; interactive filters when leaderboard exists.

---

## 5. Administrator application (`/admin`)

Separate protected route. Roles: `USER`, `ADMIN`. Admin sidebar: dashboard, data pipeline, model ops, system health, logs, users.

**Status:** In progress (Sprint A).

---

## 6. Local authentication (before Cognito)

- Demo user from env (`AUTH_DEMO_*`), admin from env (`AUTH_ADMIN_*`)
- Password hashes only in DB; plaintext only in local `.env`
- Login UI; Google button disabled until Cognito
- Replace with **Project-Cognito** at AWS step 4

**Status:** In progress (Sprint A).

---

## 7–8. User header & authorization

Profile dropdown; Admin Console for ADMIN only. Backend enforces `403` on `/admin/*` and admin APIs — do not rely on hiding links.

---

## 9. Ask BlueChip

Conversation UI, sources, no invented BCW predictions. LLM retrieves saved model output or approved tools.

---

## 10. Pricing

Free / Pro $14.99 / Research (future). Stripe later.

**Status:** UI shipped.

---

## 11–30. AWS architecture (Project)

**Rule:** No continuously running ECS web server. Lambda on demand. Aurora Serverless auto-pause to 0 ACU. ECS Fargate **one-off jobs only** for ingest/train/predict.

```
GoDaddy DNS → CloudFront → API Gateway HTTP API → Project-Lambda (FastAPI)
                              ↓
                    Project-Cognito / Project-DB / Project-S3
                              ↑
              EventBridge → Project-ModelJobs (ECS task, exits)
```

Naming: `Project`, `Project-Dev`, `Project-Prod`, `Project-Lambda`, `Project-DB`, etc. Use **Bandium work AWS account** — verify with `aws sts get-caller-identity` before any deploy.

IaC: **AWS CDK (Python)** under `infra/`. Environments: Project-Dev, Project-Prod.

See full checklist in source spec (AWS steps 1–8, Sprints A–F). **Do not start Sprint F until NFL model gates pass** per [04-bcw-v0.1.md](04-bcw-v0.1.md).

---

## Application work order

| Sprint | Focus | Status |
|--------|--------|--------|
| **A** | Product shell, auth, `/admin` | Nav done; auth in progress |
| **B** | Models UX polish | Lab shipped; charts when metrics exist |
| **C** | Games UX (weeks, matchup pages) | Open |
| **D** | Core prediction (snapshots → Ridge → persist μ) | Snapshots done; Ridge next |
| **E** | Admin dashboards (pipeline, registry, logs) | After A |
| **F** | AWS (CDK, Lambda, Aurora, Cognito) | After D gates |
