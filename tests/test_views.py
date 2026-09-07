import datetime
import pytest
from django.test import Client, RequestFactory
from django.urls import resolve, reverse
from django.utils import timezone

from chores.forms import ChoreForm
from chores.models import Chore, Roommate
from chores.views import chore_create, chore_delete, chore_list, chore_toggle


class TestChoreListRouting:
    def test_reverse_chore_list(self):
        """reverse('chore_list') resolves to '/'."""
        assert reverse("chore_list") == "/"

    def test_resolve_chore_list(self):
        """Path '/' resolves to chore_list view function."""
        match = resolve("/")
        assert match.func == chore_list
        assert match.url_name == "chore_list"


@pytest.mark.django_db
class TestChoreListViewRendering:
    def test_chore_list_status_200(self, client: Client):
        """GET request to '/' returns HTTP status code 200 OK."""
        response = client.get(reverse("chore_list"))
        assert response.status_code == 200

    def test_chore_list_template_used(self, client: Client):
        """GET request to '/' renders chores/chore_list.html template."""
        response = client.get(reverse("chore_list"))
        template_names = [t.name for t in response.templates if t.name]
        assert "chores/chore_list.html" in template_names

    def test_chore_list_context_keys(self, client: Client):
        """GET request context contains required keys: chores, tab, active_tab, today, needs_profile."""
        response = client.get(reverse("chore_list"))
        assert "chores" in response.context
        assert "tab" in response.context
        assert "active_tab" in response.context
        assert "today" in response.context
        assert "needs_profile" in response.context
        assert response.context["today"] == timezone.localdate()
        assert response.context["tab"] == "all"
        assert response.context["active_tab"] == "all"
        assert response.context["needs_profile"] is False


@pytest.mark.django_db
class TestChoreListTabNavigation:
    def test_filter_tab_navigation_links_rendered(self, client: Client):
        """Navigation bar contains links for all tabs with expected query parameters."""
        response = client.get(reverse("chore_list"))
        content = response.content.decode()

        assert 'href="?tab=all"' in content
        assert 'href="?tab=mine"' in content
        assert 'href="?tab=pending"' in content
        assert 'href="?tab=completed"' in content

    def test_active_tab_highlighting_default(self, client: Client):
        """When visiting '/' without tab query param, 'All' tab is visually active."""
        response = client.get(reverse("chore_list"))
        content = response.content.decode()
        assert response.context["active_tab"] == "all"
        # Check that 'active' class is on the tab-all element
        assert 'class="tab-link active" id="tab-all"' in content or 'id="tab-all" class="tab-link active"' in content or 'tab-link active' in content

    def test_active_tab_highlighting_all(self, client: Client):
        """When visiting '?tab=all', 'All' tab is active."""
        response = client.get(reverse("chore_list"), {"tab": "all"})
        assert response.context["active_tab"] == "all"
        content = response.content.decode()
        assert 'id="tab-all"' in content
        assert 'tab-link active' in content

    def test_active_tab_highlighting_mine(self, client: Client):
        """When visiting '?tab=mine', 'Assigned to Me' tab is active."""
        response = client.get(reverse("chore_list"), {"tab": "mine"})
        assert response.context["active_tab"] == "mine"
        content = response.content.decode()
        assert 'id="tab-mine"' in content
        assert 'tab-link active' in content

    def test_active_tab_highlighting_pending(self, client: Client):
        """When visiting '?tab=pending', 'Pending' tab is active."""
        response = client.get(reverse("chore_list"), {"tab": "pending"})
        assert response.context["active_tab"] == "pending"
        content = response.content.decode()
        assert 'id="tab-pending"' in content
        assert 'tab-link active' in content

    def test_active_tab_highlighting_completed(self, client: Client):
        """When visiting '?tab=completed', 'Completed' tab is active."""
        response = client.get(reverse("chore_list"), {"tab": "completed"})
        assert response.context["active_tab"] == "completed"
        content = response.content.decode()
        assert 'id="tab-completed"' in content
        assert 'tab-link active' in content

    def test_invalid_tab_query_param_fallback_to_all(self, client: Client):
        """Unrecognized tab query param safely falls back to 'all'."""
        for invalid_tab in ["invalid", "unknown", "123", "", "none"]:
            response = client.get(reverse("chore_list"), {"tab": invalid_tab})
            assert response.status_code == 200
            assert response.context["active_tab"] == "all"
            assert response.context["tab"] == "all"


