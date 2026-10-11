from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import AppError
from app.models.candidate import CandidateProfile
from app.models.enums import OfferStatus, TestAttemptStatus, UserRole, UserStatus, VacancyStatus
from app.models.fsp import FspLink
from app.models.offer import Offer
from app.models.taxonomy import Grade, Skill, Specialization
from app.models.testing import TestAttempt, TestQuestion
from app.models.user import AuthSession, User
from app.models.vacancy import Vacancy
from app.schemas.engagement import (
    AdminAssessmentStats,
    AdminAssessmentsResponse,
    AdminAttemptRow,
    AdminCategoriesResponse,
    AdminCategoryRow,
    AdminEvent,
    AdminGradeRef,
    AdminIndustryRef,
    AdminOverview,
    AdminQuestionTemplate,
    AdminScoreBucket,
    AdminSpecializationRef,
    AdminTaxonomySkill,
    AdminTestCatalogItem,
    AdminTestTopic,
    AdminUserRow,
)
from app.services.audit import write_audit

_DIFFICULTY = {1: "easy", 2: "medium", 3: "hard"}


def _row(
    user: User,
    *,
    profile: CandidateProfile | None = None,
    specialization: str | None = None,
    confirmed_grade: str | None = None,
    claimed_grade: str | None = None,
    test_status: str = "none",
    has_fsp_id: bool = False,
    block_reason: str | None = None,
) -> AdminUserRow:
    return AdminUserRow(
        id=user.id,
        email=user.email,
        role=user.role,
        display_name=user.display_name,
        status=user.status,
        created_at=user.created_at,
        specialization=specialization,
        confirmed_grade=confirmed_grade,
        claimed_grade=claimed_grade,
        test_status=test_status,  # type: ignore[arg-type]
        has_fsp_id=has_fsp_id,
        block_reason=block_reason,
    )


async def overview(db: AsyncSession) -> AdminOverview:
    roles = dict((await db.execute(select(User.role, func.count()).group_by(User.role))).all())
    blocked = await db.execute(
        select(func.count()).select_from(User).where(User.status == UserStatus.blocked.value)
    )
    active_vacancies = await db.execute(
        select(func.count())
        .select_from(Vacancy)
        .where(Vacancy.status == VacancyStatus.active.value)
    )
    offers = dict(
        (await db.execute(select(Offer.status, func.count()).group_by(Offer.status))).all()
    )
    completed_attempts = await db.execute(
        select(func.count())
        .select_from(TestAttempt)
        .where(TestAttempt.status == TestAttemptStatus.completed.value)
    )
    confirmed = await db.execute(
        select(func.count())
        .select_from(CandidateProfile)
        .where(CandidateProfile.verified_grade_id.is_not(None))
    )
    candidates = roles.get(UserRole.candidate.value, 0)
    employers = roles.get(UserRole.employer.value, 0)
    offers_total = sum(offers.values())
    events = await _recent_events(db)
    return AdminOverview(
        users_total=candidates + employers,
        candidates=candidates,
        employers=employers,
        vacancies_active=int(active_vacancies.scalar_one()),
        offers_open=offers.get(OfferStatus.new.value, 0) + offers.get(OfferStatus.viewed.value, 0),
        offers_accepted=offers.get(OfferStatus.accepted.value, 0),
        blocked_users=int(blocked.scalar_one()),
        confirmed_categories=int(confirmed.scalar_one()),
        assessments_completed=int(completed_attempts.scalar_one()),
        offers_total=offers_total,
        recent_events=events,
        api_status="ok",
    )


async def _recent_events(db: AsyncSession) -> list[AdminEvent]:
    events: list[AdminEvent] = []

    recent_users = (
        await db.execute(
            select(User)
            .where(User.role != UserRole.admin.value)
            .order_by(User.created_at.desc())
            .limit(3)
        )
    ).scalars().all()
    for user in recent_users:
        role_label = "кандидат" if user.role == UserRole.candidate.value else "работодатель"
        events.append(
            AdminEvent(
                id=f"reg-{user.id}",
                type="user_registered",
                title="Зарегистрирован новый пользователь",
                description=f"{user.display_name} · {role_label}",
                created_at=user.created_at,
                href="/admin/users",
            )
        )

    recent_offers = (
        await db.execute(select(Offer).order_by(Offer.sent_at.desc()).limit(3))
    ).scalars().all()
    for offer in recent_offers:
        events.append(
            AdminEvent(
                id=f"offer-{offer.id}",
                type="offer_sent",
                title="Работодатель отправил приглашение",
                description=f"{offer.company_name} → {offer.position_title}",
                created_at=offer.sent_at,
                href="/admin/offers",
            )
        )

    recent_attempts = (
        await db.execute(
            select(TestAttempt)
            .where(
                TestAttempt.status == TestAttemptStatus.completed.value,
                TestAttempt.submitted_at.is_not(None),
            )
            .order_by(TestAttempt.submitted_at.desc())
            .limit(3)
        )
    ).scalars().all()
    for attempt in recent_attempts:
        user = await db.get(User, attempt.candidate_user_id)
        events.append(
            AdminEvent(
                id=f"test-{attempt.id}",
                type="test_completed",
                title="Кандидат завершил тестирование",
                description=user.display_name if user else None,
                created_at=attempt.submitted_at or attempt.created_at,
                href="/admin/assessments",
            )
        )

    events.sort(key=lambda e: e.created_at, reverse=True)
    return events[:8]


