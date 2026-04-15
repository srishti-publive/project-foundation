from django.core.management.base import BaseCommand

from api.models import Task


class Command(BaseCommand):
    help = "Reset failed tasks back to pending. Never touches running tasks."

    def add_arguments(self, parser):
        parser.add_argument(
            "--tool-name",
            dest="tool_name",
            default=None,
            help="Limit requeue to tasks with this tool_name.",
        )

    def handle(self, *args, **options):
        # Explicit status="failed" filter means running tasks are never touched,
        # even without an additional exclusion clause.
        qs = Task.objects.filter(status="failed")

        if options["tool_name"]:
            qs = qs.filter(tool_name=options["tool_name"])

        count = qs.count()

        if count == 0:
            qualifier = f" with tool_name={options['tool_name']!r}" if options["tool_name"] else ""
            self.stdout.write(f"Nothing to requeue — no failed tasks{qualifier}.")
            return

        updated = qs.update(
            status="pending",
            started_at=None,
            completed_at=None,
        )
        self.stdout.write(
            self.style.SUCCESS(f"Requeued {updated} failed task(s) back to pending.")
        )
