"""Clean Modern Profile UI with Simplified Password Management"""

import re, time, hashlib, os
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPainter, QColor, QPainterPath, QPixmap, QImage
from database.db import get_setting, set_setting
from utils.encryption import EncryptionManager
from datetime import datetime


class PasswordManager:
    def __init__(self):
        self.encryption_manager = EncryptionManager()
        self.failed_attempts = 0
        self.last_attempt_time = 0
        self.lockout_duration = 60

    def hash_password(self, password: str) -> str: 
        return hashlib.sha256(password.encode()).hexdigest()

    def set_password(self, password: str) -> bool:
        try:
            set_setting('journal_password_hash', self.hash_password(password))
            set_setting('journal_password_enabled', 'true')
            self.reset_failed_attempts()
            return True
        except: 
            return False

    def verify_password(self, password: str) -> bool:
        if self.is_locked(): 
            return False
        stored_hash = get_setting('journal_password_hash', '')
        if not stored_hash: 
            return True
        
        is_correct = self.hash_password(password) == stored_hash
        if not is_correct:
            self.failed_attempts += 1
            self.last_attempt_time = time.time()
            if self.failed_attempts >= 5: 
                set_setting('journal_lockout_time', str(self.last_attempt_time))
        else: 
            self.reset_failed_attempts()
        return is_correct

    def change_password(self, current_password: str, new_password: str) -> bool:
        if not self.verify_password(current_password): 
            return False
        return self.set_password(new_password)

    def remove_password(self, current_password: str) -> bool:
        if not self.verify_password(current_password): 
            return False
        set_setting('journal_password_hash', '')
        set_setting('journal_password_enabled', 'false')
        self.reset_failed_attempts()
        return True

    def has_password(self) -> bool: 
        return bool(get_setting('journal_password_hash', '')) and get_setting('journal_password_enabled', 'false') == 'true'

    def is_locked(self) -> bool:
        if self.failed_attempts < 5: 
            return False
        lockout_time = float(get_setting('journal_lockout_time', '0'))
        if time.time() - lockout_time >= self.lockout_duration:
            self.reset_failed_attempts()
            return False
        return True

    def get_lockout_remaining(self) -> int:
        if not self.is_locked(): 
            return 0
        return max(0, int(self.lockout_duration - (time.time() - float(get_setting('journal_lockout_time', '0')))))

    def reset_failed_attempts(self):
        self.failed_attempts = 0
        set_setting('journal_lockout_time', '0')


class PasswordStrengthCalculator:
    @staticmethod
    def calculate_strength(password: str) -> tuple:
        """Calculate password strength and return (score, label, color, feedback)"""
        if not password:
            return 0, "", "#666666", []
        
        score = 0
        feedback = []
        
        # Length scoring
        if len(password) >= 8:
            score += 2
        elif len(password) >= 6:
            score += 1
        else:
            feedback.append("Use at least 6 characters")
        
        # Character variety scoring
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("Add lowercase letters")
            
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("Add uppercase letters")
            
        if re.search(r'\d', password):
            score += 1
        else:
            feedback.append("Add numbers")
            
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        else:
            feedback.append("Add special characters")
        
        # Determine strength label and color
        if score <= 2:
            return score, "Weak", "#ff4757", feedback
        elif score <= 4:
            return score, "Fair", "#ffa726", feedback
        elif score <= 5:
            return score, "Good", "#66bb6a", feedback
        else:
            return score, "Strong", "#42c767", feedback


class PasswordStrengthWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Strength label
        self.strength_label = QLabel()
        self.strength_label.setObjectName("strengthLabel")
        layout.addWidget(self.strength_label)
        
        # Strength meter (5 bars)
        meter_container = QHBoxLayout()
        meter_container.setSpacing(4)
        
        self.strength_bars = []
        for i in range(5):
            bar = QFrame()
            bar.setFixedSize(24, 6)
            bar.setObjectName(f"strengthBar")
            self.strength_bars.append(bar)
            meter_container.addWidget(bar)
        
        meter_container.addStretch()
        layout.addLayout(meter_container)
        
        self.hide()  # Initially hidden
        
    def update_strength(self, password: str):
        score, label, color, feedback = PasswordStrengthCalculator.calculate_strength(password)
        
        if not password:
            self.hide()
            return
            
        # Update label
        self.strength_label.setText(f"Password strength: {label}")
        self.strength_label.setStyleSheet(f"color: {color}; font-weight: 500; font-size: 12px;")
        
        # Update bars
        theme = get_setting('theme', 'light')
        empty_color = "#3a3b3c" if theme == 'dark' else "#e4e6ea"
        
        for i, bar in enumerate(self.strength_bars):
            if i < score:
                bar.setStyleSheet(f"QFrame {{background-color: {color}; border-radius: 3px;}}")
            else:
                bar.setStyleSheet(f"QFrame {{background-color: {empty_color}; border-radius: 3px;}}")
        
        self.show()


