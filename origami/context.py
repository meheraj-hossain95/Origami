from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from origami.store import Store
from origami.timer import FocusTimer


@dataclass(slots=True)
class Context:
    store: Store
    timer: FocusTimer
    navigate: Callable[[str], None] = lambda key: None
    toast: Callable[[str], None] = lambda text: None
