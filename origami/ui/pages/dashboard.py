"""Home: today's date (kept in sync with the clock), today's quote, and four quiet grouped lists."""

from __future__ import annotations

from datetime import date, datetime

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QPainter
from PySide6.QtWidgets import QFrame, QLineEdit, QVBoxLayout, QWidget

from origami.context import Context
from origami.quotes import random_quote
from origami.store import Event, Habit, Reminder, Task
from origami.ui import icons
from origami.ui.components import (
    CheckDot,
    ElidedLabel,
    IconLabel,
    Page,
    clear,
    hbox,
    label,
    retone,
    vbox,
    when_text,
)
from origami.ui.theme import PRIORITY_COLORS, event_tint, pixel_font, theme

UP_NEXT_ROWS = 6
REMINDER_ROWS = 2
UPCOMING_ROWS = 3
HABIT_ROWS = 3
UPCOMING_DAYS = 14
ROW_INSET = 46  # dividers start under the text, not under the check circle
PRIORITY_NAMES = ("Normal", "High", "Urgent")
CLOCK_MS = 30_000


def relative_day(day: date) -> str:
    delta = (day - date.today()).days
    if delta == 0:
        return "Today"
    if delta == 1:
        return "Tomorrow"
    return f"{day:%A}" if delta < 7 else f"{day:%a} {day.day} {day:%b}"


class Group(QFrame):
    """Rounded list container (Apple inset-group style) with hairline dividers between rows."""

    def __init__(self, inset: int = ROW_INSET) -> None:
        super().__init__()
        self.setProperty("group", True)
        self._inset = inset
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 4, 0, 4)
        outer.setSpacing(0)
        self.rows = QVBoxLayout()
        self.rows.setSpacing(0)
        outer.addLayout(self.rows)
        outer.addStretch(1)

    def add(self, row: QWidget) -> None:
        if self.rows.count():
            rule = QFrame()
            rule.setProperty("divider", True)
            holder = QWidget()
            holder.setLayout(hbox(rule, margins=(self._inset, 0, 0, 0)))
            self.rows.addWidget(holder)
        self.rows.addWidget(row)

    def reset(self) -> None:
        clear(self.rows)

    def note(self, text: str) -> None:
        empty = label(text, "muted")
        empty.setContentsMargins(16, 12, 16, 12)
        self.rows.addWidget(empty)


def section(title: str) -> QWidget:
    w = label(title, "group")
    w.setContentsMargins(4, 0, 0, 0)
    return w


def row_widget(*items, margins=(16, 0, 16, 0), height: int = 40) -> QWidget:
    w = QWidget()
    w.setMinimumHeight(height)
    w.setLayout(hbox(*items, spacing=12, margins=margins))
    return w


class Tinted(QWidget):
    """A caption in a priority colour (Apple Reminders-style: a coloured word, not a badge)."""

    def __init__(self, text: str, priority: int, *, ink: bool = False) -> None:
        super().__init__()
        self._label = label(text, "caption")
        self._priority, self._ink = priority, ink
        self.setLayout(hbox(self._label))
        theme.changed.connect(self._tint)
        self._tint()

    def _tint(self) -> None:
        p = theme.palette
        color = event_tint(p, self._priority)[2] if self._ink else PRIORITY_COLORS(p)[self._priority]
        self._label.setStyleSheet(f"color: {color}; font-weight: 500;")


class EventRow(QWidget):
    """Event with a thin bar in its priority colour, the title, and priority · day · time beneath."""

    def __init__(self, event: Event) -> None:
        super().__init__()
        self.priority = event.priority
        self.setMinimumHeight(46)
        title = ElidedLabel(event.title, "body")
        parts = [PRIORITY_NAMES[event.priority], relative_day(event.day)]
        if event.time:
            parts.append(f"{event.time:%H:%M}")
        meta = Tinted("  ·  ".join(parts), event.priority, ink=True)
        self.setLayout(vbox(title, meta, spacing=1, margins=(30, 6, 16, 6)))

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(PRIORITY_COLORS(theme.palette)[self.priority]))
        painter.drawRoundedRect(QRectF(16, 10, 3, self.height() - 20), 1.5, 1.5)


