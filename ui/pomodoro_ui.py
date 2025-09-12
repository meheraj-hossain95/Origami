"""
Simple Pomodoro Timer UI - Three main sections as requested
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QLabel, QSpinBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from database.db import get_setting

class PomodoroWidget(QWidget):
    """Simple Pomodoro Timer Widget with three main sections"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Timer state
        self.is_running = False
        self.is_paused = False
        self.time_remaining = 0  # in seconds
        self.session_count = 0
        self.applied_duration = 25 * 60  # Default 25 minutes in seconds
        
        # UI Timer for regular updates
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_timer)
        
        self.setup_ui()
        self.reset_timer()
        self.apply_theme()
    
    def setup_ui(self):
        """Setup the simple timer UI with three sections"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Section 1: Digital Counter and Control Buttons
        self.setup_timer_section(layout)
        
        # Section 2: Timer Duration Customization
        self.setup_duration_section(layout)
        
        # Section 3: Session Counter
        self.setup_session_section(layout)
    
    def setup_timer_section(self, layout):
        """Section 1: Digital Counter with Hours, Minutes, Seconds and Control Buttons"""
        
        # Digital counter display
        self.timer_display = QLabel("00:00:00")
        self.timer_display.setFont(QFont("Courier New", 120, QFont.Bold))  # Increased from 80 to 120
        self.timer_display.setAlignment(Qt.AlignCenter)
        self.timer_display.setMinimumHeight(50)  # Increased height for larger text
        self.timer_display.setMaximumHeight(250)
        layout.addWidget(self.timer_display)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start")
        self.start_button.setFont(QFont("Arial", 16, QFont.Bold))
        self.start_button.setMinimumSize(150, 50)
        self.start_button.clicked.connect(self.start_timer)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.setFont(QFont("Arial", 16, QFont.Bold))
        self.pause_button.setMinimumSize(150, 50)
        self.pause_button.clicked.connect(self.pause_timer)
        self.pause_button.setEnabled(False)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.setFont(QFont("Arial", 16, QFont.Bold))
        self.reset_button.setMinimumSize(150, 50)
        self.reset_button.clicked.connect(self.reset_timer)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.reset_button)
        
        layout.addLayout(button_layout)
    
    def setup_duration_section(self, layout):
        """Section 2: Timer Duration Customization"""
        
        # Duration input fields container
        self.duration_container = QWidget()
        self.duration_container.setMaximumHeight(190)  # Increased to accommodate more padding
        self.duration_container.setMinimumHeight(180)  # Increased to accommodate more padding
        
        duration_main_layout = QVBoxLayout(self.duration_container)
        duration_main_layout.setContentsMargins(30, 25, 30, 25)  # Increased padding: left, top, right, bottom
        duration_main_layout.setSpacing(20)  # Increased spacing between elements
        
        # Duration input fields in horizontal layout: Hours: [field] Min: [field] Sec: [field]
        duration_layout = QHBoxLayout()
        duration_layout.setSpacing(5)
        
        duration_layout.addStretch()
        
        # Hours: label and input
        self.hours_label = QLabel("Hours:")
        self.hours_label.setFont(QFont("Arial", 14, QFont.Bold))
        duration_layout.addWidget(self.hours_label)
        
        self.hours_input = QLineEdit()
        self.hours_input.setText("0")
        self.hours_input.setPlaceholderText("0")
        self.hours_input.setFixedSize(100, 70)  # Increased from 60x40 to 80x50
        self.hours_input.setAlignment(Qt.AlignCenter)
        duration_layout.addWidget(self.hours_input)
        
        # Min: label and input
        self.minutes_label = QLabel("Min:")
        self.minutes_label.setFont(QFont("Arial", 14, QFont.Bold))
        duration_layout.addWidget(self.minutes_label)
        
        self.minutes_input = QLineEdit()
        self.minutes_input.setText("25")  # Default 25 minutes
        self.minutes_input.setPlaceholderText("0")
        self.minutes_input.setFixedSize(100, 70)  # Increased from 60x40 to 80x50
        self.minutes_input.setAlignment(Qt.AlignCenter)
        duration_layout.addWidget(self.minutes_input)
        
        # Sec: label and input
        self.seconds_label = QLabel("Sec:")
        self.seconds_label.setFont(QFont("Arial", 14, QFont.Bold))
        duration_layout.addWidget(self.seconds_label)
        
        self.seconds_input = QLineEdit()
        self.seconds_input.setText("0")
        self.seconds_input.setPlaceholderText("0")
        self.seconds_input.setFixedSize(100, 70) # Increased from 60x40 to 80x50
        self.seconds_input.setAlignment(Qt.AlignCenter)
        duration_layout.addWidget(self.seconds_input)
        
        duration_layout.addStretch()
        
        duration_main_layout.addLayout(duration_layout)
        
        # Apply button with increased height
        self.apply_button = QPushButton("Apply Duration")
        self.apply_button.setFont(QFont("Arial", 14, QFont.Bold))
        self.apply_button.setFixedSize(180, 70)  # Increased height from 60 to 70
        self.apply_button.clicked.connect(self.apply_duration)
        duration_main_layout.addWidget(self.apply_button, alignment=Qt.AlignCenter)
        
        layout.addWidget(self.duration_container)
    
    def setup_session_section(self, layout):
        """Section 3: Session Counter"""
        
        self.session_display = QLabel("Sessions Completed: 0")
        self.session_display.setFont(QFont("Arial", 18, QFont.Bold))
        self.session_display.setAlignment(Qt.AlignCenter)
        self.session_display.setMinimumHeight(60)
        self.session_display.setMaximumHeight(80)
        layout.addWidget(self.session_display)
    
    def apply_duration(self):
        """Apply the duration settings to the timer"""
        try:
            # Get values from input fields and validate them
            hours_text = self.hours_input.text().strip()
            minutes_text = self.minutes_input.text().strip()
            seconds_text = self.seconds_input.text().strip()
            
            # Default to 0 if empty
            hours = int(hours_text) if hours_text else 0
            minutes = int(minutes_text) if minutes_text else 0
            seconds = int(seconds_text) if seconds_text else 0
            
            # Validate ranges
            if hours < 0 or hours > 23:
                hours = max(0, min(23, hours))
                self.hours_input.setText(str(hours))
            
            if minutes < 0 or minutes > 59:
                minutes = max(0, min(59, minutes))
                self.minutes_input.setText(str(minutes))
                
            if seconds < 0 or seconds > 59:
                seconds = max(0, min(59, seconds))
                self.seconds_input.setText(str(seconds))
            
            # Calculate total duration in seconds
            self.applied_duration = hours * 3600 + minutes * 60 + seconds
            
            # Always update the display immediately when applying duration
            self.time_remaining = self.applied_duration
            self.update_timer_display()
            
        except ValueError:
            # If invalid input, reset to default values
            self.hours_input.setText("0")
            self.minutes_input.setText("25")
            self.seconds_input.setText("0")
            self.applied_duration = 25 * 60  # Default 25 minutes
            self.time_remaining = self.applied_duration
            self.update_timer_display()
    
    def apply_theme(self):
        """Apply the current app theme"""
        theme = get_setting('theme', 'light')
        
        if theme == 'dark':
            self.apply_dark_theme()
        else:
            self.apply_light_theme()
        
        # Ensure duration labels are always visible
        self._style_duration_labels()
    
    def _style_duration_labels(self):
        """Explicitly style duration labels to ensure visibility"""
        theme = get_setting('theme', 'light')
        text_color = '#212529' if theme == 'light' else '#ffffff'
        
        label_style = f"""
            QLabel {{
                color: {text_color} !important;
                background-color: transparent !important;
                border: none !important;
                font-weight: bold !important;
                font-size: 16px !important;
                padding: 5px !important;
                margin: 2px !important;
            }}
        """
        
        # Apply to duration labels if they exist with !important to override container styling
        if hasattr(self, 'hours_label'):
            self.hours_label.setStyleSheet(label_style)
        if hasattr(self, 'minutes_label'):
            self.minutes_label.setStyleSheet(label_style)
        if hasattr(self, 'seconds_label'):
            self.seconds_label.setStyleSheet(label_style)
    
    def apply_light_theme(self):
        """Apply comprehensive light theme styles"""
        # Define light theme colors
        colors = {
            'bg_primary': '#f8f9fa',
            'bg_secondary': '#ffffff',
            'text_primary': '#212529',
            'text_secondary': '#6c757d',
            'border': '#dee2e6',
            'border_focus': '#80bdff',
            'primary': '#007bff',
            'primary_hover': '#0056b3',
            'primary_pressed': '#004085',
            'success': '#28a745',
            'success_hover': '#218838',
            'success_pressed': '#1e7e34',
            'warning': '#ffc107',
            'warning_hover': '#e0a800',
            'warning_pressed': '#d39e00',
            'danger': '#dc3545',
            'danger_hover': '#c82333',
            'danger_pressed': '#bd2130'
        }
        
        # Main widget background
        self.setStyleSheet(f"""
            PomodoroWidget {{
                background-color: {colors['bg_primary']};
                color: {colors['text_primary']};
            }}
        """)
        
        # Timer display
        self.timer_display.setStyleSheet(f"""
            QLabel {{
                color: {colors['text_primary']};
                background-color: {colors['bg_secondary']};
                border: 2px solid {colors['border']};
                border-radius: 12px;
                padding: 30px;
                margin: 10px;
                font-size: 120px;
                font-weight: bold;
                font-family: 'Courier New', monospace;
            }}
        """)
        
        # Control buttons
        self.start_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['success']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors['success_hover']};
            }}
            QPushButton:pressed {{
                background-color: {colors['success_pressed']};
            }}
            QPushButton:disabled {{
                background-color: #6c757d;
                color: #adb5bd;
            }}
        """)
        
        self.pause_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['warning']};
                color: #212529;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors['warning_hover']};
            }}
            QPushButton:pressed {{
                background-color: {colors['warning_pressed']};
            }}
            QPushButton:disabled {{
                background-color: #6c757d;
                color: #adb5bd;
            }}
        """)
        
        self.reset_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['danger']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors['danger_hover']};
            }}
            QPushButton:pressed {{
                background-color: {colors['danger_pressed']};
            }}
        """)
        
        # Duration container
        self.duration_container.setStyleSheet(f"""
            QWidget {{
                background-color: {colors['bg_secondary']};
                border: 2px solid {colors['border']};
                border-radius: 12px;
                padding: 20px;
                margin: 10px;
            }}
            QLabel {{
                color: {colors['text_primary']};
                background-color: transparent;
                border: none;
                font-weight: bold;
            }}
        """)
        
        # Input fields
        input_style = f"""
            QLineEdit {{
                font-size: 20px;
                font-weight: bold;
                padding: 12px;
                border: 2px solid {colors['border']};
                border-radius: 8px;
                background-color: {colors['bg_secondary']};
                color: {colors['text_primary']};
            }}
            QLineEdit:focus {{
                border-color: {colors['border_focus']};
                outline: none;
            }}
            QLineEdit:hover {{
                border-color: {colors['primary']};
            }}
        """
        
        self.hours_input.setStyleSheet(input_style)
        self.minutes_input.setStyleSheet(input_style)
        self.seconds_input.setStyleSheet(input_style)
        
        # Apply button
        self.apply_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {colors['primary_pressed']};
            }}
        """)
        
        # Session display
        self.session_display.setStyleSheet(f"""
            QLabel {{
                color: {colors['text_primary']};
                background-color: {colors['bg_secondary']};
                border: 2px solid {colors['success']};
                border-radius: 12px;
                padding: 15px;
                margin: 10px;
                font-weight: bold;
            }}
        """)
    
    def apply_dark_theme(self):
        """Apply comprehensive dark theme styles"""
        # Define dark theme colors
        colors = {
            'bg_primary': '#1a1a1a',
            'bg_secondary': '#2d2d2d',
            'text_primary': '#ffffff',
            'text_secondary': '#b0b0b0',
            'border': '#404040',
            'border_focus': '#66b3ff',
            'primary': '#0d6efd',
            'primary_hover': '#0b5ed7',
            'primary_pressed': '#0a58ca',
            'success': '#198754',
            'success_hover': '#157347',
            'success_pressed': '#146c43',
            'warning': '#fd7e14',
            'warning_hover': '#e8711c',
            'warning_pressed': '#d1641a',
            'danger': '#dc3545',
            'danger_hover': '#bb2d3b',
            'danger_pressed': '#b02a37'
        }
        
        # Main widget background
        self.setStyleSheet(f"""
            PomodoroWidget {{
                background-color: {colors['bg_primary']};
                color: {colors['text_primary']};
            }}
        """)
        
        # Timer display
        self.timer_display.setStyleSheet(f"""
            QLabel {{
                color: {colors['text_primary']};
                background-color: {colors['bg_secondary']};
                border: 2px solid {colors['border']};
                border-radius: 12px;
                padding: 30px;
                margin: 10px;
                font-size: 120px;
                font-weight: bold;
                font-family: 'Courier New', monospace;
            }}
        """)
        
        # Control buttons
        self.start_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['success']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors['success_hover']};
            }}
            QPushButton:pressed {{
                background-color: {colors['success_pressed']};
            }}
            QPushButton:disabled {{
                background-color: #6c757d;
                color: #adb5bd;
            }}
        """)
        
        self.pause_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['warning']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors['warning_hover']};
            }}
            QPushButton:pressed {{
                background-color: {colors['warning_pressed']};
            }}
            QPushButton:disabled {{
                background-color: #6c757d;
                color: #adb5bd;
            }}
        """)
        
        self.reset_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['danger']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors['danger_hover']};
            }}
            QPushButton:pressed {{
                background-color: {colors['danger_pressed']};
            }}
        """)
        
        # Duration container
        self.duration_container.setStyleSheet(f"""
            QWidget {{
                background-color: {colors['bg_secondary']};
                border: 2px solid {colors['border']};
                border-radius: 12px;
                padding: 20px;
                margin: 10px;
            }}
            QLabel {{
                color: {colors['text_primary']};
                background-color: transparent;
                border: none;
                font-weight: bold;
            }}
        """)
        
        # Input fields
        input_style = f"""
            QLineEdit {{
                font-size: 20px;
                font-weight: bold;
                padding: 12px;
                border: 2px solid {colors['border']};
                border-radius: 8px;
                background-color: {colors['bg_secondary']};
                color: {colors['text_primary']};
            }}
            QLineEdit:focus {{
                border-color: {colors['border_focus']};
                outline: none;
            }}
            QLineEdit:hover {{
                border-color: {colors['primary']};
            }}
        """
        
        self.hours_input.setStyleSheet(input_style)
        self.minutes_input.setStyleSheet(input_style)
        self.seconds_input.setStyleSheet(input_style)
        
        # Apply button
        self.apply_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {colors['primary_pressed']};
            }}
        """)
        
        # Session display
        self.session_display.setStyleSheet(f"""
            QLabel {{
                color: {colors['text_primary']};
                background-color: {colors['bg_secondary']};
                border: 2px solid {colors['success']};
                border-radius: 12px;
                padding: 15px;
                margin: 10px;
                font-weight: bold;
            }}
        """)
    
    def refresh_theme(self):
        """Refresh theme when changed - called by main window"""
        self.apply_theme()
    
    def start_timer(self):
        """Start the timer"""
        if not self.is_running:
            # Set total time in seconds from applied duration
            if not self.is_paused:
                self.time_remaining = self.applied_duration
            
            if self.time_remaining <= 0:
                return
            
            self.is_running = True
            self.is_paused = False
            
            # Update button states
            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            
            # Start the timer
            self.ui_timer.start(1000)  # Update every second
    
    def pause_timer(self):
        """Pause the timer"""
        if self.is_running:
            self.is_running = False
            self.is_paused = True
            
            # Update button states
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            
            # Stop the timer
            self.ui_timer.stop()
    
    def reset_timer(self):
        """Reset the timer"""
        self.is_running = False
        self.is_paused = False
        
        # Reset time to applied duration
        self.time_remaining = self.applied_duration
        
        # Update button states
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        
        # Stop the timer and update display
        self.ui_timer.stop()
        self.update_timer_display()
    
    def update_timer(self):
        """Update the timer every second"""
        if self.is_running and self.time_remaining > 0:
            self.time_remaining -= 1
            self.update_timer_display()
            
            # Check if timer finished
            if self.time_remaining <= 0:
                self.timer_finished()
    
    def timer_finished(self):
        """Handle when timer reaches zero"""
        self.is_running = False
        self.is_paused = False
        
        # Increment session counter
        self.session_count += 1
        self.session_display.setText(f"Sessions Completed: {self.session_count}")
        
        # Update button states
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        
        # Stop timer
        self.ui_timer.stop()
        
        # Reset time for next session using applied duration
        self.time_remaining = self.applied_duration
        
        self.update_timer_display()
    
    def update_timer_display(self):
        """Update the timer display with current time"""
        hours = self.time_remaining // 3600
        minutes = (self.time_remaining % 3600) // 60
        seconds = self.time_remaining % 60
        
        time_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.timer_display.setText(time_text)