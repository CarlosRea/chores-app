import datetime
import pytest
from django.test import Client, RequestFactory
from django.urls import resolve, reverse
from django.utils import timezone

from chores.models import Chore, Roommate
from chores.views import chore_list


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
