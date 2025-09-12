"""
Personal Software - A comprehensive productivity and wellness application
Entry point for the application
"""
import sys
import os
from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtCore import QDir, Qt
from PySide6.QtGui import QIcon

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow
from database.db import initialize_database
import config

def setup_application():
    """Initialize the application and database"""
    app = QApplication(sys.argv)
    app.setApplicationName("Origami")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Personal Productivity")
    
    # Set application icon if available
    # Handle both development and PyInstaller executable paths
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        base_path = sys._MEIPASS
    else:
        # Running as script
        base_path = os.path.dirname(__file__)
    
    icon_path = os.path.join(base_path, 'assets', 'icons', 'app_icon.ico')
    if os.path.exists(icon_path):
        icon = QIcon(icon_path)
        # Set multiple icon sizes for better system integration
        app.setWindowIcon(icon)
        # Set application properties for better taskbar integration
        app.setDesktopFileName("Origami")
        app.setApplicationDisplayName("Origami")
        # Force icon refresh for taskbar
        app.setQuitOnLastWindowClosed(True)
    else:
        # Fallback to PNG if ICO doesn't exist
        png_icon_path = os.path.join(base_path, 'assets', 'icons', 'app_icon.png')
        if os.path.exists(png_icon_path):
            icon = QIcon(png_icon_path)
            app.setWindowIcon(icon)
            app.setDesktopFileName("Origami")
            app.setApplicationDisplayName("Origami")
    
    # Initialize database
    initialize_database()
    
    # Set application style
    app.setStyle(QStyleFactory.create('Fusion'))
    
    return app

def main():
    """Main entry point"""
    app = setup_application()
    
    # Create and show main window
    main_window = MainWindow()
    main_window.show()
    
    # Start the application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

