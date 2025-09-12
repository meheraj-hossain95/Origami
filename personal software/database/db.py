"""
Database connection and initialization
"""
import sqlite3
import os
from datetime import datetime
import config

def get_connection():
    """Get database connection"""
    return sqlite3.connect(config.DB_PATH)

def initialize_database():
    """Initialize database tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create todos table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN DEFAULT FALSE,
            priority INTEGER DEFAULT 1,
            due_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create journal_entries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            encrypted_content BLOB,
            is_encrypted BOOLEAN DEFAULT FALSE,
            mood_rating INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create pomodoro_sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pomodoro_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            duration INTEGER NOT NULL,
            task_description TEXT,
            completed BOOLEAN DEFAULT FALSE,
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            ended_at TEXT
        )
    ''')
    
    # Create calendar_events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            event_date TEXT NOT NULL,
            priority TEXT DEFAULT 'normal',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create app_settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # Initialize default settings
    set_default_settings()

def set_default_settings():
    """Set default application settings"""
    settings = {
        'theme': config.DEFAULT_THEME,
        'pomodoro_duration': str(config.DEFAULT_POMODORO_DURATION),
        'short_break': str(config.DEFAULT_SHORT_BREAK),
        'long_break': str(config.DEFAULT_LONG_BREAK),
        'notifications_enabled': str(config.NOTIFICATIONS_ENABLED),
        'user_name': 'User',
        'username': 'User',
        'display_handle': '',
        'user_email': '',
        'member_since': datetime.now().strftime('%Y-%m-%d'),
        'journal_password_hash': '',
        'journal_password_enabled': 'false',
        'journal_lockout_time': '0'
    }
    
    conn = get_connection()
    cursor = conn.cursor()
    
    for key, value in settings.items():
        cursor.execute('''
            INSERT OR IGNORE INTO app_settings (key, value)
            VALUES (?, ?)
        ''', (key, value))
    
    conn.commit()
    conn.close()

def get_setting(key, default=None):
    """Get application setting"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT value FROM app_settings WHERE key = ?', (key,))
    result = cursor.fetchone()
    
    conn.close()
    
    return result[0] if result else default

def set_setting(key, value):
    """Set application setting"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO app_settings (key, value, updated_at)
        VALUES (?, ?, ?)
    ''', (key, value, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
