from __future__ import annotations

from typing import Any


class TaskAPIError(Exception):
    """Base exception for all Task API errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        body: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class AlreadyClaimedError(TaskAPIError):
    """
    Raised when ``claim()`` gets a 409 response.

    The task is no longer claimable — it was already claimed, completed,
    or does not exist.
    """


class BulkCreateError(TaskAPIError):
    """
    Raised when ``bulk_create()`` fails server-side validation.

    Attributes
    ----------
    errors : dict[int, dict]
        Maps the zero-based index of each failing task to the field-level
        error dict returned by the API, e.g.::

            {2: {"name": ["This field is required."]}}
    """

    def __init__(
        self,
        errors: dict[int, dict],
        *,
        status_code: int = 400,
        body: Any = None,
    ) -> None:
        failing = ", ".join(str(i) for i in sorted(errors))
        super().__init__(
            f"Bulk create failed validation for task(s) at index: {failing}",
            status_code=status_code,
            body=body,
        )
        self.errors = errors


class ValidationError(TaskAPIError):
    """Raised when the API returns a 400 outside of ``bulk_create()``."""
