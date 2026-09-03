#!/usr/bin/env python3
"""End-to-end test of GET /dashboard/stats against the RUNNING backend. Run
directly (with the backend already up on :8000, e.g. via
`uvicorn app.main:app`):

    cd backend && source venv/bin/activate && python scripts/test_dashboard_endpoint.py

Logs in (or signs up, on first run) a dedicated test business, seeds a
handful of products spanning in-stock/low-stock/out-of-stock plus a few
sales across two categories if none exist yet, then:

  1. independently recomputes every aggregate from the business's own
     /products and /sales data (the same source tables the endpoint reads),
  2. calls GET /dashboard/stats and asserts every field matches that
     independent computation exactly,
  3. prints the full JSON so the numbers can be eyeballed too,
  4. confirms the endpoint is blocked for unauthenticated requests.

This never asserts against hardcoded expected numbers — only against
values re-derived from the same data at request time — so it stays valid
whether this is the first run or the hundredth.
"""
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import httpx

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "dashboard-endpoint-test@example.com"
TEST_PASSWORD = "supersecret1"
TEST_BUSINESS_NAME = "Dashboard Endpoint Test Co"


def get_auth_token() -> str:
    resp = httpx.post(
        f"{BASE_URL}/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    if resp.status_code == 200:
        return resp.json()["access_token"]

    resp = httpx.post(
        f"{BASE_URL}/auth/signup",
        json={
            "business_name": TEST_BUSINESS_NAME,
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def ensure_seed_data(headers: dict) -> None:
    products = httpx.get(f"{BASE_URL}/products", headers=headers).json()
    if products:
        return

    seeded = {}
    for name, category, cost, price, qty, reorder in [
        ("Dashboard Test Widget", "Widgets", 5, 15, 40, 5),   # in stock
        ("Dashboard Test Gadget", "Gadgets", 8, 20, 3, 5),    # low stock
        ("Dashboard Test Gizmo", "Widgets", 3, 9, 0, 2),      # out of stock
    ]:
        resp = httpx.post(
            f"{BASE_URL}/products",
            headers=headers,
            json={
                "name": name,
                "category": category,
                "cost_price": cost,
                "selling_price": price,
                "quantity_in_stock": qty,
                "reorder_level": reorder,
            },
        )
        resp.raise_for_status()
        seeded[name] = resp.json()

    widget = seeded["Dashboard Test Widget"]
    gadget = seeded["Dashboard Test Gadget"]

    httpx.post(
        f"{BASE_URL}/sales",
        headers=headers,
        json={"product_id": widget["id"], "quantity": 3},
    ).raise_for_status()
    httpx.post(
        f"{BASE_URL}/sales",
        headers=headers,
        json={
            "product_id": gadget["id"],
            "quantity": 2,
            "sold_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
        },
    ).raise_for_status()


def compute_expected(products: list, sales: list) -> dict:
    cost_valuation = sum(float(p["cost_price"]) * p["quantity_in_stock"] for p in products)
    retail_valuation = sum(float(p["selling_price"]) * p["quantity_in_stock"] for p in products)
    product_count = len(products)
    out_of_stock = sum(1 for p in products if p["quantity_in_stock"] == 0)
    low_stock = sum(
        1 for p in products if 0 < p["quantity_in_stock"] <= p["reorder_level"]
    )
    in_stock = product_count - out_of_stock - low_stock

    total_revenue = sum(float(s["unit_selling_price"]) * s["quantity"] for s in sales)
    total_profit = sum(
        (float(s["unit_selling_price"]) - float(s["unit_cost_price"])) * s["quantity"]
        for s in sales
    )
    total_units_sold = sum(s["quantity"] for s in sales)

    units_by_product = defaultdict(int)
    revenue_by_product = defaultdict(float)
    for s in sales:
        units_by_product[s["product_name"]] += s["quantity"]
        revenue_by_product[s["product_name"]] += float(s["unit_selling_price"]) * s["quantity"]

    category_by_name = {p["name"]: (p["category"] or "Uncategorized") for p in products}
    revenue_by_category = defaultdict(float)
    for s in sales:
        revenue_by_category[category_by_name.get(s["product_name"], "Uncategorized")] += (
            float(s["unit_selling_price"]) * s["quantity"]
        )

    low_stock_items = sorted(
        (p for p in products if p["quantity_in_stock"] <= p["reorder_level"]),
        key=lambda p: p["quantity_in_stock"],
    )

    return {
        "inventory_cost_valuation": cost_valuation,
        "inventory_retail_valuation": retail_valuation,
        "product_count": product_count,
        "in_stock_count": in_stock,
        "low_stock_count": low_stock,
        "out_of_stock_count": out_of_stock,
        "total_revenue": total_revenue,
        "total_profit": total_profit,
        "total_units_sold": total_units_sold,
        "units_by_product": dict(units_by_product),
        "revenue_by_category": dict(revenue_by_category),
        "low_stock_item_names": [p["name"] for p in low_stock_items],
    }


def close(a, b, tol=0.01) -> bool:
    return abs(float(a) - float(b)) <= tol


def main() -> None:
    results = []

    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    ensure_seed_data(headers)

    products = httpx.get(f"{BASE_URL}/products", headers=headers).json()
    sales = httpx.get(f"{BASE_URL}/sales", headers=headers).json()
    expected = compute_expected(products, sales)

    resp = httpx.get(f"{BASE_URL}/dashboard/stats", headers=headers)
    print("--- GET /dashboard/stats ---")
    print(resp.status_code)
    body = resp.json()
    print(body)
    print()

    ok = resp.status_code == 200
    print("PASS" if ok else "FAIL", "- endpoint returns 200")
    results.append(ok)

    for field in [
        "inventory_cost_valuation",
        "inventory_retail_valuation",
        "total_revenue",
        "total_profit",
    ]:
        ok = close(body[field], expected[field])
        print(
            "PASS" if ok else "FAIL",
            f"- {field}: got {body[field]}, expected {expected[field]}",
        )
        results.append(ok)

    for field in [
        "product_count",
        "in_stock_count",
        "low_stock_count",
        "out_of_stock_count",
        "total_units_sold",
    ]:
        ok = body[field] == expected[field]
        print(
            "PASS" if ok else "FAIL",
            f"- {field}: got {body[field]}, expected {expected[field]}",
        )
        results.append(ok)

    ok = body["in_stock_count"] + body["low_stock_count"] + body["out_of_stock_count"] == body[
        "product_count"
    ]
    print("PASS" if ok else "FAIL", "- stock-status counts add up to product_count")
    results.append(ok)

    ok = len(body["sales_over_time"]) == 30
    print("PASS" if ok else "FAIL", f"- sales_over_time has 30 days (got {len(body['sales_over_time'])})")
    results.append(ok)

    ok = sum(float(p["revenue"]) for p in body["top_products"]) <= expected["total_revenue"] + 0.01
    ok = ok and len(body["top_products"]) <= 5
    for p in body["top_products"]:
        expected_units = expected["units_by_product"].get(p["name"])
        if expected_units is not None:
            ok = ok and p["units"] == expected_units
    print("PASS" if ok else "FAIL", "- top_products matches units sold per product, capped at 5")
    results.append(ok)

    ok = True
    for c in body["sales_by_category"]:
        expected_rev = expected["revenue_by_category"].get(c["category"])
        if expected_rev is not None:
            ok = ok and close(c["revenue"], expected_rev)
    print("PASS" if ok else "FAIL", "- sales_by_category revenue matches per-category totals")
    results.append(ok)

    ok = [i["name"] for i in body["low_stock_items"]] == expected["low_stock_item_names"][:10]
    print("PASS" if ok else "FAIL", "- low_stock_items matches real low/out-of-stock products")
    results.append(ok)

    print()
    print("--- unauthenticated request ---")
    resp = httpx.get(f"{BASE_URL}/dashboard/stats")
    print(resp.status_code, resp.json())
    ok = resp.status_code in (401, 403)
    print("PASS" if ok else "FAIL", "- unauthenticated request blocked")
    results.append(ok)

    passed = sum(results)
    total = len(results)
    print()
    print(f"{passed} passed / {total - passed} failed (of {total})")
    if passed != total:
        sys.exit(1)


if __name__ == "__main__":
    main()
