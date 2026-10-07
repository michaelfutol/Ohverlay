"""
Detect "another app is fullscreen" (games, video players, presentations) on Windows.

Ohverlay overlays are always-on-top; drawing them over a fullscreen app is both annoying and a
needless GPU cost. The manager hides (and freezes) overlays while this returns True.
"""

from __future__ import annotations

import os
import sys
from typing import NamedTuple


class Rect(NamedTuple):
    left: int
    top: int
    right: int
    bottom: int


def rect_covers(window: Rect, monitor: Rect) -> bool:
    """True when ``window`` fully covers ``monitor`` (borderless/exclusive fullscreen)."""
    return (window.left <= monitor.left and window.top <= monitor.top
            and window.right >= monitor.right and window.bottom >= monitor.bottom)


_SHELL_CLASSES = {"Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd"}


def is_foreground_fullscreen(own_pid: int | None = None) -> bool:
    """Whether the foreground window (not ours, not the desktop/taskbar) fills its monitor."""
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32

        class MONITORINFO(ctypes.Structure):
            _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                        ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]

        user32.GetForegroundWindow.restype = wintypes.HWND
        user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
        user32.MonitorFromWindow.restype = ctypes.c_void_p
        user32.GetMonitorInfoW.argtypes = [ctypes.c_void_p, ctypes.POINTER(MONITORINFO)]

        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return False

        cls = ctypes.create_unicode_buffer(64)
        user32.GetClassNameW(hwnd, cls, 64)
        if cls.value in _SHELL_CLASSES:
            return False

        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == (own_pid if own_pid is not None else os.getpid()):
            return False

        wr = wintypes.RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(wr)):
            return False
        monitor = user32.MonitorFromWindow(hwnd, 2)  # MONITOR_DEFAULTTONEAREST
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if not monitor or not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
            return False
        mr = info.rcMonitor
        return rect_covers(Rect(wr.left, wr.top, wr.right, wr.bottom),
                           Rect(mr.left, mr.top, mr.right, mr.bottom))
    except Exception:
        return False
