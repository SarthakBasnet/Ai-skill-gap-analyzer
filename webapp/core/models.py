"""Django models for the skill-gap analyzer knowledge base."""

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Skill(models.Model):
    name = models.CharField(max_length=120, unique=True)
    category = models.CharField(max_length=80)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class JobRole(models.Model):
    title = models.CharField(max_length=160, unique=True)
    slug = models.SlugField(max_length=180, unique=True)
    description = models.TextField()
    skills = models.ManyToManyField(Skill, through="JobSkillRequirement", related_name="job_roles")

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class JobSkillRequirement(models.Model):
    job_role = models.ForeignKey(JobRole, on_delete=models.CASCADE, related_name="skill_requirements")
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="job_requirements")
    required_level = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    importance = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])

    class Meta:
        ordering = ["job_role", "-importance", "skill"]
        unique_together = [["job_role", "skill"]]

    def __str__(self):
        return f"{self.job_role}: {self.skill}"


class UserSkill(models.Model):
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="user_skills")
    level = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    user = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.CASCADE, related_name="skill_records")
    session_key = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "skill"]

    def __str__(self):
        return f"{self.skill} (level {self.level})"


class LearningResource(models.Model):
    RESOURCE_TYPES = [(value, value.title()) for value in ("course", "documentation", "project", "book", "video")]
    LEVELS = [(value, value.title()) for value in ("beginner", "intermediate", "advanced")]

    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="learning_resources")
    title = models.CharField(max_length=200)
    url = models.URLField()
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    level = models.CharField(max_length=20, choices=LEVELS)
    is_free = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["skill", "level", "title"]

    def __str__(self):
        return self.title
