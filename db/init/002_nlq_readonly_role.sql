-- Dedicated low-privilege Postgres role for the NLQ (natural-language
-- query) safe executor — see backend/app/nlq/executor.py and
-- backend/app/nlq/db.py.
--
-- This role can only ever SELECT from products, sales, and businesses.
-- It has no write grant anywhere (INSERT/UPDATE/DELETE/TRUNCATE/DDL are
-- all impossible for it, not just disallowed by application logic), and
-- no access at all to `users` (password hashes).
--
-- This is Postgres-level defense-in-depth ON TOP OF the application-level
-- safety layer (validate_sql -> enforce_business_scope -> READ ONLY
-- transaction -> statement_timeout -> row cap). Even a hypothetical bug
-- that let a write statement slip past every one of those layers would
-- still be rejected by Postgres itself, because this role has nothing to
-- write with.
--
-- Idempotent — safe to re-run. Runs automatically on a fresh
-- `docker compose up` (anything in db/init/ is executed once, in filename
-- order, the first time the Postgres data volume is created). For an
-- already-running database — e.g. this project's existing dev volume —
-- apply it manually:
--
--   docker exec -i bevobiz_db psql -U bevobiz -d bevobiz < db/init/002_nlq_readonly_role.sql
--
-- The password below is a local-dev default, same convention as the
-- existing bevobiz_dev_pw default in .env.example — change it before
-- using this anywhere beyond local development, and update
-- NLQ_DATABASE_URL in backend/.env to match.

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'bevobiz_nlq_reader') THEN
    CREATE ROLE bevobiz_nlq_reader WITH LOGIN PASSWORD 'bevobiz_nlq_reader_dev_pw';
  END IF;
END
$$;

GRANT CONNECT ON DATABASE bevobiz TO bevobiz_nlq_reader;
GRANT USAGE ON SCHEMA public TO bevobiz_nlq_reader;

GRANT SELECT ON products TO bevobiz_nlq_reader;
GRANT SELECT ON sales TO bevobiz_nlq_reader;
GRANT SELECT ON businesses TO bevobiz_nlq_reader;

-- Deliberately no grant on `users` — never queryable via NLQ.
-- Deliberately no INSERT/UPDATE/DELETE/TRUNCATE grant anywhere, on any
-- table, ever, for this role.
--
-- New tables are NOT automatically visible to this role: if a future
-- migration adds a table that should be queryable via NLQ, add an
-- explicit `GRANT SELECT ON <table> TO bevobiz_nlq_reader;` line above
-- (and add it to app.nlq.validator.ALLOWED_TABLES /
-- TABLE_FILTER_COLUMNS too). This fails closed by design.
