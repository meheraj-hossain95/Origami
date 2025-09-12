"""
Desktop notifications functionality
"""
import os
import sys

def show_notification(title, message, timeout=5000):
    """Show a desktop notification"""
    try:
        # Try using plyer for cross-platform notifications
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            timeout=timeout
        )
    except ImportError:
        # Fallback to system-specific notifications
        if sys.platform == "win32":
            try:
                import win10toast
                toaster = win10toast.ToastNotifier()
                toaster.show_toast(title, message, duration=timeout//1000)
            except ImportError:
                # Last resort: print to console
                print(f"Notification: {title} - {message}")
        elif sys.platform == "darwin":  # macOS
            os.system(f'''osascript -e 'display notification "{message}" with title "{title}"' ''')
        elif sys.platform.startswith("linux"):
            os.system(f'notify-send "{title}" "{message}"')
        else:
            # Fallback: print to console
            print(f"Notification: {title} - {message}")

def show_success_notification(message):
    """Show a success notification"""
    show_notification("Success", message)

def show_warning_notification(message):
    """Show a warning notification"""
    show_notification("Warning", message)

def show_error_notification(message):
    """Show an error notification"""
    show_notification("Error", message)

def show_pomodoro_notification(session_type, duration):
    """Show pomodoro-specific notification"""
    if session_type == "work":
        show_notification("Pomodoro Timer", f"Work session complete! Time for a break.", 10000)
    elif session_type == "short_break":
        show_notification("Pomodoro Timer", f"Short break over! Ready to work?", 10000)
    elif session_type == "long_break":
        show_notification("Pomodoro Timer", f"Long break over! Time to get back to work!", 10000)

def show_reminder_notification(task, due_time):
    """Show a task reminder notification"""
    show_notification("Task Reminder", f"Don't forget: {task} (due {due_time})", 8000)
