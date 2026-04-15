from django.core.management.base import BaseCommand
from django.db.models import Count

from api.models import Task

# Logical sort order — not alphabetical.
_STATUS_ORDER = {"pending": 0, "running": 1, "completed": 2, "failed": 3}
_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

_COL_STATUS = 12
_COL_PRIORITY = 10
_COL_COUNT = 7


class Command(BaseCommand):
    help = "Print a table of task counts grouped by status and priority."

    def handle(self, *args, **options):
        rows = list(
            Task.objects
            .values("status", "priority")
            .annotate(count=Count("task_id"))
        )

        if not rows:
            self.stdout.write("No tasks found.")
            return

        rows.sort(
            key=lambda r: (
                _STATUS_ORDER.get(r["status"], 99),
                _PRIORITY_ORDER.get(r["priority"], 99),
            )
        )

        divider = "-" * (_COL_STATUS + _COL_PRIORITY + _COL_COUNT + 4)

        self.stdout.write(
            f"{'Status':<{_COL_STATUS}}  {'Priority':<{_COL_PRIORITY}}  {'Count':>{_COL_COUNT}}"
        )
        self.stdout.write(divider)

        total = 0
        for row in rows:
            self.stdout.write(
                f"{row['status']:<{_COL_STATUS}}  "
                f"{row['priority']:<{_COL_PRIORITY}}  "
                f"{row['count']:>{_COL_COUNT}}"
            )
            total += row["count"]

        self.stdout.write(divider)
        self.stdout.write(
            f"{'Total':<{_COL_STATUS + _COL_PRIORITY + 2}}  {total:>{_COL_COUNT}}"
        )
