from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta
from pathlib import Path

from PySide6.QtCore import QObject, QStandardPaths, Signal

PRIORITIES: tuple[str, ...] = ("Normal", "High", "Urgent")
_KEEP = object()  # update_event: leave this column unchanged

_LEGACY_DB = Path(__file__).resolve().parent.parent / "data" / "origami.db"

_SCHEMA = """
CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    done INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    done_at TEXT,
    notes TEXT NOT NULL DEFAULT '',
    priority INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    day TEXT NOT NULL,
    title TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    priority INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX events_day ON events (day);
CREATE TABLE focus_sessions (
    id INTEGER PRIMARY KEY,
    started_at TEXT NOT NULL,
    seconds INTEGER NOT NULL
);
CREATE TABLE habits (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE habit_checks (
    habit_id INTEGER NOT NULL REFERENCES habits (id) ON DELETE CASCADE,
    day TEXT NOT NULL,
    PRIMARY KEY (habit_id, day)
);
PRAGMA user_version = 5;
"""

_MIGRATION_2 = """
BEGIN;
ALTER TABLE tasks ADD COLUMN due TEXT;
ALTER TABLE tasks ADD COLUMN priority INTEGER NOT NULL DEFAULT 0;
ALTER TABLE tasks ADD COLUMN notes TEXT NOT NULL DEFAULT '';
CREATE TABLE habits (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE habit_checks (
    habit_id INTEGER NOT NULL REFERENCES habits (id) ON DELETE CASCADE,
    day TEXT NOT NULL,
    PRIMARY KEY (habit_id, day)
);
PRAGMA user_version = 2;
COMMIT;
"""

_MIGRATION_3 = """
BEGIN;
ALTER TABLE tasks DROP COLUMN due;
PRAGMA user_version = 3;
COMMIT;
"""

_MIGRATION_4 = """
BEGIN;
ALTER TABLE tasks DROP COLUMN priority;
PRAGMA user_version = 4;
COMMIT;
"""

_MIGRATION_5 = """
BEGIN;
ALTER TABLE tasks ADD COLUMN priority INTEGER NOT NULL DEFAULT 0;
PRAGMA user_version = 5;
COMMIT;
"""

# Reminders and weekly repeating events.
_MIGRATION_6 = """
BEGIN;
ALTER TABLE tasks ADD COLUMN remind_at TEXT;
ALTER TABLE tasks ADD COLUMN reminded INTEGER NOT NULL DEFAULT 0;
ALTER TABLE events ADD COLUMN time TEXT;
ALTER TABLE events ADD COLUMN remind INTEGER;
ALTER TABLE events ADD COLUMN repeat_days TEXT NOT NULL DEFAULT '';
CREATE TABLE event_alerts (
    event_id INTEGER NOT NULL REFERENCES events (id) ON DELETE CASCADE,
    day TEXT NOT NULL,
    PRIMARY KEY (event_id, day)
);
PRAGMA user_version = 6;
COMMIT;
"""

# Weekly timetable: slots that repeat every week on one weekday.
_MIGRATION_7 = """
BEGIN;
CREATE TABLE timetable (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    location TEXT NOT NULL DEFAULT '',
    day INTEGER NOT NULL,
    start TEXT NOT NULL,
    end TEXT NOT NULL,
    color INTEGER NOT NULL DEFAULT 0,
    remind INTEGER,
    created_at TEXT NOT NULL
);
CREATE TABLE timetable_alerts (
    slot_id INTEGER NOT NULL REFERENCES timetable (id) ON DELETE CASCADE,
    day TEXT NOT NULL,
    PRIMARY KEY (slot_id, day)
);
PRAGMA user_version = 7;
COMMIT;
"""

SLOT_COLORS = 6


@dataclass(slots=True, frozen=True)
class Slot:
    id: int
    title: str
    location: str
    day: int  # weekday, Mon=0
    start: time
    end: time
    color: int = 0
    remind: int | None = None

    @property
    def minutes(self) -> int:
        return (self.end.hour * 60 + self.end.minute) - (self.start.hour * 60 + self.start.minute)


