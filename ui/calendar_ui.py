from functools import partial
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QDialog, QTextEdit, QButtonGroup, QRadioButton,
    QMessageBox, QScrollArea, QGridLayout, QSizePolicy, QSpacerItem, QComboBox
)
from PySide6.QtCore import Qt, QDate, QTimer, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QCursor, QPalette
from datetime import datetime, date, timedelta
from database.models import CalendarEvent
from database.db import get_setting
from ui.common_widgets import CustomCard


# ---------------------------------------------------------------------------
# Style sheets
# ---------------------------------------------------------------------------

_CALENDAR_DARK = """
    ModernCalendarWidget { background-color: #121212; color: #e0e0e0; }
    QWidget { background-color: #121212; color: #e0e0e0; }
    QPushButton#navButton {
        background-color: #2d2d2d; color: #ffffff;
        border: 2px solid #404040; border-radius: 20px;
        font-size: 16px; font-weight: bold;
    }
    QPushButton#navButton:hover { background-color: #404040; border-color: #42a5f5; }
    QPushButton#navButton:pressed { background-color: #1a1a1a; }
    QLabel#monthYearLabel { color: #ffffff; }
    QLabel#dayHeader {
        color: #a0a0a0; padding: 10px; background-color: #2d2d2d;
        border-radius: 5px; margin: 2px;
    }
    QPushButton#dateButton {
        background-color: #1e1e1e; color: #e0e0e0;
        border: 1px solid #303030; border-radius: 8px;
        padding: 8px; min-height: 40px; font-size: 14px; font-weight: 500;
    }
    QPushButton#dateButton:hover { background-color: #2d2d2d; border-color: #42a5f5; }
    QPushButton#dateButtonToday {
        background-color: #42a5f5; color: #ffffff;
        border: 1px solid #1976d2; border-radius: 8px;
        padding: 8px; min-height: 40px; font-size: 14px; font-weight: bold;
    }
    QPushButton#dateButtonTodayWithEvent {
        background-color: #8e24aa; color: #ffffff;
        border: 3px solid #6a1b9a; border-radius: 8px;
        padding: 8px; min-height: 40px; font-size: 14px; font-weight: bold;
    }
    QPushButton#dateButtonTodayWithEvent:hover { background-color: #ab47bc; }
    QPushButton#dateButtonRed {
        background-color: #ff4444; color: #ffffff;
        border: 1px solid #303030; border-radius: 8px;
        padding: 8px; min-height: 40px; font-size: 14px; font-weight: bold;
    }
    QPushButton#dateButtonRed:hover { background-color: #ff6666; border-color: #42a5f5; }
    QPushButton#dateButtonYellow {
        background-color: #ffaa00; color: #ffffff;
        border: 1px solid #303030; border-radius: 8px;
        padding: 8px; min-height: 40px; font-size: 14px; font-weight: bold;
    }
    QPushButton#dateButtonYellow:hover { background-color: #ffbb22; border-color: #42a5f5; }
    QPushButton#dateButtonGreen {
        background-color: #44aa44; color: #ffffff;
        border: 1px solid #303030; border-radius: 8px;
        padding: 8px; min-height: 40px; font-size: 14px; font-weight: bold;
    }
    QPushButton#dateButtonGreen:hover { background-color: #66bb66; border-color: #42a5f5; }
    QPushButton#dateButtonEmpty {
        background-color: #1e1e1e; color: transparent;
        border: 1px solid #303030; border-radius: 8px;
        padding: 8px; min-height: 40px;
    }
"""

