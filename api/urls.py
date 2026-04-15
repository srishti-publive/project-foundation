from django.urls import path

from .views import (
    bulk_create_tasks,
    claim_next_task,
    create_task,
    get_tasks,
    next_task,
    scheduled_tasks,
    update_task_status,
)

urlpatterns = [
    # Collection
    path("tasks/", get_tasks),
    path("tasks/create/", create_task),
    path("tasks/bulk-create/", bulk_create_tasks),

    # Queue helpers — static segments must come before <int:task_id>
    path("tasks/next/", next_task),
    path("tasks/scheduled/", scheduled_tasks),

    # Single-task actions
    path("tasks/<int:task_id>/status/", update_task_status),
    path("tasks/<int:task_id>/claim/", claim_next_task),
]
