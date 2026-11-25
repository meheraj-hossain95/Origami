"""Weekly timetable: classes, meetings and routines that repeat every week (Mon-Sun grid)."""

from __future__ import annotations

from datetime import date, datetime, time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QMouseEvent, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QAbstractButton,
    QButtonGroup,
    QDialog,
    QFrame,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from origami.context import Context
from origami.store import SLOT_COLORS, Slot
from origami.ui.components import Card, Dropdown, Page, button, confirm, hbox, index_of, label, vbox
from origami.ui.pages.calendar import REMIND_OPTIONS, DayToggles
from origami.ui.theme import UI, mix, mono, pixel_font, theme

DAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
AXIS = 52
HEADER = 12  # room above 00:00 for its label (grid body; day names live in DayHeader)
BOTTOM = 12  # room under 24:00 for its label
DAY_HEADER = 44
HOUR_PX = 52  # all 24 hours are always available; the grid scrolls
# (light, dark) base colour per slot colour index
BASES = (
    ("#4F5BD5", "#7B86EC"),
    ("#2E6FD8", "#5B9BF0"),
    ("#0F8A8A", "#2BB3B0"),
    ("#2E8B4E", "#45B36B"),
    ("#D46B16", "#F0A050"),
    ("#C93C7E", "#E0619D"),
)


def slot_colors(index: int) -> tuple[str, str, str]:
    """(fill, bar, ink) for a slot colour index in the current theme."""
    p = theme.palette
    base = BASES[index % SLOT_COLORS][1 if p.dark else 0]
    fill = mix(base, p.surface, 0.22 if p.dark else 0.13)
    ink = mix(base, p.text, 0.80 if p.dark else 0.70)
    return fill, base, ink


