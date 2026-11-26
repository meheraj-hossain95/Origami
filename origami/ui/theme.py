from __future__ import annotations

import contextlib
import re
from dataclasses import asdict, dataclass, replace
from string import Template

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication

from origami import ASSETS

UI = "Inter"


@dataclass(slots=True, frozen=True)
class Palette:
    bg: str
    surface: str
    raised: str
    sidebar: str
    border: str
    border_strong: str
    text: str
    muted: str
    faint: str
    accent: str
    accent_hover: str
    accent_fg: str
    accent_soft: str
    info: str
    success: str
    warning: str
    danger: str
    dark: bool


LIGHT = Palette(
    bg="#F7F8FA", surface="#FFFFFF", raised="#F2F4F7", sidebar="#FBFBFC",
    border="#E4E7EC", border_strong="#D0D5DD",
    text="#101828", muted="#475467", faint="#8D96A7",
    accent="#4F5BD5", accent_hover="#4350C2", accent_fg="#FFFFFF", accent_soft="#ECEEFC",
    info="#2E6FD8", success="#079455", warning="#DC6803", danger="#D92D20", dark=False,
)
DARK = Palette(
    bg="#0F1115", surface="#171A20", raised="#1E222A", sidebar="#13161B",
    border="#272C35", border_strong="#363C47",
    text="#ECEEF2", muted="#A3ABB9", faint="#6E7686",
    accent="#6672E0", accent_hover="#7581E6", accent_fg="#FFFFFF", accent_soft="#23264A",
    info="#5B9BF0", success="#32C584", warning="#F5A524", danger="#F0605A", dark=True,
)

# key -> (label, light accent, dark accent)
ACCENTS: dict[str, tuple[str, str, str]] = {
    "indigo": ("Indigo", "#4F5BD5", "#6672E0"),
    "blue": ("Blue", "#2F6FDB", "#4D8DF0"),
    "teal": ("Teal", "#0F8A8A", "#2BB3B0"),
    "green": ("Green", "#2E8B4E", "#45B36B"),
    "orange": ("Orange", "#D46B16", "#E8893A"),
    "red": ("Red", "#D13C3C", "#E85C5C"),
    "pink": ("Pink", "#C93C7E", "#E0619D"),
    "purple": ("Purple", "#8146C9", "#9D6BE0"),
}
DEFAULT_ACCENT = "indigo"

# key -> (label, scale)
FONT_SIZES: dict[str, tuple[str, float]] = {
    "small": ("Small", 0.92),
    "default": ("Default", 1.0),
    "large": ("Large", 1.08),
    "xlarge": ("Extra large", 1.16),
}
DEFAULT_FONT_SIZE = "default"

