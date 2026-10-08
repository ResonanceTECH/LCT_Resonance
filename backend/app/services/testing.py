from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.candidate import CandidateProfile
from app.models.enums import GradeVerificationStatus, TestAttemptStatus
from app.models.taxonomy import Grade, Specialization
from app.models.testing import TestAnswer, TestAttempt, TestQuestion
from app.schemas.testing import (
    AttemptStartResponse,
    CategoryOut,
    QuestionOption,
    QuestionOut,
    SubmitTestResponse,
)
from app.services.audit import write_audit

# topic slots for MVP blueprint
BLUEPRINT: list[tuple[str, int]] = [
    ("http", 2),
    ("databases", 2),
    ("python", 3),
    ("algorithms", 1),
    ("architecture", 2),
]


async def start_attempt(
    db: AsyncSession,
    *,
    candidate_user_id: UUID,
    specialization_id: UUID,
    grade_id: UUID,
) -> AttemptStartResponse:
    spec = await db.get(Specialization, specialization_id)
    grade = await db.get(Grade, grade_id)
    if not spec or not grade:
        raise AppError("TAXONOMY_NOT_FOUND", "Specialization or grade not found", 404)

    profile = await db.get(CandidateProfile, candidate_user_id)
    if profile is None:
        raise AppError("PROFILE_NOT_FOUND", "Profile not found", 404)

    settings = get_settings()
    if (
        profile.verified_grade_id
        and profile.last_grade_change_at
        and grade_id != profile.verified_grade_id
    ):
        next_at = profile.last_grade_change_at + timedelta(days=settings.grade_cooldown_days)
        if datetime.now(UTC) < next_at:
            raise AppError(
                "GRADE_CHANGE_COOLDOWN",
                "Grade change cooldown active",
                409,
                {"next_available_at": next_at.isoformat()},
            )

    selected: list[TestQuestion] = []
    for topic, count in BLUEPRINT:
        result = await db.execute(
            select(TestQuestion).where(
                TestQuestion.specialization_id == specialization_id,
                TestQuestion.grade_id == grade_id,
                TestQuestion.topic == topic,
                TestQuestion.is_active.is_(True),
            )
        )
        pool = list(result.scalars().all())
        if len(pool) < count:
            # fallback: any topic for this grade/spec
            result = await db.execute(
                select(TestQuestion).where(
                    TestQuestion.specialization_id == specialization_id,
                    TestQuestion.grade_id == grade_id,
                    TestQuestion.is_active.is_(True),
                )
            )
            pool = list(result.scalars().all())
        if not pool:
            raise AppError("TEST_BANK_EMPTY", "No questions available for this category", 409)
        take = min(count, len(pool))
        selected.extend(random.sample(pool, take))

    # pad to 10 if needed
    if len(selected) < 10:
        result = await db.execute(
            select(TestQuestion).where(
                TestQuestion.specialization_id == specialization_id,
                TestQuestion.grade_id == grade_id,
                TestQuestion.is_active.is_(True),
            )
        )
        extras = [q for q in result.scalars().all() if q not in selected]
        random.shuffle(extras)
        selected.extend(extras[: 10 - len(selected)])

    random.shuffle(selected)
    expires = datetime.now(UTC) + timedelta(minutes=30)
    attempt = TestAttempt(
        candidate_user_id=candidate_user_id,
        specialization_id=specialization_id,
        grade_id=grade_id,
        status=TestAttemptStatus.in_progress.value,
        question_ids=[str(q.id) for q in selected],
        expires_at=expires,
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)

    questions_out: list[QuestionOut] = []
    for q in selected:
        opts = list(q.options)
        random.shuffle(opts)
        questions_out.append(
            QuestionOut(
                id=q.id,
                topic=q.topic,
                text=q.prompt,
                options=[QuestionOption(id=o["id"], text=o["text"]) for o in opts],
            )
        )

    return AttemptStartResponse(
        attempt_id=attempt.id,
        specialization=spec.slug,
        grade=grade.code,
        expires_at=expires,
        questions=questions_out,
    )


async def submit_attempt(
    db: AsyncSession,
    *,
    attempt_id: UUID,
    candidate_user_id: UUID,
    answers: list[tuple[UUID, str]],
) -> SubmitTestResponse:
    attempt = await db.get(TestAttempt, attempt_id)
    if attempt is None or attempt.candidate_user_id != candidate_user_id:
        raise AppError("TEST_NOT_FOUND", "Attempt not found", 404)
    if attempt.status == TestAttemptStatus.submitted.value:
        raise AppError("TEST_ALREADY_SUBMITTED", "Test already submitted", 409)
    if attempt.expires_at < datetime.now(UTC):
        attempt.status = TestAttemptStatus.expired.value
        await db.commit()
        raise AppError("TEST_EXPIRED", "Test attempt expired", 409)

    allowed = set(attempt.question_ids)
    correct_count = 0
    for qid, option_id in answers:
        if str(qid) not in allowed:
            continue
        question = await db.get(TestQuestion, qid)
        if question is None:
            continue
        is_correct = option_id == question.correct_answer
        if is_correct:
            correct_count += 1
        db.add(
            TestAnswer(
                attempt_id=attempt.id,
                question_id=qid,
                selected_option_id=option_id,
                is_correct=is_correct,
            )
        )

    total = max(len(attempt.question_ids), 1)
    score = int(round(100 * correct_count / total))
    settings = get_settings()
    passed = score >= settings.pass_score

    attempt.score = score
    attempt.passed = passed
    attempt.status = TestAttemptStatus.submitted.value
    attempt.submitted_at = datetime.now(UTC)

    profile = await db.get(CandidateProfile, candidate_user_id)
    assert profile is not None
    profile.last_test_score = score

    grade = await db.get(Grade, attempt.grade_id)
    spec = await db.get(Specialization, attempt.specialization_id)
    verified_grade_code: str | None = None
    category = None

    if passed:
        profile.verified_specialization_id = attempt.specialization_id
        profile.verified_grade_id = attempt.grade_id
        profile.grade_verification_status = GradeVerificationStatus.verified.value
        if profile.verified_grade_id != attempt.grade_id or not profile.last_grade_change_at:
            profile.last_grade_change_at = datetime.now(UTC)
        verified_grade_code = grade.code if grade else None
        category = CategoryOut(
            specialization=spec.slug if spec else "",
            grade=grade.code if grade else "",
        )
        await write_audit(
            db,
            action="GRADE_VERIFIED",
            entity_type="candidate",
            entity_id=str(candidate_user_id),
            actor_user_id=candidate_user_id,
            metadata={"grade": verified_grade_code, "score": score},
        )
    else:
        if profile.grade_verification_status != GradeVerificationStatus.verified.value:
            profile.grade_verification_status = GradeVerificationStatus.failed.value

    await write_audit(
        db,
        action="TEST_SUBMITTED",
        entity_type="test_attempt",
        entity_id=str(attempt.id),
        actor_user_id=candidate_user_id,
        metadata={"score": score, "passed": passed},
    )
    await db.commit()

    return SubmitTestResponse(
        attempt_id=attempt.id,
        score=score,
        passed=passed,
        tested_grade=grade.code if grade else "",
        verified_grade=verified_grade_code
        if passed
        else (
            (await db.get(Grade, profile.verified_grade_id)).code
            if profile.verified_grade_id
            else None
        ),
        category=category,
    )
