"""Pulls a candidate SQL string out of a raw LLM response.

Models routinely ignore "output only SQL" instructions and wrap the query
in a markdown code fence, or prefix it with a line of prose ("Here's the
query:"). validate_sql (app.nlq.validator) is intentionally strict and will
reject any of that as unparseable, so this best-effort cleanup happens
first. It does not make anything safer by itself — extracted text still
goes through the full validate_sql + enforce_business_scope + run_safe_query
pipeline unchanged; this module only improves the odds that well-intentioned
model output actually reaches that pipeline in a parseable shape.
"""
import re

_FENCE_PATTERN = re.compile(r"```(?:sql)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
_LEADING_KEYWORD_PATTERN = re.compile(r"\b(SELECT|WITH)\b", re.IGNORECASE)


def extract_sql_from_response(text: str) -> str:
    """Best-effort extraction of a single SQL statement from `text`."""
    candidate = text.strip()

    fence_match = _FENCE_PATTERN.search(candidate)
    if fence_match:
        candidate = fence_match.group(1).strip()

    if not _LEADING_KEYWORD_PATTERN.match(candidate):
        keyword_match = _LEADING_KEYWORD_PATTERN.search(candidate)
        if keyword_match:
            candidate = candidate[keyword_match.start():]

    return candidate.strip()