@pytest.mark.django_db
class TestChoreListFiltering:
    @pytest.fixture(autouse=True)
    def setup_chores(self):
        self.alice = Roommate.objects.create(name="Alice")
        self.bob = Roommate.objects.create(name="Bob")

        today = timezone.localdate()
        yesterday = today - datetime.timedelta(days=1)
        tomorrow = today + datetime.timedelta(days=1)

        # Chore 1: Alice assigned, pending, due yesterday
        self.chore_alice_pending = Chore.objects.create(
            title="Alice Pending Chore",
            assigned_to=self.alice,
            assigned_by=self.bob,
            due_date=yesterday,
            is_completed=False,
        )
        # Chore 2: Alice assigned, completed, due yesterday
        self.chore_alice_completed = Chore.objects.create(
            title="Alice Completed Chore",
            assigned_to=self.alice,
            assigned_by=self.bob,
            due_date=yesterday,
            is_completed=True,
        )
        # Chore 3: Bob assigned, pending, due tomorrow
        self.chore_bob_pending = Chore.objects.create(
            title="Bob Pending Chore",
            assigned_to=self.bob,
            assigned_by=self.alice,
            due_date=tomorrow,
            is_completed=False,
        )
        # Chore 4: Bob assigned, completed, due tomorrow
        self.chore_bob_completed = Chore.objects.create(
            title="Bob Completed Chore",
            assigned_to=self.bob,
            assigned_by=self.alice,
            due_date=tomorrow,
            is_completed=True,
        )

    def test_filter_all(self, client: Client):
        """When ?tab=all or default, all chores are returned."""
        response = client.get(reverse("chore_list"), {"tab": "all"})
        chores = list(response.context["chores"])
        assert len(chores) == 4
        assert self.chore_alice_pending in chores
        assert self.chore_alice_completed in chores
        assert self.chore_bob_pending in chores
        assert self.chore_bob_completed in chores

    def test_filter_pending(self, client: Client):
        """When ?tab=pending, only incomplete chores are returned."""
        response = client.get(reverse("chore_list"), {"tab": "pending"})
        chores = list(response.context["chores"])
        assert len(chores) == 2
        assert self.chore_alice_pending in chores
        assert self.chore_bob_pending in chores
        assert self.chore_alice_completed not in chores
        assert self.chore_bob_completed not in chores

    def test_filter_completed(self, client: Client):
        """When ?tab=completed, only completed chores are returned."""
        response = client.get(reverse("chore_list"), {"tab": "completed"})
        chores = list(response.context["chores"])
        assert len(chores) == 2
        assert self.chore_alice_completed in chores
        assert self.chore_bob_completed in chores
        assert self.chore_alice_pending not in chores
        assert self.chore_bob_pending not in chores

    def test_filter_mine_with_active_roommate_alice(self, client: Client):
        """When ?tab=mine and active_roommate_id is Alice, only Alice's chores are returned."""
        session = client.session
        session["active_roommate_id"] = self.alice.id
        session.save()

        response = client.get(reverse("chore_list"), {"tab": "mine"})
        chores = list(response.context["chores"])
        assert len(chores) == 2
        assert self.chore_alice_pending in chores
        assert self.chore_alice_completed in chores
        assert self.chore_bob_pending not in chores
        assert self.chore_bob_completed not in chores
        assert response.context["needs_profile"] is False

    def test_filter_mine_with_active_roommate_bob(self, client: Client):
        """When ?tab=mine and active_roommate_id is Bob, only Bob's chores are returned."""
        session = client.session
        session["active_roommate_id"] = self.bob.id
        session.save()

        response = client.get(reverse("chore_list"), {"tab": "mine"})
        chores = list(response.context["chores"])
        assert len(chores) == 2
        assert self.chore_bob_pending in chores
        assert self.chore_bob_completed in chores
        assert self.chore_alice_pending not in chores
        assert self.chore_alice_completed not in chores
        assert response.context["needs_profile"] is False

    def test_filter_mine_without_active_roommate(self, client: Client):
        """When ?tab=mine and no active roommate in session, empty list and prompt are returned."""
        response = client.get(reverse("chore_list"), {"tab": "mine"})
        chores = list(response.context["chores"])
        assert len(chores) == 0
        assert response.context["needs_profile"] is True

        content = response.content.decode()
        assert "Please select an active profile" in content
        assert "No chores found." in content

    def test_filter_mine_with_nonexistent_active_roommate_id(self, client: Client):
        """When ?tab=mine and session has non-existent roommate id, treats as no active profile."""
        session = client.session
        session["active_roommate_id"] = 99999
        session.save()

        response = client.get(reverse("chore_list"), {"tab": "mine"})
        chores = list(response.context["chores"])
        assert len(chores) == 0
        assert response.context["needs_profile"] is True

        content = response.content.decode()
        assert "Please select an active profile" in content


