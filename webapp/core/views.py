"""Template views for the browser frontend and account pages."""

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render

from webapp.api.serializers import available_roles


def home(request):
    """Render the public landing page."""
    return render(request, "core/landing.html", {"roles": available_roles()})


@login_required
def analyzer(request):
    """Render the analyzer for signed-in users."""
    return render(request, "core/home.html", {"roles": available_roles()})


def signup(request):
    """Create an account and start an authenticated session."""
    if request.user.is_authenticated:
        return redirect("analyzer")

    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("analyzer")

    return render(request, "core/signup.html", {"form": form})
