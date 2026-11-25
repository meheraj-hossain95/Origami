"""Paint the native Windows title bar in the app's own colours instead of the system accent."""

from __future__ import annotations

import ctypes
import sys

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget

# DWMWINDOWATTRIBUTE values (Windows 10 20H1+ / Windows 11).
_DARK_MODE = 20
_BORDER_COLOR = 34
_CAPTION_COLOR = 35
_TEXT_COLOR = 36


def _colorref(color: str) -> ctypes.c_uint:
    c = QColor(color)
    return ctypes.c_uint(c.red() | (c.green() << 8) | (c.blue() << 16))


class _Options(ctypes.Structure):
    _fields_ = [("flags", ctypes.c_uint), ("mask", ctypes.c_uint)]


_WTA_NONCLIENT = 1
_HIDE_CAPTION_AND_ICON = 0x1 | 0x2  # WTNCA_NODRAWCAPTION | WTNCA_NODRAWICON


def style(window: QWidget, background: str, text: str, border: str, dark: bool) -> None:
    """Best effort: silently does nothing on other platforms or older Windows builds."""
    if sys.platform != "win32":
        return
    try:
        dwm = ctypes.windll.dwmapi
        hwnd = ctypes.c_void_p(int(window.winId()))
        # No title text or icon in the bar; the taskbar and Alt+Tab still show both.
        options = _Options(_HIDE_CAPTION_AND_ICON, _HIDE_CAPTION_AND_ICON)
        ctypes.windll.uxtheme.SetWindowThemeAttribute(
            hwnd, _WTA_NONCLIENT, ctypes.byref(options), ctypes.sizeof(options)
        )
        flag = ctypes.c_int(1 if dark else 0)
        dwm.DwmSetWindowAttribute(hwnd, _DARK_MODE, ctypes.byref(flag), ctypes.sizeof(flag))
        for attribute, color in ((_CAPTION_COLOR, background), (_TEXT_COLOR, text), (_BORDER_COLOR, border)):
            value = _colorref(color)
            dwm.DwmSetWindowAttribute(hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value))
    except (AttributeError, OSError):
        pass