@pytest.mark.django_db
class TestChoreListOrdering:
    def test_chores_ordered_by_due_date_asc_then_created_at_asc(self, client: Client):
        """Chores are ordered by due_date ascending, then created_at ascending."""
        alice = Roommate.objects.create(name="Alice")
        bob = Roommate.objects.create(name="Bob")

        day1 = datetime.date(2026, 1, 10)
        day2 = datetime.date(2026, 1, 15)
        day3 = datetime.date(2026, 1, 20)

        # Create chore for day 2 first
        chore_day2_first = Chore.objects.create(
            title="Chore Day 2 First",
            assigned_to=alice,
            assigned_by=bob,
            due_date=day2,
        )
        # Create chore for day 1
        chore_day1 = Chore.objects.create(
            title="Chore Day 1",
            assigned_to=alice,
            assigned_by=bob,
            due_date=day1,
        )
        # Create second chore for day 2 (later created_at)
        chore_day2_second = Chore.objects.create(
            title="Chore Day 2 Second",
            assigned_to=alice,
            assigned_by=bob,
            due_date=day2,
        )
        # Create chore for day 3
        chore_day3 = Chore.objects.create(
            title="Chore Day 3",
            assigned_to=alice,
            assigned_by=bob,
            due_date=day3,
        )

        response = client.get(reverse("chore_list"))
        chores = list(response.context["chores"])

        assert chores == [
            chore_day1,
            chore_day2_first,
            chore_day2_second,
            chore_day3,
        ]


@pytest.mark.django_db
class TestChoreCardRendering:
    def test_chore_item_displays_required_fields(self, client: Client):
        """Chore item renders title, description, assigned_to, assigned_by, due_date, and status."""
        alice = Roommate.objects.create(name="Alice")
        bob = Roommate.objects.create(name="Bob")
        due = datetime.date(2026, 10, 1)

        chore = Chore.objects.create(
            title="Clean Kitchen Counters",
            description="Wipe down the stove and counters with spray.",
            assigned_to=alice,
            assigned_by=bob,
            due_date=due,
            is_completed=False,
        )

        response = client.get(reverse("chore_list"))
        content = response.content.decode()

        assert "Clean Kitchen Counters" in content
        assert "Wipe down the stove and counters with spray." in content
        assert "Alice" in content
        assert "Bob" in content
        assert str(due) in content
        assert "Pending" in content

    def test_chore_without_description(self, client: Client):
        """Chore without description displays without empty paragraph errors."""
        alice = Roommate.objects.create(name="Alice")
        bob = Roommate.objects.create(name="Bob")

        chore = Chore.objects.create(
            title="Take Out Trash",
            description="",
            assigned_to=alice,
            assigned_by=bob,
            due_date=datetime.date(2026, 10, 1),
            is_completed=True,
        )

        response = client.get(reverse("chore_list"))
        content = response.content.decode()

        assert "Take Out Trash" in content
        assert "Completed" in content


@pytest.mark.django_db
class TestOverdueBadgeLogic:
    def test_overdue_badge_displayed_only_for_incomplete_past_due_chores(self, client: Client):
        """Overdue badge is displayed for incomplete chores where due_date < today,

        and NOT for completed chores or future/today chores.
        """
        alice = Roommate.objects.create(name="Alice")
        bob = Roommate.objects.create(name="Bob")

        today = timezone.localdate()
        yesterday = today - datetime.timedelta(days=1)
        tomorrow = today + datetime.timedelta(days=1)

        # 1. Past-due incomplete -> OVERDUE
        chore_overdue = Chore.objects.create(
            title="Past Due Incomplete Chore",
            assigned_to=alice,
            assigned_by=bob,
            due_date=yesterday,
            is_completed=False,
        )
        # 2. Past-due completed -> NOT overdue
        chore_past_completed = Chore.objects.create(
            title="Past Due Completed Chore",
            assigned_to=alice,
            assigned_by=bob,
            due_date=yesterday,
            is_completed=True,
        )
        # 3. Due today incomplete -> NOT overdue
        chore_today_incomplete = Chore.objects.create(
            title="Due Today Incomplete Chore",
            assigned_to=alice,
            assigned_by=bob,
            due_date=today,
            is_completed=False,
        )
        # 4. Due tomorrow incomplete -> NOT overdue
        chore_future_incomplete = Chore.objects.create(
            title="Due Tomorrow Incomplete Chore",
            assigned_to=alice,
            assigned_by=bob,
            due_date=tomorrow,
            is_completed=False,
        )

        response = client.get(reverse("chore_list"))
        chores_dict = {c.id: c for c in response.context["chores"]}

        assert chores_dict[chore_overdue.id].is_overdue is True
        assert chores_dict[chore_past_completed.id].is_overdue is False
        assert chores_dict[chore_today_incomplete.id].is_overdue is False
        assert chores_dict[chore_future_incomplete.id].is_overdue is False

        content = response.content.decode()
        # Exactly one overdue badge should appear in the rendered HTML
        assert content.count("Overdue") == 1


