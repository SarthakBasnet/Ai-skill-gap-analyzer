import pytest
from django.test import Client


pytestmark = pytest.mark.django_db


def test_home_renders_frontend_form():
    response = Client().get("/")

    assert response.status_code == 200
    assert "SkillBridge" in response.content.decode()
    assert "See exactly what's between you and your" in response.content.decode()
    assert 'id="analysis-form"' in response.content.decode()
    assert 'id="job-title"' in response.content.decode()
    assert 'src="/static/core/app.js"' in response.content.decode()
