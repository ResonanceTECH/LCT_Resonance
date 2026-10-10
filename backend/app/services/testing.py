"""Testing as the frontend runs it: a session answered one question at a time.

POST /tests/sessions -> GET .../question -> POST .../answer (repeat) -> POST .../finish.
All question instances are generated at start (Backend.md, "Механика тестирования").
"""

from __future__ import annotations

import random
import secrets
from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.candidate import CandidateProfile
from app.models.enums import GradeVerificationStatus, NotificationType, TestAttemptStatus
from app.models.taxonomy import Grade
from app.models.testing import TestAttempt, TestAttemptItem, TestQuestion
from app.models.user import User
from app.schemas.testing import (
    AnswerIn,
    QuestionOption,
    TestHistoryItem,
    TestQuestionOut,
    TestResultOut,
    TestSessionOut,
    TestSessionStart,
)
from app.services import taxonomy
from app.services.audit import write_audit
from app.services.notifications import notify
from app.services.question_generators import Generator, generate, generators_for

QUESTIONS_PER_TEST = 10

# Topic slots per specialization slug. Each slot prefers generated questions, then static
# ones of the same topic; the test is topped up from the rest of the category pool.
BLUEPRINTS: dict[str, list[tuple[str, int]]] = {
    "backend": [
        ("http", 2),
        ("databases", 2),
        ("python", 3),
        ("algorithms", 1),
        ("architecture", 2),
    ],
    "frontend": [("javascript", 3), ("react", 3), ("http", 2), ("architecture", 2)],
}

# A planned slot: a static bank question or a generator to instantiate with a fresh seed.
QuestionSource = TestQuestion | Generator

_rng = random.SystemRandom()


def _now() -> datetime:
    return datetime.now(UTC)


def plan_questions(
    pool: Sequence[TestQuestion],
    blueprint: Sequence[tuple[str, int]],
    generators_by_topic: dict[str, list[Generator]],
    total: int = QUESTIONS_PER_TEST,
    rng: random.Random = _rng,
) -> list[QuestionSource]:
    """Choose what to ask: per topic slot, distinct generators first, then static items.

    Generated items cannot leak between candidates, so they are preferred; a generator is
    reused (with another seed) only when a topic has no static questions left.
    """
    static_by_topic: dict[str, list[TestQuestion]] = defaultdict(list)
    for question in pool:
        static_by_topic[question.topic].append(question)
    for questions in static_by_topic.values():
        rng.shuffle(questions)

    plan: list[QuestionSource] = []
    for topic, count in blueprint:
        generators = list(generators_by_topic.get(topic, []))
        rng.shuffle(generators)
        chosen: list[QuestionSource] = list(generators[:count])
        statics = static_by_topic.get(topic, [])
        while len(chosen) < count and statics:
            chosen.append(statics.pop())
        while len(chosen) < count and generators:
            chosen.append(rng.choice(generators))
        plan.extend(chosen)

    leftovers = [q for questions in static_by_topic.values() for q in questions]
    rng.shuffle(leftovers)
    plan.extend(leftovers[: max(0, total - len(plan))])
    all_generators = [g for gens in generators_by_topic.values() for g in gens]
    while len(plan) < total and all_generators:
        plan.append(rng.choice(all_generators))

    plan = plan[:total]
    rng.shuffle(plan)
    return plan


def _new_item(position: int, source: QuestionSource) -> TestAttemptItem:
    if isinstance(source, TestQuestion):
        options = list(source.options)
        _rng.shuffle(options)
        return TestAttemptItem(
            position=position,
            source="static",
            question_id=source.id,
            topic=source.topic,
            prompt=source.prompt,
            options=options,
            correct_option_id=source.correct_answer,
        )
    seed = secrets.randbits(63)  # fits BIGINT; stored so the task can be reproduced
    instance = generate(source.key, seed)
    return TestAttemptItem(
        position=position,
        source="generated",
        generator_key=source.key,
        seed=seed,
        topic=source.topic,
        prompt=instance.prompt,
        code=instance.code,
        options=instance.options,
        correct_option_id=instance.correct_option_id,
    )


