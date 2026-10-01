"""Load the versioned JSON knowledge base into Django."""

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from webapp.core.models import JobRole, JobSkillRequirement, LearningResource, Skill


class Command(BaseCommand):
    help = "Load skills, job roles, requirements, and learning resources from knowledge_base/"

    def handle(self, *args, **options):
        root = Path(settings.BASE_DIR) / "knowledge_base"
        skills_path = root / "skills.json"
        try:
            skills_data = json.loads(skills_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Could not read {skills_path}: {exc}") from exc

        skill_map = {}
        for item in skills_data["skills"]:
            skill, _ = Skill.objects.update_or_create(
                name=item["name"],
                defaults={"category": item["category"], "description": item.get("description", "")},
            )
            skill_map[skill.name] = skill

        role_files = sorted((root / "roles").glob("*.json"))
        if not role_files:
            raise CommandError(f"No role JSON files found under {root / 'roles'}")

        for role_path in role_files:
            try:
                role_data = json.loads(role_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise CommandError(f"Could not read {role_path}: {exc}") from exc
            role, _ = JobRole.objects.update_or_create(
                slug=role_data["slug"],
                defaults={"title": role_data["title"], "description": role_data["description"]},
            )
            for item in role_data["skills"]:
                skill_name = item["skill"]
                if skill_name not in skill_map:
                    raise CommandError(
                        f"Role '{role_data['slug']}' references unknown skill '{skill_name}'"
                    )
                skill = skill_map[skill_name]
                JobSkillRequirement.objects.update_or_create(
                    job_role=role,
                    skill=skill,
                    defaults={
                        "required_level": item["required_level"],
                        "importance": item["importance"],
                    },
                )
                for resource in item.get("resources", []):
                    LearningResource.objects.update_or_create(
                        skill=skill,
                        title=resource["title"],
                        url=resource["url"],
                        defaults={
                            "resource_type": resource["resource_type"],
                            "level": resource["level"],
                            "is_free": resource["is_free"],
                            "notes": resource.get("notes", ""),
                        },
                    )

        self.stdout.write(self.style.SUCCESS(
            "Loaded knowledge base: "
            f"{Skill.objects.count()} skills, {JobRole.objects.count()} roles, "
            f"{JobSkillRequirement.objects.count()} requirements, "
            f"{LearningResource.objects.count()} resources."
        ))
