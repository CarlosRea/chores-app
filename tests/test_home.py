import pytest
from django.conf import settings


def test_django_project_configured():
    """Verify that Django settings are loaded and chores app is installed."""
    assert settings.configured
    assert "chores" in settings.INSTALLED_APPS


@pytest.mark.django_db
def test_database_connection():
    """Verify that the SQLite database is accessible."""
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        row = cursor.fetchone()
        assert row == (1,)
