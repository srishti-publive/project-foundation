import secrets

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


class WebhookSubscription(models.Model):
    """
    Maps a user_id to a URL that should receive signed POST payloads
    whenever one of that user's tasks changes status.

    The ``secret`` is auto-generated on first save (64-char hex = 256-bit
    entropy) and is only returned to the caller at creation time.
    """

    user_id = models.IntegerField(db_index=True)
    url = models.URLField(max_length=2000)
    # 64 hex chars = 32 random bytes = 256-bit secret; never editable via API.
    secret = models.CharField(max_length=64, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.secret:
            self.secret = secrets.token_hex(32)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"WebhookSubscription(user_id={self.user_id}, url={self.url})"