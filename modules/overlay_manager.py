"""
Overlay Manager - Loads and manages HTML overlay windows via QWebEngineView.
Each overlay runs in its own transparent, always-on-top window.
"""

import json
import os
from urllib.parse import urlencode

from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtGui import QGuiApplication, QColor, QCursor

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False

from modules.overlay_registry import OVERLAY_REGISTRY  # noqa: F401  (re-exported for callers/tests)
from utils.logger import logger
from utils.paths import resource_path


def js_literal(value):
    """Serialize a Python value as a safe JavaScript literal (never interpolate raw strings into JS)."""
    return json.dumps(value, ensure_ascii=True)


def js_call(page, function_name, *args, guard=True):
    """Call ``window.<function_name>(...)`` with safely-encoded arguments; no-op if it is not defined."""
    call = f"window.{function_name}({', '.join(js_literal(a) for a in args)});"
    page.runJavaScript(f"if (window.{function_name}) {{ {call} }}" if guard else call)


class TransparentWebPage(QWebEnginePage):
    """Web page with transparent background support and console log redirect."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundColor(QColor(0, 0, 0, 0))

    def javaScriptConsoleMessage(self, level, message, lineID, sourceID):
        logger.info(f"JS [Level {level}]: {message} (Line: {lineID}, Source: {sourceID})")


class OverlayWindow(QMainWindow):
    """A transparent window hosting an HTML overlay."""

    def __init__(self, overlay_info, screen_geometry, parent=None):
        super().__init__(parent)
        self.overlay_id = overlay_info["id"]
        self.overlay_info = overlay_info

        is_interactive = overlay_info.get("interactive", False)
        flags = (
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        if not is_interactive:
            flags |= Qt.WindowTransparentForInput

        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        self.web_view = QWebEngineView(self)
        self.web_page = TransparentWebPage(self.web_view)
        self.web_view.setPage(self.web_page)

        self.web_view.setStyleSheet("background: transparent;")
        self.web_view.setAttribute(Qt.WA_TranslucentBackground)

        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)

        central = QWidget(self)
        central.setAttribute(Qt.WA_TranslucentBackground)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.web_view)
        self.setCentralWidget(central)

        # Set geometry
        if "window_size" in overlay_info:
            w, h = overlay_info["window_size"]
            x = screen_geometry.x() + (screen_geometry.width() - w) // 2
            y = screen_geometry.y() + (screen_geometry.height() - h) // 2
            self.setGeometry(x, y, w, h)
        else:
            self.setGeometry(screen_geometry)

        # Cursor tracking is driven by ONE shared timer in OverlayManager (not one per window).
        self._is_interactive = is_interactive
        self._last_cursor_pos = None
        self._cursor_inside = False

    @property
    def tracks_cursor(self):
        return not self._is_interactive

    def handle_cursor(self, pos):
        """Forward a global cursor position to the page (called by the manager's shared timer)."""
        try:
            if pos == self._last_cursor_pos:
                return
            if self._last_cursor_pos is not None:
                if abs(pos.x() - self._last_cursor_pos.x()) < 3 and abs(pos.y() - self._last_cursor_pos.y()) < 3:
                    return
            self._last_cursor_pos = pos
            geo = self.geometry()
            if geo.contains(pos):
                self._cursor_inside = True
                js_call(self.web_page, "__onCursorMove", pos.x() - geo.x(), pos.y() - geo.y())
            elif self._cursor_inside:
                self._cursor_inside = False
                js_call(self.web_page, "__onCursorLeave")
        except Exception:
            pass

    # Hidden overlays must cost ~nothing: freeze the page (stops JS timers, rAF and WebGL) and
    # thaw it the moment the window is shown again. Works for every caller of show()/hide().
    def hideEvent(self, event):
        super().hideEvent(event)
        if not event.spontaneous():
            QTimer.singleShot(0, lambda: self._set_frozen(True))

    def showEvent(self, event):
        super().showEvent(event)
        self._set_frozen(False)

    def _set_frozen(self, frozen):
        try:
            if frozen and self.isVisible():
                return  # re-shown before the deferred freeze ran
            state = QWebEnginePage.LifecycleState.Frozen if frozen else QWebEnginePage.LifecycleState.Active
            self.web_page.setLifecycleState(state)
        except Exception as exc:  # lifecycle API differs across Qt builds; never break show/hide
            logger.debug(f"Lifecycle change skipped for {self.overlay_id}: {exc}")

    def load_local_html(self, relative_path, scale=1.0, count=None, extra_params=None):
        file_path = resource_path(relative_path)
        if not os.path.exists(file_path):
            logger.error(f"HTML overlay file not found: {file_path}")
            return False

        params = []
        if scale != 1.0:
            params.append(("scale", scale))
        if count is not None:
            params.append(("count", count))
        for k, v in (extra_params or {}).items():
            params.append((k, v))
        url_string = QUrl.fromLocalFile(file_path).toString()
        if params:
            url_string += "?" + urlencode(params)
        self.web_view.load(QUrl(url_string))
        logger.info(f"Loading overlay {self.overlay_id} from {file_path} (scale={scale}, count={count})")
        return True


class OverlayManager:
    """Manages creation, visibility, and multi-monitor bounds of HTML overlays."""

    def __init__(self, config=None):
        self.config = config
        self._active = {}
        self._global_visible = True
        self._param_providers = {}
        self._fs_paused = False
        self._fs_paused_ids = []
        self._cursor_timer = QTimer()
        self._cursor_timer.setInterval(33)  # ~30 Hz, shared by every ambient overlay
        self._cursor_timer.timeout.connect(self._tick_cursor)
        self._fullscreen_timer = QTimer()
        self._fullscreen_timer.setInterval(1500)
        self._fullscreen_timer.timeout.connect(self._tick_fullscreen)
        from modules.rest_mode import RestModeController
        self.rest_mode = RestModeController(self, config=config)

    @property
    def available(self):
        return HAS_WEBENGINE

    def _get_combined_screen_geometry(self):
        screens = QGuiApplication.screens()
        if not screens:
            return None
        combined = screens[0].geometry()
        for screen in screens[1:]:
            combined = combined.united(screen.geometry())
        return combined

    def _get_taskbar_horizon_y(self, virtual_geometry):
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return virtual_geometry.height()
        full = screen.geometry()
        available = screen.availableGeometry()
        horizon_global = available.bottom() + 1 if available.bottom() < full.bottom() else full.bottom() + 1
        return max(0, min(virtual_geometry.height(), horizon_global - virtual_geometry.y()))

    # ------------------------------------------------------------------ plumbing
    def set_param_provider(self, overlay_id, provider):
        """Register ``provider() -> dict`` of extra URL params computed each time the overlay opens."""
        self._param_providers[overlay_id] = provider

    def _call(self, overlay_id, function_name, *args):
        """Invoke ``window.<function_name>(*args)`` inside an active overlay (safe, JSON-encoded)."""
        win = self._active.get(overlay_id)
        if win and win.web_page:
            js_call(win.web_page, function_name, *args)

    def _refresh_timers(self):
        """Run the shared timers only while they have work to do."""
        tracking = any(w.tracks_cursor and w.isVisible() for w in self._active.values())
        if tracking and not self._cursor_timer.isActive():
            self._cursor_timer.start()
        elif not tracking and self._cursor_timer.isActive():
            self._cursor_timer.stop()

        wants_fs = bool(self._active) and bool(
            self.config.get("performance", "pause_on_fullscreen") if self.config else False
        )
        if wants_fs and not self._fullscreen_timer.isActive():
            self._fullscreen_timer.start()
        elif not wants_fs and self._fullscreen_timer.isActive():
            self._fullscreen_timer.stop()
            self._resume_from_fullscreen()

    def _tick_cursor(self):
        pos = QCursor.pos()
        for win in self._active.values():
            if win.tracks_cursor and win.isVisible():
                win.handle_cursor(pos)

    def _tick_fullscreen(self):
        if self.is_rest_mode_active():
            self._resume_from_fullscreen()
            return
        from modules.fullscreen_guard import is_foreground_fullscreen

        if is_foreground_fullscreen():
            if not self._fs_paused:
                self._fs_paused_ids = [oid for oid, w in self._active.items() if w.isVisible()]
                for oid in self._fs_paused_ids:
                    self._active[oid].hide()
                self._fs_paused = True
                logger.info(f"Fullscreen app detected — paused {len(self._fs_paused_ids)} overlay(s)")
        else:
            self._resume_from_fullscreen()

    def _resume_from_fullscreen(self):
        if not self._fs_paused:
            return
        self._fs_paused = False
        ids, self._fs_paused_ids = self._fs_paused_ids, []
        if self._global_visible:
            for oid in ids:
                win = self._active.get(oid)
                if win:
                    win.show()
        logger.info("Fullscreen app closed — overlays resumed")

    # ------------------------------------------------------------------ lifecycle
    def open_overlay(self, overlay_id, save_state=True):
        if not self.available:
            return False

        info = next((item for item in OVERLAY_REGISTRY if item["id"] == overlay_id), None)
        if not info:
            logger.warning(f"Unknown overlay id: {overlay_id}")
            return False

        if overlay_id in self._active:
            self._active[overlay_id].show()
            return True

        geometry = self._get_combined_screen_geometry()
        if not geometry:
            logger.error("No screens found")
            return False

        win = OverlayWindow(info, geometry)

        scale = 1.0
        count = None
        if self.config:
            scale_val = self.config.get("overlays", f"{overlay_id}_scale")
            if scale_val is None:
                scale_val = self.config.get("overlays", "global_scale")
            scale = float(scale_val or 1.0)
            count_val = self.config.get("overlays", f"{overlay_id}_count")
            if count_val is not None:
                try:
                    count = int(count_val)
                except (ValueError, TypeError):
                    count = None

        extra_params = dict(info.get("extra_params") or {})
        if self.config:
            opacity_val = self.config.get("overlays", f"{overlay_id}_opacity")
            if opacity_val is not None:
                try:
                    extra_params["opacity"] = float(opacity_val)
                except (ValueError, TypeError):
                    pass

        if overlay_id == "hornwort" and self.config:
            extra_params["speed"] = self.config.get("overlays", "hornwort_growth_speed") or 1.0
            if self.config.get("overlays", "hornwort_xmas_lights"):
                extra_params["xmas"] = "1"
                extra_params["xmas_mode"] = str(self.config.get("overlays", "hornwort_xmas_mode") or "twinkle")
                extra_params["xmas_theme"] = str(self.config.get("overlays", "hornwort_xmas_theme") or "multicolor")

        if overlay_id == "betta_fish" and self.config:
            extra_params["breed"] = str(self.config.get("overlays", "betta_fish_breed") or "buttercup")

        if overlay_id == "orchid" and self.config:
            extra_params["color"] = str(self.config.get("overlays", "orchid_color") or "fuchsia")

        if overlay_id in ("moon", "orchid"):
            extra_params["ground"] = self._get_taskbar_horizon_y(geometry)

        if overlay_id == "moon" and self.config:
            latitude = self.config.get("overlays", "moon_latitude")
            longitude = self.config.get("overlays", "moon_longitude")
            if latitude is not None and longitude is not None:
                extra_params["lat"] = latitude
                extra_params["lon"] = longitude

        if overlay_id == "dragonflies" and self.config:
            extra_params["palette"] = str(self.config.get("overlays", "dragonflies_palette") or "mixed")
            extra_params["style"] = str(self.config.get("overlays", "dragonflies_style") or "percher")

        if overlay_id == "dandelions" and self.config:
            extra_params["style"] = str(self.config.get("overlays", "dandelions_style") or "cyan")

        provider = self._param_providers.get(overlay_id)
        if provider:
            try:
                extra_params.update(provider() or {})
            except Exception as exc:
                logger.warning(f"Param provider for {overlay_id} failed: {exc}")

        if win.load_local_html(info["file"], scale=scale, count=count, extra_params=extra_params):
            self._active[overlay_id] = win
            if self._global_visible and not self._fs_paused:
                win.show()
            elif self._fs_paused:
                self._fs_paused_ids.append(overlay_id)

            if save_state and self.config:
                self.config.set("overlays", overlay_id, True)
            self._refresh_timers()
            return True
        win.deleteLater()
        return False

    # ------------------------------------------------------------------ live controls
    def set_overlay_opacity(self, overlay_id, opacity):
        """Update opacity/transparency of an active overlay live without reloading."""
        opacity = max(0.0, min(1.0, float(opacity)))
        self._call(overlay_id, "setTransparency", int(round((1.0 - opacity) * 100)))
        self._call(overlay_id, "setOpacity", opacity)

    def set_overlay_scale(self, overlay_id, scale):
        """Update scale/size of an active overlay live without reloading."""
        self._call(overlay_id, "setScale", float(scale))

    def set_hornwort_growth_speed(self, speed):
        """Update Hornwort growth speed multiplier live without reloading (clamped 1.0 to 5.0)."""
        try:
            clamped_speed = max(1.0, min(5.0, float(speed)))
        except (ValueError, TypeError):
            clamped_speed = 1.0
        self._call("hornwort", "setGrowthSpeed", clamped_speed)

    def restart_hornwort_growth(self):
        """Restart hornwort plant growth from age 0."""
        if "hornwort" in self._active:
            self._call("hornwort", "restartGrowth")
            logger.info("Hornwort growth restarted via OverlayManager.")

    def set_hornwort_xmas_lights(self, enabled, mode="twinkle", theme="multicolor"):
        """Update Hornwort Christmas lights live without reloading."""
        self._call("hornwort", "setXmasLights", bool(enabled), str(mode), str(theme))

    def set_betta_fish_breed(self, breed):
        """Update Betta Fish breed live without reloading."""
        self._call("betta_fish", "__setBettaBreed", str(breed))

    def set_orchid_color(self, color):
        """Update the living orchid palette without restarting its lifecycle."""
        allowed = {"fuchsia", "blush", "white", "violet", "sunset"}
        self._call("orchid", "setOrchidColor", color if color in allowed else "fuchsia")

    def set_dragonflies_palette(self, palette):
        self._call("dragonflies", "setPalette", str(palette))

    def set_dragonflies_style(self, style):
        self._call("dragonflies", "setStyle", str(style))

    def set_dandelions_style(self, style):
        self._call("dandelions", "__setDandelionStyle", str(style))

    def dragonflies_startle(self):
        self._call("dragonflies", "scatter")

    def dragonflies_roam(self):
        self._call("dragonflies", "roam")

    def toggle_dragonflies_controls(self):
        self._call("dragonflies", "toggleControls")

    def set_moon_location(self, lat, lon):
        self._call("moon", "setLocation", float(lat), float(lon))

    def _moon_toggle(self, fn, force):
        self._call("moon", fn, *(() if force is None else (bool(force),)))

    def toggle_moon_preview(self, force=None):
        self._moon_toggle("togglePreview", force)

    def toggle_moon_dock(self, force=None):
        self._moon_toggle("toggleDock", force)

    def toggle_moon_clouds(self, force=None):
        self._moon_toggle("toggleClouds", force)

    def toggle_moon_controls(self):
        self._call("moon", "toggleControls")

    def set_cichlid_count(self, count):
        self._call("cichlid", "setCount", int(count))

    def cichlid_dart(self):
        self._call("cichlid", "dart")

    def cichlid_turn(self):
        self._call("cichlid", "turn")

    def cichlid_dig(self):
        self._call("cichlid", "dig")

    def cichlid_return_home(self):
        self._call("cichlid", "returnHome")

    def cichlid_graze(self):
        self._call("cichlid", "graze")

    def cichlid_cruise(self):
        self._call("cichlid", "cruise")

    def cichlid_front_view(self):
        self._call("cichlid", "frontView")

    def cichlid_toggle_pair(self):
        self._call("cichlid", "togglePair")

    def toggle_cichlid_controls(self):
        self._call("cichlid", "toggleControls")

    def cichlid_set_breeding_speed(self, speed):
        self._call("cichlid", "setBreedingSpeed", float(speed))

    def cichlid_set_breeding_stage(self, stage):
        """Breeding stage override ('courtship', 'eggs', 'eyed', 'wrigglers', 'fry', 'auto')."""
        self._call("cichlid", "setBreedingStage", str(stage))

    def cichlid_reset_breeding(self):
        self._call("cichlid", "resetBreeding")

    # ------------------------------------------------------------------ open / close
    def reload_overlay(self, overlay_id):
        """Reload an active overlay with updated configuration (e.g. count, scale)."""
        if overlay_id in self._active:
            self.close_overlay(overlay_id, save_state=False)
            self.open_overlay(overlay_id, save_state=False)

    def close_overlay(self, overlay_id, save_state=True):
        if overlay_id in self._active:
            win = self._active.pop(overlay_id)
            win.close()
            win.deleteLater()
            logger.info(f"Closed overlay: {overlay_id}")

            if save_state and self.config:
                self.config.set("overlays", overlay_id, False)
            self._refresh_timers()

    def toggle_overlay(self, overlay_id):
        if overlay_id in self._active:
            self.close_overlay(overlay_id)
            return False
        self.open_overlay(overlay_id)
        return True

    def is_active(self, overlay_id):
        return overlay_id in self._active

    def get_active_ids(self):
        return list(self._active.keys())

    def toggle_all_visibility(self):
        self._global_visible = not self._global_visible
        self._fs_paused = False  # an explicit user choice overrides the fullscreen auto-pause
        self._fs_paused_ids = []
        for win in self._active.values():
            if self._global_visible:
                win.show()
            else:
                win.hide()
        self._refresh_timers()
        return self._global_visible

    def restore_state(self):
        if not self.config or not self.available:
            return

        for info in OVERLAY_REGISTRY:
            oid = info["id"]
            if oid == "nature_world":
                continue
            if self.config.get("overlays", oid):
                self.open_overlay(oid, save_state=False)

    def enter_rest_mode(self):
        """Enter full-screen pitch black Rest Mode."""
        if hasattr(self, "rest_mode"):
            self.rest_mode.enter_rest_mode()

    def exit_rest_mode(self):
        """Exit Rest Mode and return to normal workspace."""
        if hasattr(self, "rest_mode"):
            self.rest_mode.exit_rest_mode()

    def toggle_rest_mode(self):
        """Toggle Rest Mode on or off."""
        if hasattr(self, "rest_mode"):
            self.rest_mode.toggle_rest_mode()

    def is_rest_mode_active(self):
        return hasattr(self, "rest_mode") and self.rest_mode.is_active()

    def handle_escape(self):
        if hasattr(self, "rest_mode"):
            return self.rest_mode.handle_escape()
        return False

    def close_all(self):
        self._cursor_timer.stop()
        self._fullscreen_timer.stop()
        if hasattr(self, "rest_mode") and self.rest_mode.is_active():
            self.rest_mode.exit_rest_mode()
        for win in list(self._active.values()):
            win.close()
            win.deleteLater()
        self._active.clear()
