"""Turns already-fetched, already-safe query results into a short
natural-language answer.

This module never touches the database and never generates SQL — it only
takes the rows/columns that app.nlq.executor.run_safe_query has already
produced (post safety-layer, post business-scoping) and asks the LLM to
phrase them in plain English. Failure here is always non-fatal: the
table/chart views must keep working even if this call fails or the model
is unreachable, so summarize_answer never raises — it returns None instead.
"""
import logging
from typing import Any, Optional

from app.llm import LLMAdapterError, get_llm_adapter

logger = logging.getLogger(__name__)

MAX_ROWS_IN_PROMPT = 20

_SUMMARY_SYSTEM_PROMPT = """\
You answer questions about a small business's inventory and sales using \
the data provided below. You will be given the original question and the \
query result data. Respond with a short, friendly answer in one or two \
sentences, in plain English, as if speaking directly to the business \
owner. Use the actual numbers from the data. Do not mention SQL, tables, \
columns, or databases. Do not repeat the question back verbatim. Output \
only the answer sentence(s) — no preamble, no markdown.\
"""


def _format_rows(columns: list[str], rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "(no rows returned)"

    shown = rows[:MAX_ROWS_IN_PROMPT]
    lines = [" | ".join(columns)]
    for row in shown:
        lines.append(" | ".join(str(row.get(col, "")) for col in columns))

    text = "\n".join(lines)
    remaining = len(rows) - len(shown)
    if remaining > 0:
        text += f"\n... ({remaining} more row(s) not shown)"
    return text


def summarize_answer(
    question: str, columns: list[str], rows: list[dict[str, Any]]
) -> Optional[str]:
    """Best-effort natural-language summary of `rows`. Never raises."""
    prompt = f"Question: {question}\n\nData:\n{_format_rows(columns, rows)}"

    try:
        adapter = get_llm_adapter()
        answer = adapter.generate(prompt=prompt, system=_SUMMARY_SYSTEM_PROMPT)
    except LLMAdapterError as exc:
        logger.warning("NLQ summarization unavailable (question=%r): %s", question, exc)
        return None
    except Exception:
        logger.exception("Unexpected NLQ summarization failure (question=%r)", question)
        return None

    answer = answer.strip()
    return answer or None