def _slot(row: sqlite3.Row) -> Slot:
    return Slot(
        row["id"],
        row["title"],
        row["location"],
        row["day"],
        time.fromisoformat(row["start"]),
        time.fromisoformat(row["end"]),
        row["color"],
        row["remind"],
    )


def _slot_times(start: time, end: time) -> tuple[str, str]:
    if end <= start:
        raise ValueError("end must be after start")
    return start.strftime("%H:%M"), end.strftime("%H:%M")


_EVENTS_TABLE = """
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    day TEXT NOT NULL,
    title TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    priority INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    time TEXT,
    remind INTEGER,
    repeat_days TEXT NOT NULL DEFAULT ''
);
"""

ALL_DAY_REMIND_AT = time(9, 0)  # reminders for all-day events fire at 09:00
REMINDER_GRACE = timedelta(minutes=30)  # reminders missed by more than this (app closed) stay silent


@dataclass(slots=True, frozen=True)
class Reminder:
    kind: str  # "task" | "event"
    id: int
    title: str
    when: datetime
    day: date | None = None  # event occurrence the alert belongs to


@dataclass(slots=True, frozen=True)
class Task:
    id: int
    title: str
    done: bool
    created_at: datetime
    done_at: datetime | None
    notes: str = ""
    priority: int = 0
    remind_at: datetime | None = None


@dataclass(slots=True, frozen=True)
class Event:
    id: int
    day: date
    title: str
    notes: str
    priority: int
    time: time | None = None  # None = all day
    remind: int | None = None  # minutes before start; None = no reminder
    repeat_days: tuple[int, ...] = ()  # weekdays (Mon=0) it repeats on; () = one-off
    start: date | None = None  # first day of a repeating series

    @property
    def repeats(self) -> bool:
        return bool(self.repeat_days)

    def starts_at(self) -> datetime:
        return datetime.combine(self.day, self.time or ALL_DAY_REMIND_AT)

    def alert_at(self) -> datetime | None:
        if self.remind is None:
            return None
        return self.starts_at() - timedelta(minutes=self.remind)


@dataclass(slots=True, frozen=True)
class Habit:
    id: int
    name: str
    streak: int
    done_today: bool
    week: tuple[bool, ...]


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _task(row: sqlite3.Row) -> Task:
    done_at = row["done_at"]
    return Task(
        row["id"],
        row["title"],
        bool(row["done"]),
        datetime.fromisoformat(row["created_at"]),
        datetime.fromisoformat(done_at) if done_at else None,
        row["notes"],
        row["priority"],
        datetime.fromisoformat(row["remind_at"]) if row["remind_at"] else None,
    )


def _priority(value: int) -> int:
    return max(0, min(int(value), len(PRIORITIES) - 1))


def _days(text: str) -> tuple[int, ...]:
    return tuple(sorted({int(d) for d in text.split(",") if d.strip().isdigit() and 0 <= int(d) <= 6}))


def _event(row: sqlite3.Row) -> Event:
    day = date.fromisoformat(row["day"])
    repeat = _days(row["repeat_days"])
    return Event(
        row["id"],
        day,
        row["title"],
        row["notes"],
        row["priority"],
        time.fromisoformat(row["time"]) if row["time"] else None,
        row["remind"],
        repeat,
        day if repeat else None,
    )


def _sort_key(event: Event) -> tuple:
    return (event.day, event.time is not None, event.time or time.min, -event.priority, event.id)


def _clean_title(title: str) -> str:
    title = title.strip()
    if not title:
        raise ValueError("title must not be empty")
    return title


def _default_dir() -> Path:
    home = os.environ.get("ORIGAMI_HOME")
    if home:
        return Path(home)
    return Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))


