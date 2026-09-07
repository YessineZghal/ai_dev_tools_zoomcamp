"""Create the next occurrence for any recurring chore that has none pending.

Occurrences are normally spawned when an assignment is completed or skipped
(``Assignment.spawn_next``). This command is the safety net — run it from cron
so a recurring chore that was never closed out still gets its next occurrence.

    uv run python manage.py generate_recurring
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from chores.models import Assignment, Chore


class Command(BaseCommand):
    help = "Create the next assignment for recurring chores with nothing pending."

    def handle(self, *args, **options):
        today = timezone.localdate()
        created = 0

        recurring = (
            Chore.objects.filter(is_active=True)
            .exclude(recurrence=Chore.Recurrence.NONE)
            .select_related("household")
        )
        for chore in recurring:
            if chore.assignments.filter(status=Assignment.Status.PENDING).exists():
                continue
            last = chore.assignments.order_by("-due_date", "-id").first()
            if last is not None:
                due = max(chore.next_due(last.due_date), today)
                assignee = chore.next_assignee(last.assignee)
            else:
                members = list(chore.household.members)
                if not members:
                    continue
                due, assignee = today, members[0]
            Assignment.objects.create(chore=chore, assignee=assignee, due_date=due)
            created += 1

        self.stdout.write(
            self.style.SUCCESS(f"generate_recurring: created {created} assignment(s).")
        )
