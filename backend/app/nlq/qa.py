"""First end-to-end natural-language-question -> SQL -> rows path.

Wires the LLM adapter (app.llm) to the existing 4b safety pipeline
(app.nlq.validator / app.nlq.scope / app.nlq.executor) — this module adds
no new safety logic of its own. The LLM's raw output is untrusted input,
exactly like a hand-typed query would be; it earns no special treatment
just because a model produced it.
"""
from typing import Any

from sqlalchemy.orm import Session

from app.llm import get_llm_adapter
from app.nlq.executor import run_safe_query
from app.nlq.schema_context import SCHEMA_DESCRIPTION
from app.nlq.sql_extraction import extract_sql_from_response
from app.nlq.validator import validate_sql


def question_to_sql_and_run(question: str, business_id: int, db: Session) -> dict[str, Any]:
    """Ask the LLM to translate `question` into SQL, then validate, scope,
    and run it for `business_id`.

    Returns {"question", "sql", "rows"} on success. Raises
    app.llm.LLMAdapterError if the model can't be reached, or
    app.nlq.ValidationError if the model's SQL doesn't pass the safety
    layer — both exceptions carry messages that are safe to show directly.
    """
    adapter = get_llm_adapter()
    raw_response = adapter.generate(prompt=question, system=SCHEMA_DESCRIPTION)
    candidate_sql = extract_sql_from_response(raw_response)

    # validate_sql is pure/side-effect-free, so calling it here (to capture
    # the canonical SQL for the response) and again inside run_safe_query
    # (which re-validates independently rather than trusting any caller)
    # is deliberate, not redundant work worth avoiding.
    cleaned_sql = validate_sql(candidate_sql)
    rows = run_safe_query(candidate_sql, business_id, db)

    return {
        "question": question,
        "sql": cleaned_sql,
        "rows": rows,
    }
