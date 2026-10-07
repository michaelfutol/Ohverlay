"""
Rest Mode & Ambient Showcase Controller for Ohverlay.
Provides a full-screen pitch-black backdrop covering all displays,
bulletproof double-Escape exit mechanism, cursor auto-hiding, and random species auto-rotation.
"""

import time
import random
from PySide6.QtWidgets import QWidget, QLabel, QApplication
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QEvent
from PySide6.QtGui import QGuiApplication

from utils.logger import logger


class RestBackdropWindow(QWidget):
    """Full-screen pitch-black canvas spanning across all connected monitors."""

    def __init__(self, controller, geometry, parent=None):
        super().__init__(parent)
        self.controller = controller

        # Frameless, stays on top, solid black
        flags = (
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WA_NoSystemBackground, False)
        self.setStyleSheet("background-color: #000000; border: none;")
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)

        if geometry:
            self.setGeometry(geometry)

        # Subtle toast indicator for single Escape press
        self.toast = QLabel("Press Esc again to return to workspace", self)
        self.toast.setAlignment(Qt.AlignCenter)
        self.toast.setStyleSheet("""
            QLabel {
                background-color: rgba(15, 23, 42, 235);
                color: #f8fafc;
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 20px;
                padding: 9px 24px;
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
                font-size: 13px;
                font-weight: 500;
            }
        """)
        self.toast.hide()

        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(self.toast.hide)

        # Cursor auto-hide after 3s of inactivity
        self._cursor_timer = QTimer(self)
        self._cursor_timer.setSingleShot(True)
        self._cursor_timer.timeout.connect(self._hide_cursor)
        self._cursor_timer.start(3000)

    def _hide_cursor(self):
        self.setCursor(Qt.BlankCursor)

    def mouseMoveEvent(self, event):
        self.unsetCursor()
        self._cursor_timer.start(3000)
        super().mouseMoveEvent(event)

    def show_toast(self, text="Press Esc again to return to workspace"):
        self.toast.setText(text)
        self.toast.adjustSize()

        # Center horizontally on primary screen or viewport
        screen = QGuiApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            local_x = geo.x() - self.x() + (geo.width() - self.toast.width()) // 2
            local_y = geo.y() - self.y() + geo.height() - 110
        else:
            local_x = (self.width() - self.toast.width()) // 2
            local_y = self.height() - 110

        self.toast.move(max(10, local_x), max(10, local_y))
        self.toast.show()
        self.toast.raise_()
        self._toast_timer.start(1800)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.controller.handle_escape()
            event.accept()
            return
        super().keyPressEvent(event)


