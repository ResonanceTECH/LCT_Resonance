from app.core.config import get_settings
from app.integrations.matching.base import Matcher
from app.integrations.matching.baseline import BaselineMatcher
from app.integrations.matching.ml import HttpMatcher


def get_matcher() -> Matcher:
    """The configured matcher. Callers fall back to `BaselineMatcher` if it fails."""
    settings = get_settings()
    if settings.matcher_provider == "ml" and settings.ml_matcher_url:
        return HttpMatcher(settings.ml_matcher_url, settings.ml_timeout_sec)
    return BaselineMatcher()


__all__ = ["BaselineMatcher", "HttpMatcher", "Matcher", "get_matcher"]
