from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import QEasingCurve, QRectF, QSize, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QFont, QKeySequence, QPainter, QPen, QShortcut
from PySide6.QtWidgets import QPushButton, QStackedWidget, QVBoxLayout, QWidget

from origami.context import Context
from origami.timer import LABELS, Mode
from origami.ui import icons
from origami.ui.components import (
    Card,
    Page,
    Ring,
    Segmented,
    WeekChart,
    button,
    divider,
    duration,
    hbox,
    icon_button,
    label,
    vbox,
)
from origami.ui.theme import UI, mono, pixel_font, theme

SIDE_WIDTH = 340
RING_SIZE = 250
ITEM = 42  # wheel row height
ROWS = 5  # visible rows per wheel
CAPTION = 26  # caption strip above the wheels
WHEEL_WIDTH = 84
COLON = 26
PAD = 14
DIAL_W = 3 * WHEEL_WIDTH + 2 * COLON + 2 * PAD
DIAL_H = CAPTION + ROWS * ITEM + 2 * PAD
PRESETS = ((5 * 60, "5m"), (10 * 60, "10m"), (15 * 60, "15m"), (25 * 60, "25m"), (45 * 60, "45m"),
           (60 * 60, "1h"))


def hms(seconds: int) -> str:
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"


class Wheel(QWidget):
    """One drum of an alarm-clock picker: scroll, drag, click or use the arrow keys."""

    changed = Signal(int)

    def __init__(self, count: int, caption: str) -> None:
        super().__init__()
        self._count = count
        self._caption = caption
        self._value = 0
        self._offset = 0.0
        self._press_y: float | None = None
        self._dragged = False
        self._wheel_acc = 0
        self._snap = QVariantAnimation(self)
        self._snap.setDuration(160)
        self._snap.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._snap.valueChanged.connect(self._on_snap)
        self.setFixedSize(WHEEL_WIDTH, CAPTION + ROWS * ITEM)
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        self.setCursor(Qt.CursorShape.SizeVerCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        theme.changed.connect(self.update)

    def value(self) -> int:
        return self._value

    def set_value(self, value: int) -> None:
        self._value = value % self._count
        self._offset = 0.0
        self.update()

    def step(self, steps: int) -> None:
        if steps:
            self._value = (self._value + steps) % self._count
            self.update()
            self.changed.emit(self._value)

    def _mid(self) -> float:
        return CAPTION + ROWS * ITEM / 2

    def _on_snap(self, value: float) -> None:
        self._offset = value
        self.update()

    def wheelEvent(self, event) -> None:
        self._wheel_acc += event.angleDelta().y()
        steps = int(self._wheel_acc / 120)
        if steps:
            self._wheel_acc -= steps * 120
            self.step(-steps)
        event.accept()

    def keyPressEvent(self, event) -> None:
        key = event.key()
        if key in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            self.step(-1 if key == Qt.Key.Key_Up else 1)
        elif key in (Qt.Key.Key_PageUp, Qt.Key.Key_PageDown):
            self.step(-5 if key == Qt.Key.Key_PageUp else 5)
        elif key in (Qt.Key.Key_Left, Qt.Key.Key_Right):
            self.focusNextPrevChild(key == Qt.Key.Key_Right)
        else:
            super().keyPressEvent(event)

    def focusInEvent(self, event) -> None:
        self.update()
        super().focusInEvent(event)

    def focusOutEvent(self, event) -> None:
        self.update()
        super().focusOutEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._snap.stop()
            self._press_y = event.position().y() - self._offset
            self._dragged = False
            self.setFocus()

    def mouseMoveEvent(self, event) -> None:
        if self._press_y is None:
            return
        offset = event.position().y() - self._press_y
        if abs(offset) > 4:
            self._dragged = True
        steps = round(-offset / ITEM)
        if steps:
            self._press_y -= steps * ITEM
            offset += steps * ITEM
            self.step(steps)
        self._offset = offset
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        if self._press_y is None:
            return
        self._press_y = None
        if not self._dragged and event.position().y() > CAPTION:
            self.step(round((event.position().y() - self._mid()) / ITEM))
        self._snap.stop()
        self._snap.setStartValue(self._offset)
        self._snap.setEndValue(0.0)
        self._snap.start()

    def paintEvent(self, event) -> None:
        pal = theme.palette
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        active = self.hasFocus() or self.underMouse()

        caption = pixel_font(UI, 11, QFont.Weight.Bold, scaled=False)
        caption.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.4)
        painter.setFont(caption)
        painter.setPen(QColor(pal.accent if active else pal.faint))
        painter.drawText(QRectF(0, 0, self.width(), CAPTION - 6), Qt.AlignmentFlag.AlignCenter, self._caption)

        painter.setClipRect(QRectF(0, CAPTION, self.width(), ROWS * ITEM))
        mid = self._mid()
        for i in range(-3, 4):
            y = mid + i * ITEM + self._offset
            distance = abs(y - mid) / ITEM
            if distance > 2.8:
                continue
            near = max(0.0, 1 - distance)
            weight = QFont.Weight.Bold if near > 0.5 else QFont.Weight.Medium
            painter.setFont(mono(round(22 + 18 * near), weight, scaled=False))
            painter.setPen(QColor(pal.text if near > 0.5 else pal.muted))
            painter.setOpacity(max(0.0, 1 - distance * 0.4))
            text = f"{(self._value + i) % self._count:02d}"
            painter.drawText(QRectF(0, y - ITEM / 2, self.width(), ITEM), Qt.AlignmentFlag.AlignCenter, text)


