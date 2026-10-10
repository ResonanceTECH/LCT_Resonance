"""Employer/candidate interactions behind the frontend's P1 screens:
shortlist, applications, saved vacancies, profile views and notifications."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _created_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def _fk(target: str) -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), ForeignKey(target, ondelete="CASCADE"), nullable=False)


class ShortlistItem(Base):
    __tablename__ = "shortlist_items"
    __table_args__ = (
        UniqueConstraint("employer_user_id", "candidate_user_id", name="uq_shortlist_item"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    employer_user_id: Mapped[uuid.UUID] = _fk("users.id")
    candidate_user_id: Mapped[uuid.UUID] = _fk("candidate_profiles.user_id")
    created_at: Mapped[datetime] = _created_at()


class Application(Base):
    """A candidate's own response to a vacancy; it also unlocks contacts (ТЗ)."""

    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("candidate_user_id", "vacancy_id", name="uq_application"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    candidate_user_id: Mapped[uuid.UUID] = _fk("candidate_profiles.user_id")
    vacancy_id: Mapped[uuid.UUID] = _fk("vacancies.id")
    created_at: Mapped[datetime] = _created_at()


class SavedVacancy(Base):
    __tablename__ = "saved_vacancies"
    __table_args__ = (UniqueConstraint("candidate_user_id", "vacancy_id", name="uq_saved_vacancy"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    candidate_user_id: Mapped[uuid.UUID] = _fk("candidate_profiles.user_id")
    vacancy_id: Mapped[uuid.UUID] = _fk("vacancies.id")
    created_at: Mapped[datetime] = _created_at()


class ProfileView(Base):
    """Recorded when an employer opens a candidate card; feeds the candidate dashboard."""

    __tablename__ = "profile_views"
    __table_args__ = (Index("ix_profile_views_candidate", "candidate_user_id"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    candidate_user_id: Mapped[uuid.UUID] = _fk("candidate_profiles.user_id")
    employer_user_id: Mapped[uuid.UUID] = _fk("users.id")
    viewed_at: Mapped[datetime] = _created_at()


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_created", "user_id", "created_at"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = _fk("users.id")
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    href: Mapped[str | None] = mapped_column(String(512))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _created_at()
