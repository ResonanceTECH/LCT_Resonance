from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiModel, GradeValue


class TestSessionStart(ApiModel):
    specialization: str = Field(min_length=1, max_length=128)
    stack: list[str] = Field(default_factory=list, max_length=30)
    claimed_grade: GradeValue
    retest: bool = False


class TestSessionOut(ApiModel):
    id: UUID
    specialization: str
    stack: list[str]
    claimed_grade: GradeValue
    current_index: int
    total_questions: int
    status: Literal["in_progress", "completed", "expired"]
    expires_at: datetime


class QuestionOption(ApiModel):
    id: str
    text: str


class TestQuestionOut(ApiModel):
    """One question of the session; the correct option never leaves the backend."""

    id: UUID  # id of the issued instance, not of a bank question
    text: str
    code: str | None = None
    options: list[QuestionOption]
    # Position in the session, so the client does not hard-code the test length.
    index: int
    total: int


class AnswerIn(ApiModel):
    question_id: UUID
    option_id: str = Field(min_length=1, max_length=32)


class TestResultOut(ApiModel):
    session_id: UUID
    score: int
    max_score: int = 100
    grade_confirmed: bool
    completed_at: datetime
    claimed_grade: GradeValue
    is_retest: bool = False
    # After a failure: when the same grade can be retried (a lower one is available now).
    retry_available_at: datetime | None = None


class TestHistoryItem(TestResultOut):
    specialization: str