# Type scale (px / weight). Headings 600, labels and controls 500, reading text 400.
QSS = Template("""
* { font-family: "$ui"; outline: none; }
QWidget { color: $text; font-size: 14px; font-weight: 400; }
QMainWindow, #Content, QScrollArea, QScrollArea > QWidget > QWidget { background: $bg; }
QScrollArea { border: none; }

#Sidebar { background: $sidebar; border: none; border-right: 1px solid $border; }
#Brand { font-size: 17px; font-weight: 700; color: $text; }
QPushButton#FocusPill {
    background: $accent_soft; color: $accent; border: none; border-radius: 8px;
    padding: 0 12px; min-height: 34px; font-size: 13px; font-weight: 500; text-align: left;
}
QPushButton#FocusPill:hover { background: $accent_soft; color: $accent_hover; }

QLabel[role="page"] { font-size: 22px; font-weight: 600; color: $text; }
QLabel[role="yearlight"] { font-size: 22px; font-weight: 400; color: $faint; }
QLabel[role="title"] { font-size: 18px; font-weight: 600; color: $text; }
QLabel[role="greeting"] { font-size: 28px; font-weight: 700; color: $text; }
QLabel[role="quotebody"] { font-family: "Georgia", serif; font-size: 15px; font-style: italic; font-weight: 400; color: $text; }
QLabel[role="h2"] { font-size: 14px; font-weight: 600; }
QLabel[role="h3"] { font-size: 14px; font-weight: 500; }
QLabel[role="body"] { font-size: 14px; }
QLabel[role="muted"] { font-size: 13px; color: $muted; }
QLabel[role="caption"] { font-size: 12px; color: $faint; }
QLabel[role="caption"][tone="danger"] { color: $danger; }
QLabel[role="caption"][tone="warning"] { color: $warning; }
QLabel[role="caption"][tone="success"] { color: $success; }
QLabel[role="caption"][tone="accent"] { color: $accent; }
QLabel[role="task"] { font-size: 14px; }
QLabel[role="taskdone"] { font-size: 14px; color: $faint; }
QLabel[role="section"] { font-size: 13px; font-weight: 600; color: $text; }
QLabel[role="group"] { font-size: 13px; font-weight: 600; color: $muted; }
QFrame[group="true"] { background: $surface; border: 1px solid $hairline; border-radius: 12px; }
QFrame[group="true"] QScrollArea, QFrame[group="true"] QScrollArea > QWidget,
QFrame[group="true"] QScrollArea > QWidget > QWidget { background: transparent; border: none; }
QLabel[role="count"] { font-size: 12px; color: $faint; }
QLabel[role="eyebrow"] { font-size: 11px; font-weight: 600; color: $faint; }
QLabel[role="mono"] { font-size: 13px; color: $muted; }
QLabel[role="stat"] { font-size: 24px; font-weight: 600; color: $text; }
QLabel[role="figure"] { font-size: 18px; font-weight: 600; color: $text; }
QLabel[role="error"] { font-size: 13px; color: $danger; }
QLabel[role="badge"] {
    font-size: 11px; font-weight: 600; padding: 1px 7px; border-radius: 8px;
    background: $accent_soft; color: $accent;
}
QLabel[role="badge"][tone="danger"] { background: $danger_soft; color: $danger; }
QLabel[role="badge"][tone="muted"] { background: $raised; color: $muted; }
QFrame[tile="true"] { background: $accent_soft; border: none; border-radius: 8px; }
QFrame[dateblock="true"] { background: $raised; border: none; border-radius: 8px; }

QFrame[card="true"] { background: $surface; border: 1px solid $border; border-radius: 12px; }
QScrollArea#DayEvents, QScrollArea#DayEvents > QWidget > QWidget,
QScrollArea#HabitList, QScrollArea#HabitList > QWidget > QWidget { background: transparent; border: none; }
QFrame[card="true"][interactive="true"]:hover { border-color: $border_strong; }
QFrame[divider="true"] { background: $border; border: none; min-height: 1px; max-height: 1px; }
QFrame[vrule="true"] { background: $border; border: none; min-width: 1px; max-width: 1px; }

QPushButton {
    background: $accent; color: $accent_fg; border: 1px solid $accent; border-radius: 8px;
    padding: 0 14px; min-height: 34px; font-size: 13px; font-weight: 500;
}
QPushButton:hover { background: $accent_hover; border-color: $accent_hover; }
QPushButton:pressed { background: $accent_press; border-color: $accent_press; }
QPushButton:focus { border: 1px solid $accent_press; }
QPushButton:disabled { background: $border; border-color: $border; color: $faint; }
QPushButton[size="sm"] { min-height: 28px; padding: 0 10px; font-size: 12px; }
QPushButton[variant="secondary"] { background: $surface; color: $text; border: 1px solid $border_strong; }
QPushButton[variant="secondary"]:hover { background: $raised; border-color: $border_strong; }
QPushButton[variant="secondary"]:pressed { background: $border; }
QPushButton[variant="secondary"]:focus { border-color: $accent; }
QPushButton[variant="secondary"]:disabled { background: $surface; color: $faint; border-color: $border; }
QPushButton[variant="secondary"]::menu-indicator { image: none; width: 0; }
QPushButton[variant="ghost"] { background: transparent; color: $muted; border: 1px solid transparent; }
QPushButton[variant="ghost"]:hover { background: $raised; color: $text; border-color: transparent; }
QPushButton[variant="ghost"]:pressed { background: $border; }
QPushButton[variant="ghost"]:disabled { background: transparent; color: $faint; border-color: transparent; }
QPushButton[variant="ghost"]::menu-indicator { image: none; width: 0; }
QPushButton[variant="link"] { background: transparent; color: $accent; border: none; padding: 0 2px; min-height: 22px; font-size: 12px; font-weight: 500; }
QPushButton[variant="link"]:hover { background: transparent; color: $accent_hover; text-decoration: underline; }
QPushButton[variant="link"]:pressed { background: transparent; }
QPushButton#PlayButton { min-width: 60px; max-width: 60px; min-height: 60px; max-height: 60px; border-radius: 30px; padding: 0; }

QPushButton[nav="true"] {
    background: transparent; color: $muted; border: none; border-radius: 8px;
    padding: 0 10px 0 10px; min-height: 36px; font-size: 14px; font-weight: 500; text-align: left;
}
QPushButton[nav="true"]:hover { background: $raised; color: $text; }
QPushButton[nav="true"]:checked { background: $accent_soft; color: $accent; font-weight: 600; }

QToolButton { border: none; background: transparent; }
QToolButton[iconButton="true"] { border-radius: 7px; padding: 6px; }
QToolButton[iconButton="true"]:hover { background: $raised; }
QToolButton[iconButton="true"]:disabled { background: transparent; }
QToolButton::menu-indicator { image: none; width: 0; }

#Segmented { background: $raised; border: none; border-radius: 8px; padding: 2px; }
QPushButton[segment="true"] {
    background: transparent; color: $muted; border: 1px solid transparent; border-radius: 6px;
    padding: 0 12px; min-height: 28px; font-size: 13px; font-weight: 500;
}
#Segmented[compact="true"] QPushButton[segment="true"] { padding: 0 8px; }
QPushButton[segment="true"]:hover { color: $text; background: transparent; border-color: transparent; }
QPushButton[segment="true"]:checked { background: $surface; color: $text; border: 1px solid $border; }

QComboBox {
    combobox-popup: 0;
    background: $surface; border: 1px solid $border_strong; border-radius: 8px; padding: 0 8px 0 10px;
    min-height: 32px; font-size: 13px;
}
QComboBox:hover { border-color: $muted; }
QComboBox::drop-down { border: none; width: 22px; subcontrol-origin: padding; subcontrol-position: center right; }
QComboBox::down-arrow { image: url("$chevron"); width: 12px; height: 12px; }
QComboBox:focus, QComboBox:on { border-color: $accent; }
QComboBox QAbstractItemView {
    background: $surface; border: 1px solid $border; border-radius: 8px; padding: 4px; outline: none;
    selection-background-color: $accent_soft; selection-color: $text;
}
QComboBox QAbstractItemView::item { min-height: 28px; padding: 0 8px; border-radius: 6px; }
QComboBox QAbstractItemView::item:hover { background: $raised; }
QPushButton[day="true"] {
    min-width: 28px; max-width: 28px; min-height: 28px; max-height: 28px; padding: 0; border-radius: 14px;
    background: $raised; color: $muted; border: 1px solid transparent; font-size: 12px; font-weight: 600;
}
QPushButton[day="true"]:hover { background: $border; color: $text; border-color: transparent; }
QPushButton[day="true"]:checked { background: $accent; color: $accent_fg; }
QTimeEdit {
    background: $surface; border: 1px solid $border_strong; border-radius: 8px; padding: 0 12px; min-height: 34px; font-size: 14px;
}
QTimeEdit:hover { border-color: $muted; }
QTimeEdit:focus { border: 1px solid $accent; }
QTimeEdit::up-button, QTimeEdit::down-button, QDateEdit::up-button, QDateEdit::down-button { width: 0; border: none; }
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDateEdit {
    background: $surface; border: 1px solid $border_strong; border-radius: 8px; padding: 0 12px; min-height: 34px; font-size: 14px;
    selection-background-color: $accent_soft; selection-color: $text;
}
QPlainTextEdit, QTextEdit { padding: 8px 12px; }
QLineEdit:hover, QPlainTextEdit:hover, QTextEdit:hover, QSpinBox:hover, QDateEdit:hover { border-color: $muted; }
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus, QDateEdit:focus { border: 1px solid $accent; }
QSpinBox { font-size: 14px; padding: 0 8px; }
QSpinBox QLineEdit, QDateEdit QLineEdit, QTimeEdit QLineEdit { background: transparent; border: none; padding: 0; min-height: 0; }
QSpinBox::up-button, QSpinBox::down-button { width: 0; border: none; }
QLineEdit[flat="true"], QPlainTextEdit[flat="true"] { background: transparent; border: none; padding: 0; }
QLineEdit[flat="true"]:hover, QPlainTextEdit[flat="true"]:hover { border: none; }
QLineEdit[flat="true"]:focus, QPlainTextEdit[flat="true"]:focus { border: none; }
QLineEdit#TaskInput { background: transparent; border: none; min-height: 40px; font-size: 14px; padding: 0 4px; }
QLineEdit#TaskInput:hover, QLineEdit#TaskInput:focus { border: none; }
QFrame#Composer { background: $surface; border: 1px solid $border_strong; border-radius: 10px; }
QFrame#Composer[active="true"] { border: 1px solid $accent; }
QLineEdit#RowEdit { font-size: 14px; }
QPlainTextEdit#RowNotes { font-size: 13px; color: $muted; }
QLineEdit#PaletteInput { background: transparent; border: none; font-size: 16px; padding: 0 4px; min-height: 40px; }
QLineEdit#PaletteInput:hover, QLineEdit#PaletteInput:focus { border: none; }

QCheckBox { spacing: 10px; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 6px; border: 1.5px solid $border_strong; background: $surface; }
QCheckBox::indicator:checked { background: $accent; border-color: $accent; }

QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: $border_strong; border-radius: 3px; min-height: 32px; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: $border_strong; border-radius: 3px; min-width: 32px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

QListWidget#PaletteList { background: transparent; border: none; }
QListWidget#PaletteList::item { background: transparent; border-radius: 8px; margin: 1px 0; }
QListWidget#PaletteList::item:hover { background: $raised; }
QListWidget#PaletteList::item:selected { background: $accent_soft; }

QFrame#PaletteCard { background: $surface; border: 1px solid $border_strong; border-radius: 14px; }

QProgressBar { background: $border; border: none; border-radius: 3px; min-height: 6px; max-height: 6px; color: transparent; }
QProgressBar::chunk { background: $accent; border-radius: 3px; }

QToolTip { background: $text; color: $bg; border: none; padding: 6px 8px; border-radius: 6px; font-size: 12px; }
QMenu { background: $surface; border: 1px solid $border; border-radius: 10px; padding: 6px; }
QMenu::item { padding: 7px 14px 7px 10px; border-radius: 6px; font-size: 13px; }
QMenu::item:selected { background: $raised; }
QMenu::icon { padding-left: 6px; }
QMenu::separator { height: 1px; background: $border; margin: 4px 6px; }
QDialog, QMessageBox { background: $surface; }
QDialog#Confirm { background: transparent; }
QMessageBox QLabel { font-size: 13px; }

#Toast { background: $text; color: $bg; border-radius: 10px; padding: 10px 18px; font-size: 13px; font-weight: 500; }
""")


