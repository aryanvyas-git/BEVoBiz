import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.llm import LLMAdapterError
from app.models.user import User
from app.nlq import ValidationError, question_to_sql_and_run
from app.schemas.nlq import AskRequest, AskResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nlq", tags=["nlq"])


@router.post("/ask", response_model=AskResponse)
def ask(
    payload: AskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AskResponse:
    """Answer a natural-language question about the current business's own
    products/sales data.

    business_id always comes from the authenticated user, never from the
    request body — the model itself is told not to filter by business_id
    at all (see app.nlq.schema_context), and app.nlq.enforce_business_scope
    would strip any attempt to override it regardless.

    This always returns HTTP 200; whether the question was actually
    answered is carried in the `executed` field. Expected failure modes
    (unsafe/unparseable generated SQL, the LLM being unreachable) are
    translated into a short, friendly `error` string — never a raw parser
    message or stack trace — with the real detail logged server-side.
    """
    try:
        result = question_to_sql_and_run(payload.question, current_user.business_id, db)
    except ValidationError as exc:
        logger.info("NLQ question rejected by safety layer (question=%r): %s", payload.question, exc)
        return AskResponse(
            question=payload.question,
            executed=False,
            error="I couldn't turn that into a safe query — try rephrasing.",
        )
    except LLMAdapterError as exc:
        logger.warning("NLQ LLM adapter error (question=%r): %s", payload.question, exc)
        return AskResponse(
            question=payload.question,
            executed=False,
            error="The AI service is unavailable right now.",
        )
    except Exception:
        logger.exception("Unexpected NLQ failure (question=%r)", payload.question)
        return AskResponse(
            question=payload.question,
            executed=False,
            error="Something went wrong answering that question.",
        )

    rows = result["rows"]
    columns = list(rows[0].keys()) if rows else []
    return AskResponse(
        question=result["question"],
        generated_sql=result["sql"],
        rows=rows,
        columns=columns,
        executed=True,
        error=None,
    )
