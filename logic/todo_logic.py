import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from database.models import Todo


class TodoManager:

    def __init__(self):
        self.todos: List[Dict] = []
        self.next_id: int = 1
        self.stats: Dict = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "active_tasks": 0,
        }
        self.load_todos()

    def add_todo(self, title: str, description: str = "", priority: int = 1) -> int:
        if not title.strip():
            raise ValueError("Todo title cannot be empty")

        todo_id = Todo.create(title.strip(), description.strip(), priority)

        self.todos.append({
            "id": todo_id,
            "title": title.strip(),
            "description": description.strip(),
            "completed": False,
            "priority": priority,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        })

        self._update_stats()
        return todo_id

    def toggle_todo(self, todo_id: int) -> bool:
        todo = self._find_todo(todo_id)

        todo["completed"] = not todo["completed"]
        todo["updated_at"] = datetime.now().isoformat()

        Todo.update_completed(todo_id, todo["completed"])
        self._update_stats()

        return todo["completed"]

    def update_todo_title(self, todo_id: int, new_title: str) -> bool:
        if not new_title.strip():
            raise ValueError("Todo title cannot be empty")

        todo = self._find_todo(todo_id)

        todo["title"] = new_title.strip()
        todo["updated_at"] = datetime.now().isoformat()

        Todo.update_title(todo_id, new_title.strip())
        return True

    def delete_todo(self, todo_id: int) -> bool:
        for i, todo in enumerate(self.todos):
            if todo["id"] == todo_id:
                Todo.delete(todo_id)
                self.todos.pop(i)
                self._update_stats()
                return True

        raise ValueError(f"Todo with ID {todo_id} not found")

    def get_todos(self, filter_type: str = "all") -> List[Dict]:
        if filter_type == "active":
            return [t for t in self.todos if not t["completed"]]
        elif filter_type == "completed":
            return [t for t in self.todos if t["completed"]]
        return self.todos.copy()

    def search_todos(self, query: str) -> List[Dict]:
        if not query.strip():
            return self.todos.copy()

        q = query.lower().strip()
        return [
            t for t in self.todos
            if q in t["title"].lower() or q in t.get("description", "").lower()
        ]

    def clear_completed(self) -> int:
        completed = [t for t in self.todos if t["completed"]]

        for todo in completed:
            Todo.delete(todo["id"])

        self.todos = [t for t in self.todos if not t["completed"]]
        self._update_stats()

        return len(completed)

    def reorder_todos(self, from_index: int, to_index: int) -> bool:
        n = len(self.todos)
        if not (0 <= from_index < n and 0 <= to_index < n and from_index != to_index):
            return False

        todo = self.todos.pop(from_index)
        self.todos.insert(to_index, todo)

        now = datetime.now().isoformat()
        for i, t in enumerate(self.todos):
            t["order"] = i
            t["updated_at"] = now

        return True

    def get_stats(self) -> Dict:
        return self.stats.copy()

    def get_completion_percentage(self) -> float:
        total = self.stats["total_tasks"]
        if total == 0:
            return 0.0
        return (self.stats["completed_tasks"] / total) * 100

    def load_todos(self):
        try:
            db_todos = Todo.get_all()
            now = datetime.now().isoformat()

            self.todos = []
            for row in db_todos:
                self.todos.append({
                    "id": row[0],
                    "title": row[1],
                    "description": row[2] or "",
                    "completed": bool(row[3]),
                    "priority": row[4] or 1,
                    "created_at": row[6] or now,
                    "updated_at": row[7] or now,
                })
                if row[0] >= self.next_id:
                    self.next_id = row[0] + 1

            self._update_stats()

        except Exception as e:
            print(f"Error loading todos from database: {e}")
            self.todos = []
            self._update_stats()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _find_todo(self, todo_id: int) -> Dict:
        for todo in self.todos:
            if todo["id"] == todo_id:
                return todo
        raise ValueError(f"Todo with ID {todo_id} not found")

    def _update_stats(self):
        completed = sum(1 for t in self.todos if t["completed"])
        total = len(self.todos)
        self.stats = {
            "total_tasks": total,
            "completed_tasks": completed,
            "active_tasks": total - completed,
        }


class TodoFilter:

    @staticmethod
    def filter_by_status(todos: List[Dict], status: str) -> List[Dict]:
        if status == "active":
            return [t for t in todos if not t["completed"]]
        elif status == "completed":
            return [t for t in todos if t["completed"]]
        return todos

    @staticmethod
    def filter_by_priority(todos: List[Dict], min_priority: int = 1) -> List[Dict]:
        return [t for t in todos if t.get("priority", 1) >= min_priority]

    @staticmethod
    def search_todos(todos: List[Dict], query: str) -> List[Dict]:
        if not query.strip():
            return todos

        q = query.lower().strip()
        return [
            t for t in todos
            if q in t["title"].lower() or q in t.get("description", "").lower()
        ]

    @staticmethod
    def sort_todos(
        todos: List[Dict],
        sort_by: str = "created_at",
        reverse: bool = False,
    ) -> List[Dict]:
        valid_fields = {"title", "created_at", "updated_at", "priority", "completed"}
        key = sort_by if sort_by in valid_fields else "created_at"
        return sorted(todos, key=lambda x: x.get(key, ""), reverse=reverse)


class TodoValidator:
    @staticmethod
    def validate_title(title: str) -> bool:
        return bool(title and title.strip() and len(title.strip()) <= 200)

    @staticmethod
    def validate_description(description: str) -> bool:
        return len(description) <= 1000

    @staticmethod
    def validate_priority(priority: int) -> bool:
        return isinstance(priority, int) and 1 <= priority <= 5

    @staticmethod
    def validate_todo_data(
        title: str,
        description: str = "",
        priority: int = 1,
    ) -> Tuple[bool, str]:
        if not TodoValidator.validate_title(title):
            return False, "Title is required and must be less than 200 characters"
        if not TodoValidator.validate_description(description):
            return False, "Description must be less than 1000 characters"
        if not TodoValidator.validate_priority(priority):
            return False, "Priority must be between 1 and 5"
        return True, ""