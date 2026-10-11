"""SQLite feature store for resumes, vacancies, and the content index."""

from app.db.store import get_store, reset_store

__all__ = ["get_store", "reset_store"]