class TimeDial(QWidget):
    """Hours : minutes : seconds picker - three wheels over a highlighted band."""

    changed = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(DIAL_W, DIAL_H)
        self.hours = Wheel(24, "HOURS")
        self.minutes = Wheel(60, "MIN")
        self.seconds = Wheel(60, "SEC")
        row = hbox(self.hours, COLON, self.minutes, COLON, self.seconds, spacing=0, margins=(PAD,) * 4)
        self.setLayout(row)
        for wheel in (self.hours, self.minutes, self.seconds):
            wheel.changed.connect(lambda _: self.changed.emit(self.total()))
        theme.changed.connect(self.update)

    def total(self) -> int:
        return self.hours.value() * 3600 + self.minutes.value() * 60 + self.seconds.value()

    def set_total(self, seconds: int) -> None:
        hours, rest = divmod(seconds, 3600)
        minutes, secs = divmod(rest, 60)
        self.hours.set_value(hours)
        self.minutes.set_value(minutes)
        self.seconds.set_value(secs)

    def paintEvent(self, event) -> None:
        pal = theme.palette
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(pal.raised))
        painter.drawRoundedRect(QRectF(self.rect()), 20, 20)

        mid = PAD + CAPTION + ROWS * ITEM / 2
        band = QRectF(PAD - 4, mid - ITEM / 2 - 4, self.width() - 2 * PAD + 8, ITEM + 8)
        painter.setBrush(QColor(pal.surface))
        painter.setPen(QPen(QColor(pal.border), 1))
        painter.drawRoundedRect(band, 12, 12)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(pal.accent))
        for k in (1, 2):
            x = PAD + k * WHEEL_WIDTH + (k - 1) * COLON + COLON / 2
            for dy in (-7, 7):
                painter.drawEllipse(QRectF(x - 2.5, mid + dy - 2.5, 5, 5))


class WeekCard(Card):
    """Mon-Sun focus time for this week; a running session counts live."""

    def __init__(self, store, timer) -> None:
        super().__init__()
        self.store, self.timer = store, timer
        self.body.setContentsMargins(18, 16, 14, 14)
        self.body.setSpacing(12)
        self.total = label("0m", "stat")
        head = hbox(
            vbox(label("This week", "h2"), label("Total focus time", "caption"), spacing=0),
            None,
            self.total,
            spacing=8,
        )
        head.setAlignment(self.total, Qt.AlignmentFlag.AlignVCenter)
        self.chart = WeekChart()
        self.body.addLayout(head)
        self.body.addWidget(divider())
        self.body.addWidget(self.chart, 1)
        self._saved: list[tuple[date, int, int]] = []
        timer.tick.connect(lambda *_: self._paint())

    def refresh(self) -> None:
        self._saved = self.store.focus_week(date.today())
        self._paint()

    def _live_seconds(self) -> int:
        timer = self.timer
        if timer.mode is Mode.SHORT or not (timer.running or timer.remaining < timer.total):
            return 0
        return timer.elapsed()

    def _paint(self) -> None:
        if not self._saved or self._saved[0][0] != date.today() - timedelta(days=date.today().weekday()):
            self._saved = self.store.focus_week(date.today())
        live = self._live_seconds()
        today = date.today()
        days = [(d, n, s + live if d == today else s) for d, n, s in self._saved]
        self.total.setText(duration(sum(s for _, _, s in days)))
        self.chart.set_data(days)


def centered(*items, spacing: int) -> QWidget:
    row = QWidget()
    row.setLayout(hbox(*items, spacing=spacing))
    return row