_CALENDAR_LIGHT = """
    ModernCalendarWidget { background-color: #f0f2f5; color: #212121; }
    QWidget { background-color: #f0f2f5; color: #212121; }
    QPushButton#navButton {
        background-color: #ffffff; color: #333333;
        border: 2px solid #e0e0e0; border-radius: 20px;
        font-size: 16px; font-weight: bold;
    }
    QPushButton#navButton:hover { background-color: #f0f2f5; border-color: #1877f2; color: #1877f2; }
    QPushButton#navButton:pressed { background-color: #e0e0e0; }
    QLabel#monthYearLabel { color: #212121; }
    QLabel#dayHeader {
        color: #616161; padding: 10px; background-color: #f5f5f5;
        border-radius: 5px; margin: 2px;
    }
    QPushButton#dateButton {
        background-color: #ffffff; color: #212121;
        border: 1px solid #e0e0e0; border-radius: 8px;
        padding: 8px; min-height: 40px; font-size: 14px; font-weight: 500;
    }
    QPushButton#dateButton:hover { background-color: #f0f2f5; border-color: #1877f2; }
    QPushButton#dateButtonToday {
        background-color: #1877f2; color: #ffffff;
        border: 1px solid #1565c0; border-radius: 8px;
        padding: 8px; min-height: 40px; font-size: 14px; font-weight: bold;
    }
    QPushButton#dateButtonTodayWithEvent {
        background-color: #8e24aa; color: #ffffff;
        border: 3px solid #6a1b9a; border-radius: 8px;
        padding: 8px; min-height: 40px; font-size: 14px; font-weight: bold;
    }
    QPushButton#dateButtonTodayWithEvent:hover { background-color: #ab47bc; }
    QPushButton#dateButtonRed {
        background-color: #ff4444; color: #ffffff;
        border: 1px solid #e0e0e0; border-radius: 8px;
        padding: 8px; min-height: 40px; font-size: 14px; font-weight: bold;
    }
    QPushButton#dateButtonRed:hover { background-color: #ff6666; border-color: #1877f2; }
    QPushButton#dateButtonYellow {
        background-color: #ffaa00; color: #ffffff;
        border: 1px solid #e0e0e0; border-radius: 8px;
        padding: 8px; min-height: 40px; font-size: 14px; font-weight: bold;
    }
    QPushButton#dateButtonYellow:hover { background-color: #ffbb22; border-color: #1877f2; }
    QPushButton#dateButtonGreen {
        background-color: #44aa44; color: #ffffff;
        border: 1px solid #e0e0e0; border-radius: 8px;
        padding: 8px; min-height: 40px; font-size: 14px; font-weight: bold;
    }
    QPushButton#dateButtonGreen:hover { background-color: #66bb66; border-color: #1877f2; }
    QPushButton#dateButtonEmpty {
        background-color: #ffffff; color: transparent;
        border: 1px solid #e0e0e0; border-radius: 8px;
        padding: 8px; min-height: 40px;
    }
"""

_EVENT_MODAL_DARK = """
    QDialog { background-color: #1e1e1e; color: #e0e0e0; }
    QLabel { color: #e0e0e0; }
    QLabel#dateLabel { color: #42a5f5; font-weight: 600; }
    QTextEdit {
        background-color: #2d2d2d; color: #e0e0e0;
        border: 2px solid #404040; border-radius: 8px;
        padding: 10px; font-size: 14px;
    }
    QTextEdit:focus { border-color: #42a5f5; }
    QRadioButton { color: #e0e0e0; spacing: 10px; }
    QRadioButton::indicator { width: 18px; height: 18px; }
    QRadioButton::indicator:unchecked {
        border: 2px solid #404040; border-radius: 9px; background-color: #2d2d2d;
    }
    QRadioButton::indicator:checked {
        border: 2px solid #42a5f5; border-radius: 9px; background-color: #42a5f5;
    }
    QPushButton#saveButton {
        background-color: #42a5f5; color: #ffffff;
        border: none; border-radius: 8px;
        padding: 12px 24px; font-weight: 600; min-width: 80px;
    }
    QPushButton#saveButton:hover { background-color: #1976d2; }
    QPushButton#cancelButton {
        background-color: #404040; color: #e0e0e0;
        border: none; border-radius: 8px;
        padding: 12px 24px; font-weight: 600; min-width: 80px;
    }
    QPushButton#cancelButton:hover { background-color: #505050; }
    QPushButton#deleteButton {
        background-color: #f44336; color: #ffffff;
        border: none; border-radius: 8px;
        padding: 12px 24px; font-weight: 600; min-width: 80px;
    }
    QPushButton#deleteButton:hover { background-color: #d32f2f; }
"""

_EVENT_MODAL_LIGHT = """
    QDialog { background-color: #ffffff; color: #212121; }
    QLabel { color: #212121; }
    QLabel#dateLabel { color: #1877f2; font-weight: 600; }
    QTextEdit {
        background-color: #ffffff; color: #212121;
        border: 2px solid #e0e0e0; border-radius: 8px;
        padding: 10px; font-size: 14px;
    }
    QTextEdit:focus { border-color: #1877f2; }
    QRadioButton { color: #212121; spacing: 10px; }
    QRadioButton::indicator { width: 18px; height: 18px; }
    QRadioButton::indicator:unchecked {
        border: 2px solid #e0e0e0; border-radius: 9px; background-color: #ffffff;
    }
    QRadioButton::indicator:checked {
        border: 2px solid #1877f2; border-radius: 9px; background-color: #1877f2;
    }
    QPushButton#saveButton {
        background-color: #1877f2; color: #ffffff;
        border: none; border-radius: 8px;
        padding: 12px 24px; font-weight: 600; min-width: 80px;
    }
    QPushButton#saveButton:hover { background-color: #1565c0; }
    QPushButton#cancelButton {
        background-color: #e0e0e0; color: #212121;
        border: none; border-radius: 8px;
        padding: 12px 24px; font-weight: 600; min-width: 80px;
    }
    QPushButton#cancelButton:hover { background-color: #d0d0d0; }
    QPushButton#deleteButton {
        background-color: #f44336; color: #ffffff;
        border: none; border-radius: 8px;
        padding: 12px 24px; font-weight: 600; min-width: 80px;
    }
    QPushButton#deleteButton:hover { background-color: #d32f2f; }
"""

