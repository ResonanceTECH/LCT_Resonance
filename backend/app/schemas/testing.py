from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class StartTestRequest(BaseModel):
    specialization_id: UUID
    grade_id: UUID


class QuestionOption(BaseModel):
    id: str
    text: str


class QuestionOut(BaseModel):
    id: UUID
    topic: str
    text: str
    options: list[QuestionOption]


class AttemptStartResponse(BaseModel):
    attempt_id: UUID
    specialization: str
    grade: str
    expires_at: datetime
    questions: list[QuestionOut]


class AnswerIn(BaseModel):
    question_id: UUID
    option_id: str


class SubmitTestRequest(BaseModel):
    answers: list[AnswerIn] = Field(min_length=1)


class CategoryOut(BaseModel):
    specialization: str
    grade: str


class SubmitTestResponse(BaseModel):
    attempt_id: UUID
    score: int
    passed: bool
    tested_grade: str
    verified_grade: str | None
    category: CategoryOut | None = None
