# Monetary roadmap — BlueChip is the product

Locked 2026-08-17. Change only by explicit override. Engineering phases: [02-phases.md](02-phases.md). Product math: [00-product-vision.md](00-product-vision.md).

**Consult this file** for pricing, packaging, AI cost, ChatGPT/MCP, Stripe, usage caps, and “who pays for the LLM.” Do not invent a different commercial model in code or copy.

---

## What we sell

BlueChipWager is the product. Not “connect your own ChatGPT.”

> **BlueChip AI — Perplexity for NFL + college football.**
> Ask a football question, get an answer grounded in BlueChip’s models, historical play-by-play, injuries, weather, market data, research papers, news, and **source citations**.

A ChatGPT app / MCP connector is a **secondary distribution channel**, built after the hosted product works.

ChatGPT Plus/Pro does **not** include API credits a web app can spend. If BlueChip hosts chat, either **we pay the API bill** or the user brings a key. We pay, and we meter it. ([OpenAI: API vs ChatGPT subscriptions][openai-api-vs-sub])

```
BlueChip subscription  =  data + models + RAG + research
AI interface           =  BlueChip web  OR  ChatGPT (later)
```

The moat is everything GPT gets access to when it connects to BlueChip — not the textarea, and not paying for GPT.

---

## Positioning

Do **not** lead with “AI sports betting assistant.” Too generic, sounds like a tout.

# BlueChipWager

### Football Intelligence

> **Ask anything about NFL and college football.**

Underneath:

```
Search stats.
Compare teams.
Interrogate models.
Research matchups.
Understand market prices.
Trace every answer to its source.
```

Betting models are **one piece** of the intelligence system. The ceiling is questions like:

- How has Josh Allen performed against Cover 2?
- Which teams have improved most in EPA since Week 5?
- Find every game since 2015 where a road favorite of 6–7 had a top-5 EPA offense.
- Why did LightGBM disagree with the market on this game?
- Show papers on NFL home-field advantage.
- Which injured players matter most to this week’s spreads?
- Compare Georgia and Ohio State on opponent-adjusted metrics.

Identity stays a research terminal ([00-product-vision.md](00-product-vision.md)): probabilities vs market, citations, no “lock of the day.”

---

## Price on football value, not OpenAI cost

Do **not** price as `OpenAI cost + 20%`. Price the corpus, models, market engine, and citations. The LLM is the interface.

Target: **average AI variable cost well under 20–25% of subscription revenue.**

Example (internal, not customer-facing):

```
$2.40  OpenAI
$0.40  embeddings / retrieval
$0.30  infrastructure
─────
$3.10  variable  vs  $14.99 Pro
```

Plenty of gross margin before fixed opex and card fees — only if we RAG tightly and route cheap queries away from frontier models.

Comparable band (context, not a promise): Outlier-style sports research apps list roughly $20 / $30 / $80; Action Network paid plans often ~$20–30; Perplexity Pro has been ~$20. **$14.99 launch Pro is defensible** while coverage is thinner than incumbents. ([Outlier on App Store][outlier]; [Reuters on Perplexity][perplexity-price])

---

## Plans

Launch product is **Pro**. Free exists so people understand the desk. Meter internally by **AI credits / USD cost**, not “questions,” because one question can cost 10× another. The copy still talks about included research, not tokens.

| Plan | Price | Customer promise (directional) |
|------|------:|--------------------------------|
| **Free** | $0 | NFL + CFB dashboard, historical stats, basic model outputs, ~10 AI questions/month, limited citations and game research |
| **Pro** | **$14.99/mo** | Full NFL + CFB research, all BlueChip models, model-vs-market, injury/weather context, historical search, RAG + citations, ~150–250 AI questions/month*, saved history |
| **Research** | **$29.99/mo** | Everything in Pro, 500–1,000 AI questions/month*, deeper research mode, larger retrieval, model comparison, backtest explorer, advanced filters, export; API later |
| **API / Quant** | $49–99+/mo | REST, bulk history, model outputs, market snapshots, CSV, higher AI limits — serious users, not launch |

