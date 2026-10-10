from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
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
from app.models.enums import (
    ContactsVisibility,
    GradeVerificationStatus,
    ProfileVisibility,
    Readiness,
    WorkFormat,
)

if TYPE_CHECKING:
    from app.models.fsp import FspAchievement
    from app.models.taxonomy import Grade, Skill, Specialization
    from app.models.user import User


class CandidateProfile(Base):
    """Professional profile; `user_id` doubles as `candidateId` in the API."""

    __tablename__ = "candidate_profiles"
    # Fetch `updated_at` via RETURNING after UPDATE; a lazy reload would fail under asyncio.
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (
        Index(
            "ix_candidate_category",
            "verified_specialization_id",
            "verified_grade_id",
            "readiness",
        ),
        CheckConstraint(
            "readiness IN ('actively_looking', 'open_to_offers', 'not_looking')",
            name="ck_candidate_readiness",
        ),
        CheckConstraint("currency = 'RUB'", name="ck_candidate_currency"),
        CheckConstraint("salary_from IS NULL OR salary_from > 0", name="ck_candidate_salary_from"),
        CheckConstraint(
            "salary_to IS NULL OR salary_from IS NULL OR salary_to >= salary_from",
            name="ck_candidate_salary_range",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    about: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(64))
    telegram: Mapped[str | None] = mapped_column(String(128))
    city: Mapped[str | None] = mapped_column(String(128))
    experience_years: Mapped[int | None] = mapped_column(Integer)
    experience_description: Mapped[str | None] = mapped_column(Text)
    desired_position: Mapped[str | None] = mapped_column(String(255))

    # Declared by the candidate ("claimed") vs confirmed by a passed test ("verified").
    declared_specialization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("specializations.id")
    )
    declared_grade_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("grades.id")
    )
    verified_specialization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("specializations.id")
    )
    verified_grade_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("grades.id")
    )
    grade_verification_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=GradeVerificationStatus.not_tested.value
    )

    salary_from: Mapped[int | None] = mapped_column(Integer)
    salary_to: Mapped[int | None] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="RUB")
    work_format: Mapped[str | None] = mapped_column(String(32), default=WorkFormat.remote.value)
    readiness: Mapped[str] = mapped_column(
        String(32), nullable=False, default=Readiness.open_to_offers.value
    )
    profile_visibility: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ProfileVisibility.employers.value
    )
    contacts_visibility: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ContactsVisibility.after_accept.value
    )
    last_grade_change_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Score of the test that confirmed the current verified grade. Failed attempts do not
    # overwrite it, otherwise one failed try at a higher grade would sink the match score.
    last_test_score: Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="candidate_profile")
    skills: Mapped[list[CandidateSkill]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )
    declared_specialization: Mapped[Specialization | None] = relationship(
        foreign_keys=[declared_specialization_id]
    )
    declared_grade: Mapped[Grade | None] = relationship(foreign_keys=[declared_grade_id])
    verified_specialization: Mapped[Specialization | None] = relationship(
        foreign_keys=[verified_specialization_id]
    )
    verified_grade: Mapped[Grade | None] = relationship(foreign_keys=[verified_grade_id])
    fsp_achievements: Mapped[list[FspAchievement]] = relationship(viewonly=True)


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"
    __table_args__ = (
        UniqueConstraint("candidate_user_id", "skill_id", name="uq_candidate_skill"),
        Index("ix_candidate_skills_skill", "skill_id", "candidate_user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    candidate: Mapped[CandidateProfile] = relationship(back_populates="skills")
    skill: Mapped[Skill] = relationship()


class Consent(Base):
    """One row per acceptance; withdrawal stamps `withdrawn_at` instead of deleting."""

    __tablename__ = "consents"
    __table_args__ = (Index("ix_consents_user_type", "user_id", "type"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
