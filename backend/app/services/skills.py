from __future__ import annotations

import re

_ALIASES = {
    "reactjs": "react",
    "js": "javascript",
    "ecmascript": "javascript",
    "ts": "typescript",
    "postgres": "postgresql",
    "py": "python",
    "golang": "go",
    "k8s": "kubernetes",
}


def normalize_skill_name(value: str) -> str:
    """Return a stable matching key for common spelling variants of skills."""
    key = re.sub(r"[^a-z0-9+#]+", "", value.casefold())
    return _ALIASES.get(key, key)
