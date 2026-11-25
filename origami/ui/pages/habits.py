from __future__ import annotations

import calendar
from datetime import date, timedelta

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from origami.context import Context
from origami.store import Habit
from origami.ui.components import (
    Card,
    CheckDot,
    ElidedLabel,
    EmptyState,
    IconLabel,
    OutsideClick,
    Page,
    button,
    clear,
    confirm,
    divider,
    hbox,
    icon_button,
    label,
    vbox,
)
from origami.ui.pages.tasks import InlineEdit
from origami.ui.theme import UI, mono, pixel_font, theme

LIST_WIDTH = 300
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
HEAD = 26
GAP = 8
EPOCH = date(2000, 1, 1)
SUGGESTIONS = (
    "Drink water",
    "Read 20 minutes",
    "Walk 8,000 steps",
    "Meditate 10 minutes",
    "No phone after 10pm",
)


def best_streak(days: set[date]) -> int:
    best = run = 0
    previous: date | None = None
    for day in sorted(days):
        run = run + 1 if previous and day - previous == timedelta(days=1) else 1
        best = max(best, run)
        previous = day
    return best


def shift_month(first: date, months: int) -> date:
    year, month = divmod(first.year * 12 + first.month - 1 + months, 12)
    return date(year, month + 1, 1)


class HabitItem(QFrame):
    """One row in the habit list: name, streak caption and today's check."""

    clicked = Signal(int)
    toggled = Signal(int)

    def __init__(self, habit: Habit, selected: bool) -> None:
        super().__init__()
        self.habit = habit
        self._selected = selected
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setMinimumHeight(60)

        check = CheckDot(habit.done_today, 22)
        check.setToolTip("Mark today done" if not habit.done_today else "Undo today")
        check.clicked.connect(lambda: self.toggled.emit(habit.id))
        name = ElidedLabel(habit.name, "h3")
        streak = habit.streak
        caption = f"{streak} day streak" if streak else "No streak yet"
        meta = hbox(
            IconLabel("flame", "warning" if streak >= 3 else "faint", 13),
            label(caption, "caption"),
            None,
            spacing=4,
        )
        self.setLayout(hbox(vbox(name, meta, spacing=2), check, spacing=12, margins=(14, 8, 14, 8)))
        self.layout().setStretch(0, 1)

    def paintEvent(self, event) -> None:
        if not (self._selected or self.underMouse()):
            return
        p = theme.palette
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(p.accent_soft if self._selected else p.raised))
        painter.drawRoundedRect(QRectF(self.rect()), 10, 10)
        if self._selected:
            painter.setBrush(QColor(p.accent))
            painter.drawRoundedRect(QRectF(0, 12, 3, self.height() - 24), 1.5, 1.5)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        # Select on press: a pending rename may rebuild the list before the release arrives.
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.habit.id)
        super().mousePressEvent(event)