async def list_users(db: AsyncSession) -> list[AdminUserRow]:
    rows = (
        await db.execute(
            select(User)
            .where(User.role != UserRole.admin.value)
            .options(selectinload(User.candidate_profile))
            .order_by(User.created_at.desc())
        )
    ).scalars().all()

    spec_ids = {
        p.declared_specialization_id
        for u in rows
        if (p := u.candidate_profile) and p.declared_specialization_id
    } | {
        p.verified_specialization_id
        for u in rows
        if (p := u.candidate_profile) and p.verified_specialization_id
    }
    grade_ids = {
        p.declared_grade_id for u in rows if (p := u.candidate_profile) and p.declared_grade_id
    } | {
        p.verified_grade_id for u in rows if (p := u.candidate_profile) and p.verified_grade_id
    }
    specs = {
        s.id: s.name
        for s in (
            await db.execute(select(Specialization).where(Specialization.id.in_(spec_ids)))
        ).scalars().all()
    } if spec_ids else {}
    grades = {
        g.id: g.code
        for g in (await db.execute(select(Grade).where(Grade.id.in_(grade_ids)))).scalars().all()
    } if grade_ids else {}

    in_progress_ids = set(
        (
            await db.execute(
                select(TestAttempt.candidate_user_id).where(
                    TestAttempt.status == TestAttemptStatus.in_progress.value
                )
            )
        ).scalars().all()
    )
    fsp_linked = set((await db.execute(select(FspLink.candidate_user_id))).scalars().all())

    result: list[AdminUserRow] = []
    for user in rows:
        profile = user.candidate_profile
        specialization = None
        confirmed_grade = None
        claimed_grade = None
        test_status = "none"
        has_fsp = user.id in fsp_linked
        if profile:
            sid = profile.verified_specialization_id or profile.declared_specialization_id
            specialization = specs.get(sid) if sid else None
            if profile.verified_grade_id:
                confirmed_grade = grades.get(profile.verified_grade_id)
                test_status = "passed"
            if profile.declared_grade_id:
                claimed_grade = grades.get(profile.declared_grade_id)
            if user.id in in_progress_ids:
                test_status = "in_progress"
        result.append(
            _row(
                user,
                profile=profile,
                specialization=specialization,
                confirmed_grade=confirmed_grade,
                claimed_grade=claimed_grade,
                test_status=test_status,
                has_fsp_id=has_fsp,
            )
        )
    return result


