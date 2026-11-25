from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from origami import ASSETS, __version__
from origami.context import Context
from origami.reminders import ReminderService
from origami.store import Store
from origami.timer import FocusTimer
from origami.ui.shell import MainWindow
from origami.ui.theme import load_fonts, theme


def run() -> None:
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName("Origami")
    app.setOrganizationName("Origami")
    app.setApplicationVersion(__version__)
    app.setWindowIcon(QIcon(str(ASSETS / "icon.png")))
    app.setStyle("Fusion")

    store = Store()
    timer = FocusTimer(store)
    app.aboutToQuit.connect(timer.shutdown)
    app.aboutToQuit.connect(store.close)

    load_fonts()
    theme.attach(app)
    theme.accent = store.get("accent", theme.accent)
    theme.font_size = store.get("font_size", theme.font_size)
    theme.set_mode(store.get("theme", "system"))

    window = MainWindow(Context(store, timer))
    reminders = ReminderService(store)
    window.attach_reminders(reminders)
    window.show()
    sys.exit(app.exec())