`*` Marketing shorthand. Ledger is credits.

### Credit packs (later)

Do not promise “250 questions.”

| Pack | Price | Role |
|------|------:|------|
| 250 BlueChip Research Credits | $5 | Overage / Free→Pro stepping stone |
| 1,000 Credits | $15 | Heavy month without upgrading |

Internal burn (can change models without changing the SKU):

| Work | Credits |
|------|--------:|
| Normal answer | 1 |
| Full matchup analysis | 3 |
| Deep research | 5 |

At 100% of included allowance:

> You've reached your included AI research allowance. Add 250 research credits for $5 or upgrade to Research.

---

## Do not sell tokens

Never show customers “You used 384,927 GPT tokens.”

**Customer UI**

```
BlueChip AI usage
──────────────────
Monthly included research
██████████████░░░░  72%
Resets Sep 1
```

At ~80%: “You've used 80% of your included BlueChip AI research for this billing cycle.”

**Internal ledger** (`ai_usage`): `user_id`, `request_id`, `model`, `input_tokens`, `cached_input_tokens`, `output_tokens`, `estimated_cost_usd`, `retrieval_count`, `created_at`.

**Subscriptions:** `plan`, `included_ai_credits`, `used_ai_credits`, `cycle_start`, `cycle_end`, `overage_enabled`.

Check remaining credits **before** an expensive call; record actuals after.

### Hard caps (internal risk, never advertised as USD)

One user must not wreck the OpenAI bill.

| Plan | Soft cap (us) | Hard cap (us) |
|------|--------------:|--------------:|
| Free | — | **$0.50**/user/month |
| Pro | $4 | **$6** unless overage enabled |
| Research | $10 | **$15** |

These are circuit breakers, not prices.

---

## Cost control: RAG + router, not a dump

Do **not** stuff 100k tokens of football into GPT. Retrieve a small package (aim 5k–10k useful tokens).

```
QUESTION → intent router → BlueChip retrieval
  (game, predictions, features, injuries, market, comps, articles)
  → small context → LLM → answer + citations
```

### Query router (this matters more than shaving pennies)

| Kind | Example | Path |
|------|---------|------|
| SIMPLE | “Buffalo EPA/play?” / last five games | SQL; no LLM or a tiny formatter |
| NORMAL | “Compare Buffalo and New England” | cheaper model |
| DEEP | full mispricing report (injuries, EPA, line move, comps) | strong reasoning model |

OpenAI API usage is metered separately from ChatGPT consumer plans, so we can attribute cost per request. ([OpenAI help][openai-api-vs-sub])

---

## Hybrid retrieval (Perplexity-shaped)

PDF → embeddings → GPT is **not** enough.

| Kind | Examples | Store |
|------|----------|--------|
| Structured | games, plays, teams, players, EPA, odds, injuries, weather, predictions, backtests | SQL |
| Unstructured | research notes, papers, news, injury reports, pressers, model docs | embeddings / vector |

Planner runs **both**, then a context builder, then the LLM.

**Citations are launch-blocking.** Every retrieved chunk needs `source_id`, title, URL, date. Do not ship Ask BlueChip without sources.

Example answer shape (not tout copy):

**BlueChip consensus:** Buffalo covers −6.5 at **56.2%** vs 52.38% break-even at −110.

Largest edges: passing EPA vs opponent pass defense. **Against:** OL questionables; NWS wind 17–22 mph.

| Model | P(cover) |
|-------|--------:|
| Elo | 52.1% |
| Logistic | 54.8% |
| Ridge margin | 55.7% |
| LightGBM | 57.4% |
| Prob. margin | 56.8% |
| **Consensus** | **56.2%** |

Sources: BlueChip model run timestamp, nflverse PBP, NFL injury report, NWS forecast, market snapshot.

---

## Tools: the AI must call the football engine

Not only retrieve docs. Tools (same layer for web AI and later MCP):

```
search_games / get_game
get_team_stats / get_player_stats
get_market_snapshot
get_model_predictions
run_matchup(home, away, spread)
search_news / get_injuries / search_research
find_similar_games
```

