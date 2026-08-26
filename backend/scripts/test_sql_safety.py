#!/usr/bin/env python3
"""Hand-written battery of tests for the NLQ SQL safety layer. Run directly:

    cd backend && source venv/bin/activate && python scripts/test_sql_safety.py

This exercises app.nlq end-to-end against the real database (validate_sql +
enforce_business_scope + actual execution) — no LLM involved. Every "valid"
case must run and come back scoped to its business; every "attack" case
must be rejected with ValidationError, not merely fail some other way.
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

logging.getLogger("sqlglot").setLevel(logging.ERROR)  # silence benign parse-fallback notices

from app.database import SessionLocal  # noqa: E402
from app.nlq import ValidationError, run_safe_query  # noqa: E402

BUSINESS_ID = 1
OTHER_BUSINESS_ID = 2


def expect_valid(label: str, sql: str, business_id: int = BUSINESS_ID) -> bool:
    db = SessionLocal()
    try:
        rows = run_safe_query(sql, business_id, db)
        print(f"PASS  {label}  ({len(rows)} row(s))")
        return True
    except Exception as exc:
        print(f"FAIL  {label}  -- expected to run, but raised {type(exc).__name__}: {exc}")
        return False
    finally:
        db.close()


def expect_rejected(label: str, sql: str, business_id: int = BUSINESS_ID) -> bool:
    db = SessionLocal()
    try:
        run_safe_query(sql, business_id, db)
        print(f"FAIL  {label}  -- expected rejection, but it ran")
        return False
    except ValidationError as exc:
        print(f"PASS  {label}  -- rejected: {exc}")
        return True
    except Exception as exc:
        print(f"FAIL  {label}  -- rejected, but wrong exception type {type(exc).__name__}: {exc}")
        return False
    finally:
        db.close()


def test_scope_is_enforced() -> bool:
    """Prove the scope enforcer decides visibility, not the query text."""
    db = SessionLocal()
    try:
        rows = run_safe_query(
            f"SELECT * FROM products WHERE business_id = {OTHER_BUSINESS_ID}",
            business_id=BUSINESS_ID,
            db=db,
        )
    except Exception as exc:
        print(f"FAIL  scope enforcer: raised unexpectedly: {exc}")
        return False
    finally:
        db.close()

    if any(row.get("business_id") == OTHER_BUSINESS_ID for row in rows):
        print("FAIL  scope enforcer: another business's rows leaked through")
        return False
    if rows:
        print(
            "FAIL  scope enforcer: expected zero rows (business "
            f"{BUSINESS_ID} shouldn't have rows matching business_id="
            f"{OTHER_BUSINESS_ID}), got some anyway"
        )
        return False

    print(
        "PASS  scope enforcer strips an explicit foreign business_id "
        f"filter (query asked for business_id={OTHER_BUSINESS_ID} while "
        f"scoped to business_id={BUSINESS_ID}; got 0 rows either way)"
    )
    return True


def main() -> None:
    results = []

    # --- Valid queries: must run, scoped to the current business ---
    results.append(
        expect_valid(
            "valid: select columns from products",
            "SELECT name, quantity_in_stock FROM products",
        )
    )
    results.append(expect_valid("valid: select * from sales", "SELECT * FROM sales"))

    # --- Attacks: every one of these must be rejected ---
    results.append(expect_rejected("attack: DROP TABLE", "DROP TABLE products"))
    results.append(expect_rejected("attack: DELETE", "DELETE FROM products"))
    results.append(expect_rejected("attack: UPDATE", "UPDATE products SET cost_price = 0"))
    results.append(
        expect_rejected(
            "attack: stacked statements",
            "SELECT * FROM products; DROP TABLE products;",
        )
    )
    results.append(expect_rejected("attack: forbidden table (users)", "SELECT * FROM users"))
    results.append(
        expect_rejected("attack: trailing line comment", "SELECT * FROM products -- comment")
    )
    results.append(expect_rejected("attack: block comment", "SELECT * FROM products /* comment */"))
    results.append(expect_rejected("attack: pg_sleep", "SELECT pg_sleep(10)"))
    results.append(
        expect_rejected(
            "attack: INSERT",
            "INSERT INTO products (name, business_id, cost_price, selling_price) "
            "VALUES ('x', 1, 1, 2)",
        )
    )
    results.append(expect_rejected("attack: SELECT INTO", "SELECT * INTO x FROM products"))
    results.append(
        expect_rejected(
            "attack: writable CTE",
            "WITH x AS (DELETE FROM products RETURNING *) SELECT * FROM x",
        )
    )
    results.append(
        expect_rejected(
            "attack: information_schema", "SELECT * FROM information_schema.tables"
        )
    )
    results.append(
        expect_rejected("attack: pg_catalog", "SELECT * FROM pg_catalog.pg_tables")
    )
    results.append(expect_rejected("attack: TRUNCATE", "TRUNCATE TABLE products"))
    results.append(expect_rejected("attack: GRANT", "GRANT ALL ON products TO PUBLIC"))
    results.append(expect_rejected("attack: REVOKE", "REVOKE ALL ON products FROM PUBLIC"))
    results.append(expect_rejected("attack: COPY", "COPY products TO '/tmp/out.csv'"))
    results.append(expect_rejected("attack: CALL", "CALL some_procedure()"))
    results.append(expect_rejected("attack: empty query", ""))

    # --- Cross-tenant scope proof ---
    results.append(test_scope_is_enforced())

    passed = sum(1 for r in results if r)
    total = len(results)
    print()
    print(f"{passed} passed / {total - passed} failed (of {total})")
    if passed != total:
        sys.exit(1)


if __name__ == "__main__":
    main()
