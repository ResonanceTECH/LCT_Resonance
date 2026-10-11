from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TestAttemptStatus


class TestQuestion(Base):
    """Static question from the bank; generated questions exist only as attempt items."""

    __tablename__ = "test_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    specialization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("specializations.id"), nullable=False
    )
    grade_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("grades.id"), nullable=False
    )
    topic: Mapped[str] = mapped_column(String(64), nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    correct_answer: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # How many attempts have shown it; past STATIC_ITEM_MAX_EXPOSURES it leaves rotation.
    exposure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class TestAttempt(Base):
    __tablename__ = "test_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    specialization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("specializations.id"), nullable=False
    )
    grade_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("grades.id"), nullable=False
    )
    score: Mapped[int | None] = mapped_column(Integer)
    passed: Mapped[bool | None] = mapped_column(Boolean)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=TestAttemptStatus.in_progress.value
    )
    # Stack the candidate asked to be tested on (frontend `stack`), kept for analytics.
    stack: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    is_retest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Position of the next unanswered item; the frontend asks questions one by one.
    current_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    items: Mapped[list["TestAttemptItem"]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan",
        order_by="TestAttemptItem.position",
    )


class TestAttemptItem(Base):
    """A question instance issued in one attempt, with the candidate's answer.

    The prompt and options are copied, so later edits of the bank do not change what was
    asked. Generated items keep their generator key and seed: the exact task can be
    reproduced when a result is disputed.
    """

    __tablename__ = "test_attempt_items"
    __table_args__ = (UniqueConstraint("attempt_id", "position", name="uq_attempt_item_position"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_attempts.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)  # static | generated
    question_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_questions.id", ondelete="SET NULL")
    )
    generator_key: Mapped[str | None] = mapped_column(String(64))
    seed: Mapped[int | None] = mapped_column(BigInteger)
    topic: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[str | None] = mapped_column(Text)
    options: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    correct_option_id: Mapped[str] = mapped_column(String(32), nullable=False)
    selected_option_id: Mapped[str | None] = mapped_column(String(32))
    is_correct: Mapped[bool | None] = mapped_column(Boolean)

    attempt: Mapped[TestAttempt] = relationship(back_populates="items")
