"""Checks the store for due reminders while the app runs (window open, minimised or in the tray)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from PySide6.QtCore import QObject, Qt, QTimer, Signal

from origami.store import Reminder, Store
from origami.timefmt import clock as show_time

MAX_WAIT_MS = 60_000
LEAD_MS = 250  # check just after the minute turns, since reminder times are whole minutes


def next_check_ms(now: datetime) -> int:
    """Milliseconds until just past the next whole minute."""
    into_minute = now.second * 1000 + now.microsecond // 1000
    return min(MAX_WAIT_MS, 60_000 - into_minute + LEAD_MS)


class ReminderService(QObject):
    fired = Signal(object)  # Reminder

    def __init__(self, store: Store, clock: Callable[[], datetime] = datetime.now) -> None:
        super().__init__()
        self._store, self._clock = store, clock
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.timeout.connect(self._tick)

    def start(self) -> None:
        self._timer.start(1500)

    def stop(self) -> None:
        self._timer.stop()

    def _tick(self) -> None:
        try:
            self.check()
        finally:
            self._timer.start(next_check_ms(self._clock()))

    def check(self) -> list[Reminder]:
        due = self._store.due_reminders(self._clock())
        for reminder in due:
            self.fired.emit(reminder)
        return due


def describe(reminder: Reminder, store: Store) -> tuple[str, str]:
    """(notification title, body) for a reminder."""
    if reminder.kind == "task":
        return reminder.title, "Task reminder"
    if reminder.kind == "slot":
        slot = next((s for s in store.timetable() if s.id == reminder.id), None)
        if slot is None:
            return reminder.title, "Timetable"
        where = f" · {slot.location}" if slot.location else ""
        return reminder.title, f"{show_time(slot.start)}–{show_time(slot.end)}{where}"
    event = store.event(reminder.id)
    if event is None or reminder.day is None:
        return reminder.title, "Event reminder"
    delta = (reminder.day - datetime.now().date()).days
    when = {0: "Today", 1: "Tomorrow"}.get(delta, f"{reminder.day:%A} {reminder.day.day} {reminder.day:%b}")
    at = f" at {show_time(event.time)}" if event.time else " · all day"
    return reminder.title, f"{when}{at}"
