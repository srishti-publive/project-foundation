"""
TaskClient — thin HTTP wrapper around the Publive Task API.

Zero Django dependencies; requires only the ``requests`` library.
"""
from __future__ import annotations

import time
import warnings
from datetime import datetime, timezone
from typing import Any, NoReturn

import requests

from .exceptions import (
    AlreadyClaimedError,
    BulkCreateError,
    TaskAPIError,
    ValidationError,
)

# HTTP status codes that warrant a retry.
_RETRYABLE = frozenset({500, 502, 503, 504})
# Total attempts (first try + 2 retries).
_MAX_ATTEMPTS = 3


# ---------------------------------------------------------------------------
# Module-level helpers (not public)
# ---------------------------------------------------------------------------

def _safe_json(resp: requests.Response) -> Any:
    """Return parsed JSON body, or raw text if parsing fails."""
    try:
        return resp.json()
    except Exception:
        return resp.text


def _is_int_key(value: str) -> bool:
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False


def _raise_for_unexpected(resp: requests.Response) -> NoReturn:
    raise TaskAPIError(
        f"Unexpected HTTP {resp.status_code}",
        status_code=resp.status_code,
        body=_safe_json(resp),
    )


def _coerce_scheduled_at(value: Any, *, stacklevel: int = 3) -> str | None:
    """
    Convert *value* to an ISO-8601 string suitable for the API.

    - ``None`` → ``None`` (field omitted from payload)
    - A timezone-aware ``datetime`` → ``.isoformat()``
    - A **naive** ``datetime`` → warns, assumes UTC, then ``.isoformat()``
    - Anything else (e.g. an already-formatted string) → returned as-is and
      left for the server to validate.
    """
    if value is None:
        return None
    if not isinstance(value, datetime):
        return value
    if value.tzinfo is None:
        warnings.warn(
            "scheduled_at has no timezone info; assuming UTC. "
            "Pass a timezone-aware datetime (e.g. datetime(..., tzinfo=timezone.utc)) "
            "to silence this warning.",
            UserWarning,
            stacklevel=stacklevel,
        )
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class TaskClient:
    """
    HTTP client for the Publive Task API.

    Parameters
    ----------
    base_url:
        Root URL of the API, e.g. ``http://localhost:8000/api``.
        Trailing slash is optional.
    timeout:
        Per-request timeout in seconds (default 30).
    session:
        Optional pre-configured ``requests.Session``.  Useful for injecting
        auth headers or a mock transport in tests.

    Example
    -------
    >>> client = TaskClient()
    >>> task = client.create("resize-image", "image_tool", user_id=42)
    >>> client.claim(task["task_id"])
    >>> client.complete(task["task_id"])
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000/api",
        timeout: float = 30,
        session: requests.Session | None = None,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout
        self._session = session or requests.Session()

    # ------------------------------------------------------------------
    # Internal request machinery
    # ------------------------------------------------------------------

    def _url(self, path: str) -> str:
        return f"{self._base}/{path.lstrip('/')}"

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        """
        Send *method* request to *path*, retrying on 5xx up to ``_MAX_ATTEMPTS``
        times with exponential back-off (1 s, 2 s between retries).

        Raises ``TaskAPIError`` on network failure or after all retries
        are exhausted with a 5xx response.
        """
        url = self._url(path)
        kwargs.setdefault("timeout", self._timeout)

        last_error: TaskAPIError | None = None

        for attempt in range(_MAX_ATTEMPTS):
            try:
                resp = self._session.request(method, url, **kwargs)
            except requests.RequestException as exc:
                # Network-level failure — not retried (nothing came back).
                raise TaskAPIError(str(exc)) from exc

            if resp.status_code not in _RETRYABLE:
                return resp

            # Server error: record and back off before retrying.
            last_error = TaskAPIError(
                f"Server error {resp.status_code} (attempt {attempt + 1}/{_MAX_ATTEMPTS})",
                status_code=resp.status_code,
                body=_safe_json(resp),
            )
            if attempt < _MAX_ATTEMPTS - 1:
                time.sleep(2 ** attempt)  # 1 s, then 2 s

        # All attempts exhausted with 5xx.
        assert last_error is not None
        raise last_error

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(
        self,
        name: str,
        tool_name: str,
        user_id: int,
        *,
        priority: str = "medium",
        input_data: str | None = None,
        scheduled_at: datetime | str | None = None,
    ) -> dict:
        """
        Create a single task.

        Parameters
        ----------
        name:
            Human-readable task name.
        tool_name:
            Identifier for the tool that will process this task.
        user_id:
            ID of the user who owns the task.
        priority:
            One of ``"low"``, ``"medium"`` (default), or ``"high"``.
        input_data:
            Optional free-form input payload (stored as text).
        scheduled_at:
            When to schedule the task.  A *naive* ``datetime`` triggers a
            ``UserWarning`` and is converted to UTC automatically.

        Returns
        -------
        dict
            The created task as returned by the API.

        Raises
        ------
        ValidationError
            If the server returns 400.
        TaskAPIError
            On network failure or exhausted 5xx retries.
        """
        payload: dict[str, Any] = {
            "name": name,
            "tool_name": tool_name,
            "user_id": user_id,
            "priority": priority,
        }
        if input_data is not None:
            payload["input_data"] = input_data
        coerced = _coerce_scheduled_at(scheduled_at, stacklevel=3)
        if coerced is not None:
            payload["scheduled_at"] = coerced

        resp = self._request("POST", "/tasks/create/", json=payload)
        if resp.status_code == 201:
            return resp.json()  # type: ignore[no-any-return]
        if resp.status_code == 400:
            raise ValidationError(
                f"Validation failed: {resp.text}",
                status_code=400,
                body=_safe_json(resp),
            )
        _raise_for_unexpected(resp)

    def claim(self, task_id: int) -> dict:
        """
        Atomically claim a task, transitioning it from ``pending`` to
        ``running``.

        Parameters
        ----------
        task_id:
            Primary key of the task to claim.

        Returns
        -------
        dict
            The updated task.

        Raises
        ------
        AlreadyClaimedError
            If the server returns 409 — the task is already claimed,
            completed, or does not exist.
        TaskAPIError
            On network failure or exhausted 5xx retries.
        """
        resp = self._request("POST", f"/tasks/{task_id}/claim/")
        if resp.status_code == 200:
            return resp.json()  # type: ignore[no-any-return]
        if resp.status_code == 409:
            raise AlreadyClaimedError(
                f"Task {task_id} is not claimable "
                "(already claimed, completed, or does not exist).",
                status_code=409,
                body=_safe_json(resp),
            )
        _raise_for_unexpected(resp)

    def complete(self, task_id: int) -> dict:
        """
        Mark a task as ``completed``.

        Parameters
        ----------
        task_id:
            Primary key of the task to complete.

        Returns
        -------
        dict
            The updated task.

        Raises
        ------
        ValidationError
            If the server returns 400 (e.g. invalid status transition).
        TaskAPIError
            On network failure or exhausted 5xx retries.
        """
        resp = self._request(
            "PATCH",
            f"/tasks/{task_id}/status/",
            json={"status": "completed"},
        )
        if resp.status_code == 200:
            return resp.json()  # type: ignore[no-any-return]
        if resp.status_code == 400:
            raise ValidationError(
                f"Validation failed: {resp.text}",
                status_code=400,
                body=_safe_json(resp),
            )
        _raise_for_unexpected(resp)

    def bulk_create(self, tasks: list[dict]) -> list[dict]:
        """
        Create multiple tasks in a single round-trip.

        Each item in *tasks* accepts the same fields as ``create()``.  The
        ``scheduled_at`` field in any item is coerced from a naive
        ``datetime`` to UTC with a ``UserWarning``, just like in
        ``create()``.

        The endpoint is **all-or-nothing**: if any item fails validation the
        entire batch is rejected and ``BulkCreateError`` is raised.

        Parameters
        ----------
        tasks:
            List of task dicts.

        Returns
        -------
        list[dict]
            The created tasks in insertion order.

        Raises
        ------
        BulkCreateError
            If the server returns 400 with a per-item error map.
            ``error.errors`` maps the failing zero-based index to its
            field errors, e.g. ``{2: {"name": ["This field is required."]}}``.
        ValidationError
            If the server returns 400 with a non-per-item error body
            (e.g. empty payload).
        TaskAPIError
            On network failure or exhausted 5xx retries.
        """
        normalized: list[dict] = []
        for i, task in enumerate(tasks):
            item = dict(task)
            if "scheduled_at" in item and isinstance(item["scheduled_at"], datetime):
                if item["scheduled_at"].tzinfo is None:
                    warnings.warn(
                        f"tasks[{i}].scheduled_at has no timezone info; assuming UTC. "
                        "Pass a timezone-aware datetime to silence this warning.",
                        UserWarning,
                        stacklevel=2,
                    )
                    item["scheduled_at"] = item["scheduled_at"].replace(
                        tzinfo=timezone.utc
                    ).isoformat()
                else:
                    item["scheduled_at"] = item["scheduled_at"].isoformat()
            normalized.append(item)

        resp = self._request("POST", "/tasks/bulk-create/", json=normalized)
        if resp.status_code == 201:
            return resp.json()  # type: ignore[no-any-return]
        if resp.status_code == 400:
            body = _safe_json(resp)
            # The API returns a dict keyed by stringified indices when items fail.
            if isinstance(body, dict):
                int_keyed = {
                    int(k): v for k, v in body.items() if _is_int_key(k)
                }
                if int_keyed:
                    raise BulkCreateError(
                        int_keyed,
                        status_code=400,
                        body=body,
                    )
            raise ValidationError(
                f"Validation failed: {resp.text}",
                status_code=400,
                body=body,
            )
        _raise_for_unexpected(resp)
