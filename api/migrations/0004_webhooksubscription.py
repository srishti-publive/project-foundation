from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0003_task_priority_scheduled_at_started_at_completed_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="WebhookSubscription",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("user_id", models.IntegerField(db_index=True)),
                ("url", models.URLField(max_length=2000)),
                ("secret", models.CharField(editable=False, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
