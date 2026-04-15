"""
Pomodoro Timer Logic - Handles all business logic for the Pomodoro timer
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from enum import Enum
from database.models import PomodoroSession

class SessionType(Enum):
    """Pomodoro session types"""
    WORK = "work"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"

class PomodoroState(Enum):
    """Pomodoro timer states"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"

class PomodoroTimer:
    """Manages Pomodoro timer functionality and state"""
    
    def __init__(self):
        # Default settings (in minutes)
        self.settings = {
            'work_duration': 25,
            'short_break_duration': 5,
            'long_break_duration': 15,
            'sessions_until_long_break': 4,
            'auto_start_breaks': False,
            'auto_start_work': False
        }
        
        # Current session state
        self.current_session_type = SessionType.WORK
        self.session_count = 0
        self.current_session_id = None
        self.task_description = ""
        
        # Timer state
        self.state = PomodoroState.STOPPED
        self.time_remaining = self.settings['work_duration'] * 60  # in seconds
        self.total_time = self.settings['work_duration'] * 60
        
        # Callbacks
        self.on_tick_callback: Optional[Callable] = None
        self.on_session_complete_callback: Optional[Callable] = None
        self.on_state_change_callback: Optional[Callable] = None
        
        # Statistics
        self.stats = {
            'total_sessions': 0,
            'completed_sessions': 0,
            'total_work_time': 0,  # in minutes
            'total_break_time': 0,  # in minutes
            'current_streak': 0,
            'best_streak': 0
        }
        
        self.load_settings()
        self.load_stats()
    
    def start_session(self, task_description: str = "") -> bool:
        """Start a new Pomodoro session"""
        if self.state == PomodoroState.RUNNING:
            return False
        
        if self.state == PomodoroState.STOPPED:
            self.task_description = task_description
            
            # Create new session in database for work sessions
            if self.current_session_type == SessionType.WORK:
                duration = self.settings['work_duration']
                self.current_session_id = PomodoroSession.create(duration, task_description)
            
            # Set timer for current session type
            self.reset_timer_for_current_session()
        
        self.state = PomodoroState.RUNNING
        self._notify_state_change()
        return True
    
    def pause_session(self) -> bool:
        """Pause the current session"""
        if self.state == PomodoroState.RUNNING:
            self.state = PomodoroState.PAUSED
            self._notify_state_change()
            return True
        return False
    
    def resume_session(self) -> bool:
        """Resume a paused session"""
        if self.state == PomodoroState.PAUSED:
            self.state = PomodoroState.RUNNING
            self._notify_state_change()
            return True
        return False
    
    def stop_session(self) -> bool:
        """Stop the current session"""
        self.state = PomodoroState.STOPPED
        self.current_session_id = None
        self.task_description = ""
        self.reset_timer_for_current_session()
        self._notify_state_change()
        return True
    
    def tick(self) -> bool:
        """Process one second tick of the timer"""
        if self.state != PomodoroState.RUNNING:
            return False
        
        self.time_remaining -= 1
        
        # Notify UI of time update
        if self.on_tick_callback:
            self.on_tick_callback(self.time_remaining, self.total_time)
        
        # Check if session is complete
        if self.time_remaining <= 0:
            self._complete_current_session()
            return True
        
        return False
    
    def _complete_current_session(self):
        """Handle completion of current session"""
        self.state = PomodoroState.FINISHED
        
        # Update statistics and database
        if self.current_session_type == SessionType.WORK:
            if self.current_session_id:
                PomodoroSession.complete_session(self.current_session_id)
            
            self.session_count += 1
            self.stats['completed_sessions'] += 1
            self.stats['total_work_time'] += self.settings['work_duration']
            self.stats['current_streak'] += 1
            
            if self.stats['current_streak'] > self.stats['best_streak']:
                self.stats['best_streak'] = self.stats['current_streak']
        
        elif self.current_session_type in [SessionType.SHORT_BREAK, SessionType.LONG_BREAK]:
            duration = (self.settings['short_break_duration'] 
                       if self.current_session_type == SessionType.SHORT_BREAK 
                       else self.settings['long_break_duration'])
            self.stats['total_break_time'] += duration
        
        # Determine next session type
        next_session = self._get_next_session_type()
        
        # Notify completion
        if self.on_session_complete_callback:
            self.on_session_complete_callback(
                self.current_session_type,
                next_session,
                self.session_count
            )
        
        # Switch to next session
        self.current_session_type = next_session
        self.reset_timer_for_current_session()
        self.state = PomodoroState.STOPPED
        
        self.save_stats()
        self._notify_state_change()
    
    def _get_next_session_type(self) -> SessionType:
        """Determine the next session type based on current progress"""
        if self.current_session_type == SessionType.WORK:
            # After work, determine break type
            if self.session_count % self.settings['sessions_until_long_break'] == 0:
                return SessionType.LONG_BREAK
            else:
                return SessionType.SHORT_BREAK
        else:
            # After any break, return to work
            return SessionType.WORK
    
    def reset_timer_for_current_session(self):
        """Reset timer for the current session type"""
        if self.current_session_type == SessionType.WORK:
            duration = self.settings['work_duration']
        elif self.current_session_type == SessionType.SHORT_BREAK:
            duration = self.settings['short_break_duration']
        else:  # LONG_BREAK
            duration = self.settings['long_break_duration']
        
        self.time_remaining = duration * 60
        self.total_time = duration * 60
    
    def get_current_session_info(self) -> Dict:
        """Get information about the current session"""
        return {
            'type': self.current_session_type.value,
            'state': self.state.value,
            'time_remaining': self.time_remaining,
            'total_time': self.total_time,
            'progress_percentage': ((self.total_time - self.time_remaining) / self.total_time) * 100,
            'session_count': self.session_count,
            'task_description': self.task_description,
            'sessions_until_long_break': self.settings['sessions_until_long_break'] - (self.session_count % self.settings['sessions_until_long_break'])
        }
    
    def get_time_display(self) -> tuple:
        """Get formatted time display (minutes, seconds)"""
        minutes = self.time_remaining // 60
        seconds = self.time_remaining % 60
        return minutes, seconds
    
    def update_settings(self, new_settings: Dict) -> bool:
        """Update Pomodoro settings"""
        valid_keys = {
            'work_duration', 'short_break_duration', 'long_break_duration',
            'sessions_until_long_break', 'auto_start_breaks', 'auto_start_work'
        }
        
        # Validate settings
        for key, value in new_settings.items():
            if key not in valid_keys:
                continue
            
            if key in ['work_duration', 'short_break_duration', 'long_break_duration']:
                if not isinstance(value, int) or value < 1 or value > 120:
                    return False
            elif key == 'sessions_until_long_break':
                if not isinstance(value, int) or value < 2 or value > 10:
                    return False
            elif key in ['auto_start_breaks', 'auto_start_work']:
                if not isinstance(value, bool):
                    return False
        
        # Apply valid settings
        for key, value in new_settings.items():
            if key in valid_keys:
                self.settings[key] = value
        
        # Reset timer if stopped
        if self.state == PomodoroState.STOPPED:
            self.reset_timer_for_current_session()
        
        self.save_settings()
        return True
    
    def get_statistics(self) -> Dict:
        """Get Pomodoro statistics"""
        return self.stats.copy()
    
    def reset_session_count(self):
        """Reset the current session count (useful for starting fresh)"""
        self.session_count = 0
        self.current_session_type = SessionType.WORK
        self.reset_timer_for_current_session()
        if self.state == PomodoroState.STOPPED:
            self._notify_state_change()
    
    def reset_statistics(self):
        """Reset all statistics"""
        self.stats = {
            'total_sessions': 0,
            'completed_sessions': 0,
            'total_work_time': 0,
            'total_break_time': 0,
            'current_streak': 0,
            'best_streak': 0
        }
        self.save_stats()
    
    def set_callbacks(self, on_tick=None, on_session_complete=None, on_state_change=None):
        """Set callback functions for timer events"""
        if on_tick:
            self.on_tick_callback = on_tick
        if on_session_complete:
            self.on_session_complete_callback = on_session_complete
        if on_state_change:
            self.on_state_change_callback = on_state_change
    
    def _notify_state_change(self):
        """Notify of state change"""
        if self.on_state_change_callback:
            self.on_state_change_callback(self.state, self.get_current_session_info())
    
    def load_settings(self):
        """Load settings from file"""
        try:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
            settings_file = os.path.join(data_dir, 'pomodoro_settings.json')
            
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
        except Exception as e:
            print(f"Error loading Pomodoro settings: {e}")
    
    def save_settings(self):
        """Save settings to file"""
        try:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            settings_file = os.path.join(data_dir, 'pomodoro_settings.json')
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving Pomodoro settings: {e}")
    
    def load_stats(self):
        """Load statistics from file"""
        try:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
            stats_file = os.path.join(data_dir, 'pomodoro_stats.json')
            
            if os.path.exists(stats_file):
                with open(stats_file, 'r', encoding='utf-8') as f:
                    saved_stats = json.load(f)
                    self.stats.update(saved_stats)
        except Exception as e:
            print(f"Error loading Pomodoro statistics: {e}")
    
    def save_stats(self):
        """Save statistics to file"""
        try:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            stats_file = os.path.join(data_dir, 'pomodoro_stats.json')
            
            stats_data = self.stats.copy()
            stats_data['last_updated'] = datetime.now().isoformat()
            
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats_data, f, indent=2)
        except Exception as e:
            print(f"Error saving Pomodoro statistics: {e}")

