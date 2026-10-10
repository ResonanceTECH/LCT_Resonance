from fastapi import APIRouter, Query
from sqlalchemy import or_, select

from app.core.deps import DbSession
from app.models.taxonomy import Grade, Skill, Specialization
from app.schemas.taxonomy import GradeOut, SkillOut, SpecializationOut
from app.services.taxonomy import like_pattern

router = APIRouter(tags=["taxonomy"])


@router.get("/specializations", response_model=list[SpecializationOut])
async def list_specializations(db: DbSession) -> list[SpecializationOut]:
    rows = (await db.execute(select(Specialization).order_by(Specialization.name))).scalars().all()
    return [SpecializationOut.model_validate(r) for r in rows]


@router.get("/grades", response_model=list[GradeOut])
async def list_grades(db: DbSession) -> list[GradeOut]:
    rows = (await db.execute(select(Grade).order_by(Grade.rank))).scalars().all()
    return [GradeOut.model_validate(r) for r in rows]


@router.get("/skills", response_model=list[SkillOut])
async def list_skills(
    db: DbSession, q: str | None = Query(default=None, max_length=64)
) -> list[SkillOut]:
    """Skill suggestions for profile and vacancy forms."""
    stmt = select(Skill).order_by(Skill.name).limit(50)
    if q and q.strip():
        pattern = like_pattern(q)
        stmt = stmt.where(
            or_(Skill.name.ilike(pattern, escape="\\"), Skill.slug.ilike(pattern, escape="\\"))
        )
    rows = (await db.execute(stmt)).scalars().all()
    return [SkillOut.model_validate(r) for r in rows]
