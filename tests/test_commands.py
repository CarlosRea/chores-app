import io
import pytest
from django.core.management import call_command
from django.utils import timezone

from chores.management.commands.seed_chores import SAMPLE_CHORE_TITLES
from chores.management.commands.seed_roommates import DEFAULT_ROOMMATES
from chores.models import Chore, Roommate


@pytest.mark.django_db
class TestSeedRoommatesCommand:
    def test_seed_roommates_empty_database(self):
        """Executing seed_roommates on empty DB creates default roommates with stdout messages."""
        assert Roommate.objects.count() == 0

        out = io.StringIO()
        call_command("seed_roommates", stdout=out)
        output = out.getvalue()

        assert Roommate.objects.count() == 3
        existing_names = set(Roommate.objects.values_list("name", flat=True))
        assert existing_names == set(DEFAULT_ROOMMATES)
        assert existing_names == {"Alice", "Bob", "Charlie"}

        for name in DEFAULT_ROOMMATES:
            assert f"Created roommate: {name}" in output
        assert "Successfully seeded 3 roommate(s)." in output

    def test_seed_roommates_idempotency(self):
        """Executing seed_roommates multiple times produces no duplicates and no errors."""
        out1 = io.StringIO()
        call_command("seed_roommates", stdout=out1)
        assert Roommate.objects.count() == 3

        out2 = io.StringIO()
        call_command("seed_roommates", stdout=out2)
        output2 = out2.getvalue()

        assert Roommate.objects.count() == 3
        assert set(Roommate.objects.values_list("name", flat=True)) == {"Alice", "Bob", "Charlie"}
        for name in DEFAULT_ROOMMATES:
            assert f"Roommate already exists: {name}" in output2
        assert "All default roommates already exist. No new records created." in output2

    def test_seed_roommates_partial_existing(self):
        """When some default roommates exist, seed_roommates creates only the missing ones."""
        Roommate.objects.create(name="Alice")
        assert Roommate.objects.count() == 1

        out = io.StringIO()
        call_command("seed_roommates", stdout=out)
        output = out.getvalue()

        assert Roommate.objects.count() == 3
        assert set(Roommate.objects.values_list("name", flat=True)) == {"Alice", "Bob", "Charlie"}
        assert "Roommate already exists: Alice" in output
        assert "Created roommate: Bob" in output
        assert "Created roommate: Charlie" in output
        assert "Successfully seeded 2 roommate(s)." in output

    def test_seed_roommates_preserves_custom_records(self):
        """Existing custom non-default roommates are not deleted or altered."""
        custom_roommate = Roommate.objects.create(name="David")
        custom_id = custom_roommate.id

        out = io.StringIO()
        call_command("seed_roommates", stdout=out)

        assert Roommate.objects.count() == 4
        assert set(Roommate.objects.values_list("name", flat=True)) == {
            "Alice",
            "Bob",
            "Charlie",
            "David",
        }
        refetched_custom = Roommate.objects.get(id=custom_id)
        assert refetched_custom.name == "David"

    def test_seed_roommates_programmatic_call(self):
        """Command can be called programmatically via call_command with default arguments."""
        assert Roommate.objects.count() == 0
        call_command("seed_roommates")
        assert Roommate.objects.count() == 3
        assert set(Roommate.objects.values_list("name", flat=True)) == {"Alice", "Bob", "Charlie"}


