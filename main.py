import sys
import os
from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtCore import QDir, Qt
from PySide6.QtGui import QIcon

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow
from database.db import initialize_database
import config

def setup_application():
    app = QApplication(sys.argv)
    app.setApplicationName("Origami")
    app.setApplicationVersion("1.0.1")
    app.setOrganizationName("Personal Productivity")
    
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    
    icon_path = os.path.join(base_path, 'assets', 'icons', 'app_icon.ico')
    if os.path.exists(icon_path):
        icon = QIcon(icon_path)
        app.setWindowIcon(icon)
        app.setDesktopFileName("Origami")
        app.setApplicationDisplayName("Origami")
        app.setQuitOnLastWindowClosed(True)
    else:
        png_icon_path = os.path.join(base_path, 'assets', 'icons', 'app_icon.png')
        if os.path.exists(png_icon_path):
            icon = QIcon(png_icon_path)
            app.setWindowIcon(icon)
            app.setDesktopFileName("Origami")
            app.setApplicationDisplayName("Origami")

    initialize_database()

    app.setStyle(QStyleFactory.create('Fusion'))
    
    return app

def main():
    
    app = setup_application()

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()