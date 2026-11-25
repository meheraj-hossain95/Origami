from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from origami import ASSETS
from origami.context import Context
from origami.reminders import ReminderService, describe
from origami.store import Reminder
from origami.timer import LABELS, Mode
from origami.ui import titlebar
from origami.ui.components import (
    Badge,
    BrandMark,
    Page,
    StyledMenu,
    Toast,
    bind_icon,
    clock,
    divider,
    hbox,
    label,
    vbox,
)
from origami.ui.pages.calendar import CalendarPage
from origami.ui.pages.dashboard import DashboardPage
from origami.ui.pages.focus import FocusPage
from origami.ui.pages.habits import HabitsPage
from origami.ui.pages.settings import SettingsPage
from origami.ui.pages.tasks import TasksPage
from origami.ui.pages.timetable import TimetablePage
from origami.ui.palette import CommandPalette
from origami.ui.theme import theme

WINDOW_SIZE = QSize(1240, 780)
MIN_SIZE = QSize(1120, 720)
NAV_ICON = 20  # icon box; glyph fills ~85% => ~17px, balanced with 15px text
NAV_GAP = 10
NAV = (
    ("dashboard", "Dashboard", "home"),
    ("tasks", "Tasks", "tasks"),
    ("habits", "Habits", "repeat"),
    ("calendar", "Calendar", "calendar"),
    ("timetable", "Timetable", "calendar-clock"),
    ("focus", "Focus", "timer"),
)