def mix(fg: str, bg: str, alpha: float) -> str:
    a, b = QColor(fg), QColor(bg)
    return QColor(
        round(a.red() * alpha + b.red() * (1 - alpha)),
        round(a.green() * alpha + b.green() * (1 - alpha)),
        round(a.blue() * alpha + b.blue() * (1 - alpha)),
    ).name()


def with_accent(p: Palette, key: str) -> Palette:
    _, light, dark = ACCENTS.get(key, ACCENTS[DEFAULT_ACCENT])
    accent = dark if p.dark else light
    hover = mix("#FFFFFF", accent, 0.12) if p.dark else mix("#000000", accent, 0.10)
    soft = mix(accent, p.surface, 0.22 if p.dark else 0.11)
    return replace(p, accent=accent, accent_hover=hover, accent_soft=soft)


def qss(p: Palette, scale: float = 1.0) -> str:
    derived = {
        "danger_soft": mix(p.danger, p.surface, 0.16 if p.dark else 0.10),
        "accent_press": mix("#000000", p.accent_hover, 0.12),
        "hairline": mix(p.border, p.surface, 0.6),
        "chevron": (ASSETS / "chevron-down.svg").as_posix(),
    }
    sheet = QSS.substitute(asdict(p), ui=UI, **derived)
    if scale != 1.0:
        sheet = re.sub(r"font-size: (\d+)px", lambda m: f"font-size: {round(int(m[1]) * scale)}px", sheet)
    return sheet


