"""Desktop notifications drawn in the app's own theme, stacked in the screen's bottom-right corner."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QGuiApplication, QMouseEvent, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from origami.ui.components import IconLabel, hbox, icon_button, label, vbox
from origami.ui.theme import theme

WIDTH = 360
SHADOW = 10  # transparent margin the soft shadow is drawn into
EDGE = 14  # gap to the screen edge
GAP = 8  # gap between stacked notifications
SHOW_MS = 8000
MAX_VISIBLE = 3


class Notification(QWidget):
    def __init__(self, title: str, body: str, icon: str, on_click: Callable[[], None] | None) -> None:
        super().__init__(
            None,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedWidth(WIDTH + 2 * SHADOW)
        self._on_click = on_click
        self.on_closed: Callable[[Notification], None] = lambda _: None

        badge = IconLabel(icon, "accent", 18)
        self._badge_box = QWidget()
        self._badge_box.setFixedSize(36, 36)
        badge.setParent(self._badge_box)
        badge.move(9, 9)
        close = icon_button("x", "Dismiss", self.dismiss, size=14)
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        head = hbox(label("Origami", "caption"), None, close, spacing=4)
        text = vbox(head, label(title, "h2", wrap=True), spacing=0)
        if body:
            text.addWidget(label(body, "muted", wrap=True))
        text.addSpacing(2)
        margins = (SHADOW + 14, SHADOW + 8, SHADOW + 8, SHADOW + 12)
        row = hbox(self._badge_box, text, spacing=12, margins=margins)
        row.setAlignment(self._badge_box, Qt.AlignmentFlag.AlignTop)
        row.setStretch(1, 1)
        self.setLayout(row)
        # Top-level windows ignore height-for-width, so size wrapped text for the fixed width ourselves.
        self.setFixedHeight(row.totalHeightForWidth(self.width()))

        self._timer = QTimer(self, singleShot=True, interval=SHOW_MS, timeout=self.dismiss)
        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._closing = False
        theme.changed.connect(self.update)

    def appear(self) -> None:
        self.setWindowOpacity(0.0)
        self.show()
        self._animate(1.0, 160)
        self._timer.start()

    def dismiss(self) -> None:
        if self._closing:
            return
        self._closing = True
        self._timer.stop()
        self._animate(0.0, 200)
        self._fade.finished.connect(self.close)

    def closeEvent(self, event) -> None:
        self.on_closed(self)
        super().closeEvent(event)

    def _animate(self, target: float, ms: int) -> None:
        self._fade.stop()
        self._fade.setDuration(ms)
        self._fade.setStartValue(self.windowOpacity())
        self._fade.setEndValue(target)
        self._fade.start()

    # Hovering keeps it on screen; leaving restarts a shorter countdown.
    def enterEvent(self, event) -> None:
        self._timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        if not self._closing:
            self._timer.start(3000)
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self._on_click:
                self._on_click()
            self.dismiss()

    def paintEvent(self, event) -> None:
        p = theme.palette
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        card = QRectF(self.rect()).adjusted(SHADOW, SHADOW, -SHADOW, -SHADOW)
        # A quiet shadow so the card separates from whatever window is behind it.
        shadow = QColor(0, 0, 0)
        for i in range(SHADOW, 0, -2):
            shadow.setAlpha(int((70 if p.dark else 22) * (1 - i / SHADOW) ** 2))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(shadow)
            painter.drawRoundedRect(card.adjusted(-i, -i + 2, i, i + 2), 12 + i, 12 + i)
        path = QPainterPath()
        path.addRoundedRect(card.adjusted(0.5, 0.5, -0.5, -0.5), 12, 12)
        painter.setPen(QPen(QColor(p.border_strong if p.dark else p.border), 1))
        painter.setBrush(QColor(p.surface))
        painter.drawPath(path)
        badge = self._badge_box.geometry()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(p.accent_soft))
        painter.drawEllipse(QRectF(badge))


class Notifier:
    """Shows notifications bottom-right on the primary screen, newest at the bottom."""

    def __init__(self) -> None:
        self._open: list[Notification] = []

    def show(
        self, title: str, body: str = "", icon: str = "bell", on_click: Callable[[], None] | None = None
    ) -> None:
        while len(self._open) >= MAX_VISIBLE:
            oldest = self._open.pop(0)
            oldest.on_closed = lambda _: None
            oldest.dismiss()
        note = Notification(title, body, icon, on_click)
        note.on_closed = self._closed
        self._open.append(note)
        self._layout()
        note.appear()

    def _closed(self, note: Notification) -> None:
        if note in self._open:
            self._open.remove(note)
            self._layout()

    def _layout(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        bottom = area.bottom() - EDGE + SHADOW
        for note in reversed(self._open):
            x = area.right() - EDGE + SHADOW - note.width()
            note.move(x, bottom - note.height())
            bottom -= note.height() - 2 * SHADOW + GAP