@pytest.mark.django_db
class TestEmptyStateDisplay:
    def test_empty_state_when_no_chores_exist(self, client: Client):
        """When no chores exist in the system, empty state message is displayed."""
        response = client.get(reverse("chore_list"))
        assert response.status_code == 200
        content = response.content.decode()
        assert "No chores found." in content

    def test_empty_state_when_filter_matches_nothing(self, client: Client):
        """When a filter matches zero chores, empty state message is displayed."""
        alice = Roommate.objects.create(name="Alice")
        bob = Roommate.objects.create(name="Bob")

        # Create only incomplete chore
        Chore.objects.create(
            title="Mop Floors",
            assigned_to=alice,
            assigned_by=bob,
            due_date=timezone.localdate(),
            is_completed=False,
        )

        response = client.get(reverse("chore_list"), {"tab": "completed"})
        assert response.status_code == 200
        assert len(response.context["chores"]) == 0
        content = response.content.decode()
        assert "No chores found." in content

    def test_empty_state_and_profile_prompt_when_mine_and_no_active_profile(self, client: Client):
        """When tab=mine with no active profile, both empty state and selection prompt are shown."""
        Roommate.objects.create(name="Alice")
        response = client.get(reverse("chore_list"), {"tab": "mine"})
        assert response.status_code == 200
        assert len(response.context["chores"]) == 0
        assert response.context["needs_profile"] is True

        content = response.content.decode()
        assert "No chores found." in content
        assert "Please select an active profile to view your assigned chores." in content


class TestChoreCreateRouting:
    def test_reverse_chore_create(self):
        """reverse('chore_create') resolves to '/chores/new/'."""
        assert reverse("chore_create") == "/chores/new/"

    def test_resolve_chore_create(self):
        """Path '/chores/new/' resolves to chore_create view function."""
        match = resolve("/chores/new/")
        assert match.func == chore_create
        assert match.url_name == "chore_create"


@pytest.mark.django_db
class TestChoreCreateGetView:
    def test_chore_create_get_status_200(self, client: Client):
        """GET request to '/chores/new/' returns HTTP status code 200 OK."""
        response = client.get(reverse("chore_create"))
        assert response.status_code == 200

    def test_chore_create_template_used(self, client: Client):
        """GET request renders chores/templates/chores/chore_form.html."""
        response = client.get(reverse("chore_create"))
        template_names = [t.name for t in response.templates if t.name]
        assert "chores/chore_form.html" in template_names

    def test_chore_create_context_contains_unbound_form(self, client: Client):
        """GET request context contains an unbound ChoreForm instance under key 'form'."""
        response = client.get(reverse("chore_create"))
        assert "form" in response.context
        form = response.context["form"]
        assert isinstance(form, ChoreForm)
        assert not form.is_bound

    def test_chore_create_renders_form_tag_and_csrf(self, client: Client):
        """Rendered form in chore_form.html contains '<form method=\"post\">' and valid csrf token."""
        response = client.get(reverse("chore_create"))
        content = response.content.decode()
        assert '<form method="post">' in content
        assert 'name="csrfmiddlewaretoken"' in content

    def test_chore_create_renders_form_controls(self, client: Client):
        """Template renders visible form controls for title, description, assigned_to, due_date."""
        response = client.get(reverse("chore_create"))
        content = response.content.decode()
        assert 'name="title"' in content
        assert 'name="description"' in content
        assert 'name="assigned_to"' in content
        assert 'name="due_date"' in content

    def test_chore_create_renders_submit_button(self, client: Client):
        """Template includes a submit button to create the chore."""
        response = client.get(reverse("chore_create"))
        content = response.content.decode()
        assert 'type="submit"' in content

    def test_chore_create_renders_cancel_link_to_chore_list(self, client: Client):
        """Template includes a cancel/back link navigating to reverse('chore_list') ('/')."""
        response = client.get(reverse("chore_create"))
        content = response.content.decode()
        assert f'href="{reverse("chore_list")}"' in content
        assert "Cancel" in content

    def test_chore_create_get_without_active_roommate_displays_prompt(self, client: Client):
        """When GET to '/chores/new/' without active roommate in session, warning prompt is displayed."""
        response = client.get(reverse("chore_create"))
        assert response.status_code == 200
        assert response.context["needs_profile"] is True
        content = response.content.decode()
        assert "select an active profile" in content or "select an active roommate" in content

    def test_chore_create_get_with_active_roommate_no_warning(self, client: Client):
        """When GET to '/chores/new/' with active roommate in session, warning prompt is not shown."""
        alice = Roommate.objects.create(name="Alice")
        session = client.session
        session["active_roommate_id"] = alice.id
        session.save()

        response = client.get(reverse("chore_create"))
        assert response.status_code == 200
        assert response.context["needs_profile"] is False


