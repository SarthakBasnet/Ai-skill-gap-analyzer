from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "webapp.api"

    def ready(self):
        # Django can call ready more than once during development autoreload;
        # initialize_matcher guards the module-level singleton in that case.
        from .matcher_singleton import initialize_matcher

        initialize_matcher()
