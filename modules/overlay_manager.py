"""
Overlay Manager - Loads and manages HTML overlay windows via QWebEngineView.
Each overlay runs in its own transparent, always-on-top window.
"""

import os
import sys
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtGui import QGuiApplication, QColor, QCursor

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False

from utils.logger import logger


OVERLAY_REGISTRY = [
    {
        "id": "moon",
        "name": "Local Moon",
        "file": "marketplace-overlays/moon-overlay.html",
        "category": "ambient",
        "description": "Local Moon with current phase, orientation, distance, true sky altitude, and occasional drifting clouds",
        "extra_params": {"transparent": "1", "controls": "0"},
    },
    {
        "id": "orchid",
        "name": "Living Moth Orchid",
        "file": "marketplace-overlays/orchid-overlay.html",
        "category": "ambient",
        "description": "Waxy Phalaenopsis with an arching flower spike, cursor physics, and an eight-hour bloom succession",
        "extra_params": {"transparent": "1", "controls": "0"},
    },
    {
        "id": "butterfly_blue",
        "name": "Blue Butterfly",
        "file": "marketplace-overlays/butterflies-blue-overlay.html",
        "category": "ambient",
        "description": "Photo-textured 3D Blue Butterfly with realistic flight and landing",
        "extra_params": {"transparent": "1", "controls": "0"},
    },
    {
        "id": "butterfly_yellow",
        "name": "Yellow Butterfly",
        "file": "marketplace-overlays/butterflies-yellow-overlay.html",
        "category": "ambient",
        "description": "Photo-textured 3D Yellow Butterfly with realistic flight and landing",
        "extra_params": {"transparent": "1", "controls": "0"},
    },
    {
        "id": "butterfly_orange",
        "name": "Orange Butterfly",
        "file": "marketplace-overlays/butterflies-orange-overlay.html",
        "category": "ambient",
        "description": "Photo-textured 3D Orange Butterfly with realistic flight and landing",
        "extra_params": {"transparent": "1", "controls": "0"},
    },
    {
        "id": "hornwort",
        "name": "Hornwort Plant",
        "file": "ohverlay-hornwort.html",
        "category": "ambient",
        "description": "Eight-hour growing hornwort plant with gentle water physics",
        "extra_params": {"transparent": "1", "controls": "0"},
    },
    {
        "id": "neon_tetra",
        "name": "Neon Tetra",
        "file": "tetra-overlay.html",
        "category": "ambient",
        "description": "Realistic 3D WebGL Neon Tetra with volumetric head-led turns and translucent fins",
        "extra_params": {"transparent": "1", "controls": "0"},
    },
    {
        "id": "betta_fish",
        "name": "Betta Fish",
        "file": "beta7.html",
        "category": "ambient",
        "description": "Hyperrealistic Canary-Gold & Cobalt Blue Halfmoon Betta Fish with procedural fins and view-dependent highlights",
        "extra_params": {"transparent": "1", "controls": "0"},
    },
    {
        "id": "cichlid",
        "name": "Jewel Cichlid",
        "file": "jewel-cichlid1 (6).html",
        "category": "ambient",
        "description": "Three-dimensional red-orange Jewel Cichlid with cyan reflective speckles, front-view inspection and gill cover respiration",
        "extra_params": {"transparent": "1", "controls": "0"},
    },
    {
        "id": "nature_world",
        "name": "Unified Nature World",
        "file": "nature-world-overlay.html",
        "category": "ambient",
        "description": "Unified single-canvas nature world with dragonflies, fireflies, and dandelions",
    },
    {
        "id": "fireflies",
        "name": "Fireflies",
        "file": "fireflies-overlay.html",
        "category": "ambient",
        "description": "Six realistic fireflies flying and flashing independently",
    },
    {
        "id": "dandelions",
        "name": "Dandelion Seeds",
        "file": "dandelions-overlay.html",
        "category": "ambient",
        "description": "Dandelion seeds floating and drifting",
    },
    {
        "id": "dragonflies",
        "name": "Realistic Dragonflies",
        "file": "dragonflies-overlay.html",
        "category": "ambient",
        "description": "High-fidelity WebGL dragonfly flight study with species presets, aerodynamic steering, and interactive reactions",
        "extra_params": {"transparent": "1", "controls": "0"},
    },
    {
        "id": "sticky_note",
        "name": "Vintage Sticky Note",
        "file": "sticky-note-overlay.html",
        "category": "office",
        "description": "Persistent technical instruction note with task deadline countdown, pin/tape styles, and drag-and-drop",
    },
    {
        "id": "exam_reviewer",
        "name": "Exam & Study Reviewer",
        "file": "exam-reviewer-overlay.html",
        "category": "learning",
        "description": "Spaced repetition exam study flashcard overlay",
    },
    {
        "id": "telegrama",
        "name": "Telegrama & Hallmark Dispatch",
        "file": "telegrama-overlay.html",
        "category": "personal",
        "description": "Literal paper telegram and Hallmark card for thoughtful 2-way messages from OFWs and family",
        "interactive": True,
        "window_size": (480, 420),
        "extra_params": {"transparent": "1"},
    },
]


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

        # Cursor tracking for non-interactive ambient overlays
        if not is_interactive:
            self._mouse_timer = QTimer(self)
            self._mouse_timer.setInterval(33)  # ~30 Hz cursor tracking
            self._last_cursor_pos = None
            self._cursor_inside = False
            self._mouse_timer.timeout.connect(self._track_cursor)
            self._mouse_timer.start()

    def _track_cursor(self):
        try:
            pos = QCursor.pos()
            if pos != self._last_cursor_pos:
                if self._last_cursor_pos is not None:
                    dx = abs(pos.x() - self._last_cursor_pos.x())
                    dy = abs(pos.y() - self._last_cursor_pos.y())
                    if dx < 3 and dy < 3:
                        return
                self._last_cursor_pos = pos
                geo = self.geometry()
                if geo.contains(pos):
                    self._cursor_inside = True
                    rel_x = pos.x() - geo.x()
                    rel_y = pos.y() - geo.y()
                    self.web_page.runJavaScript(
                        f"if (window.__onCursorMove) window.__onCursorMove({rel_x}, {rel_y});"
                    )
                elif self._cursor_inside:
                    self._cursor_inside = False
                    self.web_page.runJavaScript(
                        "if (window.__onCursorLeave) window.__onCursorLeave();"
                    )
        except Exception:
            pass

    def closeEvent(self, event):
        if hasattr(self, "_mouse_timer") and self._mouse_timer.isActive():
            self._mouse_timer.stop()
        super().closeEvent(event)

    def load_local_html(self, relative_path, scale=1.0, count=None, extra_params=None):
        file_path = os.path.abspath(relative_path)
        if not os.path.exists(file_path):
            logger.error(f"HTML overlay file not found: {file_path}")
            return False

        url = QUrl.fromLocalFile(file_path)
        url_string = url.toString()
        params = []
        if scale != 1.0:
            params.append(f"scale={scale}")
        if count is not None:
            params.append(f"count={count}")
        if extra_params:
            for k, v in extra_params.items():
                params.append(f"{k}={v}")
        if params:
            url_string += "?" + "&".join(params)
        self.web_view.load(QUrl(url_string))
        logger.info(f"Loading overlay {self.overlay_id} from {file_path} (scale={scale}, count={count})")
        return True