@pytest.mark.django_db
class TestChoreCreateCSRF:
    def test_post_without_csrf_returns_403(self):
        """Submitting POST to '/chores/new/' without a CSRF token returns HTTP status code 403 Forbidden."""
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(
            reverse("chore_create"),
            data={"title": "Test chore"},
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestChoreCreatePostSubmission:
    @pytest.fixture(autouse=True)
    def setup_data(self):
        self.alice = Roommate.objects.create(name="Alice")
        self.bob = Roommate.objects.create(name="Bob")

    def test_valid_post_creates_chore_and_redirects_to_chore_list(self, client: Client):
        """When active roommate in session, submitting valid form creates Chore with assigned_by and redirects (302)."""
        session = client.session
        session["active_roommate_id"] = self.alice.id
        session.save()

        post_data = {
            "title": "Clean kitchen",
            "description": "Wipe counters and mop floor.",
            "assigned_to": self.bob.id,
            "due_date": "2026-10-15",
        }
        response = client.post(reverse("chore_create"), data=post_data)

        assert response.status_code == 302
        assert response.url == reverse("chore_list")
        assert Chore.objects.count() == 1

        chore = Chore.objects.first()
        assert chore.title == "Clean kitchen"
        assert chore.description == "Wipe counters and mop floor."
        assert chore.assigned_to == self.bob
        assert chore.assigned_by == self.alice
        assert chore.due_date == datetime.date(2026, 10, 15)
        assert chore.is_completed is False

    def test_invalid_post_data_does_not_create_chore_and_rerenders_with_errors(self, client: Client):
        """When POST contains invalid/missing data, no record is created and form re-renders with 200."""
        session = client.session
        session["active_roommate_id"] = self.alice.id
        session.save()

        post_data = {
            "title": "",
            "description": "Preserved description text",
            "assigned_to": self.bob.id,
            "due_date": "2026-10-15",
        }
        response = client.post(reverse("chore_create"), data=post_data)

        assert response.status_code == 200
        assert Chore.objects.count() == 0
        template_names = [t.name for t in response.templates if t.name]
        assert "chores/chore_form.html" in template_names
        assert response.context["form"].errors
        assert "title" in response.context["form"].errors

        content = response.content.decode()
        assert "Preserved description text" in content

    def test_post_without_active_roommate_does_not_create_chore_and_rerenders_error(self, client: Client):
        """When POST without active roommate in session, no record is created and form re-renders with error."""
        post_data = {
            "title": "Clean kitchen",
            "description": "Some description",
            "assigned_to": self.bob.id,
            "due_date": "2026-10-15",
        }
        response = client.post(reverse("chore_create"), data=post_data)

        assert response.status_code == 200
        assert Chore.objects.count() == 0
        template_names = [t.name for t in response.templates if t.name]
        assert "chores/chore_form.html" in template_names

        content = response.content.decode()
        assert "select an active profile" in content or "select an active roommate" in content
        assert "Some description" in content

    def test_post_with_invalid_active_roommate_id_in_session(self, client: Client):
        """When POST with invalid active_roommate_id in session, no record is created and error displayed."""
        session = client.session
        session["active_roommate_id"] = 99999
        session.save()

        post_data = {
            "title": "Clean kitchen",
            "description": "Some description",
            "assigned_to": self.bob.id,
            "due_date": "2026-10-15",
        }
        response = client.post(reverse("chore_create"), data=post_data)

        assert response.status_code == 200
        assert Chore.objects.count() == 0
        content = response.content.decode()
        assert "select an active profile" in content or "select an active roommate" in content


@pytest.mark.django_db
class TestChoreListNewChoreLink:
    def test_chore_list_contains_new_chore_link(self, client: Client):
        """Template chores/chore_list.html includes a visible 'New Chore' link pointing to reverse('chore_create')."""
        response = client.get(reverse("chore_list"))
        assert response.status_code == 200
        content = response.content.decode()
        assert reverse("chore_create") in content
        assert "New Chore" in content


class TestChoreToggleAndDeleteRouting:
    def test_reverse_chore_toggle(self):
        """reverse('chore_toggle', kwargs={'pk': 1}) resolves to '/chores/1/toggle/'."""
        assert reverse("chore_toggle", kwargs={"pk": 1}) == "/chores/1/toggle/"

    def test_reverse_chore_delete(self):
        """reverse('chore_delete', kwargs={'pk': 1}) resolves to '/chores/1/delete/'."""
        assert reverse("chore_delete", kwargs={"pk": 1}) == "/chores/1/delete/"

    def test_resolve_chore_toggle(self):
        """Path '/chores/1/toggle/' maps to chore_toggle view function."""
        match = resolve("/chores/1/toggle/")
        assert match.func == chore_toggle
        assert match.url_name == "chore_toggle"

    def test_resolve_chore_delete(self):
        """Path '/chores/1/delete/' maps to chore_delete view function."""
        match = resolve("/chores/1/delete/")
        assert match.func == chore_delete
        assert match.url_name == "chore_delete"


@pytest.mark.django_db
class TestChoreActionMethodNotAllowed:
    @pytest.fixture(autouse=True)
    def setup_chore(self):
        alice = Roommate.objects.create(name="Alice")
        self.chore = Chore.objects.create(
            title="Test Chore",
            assigned_to=alice,
            assigned_by=alice,
            due_date=timezone.localdate(),
        )

    def test_chore_toggle_get_returns_405(self, client: Client):
        """GET request to '/chores/<pk>/toggle/' returns HTTP 405 Method Not Allowed."""
        url = reverse("chore_toggle", kwargs={"pk": self.chore.pk})
        response = client.get(url)
        assert response.status_code == 405

    def test_chore_toggle_non_post_returns_405(self, client: Client):
        """Non-POST requests (PUT, PATCH, DELETE) to '/chores/<pk>/toggle/' return HTTP 405."""
        url = reverse("chore_toggle", kwargs={"pk": self.chore.pk})
        for method in ["put", "patch", "delete"]:
            response = getattr(client, method)(url)
            assert response.status_code == 405

    def test_chore_delete_get_returns_405(self, client: Client):
        """GET request to '/chores/<pk>/delete/' returns HTTP 405 Method Not Allowed."""
        url = reverse("chore_delete", kwargs={"pk": self.chore.pk})
        response = client.get(url)
        assert response.status_code == 405

    def test_chore_delete_non_post_returns_405(self, client: Client):
        """Non-POST requests (PUT, PATCH) to '/chores/<pk>/delete/' return HTTP 405."""
        url = reverse("chore_delete", kwargs={"pk": self.chore.pk})
        for method in ["put", "patch"]:
            response = getattr(client, method)(url)
            assert response.status_code == 405


@pytest.mark.django_db
class TestChoreActionNotFound:
    def test_chore_toggle_nonexistent_pk_returns_404(self, client: Client):
        """POST request to '/chores/<pk>/toggle/' with non-existent pk returns HTTP 404 Not Found."""
        url = reverse("chore_toggle", kwargs={"pk": 99999})
        response = client.post(url)
        assert response.status_code == 404

    def test_chore_delete_nonexistent_pk_returns_404(self, client: Client):
        """POST request to '/chores/<pk>/delete/' with non-existent pk returns HTTP 404 Not Found."""
        url = reverse("chore_delete", kwargs={"pk": 99999})
        response = client.post(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestChoreToggleView:
    @pytest.fixture(autouse=True)
    def setup_data(self):
        self.alice = Roommate.objects.create(name="Alice")
        self.bob = Roommate.objects.create(name="Bob")

    def test_toggle_incomplete_chore_sets_completed_and_timestamp(self, client: Client):
        """POST request to toggle an incomplete chore sets is_completed=True and completed_at."""
        chore = Chore.objects.create(
            title="Sweep floors",
            assigned_to=self.alice,
            assigned_by=self.bob,
            due_date=timezone.localdate(),
            is_completed=False,
            completed_at=None,
        )
        before = timezone.now()
        url = reverse("chore_toggle", kwargs={"pk": chore.pk})
        response = client.post(url)

        assert response.status_code == 302
        chore.refresh_from_db()
        assert chore.is_completed is True
        assert chore.completed_at is not None
        after = timezone.now()
        assert before <= chore.completed_at <= after

    def test_toggle_completed_chore_sets_incomplete_and_clears_timestamp(self, client: Client):
        """POST request to toggle a completed chore sets is_completed=False and completed_at=None."""
        past_time = timezone.now() - datetime.timedelta(hours=2)
        chore = Chore.objects.create(
            title="Clean stove",
            assigned_to=self.alice,
            assigned_by=self.bob,
            due_date=timezone.localdate(),
            is_completed=True,
            completed_at=past_time,
        )
        url = reverse("chore_toggle", kwargs={"pk": chore.pk})
        response = client.post(url)

        assert response.status_code == 302
        chore.refresh_from_db()
        assert chore.is_completed is False
        assert chore.completed_at is None

    def test_toggle_redirect_safe_relative_referer(self, client: Client):
        """POST to toggle with safe local relative HTTP_REFERER redirects to that referer."""
        chore = Chore.objects.create(
            title="Wash dishes",
            assigned_to=self.alice,
            assigned_by=self.bob,
            due_date=timezone.localdate(),
        )
        url = reverse("chore_toggle", kwargs={"pk": chore.pk})
        response = client.post(url, HTTP_REFERER="/?tab=pending")
        assert response.status_code == 302
        assert response.url == "/?tab=pending"

    def test_toggle_redirect_safe_absolute_referer(self, client: Client):
        """POST to toggle with safe local absolute HTTP_REFERER redirects to that referer."""
        chore = Chore.objects.create(
            title="Wash dishes",
            assigned_to=self.alice,
            assigned_by=self.bob,
            due_date=timezone.localdate(),
        )
        url = reverse("chore_toggle", kwargs={"pk": chore.pk})
        safe_url = "http://testserver/?tab=completed"
        response = client.post(url, HTTP_REFERER=safe_url)
        assert response.status_code == 302
        assert response.url == safe_url

    def test_toggle_redirect_missing_referer(self, client: Client):
        """POST to toggle without HTTP_REFERER redirects to reverse('chore_list') ('/')."""
        chore = Chore.objects.create(
            title="Wash dishes",
            assigned_to=self.alice,
            assigned_by=self.bob,
            due_date=timezone.localdate(),
        )
        url = reverse("chore_toggle", kwargs={"pk": chore.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert response.url == reverse("chore_list")

    def test_toggle_redirect_untrusted_referer(self, client: Client):
        """POST to toggle with external/untrusted HTTP_REFERER falls back to reverse('chore_list')."""
        chore = Chore.objects.create(
            title="Wash dishes",
            assigned_to=self.alice,
            assigned_by=self.bob,
            due_date=timezone.localdate(),
        )
        url = reverse("chore_toggle", kwargs={"pk": chore.pk})
        for untrusted in ["https://evil.com/phish", "//evil.com/phish", "javascript:alert(1)"]:
            response = client.post(url, HTTP_REFERER=untrusted)
            assert response.status_code == 302
            assert response.url == reverse("chore_list")


@pytest.mark.django_db
class TestChoreDeleteView:
    @pytest.fixture(autouse=True)
    def setup_data(self):
        self.alice = Roommate.objects.create(name="Alice")
        self.bob = Roommate.objects.create(name="Bob")

    def test_delete_removes_chore_from_database(self, client: Client):
        """POST request to delete removes the chore record from the database."""
        chore = Chore.objects.create(
            title="Take out recycling",
            assigned_to=self.alice,
            assigned_by=self.bob,
            due_date=timezone.localdate(),
        )
        chore_id = chore.pk
        url = reverse("chore_delete", kwargs={"pk": chore_id})
        response = client.post(url)

        assert response.status_code == 302
        assert not Chore.objects.filter(pk=chore_id).exists()
        assert Chore.objects.count() == 0

    def test_delete_redirect_safe_relative_referer(self, client: Client):
        """POST to delete with safe local relative HTTP_REFERER redirects to that referer."""
        chore = Chore.objects.create(
            title="Mow lawn",
            assigned_to=self.alice,
            assigned_by=self.bob,
            due_date=timezone.localdate(),
        )
        url = reverse("chore_delete", kwargs={"pk": chore.pk})
        response = client.post(url, HTTP_REFERER="/?tab=all")
        assert response.status_code == 302
        assert response.url == "/?tab=all"

    def test_delete_redirect_safe_absolute_referer(self, client: Client):
        """POST to delete with safe local absolute HTTP_REFERER redirects to that referer."""
        chore = Chore.objects.create(
            title="Mow lawn",
            assigned_to=self.alice,
            assigned_by=self.bob,
            due_date=timezone.localdate(),
        )
        url = reverse("chore_delete", kwargs={"pk": chore.pk})
        safe_url = "http://testserver/?tab=mine"
        response = client.post(url, HTTP_REFERER=safe_url)
        assert response.status_code == 302
        assert response.url == safe_url

    def test_delete_redirect_missing_referer(self, client: Client):
        """POST to delete without HTTP_REFERER redirects to reverse('chore_list') ('/')."""
        chore = Chore.objects.create(
            title="Mow lawn",
            assigned_to=self.alice,
            assigned_by=self.bob,
            due_date=timezone.localdate(),
        )
        url = reverse("chore_delete", kwargs={"pk": chore.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert response.url == reverse("chore_list")

    def test_delete_redirect_untrusted_referer(self, client: Client):
        """POST to delete with untrusted/external HTTP_REFERER falls back to reverse('chore_list')."""
        chore = Chore.objects.create(
            title="Mow lawn",
            assigned_to=self.alice,
            assigned_by=self.bob,
            due_date=timezone.localdate(),
        )
        url = reverse("chore_delete", kwargs={"pk": chore.pk})
        response = client.post(url, HTTP_REFERER="https://attacker.com/steal")
        assert response.status_code == 302
        assert response.url == reverse("chore_list")

    def test_delete_redirect_untrusted_schemeless_referer(self, client: Client):
        """POST to delete with untrusted schemeless HTTP_REFERER falls back to reverse('chore_list')."""
        chore = Chore.objects.create(
            title="Mow lawn 2",
            assigned_to=self.alice,
            assigned_by=self.bob,
            due_date=timezone.localdate(),
        )
        url = reverse("chore_delete", kwargs={"pk": chore.pk})
        response = client.post(url, HTTP_REFERER="//attacker.com/steal")
        assert response.status_code == 302
        assert response.url == reverse("chore_list")


@pytest.mark.django_db
class TestChoreCardActionsRendering:
    @pytest.fixture(autouse=True)
    def setup_chores(self):
        self.alice = Roommate.objects.create(name="Alice")
        self.bob = Roommate.objects.create(name="Bob")

        self.incomplete_chore = Chore.objects.create(
            title="Dust Shelves",
            assigned_to=self.alice,
            assigned_by=self.bob,
            due_date=timezone.localdate(),
            is_completed=False,
        )
        self.completed_chore = Chore.objects.create(
            title="Water Plants",
            assigned_to=self.bob,
            assigned_by=self.alice,
            due_date=timezone.localdate(),
            is_completed=True,
        )

    def test_chore_card_renders_toggle_form_and_button_states(self, client: Client):
        """Each chore card renders a POST form to toggle with CSRF and appropriate button text."""
        response = client.get(reverse("chore_list"))
        content = response.content.decode()

        toggle_url_incomplete = reverse("chore_toggle", kwargs={"pk": self.incomplete_chore.pk})
        toggle_url_completed = reverse("chore_toggle", kwargs={"pk": self.completed_chore.pk})

        # Check forms exist
        assert f'action="{toggle_url_incomplete}"' in content
        assert f'action="{toggle_url_completed}"' in content
        assert 'method="post"' in content

        # Check button text
        assert "Done" in content or "Mark Complete" in content
        assert "Undo" in content or "Mark Incomplete" in content

    def test_chore_card_renders_delete_form_and_button(self, client: Client):
        """Each chore card renders a POST form to delete with CSRF and a Delete button."""
        response = client.get(reverse("chore_list"))
        content = response.content.decode()

        delete_url_incomplete = reverse("chore_delete", kwargs={"pk": self.incomplete_chore.pk})
        delete_url_completed = reverse("chore_delete", kwargs={"pk": self.completed_chore.pk})

        assert f'action="{delete_url_incomplete}"' in content
        assert f'action="{delete_url_completed}"' in content
        assert "Delete" in content

    def test_chore_card_forms_include_csrf_token(self, client: Client):
        """Chore cards include CSRF token fields in action forms."""
        response = client.get(reverse("chore_list"))
        content = response.content.decode()
        assert 'name="csrfmiddlewaretoken"' in content


@pytest.mark.django_db
class TestChoreActionCSRF:
    def test_toggle_post_without_csrf_returns_403(self):
        """Submitting POST to '/chores/<pk>/toggle/' without CSRF returns 403."""
        alice = Roommate.objects.create(name="Alice")
        chore = Chore.objects.create(
            title="Test chore",
            assigned_to=alice,
            assigned_by=alice,
            due_date=timezone.localdate(),
        )
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(reverse("chore_toggle", kwargs={"pk": chore.pk}))
        assert response.status_code == 403

    def test_delete_post_without_csrf_returns_403(self):
        """Submitting POST to '/chores/<pk>/delete/' without CSRF returns 403."""
        alice = Roommate.objects.create(name="Alice")
        chore = Chore.objects.create(
            title="Test chore",
            assigned_to=alice,
            assigned_by=alice,
            due_date=timezone.localdate(),
        )
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(reverse("chore_delete", kwargs={"pk": chore.pk}))
        assert response.status_code == 403

