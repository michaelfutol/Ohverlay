import os

from PySide6.QtWidgets import QApplication

from config.settings import Settings
from modules.overlay_manager import OVERLAY_REGISTRY
from ui.control_center import ControlCenter, ORCHID_COLORS


def test_orchid_is_registered_with_marketplace_asset():
    entry = next(item for item in OVERLAY_REGISTRY if item["id"] == "orchid")
    assert entry["file"] == "marketplace-overlays/orchid-overlay.html"
    assert os.path.isfile(entry["file"])


def test_orchid_contains_lifecycle_and_cursor_physics():
    source = open("marketplace-overlays/orchid-overlay.html", encoding="utf-8").read()
    assert "8*60*60*1000" in source
    assert "window.__onCursorMove" in source
    assert "function flower" in source
    assert "function spawnFallingPetal" in source
    assert 'id="size" type="range"' in source
    assert "const PALETTES=" in source


def test_orchid_color_varieties_are_saved(tmp_path):
    app = QApplication.instance() or QApplication([])
    settings = Settings(config_path=str(tmp_path / "config.json"))
    control = ControlCenter(config=settings)
    combo = control._species_widgets["orchid"]["orchid_color"]
    assert combo.count() == len(ORCHID_COLORS) == 5
    combo.setCurrentIndex(combo.findData("violet"))
    assert settings.get("overlays", "orchid_color") == "violet"
    control.close()
