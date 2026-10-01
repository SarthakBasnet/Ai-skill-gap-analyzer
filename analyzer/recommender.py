"""Rank learning resources for the skills with the largest gaps."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from analyzer.gap_scoring import GapReport


@dataclass(frozen=True)
class Recommendation:
    """A resource recommendation attached to one unresolved skill gap."""

    skill: str
    weighted_gap: float
    status: str
    resources: list[dict[str, Any]]
    priority_rank: int


def _role_file(path_or_slug: str | Path) -> Path:
    candidate = Path(path_or_slug)
    if not candidate.is_file():
        candidate = Path(__file__).parents[1] / "knowledge_base" / "roles" / f"{path_or_slug}.json"
    return candidate


def load_role_resources(path_or_slug: str | Path) -> dict[str, list[dict[str, Any]]]:
    """Load each role skill's resource list keyed by canonical skill name."""

    candidate = _role_file(path_or_slug)
    try:
        with candidate.open(encoding="utf-8") as role_file:
            data = json.load(role_file)
    except FileNotFoundError as exc:
        raise ValueError(f"role file not found: {path_or_slug!r}") from exc

    return {
        item["skill"]: list(item.get("resources", []))
        for item in data.get("skills", [])
    }


def recommend(
    gap_report: GapReport,
    role_resources: dict[str, list[dict[str, Any]]],
    top_n: int | None = None,
) -> list[Recommendation]:
    """Return ranked recommendations for missing and partial skills only."""

    if top_n is not None and top_n < 0:
        raise ValueError("top_n must be non-negative or None")

    unresolved = [
        gap for gap in gap_report.skill_gaps
        if gap.status in {"missing", "partial"}
    ]
    if top_n is not None:
        unresolved = unresolved[:top_n]

    return [
        Recommendation(
            skill=gap.skill,
            weighted_gap=gap.weighted_gap,
            status=gap.status,
            resources=list(role_resources.get(gap.skill, [])),
            priority_rank=index,
        )
        for index, gap in enumerate(unresolved, start=1)
    ]
