class ValidationError(Exception):
    """Raised when untrusted SQL fails safety validation.

    Messages on this exception are written to be safe to show directly to
    a user/developer (no raw parser internals, no stack traces) — see
    hard rule 2 in CLAUDE.md: the NLQ path is read-only, and rejections
    must be clear, not silent or crashy.
    """
