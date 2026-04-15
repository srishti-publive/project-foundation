from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Task
from .queue import get_next_task
from .serializers import TaskSerializer

# GET all tasks
@api_view(["GET"])
def get_tasks(request):
    status = request.query_params.get("status")

    if status:
        tasks = Task.objects.filter(status=status)
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
        return Response(serializer.data)

    return Response(serializer.errors)



@api_view(["PATCH"])
def update_task_status(request, task_id):
    task = get_object_or_404(Task, task_id=task_id)

    new_status = request.data.get("status")

    if new_status not in dict(Task.STATUS_CHOICES):
        return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

    task.status = new_status
    from django.utils import timezone
    if new_status == 'running':
        task.started_at = timezone.now()
    elif new_status in ('completed', 'failed'):
        task.completed_at = timezone.now()
    task.save()

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
        return Response({"detail": "No claimable tasks."}, status=status.HTTP_204_NO_CONTENT)
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