_CALENDAR_WIDGET_DARK = """
    QWidget { background-color: #121212; color: #e0e0e0; }
    QFrame { background-color: #121212; color: #e0e0e0; }
    QFrame#eventSectionFrame {
        background-color: #1e1e1e; border: 2px solid #404040;
        border-radius: 12px; margin: 0px;
    }
    QLabel#eventSectionTitle { color: #ffffff; background-color: transparent; border: none; }
    QScrollArea { background-color: #121212; border: none; }
    QScrollArea > QWidget > QWidget { background-color: #121212; }
    QLabel#headerLabel { color: #ffffff; margin-bottom: 10px; }
    QLabel#selectedDateLabel {
        color: #42a5f5; font-weight: 600; background-color: transparent; border: none;
    }
    QLabel#eventDescriptionLabel { color: #e0e0e0; font-weight: 600; background-color: transparent; border: none; }
    QLabel#priorityLabel { color: #e0e0e0; font-weight: 600; background-color: transparent; border: none; }
    QLabel { color: #e0e0e0; background-color: transparent; }
    QTextEdit {
        background-color: #2d2d2d; color: #e0e0e0;
        border: 2px solid #404040; border-radius: 8px;
        padding: 10px; font-size: 14px;
    }
    QTextEdit:focus { border-color: #42a5f5; }
    QPushButton#priorityButton {
        background-color: #2d2d2d; color: #e0e0e0;
        border: 2px solid #404040; border-radius: 8px;
        padding: 10px; font-size: 13px; font-weight: 600; min-height: 20px;
    }
    QPushButton#priorityButton:hover { border-color: #42a5f5; background-color: #404040; }
    QPushButton#priorityButton:checked {
        background-color: #42a5f5; border-color: #1976d2; color: #ffffff;
    }
    QPushButton#priorityButton:pressed { background-color: #1976d2; }
    QComboBox {
        background-color: #2d2d2d; color: #e0e0e0;
        border: 2px solid #404040; border-radius: 6px;
        padding: 10px; font-size: 14px; min-height: 25px;
    }
    QComboBox:hover { border-color: #42a5f5; }
    QComboBox::drop-down {
        border: none; width: 30px; background-color: #2d2d2d;
        border-top-right-radius: 6px; border-bottom-right-radius: 6px;
    }
    QComboBox::down-arrow {
        image: none; border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid #e0e0e0; margin-right: 10px;
    }
    QComboBox QAbstractItemView {
        background-color: #2d2d2d; color: #e0e0e0;
        border: 1px solid #404040; selection-background-color: #42a5f5;
        selection-color: #ffffff; border-radius: 4px;
        padding: 6px; min-height: 25px;
    }
    QPushButton#saveEventButton {
        background-color: #42a5f5; color: #ffffff;
        border: none; border-radius: 8px;
        padding: 15px 24px; font-weight: 600; font-size: 16px; min-height: 25px;
    }
    QPushButton#saveEventButton:hover { background-color: #1976d2; }
    QPushButton#saveEventButton:pressed { background-color: #1565c0; }
    QPushButton#deleteEventButton {
        background-color: #f44336; color: #ffffff;
        border: none; border-radius: 8px;
        padding: 15px 24px; font-weight: 600; font-size: 16px; min-height: 25px;
    }
    QPushButton#deleteEventButton:hover { background-color: #d32f2f; }
    QPushButton#deleteEventButton:pressed { background-color: #b71c1c; }
"""

