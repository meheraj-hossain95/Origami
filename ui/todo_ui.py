from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QScrollArea, QFrame, QCheckBox, QSizePolicy, QProgressBar
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from logic.todo_logic import TodoManager, TodoValidator
from database.db import get_setting


class TodoTheme:
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

    def __init__(self, todo_id, text, completed=False, parent=None):
        super().__init__(parent)
        self.todo_id = todo_id
        self.text = text
        self.completed = completed
        self.editing = False
        self._setup_ui()
        self.apply_style()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.completed)
        self.checkbox.stateChanged.connect(self.toggle_completion)
        layout.addWidget(self.checkbox)

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

        self.edit_button = QPushButton("✏️ Edit")
        self.edit_button.setToolTip("Edit this task")
        self.edit_button.clicked.connect(self.start_editing)
        layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("🗑️ Delete")
        self.delete_button.setToolTip("Delete this task")
        self.delete_button.clicked.connect(self.delete_todo)
        layout.addWidget(self.delete_button)

        self.update_completion_style()

    def apply_style(self):
        palette = TodoTheme.get_palette(get_setting('theme', 'light'))

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

        self.update_completion_style()

    def update_completion_style(self):
        palette = TodoTheme.get_palette(get_setting('theme', 'light'))

        self.text_label.setStyleSheet(f"""
            QLabel {{
                color: {palette['text_primary']};
                text-decoration: none;
                background-color: transparent;
            }}
        """)

    def toggle_completion(self, state):
        self.completed = state == Qt.Checked
        self.update_completion_style()
        self._bubble_signal('toggle_todo_completion', self.todo_id, self.completed)

    def start_editing(self, event=None):
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
                self._bubble_signal('update_todo_text', self.todo_id, self.text)

            self.editing = False
            self.text_editor.hide()
            self.text_label.show()

    def delete_todo(self):
        self._bubble_signal('delete_todo_item', self.todo_id)

    def _bubble_signal(self, method_name, *args):
        """Walk up the widget tree to find and call a handler on TodoWidget."""
        parent = self.parent()
        while parent:
            if hasattr(parent, method_name):
                getattr(parent, method_name)(*args)
                return
            parent = parent.parent()


