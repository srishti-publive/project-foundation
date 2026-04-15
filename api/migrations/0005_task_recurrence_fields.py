import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0004_webhooksubscription"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="recurrence_rule",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="task",
            name="recurrence_parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="children",
                to="api.task",
            ),
        ),
        migrations.AddField(
            model_name="task",
            name="max_recurrences",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="task",
            name="recurrence_count",
            field=models.IntegerField(default=0),
        ),
    ]