async def set_status(
    db: AsyncSession, admin: User, user_id: UUID, status: str, reason: str | None = None
) -> AdminUserRow:
    user = await db.get(User, user_id)
    if user is None or user.role == UserRole.admin.value:
        raise AppError("USER_NOT_FOUND", "Пользователь не найден", 404)
    user.status = status
    if status == UserStatus.blocked.value:
        await db.execute(
            update(AuthSession)
            .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
    await write_audit(
        db,
        action="USER_STATUS_CHANGED",
        entity_type="user",
        entity_id=str(user_id),
        actor_user_id=admin.id,
        metadata={"status": status, "reason": reason},
    )
    await db.commit()
    await db.refresh(user)
    return _row(user, block_reason=reason if status == UserStatus.blocked.value else None)


async def assessments(db: AsyncSession) -> AdminAssessmentsResponse:
    questions = (
        await db.execute(
            select(TestQuestion, Specialization, Grade)
            .join(Specialization, Specialization.id == TestQuestion.specialization_id)
            .join(Grade, Grade.id == TestQuestion.grade_id)
        )
    ).all()

    catalog_map: dict[tuple[str, str], list] = defaultdict(list)
    templates: list[AdminQuestionTemplate] = []
    for question, spec, grade in questions:
        key = (spec.name, grade.code)
        catalog_map[key].append(question)
        difficulty = _DIFFICULTY.get(question.difficulty, "medium")
        templates.append(
            AdminQuestionTemplate(
                id=str(question.id),
                specialization=spec.name,
                topic=question.topic,
                difficulty=difficulty,  # type: ignore[arg-type]
                parameterized="{{" in question.prompt or "{" in question.prompt,
                active=question.is_active,
                prompt_preview=question.prompt[:160],
            )
        )

    catalog: list[AdminTestCatalogItem] = []
    for (spec_name, grade_code), qs in catalog_map.items():
        topic_counts: dict[tuple[str, str], int] = defaultdict(int)
        for q in qs:
            topic_counts[(q.topic, _DIFFICULTY.get(q.difficulty, "medium"))] += 1
        catalog.append(
            AdminTestCatalogItem(
                id=f"{spec_name.lower()}-{grade_code}",
                specialization=spec_name,
                grade=grade_code,
                question_count=len(qs),
                status="active" if any(q.is_active for q in qs) else "archived",
                topics=[
                    AdminTestTopic(name=topic, difficulty=diff, count=count)  # type: ignore[arg-type]
                    for (topic, diff), count in sorted(topic_counts.items())
                ],
            )
        )
    catalog.sort(key=lambda c: (c.specialization, c.grade))

    attempt_rows = (
        await db.execute(
            select(TestAttempt, User, Specialization, Grade)
            .join(User, User.id == TestAttempt.candidate_user_id)
            .join(Specialization, Specialization.id == TestAttempt.specialization_id)
            .join(Grade, Grade.id == TestAttempt.grade_id)
            .where(TestAttempt.status == TestAttemptStatus.completed.value)
            .order_by(TestAttempt.submitted_at.desc().nullslast())
            .limit(50)
        )
    ).all()

    attempts: list[AdminAttemptRow] = []
    scores: list[int] = []
    passed_count = 0
    for attempt, user, spec, grade in attempt_rows:
        score = attempt.score or 0
        scores.append(score)
        if attempt.passed:
            passed_count += 1
        completed_at = attempt.submitted_at or attempt.created_at
        attempts.append(
            AdminAttemptRow(
                id=str(attempt.id),
                user_id=str(user.id),
                display_name=user.display_name,
                specialization=spec.name,
                grade=grade.code,
                score=score,
                max_score=100,
                passed=bool(attempt.passed),
                completed_at=completed_at,
                next_retest_at=completed_at + timedelta(days=90) if attempt.passed else completed_at + timedelta(days=14),
            )
        )

    total = len(scores)
    buckets = [
        AdminScoreBucket(bucket="0–49", count=sum(1 for s in scores if s < 50)),
        AdminScoreBucket(bucket="50–69", count=sum(1 for s in scores if 50 <= s < 70)),
        AdminScoreBucket(bucket="70–84", count=sum(1 for s in scores if 70 <= s < 85)),
        AdminScoreBucket(bucket="85–100", count=sum(1 for s in scores if s >= 85)),
    ]
    return AdminAssessmentsResponse(
        catalog=catalog,
        templates=templates[:100],
        attempts=attempts,
        stats=AdminAssessmentStats(
            success_rate=(passed_count / total) if total else 0.0,
            total_attempts=total,
            score_distribution=buckets,
        ),
    )


_DEFAULT_INDUSTRIES = [
    ("ind-fintech", "Финтех"),
    ("ind-edtech", "EdTech"),
    ("ind-ecommerce", "E-commerce"),
    ("ind-gaming", "Геймдев"),
    ("ind-enterprise", "Enterprise"),
]


async def categories(db: AsyncSession) -> AdminCategoriesResponse:
    specs = (await db.execute(select(Specialization).order_by(Specialization.name))).scalars().all()
    grades = (await db.execute(select(Grade).order_by(Grade.rank))).scalars().all()
    skills = (await db.execute(select(Skill).order_by(Skill.name).limit(100))).scalars().all()

    confirmed_rows = (
        await db.execute(
            select(
                CandidateProfile.verified_specialization_id,
                CandidateProfile.verified_grade_id,
                func.count(),
            )
            .where(
                CandidateProfile.verified_specialization_id.is_not(None),
                CandidateProfile.verified_grade_id.is_not(None),
            )
            .group_by(
                CandidateProfile.verified_specialization_id,
                CandidateProfile.verified_grade_id,
            )
        )
    ).all()
    confirmed_map = {(sid, gid): count for sid, gid, count in confirmed_rows}

    categories_list: list[AdminCategoryRow] = []
    for spec in specs:
        for grade in grades:
            if grade.code in {"intern", "lead"}:
                continue
            categories_list.append(
                AdminCategoryRow(
                    id=f"{spec.slug}-{grade.code}",
                    specialization=spec.name,
                    grade=grade.code,
                    confirmed_candidates=int(confirmed_map.get((spec.id, grade.id), 0)),
                )
            )

    return AdminCategoriesResponse(
        categories=categories_list,
        specializations=[AdminSpecializationRef(id=str(s.id), name=s.name) for s in specs],
        grades=[AdminGradeRef(id=str(g.id), code=g.code, name=g.name) for g in grades],
        skills=[AdminTaxonomySkill(id=str(s.id), name=s.name) for s in skills],
        industries=[AdminIndustryRef(id=i, name=n) for i, n in _DEFAULT_INDUSTRIES],
    )