class HabitMonth(QWidget):
    """Full month for one habit. Click a past day or today to toggle it."""

    toggled = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumHeight(300)
        self.setMouseTracking(True)
        self._first = date.today().replace(day=1)
        self._done: set[date] = set()
        self._hover: date | None = None
        theme.changed.connect(self.update)

    def set_month(self, first: date, done: set[date]) -> None:
        self._first, self._done = first, done
        self.update()

    def _weeks(self) -> int:
        lead = self._first.weekday()
        days = calendar.monthrange(self._first.year, self._first.month)[1]
        return (lead + days + 6) // 7

    def _geometry(self) -> tuple[float, float]:
        return self.width() / 7, (self.height() - HEAD) / self._weeks()

    def _day_at(self, pos: QPointF) -> date | None:
        if pos.y() < HEAD:
            return None
        cw, ch = self._geometry()
        col, row = int(pos.x() // cw), int((pos.y() - HEAD) // ch)
        index = row * 7 + col - self._first.weekday()
        days = calendar.monthrange(self._first.year, self._first.month)[1]
        if not 0 <= col < 7 or not 0 <= index < days:
            return None
        return self._first + timedelta(days=index)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        day = self._day_at(event.position())
        if day and day > date.today():
            day = None
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
        if day and day <= date.today() and event.button() == Qt.MouseButton.LeftButton:
            self.toggled.emit(day)

    def paintEvent(self, event) -> None:
        p = theme.palette
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cw, ch = self._geometry()

        painter.setFont(pixel_font(UI, 12, QFont.Weight.Medium))
        painter.setPen(QColor(p.faint))
        for col, name in enumerate(WEEKDAYS):
            painter.drawText(QRectF(col * cw, 0, cw, HEAD - 6), Qt.AlignmentFlag.AlignCenter, name)

        today = date.today()
        days = calendar.monthrange(self._first.year, self._first.month)[1]
        lead = self._first.weekday()
        for index in range(days):
            day = self._first + timedelta(days=index)
            row, col = divmod(lead + index, 7)
            box = QRectF(col * cw, HEAD + row * ch, cw, ch).adjusted(GAP / 2, GAP / 2, -GAP / 2, -GAP / 2)
            done = day in self._done
            future = day > today
            painter.setPen(Qt.PenStyle.NoPen)
            if done:
                painter.setBrush(QColor(p.accent_hover if day == self._hover else p.accent))
            elif day == self._hover:
                painter.setBrush(QColor(p.accent_soft))
            else:
                painter.setBrush(QColor(p.raised))
            painter.drawRoundedRect(box, 10, 10)
            if day == today and not done:
                painter.setPen(QPen(QColor(p.accent), 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(box.adjusted(1, 1, -1, -1), 9, 9)

            ink = p.accent_fg if done else (p.faint if future else p.text)
            painter.setFont(mono(13, QFont.Weight.DemiBold))
            painter.setPen(QColor(ink))
            corner = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
            painter.drawText(box.adjusted(10, 6, -8, -6), corner, str(day.day))
            if done:
                c = QPointF(box.right() - 16, box.bottom() - 15)
                tick = QPainterPath(QPointF(c.x() - 5, c.y()))
                tick.lineTo(c.x() - 1.5, c.y() + 3.5)
                tick.lineTo(c.x() + 5, c.y() - 3.5)
                painter.setPen(QPen(QColor(p.accent_fg), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                                    Qt.PenJoinStyle.RoundJoin))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(tick)


class StatCell(QWidget):
    def __init__(self, icon: str, caption: str) -> None:
        super().__init__()
        tile = QFrame()
        tile.setProperty("tile", True)
        tile.setFixedSize(34, 34)
        tile.setLayout(hbox(IconLabel(icon, "accent", 18), margins=(8, 8, 8, 8)))
        self.value: QLabel = label("0", "figure")
        self.setLayout(hbox(tile, vbox(self.value, label(caption, "caption"), spacing=0), None, spacing=10))


class HabitDetail(Card):
    """Right side: the selected habit's month, streaks and actions."""

    def __init__(self, page: HabitsPage) -> None:
        super().__init__()
        self.page = page
        self.habit: Habit | None = None
        self._first = date.today().replace(day=1)
        self.body.setContentsMargins(22, 20, 22, 20)
        self.body.setSpacing(16)

        self.name = ElidedLabel("", "title")
        self.editor = InlineEdit("", flat=False)
        self.editor.setMaxLength(60)
        self.editor.hide()
        self._editing = False
        self.editor.editingFinished.connect(lambda: self._finish(True))
        self.editor.cancelled.connect(lambda: self._finish(False))
        self._outside = OutsideClick(self.editor, lambda: self._finish(True))
        self.sub = label("", "muted")
        rename = icon_button("pencil", "Rename habit", self._begin_edit, size=16)
        self._outside.ignore(rename)
        delete = icon_button("trash", "Delete habit", self._delete, size=16)
        title = vbox(self.name, self.editor, self.sub, spacing=2)
        top = hbox(title, None, rename, delete, spacing=4)
        top.setStretch(0, 1)

        self.stats = {
            "streak": StatCell("flame", "Streak"),
            "best": StatCell("trophy", "Best"),
            "month": StatCell("calendar", "Month"),
        }
        strip = hbox(spacing=0)
        for i, cell in enumerate(self.stats.values()):
            if i:
                rule = QFrame()
                rule.setProperty("vrule", True)
                strip.addWidget(rule)
                strip.addSpacing(16)
            strip.addWidget(cell, 1)

        self.month_label = label("", "h2")
        nav = hbox(
            self.month_label,
            None,
            icon_button("chevron-left", "Previous month", lambda: self._shift(-1), size=18),
            icon_button("chevron-right", "Next month", lambda: self._shift(1), size=18),
            spacing=2,
        )
        self.month = HabitMonth()
        self.month.toggled.connect(self._toggle)

        self.body.addLayout(top)
        self.body.addLayout(strip)
        self.body.addWidget(divider())
        self.body.addLayout(nav)
        self.body.addWidget(self.month, 1)

    def show_habit(self, habit: Habit) -> None:
        if self.habit is None or self.habit.id != habit.id:
            self._first = date.today().replace(day=1)
            self._finish(True)  # switching habits keeps the rename in progress
        self.habit = habit
        self.refresh()

    def refresh(self) -> None:
        habit = self.habit
        if habit is None:
            return
        store = self.page.ctx.store
        today = date.today()
        every = store.habit_checks(habit.id, EPOCH, today)
        last = calendar.monthrange(self._first.year, self._first.month)[1]
        month_end = self._first.replace(day=last)
        in_month = {d for d in every if self._first <= d <= month_end}
        elapsed = last if month_end < today else (today.day if self._first <= today else 0)

        self.name.setText(habit.name)
        self.sub.setText("Done today" if habit.done_today else "Not done yet today")
        self.stats["streak"].value.setText(f"{habit.streak}d")
        self.stats["best"].value.setText(f"{best_streak(every)}d")
        self.stats["month"].value.setText(f"{len(in_month)}/{elapsed}" if elapsed else "0")
        self.month_label.setText(f"{self._first:%B %Y}")
        self.month.set_month(self._first, in_month)

    def _shift(self, months: int) -> None:
        self._first = shift_month(self._first, months)
        self.refresh()

    def _toggle(self, day: date) -> None:
        if self.habit:
            self.page.ctx.store.toggle_habit(self.habit.id, day)

    def _begin_edit(self) -> None:
        if self.habit is None:
            return
        if self._editing:
            self._finish(True)
            return
        self._editing = True
        self.name.hide()
        self.editor.setText(self.habit.name)
        self.editor.show()
        self.editor.setFocus()
        self.editor.selectAll()
        self._outside.start()

    def _finish(self, save: bool) -> None:
        if not self._editing:
            return
        self._editing = False
        self._outside.stop()
        text = self.editor.text().strip()
        habit = self.habit
        self.editor.hide()
        self.name.show()
        if save and habit and text and text != habit.name:
            self.name.setText(text)
            # Deferred: the store signal rebuilds this page, which must not happen mid-event.
            QTimer.singleShot(0, lambda: self.page.ctx.store.rename_habit(habit.id, text))

    def _delete(self) -> None:
        habit = self.habit
        if habit and confirm(
            self, "Delete habit", f"Delete “{habit.name}” and its history? This can't be undone."
        ):
            self.page.ctx.store.delete_habit(habit.id)
            self.page.ctx.toast("Habit deleted")


class HabitsPage(Page):
    def __init__(self, ctx: Context) -> None:
        super().__init__(ctx, "Habits", scroll=False)
        self._selected: int | None = None

        self.input = InlineEdit(placeholder="New habit, e.g. Read 20 minutes", flat=False)
        self.input.setMaxLength(60)
        self.input.returnPressed.connect(self._add)
        self.input.cancelled.connect(self.input.clear)

        self.rows = vbox(spacing=4)
        list_card = Card()
        list_card.setFixedWidth(LIST_WIDTH)
        list_card.body.setContentsMargins(12, 14, 12, 12)
        list_card.body.setSpacing(10)
        list_card.body.addWidget(self.input)
        list_card.body.addLayout(self.rows)
        list_card.body.addStretch(1)

        self.detail = HabitDetail(self)
        self.placeholder = Card()
        self.placeholder_box = QVBoxLayout()
        self.placeholder.body.addStretch(1)
        self.placeholder.body.addLayout(self.placeholder_box)
        self.placeholder.body.addStretch(1)

        columns = hbox(list_card, self.detail, self.placeholder, spacing=16)
        columns.setStretch(1, 1)
        columns.setStretch(2, 1)
        self.body.addLayout(columns, 1)

        ctx.store.changed.connect(self._on_changed)
        self._render()

    def focus_input(self) -> None:
        self.input.setFocus()

    def on_show(self) -> None:
        self._render()

    def _on_changed(self, domain: str) -> None:
        if domain == "habits":
            self._render()

    def _add(self) -> None:
        name = self.input.text().strip()
        if name:
            self.input.clear()
            self._selected = self.ctx.store.add_habit(name).id
            self._render()

    def _select(self, habit_id: int) -> None:
        self._selected = habit_id
        self._render()

    def _render(self) -> None:
        store = self.ctx.store
        habits = store.habits()
        if habits and all(h.id != self._selected for h in habits):
            self._selected = habits[0].id
        if not habits:
            self._selected = None

        clear(self.rows)
        for habit in habits:
            item = HabitItem(habit, habit.id == self._selected)
            item.clicked.connect(self._select)
            item.toggled.connect(lambda hid: store.toggle_habit(hid))
            self.rows.addWidget(item)

        selected = next((h for h in habits if h.id == self._selected), None)
        self.detail.setVisible(selected is not None)
        self.placeholder.setVisible(selected is None)
        if selected:
            self.detail.show_habit(selected)
            return
        clear(self.placeholder_box)
        self.placeholder_box.addWidget(
            EmptyState("target", "No habits yet", "Create one on the left, or start with an idea below.")
        )
        ideas = vbox(spacing=8)
        for name in SUGGESTIONS:
            chip = button(name, "secondary", icon="plus", on_click=lambda n=name: self._quick(n))
            ideas.addWidget(chip)
        holder = QWidget()
        holder.setFixedWidth(260)
        holder.setLayout(ideas)
        self.placeholder_box.addWidget(holder, 0, Qt.AlignmentFlag.AlignHCenter)

    def _quick(self, name: str) -> None:
        self._selected = self.ctx.store.add_habit(name).id
        self._render()
