from __future__ import annotations

import math
import time
from datetime import datetime
from enum import Enum

from PySide6.QtCore import QObject, QTimer, Signal

from origami.store import Store


class Mode(str, Enum):
    FOCUS = "focus"
    SHORT = "short"
    CUSTOM = "custom"


LABELS = {Mode.FOCUS: "Focus", Mode.SHORT: "Short break", Mode.CUSTOM: "Custom"}

_SETTINGS = {Mode.FOCUS: ("focus_min", 25), Mode.SHORT: ("short_min", 5)}
CUSTOM_KEY = "custom_sec"
CUSTOM_DEFAULT = 10 * 60
CUSTOM_MAX = 24 * 3600 - 1
MIN_LOG_SECONDS = 60  # stopped sessions shorter than this are not worth recording


class FocusTimer(QObject):
    tick = Signal(int, int)
    state_changed = Signal()
    completed = Signal(str)

    def __init__(self, store: Store) -> None:
        super().__init__()
        self._store = store
        self._clock = QTimer(self)
        self._clock.setInterval(200)
        self._clock.timeout.connect(self._on_tick)
        self._deadline = 0.0
        self._started_at: datetime | None = None
        self.mode = Mode.FOCUS
        self.running = False
        self.total = self.remaining = self.duration(self.mode)

    def duration(self, mode: Mode) -> int:
        if mode is Mode.CUSTOM:
            return min(max(self._store.get_int(CUSTOM_KEY, CUSTOM_DEFAULT), 0), CUSTOM_MAX)
        key, default = _SETTINGS[mode]
        return self._store.get_int(key, default) * 60

    def set_custom(self, seconds: int) -> None:
        """Store the custom length and, if idle in custom mode, load it."""
        seconds = min(max(int(seconds), 0), CUSTOM_MAX)
        self._store.set(CUSTOM_KEY, seconds)
        if self.mode is Mode.CUSTOM and not self.running:
            self._switch(Mode.CUSTOM)

    def start(self) -> None:
        if self.running or self.remaining <= 0:
            return
        self._started_at = self._started_at or datetime.now()
        self._deadline = time.monotonic() + self.remaining
        self.running = True
        self._clock.start()
        self.state_changed.emit()

    def pause(self) -> None:
        if not self.running:
            return
        self._clock.stop()
        self.remaining = self._seconds_left()
        self.running = False
        self.tick.emit(self.remaining, self.total)
        self.state_changed.emit()

    def toggle(self) -> None:
        if self.running:
            self.pause()
        else:
            self.start()

    def reset(self) -> None:
        self._switch(self.mode)

    def skip(self) -> None:
        self._switch(Mode.SHORT if self.mode is Mode.FOCUS else Mode.FOCUS)

    def set_mode(self, mode: Mode) -> None:
        self._switch(mode)

    def _seconds_left(self) -> int:
        return max(0, math.ceil(self._deadline - time.monotonic()))

    def _on_tick(self) -> None:
        remaining = self._seconds_left()
        if remaining != self.remaining:
            self.remaining = remaining
            self.tick.emit(remaining, self.total)
        if remaining == 0:
            self._complete()

    def elapsed(self) -> int:
        """Seconds actually spent in the current session so far."""
        left = self._seconds_left() if self.running else self.remaining
        return max(0, self.total - left)

    def shutdown(self) -> None:
        """Keep the time already studied when the app closes mid-session."""
        self._log_partial()
        self._clock.stop()
        self.running = False

    def _log_partial(self) -> None:
        if self.mode is Mode.SHORT or self._started_at is None:
            return
        spent = self.elapsed()
        if spent >= MIN_LOG_SECONDS:
            self._store.log_focus(self._started_at, spent)
        self._started_at = None

    def _complete(self) -> None:
        finished = self.mode
        self._clock.stop()
        self.running = False
        if finished is not Mode.SHORT:
            self._store.log_focus(self._started_at or datetime.now(), self.total)
        self._started_at = None
        upcoming = {Mode.FOCUS: Mode.SHORT, Mode.SHORT: Mode.FOCUS, Mode.CUSTOM: Mode.CUSTOM}[finished]
        self.completed.emit(finished.value)
        self._switch(upcoming)

    def _switch(self, mode: Mode) -> None:
        self._log_partial()
        self._clock.stop()
        self.running = False
        self._started_at = None
        self.mode = mode
        self.total = self.remaining = self.duration(mode)
        self.tick.emit(self.remaining, self.total)
        self.state_changed.emit()
