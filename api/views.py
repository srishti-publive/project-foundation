from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .hooks import notify
from .models import Task
from .queue import claim_task, get_next_task
from .serializers import TaskSerializer, WebhookSubscriptionSerializer
from .webhooks import validate_url


# GET all tasks
@api_view(["GET"])
def get_tasks(request):
    # Renamed from `status` to avoid shadowing `rest_framework.status`.
    status_filter = request.query_params.get("status")

    if status_filter:
        tasks = Task.objects.filter(status=status_filter)
    else:
        tasks = Task.objects.all()

    serializer = TaskSerializer(tasks, many=True)
    return Response(serializer.data)


# CREATE task (add to database)
@api_view(["POST"])
def create_task(request):
    serializer = TaskSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # Bug fix: validation errors must return 400, not the default 200.
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PATCH"])
def update_task_status(request, task_id):
    task = get_object_or_404(Task, task_id=task_id)

    new_status = request.data.get("status")

    if new_status not in dict(Task.STATUS_CHOICES):
        return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

    old_status = task.status
    task.status = new_status
    if new_status == "running" and task.started_at is None:
        task.started_at = timezone.now()
    elif new_status in ("completed", "failed"):
        task.completed_at = timezone.now()
    task.save()

    notify(old_status, new_status, task)

    serializer = TaskSerializer(task)
    return Response(serializer.data)


@api_view(["GET"])
def next_task(request):
    """
    Return the single highest-priority pending task that is ready to run.

    Delegates entirely to get_next_task() in queue.py so the ordering
    and scheduling logic stays in one place.
    """
    task = get_next_task()
    if task is None:
        # Return 200 with an explicit null body; 204 with a body is unreliable
        # because many HTTP clients discard bodies on 204 responses.
        return Response({"detail": "No claimable tasks.", "task": None})
    return Response(TaskSerializer(task).data)


@api_view(["POST"])
def claim_next_task(request, task_id):
    """
    Atomically claim a pending task (pending → running) using SELECT FOR UPDATE.

    Returns 200 with the serialized task on success, or 409 if the task is no
    longer claimable (already claimed, completed, or does not exist).
    """
    task = claim_task(task_id)
    if task is None:
        return Response(
            {"error": "Task is not claimable (already claimed, completed, or missing)."},
            status=status.HTTP_409_CONFLICT,
        )

    notify("pending", "running", task)

    return Response(TaskSerializer(task).data)


@api_view(["POST"])
def create_webhook_subscription(request):
    """
    Register a URL to receive signed webhook POSTs for a given user_id.

    The ``secret`` is returned **once** in this response and never again.
    Store it immediately — it is needed to verify ``X-Webhook-Signature``
    on incoming deliveries.
    """
    serializer = WebhookSubscriptionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    url = serializer.validated_data["url"]
    error = validate_url(url)
    if error:
        return Response({"url": [error]}, status=status.HTTP_400_BAD_REQUEST)

    sub = serializer.save()

    return Response(
        {
            "id": sub.id,
            "user_id": sub.user_id,
            "url": sub.url,
            "secret": sub.secret,
            "created_at": sub.created_at,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def task_children(request, task_id):
    """
    List all direct recurrence children of a task.

    Children are tasks whose recurrence_parent_id matches task_id.  If the
    parent task does not exist, returns 404.
    """
    get_object_or_404(Task, task_id=task_id)
    children = Task.objects.filter(recurrence_parent_id=task_id).order_by("scheduled_at")
    return Response(TaskSerializer(children, many=True).data)


@api_view(["POST"])
def cancel_recurrence(request, task_id):
    """
    Stop future recurrence spawns for a task.

    Sets max_recurrences = recurrence_count, which makes the spawn guard
    evaluate ``recurrence_count >= max_recurrences`` as True on this task,
    preventing any further children.

    Call this on the most recent pending child in the chain to stop the
    chain cleanly after it runs.
    """
    task = get_object_or_404(Task, task_id=task_id)
    task.max_recurrences = task.recurrence_count
    task.save(update_fields=["max_recurrences"])
    return Response(TaskSerializer(task).data)


@api_view(["POST"])
def bulk_create_tasks(request):
    """
    Bulk-insert an array of tasks in a single DB round-trip.

    Validates each item individually so callers get per-item error detail.
    All items must be valid — the endpoint is all-or-nothing.
    """
    if not isinstance(request.data, list):
        return Response(
            {"detail": "Expected a JSON array of tasks."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not request.data:
        return Response(
            {"detail": "Payload must not be empty."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializers = [TaskSerializer(data=item) for item in request.data]

    # Validate all items before writing anything.
    errors = {}
    for i, s in enumerate(serializers):
        if not s.is_valid():
            errors[i] = s.errors
    if errors:
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    instances = Task.objects.bulk_create(
        [Task(**s.validated_data) for s in serializers]
    )

    return Response(
        TaskSerializer(instances, many=True).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def scheduled_tasks(request):
    """
    Return all pending tasks whose scheduled_at is in the future,
    ordered by scheduled_at ascending (soonest first).
    """
    now = timezone.now()
    tasks = (
        Task.objects.filter(status="pending", scheduled_at__gt=now)
        .order_by("scheduled_at")
    )
    return Response(TaskSerializer(tasks, many=True).data)
