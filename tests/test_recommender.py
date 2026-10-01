import pytest

from analyzer.gap_scoring import SkillRequirement, calculate_gap
from analyzer.recommender import load_role_resources, recommend


def test_load_role_resources_reads_real_role():
    resources = load_role_resources("data-analyst")

    assert len(resources) >= 15
    assert resources["SQL"][0]["title"] == "SQLBolt"
    assert {"title", "url", "resource_type", "level", "is_free", "notes"} <= resources["SQL"][0].keys()


def test_recommend_excludes_met_and_preserves_gap_order_and_ranks():
    report = calculate_gap(
        [
            SkillRequirement("SQL", 4, 1.0),
            SkillRequirement("Python", 4, 0.5),
            SkillRequirement("Git", 2, 0.5),
        ],
        {"SQL": 4, "Python": 1, "Git": 0},
    )

    recommendations = recommend(report, {"Python": [{"title": "Python resource"}]})

    assert [item.skill for item in recommendations] == ["Python", "Git"]
    assert [item.priority_rank for item in recommendations] == [1, 2]
    assert all(item.status in {"missing", "partial"} for item in recommendations)


def test_recommend_keeps_skill_when_resources_are_missing():
    report = calculate_gap([SkillRequirement("SQL", 4, 1.0)], {})

    recommendations = recommend(report, {})

    assert len(recommendations) == 1
    assert recommendations[0].skill == "SQL"
    assert recommendations[0].resources == []


def test_recommend_top_n_limits_results():
    report = calculate_gap(
        [SkillRequirement("SQL", 4, 1.0), SkillRequirement("Python", 4, 0.5)],
        {},
    )

    recommendations = recommend(report, {}, top_n=1)

    assert len(recommendations) == 1
    assert recommendations[0].priority_rank == 1


def test_recommend_rejects_negative_top_n():
    report = calculate_gap([SkillRequirement("SQL", 4, 1.0)], {})

    with pytest.raises(ValueError, match="top_n"):
        recommend(report, {}, top_n=-1)
