from typing import Any, Optional

from pydantic import BaseModel, field_validator

MAX_QUESTION_LENGTH = 1000


class AskRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def question_valid(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("question must not be blank")
        if len(v) > MAX_QUESTION_LENGTH:
            raise ValueError(f"question must be at most {MAX_QUESTION_LENGTH} characters")
        return v


class AskResponse(BaseModel):
    question: str
    generated_sql: Optional[str] = None
    rows: Optional[list[dict[str, Any]]] = None
    columns: Optional[list[str]] = None
    executed: bool
    error: Optional[str] = None
