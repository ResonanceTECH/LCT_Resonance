"""Consents required by ТЗ and 152-ФЗ: processing, profile publication, FSP linking.

Every acceptance is a new row stamped with the consent text version; withdrawal sets
`withdrawn_at`, so the history of what a person agreed to and when is preserved.
Side effects of a change (hiding the profile, dropping FSP data) live in the callers.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.candidate import Consent
from app.models.enums import ConsentType
from app.schemas.consent import ConsentChange, ConsentOut
from app.services.audit import write_audit

_REQUIRED_MESSAGES = {
    ConsentType.personal_data: "Нужно согласие на обработку персональных данных",
    ConsentType.profile_publication: "Нужно согласие на публикацию профиля",
    ConsentType.fsp_sync: "Дайте согласие на получение данных из реестра ФСП",
}


async def latest_consents(db: AsyncSession, user_id: UUID) -> dict[str, Consent]:
    rows = await db.execute(
        select(Consent).where(Consent.user_id == user_id).order_by(Consent.accepted_at)
    )
    latest: dict[str, Consent] = {}
    for row in rows.scalars().all():
        latest[row.type] = row  # ordered by time: the last one wins
    return latest


def _is_active(row: Consent | None) -> bool:
    return row is not None and row.withdrawn_at is None


def to_out(latest: dict[str, Consent]) -> list[ConsentOut]:
    current = get_settings().consent_version
    out = []
    for consent_type in ConsentType:
        row = latest.get(consent_type.value)
        out.append(
            ConsentOut(
                type=consent_type.value,
                accepted=_is_active(row),
                version=row.version if row else None,
                current_version=current,
                accepted_at=row.accepted_at if row else None,
                withdrawn_at=row.withdrawn_at if row else None,
            )
        )
    return out


async def has_consent(db: AsyncSession, user_id: UUID, consent_type: ConsentType) -> bool:
    return _is_active((await latest_consents(db, user_id)).get(consent_type.value))


async def require_consent(db: AsyncSession, user_id: UUID, consent_type: ConsentType) -> None:
    if not await has_consent(db, user_id, consent_type):
        raise AppError(
            "CONSENT_REQUIRED",
            _REQUIRED_MESSAGES[consent_type],
            403,
            {"type": consent_type.value},
        )


async def apply_changes(
    db: AsyncSession, user_id: UUID, changes: list[ConsentChange]
) -> dict[ConsentType, bool]:
    """Record accept/withdraw changes (no commit). Returns the types whose state changed."""
    latest = await latest_consents(db, user_id)
    now = datetime.now(UTC)
    changed: dict[ConsentType, bool] = {}
    for change in changes:
        consent_type = ConsentType(change.type)
        row = latest.get(change.type)
        if change.accepted and not _is_active(row):
            db.add(
                Consent(
                    user_id=user_id,
                    type=change.type,
                    version=get_settings().consent_version,
                    accepted_at=now,
                )
            )
        elif not change.accepted and _is_active(row):
            row.withdrawn_at = now
        else:
            continue
        changed[consent_type] = change.accepted
        await write_audit(
            db,
            action="CONSENT_GIVEN" if change.accepted else "CONSENT_WITHDRAWN",
            entity_type="consent",
            entity_id=str(user_id),
            actor_user_id=user_id,
            metadata={"type": change.type},
        )
    return changed