@pytest.mark.django_db
class TestSeedChoresCommand:
    def test_seed_chores_empty_database(self):
        """Executing seed_chores on empty DB populates default roommates and sample chores."""
        assert Roommate.objects.count() == 0
        assert Chore.objects.count() == 0

        out = io.StringIO()
        call_command("seed_chores", stdout=out)
        output = out.getvalue()

        assert Roommate.objects.count() == 3
        assert set(Roommate.objects.values_list("name", flat=True)) == {"Alice", "Bob", "Charlie"}
        assert Chore.objects.count() == len(SAMPLE_CHORE_TITLES)
        assert set(Chore.objects.values_list("title", flat=True)) == set(SAMPLE_CHORE_TITLES)

        for name in DEFAULT_ROOMMATES:
            assert f"Created roommate: {name}" in output
        for title in SAMPLE_CHORE_TITLES:
            assert f"Created chore: {title}" in output
        assert f"Successfully seeded {len(SAMPLE_CHORE_TITLES)} chore(s)." in output

    def test_seed_chores_roommates_already_exist(self):
        """When default roommates exist, seed_chores succeeds without recreating roommates."""
        call_command("seed_roommates")
        assert Roommate.objects.count() == 3
        assert Chore.objects.count() == 0

        out = io.StringIO()
        call_command("seed_chores", stdout=out)
        output = out.getvalue()

        assert Roommate.objects.count() == 3
        assert Chore.objects.count() == len(SAMPLE_CHORE_TITLES)
        assert "Created roommate:" not in output
        for title in SAMPLE_CHORE_TITLES:
            assert f"Created chore: {title}" in output
        assert f"Successfully seeded {len(SAMPLE_CHORE_TITLES)} chore(s)." in output

    def test_seed_chores_idempotency(self):
        """Executing seed_chores multiple times produces no duplicates and no errors."""
        out1 = io.StringIO()
        call_command("seed_chores", stdout=out1)
        assert Chore.objects.count() == len(SAMPLE_CHORE_TITLES)

        out2 = io.StringIO()
        call_command("seed_chores", stdout=out2)
        output2 = out2.getvalue()

        assert Chore.objects.count() == len(SAMPLE_CHORE_TITLES)
        for title in SAMPLE_CHORE_TITLES:
            assert f"Chore already exists: {title}" in output2
        assert "All sample chores already exist. No new records created." in output2

    def test_seed_chores_partial_existing(self):
        """When a subset of sample chores already exists, only missing chores are created."""
        call_command("seed_roommates")
        alice = Roommate.objects.get(name="Alice")
        bob = Roommate.objects.get(name="Bob")

        existing_chore = Chore.objects.create(
            title=SAMPLE_CHORE_TITLES[0],
            description="Existing description",
            assigned_by=alice,
            assigned_to=bob,
            due_date=timezone.localdate(),
        )
        assert Chore.objects.count() == 1

        out = io.StringIO()
        call_command("seed_chores", stdout=out)
        output = out.getvalue()

        assert Chore.objects.count() == len(SAMPLE_CHORE_TITLES)
        assert f"Chore already exists: {SAMPLE_CHORE_TITLES[0]}" in output
        for title in SAMPLE_CHORE_TITLES[1:]:
            assert f"Created chore: {title}" in output
        assert f"Successfully seeded {len(SAMPLE_CHORE_TITLES) - 1} chore(s)." in output

        # Verify pre-existing chore was not overwritten
        existing_chore.refresh_from_db()
        assert existing_chore.description == "Existing description"

    def test_seed_chores_preserves_custom_chores(self):
        """Existing custom non-sample chores and custom roommates are preserved."""
        david = Roommate.objects.create(name="David")
        custom_chore = Chore.objects.create(
            title="Custom chore for David",
            description="Special tasks",
            assigned_by=david,
            assigned_to=david,
            due_date=timezone.localdate(),
            is_completed=False,
        )
        custom_id = custom_chore.id

        out = io.StringIO()
        call_command("seed_chores", stdout=out)

        assert Roommate.objects.count() == 4
        assert Chore.objects.count() == len(SAMPLE_CHORE_TITLES) + 1

        refetched = Chore.objects.get(id=custom_id)
        assert refetched.title == "Custom chore for David"
        assert refetched.description == "Special tasks"
        assert refetched.assigned_by == david
        assert refetched.assigned_to == david
        assert not refetched.is_completed

    def test_seed_chores_chore_states_and_distribution(self):
        """Seeded chores contain overdue incomplete, completed with completed_at, and future incomplete chores."""
        today = timezone.localdate()
        call_command("seed_chores")

        chores = list(Chore.objects.all())
        assert len(chores) == len(SAMPLE_CHORE_TITLES)

        overdue_chores = [c for c in chores if c.due_date < today and not c.is_completed and c.completed_at is None]
        assert len(overdue_chores) >= 1

        completed_chores = [c for c in chores if c.is_completed and c.completed_at is not None]
        assert len(completed_chores) >= 1
        for chore in completed_chores:
            assert timezone.is_aware(chore.completed_at)

        future_chores = [c for c in chores if c.due_date > today and not c.is_completed and c.completed_at is None]
        assert len(future_chores) >= 1

        today_chores = [c for c in chores if c.due_date == today and not c.is_completed]
        assert len(today_chores) >= 1

        # Check assigned_by and assigned_to distribution
        assigned_by_names = {c.assigned_by.name for c in chores}
        assigned_to_names = {c.assigned_to.name for c in chores}
        assert assigned_by_names == {"Alice", "Bob", "Charlie"}
        assert assigned_to_names == {"Alice", "Bob", "Charlie"}
        # Check that different assignments exist
        pairs = {(c.assigned_by.name, c.assigned_to.name) for c in chores}
        assert len(pairs) >= 3

    def test_seed_chores_stdout_reporting(self):
        """Stdout messages report created chores, skipped chores, and accurate summaries."""
        out = io.StringIO()
        call_command("seed_chores", stdout=out)
        first_output = out.getvalue()

        for title in SAMPLE_CHORE_TITLES:
            assert f"Created chore: {title}" in first_output
        assert f"Successfully seeded {len(SAMPLE_CHORE_TITLES)} chore(s)." in first_output

        out2 = io.StringIO()
        call_command("seed_chores", stdout=out2)
        second_output = out2.getvalue()

        for title in SAMPLE_CHORE_TITLES:
            assert f"Chore already exists: {title}" in second_output
        assert "All sample chores already exist. No new records created." in second_output

    def test_seed_chores_programmatic_call(self):
        """Command can be executed programmatically via call_command without extra arguments."""
        assert Chore.objects.count() == 0
        call_command("seed_chores")
        assert Chore.objects.count() == len(SAMPLE_CHORE_TITLES)