class OverlayManager:
    """Manages creation, visibility, and multi-monitor bounds of HTML overlays."""

    def __init__(self, config=None):
        self.config = config
        self._active = {}
        self._global_visible = True

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
                    op = float(opacity_val)
                    extra_params["opacity"] = op
                except (ValueError, TypeError):
                    pass

        if overlay_id == "hornwort" and self.config:
            spd = self.config.get("overlays", "hornwort_growth_speed") or 1.0
            extra_params["speed"] = spd
            xmas_enabled = self.config.get("overlays", "hornwort_xmas_lights") or False
            xmas_mode = self.config.get("overlays", "hornwort_xmas_mode") or "twinkle"
            xmas_theme = self.config.get("overlays", "hornwort_xmas_theme") or "multicolor"
            if xmas_enabled:
                extra_params["xmas"] = "1"
                extra_params["xmas_mode"] = str(xmas_mode)
                extra_params["xmas_theme"] = str(xmas_theme)

        if overlay_id == "betta_fish" and self.config:
            breed = self.config.get("overlays", "betta_fish_breed") or "buttercup"
            extra_params["breed"] = str(breed)

        if overlay_id == "orchid" and self.config:
            color = self.config.get("overlays", "orchid_color") or "fuchsia"
            extra_params["color"] = str(color)

        if overlay_id in ("moon", "orchid"):
            extra_params["ground"] = self._get_taskbar_horizon_y(geometry)

        if overlay_id == "moon" and self.config:
            latitude = self.config.get("overlays", "moon_latitude")
            longitude = self.config.get("overlays", "moon_longitude")
            if latitude is not None and longitude is not None:
                extra_params["lat"] = latitude
                extra_params["lon"] = longitude

        if overlay_id == "dragonflies" and self.config:
            palette = self.config.get("overlays", "dragonflies_palette") or "mixed"
            extra_params["palette"] = str(palette)
            style = self.config.get("overlays", "dragonflies_style") or "percher"
            extra_params["style"] = str(style)

        if overlay_id == "dandelions" and self.config:
            style = self.config.get("overlays", "dandelions_style") or "cyan"
            extra_params["style"] = str(style)

        if win.load_local_html(info["file"], scale=scale, count=count, extra_params=extra_params):
            self._active[overlay_id] = win
            if self._global_visible:
                win.show()

            if save_state and self.config:
                self.config.set("overlays", overlay_id, True)
            return True
        return False

    def set_overlay_opacity(self, overlay_id, opacity):
        """Update opacity/transparency of an active overlay live without reloading."""
        if overlay_id in self._active:
            win = self._active[overlay_id]
            t_pct = int(round(max(0.0, min(1.0, 1.0 - opacity)) * 100))
            win.web_page.runJavaScript(f"if(window.setTransparency) window.setTransparency({t_pct});")
            win.web_page.runJavaScript(f"if(window.setOpacity) window.setOpacity({opacity});")

    def set_overlay_scale(self, overlay_id, scale):
        """Update scale/size of an active overlay live without reloading."""
        if overlay_id in self._active:
            win = self._active[overlay_id]
            win.web_page.runJavaScript(f"if(window.setScale) window.setScale({scale});")

    def set_hornwort_growth_speed(self, speed):
        """Update Hornwort growth speed multiplier live without reloading (clamped 1.0 to 5.0)."""
        try:
            clamped_speed = max(1.0, min(5.0, float(speed)))
        except (ValueError, TypeError):
            clamped_speed = 1.0
        if "hornwort" in self._active:
            win = self._active["hornwort"]
            if win and win.web_page:
                win.web_page.runJavaScript(f"if(window.setGrowthSpeed) window.setGrowthSpeed({clamped_speed});")

    def restart_hornwort_growth(self):
        """Restart hornwort plant growth from age 0."""
        if "hornwort" in self._active:
            win = self._active["hornwort"]
            if win and win.web_page:
                win.web_page.runJavaScript("if(window.restartGrowth) window.restartGrowth();")
                logger.info("Hornwort growth restarted via OverlayManager.")

    def set_hornwort_xmas_lights(self, enabled, mode="twinkle", theme="multicolor"):
        """Update Hornwort Christmas lights live without reloading."""
        if "hornwort" in self._active:
            win = self._active["hornwort"]
            if win and win.web_page:
                js = f"if(window.setXmasLights) window.setXmasLights({str(bool(enabled)).lower()}, '{mode}', '{theme}');"
                win.web_page.runJavaScript(js)

    def set_betta_fish_breed(self, breed):
        """Update Betta Fish breed live without reloading."""
        if "betta_fish" in self._active:
            win = self._active["betta_fish"]
            if win and win.web_page:
                win.web_page.runJavaScript(f"if(window.__setBettaBreed) window.__setBettaBreed('{breed}');")

    def set_orchid_color(self, color):
        """Update the living orchid palette without restarting its lifecycle."""
        allowed = {"fuchsia", "blush", "white", "violet", "sunset"}
        selected = color if color in allowed else "fuchsia"
        if "orchid" in self._active:
            win = self._active["orchid"]
            if win and win.web_page:
                win.web_page.runJavaScript(f"if(window.setOrchidColor) window.setOrchidColor('{selected}');")

    def set_dragonflies_palette(self, palette):
        """Update Dragonfly species/palette preset live without reloading."""
        if "dragonflies" in self._active:
            win = self._active["dragonflies"]
            if win and win.web_page:
                win.web_page.runJavaScript(f"if(window.setPalette) window.setPalette('{palette}');")

    def set_dragonflies_style(self, style):
        """Update Dragonfly flight style live without reloading."""
        if "dragonflies" in self._active:
            win = self._active["dragonflies"]
            if win and win.web_page:
                win.web_page.runJavaScript(f"if(window.setStyle) window.setStyle('{style}');")

    def set_dandelions_style(self, style):
        """Update Dandelion style live without reloading."""
        if "dandelions" in self._active:
            win = self._active["dandelions"]
            if win and win.web_page:
                escaped = str(style).replace("'", "\\'")
                win.web_page.runJavaScript(f"if(window.__setDandelionStyle) window.__setDandelionStyle('{escaped}');")

    def dragonflies_startle(self):
        """Startle all dragonflies into evasive flight."""
        if "dragonflies" in self._active:
            win = self._active["dragonflies"]
            if win and win.web_page:
                win.web_page.runJavaScript("if(window.scatter) window.scatter();")

    def dragonflies_roam(self):
        """Command all resting dragonflies to take flight."""
        if "dragonflies" in self._active:
            win = self._active["dragonflies"]
            if win and win.web_page:
                win.web_page.runJavaScript("if(window.roam) window.roam();")

    def toggle_dragonflies_controls(self):
        """Toggle in-overlay HUD control panel."""
        if "dragonflies" in self._active:
            win = self._active["dragonflies"]
            if win and win.web_page:
                win.web_page.runJavaScript("if(window.toggleControls) window.toggleControls();")

    def set_moon_location(self, lat, lon):
        """Update Moon coordinates live without reloading."""
        if "moon" in self._active:
            win = self._active["moon"]
            if win and win.web_page:
                win.web_page.runJavaScript(f"if(window.setLocation) window.setLocation({lat}, {lon});")

    def toggle_moon_preview(self, force=None):
        """Toggle Moon preview mode (always visible) live."""
        if "moon" in self._active:
            win = self._active["moon"]
            if win and win.web_page:
                arg = f"{'true' if force else 'false'}" if force is not None else ""
                win.web_page.runJavaScript(f"if(window.togglePreview) window.togglePreview({arg});")

    def toggle_moon_dock(self, force=None):
        """Toggle Moon docking right above taskbar tray vs sky altitude."""
        if "moon" in self._active:
            win = self._active["moon"]
            if win and win.web_page:
                arg = f"{'true' if force else 'false'}" if force is not None else ""
                win.web_page.runJavaScript(f"if(window.toggleDock) window.toggleDock({arg});")

    def toggle_moon_clouds(self, force=None):
        """Toggle Moon drifting clouds live."""
        if "moon" in self._active:
            win = self._active["moon"]
            if win and win.web_page:
                arg = f"{'true' if force else 'false'}" if force is not None else ""
                win.web_page.runJavaScript(f"if(window.toggleClouds) window.toggleClouds({arg});")

    def toggle_moon_controls(self):
        """Toggle Moon in-overlay HUD control panel."""
        if "moon" in self._active:
            win = self._active["moon"]
            if win and win.web_page:
                win.web_page.runJavaScript("if(window.toggleControls) window.toggleControls();")

    def set_cichlid_count(self, count):
        """Update Jewel Cichlid count live."""
        if "cichlid" in self._active:
            win = self._active["cichlid"]
            if win and win.web_page:
                win.web_page.runJavaScript(f"if(window.setCount) window.setCount({count});")

    def cichlid_dart(self):
        """Command Jewel Cichlid to dart & brake."""
        if "cichlid" in self._active:
            win = self._active["cichlid"]
            if win and win.web_page:
                win.web_page.runJavaScript("if(window.dart) window.dart();")

    def cichlid_turn(self):
        """Command Jewel Cichlid to turn around."""
        if "cichlid" in self._active:
            win = self._active["cichlid"]
            if win and win.web_page:
                win.web_page.runJavaScript("if(window.turn) window.turn();")

    def cichlid_dig(self):
        """Command Jewel Cichlid to dig at sand."""
        if "cichlid" in self._active:
            win = self._active["cichlid"]
            if win and win.web_page:
                win.web_page.runJavaScript("if(window.dig) window.dig();")

    def cichlid_return_home(self):
        """Command Jewel Cichlid to return home."""
        if "cichlid" in self._active:
            win = self._active["cichlid"]
            if win and win.web_page:
                win.web_page.runJavaScript("if(window.returnHome) window.returnHome();")

    def cichlid_graze(self):
        """Command Jewel Cichlid to visit hornwort and graze on algae."""
        if "cichlid" in self._active:
            win = self._active["cichlid"]
            if win and win.web_page:
                win.web_page.runJavaScript("if(window.graze) window.graze();")

    def cichlid_cruise(self):
        """Command Jewel Cichlid to cruise freely in open water."""
        if "cichlid" in self._active:
            win = self._active["cichlid"]
            if win and win.web_page:
                win.web_page.runJavaScript("if(window.cruise) window.cruise();")

    def cichlid_front_view(self):
        """Toggle Jewel Cichlid front-view shape study."""
        if "cichlid" in self._active:
            win = self._active["cichlid"]
            if win and win.web_page:
                win.web_page.runJavaScript("if(window.frontView) window.frontView();")

    def cichlid_toggle_pair(self):
        """Toggle Jewel Cichlid paired demo."""
        if "cichlid" in self._active:
            win = self._active["cichlid"]
            if win and win.web_page:
                win.web_page.runJavaScript("if(window.togglePair) window.togglePair();")

    def toggle_cichlid_controls(self):
        """Toggle Jewel Cichlid in-overlay HUD control panel."""
        if "cichlid" in self._active:
            win = self._active["cichlid"]
            if win and win.web_page:
                win.web_page.runJavaScript("if(window.toggleControls) window.toggleControls();")

    def cichlid_set_breeding_speed(self, speed):
        """Set Jewel Cichlid breeding simulation speed multiplier."""
        if "cichlid" in self._active:
            win = self._active["cichlid"]
            if win and win.web_page:
                win.web_page.runJavaScript(f"if(window.setBreedingSpeed) window.setBreedingSpeed({float(speed)});")

    def cichlid_set_breeding_stage(self, stage):
        """Set Jewel Cichlid breeding stage override ('courtship', 'eggs', 'eyed', 'wrigglers', 'fry', 'auto')."""
        if "cichlid" in self._active:
            win = self._active["cichlid"]
            if win and win.web_page:
                clean_stage = str(stage).replace("'", "").replace('"', "")
                win.web_page.runJavaScript(f"if(window.setBreedingStage) window.setBreedingStage('{clean_stage}');")

    def cichlid_reset_breeding(self):
        """Reset Jewel Cichlid breeding lifecycle back to beginning."""
        if "cichlid" in self._active:
            win = self._active["cichlid"]
            if win and win.web_page:
                win.web_page.runJavaScript("if(window.resetBreeding) window.resetBreeding();")

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

    def toggle_overlay(self, overlay_id):
        if overlay_id in self._active:
            self.close_overlay(overlay_id)
            return False
        else:
            self.open_overlay(overlay_id)
            return True

    def is_active(self, overlay_id):
        return overlay_id in self._active

    def get_active_ids(self):
        return list(self._active.keys())

    def toggle_all_visibility(self):
        self._global_visible = not self._global_visible
        for win in self._active.values():
            if self._global_visible:
                win.show()
            else:
                win.hide()
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

    def close_all(self):
        for win in list(self._active.values()):
            win.close()
            win.deleteLater()
        self._active.clear()
