import sys
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QMenuBar, QStatusBar, QMessageBox, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QStackedWidget,
    QSplitter, QFrame, QGraphicsDropShadowEffect, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QIcon, QKeySequence, QPalette, QFont, QPixmap, QColor
from datetime import datetime

# Assuming these are in your project
from ui.todo_ui import TodoWidget
from ui.journal_ui import JournalWidget
from ui.calendar_ui import CalendarWidget
from ui.pomodoro_ui import PomodoroWidget
from ui.profile_ui import ProfileWidget
from database.db import get_setting, set_setting
from database.models import User
from quotes import get_random_quote

# --- Theme Definitions ---
class AppTheme:
    """Manages color palettes for different themes."""
    
    # Define color palettes for light and dark modes
    LIGHT_PALETTE = {
        'background': '#f0f2f5',  # Light gray, similar to Google/Facebook bg
        'surface': '#ffffff',     # White for cards/widgets
        'primary': '#1877f2',     # Facebook blue, or a similar strong brand color
        'on_primary': '#ffffff',  # White text on primary
        'text_primary': '#212121',# Dark gray for main text
        'text_secondary': '#616161',# Medium gray for secondary text
        'border': '#e0e0e0',      # Light border for separation
        'sidebar_bg': '#ffffff',
        'sidebar_border': '#e0e0e0',
        'sidebar_text': '#424242',
        'sidebar_text_selected': '#1877f2',
        'sidebar_item_hover': '#f0f2f5',
        'menu_bg': '#ffffff',
        'menu_text': '#424242',
        'menu_hover_bg': '#e0e0e0',
        'status_bar_bg': '#ffffff',
        'status_bar_text': '#616161',
    }

    DARK_PALETTE = {
        'background': '#121212',  # Dark background
        'surface': '#1e1e1e',     # Slightly lighter dark for cards/widgets
        'primary': '#42a5f5',     # Lighter blue for dark mode primary
        'on_primary': '#ffffff',  # White text on primary
        'text_primary': '#e0e0e0',# Light gray for main text
        'text_secondary': '#a0a0a0',# Medium light gray for secondary text
        'border': '#303030',      # Dark border for separation
        'sidebar_bg': '#1e1e1e',
        'sidebar_border': '#303030',
        'sidebar_text': '#a0a0a0',
        'sidebar_text_selected': '#42a5f5',
        'sidebar_item_hover': '#2a2a2a',
        'menu_bg': '#1e1e1e',
        'menu_text': '#e0e0e0',
        'menu_hover_bg': '#2a2a2a',
        'status_bar_bg': '#1e1e1e',
        'status_bar_text': '#a0a0a0',
    }

    @staticmethod
    def get_palette(theme_name):
        return AppTheme.DARK_PALETTE if theme_name == 'dark' else AppTheme.LIGHT_PALETTE

    @staticmethod
    def get_stylesheet(theme_name):
        palette = AppTheme.get_palette(theme_name)
        
        # Determine profile button text color based on theme
        # In light theme, use text_primary; in dark theme, use on_primary (white)
        profile_button_text_color = palette['text_primary'] if theme_name == 'light' else palette['on_primary']

        # Base styles for the entire application
        base_styles = f"""
            * {{
                font-family: 'Poppins', 'Work Sans', 'Roboto', 'Segoe UI', sans-serif;
                font-size: 17px;
                color: {palette['text_primary']};
            }}
            QMainWindow {{
                background-color: {palette['background']};
            }}
            QLabel {{
                color: {palette['text_primary']};
            }}
            QFrame {{
                background-color: {palette['surface']};
                border: none;
            }}
            QPushButton {{
                background-color: {palette['primary']};
                color: {palette['on_primary']};
                border: none;
                padding: 10px 15px;
                border-radius: 8px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {QColor(palette['primary']).lighter(110).name()};
            }}
            QPushButton:pressed {{
                background-color: {QColor(palette['primary']).darker(110).name()};
            }}
        """

        # Sidebar specific styles
        sidebar_styles = f"""
            QFrame#sidebarFrame {{ /* Use an object name for targeted styling */
                background-color: {palette['sidebar_bg']};
                border-right: 1px solid {palette['sidebar_border']};
            }}
            QPushButton#hamburgerButton {{
                background-color: transparent;
                border: 2px solid {palette['border']};
                border-radius: 8px;
                color: {palette['text_secondary']};
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton#hamburgerButton:hover {{
                background-color: {palette['sidebar_item_hover']};
                border-color: {palette['primary']};
                color: {palette['primary']};
            }}
            QPushButton#hamburgerButton:pressed {{
                background-color: {QColor(palette['primary']).lighter(150).name()};
            }}
            QListWidget {{
                background: {palette['sidebar_bg']};
                border: none;
                outline: none;
                padding: 10px 0px;
                selection-background-color: transparent;
            }}
            QListWidget::item {{
                background: transparent;
                padding: 12px 20px;
                border-radius: 8px;
                margin: 4px 0px;
                color: {palette['sidebar_text']};
                font-size: 14px;
                font-weight: 500;
            }}
            QListWidget::item:selected {{
                background-color: {palette['primary']};
                color: {palette['on_primary']};
                font-weight: 600;
            }}
            QListWidget::item:hover:!selected {{
                background-color: {palette['sidebar_item_hover']};
                color: {palette['sidebar_text_selected']};
            }}
            QLabel#versionLabel, QLabel#copyrightLabel {{
                color: {palette['text_secondary']};
                font-size: 11px;
            }}
            QPushButton#profileButton {{
                background-color: {palette['primary']};
                color: {profile_button_text_color}; /* Dynamic text color based on theme */
                border: 1px solid {palette['primary']};
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: 600;
                margin: 1px 0px;
                min-width: 70px;
            }}
            QPushButton#profileButton:hover {{
                background-color: {QColor(palette['primary']).lighter(115).name()};
                border-color: {QColor(palette['primary']).lighter(115).name()};
            }}
            QPushButton#profileButton:pressed {{
                background-color: {QColor(palette['primary']).darker(110).name()};
                border-color: {QColor(palette['primary']).darker(110).name()};
            }}
        """

        # Content area styles
        content_area_styles = f"""
            QStackedWidget {{
                background-color: {palette['background']};
            }}
            QWidget#welcomeWidget {{ /* Target WelcomeWidget specifically */
                background-color: {palette['background']};
            }}
            QLabel#greetingLabel {{
                font-size: 48px; 
                font-weight: 300;
                margin: 30px;
                color: {palette['text_primary']};
                letter-spacing: 1px;
                background-color: transparent; 
            }}
            QLabel#quoteLabel {{
                font-size: 18px; 
                font-style: italic; 
                line-height: 1.6;
                color: {palette['text_secondary']};
                font-weight: 400;
                background-color: transparent;
            }}
            /* Dashboard specific styles */
            QScrollArea {{
                background-color: {palette['background']};
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: {palette['background']};
            }}
            /* Ensure all labels have transparent backgrounds */
            QLabel {{
                background-color: transparent;
            }}
            /* Dashboard cards container styling */
            QFrame {{
                background-color: transparent;
            }}
        """

        # Status bar styles
        status_styles = f"""
            QStatusBar {{
                background-color: {palette['status_bar_bg']};
                color: {palette['status_bar_text']};
                border-top: 1px solid {palette['border']};
                padding: 5px;
                font-size: 12px;
            }}
            QMessageBox {{
                background-color: {palette['surface']};
                color: {palette['text_primary']};
            }}
            QMessageBox QPushButton {{
                background-color: {palette['primary']};
                color: {palette['on_primary']};
            }}
            QMessageBox QPushButton:hover {{
                background-color: {QColor(palette['primary']).lighter(110).name()};
            }}
        """
        
        return base_styles + sidebar_styles + content_area_styles + status_styles

