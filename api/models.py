from django.db import models

from django.db import models

class Task(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
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

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.task_id} - {self.name}"