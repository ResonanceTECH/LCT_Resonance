"""ML-03: grade status. Never auto-downgrade declared grade."""

from __future__ import annotations

from app.schemas import GradeStatusRequest, GradeStatusResponse


def grade_status(req: GradeStatusRequest) -> GradeStatusResponse:
    if req.test_score is None:
        status = "unknown"
    elif req.test_score >= req.pass_score:
        status = "confirmed"
    else:
        status = "not_confirmed"
    return GradeStatusResponse(
        declared_grade=req.declared_grade,
        test_score=req.test_score,
        grade_status=status,
    )
