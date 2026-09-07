from datetime import timedelta

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from chores.management.commands.seed_roommates import DEFAULT_ROOMMATES
from chores.models import Chore, Roommate

SAMPLE_CHORE_TITLES = [
    "Take out the trash and recycling",
    "Clean the kitchen counters and sink",
    "Vacuum the living room rug",
    "Clean the bathroom",
    "Restock paper towels and hand soap",
]


def get_sample_chores():
    today = timezone.localdate()
    now = timezone.now()

    return [
        {
            "title": "Take out the trash and recycling",
            "description": "Empty kitchen trash bin, take recycling bins to the curb, and replace bags.",
            "assigned_by": "Alice",
            "assigned_to": "Bob",
            "due_date": today - timedelta(days=2),
            "is_completed": False,
            "completed_at": None,
        },
        {
            "title": "Clean the kitchen counters and sink",
            "description": "Wipe down all countertops, scrub the sink, and run the dishwasher.",
            "assigned_by": "Bob",
            "assigned_to": "Charlie",
            "due_date": today - timedelta(days=1),
            "is_completed": True,
            "completed_at": now - timedelta(hours=6),
        },
        {
            "title": "Vacuum the living room rug",
            "description": "Vacuum the main living room area and hallway rug.",
            "assigned_by": "Charlie",
            "assigned_to": "Alice",
            "due_date": today,
            "is_completed": False,
            "completed_at": None,
        },
        {
            "title": "Clean the bathroom",
            "description": "Scrub toilet, shower/tub, and wipe bathroom mirror and sink.",
            "assigned_by": "Alice",
            "assigned_to": "Charlie",
            "due_date": today + timedelta(days=3),
            "is_completed": False,
            "completed_at": None,
        },
        {
            "title": "Restock paper towels and hand soap",
            "description": "Check supply closet and refill kitchen and bathroom soap dispensers.",
            "assigned_by": "Bob",
            "assigned_to": "Alice",
            "due_date": today + timedelta(days=5),
            "is_completed": False,
            "completed_at": None,
        },
    ]


class Command(BaseCommand):
    help = "Seed initial sample chores into the database."

    def handle(self, *args, **options):
        if Roommate.objects.filter(name__in=DEFAULT_ROOMMATES).count() < len(DEFAULT_ROOMMATES):
            call_command("seed_roommates", stdout=self.stdout)

        roommates = {r.name: r for r in Roommate.objects.filter(name__in=DEFAULT_ROOMMATES)}

        sample_chores = get_sample_chores()
        created_count = 0
        skipped_count = 0

        for item in sample_chores:
            if Chore.objects.filter(title=item["title"]).exists():
                skipped_count += 1
                self.stdout.write(f"Chore already exists: {item['title']}")
            else:
                chore = Chore.objects.create(
                    title=item["title"],
                    description=item["description"],
                    assigned_by=roommates[item["assigned_by"]],
                    assigned_to=roommates[item["assigned_to"]],
                    due_date=item["due_date"],
                    is_completed=item["is_completed"],
                    completed_at=item["completed_at"],
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created chore: {chore.title}")
                )

        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully seeded {created_count} chore(s)."
                )
            )
        else:
            self.stdout.write(
                "All sample chores already exist. No new records created."
            )