_CALENDAR_WIDGET_LIGHT = """
    QWidget { background-color: #f0f2f5; color: #212121; }
    QFrame { background-color: #f0f2f5; color: #212121; }
    QFrame#eventSectionFrame {
        background-color: #ffffff; border: 2px solid #e0e0e0;
        border-radius: 12px; margin: 0px;
    }
    QLabel#eventSectionTitle { color: #212121; background-color: transparent; border: none; }
    QScrollArea { background-color: #f0f2f5; border: none; }
    QScrollArea > QWidget > QWidget { background-color: #f0f2f5; }
    QLabel#headerLabel { color: #212121; margin-bottom: 10px; }
    QLabel#selectedDateLabel {
        color: #1877f2; font-weight: 600; background-color: transparent; border: none;
    }
    QLabel#eventDescriptionLabel { color: #212121; font-weight: 600; background-color: transparent; border: none; }
    QLabel#priorityLabel { color: #212121; font-weight: 600; background-color: transparent; border: none; }
    QLabel { color: #212121; background-color: transparent; }
    QTextEdit {
        background-color: #ffffff; color: #212121;
        border: 2px solid #e0e0e0; border-radius: 8px;
        padding: 10px; font-size: 14px;
    }
    QTextEdit:focus { border-color: #1877f2; }
    QPushButton#priorityButton {
        background-color: #ffffff; color: #212121;
        border: 2px solid #d0d0d0; border-radius: 8px;
        padding: 10px; font-size: 13px; font-weight: 600; min-height: 20px;
    }
    QPushButton#priorityButton:hover { border-color: #1877f2; background-color: #f0f2f5; }
    QPushButton#priorityButton:checked {
        background-color: #1877f2; border-color: #1565c0; color: #ffffff;
    }
    QPushButton#priorityButton:pressed { background-color: #1565c0; }
    QComboBox {
        background-color: #ffffff; color: #212121;
        border: 2px solid #d0d0d0; border-radius: 6px;
        padding: 10px; font-size: 14px; min-height: 25px;
    }
    QComboBox:hover { border-color: #1877f2; }
    QComboBox::drop-down {
        border: none; width: 30px; background-color: #ffffff;
        border-top-right-radius: 6px; border-bottom-right-radius: 6px;
    }
    QComboBox::down-arrow {
        image: none; border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid #555555; margin-right: 10px;
    }
    QComboBox QAbstractItemView {
        background-color: #ffffff; color: #212121;
        border: 1px solid #d0d0d0; selection-background-color: #1877f2;
        selection-color: #ffffff; border-radius: 4px;
        padding: 6px; min-height: 25px;
    }
    QPushButton#saveEventButton {
        background-color: #1877f2; color: #ffffff;
        border: none; border-radius: 8px;
        padding: 15px 24px; font-weight: 600; font-size: 16px; min-height: 25px;
    }
    QPushButton#saveEventButton:hover { background-color: #1565c0; }
    QPushButton#saveEventButton:pressed { background-color: #0d47a1; }
    QPushButton#deleteEventButton {
        background-color: #f44336; color: #ffffff;
        border: none; border-radius: 8px;
        padding: 15px 24px; font-weight: 600; font-size: 16px; min-height: 25px;
    }
    QPushButton#deleteEventButton:hover { background-color: #d32f2f; }
    QPushButton#deleteEventButton:pressed { background-color: #b71c1c; }
"""

_MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

_PRIORITY_OBJECT_NAMES = {
    'important': 'dateButtonRed',
    'next_important': 'dateButtonYellow',
    'normal': 'dateButtonGreen',
}


# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------

