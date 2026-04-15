"""
Todo List Logic - Handles all business logic for the todo application
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from database.models import Todo

class TodoManager:
    """Manages todo operations and data persistence"""
    
    def __init__(self):
        self.todos = []
        self.next_id = 1
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'active_tasks': 0
        }
        self.load_todos()
    
    def add_todo(self, title: str, description: str = "", priority: int = 1) -> int:
        """Add a new todo item"""
        if not title.strip():
            raise ValueError("Todo title cannot be empty")
        
        # Create in database
        todo_id = Todo.create(title.strip(), description.strip(), priority)
        
        # Add to local cache
        todo_item = {
            'id': todo_id,
            'title': title.strip(),
            'description': description.strip(),
            'completed': False,
            'priority': priority,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        self.todos.append(todo_item)
        self.update_stats()
        self.save_todos()
        
        return todo_id
    
    def toggle_todo(self, todo_id: int) -> bool:
        """Toggle todo completion status"""
        for todo in self.todos:
            if todo['id'] == todo_id:
                todo['completed'] = not todo['completed']
                todo['updated_at'] = datetime.now().isoformat()
                
                # Update in database
                Todo.update_completed(todo_id, todo['completed'])
                
                self.update_stats()
                self.save_todos()
                return todo['completed']
        
        raise ValueError(f"Todo with ID {todo_id} not found")
    
    def update_todo_title(self, todo_id: int, new_title: str) -> bool:
        """Update todo title"""
        if not new_title.strip():
            raise ValueError("Todo title cannot be empty")
        
        for todo in self.todos:
            if todo['id'] == todo_id:
                todo['title'] = new_title.strip()
                todo['updated_at'] = datetime.now().isoformat()
                
                # Update in database
                Todo.update_title(todo_id, new_title.strip())
                
                self.save_todos()
                return True
        
        raise ValueError(f"Todo with ID {todo_id} not found")
    
    def delete_todo(self, todo_id: int) -> bool:
        """Delete a todo item"""
        for i, todo in enumerate(self.todos):
            if todo['id'] == todo_id:
                # Delete from database
                Todo.delete(todo_id)
                
                # Remove from local cache
                self.todos.pop(i)
                self.update_stats()
                self.save_todos()
                return True
        
        raise ValueError(f"Todo with ID {todo_id} not found")
    
    def get_todos(self, filter_type: str = "all") -> List[Dict]:
        """Get todos based on filter"""
        if filter_type == "active":
            return [todo for todo in self.todos if not todo['completed']]
        elif filter_type == "completed":
            return [todo for todo in self.todos if todo['completed']]
        else:  # all
            return self.todos.copy()
    
    def search_todos(self, query: str) -> List[Dict]:
        """Search todos by title or description"""
        if not query.strip():
            return self.todos.copy()
        
        query = query.lower().strip()
        results = []
        
        for todo in self.todos:
            if (query in todo['title'].lower() or 
                query in todo.get('description', '').lower()):
                results.append(todo)
        
        return results
    
    def clear_completed(self) -> int:
        """Clear all completed todos"""
        completed_count = 0
        remaining_todos = []
        
        for todo in self.todos:
            if todo['completed']:
                # Delete from database
                Todo.delete(todo['id'])
                completed_count += 1
            else:
                remaining_todos.append(todo)
        
        self.todos = remaining_todos
        self.update_stats()
        self.save_todos()
        
        return completed_count
    
    def reorder_todos(self, from_index: int, to_index: int) -> bool:
        """Reorder todos (for drag and drop)"""
        if (0 <= from_index < len(self.todos) and 
            0 <= to_index < len(self.todos) and 
            from_index != to_index):
            
            todo = self.todos.pop(from_index)
            self.todos.insert(to_index, todo)
            
            # Update timestamps
            for i, todo in enumerate(self.todos):
                todo['order'] = i
                todo['updated_at'] = datetime.now().isoformat()
            
            self.save_todos()
            return True
        
        return False
    
    def get_stats(self) -> Dict:
        """Get todo statistics"""
        return self.stats.copy()
    
    def get_completion_percentage(self) -> float:
        """Get completion percentage"""
        if self.stats['total_tasks'] == 0:
            return 0.0
        return (self.stats['completed_tasks'] / self.stats['total_tasks']) * 100
    
    def update_stats(self):
        """Update todo statistics"""
        completed = sum(1 for todo in self.todos if todo['completed'])
        total = len(self.todos)
        active = total - completed
        
        self.stats.update({
            'total_tasks': total,
            'completed_tasks': completed,
            'active_tasks': active
        })
    
    def load_todos(self):
        """Load todos from database"""
        try:
            # Load from database
            db_todos = Todo.get_all()
            
            self.todos = []
            for row in db_todos:
                todo_item = {
                    'id': row[0],
                    'title': row[1],
                    'description': row[2] or "",
                    'completed': bool(row[3]),
                    'priority': row[4] or 1,
                    'created_at': row[6] or datetime.now().isoformat(),
                    'updated_at': row[7] or datetime.now().isoformat()
                }
                self.todos.append(todo_item)
                
                # Update next_id to avoid conflicts
                if row[0] >= self.next_id:
                    self.next_id = row[0] + 1
            
            self.update_stats()
            
        except Exception as e:
            print(f"Error loading todos from database: {e}")
            self.todos = []
            self.update_stats()
    
    def save_todos(self):
        """Save todos to local JSON file for backup"""
        try:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            backup_file = os.path.join(data_dir, 'todos_backup.json')
            
            backup_data = {
                'todos': self.todos,
                'stats': self.stats,
                'last_saved': datetime.now().isoformat()
            }
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error saving todos backup: {e}")

class TodoFilter:
    """Handles todo filtering and sorting operations"""
    
    @staticmethod
    def filter_by_status(todos: List[Dict], status: str) -> List[Dict]:
        """Filter todos by completion status"""
        if status == "active":
            return [todo for todo in todos if not todo['completed']]
        elif status == "completed":
            return [todo for todo in todos if todo['completed']]
        else:
            return todos
    
    @staticmethod
    def filter_by_priority(todos: List[Dict], min_priority: int = 1) -> List[Dict]:
        """Filter todos by minimum priority"""
        return [todo for todo in todos if todo.get('priority', 1) >= min_priority]
    
    @staticmethod
    def search_todos(todos: List[Dict], query: str) -> List[Dict]:
        """Search todos by text"""
        if not query.strip():
            return todos
        
        query = query.lower().strip()
        results = []
        
        for todo in todos:
            if (query in todo['title'].lower() or 
                query in todo.get('description', '').lower()):
                results.append(todo)
        
        return results
    
    @staticmethod
    def sort_todos(todos: List[Dict], sort_by: str = "created_at", reverse: bool = False) -> List[Dict]:
        """Sort todos by specified field"""
        valid_fields = ['title', 'created_at', 'updated_at', 'priority', 'completed']
        
        if sort_by not in valid_fields:
            sort_by = 'created_at'
        
        return sorted(todos, key=lambda x: x.get(sort_by, ''), reverse=reverse)

class TodoValidator:
    """Validates todo input data"""
    
    @staticmethod
    def validate_title(title: str) -> bool:
        """Validate todo title"""
        return bool(title and title.strip() and len(title.strip()) <= 200)
    
    @staticmethod
    def validate_description(description: str) -> bool:
        """Validate todo description"""
        return len(description) <= 1000
    
    @staticmethod
    def validate_priority(priority: int) -> bool:
        """Validate priority value"""
        return isinstance(priority, int) and 1 <= priority <= 5
    
    @staticmethod
    def validate_todo_data(title: str, description: str = "", priority: int = 1) -> tuple:
        """Validate all todo data and return (is_valid, error_message)"""
        if not TodoValidator.validate_title(title):
            return False, "Title is required and must be less than 200 characters"
        
        if not TodoValidator.validate_description(description):
            return False, "Description must be less than 1000 characters"
        
        if not TodoValidator.validate_priority(priority):
            return False, "Priority must be between 1 and 5"
        
        return True, ""
