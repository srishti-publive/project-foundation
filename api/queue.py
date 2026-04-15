from django.db import transaction
from django.db.models import Case, IntegerField, Q, Value, When
from django.utils import timezone

from .models import Task

# Maps priority label → sort rank (lower = runs first)
_PRIORITY_RANK = {
    "high": 1,
    "medium": 2,
    "low": 3,
}


def get_next_task() -> Task | None:
    """
    Return the highest-priority pending task that is ready to run, or None.

    Eligibility rules:
      - status must be 'pending'
      - scheduled_at is either unset or not in the future

    Ordering: priority high→low, then created_at oldest→newest as a tiebreaker.
    """
    now = timezone.now()

    priority_rank = Case(
        When(priority="high", then=Value(_PRIORITY_RANK["high"])),
        When(priority="medium", then=Value(_PRIORITY_RANK["medium"])),
        When(priority="low", then=Value(_PRIORITY_RANK["low"])),
        output_field=IntegerField(),
    )

    return (
        Task.objects.filter(
            status="pending",
        )
        .filter(Q(scheduled_at__isnull=True) | Q(scheduled_at__lte=now))
        .annotate(priority_rank=priority_rank)
        .order_by("priority_rank", "created_at")
        .first()
    )


def claim_task(task_id: int) -> Task | None:
    """
    Atomically transition a task from pending → running.

    Uses SELECT FOR UPDATE to serialise concurrent workers: only one caller
    will see status='pending' after acquiring the row lock; all others get
    None and must move on.

    Returns the updated Task on success, or None if the task no longer
    qualifies (already claimed, completed, or does not exist).
    """
    with transaction.atomic():
        try:
            task = (
                Task.objects.select_for_update()
                .get(task_id=task_id, status="pending")
            )
        except Task.DoesNotExist:
            # Either the task_id is wrong or another worker already claimed it.
            return None

        task.status = "running"
        task.started_at = timezone.now()
        task.save(update_fields=["status", "started_at"])

    return task
