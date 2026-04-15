# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_task_input_data_task_output_data_task_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='priority',
            field=models.CharField(
                choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
                default='medium',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='task',
            name='scheduled_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='task',
            name='started_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='task',
            name='completed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
