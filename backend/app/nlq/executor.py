"""Runs untrusted SQL that has passed through the full NLQ safety pipeline.

This is the only function in the codebase that should ever execute
LLM-generated SQL. It doesn't trust its own callers either: it always
re-runs validate_sql + enforce_business_scope itself rather than accepting
already-validated SQL, and it stacks independent defenses (Postgres
READ ONLY transaction, statement_timeout, hard row LIMIT) so that a bug in
any single layer isn't enough to cause damage or a hang.
"""
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

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


def run_safe_query(sql: str, business_id: int, db: Session) -> list[dict]:
    """Validate, scope, and execute untrusted SQL for one business.

    Layered defenses, each independent of the others:
      1. validate_sql — structural allowlist (single SELECT, known
         tables only, no writes anywhere in the tree including inside
         CTEs, no comments, no stacked statements).
      2. enforce_business_scope — rewrites every table reference so only
         the current tenant's rows are visible, regardless of what the
         query selects, groups, or joins, and regardless of whether it
         mentions business_id at all.
      3. A Postgres READ ONLY transaction — even if something slipped
         past (1) and (2), the database itself refuses any write.
      4. statement_timeout — bounds how long a single query may run.
      5. A hard outer LIMIT — bounds how many rows a single query can
         return, independent of any LIMIT (or lack of one) in the SQL.
    """
    cleaned_sql = validate_sql(sql)
    scoped_sql = enforce_business_scope(cleaned_sql, business_id)
    limited_sql = f"SELECT * FROM ({scoped_sql}) AS __nlq_result LIMIT :{_ROW_LIMIT_PARAM}"

    # A prior dependency in this request (e.g. auth, reading the current
    # user) may have already opened an implicit transaction on this
    # session. `SET TRANSACTION READ ONLY` must be the first statement of
    # its transaction, so start from a clean one.
    db.rollback()

    try:
        db.execute(text("SET TRANSACTION READ ONLY"))
        # SET LOCAL doesn't accept bind parameters in Postgres; the value
        # here is our own hardcoded constant, never user input.
        db.execute(text(f"SET LOCAL statement_timeout = {STATEMENT_TIMEOUT_MS}"))
        result = db.execute(
            text(limited_sql),
            {BUSINESS_ID_PARAM: business_id, _ROW_LIMIT_PARAM: MAX_ROWS},
        )
        rows = [dict(row._mapping) for row in result]
    finally:
        db.rollback()  # read-only query: nothing to persist either way

    return [{key: _jsonable(value) for key, value in row.items()} for row in rows]
