from django.core.management.base import BaseCommand

from api.models import Task

# Idempotency key: "name".  Re-running this command will skip any task whose
# name already exists in the database and only insert the missing ones.
#
# The "seed:" prefix makes these easy to distinguish from real tasks and
# prevents accidental name collisions in shared environments.
SEED_TASKS = [
    {
        "name": "seed: resize-image-1",
        "tool_name": "image_tool",
        "user_id": 1,
        "priority": "high",
        "input_data": '{"url": "https://example.com/img1.png"}',
    },
    {
        "name": "seed: resize-image-2",
        "tool_name": "image_tool",
        "user_id": 2,
        "priority": "medium",
    },
    {
        "name": "seed: classify-image",
        "tool_name": "image_tool",
        "user_id": 3,
        "priority": "high",
    },
    {
        "name": "seed: summarise-doc-1",
        "tool_name": "text_tool",
        "user_id": 1,
        "priority": "medium",
        "input_data": '{"doc_id": 42}',
    },
    {
        "name": "seed: summarise-doc-2",
        "tool_name": "text_tool",
        "user_id": 3,
        "priority": "low",
    },
    {
        "name": "seed: generate-report",
        "tool_name": "text_tool",
        "user_id": 2,
        "priority": "low",
    },
    {
        "name": "seed: run-etl-daily",
        "tool_name": "data_tool",
        "user_id": 1,
        "priority": "high",
    },
    {
        "name": "seed: run-etl-weekly",
        "tool_name": "data_tool",
        "user_id": 1,
        "priority": "low",
    },
    {
        "name": "seed: ingest-csv",
        "tool_name": "data_tool",
        "user_id": 3,
        "priority": "medium",
    },
    {
        "name": "seed: analyse-sentiment",
        "tool_name": "analysis_tool",
        "user_id": 2,
        "priority": "medium",
        "input_data": '{"text": "sample text for sentiment analysis"}',
    },
]


class Command(BaseCommand):
    help = "Seed the database with sample tasks (idempotent — safe to run multiple times)."

    def handle(self, *args, **options):
        created_count = 0

        for data in SEED_TASKS:
            name = data["name"]
            defaults = {k: v for k, v in data.items() if k != "name"}
            _, created = Task.objects.get_or_create(name=name, defaults=defaults)
            if created:
                created_count += 1

        skipped = len(SEED_TASKS) - created_count

        if created_count == 0:
            self.stdout.write(
                f"All {skipped} seed task(s) already exist — nothing to do."
            )
            return

        msg = f"Created {created_count} seed task(s)."
        if skipped:
            msg += f" Skipped {skipped} that already existed."
        self.stdout.write(self.style.SUCCESS(msg))
