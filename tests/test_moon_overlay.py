import os
from pathlib import Path
from PySide6.QtWidgets import QApplication

from config.settings import Settings
from modules.overlay_manager import OVERLAY_REGISTRY, OverlayManager
from ui.control_center import ControlCenter


def test_moon_is_registered_with_local_asset():
    entry = next(item for item in OVERLAY_REGISTRY if item["id"] == "moon")
    assert entry["file"] == "marketplace-overlays/moon-overlay.html"
    assert os.path.isfile(entry["file"])


def test_moon_coordinates_are_private_validated_settings(tmp_path):
    settings = Settings(config_path=str(tmp_path / "config.json"))
    settings.set("overlays", "moon_latitude", 120)
    settings.set("overlays", "moon_longitude", -240)
    settings._validate()
    assert settings.get("overlays", "moon_latitude") == 90.0
    assert settings.get("overlays", "moon_longitude") == -180.0

    settings.set("overlays", "moon_latitude", "unknown")
    settings.set("overlays", "moon_longitude", "")
    settings._validate()
    assert settings.get("overlays", "moon_latitude") is None
    assert settings.get("overlays", "moon_longitude") is None


def test_control_center_saves_decimal_coordinates(tmp_path):
    app = QApplication.instance() or QApplication([])
    settings = Settings(config_path=str(tmp_path / "config.json"))
    control = ControlCenter(config=settings)
    location = control._species_widgets["moon"]["moon_location"]
    location.setText("14.5995, 120.9842")
    control._on_moon_location_saved(location)
    assert settings.get("overlays", "moon_latitude") == 14.5995
    assert settings.get("overlays", "moon_longitude") == 120.9842
    control.close()


def test_moon_2inch_and_tray_dock_configuration():
    source = Path("marketplace-overlays/moon-overlay.html").read_text(encoding="utf-8")
    # Base diameter around 180px (~2 inches at 96 DPI)
    assert "diameter = 180" in source
    assert "180 * scale" in source
    # Right strip positioning
    assert "baseX = width - rightMargin - diameter * 0.5" in source
    # Docked to tray above taskbar
    assert "dockedToTray" in source
    assert "taskbarHorizon - diameter * 0.5" in source
    # No clipping rectangle that slices moon in half
    assert "ctx.clip()" not in source


def test_overlay_manager_moon_bridge_and_controls(tmp_path):
    settings = Settings(config_path=str(tmp_path / "config.json"))
    mgr = OverlayManager(config=settings)

    class DummyWebPage:
        def __init__(self):
            self.scripts = []

        def runJavaScript(self, script):
            self.scripts.append(script)

    class DummyWindow:
        def __init__(self):
            self.web_page = DummyWebPage()

    mgr._active["moon"] = DummyWindow()

    mgr.set_moon_location(14.5995, 120.9842)
    assert any("window.setLocation" in s and "14.5995" in s for s in mgr._active["moon"].web_page.scripts)

    mgr.toggle_moon_preview(True)
    assert any("window.togglePreview(true)" in s for s in mgr._active["moon"].web_page.scripts)

    mgr.toggle_moon_dock(True)
    assert any("window.toggleDock(true)" in s for s in mgr._active["moon"].web_page.scripts)

    mgr.toggle_moon_clouds(True)
    assert any("window.toggleClouds(true)" in s for s in mgr._active["moon"].web_page.scripts)

    mgr.toggle_moon_controls()
    assert any("window.toggleControls()" in s for s in mgr._active["moon"].web_page.scripts)
