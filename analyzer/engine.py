"""Thin orchestration layer for matching, scoring, and recommendations."""

from __future__ import annotations

from dataclasses import dataclass

from analyzer.gap_scoring import GapReport, calculate_gap, load_role
from analyzer.matching import SkillMatcher
from analyzer.recommender import Recommendation, load_role_resources, recommend


@dataclass(frozen=True)
class AnalysisResult:
    """Complete output from one role analysis."""

    role_title: str
    gap_report: GapReport
    recommendations: list[Recommendation]
    unmatched_inputs: list[str]


def analyze(
    job_title_or_slug: str,
    user_skills_freetext: dict[str, int],
    matcher: SkillMatcher | None = None,
    top_n: int | None = None,
) -> AnalysisResult:
    """Analyze free-text user skills against a role and recommend resources."""

    try:
        role_title, requirements = load_role(job_title_or_slug)
    except (FileNotFoundError, OSError, ValueError) as exc:
        raise ValueError(f"unknown role: {job_title_or_slug!r}") from exc

    # In Django, pass a shared app-startup matcher here instead of creating one per call.
    active_matcher = matcher or SkillMatcher()
    inputs = list(user_skills_freetext)
    matches = active_matcher.match_many(inputs)
    matched_skills: dict[str, int] = {}
    unmatched_inputs: list[str] = []
    for input_text, level, result in zip(inputs, user_skills_freetext.values(), matches):
        if not result.matched or result.matched_skill is None:
            unmatched_inputs.append(input_text)
            continue
        # If multiple phrases map to one skill, retain the user's highest level.
        matched_skills[result.matched_skill] = max(
            level, matched_skills.get(result.matched_skill, 0)
        )

    gap_report = calculate_gap(requirements, matched_skills, role_title)
    role_resources = load_role_resources(job_title_or_slug)
    recommendations = recommend(gap_report, role_resources, top_n=top_n)
    return AnalysisResult(role_title, gap_report, recommendations, unmatched_inputs)
