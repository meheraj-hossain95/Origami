"""
Task Completion Card - Shows daily task completion statistics
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QFrame
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
from datetime import datetime, date
from ui.common_widgets import CustomCard
from logic.todo_logic import TodoManager
from database.db import get_setting

class TaskCompletionCard(CustomCard):
    """Card widget for displaying today's task completion statistics on dashboard"""
    
    def __init__(self, parent=None):
        super().__init__("Today's Progress", parent)
        self.todo_manager = TodoManager()
        self.current_gradient_color = '#4CAF50'  # Default color
        self.setup_completion_ui()
        self.load_task_stats()
        
        # Auto-refresh stats periodically
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.load_task_stats)
        self.refresh_timer.start(60000)  # Refresh every minute
    
    def refresh_theme(self):
        """Refresh theme when changed"""
        super().refresh_theme()  # Call parent's refresh_theme method
        self.load_task_stats()  # Reload to apply theme-aware styling
    
    def setup_completion_ui(self):
        """Setup the task completion UI"""
        # Stats row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)  # Consistent spacing between stat frames
        
        # Completed tasks
        self.completed_frame = self.create_stat_frame("0", "Completed", "#4CAF50")
        stats_layout.addWidget(self.completed_frame)
        
        # Remaining tasks  
        self.remaining_frame = self.create_stat_frame("0", "Remaining", "#FF9800")
        stats_layout.addWidget(self.remaining_frame)
        
        # Total tasks
        self.total_frame = self.create_stat_frame("0", "Total", "#2196F3")
        stats_layout.addWidget(self.total_frame)
        
        self.content_layout.addLayout(stats_layout)
        
        # Progress bar section with modern styling
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(10)  # Increased spacing
        
        # Progress label with better typography
        self.progress_label = QLabel("0% Complete")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setFont(QFont("Arial", 16, QFont.Bold))  # Larger, more prominent
        self.progress_label.setObjectName("progressLabel")
        progress_layout.addWidget(self.progress_label)
        
        # Modern progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(12)  # Slightly thicker
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setObjectName("taskProgressBar")
        progress_layout.addWidget(self.progress_bar)
        
        self.content_layout.addLayout(progress_layout)
        
        # Add productivity insights section
        insights_layout = QVBoxLayout()
        insights_layout.setSpacing(6)
        
        # Productivity insight label
        self.insight_label = QLabel("Track your daily productivity")
        self.insight_label.setAlignment(Qt.AlignCenter)
        self.insight_label.setFont(QFont("Arial", 13, QFont.Medium))  # Improved font
        self.insight_label.setObjectName("insightLabel")
        insights_layout.addWidget(self.insight_label)
        
        # Quick action hint
        self.action_hint = QLabel("• Add tasks to get started")
        self.action_hint.setAlignment(Qt.AlignCenter)
        self.action_hint.setFont(QFont("Arial", 11, QFont.Normal))  # Slightly larger
        self.action_hint.setObjectName("actionHint")
        insights_layout.addWidget(self.action_hint)
        
        self.content_layout.addLayout(insights_layout)
    
    def create_stat_frame(self, value, label, color):
        """Create a statistics frame"""
        frame = QFrame()
        frame.setFixedHeight(90)  # Increased height from 75 to 90
        frame.setObjectName("statFrame")
        
        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(6)  # Slightly more spacing
        layout.setContentsMargins(12, 12, 12, 12)  # More balanced padding
        
        # Value label with larger typography
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setFont(QFont("Arial", 32, QFont.Bold))  # Increased from 26 to 32
        value_label.setObjectName("statValue")
        value_label.setStyleSheet(f"""
            color: {color};
            font-weight: 800;
            letter-spacing: -1px;
            background-color: transparent;
            border: none;
            line-height: 1.0;
        """)
        layout.addWidget(value_label)
        
        # Description label with larger typography
        desc_label = QLabel(label)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setFont(QFont("Arial", 13, QFont.Medium))  # Increased from 11 to 13
        desc_label.setObjectName("statDescription")
        desc_label.setStyleSheet("background-color: transparent; border: none; letter-spacing: 0.3px;")
        layout.addWidget(desc_label)
        
        # Store references for updates
        frame.value_label = value_label
        frame.desc_label = desc_label
        frame.color = color
        
        return frame
    
    def load_task_stats(self):
        """Load today's task statistics"""
        # Get current stats from todo manager
        stats = self.todo_manager.get_stats()
        completed = stats['completed_tasks']
        total = stats['total_tasks']
        remaining = stats['active_tasks']
        
        # Calculate completion percentage
        completion_percentage = 0
        if total > 0:
            completion_percentage = int((completed / total) * 100)
        
        # Update stat frames
        self.completed_frame.value_label.setText(str(completed))
        self.remaining_frame.value_label.setText(str(remaining))
        self.total_frame.value_label.setText(str(total))
        
        # Update progress with professional messages
        if total == 0:
            self.progress_label.setText("Ready to start your day")
            self.insight_label.setText("No tasks created yet")
            self.action_hint.setText("• Navigate to Tasks to create your first task")
        elif completion_percentage == 100:
            self.progress_label.setText("All tasks completed")
            self.insight_label.setText("Excellent work today!")
            self.action_hint.setText("• Consider planning tomorrow's tasks")
        elif completion_percentage >= 75:
            self.progress_label.setText(f"{completion_percentage}% Complete")
            self.insight_label.setText("Great progress today")
            self.action_hint.setText("• You're almost done!")
        elif completion_percentage >= 50:
            self.progress_label.setText(f"{completion_percentage}% Complete")
            self.insight_label.setText("Keep up the momentum")
            self.action_hint.setText("• You're halfway there")
        elif completion_percentage >= 25:
            self.progress_label.setText(f"{completion_percentage}% Complete")
            self.insight_label.setText("Making steady progress")
            self.action_hint.setText("• Focus on your next task")
        else:
            self.progress_label.setText(f"{completion_percentage}% Complete")
            self.insight_label.setText("Just getting started")
            self.action_hint.setText("• Take it one task at a time")
            
        self.progress_bar.setValue(completion_percentage)
        
        # Update progress bar color based on completion percentage
        self.update_progress_bar_color(completion_percentage)
        
        # Apply theme-aware styling
        self.apply_theme_aware_styling()
    
    def update_progress_bar_color(self, percentage):
        """Update progress bar color based on completion percentage"""
        if percentage == 0:
            gradient_color = "#9E9E9E"  # Gray for 0%
        elif percentage < 25:
            gradient_color = "#F44336"  # Red for low completion
        elif percentage < 50:
            gradient_color = "#FF9800"  # Orange for medium-low completion
        elif percentage < 75:
            gradient_color = "#FFC107"  # Yellow for medium completion
        elif percentage < 100:
            gradient_color = "#4CAF50"  # Green for high completion
        else:
            gradient_color = "#2E7D32"  # Dark green for 100% completion
        
        # Store gradient color for theme styling
        self.current_gradient_color = gradient_color
    
    def apply_theme_aware_styling(self):
        """Apply modern styling based on current theme"""
        theme = get_setting('theme', 'light')
        
        # Get the current gradient color (default to green if not set)
        gradient_color = getattr(self, 'current_gradient_color', '#4CAF50')
        
        # Modern styling for stat frames
        if theme == 'dark':
            stat_frame_style = """
                QFrame#statFrame {
                    background-color: transparent;
                    border-radius: 12px;
                   
                }
                QLabel#statDescription {
                    color: #b8b8b8;
                    font-weight: 600;
                    letter-spacing: 0.4px;
                    background-color: transparent;
                   
                }
                QLabel#statValue {
                    background-color: transparent;
                   
                }
                QLabel {
                    background-color: transparent;
                   
                }
            """
            
            progress_label_color = "#f5f5f5"
            insight_color = "#c0c0c0"
            hint_color = "#a0a0a0"
            progress_bar_style = f"""
                QProgressBar#taskProgressBar {{
                    border: none;
                    border-radius: 6px;
                    background-color: #404040;
                    text-align: center;
                }}
                QProgressBar#taskProgressBar::chunk {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                              stop:0 {gradient_color}, stop:1 {self.lighten_color(gradient_color, 25)});
                    border-radius: 6px;
                }}
            """
        else:
            stat_frame_style = """
                QFrame#statFrame {
                    background-color: transparent;
                    border-radius: 12px;
                   
                }
                QLabel#statDescription {
                    color: #6c757d;
                    font-weight: 600;
                    letter-spacing: 0.4px;
                    background-color: transparent;
                    
                }
                QLabel#statValue {
                    background-color: transparent;
                    
                }
                QLabel {
                    background-color: transparent;
                   
                }
            """
            
            progress_label_color = "#212529"
            insight_color = "#495057"
            hint_color = "#6c757d"
            progress_bar_style = f"""
                QProgressBar#taskProgressBar {{
                    border: none;
                    border-radius: 6px;
                    background-color: #e9ecef;
                    text-align: center;
                }}
                QProgressBar#taskProgressBar::chunk {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                              stop:0 {gradient_color}, stop:1 {self.lighten_color(gradient_color, 25)});
                    border-radius: 6px;
                }}
            """
        
        # Apply styles to all stat frames
        for frame in [self.completed_frame, self.remaining_frame, self.total_frame]:
            frame.setStyleSheet(stat_frame_style)
            # Ensure all child labels have transparent backgrounds and no borders
            for label in frame.findChildren(QLabel):
                current_style = label.styleSheet()
                if 'background-color: transparent' not in current_style or 'border: none' not in current_style:
                    label.setStyleSheet(current_style + '; background-color: transparent; border: none;')
        
        self.progress_label.setStyleSheet(f"""
            QLabel#progressLabel {{
                color: {progress_label_color};
                margin: 8px 0px;
                font-weight: 700;
                letter-spacing: -0.3px;
                background-color: transparent;
                border: none;
                line-height: 1.2;
            }}
        """)
        
        self.insight_label.setStyleSheet(f"""
            QLabel#insightLabel {{
                color: {insight_color};
                font-weight: 500;
                background-color: transparent;
                border: none;
                line-height: 1.4;
                letter-spacing: 0.2px;
            }}
        """)
        
        self.action_hint.setStyleSheet(f"""
            QLabel#actionHint {{
                color: {hint_color};
                font-style: italic;
                background-color: transparent;
                border: none;
                line-height: 1.3;
                letter-spacing: 0.1px;
            }}
        """)
        
        self.progress_bar.setStyleSheet(progress_bar_style)
        
        # Force refresh all child widgets
        self.update()
        for child in self.findChildren(QWidget):
            child.update()
    
    def lighten_color(self, color_hex, percent):
        """Lighten a hex color by a percentage"""
        # Remove the # if present
        if color_hex.startswith('#'):
            color_hex = color_hex[1:]
        
        # Convert to RGB
        r = int(color_hex[0:2], 16)
        g = int(color_hex[2:4], 16) 
        b = int(color_hex[4:6], 16)
        
        # Lighten each component
        r = min(255, int(r + (255 - r) * percent / 100))
        g = min(255, int(g + (255 - g) * percent / 100))
        b = min(255, int(b + (255 - b) * percent / 100))
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def update_stats(self):
        """Public method to update stats (called from outside)"""
        # Reload the todo manager to get fresh data
        self.todo_manager.load_todos()
        self.load_task_stats()