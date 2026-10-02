"""URL configuration for the skill-gap analyzer."""

from django.contrib.auth import views as auth_views
from django.urls import include, path

from webapp.core.views import analyzer, home, signup

urlpatterns = [
    path("", home, name="home"),
    path("analyzer/", analyzer, name="analyzer"),
    path("accounts/signup/", signup, name="signup"),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(
            template_name="core/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path("api/", include("webapp.api.urls")),
]
