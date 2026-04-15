"""
publive-sdk — Python client for the Publive Task API.

Quick start::

    from sdk.py import TaskClient, AlreadyClaimedError

    client = TaskClient()                          # default: http://localhost:8000/api

    # Create a task
    task = client.create("resize-image", "image_tool", user_id=42)

    # Claim it (pending → running)
    try:
        running = client.claim(task["task_id"])
    except AlreadyClaimedError:
        print("Someone else grabbed it first")

    # Mark done
    client.complete(task["task_id"])

    # Bulk-insert with per-item error detail
    from sdk.py import BulkCreateError
    try:
        client.bulk_create([
            {"name": "task-a", "tool_name": "t", "user_id": 1},
            {"name": "",       "tool_name": "t", "user_id": 1},  # bad
        ])
    except BulkCreateError as exc:
        print(exc.errors)   # {1: {"name": ["This field may not be blank."]}}
"""

from .client import TaskClient
from .exceptions import (
    AlreadyClaimedError,
    BulkCreateError,
    TaskAPIError,
    ValidationError,
)

__all__ = [
    "TaskClient",
    "TaskAPIError",
    "AlreadyClaimedError",
    "BulkCreateError",
    "ValidationError",
]
