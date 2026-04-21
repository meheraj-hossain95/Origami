import json
import os
from datetime import datetime
from typing import Callable, Dict, List, Optional
from enum import Enum

from database.models import PomodoroSession


class SessionType(Enum):
    WORK = "work"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


class PomodoroState(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"


class PomodoroTimer:
    _DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    _SETTINGS_FILE = os.path.join(_DATA_DIR, "pomodoro_settings.json")
    _STATS_FILE = os.path.join(_DATA_DIR, "pomodoro_stats.json")

    def __init__(self):
        self.settings: Dict = {
            "work_duration": 25,
            "short_break_duration": 5,
            "long_break_duration": 15,
            "sessions_until_long_break": 4,
            "auto_start_breaks": False,
            "auto_start_work": False,
        }

        self.current_session_type = SessionType.WORK
        self.session_count = 0
        self.current_session_id: Optional[int] = None
        self.task_description = ""

        self.state = PomodoroState.STOPPED
        self.time_remaining = self.settings["work_duration"] * 60
        self.total_time = self.settings["work_duration"] * 60

        self.on_tick_callback: Optional[Callable] = None
        self.on_session_complete_callback: Optional[Callable] = None
        self.on_state_change_callback: Optional[Callable] = None

        self.stats: Dict = {
            "total_sessions": 0,
            "completed_sessions": 0,
            "total_work_time": 0,
            "total_break_time": 0,
            "current_streak": 0,
            "best_streak": 0,
        }

        self.load_settings()
        self.load_stats()

    # ------------------------------------------------------------------
    # Session control
    # ------------------------------------------------------------------

    def start_session(self, task_description: str = "") -> bool:
        if self.state == PomodoroState.RUNNING:
            return False

        if self.state == PomodoroState.STOPPED:
            self.task_description = task_description

            if self.current_session_type == SessionType.WORK:
                self.current_session_id = PomodoroSession.create(
                    self.settings["work_duration"], task_description
                )

            self.reset_timer_for_current_session()

        self.state = PomodoroState.RUNNING
        self._notify_state_change()
        return True

    def pause_session(self) -> bool:
        if self.state == PomodoroState.RUNNING:
            self.state = PomodoroState.PAUSED
            self._notify_state_change()
            return True
        return False

    def resume_session(self) -> bool:
        if self.state == PomodoroState.PAUSED:
            self.state = PomodoroState.RUNNING
            self._notify_state_change()
            return True
        return False

    def stop_session(self) -> bool:
        self.state = PomodoroState.STOPPED
        self.current_session_id = None
        self.task_description = ""
        self.reset_timer_for_current_session()
        self._notify_state_change()
        return True

    def tick(self) -> bool:
        if self.state != PomodoroState.RUNNING:
            return False

        self.time_remaining -= 1

        if self.on_tick_callback:
            self.on_tick_callback(self.time_remaining, self.total_time)

        if self.time_remaining <= 0:
            self._complete_current_session()
            return True

        return False

    # ------------------------------------------------------------------
    # Internal session handling
    # ------------------------------------------------------------------

    def _complete_current_session(self):
        self.state = PomodoroState.FINISHED

        if self.current_session_type == SessionType.WORK:
            if self.current_session_id:
                PomodoroSession.complete_session(self.current_session_id)

            self.session_count += 1
            self.stats["completed_sessions"] += 1
            self.stats["total_work_time"] += self.settings["work_duration"]
            self.stats["current_streak"] += 1

            if self.stats["current_streak"] > self.stats["best_streak"]:
                self.stats["best_streak"] = self.stats["current_streak"]

        elif self.current_session_type in (SessionType.SHORT_BREAK, SessionType.LONG_BREAK):
            duration = (
                self.settings["short_break_duration"]
                if self.current_session_type == SessionType.SHORT_BREAK
                else self.settings["long_break_duration"]
            )
            self.stats["total_break_time"] += duration

        next_session = self._get_next_session_type()

        if self.on_session_complete_callback:
            self.on_session_complete_callback(
                self.current_session_type, next_session, self.session_count
            )

        self.current_session_type = next_session
        self.reset_timer_for_current_session()
        self.state = PomodoroState.STOPPED

        self.save_stats()
        self._notify_state_change()

    def _get_next_session_type(self) -> SessionType:
        if self.current_session_type != SessionType.WORK:
            return SessionType.WORK

        if self.session_count % self.settings["sessions_until_long_break"] == 0:
            return SessionType.LONG_BREAK

        return SessionType.SHORT_BREAK

    def reset_timer_for_current_session(self):
        duration_map = {
            SessionType.WORK: self.settings["work_duration"],
            SessionType.SHORT_BREAK: self.settings["short_break_duration"],
            SessionType.LONG_BREAK: self.settings["long_break_duration"],
        }
        duration = duration_map[self.current_session_type]
        self.time_remaining = duration * 60
        self.total_time = duration * 60

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_current_session_info(self) -> Dict:
        return {
            "type": self.current_session_type.value,
            "state": self.state.value,
            "time_remaining": self.time_remaining,
            "total_time": self.total_time,
            "progress_percentage": (
                (self.total_time - self.time_remaining) / self.total_time
            ) * 100,
            "session_count": self.session_count,
            "task_description": self.task_description,
            "sessions_until_long_break": (
                self.settings["sessions_until_long_break"]
                - (self.session_count % self.settings["sessions_until_long_break"])
            ),
        }

    def get_time_display(self) -> tuple:
        return self.time_remaining // 60, self.time_remaining % 60

    def get_statistics(self) -> Dict:
        return self.stats.copy()

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def update_settings(self, new_settings: Dict) -> bool:
        """Validate and apply new settings. Returns False on any validation failure."""
        _DURATION_KEYS = {"work_duration", "short_break_duration", "long_break_duration"}
        _BOOL_KEYS = {"auto_start_breaks", "auto_start_work"}
        _VALID_KEYS = _DURATION_KEYS | _BOOL_KEYS | {"sessions_until_long_break"}

        for key, value in new_settings.items():
            if key not in _VALID_KEYS:
                continue
            if key in _DURATION_KEYS:
                if not isinstance(value, int) or not (1 <= value <= 120):
                    return False
            elif key == "sessions_until_long_break":
                if not isinstance(value, int) or not (2 <= value <= 10):
                    return False
            elif key in _BOOL_KEYS:
                if not isinstance(value, bool):
                    return False

        for key, value in new_settings.items():
            if key in _VALID_KEYS:
                self.settings[key] = value

        if self.state == PomodoroState.STOPPED:
            self.reset_timer_for_current_session()

        self.save_settings()
        return True

    # ------------------------------------------------------------------
    # State resets
    # ------------------------------------------------------------------

    def reset_session_count(self):
        self.session_count = 0
        self.current_session_type = SessionType.WORK
        self.reset_timer_for_current_session()
        if self.state == PomodoroState.STOPPED:
            self._notify_state_change()

    def reset_statistics(self):
        self.stats = {
            "total_sessions": 0,
            "completed_sessions": 0,
            "total_work_time": 0,
            "total_break_time": 0,
            "current_streak": 0,
            "best_streak": 0,
        }
        self.save_stats()

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def set_callbacks(
        self,
        on_tick: Optional[Callable] = None,
        on_session_complete: Optional[Callable] = None,
        on_state_change: Optional[Callable] = None,
    ):
        if on_tick:
            self.on_tick_callback = on_tick
        if on_session_complete:
            self.on_session_complete_callback = on_session_complete
        if on_state_change:
            self.on_state_change_callback = on_state_change

    def _notify_state_change(self):
        if self.on_state_change_callback:
            self.on_state_change_callback(self.state, self.get_current_session_info())

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load_settings(self):
        try:
            if os.path.exists(self._SETTINGS_FILE):
                with open(self._SETTINGS_FILE, "r", encoding="utf-8") as f:
                    self.settings.update(json.load(f))
        except Exception as e:
            print(f"Error loading Pomodoro settings: {e}")

    def save_settings(self):
        try:
            os.makedirs(self._DATA_DIR, exist_ok=True)
            with open(self._SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving Pomodoro settings: {e}")

    def load_stats(self):
        try:
            if os.path.exists(self._STATS_FILE):
                with open(self._STATS_FILE, "r", encoding="utf-8") as f:
                    self.stats.update(json.load(f))
        except Exception as e:
            print(f"Error loading Pomodoro statistics: {e}")

    def save_stats(self):
        try:
            os.makedirs(self._DATA_DIR, exist_ok=True)
            stats_data = {**self.stats, "last_updated": datetime.now().isoformat()}
            with open(self._STATS_FILE, "w", encoding="utf-8") as f:
                json.dump(stats_data, f, indent=2)
        except Exception as e:
            print(f"Error saving Pomodoro statistics: {e}")


class PomodoroSessionHistory:
    @staticmethod
    def get_recent_sessions(limit: int = 10) -> List[Dict]:
        try:
            return [
                {
                    "id": s[0],
                    "duration": s[1],
                    "task_description": s[2] or "No description",
                    "completed": bool(s[3]),
                    "started_at": s[4],
                    "ended_at": s[5],
                }
                for s in PomodoroSession.get_recent_sessions(limit)
            ]
        except Exception as e:
            print(f"Error getting recent sessions: {e}")
            return []

    @staticmethod
    def get_daily_stats(date: datetime = None) -> Dict:
        if date is None:
            date = datetime.now()
        return {
            "date": date.strftime("%Y-%m-%d"),
            "completed_sessions": 0,
            "total_work_time": 0,
            "total_break_time": 0,
            "productivity_score": 0,
        }

    @staticmethod
    def get_weekly_stats() -> Dict:
        return {
            "week_start": datetime.now().strftime("%Y-%m-%d"),
            "total_sessions": 0,
            "total_work_time": 0,
            "average_daily_sessions": 0,
            "most_productive_day": "Monday",
        }


class PomodoroNotification:
    @staticmethod
    def show_session_complete(session_type: SessionType, next_session: SessionType):
        try:
            from utils.notifications import show_notification

            if session_type == SessionType.WORK:
                message = (
                    "Great work! Time for a long break."
                    if next_session == SessionType.LONG_BREAK
                    else "Well done! Take a short break."
                )
                show_notification("Pomodoro Complete!", message)
            else:
                show_notification("Break Over!", "Ready to get back to work?")
        except Exception as e:
            print(f"Error showing notification: {e}")

    @staticmethod
    def show_reminder(message: str):
        try:
            from utils.notifications import show_notification

            show_notification("Pomodoro Reminder", message)
        except Exception as e:
            print(f"Error showing reminder: {e}")