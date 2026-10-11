"""Second-stage ordering after the matcher.

Contract order (ML-08), then content similarity, then a stable id:

    score desc → test component desc → category score desc
    → content similarity desc → candidateId asc
"""

from __future__ import annotations

from app.matcher import ScoredPair
from app.schemas import MatcherMatch


def rerank(pairs: list[ScoredPair]) -> list[MatcherMatch]:
    ordered = sorted(
        pairs,
        key=lambda pair: (
            -pair.match.score,
            -(pair.match.components.test if pair.match.components else 0.0),
            -(pair.match.category_score or 0.0),
            -pair.content_similarity,
            pair.match.candidate_id,
        ),
    )
    return [pair.match for pair in ordered]
