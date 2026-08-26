#!/usr/bin/env python3
"""Manual smoke test for the first end-to-end NL question -> SQL -> rows
path (sub-step 4c). Run directly:

    cd backend && source venv/bin/activate && python scripts/test_nlq_pipeline.py

Asks the configured LLM provider (whatever LLM_PROVIDER/LLM_MODEL resolve
to — Groq by default, or Ollama if set) a handful of real questions about
business 1's data, prints the SQL it generated and the rows that came
back, and reports whether each one succeeded. This is for manual
eyeballing of SQL quality — it is not a safety test (that's
scripts/test_sql_safety.py, which doesn't touch the LLM at all).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.llm import LLMAdapterError  # noqa: E402
from app.nlq import ValidationError, question_to_sql_and_run  # noqa: E402

BUSINESS_ID = 1

QUESTIONS = [
    "What products do I have in stock?",
    "Which product has the highest quantity in stock?",
    "What is my total revenue from all sales?",
    "How many units of each product have I sold?",
    "What was my total profit last month?",
]


def main() -> None:
    successes = 0
    for question in QUESTIONS:
        print(f"Q: {question}")
        try:
            result = question_to_sql_and_run(question, BUSINESS_ID)
        except (ValidationError, LLMAdapterError) as exc:
            print(f"  FAILED ({type(exc).__name__}): {exc}")
            print()
            continue

        print(f"  SQL:     {result['sql']}")
        print(f"  COLUMNS: {result['columns']}")
        print(f"  ROWS:    {result['rows']}")
        print()
        successes += 1

    print(f"{successes} / {len(QUESTIONS)} questions produced a valid, executed query.")


if __name__ == "__main__":
    main()
