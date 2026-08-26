"""Gatekeeper for untrusted, LLM-generated SQL.

Every string that reaches `run_safe_query` (app.nlq.executor) is treated as
hostile input, no matter how it was produced. This module's job is to prove
a given string is a single, side-effect-free SELECT over our own known
tables before it's allowed anywhere near a database connection.

We lean on sqlglot (a real SQL parser) instead of regex for the structural
checks — regex can't reliably tell "a DELETE inside a CTE" from "the word
DELETE inside a string literal", but walking a parsed AST can. Regex is
still used for one thing regex is good at and parsers are bad at: refusing
to parse SQL containing comments at all, which is cheap defense-in-depth
against tricks that rely on how *other* tools (not sqlglot) tokenize
comments.
"""
import re

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from app.nlq.errors import ValidationError

# Tables an NLQ answer is allowed to touch. `users` holds password hashes
# and is deliberately never in this set — see CLAUDE.md hard rule 2.
ALLOWED_TABLES = {"products", "sales", "businesses"}

# Column used to scope each allowed table to the current tenant. Every
# table in ALLOWED_TABLES must have an entry here (enforced by tests).
# `businesses` has no business_id column — it's the row for the business
# itself, so it's scoped by its own primary key instead.
TABLE_FILTER_COLUMNS = {
    "products": "business_id",
    "sales": "business_id",
    "businesses": "id",
}

# Statement/DDL/DML node types that must never appear anywhere in the
# parsed tree — not just at the top level. Postgres allows data-modifying
# CTEs (`WITH x AS (DELETE FROM ... RETURNING *) SELECT * FROM x`), so a
# check that only looks at the root node type is not enough; we walk the
# whole tree for these. exp.Command is sqlglot's catch-all for statement
# types it has no dedicated class for (GRANT, REVOKE, COPY, CALL, VACUUM,
# LISTEN, etc.) — treating it as disallowed is what makes this an
# allowlist ("must parse as exactly exp.Select") rather than a blocklist.
_DISALLOWED_NODE_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,
    exp.Create,
    exp.TruncateTable,
    exp.Command,
)

# Function calls that can leak data, hang the connection, or mutate
# session/server state. These all parse as exp.Anonymous (sqlglot has no
# dedicated expression class for them) — safe aggregates like SUM/COUNT
# parse as their own classes and are untouched by this check.
_BLOCKED_FUNCTION_NAMES = {
    "pg_sleep",
    "pg_terminate_backend",
    "pg_cancel_backend",
    "pg_read_file",
    "pg_read_binary_file",
    "pg_ls_dir",
    "pg_reload_conf",
    "pg_rotate_logfile",
    "dblink",
    "dblink_connect",
    "dblink_exec",
    "lo_import",
    "lo_export",
    "lo_read",
    "lo_write",
    "set_config",
    "current_setting",
    "copy",
}

# Comments are a classic vector for smuggling tokens past a naive check,
# and there is no legitimate reason a natural-language question would
# need one in its generated SQL. Rejected outright, before parsing.
_COMMENT_PATTERN = re.compile(r"--|/\*")


def collect_cte_names(parsed: exp.Expression) -> set[str]:
    return {cte.alias.lower() for cte in parsed.find_all(exp.CTE) if cte.alias}


def _real_table_nodes(parsed: exp.Expression) -> list[exp.Table]:
    """All exp.Table nodes that reference an actual base table.

    Excludes references to CTE names (e.g. the `recent` in
    `WITH recent AS (...) SELECT * FROM recent`) — those aren't tables,
    they're names the query itself defined, and the real table inside the
    CTE's body is already covered separately by this same walk.
    """
    cte_names = collect_cte_names(parsed)
    return [t for t in parsed.find_all(exp.Table) if t.name.lower() not in cte_names]


def _check_single_select(parsed: exp.Expression) -> None:
    if not isinstance(parsed, exp.Select):
        raise ValidationError(
            f"Only SELECT statements are allowed (got {type(parsed).__name__})."
        )


def _check_no_dangerous_nodes(parsed: exp.Expression) -> None:
    disallowed = list(parsed.find_all(*_DISALLOWED_NODE_TYPES))
    if disallowed:
        kind = type(disallowed[0]).__name__
        raise ValidationError(
            f"Disallowed SQL construct: {kind}. Only a single read-only "
            "SELECT is allowed — this includes inside CTEs."
        )

    for select in parsed.find_all(exp.Select):
        if select.args.get("into"):
            raise ValidationError("SELECT INTO is not allowed.")


def _check_functions(parsed: exp.Expression) -> None:
    for func in parsed.find_all(exp.Anonymous):
        name = (func.name or "").lower()
        if name.startswith("pg_") or name in _BLOCKED_FUNCTION_NAMES:
            raise ValidationError(
                f"Function '{name}' is not allowed in natural-language queries."
            )


def check_tables(parsed: exp.Expression) -> list[exp.Table]:
    tables = _real_table_nodes(parsed)
    for table in tables:
        if table.db or table.catalog:
            raise ValidationError(
                "Schema-qualified table references are not allowed "
                f"(got '{table.sql()}')."
            )
        name = table.name.lower()
        if name not in ALLOWED_TABLES:
            raise ValidationError(
                f"Table '{name}' is not allowed in natural-language queries."
            )
    if not tables:
        raise ValidationError("Query must reference at least one allowed table.")
    return tables


def validate_sql(sql: str) -> str:
    """Validate untrusted SQL and return a cleaned, canonical version of it.

    Raises ValidationError (safe to display) if `sql` is anything other
    than a single, side-effect-free SELECT over an allowed table.
    """
    if not sql or not sql.strip():
        raise ValidationError("Empty query.")

    if _COMMENT_PATTERN.search(sql):
        raise ValidationError("SQL comments are not allowed.")

    try:
        statements = [s for s in sqlglot.parse(sql, dialect="postgres") if s is not None]
    except ParseError as exc:
        raise ValidationError(f"Could not parse SQL: {exc}") from exc

    if len(statements) != 1:
        raise ValidationError(
            "Only a single SQL statement is allowed (no stacked queries)."
        )

    parsed = statements[0]

    _check_single_select(parsed)
    _check_no_dangerous_nodes(parsed)
    _check_functions(parsed)
    check_tables(parsed)

    return parsed.sql(dialect="postgres")