def px(size: float) -> int:
    """Scale a pixel font size by the user's font-size preference."""
    return max(8, round(size * theme.scale))


def pixel_font(family: str, size: int, weight: QFont.Weight, *, scaled: bool = True) -> QFont:
    font = QFont(family)
    font.setPixelSize(px(size) if scaled else size)
    font.setWeight(weight)
    return font


def mono(size: int, weight: QFont.Weight = QFont.Weight.Medium, *, scaled: bool = True) -> QFont:
    font = pixel_font(UI, size, weight, scaled=scaled)
    with contextlib.suppress(AttributeError):
        font.setFeature(QFont.Tag("tnum"), 1)
    return font


def PRIORITY_COLORS(p: Palette) -> tuple[str, str, str]:
    """Base colour per priority: 0 normal = blue, 1 high = amber, 2 urgent = red."""
    return (p.info, p.warning, p.danger)


def event_tint(p: Palette, priority: int) -> tuple[str, str, str]:
    """(soft fill, stronger fill, ink) for a priority: 0 normal=blue, 1 high=amber, 2 urgent=red."""
    base = PRIORITY_COLORS(p)[max(0, min(priority, 2))]
    soft = mix(base, p.surface, 0.15)
    strong = mix(base, p.surface, 0.25)
    ink = mix(base, p.text, 0.85 if p.dark else 0.78)
    return soft, strong, ink


