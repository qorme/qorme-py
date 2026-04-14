from datetime import datetime, timedelta, timezone

_MICROSECOND = timedelta(microseconds=1)


def utcnow() -> datetime:
    """Get the current UTC datetime."""
    return datetime.now(tz=timezone.utc)


def microseconds_since(start: datetime) -> int:
    """Get the number of microseconds since the given start datetime."""
    return int((utcnow() - start) / _MICROSECOND)
