"""ML-01: skill spelling normalization."""

from __future__ import annotations

import re

from app.skills.dictionary import SKILL_ALIASES

_NON_ALNUM = re.compile(r"[^a-z0-9+#]+")


def normalize_skill_key(value: str) -> str:
    """Stable matching key (lowercase, punctuation stripped)."""
    raw = value.casefold().strip()
    key = _NON_ALNUM.sub("", raw)
    if key in SKILL_ALIASES:
        return _NON_ALNUM.sub("", SKILL_ALIASES[key].casefold())
    # React.js → reactjs → react via alias; also strip trailing "js" for known libs handled above.
    return key


def canonicalize_skill(value: str) -> str:
    """Human-readable canonical form for explanations / storage hints."""
    key = _NON_ALNUM.sub("", value.casefold().strip())
    return SKILL_ALIASES.get(key, value.strip())


def normalize_skills(skills: list[str]) -> list[str]:
    """Deduplicate by matching key, keep first canonical display name."""
    seen: set[str] = set()
    out: list[str] = []
    for skill in skills:
        if not skill or not skill.strip():
            continue
        key = normalize_skill_key(skill)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(canonicalize_skill(skill))
    return out
