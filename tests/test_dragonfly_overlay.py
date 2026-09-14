import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from config.settings import Settings
from modules.overlay_manager import OVERLAY_REGISTRY, OverlayManager
from ui.control_center import ControlCenter, DRAGONFLY_PALETTES, DRAGONFLY_STYLES


def test_dragonfly_is_registered_with_overlay_file():
    entry = next(item for item in OVERLAY_REGISTRY if item["id"] == "dragonflies")
    assert entry["file"] == "dragonflies-overlay.html"
    assert os.path.isfile(entry["file"])
    assert entry["extra_params"]["transparent"] == "1"
    assert entry["extra_params"]["controls"] == "0"


def test_dragonfly_contains_webgl_engine_and_desktop_bridge():
    source = Path("dragonflies-overlay.html").read_text(encoding="utf-8")
    assert "DragonflyCore" in source
    assert "preserveDrawingBuffer:true" in source
    assert "window.__onCursorMove" in source
    assert "window.__onCursorLeave" in source
    assert "window.setPalette" in source
    assert "window.setStyle" in source
    assert "window.setCount" in source
    assert "window.setScale" in source
    assert "window.setOpacity" in source
    assert "window.scatter" in source
    assert "window.roam" in source
    assert "window.toggleControls" in source
    # Verify built-in controls and UI elements are retained
    assert 'id="panel"' in source
    assert 'id="restore"' in source
    assert 'id="palette"' in source
    assert 'id="style"' in source
    assert 'id="count"' in source
    assert 'id="size"' in source


def test_dragonfly_settings_validation(tmp_path):
    config_file = tmp_path / "config.json"
    settings = Settings(config_path=str(config_file))
    assert settings.get("overlays", "dragonflies_palette") == "mixed"
    assert settings.get("overlays", "dragonflies_style") == "percher"

    # Test invalid palette fallback
    settings.set("overlays", "dragonflies_palette", "invalid_palette")
    settings._validate()
    assert settings.get("overlays", "dragonflies_palette") == "mixed"

    # Test valid palette
    settings.set("overlays", "dragonflies_palette", "emperor-male")
    settings._validate()
    assert settings.get("overlays", "dragonflies_palette") == "emperor-male"

    # Test invalid style fallback
    settings.set("overlays", "dragonflies_style", "super_fast")
    settings._validate()
    assert settings.get("overlays", "dragonflies_style") == "percher"


def test_dragonfly_control_center_widgets_and_signals(tmp_path):
    app = QApplication.instance() or QApplication([])
    config_file = tmp_path / "config.json"
    settings = Settings(config_path=str(config_file))
    control = ControlCenter(config=settings)

    df_widgets = control._species_widgets["dragonflies"]
    assert "dragonfly_palette" in df_widgets and df_widgets["dragonfly_palette"] is not None
    assert "dragonfly_style" in df_widgets and df_widgets["dragonfly_style"] is not None
    assert "dragonfly_startle" in df_widgets and df_widgets["dragonfly_startle"] is not None
    assert "dragonfly_roam" in df_widgets and df_widgets["dragonfly_roam"] is not None

    palette_combo = df_widgets["dragonfly_palette"]
    assert palette_combo.count() == len(DRAGONFLY_PALETTES) == 10

    style_combo = df_widgets["dragonfly_style"]
    assert style_combo.count() == len(DRAGONFLY_STYLES) == 2

    # Change palette in UI and verify settings updated
    idx = palette_combo.findData("ruddy-male")
    palette_combo.setCurrentIndex(idx)
    assert settings.get("overlays", "dragonflies_palette") == "ruddy-male"

    # Change style in UI and verify settings updated
    idx_style = style_combo.findData("patrol")
    style_combo.setCurrentIndex(idx_style)
    assert settings.get("overlays", "dragonflies_style") == "patrol"

    control.close()
