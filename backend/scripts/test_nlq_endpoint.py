#!/usr/bin/env python3
"""End-to-end test of POST /nlq/ask against the RUNNING backend. Run directly
(with the backend already up on :8000, e.g. via `uvicorn app.main:app`):

    cd backend && source venv/bin/activate && python scripts/test_nlq_endpoint.py

Signs up (or logs into, on a rerun) a dedicated test business, seeds a
product + a sale if none exist yet, then exercises the endpoint: a normal
question, an empty question (rejected before it ever reaches the model),
a garbage question (should fail gracefully, not crash), and an
unauthenticated request (must be blocked). Prints each full response and a
PASS/FAIL summary.
"""
import sys

import httpx

BASE_URL = "http://localhost:8000"
# /nlq/ask makes two sequential LLM calls (SQL generation, then answer
# summarization) — a short default timeout is too easy to trip, especially
# against a local Ollama model.
REQUEST_TIMEOUT = 60.0
TEST_EMAIL = "nlq-endpoint-test@example.com"
TEST_PASSWORD = "supersecret1"
TEST_BUSINESS_NAME = "NLQ Endpoint Test Co"


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

    product = httpx.post(
        f"{BASE_URL}/products",
        headers=headers,
        json={
            "name": "NLQ Test Widget",
            "category": "Test",
            "cost_price": 5,
            "selling_price": 15,
            "quantity_in_stock": 20,
        },
    ).json()

    httpx.post(
        f"{BASE_URL}/sales",
        headers=headers,
        json={"product_id": product["id"], "quantity": 2},
    ).raise_for_status()


def ask(question: str, headers: dict) -> httpx.Response:
    return httpx.post(
        f"{BASE_URL}/nlq/ask",
        headers=headers,
        json={"question": question},
        timeout=REQUEST_TIMEOUT,
    )


def main() -> None:
    results = []

    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    ensure_seed_data(headers)

    # --- Normal question: should execute and return sql + rows + columns ---
    print("--- normal question ---")
    resp = ask("What is our total revenue?", headers)
    body = resp.json()
    print(body)
    print(f"  answer: {body.get('answer')!r}")
    ok = bool(
        resp.status_code == 200
        and body["executed"] is True
        and body["error"] is None
        and body["generated_sql"]
        and body["rows"] is not None
        and body["columns"] is not None
    )
    print("PASS" if ok else "FAIL", "- normal question executed with sql/rows/columns")
    results.append(ok)
    print()

    # --- Empty question: rejected before ever reaching the model (422) ---
    print("--- empty question ---")
    resp = ask("", headers)
    print(resp.status_code, resp.json())
    ok = resp.status_code == 422
    print("PASS" if ok else "FAIL", "- empty question rejected with 422")
    results.append(ok)
    print()

    # --- Garbage question: must fail gracefully, not crash ---
    print("--- garbage question ---")
    resp = ask("sdkjfh skdjfh 12345 !!! asjdh purple triangle Tuesday", headers)
    body = resp.json()
    print(resp.status_code, body)
    print(f"  answer: {body.get('answer')!r}")
    ok = bool(
        resp.status_code == 200
        and (body["executed"] is True or (body["executed"] is False and bool(body["error"])))
    )
    print(
        "PASS" if ok else "FAIL",
        "- garbage question handled without crashing"
        + (" (model produced something that happened to be valid SQL)" if body.get("executed") else ""),
    )
    results.append(ok)
    print()

    # --- Unauthenticated: must be blocked ---
    print("--- unauthenticated request ---")
    resp = httpx.post(f"{BASE_URL}/nlq/ask", json={"question": "What is our total revenue?"})
    print(resp.status_code, resp.json())
    ok = resp.status_code in (401, 403)
    print("PASS" if ok else "FAIL", "- unauthenticated request blocked")
    results.append(ok)
    print()

    passed = sum(results)
    total = len(results)
    print(f"{passed} passed / {total - passed} failed (of {total})")
    if passed != total:
        sys.exit(1)


if __name__ == "__main__":
    main()
