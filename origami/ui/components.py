from __future__ import annotations

import contextlib
import html
from collections.abc import Callable, Sequence
from datetime import date, datetime, time, timedelta

from PySide6.QtCore import (
    QCoreApplication,
    QEasingCurve,
    QEvent,
    QObject,
    QPoint,
    QPointF,
    QPropertyAnimation,
    QRect,
    QRectF,
    QSize,
    Qt,
    QTimer,
    QVariantAnimation,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPalette,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QAbstractButton,
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLayout,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from origami import timefmt
from origami.context import Context
from origami.ui import icons
from origami.ui.theme import PRIORITY_COLORS, UI, event_tint, mono, pixel_font, theme

SPACING = {"eyebrow": 0.6}
TABULAR = frozenset({"mono", "stat"})


def label(text: str = "", role: str | None = None, *, wrap: bool = False) -> QLabel:
    """Labels are plain text: a title like "<b>x</b>" is shown as typed, never rendered as HTML."""
    w = QLabel(text.upper() if role == "eyebrow" else text)
    w.setTextFormat(Qt.TextFormat.PlainText)
    _apply_role(w, role)
    w.setWordWrap(wrap)
    return w


def _apply_role(w: QLabel, role: str | None) -> None:
    if role is None:
        return
    w.setProperty("role", role)
    if role in SPACING or role in TABULAR:
        font = w.font()
        if role in SPACING:
            font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, SPACING[role])
        if role in TABULAR:
            with contextlib.suppress(AttributeError):
                font.setFeature(QFont.Tag("tnum"), 1)
        w.setFont(font)


def plain_tip(text: str) -> str:
    """Tooltip text that shows user content literally (tooltips otherwise sniff for HTML)."""
    return f"<p style='white-space:pre'>{html.escape(text)}</p>" if text else ""


def clock(seconds: int) -> str:
    hours, rest = divmod(seconds, 3600)
    if hours:
        return f"{hours}:{rest // 60:02d}:{rest % 60:02d}"
    return f"{rest // 60:02d}:{rest % 60:02d}"


class _Tint(QObject):
    def __init__(
        self, target: QAbstractButton, name: str, color: str, checked: str | None, size: int, pad: int
    ) -> None:
        super().__init__(target)
        self._target, self._name, self._color, self._checked = target, name, color, checked
        self._size, self._pad = size, pad
        theme.changed.connect(self.apply)
        if target.isCheckable():
            target.toggled.connect(self.apply)
        self.apply()

    def apply(self, *_: object) -> None:
        attr = self._checked if self._checked and self._target.isChecked() else self._color
        self._target.setIcon(icons.icon(self._name, getattr(theme.palette, attr), self._size, self._pad))


def bind_icon(
    target: QAbstractButton,
    name: str,
    color: str = "muted",
    *,
    checked: str | None = None,
    size: int = 16,
    pad: int = 0,
) -> None:
    _Tint(target, name, color, checked, size, pad)


def button(
    text: str, variant: str = "primary", *, icon: str | None = None, on_click: Callable | None = None
) -> QPushButton:
    b = QPushButton(text)
    b.setProperty("variant", variant)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    if icon:
        pad = 6 if text else 0
        bind_icon(b, icon, "accent_fg" if variant == "primary" else "muted", size=16, pad=pad)
        b.setIconSize(QSize(16 + pad, 16))
    if on_click:
        b.clicked.connect(lambda _=False: on_click())
    return b


def icon_button(name: str, tooltip: str, on_click: Callable | None = None, *, size: int = 16) -> QToolButton:
    b = QToolButton()
    b.setProperty("iconButton", True)
    b.setToolTip(tooltip)
    b.setAccessibleName(tooltip)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setIconSize(QSize(size, size))
    bind_icon(b, name, "muted", size=size)
    if on_click:
        b.clicked.connect(lambda _=False: on_click())
    return b


def show_if(w: QWidget, visible: bool) -> None:
    """setVisible that never turns a parentless widget into a flashing top-level window."""
    if visible and w.parentWidget() is None:
        return
    w.setVisible(visible)


def divider() -> QFrame:
    line = QFrame()
    line.setProperty("divider", True)
    line.setFixedHeight(1)
    return line


def clear(layout: QLayout) -> None:
    while (item := layout.takeAt(0)) is not None:
        if (w := item.widget()) is not None:
            w.hide()  # explicit hide stops Qt's queued show from popping it up as a loose window
            w.setParent(None)
            w.deleteLater()
        elif (child := item.layout()) is not None:
            clear(child)
            child.deleteLater()


def _fill(
    box: QHBoxLayout | QVBoxLayout, items: tuple, spacing: int, margins: tuple[int, int, int, int]
) -> None:
    box.setSpacing(spacing)
    box.setContentsMargins(*margins)
    for item in items:
        if item is None:
            box.addStretch(1)
        elif isinstance(item, int):
            box.addSpacing(item)
        elif isinstance(item, QLayout):
            box.addLayout(item)
        else:
            box.addWidget(item)


