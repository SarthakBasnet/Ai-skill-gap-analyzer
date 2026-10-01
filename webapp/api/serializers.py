"""DRF serializers for the skill-gap API."""

from pathlib import Path
import json

from rest_framework import serializers


ROLE_DIRECTORY = Path(__file__).resolve().parents[2] / "knowledge_base" / "roles"


def available_roles() -> list[dict]:
    """Return the versioned role metadata used by the framework-independent code."""
    roles = []
    for path in sorted(ROLE_DIRECTORY.glob("*.json")):
        with path.open(encoding="utf-8") as role_file:
            data = json.load(role_file)
        roles.append({
            "title": data["title"],
            "slug": data["slug"],
            "description": data["description"],
        })
    return roles


class SkillGapRequestSerializer(serializers.Serializer):
    job_title = serializers.CharField(required=True, allow_blank=False)
    skills = serializers.DictField(
        child=serializers.IntegerField(min_value=0, max_value=5),
        required=True,
        allow_empty=False,
    )
    top_n = serializers.IntegerField(required=False, allow_null=True, min_value=1, default=None)

    def validate_job_title(self, value):
        value = value.strip()
        for role in available_roles():
            if value.casefold() in {role["slug"].casefold(), role["title"].casefold()}:
                # analyze/load_role resolves slugs, so normalize titles to slugs here.
                return role["slug"]
        raise serializers.ValidationError(f"unknown role: {value!r}")


class SkillGapResponseSerializer(serializers.Serializer):
    """Documented response shape; views pass it a normalized response dictionary."""

    role_title = serializers.CharField()
    overall_gap_score = serializers.FloatField()
    overall_match_percent = serializers.FloatField()
    skill_gaps = serializers.ListField(child=serializers.DictField())
    recommendations = serializers.ListField(child=serializers.DictField())
    unmatched_inputs = serializers.ListField(child=serializers.CharField())
