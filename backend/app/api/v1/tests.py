from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.core.deps import DbSession, require_roles
from app.core.errors import AppError
from app.models.enums import UserRole
from app.models.testing import TestAttempt
from app.models.user import User
from app.schemas.testing import AttemptStartResponse, StartTestRequest, SubmitTestRequest, SubmitTestResponse
from app.services import testing as testing_service

router = APIRouter(prefix="/tests", tags=["tests"])


@router.post("/attempts", response_model=AttemptStartResponse)
async def start_attempt(
    payload: StartTestRequest,
    db: DbSession,
    user: User = Depends(require_roles(UserRole.candidate)),
) -> AttemptStartResponse:
    return await testing_service.start_attempt(
        db,
        candidate_user_id=user.id,
        specialization_id=payload.specialization_id,
        grade_id=payload.grade_id,
    )


@router.get("/attempts/me")
async def my_attempts(
    db: DbSession,
    user: User = Depends(require_roles(UserRole.candidate)),
) -> list[dict]:
    rows = (
        await db.execute(
            select(TestAttempt)
            .where(TestAttempt.candidate_user_id == user.id)
            .order_by(TestAttempt.created_at.desc())
        )
    ).scalars().all()
    return [
        {
            "id": str(r.id),
            "score": r.score,
            "passed": r.passed,
            "status": r.status,
            "specialization_id": str(r.specialization_id),
            "grade_id": str(r.grade_id),
            "submitted_at": r.submitted_at,
        }
        for r in rows
    ]


@router.get("/attempts/{attempt_id}")
async def get_attempt(
    attempt_id: UUID,
    db: DbSession,
    user: User = Depends(require_roles(UserRole.candidate)),
) -> dict:
    attempt = await db.get(TestAttempt, attempt_id)
    if attempt is None or attempt.candidate_user_id != user.id:
        raise AppError("TEST_NOT_FOUND", "Attempt not found", 404)
    return {
        "id": str(attempt.id),
        "status": attempt.status,
        "score": attempt.score,
        "passed": attempt.passed,
        "expires_at": attempt.expires_at,
    }


@router.post("/attempts/{attempt_id}/submit", response_model=SubmitTestResponse)
async def submit_attempt(
    attempt_id: UUID,
    payload: SubmitTestRequest,
    db: DbSession,
    user: User = Depends(require_roles(UserRole.candidate)),
) -> SubmitTestResponse:
    answers = [(a.question_id, a.option_id) for a in payload.answers]
    return await testing_service.submit_attempt(
        db,
        attempt_id=attempt_id,
        candidate_user_id=user.id,
        answers=answers,
    )
