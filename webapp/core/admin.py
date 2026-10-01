from django.contrib import admin

from .models import JobRole, JobSkillRequirement, LearningResource, Skill, UserSkill

admin.site.register([Skill, JobRole, JobSkillRequirement, UserSkill, LearningResource])
