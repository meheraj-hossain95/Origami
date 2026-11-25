from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import QEvent, QObject, QSize, Qt
from PySide6.QtWidgets import QDialog, QFrame, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from origami.context import Context
from origami.ui.components import IconLabel, divider, hbox, label
from origami.ui.theme import theme

PAGES = (
    ("dashboard", "Dashboard", "home", "Ctrl+1"),
    ("tasks", "Tasks", "tasks", "Ctrl+2"),
    ("habits", "Habits", "repeat", "Ctrl+3"),
    ("calendar", "Calendar", "calendar", "Ctrl+4"),
    ("timetable", "Timetable", "calendar-clock", "Ctrl+5"),
    ("focus", "Focus", "timer", "Ctrl+6"),
)
ROW_HEIGHT = 40
MAX_ROWS = 8
HEADER_HEIGHT = 49


@dataclass(slots=True)
class Action:
    text: str
    icon: str
    run: Callable[[], None]
    caption: str = ""


def _subsequence(needle: str, hay: str) -> bool:
    it = iter(hay)
    return all(ch in it for ch in needle)


class CommandPalette(QDialog):
    def __init__(self, parent: QWidget, ctx: Context) -> None:
        super().__init__(parent, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.ctx = ctx
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self._input = QLineEdit()
        self._input.setObjectName("PaletteInput")
        self._input.setPlaceholderText("Type a command, or add a task…")
        self._input.textChanged.connect(self._refresh)
        self._input.returnPressed.connect(self._run_current)
        self._input.installEventFilter(self)

        self._list = QListWidget()
        self._list.setObjectName("PaletteList")
        self._list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._list.itemClicked.connect(lambda item: self._run(self._list.row(item)))
        self._empty = label("No matching commands", "muted")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty.setFixedHeight(64)

        card = QFrame()
        card.setFixedWidth(560)
        card.setObjectName("PaletteCard")
        column = QVBoxLayout(card)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(0)
        column.addLayout(
            hbox(IconLabel("search", "faint", 18), self._input, spacing=8, margins=(16, 4, 16, 4))
        )
        column.addWidget(divider())
        column.addWidget(self._list)
        column.addWidget(self._empty)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(card)

        self._actions: list[Action] = []
        self._refresh()

    def popup(self) -> None:
        window = self.parentWidget().window()
        top = window.mapToGlobal(window.rect().topLeft())
        self.move(top.x() + (window.width() - self.width()) // 2, top.y() + round(window.height() * 0.18))
        self.show()
        self._input.setFocus()

    def _catalog(self, query: str) -> list[Action]:
        ctx, timer = self.ctx, self.ctx.timer
        actions = [
            Action(f"Go to {name}", icon, lambda k=key: ctx.navigate(k), shortcut)
            for key, name, icon, shortcut in PAGES
        ]
        actions += [
            Action(
                "Pause focus timer" if timer.running else "Start focus timer",
                "pause" if timer.running else "play",
                timer.toggle,
            ),
            Action(
                "Switch to light theme" if theme.palette.dark else "Switch to dark theme",
                "sun" if theme.palette.dark else "moon",
                self._toggle_theme,
            ),
            Action("Export data…", "download", lambda: ctx.navigate("settings")),
        ]
        needle = query.lower().replace(" ", "")
        if needle:
            actions = [a for a in actions if _subsequence(needle, a.text.lower().replace(" ", ""))]
            actions.sort(key=lambda a: needle not in a.text.lower().replace(" ", ""))
        if query:
            actions.insert(0, Action(f"Add task: {query}", "plus", lambda: self._add_task(query)))
            actions.insert(1, Action(f"Add habit: {query}", "repeat", lambda: self._add_habit(query)))
        return actions

    def _refresh(self) -> None:
        self._actions = self._catalog(self._input.text().strip())
        self._list.clear()
        for action in self._actions:
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, ROW_HEIGHT))
            self._list.addItem(item)
            row = QWidget()
            row.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            row.setLayout(
                hbox(
                    IconLabel(action.icon, "muted", 16),
                    label(action.text, "body"),
                    None,
                    label(action.caption, "caption"),
                    spacing=12,
                    margins=(12, 0, 12, 0),
                )
            )
            self._list.setItemWidget(item, row)
        has = bool(self._actions)
        list_height = min(len(self._actions), MAX_ROWS) * (ROW_HEIGHT + 2) + 12
        self._list.setVisible(has)
        self._empty.setVisible(not has)
        if has:
            self._list.setCurrentRow(0)
            self._list.setFixedHeight(list_height)
        body = list_height if has else self._empty.height()
        self.setFixedHeight(HEADER_HEIGHT + body)

    def _move(self, step: int) -> None:
        count = self._list.count()
        if count:
            self._list.setCurrentRow((self._list.currentRow() + step) % count)

    def _run_current(self) -> None:
        self._run(self._list.currentRow())

    def _run(self, index: int) -> None:
        if 0 <= index < len(self._actions):
            action = self._actions[index]
            self.close()
            action.run()

    def _add_task(self, query: str) -> None:
        self.ctx.store.add_task(query)
        self.ctx.toast("Added to Tasks")

    def _add_habit(self, name: str) -> None:
        self.ctx.store.add_habit(name)
        self.ctx.toast("Habit added")

    def _toggle_theme(self) -> None:
        mode = "light" if theme.palette.dark else "dark"
        self.ctx.store.set("theme", mode)
        theme.set_mode(mode)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self._input and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key in (Qt.Key.Key_Down, Qt.Key.Key_Up):
                self._move(1 if key == Qt.Key.Key_Down else -1)
                return True
        return super().eventFilter(watched, event)

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.ActivationChange and not self.isActiveWindow():
            self.close()
        super().changeEvent(event)
