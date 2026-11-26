"""How clock times are shown: 24-hour (18:30) or 12-hour (6:30 PM). Stored values are always 24-hour."""

from __future__ import annotations

from datetime import datetime, time

_hour24 = True


def hour24() -> bool:
    return _hour24


def set_hour24(enabled: bool) -> None:
    global _hour24
    _hour24 = enabled


def clock(moment: time | datetime, *, short: bool = False) -> str:
    """`short` drops ":00" on the hour in 12-hour mode (10 AM), for tight spots like month cells."""
    if _hour24:
        return f"{moment:%H:%M}"
    minutes = "" if short and moment.minute == 0 else f":{moment:%M}"
    return f"{moment.hour % 12 or 12}{minutes} {'AM' if moment.hour < 12 else 'PM'}"


def hour_label(hour: int) -> str:
    """Axis label for a whole hour; 24 means the midnight at the end of the day."""
    if _hour24:
        return f"{hour % 24:02d}:00"
    hour %= 24
    return f"{hour % 12 or 12} {'AM' if hour < 12 else 'PM'}"
