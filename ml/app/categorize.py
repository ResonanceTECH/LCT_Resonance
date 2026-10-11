"""ML-02: professional category inference.

Declared specialization dominates; skills / FSP / roles are soft evidence only.
"""

from __future__ import annotations

from app.schemas import CategorizeRequest, CategorizeResponse, MatcherFspAchievement
from app.skills.dictionary import FSP_DISCIPLINE_CATEGORY, SKILL_CATEGORY_PRIORS
from app.skills.normalize import canonicalize_skill

CATEGORIES = [
    "Frontend",
    "Backend",
    "Mobile",
    "ML / Data Science",
    "Data Engineering",
    "DevOps",
    "QA",
    "Cybersecurity",
    "Algorithms",
    "Other",
]

# Map free-text / Backend specialization names onto the MVP taxonomy.
_SPEC_ALIASES: dict[str, str] = {
    "frontend": "Frontend",
    "backend": "Backend",
    "mobile": "Mobile",
    "ml": "ML / Data Science",
    "ml / data science": "ML / Data Science",
    "data science": "ML / Data Science",
    "data engineering": "Data Engineering",
    "devops": "DevOps",
    "qa": "QA",
    "cybersecurity": "Cybersecurity",
    "security": "Cybersecurity",
    "algorithms": "Algorithms",
    "other": "Other",
}

DECLARED_WEIGHT = 3.0
SKILL_WEIGHT = 1.0
FSP_WEIGHT = 0.8
ROLE_WEIGHT = 0.4
# Soft confirmation of the declared track when experience is present (never overrides skills alone).
EXPERIENCE_WEIGHT = 0.35


def _norm_spec(value: str | None) -> str | None:
    if not value:
        return None
    key = value.strip().casefold()
    return _SPEC_ALIASES.get(key, value.strip())


def _fsp_votes(achievements: list[MatcherFspAchievement]) -> dict[str, float]:
    votes: dict[str, float] = {}
    for a in achievements:
        if a.verified is False:
            continue
        blob = " ".join(filter(None, [a.discipline, a.title])).casefold()
        for needle, category in FSP_DISCIPLINE_CATEGORY.items():
            if needle in blob:
                votes[category] = votes.get(category, 0.0) + FSP_WEIGHT
                break
    return votes


def _role_votes(roles: list[str]) -> dict[str, float]:
    votes: dict[str, float] = {}
    for role in roles:
        r = role.casefold()
        if "backend" in r or "сервер" in r:
            votes["Backend"] = votes.get("Backend", 0.0) + ROLE_WEIGHT
        elif "front" in r or "веб" in r:
            votes["Frontend"] = votes.get("Frontend", 0.0) + ROLE_WEIGHT
        elif "mobile" in r or "мобил" in r:
            votes["Mobile"] = votes.get("Mobile", 0.0) + ROLE_WEIGHT
        elif "ml" in r or "данн" in r:
            votes["ML / Data Science"] = votes.get("ML / Data Science", 0.0) + ROLE_WEIGHT
    return votes


def categorize(req: CategorizeRequest) -> CategorizeResponse:
    scores: dict[str, float] = {c: 0.0 for c in CATEGORIES}
    reasons: list[str] = []

    declared = _norm_spec(req.specialization)
    if declared and declared in scores:
        scores[declared] += DECLARED_WEIGHT
        reasons.append(f"Кандидат указал специализацию {declared}")
    elif declared:
        scores["Other"] += DECLARED_WEIGHT * 0.5
        reasons.append(f"Кандидат указал специализацию {declared}")

    supporting: list[str] = []
    for raw in req.skills:
        canonical = canonicalize_skill(raw)
        priors = SKILL_CATEGORY_PRIORS.get(canonical, {})
        for category, w in priors.items():
            if category in scores:
                scores[category] += SKILL_WEIGHT * w
        if declared and declared in priors and canonical not in supporting:
            supporting.append(canonical)
    if supporting:
        reasons.append("В профиле указаны " + " и ".join(supporting[:3]))

    for category, w in _fsp_votes(req.fsp_achievements).items():
        scores[category] = scores.get(category, 0.0) + w
    if req.fsp_achievements and any(a.verified for a in req.fsp_achievements):
        reasons.append("Учтены подтверждённые достижения ФСП")

    for category, w in _role_votes(req.competition_roles).items():
        scores[category] = scores.get(category, 0.0) + w

    months = req.experience_months or 0
    if declared and declared in scores and months > 0:
        scores[declared] += EXPERIENCE_WEIGHT * min(1.0, months / 24.0)
        if months >= 12:
            reasons.append(f"Указан опыт {months} мес.")

    total = sum(scores.values())
    if total <= 0:
        return CategorizeResponse(
            candidate_id=req.candidate_id,
            category="Other",
            confidence=0.0,
            reasons=["Недостаточно сигналов для категоризации"],
        )

    best = max(CATEGORIES, key=lambda c: scores[c])
    confidence = round(scores[best] / total, 4)
    if not reasons:
        reasons.append(f"Категория выведена по навыкам: {best}")

    return CategorizeResponse(
        candidate_id=req.candidate_id,
        category=best,
        confidence=confidence,
        reasons=reasons,
    )
