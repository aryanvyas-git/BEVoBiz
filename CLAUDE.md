# BEVoBIZ

## Project summary

BEVoBIZ is a multi-tenant inventory + sales management SaaS for small
businesses. Each business (tenant) tracks its own inventory and sales.
A later phase adds an AI natural-language-to-SQL search bar so business
owners can ask plain-English questions about their data ("what were my
top 5 products last month?") and get back a table/chart answer.

## Stack

- **Frontend:** React (Vite), React Router, Axios
- **Backend:** FastAPI (Python), SQLAlchemy, Alembic, JWT auth (PyJWT),
  passlib[bcrypt] for password hashing
- **Database:** PostgreSQL 16 with the pgvector extension, run via Docker
  Compose
- **LLM access:** a single swappable adapter interface. Ollama (local) is
  the first implementation; the adapter must make it trivial to swap in
  Groq or a paid hosted API later without touching call sites.

## HARD RULES (apply in every phase, no exceptions)

1. **Tenant isolation.** Every domain table has a `business_id` column.
   Every query — reads and writes — is scoped to the current
   authenticated user's `business_id`. There is no cross-tenant access,
   ever, including in admin tooling or the AI search path.
2. **AI search is READ-ONLY.** The natural-language-to-SQL engine may
   only ever generate and execute `SELECT` statements. It must never be
   able to run INSERT/UPDATE/DELETE/DDL, regardless of what the user
   asks for. This is enforced by a safety layer, not just prompting.
3. **Sales snapshot pricing.** Sale line items must store
   `unit_cost_price` and `unit_selling_price` as captured at the moment
   of sale. Historical profit is always computed from these snapshot
   columns — never recalculated from a product's *current* price, which
   would silently rewrite history when prices change.
4. **One LLM adapter.** All LLM access goes through a single swappable
   adapter interface. No direct model/API calls scattered through
   routers, services, or scripts. Swapping providers (Ollama → Groq →
   paid API) should mean changing one implementation, not hunting
   through the codebase.

## Phase plan

1. **Phase 1 — Foundation & Auth**: project scaffolding, Docker Compose
   Postgres+pgvector, Alembic, `businesses`/`users` tables, JWT
   signup/login/me, React auth pages + protected dashboard.
2. **Phase 2 — Inventory CRUD**: products table (business-scoped), CRUD
   endpoints and UI.
3. **Phase 3 — Sales recording**: sales + sale line item tables with
   snapshot pricing (see hard rule 3), recording UI.
4. **Phase 4 — NL-to-SQL engine** (complete): swappable LLM adapter +
   Ollama, a SELECT-only SQL safety/validation layer with a scoped
   read-only executor, an LLM SQL-generation pipeline on top of it, and
   a protected `POST /nlq/ask` endpoint. Vector/RAG schema grounding was
   deliberately **not** built — the current two-table schema is small
   enough for static schema context to work well; logged as a future
   enhancement (see `backend/app/nlq/schema_context.py`) for whenever the
   schema grows enough to need it.
5. **Phase 5 — Search bar UI** (current phase): natural-language input
   with table, bar chart, and pie chart output rendering, calling
   `POST /nlq/ask`.
6. **Phase 6 — Polish & hardening**: production hardening, error
   handling, security review, UX polish. Includes: create a dedicated
   low-privilege Postgres role (SELECT-only on products/sales/businesses,
   no write grants anywhere) for the NLQ executor to connect as, instead
   of reusing the app's normal role. Deferred from Phase 4 sub-step 4b —
   the validator + business-scope rewrite + per-query READ ONLY
   transaction already make writes structurally unreachable, so this is
   an additional defense-in-depth layer, not a gap in the current one.

## Current phase

**Phase 5.** Phase 4 is complete: LLM adapter (4a), SQL safety layer (4b),
question-to-SQL pipeline (4c), and the `POST /nlq/ask` endpoint (4d) are
all built and verified under `backend/app/nlq/` and `backend/app/llm/`.
RAG/vector schema grounding was deliberately deferred (see Phase 4 note
above) — not a gap, a deferred enhancement for when the schema is bigger.
Scope now is the Phase 5 search bar UI: a natural-language input calling
`POST /nlq/ask`, rendering its `rows`/`columns` as a table plus bar/pie
chart views. Do not build Phase 6 hardening yet.
