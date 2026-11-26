"""Which kinds of things may send a notification. Stored as 0/1 settings."""

NOTIFY_DEFAULTS = {"notify_tasks": 1, "notify_focus": 1, "notify_events": 0, "notify_timetable": 0}
KIND_KEYS = {"task": "notify_tasks", "event": "notify_events", "slot": "notify_timetable"}
