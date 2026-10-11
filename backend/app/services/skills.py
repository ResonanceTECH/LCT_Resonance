from __future__ import annotations

import re

# Matching keys → canonical key. Keep in sync with ml/app/skills/dictionary.py (subset is OK).
_ALIASES = {
    "reactjs": "react",
    "reactnative": "reactnative",
    "js": "javascript",
    "ecmascript": "javascript",
    "es6": "javascript",
    "ts": "typescript",
    "postgres": "postgresql",
    "pgsql": "postgresql",
    "py": "python",
    "python3": "python",
    "golang": "go",
    "k8s": "kubernetes",
    "nodejs": "nodejs",
    "node": "nodejs",
    "nextjs": "nextjs",
    "vuejs": "vue",
    "angularjs": "angular",
    "cplusplus": "cplusplus",
    "cpp": "cplusplus",
    "csharp": "csharp",
    "cs": "csharp",
    "tf": "tensorflow",
    "sklearn": "scikitlearn",
    "scikitlearn": "scikitlearn",
    "cicd": "cicd",
    "githubactions": "cicd",
    "mongo": "mongodb",
    "tailwindcss": "tailwind",
    "tailwind": "tailwind",
}


def normalize_skill_name(value: str) -> str:
    """Return a stable matching key for common spelling variants of skills."""
    key = re.sub(r"[^a-z0-9+#]+", "", value.casefold())
    return _ALIASES.get(key, key)
