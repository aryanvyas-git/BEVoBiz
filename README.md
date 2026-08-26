# BEVoBIZ

Multi-tenant inventory + sales management SaaS. See `CLAUDE.md` for the
project summary, hard rules, and phase plan.

## Phase 1 — run order

Run these steps in order from the `BEVoBIZ` project root.

### 1. Start Postgres (with pgvector)

```bash
docker compose up -d
```

This starts Postgres 16 with the pgvector extension on `localhost:5432`
(credentials come from the root `.env` — copy `.env.example` if you
don't have one yet). On a fresh database volume this also creates the
`bevobiz_nlq_reader` low-privilege role used by the AI search feature
(see `db/init/002_nlq_readonly_role.sql`). If you already had a database
volume from before this role existed, apply it manually once:

```bash
docker exec -i bevobiz_db psql -U bevobiz -d bevobiz < db/init/002_nlq_readonly_role.sql
```

### 2. Configure and run the backend

```bash
cd backend
cp .env.example .env   # edit JWT_SECRET etc. if needed
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

The API is now running at `http://localhost:8000`. Swagger docs at
`http://localhost:8000/docs`.

### 3. Configure and run the frontend

In a new terminal:

```bash
cd frontend
cp .env.example .env   # defaults to http://localhost:8000
npm install
npm run dev
```

The app is now running at `http://localhost:5173`.

### 4. Try it out

- Go to `http://localhost:5173/signup`, create a business + account.
- You're redirected to the dashboard, showing "Welcome, {business name}".
- Refresh the page — you stay logged in.
- Click Logout — you're returned to the login page.

## Security

The AI search bar (`POST /nlq/ask`) lets a user's own plain-English
question drive LLM-generated SQL against the database. Since that SQL is
untrusted input no matter how it was produced, every generated query
passes through several independent layers before touching real data —
each one assumes the others might fail:

1. **SELECT-only, by parsing, not by prompting.** `app/nlq/validator.py`
   parses candidate SQL with a real SQL parser (sqlglot) and rejects
   anything that isn't exactly one read-only `SELECT` — including writes
   hidden inside a CTE (Postgres allows `WITH x AS (DELETE ...) SELECT
   ...`), stacked statements, comments, and dangerous functions
   (`pg_sleep`, `dblink*`, etc). Only `products`, `sales`, and
   `businesses` may be referenced; `users` (password hashes) is never
   queryable, and no other table or schema (`information_schema`,
   `pg_catalog`, ...) is reachable.
2. **Mandatory business scoping.** `app/nlq/scope.py` rewrites every table
   reference the query touches into a pre-filtered subquery
   (`products` → `(SELECT * FROM products WHERE business_id = :id) AS
   products`), so a result can only ever contain the current user's own
   business's rows — regardless of what the LLM's SQL selects, joins, or
   omits. `business_id` is always a bound parameter, never
   string-interpolated.
3. **A dedicated low-privilege database role.** The executor connects as
   `bevobiz_nlq_reader` (see `db/init/002_nlq_readonly_role.sql`), a
   Postgres role with `SELECT` on `products`/`sales`/`businesses` and
   nothing else — no write grant anywhere, on any table. Even a
   hypothetical bug in (1) or (2) still can't produce a write, because
   the role has none to give.
4. **A read-only transaction, a statement timeout, and a row cap.**
   `app/nlq/executor.py` also runs every query inside `SET TRANSACTION
   READ ONLY`, bounds it with a 5-second `statement_timeout`, and caps
   the result at 1000 rows regardless of what the query itself asks for.

The natural-language *answer* (`app/nlq/summarize.py`) is a second,
separate LLM call that only ever sees rows already fetched through this
entire pipeline — it never touches the database and never generates SQL.

Every domain route (`/products/*`, `/sales/*`, `/nlq/ask`) requires
authentication and is scoped to `current_user.business_id`; there is no
endpoint that accepts a `business_id` from the request body. Unhandled
exceptions never reach the client as a stack trace — a catch-all handler
in `app/main.py` returns a generic `{"detail": "..."}` JSON body and logs
the real error server-side.

See `scripts/test_sql_safety.py` for the safety-layer test battery.

## Notes

- `backend/.env` and `frontend/.env` are gitignored — use the
  `.env.example` files as templates.
- Adding new tables later: create the SQLAlchemy model, import it in
  `backend/app/models/__init__.py`, then run
  `alembic revision --autogenerate -m "..."` followed by
  `alembic upgrade head`.
