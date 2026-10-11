from app.categorize import categorize
from app.grade import grade_status
from app.schemas import (
    CategorizeRequest,
    GradeStatusRequest,
    MatcherFspAchievement,
)


def test_declared_specialization_dominates():
    result = categorize(
        CategorizeRequest(
            candidate_id=15,
            specialization="Frontend",
            skills=["React", "TypeScript", "Python"],
        )
    )
    assert result.category == "Frontend"
    assert result.confidence >= 0.5
    assert any("Frontend" in r for r in result.reasons)


def test_skills_infer_backend_without_declaration():
    result = categorize(
        CategorizeRequest(skills=["Python", "FastAPI", "PostgreSQL", "Docker"])
    )
    assert result.category == "Backend"


def test_fsp_is_soft_signal_not_tech_proof():
    result = categorize(
        CategorizeRequest(
            specialization="Backend",
            skills=["Python"],
            fsp_achievements=[
                MatcherFspAchievement(
                    id="1",
                    title="Кубок",
                    discipline="Программирование продуктовое",
                    verified=True,
                )
            ],
        )
    )
    assert result.category == "Backend"


def test_grade_never_auto_downgrades():
    out = grade_status(GradeStatusRequest(declared_grade="Middle", test_score=62))
    assert out.declared_grade == "Middle"
    assert out.grade_status == "not_confirmed"


def test_grade_confirmed_on_pass():
    out = grade_status(GradeStatusRequest(declared_grade="Junior", test_score=82))
    assert out.grade_status == "confirmed"
