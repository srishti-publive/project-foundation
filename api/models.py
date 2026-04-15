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

    # --- Recurrence fields ---------------------------------------------------
    # A cron expression ("*/5 * * * *") or ISO 8601 interval ("R/PT1H").
    # Null means the task does not recur.
    recurrence_rule = models.CharField(max_length=200, blank=True, null=True)

    # Points to the task that spawned this one.  SET_NULL means children
    # become orphans if the parent is deleted — they still run normally.
    recurrence_parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )

    # Maximum number of child tasks to spawn (null = unlimited).
    # 0 is treated the same as having no rule — no children are ever created.
    max_recurrences = models.IntegerField(null=True, blank=True)

    # How many ancestors this task has in its recurrence chain.
    # The root task starts at 0; each spawned child is parent.recurrence_count + 1.
    recurrence_count = models.IntegerField(default=0)

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