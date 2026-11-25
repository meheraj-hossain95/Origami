from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import date, time, timedelta

from PySide6.QtCore import QPointF, QRect, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QMouseEvent, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QWidget,
)

from origami.context import Context
from origami.store import PRIORITIES, Event
from origami.ui.components import (
    Card,
    Dropdown,
    EmptyState,
    IconLabel,
    Page,
    PriorityPill,
    Segmented,
    button,
    clear,
    confirm,
    divider,
    hbox,
    icon_button,
    index_of,
    label,
    vbox,
)
from origami.ui.theme import UI, event_tint, mono, pixel_font, px, theme

HEADER = 40
LINE = 24
PANEL_WIDTH = 272
WEEKDAYS = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")
NO_PEN = Qt.PenStyle.NoPen


def tint(priority: int, index: int) -> QColor:
    return QColor(event_tint(theme.palette, priority)[index])


def top_priority(events: list[Event]) -> int:
    return max(event.priority for event in events)


class MonthGrid(QWidget):
    selected = Signal(object)
    activated = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(420, 360)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        today = date.today()
        self._first = today.replace(day=1)
        self._selected = today
        self._hover: date | None = None
        self._events: dict[date, list[Event]] = {}
        theme.changed.connect(self.update)

    def start(self) -> date:
        return self._first - timedelta(days=self._first.weekday())

    def set_month(self, first: date) -> None:
        self._first = first
        self.update()

    def set_selected(self, day: date) -> None:
        self._selected = day
        self.update()

    def set_events(self, events: dict[date, list[Event]]) -> None:
        self._events = events
        self.update()

    def _edges(self) -> tuple[list[int], list[int]]:
        rows = self.height() - HEADER
        xs = [round(i * self.width() / 7) for i in range(8)]
        ys = [HEADER + round(i * rows / 6) for i in range(7)]
        return xs, ys

    def _day_at(self, pos: QPointF) -> date | None:
        if pos.y() < HEADER or not self.rect().contains(pos.toPoint()):
            return None
        col = min(int(pos.x() * 7 / self.width()), 6)
        row = min(int((pos.y() - HEADER) * 6 / (self.height() - HEADER)), 5)
        return self.start() + timedelta(days=row * 7 + col)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        day = self._day_at(event.position())
        if day != self._hover:
            self._hover = day
            self.setCursor(Qt.CursorShape.PointingHandCursor if day else Qt.CursorShape.ArrowCursor)
            self.update()

    def leaveEvent(self, event) -> None:
        self._hover = None
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        day = self._day_at(event.position())
        if day and event.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(day)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        day = self._day_at(event.position())
        if day and event.button() == Qt.MouseButton.LeftButton:
            self.activated.emit(day)

    def paintEvent(self, event) -> None:
        pal = theme.palette
        width, height = self.width(), self.height()
        xs, ys = self._edges()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        frame = QPainterPath()
        frame.addRoundedRect(QRectF(0.5, 0.5, width - 1, height - 1), 14, 14)
        painter.setClipPath(frame)
        painter.fillPath(frame, QColor(pal.surface))
        painter.fillRect(0, 0, width, HEADER, QColor(pal.raised))

        font = pixel_font(UI, 11, QFont.Weight.DemiBold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.0)
        painter.setFont(font)
        painter.setPen(QColor(pal.faint))
        for col, name in enumerate(WEEKDAYS):
            cell = QRect(xs[col] + 12, 0, xs[col + 1] - xs[col] - 12, HEADER)
            painter.drawText(cell, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, name)

        start = self.start()
        for index in range(42):
            row, col = divmod(index, 7)
            cell = QRect(xs[col], ys[row], xs[col + 1] - xs[col], ys[row + 1] - ys[row])
            self._paint_cell(painter, start + timedelta(days=index), cell)

        painter.setPen(QPen(QColor(pal.border), 1))
        for x in xs[1:7]:
            painter.drawLine(QPointF(x + 0.5, HEADER), QPointF(x + 0.5, height))
        for y in ys[:6]:
            painter.drawLine(QPointF(0, y + 0.5), QPointF(width, y + 0.5))
        painter.setClipping(False)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(frame)

    def _paint_cell(self, painter: QPainter, day: date, cell: QRect) -> None:
        pal = theme.palette
        in_month = day.month == self._first.month
        events = self._events.get(day, [])
        level = top_priority(events) if events else None
        painter.setOpacity(1 if in_month else 0.55)
        if level is not None:
            painter.fillRect(cell, tint(level, 1 if day == self._hover else 0))
        elif day == self._selected:
            painter.fillRect(cell, QColor(pal.accent_soft))
        elif day == self._hover:
            painter.fillRect(cell, QColor(pal.raised))
        painter.setOpacity(1)
        if day == self._selected:
            painter.setPen(QPen(QColor(pal.accent), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(cell).adjusted(1.5, 1.5, -1, -1))

        number = QRectF(cell.x() + 6, cell.y() + 6, 28, 28)
        color = pal.text if in_month else pal.faint
        if day == date.today():
            painter.setPen(NO_PEN)
            painter.setBrush(QColor(pal.accent))
            painter.drawEllipse(number)
            color = pal.accent_fg
        painter.setFont(mono(14, QFont.Weight.DemiBold if in_month else QFont.Weight.Normal))
        painter.setPen(QColor(color))
        painter.drawText(number, Qt.AlignmentFlag.AlignCenter, str(day.day))

        if not events:
            return
        font = pixel_font(UI, 12, QFont.Weight.Medium)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        line = max(LINE, px(LINE))
        lines = max((cell.height() - 42) // line, 1)
        shown = events if len(events) <= lines else events[: lines - 1]
        painter.setOpacity(1 if in_month else 0.55)
        y = cell.y() + 40
        for event in shown:
            pill = QRectF(cell.x() + 5, y, cell.width() - 10, line - 3)
            painter.setPen(NO_PEN)
            painter.setBrush(tint(event.priority, 1))
            painter.drawRoundedRect(pill, 5, 5)
            text = pill.adjusted(7, 0, -4, 0)
            painter.setPen(tint(event.priority, 2))
            name = f"{event.time:%H:%M} {event.title}" if event.time else event.title
            elided = metrics.elidedText(name, Qt.TextElideMode.ElideRight, int(text.width()))
            painter.drawText(text, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided)
            y += line
        if len(events) > len(shown):
            painter.setPen(QColor(pal.muted))
            more = QRectF(cell.x() + 10, y, cell.width() - 16, line - 3)
            painter.drawText(
                more,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                f"+{len(events) - len(shown)} more",
            )
        painter.setOpacity(1)


REMIND_OPTIONS: tuple[tuple[str, int | None], ...] = (
    ("No reminder", None),
    ("At start", 0),
    ("5 min before", 5),
    ("15 min before", 15),
    ("30 min before", 30),
    ("1 hour before", 60),
    ("1 day before", 24 * 60),
)
DAY_LETTERS = ("M", "T", "W", "T", "F", "S", "S")
DAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def repeat_text(days: tuple[int, ...]) -> str:
    if len(days) == 7:
        return "Every day"
    if days == (0, 1, 2, 3, 4):
        return "Every weekday"
    return "Every " + ", ".join(DAY_NAMES[d] for d in days)


def remind_text(minutes: int) -> str:
    return next((text for text, m in REMIND_OPTIONS if m == minutes), f"{minutes} min before")


class DayToggles(QWidget):
    """Seven round toggles (Mon..Sun). None selected means the event happens once."""

    def __init__(self) -> None:
        super().__init__()
        self._buttons: list[QPushButton] = []
        row = hbox(spacing=4)
        for i, letter in enumerate(DAY_LETTERS):
            b = QPushButton(letter)
            b.setCheckable(True)
            b.setProperty("day", True)
            b.setToolTip(DAY_NAMES[i])
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self._buttons.append(b)
            row.addWidget(b)
        row.addStretch(1)
        self.setLayout(row)

    def days(self) -> tuple[int, ...]:
        return tuple(i for i, b in enumerate(self._buttons) if b.isChecked())

    def set_days(self, days: tuple[int, ...]) -> None:
        for i, b in enumerate(self._buttons):
            b.setChecked(i in days)


class EventRow(QWidget):
    def __init__(self, event: Event, on_edit, on_delete) -> None:
        super().__init__()
        title = label(event.title, "h3", wrap=True)
        facts = [f"{event.time:%H:%M}" if event.time else "All day"]
        if event.repeats:
            facts.append(repeat_text(event.repeat_days))
        meta = [label("  ·  ".join(facts), "caption")]
        if event.remind is not None:
            meta.append(IconLabel("bell", "muted", 12))
            meta[-1].setToolTip(f"Reminder: {remind_text(event.remind)}")
        texts = [title, hbox(*meta, None, spacing=6), hbox(PriorityPill(event.priority), None)]
        if event.notes:
            texts.append(label(event.notes, "muted", wrap=True))
        for text in texts:
            if isinstance(text, QWidget):
                text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.actions = [
            icon_button("pencil", "Edit", lambda: on_edit(event), size=14),
            icon_button("trash", "Delete", lambda: on_delete(event), size=14),
        ]
        for action in self.actions:
            policy = action.sizePolicy()
            policy.setRetainSizeWhenHidden(True)
            action.setSizePolicy(policy)
            action.hide()

        self._priority = event.priority
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 6, 8)
        layout.setSpacing(6)
        layout.addLayout(vbox(*texts, spacing=4), 1)
        for action in self.actions:
            layout.addWidget(action, 0, Qt.AlignmentFlag.AlignTop)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(NO_PEN)
        painter.setBrush(tint(self._priority, 0))
        painter.drawRoundedRect(QRectF(self.rect()), 8, 8)
        painter.setBrush(tint(self._priority, 2))
        painter.drawRoundedRect(QRectF(0, 0, 4, self.height()), 2, 2)

    def enterEvent(self, event) -> None:
        for action in self.actions:
            action.show()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        for action in self.actions:
            action.hide()
        super().leaveEvent(event)


class CalendarPage(Page):
    def __init__(self, ctx: Context) -> None:
        super().__init__(ctx, "Calendar", scroll=False)
        today = date.today()
        self._first = today.replace(day=1)
        self._selected = today
        self._editing: Event | None = None

        self.title_label.hide()
        self.month_label = label("", "page")
        self.year_label = label("", "yearlight")
        prev_btn = icon_button("chevron-left", "Previous month", lambda: self._shift(-1), size=18)
        next_btn = icon_button("chevron-right", "Next month", lambda: self._shift(1), size=18)
        today_btn = button("Today", "secondary", icon="calendar", on_click=lambda: self._show(date.today()))
        today_btn.setProperty("size", "sm")
        title = hbox(self.month_label, self.year_label, spacing=10)
        title.setAlignment(self.year_label, Qt.AlignmentFlag.AlignBaseline)
        self.heading.insertLayout(0, hbox(title, 8, prev_btn, next_btn, spacing=2))
        self.header.addWidget(today_btn)

        self.grid = MonthGrid()
        self.grid.selected.connect(self._show)
        self.grid.activated.connect(self._activate)
        self.body.addLayout(hbox(self.grid, self._build_panel(), spacing=12), 1)

        ctx.store.changed.connect(self._on_changed)
        self._show(today)

    def _build_panel(self) -> Card:
        self.day_title = label(role="title")
        self.day_sub = label(role="muted")
        self.events_box = vbox(spacing=8)
        self.form_title = label("New event", "eyebrow")
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Event title")
        self.title_edit.setMaxLength(120)
        self.title_edit.returnPressed.connect(self._submit)
        self.notes_edit = QPlainTextEdit()
        self.notes_edit.setPlaceholderText("Notes (optional)")
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setMaximumHeight(48)
        self.priority = Segmented([(str(i), name) for i, name in enumerate(PRIORITIES)], "0")
        self.priority.setProperty("compact", True)
        self.time_box = Dropdown()
        self.time_box.addItem("All day", None)
        for minutes in range(0, 24 * 60, 15):
            slot = time(minutes // 60, minutes % 60)
            self.time_box.addItem(f"{slot:%H:%M}", slot)
        self.time_box.setToolTip("Start time")
        self.remind_box = Dropdown()
        for text, minutes in REMIND_OPTIONS:
            self.remind_box.addItem(text, minutes)
        self.remind_box.setToolTip("Reminder")
        self.repeat = DayToggles()
        self.cancel_button = button("Cancel", "ghost", on_click=self._reset_form)
        self.submit_button = button("Add event", on_click=self._submit)

        panel = Card()
        self.panel = panel
        theme.changed.connect(self._size_panel)
        self._size_panel()
        panel.body.setContentsMargins(16, 16, 16, 14)
        panel.body.setSpacing(10)
        panel.body.addLayout(vbox(self.day_title, self.day_sub, spacing=0))
        panel.body.addWidget(divider())
        panel.body.addLayout(self.events_box)
        panel.body.addStretch(1)
        panel.body.addWidget(divider())
        panel.body.addWidget(self.form_title)
        panel.body.addWidget(self.title_edit)
        panel.body.addWidget(self.notes_edit)
        when = hbox(self.time_box, self.remind_box, spacing=8)
        when.setStretch(0, 1)
        when.setStretch(1, 1)
        panel.body.addLayout(when)
        panel.body.addLayout(vbox(label("Repeat every week on", "caption"), self.repeat, spacing=6))
        panel.body.addWidget(self.priority)
        panel.body.addLayout(hbox(None, self.cancel_button, self.submit_button, None))
        self.cancel_button.hide()
        return panel

    def _size_panel(self) -> None:
        self.panel.setFixedWidth(round(PANEL_WIDTH * max(1.0, theme.scale)))

    def on_show(self) -> None:
        self._reload()

    def _on_changed(self, domain: str) -> None:
        if domain == "events":
            self._reload()

    def _show(self, day: date) -> None:
        self._first = day.replace(day=1)
        self._selected = day
        self.month_label.setText(f"{day:%B}")
        self.year_label.setText(str(day.year))
        self.grid.set_month(self._first)
        self.grid.set_selected(day)
        self._reset_form()
        self._reload()

    def _activate(self, day: date) -> None:
        self._show(day)
        self.title_edit.setFocus()

    def _shift(self, months: int) -> None:
        year, month = divmod(self._first.year * 12 + self._first.month - 1 + months, 12)
        last = calendar.monthrange(year, month + 1)[1]
        self._show(date(year, month + 1, min(self._selected.day, last)))

    def _reload(self) -> None:
        start = self.grid.start()
        by_day: dict[date, list[Event]] = defaultdict(list)
        for event in self.ctx.store.events_between(start, start + timedelta(days=41)):
            by_day[event.day].append(event)
        self.grid.set_events(by_day)

        self.day_title.setText(f"{self._selected:%A} {self._selected.day}")
        self.day_sub.setText(f"{self._selected:%B %Y}")
        events = by_day.get(self._selected, [])
        clear(self.events_box)
        if not events:
            self.events_box.addWidget(EmptyState("calendar", "Nothing scheduled", "Add an event below."))
        for event in events:
            self.events_box.addWidget(EventRow(event, self._edit, self._delete))
        if self._editing and all(event.id != self._editing.id for event in events):
            self._reset_form()

    def _edit(self, event: Event) -> None:
        self._editing = event
        self.form_title.setText("Edit event")
        self.title_edit.setText(event.title)
        self.notes_edit.setPlainText(event.notes)
        self.priority.set_value(str(event.priority))
        self.time_box.setCurrentIndex(max(0, index_of(self.time_box, event.time)) if event.time else 0)
        self._set_remind(event.remind)
        self.repeat.set_days(event.repeat_days)
        self.submit_button.setText("Save")
        self.cancel_button.show()
        self.title_edit.setFocus()

    def _delete(self, event: Event) -> None:
        if event.repeats and not confirm(
            self,
            "Delete repeating event",
            f"“{event.title}” repeats {repeat_text(event.repeat_days).lower()}. Delete every occurrence?",
        ):
            return
        self.ctx.store.delete_event(event.id)
        self.ctx.toast("Event deleted")

    def _reset_form(self) -> None:
        self._editing = None
        self.form_title.setText("New event")
        self.title_edit.clear()
        self.notes_edit.clear()
        self.priority.set_value("0")
        self.time_box.setCurrentIndex(0)
        self._set_remind(None)
        self.repeat.set_days(())
        self.submit_button.setText("Add event")
        self.cancel_button.hide()

    def _set_remind(self, minutes: int | None) -> None:
        index = index_of(self.remind_box, minutes)
        if index < 0 and minutes is not None:
            self.remind_box.addItem(f"{minutes} min before", minutes)
            index = self.remind_box.count() - 1
        self.remind_box.setCurrentIndex(max(index, 0))

    def _submit(self) -> None:
        title = self.title_edit.text().strip()
        if not title:
            self.title_edit.setFocus()
            return
        notes = self.notes_edit.toPlainText().strip()
        priority = int(self.priority.value())
        options = {
            "at": self.time_box.currentData(),
            "remind": self.remind_box.currentData(),
            "repeat_days": self.repeat.days(),
        }
        store = self.ctx.store
        if self._editing:
            store.update_event(self._editing.id, title, notes, priority, **options)
            self.ctx.toast("Event updated")
        else:
            store.add_event(self._selected, title, notes, priority, **options)
            self.ctx.toast("Repeats every week" if options["repeat_days"] else "Event added")
        self._reset_form()
