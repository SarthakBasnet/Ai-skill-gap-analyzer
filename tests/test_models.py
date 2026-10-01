import json
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db import transaction

from webapp.core.models import JobRole, JobSkillRequirement, Skill, UserSkill


ROOT = Path(__file__).parents[1] / "knowledge_base"


@pytest.fixture
def loaded_db(db):
    call_command("load_knowledge_base", verbosity=0)
    return db


def test_loader_creates_expected_roles_and_requirements(loaded_db):
    role_data = [json.loads(path.read_text(encoding="utf-8")) for path in sorted((ROOT / "roles").glob("*.json"))]
    assert JobRole.objects.count() == 5
    for data in role_data:
        role = JobRole.objects.get(slug=data["slug"])
        assert role.skill_requirements.count() == len(data["skills"])


def test_loader_is_idempotent(loaded_db):
    before = (Skill.objects.count(), JobRole.objects.count(), JobSkillRequirement.objects.count())
    call_command("load_knowledge_base", verbosity=0)
    assert before == (Skill.objects.count(), JobRole.objects.count(), JobSkillRequirement.objects.count())


def test_requirement_unique_together_and_validators(loaded_db):
    role = JobRole.objects.first()
    requirement = role.skill_requirements.first()
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            JobSkillRequirement.objects.create(
                job_role=role, skill=requirement.skill, required_level=3, importance=0.5
            )
    invalid_level = JobSkillRequirement(job_role=role, skill=Skill.objects.exclude(pk=requirement.skill_id).first(), required_level=6, importance=0.5)
    with pytest.raises(ValidationError):
        invalid_level.full_clean()
    invalid_importance = JobSkillRequirement(job_role=role, skill=Skill.objects.exclude(pk=requirement.skill_id).first(), required_level=3, importance=1.1)
    with pytest.raises(ValidationError):
        invalid_importance.full_clean()


def test_user_skill_creation(loaded_db):
    user = get_user_model().objects.create_user(username="learner")
    record = UserSkill.objects.create(skill=Skill.objects.get(name="Python"), level=3, user=user, session_key="session-1")
    assert record.user == user
    assert record.session_key == "session-1"