class TodoWidget(QWidget):
    # Emitted when any task is added, updated, completed, or deleted.
    tasks_updated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.todo_manager = TodoManager()
        self._setup_ui()
        self.load_todos()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(30)

        self._apply_main_theme()
        self._setup_header(layout)
        self._setup_add_task(layout)
        self._setup_todo_list(layout)

    def _apply_main_theme(self):
        palette = TodoTheme.get_palette(get_setting('theme', 'light'))
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

    def _setup_header(self, layout):
        palette = TodoTheme.get_palette(get_setting('theme', 'light'))

        self.progress_frame = QFrame()
        self.progress_frame.setStyleSheet("QFrame { background-color: transparent; border: none; padding: 8px; }")

        progress_layout = QVBoxLayout(self.progress_frame)
        progress_layout.setContentsMargins(10, 8, 10, 8)
        progress_layout.setSpacing(4)

        self.progress_label = QLabel("0% Complete (0 of 0 tasks)")
        self.progress_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.progress_label.setStyleSheet(f"color: {palette['text_primary']}; margin-bottom: 2px; background-color: transparent;")
        self.progress_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
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

        layout.addWidget(self.progress_frame)

    def _setup_add_task(self, layout):
        palette = TodoTheme.get_palette(get_setting('theme', 'light'))

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
        add_layout.setContentsMargins(10, 8, 10, 8)
        add_layout.setSpacing(8)

        self.add_input = QLineEdit()
        self.add_input.setPlaceholderText("What do you need to do?")
        self.add_input.setFont(QFont("Segoe UI", 16))
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

        self.add_button = QPushButton("Add Task")
        self.add_button.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.add_button.setToolTip("Add new task")
        self.add_button.clicked.connect(self.add_todo)
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
        add_layout.addWidget(self.add_button)

        self.clear_all_button = QPushButton("Clear All")
        self.clear_all_button.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.clear_all_button.setToolTip("Clear all tasks")
        self.clear_all_button.clicked.connect(self.clear_all_tasks)
        self.clear_all_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover { background-color: #c82333; }
            QPushButton:pressed { background-color: #bd2130; }
        """)
        add_layout.addWidget(self.clear_all_button)

        layout.addWidget(self.add_frame)

    def _setup_todo_list(self, layout):
        palette = TodoTheme.get_palette(get_setting('theme', 'light'))

        self.list_frame = QFrame()
        self.list_frame.setStyleSheet("QFrame { background-color: transparent; border: none; }")

        list_layout = QVBoxLayout(self.list_frame)
        list_layout.setContentsMargins(20, 20, 20, 20)
        list_layout.setSpacing(0)

        self.list_title = QLabel("Your Tasks")
        self.list_title.setFont(QFont("Segoe UI", 28, QFont.Bold))
        self.list_title.setStyleSheet(f"color: {palette['text_primary']}; margin-bottom: 20px; background-color: transparent;")
        list_layout.addWidget(self.list_title)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea { border: none; background-color: transparent; }
            QScrollBar:vertical {
                border: none; background-color: transparent;
                width: 8px; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: transparent;
                border-radius: 4px; min-height: 20px;
            }
            QScrollBar::handle:vertical:hover { background-color: transparent; }
        """)

        self.todo_container = QWidget()
        self.todo_container.setStyleSheet("QWidget { background-color: transparent; border: none; }")
        self.todo_layout = QVBoxLayout(self.todo_container)
        self.todo_layout.setContentsMargins(0, 0, 0, 0)
        self.todo_layout.setSpacing(0)

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
        self.empty_label.hide()
        self.todo_layout.addWidget(self.empty_label)

        self.scroll_area.setWidget(self.todo_container)
        list_layout.addWidget(self.scroll_area)

        layout.addWidget(self.list_frame)

    # --- Public API (called by SimpleTodoItem via _bubble_signal) ---

    def add_todo(self):
        text = self.add_input.text().strip()
        if not text:
            return
        try:
            self.todo_manager.add_todo(text)
            self.add_input.clear()
            self.load_todos()
            self.tasks_updated.emit()
        except Exception:
            self.load_todos()

    def load_todos(self):
        self._clear_todo_display()

        todos = self.todo_manager.get_todos()
        self.empty_label.hide()

        for todo in sorted(todos, key=lambda x: x['created_at'], reverse=True):
            item = SimpleTodoItem(todo['id'], todo['title'], todo['completed'])
            item.setParent(self.todo_container)
            self.todo_layout.addWidget(item)

        self.todo_layout.addStretch()
        self._update_progress()

    def toggle_todo_completion(self, todo_id, completed):
        try:
            self.todo_manager.toggle_todo(todo_id)
            self._update_progress()
            self.tasks_updated.emit()
        except Exception:
            self.load_todos()

    def update_todo_text(self, todo_id, new_text):
        try:
            self.todo_manager.update_todo_title(todo_id, new_text)
            self.tasks_updated.emit()
        except Exception:
            self.load_todos()

    def delete_todo_item(self, todo_id):
        try:
            self.todo_manager.delete_todo(todo_id)
            self.load_todos()
            self.tasks_updated.emit()
        except Exception:
            self.load_todos()

    def clear_all_tasks(self):
        try:
            todos = self.todo_manager.get_todos()
            if not todos:
                return
            for todo in todos:
                self.todo_manager.delete_todo(todo['id'])
            self.load_todos()
        except Exception:
            self.load_todos()

    # --- Theme ---

    def refresh_theme(self):
        """Re-apply the active theme across all components and todo items."""
        self._apply_main_theme()
        self._apply_theme_to_components()
        self._refresh_todo_item_themes()
        self._update_progress()

    def _apply_theme_to_components(self):
        palette = TodoTheme.get_palette(get_setting('theme', 'light'))

        if hasattr(self, 'list_title'):
            self.list_title.setStyleSheet(f"color: {palette['text_primary']}; margin-bottom: 20px; background-color: transparent;")

        if hasattr(self, 'progress_frame'):
            self.progress_frame.setStyleSheet("QFrame { background-color: transparent; border: none; padding: 8px; }")

        if hasattr(self, 'progress_label'):
            self.progress_label.setStyleSheet(f"color: {palette['text_primary']}; margin-bottom: 2px; background-color: transparent;")

        if hasattr(self, 'progress_bar'):
            self.progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: none; border-radius: 4px;
                    background-color: transparent;
                }}
                QProgressBar::chunk {{
                    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 {palette['progress_fill']}, stop: 1 {palette['progress_fill']});
                    border-radius: 4px;
                }}
            """)

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
            self.add_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {palette['primary']};
                    color: white; border: none;
                    border-radius: 6px; padding: 8px 16px;
                    font-weight: bold; min-width: 80px;
                }}
                QPushButton:hover {{
                    background-color: {QColor(palette['primary']).lighter(110).name()};
                }}
                QPushButton:pressed {{
                    background-color: {QColor(palette['primary']).darker(110).name()};
                }}
            """)

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

    def _refresh_todo_item_themes(self):
        for i in range(self.todo_layout.count()):
            item = self.todo_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), SimpleTodoItem):
                item.widget().apply_style()

    # --- Internal helpers ---

    def _clear_todo_display(self):
        while self.todo_layout.count():
            child = self.todo_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

    def _update_progress(self):
        todos = self.todo_manager.get_todos()
        total = len(todos)
        completed = sum(1 for t in todos if t['completed'])

        if total == 0:
            self.progress_label.setText("Ready to add your first task!")
            self.progress_bar.setValue(0)
        else:
            pct = int((completed / total) * 100)
            self.progress_label.setText(f"{pct}% Complete ({completed} of {total} tasks)")
            self.progress_bar.setValue(pct)