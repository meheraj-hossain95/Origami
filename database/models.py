from datetime import datetime
from database.db import get_connection

class Todo:
   
    @staticmethod
    def create(title, description="", priority=1, due_date=None):
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO todos (title, description, priority, due_date)
            VALUES (?, ?, ?, ?)
        ''', (title, description, priority, due_date))
        
        todo_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return todo_id
    
    @staticmethod
    def get_all():
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM todos ORDER BY created_at DESC')
        todos = cursor.fetchall()
        
        conn.close()
        return todos
    
    @staticmethod
    def update_completed(todo_id, completed):
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE todos SET completed = ?, updated_at = ?
            WHERE id = ?
        ''', (completed, datetime.now().isoformat(), todo_id))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def update_title(todo_id, title):
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE todos SET title = ?, updated_at = ?
            WHERE id = ?
        ''', (title, datetime.now().isoformat(), todo_id))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def delete(todo_id):
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
        
        conn.commit()
        conn.close()

class JournalEntry:

    def __init__(self, id=None, title="", content="", encrypted_content=None, is_encrypted=False, 
                 mood_rating=3, created_at=None, updated_at=None):
        self.id = id
        self.title = title
        self.content = content
        self.encrypted_content = encrypted_content
        self.is_encrypted = is_encrypted
        self.mood_rating = mood_rating
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    @staticmethod
    def create(title, content, mood_rating=None, is_encrypted=False):

        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO journal_entries (title, content, mood_rating, is_encrypted)
            VALUES (?, ?, ?, ?)
        ''', (title, content, mood_rating, is_encrypted))
        
        entry_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return entry_id
    
    @staticmethod
    def create_with_date(title, content, entry_date, mood_rating=None, is_encrypted=False):

        conn = get_connection()
        cursor = conn.cursor()
        
        # Convert date to datetime for storage
        if isinstance(entry_date, datetime):
            created_at = entry_date.isoformat()
        else:
            created_at = datetime.combine(entry_date, datetime.min.time()).isoformat()
        
        cursor.execute('''
            INSERT INTO journal_entries (title, content, mood_rating, is_encrypted, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, content, mood_rating, is_encrypted, created_at, datetime.now().isoformat()))
        
        entry_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return entry_id
    
    @staticmethod
    def get_all():

        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM journal_entries ORDER BY created_at DESC')
        rows = cursor.fetchall()
        
        conn.close()
        
        entries = []
        for row in rows:
            entry = JournalEntry(
                id=row[0],
                title=row[1],
                content=row[2],
                encrypted_content=row[3] if len(row) > 3 else None,
                is_encrypted=bool(row[4]) if len(row) > 4 else False,
                mood_rating=row[5] if len(row) > 5 and row[5] is not None else 3,
                created_at=datetime.fromisoformat(row[6]) if len(row) > 6 and row[6] else datetime.now(),
                updated_at=datetime.fromisoformat(row[7]) if len(row) > 7 and row[7] else datetime.now()
            )
            entries.append(entry)
        
        return entries
    
    @staticmethod
    def get_by_date(entry_date):

        conn = get_connection()
        cursor = conn.cursor()
        
        if isinstance(entry_date, datetime):
            start_date = entry_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = entry_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            start_date = datetime.combine(entry_date, datetime.min.time())
            end_date = datetime.combine(entry_date, datetime.max.time())
        
        cursor.execute('''
            SELECT * FROM journal_entries 
            WHERE created_at >= ? AND created_at <= ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (start_date.isoformat(), end_date.isoformat()))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return JournalEntry(
                id=row[0],
                title=row[1],
                content=row[2],
                encrypted_content=row[3] if len(row) > 3 else None,
                is_encrypted=bool(row[4]) if len(row) > 4 else False,
                mood_rating=row[5] if len(row) > 5 and row[5] is not None else 3,
                created_at=datetime.fromisoformat(row[6]) if len(row) > 6 and row[6] else datetime.now(),
                updated_at=datetime.fromisoformat(row[7]) if len(row) > 7 and row[7] else datetime.now()
            )
        
        return None
    
    @staticmethod
    def search_entries(query):

        conn = get_connection()
        cursor = conn.cursor()
        
        # Search by content (case-insensitive)
        cursor.execute('''
            SELECT * FROM journal_entries 
            WHERE LOWER(content) LIKE ? OR LOWER(title) LIKE ?
            ORDER BY created_at DESC
        ''', (f'%{query.lower()}%', f'%{query.lower()}%'))
        
        rows = cursor.fetchall()
        conn.close()
        
        entries = []
        for row in rows:
            entry = JournalEntry(
                id=row[0],
                title=row[1],
                content=row[2],
                encrypted_content=row[3] if len(row) > 3 else None,
                is_encrypted=bool(row[4]) if len(row) > 4 else False,
                mood_rating=row[5] if len(row) > 5 and row[5] is not None else 3,
                created_at=datetime.fromisoformat(row[6]) if len(row) > 6 and row[6] else datetime.now(),
                updated_at=datetime.fromisoformat(row[7]) if len(row) > 7 and row[7] else datetime.now()
            )
            entries.append(entry)
        
        return entries
    
    def update(self, title=None, content=None, mood_rating=None):

        if not self.id:
            return
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Build update query dynamically
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
            self.title = title
        
        if content is not None:
            updates.append("content = ?")
            params.append(content)
            self.content = content
        
        if mood_rating is not None:
            updates.append("mood_rating = ?")
            params.append(mood_rating)
            self.mood_rating = mood_rating
        
        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            self.updated_at = datetime.now()
            
            params.append(self.id)
            
            query = f"UPDATE journal_entries SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            
            conn.commit()
        
        conn.close()
    
    def delete(self):

        if self.id:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM journal_entries WHERE id = ?', (self.id,))
            
            conn.commit()
            conn.close()
    
    def get_formatted_date(self):

        return self.created_at.strftime("%B %d, %Y")
    
    def get_content_preview(self, max_length=150):

        content = self.content
        if self.is_encrypted and self.encrypted_content:
            content = "[Encrypted Entry]"
        
        return content[:max_length] + "..." if len(content) > max_length else content

