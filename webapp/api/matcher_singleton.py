"""The process-wide embedding matcher used by API requests."""

from analyzer.matching import SkillMatcher


_matcher: SkillMatcher | None = None


def initialize_matcher() -> SkillMatcher:
    """Create the matcher once and return the shared instance."""
    global _matcher
    if _matcher is None:
        # Load the locally trained Word2Vec model once at process startup.
        _matcher = SkillMatcher()
    return _matcher


def get_matcher() -> SkillMatcher:
    """Return the matcher initialized during Django app startup."""
    if _matcher is None:
        return initialize_matcher()
    return _matcher
