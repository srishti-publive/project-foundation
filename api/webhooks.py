"""
Outbound webhook delivery for task status transitions.

Every WebhookSubscription row for the affected user_id receives a signed
POST in a daemon thread so delivery never blocks the HTTP response.

Payload shape::

    {
        "event": "task.status_changed",
        "from_status": "pending",
        "to_status": "running",
        "task": { ...TaskSerializer fields... }
    }

Signature::

    X-Webhook-Signature: sha256=<lowercase-hex-hmac-sha256-over-raw-body>

The receiver should recompute the signature using the secret shown at
subscription-creation time and compare with ``hmac.compare_digest``.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import threading
import time
from urllib.parse import urlparse

import requests as http_client
from django.conf import settings

logger = logging.getLogger(__name__)

_RETRYABLE_STATUSES = frozenset({500, 502, 503, 504})
_MAX_ATTEMPTS = 3
_DELIVERY_TIMEOUT = 10  # seconds per attempt


# ---------------------------------------------------------------------------
# URL validation (called at subscription-creation time in the view)
# ---------------------------------------------------------------------------

def validate_url(url: str) -> str | None:
    """
    Return an error message if *url* is not allowed, or ``None`` if it is.

    Allowed hosts are read from ``settings.WEBHOOK_ALLOWED_HOSTS`` (a list).
    An empty list means no host restrictions (permissive dev default).
    """
    allowed: list[str] = getattr(settings, "WEBHOOK_ALLOWED_HOSTS", [])
    if not allowed:
        return None  # no restriction configured
    hostname = urlparse(url).hostname
    if hostname not in allowed:
        return (
            f"Webhook URL host '{hostname}' is not permitted. "
            f"Allowed: {', '.join(allowed)}"
        )
    return None


# ---------------------------------------------------------------------------
# HMAC signing
# ---------------------------------------------------------------------------

def _sign(secret: str, body: bytes) -> str:
    """Return ``'sha256=<hex>'`` HMAC-SHA256 signature over *body*."""
    mac = hmac.new(secret.encode(), body, digestmod=hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


# ---------------------------------------------------------------------------
# Delivery (runs inside a daemon thread)
# ---------------------------------------------------------------------------

def _deliver(url: str, secret: str, payload: dict) -> None:
    """
    POST *payload* to *url*, retrying up to ``_MAX_ATTEMPTS`` times on 5xx
    with exponential back-off (1 s, 2 s).  All exceptions are caught and
    logged; nothing is re-raised because this function runs in a daemon thread.
    """
    try:
        body = json.dumps(payload, default=str).encode()
    except Exception:
        logger.exception("Failed to serialise webhook payload for %s — skipping", url)
        return

    signature = _sign(secret, body)
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
    }

    for attempt in range(_MAX_ATTEMPTS):
        try:
            resp = http_client.post(
                url, data=body, headers=headers, timeout=_DELIVERY_TIMEOUT
            )
        except http_client.RequestException as exc:
            logger.warning(
                "Webhook delivery to %s failed (attempt %d/%d): %s",
                url, attempt + 1, _MAX_ATTEMPTS, exc,
            )
            if attempt < _MAX_ATTEMPTS - 1:
                time.sleep(2 ** attempt)
            continue

        if resp.status_code not in _RETRYABLE_STATUSES:
            if resp.ok:
                logger.debug(
                    "Webhook delivered to %s (HTTP %s)", url, resp.status_code
                )
            else:
                logger.warning(
                    "Webhook to %s returned non-retryable HTTP %s",
                    url, resp.status_code,
                )
            return  # success or permanent failure — stop retrying

        logger.warning(
            "Webhook to %s returned HTTP %s (attempt %d/%d), retrying…",
            url, resp.status_code, attempt + 1, _MAX_ATTEMPTS,
        )
        if attempt < _MAX_ATTEMPTS - 1:
            time.sleep(2 ** attempt)

    logger.error(
        "Webhook to %s failed permanently after %d attempts", url, _MAX_ATTEMPTS
    )


# ---------------------------------------------------------------------------
# Dispatch (called from hooks.notify — runs in the request thread)
# ---------------------------------------------------------------------------

def dispatch(from_status: str, to_status: str, task) -> None:
    """
    Look up all WebhookSubscription rows for *task.user_id* and fire each
    one in a separate daemon thread so this call returns immediately.
    """
    # Import here to keep the module importable before Django is fully set up
    # and to avoid any circular-import issues.
    from .models import WebhookSubscription  # noqa: PLC0415
    from .serializers import TaskSerializer  # noqa: PLC0415

    try:
        subscriptions = list(
            WebhookSubscription.objects.filter(user_id=task.user_id)
        )
    except Exception:
        logger.exception(
            "Could not query WebhookSubscription for user_id=%s — skipping dispatch",
            task.user_id,
        )
        return

    if not subscriptions:
        return

    # Serialise once; all threads share the same read-only payload dict.
    payload = {
        "event": "task.status_changed",
        "from_status": from_status,
        "to_status": to_status,
        "task": dict(TaskSerializer(task).data),
    }

    for sub in subscriptions:
        thread = threading.Thread(
            target=_deliver,
            args=(sub.url, sub.secret, payload),
            daemon=True,
            name=f"webhook-{sub.pk}-{task.task_id}",
        )
        thread.start()
