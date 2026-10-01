"""Framework-independent skill-gap scoring.

For each requirement, ``raw_gap = max(0, required_level - user_level)`` and
``weighted_gap = raw_gap * importance``. The overall gap score is
``sum(weighted_gap) / sum(required_level * importance)`` and is between 0.0
and 1.0. The match percentage is ``round((1 - overall_gap_score) * 100, 1)``.
Over-qualified users receive no negative gap or bonus. Requirements with no
importance contribute zero to both sums.
"""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Union


@dataclass(frozen=True)
class SkillRequirement:
    """A role's expected level and relative importance for one skill."""

    skill: str
    required_level: int
    importance: float


@dataclass(frozen=True)
class SkillGap:
    """The calculated gap between a requirement and a user's skill level."""

    skill: str
    required_level: int
    user_level: int
    raw_gap: int
    weighted_gap: float
    importance: float
    status: str


@dataclass(frozen=True)
class GapReport:
    """A complete, sorted gap report for one role."""

    role_title: str
    skill_gaps: list[SkillGap]
    overall_gap_score: float
    overall_match_percent: float
    missing: list[SkillGap]
    partial: list[SkillGap]
    met: list[SkillGap]


def _validate_requirement(requirement: SkillRequirement) -> None:
    """Validate one requirement and raise a descriptive ``ValueError``."""
    if not isinstance(requirement.required_level, int) or isinstance(
        requirement.required_level, bool
    ) or not 1 <= requirement.required_level <= 5:
        raise ValueError(
            f"required_level for {requirement.skill!r} must be an integer from 1 to 5"
        )
    if not isinstance(requirement.importance, (int, float)) or isinstance(
        requirement.importance, bool
    ) or not 0 <= requirement.importance <= 1:
        raise ValueError(
            f"importance for {requirement.skill!r} must be a number from 0 to 1"
        )


def load_role(path_or_slug: Union[str, Path]) -> tuple[str, list[SkillRequirement]]:
    """Load a role JSON file by slug or path and return its title and requirements."""
    candidate = Path(path_or_slug)
    if not candidate.is_file():
        candidate = Path(__file__).parents[1] / "knowledge_base" / "roles" / f"{path_or_slug}.json"
    with candidate.open(encoding="utf-8") as role_file:
        data = json.load(role_file)
    requirements = [
        SkillRequirement(
            skill=item["skill"],
            required_level=item["required_level"],
            importance=item["importance"],
        )
        for item in data["skills"]
    ]
    if not requirements:
        raise ValueError("role must contain at least one skill requirement")
    for requirement in requirements:
        _validate_requirement(requirement)
    return data["title"], requirements


def calculate_gap(
    requirements: list[SkillRequirement],
    user_skills: dict[str, int],
    role_title: str = "",
) -> GapReport:
    """Calculate sorted skill gaps for a user's case-insensitive skill profile."""
    if not requirements:
        raise ValueError("requirements must not be empty")
    for requirement in requirements:
        _validate_requirement(requirement)

    for name, level in user_skills.items():
        if not isinstance(level, int) or isinstance(level, bool) or not 0 <= level <= 5:
            raise ValueError(f"user level for {name!r} must be an integer from 0 to 5")
    normalized_user = {
        name.strip().casefold(): level for name, level in user_skills.items()
    }
    gaps = []
    for requirement in requirements:
        user_level = normalized_user.get(requirement.skill.strip().casefold(), 0)
        raw_gap = max(0, requirement.required_level - user_level)
        status = "missing" if user_level == 0 else (
            "partial" if user_level < requirement.required_level else "met"
        )
        gaps.append(
            SkillGap(
                skill=requirement.skill,
                required_level=requirement.required_level,
                user_level=user_level,
                raw_gap=raw_gap,
                weighted_gap=raw_gap * requirement.importance,
                importance=requirement.importance,
                status=status,
            )
        )

    gaps.sort(key=lambda gap: (-gap.weighted_gap, -gap.importance, gap.skill))
    denominator = sum(item.required_level * item.importance for item in requirements)
    gap_score = sum(item.weighted_gap for item in gaps) / denominator if denominator else 0.0
    gap_score = min(1.0, max(0.0, gap_score))
    return GapReport(
        role_title=role_title,
        skill_gaps=gaps,
        overall_gap_score=gap_score,
        overall_match_percent=round((1 - gap_score) * 100, 1),
        missing=[gap for gap in gaps if gap.status == "missing"],
        partial=[gap for gap in gaps if gap.status == "partial"],
        met=[gap for gap in gaps if gap.status == "met"],
    )
