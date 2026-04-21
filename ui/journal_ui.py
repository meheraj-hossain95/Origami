from datetime import datetime, date

from PySide6.QtCore import Qt, QTimer, QDate, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QCheckBox, QDateEdit, QFrame, QGraphicsDropShadowEffect,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QScrollArea, QSizePolicy, QStackedWidget,
    QTextEdit, QVBoxLayout, QWidget,
)

from database.db import get_connection, get_setting, set_setting
from database.models import JournalEntry
from utils.encryption import decrypt_journal_entry, encrypt_journal_entry

_DARK_PALETTE = {
    'background': '#121212',
    'surface': '#1e1e1e',
    'primary': '#42a5f5',
    'text_primary': '#e0e0e0',
    'text_secondary': '#a0a0a0',
    'border': '#303030',
}

_LIGHT_PALETTE = {
    'background': '#f0f2f5',
    'surface': '#ffffff',
    'primary': '#1877f2',
    'text_primary': '#212121',
    'text_secondary': '#616161',
    'border': '#e0e0e0',
}


def _get_palette(theme: str) -> dict:
    try:
        from ui.main_window import AppTheme
        return AppTheme.get_palette(theme)
    except ImportError:
        return _DARK_PALETTE if theme == 'dark' else _LIGHT_PALETTE


class JournalWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.password_manager = None
        self.is_authenticated = False
        self.password_check_done = False
        self.current_entry_date = None
        self.search_query = ""
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.stacked_widget = QStackedWidget()
        self.create_password_page()
        self.create_journal_stack()
        self.main_layout.addWidget(self.stacked_widget)
        self.check_authentication_state()

    # ── Password page ──────────────────────────────────────────────────────────

    def create_password_page(self):
        self.password_widget = QWidget()
        self.password_widget.setObjectName("passwordPromptWidget")

        main_layout = QVBoxLayout(self.password_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.blur_background = QWidget()
        self.blur_background.setObjectName("blurBackground")
        blur_layout = QVBoxLayout(self.blur_background)
        blur_layout.setAlignment(Qt.AlignCenter)
        blur_layout.setContentsMargins(50, 100, 50, 100)

        self.password_card = QFrame()
        self.password_card.setObjectName("passwordCard")
        self.password_card.setMaximumWidth(500)
        self.password_card.setMinimumHeight(400)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 10)
        self.password_card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.password_card)
        card_layout.setAlignment(Qt.AlignCenter)
        card_layout.setSpacing(30)
        card_layout.setContentsMargins(40, 50, 40, 50)

        lock_icon = QLabel("🔒")
        lock_icon.setAlignment(Qt.AlignCenter)
        lock_icon.setObjectName("lockIcon")
        lock_icon.setStyleSheet("font-size: 48px; margin-bottom: 10px;")

        title_label = QLabel("Journal Access Required")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("passwordPromptTitle")
        title_label.setStyleSheet("font-size: 28px; font-weight: bold; margin-bottom: 8px;")

        self.status_label = QLabel("Enter your journal password to continue")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setObjectName("passwordPromptStatus")
        self.status_label.setStyleSheet("font-size: 16px; margin-bottom: 20px; opacity: 0.8;")

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setObjectName("passwordPromptInput")
        self.password_input.setMinimumHeight(50)
        self.password_input.returnPressed.connect(self.verify_password)

        self.unlock_button = QPushButton("Unlock Journal")
        self.unlock_button.setObjectName("passwordPromptButton")
        self.unlock_button.setMinimumHeight(50)
        self.unlock_button.clicked.connect(self.verify_password)

        self.attempts_warning = QLabel()
        self.attempts_warning.setAlignment(Qt.AlignCenter)
        self.attempts_warning.setObjectName("passwordPromptWarning")
        self.attempts_warning.hide()

        for w in (lock_icon, title_label, self.status_label,
                  self.password_input, self.unlock_button, self.attempts_warning):
            card_layout.addWidget(w)
        card_layout.addStretch()

        blur_layout.addWidget(self.password_card, 0, Qt.AlignCenter)
        main_layout.addWidget(self.blur_background)

        self.apply_password_prompt_styling()
        self.stacked_widget.addWidget(self.password_widget)

    # ── Journal content stack ──────────────────────────────────────────────────

    def create_journal_stack(self):
        self.journal_stack = QStackedWidget()
        self.create_dashboard_page()
        self.create_entry_page()
        self.stacked_widget.addWidget(self.journal_stack)

    def create_dashboard_page(self):
        self.dashboard_widget = QWidget()
        layout = QVBoxLayout(self.dashboard_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Daily Journal")
        title_label.setFont(QFont("Arial", 24, QFont.Bold))
        title_label.setObjectName("dashboardTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Search + new entry controls
        top_bar = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by date (YYYY-MM-DD) or keyword...")
        self.search_input.setMinimumHeight(40)
        self.search_input.setObjectName("searchInput")
        self.search_input.textChanged.connect(self.filter_entries)
        top_bar.addWidget(self.search_input, 2)

        top_bar.addWidget(QLabel("New Entry:"))

        self.date_selector = QDateEdit(QDate.currentDate())
        self.date_selector.setDisplayFormat("yyyy-MM-dd")
        self.date_selector.setMinimumHeight(40)
        self.date_selector.setObjectName("dateSelector")
        self.date_selector.setCalendarPopup(True)
        top_bar.addWidget(self.date_selector)

        self.new_entry_button = QPushButton("Create Entry")
        self.new_entry_button.setMinimumHeight(40)
        self.new_entry_button.setObjectName("newEntryButton")
        self.new_entry_button.clicked.connect(self.create_new_entry)
        top_bar.addWidget(self.new_entry_button)

        layout.addLayout(top_bar)

        # Entries list header
        list_header = QHBoxLayout()
        entries_label = QLabel("Last 10 Entries")
        entries_label.setFont(QFont("Arial", 16, QFont.Bold))
        entries_label.setObjectName("entriesListTitle")
        list_header.addWidget(entries_label)
        list_header.addStretch()
        layout.addLayout(list_header)
        layout.addSpacing(5)

        # Scrollable entries list
        self.entries_scroll = QScrollArea()
        self.entries_scroll.setWidgetResizable(True)
        self.entries_scroll.setObjectName("entriesScrollArea")
        self.entries_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.entries_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.entries_list_widget = QWidget()
        self.entries_list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.entries_list_layout = QVBoxLayout(self.entries_list_widget)
        self.entries_list_layout.setSpacing(5)
        self.entries_list_layout.setContentsMargins(0, 0, 0, 0)
        self.entries_list_layout.setAlignment(Qt.AlignTop)

        self.entries_scroll.setWidget(self.entries_list_widget)
        layout.addWidget(self.entries_scroll)

        self.apply_dashboard_styling()
        self.journal_stack.addWidget(self.dashboard_widget)

    def create_entry_page(self):
        self.entry_widget = QWidget()
        layout = QVBoxLayout(self.entry_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
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

        layout.addLayout(header_layout)

        writing_label = QLabel("Your thoughts for today:")
        writing_label.setFont(QFont("Arial", 14))
        writing_label.setObjectName("writingAreaLabel")
        layout.addWidget(writing_label)

        self.entry_text_edit = QTextEdit()
        self.entry_text_edit.setPlaceholderText("Write your journal entry here...")
        self.entry_text_edit.setObjectName("entryTextEdit")
        self.entry_text_edit.setMinimumHeight(400)
        layout.addWidget(self.entry_text_edit)

        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        self.save_button = QPushButton("Save Entry")
        self.save_button.setObjectName("saveButton")
        self.save_button.setMinimumHeight(50)
        self.save_button.setMinimumWidth(150)
        self.save_button.clicked.connect(self.save_entry)
        footer_layout.addWidget(self.save_button)

        layout.addLayout(footer_layout)

        self.apply_entry_page_styling()
        self.journal_stack.addWidget(self.entry_widget)

    # ── Styling ────────────────────────────────────────────────────────────────

    def apply_password_prompt_styling(self):
        palette = _get_palette(get_setting('theme', 'light'))
        self.password_widget.setStyleSheet(f"""
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
            QLabel#passwordPromptWarning {{
                color: #ff4757;
                font-size: 14px;
                font-weight: 600;
                background-color: rgba(255, 71, 87, 0.1);
                padding: 10px 15px;
                border-radius: 8px;
            }}
        """)

    def apply_dashboard_styling(self):
        palette = _get_palette(get_setting('theme', 'light'))
        self.dashboard_widget.setStyleSheet(f"""
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
            QScrollArea#entriesScrollArea {{
                background-color: {palette['background']};
                border: none;
            }}
        """)

    def apply_entry_page_styling(self):
        palette = _get_palette(get_setting('theme', 'light'))
        self.entry_widget.setStyleSheet(f"""
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
        """)

    def apply_entry_widget_styling(self, widget):
        palette = _get_palette(get_setting('theme', 'light'))
        widget.setStyleSheet(f"""
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
        """)

    # ── Authentication ─────────────────────────────────────────────────────────

    def check_authentication_state(self):
        if self.password_check_done:
            return

        self.password_check_done = True

        try:
            from ui.profile_ui import PasswordManager
            self.password_manager = PasswordManager()

            if self.password_manager.has_password():
                self.show_password_prompt()
            else:
                self.show_journal_content()
        except Exception as e:
            print(f"Warning: authentication check failed: {e}")
            self.show_journal_content()

    def show_password_prompt(self):
        self.apply_password_prompt_styling()
        self.stacked_widget.setCurrentWidget(self.password_widget)
        self.password_input.setFocus()

    def show_journal_content(self):
        self.stacked_widget.setCurrentWidget(self.journal_stack)
        self.journal_stack.setCurrentWidget(self.dashboard_widget)
        self.is_authenticated = True
        self.load_entries()

    def verify_password(self):
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
                self.is_authenticated = True
                self.show_journal_content()
            else:
                self.password_input.clear()
                self.show_error_feedback("Incorrect password")

                if hasattr(self.password_manager, 'failed_attempts'):
                    remaining = 5 - self.password_manager.failed_attempts
                    if remaining > 0:
                        self.attempts_warning.setText(f"⚠ {remaining} attempts remaining")
                        self.attempts_warning.show()
        except Exception as e:
            self.show_error_feedback("Authentication error")
            print(f"Error verifying password: {e}")

    def show_error_feedback(self, message: str):
        self.status_label.setText(message)
        self.status_label.setStyleSheet("font-size: 14px; color: #ff4757; font-weight: 600;")
        QTimer.singleShot(3000, self.reset_status_message)

    def reset_status_message(self):
        self.status_label.setText("Enter your journal password to continue")
        self.status_label.setStyleSheet("font-size: 14px; opacity: 0.8;")

    # ── Entry navigation ───────────────────────────────────────────────────────

    def create_new_entry(self):
        selected_date = self.date_selector.date().toPython()
        self.current_entry_date = selected_date
        self.entry_date_label.setText(selected_date.strftime("%A, %B %d, %Y"))
        self.load_entry_for_date(selected_date)
        self.journal_stack.setCurrentWidget(self.entry_widget)
        self.entry_text_edit.setFocus()

    def edit_entry(self, entry_date):
        self.current_entry_date = entry_date
        self.entry_date_label.setText(entry_date.strftime("%A, %B %d, %Y"))
        self.load_entry_for_date(entry_date)
        self.journal_stack.setCurrentWidget(self.entry_widget)
        self.entry_text_edit.setFocus()

    def go_back_to_dashboard(self):
        self.journal_stack.setCurrentWidget(self.dashboard_widget)
        self.current_entry_date = None
        self.load_entries()

    # ── Entry loading & saving ─────────────────────────────────────────────────

    def load_entry_for_date(self, entry_date):
        try:
            for entry in JournalEntry.get_all():
                e_date = (entry.created_at.date() if isinstance(entry.created_at, datetime)
                          else datetime.fromisoformat(entry.created_at).date())
                if e_date == entry_date:
                    content = entry.content
                    if entry.is_encrypted and getattr(entry, 'encrypted_content', None):
                        try:
                            content = decrypt_journal_entry(entry.encrypted_content)
                        except Exception as e:
                            content = "[Encrypted content — unable to decrypt]"
                            print(f"Error decrypting entry: {e}")
                    self.entry_text_edit.setPlainText(content)
                    return
            self.entry_text_edit.clear()
        except Exception as e:
            print(f"Error loading entry for date: {e}")
            self.entry_text_edit.clear()

    def get_entry_for_date(self, entry_date):
        try:
            for entry in JournalEntry.get_all():
                e_date = (entry.created_at.date() if isinstance(entry.created_at, datetime)
                          else datetime.fromisoformat(entry.created_at).date())
                if e_date == entry_date:
                    return entry
        except Exception as e:
            print(f"Error getting entry for date: {e}")
        return None

    def save_entry(self):
        if not self.is_authenticated or not self.current_entry_date:
            return

        content = self.entry_text_edit.toPlainText().strip()
        if not content:
            self.show_save_feedback("⚠ Entry cannot be empty", "#ff4757")
            return

        try:
            existing = self.get_entry_for_date(self.current_entry_date)
            if existing:
                self._update_existing_entry(existing, content)
            else:
                self._create_new_entry_record(content)

            self.show_save_feedback("✓ Entry saved successfully", "#4CAF50")
            QTimer.singleShot(1500, self.go_back_to_dashboard)
        except Exception as e:
            self.show_save_feedback("✗ Error saving entry", "#ff4757")
            print(f"Error saving journal entry: {e}")

    def _update_existing_entry(self, entry, content: str):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE journal_entries SET content = ?, updated_at = ? WHERE id = ?",
            (content, datetime.now().isoformat(), entry.id),
        )
        conn.commit()
        conn.close()

    def _create_new_entry_record(self, content: str):
        title = f"Entry for {self.current_entry_date.strftime('%B %d, %Y')}"
        entry_datetime = datetime.combine(self.current_entry_date, datetime.min.time())
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO journal_entries (title, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (title, content, entry_datetime.isoformat(), datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()

    # ── Dashboard list ─────────────────────────────────────────────────────────

    def load_entries(self):
        if not self.is_authenticated:
            return

        # Clear existing widgets
        for i in reversed(range(self.entries_list_layout.count())):
            child = self.entries_list_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        try:
            entries = JournalEntry.get_all()

            if self.search_query:
                entries = self.filter_entries_by_search(entries, self.search_query)
            else:
                entries = entries[:10]

            if not entries:
                label = QLabel("No journal entries found.")
                label.setAlignment(Qt.AlignCenter)
                label.setObjectName("noEntriesLabel")
                label.setStyleSheet("color: #888; font-style: italic; padding: 10px; font-size: 14px;")
                self.entries_list_layout.addWidget(label)
            else:
                for entry in entries:
                    self.entries_list_layout.addWidget(self.create_entry_widget(entry))

        except Exception as e:
            label = QLabel(f"Error loading journal entries: {e}")
            label.setAlignment(Qt.AlignCenter)
            label.setObjectName("errorLabel")
            label.setStyleSheet("color: #ff4757; font-style: italic; padding: 10px; font-size: 14px;")
            self.entries_list_layout.addWidget(label)
            print(f"Error loading journal entries: {e}")

        self.entries_list_widget.adjustSize()
        self.entries_scroll.verticalScrollBar().setValue(0)

    def create_entry_widget(self, entry) -> QFrame:
        entry_frame = QFrame()
        entry_frame.setObjectName("entryFrame")
        entry_layout = QVBoxLayout(entry_frame)
        entry_layout.setContentsMargins(10, 6, 10, 6)
        entry_layout.setSpacing(4)

        header_layout = QHBoxLayout()

        entry_date = (entry.created_at.date() if isinstance(entry.created_at, datetime)
                      else datetime.fromisoformat(entry.created_at).date())

        date_label = QLabel(entry_date.strftime("%B %d, %Y"))
        date_label.setFont(QFont("Arial", 13, QFont.Bold))
        date_label.setObjectName("entryDateLabel")
        header_layout.addWidget(date_label)
        header_layout.addStretch()

        edit_button = QPushButton("Edit")
        edit_button.setObjectName("editButton")
        edit_button.clicked.connect(lambda: self.edit_entry(entry_date))

        delete_button = QPushButton("Delete")
        delete_button.setObjectName("deleteButton")
        delete_button.clicked.connect(lambda: self.delete_entry(entry))

        header_layout.addWidget(edit_button)
        header_layout.addWidget(delete_button)
        entry_layout.addLayout(header_layout)

        self.apply_entry_widget_styling(entry_frame)
        return entry_frame

    def delete_entry(self, entry):
        entry_date = (entry.created_at.date() if isinstance(entry.created_at, datetime)
                      else datetime.fromisoformat(entry.created_at).date())

        msg = QMessageBox()
        msg.setWindowTitle("Delete Entry")
        msg.setText(f"Are you sure you want to delete the entry from {entry_date.strftime('%B %d, %Y')}?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)

        if get_setting('theme', 'light') == 'dark':
            msg.setStyleSheet("""
                QMessageBox { background-color: #1e1e1e; color: #e0e0e0; }
                QPushButton {
                    background-color: #42a5f5; color: white;
                    border: none; padding: 8px 16px;
                    border-radius: 4px; min-width: 80px;
                }
                QPushButton:hover { background-color: #1976d2; }
            """)

        if msg.exec() == QMessageBox.Yes:
            try:
                entry.delete()
                self.load_entries()
                self.show_temporary_message("Entry deleted successfully", "#4CAF50")
            except Exception as e:
                self.show_temporary_message("Error deleting entry", "#f44336")
                print(f"Error deleting entry: {e}")

    # ── Search ─────────────────────────────────────────────────────────────────

    def filter_entries(self):
        self.search_query = self.search_input.text().strip()
        self.load_entries()

    def filter_entries_by_search(self, entries, query: str) -> list:
        if not query:
            return entries

        filtered = []
        query_lower = query.lower()

        for entry in entries:
            e_date = (entry.created_at.date() if isinstance(entry.created_at, datetime)
                      else datetime.fromisoformat(entry.created_at).date())

            if query in e_date.strftime("%Y-%m-%d"):
                filtered.append(entry)
                continue

            content = entry.content
            if entry.is_encrypted and getattr(entry, 'encrypted_content', None):
                try:
                    content = decrypt_journal_entry(entry.encrypted_content)
                except Exception:
                    content = ""

            if query_lower in content.lower():
                filtered.append(entry)

        return filtered

    # ── Feedback helpers ───────────────────────────────────────────────────────

    def show_save_feedback(self, message: str, color: str):
        original_text = self.save_button.text()
        original_style = self.save_button.styleSheet()
        self.save_button.setText(message)
        self.save_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white; border: none;
                border-radius: 12px; padding: 15px 30px;
                font-size: 16px; font-weight: 600;
            }}
        """)
        QTimer.singleShot(2000, lambda: [
            self.save_button.setText(original_text),
            self.save_button.setStyleSheet(original_style),
        ])

    def show_temporary_message(self, message: str, color: str):
        original_placeholder = self.search_input.placeholderText()
        original_style = self.search_input.styleSheet()
        self.search_input.setPlaceholderText(message)
        self.search_input.setStyleSheet(f"QLineEdit {{ color: {color}; font-weight: 600; }}")
        QTimer.singleShot(3000, lambda: [
            self.search_input.setPlaceholderText(original_placeholder),
            self.search_input.setStyleSheet(original_style),
        ])

    # ── Theme refresh ──────────────────────────────────────────────────────────

    def refresh_theme(self):
        if hasattr(self, 'password_widget') and self.password_widget.isVisible():
            self.apply_password_prompt_styling()
        if hasattr(self, 'dashboard_widget'):
            self.apply_dashboard_styling()
        if hasattr(self, 'entry_widget'):
            self.apply_entry_page_styling()
        if self.is_authenticated and hasattr(self, 'entries_list_layout'):
            self.load_entries()

    def showEvent(self, event):
        super().showEvent(event)
        if not self.password_check_done:
            self.check_authentication_state()
        else:
            self.refresh_theme()
            if (self.is_authenticated
                    and hasattr(self, 'journal_stack')
                    and self.journal_stack.currentWidget() == self.dashboard_widget):
                self.load_entries()