class ModernInput(QLineEdit):
    def __init__(self, placeholder="", validation_func=None, max_length=None):
        super().__init__()
        self.validation_func = validation_func
        self.is_valid_input = True
        self.setPlaceholderText(placeholder)
        if max_length: self.setMaxLength(max_length)
        self.textChanged.connect(self.validate_input)

    def validate_input(self):
        if self.validation_func:
            self.is_valid_input = self.validation_func(self.text())
            self.update_validation_style()

    def update_validation_style(self):
        theme = get_setting('theme', 'light')
        base_style = self.get_base_style(theme)
        if not self.is_valid_input and self.text():
            error_bg = "#2c1810" if theme == 'dark' else "#fff5f5"
            self.setStyleSheet(base_style + f"border: 2px solid #ff4757; background-color: {error_bg};")
        else: self.setStyleSheet(base_style)

    def get_base_style(self, theme):
        if theme == 'dark':
            return """QLineEdit {background-color: #3a3b3c; border: 2px solid #606770; border-radius: 8px; padding: 12px 16px; 
                     font-size: 14px; color: #e4e6ea; font-weight: 500;} QLineEdit:focus {border: 2px solid #2d88ff; background-color: #242526;}"""
        return """QLineEdit {background-color: #ffffff; border: 2px solid #e4e6ea; border-radius: 8px; padding: 12px 16px; 
                 font-size: 14px; color: #1c1e21; font-weight: 500;} QLineEdit:focus {border: 2px solid #1877f2;}"""


class ModernButton(QPushButton):
    def __init__(self, text, button_type="primary"):
        super().__init__(text)
        self.button_type = button_type
        self.setMinimumHeight(45)
        self.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        self.setCursor(Qt.PointingHandCursor)
        self.update_style()

    def update_style(self):
        theme = get_setting('theme', 'light')
        styles = {
            'primary': {
                'dark': "QPushButton {background-color: #2d88ff; color: white; border: none; border-radius: 8px; padding: 12px 24px; font-weight: 600;} QPushButton:hover {background-color: #4c9aff;} QPushButton:disabled {background-color: #3a3b3c; color: #606770;}",
                'light': "QPushButton {background-color: #1877f2; color: white; border: none; border-radius: 8px; padding: 12px 24px; font-weight: 600;} QPushButton:hover {background-color: #166fe5;} QPushButton:disabled {background-color: #e4e6ea; color: #8a8d91;}"
            },
            'secondary': {
                'dark': "QPushButton {background-color: transparent; color: #e4e6ea; border: 2px solid #606770; border-radius: 8px; padding: 12px 24px; font-weight: 600;} QPushButton:hover {background-color: #3a3b3c;}",
                'light': "QPushButton {background-color: transparent; color: #1c1e21; border: 2px solid #dddfe2; border-radius: 8px; padding: 12px 24px; font-weight: 600;} QPushButton:hover {background-color: #f0f2f5;}"
            },
            'danger': {
                'dark': "QPushButton {background-color: #ff4757; color: white; border: none; border-radius: 8px; padding: 12px 24px; font-weight: 600;} QPushButton:hover {background-color: #ff6b7a;}",
                'light': "QPushButton {background-color: #ff4757; color: white; border: none; border-radius: 8px; padding: 12px 24px; font-weight: 600;} QPushButton:hover {background-color: #ff6b7a;}"
            }
        }
        self.setStyleSheet(styles[self.button_type][theme])