“What if the line moves from BUF −6.5 to −7?” → `run_matchup(..., spread=-7)` → table of cover/push probabilities. That is the killer feature.

---

## Distribution: web first, MCP second

OpenAI Apps can expose a service to ChatGPT via MCP. ([Apps in ChatGPT][openai-apps]) Full MCP is currently skewed to Business/Enterprise/Edu; Pro is more limited developer-mode read/fetch. ([Developer mode / MCP][openai-mcp]) **Do not make signup depend on another company’s plan matrix.**

```
BlueChip web (hosted AI)     ChatGPT / Claude / Cursor / other MCP
            \                       /
             \                     /
              same tools/ + API
                     |
              DATA + MODELS + RAG
```

Copy when MCP exists: “Already use ChatGPT? Connect BlueChip.” Bonus, not the funnel.

### Do not ask consumers for an OpenAI API key at launch

BYO key = our AI COGS ≈ 0, and **terrible** onboarding (OpenAI developer account, card, project, key, paste). Advanced developer option **later**. Mainstream: BlueChip-hosted AI included in the subscription.

---

## Target layout (when we build Ask BlueChip)

AI and MCP **share** `app/tools/`. That is required.

```
app/
  ai/          agent, intent router, prompts, citations
  tools/       games, teams, models, markets, injuries, research
  rag/         chunk, embed, retrieve, ingest
  mcp/         thin server over the same tools
```

`POST /api/ask` `{ "question": "..." }` → router → SQL and/or retrieval → answer + sources.

Vector store: Postgres + pgvector when we leave SQLite; until then, do not vectorize the whole NFL. Week-one tools can be SQL-only.

Usage tables sketched above belong in the Data Contract when auth exists — not before.

---

## Build order (commercial, not a substitute for Model Lab)

A credible **Ask BlueChip v0.1** is a 7–14 day slice **after** there is enough football engine to cite — not while we still lack 1999+ PBP and a pregame model. Ruthless scope: one Ask page, citations, a handful of tools. Not all of Perplexity.

| When | What |
|------|------|
| After models + auth make sense | Days 1–2: `app/ai`, `app/tools` (`get_games`, `get_game`, `get_team_metrics`, `get_model_prediction`, `get_market`). OpenAI SDK. pgvector later. |
| | Days 3–4: `POST /api/ask`, SQL-backed answers |
| | Days 5–6: doc RAG (our research notes, model docs, saved papers) |
| | Day 7: citations — **no launch without them** |
| Week two of Ask | injuries/news RAG, `run_matchup`, conversation history, auth, Stripe, `ai_usage`, rate limits |
| Only then | MCP server — cheap once tools exist |

Stripe, plans, and credit packs are **not** current coding. Current coding remains Data Contract + history + WP replication ([TODO.md](TODO.md)).

---

## Locked commercial calls

| Call | Decision |
|------|----------|
| Primary product | BlueChip-hosted Football Intelligence (web), $14.99 Pro launch |
| ChatGPT / MCP | Secondary client on the same tools/API |
| Consumer OpenAI key | No at launch |
| Customer metering | Research credits / % of included AI; never raw tokens |
| Wholesale pricing | Value of the football product; AI COGS target &lt; 20–25% of sub |
| Cost control | Intent router + tight RAG + internal USD hard caps |
| Citations | Required on every grounded answer |
| Tout copy | Forbidden; same as the research terminal |

---

## Sources

[openai-api-vs-sub]: https://help.openai.com/en/articles/8156019-is-api-usage-included-in-chatgpt-subscriptions-even-if-i-have-a-paid-chatgpt-account
[openai-apps]: https://help.openai.com/en/articles/11487775-connectors-in
[openai-mcp]: https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt-beta
[outlier]: https://apps.apple.com/us/app/outlier-smart-sports-betting/id6443885102
[perplexity-price]: https://www.reuters.com/business/paypal-venmo-users-gain-early-access-perplexitys-comet-ai-browser-2025-09-03/
