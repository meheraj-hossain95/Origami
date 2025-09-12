"""
Miscellaneous helper functions used across the app
"""
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

def format_datetime(dt_string: str, format_type: str = "display") -> str:
    """Format datetime string for display"""
    try:
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        
        if format_type == "display":
            return dt.strftime("%Y-%m-%d %H:%M")
        elif format_type == "date_only":
            return dt.strftime("%Y-%m-%d")
        elif format_type == "time_only":
            return dt.strftime("%H:%M")
        elif format_type == "friendly":
            now = datetime.now()
            diff = now - dt.replace(tzinfo=None)
            
            if diff.days > 0:
                return f"{diff.days} days ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hours ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minutes ago"
            else:
                return "Just now"
        else:
            return dt_string
    except Exception:
        return dt_string

def calculate_percentage(current: float, target: float) -> float:
    """Calculate percentage with safe division"""
    if target == 0:
        return 0
    return min((current / target) * 100, 100)

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    import re
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename

def ensure_directory_exists(directory_path: str):
    """Ensure directory exists, create if it doesn't"""
    os.makedirs(directory_path, exist_ok=True)

def read_json_file(file_path: str) -> Dict[str, Any]:
    """Read JSON file safely"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def write_json_file(file_path: str, data: Dict[str, Any]):
    """Write JSON file safely"""
    try:
        ensure_directory_exists(os.path.dirname(file_path))
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise Exception(f"Failed to write JSON file: {str(e)}")

def validate_email(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generate_uuid() -> str:
    """Generate a UUID string"""
    import uuid
    return str(uuid.uuid4())

def get_week_boundaries(date: datetime = None) -> tuple:
    """Get start and end of week for given date"""
    if date is None:
        date = datetime.now()
    
    # Get Monday of the week
    start_of_week = date - timedelta(days=date.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get Sunday of the week
    end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    return start_of_week, end_of_week

def parse_duration_string(duration_str: str) -> int:
    """Parse duration string to minutes (e.g., '25m', '1h 30m', '90')"""
    try:
        duration_str = duration_str.lower().strip()
        total_minutes = 0
        
        # Handle different formats
        if 'h' in duration_str and 'm' in duration_str:
            # Format: "1h 30m"
            parts = duration_str.split()
            for part in parts:
                if 'h' in part:
                    hours = int(part.replace('h', ''))
                    total_minutes += hours * 60
                elif 'm' in part:
                    minutes = int(part.replace('m', ''))
                    total_minutes += minutes
        elif 'h' in duration_str:
            # Format: "1h"
            hours = int(duration_str.replace('h', ''))
            total_minutes = hours * 60
        elif 'm' in duration_str:
            # Format: "25m"
            total_minutes = int(duration_str.replace('m', ''))
        else:
            # Assume minutes if no unit
            total_minutes = int(duration_str)
        
        return max(total_minutes, 1)  # Minimum 1 minute
    except Exception:
        return 25  # Default to 25 minutes

def format_duration(minutes: int) -> str:
    """Format minutes to human-readable duration"""
    if minutes < 60:
        return f"{minutes}m"
    else:
        hours = minutes // 60
        remaining_minutes = minutes % 60
        if remaining_minutes == 0:
            return f"{hours}h"
        else:
            return f"{hours}h {remaining_minutes}m"

def get_color_for_priority(priority: int) -> str:
    """Get color code for priority level"""
    colors = {
        1: "#4CAF50",  # Green - Low priority
        2: "#8BC34A",  # Light Green
        3: "#FF9800",  # Orange - Medium priority
        4: "#FF5722",  # Deep Orange
        5: "#F44336"   # Red - High priority
    }
    return colors.get(priority, "#4CAF50")

def get_mood_emoji(mood_rating: int) -> str:
    """Get emoji for mood rating"""
    moods = {
        1: "😢",
        2: "😔", 
        3: "😐",
        4: "😊",
        5: "😄"
    }
    return moods.get(mood_rating, "😐")

def calculate_streak(dates: List[datetime]) -> int:
    """Calculate consecutive streak from list of dates"""
    if not dates:
        return 0
    
    # Sort dates in descending order
    sorted_dates = sorted([d.date() if isinstance(d, datetime) else d for d in dates], reverse=True)
    
    streak = 0
    expected_date = datetime.now().date()
    
    for date in sorted_dates:
        if date == expected_date or date == expected_date - timedelta(days=streak):
            streak += 1
            expected_date = date
        else:
            break
    
    return streak

def export_data_to_csv(data: List[Dict], filename: str):
    """Export data to CSV file"""
    try:
        import csv
        
        if not data:
            return
        
        ensure_directory_exists(os.path.dirname(filename))
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in data:
                writer.writerow(row)
    except Exception as e:
        raise Exception(f"Failed to export CSV: {str(e)}")

def backup_database(db_path: str, backup_dir: str):
    """Create a backup of the database"""
    try:
        import shutil
        
        ensure_directory_exists(backup_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        shutil.copy2(db_path, backup_path)
        return backup_path
    except Exception as e:
        raise Exception(f"Backup failed: {str(e)}")
