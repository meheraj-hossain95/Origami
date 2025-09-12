"""
Configuration file for Origami application
"""
import os
import sys

# Get the application directory (works for both script and executable)
if getattr(sys, 'frozen', False):
    # Running as executable
    app_dir = os.path.dirname(sys.executable)
else:
    # Running as script
    app_dir = os.path.dirname(__file__)

# Database configuration
DB_PATH = os.path.join(app_dir, 'data', 'origami.db')

# Default settings
DEFAULT_THEME = 'dark'  # 'dark' or 'light'
DEFAULT_POMODORO_DURATION = 25  # minutes
DEFAULT_SHORT_BREAK = 5  # minutes
DEFAULT_LONG_BREAK = 15  # minutes

# Encryption settings
ENCRYPTION_KEY_FILE = os.path.join(app_dir, 'data', 'key.key')

# AI settings
AI_SUGGESTIONS_ENABLED = True
MIN_ENTRIES_FOR_SUGGESTIONS = 5

# Notification settings
NOTIFICATIONS_ENABLED = True

# Create data directory if it doesn't exist
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
