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
5. **Phase 5 — Search bar UI** (complete): natural-language search bar on
   the dashboard calling `POST /nlq/ask`, with a plain-English answer
   headline, a Table/Bar chart/Pie chart view toggle (generic — no
   hardcoded column names, degrades to a friendly message when a result
   isn't chartable), and an expandable "Show query" SQL detail. The
   backend also gained a second, rows-only LLM call
   (`app.nlq.summarize_answer`) that phrases the natural-language answer
   without touching the database or generating SQL.
6. **Phase 6 — Polish & hardening** (complete): a dedicated low-privilege
   Postgres role (`bevobiz_nlq_reader` — SELECT-only on
   products/sales/businesses, no write grant anywhere, no access to
   users; see `db/init/002_nlq_readonly_role.sql`) that `app.nlq.executor`
   now connects as via its own engine (`app.nlq.db`), instead of reusing
   the app's normal role — this closes the item deferred from Phase 4
   sub-step 4b. Also: fixed the known 4d gap where a zero-row NLQ result
   reported empty `columns`; a global exception handler so no endpoint
   ever leaks a stack trace; consistent loading/error/empty states
   app-wide; a shared frontend error-message helper (fixes a real crash
   risk where a 422 validation array was rendered directly as a React
   child); basic input-length/range validation on every POST/PUT body.

## Current phase

**Phase 6 is complete.** Phases 1–6 (foundation through hardening) are
done, tested, and pushed. Do not build new product features without an
explicit new phase — this file should be updated whenever one starts.
