import json
from pathlib import Path


ROOT = Path(__file__).parents[1] / "knowledge_base"
SKILLS = json.loads((ROOT / "skills.json").read_text(encoding="utf-8"))["skills"]
ROLES = [json.loads(path.read_text(encoding="utf-8")) for path in sorted((ROOT / "roles").glob("*.json"))]
SKILL_NAMES = {item["name"] for item in SKILLS}
RESOURCE_TYPES = {"course", "documentation", "project", "book", "video"}
LEVELS = {"beginner", "intermediate", "advanced"}


def test_skills_have_required_fields_and_no_duplicates():
    assert 60 <= len(SKILLS) <= 80
    assert len(SKILL_NAMES) == len(SKILLS)
    for skill in SKILLS:
        assert {"name", "category", "description"} <= skill.keys()


def test_roles_have_valid_requirements_and_resources():
    assert len(ROLES) == 5
    for role in ROLES:
        assert {"title", "slug", "description", "skills"} <= role.keys()
        assert 15 <= len(role["skills"]) <= 25
        names = [item["skill"] for item in role["skills"]]
        assert len(names) == len(set(names))
        assert set(names) <= SKILL_NAMES
        for requirement in role["skills"]:
            assert isinstance(requirement["required_level"], int)
            assert 1 <= requirement["required_level"] <= 5
            assert isinstance(requirement["importance"], float)
            assert 0.0 <= requirement["importance"] <= 1.0
            assert requirement["resources"]
            for resource in requirement["resources"]:
                assert resource["resource_type"] in RESOURCE_TYPES
                assert resource["level"] in LEVELS
                assert resource["url"].startswith("https://")
