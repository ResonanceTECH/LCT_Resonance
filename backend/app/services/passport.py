"""Public Career Passport: the shareable link, publication rules and the public page.

The link is `/p/<name>-<token>`, e.g. `/p/anna-kovaleva-k7m2q9xw`. Only the token is looked
up, so the readable part follows the current name and links shared before a rename keep
working. The internal user id never appears in the link.
"""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.candidate import PASSPORT_TOKEN_ALPHABET, PASSPORT_TOKEN_LENGTH, CandidateProfile
from app.models.enums import ConsentType
from app.models.user import User
from app.schemas.candidate import CandidatePassport, PublicPassport
from app.services import consents, profiles
from app.services.candidate import get_profile
from app.services.fsp import list_achievements
from app.services.insights import skill_radar
from app.services.matching import MATCH_PROFILE_OPTIONS

NAME_PART_MAX = 40
_TOKEN = re.compile(rf"[{PASSPORT_TOKEN_ALPHABET}]{{{PASSPORT_TOKEN_LENGTH}}}")
# Simplified passport-style transliteration: readable, ASCII only.
_TRANSLIT = dict(
    zip(
        "абвгдеёжзийклмнопрстуфхцчшщыэюя",
        "a b v g d e e zh z i y k l m n o p r s t u f kh ts ch sh shch y e yu ya".split(),
        strict=True,
    )
) | {"ъ": "", "ь": ""}


def _name_part(full_name: str) -> str:
    """'Анна Ковалёва' -> 'anna-kovaleva'. Whole words only, up to NAME_PART_MAX chars."""
    latin = "".join(_TRANSLIT.get(ch, ch) for ch in full_name.lower())
    part = ""
    for word in re.findall(r"[a-z0-9]+", latin):
        longer = f"{part}-{word}" if part else word
        if len(longer) > NAME_PART_MAX:
            break
        part = longer
    return part


def passport_slug(profile: CandidateProfile) -> str:
    name = _name_part(profile.full_name)
    return f"{name}-{profile.passport_token}" if name else profile.passport_token


def passport_url(profile: CandidateProfile) -> str:
    return f"{get_settings().public_app_url.rstrip('/')}/p/{passport_slug(profile)}"


def token_from_slug(slug: str) -> str | None:
    token = slug.rsplit("-", 1)[-1].lower()
    return token if _TOKEN.fullmatch(token) else None


async def _unpublished_reason(
    db: AsyncSession, profile: CandidateProfile, user: User
) -> str | None:
    """Why the passport is not public, as a code the frontend turns into a hint or a button."""
    if user.email_verified_at is None:
        return "EMAIL_NOT_VERIFIED"
    # Publishing the profile is a separate consent (152-FZ); giving it also makes the
    # profile visible, so one button on the frontend covers both.
    if (
        not await consents.has_consent(db, user.id, ConsentType.profile_publication)
        or profile.profile_visibility not in profiles.VISIBLE_PROFILE_VALUES
    ):
        return "CONSENT_REQUIRED"
    return None


async def my_passport(db: AsyncSession, user: User) -> CandidatePassport:
    profile = await get_profile(db, user.id)
    reason = await _unpublished_reason(db, profile, user)
    return CandidatePassport(
        slug=passport_slug(profile),
        url=passport_url(profile),
        published=reason is None,
        reason=reason,
    )


async def public_passport(db: AsyncSession, slug: str) -> PublicPassport:
    """No auth: shown only for a visible profile with the consent to publication."""
    not_found = AppError("PASSPORT_NOT_FOUND", "Паспорт не найден или скрыт кандидатом", 404)
    token = token_from_slug(slug)
    if token is None:
        raise not_found
    profile = (
        await db.execute(
            select(CandidateProfile)
            .join(User, User.id == CandidateProfile.user_id)
            .where(CandidateProfile.passport_token == token, *profiles.visible_to_employers())
            .options(*MATCH_PROFILE_OPTIONS)
        )
    ).scalar_one_or_none()
    if profile is None or not await consents.has_consent(
        db, profile.user_id, ConsentType.profile_publication
    ):
        raise not_found
    facts = (await profiles.load_facts(db, [profile.user_id]))[profile.user_id]
    return PublicPassport(
        profile=profiles.to_out(profile, facts),
        achievements=await list_achievements(db, profile.user_id),
        radar=skill_radar(profile),
        public_url=passport_url(profile),
    )
