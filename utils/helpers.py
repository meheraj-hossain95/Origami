import os, json, re, uuid, csv, shutil
from datetime import datetime, timedelta
from typing import List, Dict, Any


def format_datetime(dt_string: str, format_type: str = "display") -> str:
    try:
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))

        if format_type == "display":
            return dt.strftime("%Y-%m-%d %H:%M")
        if format_type == "date_only":
            return dt.strftime("%Y-%m-%d")
        if format_type == "time_only":
            return dt.strftime("%H:%M")
        if format_type == "friendly":
            diff = datetime.now() - dt.replace(tzinfo=None)
            if diff.days:
                return f"{diff.days} days ago"
            if diff.seconds >= 3600:
                return f"{diff.seconds // 3600} hours ago"
            if diff.seconds >= 60:
                return f"{diff.seconds // 60} minutes ago"
            return "Just now"
        return dt_string
    except Exception:
        return dt_string


def calculate_percentage(current: float, target: float) -> float:
    return 0 if target == 0 else min((current / target) * 100, 100)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    return text if len(text) <= max_length else text[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename).strip(' .')
    return filename[:200]


def ensure_directory_exists(path: str):
    os.makedirs(path, exist_ok=True)


def read_json_file(path: str) -> Dict[str, Any]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def write_json_file(path: str, data: Dict[str, Any]):
    ensure_directory_exists(os.path.dirname(path))
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise Exception(f"JSON write failed: {e}")


def validate_email(email: str) -> bool:
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email) is not None


def generate_uuid() -> str:
    return str(uuid.uuid4())


def get_week_boundaries(date: datetime = None):
    date = date or datetime.now()
    start = (date - timedelta(days=date.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    return start, end


def parse_duration_string(s: str) -> int:
    try:
        s = s.lower().strip()
        h = m = 0

        if 'h' in s:
            h = int(s.split('h')[0].strip())
        if 'm' in s:
            m = int(s.split('m')[0].split()[-1])

        total = h * 60 + m if ('h' in s or 'm' in s) else int(s)
        return max(total, 1)
    except Exception:
        return 25


def format_duration(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    return f"{h}h" if m == 0 and h else f"{h}h {m}m" if h else f"{m}m"


def get_color_for_priority(priority: int) -> str:
    return {
        1: "#4CAF50",
        2: "#8BC34A",
        3: "#FF9800",
        4: "#FF5722",
        5: "#F44336"
    }.get(priority, "#4CAF50")


def get_mood_emoji(mood: int) -> str:
    return {1: "😢", 2: "😔", 3: "😐", 4: "😊", 5: "😄"}.get(mood, "😐")


def calculate_streak(dates: List[datetime]) -> int:
    if not dates:
        return 0

    dates = sorted({d.date() for d in dates}, reverse=True)
    streak, today = 0, datetime.now().date()

    for d in dates:
        if d == today - timedelta(days=streak):
            streak += 1
        else:
            break
    return streak


def export_data_to_csv(data: List[Dict], filename: str):
    if not data:
        return

    ensure_directory_exists(os.path.dirname(filename))
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    except Exception as e:
        raise Exception(f"CSV export failed: {e}")


def backup_database(db_path: str, backup_dir: str) -> str:
    ensure_directory_exists(backup_dir)
    try:
        name = f"backup_{datetime.now():%Y%m%d_%H%M%S}.db"
        path = os.path.join(backup_dir, name)
        shutil.copy2(db_path, path)
        return path
    except Exception as e:
        raise Exception(f"Backup failed: {e}")