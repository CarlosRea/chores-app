from pathlib import Path
import pytest
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.template.loader import render_to_string
from django.test import Client, RequestFactory
from django.urls import reverse

from chores.models import Roommate


@pytest.mark.django_db
class TestBaseTemplateStructure:
    def test_base_template_html5_elements(self):
        """Base template contains standard HTML5 structure, viewport meta, and default title."""
        rendered = render_to_string("chores/base.html", {})
        assert "<!DOCTYPE html>" in rendered
        assert '<html lang="en">' in rendered
        assert "<head>" in rendered
        assert "</head>" in rendered
        assert "<body>" in rendered
        assert "</body>" in rendered
        assert '<meta name="viewport" content="width=device-width, initial-scale=1.0">' in rendered
        assert "<title>Shared Household Chores</title>" in rendered

    def test_base_template_responsive_styles(self):
        """Base template contains responsive CSS media query and key UI component styles."""
        rendered = render_to_string("chores/base.html", {})
        assert "@media (max-width: 640px)" in rendered
        assert ".navbar" in rendered
        assert ".btn-new-chore" in rendered
        assert ".active-profile-badge" in rendered
        assert ".alert" in rendered
        assert ".alert-success" in rendered
        assert ".alert-error" in rendered


@pytest.mark.django_db
class TestNavigationHeader:
    def test_navbar_brand_links_to_chore_list(self, client: Client):
        """Navbar brand link points to reverse('chore_list')."""
        response = client.get(reverse("chore_list"))
        assert response.status_code == 200
        content = response.content.decode()
        assert f'href="{reverse("chore_list")}"' in content
        assert "Household Chores" in content

    def test_navbar_new_chore_link(self, client: Client):
        """Navbar contains 'New Chore' link pointing to reverse('chore_create')."""
        response = client.get(reverse("chore_list"))
        assert response.status_code == 200
        content = response.content.decode()
        assert f'href="{reverse("chore_create")}"' in content
        assert "New Chore" in content

    def test_navbar_rendered_on_all_pages_extending_base(self, client: Client):
        """Navbar header is rendered on both chore_list and chore_create pages."""
        for url in [reverse("chore_list"), reverse("chore_create")]:
            resp = client.get(url)
            assert resp.status_code == 200
            content = resp.content.decode()
            assert '<header class="navbar">' in content
            assert f'href="{reverse("chore_list")}"' in content
            assert f'href="{reverse("chore_create")}"' in content


@pytest.mark.django_db
class TestActiveRoommateIndicator:
    def test_indicator_displays_active_roommate_name(self, client: Client):
        """When active_roommate is in session, badge displays the active roommate's name."""
        roommate = Roommate.objects.create(name="Dana")
        session = client.session
        session["active_roommate_id"] = roommate.id
        session.save()

        response = client.get(reverse("chore_list"))
        assert response.status_code == 200
        content = response.content.decode()
        assert "Dana" in content
        assert "Active: <strong>Dana</strong>" in content

    def test_indicator_displays_no_active_profile_when_unset(self, client: Client):
        """When active_roommate is None, badge displays 'No active profile'."""
        response = client.get(reverse("chore_list"))
        assert response.status_code == 200
        content = response.content.decode()
        assert "No active profile" in content


