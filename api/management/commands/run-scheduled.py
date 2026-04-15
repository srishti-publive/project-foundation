from django.core.management.base import BaseCommand
from django.utils import timezone

from api.models import Task


class Command(BaseCommand):
    help = "Dispatch tasks whose scheduled_at has passed"

    def handle(self, *args, **options):
        now = timezone.now()
        due = Task.objects.filter(status="pending", scheduled_at__lte=now)

        # Bug fix: previously this only updated `status` and left `started_at`
        # null. Workers and auditors need the real start timestamp.
        count = due.update(status="running", started_at=now)

        self.stdout.write(f"Dispatched {count} scheduled tasks")
