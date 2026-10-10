from uuid import UUID

from fastapi import APIRouter

from app.core.deps import CandidateUser, DbSession
from app.schemas.testing import (
    AnswerIn,
    TestHistoryItem,
    TestQuestionOut,
    TestResultOut,
    TestSessionOut,
    TestSessionStart,
)
from app.services import testing

router = APIRouter(prefix="/tests", tags=["tests"])


@router.post("/sessions", response_model=TestSessionOut)
async def start_session(
    payload: TestSessionStart, db: DbSession, user: CandidateUser
) -> TestSessionOut:
    """Starting the same test again resumes the open session."""
    return await testing.start_session(db, user, payload)


@router.get("/sessions/{session_id}/question", response_model=TestQuestionOut)
async def current_question(session_id: UUID, db: DbSession, user: CandidateUser) -> TestQuestionOut:
    return await testing.current_question(db, user, session_id)


@router.post("/sessions/{session_id}/answer", response_model=TestSessionOut)
async def answer(
    session_id: UUID, payload: AnswerIn, db: DbSession, user: CandidateUser
) -> TestSessionOut:
    return await testing.answer(db, user, session_id, payload)


@router.post("/sessions/{session_id}/finish", response_model=TestResultOut)
async def finish(session_id: UUID, db: DbSession, user: CandidateUser) -> TestResultOut:
    """Scored on the server; unanswered questions count as wrong."""
    return await testing.finish(db, user, session_id)


@router.get("/sessions/{session_id}/result", response_model=TestResultOut)
async def result(session_id: UUID, db: DbSession, user: CandidateUser) -> TestResultOut:
    return await testing.result(db, user, session_id)


@router.get("/history", response_model=list[TestHistoryItem])
async def history(db: DbSession, user: CandidateUser) -> list[TestHistoryItem]:
    return await testing.history(db, user)
