<p align="center">
  <img src="origami/assets/icon.png" alt="Origami" width="11"/>
</p>

<h1 align="center">Origami</h1>

<p align="center">
  A quiet desktop home for your tasks, habits, schedule and focus time.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Qt-PySide6-41CD52?style=flat-square&logo=qt&logoColor=white" alt="PySide6">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square" alt="Platform">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-F7C948?style=flat-square" alt="MIT License"></a>
</p>

<p align="center">
  <img src="docs/dashboard-light.png" alt="Origami dashboard" width="720"/>
</p>

Most productivity apps want to be your whole operating system. Origami just wants to be the window you open in the morning. It shows what's due today, which habits you've kept up, what's coming this week and how much focused work you've actually done. Then it gets out of the way.

Everything stays on your computer in a single local database. You don't need an account and nothing syncs to anyone's cloud.

## What's inside

**Dashboard.** Today's date, a quote to start on, your next tasks, upcoming events, today's reminders and habit check-offs, all on one screen.

**Tasks.** One list, sorted by priority. Add notes and a reminder to any task. Finished tasks move to a Completed section so they're out of your way but still there if you need them.

**Habits.** Check a habit off for today, keep your streak going, and look back over the month to see how consistent you've really been.

**Calendar.** A month view with color-coded priorities, optional times, reminders and events that repeat weekly.

**Timetable.** A Monday-to-Sunday grid for the things that happen every week, such as classes, gym sessions and meetings. Each block can carry a location and a reminder.

**Focus.** A Pomodoro timer with focus, short-break and custom modes. Sessions are logged automatically, and a weekly chart shows where your hours went.

**Notifications.** Themed reminder pop-ups with a sound of your choice, and a switch for each kind: tasks, Pomodoro, calendar events and timetable. They keep arriving from the system tray after you close the window.

**Settings.** Light, dark or system theme, eight accent colors, four text sizes and a 24-hour or 12-hour clock. Your data can be exported to JSON in one click.

**And the small things:** a `Ctrl+K` command palette for jumping anywhere, keyboard shortcuts for every page, and only ever one copy of the app running at a time.

## A closer look

<table>
  <tr>
    <td><img src="docs/tasks-light.png" alt="Tasks"/></td>
    <td><img src="docs/habits-light.png" alt="Habits"/></td>
  </tr>
  <tr>
    <td align="center"><sub>Tasks</sub></td>
    <td align="center"><sub>Habits</sub></td>
  </tr>
  <tr>
    <td><img src="docs/calendar-light.png" alt="Calendar"/></td>
    <td><img src="docs/timetable-light.png" alt="Timetable"/></td>
  </tr>
  <tr>
    <td align="center"><sub>Calendar</sub></td>
    <td align="center"><sub>Timetable</sub></td>
  </tr>
  <tr>
    <td><img src="docs/settings-dark.png" alt="Settings"/></td>
    <td><img src="docs/focus-dark.png" alt="Focus timer in dark mode"/></td>
  </tr>
  <tr>
    <td align="center"><sub>Settings</sub></td>
    <td align="center"><sub>Focus</sub></td>
  </tr>
</table>

## Download for Windows

Get `Origami-1.0.0-Windows-x64.zip` from the [Releases page](https://github.com/meheraj-hossain95/Origami/releases), extract it and run `Origami-1.0.0-Setup.exe`. No Python needed. Prefer not to install? Run `Origami-Portable\Origami.exe` instead.

Uninstall from **Settings → Apps → Installed apps**. You'll be asked whether to keep your data.

## Running from source

You'll need Python 3.10 or newer.

```bash
git clone https://github.com/meheraj-hossain95/origami.git
cd origami

python -m venv .venv
.venv\Scripts\activate        # macOS / Linux: source .venv/bin/activate

pip install -r requirements.txt
python -m origami
```

You can also install it as a package with `pip install .` and launch it with the `origami` command.

Only one copy runs at a time: launching Origami again brings the open window forward.

## Keyboard shortcuts

| Shortcut | Action |
| --- | --- |
| `Ctrl+K` | Open the command palette |
| `Ctrl+1` to `Ctrl+6` | Jump to Dashboard, Tasks, Habits, Calendar, Timetable or Focus |
| `Ctrl+N` | New task |
| `Ctrl+,` | Settings |
| `Space` | Start or pause the timer (on the Focus page) |

## Where your data lives

Origami keeps everything in one SQLite file inside your system's app-data folder (`%APPDATA%\Origami` on Windows). **Settings → Open folder** takes you straight there. To keep the data somewhere else, such as a synced folder, set the `ORIGAMI_HOME` environment variable before you launch the app.

If you used Origami 1.x, your old tasks, events and settings are imported automatically the first time you run this version.

## Project layout

```
origami/
├── app.py          startup and wiring
├── store.py        SQLite data layer; emits a signal whenever something changes
├── timer.py        drift-free Pomodoro timer
├── reminders.py    checks for due reminders in the background
├── sounds.py       reminder sounds, played through the operating system
├── timefmt.py      24-hour or 12-hour time display
├── instance.py     keeps a single copy of the app running
└── ui/
    ├── theme.py    colors, fonts and the single app-wide stylesheet
    ├── shell.py    main window, sidebar, tray
    ├── notify.py   themed desktop notifications
    ├── palette.py  Ctrl+K command palette
    └── pages/      dashboard, tasks, habits, calendar, timetable, focus, settings
```

Pages never talk to each other directly. Each one listens for change signals from the store and redraws itself. Because the whole look comes from one generated stylesheet, switching themes or accent colors is a single call.

## Credits

Typeface: [Inter](https://rsms.me/inter/) (SIL Open Font License). Icons: [Lucide](https://lucide.dev) (ISC).

## License

Origami is released under the [MIT License](LICENSE).
