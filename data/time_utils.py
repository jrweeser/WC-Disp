from __future__ import annotations

from datetime import datetime, timezone


def utc_iso_to_local_naive(timestamp: str) -> datetime | None:
    """Convert an ISO-8601 UTC timestamp to naive local time."""
    if not timestamp:
        return None
    normalized = timestamp.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone().replace(tzinfo=None)


def local_now() -> datetime:
    return datetime.now()