def hbox(
    *items: QWidget | QLayout | int | None,
    spacing: int = 8,
    margins: tuple[int, int, int, int] = (0, 0, 0, 0),
) -> QHBoxLayout:
    box = QHBoxLayout()
    _fill(box, items, spacing, margins)
    return box


def vbox(
    *items: QWidget | QLayout | int | None,
    spacing: int = 8,
    margins: tuple[int, int, int, int] = (0, 0, 0, 0),
) -> QVBoxLayout:
    box = QVBoxLayout()
    _fill(box, items, spacing, margins)
    return box


class ElidedLabel(QLabel):
    def __init__(
        self, text: str = "", role: str | None = None, mode: Qt.TextElideMode = Qt.TextElideMode.ElideRight
    ) -> None:
        super().__init__(text)
        _apply_role(self, role)
        self._mode = mode

    def minimumSizeHint(self) -> QSize:
        return QSize(0, super().minimumSizeHint().height())

    def paintEvent(self, event) -> None:
        rect = self.contentsRect()
        painter = QPainter(self)
        painter.setFont(self.font())
        painter.setPen(self.palette().color(QPalette.ColorRole.WindowText))
        text = QFontMetrics(self.font()).elidedText(self.text(), self._mode, rect.width())
        painter.drawText(rect, int(self.alignment()), text)


class IconLabel(QLabel):
    def __init__(self, name: str, color: str = "muted", size: int = 18) -> None:
        super().__init__()
        self._name, self._color, self._size = name, color, size
        self.setFixedSize(size, size)
        theme.changed.connect(self._tint)
        self._tint()

    def set_color(self, color: str) -> None:
        self._color = color
        self._tint()

    def set_name(self, name: str) -> None:
        if name != self._name:
            self._name = name
            self._tint()

    def _tint(self) -> None:
        self.setPixmap(icons.pixmap(self._name, getattr(theme.palette, self._color), self._size))


class BrandMark(QWidget):
    """The Origami fox as a one-colour watermark, tinted with a palette colour so it suits any theme."""

    def __init__(self, size: int = 28, color: str = "accent") -> None:
        super().__init__()
        from origami import ASSETS

        self._mask = QPixmap(str(ASSETS / "mark.png"))
        self._color = color
        self.setFixedSize(size, size)
        theme.changed.connect(self.update)

    def paintEvent(self, event) -> None:
        dpr = self.devicePixelRatioF()
        size = self.size() * dpr
        tinted = QPixmap(size)
        tinted.fill(Qt.GlobalColor.transparent)
        p = QPainter(tinted)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        smooth = Qt.TransformationMode.SmoothTransformation
        p.drawPixmap(tinted.rect(), self._mask.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, smooth))
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        p.fillRect(tinted.rect(), QColor(getattr(theme.palette, self._color)))
        p.end()
        tinted.setDevicePixelRatio(dpr)
        QPainter(self).drawPixmap(0, 0, tinted)


class Card(QFrame):
    clicked = Signal()

    def __init__(self, title: str | None = None, *, interactive: bool = False, eyebrow: bool = True) -> None:
        super().__init__()
        self.setProperty("card", True)
        self.setProperty("interactive", interactive)
        self._interactive = interactive
        if interactive:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(18, 16, 18, 16)
        self.body.setSpacing(12)
        if title:
            self.body.addWidget(label(title, "eyebrow" if eyebrow else "h2"))

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if (
            self._interactive
            and event.button() == Qt.MouseButton.LeftButton
            and self.rect().contains(event.position().toPoint())
        ):
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class Segmented(QFrame):
    changed = Signal(str)

    def __init__(self, options: Sequence[tuple[str, str]], value: str | None = None) -> None:
        super().__init__()
        self.setObjectName("Segmented")
        self._keys = [key for key, _ in options]
        self._group = QButtonGroup(self)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(2)
        for i, (_, text) in enumerate(options):
            b = QPushButton(text)
            b.setCheckable(True)
            b.setProperty("segment", True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            self._group.addButton(b, i)
            row.addWidget(b)
        self._group.idClicked.connect(lambda i: self.changed.emit(self._keys[i]))
        self.set_value(value if value is not None else self._keys[0])

    def value(self) -> str:
        return self._keys[self._group.checkedId()]

    def set_value(self, key: str) -> None:
        self._group.button(self._keys.index(key)).setChecked(True)


class Switch(QAbstractButton):
    """On/off toggle: an accent pill when on, a quiet grey one when off."""

    def __init__(self, checked: bool = False) -> None:
        super().__init__()
        self.setCheckable(True)
        self.setChecked(checked)
        self.setFixedSize(36, 20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)  # keyboard focus only, so clicks leave no ring
        theme.changed.connect(self.update)

    def paintEvent(self, event) -> None:
        p = theme.palette
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(p.accent if self.isChecked() else p.border_strong))
        painter.drawRoundedRect(QRectF(self.rect()), 10, 10)
        painter.setBrush(QColor("#FFFFFF"))
        x = self.width() - 18 if self.isChecked() else 2
        painter.drawEllipse(QRectF(x, 2, 16, 16))
        if self.hasFocus() and self.focusPolicy() != Qt.FocusPolicy.NoFocus:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(p.accent), 1.5))
            painter.drawRoundedRect(QRectF(self.rect()).adjusted(0.75, 0.75, -0.75, -0.75), 9.25, 9.25)


