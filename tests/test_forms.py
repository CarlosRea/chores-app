import datetime
import pytest
from django import forms
from django.core.exceptions import ValidationError

from chores.forms import ChoreForm
from chores.models import Chore, Roommate


@pytest.mark.django_db
class TestChoreFormFields:
    def test_form_fields_included(self):
        """ChoreForm includes title, description, assigned_to, and due_date."""
        form = ChoreForm()
        assert set(form.fields.keys()) == {"title", "description", "assigned_to", "due_date"}

    def test_form_fields_excluded(self):
        """ChoreForm excludes assigned_by, is_completed, completed_at, and created_at."""
        form = ChoreForm()
        for excluded_field in ["assigned_by", "is_completed", "completed_at", "created_at"]:
            assert excluded_field not in form.fields

    def test_due_date_widget_configured_as_date_input(self):
        """ChoreForm configures due_date widget with HTML5 date input type."""
        form = ChoreForm()
        due_date_widget = form.fields["due_date"].widget
        assert isinstance(due_date_widget, forms.DateInput)
        assert due_date_widget.input_type == "date"
        assert 'type="date"' in str(form["due_date"])

    def test_assigned_to_queryset_ordered_alphabetically_by_name(self):
        """ChoreForm populates assigned_to with all roommates ordered alphabetically by name."""
        Roommate.objects.create(name="Zach")
        Roommate.objects.create(name="Alice")
        Roommate.objects.create(name="Charlie")
        Roommate.objects.create(name="Bob")

        form = ChoreForm()
        queryset_names = list(form.fields["assigned_to"].queryset.values_list("name", flat=True))
        assert queryset_names == ["Alice", "Bob", "Charlie", "Zach"]


@pytest.mark.django_db
class TestChoreFormValidation:
    @pytest.fixture(autouse=True)
    def setup_roommates(self):
        self.alice = Roommate.objects.create(name="Alice")
        self.bob = Roommate.objects.create(name="Bob")

    def test_valid_form_with_all_fields(self):
        """ChoreForm is valid when all fields including description are provided."""
        form_data = {
            "title": "Clean kitchen",
            "description": "Wipe counters and mop floor.",
            "assigned_to": self.alice.id,
            "due_date": "2026-10-15",
        }
        form = ChoreForm(data=form_data)
        assert form.is_valid(), form.errors
        assert form.cleaned_data["title"] == "Clean kitchen"
        assert form.cleaned_data["description"] == "Wipe counters and mop floor."
        assert form.cleaned_data["assigned_to"] == self.alice
        assert form.cleaned_data["due_date"] == datetime.date(2026, 10, 15)

    def test_valid_form_with_blank_description(self):
        """ChoreForm validation succeeds when optional field description is blank."""
        form_data = {
            "title": "Take out trash",
            "description": "",
            "assigned_to": self.bob.id,
            "due_date": "2026-10-15",
        }
        form = ChoreForm(data=form_data)
        assert form.is_valid(), form.errors
        assert form.cleaned_data["description"] == ""

    def test_validation_fails_empty_title(self):
        """ChoreForm validation fails when title is empty."""
        form_data = {
            "title": "",
            "description": "Some description",
            "assigned_to": self.alice.id,
            "due_date": "2026-10-15",
        }
        form = ChoreForm(data=form_data)
        assert not form.is_valid()
        assert "title" in form.errors

    def test_validation_fails_whitespace_only_title(self):
        """ChoreForm validation fails when title contains only whitespace."""
        form_data = {
            "title": "    \t \n  ",
            "description": "Some description",
            "assigned_to": self.alice.id,
            "due_date": "2026-10-15",
        }
        form = ChoreForm(data=form_data)
        assert not form.is_valid()
        assert "title" in form.errors

    def test_title_is_stripped_of_surrounding_whitespace(self):
        """Valid title with surrounding whitespace is stripped upon clean."""
        form_data = {
            "title": "  Wash dishes  ",
            "description": "",
            "assigned_to": self.alice.id,
            "due_date": "2026-10-15",
        }
        form = ChoreForm(data=form_data)
        assert form.is_valid(), form.errors
        assert form.cleaned_data["title"] == "Wash dishes"

    def test_validation_fails_missing_assigned_to(self):
        """ChoreForm validation fails when assigned_to is not selected."""
        form_data = {
            "title": "Dust shelves",
            "description": "",
            "assigned_to": "",
            "due_date": "2026-10-15",
        }
        form = ChoreForm(data=form_data)
        assert not form.is_valid()
        assert "assigned_to" in form.errors

    def test_validation_fails_nonexistent_assigned_to(self):
        """ChoreForm validation fails when assigned_to references a non-existent roommate."""
        form_data = {
            "title": "Dust shelves",
            "description": "",
            "assigned_to": 99999,
            "due_date": "2026-10-15",
        }
        form = ChoreForm(data=form_data)
        assert not form.is_valid()
        assert "assigned_to" in form.errors

    def test_validation_fails_empty_due_date(self):
        """ChoreForm validation fails when due_date is empty."""
        form_data = {
            "title": "Dust shelves",
            "description": "",
            "assigned_to": self.alice.id,
            "due_date": "",
        }
        form = ChoreForm(data=form_data)
        assert not form.is_valid()
        assert "due_date" in form.errors

    def test_validation_fails_invalid_due_date(self):
        """ChoreForm validation fails when due_date is not a valid date string."""
        form_data = {
            "title": "Dust shelves",
            "description": "",
            "assigned_to": self.alice.id,
            "due_date": "not-a-valid-date",
        }
        form = ChoreForm(data=form_data)
        assert not form.is_valid()
        assert "due_date" in form.errors

    def test_form_save_with_assigned_by(self):
        """Form can save chore instance with commit=False and set assigned_by."""
        form_data = {
            "title": "Vacuum living room",
            "description": "Including under the sofa",
            "assigned_to": self.alice.id,
            "due_date": "2026-10-20",
        }
        form = ChoreForm(data=form_data)
        assert form.is_valid()
        chore = form.save(commit=False)
        chore.assigned_by = self.bob
        chore.save()

        assert chore.pk is not None
        assert chore.title == "Vacuum living room"
        assert chore.assigned_to == self.alice
        assert chore.assigned_by == self.bob
        assert chore.due_date == datetime.date(2026, 10, 20)
