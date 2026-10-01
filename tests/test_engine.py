import pytest

from analyzer.engine import AnalysisResult, analyze
from analyzer.matching import SkillMatcher


@pytest.fixture(scope="module")
def matcher():
    return SkillMatcher()


@pytest.mark.slow
def test_analyze_builds_consistent_result_from_free_text(matcher):
    result = analyze(
        "data-analyst",
        {"SQL": 4, "wrote SQL queries": 2, "Python": 2, "built dashboards": 1},
        matcher=matcher,
        top_n=3,
    )

    assert isinstance(result, AnalysisResult)
    assert result.role_title == "Data Analyst"
    assert len(result.gap_report.skill_gaps) == 15
    assert len(result.gap_report.missing) + len(result.gap_report.partial) + len(result.gap_report.met) == 15
    assert result.gap_report.skill_gaps[0].skill == "Statistics"
    assert all(item.status in {"missing", "partial"} for item in result.recommendations)
    assert len(result.recommendations) == 3


@pytest.mark.slow
def test_analyze_reports_unmatched_input_without_false_skill(matcher):
    result = analyze("data-analyst", {"I like pizza": 5}, matcher=matcher)

    assert result.unmatched_inputs == ["I like pizza"]
    assert all(gap.user_level == 0 for gap in result.gap_report.skill_gaps)


@pytest.mark.slow
def test_analyze_uses_maximum_level_for_duplicate_matches(matcher):
    result = analyze(
        "data-analyst",
        {"SQL": 1, "wrote SQL queries": 4},
        matcher=matcher,
    )

    sql_gap = next(gap for gap in result.gap_report.skill_gaps if gap.skill == "SQL")
    assert sql_gap.user_level == 4
    assert sql_gap.status == "met"


def test_analyze_rejects_unknown_role():
    with pytest.raises(ValueError, match="unknown role"):
        analyze("not-a-real-role", {}, matcher=object())
