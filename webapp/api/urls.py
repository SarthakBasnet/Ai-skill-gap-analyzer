"""API URL configuration."""

from django.urls import path

from .views import RolesView, SkillGapView

urlpatterns = []

urlpatterns = [
    path("skill-gap/", SkillGapView.as_view(), name="skill-gap"),
    path("roles/", RolesView.as_view(), name="roles"),
]