@pytest.mark.django_db
class TestProfileSwitcherDropdown:
    def test_switcher_renders_options_for_all_roommates(self, client: Client):
        """Switcher select options point to reverse('switch_user') for each roommate."""
        alice = Roommate.objects.create(name="Alice")
        bob = Roommate.objects.create(name="Bob")

        response = client.get(reverse("chore_list"))
        assert response.status_code == 200
        content = response.content.decode()

        assert reverse("switch_user", kwargs={"user_id": alice.id}) in content
        assert reverse("switch_user", kwargs={"user_id": bob.id}) in content
        assert "Alice" in content
        assert "Bob" in content

    def test_switcher_marks_active_roommate_selected(self, client: Client):
        """When active_roommate is set, corresponding entry in switcher is marked selected."""
        alice = Roommate.objects.create(name="Alice")
        bob = Roommate.objects.create(name="Bob")

        session = client.session
        session["active_roommate_id"] = bob.id
        session.save()

        response = client.get(reverse("chore_list"))
        assert response.status_code == 200
        content = response.content.decode()

        bob_url = reverse("switch_user", kwargs={"user_id": bob.id})
        alice_url = reverse("switch_user", kwargs={"user_id": alice.id})

        assert f'value="{bob_url}" selected' in content
        assert f'value="{alice_url}" selected' not in content

    def test_switcher_renders_cleanly_when_no_roommates_exist(self, client: Client):
        """When database has zero roommates, switcher dropdown renders without errors."""
        assert Roommate.objects.count() == 0
        response = client.get(reverse("chore_list"))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'class="profile-switcher-select"' in content
        assert "Switch profile..." in content


@pytest.mark.django_db
class TestFlashMessagesBlock:
    def test_no_flash_message_rendered_when_messages_empty(self, client: Client):
        """When no messages are present, message container and alert elements are absent."""
        response = client.get(reverse("chore_list"))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'class="messages-container"' not in content
        assert 'class="alert' not in content

    def test_flash_messages_rendered_with_tag_classes(self, rf: RequestFactory):
        """Messages render with their corresponding tag CSS classes."""
        request = rf.get("/")
        # Setup session and message storage
        request.session = {}
        messages = FallbackStorage(request)
        messages.add(20, "Info alert message", "info")
        messages.add(25, "Success alert message", "success")
        messages.add(30, "Warning alert message", "warning")
        messages.add(40, "Error alert message", "error")
        request._messages = messages

        rendered = render_to_string("chores/base.html", {"messages": messages}, request=request)

        assert 'class="messages-container"' in rendered
        assert "alert alert-info info" in rendered
        assert "alert alert-success success" in rendered
        assert "alert alert-warning warning" in rendered
        assert "alert alert-error error" in rendered
        assert "Info alert message" in rendered
        assert "Success alert message" in rendered
        assert "Warning alert message" in rendered
        assert "Error alert message" in rendered


@pytest.mark.django_db
class TestChildTemplateInheritance:
    def test_chore_list_template_inheritance(self, client: Client):
        """chore_list.html extends chores/base.html, overrides title, and renders content in block."""
        response = client.get(reverse("chore_list"))
        assert response.status_code == 200
        template_names = [t.name for t in response.templates if t.name]
        assert "chores/chore_list.html" in template_names
        assert "chores/base.html" in template_names

        content = response.content.decode()
        assert "<title>Chore Board - Household Chores</title>" in content
        assert '<header class="navbar">' in content

    def test_chore_form_template_inheritance(self, client: Client):
        """chore_form.html extends chores/base.html, overrides title, and renders content in block."""
        response = client.get(reverse("chore_create"))
        assert response.status_code == 200
        template_names = [t.name for t in response.templates if t.name]
        assert "chores/chore_form.html" in template_names
        assert "chores/base.html" in template_names

        content = response.content.decode()
        assert "<title>New Chore - Household Chores</title>" in content
        assert '<header class="navbar">' in content

    def test_child_templates_do_not_duplicate_html_head_body(self):
        """Raw child template files do not contain <!DOCTYPE html>, <head>, or <body>."""
        template_dir = Path(__file__).resolve().parent.parent / "chores" / "templates" / "chores"

        for template_name in ["chore_list.html", "chore_form.html"]:
            file_path = template_dir / template_name
            content = file_path.read_text()

            assert '{% extends "chores/base.html" %}' in content
            assert "{% block content %}" in content
            assert "<!DOCTYPE" not in content
            assert "<html" not in content
            assert "<head" not in content
            assert "<body" not in content
