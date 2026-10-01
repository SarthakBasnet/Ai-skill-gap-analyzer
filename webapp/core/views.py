"""Template views for the minimal browser frontend."""

from django.shortcuts import render

from .models import JobRole


def home(request):
    """Render the analyzer form with the available roles."""
    return render(request, "core/home.html", {"roles": JobRole.objects.all()})