class ModernCalendarWidget(QWidget):

    date_clicked = Signal(QDate)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_month = QDate.currentDate().month()
        self.current_year = QDate.currentDate().year()
        self.events = {}
        self.date_buttons = {}
        self.setup_ui()
        self.load_events()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header: prev / month-year / next
        header_layout = QHBoxLayout()

        self.prev_button = QPushButton("◀")
        self.prev_button.setFixedSize(40, 40)
        self.prev_button.setObjectName("navButton")
        self.prev_button.clicked.connect(self.previous_month)
        header_layout.addWidget(self.prev_button)

        self.month_year_label = QLabel()
        self.month_year_label.setAlignment(Qt.AlignCenter)
        self.month_year_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.month_year_label.setObjectName("monthYearLabel")
        header_layout.addWidget(self.month_year_label, 1)

        self.next_button = QPushButton("▶")
        self.next_button.setFixedSize(40, 40)
        self.next_button.setObjectName("navButton")
        self.next_button.clicked.connect(self.next_month)
        header_layout.addWidget(self.next_button)

        layout.addLayout(header_layout)

        # Day-of-week headers (Sunday-first)
        self.calendar_grid = QGridLayout()
        self.calendar_grid.setSpacing(2)
        for i, day in enumerate(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]):
            lbl = QLabel(day)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFont(QFont("Arial", 12, QFont.Bold))
            lbl.setObjectName("dayHeader")
            self.calendar_grid.addWidget(lbl, 0, i)

        layout.addLayout(self.calendar_grid)

        self.update_calendar()
        self.apply_theme()

    def apply_theme(self):
        theme = get_setting('theme', 'light')
        self.setStyleSheet(_CALENDAR_DARK if theme == 'dark' else _CALENDAR_LIGHT)

    def update_calendar(self):
        for button in self.date_buttons.values():
            button.deleteLater()
        self.date_buttons.clear()

        self.month_year_label.setText(
            f"{_MONTH_NAMES[self.current_month - 1]} {self.current_year}"
        )

        first_day = QDate(self.current_year, self.current_month, 1)
        days_in_month = first_day.daysInMonth()
        start_weekday = first_day.dayOfWeek()  # 1=Monday … 7=Sunday

        # Convert to Sunday-based column index (0=Sun, 1=Mon, …)
        start_col = 0 if start_weekday == 7 else start_weekday
        today = QDate.currentDate()

        # Fixed 5-row × 7-column grid (rows 1-5; row 0 is the header)
        for row in range(1, 6):
            for col in range(7):
                day_number = (row - 1) * 7 + col - start_col + 1

                if 1 <= day_number <= days_in_month:
                    button_date = QDate(self.current_year, self.current_month, day_number)
                    date_key = button_date.toString("yyyy-MM-dd")
                    has_events = bool(self.events.get(date_key))
                    is_today = button_date == today

                    btn = QPushButton(str(day_number))
                    btn.setCursor(QCursor(Qt.PointingHandCursor))
                    btn.date_info = button_date
                    btn.clicked.connect(partial(self.emit_date_clicked, button_date))

                    if has_events and is_today:
                        btn.setObjectName("dateButtonTodayWithEvent")
                    elif has_events:
                        priority = self.events[date_key][0].priority
                        btn.setObjectName(_PRIORITY_OBJECT_NAMES.get(priority, "dateButtonGreen"))
                    elif is_today:
                        btn.setObjectName("dateButtonToday")
                    else:
                        btn.setObjectName("dateButton")

                    self.date_buttons[date_key] = btn
                else:
                    btn = QPushButton("")
                    btn.setObjectName("dateButtonEmpty")
                    btn.setEnabled(False)

                self.calendar_grid.addWidget(btn, row, col)

        self.style().unpolish(self)
        self.style().polish(self)

    def emit_date_clicked(self, date):
        self.date_clicked.emit(date)

        # Propagate the active date up to the CalendarWidget parent if present
        parent = self.parent()
        while parent and not isinstance(parent, CalendarWidget):
            parent = parent.parent()
        if parent:
            parent._active_date = date

    def previous_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.update_calendar()
        self.load_events()

    def next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.update_calendar()
        self.load_events()

    def load_events(self):
        self.events.clear()
        for event in CalendarEvent.get_all():
            date_key = event.event_date.isoformat()
            self.events.setdefault(date_key, []).append(event)
        self.update_calendar()

    def refresh_theme(self):
        self.apply_theme()
        self.update_calendar()


class EventModal(QDialog):

    event_saved = Signal(object)
    event_deleted = Signal(object)

    def __init__(self, event_date, event=None, parent=None):
        super().__init__(parent)
        self.event_date = event_date
        self.event = event
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setup_ui()
        self.apply_theme()
        if event:
            self.load_event_data()

    def setup_ui(self):
        self.setWindowTitle("Event Details")
        self.setFixedSize(600, 450)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title_label = QLabel("Add Event" if not self.event else "Edit Event")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        date_label = QLabel(f"Date: {self.event_date.toString('MMMM d, yyyy')}")
        date_label.setFont(QFont("Arial", 12))
        date_label.setObjectName("dateLabel")
        layout.addWidget(date_label)

        layout.addWidget(QLabel("Event Description:"))

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Enter event details...")
        self.description_input.setMinimumHeight(100)
        self.description_input.setMaximumHeight(150)
        layout.addWidget(self.description_input)

        layout.addWidget(QLabel("Priority:"))

        self.priority_group = QButtonGroup(self)

        self.important_radio = QRadioButton("🔴 High")
        self.important_radio.setFont(QFont("Arial", 11))
        self.priority_group.addButton(self.important_radio, 1)
        layout.addWidget(self.important_radio)

        self.next_important_radio = QRadioButton("🟡 Medium")
        self.next_important_radio.setFont(QFont("Arial", 11))
        self.priority_group.addButton(self.next_important_radio, 2)
        layout.addWidget(self.next_important_radio)

        self.normal_radio = QRadioButton("🟢 Low")
        self.normal_radio.setFont(QFont("Arial", 11))
        self.normal_radio.setChecked(True)
        self.priority_group.addButton(self.normal_radio, 3)
        layout.addWidget(self.normal_radio)

        buttons_layout = QHBoxLayout()

        if self.event:
            self.delete_button = QPushButton("Delete")
            self.delete_button.setObjectName("deleteButton")
            self.delete_button.clicked.connect(self.delete_event)
            buttons_layout.addWidget(self.delete_button)

        buttons_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        self.save_button = QPushButton("Save")
        self.save_button.setObjectName("saveButton")
        self.save_button.clicked.connect(self.save_event)
        buttons_layout.addWidget(self.save_button)

        layout.addLayout(buttons_layout)

    def apply_theme(self):
        theme = get_setting('theme', 'light')
        self.setStyleSheet(_EVENT_MODAL_DARK if theme == 'dark' else _EVENT_MODAL_LIGHT)

    def refresh_theme(self):
        self.apply_theme()

    def load_event_data(self):
        if not self.event:
            return
        self.description_input.setText(self.event.description)
        if self.event.priority == 'important':
            self.important_radio.setChecked(True)
        elif self.event.priority == 'next_important':
            self.next_important_radio.setChecked(True)
        else:
            self.normal_radio.setChecked(True)

    def get_selected_priority(self):
        if self.important_radio.isChecked():
            return 'important'
        if self.next_important_radio.isChecked():
            return 'next_important'
        return 'normal'

    def save_event(self):
        description = self.description_input.toPlainText().strip()
        if not description:
            QMessageBox.warning(self, "Warning", "Please enter an event description.")
            return

        priority = self.get_selected_priority()

        if self.event:
            self.event.update(description=description, priority=priority)
        else:
            event_date_py = self.event_date.toPython()
            event_id = CalendarEvent.create(
                title=description[:50],
                description=description,
                event_date=event_date_py,
                priority=priority,
            )
            self.event = CalendarEvent(
                id=event_id,
                title=description[:50],
                description=description,
                event_date=event_date_py,
                priority=priority,
            )

        self.event_saved.emit(self.event)
        self.accept()

    def delete_event(self):
        if not self.event:
            return
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this event?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.event.delete()
            self.event_deleted.emit(self.event)
            self.accept()