def score_percent(correct: int, total: int) -> int:
    return round(100 * correct / max(total, 1))


def _retry_available_at(submitted_at: datetime) -> datetime:
    return submitted_at + timedelta(hours=get_settings().test_retry_cooldown_hours)


def _format_date(value: datetime) -> str:
    return value.strftime("%d.%m.%Y %H:%M UTC")


def _check_grade_cooldown(
    profile: CandidateProfile, specialization_id: UUID, grade_id: UUID
) -> None:
    """A confirmed category may change at most once per GRADE_COOLDOWN_DAYS.

    Re-testing the current category is always allowed.
    """
    if not profile.verified_grade_id or not profile.last_grade_change_at:
        return
    if (
        profile.verified_grade_id == grade_id
        and profile.verified_specialization_id == specialization_id
    ):
        return
    next_at = profile.last_grade_change_at + timedelta(days=get_settings().grade_cooldown_days)
    if _now() < next_at:
        raise AppError(
            "GRADE_CHANGE_COOLDOWN",
            f"Сменить подтверждённую категорию можно после {_format_date(next_at)}",
            409,
            {"nextAvailableAt": next_at.isoformat()},
        )


async def _check_retry_cooldown(
    db: AsyncSession, *, candidate_user_id: UUID, specialization_id: UUID, grade: Grade
) -> None:
    """After a failed attempt the same or a higher grade waits TEST_RETRY_COOLDOWN_HOURS.

    A lower grade stays available at once (CJM: "повторная попытка доступна после
    таймаута"; Backend.md: a failure must not block trying a lower level).
    """
    hours = get_settings().test_retry_cooldown_hours
    if hours == 0:
        return
    result = await db.execute(
        select(TestAttempt.submitted_at)
        .join(Grade, Grade.id == TestAttempt.grade_id)
        .where(
            TestAttempt.candidate_user_id == candidate_user_id,
            TestAttempt.specialization_id == specialization_id,
            TestAttempt.passed.is_(False),
            TestAttempt.submitted_at > _now() - timedelta(hours=hours),
            # The failed grade is not above the requested one: same or higher is paused.
            Grade.rank <= grade.rank,
        )
        .order_by(TestAttempt.submitted_at.desc())
        .limit(1)
    )
    last_failed_at = result.scalar_one_or_none()
    if last_failed_at is not None:
        next_at = _retry_available_at(last_failed_at)
        raise AppError(
            "TEST_RETRY_COOLDOWN",
            f"Повторить тест этого уровня можно после {_format_date(next_at)}; "
            "уровень ниже доступен сейчас",
            409,
            {"nextAvailableAt": next_at.isoformat()},
        )


async def _get_profile(db: AsyncSession, user_id: UUID) -> CandidateProfile:
    profile = await db.get(CandidateProfile, user_id)
    if profile is None:
        raise AppError("PROFILE_NOT_FOUND", "Профиль не найден", 404)
    return profile


async def _get_session(
    db: AsyncSession, session_id: UUID, user: User, *, for_update: bool = False
) -> TestAttempt:
    stmt = (
        select(TestAttempt)
        .where(TestAttempt.id == session_id)
        .options(selectinload(TestAttempt.items))
        .execution_options(populate_existing=True)
    )
    if for_update:
        stmt = stmt.with_for_update()
    session = (await db.execute(stmt)).scalar_one_or_none()
    if session is None or session.candidate_user_id != user.id:
        raise AppError("TEST_SESSION_NOT_FOUND", "Сессия не найдена", 404)
    return session


async def _ensure_open(db: AsyncSession, session: TestAttempt) -> None:
    if session.status == TestAttemptStatus.completed.value:
        raise AppError("TEST_SESSION_COMPLETED", "Тест уже завершён", 409)
    if session.status == TestAttemptStatus.expired.value or session.expires_at <= _now():
        session.status = TestAttemptStatus.expired.value
        await db.commit()
        raise AppError("TEST_SESSION_EXPIRED", "Время на тест истекло, начните заново", 409)


