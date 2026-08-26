"""Forces every base-table reference in a validated query onto one tenant.

Design choice — table-level rewrite, not an outer WHERE:

The obvious-looking approach is to wrap the whole query and add
`WHERE business_id = :business_id` on the outside. That only works if the
outer SELECT's column list happens to include business_id, which we can't
require of an LLM's output and don't want to — "SELECT name, quantity_in_stock
FROM products" must be scoped correctly even though business_id never
appears in it.

Instead, every real `exp.Table` node found anywhere in the parsed tree
(top-level FROM, JOINs, subqueries, and inside CTE bodies) is replaced with
a derived table that pre-filters that table down to the current tenant
before the rest of the query ever sees it:

    products  ->  (SELECT * FROM products WHERE business_id = :business_id) AS products

This holds regardless of what the outer query projects, groups, joins, or
nests, which is the actual invariant we need: the LLM's SQL can omit or
even try to override business_id and it doesn't matter — the row set
underneath every table reference is already scoped before that SQL runs.

business_id is bound as a parameter, never interpolated as a literal — see
_PARAM_NAME below for why that requires one extra step with sqlglot.
"""
import sqlglot
from sqlglot import exp

from app.nlq.errors import ValidationError
from app.nlq.validator import TABLE_FILTER_COLUMNS, check_tables, collect_cte_names

# sqlglot's Postgres dialect renders a `:name` placeholder as psycopg's
# native `%(name)s` pyformat style when generating SQL text (this is
# necessary elsewhere so that e.g. DATE_TRUNC round-trips as valid Postgres
# instead of being generated in a different SQL dialect's flavor). SQLAlchemy's
# text() wants `:name` regardless of driver, so after generating with
# dialect="postgres" we translate the one known pyformat token back to a
# colon placeholder with a plain string replace. Using a distinctive,
# unlikely-to-collide parameter name (rather than "business_id") keeps that
# replace from ever touching unrelated text an LLM's SQL might contain.
_PARAM_NAME = "__nlq_business_id"
_PYFORMAT_TOKEN = f"%({_PARAM_NAME})s"
_COLON_TOKEN = f":{_PARAM_NAME}"

BUSINESS_ID_PARAM = _PARAM_NAME


def enforce_business_scope(sql: str, business_id: int) -> str:
    """Rewrite `sql` so every allowed table it touches is pre-filtered to
    one tenant. Returns SQL with a `:__nlq_business_id` bind parameter —
    the caller must supply `{"__nlq_business_id": business_id}` as params
    when executing it. `business_id` here is only used to size-check
    nothing else; the actual value is never interpolated into the SQL text.
    """
    parsed = sqlglot.parse_one(sql, dialect="postgres")

    # Defense-in-depth: re-check the table allowlist here too, so this
    # function is safe even if it's ever called without validate_sql
    # having run first.
    check_tables(parsed)

    cte_names = collect_cte_names(parsed)
    replaced = 0

    for table in list(parsed.find_all(exp.Table)):
        name = table.name.lower()
        if name in cte_names:
            continue

        filter_column = TABLE_FILTER_COLUMNS[name]  # guaranteed present by check_tables
        alias = table.alias_or_name
        filtered = (
            exp.select("*")
            .from_(name)
            .where(f"{filter_column} = :{_PARAM_NAME}")
            .subquery(alias=alias)
        )
        table.replace(filtered)
        replaced += 1

    if replaced == 0:
        # check_tables already guarantees at least one allowed table is
        # referenced, so getting here means our own rewrite logic missed
        # something — fail closed rather than run an unscoped query.
        raise ValidationError("Could not scope query to the current business.")

    generated = parsed.sql(dialect="postgres")

    if generated.count(_PYFORMAT_TOKEN) != replaced:
        # Should be unreachable, but if it ever happens, fail closed
        # instead of silently executing a mis-scoped query.
        raise ValidationError("Could not safely bind business_id into the query.")

    return generated.replace(_PYFORMAT_TOKEN, _COLON_TOKEN)