class FocusPage(Page):
    def __init__(self, ctx: Context) -> None:
        super().__init__(ctx, "Focus", scroll=False)
        timer = ctx.timer
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        self.modes = Segmented([(mode.value, LABELS[mode]) for mode in Mode], timer.mode.value)
        self.modes.changed.connect(lambda key: timer.set_mode(Mode(key)))
        self.ring = Ring(RING_SIZE, 11)
        self.dial = TimeDial()
        self.dial.changed.connect(timer.set_custom)
        self.face = QStackedWidget()
        self.face.setFixedSize(max(DIAL_W, RING_SIZE), max(DIAL_H, RING_SIZE))
        for widget in (self.ring, self.dial):
            holder = QWidget()
            holder.setLayout(vbox(None, hbox(None, widget, None), None))
            self.face.addWidget(holder)

        self.play = QPushButton()
        self.play.setObjectName("PlayButton")
        self.play.setFixedSize(64, 64)
        self.play.setIconSize(QSize(24, 24))
        self.play.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.play.clicked.connect(timer.toggle)

        controls = centered(
            icon_button("reset", "Reset", timer.reset, size=20),
            self.play,
            icon_button("skip", "Skip", timer.skip, size=20),
            spacing=28,
        )
        self.presets = QWidget()
        chips = hbox(spacing=6)
        for seconds, text in PRESETS:
            chip = button(text, "secondary", on_click=lambda v=seconds: self._preset(v))
            chip.setProperty("size", "sm")
            chip.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            chips.addWidget(chip)
        self.presets.setLayout(chips)
        policy = self.presets.sizePolicy()
        policy.setRetainSizeWhenHidden(True)
        self.presets.setSizePolicy(policy)
        self.hint = label("", "caption")

        timer_card = Card()
        timer_card.body.setContentsMargins(20, 18, 20, 18)
        timer_card.body.setSpacing(14)
        timer_card.body.addStretch(1)
        for widget in (self.modes, self.face, controls, self.presets, self.hint):
            timer_card.body.addWidget(widget, 0, Qt.AlignmentFlag.AlignHCenter)
        timer_card.body.addStretch(1)

        self.week = WeekCard(ctx.store, timer)

        side = QVBoxLayout()
        side.setContentsMargins(0, 0, 0, 0)
        side.addWidget(self.week, 1)
        side_box = QWidget()
        side_box.setFixedWidth(SIDE_WIDTH)
        side_box.setLayout(side)

        columns = hbox(timer_card, side_box, spacing=14)
        columns.setStretch(0, 1)
        self.body.addLayout(columns, 1)

        space = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        space.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        space.activated.connect(timer.toggle)
        timer.tick.connect(self._tick)
        timer.state_changed.connect(self._sync)
        ctx.store.changed.connect(self._on_changed)
        theme.changed.connect(self._sync)
        self._sync()
        self._stats()

    def on_show(self) -> None:
        self._sync()
        self._stats()
        self.setFocus()

    def _on_changed(self, domain: str) -> None:
        if domain == "focus":
            self._stats()

    def _stats(self) -> None:
        self.week.refresh()

    def _preset(self, seconds: int) -> None:
        self.dial.set_total(seconds)
        self.ctx.timer.set_custom(seconds)

    def _editing(self) -> bool:
        timer = self.ctx.timer
        return timer.mode is Mode.CUSTOM and not timer.running and timer.remaining == timer.total

    def _tick(self, remaining: int, total: int) -> None:
        self.ring.set_value(remaining / total if total else 0, hms(remaining), LABELS[self.ctx.timer.mode])
        self._sync_face()

    def _sync_face(self) -> None:
        timer = self.ctx.timer
        editing = self._editing()
        if editing and self.face.currentIndex() != 1:
            self.dial.set_total(timer.total)
        self.face.setCurrentIndex(1 if editing else 0)
        self.presets.setVisible(editing)
        self.play.setEnabled(timer.remaining > 0)
        if editing:
            hint = "Scroll, drag or use the arrow keys to set the time"
        elif timer.mode is Mode.CUSTOM:
            hint = "Reset to change the time"
        else:
            hint = "Press Space to start or pause"
        self.hint.setText(hint)

    def _sync(self) -> None:
        timer = self.ctx.timer
        pal = theme.palette
        self.modes.set_value(timer.mode.value)
        self.ring.set_color(pal.success if timer.mode is Mode.SHORT else None)
        self._tick(timer.remaining, timer.total)
        self.play.setIcon(icons.icon("pause" if timer.running else "play", pal.accent_fg, 24))
        self.play.setToolTip("Pause" if timer.running else "Start")
