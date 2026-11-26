from __future__ import annotations

from datetime import date
from pathlib import Path

from PySide6.QtCore import QRectF, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QAbstractButton, QButtonGroup, QFileDialog, QHBoxLayout, QLayout, QWidget

from origami import __version__, sounds, timefmt
from origami.context import Context
from origami.notify_prefs import NOTIFY_DEFAULTS
from origami.ui.components import (
    Card,
    ElidedLabel,
    Page,
    Segmented,
    Switch,
    button,
    divider,
    hbox,
    label,
    vbox,
)
from origami.ui.theme import ACCENTS, DEFAULT_ACCENT, DEFAULT_FONT_SIZE, FONT_SIZES, theme

THEMES = (("system", "System"), ("light", "Light"), ("dark", "Dark"))
NOTIFY_KINDS = (
    ("notify_tasks", "Task reminders", "When a task's reminder time comes"),
    ("notify_focus", "Pomodoro", "When a focus session or break ends"),
    ("notify_events", "Calendar events", "For events you've set a reminder on"),
    ("notify_timetable", "Timetable", "For timetable blocks you've set a reminder on"),
)
CLOCKS = (("24", "24-hour"), ("12", "12-hour"))
SWATCH = 30


def row(title: str, hint: str, control: QWidget | QLayout) -> QHBoxLayout:
    return hbox(vbox(label(title, "h3"), label(hint, "muted"), spacing=2), None, control, spacing=16)


class Swatch(QAbstractButton):
    """Round colour chip; a ring and tick mark the chosen one."""

    def __init__(self, key: str) -> None:
        super().__init__()
        self.key = key
        self.setCheckable(True)
        self.setFixedSize(SWATCH + 8, SWATCH + 8)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(ACCENTS[key][0])
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        theme.changed.connect(self.update)

    def paintEvent(self, event) -> None:
        pal = theme.palette
        _, light, dark = ACCENTS[self.key]
        color = QColor(dark if pal.dark else light)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        outer = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)
        if self.isChecked() or self.underMouse():
            painter.setPen(QPen(color if self.isChecked() else QColor(pal.border_strong), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(outer)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(outer.adjusted(4, 4, -4, -4))
        if self.isChecked():
            c = outer.center()
            tick = QPainterPath()
            tick.moveTo(c.x() - 5, c.y() + 0.5)
            tick.lineTo(c.x() - 1.5, c.y() + 4)
            tick.lineTo(c.x() + 5.5, c.y() - 4)
            pen = QPen(QColor("#FFFFFF"), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(tick)


class AccentPicker(QWidget):
    changed = Signal(str)

    def __init__(self, value: str) -> None:
        super().__init__()
        self._group = QButtonGroup(self)
        layout = hbox(spacing=2)
        self._swatches: dict[str, Swatch] = {}
        for key in ACCENTS:
            swatch = Swatch(key)
            self._group.addButton(swatch)
            self._swatches[key] = swatch
            layout.addWidget(swatch)
            swatch.clicked.connect(lambda _=False, k=key: self.changed.emit(k))
        self.setLayout(layout)
        self._swatches.get(value, self._swatches[DEFAULT_ACCENT]).setChecked(True)


class SettingsPage(Page):
    def __init__(self, ctx: Context) -> None:
        super().__init__(ctx, "Settings")
        store = ctx.store
        self.body.setSpacing(20)

        appearance = Card("Appearance")
        appearance.body.setSpacing(16)
        theme_picker = Segmented(THEMES, store.get("theme", "system"))
        theme_picker.changed.connect(self._set_theme)
        appearance.body.addLayout(row("Theme", "Follow the system or pick one", theme_picker))
        appearance.body.addWidget(divider())
        accent = AccentPicker(store.get("accent", DEFAULT_ACCENT))
        accent.changed.connect(self._set_accent)
        appearance.body.addLayout(row("Color", "Buttons, highlights and progress", accent))
        appearance.body.addWidget(divider())
        sizes = [(key, name) for key, (name, _) in FONT_SIZES.items()]
        size_picker = Segmented(sizes, store.get("font_size", DEFAULT_FONT_SIZE))
        size_picker.changed.connect(self._set_font_size)
        appearance.body.addLayout(row("Text size", "Make text smaller or larger", size_picker))
        appearance.body.addWidget(divider())
        clock_picker = Segmented(CLOCKS, "24" if timefmt.hour24() else "12")
        clock_picker.changed.connect(self._set_clock)
        appearance.body.addLayout(row("Time format", "Show times as 18:30 or 6:30 PM", clock_picker))
        self.body.addWidget(appearance)

        alerts = Card("Notifications")
        alerts.body.setSpacing(16)
        current = store.get("reminder_sound", sounds.DEFAULT_SOUND)
        sound_picker = Segmented(list(sounds.SOUNDS.items()), current)
        sound_picker.changed.connect(self._set_sound)
        alerts.body.addLayout(row("Reminder sound", "Pick one to hear it", sound_picker))
        for key, title, hint in NOTIFY_KINDS:
            alerts.body.addWidget(divider())
            switch = Switch(bool(store.get_int(key, NOTIFY_DEFAULTS[key])))
            switch.toggled.connect(lambda on, k=key: self.ctx.store.set(k, int(on)))
            alerts.body.addLayout(row(title, hint, switch))
        self.body.addWidget(alerts)

        data = Card("Data")
        path = str(store.path.parent)
        location = ElidedLabel(path, "mono", mode=Qt.TextElideMode.ElideMiddle)
        location.setToolTip(path)
        open_folder = button("Open folder", "secondary", icon="folder", on_click=self._open_folder)
        folder_row = hbox(location, open_folder, spacing=16)
        folder_row.setStretch(0, 1)
        data.body.addLayout(folder_row)
        data.body.addLayout(hbox(button("Export JSON", "secondary", on_click=self._export), None))
        data.body.addWidget(label(f"Origami {__version__}", "caption"))
        self.body.addWidget(data)

    def _set_theme(self, mode: str) -> None:
        self.ctx.store.set("theme", mode)
        theme.set_mode(mode)

    def _set_accent(self, key: str) -> None:
        self.ctx.store.set("accent", key)
        theme.set_accent(key)

    def _set_font_size(self, key: str) -> None:
        self.ctx.store.set("font_size", key)
        theme.set_font_size(key)

    def _set_clock(self, key: str) -> None:
        self.ctx.store.set("clock", key)
        timefmt.set_hour24(key != "12")
        theme.changed.emit()  # repaint drawn widgets (calendar grid, timetable)
        for domain in ("tasks", "events", "reminders", "timetable"):
            self.ctx.store.changed.emit(domain)  # pages rebuild their text

    def _set_sound(self, key: str) -> None:
        self.ctx.store.set("reminder_sound", key)
        sounds.play(key)

    def _open_folder(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.ctx.store.path.parent)))

    def _export(self) -> None:
        default = Path.home() / "Documents" / f"origami-{date.today():%Y-%m-%d}.json"
        name, _ = QFileDialog.getSaveFileName(self, "Export data", str(default), "JSON (*.json)")
        if not name:
            return
        try:
            self.ctx.store.export_json(Path(name))
        except OSError:
            self.ctx.toast("Export failed")
        else:
            self.ctx.toast("Exported")
