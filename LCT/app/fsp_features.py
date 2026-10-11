"""ML-04: FSP achievements → ranking features. Never mutates `verified`."""

from __future__ import annotations

from app.schemas import MatcherFspAchievement, MatcherVacancy
from app.skills.dictionary import FSP_DISCIPLINE_CATEGORY
from app.skills.normalize import normalize_skill_key

FSP_POINTS = {"participation": 10, "finalist": 20, "prize": 30}
FSP_SPORT_RANK_BONUS = 40
FSP_SIGNAL_CAP = 100
FSP_RELEVANCE_BONUS = 15  # once, if any verified achievement is relevant


def _place_type(achievement: MatcherFspAchievement) -> str:
    if achievement.achievement_type in FSP_POINTS:
        return achievement.achievement_type
    text = (achievement.place_or_result or "").casefold()
    if any(x in text for x in ("1 место", "2 место", "3 место", "призёр", "призер", "победитель")):
        return "prize"
    if "финал" in text:
        return "finalist"
    return "participation"


def verified_only(achievements: list[MatcherFspAchievement]) -> list[MatcherFspAchievement]:
    return [a for a in achievements if a.verified]


def fsp_signal(achievements: list[MatcherFspAchievement], vacancy: MatcherVacancy | None = None) -> float:
    """0..100 signal. Empty / unverified → 0 (ML-10: not an error)."""
    verified = verified_only(achievements)
    if not verified:
        return 0.0
    points = sum(FSP_POINTS.get(_place_type(a), FSP_POINTS["participation"]) for a in verified)
    if any(a.sport_rank for a in verified):
        points += FSP_SPORT_RANK_BONUS
    if vacancy is not None and relevant_achievements(verified, vacancy):
        points += FSP_RELEVANCE_BONUS
    return float(min(FSP_SIGNAL_CAP, points))


def relevant_achievements(
    achievements: list[MatcherFspAchievement], vacancy: MatcherVacancy
) -> list[MatcherFspAchievement]:
    keys = {
        normalize_skill_key(s)
        for s in [vacancy.specialization, *vacancy.required_skills, *vacancy.nice_to_have_skills]
    }
    keys.discard("")
    spec = vacancy.specialization.strip().casefold()

    out: list[MatcherFspAchievement] = []
    for a in verified_only(achievements):
        blob = " ".join(filter(None, [a.discipline, a.title, a.place_or_result]))
        words = {normalize_skill_key(w) for w in blob.replace("/", " ").split()}
        if words & keys or normalize_skill_key(blob) in keys:
            out.append(a)
            continue
        for needle, category in FSP_DISCIPLINE_CATEGORY.items():
            if needle in blob.casefold() and (
                category.casefold() == spec or category.casefold() in spec
            ):
                out.append(a)
                break
    return out


def fsp_feature_vector(achievements: list[MatcherFspAchievement]) -> dict[str, float | int | bool]:
    verified = verified_only(achievements)
    return {
        "has_verified": bool(verified),
        "count": len(verified),
        "has_sport_rank": any(a.sport_rank for a in verified),
        "prize_count": sum(1 for a in verified if _place_type(a) == "prize"),
        "signal": fsp_signal(achievements),
    }
