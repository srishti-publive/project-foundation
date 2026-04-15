from __future__ import annotations

import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from api.models import Task
from api.recurrence import compute_next

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Dispatch due scheduled tasks and spawn recurrence children"

    def handle(self, *args, **options):
        now = timezone.now()
        due = list(Task.objects.filter(status="pending", scheduled_at__lte=now))

        if not due:
            self.stdout.write("No scheduled tasks due.")
            return

        dispatched = 0
        spawned = 0

        for task in due:
            task.status = "running"
            task.started_at = now
            task.save(update_fields=["status", "started_at"])
            dispatched += 1

            if _should_spawn(task):
                if _spawn_next(task, now):
                    spawned += 1

        msg = f"Dispatched {dispatched} task(s)"
        if spawned:
            msg += f", spawned {spawned} recurrence child(ren)"
        self.stdout.write(msg)


# ---------------------------------------------------------------------------
# Recurrence helpers
# ---------------------------------------------------------------------------

def _should_spawn(task: Task) -> bool:
    """
    Return True if *task* should have a child spawned after it runs.

    Rules:
    - No recurrence_rule → never spawn.
    - max_recurrences == 0 → never spawn (same as no rule).
    - max_recurrences is not None and recurrence_count >= max_recurrences
      → chain has reached its limit.
    """
    if not task.recurrence_rule:
        return False
    if task.max_recurrences == 0:
        return False
    if task.max_recurrences is not None and task.recurrence_count >= task.max_recurrences:
        return False
    return True


def _spawn_next(task: Task, now) -> bool:
    """
    Compute the next scheduled_at and create a child task.

    Returns True if a child was created, False if skipped or the next time
    could not be computed.

    Idempotency: if a pending child for the same parent and scheduled_at
    already exists (e.g. the command ran twice), the spawn is skipped.
    """
    from_dt = task.scheduled_at or now
    next_scheduled = compute_next(task.recurrence_rule, from_dt)

    if next_scheduled is None:
        logger.warning(
            "Task %s: could not compute next run from rule %r — skipping spawn",
            task.task_id,
            task.recurrence_rule,
        )
        return False

    # Duplicate guard: only one pending child per (parent, scheduled_at).
    if Task.objects.filter(
        recurrence_parent=task,
        status="pending",
        scheduled_at=next_scheduled,
    ).exists():
        logger.debug(
            "Task %s: pending child already exists for %s — skipping duplicate spawn",
            task.task_id,
            next_scheduled,
        )
        return False

    Task.objects.create(
        name=task.name,
        tool_name=task.tool_name,
        user_id=task.user_id,
        input_data=task.input_data,
        priority=task.priority,
        status="pending",
        scheduled_at=next_scheduled,
        recurrence_rule=task.recurrence_rule,
        recurrence_parent=task,
        max_recurrences=task.max_recurrences,
        # Each child records its generation so cancel-recurrence and
        # max_recurrences checks are self-contained on the child.
        recurrence_count=task.recurrence_count + 1,
    )
    return True
