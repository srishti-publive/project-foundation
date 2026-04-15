from django.urls import path

from .views import (
    bulk_create_tasks,
    cancel_recurrence,
    claim_next_task,
    create_task,
    create_webhook_subscription,
    get_tasks,
    next_task,
    scheduled_tasks,
    task_children,
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
    path("tasks/<int:task_id>/children/", task_children),
    path("tasks/<int:task_id>/cancel-recurrence/", cancel_recurrence),

    # Webhook subscriptions
    path("webhooks/subscribe/", create_webhook_subscription),
]