class Store(QObject):
    changed = Signal(str)

    def __init__(self, path: Path | None = None) -> None:
        super().__init__()
        self.path = Path(path) if path else _default_dir() / "origami.db"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(self.path)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA foreign_keys=ON")
        version = self._db.execute("PRAGMA user_version").fetchone()[0]
        if version < 1:
            self._db.executescript(_SCHEMA)
            if path is None:
                self._import_legacy()
        else:
            if version < 2:
                self._db.executescript(_MIGRATION_2)
            if version < 3:
                self._db.executescript(_MIGRATION_3)
            if version < 4:
                self._db.executescript(_MIGRATION_4)
            if version < 5:
                self._db.executescript(_MIGRATION_5)
        if self._db.execute("PRAGMA user_version").fetchone()[0] < 6:
            tables = {r[0] for r in self._db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            script = _MIGRATION_6
            if "events" not in tables:
                script = script.replace("ALTER TABLE events ADD COLUMN time TEXT;", "").replace(
                    "ALTER TABLE events ADD COLUMN remind INTEGER;", ""
                ).replace("ALTER TABLE events ADD COLUMN repeat_days TEXT NOT NULL DEFAULT '';", "")
                script = script.replace("BEGIN;", "BEGIN;" + _EVENTS_TABLE, 1)
            self._db.executescript(script)
        if self._db.execute("PRAGMA user_version").fetchone()[0] < 7:
            self._db.executescript(_MIGRATION_7)

    def close(self) -> None:
        self._db.close()

    def _import_legacy(self) -> None:
        if not _LEGACY_DB.exists():
            return
        try:
            with closing(sqlite3.connect(f"{_LEGACY_DB.as_uri()}?mode=ro", uri=True)) as old:
                old.row_factory = sqlite3.Row
                tables = {r[0] for r in old.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                with self._db:
                    if "todos" in tables:
                        for r in old.execute("SELECT title, completed, created_at FROM todos"):
                            created = datetime.fromisoformat(r["created_at"]).isoformat(timespec="seconds")
                            done = bool(r["completed"])
                            self._db.execute(
                                "INSERT INTO tasks (title, done, created_at, done_at) VALUES (?, ?, ?, ?)",
                                (r["title"], done, created, created if done else None),
                            )
                    if "calendar_events" in tables:
                        priorities = {"important": 2, "next_important": 1}
                        for r in old.execute(
                            "SELECT title, description, event_date, priority FROM calendar_events"
                        ):
                            self._db.execute(
                                "INSERT INTO events (day, title, notes, priority, created_at)"
                                " VALUES (?, ?, ?, ?, ?)",
                                (
                                    date.fromisoformat(str(r["event_date"])[:10]).isoformat(),
                                    r["title"],
                                    r["description"] or "",
                                    priorities.get(r["priority"], 0),
                                    _now(),
                                ),
                            )
                    if "app_settings" in tables:
                        legacy = dict(old.execute("SELECT key, value FROM app_settings").fetchall())
                        name = legacy.get("username") or legacy.get("user_name")
                        if name and name != "User":
                            self._put("name", name)
                        if legacy.get("theme"):
                            self._put("theme", legacy["theme"])
        except (sqlite3.Error, ValueError, TypeError):
            pass

    def _put(self, key: str, value: str | int) -> None:
        self._db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?)"
            " ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )

    def get(self, key: str, default: str = "") -> str:
        row = self._db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def get_int(self, key: str, default: int) -> int:
        try:
            return int(self.get(key, str(default)))
        except ValueError:
            return default

    def set(self, key: str, value: str | int) -> None:
        with self._db:
            self._put(key, value)
        self.changed.emit("settings")

    def tasks(self) -> list[Task]:
        rows = self._db.execute(
            "SELECT * FROM tasks ORDER BY done,"
            " CASE done WHEN 0 THEN priority ELSE 0 END DESC,"
            " CASE done WHEN 0 THEN created_at ELSE done_at END DESC, id DESC"
        )
        return [_task(r) for r in rows]

    def set_task_priority(self, task_id: int, priority: int) -> None:
        with self._db:
            self._db.execute("UPDATE tasks SET priority = ? WHERE id = ?", (_priority(priority), task_id))
        self.changed.emit("tasks")

    def task(self, task_id: int) -> Task | None:
        row = self._db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return _task(row) if row else None

    def add_task(self, title: str, notes: str = "", priority: int = 0) -> Task:
        title = _clean_title(title)
        with self._db:
            cur = self._db.execute(
                "INSERT INTO tasks (title, created_at, notes, priority) VALUES (?, ?, ?, ?)",
                (title, _now(), notes.strip(), _priority(priority)),
            )
        self.changed.emit("tasks")
        return _task(self._db.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone())

    def update_task(self, task_id: int, *, title: str, notes: str) -> None:
        title = _clean_title(title)
        with self._db:
            self._db.execute(
                "UPDATE tasks SET title = ?, notes = ? WHERE id = ?",
                (title, notes.strip(), task_id),
            )
        self.changed.emit("tasks")

    def set_done(self, task_id: int, done: bool) -> None:
        with self._db:
            self._db.execute(
                "UPDATE tasks SET done = ?, done_at = ? WHERE id = ?",
                (done, _now() if done else None, task_id),
            )
        self.changed.emit("tasks")

    def rename_task(self, task_id: int, title: str) -> None:
        title = _clean_title(title)
        with self._db:
            self._db.execute("UPDATE tasks SET title = ? WHERE id = ?", (title, task_id))
        self.changed.emit("tasks")

    def delete_task(self, task_id: int) -> None:
        with self._db:
            self._db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.changed.emit("tasks")

    def clear_done(self) -> int:
        with self._db:
            count = self._db.execute("DELETE FROM tasks WHERE done = 1").rowcount
        self.changed.emit("tasks")
        return count

    def open_count(self) -> int:
        return self._db.execute("SELECT COUNT(*) FROM tasks WHERE done = 0").fetchone()[0]

    def task_counts(self) -> tuple[int, int]:
        row = self._db.execute("SELECT COALESCE(SUM(done), 0), COUNT(*) FROM tasks").fetchone()
        return row[0], row[1]

    def events_between(self, start: date, end: date) -> list[Event]:
        """Every occurrence from start to end inclusive; weekly events appear once per matching day."""
        rows = self._db.execute(
            "SELECT * FROM events WHERE (repeat_days = '' AND day BETWEEN ? AND ?)"
            " OR (repeat_days != '' AND day <= ?)",
            (start.isoformat(), end.isoformat(), end.isoformat()),
        )
        found: list[Event] = []
        for row in rows:
            event = _event(row)
            if not event.repeats:
                found.append(event)
                continue
            first = max(start, event.day)
            for offset in range((end - first).days + 1):
                day = first + timedelta(days=offset)
                if day.weekday() in event.repeat_days:
                    found.append(replace(event, day=day))
        return sorted(found, key=_sort_key)

    def event(self, event_id: int) -> Event | None:
        row = self._db.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        return _event(row) if row else None

    def upcoming_window(self, days: int = 14) -> list[Event]:
        """Occurrences from today through the next `days` days, most important first, then soonest."""
        today = date.today()
        events = self.events_between(today, today + timedelta(days=days))
        return sorted(events, key=lambda e: (-e.priority, *_sort_key(e)))

    def add_event(
        self,
        day: date,
        title: str,
        notes: str = "",
        priority: int = 0,
        *,
        at: time | None = None,
        remind: int | None = None,
        repeat_days: tuple[int, ...] = (),
    ) -> Event:
        title = _clean_title(title)
        with self._db:
            cur = self._db.execute(
                "INSERT INTO events (day, title, notes, priority, created_at, time, remind, repeat_days)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    day.isoformat(),
                    title,
                    notes.strip(),
                    _priority(priority),
                    _now(),
                    at.strftime("%H:%M") if at else None,
                    remind,
                    ",".join(map(str, _days(",".join(map(str, repeat_days))))),
                ),
            )
        self.changed.emit("events")
        return _event(self._db.execute("SELECT * FROM events WHERE id = ?", (cur.lastrowid,)).fetchone())

    def update_event(
        self,
        event_id: int,
        title: str,
        notes: str,
        priority: int,
        *,
        at: time | None | object = _KEEP,
        remind: int | None | object = _KEEP,
        repeat_days: tuple[int, ...] | object = _KEEP,
    ) -> None:
        title = _clean_title(title)
        fields = {"title": title, "notes": notes.strip(), "priority": _priority(priority)}
        if at is not _KEEP:
            fields["time"] = at.strftime("%H:%M") if at else None
        if remind is not _KEEP:
            fields["remind"] = remind
        if repeat_days is not _KEEP:
            fields["repeat_days"] = ",".join(map(str, _days(",".join(map(str, repeat_days)))))
        assignments = ", ".join(f"{name} = ?" for name in fields)
        with self._db:
            self._db.execute(f"UPDATE events SET {assignments} WHERE id = ?", (*fields.values(), event_id))
            # Changing the time or reminder re-arms alerts that have not happened yet.
            self._db.execute(
                "DELETE FROM event_alerts WHERE event_id = ? AND day >= ?",
                (event_id, date.today().isoformat()),
            )
        self.changed.emit("events")

    def timetable(self) -> list[Slot]:
        rows = self._db.execute("SELECT * FROM timetable ORDER BY day, start, end, id")
        return [_slot(r) for r in rows]

    def add_slots(
        self,
        title: str,
        days: tuple[int, ...],
        start: time,
        end: time,
        *,
        location: str = "",
        color: int = 0,
        remind: int | None = None,
    ) -> list[Slot]:
        """One slot per chosen weekday, so each day can later be edited or removed on its own."""
        title = _clean_title(title)
        days = _days(",".join(map(str, days)))
        if not days:
            raise ValueError("pick at least one day")
        begin, finish = _slot_times(start, end)
        ids = []
        with self._db:
            for day in days:
                cur = self._db.execute(
                    "INSERT INTO timetable (title, location, day, start, end, color, remind, created_at)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (title, location.strip(), day, begin, finish, color % SLOT_COLORS, remind, _now()),
                )
                ids.append(cur.lastrowid)
        self.changed.emit("timetable")
        return [s for s in self.timetable() if s.id in ids]

    def update_slot(
        self,
        slot_id: int,
        title: str,
        day: int,
        start: time,
        end: time,
        *,
        location: str = "",
        color: int = 0,
        remind: int | None = None,
    ) -> None:
        title = _clean_title(title)
        begin, finish = _slot_times(start, end)
        with self._db:
            self._db.execute(
                "UPDATE timetable SET title = ?, location = ?, day = ?, start = ?, end = ?, color = ?,"
                " remind = ? WHERE id = ?",
                (title, location.strip(), day % 7, begin, finish, color % SLOT_COLORS, remind, slot_id),
            )
            self._db.execute(
                "DELETE FROM timetable_alerts WHERE slot_id = ? AND day >= ?",
                (slot_id, date.today().isoformat()),
            )
        self.changed.emit("timetable")

    def delete_slot(self, slot_id: int) -> None:
        with self._db:
            self._db.execute("DELETE FROM timetable WHERE id = ?", (slot_id,))
        self.changed.emit("timetable")

    def set_task_reminder(self, task_id: int, when: datetime | None) -> None:
        with self._db:
            self._db.execute(
                "UPDATE tasks SET remind_at = ?, reminded = 0 WHERE id = ?",
                (when.isoformat(timespec="minutes") if when else None, task_id),
            )
        self.changed.emit("tasks")

    def pending_reminders(self, now: datetime, horizon: timedelta = timedelta(hours=36)) -> list[Reminder]:
        """Reminders that have not fired yet and are due before now + horizon, soonest first."""
        found: list[Reminder] = []
        for row in self._db.execute(
            "SELECT id, title, remind_at FROM tasks WHERE done = 0 AND reminded = 0 AND remind_at IS NOT NULL"
            " AND remind_at <= ?",
            ((now + horizon).isoformat(timespec="minutes"),),
        ):
            found.append(Reminder("task", row["id"], row["title"], datetime.fromisoformat(row["remind_at"])))
        sent = {(r["event_id"], r["day"]) for r in self._db.execute("SELECT event_id, day FROM event_alerts")}
        # An alert can be up to a day before its event, so look one day further ahead.
        first, last = now.date() - timedelta(days=1), (now + horizon).date() + timedelta(days=1)
        for event in self.events_between(first, last):
            when = event.alert_at()
            if when is None or (event.id, event.day.isoformat()) in sent or when > now + horizon:
                continue
            found.append(Reminder("event", event.id, event.title, when, event.day))
        slots = [s for s in self.timetable() if s.remind is not None]
        if slots:
            fired = {(r["slot_id"], r["day"]) for r in self._db.execute("SELECT * FROM timetable_alerts")}
            for offset in range((last - first).days + 1):
                day = first + timedelta(days=offset)
                for slot in slots:
                    if slot.day != day.weekday() or (slot.id, day.isoformat()) in fired:
                        continue
                    when = datetime.combine(day, slot.start) - timedelta(minutes=slot.remind)
                    if when <= now + horizon:
                        found.append(Reminder("slot", slot.id, slot.title, when, day))
        return sorted(found, key=lambda r: r.when)

    def due_reminders(self, now: datetime) -> list[Reminder]:
        """Reminders due now. Each is marked as delivered; ones missed long ago are dropped silently."""
        due = [r for r in self.pending_reminders(now, timedelta(0)) if r.when <= now]
        with self._db:
            for r in due:
                if r.kind == "task":
                    self._db.execute("UPDATE tasks SET reminded = 1 WHERE id = ?", (r.id,))
                elif r.kind == "slot":
                    self._db.execute(
                        "INSERT OR IGNORE INTO timetable_alerts (slot_id, day) VALUES (?, ?)",
                        (r.id, r.day.isoformat()),
                    )
                else:
                    self._db.execute(
                        "INSERT OR IGNORE INTO event_alerts (event_id, day) VALUES (?, ?)",
                        (r.id, r.day.isoformat()),
                    )
        if due:
            self.changed.emit("reminders")
        return [r for r in due if now - r.when <= REMINDER_GRACE]

    def delete_event(self, event_id: int) -> None:
        with self._db:
            self._db.execute("DELETE FROM events WHERE id = ?", (event_id,))
        self.changed.emit("events")

    def log_focus(self, started_at: datetime, seconds: int) -> None:
        with self._db:
            self._db.execute(
                "INSERT INTO focus_sessions (started_at, seconds) VALUES (?, ?)",
                (started_at.isoformat(timespec="seconds"), seconds),
            )
        self.changed.emit("focus")

    def focus_between(self, start: date, end: date) -> list[tuple[date, int, int]]:
        """(day, sessions, seconds) for every day from start to end inclusive, zero-filled."""
        rows = self._db.execute(
            "SELECT substr(started_at, 1, 10) AS d, COUNT(*) AS n, SUM(seconds) AS total"
            " FROM focus_sessions WHERE substr(started_at, 1, 10) BETWEEN ? AND ? GROUP BY d",
            (start.isoformat(), end.isoformat()),
        )
        found = {r["d"]: (r["n"], r["total"]) for r in rows}
        days = (end - start).days + 1
        return [
            (d, *found.get(d.isoformat(), (0, 0)))
            for d in (start + timedelta(days=i) for i in range(max(days, 0)))
        ]

    def focus_week(self, monday: date) -> list[tuple[date, int, int]]:
        """Monday-to-Sunday totals for the calendar week starting on `monday`."""
        monday -= timedelta(days=monday.weekday())
        return self.focus_between(monday, monday + timedelta(days=6))

    def habits(self) -> list[Habit]:
        today = date.today()
        checks: dict[int, set[date]] = {}
        for r in self._db.execute("SELECT habit_id, day FROM habit_checks"):
            checks.setdefault(r["habit_id"], set()).add(date.fromisoformat(r["day"]))
        result = []
        for r in self._db.execute("SELECT id, name FROM habits ORDER BY position, id"):
            days = checks.get(r["id"], set())
            cursor = today if today in days else today - timedelta(days=1)
            streak = 0
            while cursor in days:
                streak += 1
                cursor -= timedelta(days=1)
            result.append(
                Habit(
                    r["id"],
                    r["name"],
                    streak,
                    today in days,
                    tuple(today - timedelta(days=i) in days for i in range(6, -1, -1)),
                )
            )
        return result

    def add_habit(self, name: str) -> Habit:
        name = _clean_title(name)
        with self._db:
            cur = self._db.execute(
                "INSERT INTO habits (name, created_at, position)"
                " VALUES (?, ?, (SELECT COALESCE(MAX(position), -1) + 1 FROM habits))",
                (name, _now()),
            )
        self.changed.emit("habits")
        return next(h for h in self.habits() if h.id == cur.lastrowid)

    def rename_habit(self, habit_id: int, name: str) -> None:
        name = _clean_title(name)
        with self._db:
            self._db.execute("UPDATE habits SET name = ? WHERE id = ?", (name, habit_id))
        self.changed.emit("habits")

    def delete_habit(self, habit_id: int) -> None:
        with self._db:
            self._db.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
        self.changed.emit("habits")

    def toggle_habit(self, habit_id: int, day: date | None = None) -> bool:
        day = day or date.today()
        if day > date.today():
            raise ValueError("cannot check a future day")
        key = (habit_id, day.isoformat())
        with self._db:
            deleted = self._db.execute(
                "DELETE FROM habit_checks WHERE habit_id = ? AND day = ?", key
            ).rowcount
            if not deleted:
                self._db.execute("INSERT INTO habit_checks (habit_id, day) VALUES (?, ?)", key)
        self.changed.emit("habits")
        return not deleted

    def habit_checks(self, habit_id: int, start: date, end: date) -> set[date]:
        rows = self._db.execute(
            "SELECT day FROM habit_checks WHERE habit_id = ? AND day BETWEEN ? AND ?",
            (habit_id, start.isoformat(), end.isoformat()),
        )
        return {date.fromisoformat(r["day"]) for r in rows}

    def habit_counts(self) -> tuple[int, int]:
        row = self._db.execute(
            "SELECT COUNT(*), COALESCE(SUM(EXISTS (SELECT 1 FROM habit_checks c"
            " WHERE c.habit_id = habits.id AND c.day = ?)), 0) FROM habits",
            (date.today().isoformat(),),
        ).fetchone()
        return row[1], row[0]

    def _table(self, sql: str) -> list[dict]:
        return [dict(r) for r in self._db.execute(sql)]

    def export_json(self, path: Path) -> None:
        checks: dict[int, list[str]] = {}
        for r in self._db.execute("SELECT habit_id, day FROM habit_checks ORDER BY day"):
            checks.setdefault(r["habit_id"], []).append(r["day"])
        habits = [
            {**h, "checks": checks.get(h["id"], [])}
            for h in self._table("SELECT * FROM habits ORDER BY position, id")
        ]
        keys = ("theme", "accent", "font_size", "focus_min", "short_min", "custom_sec")
        data = {
            "version": 2,
            "exported_at": _now(),
            "settings": {k: self.get(k) for k in keys if self.get(k)},
            "tasks": self._table("SELECT * FROM tasks ORDER BY id"),
            "events": self._table("SELECT * FROM events ORDER BY day, id"),
            "habits": habits,
            "focus_sessions": self._table("SELECT * FROM focus_sessions ORDER BY id"),
        }
        Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
