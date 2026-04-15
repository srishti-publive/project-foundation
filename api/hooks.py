"""
In-process hook registry for task status transitions.

Usage::

    from api.hooks import on_transition

    @on_transition("pending", "running")
    def log_task_started(task):
        print(f"Task {task.task_id} is now running")

Hooks are called synchronously in the request thread.  If a hook raises,
the exception is caught, logged, and execution continues — hooks must never
crash the calling view.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Callable

logger = logging.getLogger(__name__)

# (from_status, to_status) → ordered list of callables
_registry: dict[tuple[str, str], list[Callable]] = defaultdict(list)


def on_transition(from_status: str, to_status: str) -> Callable:
    """
    Decorator: register *fn* to be called whenever a task moves from
    *from_status* to *to_status*.

    The decorated function receives the (already-saved) Task instance as
    its only argument.
    """
    def decorator(fn: Callable) -> Callable:
        _registry[(from_status, to_status)].append(fn)
        return fn
    return decorator


def fire(from_status: str, to_status: str, task) -> None:
    """
    Call every in-process hook registered for (from_status → to_status).

    Exceptions are caught per-hook, logged, and suppressed so that a
    misbehaving hook never bubbles up into the HTTP response.
    """
    for fn in _registry.get((from_status, to_status), []):
        try:
            fn(task)
        except Exception:
            logger.exception(
                "Hook %r raised an exception for task %s (%s → %s) — skipping",
                fn.__qualname__,
                task.task_id,
                from_status,
                to_status,
            )


def notify(from_status: str, to_status: str, task) -> None:
    """
    Unified entry-point called by views after every status transition.

    1. Fires all registered in-process hooks synchronously.
    2. Dispatches outbound webhooks in background threads (non-blocking).
    """
    fire(from_status, to_status, task)

    # Deferred import avoids a circular dependency at module load time
    # (webhooks → models/serializers; hooks imports nothing from api at top level).
    from .webhooks import dispatch  # noqa: PLC0415
    dispatch(from_status, to_status, task)
