"""Template views for the minimal browser frontend."""

from django.shortcuts import render

from webapp.api.serializers import available_roles


def home(request):
    """Render the analyzer form from the versioned role files."""
    return render(request, "core/home.html", {"roles": available_roles()})
