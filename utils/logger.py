from loguru import logger
import os
import sys
import tempfile


def _get_candidate_log_dirs():
    """Return writable-preferred directories in fallback order."""
    candidates = []

    if getattr(sys, "frozen", False):
        # Packaged builds often run from protected locations (e.g., Program Files).
        # Prefer per-user application data folders in frozen mode.
        local_app_data = os.getenv("LOCALAPPDATA")
        app_data = os.getenv("APPDATA")
        home = os.path.expanduser("~")

        if local_app_data:
            candidates.append(os.path.join(local_app_data, "Ohverlay", "logs"))
        if app_data:
            candidates.append(os.path.join(app_data, "Ohverlay", "logs"))
        if home and home != "~":
            candidates.append(os.path.join(home, ".ohverlay", "logs"))

        # Keep executable directory as a late fallback for portable/unrestricted setups.
        exe_dir = os.path.dirname(sys.executable)
        if exe_dir:
            candidates.append(exe_dir)
    else:
        # Development: keep logs out of the repo checkout.
        home = os.path.expanduser("~")
        if home and home != "~":
            candidates.append(os.path.join(home, ".ohverlay", "logs"))

    # Final fallback for any environment.
    candidates.append(tempfile.gettempdir())

    # De-duplicate while preserving order.
    seen = set()
    unique_candidates = []
    for path in candidates:
        if path and path not in seen:
            seen.add(path)
            unique_candidates.append(path)
    return unique_candidates


def setup_logger():
    logger.remove()

    # sys.stderr is None when running as a windowed .exe (PyInstaller console=False)
    if sys.stderr is not None:
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:7}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="DEBUG",
        )

    # Add file sink from a writable location and gracefully fallback if unavailable.
    file_sink_configured = False
    for log_dir in _get_candidate_log_dirs():
        try:
            os.makedirs(log_dir, exist_ok=True)
            logger.add(
                os.path.join(log_dir, "ohverlay.log"),
                rotation="10 MB",
                level="DEBUG",
            )
            file_sink_configured = True
            break
        except Exception:
            continue

    # Last-resort stderr sink: in rare environments, sys.stderr can be None and
    # all file paths may fail (permissions, read-only filesystem, etc.).
    if not file_sink_configured and sys.stderr is None and sys.__stderr__ is not None:
        logger.add(sys.__stderr__, level="DEBUG")


setup_logger()
