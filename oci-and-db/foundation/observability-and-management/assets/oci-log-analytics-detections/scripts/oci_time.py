#!/usr/bin/env python3
"""Helpers for building OCI Log Analytics absolute time windows."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone


LOOKBACK_RE = re.compile(r"^(?P<value>\d+)(?P<unit>[smhdw])$", re.IGNORECASE)

UNIT_TO_KWARGS = {
    "s": "seconds",
    "m": "minutes",
    "h": "hours",
    "d": "days",
    "w": "weeks",
}


def parse_lookback(lookback: str) -> timedelta:
    """Parse a compact lookback like ``5m`` or ``7d`` into a timedelta."""
    if not lookback:
        raise ValueError("lookback must be non-empty")

    match = LOOKBACK_RE.fullmatch(lookback.strip())
    if not match:
        raise ValueError(f"unsupported lookback value: {lookback}")

    value = int(match.group("value"))
    unit = match.group("unit").lower()
    if value <= 0:
        raise ValueError(f"lookback must be positive: {lookback}")

    return timedelta(**{UNIT_TO_KWARGS[unit]: value})


def build_time_window(lookback: str, now: datetime | None = None) -> tuple[datetime, datetime]:
    """Return a UTC ``(start, end)`` tuple for an OCI absolute query window."""
    end = now or datetime.now(timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    else:
        end = end.astimezone(timezone.utc)

    start = end - parse_lookback(lookback)
    return start, end