class UpcomingEventsCard(CustomCard):

    def __init__(self, parent=None):
        super().__init__("Upcoming Events", parent)
        self.setup_events_ui()
        self.load_events()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.load_events)
        self.refresh_timer.start(300_000)  # 5 minutes

    def setup_events_ui(self):
        self.events_layout = QVBoxLayout()
        self.events_layout.setSpacing(8)
        self.content_layout.addLayout(self.events_layout)

    def refresh_events_immediately(self):
        self.load_events()

    def refresh_theme(self):
        super().refresh_theme()
        self.load_events()

    def load_events(self):
        for i in reversed(range(self.events_layout.count())):
            widget = self.events_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        upcoming_events = CalendarEvent.get_upcoming_events(limit=2)

        if not upcoming_events:
            lbl = QLabel("No upcoming events scheduled")
            lbl.setStyleSheet(
                "color: #888; font-style: italic; padding: 30px 20px; "
                "font-size: 14px; text-align: center; "
                "background-color: transparent; font-weight: 500;"
            )
            lbl.setAlignment(Qt.AlignCenter)
            self.events_layout.addWidget(lbl)
        else:
            for event in upcoming_events:
                self.events_layout.addWidget(self.create_event_widget(event))

    def create_event_widget(self, event):
        event_frame = QFrame()
        event_frame.setObjectName("eventFrame")

        layout = QVBoxLayout(event_frame)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)

        header_layout = QHBoxLayout()

        date_label = QLabel(event.get_formatted_date())
        date_label.setFont(QFont("Arial", 13, QFont.Bold))
        date_label.setObjectName("eventDate")
        date_label.setStyleSheet("background-color: transparent; border: none;")
        header_layout.addWidget(date_label)
        header_layout.addStretch()

        priority_dot = QFrame()
        priority_dot.setFixedSize(12, 12)
        priority_dot.setStyleSheet(
            f"background-color: {event.get_priority_color()}; "
            "border-radius: 6px; border: none;"
        )
        priority_dot.setToolTip(f"Priority: {event.get_priority_display()}")
        header_layout.addWidget(priority_dot)

        layout.addLayout(header_layout)

        from ui.common_widgets import MarqueeLabel
        desc_label = MarqueeLabel(event.description)
        desc_label.setObjectName("eventDescription")
        desc_label.setFont(QFont("Arial", 12))
        desc_label.setStyleSheet("background-color: transparent; border: none;")
        layout.addWidget(desc_label)

        theme = get_setting('theme', 'light')
        if theme == 'dark':
            event_frame.setStyleSheet("""
                QFrame#eventFrame {
                    background-color: #262626; border: 2px solid #505050;
                    border-radius: 12px; margin: 4px 0px;
                }
                QLabel#eventDate {
                    color: #64b5f6; font-weight: 700;
                    background-color: transparent; border: none;
                }
                QLabel#eventDescription, MarqueeLabel#eventDescription {
                    color: #e8e8e8; background-color: transparent; border: none;
                }
            """)
        else:
            event_frame.setStyleSheet("""
                QFrame#eventFrame {
                    background-color: #f8f9fa; border: 2px solid #c6cbd1;
                    border-radius: 12px; margin: 4px 0px;
                }
                QLabel#eventDate {
                    color: #1565c0; font-weight: 700;
                    background-color: transparent; border: none;
                }
                QLabel#eventDescription, MarqueeLabel#eventDescription {
                    color: #495057; background-color: transparent; border: none;
                }
            """)

        return event_frame