async def _session_out(db: AsyncSession, session: TestAttempt) -> TestSessionOut:
    spec = await taxonomy.get_specialization(db, session.specialization_id)
    grade = await taxonomy.get_grade(db, session.grade_id)
    return TestSessionOut(
        id=session.id,
        specialization=spec.name,
        stack=session.stack,
        claimed_grade=grade.code,
        current_index=session.current_index,
        total_questions=len(session.items),
        status=session.status,
        expires_at=session.expires_at,
    )


async def start_session(db: AsyncSession, user: User, payload: TestSessionStart) -> TestSessionOut:
    spec = await taxonomy.specialization_by_name(db, payload.specialization)
    grade = await taxonomy.grade_by_code(db, payload.claimed_grade)
    profile = await _get_profile(db, user.id)
    _check_grade_cooldown(profile, spec.id, grade.id)

    # One open session at a time. Re-starting the same test resumes it, so restarting
    # does not reveal a fresh set of questions; another category abandons the old one.
    open_sessions = await db.execute(
        select(TestAttempt)
        .where(
            TestAttempt.candidate_user_id == user.id,
            TestAttempt.status == TestAttemptStatus.in_progress.value,
            TestAttempt.expires_at > _now(),
        )
        .options(selectinload(TestAttempt.items))
    )
    for session in open_sessions.scalars().all():
        if session.specialization_id == spec.id and session.grade_id == grade.id:
            return await _session_out(db, session)
        session.status = TestAttemptStatus.expired.value
    await _check_retry_cooldown(
        db, candidate_user_id=user.id, specialization_id=spec.id, grade=grade
    )

    settings = get_settings()
    pool = (
        (
            await db.execute(
                select(TestQuestion).where(
                    TestQuestion.specialization_id == spec.id,
                    TestQuestion.grade_id == grade.id,
                    TestQuestion.is_active.is_(True),
                    TestQuestion.exposure_count < settings.static_item_max_exposures,
                )
            )
        )
        .scalars()
        .all()
    )
    # Generators define difficulty by structure; they serve the grades the bank covers.
    generators = generators_for(spec.slug) if pool else {}
    plan = plan_questions(pool, BLUEPRINTS.get(spec.slug, []), generators)
    if len(plan) < QUESTIONS_PER_TEST:
        raise AppError(
            "TEST_BANK_INSUFFICIENT",
            f"Тест для категории {spec.name} {grade.code} пока не готов: в банке мало вопросов",
            409,
            {"available": len(plan)},
        )

    for source in plan:
        if isinstance(source, TestQuestion):
            source.exposure_count += 1
    session = TestAttempt(
        candidate_user_id=user.id,
        specialization_id=spec.id,
        grade_id=grade.id,
        status=TestAttemptStatus.in_progress.value,
        stack=[s.strip() for s in payload.stack if s.strip()],
        is_retest=payload.retest,
        current_index=0,
        expires_at=_now() + timedelta(minutes=settings.test_attempt_ttl_min),
        items=[_new_item(position, source) for position, source in enumerate(plan)],
    )
    db.add(session)
    await db.commit()
    return await _session_out(db, session)


async def current_question(db: AsyncSession, user: User, session_id: UUID) -> TestQuestionOut:
    session = await _get_session(db, session_id, user)
    await _ensure_open(db, session)
    if session.current_index >= len(session.items):
        raise AppError("TEST_NO_MORE_QUESTIONS", "Вопросы закончились — завершите тест", 409)
    item = session.items[session.current_index]
    return TestQuestionOut(
        id=item.id,
        text=item.prompt,
        code=item.code,
        options=[QuestionOption(id=str(o["id"]), text=str(o["text"])) for o in item.options],
        index=session.current_index,
        total=len(session.items),
    )


async def answer(
    db: AsyncSession, user: User, session_id: UUID, payload: AnswerIn
) -> TestSessionOut:
    session = await _get_session(db, session_id, user, for_update=True)
    await _ensure_open(db, session)
    item = next((i for i in session.items if i.id == payload.question_id), None)
    if item is None:
        raise AppError("TEST_QUESTION_NOT_FOUND", "Вопрос не относится к этой сессии", 404)
    if payload.option_id not in {str(o["id"]) for o in item.options}:
        raise AppError("INVALID_TEST_OPTION", "Такого варианта ответа нет", 422)
    item.selected_option_id = payload.option_id
    item.is_correct = payload.option_id == item.correct_option_id
    unanswered = [i.position for i in session.items if i.selected_option_id is None]
    session.current_index = min(unanswered) if unanswered else len(session.items)
    await db.commit()
    return await _session_out(db, session)


