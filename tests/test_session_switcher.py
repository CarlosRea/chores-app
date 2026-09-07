import pytest
from django.template import Context, RequestContext, Template
from django.test import RequestFactory
from django.urls import resolve, reverse

from chores.context_processors import active_roommate
from chores.models import Roommate
from chores.views import switch_user


class TestSwitchUserURL:
    def test_reverse_switch_user(self):
        """reverse('switch_user', kwargs={'user_id': 1}) resolves to '/switch-user/1/'."""
        url = reverse("switch_user", kwargs={"user_id": 1})
        assert url == "/switch-user/1/"

    def test_resolve_switch_user(self):
        """'/switch-user/1/' resolves to switch_user view."""
        match = resolve("/switch-user/1/")
        assert match.func == switch_user
        assert match.url_name == "switch_user"
        assert match.kwargs == {"user_id": 1}


@pytest.mark.django_db
class TestSwitchUserView:
    def test_switch_user_existing_sets_session_and_redirects(self, client):
        """GET request to switch_user with an existing user_id sets active_roommate_id and returns 302."""
        roommate = Roommate.objects.create(name="Alice")
        url = reverse("switch_user", kwargs={"user_id": roommate.id})

        response = client.get(url)

        assert response.status_code == 302
        assert response.url == "/"
        assert client.session.get("active_roommate_id") == roommate.id

    def test_switch_user_redirects_to_safe_relative_referer(self, client):
        """GET request with safe local relative HTTP_REFERER redirects back to that referer URL."""
        roommate = Roommate.objects.create(name="Bob")
        url = reverse("switch_user", kwargs={"user_id": roommate.id})

        response = client.get(url, HTTP_REFERER="/chores/")

        assert response.status_code == 302
        assert response.url == "/chores/"
        assert client.session.get("active_roommate_id") == roommate.id

    def test_switch_user_redirects_to_safe_absolute_referer(self, client):
        """GET request with safe local absolute HTTP_REFERER redirects back to that referer URL."""
        roommate = Roommate.objects.create(name="Bob")
        url = reverse("switch_user", kwargs={"user_id": roommate.id})

        response = client.get(url, HTTP_REFERER="http://testserver/chores/?status=pending")

        assert response.status_code == 302
        assert response.url == "http://testserver/chores/?status=pending"
        assert client.session.get("active_roommate_id") == roommate.id

    def test_switch_user_no_referer_redirects_to_root(self, client):
        """GET request without HTTP_REFERER header redirects to '/'."""
        roommate = Roommate.objects.create(name="Charlie")
        url = reverse("switch_user", kwargs={"user_id": roommate.id})

        response = client.get(url)

        assert response.status_code == 302
        assert response.url == "/"

    def test_switch_user_untrusted_external_referer_redirects_to_root(self, client):
        """GET request with untrusted or external HTTP_REFERER redirects to '/'."""
        roommate = Roommate.objects.create(name="Dana")
        url = reverse("switch_user", kwargs={"user_id": roommate.id})

        for evil_url in [
            "https://evil.com/",
            "https://evil.com/steal-creds",
            "//evil.com/test",
            "javascript:alert(1)",
        ]:
            response = client.get(url, HTTP_REFERER=evil_url)
            assert response.status_code == 302
            assert response.url == "/"

    def test_switch_user_nonexistent_user_returns_404(self, client):
        """GET request with a non-existent user_id returns HTTP 404 Not Found."""
        url = reverse("switch_user", kwargs={"user_id": 99999})
        response = client.get(url)
        assert response.status_code == 404

    def test_switch_user_nonexistent_user_does_not_modify_session(self, client):
        """GET request with a non-existent user_id does not set or modify active_roommate_id in session."""
        # Test 1: empty session remains unset
        url_missing = reverse("switch_user", kwargs={"user_id": 99999})
        response = client.get(url_missing)
        assert response.status_code == 404
        assert "active_roommate_id" not in client.session

        # Test 2: existing session value is preserved
        existing_roommate = Roommate.objects.create(name="Eve")
        session = client.session
        session["active_roommate_id"] = existing_roommate.id
        session.save()

        response = client.get(url_missing)
        assert response.status_code == 404
        assert client.session.get("active_roommate_id") == existing_roommate.id


@pytest.mark.django_db
class TestActiveRoommateContextProcessor:
    def test_context_processor_structure(self, rf: RequestFactory):
        """Context processor returns dictionary with 'active_roommate' and 'all_roommates' keys."""
        request = rf.get("/")
        request.session = {}

        result = active_roommate(request)

        assert isinstance(result, dict)
        assert "active_roommate" in result
        assert "all_roommates" in result

    def test_context_processor_no_session_attribute(self, rf: RequestFactory):
        """When request object lacks session attribute, active_roommate is None without error."""
        request = rf.get("/")
        # request without session attribute
        result = active_roommate(request)
        assert result["active_roommate"] is None

    def test_context_processor_session_unset(self, rf: RequestFactory):
        """When request.session does not contain 'active_roommate_id', active_roommate is None."""
        request = rf.get("/")
        request.session = {}

        result = active_roommate(request)
        assert result["active_roommate"] is None

    def test_context_processor_session_valid_user(self, rf: RequestFactory):
        """When request.session['active_roommate_id'] matches existing Roommate, it is returned."""
        roommate = Roommate.objects.create(name="Frank")
        request = rf.get("/")
        request.session = {"active_roommate_id": roommate.id}

        result = active_roommate(request)
        assert result["active_roommate"] == roommate

    def test_context_processor_session_nonexistent_user(self, rf: RequestFactory):
        """When active_roommate_id does not exist in DB, active_roommate is None without error."""
        request = rf.get("/")
        request.session = {"active_roommate_id": 99999}

        result = active_roommate(request)
        assert result["active_roommate"] is None

    def test_context_processor_session_invalid_value_type(self, rf: RequestFactory):
        """When active_roommate_id is not a valid integer, active_roommate is None without error."""
        request = rf.get("/")
        request.session = {"active_roommate_id": "not-an-int"}

        result = active_roommate(request)
        assert result["active_roommate"] is None

    def test_context_processor_all_roommates_ordered_by_name(self, rf: RequestFactory):
        """all_roommates contains a queryset of all Roommate records ordered by name."""
        Roommate.objects.create(name="Zara")
        Roommate.objects.create(name="Adam")
        Roommate.objects.create(name="Maya")

        request = rf.get("/")
        request.session = {}

        result = active_roommate(request)
        names = list(result["all_roommates"].values_list("name", flat=True))
        assert names == ["Adam", "Maya", "Zara"]

    def test_context_processor_integrated_in_template_rendering(self, rf: RequestFactory):
        """Context processor is automatically invoked and available during template rendering."""
        roommate = Roommate.objects.create(name="Alice")
        Roommate.objects.create(name="Bob")

        request = rf.get("/")
        request.session = {"active_roommate_id": roommate.id}

        template = Template(
            "Active: {{ active_roommate.name }}; All: {% for r in all_roommates %}{{ r.name }} {% endfor %}"
        )
        rendered = template.render(RequestContext(request))

        assert "Active: Alice;" in rendered
        assert "All: Alice Bob " in rendered