# --- Modified WelcomeWidget ---
class WelcomeWidget(QWidget):
    """Welcome widget with time-based greeting and motivational quotes"""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("welcomeWidget") # Set object name for styling
        self.setup_ui()
        self.update_greeting()
        
        # Update greeting every minute
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_greeting)
        self.timer.start(60000)  # Update every minute
    
    def refresh_theme(self):
        """Refresh theme for welcome widget components"""
        # Update greeting and quote label styles based on current theme
        theme = get_setting('theme', 'light')
        
        if theme == 'dark':
            self.greeting_label.setStyleSheet("""
                QLabel#greetingLabel {
                    color: #e0e0e0;
                    background-color: transparent;
                }
            """)
            self.quote_label.setStyleSheet("""
                QLabel#quoteLabel {
                    color: #a0a0a0;
                    background-color: transparent;
                }
            """)
        else:
            self.greeting_label.setStyleSheet("""
                QLabel#greetingLabel {
                    color: #212121;
                    background-color: transparent;
                }
            """)
            self.quote_label.setStyleSheet("""
                QLabel#quoteLabel {
                    color: #616161;
                    background-color: transparent;
                }
            """)
        
        # Refresh dashboard cards
        if hasattr(self, 'upcoming_events_card') and hasattr(self.upcoming_events_card, 'refresh_theme'):
            self.upcoming_events_card.refresh_theme()
        if hasattr(self, 'task_completion_card') and hasattr(self.task_completion_card, 'refresh_theme'):
            self.task_completion_card.refresh_theme()
        
        # Force update the entire widget
        self.update()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(30, 100, 30, 100)
        layout.setSpacing(20) # Adjusted spacing
        
        # Greeting label
        self.greeting_label = QLabel()
        self.greeting_label.setObjectName("greetingLabel") # Object name for styling
        self.greeting_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.greeting_label)
        
        # Quote container (no specific styling here, relies on global QFrame)
        quote_container = QFrame()
        quote_container.setStyleSheet("background-color: transparent;") # Ensure no background on container
        quote_layout = QVBoxLayout(quote_container)
        quote_layout.setContentsMargins(20, 20, 20, 20) # Padding for quote
        
        # Quote label
        self.quote_label = QLabel()
        self.quote_label.setObjectName("quoteLabel") # Object name for styling
        self.quote_label.setAlignment(Qt.AlignCenter)
        self.quote_label.setWordWrap(True)
        quote_layout.addWidget(self.quote_label)
        
        layout.addWidget(quote_container)
        
        # Cards section - horizontal layout for side-by-side cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(24)  # Better spacing between cards
        cards_layout.setContentsMargins(20, 0, 20, 20)  # Margins around the cards section
        
        # Upcoming Events Card
        from ui.calendar_ui import UpcomingEventsCard
        self.upcoming_events_card = UpcomingEventsCard()
        cards_layout.addWidget(self.upcoming_events_card)
        
        # Task Completion Card
        from ui.task_completion_card import TaskCompletionCard
        self.task_completion_card = TaskCompletionCard()
        cards_layout.addWidget(self.task_completion_card)
        
        layout.addLayout(cards_layout)
        
        # Add some breathing space
        layout.addStretch()
        
        self.setLayout(layout)
    
    def update_greeting(self):
        # Get current time
        now = datetime.now()
        hour = now.hour
        
        # Get user display handle or fallback to username
        display_handle = get_setting('display_handle', '')
        user_name = get_setting('username', get_setting('user_name', 'User'))
        
        # Set greeting based on time of day with personalization
        if 5 <= hour < 12:
            base_greeting = "Good Morning"
        elif 12 <= hour < 17:
            base_greeting = "Good Afternoon"
        else:
            base_greeting = "Good Evening"
        
        # Use display handle if available, otherwise username
        if display_handle and display_handle.strip():
            greeting = f"{base_greeting}, {display_handle}"
        elif user_name and user_name != "User":
            greeting = f"{base_greeting}, {user_name}"
        else:
            greeting = f"{base_greeting}"
        
        self.greeting_label.setText(greeting)
        
        # Get random quote from quotes file
        random_quote = get_random_quote()
        self.quote_label.setText(random_quote)

