from django.core.management.base import BaseCommand

from chores.models import Roommate

DEFAULT_ROOMMATES = ["Alice", "Bob", "Charlie"]


class Command(BaseCommand):
    help = "Seed initial default roommates into the database."

    def handle(self, *args, **options):
        created_count = 0
        for name in DEFAULT_ROOMMATES:
            roommate, created = Roommate.objects.get_or_create(name=name)
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created roommate: {roommate.name}")
                )
            else:
                self.stdout.write(f"Roommate already exists: {roommate.name}")

        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully seeded {created_count} roommate(s)."
                )
            )
        else:
            self.stdout.write(
                "All default roommates already exist. No new records created."
            )
