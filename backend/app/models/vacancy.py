from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import VacancyStatus, WorkFormat

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.taxonomy import Grade, Skill, Specialization


class Vacancy(Base):
    __tablename__ = "vacancies"
    # Fetch `updated_at` via RETURNING after UPDATE; a lazy reload would fail under asyncio.
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (
        CheckConstraint("salary_from > 0", name="ck_vacancy_salary_from"),
        CheckConstraint("salary_to >= salary_from", name="ck_vacancy_salary_range"),
        Index("ix_vacancies_search", "specialization_id", "grade_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    # Snapshot shown on the vacancy and its offers; defaults to the company profile name.
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    specialization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("specializations.id"), nullable=False
    )
    grade_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("grades.id"), nullable=False
    )
    salary_from: Mapped[int] = mapped_column(Integer, nullable=False)
    salary_to: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="RUB")
    work_format: Mapped[str] = mapped_column(String(32), nullable=False, default=WorkFormat.remote.value)
    city: Mapped[str | None] = mapped_column(String(128))
    extra_info: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=VacancyStatus.draft.value)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    company: Mapped[Company] = relationship(back_populates="vacancies")
    specialization: Mapped[Specialization] = relationship()
    grade: Mapped[Grade] = relationship()
    skills: Mapped[list[VacancySkill]] = relationship(
        back_populates="vacancy", cascade="all, delete-orphan"
    )


class VacancySkill(Base):
    __tablename__ = "vacancy_skills"
    __table_args__ = (UniqueConstraint("vacancy_id", "skill_id", name="uq_vacancy_skill"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vacancy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vacancies.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    weight: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    vacancy: Mapped[Vacancy] = relationship(back_populates="skills")
    skill: Mapped[Skill] = relationship()