class CalendarWidget(QWidget):

    events_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_date = QDate.currentDate()
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 20, 0, 20)

        calendar_container = QWidget()
        calendar_layout = QVBoxLayout(calendar_container)
        calendar_layout.setContentsMargins(10, 0, 10, 0)

        self.calendar = ModernCalendarWidget()
        self.calendar.date_clicked.connect(self.on_date_clicked)
        calendar_layout.addWidget(self.calendar)
        layout.addWidget(calendar_container)

        event_section_container = QWidget()
        event_section_layout = QVBoxLayout(event_section_container)
        event_section_layout.setContentsMargins(10, 0, 10, 0)

        self.setup_event_section()
        event_section_layout.addWidget(self.create_event_section())
        layout.addWidget(event_section_container)

        layout.addStretch()

    def setup_event_section(self):

        self.event_description = None
        self.priority_dropdown = None
        self.selected_date_label = None
        self.desc_label = None
        self.priority_label = None
        self.save_button = None
        self.delete_button = None

    def create_event_section(self):
        event_container = QWidget()
        event_layout = QVBoxLayout(event_container)
        event_layout.setContentsMargins(0, 0, 0, 0)
        event_layout.setSpacing(15)

        event_frame = QFrame()
        event_frame.setObjectName("eventSectionFrame")
        frame_layout = QVBoxLayout(event_frame)
        frame_layout.setContentsMargins(20, 20, 20, 20)
        frame_layout.setSpacing(15)

        title_label = QLabel("Add Event")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setObjectName("eventSectionTitle")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("background-color: transparent; border: none;")
        frame_layout.addWidget(title_label)

        self.selected_date_label = QLabel(
            f"Selected Date: {self.selected_date.toString('MMMM d, yyyy')}"
        )
        self.selected_date_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.selected_date_label.setObjectName("selectedDateLabel")
        self.selected_date_label.setStyleSheet(
            "color: #1877f2; background-color: transparent; border: none; font-weight: 600;"
        )
        frame_layout.addWidget(self.selected_date_label)

        self.event_description = QTextEdit()
        self.event_description.setPlaceholderText("Enter event details...")
        self.event_description.setMinimumHeight(120)
        self.event_description.setMaximumHeight(200)
        self.event_description.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        frame_layout.addWidget(self.event_description)

        # Priority row
        priority_row = QHBoxLayout()
        priority_row.setSpacing(15)

        self.priority_label = QLabel("Priority:")
        self.priority_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.priority_label.setObjectName("priorityLabel")
        self.priority_label.setStyleSheet("background-color: transparent; border: none;")
        self.priority_label.setFixedWidth(60)
        priority_row.addWidget(self.priority_label)

        self.priority_button_group = QButtonGroup(self)

        self.important_button = QPushButton("🔴 High")
        self.important_button.setObjectName("priorityButton")
        self.important_button.setCheckable(True)
        self.important_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.important_button.setMinimumHeight(40)
        self.priority_button_group.addButton(self.important_button, 0)
        priority_row.addWidget(self.important_button)

        self.next_important_button = QPushButton("🟡 Medium")
        self.next_important_button.setObjectName("priorityButton")
        self.next_important_button.setCheckable(True)
        self.next_important_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.next_important_button.setMinimumHeight(40)
        self.priority_button_group.addButton(self.next_important_button, 1)
        priority_row.addWidget(self.next_important_button)

        self.normal_button = QPushButton("🟢 Low")
        self.normal_button.setObjectName("priorityButton")
        self.normal_button.setCheckable(True)
        self.normal_button.setChecked(True)
        self.normal_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.normal_button.setMinimumHeight(40)
        self.priority_button_group.addButton(self.normal_button, 2)
        priority_row.addWidget(self.normal_button)

        frame_layout.addLayout(priority_row)

        # Action buttons
        button_row = QHBoxLayout()
        button_row.setSpacing(15)
        button_row.addStretch()

        self.delete_button = QPushButton("Delete Event")
        self.delete_button.setObjectName("deleteEventButton")
        self.delete_button.setMinimumHeight(45)
        self.delete_button.setFixedWidth(200)
        self.delete_button.clicked.connect(self.delete_event)
        self.delete_button.hide()
        button_row.addWidget(self.delete_button)

        self.save_button = QPushButton("Save Event")
        self.save_button.setObjectName("saveEventButton")
        self.save_button.setMinimumHeight(45)
        self.save_button.setFixedWidth(200)
        self.save_button.clicked.connect(self.save_event)
        button_row.addWidget(self.save_button)

        button_row.addStretch()
        frame_layout.addLayout(button_row)

        event_layout.addWidget(event_frame)
        self.ensure_button_colors()
        return event_container

    def on_date_clicked(self, date):
        self.selected_date = date
        self.selected_date_label.setText(
            f"Selected Date: {date.toString('MMMM d, yyyy')}"
        )
        self.ensure_label_transparency()

        existing_events = CalendarEvent.get_by_date(date.toPython())
        if existing_events:
            event = existing_events[0]
            self.event_description.setText(event.description)
            if event.priority == 'important':
                self.important_button.setChecked(True)
            elif event.priority == 'next_important':
                self.next_important_button.setChecked(True)
            else:
                self.normal_button.setChecked(True)
            self.delete_button.show()
        else:
            self.event_description.clear()
            self.normal_button.setChecked(True)
            self.delete_button.hide()

        self.apply_theme()

    def save_event(self):
        description = self.event_description.toPlainText().strip()
        if not description:
            self.selected_date_label.setText(
                f"Selected Date: {self.selected_date.toString('MMMM d, yyyy')} "
                "- Please enter description"
            )
            return

        priority_data = self.get_selected_priority()
        existing_events = CalendarEvent.get_by_date(self.selected_date.toPython())

        if existing_events:
            existing_events[0].update(description=description, priority=priority_data)
            status = "Event Updated!"
        else:
            CalendarEvent.create(
                title=description[:50],
                description=description,
                event_date=self.selected_date.toPython(),
                priority=priority_data,
            )
            status = "Event Saved!"

        self.selected_date_label.setText(
            f"Selected Date: {self.selected_date.toString('MMMM d, yyyy')} - {status}"
        )

        self.calendar.load_events()
        self.events_changed.emit()

        self.event_description.clear()
        self.normal_button.setChecked(True)
        self.delete_button.hide()

    def delete_event(self):
        existing_events = CalendarEvent.get_by_date(self.selected_date.toPython())
        if existing_events:
            existing_events[0].delete()
            self.selected_date_label.setText(
                f"Selected Date: {self.selected_date.toString('MMMM d, yyyy')} - Event Deleted!"
            )
            self.calendar.load_events()
            self.events_changed.emit()
            self.event_description.clear()
            self.normal_button.setChecked(True)
            self.delete_button.hide()
        else:
            self.selected_date_label.setText(
                f"Selected Date: {self.selected_date.toString('MMMM d, yyyy')} - No event to delete"
            )

    def get_selected_priority(self):
        if self.important_button.isChecked():
            return 'important'
        if self.next_important_button.isChecked():
            return 'next_important'
        return 'normal'

    def on_event_saved(self, event):
        pass

    def on_event_deleted(self, event):
        pass

    def apply_theme(self):
        theme = get_setting('theme', 'light')
        self.setStyleSheet(_CALENDAR_WIDGET_DARK if theme == 'dark' else _CALENDAR_WIDGET_LIGHT)
        self.ensure_label_transparency()
        self.ensure_button_colors()

    def ensure_label_transparency(self):
        theme = get_setting('theme', 'light')
        blue = "#42a5f5" if theme == 'dark' else "#1877f2"

        if self.selected_date_label:
            self.selected_date_label.setStyleSheet(
                f"color: {blue}; background-color: transparent; border: none; font-weight: 600;"
            )

        for attr in ('desc_label', 'priority_label'):
            lbl = getattr(self, attr, None)
            if lbl:
                style = lbl.styleSheet()
                if "background-color: transparent" not in style:
                    lbl.setStyleSheet(style + "; background-color: transparent; border: none;")

    def ensure_button_colors(self):
        theme = get_setting('theme', 'light')
        save_bg = "#42a5f5" if theme == 'dark' else "#1877f2"

        if self.save_button:
            self.save_button.setStyleSheet(
                f"background-color: {save_bg}; color: #ffffff; border: none; "
                "border-radius: 8px; font-weight: 600; font-size: 13px;"
            )
        if self.delete_button:
            self.delete_button.setStyleSheet(
                "background-color: #f44336; color: #ffffff; border: none; "
                "border-radius: 8px; font-weight: 600; font-size: 13px;"
            )

    def refresh_theme(self):
        self.apply_theme()
        self.calendar.refresh_theme()
        self.ensure_label_transparency()
        self.ensure_button_colors()

        for child in self.findChildren(CustomCard):
            if hasattr(child, 'refresh_theme'):
                child.refresh_theme()

        from ui.common_widgets import ModernButton
        for child in self.findChildren(ModernButton):
            if hasattr(child, 'refresh_theme'):
                child.refresh_theme()

        for child in self.findChildren(UpcomingEventsCard):
            if hasattr(child, 'refresh_theme'):
                child.refresh_theme()

        self.update()
        self.calendar.update_calendar()