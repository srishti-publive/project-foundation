from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from api.models import Task


class Command(BaseCommand):
    help = "Mark all pending tasks as failed with a reason string."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reason",
            required=True,
            help="Human-readable explanation stored in each task's output_data.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be affected without writing anything.",
        )

    def handle(self, *args, **options):
        reason = options["reason"]
        dry_run = options["dry_run"]

        pending = Task.objects.filter(status="pending")
        count = pending.count()

        if count == 0:
            self.stdout.write("Nothing to drain — no pending tasks.")
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[dry-run] Would drain {count} pending task(s):"
                )
            )
            for task in pending.order_by("task_id"):
                self.stdout.write(
                    f"  #{task.task_id}  {task.name!r}  "
                    f"(priority={task.priority}, tool={task.tool_name})"
                )
            return

        updated = pending.update(
            status="failed",
            completed_at=timezone.now(),
            output_data=f"Drained: {reason}",
        )
        self.stdout.write(
            self.style.SUCCESS(f"Drained {updated} pending task(s) as failed.")
        )
