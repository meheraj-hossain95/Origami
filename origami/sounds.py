"""Reminder sounds, played through the operating system so no audio library is needed."""

from __future__ import annotations

import shutil
import subprocess
import sys

from origami import ASSETS

# key -> label; "none" keeps reminders silent.
SOUNDS: dict[str, str] = {
    "none": "None",
    "chime": "Chime",
    "bell": "Bell",
    "ping": "Ping",
    "marimba": "Marimba",
    "pulse": "Pulse",
}
DEFAULT_SOUND = "chime"


def play(key: str) -> None:
    """Fire and forget; never raises, so a missing player can't break a reminder."""
    path = ASSETS / "sounds" / f"{key}.wav"
    if key == "none" or not path.exists():
        return
    try:
        if sys.platform == "win32":
            import winsound

            winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
            return
        player = ["afplay"] if sys.platform == "darwin" else next(
            ([p] for p in ("paplay", "aplay", "pw-play") if shutil.which(p)), None
        )
        if player:
            quiet = subprocess.DEVNULL
            subprocess.Popen([*player, str(path)], stdout=quiet, stderr=quiet, start_new_session=True)
    except (OSError, RuntimeError):
        pass