class PomodoroSession:
    
    @staticmethod
    def create(duration, task_description=""):

        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO pomodoro_sessions (duration, task_description)
            VALUES (?, ?)
        ''', (duration, task_description))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return session_id
    
    @staticmethod
    def complete_session(session_id):

        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE pomodoro_sessions 
            SET completed = TRUE, ended_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), session_id))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_recent_sessions(limit=10):

        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM pomodoro_sessions 
            ORDER BY started_at DESC 
            LIMIT ?
        ''', (limit,))
        
        sessions = cursor.fetchall()
        conn.close()
        
        return sessions

class CalendarEvent:
    
    def __init__(self, id=None, title="", description="", event_date=None, 
                 priority="normal", created_at=None, updated_at=None):
        self.id = id
        self.title = title
        self.description = description
        self.event_date = event_date or datetime.now().date()
        self.priority = priority  # 'important', 'next_important', 'normal'
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    @staticmethod
    def create(title, description="", event_date=None, priority="normal"):
        conn = get_connection()
        cursor = conn.cursor()
        
        # Format date for database storage
        if event_date:
            if isinstance(event_date, datetime):
                date_str = event_date.date().isoformat()
            else:
                date_str = event_date.isoformat()
        else:
            date_str = datetime.now().date().isoformat()
        
        cursor.execute('''
            INSERT INTO calendar_events (title, description, event_date, priority)
            VALUES (?, ?, ?, ?)
        ''', (title, description, date_str, priority))
        
        event_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return event_id
    
    @staticmethod
    def get_all():
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM calendar_events ORDER BY event_date ASC')
        rows = cursor.fetchall()
        
        conn.close()
        
        events = []
        for row in rows:
            event = CalendarEvent(
                id=row[0],
                title=row[1],
                description=row[2] or "",
                event_date=datetime.fromisoformat(row[3]).date(),
                priority=row[4] or "normal",
                created_at=datetime.fromisoformat(row[5]) if row[5] else datetime.now(),
                updated_at=datetime.fromisoformat(row[6]) if row[6] else datetime.now()
            )
            events.append(event)
        
        return events
    
    @staticmethod
    def get_by_date(event_date):
        conn = get_connection()
        cursor = conn.cursor()
        
        if isinstance(event_date, datetime):
            date_str = event_date.date().isoformat()
        else:
            date_str = event_date.isoformat()
        
        cursor.execute('''
            SELECT * FROM calendar_events 
            WHERE event_date = ?
            ORDER BY created_at ASC
        ''', (date_str,))
        
        rows = cursor.fetchall()
        conn.close()
        
        events = []
        for row in rows:
            event = CalendarEvent(
                id=row[0],
                title=row[1],
                description=row[2] or "",
                event_date=datetime.fromisoformat(row[3]).date(),
                priority=row[4] or "normal",
                created_at=datetime.fromisoformat(row[5]) if row[5] else datetime.now(),
                updated_at=datetime.fromisoformat(row[6]) if row[6] else datetime.now()
            )
            events.append(event)
        
        return events
    
    @staticmethod
    def get_upcoming_events(limit=2):
        conn = get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().date().isoformat()
        
        cursor.execute('''
            SELECT * FROM calendar_events 
            WHERE event_date >= ?
            ORDER BY event_date ASC, created_at ASC
            LIMIT ?
        ''', (today, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        events = []
        for row in rows:
            event = CalendarEvent(
                id=row[0],
                title=row[1],
                description=row[2] or "",
                event_date=datetime.fromisoformat(row[3]).date(),
                priority=row[4] or "normal",
                created_at=datetime.fromisoformat(row[5]) if row[5] else datetime.now(),
                updated_at=datetime.fromisoformat(row[6]) if row[6] else datetime.now()
            )
            events.append(event)
        
        return events
    
    def update(self, title=None, description=None, priority=None):
        if not self.id:
            return
        
        conn = get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
            self.title = title
        
        if description is not None:
            updates.append("description = ?")
            params.append(description)
            self.description = description
        
        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)
            self.priority = priority
        
        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            self.updated_at = datetime.now()
            
            params.append(self.id)
            
            query = f"UPDATE calendar_events SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            
            conn.commit()
        
        conn.close()
    
    def delete(self):
        if self.id:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM calendar_events WHERE id = ?', (self.id,))
            
            conn.commit()
            conn.close()
    
    def get_formatted_date(self):
        if isinstance(self.event_date, str):
            event_date = datetime.fromisoformat(self.event_date).date()
        else:
            event_date = self.event_date
        
        return event_date.strftime("%B %d, %Y")
    
    def get_priority_color(self):
        priority_colors = {
            'important': '#ff4444',        # Red
            'next_important': '#ffaa00',   # Yellow/Orange
            'normal': '#44aa44'            # Green
        }
        return priority_colors.get(self.priority, '#44aa44')
    
    def get_priority_display(self):
        priority_display = {
            'important': 'Important',
            'next_important': 'Next Important', 
            'normal': 'Normal'
        }
        return priority_display.get(self.priority, 'Normal')

class User:
  
    @staticmethod
    def get_profile():

        from database.db import get_setting
        
        profile = {
            'name': get_setting('user_name', 'User'),
            'email': get_setting('user_email', ''),
            'member_since': get_setting('member_since', ''),
            'profile_last_updated': get_setting('profile_last_updated', ''),
            'theme': get_setting('theme', 'light')
        }
        
        return profile
    
    @staticmethod
    def update_profile(name, email):
        from database.db import set_setting, get_setting
        
        set_setting('user_name', name)
        set_setting('user_email', email)
        set_setting('profile_last_updated', datetime.now().isoformat())
        
        if not get_setting('member_since', ''):
            set_setting('member_since', datetime.now().strftime('%Y-%m-%d'))
    
    @staticmethod
    def get_name():
        from database.db import get_setting
        return get_setting('user_name', 'User')
