from __future__ import annotations

from app.schemas.common import MatchComponents, Reason
from app.schemas.matcher_contract import (
    MatcherMatch,
    MatchingRequest,
    MatchingResponse,
)

FSP_WEIGHTS = {
    "participation": 10,
    "finalist": 20,
    "prize": 30,
    "sport_rank": 40,
}

REASON_TEXT = {
    "CATEGORY_MATCH": "Подтверждённая категория совпадает с потребностью",
    "TEST_STRONG": "Сильный результат тестирования",
    "SKILLS_MATCH": "Совпадают обязательные навыки",
    "SKILLS_PARTIAL": "Частичное совпадение навыков",
    "FSP_VERIFIED": "Есть подтверждённые достижения ФСП",
    "WORK_FORMAT_MATCH": "Подходит формат работы",
    "SALARY_FIT": "Зарплатные ожидания укладываются в вилку",
}


class BaselineMatcher:
    async def rank(self, request: MatchingRequest) -> MatchingResponse:
        matches: list[MatcherMatch] = []
        for cand in request.candidates:
            if cand.verified_specialization != request.need.specialization:
                continue
            if cand.verified_grade != request.need.grade:
                continue

            test_score = float(cand.test_score or 0)
            skill_match, matched, missing = self._skills(
                set(cand.skills),
                request.need.required_skills,
                request.need.optional_skills,
            )
            fsp_signal = self._fsp(cand.fsp_achievements)
            conditions = self._conditions(cand, request)

            score = (
                0.50 * test_score
                + 0.25 * skill_match
                + 0.15 * fsp_signal
                + 0.10 * conditions
            )
            reasons_codes: list[str] = ["CATEGORY_MATCH"]
            if test_score >= 70:
                reasons_codes.append("TEST_STRONG")
            if missing == [] and request.need.required_skills:
                reasons_codes.append("SKILLS_MATCH")
            elif matched:
                reasons_codes.append("SKILLS_PARTIAL")
            if cand.fsp_achievements:
                reasons_codes.append("FSP_VERIFIED")
            if request.need.work_format and cand.work_format == request.need.work_format:
                reasons_codes.append("WORK_FORMAT_MATCH")
            if (
                request.need.salary_to is not None
                and cand.salary_min is not None
                and cand.salary_min <= request.need.salary_to
            ):
                reasons_codes.append("SALARY_FIT")

            matches.append(
                MatcherMatch(
                    candidate_id=cand.id,
                    score=round(score, 2),
                    components=MatchComponents(
                        test=round(0.50 * test_score, 2),
                        skills=round(0.25 * skill_match, 2),
                        fsp=round(0.15 * fsp_signal, 2),
                        conditions=round(0.10 * conditions, 2),
                    ),
                    matched_skills=matched,
                    missing_skills=missing,
                    reason_codes=reasons_codes,
                )
            )

        matches.sort(key=lambda m: m.score, reverse=True)
        return MatchingResponse(matches=matches, model_version="baseline-v1")

    def _skills(
        self, candidate_skills: set[str], required: list[str], optional: list[str]
    ) -> tuple[float, list[str], list[str]]:
        cand = {s.lower() for s in candidate_skills}
        req = [s.lower() for s in required]
        opt = [s.lower() for s in optional]
        total = 2 * len(req) + 1 * len(opt)
        if total == 0:
            return 100.0, [], []
        matched_w = 0
        matched: list[str] = []
        missing: list[str] = []
        for s in req:
            if s in cand:
                matched_w += 2
                matched.append(s)
            else:
                missing.append(s)
        for s in opt:
            if s in cand:
                matched_w += 1
                matched.append(s)
            else:
                missing.append(s)
        return 100.0 * matched_w / total, matched, missing

    def _fsp(self, achievements) -> float:
        total = 0
        for a in achievements:
            total += FSP_WEIGHTS.get(a.type, 5)
            if a.discipline and "rank" in (a.result or "").lower():
                total += FSP_WEIGHTS["sport_rank"]
        return float(min(100, total))

    def _conditions(self, cand, request: MatchingRequest) -> float:
        wf = 50.0
        if request.need.work_format:
            wf = 100.0 if cand.work_format == request.need.work_format else 0.0
        sal = 50.0
        if request.need.salary_to is not None and cand.salary_min is not None:
            sal = 100.0 if cand.salary_min <= request.need.salary_to else 0.0
        elif cand.salary_min is None:
            sal = 50.0
        return 0.5 * wf + 0.5 * sal


def reasons_from_codes(codes: list[str], test_score: int | None = None) -> list[Reason]:
    out: list[Reason] = []
    for code in codes:
        text = REASON_TEXT.get(code, code)
        if code == "TEST_STRONG" and test_score is not None:
            text = f"Результат тестирования {test_score}/100"
        out.append(Reason(code=code, text=text))
    return out
