"""Runs untrusted SQL that has passed through the full NLQ safety pipeline.

This is the only function in the codebase that should ever execute
LLM-generated SQL. It doesn't trust its own callers either: it always
re-runs validate_sql + enforce_business_scope itself rather than accepting
already-validated SQL, and it stacks independent defenses (a dedicated
low-privilege DB role, a Postgres READ ONLY transaction, statement_timeout,
a hard row LIMIT) so that a bug in any single layer isn't enough to cause
damage or a hang.
"""
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy import text

from app.nlq.db import nlq_engine
from app.nlq.scope import BUSINESS_ID_PARAM, enforce_business_scope
from app.nlq.validator import validate_sql

MAX_ROWS = 1000
STATEMENT_TIMEOUT_MS = 5000

_ROW_LIMIT_PARAM = "__nlq_row_limit"


def _jsonable(value: Any) -> Any:
    """Make DB values safe to hand back as plain JSON."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    return value


def run_safe_query(sql: str, business_id: int) -> tuple[list[str], list[dict]]:
    """Validate, scope, and execute untrusted SQL for one business.

    Returns (columns, rows) — columns come from the query's own result
    metadata, so they're correct even when zero rows come back.

    Layered defenses, each independent of the others:
      1. validate_sql — structural allowlist (single SELECT, known
         tables only, no writes anywhere in the tree including inside
         CTEs, no comments, no stacked statements).
      2. enforce_business_scope — rewrites every table reference so only
         the current tenant's rows are visible, regardless of what the
         query selects, groups, or joins, and regardless of whether it
         mentions business_id at all.
      3. A dedicated Postgres role (bevobiz_nlq_reader) that can only
         SELECT from products/sales/businesses — see app.nlq.db. Even a
         bug in (1) or (2) can't produce a write; the role has none to give.
      4. A Postgres READ ONLY transaction, belt-and-suspenders on top of (3).
      5. statement_timeout — bounds how long a single query may run.
      6. A hard outer LIMIT — bounds how many rows a single query can
         return, independent of any LIMIT (or lack of one) in the SQL.
    """
    cleaned_sql = validate_sql(sql)
    scoped_sql = enforce_business_scope(cleaned_sql, business_id)
    limited_sql = f"SELECT * FROM ({scoped_sql}) AS __nlq_result LIMIT :{_ROW_LIMIT_PARAM}"

    # A fresh connection dedicated to this one query, so there's no risk
    # of an earlier statement on some shared session having already
    # started a transaction — SET TRANSACTION READ ONLY is guaranteed to
    # be the first statement of its transaction, as Postgres requires.
    with nlq_engine.connect() as conn:
        with conn.begin():
            conn.execute(text("SET TRANSACTION READ ONLY"))
            # SET LOCAL doesn't accept bind parameters in Postgres; the
            # value here is our own hardcoded constant, never user input.
            conn.execute(text(f"SET LOCAL statement_timeout = {STATEMENT_TIMEOUT_MS}"))
            result = conn.execute(
                text(limited_sql),
                {BUSINESS_ID_PARAM: business_id, _ROW_LIMIT_PARAM: MAX_ROWS},
            )
            columns = list(result.keys())
            rows = [dict(row._mapping) for row in result]

    jsonable_rows = [{key: _jsonable(value) for key, value in row.items()} for row in rows]
    return columns, jsonable_rows