class Ring(QWidget):
    def __init__(self, size: int = 120, thickness: int = 8) -> None:
        super().__init__()
        self.setFixedSize(size, size)
        self._thickness = thickness
        self._fraction = 0.0
        self._text = ""
        self._sub = ""
        self._color: str | None = None
        theme.changed.connect(self.update)

    def set_value(self, fraction: float, text: str = "", sub: str = "") -> None:
        self._fraction = min(max(fraction, 0.0), 1.0)
        self._text, self._sub = text, sub
        self.update()

    def set_color(self, color: str | None) -> None:
        self._color = color
        self.update()

    def paintEvent(self, event) -> None:
        p = theme.palette
        size = self.width()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        inset = self._thickness / 2
        rect = QRectF(inset, inset, size - self._thickness, size - self._thickness)
        pen = QPen(QColor(p.border), self._thickness, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawEllipse(rect)
        if self._fraction > 0:
            pen.setColor(QColor(self._color or p.accent))
            painter.setPen(pen)
            painter.drawArc(rect, 90 * 16, -round(self._fraction * 360 * 16))
        if not self._text:
            return
        main_font = mono(round(size * 0.2), scaled=False)
        sub_font = pixel_font(UI, max(9, round(size * 0.09)), QFont.Weight.Normal, scaled=False)
        main_h = QFontMetrics(main_font).height()
        sub_h = QFontMetrics(sub_font).height() if self._sub else 0
        top = (size - main_h - sub_h) / 2
        painter.setFont(main_font)
        painter.setPen(QColor(p.text))
        painter.drawText(QRectF(0, top, size, main_h), Qt.AlignmentFlag.AlignCenter, self._text)
        if self._sub:
            painter.setFont(sub_font)
            painter.setPen(QColor(p.muted))
            painter.drawText(QRectF(0, top + main_h, size, sub_h), Qt.AlignmentFlag.AlignCenter, self._sub)


class CheckDot(QAbstractButton):
    def __init__(self, checked: bool = False, size: int = 20, name: str = "") -> None:
        super().__init__()
        self.setCheckable(True)
        self.setChecked(checked)
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        if name:
            self.setAccessibleName(name)
        self.priority = 0  # >0 rings the dot in that priority's colour, for tinted rows
        theme.changed.connect(self.update)

    def paintEvent(self, event) -> None:
        p = theme.palette
        hover = (self.underMouse() or self.hasFocus()) and self.isEnabled()
        ring = PRIORITY_COLORS(p)[min(self.priority, 2)] if self.priority else p.border_strong
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(self.width() / 20, self.height() / 20)
        rect = QRectF(0, 0, 20, 20).adjusted(1, 1, -1, -1)
        if self.isChecked():
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(p.accent_hover if hover else p.accent))
            painter.drawEllipse(rect)
        else:
            painter.setPen(QPen(QColor(p.accent if hover else ring), 1.5))
            painter.setBrush(QColor(p.accent_soft) if hover else Qt.BrushStyle.NoBrush)
            painter.drawEllipse(rect)
        if self.isChecked() or hover:
            tick = QPainterPath(QPointF(6, 10.4))
            tick.lineTo(8.9, 13.2)
            tick.lineTo(14, 7.4)
            color = QColor(p.accent_fg if self.isChecked() else p.accent)
            painter.setPen(
                QPen(color, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            )
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(tick)


class EmptyState(QWidget):
    def __init__(self, icon: str, title: str, hint: str = "") -> None:
        super().__init__()
        tile = QFrame()
        tile.setProperty("dateblock", True)
        tile.setFixedSize(44, 44)
        tile.setLayout(hbox(IconLabel(icon, "muted", 22), margins=(11, 11, 11, 11)))
        column = vbox(tile, 4, label(title, "h2"), spacing=4, margins=(0, 24, 0, 24))
        if hint:
            column.addWidget(label(hint, "muted"))
        for i in range(column.count()):
            if (w := column.itemAt(i).widget()) is not None:
                column.setAlignment(w, Qt.AlignmentFlag.AlignHCenter)
        self.setLayout(column)


def retone(w: QWidget, tone: str | None) -> None:
    if w.property("tone") == tone:
        return
    w.setProperty("tone", tone)
    w.style().unpolish(w)
    w.style().polish(w)


class Badge(QLabel):
    def __init__(self) -> None:
        super().__init__()
        self.setProperty("role", "badge")
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_text("")

    def set_text(self, text: str) -> None:
        self.setText(text)
        show_if(self, text not in ("", "0"))


def duration(seconds: int, *, compact: bool = False) -> str:
    """1h 35m / 45m / 0m. compact drops the space: 1h35."""
    hours, minutes = divmod(max(0, seconds) // 60, 60)
    if not hours:
        return f"{minutes}m"
    if compact:
        return f"{hours}h{minutes:02d}" if minutes else f"{hours}h"
    return f"{hours}h {minutes}m" if minutes else f"{hours}h"


def _nice_step(peak_minutes: float) -> int:
    for step in (15, 30, 60, 120, 180, 240, 360, 480):
        if step * 4 >= peak_minutes:
            return step
    return 720


class WeekChart(QWidget):
    """Monday-to-Sunday focus minutes with a labelled time axis, value labels and hover details."""

    AXIS = 40
    TOP = 22
    BOTTOM = 26

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumHeight(190)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self._days: list[tuple[date, int, int]] = []
        self._hover: int | None = None
        theme.changed.connect(self.update)

    def set_data(self, days: list[tuple[date, int, int]]) -> None:
        self._days = days
        self.update()

    def _slot(self) -> float:
        return (self.width() - self.AXIS) / max(len(self._days), 1)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        x = event.position().x() - self.AXIS
        index = int(x // self._slot()) if x >= 0 else None
        if index is not None and not 0 <= index < len(self._days):
            index = None
        if index != self._hover:
            self._hover = index
            self.update()
            if index is None:
                self.setToolTip("")
            else:
                day, _, seconds = self._days[index]
                detail = f"{duration(seconds)} focused" if seconds else "No focus time"
                self.setToolTip(f"{day:%A}, {day.day} {day:%b}\n{detail}")

    def leaveEvent(self, event) -> None:
        self._hover = None
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:
        if not self._days:
            return
        p = theme.palette
        today = date.today()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        plot_top, plot_bottom = float(self.TOP), float(self.height() - self.BOTTOM)
        plot_h = plot_bottom - plot_top
        peak = max(s for _, _, s in self._days) / 60
        step = _nice_step(peak)
        lines = max(2, min(4, int(-(-peak // step)) or 2))
        ceiling = step * lines

        axis_font = mono(11, QFont.Weight.Normal)
        painter.setFont(axis_font)
        for i in range(lines + 1):
            y = plot_bottom - plot_h * i / lines
            style = Qt.PenStyle.SolidLine if i == 0 else Qt.PenStyle.DashLine
            painter.setPen(QPen(QColor(p.border), 1, style))
            painter.drawLine(QPointF(self.AXIS, y + 0.5), QPointF(self.width(), y + 0.5))
            painter.setPen(QColor(p.faint))
            text = duration(step * i * 60, compact=True) if i else "0"
            painter.drawText(
                QRectF(0, y - 8, self.AXIS - 8, 16),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                text,
            )

        slot = self._slot()
        bar_w = min(26.0, slot * 0.56)
        value_font = mono(11, QFont.Weight.DemiBold)
        day_font = pixel_font(UI, 12, QFont.Weight.Medium)
        today_font = pixel_font(UI, 12, QFont.Weight.DemiBold)
        metrics = QFontMetrics(value_font)
        soft_bar = QColor(p.accent)
        soft_bar.setAlphaF(0.42 if p.dark else 0.32)
        for i, (day, _, seconds) in enumerate(self._days):
            left = self.AXIS + slot * i
            if i == self._hover:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(p.raised))
                painter.drawRoundedRect(QRectF(left + 2, plot_top, slot - 4, plot_h + self.BOTTOM - 2), 6, 6)
            x = left + (slot - bar_w) / 2
            is_today = day == today
            if seconds:
                h = max(3.0, plot_h * (seconds / 60) / ceiling)
                bar = QPainterPath()
                bar.addRoundedRect(QRectF(x, plot_bottom - h, bar_w, h + 4), 5, 5)
                painter.save()
                painter.setClipRect(QRectF(x, plot_top - 2, bar_w, plot_h + 2))
                painter.fillPath(bar, QColor(p.accent) if is_today or i == self._hover else soft_bar)
                painter.restore()
                text = duration(seconds)
                if metrics.horizontalAdvance(text) > slot - 2:
                    text = duration(seconds, compact=True)
                if metrics.horizontalAdvance(text) <= slot:
                    painter.setFont(value_font)
                    painter.setPen(QColor(p.text if is_today else p.muted))
                    painter.drawText(
                        QRectF(left, plot_bottom - h - 18, slot, 16), Qt.AlignmentFlag.AlignCenter, text
                    )
            elif day <= today:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(p.border_strong))
                painter.drawRoundedRect(QRectF(x, plot_bottom - 2, bar_w, 2), 1, 1)
            painter.setFont(today_font if is_today else day_font)
            painter.setPen(QColor(p.accent if is_today else (p.faint if day > today else p.muted)))
            painter.drawText(
                QRectF(left, plot_bottom + 6, slot, self.BOTTOM - 6),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                f"{day:%a}",
            )


class PriorityPill(QWidget):
    """Soft rounded chip with a dot: Normal (blue), High (amber), Urgent (red)."""

    NAMES = ("Normal", "High", "Urgent")

    def __init__(self, priority: int = 0) -> None:
        super().__init__()
        self._priority = priority
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        theme.changed.connect(self._resize)
        self._resize()

    def _font(self) -> QFont:
        return pixel_font(UI, 11, QFont.Weight.DemiBold)

    def _resize(self) -> None:
        text = self.NAMES[self._priority]
        width = QFontMetrics(self._font()).horizontalAdvance(text) + 26
        self.setFixedSize(width, px_round(20))
        self.update()

    def paintEvent(self, event) -> None:
        soft, _, ink = event_tint(theme.palette, self._priority)
        base = PRIORITY_COLORS(theme.palette)[self._priority]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect())
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(soft))
        painter.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)
        painter.setBrush(QColor(base))
        painter.drawEllipse(QPointF(10, rect.center().y()), 3, 3)
        painter.setFont(self._font())
        painter.setPen(QColor(ink))
        text = self.NAMES[self._priority]
        painter.drawText(rect.adjusted(17, 0, -8, 0), Qt.AlignmentFlag.AlignVCenter, text)


def px_round(size: int) -> int:
    return round(size * max(1.0, theme.scale))


def priority_menu(parent: QWidget, current: int, on_pick: Callable[[int], None]) -> QMenu:
    menu = StyledMenu(parent)
    for level in (2, 1, 0):
        color = PRIORITY_COLORS(theme.palette)[level]
        action = menu.addAction(icons.icon("dot", color, 14), PriorityPill.NAMES[level])
        action.setCheckable(True)
        action.setChecked(level == current)
        action.triggered.connect(lambda _=False, lv=level: on_pick(lv))
    return menu


def show_menu(menu: QMenu, anchor: QWidget) -> None:
    """Open `menu` under `anchor`, right-aligned to it and kept inside the app window."""
    menu.ensurePolished()
    size = menu.sizeHint()
    area = anchor.window().geometry().adjusted(8, 8, -8, -8)
    button = QRect(anchor.mapToGlobal(QPoint(0, 0)), anchor.size())
    x = min(max(button.right() + 1 - size.width(), area.left()), area.right() + 1 - size.width())
    y = button.bottom() + 5
    if y + size.height() > area.bottom() + 1:
        y = button.top() - 5 - size.height()
    menu.exec(QPoint(x, max(y, area.top())))
    menu.deleteLater()


class OutsideClick(QObject):
    """Calls `callback` once on a mouse press outside `widget` (inline editors lose no edits)."""

    def __init__(self, widget: QWidget, callback: Callable[[], None]) -> None:
        super().__init__(widget)
        self._widget, self._callback = widget, callback
        self._active = False
        self._ignored: list[QWidget] = []

    def ignore(self, widget: QWidget) -> None:
        """Clicks on this widget (e.g. the button that toggles editing) don't count as outside."""
        self._ignored.append(widget)

    def _hits(self, widget: QWidget, pos) -> bool:
        return widget.isVisible() and widget.rect().contains(widget.mapFromGlobal(pos))

    def start(self) -> None:
        app = QCoreApplication.instance()
        if not self._active and app is not None:
            app.installEventFilter(self)
            self._active = True

    def stop(self) -> None:
        app = QCoreApplication.instance()
        if self._active and app is not None:
            app.removeEventFilter(self)
        self._active = False

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if (
            self._active
            and event.type() == QEvent.Type.MouseButtonPress
            and isinstance(watched, QWidget)
            and watched.window() is self._widget.window()
        ):
            pos = event.globalPosition().toPoint()
            if not any(self._hits(w, pos) for w in (self._widget, *self._ignored)):
                self.stop()
                QTimer.singleShot(0, self._callback)
        return False


class StyledMenu(QMenu):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            self.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)


class _ScrollHost(QWidget):
    def __init__(self, area: QScrollArea) -> None:
        super().__init__()
        self._area = area

    def event(self, event: QEvent) -> bool:
        handled = super().event(event)
        if event.type() == QEvent.Type.LayoutRequest:
            self.setMinimumHeight(self.sizeHint().height())
            QCoreApplication.sendEvent(self._area, QEvent(QEvent.Type.LayoutRequest))
        return handled


class Page(QWidget):
    def __init__(
        self,
        ctx: Context,
        title: str,
        *,
        scroll: bool = True,
        max_width: int = 0,
        heading: bool = True,
    ) -> None:
        super().__init__()
        self.ctx = ctx
        self._stale = False
        self.title_label = label(title, "page")
        self.heading = vbox(self.title_label, spacing=2)
        self.header = hbox(spacing=8)
        self.header.setContentsMargins(0, 0, 0, 0)
        self.body = vbox(spacing=16)

        top = hbox(self.heading, None, self.header, spacing=16)
        top.setAlignment(self.header, Qt.AlignmentFlag.AlignVCenter)
        column = vbox(spacing=18)
        if heading:
            column.addLayout(top)
        column.addLayout(self.body, 0 if scroll else 1)
        if scroll:
            column.addStretch(1)
        content = QWidget()
        content.setLayout(column)
        if max_width:
            content.setMaximumWidth(max_width)

        area = QScrollArea() if scroll else None
        host = _ScrollHost(area) if area else self
        row = QHBoxLayout(host)
        row.setContentsMargins(24, 22, 14 if scroll else 24, 20)
        row.addStretch(1)
        row.addWidget(content, 100)
        row.addStretch(1)
        if area:
            area.setWidgetResizable(True)
            area.setFrameShape(QFrame.Shape.NoFrame)
            area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            area.setWidget(host)
            outer = QVBoxLayout(self)
            outer.setContentsMargins(0, 0, 0, 0)
            outer.addWidget(area)

    def on_show(self) -> None:
        return None

    def show_page(self) -> None:
        """Called by the shell on navigation: a full refresh, so nothing is left to catch up."""
        self._stale = False
        self.on_show()

    def live(self) -> bool:
        """For store-change handlers: True when the page is on screen and should refresh now.

        A hidden page only remembers that it is out of date; it refreshes when it is shown again, so
        a change made on one page never rebuilds every other page in the background.
        """
        if self.isVisible():
            return True
        self._stale = True
        return False

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._stale:
            QTimer.singleShot(0, self._catch_up)

    def _catch_up(self) -> None:
        if self._stale and self.isVisible():
            self.show_page()


class Dropdown(QComboBox):
    """Combo box whose list is 8 rows tall and opens on the selected value."""

    VISIBLE = 8

    def __init__(self) -> None:
        super().__init__()
        self.setMaxVisibleItems(self.VISIBLE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        view = self.view()
        view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def showPopup(self) -> None:
        super().showPopup()
        index = self.model().index(self.currentIndex(), self.modelColumn())
        self.view().scrollTo(index, QAbstractItemView.ScrollHint.PositionAtCenter)


def index_of(combo, value: object) -> int:
    """QComboBox.findData can't match Python objects such as datetime.time; compare in Python."""
    return next((i for i in range(combo.count()) if combo.itemData(i) == value), -1)


def when_text(moment: datetime) -> str:
    """Today 18:00 / Tomorrow 09:00 / Mon 30 Nov 09:00."""
    delta = (moment.date() - date.today()).days
    day = {0: "Today", 1: "Tomorrow", -1: "Yesterday"}.get(delta, f"{moment:%a} {moment.day} {moment:%b}")
    return f"{day} {timefmt.clock(moment)}"


def _round_up(moment: datetime, minutes: int = 5) -> datetime:
    moment = moment.replace(second=0, microsecond=0)
    extra = -moment.minute % minutes
    return moment + timedelta(minutes=extra)


class Wheel(QWidget):
    """One drum of an alarm-clock picker: scroll, drag, click or use the arrow keys.

    `fmt` turns a value into its label; `wrap=False` stops at both ends instead of cycling.
    """

    changed = Signal(int)

    def __init__(
        self,
        count: int,
        caption: str,
        *,
        fmt: Callable[[int], str] = lambda v: f"{v:02d}",
        width: int = 84,
        item: int = 42,
        rows: int = 5,
        caption_h: int = 26,
        font: tuple[int, int] = (22, 18),
        wrap: bool = True,
    ) -> None:
        super().__init__()
        self._count = count
        self._caption = caption
        self._fmt, self._wrap, self._font = fmt, wrap, font
        self.item, self.rows, self.caption_h = item, rows, caption_h
        self._value = 0
        self._offset = 0.0
        self._press_y: float | None = None
        self._dragged = False
        self._wheel_acc = 0
        self._snap = QVariantAnimation(self)
        self._snap.setDuration(160)
        self._snap.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._snap.valueChanged.connect(self._on_snap)
        self.setFixedSize(width, caption_h + rows * item)
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        self.setCursor(Qt.CursorShape.SizeVerCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        theme.changed.connect(self.update)

    def value(self) -> int:
        return self._value

    def _fit(self, value: int) -> int:
        return value % self._count if self._wrap else max(0, min(value, self._count - 1))

    def set_value(self, value: int) -> None:
        self._value = self._fit(value)
        self._offset = 0.0
        self.update()

    def step(self, steps: int) -> None:
        value = self._fit(self._value + steps)
        if value != self._value:
            self._value = value
            self.update()
            self.changed.emit(self._value)

    def _mid(self) -> float:
        return self.caption_h + self.rows * self.item / 2

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
        steps = round(-offset / self.item)
        if steps:
            self._press_y -= steps * self.item
            offset += steps * self.item
            self.step(steps)
        self._offset = offset
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        if self._press_y is None:
            return
        self._press_y = None
        if not self._dragged and event.position().y() > self.caption_h:
            self.step(round((event.position().y() - self._mid()) / self.item))
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
        head = QRectF(0, 0, self.width(), self.caption_h - 6)
        painter.drawText(head, Qt.AlignmentFlag.AlignCenter, self._caption)

        painter.setClipRect(QRectF(0, self.caption_h, self.width(), self.rows * self.item))
        mid = self._mid()
        for i in range(-3, 4):
            y = mid + i * self.item + self._offset
            distance = abs(y - mid) / self.item
            if distance > 2.8:
                continue
            near = max(0.0, 1 - distance)
            weight = QFont.Weight.Bold if near > 0.5 else QFont.Weight.Medium
            painter.setFont(mono(round(self._font[0] + self._font[1] * near), weight, scaled=False))
            painter.setPen(QColor(pal.text if near > 0.5 else pal.muted))
            painter.setOpacity(max(0.0, 1 - distance * 0.4))
            value = self._value + i
            if not self._wrap and not 0 <= value < self._count:
                continue
            text = self._fmt(value % self._count)
            cell = QRectF(0, y - self.item / 2, self.width(), self.item)
            painter.drawText(cell, Qt.AlignmentFlag.AlignCenter, text)


class DateTimeDial(QWidget):
    """Day, hour and minute wheels (plus AM/PM in 12-hour mode) over one highlighted band."""

    changed = Signal()
    DAYS = 366
    ITEM, ROWS, CAPTION, PAD = 34, 5, 24, 10

    def __init__(self, initial: datetime) -> None:
        super().__init__()
        self._today = date.today()
        size = {"item": self.ITEM, "rows": self.ROWS, "caption_h": self.CAPTION}
        self.day = Wheel(self.DAYS, "DAY", fmt=self._day_text, width=128, font=(12, 3), wrap=False, **size)
        self._h24 = timefmt.hour24()
        if self._h24:
            self.hour = Wheel(24, "HOUR", width=56, font=(15, 7), **size)
        else:
            self.hour = Wheel(12, "HOUR", fmt=lambda v: str(v or 12), width=56, font=(15, 7), **size)
        self.minute = Wheel(12, "MIN", fmt=lambda v: f"{v * 5:02d}", width=56, font=(15, 7), **size)
        wheels = [self.day, self.hour, self.minute]
        if not self._h24:
            self.half = Wheel(2, "", fmt=("AM", "PM").__getitem__, width=52, font=(12, 3), wrap=False, **size)
            wheels.append(self.half)
        self.setLayout(hbox(*wheels, spacing=4, margins=(self.PAD,) * 4))
        self.set_value(initial)
        for wheel in wheels:
            wheel.changed.connect(lambda _: self.changed.emit())
        theme.changed.connect(self.update)

    def _day_text(self, offset: int) -> str:
        if offset < 2:
            return ("Today", "Tomorrow")[offset]
        d = self._today + timedelta(days=offset)
        return f"{d:%a} {d.day} {d:%b}"

    def set_value(self, moment: datetime) -> None:
        self.day.set_value((moment.date() - self._today).days)
        if self._h24:
            self.hour.set_value(moment.hour)
        else:
            self.hour.set_value(moment.hour % 12)
            self.half.set_value(moment.hour // 12)
        self.minute.set_value(moment.minute // 5)

    def value(self) -> datetime:
        hour = self.hour.value() if self._h24 else self.hour.value() + 12 * self.half.value()
        day = self._today + timedelta(days=self.day.value())
        return datetime.combine(day, time(hour, self.minute.value() * 5))

    def paintEvent(self, event) -> None:
        pal = theme.palette
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(pal.raised))
        painter.drawRoundedRect(QRectF(self.rect()), 14, 14)
        mid = self.PAD + self.CAPTION + self.ROWS * self.ITEM / 2
        band = QRectF(self.PAD - 4, mid - self.ITEM / 2 - 2, self.width() - 2 * self.PAD + 8, self.ITEM + 4)
        painter.setBrush(QColor(pal.surface))
        painter.setPen(QPen(QColor(pal.border), 1))
        painter.drawRoundedRect(band, 10, 10)


def pick_reminder(
    parent: QWidget, current: datetime | None, on_pick: Callable[[datetime | None], None]
) -> None:
    """Straight to the date & time picker; an existing reminder can also be removed from there."""
    initial = current if current and current > datetime.now() else datetime.now() + timedelta(hours=1)
    remove = (lambda: on_pick(None)) if current is not None else None
    picked = pick_datetime(parent, initial, on_remove=remove)
    if picked is not None:
        on_pick(picked)


def pick_datetime(
    parent: QWidget,
    initial: datetime,
    title: str = "Remind me",
    *,
    on_remove: Callable[[], None] | None = None,
) -> datetime | None:
    dialog = QDialog(parent, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
    dialog.setObjectName("Confirm")
    dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    dialog.setModal(True)
    initial = _round_up(initial, 5)
    dial = DateTimeDial(initial)
    dialog.setFixedWidth(max(360, dial.sizeHint().width() + 48))
    summary = label("", "caption")
    summary.setAlignment(Qt.AlignmentFlag.AlignCenter)
    picked = dial.value

    def refresh() -> None:
        late = picked() <= datetime.now()
        summary.setText("That time has already passed" if late else f"Reminder: {when_text(picked())}")
        retone(summary, "danger" if late else "accent")
        ok.setEnabled(not late)

    card = Card()
    card.body.setContentsMargins(24, 22, 24, 20)
    card.body.setSpacing(12)
    card.body.addWidget(label(title, "h2"))
    card.body.addWidget(dial, 0, Qt.AlignmentFlag.AlignHCenter)
    dial.changed.connect(refresh)
    card.body.addWidget(summary)
    card.body.addSpacing(4)
    cancel = button("Cancel", "secondary", on_click=dialog.reject)
    ok = button("Set reminder", on_click=dialog.accept)
    actions = hbox(None, cancel, ok, spacing=8)
    if on_remove is not None:

        def remove() -> None:
            dialog.reject()
            on_remove()

        actions.insertWidget(0, button("Remove", "ghost", on_click=remove))
    card.body.addLayout(actions)
    refresh()
    shell = QVBoxLayout(dialog)
    shell.setContentsMargins(0, 0, 0, 0)
    shell.addWidget(card)
    dialog.adjustSize()
    anchor = parent.window().frameGeometry().center()
    dialog.move(anchor - dialog.rect().center())
    accepted = dialog.exec() == QDialog.DialogCode.Accepted
    value = picked()
    dialog.deleteLater()
    return value if accepted else None


def confirm(parent: QWidget, title: str, text: str, action: str = "Delete") -> bool:
    dialog = QDialog(parent, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
    dialog.setObjectName("Confirm")
    dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    dialog.setModal(True)
    dialog.setFixedWidth(380)
    card = Card()
    card.body.setContentsMargins(24, 24, 24, 20)
    card.body.setSpacing(8)
    cancel = button("Cancel", "secondary", on_click=dialog.reject)
    ok = button(action, on_click=dialog.accept)
    card.body.addWidget(label(title, "h2"))
    card.body.addWidget(label(text, "muted", wrap=True))
    card.body.addSpacing(12)
    card.body.addLayout(hbox(None, cancel, ok, spacing=8))
    shell = QVBoxLayout(dialog)
    shell.setContentsMargins(0, 0, 0, 0)
    shell.addWidget(card)
    dialog.adjustSize()
    anchor = parent.window().frameGeometry().center()
    dialog.move(anchor - dialog.rect().center())
    accepted = dialog.exec() == QDialog.DialogCode.Accepted
    dialog.deleteLater()
    return accepted


class Toast(QLabel):
    def __init__(self, parent: QWidget, text: str) -> None:
        super().__init__(text, parent)
        self.setObjectName("Toast")
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._effect = QGraphicsOpacityEffect(self)
        self._effect.setOpacity(0.0)
        self.setGraphicsEffect(self._effect)
        self._fade = QPropertyAnimation(self._effect, b"opacity", self)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._hold = QTimer(self)
        self._hold.setSingleShot(True)
        self._hold.timeout.connect(self._hide)
        self.ensurePolished()
        self.adjustSize()
        self.move((parent.width() - self.width()) // 2, parent.height() - self.height() - 32)
        self.show()
        self.raise_()
        self._animate(1.0, 180)
        self._hold.start(2200)

    def _animate(self, target: float, ms: int) -> None:
        self._fade.stop()
        self._fade.setDuration(ms)
        self._fade.setStartValue(self._effect.opacity())
        self._fade.setEndValue(target)
        self._fade.start()

    def _hide(self) -> None:
        self._animate(0.0, 260)
        self._fade.finished.connect(self.deleteLater)

    @staticmethod
    def show_text(parent: QWidget, text: str) -> None:
        for old in parent.findChildren(Toast, options=Qt.FindChildOption.FindDirectChildrenOnly):
            old.hide()
            old.deleteLater()
        Toast(parent, text)