def load_fonts() -> None:
    for path in sorted((ASSETS / "fonts").glob("*.ttf")):
        QFontDatabase.addApplicationFont(str(path))
    font = QFont(UI, 10)
    font.setHintingPreference(QFont.HintingPreference.PreferVerticalHinting)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    QApplication.setFont(font)


def _qpalette(p: Palette) -> QPalette:
    pal = QPalette()
    roles = {
        QPalette.ColorRole.Window: p.bg,
        QPalette.ColorRole.WindowText: p.text,
        QPalette.ColorRole.Base: p.surface,
        QPalette.ColorRole.AlternateBase: p.raised,
        QPalette.ColorRole.Text: p.text,
        QPalette.ColorRole.Button: p.surface,
        QPalette.ColorRole.ButtonText: p.text,
        QPalette.ColorRole.ToolTipBase: p.text,
        QPalette.ColorRole.ToolTipText: p.bg,
        QPalette.ColorRole.Highlight: p.accent,
        QPalette.ColorRole.HighlightedText: p.accent_fg,
        QPalette.ColorRole.PlaceholderText: p.faint,
    }
    for role, color in roles.items():
        pal.setColor(role, QColor(color))
    return pal


class ThemeManager(QObject):
    changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.mode = "system"
        self.accent = DEFAULT_ACCENT
        self.font_size = DEFAULT_FONT_SIZE
        self.palette = LIGHT
        self._app: QApplication | None = None

    @property
    def scale(self) -> float:
        return FONT_SIZES.get(self.font_size, FONT_SIZES[DEFAULT_FONT_SIZE])[1]

    def set_accent(self, key: str) -> None:
        self.accent = key if key in ACCENTS else DEFAULT_ACCENT
        self.set_mode(self.mode)

    def set_font_size(self, key: str) -> None:
        self.font_size = key if key in FONT_SIZES else DEFAULT_FONT_SIZE
        self.set_mode(self.mode)

    def attach(self, app: QApplication) -> None:
        self._app = app
        app.styleHints().colorSchemeChanged.connect(self._on_scheme)

    def set_mode(self, mode: str) -> None:
        self.mode = mode if mode in ("system", "light", "dark") else "system"
        app = self._app
        if app is None:
            return
        # No QStyleHints.setColorScheme: the app paints every colour itself, and forcing Qt's scheme
        # made the first switch stall for over a second while Windows reloaded its native theme.
        self.palette = self._resolve()
        # Clearing first is ~5x faster than swapping one sheet for another: Qt then skips diffing
        # every widget against the old rules. Both calls finish before the next paint, so no flicker.
        app.setStyleSheet("")
        app.setStyleSheet(qss(self.palette, self.scale))
        app.setPalette(_qpalette(self.palette))
        self.changed.emit()

    def _base(self) -> Palette:
        if self.mode == "system" and self._app is not None:
            return DARK if self._app.styleHints().colorScheme() == Qt.ColorScheme.Dark else LIGHT
        return DARK if self.mode == "dark" else LIGHT

    def _resolve(self) -> Palette:
        return with_accent(self._base(), self.accent)

    def _on_scheme(self) -> None:
        if self.mode == "system" and self._base().dark != self.palette.dark:
            self.set_mode("system")


theme = ThemeManager()
