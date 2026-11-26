from __future__ import annotations

import sys
from pathlib import Path

__version__ = "1.0.0"

_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
ASSETS = _ROOT / "origami" / "assets"