class CircularAvatar(QLabel):
    def __init__(self, size=80):
        super().__init__()
        self.avatar_size = size
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        
        # Load the user.png image
        self.load_user_image()

    def load_user_image(self):
        """Load the user.png image as the profile avatar with transparent background"""
        try:
            # Get the absolute path to the user.png file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            image_path = os.path.join(project_root, "assets", "icons", "user.png")
            
            if os.path.exists(image_path):
                original_pixmap = QPixmap(image_path)
                if not original_pixmap.isNull():
                    # Scale the original pixmap to fit
                    scaled_pixmap = original_pixmap.scaled(
                        self.avatar_size, self.avatar_size, 
                        Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    
                    # Create a new pixmap with transparent background
                    transparent_pixmap = QPixmap(self.avatar_size, self.avatar_size)
                    transparent_pixmap.fill(Qt.transparent)
                    
                    # Create a mask from the scaled pixmap to remove white background
                    # Convert white pixels to transparent
                    image = scaled_pixmap.toImage()
                    for x in range(image.width()):
                        for y in range(image.height()):
                            pixel = image.pixel(x, y)
                            color = QColor(pixel)
                            # If pixel is white or very light (close to white), make it transparent
                            if color.red() > 240 and color.green() > 240 and color.blue() > 240:
                                image.setPixel(x, y, 0)  # Set to transparent
                    
                    # Convert back to pixmap
                    processed_pixmap = QPixmap.fromImage(image)
                    
                    # Paint the processed image onto the transparent background
                    painter = QPainter(transparent_pixmap)
                    painter.setRenderHint(QPainter.Antialiasing)
                    
                    # Center the image
                    x = (self.avatar_size - processed_pixmap.width()) // 2
                    y = (self.avatar_size - processed_pixmap.height()) // 2
                    
                    painter.drawPixmap(x, y, processed_pixmap)
                    painter.end()
                    
                    self.setPixmap(transparent_pixmap)
                    return
        except Exception as e:
            print(f"Error loading user image: {e}")
        
        # Fallback: don't set any pixmap, will use emoji in paintEvent

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, self.width(), self.height())
        painter.setClipPath(path)
        
        theme = get_setting('theme', 'light')
        text_color = QColor('#e4e6ea' if theme == 'dark' else '#1c1e21')
        
        if self.pixmap(): 
            painter.drawPixmap(self.rect(), self.pixmap())
        else:
            painter.setPen(text_color)
            font = painter.font()
            font.setPointSize(int(self.avatar_size * 0.4))
            font.setWeight(QFont.Weight.Medium)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, "👤")


class SuccessToast(QFrame):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        
        self.icon_label = QLabel("✓")
        self.icon_label.setStyleSheet("color: #42c767; font-size: 16px; font-weight: bold;")
        self.message_label = QLabel(message)
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.message_label)
        layout.addStretch()
        
        # Apply theme on creation
        self.update_theme()
        
    def update_theme(self):
        """Update toast appearance based on current theme"""
        theme = get_setting('theme', 'light')
        if theme == 'dark':
            self.setStyleSheet("QFrame {background-color: #2d4a2b; border: 1px solid #42c767; border-radius: 8px;}")
            self.message_label.setStyleSheet("color: #e4e6ea; font-size: 14px; font-weight: 500;")
        else:
            self.setStyleSheet("QFrame {background-color: #e8f5e8; border: 1px solid #42c767; border-radius: 8px;}")
            self.message_label.setStyleSheet("color: #1c1e21; font-size: 14px; font-weight: 500;")


