import datetime
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from chores.models import Chore, Roommate


@pytest.mark.django_db
class TestRoommateModel:
    def test_create_roommate_success(self):
        """Roommate can be created with valid name."""
        roommate = Roommate.objects.create(name="Alice")
        assert roommate.pk is not None
        assert roommate.name == "Alice"

    def test_str_representation(self):
        """Roommate.__str__() returns self.name."""
        roommate = Roommate(name="Bob")
        assert str(roommate) == "Bob"

    def test_duplicate_name_raises_integrity_error(self):
        """Attempting to save a Roommate with duplicate name raises IntegrityError."""
        Roommate.objects.create(name="Charlie")
        with pytest.raises(IntegrityError):
            Roommate.objects.create(name="Charlie")

    def test_name_exceeding_max_length_raises_validation_error(self):
        """Calling full_clean() on Roommate with name > 50 chars raises ValidationError."""
        long_name = "A" * 51
        roommate = Roommate(name=long_name)
        with pytest.raises(ValidationError) as exc_info:
            roommate.full_clean()
        assert "name" in exc_info.value.message_dict

    def test_blank_name_raises_validation_error(self):
        """Calling full_clean() on Roommate with blank name raises ValidationError."""
        roommate = Roommate(name="")
        with pytest.raises(ValidationError) as exc_info:
            roommate.full_clean()
        assert "name" in exc_info.value.message_dict


