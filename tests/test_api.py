import pytest
from rest_framework.test import APIClient

from webapp.api.matcher_singleton import get_matcher


pytestmark = pytest.mark.slow


@pytest.fixture
def client():
    return APIClient()


def test_skill_gap_returns_consistent_analysis(client):
    response = client.post("/api/skill-gap/", {"job_title": "data-analyst", "skills": {"Python": 3, "SQL": 4}}, format="json")
    assert response.status_code == 200
    data = response.json()
    assert {"role_title", "overall_gap_score", "overall_match_percent", "skill_gaps", "recommendations", "unmatched_inputs"} <= data.keys()
    assert len(data["skill_gaps"]) == 15
    statuses = [item["status"] for item in data["skill_gaps"]]
    assert sum(statuses.count(status) for status in ("missing", "partial", "met")) == 15
    assert data["overall_match_percent"] == round((1 - data["overall_gap_score"]) * 100, 1)


def test_skill_gap_rejects_unknown_role(client):
    response = client.post("/api/skill-gap/", {"job_title": "unknown", "skills": {"Python": 3}}, format="json")
    assert response.status_code == 400
    assert "job_title" in response.json()


def test_skill_gap_rejects_missing_skills(client):
    response = client.post("/api/skill-gap/", {"job_title": "data-analyst"}, format="json")
    assert response.status_code == 400
    assert "skills" in response.json()


def test_skill_gap_rejects_out_of_range_level(client):
    response = client.post("/api/skill-gap/", {"job_title": "data-analyst", "skills": {"Python": 7}}, format="json")
    assert response.status_code == 400
    assert "skills" in response.json()


def test_skill_gap_returns_unmatched_inputs(client):
    response = client.post("/api/skill-gap/", {"job_title": "data-analyst", "skills": {"I like pizza": 5}}, format="json")
    assert response.status_code == 200
    assert response.json()["unmatched_inputs"] == ["I like pizza"]


def test_roles_lists_json_roles(client):
    response = client.get("/api/roles/")
    assert response.status_code == 200
    roles = response.json()
    assert len(roles) == 5
    assert all({"title", "slug", "description"} <= role.keys() for role in roles)


def test_matcher_is_shared():
    assert get_matcher() is get_matcher()
