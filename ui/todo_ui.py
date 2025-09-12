"""
Simple Modern Todo List UI - Clean, minimal design inspired by Google/Facebook
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QLabel, QScrollArea, QFrame, QCheckBox, QSizePolicy, QProgressBar
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from datetime import datetime

from logic.todo_logic import TodoManager, TodoValidator
from database.db import get_setting

# Theme color palettes
class TodoTheme:
    """Theme colors for Todo UI"""
    LIGHT_PALETTE = {
        'background': '#f0f2f5',
        'surface': '#ffffff',
        'primary': '#1877f2',
        'text_primary': '#1c1e21',
        'text_secondary': '#65676b',
        'border': '#e1e5e9',
        'input_bg': '#f7f8fa',
        'progress_bg': '#f0f2f5',
        'progress_fill': '#42b883',
        'completed_bg': '#42b883',
        'completed_text': '#ffffff',
        'button_bg': '#f0f2f5',
        'button_text': '#1c1e21',
        'button_hover': '#e4e6ea'
    }
    
    DARK_PALETTE = {
        'background': '#121212',
        'surface': '#1e1e1e',
        'primary': '#42a5f5',
        'text_primary': '#e0e0e0',
        'text_secondary': '#a0a0a0',
        'border': '#303030',
        'input_bg': '#2a2a2a',
        'progress_bg': '#303030',
        'progress_fill': '#4caf50',
        'completed_bg': '#4caf50',
        'completed_text': '#ffffff',
        'button_bg': '#303030',
        'button_text': '#e0e0e0',
        'button_hover': '#404040'
    }
    
    @staticmethod
    def get_palette(theme_name):
        return TodoTheme.DARK_PALETTE if theme_name == 'dark' else TodoTheme.LIGHT_PALETTE

class SimpleTodoItem(QFrame):
    """A simple todo item with modern styling"""
    
    def __init__(self, todo_id, text, completed=False, parent=None):
        super().__init__(parent)
        self.todo_id = todo_id
        self.text = text
        self.completed = completed
        self.editing = False
        self.setup_ui()
        self.apply_style()
    
    def setup_ui(self):
        """Setup the todo item UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # Checkbox for completion
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.completed)
        self.checkbox.stateChanged.connect(self.toggle_completion)
        layout.addWidget(self.checkbox)
        
        # Text display/editor
        self.text_label = QLabel(self.text)
        self.text_label.setWordWrap(True)
        self.text_label.setFont(QFont("Segoe UI", 14))
        self.text_label.mouseDoubleClickEvent = self.start_editing
        layout.addWidget(self.text_label, 1)
        
        self.text_editor = QLineEdit(self.text)
        self.text_editor.setFont(QFont("Segoe UI", 14))
        self.text_editor.hide()
        self.text_editor.editingFinished.connect(self.finish_editing)
        self.text_editor.returnPressed.connect(self.finish_editing)
        layout.addWidget(self.text_editor, 1)
        
        # Edit button
        self.edit_button = QPushButton("✏️ Edit")
        self.edit_button.clicked.connect(self.start_editing)
        layout.addWidget(self.edit_button)
        
        # Delete button
        self.delete_button = QPushButton("🗑️ Delete")
        self.delete_button.clicked.connect(self.delete_todo)
        layout.addWidget(self.delete_button)
        
        # Ensure connections are established properly
        self.edit_button.setToolTip("Edit this task")
        self.delete_button.setToolTip("Delete this task")
        
        self.update_completion_style()
    
    def apply_style(self):
        """Apply modern Google/Facebook-like styling with theme support"""
        theme_name = get_setting('theme', 'light')
        palette = TodoTheme.get_palette(theme_name)
        
        self.setStyleSheet(f"""
            SimpleTodoItem {{
                background-color: {palette['surface']};
                border: 1px solid {palette['border']};
                border-radius: 12px;
                margin: 8px 0px;
            }}
            SimpleTodoItem:hover {{
                border-color: {palette['primary']};
            }}
            QCheckBox {{
                spacing: 8px;
                background-color: transparent;
            }}
            QCheckBox::indicator {{
                width: 24px;
                height: 24px;
                border-radius: 12px;
                border: 2px solid {palette['border']};
                background-color: {palette['surface']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {palette['progress_fill']};
                border-color: {palette['progress_fill']};
            }}
            QPushButton {{
                background-color: {palette['button_bg']};
                color: {palette['button_text']};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 14px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {palette['button_hover']};
            }}
            QPushButton:pressed {{
                background-color: {palette['button_hover']};
            }}
            QLineEdit {{
                border: 2px solid {palette['border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: {palette['surface']};
                color: {palette['text_primary']};
            }}
            QLineEdit:focus {{
                border-color: {palette['primary']};
                outline: none;
            }}
        """)
        
        # Apply completion styling after base style
        self.update_completion_style()
    
    def toggle_completion(self, state):
        """Handle completion toggle with smooth color transition"""
        self.completed = state == Qt.Checked
        self.update_completion_style()
        
        # Find and signal parent TodoWidget
        parent_widget = self.parent()
        while parent_widget:
            if hasattr(parent_widget, 'toggle_todo_completion'):
                parent_widget.toggle_todo_completion(self.todo_id, self.completed)
                break
            parent_widget = parent_widget.parent()
    
    def update_completion_style(self):
        """Update style based on completion - no visual changes for completed tasks"""
        theme_name = get_setting('theme', 'light')
        palette = TodoTheme.get_palette(theme_name)
        
        # No visual difference between completed and uncompleted tasks
        self.text_label.setStyleSheet(f"""
            QLabel {{
                color: {palette['text_primary']};
                text-decoration: none;
                background-color: transparent;
            }}
        """)
    
    def start_editing(self, event=None):
        """Start inline editing"""
        if not self.editing:
            self.editing = True
            self.text_label.hide()
            self.text_editor.setText(self.text)
            self.text_editor.show()
            self.text_editor.setFocus()
            self.text_editor.selectAll()
    
    def finish_editing(self):
        """Finish inline editing"""
        if self.editing:
            new_text = self.text_editor.text().strip()
            if new_text and new_text != self.text:
                self.text = new_text
                self.text_label.setText(self.text)
                
                # Find and signal parent TodoWidget
                parent_widget = self.parent()
                while parent_widget:
                    if hasattr(parent_widget, 'update_todo_text'):
                        parent_widget.update_todo_text(self.todo_id, self.text)
                        break
                    parent_widget = parent_widget.parent()
            
            self.editing = False
            self.text_editor.hide()
            self.text_label.show()
    
    def delete_todo(self):
        """Delete this todo item"""
        # Find and signal parent TodoWidget
        parent_widget = self.parent()
        while parent_widget:
            if hasattr(parent_widget, 'delete_todo_item'):
                parent_widget.delete_todo_item(self.todo_id)
                break
            parent_widget = parent_widget.parent()