@pytest.mark.django_db
class TestChoreModel:
    @pytest.fixture
    def assigner(self):
        return Roommate.objects.create(name="Assigner")

    @pytest.fixture
    def assignee(self):
        return Roommate.objects.create(name="Assignee")

    def test_create_chore_success(self, assigner, assignee):
        """Chore can be created with all specified fields."""
        due_date = datetime.date.today() + datetime.timedelta(days=2)
        chore = Chore.objects.create(
            title="Clean Kitchen",
            description="Wipe counters and mop floor",
            assigned_by=assigner,
            assigned_to=assignee,
            due_date=due_date,
        )
        assert chore.pk is not None
        assert chore.title == "Clean Kitchen"
        assert chore.description == "Wipe counters and mop floor"
        assert chore.assigned_by == assigner
        assert chore.assigned_to == assignee
        assert chore.due_date == due_date
        assert chore.is_completed is False
        assert chore.completed_at is None
        assert chore.created_at is not None

    def test_str_representation(self, assigner, assignee):
        """Chore.__str__() returns self.title."""
        chore = Chore(
            title="Take out trash",
            assigned_by=assigner,
            assigned_to=assignee,
            due_date=datetime.date.today(),
        )
        assert str(chore) == "Take out trash"

    def test_description_defaults_to_empty_string(self, assigner, assignee):
        """Creating a Chore without description succeeds and defaults to empty string."""
        chore = Chore.objects.create(
            title="Wash Dishes",
            assigned_by=assigner,
            assigned_to=assignee,
            due_date=datetime.date.today(),
        )
        assert chore.description == ""

    def test_default_completion_status(self, assigner, assignee):
        """A newly created Chore has is_completed=False and completed_at=None by default."""
        chore = Chore.objects.create(
            title="Vacuum Living Room",
            assigned_by=assigner,
            assigned_to=assignee,
            due_date=datetime.date.today(),
        )
        assert chore.is_completed is False
        assert chore.completed_at is None

    def test_can_set_completion_status(self, assigner, assignee):
        """A Chore can be marked completed with a completed_at timestamp."""
        now = timezone.now()
        chore = Chore.objects.create(
            title="Water Plants",
            assigned_by=assigner,
            assigned_to=assignee,
            due_date=datetime.date.today(),
            is_completed=True,
            completed_at=now,
        )
        chore.refresh_from_db()
        assert chore.is_completed is True
        assert chore.completed_at is not None

    def test_same_roommate_as_assigner_and_assignee(self, assigner):
        """A Chore can have the same Roommate instance as both assigned_by and assigned_to."""
        chore = Chore.objects.create(
            title="Self-assigned Task",
            assigned_by=assigner,
            assigned_to=assigner,
            due_date=datetime.date.today(),
        )
        assert chore.assigned_by == assigner
        assert chore.assigned_to == assigner

    def test_reverse_relationships(self, assigner, assignee):
        """Reverse relationships assigned_chores and my_chores return expected QuerySets."""
        chore1 = Chore.objects.create(
            title="Chore 1",
            assigned_by=assigner,
            assigned_to=assignee,
            due_date=datetime.date.today(),
        )
        chore2 = Chore.objects.create(
            title="Chore 2",
            assigned_by=assigner,
            assigned_to=assigner,
            due_date=datetime.date.today(),
        )

        assert list(assigner.assigned_chores.all().order_by("id")) == [chore1, chore2]
        assert list(assigner.my_chores.all()) == [chore2]
        assert list(assignee.assigned_chores.all()) == []
        assert list(assignee.my_chores.all()) == [chore1]

    def test_title_exceeding_max_length_raises_validation_error(self, assigner, assignee):
        """Calling full_clean() on a Chore with title > 150 chars raises ValidationError."""
        chore = Chore(
            title="T" * 151,
            assigned_by=assigner,
            assigned_to=assignee,
            due_date=datetime.date.today(),
        )
        with pytest.raises(ValidationError) as exc_info:
            chore.full_clean()
        assert "title" in exc_info.value.message_dict

    def test_blank_title_raises_validation_error(self, assigner, assignee):
        """Calling full_clean() on a Chore with blank title raises ValidationError."""
        chore = Chore(
            title="",
            assigned_by=assigner,
            assigned_to=assignee,
            due_date=datetime.date.today(),
        )
        with pytest.raises(ValidationError) as exc_info:
            chore.full_clean()
        assert "title" in exc_info.value.message_dict

    def test_cascade_delete_on_assigned_by_roommate(self, assigner, assignee):
        """Deleting assigner cascades and deletes chore without deleting assignee."""
        chore = Chore.objects.create(
            title="Chore to delete",
            assigned_by=assigner,
            assigned_to=assignee,
            due_date=datetime.date.today(),
        )
        chore_id = chore.id
        assignee_id = assignee.id

        assigner.delete()

        assert not Chore.objects.filter(id=chore_id).exists()
        assert Roommate.objects.filter(id=assignee_id).exists()

    def test_cascade_delete_on_assigned_to_roommate(self, assigner, assignee):
        """Deleting assignee cascades and deletes chore without deleting assigner."""
        chore = Chore.objects.create(
            title="Chore to delete",
            assigned_by=assigner,
            assigned_to=assignee,
            due_date=datetime.date.today(),
        )
        chore_id = chore.id
        assigner_id = assigner.id

        assignee.delete()

        assert not Chore.objects.filter(id=chore_id).exists()
        assert Roommate.objects.filter(id=assigner_id).exists()

    def test_cascade_delete_multiple_chores_for_roommate(self, assigner, assignee):
        """Deleting a roommate deletes all chores where they are assigned_by or assigned_to."""
        # Chore 1: assigner is assigned_by
        chore1 = Chore.objects.create(
            title="Chore 1",
            assigned_by=assigner,
            assigned_to=assignee,
            due_date=datetime.date.today(),
        )
        # Chore 2: assigner is assigned_to
        chore2 = Chore.objects.create(
            title="Chore 2",
            assigned_by=assignee,
            assigned_to=assigner,
            due_date=datetime.date.today(),
        )
        # Chore 3: assigner is both
        chore3 = Chore.objects.create(
            title="Chore 3",
            assigned_by=assigner,
            assigned_to=assigner,
            due_date=datetime.date.today(),
        )

        assigner.delete()

        assert not Chore.objects.filter(id__in=[chore1.id, chore2.id, chore3.id]).exists()
        assert Roommate.objects.filter(id=assignee.id).exists()

    def test_model_fields_configuration(self):
        """Verify model field types, max_lengths, related names, and defaults."""
        from django.db import models

        name_field = Roommate._meta.get_field("name")
        assert isinstance(name_field, models.CharField)
        assert name_field.max_length == 50
        assert name_field.unique is True

        title_field = Chore._meta.get_field("title")
        assert isinstance(title_field, models.CharField)
        assert title_field.max_length == 150

        desc_field = Chore._meta.get_field("description")
        assert isinstance(desc_field, models.TextField)
        assert desc_field.blank is True

        assigned_by_field = Chore._meta.get_field("assigned_by")
        assert isinstance(assigned_by_field, models.ForeignKey)
        assert assigned_by_field.remote_field.model == Roommate
        assert assigned_by_field.remote_field.related_name == "assigned_chores"
        assert assigned_by_field.remote_field.on_delete == models.CASCADE

        assigned_to_field = Chore._meta.get_field("assigned_to")
        assert isinstance(assigned_to_field, models.ForeignKey)
        assert assigned_to_field.remote_field.model == Roommate
        assert assigned_to_field.remote_field.related_name == "my_chores"
        assert assigned_to_field.remote_field.on_delete == models.CASCADE

        due_date_field = Chore._meta.get_field("due_date")
        assert isinstance(due_date_field, models.DateField)

        is_completed_field = Chore._meta.get_field("is_completed")
        assert isinstance(is_completed_field, models.BooleanField)
        assert is_completed_field.default is False

        completed_at_field = Chore._meta.get_field("completed_at")
        assert isinstance(completed_at_field, models.DateTimeField)
        assert completed_at_field.null is True
        assert completed_at_field.blank is True

        created_at_field = Chore._meta.get_field("created_at")
        assert isinstance(created_at_field, models.DateTimeField)
        assert created_at_field.auto_now_add is True