# --- Modified MainWindow ---
class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Origami - Productivity & Wellness")
        self.setGeometry(100, 100, 1400, 900)
        
        # Set window icon
        self.set_window_icon()
        
        # Initialize sidebar properties
        self.sidebar_width = 265 # Fixed sidebar width
        
        # Setup UI
        self.setup_ui()
        self.setup_status_bar()
        
        # Load settings and apply theme
        self.load_settings()
        self.apply_theme()
    
    def set_window_icon(self):
        """Set the window icon with proper path resolution"""
        # Handle both development and PyInstaller executable paths
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable
            base_path = sys._MEIPASS
        else:
            # Running as script
            base_path = os.path.dirname(os.path.dirname(__file__))
        
        icon_path = os.path.join(base_path, 'assets', 'icons', 'app_icon.ico')
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.setWindowIcon(icon)
    

    def setup_ui(self):
        """Setup the main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal layout
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create sidebar
        self.setup_sidebar()
        self.main_layout.addWidget(self.sidebar_frame)
        
        # Create main content area
        self.setup_content_area()
        self.main_layout.addWidget(self.content_area)
        
        # Set initial page
        self.show_page(0)  # Show welcome page by default
    
    def setup_sidebar(self):
        """Setup the navigation sidebar with professional design"""
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setObjectName("sidebarFrame") # Object name for styling
        self.sidebar_frame.setFixedWidth(self.sidebar_width)
        
        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.setContentsMargins(20, 15, 20, 20)
        sidebar_layout.setSpacing(15)
        
        # Navigation list with modern styling
        self.nav_list = QListWidget()
        self.nav_list.setFrameStyle(QFrame.NoFrame)
        self.nav_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Remove scrollbar
        self.nav_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Remove scrollbar
        
        # Add navigation items
        self.nav_items_data = [
            ("Dashboard", "welcome"),
            ("Tasks", "todo"),
            ("Journal", "journal"), 
            ("Calendar", "calendar"),
            ("Focus Timer", "pomodoro")
        ]
        
        for text, data in self.nav_items_data:
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, data)
            self.nav_list.addItem(item)
        
        self.nav_list.setCurrentRow(0)  # Select first item by default
        self.nav_list.currentRowChanged.connect(self.show_page)
        
        sidebar_layout.addWidget(self.nav_list)
        
        # Professional footer section
        self.footer_frame = QFrame()
        self.footer_frame.setStyleSheet("background-color: transparent; border: none;") # Rely on global styles
        footer_layout = QVBoxLayout(self.footer_frame)
        footer_layout.setSpacing(5)  # Reduced spacing to bring elements closer
        footer_layout.setContentsMargins(0, 10, 0, 0)
        
        # Profile button (shows user name and acts as profile access)
        self.profile_button = QPushButton("User")
        self.profile_button.setObjectName("profileButton")
        self.profile_button.clicked.connect(self.show_profile)
        self.profile_button.setFixedHeight(40)
        self.profile_button.setCursor(Qt.PointingHandCursor)  # Ensure cursor changes
        self.profile_button.setStyleSheet("""
            QPushButton#profileButton {
                background-color: #3B5284;       /* Neutral professional blue */
                color: #ffffff;                   /* White text */
                border: none;
                border-radius: 5px;
                font-weight: 600;
                font-size: 13px;
                padding: 10px 10px;
            }
            QPushButton#profileButton:hover {
                background-color: #1e70d1;       /* Slightly lighter on hover */
            }
            QPushButton#profileButton:pressed {
                background-color: #0f4c8c;       /* Slightly darker on press */
            }
        """)

        # Version info with modern styling
        self.version_label = QLabel("Version 1.0.0")
        self.version_label.setObjectName("versionLabel")
        self.version_label.setAlignment(Qt.AlignCenter)
        
        # Copyright with professional look
        self.copyright_label = QLabel("© 2025 Origami")
        self.copyright_label.setObjectName("copyrightLabel")
        self.copyright_label.setAlignment(Qt.AlignCenter)
        
        footer_layout.addWidget(self.profile_button)
        footer_layout.addWidget(self.version_label)
        footer_layout.addWidget(self.copyright_label)
        
        sidebar_layout.addWidget(self.footer_frame)
    

    
    def setup_content_area(self):
        """Setup the main content area"""
        self.content_area = QStackedWidget()
        
        # Create widgets
        self.welcome_widget = WelcomeWidget()
        self.todo_widget = TodoWidget()
        self.journal_widget = JournalWidget()
        self.calendar_widget = CalendarWidget()
        self.pomodoro_widget = PomodoroWidget()
        self.profile_widget = ProfileWidget()
        
        # Connect signals
        self.profile_widget.profile_updated.connect(self.update_user_display)
        self.profile_widget.password_removed.connect(self.handle_password_removed)
        self.profile_widget.theme_changed.connect(self.handle_theme_change)
        
        # Connect todo widget to task completion card
        self.todo_widget.tasks_updated.connect(self.update_task_completion_card)
        
        # Connect calendar widget to upcoming events card for immediate refresh
        self.calendar_widget.events_changed.connect(self.refresh_upcoming_events)
        
        widgets_to_add = [
            self.welcome_widget,
            self.todo_widget,
            self.journal_widget,
            self.calendar_widget,
            self.pomodoro_widget,
            self.profile_widget
        ]
        
        for widget in widgets_to_add:
            # Wrap each widget in a QScrollArea if content might exceed visible area
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setWidget(widget)
            scroll_area.setFrameShape(QFrame.NoFrame) # No border for scroll area
            scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
            self.content_area.addWidget(scroll_area)
    
    def show_page(self, index):
        """Show the selected page"""
        if 0 <= index < 5:  # Only handle the 5 main navigation pages
            self.content_area.setCurrentIndex(index)
            
            # If showing dashboard (index 0), refresh the task completion card
            if index == 0 and hasattr(self, 'welcome_widget') and hasattr(self.welcome_widget, 'task_completion_card'):
                self.welcome_widget.task_completion_card.update_stats()
            
            # Update status bar based on current page
            pages = ["Dashboard", "Tasks", "Journal", "Calendar", "Focus Timer"]
            if index < len(pages):
                self.statusBar().showMessage(f"Current page: {pages[index]}")
    
    def show_profile(self):
        """Show the profile page"""
        # Profile widget is at index 5 (after the 5 main pages)
        self.content_area.setCurrentIndex(5)
        self.statusBar().showMessage("Current page: Profile")
        
        # Deselect any navigation item
        self.nav_list.setCurrentRow(-1)
    
    def update_task_completion_card(self):
        """Update the task completion card when tasks change"""
        if hasattr(self, 'welcome_widget') and hasattr(self.welcome_widget, 'task_completion_card'):
            self.welcome_widget.task_completion_card.update_stats()
    
    def refresh_upcoming_events(self):
        """Refresh the upcoming events card immediately when calendar events change"""
        if hasattr(self, 'welcome_widget') and hasattr(self.welcome_widget, 'upcoming_events_card'):
            self.welcome_widget.upcoming_events_card.refresh_events_immediately()
    
    def handle_theme_change(self, theme):
        """Handle theme change from profile widget"""
        self.apply_theme()
        
        # Also refresh theme for any open modal dialogs
        from ui.calendar_ui import EventModal
        for child in self.findChildren(EventModal):
            if hasattr(child, 'refresh_theme'):
                child.refresh_theme()
    
    def update_user_display(self, name):
        """Update the user display when profile is changed"""
        self.profile_button.setText(f"{name}")
        self.profile_button.setToolTip("")
        
        # Update the greeting in welcome widget
        self.welcome_widget.update_greeting()
        
        self.statusBar().showMessage(f"Profile updated for {name}", 3000)
    
    def handle_password_removed(self):
        """Handle when password is removed from profile"""
        # Reset journal authentication state so it doesn't ask for password anymore
        self.journal_widget.reset_authentication_state()
        self.statusBar().showMessage("Password removed - journal access updated", 3000)
    
    def setup_status_bar(self):
        """Setup the status bar"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        # Styles applied via AppTheme.get_stylesheet
        status_bar.showMessage("Ready")
    
    def apply_theme(self):
        """Apply the current theme dynamically."""
        # Prevent recursive calls during theme application
        if hasattr(self, '_applying_theme') and self._applying_theme:
            return
        
        self._applying_theme = True
        try:
            theme_name = get_setting('theme', 'light') # Default to light
            
            # Apply the combined stylesheet
            self.setStyleSheet(AppTheme.get_stylesheet(theme_name))
            
            # Manually update elements that don't inherit QMainWindow style easily
            # For example, the status bar might need a direct refresh
            palette = AppTheme.get_palette(theme_name)
            self.statusBar().setStyleSheet(f"QStatusBar {{ background-color: {palette['status_bar_bg']}; color: {palette['status_bar_text']}; border-top: 1px solid {palette['border']}; padding: 5px; font-size: 12px; }}")
            
            # Re-apply stylesheet to specific widgets if their styles don't cascade properly
            # Or, ideally, ensure all styles are in the global stylesheet with object names
            self.nav_list.setStyleSheet(AppTheme.get_stylesheet(theme_name) + """
                QListWidget {
                    background: %s;
                    border: none;
                    outline: none;
                    padding: 10px 0px;
                    selection-background-color: transparent;
                }
                QListWidget::item {
                    background: transparent;
                    padding: 10px 18px;
                    border-radius: 4px;
                    margin: 4px 0px;
                    color: %s;
                    font-size: 16px;
                    font-weight: 700;
                }
                QListWidget::item:selected {
                    background-color: %s;
                    color: %s;
                    font-weight: 800;
                }
                QListWidget::item:hover:!selected {
                    background-color: %s;
                    color: %s;
                }
            """ % (
                palette['sidebar_bg'], palette['sidebar_text'], 
                palette['primary'], palette['on_primary'], 
                palette['sidebar_item_hover'], palette['sidebar_text_selected']
            ))
            
            # Refresh theme for all widgets that support it
            widgets_to_refresh = [
                self.welcome_widget,
                self.todo_widget,
                self.journal_widget, 
                self.calendar_widget,
                self.pomodoro_widget,
                self.profile_widget
            ]
            
            for widget in widgets_to_refresh:
                if hasattr(widget, 'refresh_theme'):
                    widget.refresh_theme()
            
            # Also refresh theme for any open modal dialogs
            from ui.calendar_ui import EventModal
            for child in self.findChildren(EventModal):
                if hasattr(child, 'refresh_theme'):
                    child.refresh_theme()
                    
            # Refresh any other common widget types
            from ui.common_widgets import CustomCard, ModernButton
            for child in self.findChildren(CustomCard):
                if hasattr(child, 'refresh_theme'):
                    child.refresh_theme()
            for child in self.findChildren(ModernButton):
                if hasattr(child, 'refresh_theme'):
                    child.refresh_theme()
            
            # Ensure all QLabels across the application have transparent backgrounds
            for label in self.findChildren(QLabel):
                current_style = label.styleSheet()
                if 'background-color: transparent' not in current_style:
                    new_style = current_style + '; background-color: transparent;' if current_style else 'background-color: transparent;'
                    label.setStyleSheet(new_style)
                    
        finally:
            self._applying_theme = False



    def load_settings(self):
        """Load application settings"""
        # Load username for profile button
        username = get_setting('username', get_setting('user_name', 'User'))
        self.profile_button.setText(f"{username}")
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        pass
    
    
    def closeEvent(self, event):
        """Handle application close event"""
        # Accept the close event without confirmation
        event.accept()
    
    def resizeEvent(self, event):
        """Handle window resize event"""
        super().resizeEvent(event)
        # Removed responsive sidebar collapsing