class PomodoroSessionHistory:
    """Manages Pomodoro session history and analytics"""
    
    @staticmethod
    def get_recent_sessions(limit: int = 10) -> List[Dict]:
        """Get recent Pomodoro sessions"""
        try:
            sessions = PomodoroSession.get_recent_sessions(limit)
            
            formatted_sessions = []
            for session in sessions:
                formatted_session = {
                    'id': session[0],
                    'duration': session[1],
                    'task_description': session[2] or "No description",
                    'completed': bool(session[3]),
                    'started_at': session[4],
                    'ended_at': session[5]
                }
                formatted_sessions.append(formatted_session)
            
            return formatted_sessions
        except Exception as e:
            print(f"Error getting recent sessions: {e}")
            return []
    
    @staticmethod
    def get_daily_stats(date: datetime = None) -> Dict:
        """Get statistics for a specific day"""
        if date is None:
            date = datetime.now()
        
        # This would need database queries with date filtering
        # For now, return basic stats
        return {
            'date': date.strftime('%Y-%m-%d'),
            'completed_sessions': 0,
            'total_work_time': 0,
            'total_break_time': 0,
            'productivity_score': 0
        }
    
    @staticmethod
    def get_weekly_stats() -> Dict:
        """Get statistics for the current week"""
        # This would aggregate daily stats
        return {
            'week_start': datetime.now().strftime('%Y-%m-%d'),
            'total_sessions': 0,
            'total_work_time': 0,
            'average_daily_sessions': 0,
            'most_productive_day': 'Monday'
        }

class PomodoroNotification:
    """Handles Pomodoro timer notifications"""
    
    @staticmethod
    def show_session_complete(session_type: SessionType, next_session: SessionType):
        """Show notification when a session completes"""
        try:
            from utils.notifications import show_notification
            
            if session_type == SessionType.WORK:
                if next_session == SessionType.LONG_BREAK:
                    show_notification(
                        "Pomodoro Complete!", 
                        "Great work! Time for a long break."
                    )
                else:
                    show_notification(
                        "Pomodoro Complete!", 
                        "Well done! Take a short break."
                    )
            else:
                show_notification(
                    "Break Over!", 
                    "Ready to get back to work?"
                )
        except Exception as e:
            print(f"Error showing notification: {e}")
    
    @staticmethod
    def show_reminder(message: str):
        """Show a general reminder notification"""
        try:
            from utils.notifications import show_notification
            show_notification("Pomodoro Reminder", message)
        except Exception as e:
            print(f"Error showing reminder: {e}")