class RestModeController(QObject):
    """Manages entering/exiting Rest Mode, double-Escape exit, and species rotation."""

    rest_mode_entered = Signal()
    rest_mode_exited = Signal()
    species_rotated = Signal(str)
    rotation_interval_changed = Signal(int)
    auto_rotate_toggled = Signal(bool)

    def __init__(self, overlay_manager, config=None, parent=None):
        super().__init__(parent)
        self.overlay_manager = overlay_manager
        self.config = config
        self.active = False
        self.last_escape_time = 0.0
        self.escape_threshold = 0.75  # 750ms window for double escape
        self.saved_overlays = []
        self.backdrop_window = None

        # Rotation configuration
        cfg_rotate = True
        cfg_interval = 5
        if self.config:
            val_rot = self.config.get("rest_mode", "auto_rotate")
            if val_rot is not None:
                cfg_rotate = bool(val_rot)
            val_int = self.config.get("rest_mode", "rotation_interval_minutes")
            if val_int is not None:
                try:
                    cfg_interval = max(1, min(60, int(val_int)))
                except (ValueError, TypeError):
                    cfg_interval = 5

        self.auto_rotate = cfg_rotate
        self.interval_minutes = cfg_interval
        self.current_showcase_species = None

        self.rotation_timer = QTimer(self)
        self.rotation_timer.timeout.connect(self._on_rotate_timeout)

        self._filter_installed = False

    def _install_filter(self):
        q_app = QApplication.instance()
        if q_app and not self._filter_installed:
            q_app.installEventFilter(self)
            self._filter_installed = True

    def _remove_filter(self):
        q_app = QApplication.instance()
        if q_app and self._filter_installed:
            try:
                q_app.removeEventFilter(self)
            except Exception:
                pass
            self._filter_installed = False

    def __del__(self):
        try:
            self._remove_filter()
        except Exception:
            pass

    def eventFilter(self, watched, event):
        """Trap Escape key globally across all Qt windows while in Rest Mode."""
        try:
            if getattr(self, "active", False):
                if event is not None and event.type() == QEvent.KeyPress:
                    if event.key() == Qt.Key_Escape:
                        handled = self.handle_escape()
                        if handled:
                            return True
        except Exception:
            pass
        return super().eventFilter(watched, event)

    def is_active(self):
        return self.active

    def set_auto_rotate(self, enabled):
        self.auto_rotate = bool(enabled)
        if self.config:
            self.config.set("rest_mode", "auto_rotate", self.auto_rotate)
            self.config.save()
        if self.active:
            if self.auto_rotate:
                self._start_rotation_timer()
            else:
                self.rotation_timer.stop()
        self.auto_rotate_toggled.emit(self.auto_rotate)

    def set_rotation_interval(self, minutes):
        try:
            val = max(1, min(60, int(minutes)))
        except (ValueError, TypeError):
            val = 5
        self.interval_minutes = val
        if self.config:
            self.config.set("rest_mode", "rotation_interval_minutes", val)
            self.config.save()
        if self.active and self.auto_rotate:
            self._start_rotation_timer()
        self.rotation_interval_changed.emit(val)

    def _start_rotation_timer(self):
        self.rotation_timer.stop()
        interval_ms = int(self.interval_minutes * 60 * 1000)
        self.rotation_timer.start(interval_ms)
        logger.info(f"Rest Mode auto-rotation timer started ({self.interval_minutes}m interval)")

    def get_eligible_species(self):
        """Return list of ambient species IDs available for rotation."""
        from modules.overlay_manager import OVERLAY_REGISTRY
        eligible = []
        for item in OVERLAY_REGISTRY:
            oid = item.get("id")
            cat = item.get("category", "")
            if cat == "ambient" and oid not in ("nature_world", "sticky_note", "exam_reviewer"):
                eligible.append(oid)
        return eligible

    def enter_rest_mode(self):
        """Activate full-screen pitch black Rest Mode with overlays on top."""
        if self.active:
            return

        self.active = True
        self.last_escape_time = 0.0
        self._install_filter()

        # 1. Save currently active overlays
        self.saved_overlays = list(self.overlay_manager.get_active_ids())

        # 2. Show pitch-black backdrop covering all displays
        geo = self.overlay_manager._get_combined_screen_geometry()
        if not self.backdrop_window:
            self.backdrop_window = RestBackdropWindow(self, geo)
        else:
            self.backdrop_window.setGeometry(geo)

        self.backdrop_window.show()
        self.backdrop_window.raise_()
        self.backdrop_window.activateWindow()

        # 3. If no overlays are active or auto-rotate is enabled, ensure at least one runs
        eligible = self.get_eligible_species()
        if self.auto_rotate:
            if not self.saved_overlays and eligible:
                first_pick = random.choice(eligible)
                self.overlay_manager.open_overlay(first_pick, save_state=False)
                self.current_showcase_species = first_pick
            self._start_rotation_timer()
        elif not self.saved_overlays and eligible:
            first_pick = random.choice(eligible)
            self.overlay_manager.open_overlay(first_pick, save_state=False)

        # 4. Bring all active overlay windows to float directly on top of the black canvas
        self._raise_overlays()

        self.rest_mode_entered.emit()
        logger.info("Rest Mode entered — Pitch black canvas active. Press Esc 2x to return.")

    def _raise_overlays(self):
        """Raise all active overlay windows above the black backdrop."""
        for win in list(self.overlay_manager._active.values()):
            win.show()
            win.raise_()

    def exit_rest_mode(self):
        """Exit Rest Mode and restore normal workspace."""
        if not self.active:
            return

        self.active = False
        self.rotation_timer.stop()
        self._remove_filter()

        if self.backdrop_window:
            self.backdrop_window.unsetCursor()
            self.backdrop_window.hide()

        # Restore previous overlay state if configured
        restore = True
        if self.config:
            val = self.config.get("rest_mode", "restore_on_exit")
            if val is not None:
                restore = bool(val)

        if restore:
            current_active = list(self.overlay_manager.get_active_ids())
            for oid in current_active:
                if oid not in self.saved_overlays:
                    self.overlay_manager.close_overlay(oid, save_state=False)
            for oid in self.saved_overlays:
                if not self.overlay_manager.is_active(oid):
                    self.overlay_manager.open_overlay(oid, save_state=False)

        self.rest_mode_exited.emit()
        logger.info("Rest Mode exited — Workspace restored.")

    def toggle_rest_mode(self):
        if self.active:
            self.exit_rest_mode()
        else:
            self.enter_rest_mode()

    def handle_escape(self):
        """Handle Escape press with double-escape detection."""
        if not self.active:
            return False

        now = time.time()
        if now - self.last_escape_time <= self.escape_threshold:
            # Double Escape detected!
            self.last_escape_time = 0.0
            self.exit_rest_mode()
            return True
        else:
            self.last_escape_time = now
            if self.backdrop_window:
                self.backdrop_window.show_toast("Press Esc again to return to workspace")
            return False

    def _on_rotate_timeout(self):
        """Rotate to a random ambient species."""
        if not self.active or not self.auto_rotate:
            return

        eligible = self.get_eligible_species()
        if not eligible:
            return

        active_now = self.overlay_manager.get_active_ids()
        candidates = [s for s in eligible if s not in active_now] or eligible
        chosen = random.choice(candidates)

        # Close currently active overlays that were rotating
        for oid in list(active_now):
            self.overlay_manager.close_overlay(oid, save_state=False)

        # Open chosen new species
        self.overlay_manager.open_overlay(chosen, save_state=False)
        self._raise_overlays()

        self.current_showcase_species = chosen
        self.species_rotated.emit(chosen)
        logger.info(f"Rest Mode auto-rotated species to: {chosen}")
