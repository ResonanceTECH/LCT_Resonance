from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import FspSyncStatus


class FspLink(Base):
    __tablename__ = "fsp_links"

    candidate_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_profiles.user_id", ondelete="CASCADE"), primary_key=True
    )
    fsp_member_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    sync_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=FspSyncStatus.none.value
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class FspAchievement(Base):
    __tablename__ = "fsp_achievements"
    __table_args__ = (
        UniqueConstraint("candidate_user_id", "source", "external_id", name="uq_fsp_achievement"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_profiles.user_id", ondelete="CASCADE"), nullable=False
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="fsp")
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    achievement_type: Mapped[str] = mapped_column(String(64), nullable=False)
    discipline: Mapped[str | None] = mapped_column(String(255))
    competition_name: Mapped[str | None] = mapped_column(String(255))
    result: Mapped[str | None] = mapped_column(String(255))
    place: Mapped[int | None] = mapped_column(Integer)
    role: Mapped[str | None] = mapped_column(String(128))
    sport_rank: Mapped[str | None] = mapped_column(String(128))
    achieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