class WeekDots(QWidget):
    """Seven small squares: the habit's last seven days, today on the right."""

    def __init__(self, week: tuple[bool, ...]) -> None:
        super().__init__()
        self._week = week
        self.setFixedSize(7 * 8 + 6 * 3, 10)
        theme.changed.connect(self.update)

    def paintEvent(self, event) -> None:
        p = theme.palette
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        for i, done in enumerate(self._week):
            painter.setBrush(QColor(p.accent if done else p.border))
            painter.drawRoundedRect(QRectF(i * 11, 1, 8, 8), 2, 2)


class QuoteMark(QWidget):
    """A large opening quotation mark in the accent colour."""

    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(34, 34)
        theme.changed.connect(self.update)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(pixel_font("Georgia", 56, QFont.Weight.Bold, scaled=False))
        painter.setPen(QColor(theme.palette.accent))
        painter.drawText(QRectF(0, -8, 34, 64), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, "“")


class QuoteCard(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setProperty("group", True)
        self.text = label("", "quotebody", wrap=True)
        self.author = label("", "caption")
        column = vbox(self.text, self.author, spacing=6)
        row = hbox(QuoteMark(), column, spacing=12, margins=(18, 14, 22, 14))
        row.setAlignment(Qt.AlignmentFlag.AlignTop)
        row.setStretch(1, 1)
        self.setLayout(row)

    def set_quote(self, text: str, author: str) -> None:
        self.text.setText(text)
        self.author.setText(author.upper())


class DashboardPage(Page):
    def __init__(self, ctx: Context) -> None:
        super().__init__(ctx, "", scroll=False)
        self.title_label.setProperty("role", "greeting")
        self.heading.setContentsMargins(2, 4, 0, 2)

        self._quote = QuoteCard()
        self._tasks = Group()
        self._quick = QLineEdit()
        self._quick.setProperty("flat", True)
        self._quick.setMaxLength(200)
        self._quick.setPlaceholderText("Add a task")
        self._quick_icon = self._quick.addAction(QIcon(), QLineEdit.ActionPosition.LeadingPosition)
        self._quick.returnPressed.connect(self._quick_add)
        theme.changed.connect(self._tint_quick)
        self._tint_quick()
        self._reminders = Group(inset=42)
        self._upcoming = Group(inset=30)
        self._habits = Group()

        left = QVBoxLayout()
        left.setSpacing(8)
        left.addWidget(section("Up next"))
        left.addWidget(self._tasks, 3)
        left.addSpacing(10)
        left.addWidget(section("Reminders"))
        left.addWidget(self._reminders, 2)
        right = QVBoxLayout()
        right.setSpacing(8)
        right.addWidget(section("Coming up"))
        right.addWidget(self._upcoming, 3)
        right.addSpacing(10)
        right.addWidget(section("Habits"))
        right.addWidget(self._habits, 2)
        columns = hbox(left, right, spacing=20)
        columns.setStretch(0, 1)
        columns.setStretch(1, 1)
        self.body.setSpacing(16)
        self.body.addWidget(self._quote)
        self.body.addLayout(columns, 1)

        self._clock = QTimer(self)
        self._clock.setInterval(CLOCK_MS)
        self._clock.timeout.connect(self._tick)
        self._clock.start()
        self._day = date.today()
        ctx.store.changed.connect(self._on_changed)
        self.on_show()

    def on_show(self) -> None:
        self._refresh_header()
        self._refresh_tasks()
        self._refresh_reminders()
        self._refresh_upcoming()
        self._refresh_habits()

    def _tick(self) -> None:
        self._refresh_header()
        self._refresh_reminders()
        if date.today() != self._day:  # past midnight: relative days and habits change too
            self._day = date.today()
            self.on_show()

    def _on_changed(self, domain: str) -> None:
        refreshers = {
            "tasks": (self._refresh_tasks, self._refresh_reminders),
            "events": (self._refresh_upcoming, self._refresh_reminders),
            "reminders": (self._refresh_reminders,),
            "habits": (self._refresh_habits,),
        }
        for refresh in refreshers.get(domain, ()):
            refresh()

    def _tint_quick(self) -> None:
        self._quick_icon.setIcon(icons.icon("plus", theme.palette.accent, 18))

    def _quick_add(self) -> None:
        text = self._quick.text().strip()
        if text:
            self.ctx.store.add_task(text)
            self._quick.clear()
            self._quick.setFocus()

    def _refresh_header(self) -> None:
        now = datetime.now()
        self.title_label.setText(f"{now:%A}, {now.day} {now:%B}")
        text, author = random_quote(now.date().toordinal())
        self._quote.set_quote(text, author)

    def _refresh_tasks(self) -> None:
        pending = [t for t in self.ctx.store.tasks() if not t.done]
        group = self._tasks
        self._quick.setParent(None)
        group.reset()
        group.add(row_widget(self._quick, margins=(12, 0, 16, 0)))
        for task in pending[:UP_NEXT_ROWS]:
            group.add(self._task_row(task))
        if len(pending) > UP_NEXT_ROWS:
            group.note(f"{len(pending) - UP_NEXT_ROWS} more in Tasks")
        elif not pending:
            group.note("Nothing to do. Enjoy the calm.")

    def _task_row(self, task: Task) -> QWidget:
        dot = CheckDot(False)
        dot.toggled.connect(lambda checked, tid=task.id: self.ctx.store.set_done(tid, checked))
        title = ElidedLabel(task.title, "body")
        items: list = [dot, title]
        if task.priority:
            items.append(Tinted(PRIORITY_NAMES[task.priority], task.priority))
        row = row_widget(*items)
        row.layout().setStretch(1, 1)
        return row

    def _refresh_reminders(self) -> None:
        now = datetime.now()
        store = self.ctx.store
        upcoming = [r for r in store.pending_reminders(now) if r.when >= now]
        group = self._reminders
        group.reset()
        for reminder in upcoming[:REMINDER_ROWS]:
            group.add(self._reminder_row(reminder, now))
        if len(upcoming) > REMINDER_ROWS:
            group.note(f"{len(upcoming) - REMINDER_ROWS} more later")
        elif not upcoming:
            group.note("No reminders in the next day and a half.")

    @staticmethod
    def _reminder_row(reminder: Reminder, now: datetime) -> QWidget:
        late = reminder.when < now
        when = label(when_text(reminder.when), "caption")
        retone(when, "danger" if late else None)
        title = ElidedLabel(reminder.title, "body")
        kind = "calendar" if reminder.kind == "event" else "bell"
        row = row_widget(IconLabel(kind, "danger" if late else "accent", 16), title, when)
        row.layout().setStretch(1, 1)
        return row

    def _refresh_upcoming(self) -> None:
        events = self.ctx.store.upcoming_window(UPCOMING_DAYS)
        group = self._upcoming
        group.reset()
        for event in events[:UPCOMING_ROWS]:
            group.add(EventRow(event))
        if len(events) > UPCOMING_ROWS:
            group.note(f"{len(events) - UPCOMING_ROWS} more in Calendar")
        elif not events:
            group.note(f"Nothing in the next {UPCOMING_DAYS} days.")

    def _refresh_habits(self) -> None:
        habits = sorted(self.ctx.store.habits(), key=lambda h: h.done_today)
        group = self._habits
        group.reset()
        for habit in habits[:HABIT_ROWS]:
            group.add(self._habit_row(habit))
        if not habits:
            group.note("No habits yet.")

    def _habit_row(self, habit: Habit) -> QWidget:
        dot = CheckDot(habit.done_today)
        dot.toggled.connect(lambda _, hid=habit.id: self.ctx.store.toggle_habit(hid))
        name = ElidedLabel(habit.name, "body")
        if habit.done_today:
            name.setEnabled(False)
        streak = label(f"{habit.streak}d" if habit.streak else "", "caption")
        row = row_widget(dot, name, WeekDots(habit.week), streak)
        row.layout().setStretch(1, 1)
        return row
