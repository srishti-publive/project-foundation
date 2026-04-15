"""
Recurrence rule validation and next-scheduled-at computation.

Supported formats
-----------------
Cron (5 or 6 fields):
    ``*/5 * * * *``      every 5 minutes
    ``0 9 * * 1``        every Monday at 09:00

ISO 8601 recurrence intervals:
    ``R/PT1H``           every hour, indefinitely
    ``R5/PT30M``         every 30 minutes, max 5 times (max tracked externally)
    ``R/P1D``            every day
    ``R/P1W``            every week

The repetition count prefix (``R`` or ``Rn``) is accepted for syntactic
validity but is not used here — max_recurrences on the Task model owns
that constraint.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta

from croniter import croniter

# ---------------------------------------------------------------------------
# ISO 8601 duration parsing
# ---------------------------------------------------------------------------

# Matches "R" or "R5" followed by "/" and a duration starting with "P"
_ISO_RECURRENCE_RE = re.compile(r"^R\d*/(P.+)$")

# Full ISO 8601 duration pattern — every component is optional but at least
# one must be present (enforced by the zero-length check in _parse_iso_duration).
_ISO_DURATION_RE = re.compile(
    r"^P"
    r"(?:(?P<years>\d+)Y)?"
    r"(?:(?P<months>\d+)M)?"
    r"(?:(?P<weeks>\d+)W)?"
    r"(?:(?P<days>\d+)D)?"
    r"(?:T"
    r"(?:(?P<hours>\d+)H)?"
    r"(?:(?P<minutes>\d+)M)?"
    r"(?:(?P<seconds>\d+)S)?"
    r")?$"
)


def _parse_iso_duration(duration_str: str) -> timedelta | None:
    """
    Convert an ISO 8601 duration string to a :class:`timedelta`.

    Years are approximated as 365 days; months as 30 days.
    Returns ``None`` if the string is syntactically invalid or resolves to
    zero length (a zero-length interval would cause an infinite tight loop).
    """
    m = _ISO_DURATION_RE.match(duration_str)
    if not m:
        return None

    g = m.groupdict(default="0")
    total_days = (
        int(g["days"])
        + int(g["years"]) * 365
        + int(g["months"]) * 30
    )
    delta = timedelta(
        weeks=int(g["weeks"]),
        days=total_days,
        hours=int(g["hours"]),
        minutes=int(g["minutes"]),
        seconds=int(g["seconds"]),
    )
    return delta if delta.total_seconds() > 0 else None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def is_valid_recurrence_rule(rule: str) -> bool:
    """
    Return ``True`` if *rule* is a valid cron expression or ISO 8601
    recurrence interval; ``False`` otherwise.
    """
    if not rule:
        return False

    iso_match = _ISO_RECURRENCE_RE.match(rule)
    if iso_match:
        return _parse_iso_duration(iso_match.group(1)) is not None

    return croniter.is_valid(rule)


def compute_next(rule: str, from_dt: datetime) -> datetime | None:
    """
    Return the next occurrence datetime after *from_dt* according to *rule*.

    Returns ``None`` if the rule is invalid or cannot produce a next time
    (should not happen for rules that already passed ``is_valid_recurrence_rule``,
    but callers should handle it defensively).
    """
    iso_match = _ISO_RECURRENCE_RE.match(rule)
    if iso_match:
        delta = _parse_iso_duration(iso_match.group(1))
        return (from_dt + delta) if delta is not None else None

    try:
        return croniter(rule, from_dt).get_next(datetime)
    except (ValueError, KeyError):
        return None
