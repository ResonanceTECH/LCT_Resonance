"""Rebuild content vectors and the inverted index from stored profiles.

Run after a bulk load:

    python -m app.offline.build
"""

from __future__ import annotations

from app.db.store import Store, get_store


def rebuild_index(store: Store | None = None) -> int:
    target = store or get_store()
    return target.rebuild()


def main() -> None:
    indexed = rebuild_index()
    print(f"indexed {indexed} documents")


if __name__ == "__main__":
    main()