def _minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def time_options(first: int = 0, last: int = 24 * 60 - 15) -> list[time]:
    return [time(m // 60, m % 60) for m in range(first, last + 1, 15)]


class WeekGrid(QWidget):
    slot_clicked = Signal(object)
    empty_clicked = Signal(int, object)  # weekday, time

    def __init__(self) -> None:
        super().__init__()
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(560)
        self.setFixedHeight(HEADER + 24 * HOUR_PX + BOTTOM)
        self._slots: list[Slot] = []
        self._boxes: list[tuple[QRectF, Slot]] = []
        self._hover_slot: int | None = None
        self._hover_cell: tuple[int, int] | None = None  # (day, half-hour index)
        theme.changed.connect(self.update)
        self._clock = QTimer(self, interval=60_000, timeout=self.update)
        self._clock.start()

    def set_slots(self, slots: list[Slot]) -> None:
        self._slots = slots
        self.update()

    def _metrics(self) -> tuple[float, float, int, int]:
        return (self.width() - AXIS) / 7, float(HOUR_PX), 0, 24

    def y_for(self, minutes: int) -> int:
        return round(self._y(minutes))

    def _y(self, minutes: int) -> float:
        _, hour, first, _ = self._metrics()
        return HEADER + (minutes - first * 60) / 60 * hour

    def _layout_boxes(self) -> list[tuple[QRectF, Slot]]:
        col, _, _, _ = self._metrics()
        boxes: list[tuple[QRectF, Slot]] = []
        for day in range(7):
            todays = sorted((s for s in self._slots if s.day == day), key=lambda s: (s.start, s.end))
            # Split the day into clusters of overlapping slots; only those share the column width.
            clusters: list[list[Slot]] = []
            cluster_end = -1
            for s in todays:
                if _minutes(s.start) >= cluster_end:
                    clusters.append([])
                clusters[-1].append(s)
                cluster_end = max(cluster_end, _minutes(s.end))
            for cluster in clusters:
                lanes: list[int] = []  # end minute per lane
                placed: list[tuple[Slot, int]] = []
                for s in cluster:
                    lane = next((i for i, end in enumerate(lanes) if end <= _minutes(s.start)), len(lanes))
                    if lane == len(lanes):
                        lanes.append(0)
                    lanes[lane] = _minutes(s.end)
                    placed.append((s, lane))
                width = (col - 6) / len(lanes)
                for s, lane in placed:
                    x = AXIS + day * col + 3 + lane * width
                    top, bottom = self._y(_minutes(s.start)), self._y(_minutes(s.end))
                    boxes.append((QRectF(x, top + 1, width - 2, max(bottom - top - 2, 16)), s))
        return boxes

    def _cell_at(self, pos: QPointF) -> tuple[int, time] | None:
        col, hour, first, last = self._metrics()
        if pos.x() < AXIS or pos.y() < HEADER:
            return None
        day = min(int((pos.x() - AXIS) // col), 6)
        minutes = first * 60 + int((pos.y() - HEADER) / hour * 2) * 30
        if minutes >= last * 60:
            return None
        return day, time(minutes // 60, minutes % 60)

    def _slot_at(self, pos: QPointF) -> Slot | None:
        return next((s for box, s in reversed(self._boxes) if box.contains(pos)), None)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.position()
        slot = self._slot_at(pos)
        cell = None if slot else self._cell_at(pos)
        key = (cell[0], _minutes(cell[1]) // 30) if cell else None
        hover = slot.id if slot else None
        if hover != self._hover_slot or key != self._hover_cell:
            self._hover_slot, self._hover_cell = hover, key
            shape = Qt.CursorShape.PointingHandCursor if (slot or cell) else Qt.CursorShape.ArrowCursor
            self.setCursor(shape)
            if slot:
                where = f"\n{slot.location}" if slot.location else ""
                self.setToolTip(f"{slot.title}\n{slot.start:%H:%M}–{slot.end:%H:%M}{where}")
            else:
                self.setToolTip("")
            self.update()

    def leaveEvent(self, event) -> None:
        self._hover_slot = self._hover_cell = None
        self.update()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        pos = event.position()
        slot = self._slot_at(pos)
        if slot:
            self.slot_clicked.emit(slot)
        elif cell := self._cell_at(pos):
            self.empty_clicked.emit(*cell)

    def paintEvent(self, event) -> None:
        p = theme.palette
        col, hour, first, last = self._metrics()
        today = date.today().weekday()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # today's column tint
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(mix(p.accent, p.surface, 0.05 if not p.dark else 0.08)))
        painter.drawRect(QRectF(AXIS + today * col, HEADER, col, self.height() - HEADER - BOTTOM))

        # hour lines + labels (half hours as faint dashes)
        painter.setFont(mono(11, QFont.Weight.Normal))
        for h in range(first, last + 1):
            y = HEADER + (h - first) * hour
            painter.setPen(QPen(QColor(p.border), 1))
            painter.drawLine(QPointF(AXIS - 4, y + 0.5), QPointF(self.width(), y + 0.5))
            if h < last:
                painter.setPen(QPen(QColor(mix(p.border, p.surface, 0.55)), 1, Qt.PenStyle.DashLine))
                half = y + hour / 2
                painter.drawLine(QPointF(AXIS, half + 0.5), QPointF(self.width(), half + 0.5))
            painter.setPen(QColor(p.faint))
            painter.drawText(
                QRectF(0, y - 8, AXIS - 10, 16),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"{h % 24:02d}:00",
            )
        painter.setPen(QPen(QColor(p.border), 1))
        for day in range(8):
            x = AXIS + day * col
            painter.drawLine(QPointF(x + 0.5, HEADER), QPointF(x + 0.5, self.height() - BOTTOM))

        # hovered empty half hour
        if self._hover_cell:
            day, half = self._hover_cell
            top = self._y(half * 30)
            cell = QRectF(AXIS + day * col + 3, top + 1, col - 6, hour / 2 - 2)
            painter.setPen(QPen(QColor(p.accent), 1, Qt.PenStyle.DashLine))
            painter.setBrush(QColor(p.accent_soft))
            painter.drawRoundedRect(cell, 6, 6)
            painter.setPen(QColor(p.accent))
            painter.setFont(pixel_font(UI, 11, QFont.Weight.DemiBold))
            painter.drawText(cell, Qt.AlignmentFlag.AlignCenter, f"+ {half // 2:02d}:{half % 2 * 30:02d}")

        # slots
        self._boxes = self._layout_boxes()
        title_font = pixel_font(UI, 12, QFont.Weight.DemiBold)
        small = pixel_font(UI, 11, QFont.Weight.Normal)
        tm, sm = QFontMetrics(title_font), QFontMetrics(small)
        for box, s in self._boxes:
            fill, bar, ink = slot_colors(s.color)
            hovered = s.id == self._hover_slot
            path = QPainterPath()
            path.addRoundedRect(box, 6, 6)
            painter.fillPath(path, QColor(mix(bar, fill, 0.18) if hovered else fill))
            painter.save()
            painter.setClipPath(path)
            painter.fillRect(QRectF(box.x(), box.y(), 3, box.height()), QColor(bar))
            text = box.adjusted(8, 4, -4, -2)
            if box.height() < tm.height() + sm.height() + 6:
                # Short slot: one line, vertically centred.
                painter.setFont(title_font)
                painter.setPen(QColor(ink))
                line = f"{s.title}  {s.start:%H:%M}"
                metrics_text = tm.elidedText(line, Qt.TextElideMode.ElideRight, int(text.width()))
                painter.drawText(
                    box.adjusted(8, 0, -4, 0),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    metrics_text,
                )
                painter.restore()
                continue
            lines = [(s.title, title_font, tm, ink)]
            lines.append((f"{s.start:%H:%M}–{s.end:%H:%M}", small, sm, ink))
            if s.location:
                lines.append((s.location, small, sm, ink))
            y = text.y()
            for content, font, metrics, color in lines:
                if y + metrics.height() > text.bottom() + 2 and y != text.y():
                    break
                painter.setFont(font)
                painter.setPen(QColor(color))
                elided = metrics.elidedText(content, Qt.TextElideMode.ElideRight, int(text.width()))
                painter.drawText(QRectF(text.x(), y, text.width(), metrics.height()), 0, elided)
                y += metrics.height()
            painter.restore()

        # current time
        now = datetime.now()
        minutes = now.hour * 60 + now.minute
        if first * 60 <= minutes <= last * 60:
            y = self._y(minutes)
            x0 = AXIS + today * col
            painter.setPen(QPen(QColor(p.danger), 2))
            painter.drawLine(QPointF(x0, y), QPointF(x0 + col, y))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(p.danger))
            painter.drawEllipse(QPointF(x0, y), 4, 4)


class DayHeader(QWidget):
    """Day names above the scrolling grid, aligned to its columns; today in an accent pill."""

    def __init__(self) -> None:
        super().__init__()
        self.setFixedHeight(DAY_HEADER)
        theme.changed.connect(self.update)
        QTimer(self, interval=60_000, timeout=self.update).start()

    def paintEvent(self, event) -> None:
        p = theme.palette
        col = (self.width() - AXIS) / 7
        today = date.today().weekday()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(pixel_font(UI, 12, QFont.Weight.DemiBold))
        for day in range(7):
            cell = QRectF(AXIS + day * col, 0, col, DAY_HEADER)
            if day == today:
                pill = QRectF(cell.center().x() - 24, (DAY_HEADER - 24) / 2, 48, 24)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(p.accent))
                painter.drawRoundedRect(pill, 12, 12)
                painter.setPen(QColor(p.accent_fg))
            else:
                painter.setPen(QColor(p.muted))
            painter.drawText(cell, Qt.AlignmentFlag.AlignCenter, DAY_NAMES[day])
        painter.setPen(QPen(QColor(p.border), 1))
        painter.drawLine(QPointF(0, self.height() - 0.5), QPointF(self.width(), self.height() - 0.5))


class Swatch(QAbstractButton):
    def __init__(self, index: int) -> None:
        super().__init__()
        self.index = index
        self.setCheckable(True)
        self.setFixedSize(26, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        theme.changed.connect(self.update)

    def paintEvent(self, event) -> None:
        _, base, _ = slot_colors(self.index)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)
        if self.isChecked():
            painter.setPen(QPen(QColor(base), 2))
            painter.drawEllipse(rect)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(base))
        painter.drawEllipse(rect.adjusted(4, 4, -4, -4))


class SlotDialog(QDialog):
    """Create or edit a timetable slot."""

    def __init__(self, parent: QWidget, slot: Slot | None, day: int, start: time) -> None:
        super().__init__(parent, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("Confirm")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedWidth(420)
        self.deleted = False

        self.title = QLineEdit(slot.title if slot else "")
        self.title.setPlaceholderText("Title, e.g. Statistics lecture or Team standup")
        self.title.setMaxLength(80)
        self.location = QLineEdit(slot.location if slot else "")
        self.location.setPlaceholderText("Location or link (optional)")
        self.location.setMaxLength(120)
        self.days = DayToggles()
        self.days.set_days((slot.day,) if slot else (day,))
        self.start = Dropdown()
        self.end = Dropdown()
        for t in time_options():
            self.start.addItem(f"{t:%H:%M}", t)
        for t in [*time_options(15), time(23, 59)]:
            self.end.addItem(f"{t:%H:%M}", t)
        begin = slot.start if slot else start
        finish = slot.end if slot else time(min(begin.hour + 1, 23), begin.minute)
        self.start.setCurrentIndex(max(index_of(self.start, begin), 0))
        self.end.setCurrentIndex(max(index_of(self.end, finish), 0))
        self.start.currentIndexChanged.connect(self._keep_order)
        self.remind = Dropdown()
        for text, minutes in REMIND_OPTIONS[:-1]:  # "1 day before" makes little sense weekly
            self.remind.addItem(text, minutes)
        self.remind.setCurrentIndex(max(index_of(self.remind, slot.remind if slot else None), 0))
        self.colors = QButtonGroup(self)
        swatches = hbox(spacing=4)
        for i in range(SLOT_COLORS):
            sw = Swatch(i)
            self.colors.addButton(sw, i)
            swatches.addWidget(sw)
        swatches.addStretch(1)
        self.colors.button((slot.color if slot else 0) % SLOT_COLORS).setChecked(True)
        self.error = label("", "error")
        self.error.hide()

        card = Card()
        card.body.setContentsMargins(24, 22, 24, 20)
        card.body.setSpacing(12)
        card.body.addWidget(label("Edit slot" if slot else "Add to timetable", "title"))
        card.body.addWidget(self.title)
        card.body.addWidget(self.location)
        card.body.addLayout(self._field("Repeats every", self.days))
        times = hbox(self.start, label("to", "muted"), self.end, None, spacing=8)
        card.body.addLayout(self._field("Time", times))
        card.body.addLayout(self._field("Reminder", hbox(self.remind, None)))
        card.body.addLayout(self._field("Colour", swatches))
        card.body.addWidget(self.error)
        card.body.addSpacing(6)
        actions = hbox(spacing=8)
        if slot:
            actions.addWidget(button("Delete", "danger", on_click=self._delete))
        actions.addStretch(1)
        actions.addWidget(button("Cancel", "secondary", on_click=self.reject))
        actions.addWidget(button("Save" if slot else "Add", on_click=self._accept))
        card.body.addLayout(actions)
        shell = QVBoxLayout(self)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.addWidget(card)
        self.title.returnPressed.connect(self._accept)
        self.adjustSize()
        anchor = parent.window().frameGeometry().center()
        self.move(anchor - self.rect().center())
        self.title.setFocus()

    @staticmethod
    def _field(name: str, control) -> object:
        caption = label(name, "caption")
        caption.setFixedWidth(92)
        row = hbox(caption, control, spacing=8)
        row.setStretch(1, 1)
        return row

    def _keep_order(self) -> None:
        start, end = self.start.currentData(), self.end.currentData()
        if end <= start:
            target = time(min(start.hour + 1, 23), start.minute if start.hour < 23 else 59)
            found = index_of(self.end, target)
            self.end.setCurrentIndex(found if found >= 0 else self.end.count() - 1)

    def _fail(self, text: str) -> None:
        self.error.setText(text)
        self.error.show()

    def _accept(self) -> None:
        if not self.title.text().strip():
            self.title.setFocus()
            return self._fail("Give it a title.")
        if not self.days.days():
            return self._fail("Pick at least one day.")
        if self.end.currentData() <= self.start.currentData():
            return self._fail("End time must be after the start.")
        self.accept()

    def _delete(self) -> None:
        self.deleted = True
        self.accept()

    def values(self) -> dict:
        return {
            "title": self.title.text().strip(),
            "location": self.location.text().strip(),
            "days": self.days.days(),
            "start": self.start.currentData(),
            "end": self.end.currentData(),
            "color": self.colors.checkedId(),
            "remind": self.remind.currentData(),
        }


class TimetablePage(Page):
    def __init__(self, ctx: Context) -> None:
        super().__init__(ctx, "Timetable", scroll=False)
        self.grid = WeekGrid()
        self.grid.slot_clicked.connect(self._edit)
        self.grid.empty_clicked.connect(self._add)
        self.area = QScrollArea()
        self.area.setWidgetResizable(True)
        self.area.setFrameShape(QFrame.Shape.NoFrame)
        self.area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.area.setWidget(self.grid)
        self.area.viewport().setAutoFillBackground(False)
        self.grid.setAutoFillBackground(False)
        bar = self.area.verticalScrollBar().sizeHint().width()
        frame = QFrame()
        frame.setProperty("group", True)
        frame.setLayout(
            vbox(hbox(DayHeader(), margins=(0, 0, bar, 0)), self.area, spacing=0, margins=(6, 0, 2, 2))
        )
        self.body.addWidget(frame, 1)
        self._scrolled = False
        ctx.store.changed.connect(lambda domain: domain == "timetable" and self._reload())
        self._reload()

    def on_show(self) -> None:
        self._reload()
        if not self._scrolled:
            self._scrolled = True
            QTimer.singleShot(0, self.scroll_to_now)

    def scroll_to_now(self) -> None:
        """Open where the day is: two hours before now, so night owls and early birds both land right."""
        now = datetime.now()
        top = self.grid.y_for(max(0, now.hour * 60 + now.minute - 120)) - 4
        self.area.verticalScrollBar().setValue(top)

    def _reload(self) -> None:
        self.grid.set_slots(self.ctx.store.timetable())

    def _add(self, day: int, start: time) -> None:
        dialog = SlotDialog(self, None, day, start)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        v = dialog.values()
        self.ctx.store.add_slots(
            v["title"], v["days"], v["start"], v["end"],
            location=v["location"], color=v["color"], remind=v["remind"],
        )
        count = len(v["days"])
        self.ctx.toast(f"Added on {count} days" if count > 1 else "Added to timetable")

    def _edit(self, slot: Slot) -> None:
        dialog = SlotDialog(self, slot, slot.day, slot.start)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        store = self.ctx.store
        if dialog.deleted:
            if confirm(self, "Delete slot", f"Remove “{slot.title}” on {DAY_NAMES[slot.day]}s?"):
                store.delete_slot(slot.id)
                self.ctx.toast("Removed from timetable")
            return
        v = dialog.values()
        days = v["days"]
        keep = slot.day if slot.day in days else days[0]
        store.update_slot(
            slot.id, v["title"], keep, v["start"], v["end"],
            location=v["location"], color=v["color"], remind=v["remind"],
        )
        extra = tuple(d for d in days if d != keep)
        if extra:
            store.add_slots(
                v["title"], extra, v["start"], v["end"],
                location=v["location"], color=v["color"], remind=v["remind"],
            )
        self.ctx.toast("Timetable updated")
