"""WSGI configuration for the skill-gap analyzer."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.webapp.settings")
application = get_wsgi_application()
