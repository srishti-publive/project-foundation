from django.db import models


class Task(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    task_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    tool_name = models.CharField(max_length=200)
    user_id = models.IntegerField()

    input_data = models.TextField(blank=True, null=True)
    output_data = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="medium"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_at = models.DateTimeField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.task_id} - {self.name}"