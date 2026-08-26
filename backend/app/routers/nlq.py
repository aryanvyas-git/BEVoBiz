import logging

from fastapi import APIRouter, Depends

from app.deps import get_current_user
from app.llm import LLMAdapterError
from app.models.user import User
from app.nlq import ValidationError, question_to_sql_and_run, summarize_answer
from app.schemas.nlq import AskRequest, AskResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nlq", tags=["nlq"])


@router.post("/ask", response_model=AskResponse)
def ask(
    payload: AskRequest,
    current_user: User = Depends(get_current_user),
) -> AskResponse:
    """Answer a natural-language question about the current business's own
    products/sales data.

    business_id always comes from the authenticated user, never from the
    request body — the model itself is told not to filter by business_id
    at all (see app.nlq.schema_context), and app.nlq.enforce_business_scope
    would strip any attempt to override it regardless. Note there's no
    `db` dependency here: the NLQ pipeline connects to Postgres itself,
    as a dedicated low-privilege role (see app.nlq.db) — this endpoint
    never touches the app's normal database session at all.

    This always returns HTTP 200; whether the question was actually
    answered is carried in the `executed` field. Expected failure modes
    (unsafe/unparseable generated SQL, the LLM being unreachable) are
    translated into a short, friendly `error` string — never a raw parser
    message or stack trace — with the real detail logged server-side.
    """
    try:
        result = question_to_sql_and_run(payload.question, current_user.business_id)
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
    columns = result["columns"]

    # Best-effort natural-language summary. This never raises (see
    # app.nlq.summarize) and never touches the DB or generates SQL — it
    # only phrases the rows we already fetched. A failure here must not
    # take down the table/chart data, so it's deliberately outside the
    # try/except above that handles SQL generation/execution failures.
    answer = summarize_answer(result["question"], columns, rows)

    return AskResponse(
        question=result["question"],
        answer=answer,
        generated_sql=result["sql"],
        rows=rows,
        columns=columns,
        executed=True,
        error=None,
    )
