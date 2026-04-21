from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QListWidget, QListWidgetItem,
    QLineEdit, QTextEdit, QCheckBox, QSlider, QSpinBox,
    QProgressBar, QGraphicsDropShadowEffect, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve, QRect, QPoint
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QPixmap, QIcon, QFontMetrics
from datetime import datetime
from database.db import get_setting


class CustomCard(QFrame):
    """Modern card widget with shadow and rounded corners."""

    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.title = title
        self.title_label = None
        self.setup_ui(title)
        self.apply_card_style()

    def setup_ui(self, title):
        self.setFrameStyle(QFrame.NoFrame)
        self.setMinimumSize(300, 250)
        self.setMaximumSize(500, 450)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        if title:
            self.title_label = QLabel(title)
            self.title_label.setFont(QFont("Arial", 18, QFont.Bold))
            self.title_label.setAlignment(Qt.AlignCenter)
            self.title_label.setObjectName("cardTitle")
            self.title_label.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.title_label, 0, Qt.AlignTop)

        layout.addSpacing(8)

        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(12)
        layout.addLayout(self.content_layout)

    def apply_card_style(self):
        """Apply card styling based on current theme."""
        theme = get_setting('theme', 'light')

        if theme == 'dark':
            self.setStyleSheet("""
                QFrame {
                    background-color: #1e1e1e;
                    border-radius: 16px;
                    border: 2px solid #404040;
                }
                QLabel#cardTitle {
                    color: #ffffff;
                    margin: 0px;
                    padding: 0px;
                    background-color: transparent;
                    border: none;
                    font-weight: 700;
                    letter-spacing: -0.5px;
                }
                QLabel {
                    background-color: transparent;
                    color: #e0e0e0;
                }
                QWidget { background-color: transparent; }
            """)
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(30)
            shadow.setColor(QColor(0, 0, 0, 150))
            shadow.setOffset(0, 8)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border-radius: 16px;
                    border: 2px solid #d1d5db;
                }
                QLabel#cardTitle {
                    color: #1a1a1a;
                    margin: 0px;
                    padding: 0px;
                    background-color: transparent;
                    border: none;
                    font-weight: 700;
                    letter-spacing: -0.5px;
                }
                QLabel {
                    background-color: transparent;
                    color: #333333;
                }
                QWidget { background-color: transparent; }
            """)
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(25)
            shadow.setColor(QColor(0, 0, 0, 60))
            shadow.setOffset(0, 6)

        self.setGraphicsEffect(shadow)

        for label in self.findChildren(QLabel):
            if 'background-color: transparent' not in label.styleSheet():
                label.setStyleSheet(label.styleSheet() + '; background-color: transparent;')

    def refresh_theme(self):
        self.apply_card_style()

    def add_widget(self, widget):
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        self.content_layout.addLayout(layout)


class ModernButton(QPushButton):
    """Modern styled button with hover effects and theme awareness."""

    def __init__(self, text="", button_type="primary", parent=None):
        super().__init__(text, parent)
        self.button_type = button_type
        self.apply_style()

    def apply_style(self):
        """Apply button styling based on type and current theme."""
        theme = get_setting('theme', 'light')

        if self.button_type == "primary":
            if theme == 'dark':
                self.setStyleSheet("""
                    QPushButton {
                        background-color: #42a5f5; color: #ffffff;
                        border: none; padding: 12px 24px;
                        border-radius: 8px; font-weight: 600; font-size: 14px;
                    }
                    QPushButton:hover { background-color: #1976d2; }
                    QPushButton:pressed { background-color: #1565c0; }
                    QPushButton:disabled { background-color: #404040; color: #808080; }
                """)
            else:
                self.setStyleSheet("""
                    QPushButton {
                        background-color: #1877f2; color: #ffffff;
                        border: none; padding: 12px 24px;
                        border-radius: 8px; font-weight: 600; font-size: 14px;
                    }
                    QPushButton:hover { background-color: #1565c0; }
                    QPushButton:pressed { background-color: #0d47a1; }
                    QPushButton:disabled { background-color: #cccccc; color: #666666; }
                """)

        elif self.button_type == "secondary":
            if theme == 'dark':
                self.setStyleSheet("""
                    QPushButton {
                        background-color: transparent; color: #42a5f5;
                        border: 2px solid #42a5f5; padding: 10px 22px;
                        border-radius: 8px; font-weight: 600; font-size: 14px;
                    }
                    QPushButton:hover { background-color: #42a5f5; color: #ffffff; }
                    QPushButton:pressed { background-color: #1976d2; }
                """)
            else:
                self.setStyleSheet("""
                    QPushButton {
                        background-color: transparent; color: #1877f2;
                        border: 2px solid #1877f2; padding: 10px 22px;
                        border-radius: 8px; font-weight: 600; font-size: 14px;
                    }
                    QPushButton:hover { background-color: #1877f2; color: #ffffff; }
                    QPushButton:pressed { background-color: #1565c0; }
                """)

        elif self.button_type == "danger":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #f44336; color: #ffffff;
                    border: none; padding: 12px 24px;
                    border-radius: 8px; font-weight: 600; font-size: 14px;
                }
                QPushButton:hover { background-color: #d32f2f; }
                QPushButton:pressed { background-color: #b71c1c; }
            """)

    def refresh_theme(self):
        self.apply_style()


class TodoItem(QFrame):
    """Todo item widget with checkbox, inline editing, and delete action."""

    completed_changed = Signal(int, bool)
    text_changed = Signal(int, str)
    delete_requested = Signal(int)

    def __init__(self, todo_id, text, completed=False, parent=None):
        super().__init__(parent)
        self.todo_id = todo_id
        self.text = text
        self.completed = completed
        self.editing = False
        self.setup_ui()
        self.apply_style()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(12)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.completed)
        self.checkbox.stateChanged.connect(self.on_completion_changed)
        layout.addWidget(self.checkbox)

        self.text_label = QLabel(self.text)
        self.text_label.setWordWrap(True)
        self.text_label.mouseDoubleClickEvent = self.start_editing
        layout.addWidget(self.text_label, 1)

        self.text_editor = QLineEdit(self.text)
        self.text_editor.hide()
        self.text_editor.editingFinished.connect(self.finish_editing)
        self.text_editor.returnPressed.connect(self.finish_editing)
        layout.addWidget(self.text_editor, 1)

        self.delete_button = QPushButton("✖")
        self.delete_button.setFixedSize(30, 30)
        self.delete_button.clicked.connect(lambda: self.delete_requested.emit(self.todo_id))
        layout.addWidget(self.delete_button)

        self.update_completion_style()

    def apply_style(self):
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
                margin: 2px 0px;
            }
            QFrame:hover { border-color: #4CAF50; background-color: #fafafa; }
            QCheckBox { spacing: 5px; }
            QCheckBox::indicator {
                width: 20px; height: 20px;
                border-radius: 4px; border: 2px solid #ddd;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50; border-color: #4CAF50;
            }
            QPushButton {
                background-color: transparent; color: #f44336;
                border: none; border-radius: 15px; font-weight: bold;
            }
            QPushButton:hover { background-color: #f44336; color: white; }
        """)

    def on_completion_changed(self, state):
        self.completed = state == Qt.Checked
        self.update_completion_style()
        self.completed_changed.emit(self.todo_id, self.completed)

    def update_completion_style(self):
        if self.completed:
            self.text_label.setStyleSheet(
                "QLabel { color: #888; text-decoration: line-through; font-style: italic; }"
            )
            self.setStyleSheet(self.styleSheet() + "QFrame { background-color: #e8f5e8; }")
        else:
            self.text_label.setStyleSheet(
                "QLabel { color: #333; text-decoration: none; font-style: normal; }"
            )

    def start_editing(self, event):
        if not self.editing:
            self.editing = True
            self.text_label.hide()
            self.text_editor.setText(self.text)
            self.text_editor.show()
            self.text_editor.setFocus()
            self.text_editor.selectAll()

    def finish_editing(self):
        if self.editing:
            new_text = self.text_editor.text().strip()
            if new_text and new_text != self.text:
                self.text = new_text
                self.text_label.setText(self.text)
                self.text_changed.emit(self.todo_id, self.text)

            self.editing = False
            self.text_editor.hide()
            self.text_label.show()


class TimerDisplay(QWidget):
    """Large digital timer display for Pomodoro sessions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.minutes = 25
        self.seconds = 0
        self.is_break_mode = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.timer_label = QLabel("25:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setFont(QFont("Arial", 72, QFont.Bold))
        self.update_style()
        layout.addWidget(self.timer_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(25 * 60)
        self.progress_bar.setValue(25 * 60)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self._apply_progress_style(color="#4CAF50")
        layout.addWidget(self.progress_bar)

    def _apply_progress_style(self, color):
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none; border-radius: 4px; background-color: #e0e0e0;
            }}
            QProgressBar::chunk {{
                background-color: {color}; border-radius: 4px;
            }}
        """)

    def update_time(self, minutes, seconds):
        self.minutes = minutes
        self.seconds = seconds
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")
        self.progress_bar.setValue(minutes * 60 + seconds)

    def set_break_mode(self, is_break):
        self.is_break_mode = is_break
        self.update_style()
        self._apply_progress_style(color="#FF9800" if is_break else "#4CAF50")

    def update_style(self):
        color = "#FF9800" if self.is_break_mode else "#4CAF50"
        self.timer_label.setStyleSheet(
            f"QLabel {{ color: {color}; background-color: transparent; }}"
        )

    def set_duration(self, minutes):
        total_seconds = minutes * 60
        self.progress_bar.setMaximum(total_seconds)
        self.progress_bar.setValue(total_seconds)


class CircularProgress(QWidget):
    """Circular progress indicator widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0
        self.maximum = 100
        self.setFixedSize(120, 120)

    def set_progress(self, value):
        self.progress = min(max(0, value), self.maximum)
        self.update()

    def set_maximum(self, value):
        self.maximum = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setPen(QPen(QColor("#e0e0e0"), 8))
        painter.drawEllipse(10, 10, 100, 100)

        painter.setPen(QPen(QColor("#4CAF50"), 8))
        span_angle = int((self.progress / self.maximum) * 360 * 16)
        painter.drawArc(10, 10, 100, 100, 90 * 16, -span_angle)

        painter.setPen(QPen(QColor("#333"), 2))
        painter.setFont(QFont("Arial", 16, QFont.Bold))
        percentage = int((self.progress / self.maximum) * 100)
        painter.drawText(self.rect(), Qt.AlignCenter, f"{percentage}%")


class JournalEntryWidget(QFrame):
    """Widget for displaying journal entries in the two-page design."""

    edit_requested = Signal(object)
    delete_requested = Signal(object)

    def __init__(self, entry, parent=None):
        super().__init__(parent)
        self.entry = entry
        self.setup_ui()
        self.apply_style()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        header_layout = QHBoxLayout()

        if hasattr(self.entry, 'created_at'):
            entry_date = (
                datetime.fromisoformat(self.entry.created_at)
                if isinstance(self.entry.created_at, str)
                else self.entry.created_at
            )
            date_str = entry_date.strftime("%B %d, %Y")
        else:
            date_str = "Unknown Date"

        date_label = QLabel(date_str)
        date_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(date_label)
        header_layout.addStretch()

        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("editButton")
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.entry))

        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("deleteButton")
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.entry))

        header_layout.addWidget(edit_btn)
        header_layout.addWidget(delete_btn)
        layout.addLayout(header_layout)

        if hasattr(self.entry, 'get_content_preview'):
            content_preview = self.entry.get_content_preview(200)
        else:
            content = getattr(self.entry, 'content', '')
            if hasattr(self.entry, 'is_encrypted') and self.entry.is_encrypted:
                content = "[Encrypted Entry]"
            content_preview = content[:200] + "..." if len(content) > 200 else content

        content_label = QLabel(content_preview)
        content_label.setWordWrap(True)
        content_label.setObjectName("contentPreview")
        layout.addWidget(content_label)

        if hasattr(self.entry, 'mood_rating') and self.entry.mood_rating:
            mood_emojis = {1: "😢", 2: "😔", 3: "😐", 4: "😊", 5: "😄"}
            mood_layout = QHBoxLayout()
            mood_layout.addWidget(QLabel("Mood:"))
            mood_layout.addWidget(QLabel(mood_emojis.get(self.entry.mood_rating, "😐")))
            mood_layout.addStretch()
            layout.addLayout(mood_layout)

    def apply_style(self):
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
                margin: 5px 0px;
            }
            QFrame:hover { border-color: #2196F3; background-color: #fafafa; }
            QLabel { color: #333; }
            QLabel#contentPreview { color: #666; font-size: 13px; line-height: 1.4; }
            QPushButton#editButton {
                background-color: #2196F3; color: white;
                border: none; border-radius: 6px;
                padding: 6px 12px; font-size: 12px; font-weight: 600; min-width: 60px;
            }
            QPushButton#editButton:hover { background-color: #1976D2; }
            QPushButton#deleteButton {
                background-color: #f44336; color: white;
                border: none; border-radius: 6px;
                padding: 6px 12px; font-size: 12px; font-weight: 600; min-width: 60px;
            }
            QPushButton#deleteButton:hover { background-color: #d32f2f; }
        """)


class MarqueeLabel(QLabel):
    """Label widget with marquee scrolling for text that overflows its container."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.full_text = text
        self.scroll_position = 0
        self.scroll_direction = 1
        self.scroll_speed = 2
        self.pause_duration = 2000
        self.is_paused = False
        self.needs_scrolling = False

        self.scroll_timer = QTimer()
        self.scroll_timer.timeout.connect(self.update_scroll)
        self.scroll_timer.setInterval(50)

        self.pause_timer = QTimer()
        self.pause_timer.timeout.connect(self.resume_scrolling)
        self.pause_timer.setSingleShot(True)

        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def setText(self, text):
        self.full_text = text
        super().setText(text)
        self.check_scrolling_needed()

    def setFont(self, font):
        super().setFont(font)
        self.check_scrolling_needed()

    def check_scrolling_needed(self):
        if not self.full_text:
            return

        font_metrics = QFontMetrics(self.font())
        text_width = font_metrics.horizontalAdvance(self.full_text)
        widget_width = self.width() - 20

        self.needs_scrolling = text_width > widget_width

        if self.needs_scrolling:
            self.start_marquee()
        else:
            self.stop_marquee()
            super().setText(self.full_text)

    def start_marquee(self):
        if not self.scroll_timer.isActive():
            self.scroll_position = 0
            self.scroll_direction = 1
            self.is_paused = False
            self.scroll_timer.start()

    def stop_marquee(self):
        self.scroll_timer.stop()
        self.pause_timer.stop()
        self.scroll_position = 0

    def update_scroll(self):
        if self.is_paused:
            return

        font_metrics = QFontMetrics(self.font())
        text_width = font_metrics.horizontalAdvance(self.full_text)
        widget_width = self.width() - 20

        if text_width <= widget_width:
            self.stop_marquee()
            return

        max_scroll = text_width - widget_width
        self.scroll_position += self.scroll_speed * self.scroll_direction

        if self.scroll_direction == 1 and self.scroll_position >= max_scroll:
            self.scroll_position = max_scroll
            self.pause_and_reverse()
        elif self.scroll_direction == -1 and self.scroll_position <= 0:
            self.scroll_position = 0
            self.pause_and_reverse()

        self.update_visible_text()

    def update_visible_text(self):
        font_metrics = QFontMetrics(self.font())
        widget_width = self.width() - 20

        start_char = 0
        current_width = 0
        for i, char in enumerate(self.full_text):
            if current_width >= self.scroll_position:
                start_char = i
                break
            current_width += font_metrics.horizontalAdvance(char)

        visible_text = ""
        current_width = 0
        for i in range(start_char, len(self.full_text)):
            char = self.full_text[i]
            char_width = font_metrics.horizontalAdvance(char)
            if current_width + char_width > widget_width:
                break
            visible_text += char
            current_width += char_width

        super().setText(visible_text)

    def pause_and_reverse(self):
        self.is_paused = True
        self.scroll_direction *= -1
        self.pause_timer.start(self.pause_duration)

    def resume_scrolling(self):
        self.is_paused = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(10, self.check_scrolling_needed)

    def enterEvent(self, event):
        super().enterEvent(event)
        self.scroll_speed = 1
        self.scroll_timer.setInterval(80)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.scroll_speed = 2
        self.scroll_timer.setInterval(50)