async def _result_out(db: AsyncSession, session: TestAttempt) -> TestResultOut:
    grade = await taxonomy.get_grade(db, session.grade_id)
    retry_at = None
    if not session.passed and get_settings().test_retry_cooldown_hours and session.submitted_at:
        retry_at = _retry_available_at(session.submitted_at)
    return TestResultOut(
        session_id=session.id,
        score=session.score or 0,
        grade_confirmed=bool(session.passed),
        completed_at=session.submitted_at or session.created_at,
        claimed_grade=grade.code,
        is_retest=session.is_retest,
        retry_available_at=retry_at,
    )


async def finish(db: AsyncSession, user: User, session_id: UUID) -> TestResultOut:
    # Row lock: a double submit must not score the session twice.
    session = await _get_session(db, session_id, user, for_update=True)
    await _ensure_open(db, session)

    # Unanswered questions count as wrong.
    score = score_percent(sum(bool(i.is_correct) for i in session.items), len(session.items))
    passed = score >= get_settings().pass_score
    session.score = score
    session.passed = passed
    session.status = TestAttemptStatus.completed.value
    session.submitted_at = _now()
    session.current_index = len(session.items)

    profile = await _get_profile(db, user.id)
    spec = await taxonomy.get_specialization(db, session.specialization_id)
    grade = await taxonomy.get_grade(db, session.grade_id)
    if passed:
        category_changed = (
            profile.verified_grade_id != session.grade_id
            or profile.verified_specialization_id != session.specialization_id
        )
        if category_changed or profile.last_grade_change_at is None:
            profile.last_grade_change_at = _now()
        profile.verified_specialization_id = session.specialization_id
        profile.verified_grade_id = session.grade_id
        profile.grade_verification_status = GradeVerificationStatus.verified.value
        # Only a passing score represents the verified category used in matching.
        profile.last_test_score = score
        notify(
            db,
            user_id=user.id,
            type=NotificationType.system,
            title="Грейд подтверждён",
            body=f"{spec.name} {grade.code}: {score}/100. Вы в подборке работодателей.",
            href="/candidate/profile",
        )
        await write_audit(
            db,
            action="GRADE_CONFIRMED",
            entity_type="candidate",
            entity_id=str(user.id),
            actor_user_id=user.id,
            metadata={"grade": grade.code, "score": score},
        )
    elif profile.grade_verification_status != GradeVerificationStatus.verified.value:
        # A failed attempt never downgrades an already confirmed grade.
        profile.grade_verification_status = GradeVerificationStatus.failed.value

    await write_audit(
        db,
        action="TEST_FINISHED",
        entity_type="test_session",
        entity_id=str(session.id),
        actor_user_id=user.id,
        metadata={"score": score, "passed": passed},
    )
    await db.commit()
    return await _result_out(db, session)


async def result(db: AsyncSession, user: User, session_id: UUID) -> TestResultOut:
    session = await _get_session(db, session_id, user)
    if session.status != TestAttemptStatus.completed.value:
        raise AppError("TEST_RESULT_UNAVAILABLE", "Результат недоступен: тест не завершён", 404)
    return await _result_out(db, session)


async def history(db: AsyncSession, user: User) -> list[TestHistoryItem]:
    rows = await db.execute(
        select(TestAttempt)
        .where(
            TestAttempt.candidate_user_id == user.id,
            TestAttempt.status == TestAttemptStatus.completed.value,
        )
        .order_by(TestAttempt.submitted_at.desc())
    )
    items = []
    for session in rows.scalars().all():
        spec = await taxonomy.get_specialization(db, session.specialization_id)
        base = await _result_out(db, session)
        items.append(TestHistoryItem(**base.model_dump(), specialization=spec.name))
    return items
