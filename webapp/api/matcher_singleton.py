"""The process-wide embedding matcher used by API requests."""

from analyzer.matching import SkillMatcher


_matcher: SkillMatcher | None = None


def initialize_matcher() -> SkillMatcher:
    """Create the matcher once and return the shared instance."""
    global _matcher
    if _matcher is None:
        # The embedding model is about 90 MB and takes seconds to load, so it
        # must not be loaded again for every API request.
        _matcher = SkillMatcher()
    return _matcher


def get_matcher() -> SkillMatcher:
    """Return the matcher initialized during Django app startup."""
    if _matcher is None:
        return initialize_matcher()
    return _matcher
