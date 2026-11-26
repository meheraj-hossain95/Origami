from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from origami import ASSETS, __version__, instance, timefmt
from origami.context import Context
from origami.reminders import ReminderService
from origami.store import Store, default_dir
from origami.timer import FocusTimer
from origami.ui.theme import load_fonts, theme


def _windows_identity() -> None:
    """Give the process its own taskbar identity, so Windows shows Origami's icon instead of Python's."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Origami.Desktop")
    except (AttributeError, OSError):
        pass


def run() -> None:
    _windows_identity()
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName("Origami")
    app.setOrganizationName("Origami")
    app.setApplicationVersion(__version__)
    app.setWindowIcon(QIcon(str(ASSETS / "icon.png")))
    app.setStyle("Fusion")

    name = instance.server_name(default_dir())
    if instance.notify_running(name):
        return  # the running copy brings its window forward
    # Listen before the slow start-up below, so a second launch during it still finds this copy.
    windows: list = []
    server = instance.listen(name, lambda: windows and windows[0].reveal())  # noqa: F841 - lives with the app

    from origami.ui.shell import MainWindow  # the whole UI; imported only once this copy is the one

    store = Store()
    timer = FocusTimer(store)
    app.aboutToQuit.connect(timer.shutdown)
    app.aboutToQuit.connect(store.close)

    load_fonts()
    theme.attach(app)
    theme.accent = store.get("accent", theme.accent)
    theme.font_size = store.get("font_size", theme.font_size)
    theme.set_mode(store.get("theme", "system"))
    timefmt.set_hour24(store.get("clock", "24") != "12")

    window = MainWindow(Context(store, timer))
    windows.append(window)
    reminders = ReminderService(store)
    window.attach_reminders(reminders)
    window.show()
    sys.exit(app.exec())
