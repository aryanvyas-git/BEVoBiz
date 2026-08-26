#!/usr/bin/env python3
"""Manual smoke test for the LLM adapter. Not part of the app; run directly:

    cd backend && source venv/bin/activate && python scripts/test_llm.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings  # noqa: E402
from app.llm import LLMAdapterError, get_llm_adapter  # noqa: E402


def main() -> None:
    print(f"Provider: {settings.LLM_PROVIDER}")
    print(f"Model:    {settings.LLM_MODEL}")
    print(f"Base URL: {settings.OLLAMA_BASE_URL}")
    print()

    adapter = get_llm_adapter()

    try:
        reply = adapter.generate("Say hello in one short sentence.")
    except LLMAdapterError as exc:
        print(f"LLM adapter error: {exc}")
        sys.exit(1)

    print("Response:")
    print(reply)


if __name__ == "__main__":
    main()
