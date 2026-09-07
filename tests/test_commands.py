import io
import pytest
from django.core.management import call_command

from chores.management.commands.seed_roommates import DEFAULT_ROOMMATES
from chores.models import Roommate


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