class ProfileWidget(QWidget):
    profile_updated = Signal(str)
    password_removed = Signal()
    theme_changed = Signal(str)  # New signal for theme changes

    def __init__(self):
        super().__init__()
        self.password_manager = PasswordManager()
        self.success_toast = None
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        self.create_header(layout)
        # Content
        self.create_content(layout)
        
        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def create_header(self, parent_layout):
        # Modern transparent header that adapts to theme
        header = QFrame()
        header.setObjectName("profileHeader")
        header.setFixedHeight(180)

        layout = QVBoxLayout(header)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(0)

        # Avatar + User Info container
        info_container = QHBoxLayout()
        info_container.setSpacing(20)

        # Floating Avatar
        self.avatar = CircularAvatar(90)
        self.avatar.setObjectName("profileAvatar")
        info_container.addWidget(self.avatar)

        # User Info
        user_info = QVBoxLayout()
        user_info.setSpacing(4)

        self.display_name = QLabel()
        self.display_name.setObjectName("profileDisplayName")

        self.display_handle = QLabel()
        self.display_handle.setObjectName("profileDisplayHandle")

        self.display_email = QLabel()
        self.display_email.setObjectName("profileDisplayEmail")

        user_info.addWidget(self.display_name)
        user_info.addWidget(self.display_handle)
        user_info.addWidget(self.display_email)
        user_info.addStretch()

        info_container.addLayout(user_info)
        info_container.addStretch()

        layout.addStretch()
        layout.addLayout(info_container)
        layout.addStretch()

        parent_layout.addWidget(header)


    def create_content(self, parent_layout):
        content = QFrame()
        content.setObjectName("profileContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(24)
        
        # Personal Info Card
        self.create_card(layout, "Personal Information", self.create_personal_form)
        # Personalization Card
        self.create_card(layout, "Personalization", self.create_personalization_form)
        # Security Card
        self.create_card(layout, "Journal Security", self.create_security_form)
        # Buttons
        self.create_action_buttons(layout)
        
        parent_layout.addWidget(content)

    def create_card(self, parent_layout, title, form_creator):
        card = QFrame()
        card.setObjectName("profileCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        
        title_layout = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("profileCardTitle")
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        card_layout.addLayout(title_layout)
        form_creator(card_layout)
        parent_layout.addWidget(card)

    def create_personal_form(self, layout):
        form = QVBoxLayout()
        
        # Username
        form.addWidget(QLabel("Username"))
        self.username_input = ModernInput("Enter your username", max_length=30)
        form.addWidget(self.username_input)
        
        # Handle
        form.addWidget(QLabel("Display Handle"))
        self.handle_input = ModernInput("@handle", max_length=20)
        form.addWidget(self.handle_input)
        
        # Email
        form.addWidget(QLabel("Email Address"))
        self.email_input = ModernInput("your@email.com", validation_func=self.validate_email)
        form.addWidget(self.email_input)
        
        layout.addLayout(form)

    def create_personalization_form(self, layout):
        form = QVBoxLayout()
        
        # Theme Toggle Section
        theme_section = QHBoxLayout()
        theme_section.setSpacing(15)
        
        # Theme label
        theme_label = QLabel("App Theme:")
        theme_label.setMinimumWidth(100)
        theme_section.addWidget(theme_label)
        
        # Theme toggle button
        self.theme_toggle_button = ModernButton("", "secondary")
        self.theme_toggle_button.setFixedSize(150, 50)  # Increased width and height
        self.theme_toggle_button.clicked.connect(self.toggle_theme)
        self.update_theme_button()
        theme_section.addWidget(self.theme_toggle_button)
        
        theme_section.addStretch()
        
        form.addLayout(theme_section)
        
        # You can add more personalization options here in the future
        # For example: Font size, Language, Notifications preferences, etc.
        
        layout.addLayout(form)

    def create_security_form(self, layout):
        # Main container for password management
        self.password_container = QWidget()
        password_layout = QVBoxLayout(self.password_container)
        password_layout.setSpacing(20)
        
        # Status indicator
        self.create_password_status(password_layout)
        
        # Messages section
        self.message_label = QLabel()
        self.message_label.setObjectName("messageLabel")
        self.message_label.setWordWrap(True)
        self.message_label.hide()
        password_layout.addWidget(self.message_label)
        
        # Dynamic form container
        self.form_container = QWidget()
        self.form_layout = QVBoxLayout(self.form_container)
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.addWidget(self.form_container)
        
        # Build the appropriate form
        self.build_password_form()
        
        layout.addWidget(self.password_container)
    
    def create_password_status(self, layout):
        status_frame = QFrame()
        status_frame.setObjectName("passwordStatusFrame")
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(20, 16, 20, 16)
        status_layout.setSpacing(16)
        
        # Icon
        self.status_icon = QLabel()
        self.status_icon.setFixedSize(40, 40)
        self.status_icon.setAlignment(Qt.AlignCenter)
        self.status_icon.setObjectName("statusIcon")
        
        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        self.status_title = QLabel()
        self.status_title.setObjectName("statusTitle")
        
        self.status_description = QLabel()
        self.status_description.setObjectName("statusDescription")
        self.status_description.setWordWrap(False)
        
        text_layout.addWidget(self.status_title)
        text_layout.addWidget(self.status_description)
        
        status_layout.addWidget(self.status_icon)
        status_layout.addLayout(text_layout)
        status_layout.addStretch()
        
        self.update_password_status()
        layout.addWidget(status_frame)
    
    def update_password_status(self):
        if self.password_manager.has_password():
            self.status_icon.setText("🔒")
            self.status_title.setText("Protection Enabled")
            self.status_description.setText("Your journal entries are secured with password protection")
            self.status_icon.setProperty("state", "enabled")
        else:
            self.status_icon.setText("🔓")
            self.status_title.setText("Protection Disabled")
            self.status_description.setText("Set a password to secure your journal entries")
            self.status_icon.setProperty("state", "disabled")
    
    def build_password_form(self):
        # Clear existing form
        while self.form_layout.count():
            child = self.form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if self.password_manager.has_password():
            self.create_protection_enabled_form()
        else:
            self.create_protection_disabled_form()
        
        # Reapply theme to newly created widgets
        self.apply_theme()
    
    def create_protection_disabled_form(self):
        """Mode 1: Protection disabled - Show set password form"""
        form_frame = QFrame()
        form_frame.setObjectName("passwordFormFrame")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(24, 24, 24, 24)
        form_layout.setSpacing(16)
        
        # New password field
        form_layout.addWidget(QLabel("New Password"))
        self.new_password_input = ModernInput("Enter your password")
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.new_password_input.textChanged.connect(self.on_new_password_changed)
        form_layout.addWidget(self.new_password_input)
        
        # Password strength widget
        self.password_strength_widget = PasswordStrengthWidget()
        form_layout.addWidget(self.password_strength_widget)
        
        # Confirm password field
        form_layout.addWidget(QLabel("Confirm Password"))
        self.confirm_password_input = ModernInput("Confirm your password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.textChanged.connect(self.validate_set_password_form)
        form_layout.addWidget(self.confirm_password_input)
        
        # Set password button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.set_password_button = ModernButton("Set Password Protection", "primary")
        self.set_password_button.clicked.connect(self.set_password)
        self.set_password_button.setEnabled(False)
        button_layout.addWidget(self.set_password_button)
        button_layout.addStretch()
        form_layout.addLayout(button_layout)
        
        self.form_layout.addWidget(form_frame)
    
    def create_protection_enabled_form(self):
        """Mode 2: Protection enabled - Show change password and remove password"""
        # Change password section
        change_frame = QFrame()
        change_frame.setObjectName("passwordFormFrame")
        change_layout = QVBoxLayout(change_frame)
        change_layout.setContentsMargins(24, 20, 24, 20)
        change_layout.setSpacing(16)
        
        # Current password for change
        change_layout.addWidget(QLabel("Current Password"))
        self.current_password_change_input = ModernInput("Enter current password")
        self.current_password_change_input.setEchoMode(QLineEdit.Password)
        change_layout.addWidget(self.current_password_change_input)
        
        # New password for change
        change_layout.addWidget(QLabel("New Password"))
        self.new_password_change_input = ModernInput("Enter new password")
        self.new_password_change_input.setEchoMode(QLineEdit.Password)
        self.new_password_change_input.textChanged.connect(self.on_change_password_changed)
        change_layout.addWidget(self.new_password_change_input)
        
        # Password strength widget for change
        self.change_password_strength_widget = PasswordStrengthWidget()
        change_layout.addWidget(self.change_password_strength_widget)
        
        # Change password button
        change_button_layout = QHBoxLayout()
        change_button_layout.addStretch()
        self.change_password_button = ModernButton("Change Password", "primary")
        self.change_password_button.clicked.connect(self.change_password)
        change_button_layout.addWidget(self.change_password_button)
        change_button_layout.addStretch()
        change_layout.addLayout(change_button_layout)
        
        self.form_layout.addWidget(change_frame)
        
        # Remove password section
        remove_frame = QFrame()
        remove_frame.setObjectName("passwordFormFrame")
        remove_layout = QVBoxLayout(remove_frame)
        remove_layout.setContentsMargins(24, 20, 24, 20)
        remove_layout.setSpacing(16)
        
        # Current password for removal
        remove_layout.addWidget(QLabel("Current Password"))
        self.current_password_remove_input = ModernInput("Enter current password to remove protection")
        self.current_password_remove_input.setEchoMode(QLineEdit.Password)
        remove_layout.addWidget(self.current_password_remove_input)
        
        # Remove password button
        remove_button_layout = QHBoxLayout()
        remove_button_layout.addStretch()
        self.remove_password_button = ModernButton("Remove Password Protection", "danger")
        self.remove_password_button.clicked.connect(self.remove_password)
        remove_button_layout.addWidget(self.remove_password_button)
        remove_button_layout.addStretch()
        remove_layout.addLayout(remove_button_layout)
        
        self.form_layout.addWidget(remove_frame)
    
    def on_new_password_changed(self):
        password = self.new_password_input.text()
        self.password_strength_widget.update_strength(password)
        self.validate_set_password_form()
    
    def on_change_password_changed(self):
        password = self.new_password_change_input.text()
        self.change_password_strength_widget.update_strength(password)
    
    def validate_set_password_form(self):
        if hasattr(self, 'new_password_input') and hasattr(self, 'confirm_password_input'):
            password = self.new_password_input.text()
            confirm = self.confirm_password_input.text()
            is_valid = (len(password) >= 6 and 
                       password == confirm and 
                       len(password) > 0 and 
                       len(confirm) > 0)
            if hasattr(self, 'set_password_button'):
                self.set_password_button.setEnabled(is_valid)
    
    def show_message(self, message: str, message_type: str = "error"):
        """Show inline message"""
        self.message_label.setText(message)
        
        if message_type == "success":
            self.message_label.setStyleSheet("color: #42c767; font-weight: 500; background-color: rgba(66, 199, 103, 0.1); padding: 12px; border-radius: 6px; border-left: 4px solid #42c767;")
        elif message_type == "error":
            self.message_label.setStyleSheet("color: #ff4757; font-weight: 500; background-color: rgba(255, 71, 87, 0.1); padding: 12px; border-radius: 6px; border-left: 4px solid #ff4757;")
        
        self.message_label.show()
        
        # Auto-hide success messages
        if message_type == "success":
            QTimer.singleShot(3000, self.hide_message)
    
    def hide_message(self):
        self.message_label.hide()
    
    def clear_all_password_fields(self):
        """Clear all password input fields"""
        for field_name in ['new_password_input', 'confirm_password_input', 
                          'current_password_change_input', 'new_password_change_input', 
                          'current_password_remove_input']:
            if hasattr(self, field_name):
                field = getattr(self, field_name)
                if field:
                    field.clear()
    def set_password(self):
        """Set a new password for journal protection"""
        self.hide_message()
        
        password = self.new_password_input.text()
        confirm = self.confirm_password_input.text()
        
        # Validation
        if not password:
            return self.show_message("Password cannot be empty", "error")
        
        if len(password) < 6:
            return self.show_message("Password must be at least 6 characters long", "error")
        
        if password != confirm:
            return self.show_message("Passwords do not match", "error")
        
        # Set the password
        if self.password_manager.set_password(password):
            # Show success message FIRST
            self.show_message("✓ Password protection enabled successfully!", "success")
            
            # Now switch to protection enabled mode (shows change/remove options)
            self.switch_to_protection_enabled()
        else:
            self.show_message("Failed to set password. Please try again.", "error")

    def change_password(self):
        """Change the existing password"""
        self.hide_message()
        
        current = self.current_password_change_input.text()
        new_password = self.new_password_change_input.text()
        
        # Validation
        if not current or not new_password:
            return self.show_message("Please fill in all password fields", "error")
        
        if len(new_password) < 6:
            return self.show_message("New password must be at least 6 characters long", "error")
        
        if current == new_password:
            return self.show_message("New password must be different from current password", "error")
        
        # Change password
        if self.password_manager.change_password(current, new_password):
            self.show_message("Password updated successfully!", "success")
            self.clear_all_password_fields()
        else:
            self.show_message("Current password is incorrect", "error")

    def remove_password(self):
        """Remove password protection"""
        self.hide_message()
        
        current = self.current_password_remove_input.text()
        
        if not current:
            return self.show_message("Please enter your current password", "error")
        
        # Remove password
        if self.password_manager.remove_password(current):
            # Emit signal that password was removed
            self.password_removed.emit()
            
            # Immediately switch to protection disabled mode
            self.switch_to_protection_disabled()
            
            # Show success message after switching
            self.show_message("Password protection removed successfully!", "success")
        else:
            self.show_message("Current password is incorrect", "error")

    def switch_to_protection_enabled(self):
        """Switch to protection enabled mode"""
        self.hide_message()
        self.update_password_status()
        self.build_password_form()
        # Ensure theme is applied after switching
        self.apply_theme()

    def switch_to_protection_disabled(self):
        """Switch to protection disabled mode"""
        self.hide_message()
        # Force update the password status first
        self.update_password_status()
        # Clear and rebuild the form for disabled mode
        self.build_password_form()
        # Ensure theme is applied after switching
        self.apply_theme()

    def create_action_buttons(self, layout):
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.discard_button = ModernButton("Discard Changes", "secondary")
        self.discard_button.setMinimumHeight(60)  # Increased height
        self.discard_button.clicked.connect(self.load_profile_data)
        self.save_button = ModernButton("Save Changes", "primary")
        self.save_button.setMinimumHeight(60)  # Increased height
        self.save_button.clicked.connect(self.save_profile)
        
        button_layout.addWidget(self.discard_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

    def validate_email(self, email: str) -> bool:
        return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None if email else True

    def show_success_toast(self, message):
        if self.success_toast: 
            self.success_toast.deleteLater()
        self.success_toast = SuccessToast(message, self)
        # Ensure the toast uses the current theme
        self.success_toast.update_theme()
        self.success_toast.setGeometry(20, 20, self.width() - 40, 50)
        self.success_toast.show()
        QTimer.singleShot(3000, lambda: self.success_toast.deleteLater() if self.success_toast else None)

    def load_profile_data(self):
        username = get_setting('username', '')
        handle = get_setting('display_handle', '')
        email = get_setting('user_email', '')
        
        self.username_input.setText(username)
        self.handle_input.setText(handle)
        self.email_input.setText(email)
        
        self.display_name.setText(username or "Welcome!")
        self.display_handle.setText(f"Good evening, {handle}" if handle else "Good evening, user")
        self.display_email.setText(email or "no-email@example.com")
        
        # Update theme button
        self.update_theme_button()
        
        # Update password status and build appropriate form
        self.update_password_status()
        self.build_password_form()

    def save_profile(self):
        username = self.username_input.text().strip()
        handle = self.handle_input.text().strip()
        email = self.email_input.text().strip()
        
        if not username: 
            return self.show_message("Username is required", "error")
        if email and not self.validate_email(email): 
            return self.show_message("Please enter a valid email address", "error")
        
        set_setting('username', username)
        set_setting('display_handle', handle)
        set_setting('user_email', email)
        set_setting('user_name', username)
        set_setting('profile_last_updated', datetime.now().isoformat())
        
        self.display_name.setText(username)
        self.display_handle.setText(f"Good evening, {handle}" if handle else "Good evening, user")
        self.display_email.setText(email or "no-email@example.com")
        
        original_text = self.save_button.text()
        original_style = self.save_button.styleSheet()
        self.save_button.setText("✓ Saved")
        self.save_button.setStyleSheet("QPushButton {background-color: #42c767; color: white; border: none; border-radius: 8px; padding: 12px 24px; font-weight: 600;}")
        QTimer.singleShot(2000, lambda: [self.save_button.setText(original_text), self.save_button.setStyleSheet(original_style)])
        
        self.profile_updated.emit(username)
        self.show_success_toast("Profile updated successfully!")
    
    def toggle_theme(self):
        """Toggle between dark and light theme"""
        current_theme = get_setting('theme', 'light')
        new_theme = 'light' if current_theme == 'dark' else 'dark'
        set_setting('theme', new_theme)
        
        # Update the button appearance
        self.update_theme_button()
        
        # Apply the new theme to this widget
        self.apply_theme()
        
        # Emit signal to notify main window
        self.theme_changed.emit(new_theme)
    
    def update_theme_button(self):
        """Update the theme toggle button text"""
        current_theme = get_setting('theme', 'light')
        if current_theme == 'dark':
            self.theme_toggle_button.setText("Light Mode")
        else:
            self.theme_toggle_button.setText("Dark Mode")
        
        # Update button style for current theme
        self.theme_toggle_button.update_style()

    def show_success_toast(self, message):
        if self.success_toast: 
            self.success_toast.deleteLater()
        self.success_toast = SuccessToast(message, self)
        # Ensure the toast uses the current theme
        self.success_toast.update_theme()
        self.success_toast.setGeometry(20, 20, self.width() - 40, 50)
        self.success_toast.show()
        QTimer.singleShot(3000, lambda: self.success_toast.deleteLater() if self.success_toast else None)

    def apply_theme(self):
        theme = get_setting('theme', 'light')
        
        if theme == 'dark':
            self.setStyleSheet("""
                QWidget {background-color: #121212; font-family: 'Segoe UI'; color: #f5f5f5;}
                QFrame#profileHeader {background: qlineargradient(x1:1, y1:0, x2:0, y2:1, stop:0 #1E40AF, stop:1 #38BDF8);}

                QFrame#profileContent {background-color: #121212;}

                /* General QLabel rule - makes ALL labels transparent */
                QLabel {background-color: transparent;}

                QLabel#profileAvatar {background-color: transparent !important;}
                QLabel#profileDisplayName {color: #ffffff; font-size: 28px; font-weight: bold;}
                QLabel#profileDisplayHandle, QLabel#profileDisplayEmail {color: #b3b3b3; font-size: 16px;}
                QLabel#profileCardTitle {font-size: 20px; font-weight: bold; color: #f5f5f5;}
                QLabel#personalCardTitle {font-size: 20px; font-weight: bold; color: #f5f5f5;}
                QLabel#securityCardTitle {font-size: 20px; font-weight: bold; color: #f5f5f5; padding-left: 16px;}
                QLabel#statusDescription {white-space: nowrap; font-size: 12px;}

                QFrame#profileCard {background-color: transparent; border: 1px solid #333333; border-radius: 12px;}

                /* Simplified Password Management Styles */
                QFrame#passwordStatusFrame {background-color: #1f1f1f; border: 1px solid #333333; border-radius: 12px;}
                QLabel#statusIcon[state="enabled"] {background-color: #1b4332; border-radius: 20px; color: #42c767;}
                QLabel#statusIcon[state="disabled"] {background-color: #3c1810; border-radius: 20px; color: #ffa726;}

                QFrame#passwordFormFrame {background-color: #1f1f1f; border: 1px solid #333333; border-radius: 12px; margin-bottom: 12px;}
                QLabel#strengthLabel {color: #b3b3b3; font-size: 12px; font-weight: 500; margin-top: 4px;}
            """)
        else:
            self.setStyleSheet("""
                QWidget {background-color: #f0f2f5; font-family: 'Segoe UI'; color: #1c1e21;}
                QFrame#profileHeader {background: qlineargradient(x1:1, y1:0, x2:0, y2:1, stop:0 #1E40AF, stop:1 #38BDF8);}
                QFrame#profileContent {background-color: #f0f2f5;}
                
                QLabel#profileDisplayName,
                QLabel#profileDisplayHandle,
                QLabel#profileDisplayEmail,
                QLabel#profileCardTitle,
                QLabel#statusTitle,
                QLabel#statusDescription,
                QLabel#formHeader,
                QLabel#sectionHeader,
                QLabel#messageLabel,
                QLabel#strengthLabel,
                QLabel#profileAvatar {
                    background-color: transparent !important;
                }

                QLabel#profileDisplayName {color: white; font-size: 28px; font-weight: bold;}
                QLabel#profileDisplayHandle, QLabel#profileDisplayEmail {color: #b8c5d6; font-size: 16px;}
                QLabel#profileCardTitle {font-size: 20px; font-weight: bold; color: #1c1e21;}
                QLabel#statusDescription {white-space: nowrap; font-size: 14px;}
                
                QFrame#profileCard {background-color: transparent; border: 1px solid #dddfe2; border-radius: 12px;}
                
                /* Simplified Password Management Styles */
                QFrame#passwordStatusFrame {background-color: white; border: 1px solid #dddfe2; border-radius: 12px;}
                QLabel#statusIcon[state="enabled"] {background-color: #e8f5e8; border-radius: 20px; color: #2e7d32;}
                QLabel#statusIcon[state="disabled"] {background-color: #fff3e0; border-radius: 20px; color: #f57c00;}
                
                QFrame#passwordFormFrame {background-color: white; border: 1px solid #dddfe2; border-radius: 12px; margin-bottom: 12px;}
                QLabel#strengthLabel {color: #616161; font-size: 12px; font-weight: 500; margin-top: 4px;}
            """)

        # Update all modern components
        for widget in self.findChildren(ModernInput): 
            widget.update_validation_style()
        for widget in self.findChildren(ModernButton): 
            widget.update_style()
            
    def update_theme(self):
        """Public method to be called when the main application theme changes"""
        self.apply_theme()
        # Force update any existing success toast
        if self.success_toast:
            self.success_toast.deleteLater()
            self.success_toast = None

    def refresh_theme(self):
        """Public method to be called when the main application theme changes - used by main window"""
        self.apply_theme()
        # Force update any existing success toast
        if self.success_toast:
            self.success_toast.deleteLater()
            self.success_toast = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.success_toast: self.success_toast.setGeometry(20, 20, self.width() - 40, 50)

    def showEvent(self, event):
        super().showEvent(event)
        self.apply_theme()
        self.load_profile_data()