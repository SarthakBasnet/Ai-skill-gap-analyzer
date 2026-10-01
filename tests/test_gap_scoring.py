import pytest

from analyzer.gap_scoring import SkillRequirement, calculate_gap, load_role


def test_perfect_match_has_no_gap():
    requirements = [SkillRequirement("SQL", 4, 1.0)]

    report = calculate_gap(requirements, {"sql": 4})

    assert report.overall_gap_score == 0.0
    assert report.overall_match_percent == 100.0
    assert report.met[0].status == "met"


def test_no_skills_are_all_missing():
    requirements = [SkillRequirement("SQL", 4, 1.0), SkillRequirement("Python", 2, 0.5)]

    report = calculate_gap(requirements, {})

    # weighted gaps = (4 * 1.0) + (2 * 0.5) = 5; denominator = 5.
    assert report.overall_gap_score == 1.0
    assert report.overall_match_percent == 0.0
    assert len(report.missing) == 2
    assert not report.partial and not report.met


def test_partial_match_uses_weighted_gap_formula():
    requirements = [SkillRequirement("SQL", 4, 1.0), SkillRequirement("Python", 4, 0.5)]

    report = calculate_gap(requirements, {"SQL": 2, "Python": 3})

    # weighted gaps = (4 - 2) * 1.0 + (4 - 3) * 0.5 = 2.5.
    # denominator = 4 * 1.0 + 4 * 0.5 = 6; score = 2.5 / 6.
    assert report.overall_gap_score == pytest.approx(2.5 / 6)
    assert report.overall_match_percent == 58.3
    assert all(gap.status == "partial" for gap in report.partial)


def test_overqualified_user_has_no_negative_gap():
    report = calculate_gap([SkillRequirement("SQL", 3, 1.0)], {"SQL": 5})

    gap = report.skill_gaps[0]
    assert gap.raw_gap == 0
    assert gap.weighted_gap == 0.0
    assert gap.status == "met"


def test_skill_gaps_are_ordered_by_gap_importance_then_name():
    requirements = [
        SkillRequirement("Zulu", 4, 0.5),
        SkillRequirement("Alpha", 4, 0.5),
        SkillRequirement("Beta", 3, 1.0),
    ]

    report = calculate_gap(requirements, {"Zulu": 2, "Alpha": 2, "Beta": 1})

    # Zulu/Alpha weighted gaps = 2 * .5 = 1; Beta weighted gap = 2 * 1 = 2.
    assert [gap.skill for gap in report.skill_gaps] == ["Beta", "Alpha", "Zulu"]


def test_matching_trims_and_ignores_case_and_unknown_skills():
    report = calculate_gap([SkillRequirement("Data Science", 3, 1.0)], {
        "  DATA SCIENCE ": 3,
        "Unrelated Skill": 5,
    })

    assert report.skill_gaps[0].skill == "Data Science"
    assert report.skill_gaps[0].user_level == 3
    assert report.overall_gap_score == 0.0


def test_validation_errors_are_clear():
    requirement = [SkillRequirement("SQL", 3, 0.5)]
    with pytest.raises(ValueError, match="user level"):
        calculate_gap(requirement, {"SQL": 6})
    with pytest.raises(ValueError, match="importance"):
        calculate_gap([SkillRequirement("SQL", 3, 1.1)], {})
    with pytest.raises(ValueError, match="required_level"):
        calculate_gap([SkillRequirement("SQL", 0, 0.5)], {})
    with pytest.raises(ValueError, match="must not be empty"):
        calculate_gap([], {})


def test_load_role_reads_data_analyst_fixture():
    title, requirements = load_role("data-analyst")

    assert title == "Data Analyst"
    assert len(requirements) >= 15
    assert all(1 <= item.required_level <= 5 and 0.0 <= item.importance <= 1.0
               for item in requirements)


def test_real_role_report_is_internally_consistent():
    title, requirements = load_role("data-analyst")
    report = calculate_gap(requirements, {"SQL": 4, "python": 2, "Git": 1}, title)

    assert len(report.met) + len(report.partial) + len(report.missing) == len(requirements)
    assert 0.0 <= report.overall_gap_score <= 1.0
    assert report.role_title == title