class MainWindow(QMainWindow):
    def __init__(self, ctx: Context) -> None:
        super().__init__()
        self.ctx = ctx
        self._tray: QSystemTrayIcon | None = None
        self._reminder_target = "dashboard"
        self.setWindowTitle("Origami")
        self.setMinimumSize(MIN_SIZE)
        area = self.screen().availableGeometry()
        self.resize(min(WINDOW_SIZE.width(), area.width()), min(WINDOW_SIZE.height(), area.height() - 40))
        self.move(area.center() - self.rect().center())

        ctx.navigate = self.go
        ctx.toast = lambda text: Toast.show_text(self, text)

        self._pages: dict[str, Page] = {
            "dashboard": DashboardPage(ctx),
            "tasks": TasksPage(ctx),
            "habits": HabitsPage(ctx),
            "calendar": CalendarPage(ctx),
            "timetable": TimetablePage(ctx),
            "focus": FocusPage(ctx),
            "settings": SettingsPage(ctx),
        }
        self._stack = QStackedWidget()
        self._stack.setObjectName("Content")
        for page in self._pages.values():
            self._stack.addWidget(page)

        root = QWidget()
        row = hbox(self._build_sidebar(), self._stack, spacing=0)
        row.setStretchFactor(self._stack, 1)
        root.setLayout(row)
        self.setCentralWidget(root)

        for i, (key, _, _) in enumerate(NAV, start=1):
            QShortcut(QKeySequence(f"Ctrl+{i}"), self, activated=lambda k=key: self.go(k))
        QShortcut(QKeySequence("Ctrl+,"), self, activated=lambda: self.go("settings"))
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self._new_task)
        QShortcut(QKeySequence("Ctrl+K"), self, activated=self.open_palette)

        ctx.store.changed.connect(self._on_store_changed)
        ctx.timer.tick.connect(self._refresh_pill)
        ctx.timer.state_changed.connect(self._refresh_pill)
        ctx.timer.completed.connect(self._notify)
        self._refresh_badges()
        self._refresh_pill()
        theme.changed.connect(self._style_titlebar)
        self.go("dashboard")

    def attach_reminders(self, service: ReminderService) -> None:
        """Run in the tray so reminders keep arriving after the window is closed."""
        service.fired.connect(self._on_reminder)
        tray = self._ensure_tray()
        if tray is not None:
            QApplication.instance().setQuitOnLastWindowClosed(False)
        service.start()

    def _ensure_tray(self) -> QSystemTrayIcon | None:
        if self._tray is not None or not QSystemTrayIcon.isSystemTrayAvailable():
            return self._tray
        tray = QSystemTrayIcon(QIcon(str(ASSETS / "icon.png")), self)
        tray.setToolTip("Origami")
        menu = StyledMenu(self)
        menu.addAction("Open Origami", self.reveal)
        menu.addSeparator()
        menu.addAction("Quit", QApplication.instance().quit)
        tray.setContextMenu(menu)
        tray.activated.connect(
            lambda reason: self.reveal() if reason != QSystemTrayIcon.ActivationReason.Context else None
        )
        tray.messageClicked.connect(lambda: self.reveal(self._reminder_target))
        tray.show()
        self._tray = tray
        return tray

    def reveal(self, page: str | None = None) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()
        if page:
            self.go(page)

    def _on_reminder(self, reminder: Reminder) -> None:
        title, body = describe(reminder, self.ctx.store)
        self._reminder_target = {"task": "tasks", "slot": "timetable"}.get(reminder.kind, "calendar")
        tray = self._ensure_tray()
        if tray is not None:
            tray.showMessage(title, body, QSystemTrayIcon.MessageIcon.Information, 10_000)
        QApplication.alert(self)
        if self.isVisible():
            self.ctx.toast(f"Reminder: {title}")

    def closeEvent(self, event) -> None:
        app = QApplication.instance()
        if self._tray is not None and not app.quitOnLastWindowClosed():
            event.ignore()
            self.hide()
            if not self.ctx.store.get_int("tray_hint_shown", 0):
                self.ctx.store.set("tray_hint_shown", 1)
                self._tray.showMessage(
                    "Origami is still running",
                    "Reminders will keep arriving. Right-click the tray icon to quit.",
                    QSystemTrayIcon.MessageIcon.Information,
                    6000,
                )
            return
        super().closeEvent(event)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._style_titlebar()

    def _style_titlebar(self) -> None:
        p = theme.palette
        titlebar.style(self, p.bg, p.text, p.border, p.dark)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(224)

        wordmark = label("Origami")
        wordmark.setObjectName("Brand")


        self._nav: dict[str, QPushButton] = {}
        nav = vbox(spacing=4)
        for key, text, icon in NAV:
            b = QPushButton(text)
            b.setProperty("nav", True)
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setIconSize(QSize(NAV_ICON + NAV_GAP, NAV_ICON))
            bind_icon(b, icon, "muted", checked="accent", size=NAV_ICON, pad=NAV_GAP)
            b.clicked.connect(lambda _=False, k=key: self.go(k))
            self._nav[key] = b
            nav.addWidget(b)
        self._badges = {key: Badge() for key in ("tasks", "habits")}
        for key, badge in self._badges.items():
            badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            row = hbox(None, badge, margins=(0, 0, 8, 0))
            row.setAlignment(badge, Qt.AlignmentFlag.AlignVCenter)
            self._nav[key].setLayout(row)

        self._pill = QPushButton()
        self._pill.setObjectName("FocusPill")
        self._pill.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pill.clicked.connect(lambda: self.go("focus"))

        settings = QPushButton("Settings")
        settings.setProperty("nav", True)
        settings.setCheckable(True)
        settings.setCursor(Qt.CursorShape.PointingHandCursor)
        settings.setIconSize(QSize(NAV_ICON + NAV_GAP, NAV_ICON))
        bind_icon(settings, "settings", "muted", checked="accent", size=NAV_ICON, pad=NAV_GAP)
        settings.clicked.connect(lambda: self.go("settings"))
        self._nav["settings"] = settings

        column = QVBoxLayout(sidebar)
        column.setContentsMargins(12, 20, 12, 12)
        column.setSpacing(0)
        brand = hbox(BrandMark(30), wordmark, spacing=10, margins=(6, 0, 0, 0))
        brand.setAlignment(wordmark, Qt.AlignmentFlag.AlignVCenter)
        column.addLayout(brand)
        column.addSpacing(24)
        column.addLayout(nav)
        column.addStretch(1)
        column.addWidget(self._pill)
        column.addSpacing(12)
        column.addWidget(divider())
        column.addSpacing(12)
        column.addWidget(settings)
        return sidebar

    def go(self, key: str) -> None:
        page = self._pages[key]
        self._stack.setCurrentWidget(page)
        for k, b in self._nav.items():
            b.setChecked(k == key)
        page.on_show()

    def _new_task(self) -> None:
        self.go("tasks")
        self.focus_new_task()

    def focus_new_task(self) -> None:
        page = self._pages["tasks"]
        if hasattr(page, "focus_input"):
            page.focus_input()

    def open_palette(self) -> None:
        CommandPalette(self, self.ctx).popup()

    def _on_store_changed(self, domain: str) -> None:
        if domain in ("tasks", "habits"):
            self._refresh_badges()

    def _refresh_badges(self) -> None:
        store = self.ctx.store
        self._badges["tasks"].set_text(str(store.open_count()))
        done, total = store.habit_counts()
        self._badges["habits"].set_text(str(total - done))

    def _refresh_pill(self, *_: object) -> None:
        timer = self.ctx.timer
        active = timer.running or timer.remaining < timer.total
        self._pill.setVisible(active)
        if active:
            state = "" if timer.running else " · paused"
            self._pill.setText(f"{LABELS[timer.mode]} · {clock(timer.remaining)}{state}")

    def _notify(self, mode: str) -> None:
        title, body = (
            ("Focus complete", "Take a breather.")
            if mode == Mode.FOCUS.value
            else ("Break over", "Ready for the next session?")
        )
        tray = self._ensure_tray()
        if tray is not None:
            self._reminder_target = "focus"
            tray.showMessage(title, body, QSystemTrayIcon.MessageIcon.NoIcon, 4000)
        QApplication.alert(self)
