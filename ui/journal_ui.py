"""
Journal UI components with two-page design and password protection
"""
import time
from datetime import datetime, date
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QScrollArea, QTextEdit, QDateEdit,
    QLabel, QCheckBox, QMessageBox, QFrame, QStackedWidget,
    QGraphicsDropShadowEffect, QListWidget, QListWidgetItem,
    QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QDate, Signal
from PySide6.QtGui import QFont, QColor

from database.models import JournalEntry
from database.db import get_setting, set_setting
from utils.encryption import encrypt_journal_entry, decrypt_journal_entry

class JournalWidget(QWidget):
    """Journal management widget with two-page design and password protection"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.password_manager = None
        self.is_authenticated = False
        self.password_check_done = False
        self.current_entry_date = None
        self.search_query = ""
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the journal UI with password and two-page design"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create stacked widget to switch between password prompt and content
        self.stacked_widget = QStackedWidget()
        
        # Create password prompt page
        self.create_password_page()
        
        # Create journal content stack (dashboard + entry page)
        self.create_journal_stack()
        
        # Add to main layout
        self.main_layout.addWidget(self.stacked_widget)
        
        # Check authentication state
        self.check_authentication_state()
    
    def create_password_page(self):
        """Create password prompt page with modern design"""
        self.password_widget = QWidget()
        self.password_widget.setObjectName("passwordPromptWidget")
        
        # Main layout for password widget
        main_password_layout = QVBoxLayout(self.password_widget)
        main_password_layout.setContentsMargins(0, 0, 0, 0)
        main_password_layout.setSpacing(0)
        
        # Background container
        self.blur_background = QWidget()
        self.blur_background.setObjectName("blurBackground")
        blur_layout = QVBoxLayout(self.blur_background)
        blur_layout.setAlignment(Qt.AlignCenter)
        blur_layout.setContentsMargins(50, 100, 50, 100)
        
        # Password card container
        self.password_card = QFrame()
        self.password_card.setObjectName("passwordCard")
        self.password_card.setMaximumWidth(500)
        self.password_card.setMinimumHeight(400)
        
        # Add shadow effect to card
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 10)
        self.password_card.setGraphicsEffect(shadow)
        
        # Card content layout
        card_layout = QVBoxLayout(self.password_card)
        card_layout.setAlignment(Qt.AlignCenter)
        card_layout.setSpacing(30)
        card_layout.setContentsMargins(40, 50, 40, 50)
        
        # Lock icon
        lock_icon = QLabel("🔒")
        lock_icon.setAlignment(Qt.AlignCenter)
        lock_icon.setObjectName("lockIcon")
        lock_icon.setStyleSheet("font-size: 48px; margin-bottom: 10px;")
        
        # Title
        title_label = QLabel("Journal Access Required")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("passwordPromptTitle")
        title_label.setStyleSheet("font-size: 28px; font-weight: bold; margin-bottom: 8px;")
        
        # Status message
        self.status_label = QLabel("Enter your journal password to continue")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setObjectName("passwordPromptStatus")
        self.status_label.setStyleSheet("font-size: 16px; margin-bottom: 20px; opacity: 0.8;")
        
        # Password input
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setObjectName("passwordPromptInput")
        self.password_input.setMinimumHeight(50)
        self.password_input.returnPressed.connect(self.verify_password)
        
        # Unlock button
        self.unlock_button = QPushButton("Unlock Journal")
        self.unlock_button.setObjectName("passwordPromptButton")
        self.unlock_button.setMinimumHeight(50)
        self.unlock_button.clicked.connect(self.verify_password)
        
        # Failed attempts warning
        self.attempts_warning = QLabel()
        self.attempts_warning.setAlignment(Qt.AlignCenter)
        self.attempts_warning.setObjectName("passwordPromptWarning")
        self.attempts_warning.hide()
        
        # Add widgets to card layout
        card_layout.addWidget(lock_icon)
        card_layout.addWidget(title_label)
        card_layout.addWidget(self.status_label)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(self.unlock_button)
        card_layout.addWidget(self.attempts_warning)
        card_layout.addStretch()
        
        # Add card to blur background
        blur_layout.addWidget(self.password_card, 0, Qt.AlignCenter)
        main_password_layout.addWidget(self.blur_background)
        
        # Apply initial styling
        self.apply_password_prompt_styling()
        
        # Add to stacked widget
        self.stacked_widget.addWidget(self.password_widget)
    
    def create_journal_stack(self):
        """Create the journal content stack with dashboard and entry pages"""
        self.journal_stack = QStackedWidget()
        
        # Create dashboard (first page)
        self.create_dashboard_page()
        
        # Create entry editor (second page)
        self.create_entry_page()
        
        # Add to main stacked widget
        self.stacked_widget.addWidget(self.journal_stack)
    
    def create_dashboard_page(self):
        """Create the first page - dashboard with search and entries list"""
        self.dashboard_widget = QWidget()
        dashboard_layout = QVBoxLayout(self.dashboard_widget)
        dashboard_layout.setContentsMargins(20, 20, 20, 20)
        dashboard_layout.setSpacing(20)  # Reduced from 20 to 15
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Daily Journal")
        title_label.setFont(QFont("Arial", 24, QFont.Bold))
        title_label.setObjectName("dashboardTitle")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        dashboard_layout.addLayout(header_layout)
        
        # Top bar with search and new entry
        top_bar_layout = QHBoxLayout()
        
        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by date (YYYY-MM-DD) or keyword...")
        self.search_input.setMinimumHeight(40)
        self.search_input.setObjectName("searchInput")
        self.search_input.textChanged.connect(self.filter_entries)
        top_bar_layout.addWidget(self.search_input, 2)
        
        # New entry date selector
        new_entry_label = QLabel("New Entry:")
        top_bar_layout.addWidget(new_entry_label)
        
        self.date_selector = QDateEdit(QDate.currentDate())
        self.date_selector.setDisplayFormat("yyyy-MM-dd")
        self.date_selector.setMinimumHeight(40)
        self.date_selector.setObjectName("dateSelector")
        self.date_selector.setCalendarPopup(True)
        top_bar_layout.addWidget(self.date_selector)
        
        # Go to entry button
        self.new_entry_button = QPushButton("Create Entry")
        self.new_entry_button.setMinimumHeight(40)
        self.new_entry_button.setObjectName("newEntryButton")
        self.new_entry_button.clicked.connect(self.create_new_entry)
        top_bar_layout.addWidget(self.new_entry_button)
        
        dashboard_layout.addLayout(top_bar_layout)

        # Entries list header
        list_header_layout = QHBoxLayout()
        entries_label = QLabel("Last 10 Entries")
        entries_label.setFont(QFont("Arial", 16, QFont.Bold))
        entries_label.setObjectName("entriesListTitle")
        list_header_layout.addWidget(entries_label)
        
        list_header_layout.addStretch()
        
        dashboard_layout.addLayout(list_header_layout)
        
        # Add smaller spacing before entries list
        dashboard_layout.addSpacing(5)  # Small spacing before entries list
        
        # Entries list scroll area
        self.entries_scroll = QScrollArea()
        self.entries_scroll.setWidgetResizable(True)
        self.entries_scroll.setObjectName("entriesScrollArea")
        # Optimize scroll area to only take needed space
        self.entries_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.entries_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.entries_list_widget = QWidget()
        self.entries_list_layout = QVBoxLayout(self.entries_list_widget)
        self.entries_list_layout.setSpacing(5)  # Reduced spacing for tighter layout
        self.entries_list_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for tighter layout
        self.entries_list_layout.setAlignment(Qt.AlignTop)  # Ensure content aligns to top
        
        # Set size policy to prevent unnecessary expansion when fewer entries
        from PySide6.QtWidgets import QSizePolicy
        self.entries_list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        
        self.entries_scroll.setWidget(self.entries_list_widget)
        
        dashboard_layout.addWidget(self.entries_scroll)
        
        # Apply styling
        self.apply_dashboard_styling()
        
        # Add to journal stack
        self.journal_stack.addWidget(self.dashboard_widget)
    
    def create_entry_page(self):
        """Create the second page - entry editor"""
        self.entry_widget = QWidget()
        entry_layout = QVBoxLayout(self.entry_widget)
        entry_layout.setContentsMargins(20, 20, 20, 20)
        entry_layout.setSpacing(20)
        
        # Header with date and back button
        header_layout = QHBoxLayout()
        
        self.back_button = QPushButton("← Back to Journal")
        self.back_button.setObjectName("backButton")
        self.back_button.setMinimumHeight(40)
        self.back_button.clicked.connect(self.go_back_to_dashboard)
        header_layout.addWidget(self.back_button)
        
        header_layout.addStretch()
        
        self.entry_date_label = QLabel()
        self.entry_date_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.entry_date_label.setObjectName("entryDateLabel")
        header_layout.addWidget(self.entry_date_label)
        
        entry_layout.addLayout(header_layout)
        
        # Writing area
        writing_label = QLabel("Your thoughts for today:")
        writing_label.setFont(QFont("Arial", 14))
        writing_label.setObjectName("writingAreaLabel")
        entry_layout.addWidget(writing_label)
        
        self.entry_text_edit = QTextEdit()
        self.entry_text_edit.setPlaceholderText("Write your journal entry here...")
        self.entry_text_edit.setObjectName("entryTextEdit")
        self.entry_text_edit.setMinimumHeight(400)
        entry_layout.addWidget(self.entry_text_edit)
        
        # Footer with save button
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        self.save_button = QPushButton("Save Entry")
        self.save_button.setObjectName("saveButton")
        self.save_button.setMinimumHeight(50)
        self.save_button.setMinimumWidth(150)
        self.save_button.clicked.connect(self.save_entry)
        footer_layout.addWidget(self.save_button)
        
        entry_layout.addLayout(footer_layout)
        
        # Apply styling
        self.apply_entry_page_styling()
        
        # Add to journal stack
        self.journal_stack.addWidget(self.entry_widget)
    
    def apply_password_prompt_styling(self):
        """Apply theme-aware styling to password prompt"""
        current_theme = get_setting('theme', 'light')
        
        try:
            from ui.main_window import AppTheme
            palette = AppTheme.get_palette(current_theme)
        except ImportError:
            # Fallback colors
            if current_theme == 'dark':
                palette = {
                    'background': '#121212',
                    'surface': '#1e1e1e',
                    'primary': '#42a5f5',
                    'text_primary': '#e0e0e0',
                    'text_secondary': '#a0a0a0',
                    'border': '#303030'
                }
            else:
                palette = {
                    'background': '#f0f2f5',
                    'surface': '#ffffff',
                    'primary': '#1877f2',
                    'text_primary': '#212121',
                    'text_secondary': '#616161',
                    'border': '#e0e0e0'
                }
        
        style = f"""
            QWidget#blurBackground {{
                background-color: {palette['background']};
            }}
            QFrame#passwordCard {{
                background-color: {palette['surface']};
                border: 2px solid {palette['border']};
                border-radius: 20px;
            }}
            QLabel#passwordPromptTitle {{
                color: {palette['text_primary']};
                font-size: 28px; 
                font-weight: bold;
            }}
            QLabel#passwordPromptStatus {{
                color: {palette['text_secondary']};
                font-size: 16px;
            }}
            QLabel#lockIcon {{
                color: {palette['text_primary']};
                font-size: 48px;
            }}
            QLineEdit#passwordPromptInput {{
                color: {palette['text_primary']};
                background-color: {palette['surface']};
                padding: 15px 20px;
                font-size: 16px;
                border: 2px solid {palette['border']};
                border-radius: 12px;
            }}
            QLineEdit#passwordPromptInput:focus {{
                border-color: {palette['primary']};
            }}
            QPushButton#passwordPromptButton {{
                background-color: {palette['primary']};
                color: white;
                border: none;
                border-radius: 12px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: 600;
            }}
            QPushButton#passwordPromptButton:hover {{
                background-color: {palette['primary']};
                opacity: 0.9;
            }}
            QLabel#passwordPromptWarning {{
                color: #ff4757;
                font-size: 14px;
                font-weight: 600;
                background-color: rgba(255, 71, 87, 0.1);
                padding: 10px 15px;
                border-radius: 8px;
            }}
        """
        
        self.password_widget.setStyleSheet(style)
    
    def apply_dashboard_styling(self):
        """Apply theme-aware styling to dashboard"""
        current_theme = get_setting('theme', 'light')
        
        try:
            from ui.main_window import AppTheme
            palette = AppTheme.get_palette(current_theme)
        except ImportError:
            # Fallback colors
            if current_theme == 'dark':
                palette = {
                    'background': '#121212',
                    'surface': '#1e1e1e',
                    'primary': '#42a5f5',
                    'text_primary': '#e0e0e0',
                    'text_secondary': '#a0a0a0',
                    'border': '#303030'
                }
            else:
                palette = {
                    'background': '#f0f2f5',
                    'surface': '#ffffff',
                    'primary': '#1877f2',
                    'text_primary': '#212121',
                    'text_secondary': '#616161',
                    'border': '#e0e0e0'
                }
        
        style = f"""
            QWidget {{
                background-color: {palette['background']};
                color: {palette['text_primary']};
            }}
            QLabel#dashboardTitle {{
                color: {palette['text_primary']};
                font-size: 24px;
                font-weight: bold;
            }}
            QLabel#entriesListTitle {{
                color: {palette['text_primary']};
                font-size: 16px;
                font-weight: bold;
            }}
            QLineEdit#searchInput {{
                background-color: {palette['surface']};
                border: 2px solid {palette['border']};
                border-radius: 8px;
                padding: 10px 15px;
                font-size: 14px;
                color: {palette['text_primary']};
            }}
            QLineEdit#searchInput:focus {{
                border-color: {palette['primary']};
            }}
            QDateEdit#dateSelector {{
                background-color: {palette['surface']};
                border: 2px solid {palette['border']};
                border-radius: 8px;
                padding: 8px 12px;
                color: {palette['text_primary']};
                min-width: 120px;
            }}
            QPushButton#newEntryButton {{
                background-color: {palette['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
                min-width: 100px;
            }}
            QPushButton#newEntryButton:hover {{
                background-color: {palette['primary']};
                opacity: 0.9;
            }}
            QScrollArea#entriesScrollArea {{
                background-color: {palette['background']};
                border: none;
            }}
        """
        
        self.dashboard_widget.setStyleSheet(style)
    
    def apply_entry_page_styling(self):
        """Apply theme-aware styling to entry page"""
        current_theme = get_setting('theme', 'light')
        
        try:
            from ui.main_window import AppTheme
            palette = AppTheme.get_palette(current_theme)
        except ImportError:
            # Fallback colors
            if current_theme == 'dark':
                palette = {
                    'background': '#121212',
                    'surface': '#1e1e1e',
                    'primary': '#42a5f5',
                    'text_primary': '#e0e0e0',
                    'text_secondary': '#a0a0a0',
                    'border': '#303030'
                }
            else:
                palette = {
                    'background': '#f0f2f5',
                    'surface': '#ffffff',
                    'primary': '#1877f2',
                    'text_primary': '#212121',
                    'text_secondary': '#616161',
                    'border': '#e0e0e0'
                }
        
        style = f"""
            QWidget {{
                background-color: {palette['background']};
                color: {palette['text_primary']};
            }}
            QLabel#entryDateLabel {{
                color: {palette['text_primary']};
                font-size: 18px;
                font-weight: bold;
            }}
            QLabel#writingAreaLabel {{
                color: {palette['text_primary']};
                font-size: 14px;
            }}
            QPushButton#backButton {{
                background-color: {palette['text_secondary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
            }}
            QPushButton#backButton:hover {{
                background-color: {palette['text_secondary']};
                opacity: 0.8;
            }}
            QTextEdit#entryTextEdit {{
                background-color: {palette['surface']};
                border: 2px solid {palette['border']};
                border-radius: 12px;
                padding: 15px;
                font-size: 14px;
                line-height: 1.5;
                color: {palette['text_primary']};
            }}
            QTextEdit#entryTextEdit:focus {{
                border-color: {palette['primary']};
            }}
            QPushButton#saveButton {{
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: 600;
            }}
            QPushButton#saveButton:hover {{
                background-color: #45a049;
            }}
        """
        
        self.entry_widget.setStyleSheet(style)
    
    
    def check_authentication_state(self):
        """Check authentication state without triggering multiple times"""
        if self.password_check_done:
            return
        
        self.password_check_done = True
        
        try:
            # Import here to avoid circular imports
            from ui.profile_ui import PasswordManager
            
            self.password_manager = PasswordManager()
            
            if not self.password_manager.has_password():
                # No password set, show content directly
                self.show_journal_content()
            else:
                # Password required, show prompt
                self.show_password_prompt()
        except ImportError as e:
            # If PasswordManager is not available, show content directly
            print(f"Warning: PasswordManager not available: {e}")
            self.show_journal_content()
        except Exception as e:
            # Handle any other errors gracefully
            print(f"Error in authentication check: {e}")
            self.show_journal_content()
    
    def show_password_prompt(self):
        """Show password prompt"""
        self.apply_password_prompt_styling()
        self.stacked_widget.setCurrentWidget(self.password_widget)
        self.password_input.setFocus()
    
    def show_journal_content(self):
        """Show main journal content"""
        self.stacked_widget.setCurrentWidget(self.journal_stack)
        self.journal_stack.setCurrentWidget(self.dashboard_widget)
        self.is_authenticated = True
        self.load_entries()
    
    def verify_password(self):
        """Verify entered password"""
        if not self.password_input.isEnabled():
            return
        
        password = self.password_input.text()
        if not password:
            self.show_error_feedback("Please enter a password")
            return
        
        if not self.password_manager:
            self.show_error_feedback("Password manager not available")
            return
        
        try:
            if hasattr(self.password_manager, 'verify_password') and self.password_manager.verify_password(password):
                # Success - show journal content
                self.is_authenticated = True
                self.show_journal_content()
            else:
                # Failed attempt
                self.password_input.clear()
                self.show_error_feedback("Incorrect password")
                
                # Show attempts warning if available
                if hasattr(self.password_manager, 'failed_attempts'):
                    remaining = 5 - self.password_manager.failed_attempts
                    if remaining > 0:
                        self.attempts_warning.setText(f"⚠ {remaining} attempts remaining")
                        self.attempts_warning.show()
        except Exception as e:
            self.show_error_feedback("Authentication error")
            print(f"Error verifying password: {e}")
    
    def show_error_feedback(self, message):
        """Show error feedback with temporary styling"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("font-size: 14px; color: #ff4757; font-weight: 600;")
        
        # Reset to normal after 3 seconds
        QTimer.singleShot(3000, self.reset_status_message)
    
    def reset_status_message(self):
        """Reset status message to normal"""
        self.status_label.setText("Enter your journal password to continue")
        self.status_label.setStyleSheet("font-size: 14px; opacity: 0.8;")
    
    def create_new_entry(self):
        """Navigate to entry page for new entry"""
        selected_date = self.date_selector.date().toPython()
        self.current_entry_date = selected_date
        
        # Set the date label
        self.entry_date_label.setText(selected_date.strftime("%A, %B %d, %Y"))
        
        # Load existing entry for this date if it exists
        self.load_entry_for_date(selected_date)
        
        # Switch to entry page
        self.journal_stack.setCurrentWidget(self.entry_widget)
        self.entry_text_edit.setFocus()
    
    def load_entry_for_date(self, entry_date):
        """Load existing entry for the specified date"""
        try:
            # Get all entries and find one for this date
            all_entries = JournalEntry.get_all()
            
            for entry in all_entries:
                entry_date_obj = entry.created_at.date() if isinstance(entry.created_at, datetime) else datetime.fromisoformat(entry.created_at).date()
                if entry_date_obj == entry_date:
                    # Found existing entry, decrypt if needed
                    content = entry.content
                    if entry.is_encrypted and hasattr(entry, 'encrypted_content') and entry.encrypted_content:
                        try:
                            # Try to decrypt (this would need the journal password)
                            content = decrypt_journal_entry(entry.encrypted_content)
                        except Exception as e:
                            content = "[Encrypted content - unable to decrypt]"
                            print(f"Error decrypting entry: {e}")
                    
                    self.entry_text_edit.setPlainText(content)
                    return
            
            # No existing entry, clear the text area
            self.entry_text_edit.clear()
            
        except Exception as e:
            print(f"Error loading entry for date: {e}")
            self.entry_text_edit.clear()
    
    def go_back_to_dashboard(self):
        """Navigate back to dashboard"""
        self.journal_stack.setCurrentWidget(self.dashboard_widget)
        self.current_entry_date = None
        # Refresh the entries list to show any new entries
        self.load_entries()
    
    def save_entry(self):
        """Save the current entry"""
        if not self.is_authenticated or not self.current_entry_date:
            return
        
        content = self.entry_text_edit.toPlainText().strip()
        if not content:
            # Show error in save button
            self.show_save_feedback("⚠ Entry cannot be empty", "#ff4757")
            return
        
        try:
            # Check if entry already exists for this date
            existing_entry = self.get_entry_for_date(self.current_entry_date)
            
            if existing_entry:
                # Update existing entry
                self.update_existing_entry(existing_entry, content)
            else:
                # Create new entry
                self.create_new_entry_record(content)
            
            # Show success feedback
            self.show_save_feedback("✓ Entry saved successfully", "#4CAF50")
            
            # Go back to dashboard after a short delay
            QTimer.singleShot(1500, self.go_back_to_dashboard)
            
        except Exception as e:
            self.show_save_feedback("✗ Error saving entry", "#ff4757")
            print(f"Error saving journal entry: {e}")
    
    def get_entry_for_date(self, entry_date):
        """Get existing entry for the specified date"""
        try:
            all_entries = JournalEntry.get_all()
            
            for entry in all_entries:
                entry_date_obj = entry.created_at.date() if isinstance(entry.created_at, datetime) else datetime.fromisoformat(entry.created_at).date()
                if entry_date_obj == entry_date:
                    return entry
            
            return None
            
        except Exception as e:
            print(f"Error getting entry for date: {e}")
            return None
    
    def update_existing_entry(self, entry, content):
        """Update an existing journal entry"""
        try:
            # Update the entry in database
            from database.db import get_connection
            
            conn = get_connection()
            cursor = conn.cursor()
            
            # For now, store as plain text (encryption can be added later)
            cursor.execute('''
                UPDATE journal_entries 
                SET content = ?, updated_at = ?
                WHERE id = ?
            ''', (content, datetime.now().isoformat(), entry.id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            raise Exception(f"Failed to update entry: {str(e)}")
    
    def create_new_entry_record(self, content):
        """Create a new journal entry record"""
        try:
            # Create entry with the selected date
            entry_title = f"Entry for {self.current_entry_date.strftime('%B %d, %Y')}"
            
            # Create the entry
            from database.db import get_connection
            
            conn = get_connection()
            cursor = conn.cursor()
            
            # Use the selected date as the created_at timestamp
            entry_datetime = datetime.combine(self.current_entry_date, datetime.min.time())
            
            cursor.execute('''
                INSERT INTO journal_entries (title, content, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (entry_title, content, entry_datetime.isoformat(), datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            raise Exception(f"Failed to create entry: {str(e)}")
    
    def show_save_feedback(self, message, color):
        """Show feedback in the save button"""
        original_text = self.save_button.text()
        original_style = self.save_button.styleSheet()
        
        self.save_button.setText(message)
        self.save_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 12px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: 600;
            }}
        """)
        
        # Reset button after delay
        QTimer.singleShot(2000, lambda: [
            self.save_button.setText(original_text),
            self.save_button.setStyleSheet(original_style)
        ])
    
    def load_entries(self):
        """Load and display journal entries on dashboard"""
        if not self.is_authenticated:
            return
        
        # Clear existing entries
        for i in reversed(range(self.entries_list_layout.count())):
            child = self.entries_list_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        try:
            # Load entries from database
            entries = JournalEntry.get_all()
            
            # Apply search filter if active
            if self.search_query:
                entries = self.filter_entries_by_search(entries, self.search_query)
            
            # Limit to last 10 entries if no search
            if not self.search_query:
                entries = entries[:10]
            
            if not entries:
                no_entries_label = QLabel("No journal entries found.")
                no_entries_label.setAlignment(Qt.AlignCenter)
                no_entries_label.setObjectName("noEntriesLabel")
                no_entries_label.setStyleSheet("color: #888; font-style: italic; padding: 10px; font-size: 14px;")  # Reduced padding
                self.entries_list_layout.addWidget(no_entries_label)
            else:
                for entry in entries:
                    entry_widget = self.create_entry_widget(entry)
                    self.entries_list_layout.addWidget(entry_widget)
        
        except Exception as e:
            error_label = QLabel(f"Error loading journal entries: {str(e)}")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setObjectName("errorLabel")
            error_label.setStyleSheet("color: #ff4757; font-style: italic; padding: 10px; font-size: 14px;")  # Reduced padding
            self.entries_list_layout.addWidget(error_label)
            print(f"Error loading journal entries: {e}")
        
        # Remove the addStretch() to prevent gaps when there are fewer than 10 entries
        # The scroll area will automatically size based on content
        
        # Ensure proper widget sizing after loading entries
        self.entries_list_widget.adjustSize()
        self.entries_scroll.ensureWidgetVisible(self.entries_list_widget)
        
        # Scroll to top to avoid gaps, especially after search
        self.entries_scroll.verticalScrollBar().setValue(0)
    
    def create_entry_widget(self, entry):
        """Create a widget for displaying a journal entry"""
        entry_frame = QFrame()
        entry_frame.setObjectName("entryFrame")
        entry_layout = QVBoxLayout(entry_frame)
        entry_layout.setContentsMargins(10, 6, 10, 6)  # Further reduced margins for lower height
        entry_layout.setSpacing(4)  # Further reduced spacing for more compact layout
        
        # Header with date
        header_layout = QHBoxLayout()
        
        entry_date = entry.created_at.date() if isinstance(entry.created_at, datetime) else datetime.fromisoformat(entry.created_at).date()
        date_label = QLabel(entry_date.strftime("%B %d, %Y"))
        date_label.setFont(QFont("Arial", 13, QFont.Bold))  # Reduced font size for more compact layout
        date_label.setObjectName("entryDateLabel")
        header_layout.addWidget(date_label)
        
        header_layout.addStretch()
        
        # Edit and Delete buttons
        edit_button = QPushButton("Edit")
        edit_button.setObjectName("editButton")
        edit_button.clicked.connect(lambda: self.edit_entry(entry_date))
        
        delete_button = QPushButton("Delete")
        delete_button.setObjectName("deleteButton")
        delete_button.clicked.connect(lambda: self.delete_entry(entry))
        
        header_layout.addWidget(edit_button)
        header_layout.addWidget(delete_button)
        
        entry_layout.addLayout(header_layout)
        
        # Apply styling
        self.apply_entry_widget_styling(entry_frame)
        
        return entry_frame
    
    def apply_entry_widget_styling(self, widget):
        """Apply styling to entry widget"""
        current_theme = get_setting('theme', 'light')
        
        try:
            from ui.main_window import AppTheme
            palette = AppTheme.get_palette(current_theme)
        except ImportError:
            if current_theme == 'dark':
                palette = {
                    'surface': '#1e1e1e',
                    'text_primary': '#e0e0e0',
                    'text_secondary': '#a0a0a0',
                    'border': '#303030',
                    'primary': '#42a5f5'
                }
            else:
                palette = {
                    'surface': '#ffffff',
                    'text_primary': '#212121',
                    'text_secondary': '#616161',
                    'border': '#e0e0e0',
                    'primary': '#1877f2'
                }
        
        style = f"""
            QFrame#entryFrame {{
                background-color: {palette['surface']};
                border: 2px solid {palette['border']};
                border-radius: 8px;
                margin: 2px 0px;
                max-height: 50px;
                min-height: 45px;
            }}
            QFrame#entryFrame:hover {{
                border-color: {palette['primary']};
            }}
            QLabel#entryDateLabel {{
                color: {palette['text_primary']};
                font-size: 13px;
                font-weight: bold;
                background-color: transparent;
                padding: 2px 0px;
            }}
            QPushButton#editButton {{
                background-color: {palette['primary']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 600;
                min-width: 55px;
                max-height: 28px;
                min-height: 28px;
            }}
            QPushButton#editButton:hover {{
                background-color: {palette['primary']};
                opacity: 0.8;
            }}
            QPushButton#deleteButton {{
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 600;
                min-width: 55px;
                max-height: 28px;
                min-height: 28px;
            }}
            QPushButton#deleteButton:hover {{
                background-color: #d32f2f;
            }}
        """
        
        widget.setStyleSheet(style)
    
    def edit_entry(self, entry_date):
        """Edit an existing entry"""
        self.current_entry_date = entry_date
        self.entry_date_label.setText(entry_date.strftime("%A, %B %d, %Y"))
        self.load_entry_for_date(entry_date)
        self.journal_stack.setCurrentWidget(self.entry_widget)
        self.entry_text_edit.setFocus()
    
    def delete_entry(self, entry):
        """Delete a journal entry with confirmation"""
        entry_date = entry.created_at.date() if isinstance(entry.created_at, datetime) else datetime.fromisoformat(entry.created_at).date()
        
        # Show confirmation dialog
        msg = QMessageBox()
        msg.setWindowTitle("Delete Entry")
        msg.setText(f"Are you sure you want to delete the entry from {entry_date.strftime('%B %d, %Y')}?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        
        # Apply theme to message box
        current_theme = get_setting('theme', 'light')
        if current_theme == 'dark':
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                }
                QPushButton {
                    background-color: #42a5f5;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #1976d2;
                }
            """)
        
        result = msg.exec()
        
        if result == QMessageBox.Yes:
            try:
                # Delete the entry
                entry.delete()
                
                # Reload entries
                self.load_entries()
                
                # Show success message briefly
                self.show_temporary_message("Entry deleted successfully", "#4CAF50")
                
            except Exception as e:
                self.show_temporary_message("Error deleting entry", "#f44336")
                print(f"Error deleting entry: {e}")
    
    def show_temporary_message(self, message, color):
        """Show a temporary message in the search bar"""
        original_placeholder = self.search_input.placeholderText()
        original_style = self.search_input.styleSheet()
        
        self.search_input.setPlaceholderText(message)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                color: {color};
                font-weight: 600;
            }}
        """)
        
        # Reset after 3 seconds
        QTimer.singleShot(3000, lambda: [
            self.search_input.setPlaceholderText(original_placeholder),
            self.search_input.setStyleSheet(original_style)
        ])
    
    def filter_entries(self):
        """Filter entries based on search query"""
        query = self.search_input.text().strip()
        self.search_query = query
        
        self.load_entries()
    
    def filter_entries_by_search(self, entries, query):
        """Filter entries by search query"""
        if not query:
            return entries
        
        filtered_entries = []
        query_lower = query.lower()
        
        for entry in entries:
            # Check date match (YYYY-MM-DD format)
            entry_date = entry.created_at.date() if isinstance(entry.created_at, datetime) else datetime.fromisoformat(entry.created_at).date()
            if query in entry_date.strftime("%Y-%m-%d"):
                filtered_entries.append(entry)
                continue
            
            # Check content match (decrypt if needed)
            content = entry.content
            if entry.is_encrypted and hasattr(entry, 'encrypted_content') and entry.encrypted_content:
                try:
                    content = decrypt_journal_entry(entry.encrypted_content)
                except Exception:
                    content = ""  # Skip encrypted content that can't be decrypted
            
            if query_lower in content.lower():
                filtered_entries.append(entry)
        
        return filtered_entries
    
    def refresh_theme(self):
        """Refresh theme styling when app theme changes"""
        if hasattr(self, 'password_widget') and self.password_widget.isVisible():
            self.apply_password_prompt_styling()
        
        if hasattr(self, 'dashboard_widget'):
            self.apply_dashboard_styling()
        
        if hasattr(self, 'entry_widget'):
            self.apply_entry_page_styling()
        
        # Reload entries to apply new theme styling
        if self.is_authenticated and hasattr(self, 'entries_list_layout'):
            self.load_entries()
    
    def showEvent(self, event):
        """Called when widget is shown"""
        super().showEvent(event)
        if not self.password_check_done:
            self.check_authentication_state()
        else:
            # Refresh styling for theme changes
            self.refresh_theme()
            # Refresh entries if authenticated and on dashboard
            if self.is_authenticated and hasattr(self, 'journal_stack') and self.journal_stack.currentWidget() == self.dashboard_widget:
                self.load_entries()
