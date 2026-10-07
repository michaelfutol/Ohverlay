"""
Path helpers that work identically from source checkouts and PyInstaller bundles.

Never resolve bundled assets against the current working directory — a desktop
shortcut, the installer, or ``pythonw`` can all launch with an unrelated CWD.
"""

from __future__ import annotations

import os
import sys


def project_root() -> str:
    """Directory that contains the bundled/source assets (HTML overlays, etc.)."""
    if getattr(sys, "frozen", False):
        # PyInstaller one-file extracts to _MEIPASS; one-dir keeps data next to the exe.
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_path(relative_path: str) -> str:
    """Absolute path to a bundled resource, independent of the CWD."""
    return os.path.normpath(os.path.join(project_root(), *str(relative_path).replace("\\", "/").split("/")))
