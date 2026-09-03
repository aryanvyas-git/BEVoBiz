# BEVoBIZ

Multi-tenant inventory & sales management SaaS for small businesses, with an AI assistant that answers plain-English questions about a business's own data by safely generating and running SQL.

[![Python](https://img.shields.io/badge/Python-3.9-3776AB?logo=python&logoColor=white)](backend/requirements.txt)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](backend/requirements.txt)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=black)](frontend/package.json)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](docker-compose.yml)
[![pgvector](https://img.shields.io/badge/pgvector-enabled-4169E1)](db/init/001_extensions.sql)
[![sqlglot](https://img.shields.io/badge/sqlglot-SQL%20safety%20layer-orange)](backend/app/nlq/validator.py)
[![Groq](https://img.shields.io/badge/Groq-LLM%20provider-F55036)](backend/app/llm/groq_adapter.py)

<!-- Drop a full-width screenshot of the dashboard (KPIs + charts) at docs/screenshots/dashboard.png -->
![BEVoBIZ dashboard](docs/screenshots/dashboard.png)

## What this is

A business owner signs up, tracks inventory, and records sales. Every table in the database carries a `business_id`, and every query in the app — no exceptions — is scoped to the authenticated user's own business. On top of that sits a natural-language search bar: a business owner can type a question like *"how many units of each product did I sell last month?"*, and the app generates the SQL, runs it safely, and returns an answer.

The interesting engineering problem here isn't the CRUD — it's **letting an LLM write and execute SQL against a real multi-tenant database without that being a standing security risk.** That's the core of this project, and the [How the AI stays safe](#how-the-ai-stays-safe) section below is the part worth reading closely.

## The standout feature — AI natural-language search

<!-- Drop a screenshot of a question being asked and answered (answer + table/chart) at docs/screenshots/nlq-search.png -->
![NLQ search in action](docs/screenshots/nlq-search.png)

This is text-to-SQL, not a set of canned reports. There's no fixed list of questions it can answer — the LLM writes a fresh PostgreSQL `SELECT` for whatever's asked, on demand.

Given a question typed into the search bar (`POST /nlq/ask`):

1. **Schema context** — a hand-written description of the `products` and `sales` tables (columns, meaning, the snapshot-pricing rule) is handed to the LLM as static context (`app/nlq/schema_context.py`). The schema is small enough today that this works well; vector-based retrieval is scaffolded for when it grows (see [Engineering notes](#engineering-notes)).
2. **SQL generation** — the configured LLM adapter turns the question into a single PostgreSQL `SELECT`.
3. **Safety pipeline** — the generated SQL is parsed, validated, rewritten to enforce tenant scoping, and executed under a locked-down database role. Explained in full below.
4. **Answer** — a second, separate LLM call (`app/nlq/summarize.py`) phrases a plain-English answer from the rows already fetched. It never touches the database and never generates SQL — a failure here can't affect what was already retrieved.
5. **Result** — the frontend shows the plain-English answer alongside a Table / Bar chart / Pie chart toggle (`NlqResultPanel.jsx`, `NlqChart.jsx`) and an expandable "Show query" panel with the exact SQL that ran. The chart view is generic — it works off whatever columns the query returns, with no hardcoded column names, and degrades to a friendly message when a result isn't chartable.

## How the AI stays safe

Running LLM-generated SQL against a real database is the riskiest thing this app does, so it's treated that way: **every layer assumes the others might fail.** A bug or a successful prompt injection in any single layer is not enough to leak another tenant's data, read the `users` table, or write anything.

| Layer | What it does | Where |
|---|---|---|
| **1. Parser-based validation** | Parses the candidate SQL with a real SQL parser (`sqlglot`) — not regex — and rejects anything that isn't exactly one read-only `SELECT`. This includes writes hidden inside a CTE (Postgres allows `WITH x AS (DELETE FROM ... RETURNING *) SELECT ...`), stacked statements, SQL comments, and dangerous functions (`pg_sleep`, `dblink*`, `pg_read_file`, etc). Only `products`, `sales`, and `businesses` may be referenced — `users` (password hashes) is not in the allowlist and can never be queried this way. | `app/nlq/validator.py` |
| **2. Mandatory business-scoping rewrite** | Rewrites *every* table reference the parsed query touches into a pre-filtered subquery — `products` becomes `(SELECT * FROM products WHERE business_id = :id) AS products` — so the result can only ever contain the current tenant's rows, regardless of what the LLM's SQL selects, joins, groups by, or omits entirely. `business_id` is always a bound parameter, never string-interpolated. | `app/nlq/scope.py` |
| **3. Dedicated low-privilege database role** | The executor connects as `bevobiz_nlq_reader`, a Postgres role with `SELECT` granted only on `products`/`sales`/`businesses` and no write grant anywhere, on any table. Even a hypothetical bug in layers 1 or 2 that let something slip through still can't produce a write or read `users` — the role is physically incapable of it, independent of any application code. | `db/init/002_nlq_readonly_role.sql`, `app/nlq/db.py` |
| **4. Read-only transaction, timeout, row cap** | Every query additionally runs inside `SET TRANSACTION READ ONLY`, is bounded by a 5-second `statement_timeout`, and is wrapped in a hard outer `LIMIT 1000` — independent of whatever `LIMIT` (or lack of one) the generated SQL contains. | `app/nlq/executor.py` |

This is backed by an automated safety test suite — 23 cases (`scripts/test_sql_safety.py`) that run the pipeline end-to-end against a real database: valid queries that must execute correctly, and attacks (`DROP TABLE`, `DELETE`, `UPDATE`, stacked statements, a writable CTE, `information_schema`/`pg_catalog` access, `pg_sleep`, `GRANT`/`REVOKE`, `COPY`, `CALL`, SQL comments, `SELECT INTO`, querying `users`, and more) that must every one be rejected — plus a dedicated check that cross-tenant scoping actually holds under a query that tries to filter to a *different* business's `business_id`.

## Other key features

<!-- Drop a screenshot of the inventory table/CRUD UI at docs/screenshots/inventory.png -->
![Inventory view](docs/screenshots/inventory.png)

- **Multi-tenant by construction.** Every domain table (`products`, `sales`, `users`) has a `business_id` foreign key, and every route derives it from the authenticated JWT — never from the request body. There is no endpoint that lets a client pass a `business_id`.
- **Inventory CRUD** with `Numeric(12, 2)` pricing (no float rounding drift) and a per-product `reorder_level`.
- **Snapshot pricing on sales.** Each sale line item stores `unit_cost_price` and `unit_selling_price` captured at the moment of sale, alongside the product's live-editable `cost_price`/`selling_price`. Historical profit is always computed from the snapshot columns, never the product's current price — so editing a product's price today can't silently rewrite last month's profit numbers. This is enforced at the schema-context level for the NLQ engine too (it's explicitly told never to join `sales` to `products` for pricing).
- **Overselling prevented server-side.** Recording a sale takes a row-level lock (`SELECT ... FOR UPDATE`) on the product before checking stock, so two concurrent sales against the same product can't both pass the stock check against a stale quantity.
- **Reorder thresholds + low-stock alerts**, computed from real inventory state and surfaced on the dashboard.
- **A real KPI dashboard** (`GET /dashboard/stats`) — inventory valuation (cost and retail), revenue, profit, units sold, a 30-day sales trend, top products, sales by category, and low-stock items — all computed with SQL aggregates over live data, not mocked.
- **Multi-format AI output.** Every NLQ answer is a plain-English headline plus a Table / Bar / Pie toggle over the same underlying rows.

## Architecture

```
┌──────────────┐      JWT (Bearer)      ┌───────────────────────────────────────────┐
│ React (Vite) │ ─────────────────────▶ │              FastAPI backend               │
│ frontend     │ ◀───────────────────── │  auth · products · sales · dashboard       │
└──────────────┘        JSON            │                                             │
                                         │  ┌───────────────────────────────────────┐ │
                                         │  │            NLQ pipeline                │ │
                                         │  │                                         │ │
                                         │  │  schema_context ──▶ LLM adapter         │ │
                                         │  │                        │ (Groq/Ollama)  │ │
                                         │  │                        ▼                │ │
                                         │  │              validator (sqlglot)        │ │
                                         │  │                        │                │ │
                                         │  │           enforce_business_scope        │ │
                                         │  │                        │                │ │
                                         │  │              scoped executor            │ │
                                         │  │        (bevobiz_nlq_reader role,        │ │
                                         │  │      READ ONLY txn, timeout, LIMIT)     │ │
                                         │  └────────────────────────┬────────────────┘ │
                                         └───────────────────────────┼──────────────────┘
                                                                      ▼
                                         ┌───────────────────────────────────────────┐
                                         │         PostgreSQL 16 + pgvector           │
                                         │   businesses · users · products · sales    │
                                         └───────────────────────────────────────────┘
```

**Swappable LLM adapter.** Every LLM-backed feature — SQL generation and answer summarization — goes through `app.llm.get_llm_adapter()`, never a provider class directly (`app/llm/base.py` defines the interface; `app/llm/factory.py` picks the implementation from `LLM_PROVIDER`). Today that's `GroqAdapter` (hosted, default) or `OllamaAdapter` (local/offline). Adding a third provider — OpenAI, a different hosted API — means adding one adapter module and one branch in the factory; no call site anywhere else in the codebase changes. The current default model, set in `backend/app/config.py`, is Groq's **`openai/gpt-oss-120b`**.

## Tech stack

**Backend**

| Library | Version | Role |
|---|---|---|
| FastAPI | 0.115.6 | API framework |
| SQLAlchemy | 2.0.36 | ORM |
| Alembic | 1.14.0 | Migrations |
| psycopg | 3.2.13 | Postgres driver |
| sqlglot | 30.17.0 | Parses & rewrites untrusted LLM-generated SQL |
| Pydantic | 2.10.4 | Request/response validation |
| PyJWT | 2.10.1 | JWT auth |
| passlib[bcrypt] | 1.7.4 | Password hashing |
| groq | 1.0.0 | Hosted LLM provider (default) |
| ollama | 0.6.2 | Local LLM provider |

**Frontend**

| Library | Version | Role |
|---|---|---|
| React | ^18.3.1 | UI |
| React Router | ^6.28.1 | Routing |
| Axios | ^1.7.9 | HTTP client |
| Recharts | ^3.10.1 | Bar/pie charts (dashboard + NLQ results) |
| Vite | ^5.4.11 | Dev server / build |

**Database & infra**

- PostgreSQL 16 with the **pgvector** extension (`pgvector/pgvector:pg16`), run via Docker Compose. pgvector is enabled today but not yet queried — it's in place for planned RAG-based schema grounding as the schema grows (see [Engineering notes](#engineering-notes)).
- A dedicated Postgres role, `bevobiz_nlq_reader`, with `SELECT`-only grants on `products`/`sales`/`businesses` (`db/init/002_nlq_readonly_role.sql`), used exclusively by the NLQ executor.

## Getting started

**Prerequisites:** Docker, Node.js, Python 3.9+, and a [Groq API key](https://console.groq.com) (free tier works) — or [Ollama](https://ollama.com) running locally if you'd rather not use a hosted API.

### 1. Start Postgres

```bash
docker compose up -d
```

Starts Postgres 16 with pgvector on `localhost:5432` (credentials from the root `.env` — copy `.env.example` first if you don't have one). On a fresh volume this also creates the `bevobiz_nlq_reader` role automatically.

### 2. Backend

```bash
cd backend
cp .env.example .env   # then edit — see env vars below
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

API at `http://localhost:8000`, Swagger docs at `http://localhost:8000/docs`.

Backend `.env` variables (see `backend/app/config.py` for defaults):

```bash
DATABASE_URL=postgresql+psycopg://bevobiz:bevobiz_dev_pw@localhost:5432/bevobiz
JWT_SECRET=change-me
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
FRONTEND_ORIGIN=http://localhost:5173

LLM_PROVIDER=groq              # or: ollama
LLM_MODEL=openai/gpt-oss-120b  # Groq model name; a local model name if using Ollama
GROQ_API_KEY=your-groq-api-key-here
OLLAMA_BASE_URL=http://localhost:11434

NLQ_DATABASE_URL=postgresql+psycopg://bevobiz_nlq_reader:bevobiz_nlq_reader_dev_pw@localhost:5432/bevobiz
```

To run fully offline, set `LLM_PROVIDER=ollama`, point `LLM_MODEL` at a model you've pulled locally, and drop `GROQ_API_KEY`.

### 3. Frontend

```bash
cd frontend
cp .env.example .env   # VITE_API_URL=http://localhost:8000
npm install
npm run dev
```

App at `http://localhost:5173`.

`backend/.env` and `frontend/.env` are gitignored — never commit real secrets; use the `.env.example` files as templates.

## Engineering notes

This was built in deliberate, reviewable phases rather than all at once — each one shipped and tested before the next started:

1. **Foundation & auth** — project scaffolding, Docker Compose Postgres+pgvector, Alembic, `businesses`/`users` tables, JWT signup/login/me.
2. **Inventory CRUD** — business-scoped `products` table and endpoints.
3. **Sales recording** — `sales` table with snapshot pricing, server-side stock decrement.
4. **NL-to-SQL engine** — the swappable LLM adapter, the sqlglot-based safety layer, the scoped executor, and `POST /nlq/ask`.
5. **Search bar UI** — the natural-language search bar, plain-English answers, and the table/bar/pie result view.
6. **Polish & hardening** — the dedicated read-only Postgres role for NLQ, a global exception handler so no endpoint ever leaks a stack trace, consistent loading/error/empty states, and a frontend fix for a real crash risk (a 422 validation error array being rendered directly as a React child).

**Deliberately not built (yet):**

- **RAG-based schema grounding.** The NLQ engine currently hands the LLM a static, hand-written schema description (`app/nlq/schema_context.py`) rather than retrieving relevant schema fragments via pgvector embeddings. With two tables, static context works well and retrieval would add complexity without benefit — pgvector is already wired into the database for when the schema grows enough to need it.
- **Suppliers & purchase orders, warehouses/multi-location support, and deeper analytics** — present in the UI as disabled "Coming soon" sidebar items, not yet implemented.

Being upfront about what's built versus what's scaffolded/planned is a deliberate choice — it's a more honest signal than pretending everything is finished.

## Author

**[Your Name]**
GitHub: [github.com/aryanvyas-git](https://github.com/aryanvyas-git) — repo: [BEVoBiz](https://github.com/aryanvyas-git/BEVoBiz)

License: MIT (or your choice) — no `LICENSE` file is currently present in this repo.
