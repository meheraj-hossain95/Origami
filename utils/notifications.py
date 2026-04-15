import sys

def show_notification(title, message, timeout=5):
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            timeout=timeout
        )
    except Exception:
        print(f"{title}: {message}")


def show_success(message):
    show_notification("Success", message)


def show_warning(message):
    show_notification("Warning", message)


def show_error(message):
    show_notification("Error", message)


def show_pomodoro(session_type):
    messages = {
        "work": "Work session complete! Take a break.",
        "short_break": "Break over! Back to work.",
        "long_break": "Long break over! Resume work."
    }
    show_notification("Pomodoro", messages.get(session_type, "Session done"))


def show_reminder(task, due_time):
    show_notification("Reminder", f"{task} (due {due_time})")