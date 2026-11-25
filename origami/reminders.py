"""Checks the store for due reminders while the app runs (window open, minimised or in the tray)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from PySide6.QtCore import QObject, QTimer, Signal

from origami.store import Reminder, Store

CHECK_MS = 15_000


class ReminderService(QObject):
    fired = Signal(object)  # Reminder

    def __init__(self, store: Store, clock: Callable[[], datetime] = datetime.now) -> None:
        super().__init__()
        self._store, self._clock = store, clock
        self._timer = QTimer(self)
        self._timer.setInterval(CHECK_MS)
        self._timer.timeout.connect(self.check)

    def start(self) -> None:
        self._timer.start()
        QTimer.singleShot(1500, self.check)

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
        return reminder.title, f"{slot.start:%H:%M}–{slot.end:%H:%M}{where}"
    event = store.event(reminder.id)
    if event is None or reminder.day is None:
        return reminder.title, "Event reminder"
    today = datetime.now().date()
    delta = (reminder.day - today).days
    when = {0: "Today", 1: "Tomorrow"}.get(delta, f"{reminder.day:%A} {reminder.day.day} {reminder.day:%b}")
    at = f" at {event.time:%H:%M}" if event.time else " · all day"
    return reminder.title, f"{when}{at}"
