"""
Modern Calendar UI with event management and dashboard integration
"""
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

class ModernCalendarWidget(QWidget):
    """Modern calendar widget with custom design"""
    
    date_clicked = Signal(QDate)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_month = QDate.currentDate().month()
        self.current_year = QDate.currentDate().year()
        self.events = {}  # Store events by date string
        self.date_buttons = {}  # Store date button references
        self.setup_ui()
        self.load_events()
        
    def setup_ui(self):
        """Setup the modern calendar UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with month/year and navigation
        header_layout = QHBoxLayout()
        
        # Previous month button
        self.prev_button = QPushButton("◀")
        self.prev_button.setFixedSize(40, 40)
        self.prev_button.setObjectName("navButton")
        self.prev_button.clicked.connect(self.previous_month)
        header_layout.addWidget(self.prev_button)
        
        # Month and Year display
        self.month_year_label = QLabel()
        self.month_year_label.setAlignment(Qt.AlignCenter)
        self.month_year_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.month_year_label.setObjectName("monthYearLabel")
        header_layout.addWidget(self.month_year_label, 1)
        
        # Next month button
        self.next_button = QPushButton("▶")
        self.next_button.setFixedSize(40, 40)
        self.next_button.setObjectName("navButton")
        self.next_button.clicked.connect(self.next_month)
        header_layout.addWidget(self.next_button)
        
        layout.addLayout(header_layout)
        
        # Calendar grid
        self.calendar_grid = QGridLayout()
        self.calendar_grid.setSpacing(2)
        
        # Day headers - starting from Sunday
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for i, day in enumerate(days):
            day_label = QLabel(day)
            day_label.setAlignment(Qt.AlignCenter)
            day_label.setFont(QFont("Arial", 12, QFont.Bold))
            day_label.setObjectName("dayHeader")
            self.calendar_grid.addWidget(day_label, 0, i)
        
        # Date cells will be added dynamically
        layout.addLayout(self.calendar_grid)
        
        self.update_calendar()
        self.apply_theme()
    
    def apply_theme(self):
        """Apply theme-aware styling"""
        theme = get_setting('theme', 'light')
        
        if theme == 'dark':
            self.setStyleSheet("""
                ModernCalendarWidget {
                    background-color: #121212;
                    color: #e0e0e0;
                }
                QWidget {
                    background-color: #121212;
                    color: #e0e0e0;
                }
                QPushButton#navButton {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 2px solid #404040;
                    border-radius: 20px;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton#navButton:hover {
                    background-color: #404040;
                    border-color: #42a5f5;
                }
                QPushButton#navButton:pressed {
                    background-color: #1a1a1a;
                }
                QLabel#monthYearLabel {
                    color: #ffffff;
                }
                QLabel#dayHeader {
                    color: #a0a0a0;
                    padding: 10px;
                    background-color: #2d2d2d;
                    border-radius: 5px;
                    margin: 2px;
                }
                QPushButton#dateButton {
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                    border: 1px solid #303030;
                    border-radius: 8px;
                    padding: 8px;
                    min-height: 40px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton#dateButton:hover {
                    background-color: #2d2d2d;
                    border-color: #42a5f5;
                }
                QPushButton#dateButtonToday {
                    background-color: #42a5f5;
                    color: #ffffff;
                    border: 1px solid #1976d2;
                    border-radius: 8px;
                    padding: 8px;
                    min-height: 40px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton#dateButtonTodayWithEvent {
                    background-color: #8e24aa;
                    color: #ffffff;
                    border: 3px solid #6a1b9a;
                    border-radius: 8px;
                    padding: 8px;
                    min-height: 40px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton#dateButtonTodayWithEvent:hover {
                    background-color: #ab47bc;
                }
                QPushButton#dateButtonRed {
                    background-color: #ff4444;
                    color: #ffffff;
                    border: 1px solid #303030;
                    border-radius: 8px;
                    padding: 8px;
                    min-height: 40px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton#dateButtonRed:hover {
                    background-color: #ff6666;
                    border-color: #42a5f5;
                }
                QPushButton#dateButtonYellow {
                    background-color: #ffaa00;
                    color: #ffffff;
                    border: 1px solid #303030;
                    border-radius: 8px;
                    padding: 8px;
                    min-height: 40px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton#dateButtonYellow:hover {
                    background-color: #ffbb22;
                    border-color: #42a5f5;
                }
                QPushButton#dateButtonGreen {
                    background-color: #44aa44;
                    color: #ffffff;
                    border: 1px solid #303030;
                    border-radius: 8px;
                    padding: 8px;
                    min-height: 40px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton#dateButtonGreen:hover {
                    background-color: #66bb66;
                    border-color: #42a5f5;
                }
                QPushButton#dateButtonEmpty {
                    background-color: #1e1e1e;
                    color: transparent;
                    border: 1px solid #303030;
                    border-radius: 8px;
                    padding: 8px;
                    min-height: 40px;
                }
            """)
        else:
            self.setStyleSheet("""
                ModernCalendarWidget {
                    background-color: #f0f2f5;
                    color: #212121;
                }
                QWidget {
                    background-color: #f0f2f5;
                    color: #212121;
                }
                QPushButton#navButton {
                    background-color: #ffffff;
                    color: #333333;
                    border: 2px solid #e0e0e0;
                    border-radius: 20px;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton#navButton:hover {
                    background-color: #f0f2f5;
                    border-color: #1877f2;
                    color: #1877f2;
                }
                QPushButton#navButton:pressed {
                    background-color: #e0e0e0;
                }
                QLabel#monthYearLabel {
                    color: #212121;
                }
                QLabel#dayHeader {
                    color: #616161;
                    padding: 10px;
                    background-color: #f5f5f5;
                    border-radius: 5px;
                    margin: 2px;
                }
                QPushButton#dateButton {
                    background-color: #ffffff;
                    color: #212121;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 8px;
                    min-height: 40px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton#dateButton:hover {
                    background-color: #f0f2f5;
                    border-color: #1877f2;
                }
                QPushButton#dateButtonToday {
                    background-color: #1877f2;
                    color: #ffffff;
                    border: 1px solid #1565c0;
                    border-radius: 8px;
                    padding: 8px;
                    min-height: 40px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton#dateButtonTodayWithEvent {
                    background-color: #8e24aa;
                    color: #ffffff;
                    border: 3px solid #6a1b9a;
                    border-radius: 8px;
                    padding: 8px;
                    min-height: 40px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton#dateButtonTodayWithEvent:hover {
                    background-color: #ab47bc;
                }
                QPushButton#dateButtonRed {
                    background-color: #ff4444;
                    color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 8px;
                    min-height: 40px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton#dateButtonRed:hover {
                    background-color: #ff6666;
                    border-color: #1877f2;
                }
                QPushButton#dateButtonYellow {
                    background-color: #ffaa00;
                    color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 8px;
                    min-height: 40px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton#dateButtonYellow:hover {
                    background-color: #ffbb22;
                    border-color: #1877f2;
                }
                QPushButton#dateButtonGreen {
                    background-color: #44aa44;
                    color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 8px;
                    min-height: 40px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton#dateButtonGreen:hover {
                    background-color: #66bb66;
                    border-color: #1877f2;
                }
                QPushButton#dateButtonEmpty {
                    background-color: #ffffff;
                    color: transparent;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 8px;
                    min-height: 40px;
                }
            """)
    
    def update_calendar(self):
        """Update the calendar grid for current month"""
        # Clear existing date buttons
        for button in self.date_buttons.values():
            button.deleteLater()
        self.date_buttons.clear()
        
        # Update month/year label
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        self.month_year_label.setText(f"{month_names[self.current_month - 1]} {self.current_year}")
        
        # Get first day of month and number of days
        first_day = QDate(self.current_year, self.current_month, 1)
        days_in_month = first_day.daysInMonth()
        start_weekday = first_day.dayOfWeek()  # 1 = Monday, 7 = Sunday
        
        # Convert to Sunday-based (0 = Sunday, 1 = Monday, etc.)
        if start_weekday == 7:  # Sunday
            start_col = 0
        else:
            start_col = start_weekday  # Monday=1, Tuesday=2, etc.
        
        # Today for highlighting
        today = QDate.currentDate()
        
        # Create exactly 5 rows of 7 columns (35 cells total) - all cells always visible
        for row in range(1, 6):  # Rows 1-5 (row 0 is headers)
            for col in range(7):  # Columns 0-6 (Sun-Sat)
                cell_index = (row - 1) * 7 + col  # 0-34
                day_number = cell_index - start_col + 1
                
                # Always create a button for every cell
                if day_number > 0 and day_number <= days_in_month:
                    # Valid day - create button with date
                    date_button = QPushButton(str(day_number))
                    date_button.setCursor(QCursor(Qt.PointingHandCursor))
                    
                    # Store date info
                    button_date = QDate(self.current_year, self.current_month, day_number)
                    date_key = button_date.toString("yyyy-MM-dd")
                    
                    # Check if this date has events and apply styling
                    has_events = date_key in self.events and self.events[date_key]
                    is_today = button_date == today
                    
                    if has_events and is_today:
                        # Special styling for today's date when it has an event
                        date_button.setObjectName("dateButtonTodayWithEvent")
                    elif has_events:
                        # Get the first event's priority to determine color
                        event = self.events[date_key][0]
                        if event.priority == 'important':
                            date_button.setObjectName("dateButtonRed")
                        elif event.priority == 'next_important':
                            date_button.setObjectName("dateButtonYellow")
                        else:
                            date_button.setObjectName("dateButtonGreen")
                    elif is_today:
                        # Only show today styling if there's no event
                        date_button.setObjectName("dateButtonToday")
                    else:
                        date_button.setObjectName("dateButton")
                    
                    # Store the date in the button for later retrieval
                    date_button.date_info = button_date
                    
                    # Connect click event using partial to avoid closure issues
                    from functools import partial
                    date_button.clicked.connect(partial(self.emit_date_clicked, button_date))
                    
                    self.date_buttons[date_key] = date_button
                else:
                    # Empty cell - create disabled button that looks empty
                    date_button = QPushButton("")
                    date_button.setObjectName("dateButtonEmpty")
                    date_button.setEnabled(False)  # Make it non-clickable
                
                # Add button to grid (every cell gets a button)
                self.calendar_grid.addWidget(date_button, row, col)
        
        # Refresh style
        self.style().unpolish(self)
        self.style().polish(self)
    
    def emit_date_clicked(self, date):
        """Helper method to emit date clicked signal"""
        self.date_clicked.emit(date)
        
        # Store reference to any open modal for theme synchronization
        if hasattr(self, 'parent') and self.parent():
            calendar_widget = self.parent()
            # Find the main CalendarWidget parent
            while calendar_widget and not isinstance(calendar_widget, CalendarWidget):
                calendar_widget = calendar_widget.parent()
            if calendar_widget:
                calendar_widget._active_date = date
    
    def previous_month(self):
        """Navigate to previous month"""
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        
        self.update_calendar()
        self.load_events()
    
    def next_month(self):
        """Navigate to next month"""
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        
        self.update_calendar()
        self.load_events()
    
    def load_events(self):
        """Load events from database"""
        all_events = CalendarEvent.get_all()
        self.events.clear()
        
        for event in all_events:
            date_key = event.event_date.isoformat()
            if date_key not in self.events:
                self.events[date_key] = []
            self.events[date_key].append(event)
        
        # Update calendar to reflect events
        self.update_calendar()
    
    def refresh_theme(self):
        """Refresh theme when changed"""
        self.apply_theme()
        self.update_calendar()  # Force rebuild with new theme

class EventModal(QDialog):
    """Modal dialog for creating/editing events"""
    
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
    
    def refresh_theme(self):
        """Refresh theme when changed"""
        self.apply_theme()
    
    def setup_ui(self):
        """Setup the modal UI"""
        self.setWindowTitle("Event Details")
        self.setFixedSize(600, 450)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Add Event" if not self.event else "Edit Event")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Date display
        date_str = self.event_date.toString("MMMM d, yyyy")
        date_label = QLabel(f"Date: {date_str}")
        date_label.setFont(QFont("Arial", 12))
        date_label.setObjectName("dateLabel")
        layout.addWidget(date_label)
        
        # Event description
        desc_label = QLabel("Event Description:")
        desc_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(desc_label)
        
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Enter event details...")
        self.description_input.setMinimumHeight(100)
        self.description_input.setMaximumHeight(150)
        layout.addWidget(self.description_input)
        
        # Priority selection
        priority_label = QLabel("Priority:")
        priority_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(priority_label)
        
        priority_layout = QVBoxLayout()
        priority_layout.setSpacing(10)
        
        self.priority_group = QButtonGroup(self)
        
        # Important (Red)
        self.important_radio = QRadioButton("🔴 High")
        self.important_radio.setFont(QFont("Arial", 11))
        self.priority_group.addButton(self.important_radio, 1)
        priority_layout.addWidget(self.important_radio)
        
        # Next Important (Yellow)
        self.next_important_radio = QRadioButton("🟡 Medium")
        self.next_important_radio.setFont(QFont("Arial", 11))
        self.priority_group.addButton(self.next_important_radio, 2)
        priority_layout.addWidget(self.next_important_radio)
        
        # Normal (Green) - Default
        self.normal_radio = QRadioButton("🟢 Low")
        self.normal_radio.setFont(QFont("Arial", 11))
        self.normal_radio.setChecked(True)
        self.priority_group.addButton(self.normal_radio, 3)
        priority_layout.addWidget(self.normal_radio)
        
        layout.addLayout(priority_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        # Delete button (only for existing events)
        if self.event:
            self.delete_button = QPushButton("Delete")
            self.delete_button.setObjectName("deleteButton")
            self.delete_button.clicked.connect(self.delete_event)
            buttons_layout.addWidget(self.delete_button)
        
        buttons_layout.addStretch()
        
        # Cancel and Save buttons
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
        """Apply theme-aware styling"""
        theme = get_setting('theme', 'light')
        
        if theme == 'dark':
            self.setStyleSheet("""
                QDialog {
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                }
                QLabel {
                    color: #e0e0e0;
                }
                QLabel#dateLabel {
                    color: #42a5f5;
                    font-weight: 600;
                }
                QTextEdit {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 2px solid #404040;
                    border-radius: 8px;
                    padding: 10px;
                    font-size: 14px;
                }
                QTextEdit:focus {
                    border-color: #42a5f5;
                }
                QRadioButton {
                    color: #e0e0e0;
                    spacing: 10px;
                }
                QRadioButton::indicator {
                    width: 18px;
                    height: 18px;
                }
                QRadioButton::indicator:unchecked {
                    border: 2px solid #404040;
                    border-radius: 9px;
                    background-color: #2d2d2d;
                }
                QRadioButton::indicator:checked {
                    border: 2px solid #42a5f5;
                    border-radius: 9px;
                    background-color: #42a5f5;
                }
                QPushButton#saveButton {
                    background-color: #42a5f5;
                    color: #ffffff;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: 600;
                    min-width: 80px;
                }
                QPushButton#saveButton:hover {
                    background-color: #1976d2;
                }
                QPushButton#cancelButton {
                    background-color: #404040;
                    color: #e0e0e0;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: 600;
                    min-width: 80px;
                }
                QPushButton#cancelButton:hover {
                    background-color: #505050;
                }
                QPushButton#deleteButton {
                    background-color: #f44336;
                    color: #ffffff;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: 600;
                    min-width: 80px;
                }
                QPushButton#deleteButton:hover {
                    background-color: #d32f2f;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: #ffffff;
                    color: #212121;
                }
                QLabel {
                    color: #212121;
                }
                QLabel#dateLabel {
                    color: #1877f2;
                    font-weight: 600;
                }
                QTextEdit {
                    background-color: #ffffff;
                    color: #212121;
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 10px;
                    font-size: 14px;
                }
                QTextEdit:focus {
                    border-color: #1877f2;
                }
                QRadioButton {
                    color: #212121;
                    spacing: 10px;
                }
                QRadioButton::indicator {
                    width: 18px;
                    height: 18px;
                }
                QRadioButton::indicator:unchecked {
                    border: 2px solid #e0e0e0;
                    border-radius: 9px;
                    background-color: #ffffff;
                }
                QRadioButton::indicator:checked {
                    border: 2px solid #1877f2;
                    border-radius: 9px;
                    background-color: #1877f2;
                }
                QPushButton#saveButton {
                    background-color: #1877f2;
                    color: #ffffff;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: 600;
                    min-width: 80px;
                }
                QPushButton#saveButton:hover {
                    background-color: #1565c0;
                }
                QPushButton#cancelButton {
                    background-color: #e0e0e0;
                    color: #212121;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: 600;
                    min-width: 80px;
                }
                QPushButton#cancelButton:hover {
                    background-color: #d0d0d0;
                }
                QPushButton#deleteButton {
                    background-color: #f44336;
                    color: #ffffff;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: 600;
                    min-width: 80px;
                }
                QPushButton#deleteButton:hover {
                    background-color: #d32f2f;
                }
            """)
    
    def load_event_data(self):
        """Load existing event data into form"""
        if self.event:
            self.description_input.setText(self.event.description)
            
            # Set priority radio button
            if self.event.priority == 'important':
                self.important_radio.setChecked(True)
            elif self.event.priority == 'next_important':
                self.next_important_radio.setChecked(True)
            else:
                self.normal_radio.setChecked(True)
    
    def get_selected_priority(self):
        """Get selected priority"""
        if self.important_radio.isChecked():
            return 'important'
        elif self.next_important_radio.isChecked():
            return 'next_important'
        else:
            return 'normal'
    
    def save_event(self):
        """Save the event"""
        description = self.description_input.toPlainText().strip()
        if not description:
            QMessageBox.warning(self, "Warning", "Please enter an event description.")
            return
        
        priority = self.get_selected_priority()
        
        if self.event:
            # Update existing event
            self.event.update(description=description, priority=priority)
        else:
            # Create new event
            event_date_py = self.event_date.toPython()
            event_id = CalendarEvent.create(
                title=description[:50],  # Use first 50 chars as title
                description=description,
                event_date=event_date_py,
                priority=priority
            )
            
            # Create event object for signal
            self.event = CalendarEvent(
                id=event_id,
                title=description[:50],
                description=description,
                event_date=event_date_py,
                priority=priority
            )
        
        self.event_saved.emit(self.event)
        self.accept()
    
    def delete_event(self):
        """Delete the event"""
        if self.event:
            reply = QMessageBox.question(
                self, 
                "Confirm Delete", 
                "Are you sure you want to delete this event?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.event.delete()
                self.event_deleted.emit(self.event)
                self.accept()

class UpcomingEventsCard(CustomCard):
    """Card widget for displaying upcoming events on dashboard"""
    
    def __init__(self, parent=None):
        super().__init__("Upcoming Events", parent)
        self.setup_events_ui()
        self.load_events()
        
        # Auto-refresh events periodically
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.load_events)
        self.refresh_timer.start(300000)  # Refresh every 5 minutes
    
    def refresh_events_immediately(self):
        """Refresh events immediately - can be called externally"""
        self.load_events()
    
    def refresh_theme(self):
        """Refresh theme when changed"""
        super().refresh_theme()  # Call parent's refresh_theme method
        self.load_events()  # Reload to apply theme-aware styling
    
    def setup_events_ui(self):
        """Setup the upcoming events UI"""
        self.events_layout = QVBoxLayout()
        self.events_layout.setSpacing(8)  # Consistent spacing between events
        self.content_layout.addLayout(self.events_layout)
        
    def load_events(self):
        """Load upcoming events from database"""
        # Clear existing event widgets
        for i in reversed(range(self.events_layout.count())):
            child = self.events_layout.itemAt(i).widget()
            if child:
                child.deleteLater()
        
        # Get upcoming events
        upcoming_events = CalendarEvent.get_upcoming_events(limit=2)
        
        if not upcoming_events:
            no_events_label = QLabel("No upcoming events scheduled")
            no_events_label.setStyleSheet("""
                color: #888; 
                font-style: italic; 
                padding: 30px 20px; 
                font-size: 14px;
                text-align: center;
                background-color: transparent;
                font-weight: 500;
            """)
            no_events_label.setAlignment(Qt.AlignCenter)
            self.events_layout.addWidget(no_events_label)
        else:
            for event in upcoming_events:
                event_widget = self.create_event_widget(event)
                self.events_layout.addWidget(event_widget)
    
    def create_event_widget(self, event):
        """Create a widget for displaying an event"""
        event_frame = QFrame()
        event_frame.setObjectName("eventFrame")
        
        layout = QVBoxLayout(event_frame)
        layout.setContentsMargins(18, 14, 18, 14)  # More generous padding
        layout.setSpacing(8)  # Better spacing
        
        # Header with date and priority
        header_layout = QHBoxLayout()
        
        # Date display
        date_label = QLabel(event.get_formatted_date())
        date_label.setFont(QFont("Arial", 13, QFont.Bold))  # Slightly larger
        date_label.setObjectName("eventDate")
        date_label.setStyleSheet("background-color: transparent; border: none;")
        header_layout.addWidget(date_label)
        
        header_layout.addStretch()
        
        # Modern priority indicator
        priority_color = event.get_priority_color()
        priority_indicator = QFrame()
        priority_indicator.setFixedSize(12, 12)  # Slightly larger
        priority_indicator.setStyleSheet(f"""
            background-color: {priority_color};
            border-radius: 6px;
            border: none;
        """)
        priority_indicator.setToolTip(f"Priority: {event.get_priority_display()}")
        header_layout.addWidget(priority_indicator)
        
        layout.addLayout(header_layout)
        
        # Event description with marquee effect
        from ui.common_widgets import MarqueeLabel
        desc_label = MarqueeLabel(event.description)
        desc_label.setObjectName("eventDescription")
        desc_label.setFont(QFont("Arial", 12))  # Slightly larger
        desc_label.setStyleSheet("background-color: transparent; border: none;")
        layout.addWidget(desc_label)
        
        # Apply modern styling based on theme
        theme = get_setting('theme', 'light')
        if theme == 'dark':
            event_frame.setStyleSheet("""
                QFrame#eventFrame {
                    background-color: #262626;
                    border: 2px solid #505050;
                    border-radius: 12px;
                    margin: 4px 0px;
                }
                QLabel#eventDate {
                    color: #64b5f6;
                    font-weight: 700;
                    background-color: transparent;
                    border: none;
                    letter-spacing: -0.2px;
                }
                QLabel#eventDescription, MarqueeLabel#eventDescription {
                    color: #e8e8e8;
                    line-height: 1.5;
                    margin-top: 2px;
                    background-color: transparent;
                    border: none;
                    letter-spacing: 0.1px;
                }
            """)
        else:
            event_frame.setStyleSheet("""
                QFrame#eventFrame {
                    background-color: #f8f9fa;
                    border: 2px solid #c6cbd1;
                    border-radius: 12px;
                    margin: 4px 0px;
                }
                QLabel#eventDate {
                    color: #1565c0;
                    font-weight: 700;
                    background-color: transparent;
                    border: none;
                    letter-spacing: -0.2px;
                }
                QLabel#eventDescription, MarqueeLabel#eventDescription {
                    color: #495057;
                    line-height: 1.5;
                    margin-top: 2px;
                    background-color: transparent;
                    border: none;
                    letter-spacing: 0.1px;
                }
            """)
        
        return event_frame

class CalendarWidget(QWidget):
    """Main calendar widget with modern design"""
    
    # Signal to notify when events change
    events_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_date = QDate.currentDate()
        self.setup_ui()
        self.apply_theme()
    
    def setup_ui(self):
        """Setup the main calendar UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 20, 0, 20)  # Remove side margins completely for full width
        
        # Modern calendar widget with padding
        calendar_container = QWidget()
        calendar_layout = QVBoxLayout(calendar_container)
        calendar_layout.setContentsMargins(10, 0, 10, 0)  # Add padding only to calendar
        
        self.calendar = ModernCalendarWidget()
        self.calendar.date_clicked.connect(self.on_date_clicked)
        calendar_layout.addWidget(self.calendar)
        
        layout.addWidget(calendar_container)
        
        # Event creation section - match calendar width with same margins
        event_section_container = QWidget()
        event_section_layout = QVBoxLayout(event_section_container)
        event_section_layout.setContentsMargins(10, 0, 10, 0)  # Same margins as calendar
        
        self.setup_event_section()
        event_section = self.create_event_section()
        event_section_layout.addWidget(event_section)
        
        layout.addWidget(event_section_container)
        
        # Add stretch to push content up
        layout.addStretch()
    
    def setup_event_section(self):
        """Setup the event creation section variables"""
        self.event_description = None
        self.priority_dropdown = None
        self.selected_date_label = None
        self.desc_label = None
        self.priority_label = None
        self.save_button = None
        self.delete_button = None
    
    def create_event_section(self):
        """Create the event creation section below calendar"""
        # Create container widget with full width
        event_container = QWidget()
        event_layout = QVBoxLayout(event_container)
        event_layout.setContentsMargins(0, 0, 0, 0)  # Remove all margins for full width
        event_layout.setSpacing(15)
        
        # Create content frame with full width
        event_frame = QFrame()
        event_frame.setObjectName("eventSectionFrame")
        event_frame_layout = QVBoxLayout(event_frame)
        event_frame_layout.setContentsMargins(20, 20, 20, 20)  # Internal padding only
        event_frame_layout.setSpacing(15)
        
        # Title - centered
        title_label = QLabel("Add Event")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setObjectName("eventSectionTitle")
        title_label.setAlignment(Qt.AlignCenter)  # Center the title
        title_label.setStyleSheet("background-color: transparent; border: none;")
        event_frame_layout.addWidget(title_label)
        
        # Selected date display - full width
        self.selected_date_label = QLabel(f"Selected Date: {self.selected_date.toString('MMMM d, yyyy')}")
        self.selected_date_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.selected_date_label.setObjectName("selectedDateLabel")
        self.selected_date_label.setStyleSheet("color: #1877f2; background-color: transparent; border: none; font-weight: 600;")
        event_frame_layout.addWidget(self.selected_date_label)
        
        # Description input - full width with no constraints (removed description label)
        self.event_description = QTextEdit()
        self.event_description.setPlaceholderText("Enter event details...")
        self.event_description.setMinimumHeight(120)  # Increased height
        self.event_description.setMaximumHeight(200)  # Increased max height
        self.event_description.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Full width expansion
        event_frame_layout.addWidget(self.event_description)
        
        # Priority section - label and buttons on same line
        priority_section_layout = QHBoxLayout()
        priority_section_layout.setSpacing(15)
        
        # Priority label
        self.priority_label = QLabel("Priority:")
        self.priority_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.priority_label.setObjectName("priorityLabel")
        self.priority_label.setStyleSheet("background-color: transparent; border: none;")
        self.priority_label.setFixedWidth(60)  # Fixed width for alignment
        priority_section_layout.addWidget(self.priority_label)
        
        # Create button group for exclusive selection
        self.priority_button_group = QButtonGroup(self)
        
        # Important button
        self.important_button = QPushButton("🔴 High")
        self.important_button.setObjectName("priorityButton")
        self.important_button.setCheckable(True)
        self.important_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.important_button.setMinimumHeight(40)
        self.priority_button_group.addButton(self.important_button, 0)
        priority_section_layout.addWidget(self.important_button)
        
        # Next Important button
        self.next_important_button = QPushButton("🟡 Medium")
        self.next_important_button.setObjectName("priorityButton")
        self.next_important_button.setCheckable(True)
        self.next_important_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.next_important_button.setMinimumHeight(40)
        self.priority_button_group.addButton(self.next_important_button, 1)
        priority_section_layout.addWidget(self.next_important_button)
        
        # Normal button (default selected)
        self.normal_button = QPushButton("🟢 Low")
        self.normal_button.setObjectName("priorityButton")
        self.normal_button.setCheckable(True)
        self.normal_button.setChecked(True)  # Default selection
        self.normal_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.normal_button.setMinimumHeight(40)
        self.priority_button_group.addButton(self.normal_button, 2)
        priority_section_layout.addWidget(self.normal_button)
        
        event_frame_layout.addLayout(priority_section_layout)
        
        # Button section - full width
        button_section_layout = QHBoxLayout()
        button_section_layout.setSpacing(15)
        
        # Add stretch before buttons to center them when delete is hidden
        button_section_layout.addStretch()
        
        # Delete button (initially hidden) - fixed width
        self.delete_button = QPushButton("Delete Event")
        self.delete_button.setObjectName("deleteEventButton")
        self.delete_button.setMinimumHeight(45)
        self.delete_button.setFixedWidth(200)  # Fixed width instead of expanding
        self.delete_button.clicked.connect(self.delete_event)
        self.delete_button.hide()  # Initially hidden
        button_section_layout.addWidget(self.delete_button)
        
        # Save button - fixed width instead of expanding
        self.save_button = QPushButton("Save Event")
        self.save_button.setObjectName("saveEventButton")
        self.save_button.setMinimumHeight(45)
        self.save_button.setFixedWidth(200)  # Fixed width instead of expanding
        self.save_button.clicked.connect(self.save_event)
        button_section_layout.addWidget(self.save_button)
        
        # Add stretch after buttons to center them
        button_section_layout.addStretch()
        
        event_frame_layout.addLayout(button_section_layout)
        
        # Add frame to container
        event_layout.addWidget(event_frame)
        
        # Apply initial button colors
        self.ensure_button_colors()
        
        return event_container
    
    def on_date_clicked(self, date):
        """Handle date click to select date for event creation"""
        self.selected_date = date
        self.selected_date_label.setText(f"Selected Date: {date.toString('MMMM d, yyyy')}")
        
        # Ensure transparency is maintained after text update
        self.ensure_label_transparency()
        
        # Load existing event for this date if any
        existing_events = CalendarEvent.get_by_date(date.toPython())
        if existing_events:
            event = existing_events[0]
            self.event_description.setText(event.description)
            
            # Set priority buttons
            if event.priority == 'important':
                self.important_button.setChecked(True)
            elif event.priority == 'next_important':
                self.next_important_button.setChecked(True)
            else:
                self.normal_button.setChecked(True)
            
            # Show delete button for existing events
            self.delete_button.show()
        else:
            # Clear form for new event
            self.event_description.clear()
            self.normal_button.setChecked(True)  # Default to Normal
            
            # Hide delete button for new events
            self.delete_button.hide()
        
        # Refresh theme for form elements
        self.apply_theme()
    
    def save_event(self):
        """Save the event for the selected date"""
        description = self.event_description.toPlainText().strip()
        if not description:
            # Show a simple status message instead of popup
            self.selected_date_label.setText(f"Selected Date: {self.selected_date.toString('MMMM d, yyyy')} - Please enter description")
            return
        
        priority_data = self.get_selected_priority()
        
        # Check if event already exists for this date
        existing_events = CalendarEvent.get_by_date(self.selected_date.toPython())
        
        if existing_events:
            # Update existing event
            event = existing_events[0]
            event.update(description=description, priority=priority_data)
            self.selected_date_label.setText(f"Selected Date: {self.selected_date.toString('MMMM d, yyyy')} - Event Updated!")
        else:
            # Create new event
            CalendarEvent.create(
                title=description[:50],
                description=description,
                event_date=self.selected_date.toPython(),
                priority=priority_data
            )
            self.selected_date_label.setText(f"Selected Date: {self.selected_date.toString('MMMM d, yyyy')} - Event Saved!")
        
        # Refresh calendar to show color coding
        self.calendar.load_events()
        
        # Emit signal to refresh dashboard
        self.events_changed.emit()
        
        # Clear form
        self.event_description.clear()
        self.normal_button.setChecked(True)  # Reset to Normal
        
        # Hide delete button if it was visible
        if hasattr(self, 'delete_button'):
            self.delete_button.hide()
    
    def delete_event(self):
        """Delete the event for the selected date"""
        existing_events = CalendarEvent.get_by_date(self.selected_date.toPython())
        
        if existing_events:
            event = existing_events[0]
            event.delete()
            self.selected_date_label.setText(f"Selected Date: {self.selected_date.toString('MMMM d, yyyy')} - Event Deleted!")
            
            # Refresh calendar to remove color coding
            self.calendar.load_events()
            
            # Emit signal to refresh dashboard
            self.events_changed.emit()
            
            # Clear form and hide delete button
            self.event_description.clear()
            self.normal_button.setChecked(True)  # Reset to Normal
            self.delete_button.hide()
        else:
            self.selected_date_label.setText(f"Selected Date: {self.selected_date.toString('MMMM d, yyyy')} - No event to delete")
    
    def get_selected_priority(self):
        """Get selected priority from buttons"""
        if self.important_button.isChecked():
            return 'important'
        elif self.next_important_button.isChecked():
            return 'next_important'
        else:
            return 'normal'
    
    def on_event_saved(self, event):
        """Handle event save - kept for compatibility but not used"""
        pass
    
    def on_event_deleted(self, event):
        """Handle event deletion - kept for compatibility but not used"""
        pass
    
    def apply_theme(self):
        """Apply theme-aware styling"""
        theme = get_setting('theme', 'light')
        
        if theme == 'dark':
            self.setStyleSheet("""
                QWidget {
                    background-color: #121212;
                    color: #e0e0e0;
                }
                QFrame {
                    background-color: #121212;
                    color: #e0e0e0;
                }
                QFrame#eventSectionFrame {
                    background-color: #1e1e1e;
                    border: 2px solid #404040;
                    border-radius: 12px;
                    margin: 0px;
                }
                QLabel#eventSectionTitle {
                    color: #ffffff;
                    background-color: transparent;
                    border: none;
                }
                QScrollArea {
                    background-color: #121212;
                    border: none;
                }
                QScrollArea > QWidget > QWidget {
                    background-color: #121212;
                }
                QLabel#headerLabel {
                    color: #ffffff;
                    margin-bottom: 10px;
                }
                QLabel#selectedDateLabel {
                    color: #42a5f5;
                    font-weight: 600;
                    background-color: transparent;
                    border: none;
                }
                QLabel#eventDescriptionLabel {
                    color: #e0e0e0;
                    font-weight: 600;
                    background-color: transparent;
                    border: none;
                }
                QLabel#priorityLabel {
                    color: #e0e0e0;
                    font-weight: 600;
                    background-color: transparent;
                    border: none;
                }
                QLabel {
                    color: #e0e0e0;
                    background-color: transparent;
                }
                QTextEdit {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 2px solid #404040;
                    border-radius: 8px;
                    padding: 10px;
                    font-size: 14px;
                }
                QTextEdit:focus {
                    border-color: #42a5f5;
                }
                QPushButton#priorityButton {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 2px solid #404040;
                    border-radius: 8px;
                    padding: 10px;
                    font-size: 13px;
                    font-weight: 600;
                    min-height: 20px;
                }
                QPushButton#priorityButton:hover {
                    border-color: #42a5f5;
                    background-color: #404040;
                }
                QPushButton#priorityButton:checked {
                    background-color: #42a5f5;
                    border-color: #1976d2;
                    color: #ffffff;
                }
                QPushButton#priorityButton:pressed {
                    background-color: #1976d2;
                }
                QComboBox {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 2px solid #404040;
                    border-radius: 6px;
                    padding: 10px;
                    font-size: 14px;
                    min-height: 25px;
                }
                QComboBox:hover {
                    border-color: #42a5f5;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 30px;
                    background-color: #2d2d2d;
                    border-top-right-radius: 6px;
                    border-bottom-right-radius: 6px;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 5px solid #e0e0e0;
                    margin-right: 10px;
                }
                QComboBox QAbstractItemView {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #404040;
                    selection-background-color: #42a5f5;
                    selection-color: #ffffff;
                    border-radius: 4px;
                    padding: 6px;
                    min-height: 25px;
                }
                QPushButton#saveEventButton {
                    background-color: #42a5f5;
                    color: #ffffff;
                    border: none;
                    border-radius: 8px;
                    padding: 15px 24px;
                    font-weight: 600;
                    font-size: 16px;
                    min-height: 25px;
                }
                QPushButton#saveEventButton:hover {
                    background-color: #1976d2;
                }
                QPushButton#saveEventButton:pressed {
                    background-color: #1565c0;
                }
                QPushButton#deleteEventButton {
                    background-color: #f44336;
                    color: #ffffff;
                    border: none;
                    border-radius: 8px;
                    padding: 15px 24px;
                    font-weight: 600;
                    font-size: 16px;
                    min-height: 25px;
                }
                QPushButton#deleteEventButton:hover {
                    background-color: #d32f2f;
                }
                QPushButton#deleteEventButton:pressed {
                    background-color: #b71c1c;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: #f0f2f5;
                    color: #212121;
                }
                QFrame {
                    background-color: #f0f2f5;
                    color: #212121;
                }
                QFrame#eventSectionFrame {
                    background-color: #ffffff;
                    border: 2px solid #e0e0e0;
                    border-radius: 12px;
                    margin: 0px;
                }
                QLabel#eventSectionTitle {
                    color: #212121;
                    background-color: transparent;
                    border: none;
                }
                QScrollArea {
                    background-color: #f0f2f5;
                    border: none;
                }
                QScrollArea > QWidget > QWidget {
                    background-color: #f0f2f5;
                }
                QLabel#headerLabel {
                    color: #212121;
                    margin-bottom: 10px;
                }
                QLabel#selectedDateLabel {
                    color: #1877f2;
                    font-weight: 600;
                    background-color: transparent;
                    border: none;
                }
                QLabel#eventDescriptionLabel {
                    color: #212121;
                    font-weight: 600;
                    background-color: transparent;
                    border: none;
                }
                QLabel#priorityLabel {
                    color: #212121;
                    font-weight: 600;
                    background-color: transparent;
                    border: none;
                }
                QLabel {
                    color: #212121;
                    background-color: transparent;
                }
                QTextEdit {
                    background-color: #ffffff;
                    color: #212121;
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 10px;
                    font-size: 14px;
                }
                QTextEdit:focus {
                    border-color: #1877f2;
                }
                QPushButton#priorityButton {
                    background-color: #ffffff;
                    color: #212121;
                    border: 2px solid #d0d0d0;
                    border-radius: 8px;
                    padding: 10px;
                    font-size: 13px;
                    font-weight: 600;
                    min-height: 20px;
                }
                QPushButton#priorityButton:hover {
                    border-color: #1877f2;
                    background-color: #f0f2f5;
                }
                QPushButton#priorityButton:checked {
                    background-color: #1877f2;
                    border-color: #1565c0;
                    color: #ffffff;
                }
                QPushButton#priorityButton:pressed {
                    background-color: #1565c0;
                }
                QComboBox {
                    background-color: #ffffff;
                    color: #212121;
                    border: 2px solid #d0d0d0;
                    border-radius: 6px;
                    padding: 10px;
                    font-size: 14px;
                    min-height: 25px;
                }
                QComboBox:hover {
                    border-color: #1877f2;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 30px;
                    background-color: #ffffff;
                    border-top-right-radius: 6px;
                    border-bottom-right-radius: 6px;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 5px solid #555555;
                    margin-right: 10px;
                }
                QComboBox QAbstractItemView {
                    background-color: #ffffff;
                    color: #212121;
                    border: 1px solid #d0d0d0;
                    selection-background-color: #1877f2;
                    selection-color: #ffffff;
                    border-radius: 4px;
                    padding: 6px;
                    min-height: 25px;
                }
                QPushButton#saveEventButton {
                    background-color: #1877f2;
                    color: #ffffff;
                    border: none;
                    border-radius: 8px;
                    padding: 15px 24px;
                    font-weight: 600;
                    font-size: 16px;
                    min-height: 25px;
                }
                QPushButton#saveEventButton:hover {
                    background-color: #1565c0;
                }
                QPushButton#saveEventButton:pressed {
                    background-color: #0d47a1;
                }
                QPushButton#deleteEventButton {
                    background-color: #f44336;
                    color: #ffffff;
                    border: none;
                    border-radius: 8px;
                    padding: 15px 24px;
                    font-weight: 600;
                    font-size: 16px;
                    min-height: 25px;
                }
                QPushButton#deleteEventButton:hover {
                    background-color: #d32f2f;
                }
                QPushButton#deleteEventButton:pressed {
                    background-color: #b71c1c;
                }
            """)
        
        # Explicitly ensure label transparency
        self.ensure_label_transparency()
        
        # Explicitly ensure button colors
        self.ensure_button_colors()
    
    def ensure_label_transparency(self):
        """Ensure all event labels have transparent backgrounds and borders"""
        # Get current theme to apply appropriate blue color for selected date
        theme = get_setting('theme', 'light')
        blue_color = "#42a5f5" if theme == 'dark' else "#1877f2"
        
        if hasattr(self, 'selected_date_label') and self.selected_date_label:
            # Keep blue color for selected date label
            selected_date_style = f"color: {blue_color}; background-color: transparent; border: none; font-weight: 600;"
            self.selected_date_label.setStyleSheet(selected_date_style)
        
        if hasattr(self, 'desc_label') and self.desc_label:
            current_style = self.desc_label.styleSheet()
            transparent_style = "background-color: transparent; border: none;"
            if "background-color: transparent" not in current_style:
                self.desc_label.setStyleSheet(current_style + "; " + transparent_style)
        
        if hasattr(self, 'priority_label') and self.priority_label:
            current_style = self.priority_label.styleSheet()
            transparent_style = "background-color: transparent; border: none;"
            if "background-color: transparent" not in current_style:
                self.priority_label.setStyleSheet(current_style + "; " + transparent_style)
    
    def ensure_button_colors(self):
        """Ensure Save and Delete buttons have proper colors"""
        theme = get_setting('theme', 'light')
        
        if hasattr(self, 'save_button') and self.save_button:
            if theme == 'dark':
                save_style = """
                    background-color: #42a5f5;
                    color: #ffffff;
                    border: none;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 13px;
                """
            else:
                save_style = """
                    background-color: #1877f2;
                    color: #ffffff;
                    border: none;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 13px;
                """
            self.save_button.setStyleSheet(save_style)
        
        if hasattr(self, 'delete_button') and self.delete_button:
            delete_style = """
                background-color: #f44336;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            """
            self.delete_button.setStyleSheet(delete_style)
    
    def refresh_theme(self):
        """Refresh theme when changed"""
        self.apply_theme()
        self.calendar.refresh_theme()
        
        # Ensure labels remain transparent after theme change
        self.ensure_label_transparency()
        
        # Ensure buttons have proper colors after theme change
        self.ensure_button_colors()
        
        # Refresh theme for all custom cards and components
        for child in self.findChildren(CustomCard):
            if hasattr(child, 'refresh_theme'):
                child.refresh_theme()
        
        # Refresh theme for any ModernButton instances
        from ui.common_widgets import ModernButton
        for child in self.findChildren(ModernButton):
            if hasattr(child, 'refresh_theme'):
                child.refresh_theme()
        
        # Refresh theme for any UpcomingEventsCard instances
        for child in self.findChildren(UpcomingEventsCard):
            if hasattr(child, 'refresh_theme'):
                child.refresh_theme()
                
        # Force update of all child widgets
        self.update()
        self.calendar.update_calendar()