class TodoWidget(QWidget):
    """Simple, modern Todo List Widget inspired by Google/Facebook design"""
    
    # Signal emitted when tasks are updated (added, completed, deleted, etc.)
    tasks_updated = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize todo manager
        self.todo_manager = TodoManager()
        
        self.setup_ui()
        self.load_todos()
    
    def setup_ui(self):
        """Setup the clean, simple UI with theme support"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(30)
        
        # Apply theme to main widget
        self.apply_main_theme()
        
        # Modern header
        self.setup_header(layout)
        
        # Add task section
        self.setup_add_task(layout)
        
        # Todo list
        self.setup_todo_list(layout)
    
    def apply_main_theme(self):
        """Apply theme to the main widget background"""
        theme_name = get_setting('theme', 'light')
        palette = TodoTheme.get_palette(theme_name)
        
        self.setStyleSheet(f"""
            TodoWidget {{
                background-color: {palette['background']};
                color: {palette['text_primary']};
            }}
            QWidget {{
                background-color: {palette['background']};
                color: {palette['text_primary']};
            }}
        """)
    
    def setup_header(self, layout):
        """Setup modern header section with progress bar and theme support"""
        theme_name = get_setting('theme', 'light')
        palette = TodoTheme.get_palette(theme_name)
        
        header_layout = QVBoxLayout()
        
        # Title - Increased size DRAMATICALL
        
        # Removed subtitle label completely
        
        # Progress section - Much smaller height
        self.progress_frame = QFrame()
        self.progress_frame.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: none;
                padding: 8px;
            }}
        """)
        
        progress_layout = QVBoxLayout(self.progress_frame)
        progress_layout.setContentsMargins(10, 8, 10, 8)  # Much smaller padding
        progress_layout.setSpacing(4)  # Much smaller spacing
        
        # Progress label - smaller
        self.progress_label = QLabel("0% Complete (0 of 0 tasks)")
        self.progress_label.setFont(QFont("Segoe UI", 18, QFont.Bold))  # Increased font size more
        self.progress_label.setStyleSheet(f"color: {palette['text_primary']}; margin-bottom: 2px; background-color: transparent;")  # Added transparent background
        self.progress_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.progress_label)
        
        # Progress bar - much thinner
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)  # Very thin - 8px
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background-color: {palette['progress_bg']};
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {palette['progress_fill']}, stop: 1 {palette['progress_fill']});
                border-radius: 4px;
            }}
        """)
        progress_layout.addWidget(self.progress_bar)
        
        header_layout.addWidget(self.progress_frame)
        layout.addLayout(header_layout)
    
    def setup_add_task(self, layout):
        """Setup add task section with theme support"""
        theme_name = get_setting('theme', 'light')
        palette = TodoTheme.get_palette(theme_name)
        
        self.add_frame = QFrame()
        self.add_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {palette['surface']};
                border-radius: 8px;
                border: 1px solid {palette['border']};
                padding: 8px;
            }}
        """)
        
        add_layout = QHBoxLayout(self.add_frame)
        add_layout.setContentsMargins(10, 8, 10, 8)  # Much smaller padding
        add_layout.setSpacing(8)  # Smaller spacing
        
        # Input field - Much smaller
        self.add_input = QLineEdit()
        self.add_input.setPlaceholderText("What do you need to do?")
        self.add_input.setFont(QFont("Segoe UI", 16))  # Increased font size
        self.add_input.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid {palette['border']};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 16px;
                background-color: {palette['input_bg']};
                color: {palette['text_primary']};
            }}
            QLineEdit:focus {{
                border-color: {palette['primary']};
                background-color: {palette['surface']};
            }}
        """)
        self.add_input.returnPressed.connect(self.add_todo)
        add_layout.addWidget(self.add_input, 1)
        
        # Add button - Much smaller
        self.add_button = QPushButton("Add Task")
        self.add_button.setFont(QFont("Segoe UI", 12, QFont.Bold))  # Smaller font
        self.add_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {palette['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {QColor(palette['primary']).lighter(110).name()};
            }}
            QPushButton:pressed {{
                background-color: {QColor(palette['primary']).darker(110).name()};
            }}
        """)
        # Connect the button signal
        self.add_button.clicked.connect(self.add_todo)
        self.add_button.setToolTip("Add new task")
        add_layout.addWidget(self.add_button)
        
        # Clear All button - Much smaller
        self.clear_all_button = QPushButton("Clear All")
        self.clear_all_button.setFont(QFont("Segoe UI", 12, QFont.Bold))  # Smaller font
        self.clear_all_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: #c82333;
            }}
            QPushButton:pressed {{
                background-color: #bd2130;
            }}
        """)
        # Connect the button signal
        self.clear_all_button.clicked.connect(self.clear_all_tasks)
        self.clear_all_button.setToolTip("Clear all tasks")
        add_layout.addWidget(self.clear_all_button)
        
        layout.addWidget(self.add_frame)
    
    def setup_todo_list(self, layout):
        """Setup the todo list section with theme support"""
        theme_name = get_setting('theme', 'light')
        palette = TodoTheme.get_palette(theme_name)
        
        # Container frame
        self.list_frame = QFrame()
        self.list_frame.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: none;
            }}
        """)
        
        list_layout = QVBoxLayout(self.list_frame)
        list_layout.setContentsMargins(20, 20, 20, 20)
        list_layout.setSpacing(0)
        
        # List title
        self.list_title = QLabel("Your Tasks")
        self.list_title.setFont(QFont("Segoe UI", 28, QFont.Bold))
        self.list_title.setStyleSheet(f"color: {palette['text_primary']}; margin-bottom: 20px; background-color: transparent;")
        list_layout.addWidget(self.list_title)
        
        # Scroll area for tasks
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                border: none;
                background-color: transparent;
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: transparent;
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: transparent;
            }}
        """)
        
        # Todo container
        self.todo_container = QWidget()
        self.todo_container.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
                border: none;
            }}
        """)
        self.todo_layout = QVBoxLayout(self.todo_container)
        self.todo_layout.setContentsMargins(0, 0, 0, 0)
        self.todo_layout.setSpacing(0)
        
        # Empty state message - hidden by default
        self.empty_label = QLabel("No tasks yet!\nAdd your first task above to get started.")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setFont(QFont("Segoe UI", 18))
        self.empty_label.setStyleSheet(f"""
            QLabel {{
                color: {palette['text_secondary']};
                padding: 60px;
                background-color: {palette['input_bg']};
                border-radius: 12px;
                border: 2px dashed {palette['border']};
            }}
        """)
        self.empty_label.hide()  # Always hide - no empty state messages
        self.todo_layout.addWidget(self.empty_label)
        
        self.scroll_area.setWidget(self.todo_container)
        list_layout.addWidget(self.scroll_area)
        
        layout.addWidget(self.list_frame)
    
    def add_todo(self):
        """Add a new todo item"""
        text = self.add_input.text().strip()
        
        if not text:
            return
        
        try:
            # Add todo using manager
            self.todo_manager.add_todo(text)
            
            # Clear input
            self.add_input.clear()
            
            # Refresh display and progress
            self.load_todos()
            self.update_progress()
            
            # Emit signal to notify other widgets
            self.tasks_updated.emit()
            
        except Exception as e:
            # Silent error handling - reload to fix inconsistent state
            self.load_todos()
    
    def load_todos(self):
        """Load and display todos"""
        # Clear existing todos
        self.clear_todo_display()
        
        # Get all todos
        todos = self.todo_manager.get_todos()
        
        # Always hide empty label - no messages needed
        self.empty_label.hide()
        
        # Create todo items if any exist
        if todos:
            for todo in sorted(todos, key=lambda x: x['created_at'], reverse=True):
                todo_item = SimpleTodoItem(
                    todo['id'],
                    todo['title'],
                    todo['completed']
                )
                
                # Ensure proper parent-child relationship
                todo_item.setParent(self.todo_container)
                self.todo_layout.addWidget(todo_item)
        
        # Add spacer at the end
        self.todo_layout.addStretch()
        
        # Update progress bar
        self.update_progress()
    
    def update_progress(self):
        """Update progress bar and label based on completed tasks"""
        todos = self.todo_manager.get_todos()
        total_tasks = len(todos)
        completed_tasks = len([todo for todo in todos if todo['completed']])
        
        # Handle empty state cleanly
        if total_tasks == 0:
            percentage = 0
            self.progress_label.setText("Ready to add your first task!")
        else:
            percentage = int((completed_tasks / total_tasks) * 100)
            self.progress_label.setText(f"{percentage}% Complete ({completed_tasks} of {total_tasks} tasks)")
        
        self.progress_bar.setValue(percentage)
    
    def clear_todo_display(self):
        """Clear the todo display"""
        while self.todo_layout.count():
            child = self.todo_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
    
    def toggle_todo_completion(self, todo_id, completed):
        """Handle todo completion toggle"""
        try:
            self.todo_manager.toggle_todo(todo_id)
            self.update_progress()
            
            # Emit signal to notify other widgets
            self.tasks_updated.emit()
        except Exception as e:
            # Silent error handling - reload to fix inconsistent state
            self.load_todos()
    
    def update_todo_text(self, todo_id, new_text):
        """Handle todo text update"""
        try:
            self.todo_manager.update_todo_title(todo_id, new_text)
            
            # Emit signal to notify other widgets
            self.tasks_updated.emit()
        except Exception as e:
            # Silent error handling - reload to fix inconsistent state
            self.load_todos()
    
    def clear_all_tasks(self):
        """Clear all tasks after confirmation"""
        try:
            # Get all todos to check if there are any
            todos = self.todo_manager.get_todos()
            
            if not todos:
                return  # No tasks to clear
            
            # Clear all todos using the manager
            for todo in todos:
                self.todo_manager.delete_todo(todo['id'])
            
            # Refresh display and progress
            self.load_todos()
            self.update_progress()
            
        except Exception as e:
            # Silent error handling - reload to fix inconsistent state
            self.load_todos()
    
    def delete_todo_item(self, todo_id):
        """Handle todo deletion"""
        try:
            self.todo_manager.delete_todo(todo_id)
            self.load_todos()
            self.update_progress()
            
            # Emit signal to notify other widgets
            self.tasks_updated.emit()
        except Exception as e:
            # Silent error handling - reload to fix inconsistent state
            self.load_todos()
    
    def apply_theme_to_components(self):
        """Apply theme to existing components without recreating them"""
        theme_name = get_setting('theme', 'light')
        palette = TodoTheme.get_palette(theme_name)
        
        # Update title label
        if hasattr(self, 'title_label'):
            self.title_label.setStyleSheet(f"color: {palette['text_primary']}; margin-bottom: 25px; padding: 20px;")
        
        # Update list title
        if hasattr(self, 'list_title'):
            self.list_title.setStyleSheet(f"color: {palette['text_primary']}; margin-bottom: 20px; background-color: transparent !important;")
        
        # Update header frame and progress components
        if hasattr(self, 'progress_frame'):
            self.progress_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: transparent;
                    border: none;
                    padding: 8px;
                }}
            """)
        
        if hasattr(self, 'progress_label'):
            self.progress_label.setStyleSheet(f"color: {palette['text_primary']}; margin-bottom: 2px; background-color: transparent !important;")
        
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    border-radius: 4px;
                    background-color: transparent !important;
                }}
                QProgressBar::chunk {{
                    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 {palette['progress_fill']}, stop: 1 {palette['progress_fill']});
                    border-radius: 4px;
                }}
            """)
        
        # Update add task frame and components
        if hasattr(self, 'add_frame'):
            self.add_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {palette['surface']};
                    border-radius: 8px;
                    border: 1px solid {palette['border']};
                    padding: 8px;
                }}
            """)
        
        if hasattr(self, 'add_input'):
            self.add_input.setStyleSheet(f"""
                QLineEdit {{
                    border: 2px solid {palette['border']};
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 12px;
                    background-color: {palette['input_bg']};
                    color: {palette['text_primary']};
                }}
                QLineEdit:focus {{
                    border-color: {palette['primary']};
                    background-color: {palette['surface']};
                }}
            """)
        
        if hasattr(self, 'add_button'):
            from PySide6.QtGui import QColor
            self.add_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {palette['primary']};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                    min-width: 80px;
                }}
                QPushButton:hover {{
                    background-color: {QColor(palette['primary']).lighter(110).name()};
                }}
                QPushButton:pressed {{
                    background-color: {QColor(palette['primary']).darker(110).name()};
                }}
            """)
        
        if hasattr(self, 'clear_all_button'):
            self.clear_all_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                    min-width: 80px;
                }}
                QPushButton:hover {{
                    background-color: #c82333;
                }}
                QPushButton:pressed {{
                    background-color: #bd2130;
                }}
            """)
        
        # Update list frame
        if hasattr(self, 'list_frame'):
            self.list_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: transparent;
                    border: none;
                }}
            """)
        
        # Update scroll area
        if hasattr(self, 'scroll_area'):
            self.scroll_area.setStyleSheet(f"""
                QScrollArea {{
                    border: none;
                    background-color: transparent;
                }}
                QScrollBar:vertical {{
                    border: none;
                    background-color: transparent;
                    width: 8px;
                    border-radius: 4px;
                }}
                QScrollBar::handle:vertical {{
                    background-color: transparent;
                    border-radius: 4px;
                    min-height: 20px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background-color: transparent;
                }}
            """)
        
        # Update todo container
        if hasattr(self, 'todo_container'):
            self.todo_container.setStyleSheet(f"""
                QWidget {{
                    background-color: transparent;
                    border: none;
                }}
            """)
        
        # Update empty label
        if hasattr(self, 'empty_label'):
            self.empty_label.setStyleSheet(f"""
                QLabel {{
                    color: {palette['text_secondary']};
                    padding: 60px;
                    background-color: {palette['input_bg']};
                    border-radius: 12px;
                    border: 2px dashed {palette['border']};
                }}
            """)

    def refresh_theme(self):
        """Refresh theme when changed by main window"""
        # Apply theme to main widget
        self.apply_main_theme()
        
        # Reapply styles to existing components instead of recreating
        self.apply_theme_to_components()
        
        # Update all existing todo items with new theme
        self.refresh_existing_todo_items()
        
        # Update progress and other elements
        self.update_progress()
    
    def refresh_existing_todo_items(self):
        """Refresh theme for all existing todo items"""
        for i in range(self.todo_layout.count()):
            item = self.todo_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, SimpleTodoItem):
                    # Force theme update for the todo item
                    widget.apply_style()
                    # Make sure completion state is properly reflected
                    if hasattr(widget, 'completed'):
                        widget.update_completion_style()