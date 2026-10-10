from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import OfferStatus, WorkFormat

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.user import User


class Offer(Base):
    __tablename__ = "offers"
    __table_args__ = (
        CheckConstraint("salary_from > 0", name="ck_offer_salary_from"),
        CheckConstraint("salary_to >= salary_from", name="ck_offer_salary_range"),
        Index(
            "uq_offers_active_vacancy",
            "employer_user_id",
            "candidate_user_id",
            "vacancy_id",
            unique=True,
            postgresql_where=text("status IN ('new', 'viewed') AND vacancy_id IS NOT NULL"),
        ),
        Index(
            "uq_offers_active_no_vacancy",
            "employer_user_id",
            "candidate_user_id",
            unique=True,
            postgresql_where=text("status IN ('new', 'viewed') AND vacancy_id IS NULL"),
        ),
        Index("ix_offers_candidate_status", "candidate_user_id", "status"),
        Index("ix_offers_employer_status", "employer_user_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employer_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    candidate_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False
    )
    vacancy_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vacancies.id")
    )
    # Snapshot: the terms the candidate saw stay unchanged if the company is renamed.
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    position_title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    salary_from: Mapped[int] = mapped_column(Integer, nullable=False)
    salary_to: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="RUB")
    work_format: Mapped[str] = mapped_column(String(32), nullable=False, default=WorkFormat.remote.value)
    employer_contact: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=OfferStatus.new.value)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    company: Mapped[Company] = relationship()
    employer: Mapped[User] = relationship(foreign_keys=[employer_user_id])
