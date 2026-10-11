"""ML-07: structured reason codes (Backend renders labels)."""

from __future__ import annotations

from app.fsp_features import relevant_achievements, verified_only
from app.schemas import MatcherCandidate, MatcherReason, MatcherVacancy
from app.scoring import STRONG_TEST_SCORE, salary_fits, work_format_fits


def build_reasons(
    candidate: MatcherCandidate,
    vacancy: MatcherVacancy,
    matched: list[str],
) -> list[MatcherReason]:
    out: list[MatcherReason] = []

    if (candidate.specialization or "").casefold() == vacancy.specialization.casefold():
        out.append(
            MatcherReason(
                code="SPECIALIZATION_MATCH", params={"specialization": vacancy.specialization}
            )
        )
    else:
        out.append(
            MatcherReason(
                code="SPECIALIZATION_MISMATCH",
                params={"specialization": candidate.specialization or "не указана"},
                positive=False,
            )
        )

    if (candidate.confirmed_grade or "").casefold() == vacancy.required_grade.casefold():
        out.append(MatcherReason(code="GRADE_CONFIRMED", params={"grade": vacancy.required_grade}))
        if candidate.test_score is not None:
            out.append(
                MatcherReason(
                    code="TEST_SCORE",
                    params={"score": candidate.test_score},
                    positive=candidate.test_score >= STRONG_TEST_SCORE,
                )
            )
    else:
        out.append(
            MatcherReason(
                code="GRADE_NOT_CONFIRMED",
                params={"grade": vacancy.required_grade},
                positive=False,
            )
        )

    if vacancy.required_skills:
        required_matched = sum(1 for s in vacancy.required_skills if s in matched)
        out.append(
            MatcherReason(
                code="SKILLS_REQUIRED",
                params={"matched": required_matched, "total": len(vacancy.required_skills)},
                positive=required_matched == len(vacancy.required_skills),
            )
        )

    if vacancy.nice_to_have_skills:
        optional_matched = sum(1 for s in vacancy.nice_to_have_skills if s in matched)
        out.append(
            MatcherReason(
                code="SKILLS_OPTIONAL",
                params={"matched": optional_matched, "total": len(vacancy.nice_to_have_skills)},
                positive=optional_matched > 0,
            )
        )

    wf = work_format_fits(candidate, vacancy)
    if wf is not None:
        out.append(
            MatcherReason(
                code="WORK_FORMAT_MATCH" if wf else "WORK_FORMAT_MISMATCH",
                params={
                    "workFormat": vacancy.work_format
                    if wf
                    else (candidate.work_format or (candidate.work_formats[0] if candidate.work_formats else ""))
                },
                positive=wf,
            )
        )

    sal = salary_fits(candidate, vacancy)
    if sal is not None:
        out.append(
            MatcherReason(code="SALARY_MATCH" if sal else "SALARY_MISMATCH", positive=sal)
        )

    verified = verified_only(candidate.fsp_achievements)
    if verified:
        out.append(MatcherReason(code="FSP_VERIFIED", params={"count": len(verified)}))
    relevant = relevant_achievements(candidate.fsp_achievements, vacancy)
    if relevant:
        discipline = relevant[0].discipline or relevant[0].title
        out.append(MatcherReason(code="FSP_RELEVANT", params={"discipline": discipline}))

    return out
