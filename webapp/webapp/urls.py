"""URL configuration for the skill-gap analyzer."""

from django.urls import include, path

from webapp.core.views import home

urlpatterns = [
    path("", home, name="home"),
    path("api/", include("webapp.api.urls")),
]
