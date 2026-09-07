from django.db import models


class Roommate(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name


class Chore(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True, default="")
    assigned_by = models.ForeignKey(
        Roommate,
        on_delete=models.CASCADE,
        related_name="assigned_chores",
    )
    assigned_to = models.ForeignKey(
        Roommate,
        on_delete=models.CASCADE,
        related_name="my_chores",
    )
    due_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title
