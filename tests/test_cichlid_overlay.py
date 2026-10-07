import os
from PySide6.QtWidgets import QApplication
from config.settings import Settings
from modules.overlay_manager import OVERLAY_REGISTRY, OverlayManager
from ui.control_center import ControlCenter


def test_cichlid_is_registered_with_overlay_file():
    entry = next(item for item in OVERLAY_REGISTRY if item["id"] == "cichlid")
    assert entry["file"] == "jewel-cichlid1 (6).html"
    assert os.path.isfile(entry["file"])


def test_cichlid_html_contains_webgl_engine_and_desktop_bridge():
    with open("jewel-cichlid1 (6).html", "r", encoding="utf-8") as f:
        html = f.read()

    # Verify zero-flicker WebGL config
    assert "preserveDrawingBuffer:true" in html or "preserveDrawingBuffer: true" in html
    assert "powerPreference:'high-performance'" in html or "powerPreference: 'high-performance'" in html

    # Verify live bridge methods
    assert "window.setCount =" in html
    assert "window.setScale =" in html
    assert "window.setOpacity =" in html
    assert "window.dart =" in html
    assert "window.turn =" in html
    assert "window.dig =" in html
    assert "window.returnHome =" in html
    assert "window.frontView =" in html
    assert "window.togglePair =" in html
    assert "window.toggleControls =" in html
    assert "window.__onCursorMove =" in html
    assert "window.setBreedingSpeed =" in html
    assert "window.setBreedingStage =" in html
    assert "window.resetBreeding =" in html
    assert "window.getBreedingState =" in html


def test_cichlid_settings_validation(tmp_path):
    settings = Settings(config_path=str(tmp_path / "config.json"))
    assert settings.get("overlays", "cichlid") is False
    assert settings.get("overlays", "cichlid_count") == 1
    assert settings.get("overlays", "cichlid_scale") == 1.0

    settings.set("overlays", "cichlid_count", 99)
    settings._validate()
    assert settings.get("overlays", "cichlid_count") == 1

    settings.set("overlays", "cichlid_count", 4)
    settings._validate()
    assert settings.get("overlays", "cichlid_count") == 4


def test_cichlid_control_center_widgets_and_signals(tmp_path):
    app = QApplication.instance() or QApplication([])
    settings = Settings(config_path=str(tmp_path / "config.json"))
    control = ControlCenter(config=settings)

    assert "cichlid" in control._species_widgets
    w = control._species_widgets["cichlid"]
    assert w["count_label"].text() == "1"

    # Test toggling
    control._on_species_toggled("cichlid", True)
    assert settings.get("overlays", "cichlid") is True

    control.close()


def test_cichlid_overlay_manager_bridge(tmp_path):
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

    mgr._active["cichlid"] = DummyWindow()

    mgr.set_cichlid_count(3)
    assert any("window.setCount(3)" in s for s in mgr._active["cichlid"].web_page.scripts)

    mgr.cichlid_dart()
    assert any("window.dart()" in s for s in mgr._active["cichlid"].web_page.scripts)

    mgr.cichlid_turn()
    assert any("window.turn()" in s for s in mgr._active["cichlid"].web_page.scripts)

    mgr.cichlid_dig()
    assert any("window.dig()" in s for s in mgr._active["cichlid"].web_page.scripts)

    mgr.cichlid_return_home()
    assert any("window.returnHome()" in s for s in mgr._active["cichlid"].web_page.scripts)

    mgr.cichlid_front_view()
    assert any("window.frontView()" in s for s in mgr._active["cichlid"].web_page.scripts)

    mgr.cichlid_toggle_pair()
    assert any("window.togglePair()" in s for s in mgr._active["cichlid"].web_page.scripts)

    mgr.cichlid_graze()
    assert any("window.graze()" in s for s in mgr._active["cichlid"].web_page.scripts)

    mgr.cichlid_cruise()
    assert any("window.cruise()" in s for s in mgr._active["cichlid"].web_page.scripts)

    mgr.toggle_cichlid_controls()
    assert any("window.toggleControls()" in s for s in mgr._active["cichlid"].web_page.scripts)

    mgr.cichlid_set_breeding_speed(5.0)
    assert any("setBreedingSpeed(5.0)" in s for s in mgr._active["cichlid"].web_page.scripts)

    mgr.cichlid_set_breeding_stage("eggs")
    assert any('setBreedingStage("eggs")' in s for s in mgr._active["cichlid"].web_page.scripts)

    mgr.cichlid_reset_breeding()
    assert any("resetBreeding()" in s for s in mgr._active["cichlid"].web_page.scripts)


def test_cichlid_opacity_query_and_live_scaling():
    with open("jewel-cichlid1 (6).html", "r", encoding="utf-8") as f:
        html = f.read()

    # Ensure opacity query parameter normalizes floats (e.g. 1.0 -> 100%)
    assert "query.has('opacity')" in html
    assert "rawOp <= 1.0 ? rawOp * 100 : rawOp" in html or "rawOp<=1.0?rawOp*100:rawOp" in html

    # Ensure window.setOpacity also accepts 0..1 float without reducing to 1%
    assert "val <= 1.0 ? val * 100 : val" in html


def test_cichlid_stones_removed_and_clean_water():
    with open("jewel-cichlid1 (6).html", "r", encoding="utf-8") as f:
        html = f.read()

    # Stones and sand wash are removed from habitat rendering
    assert "showHabitat:false" in html or "showHabitat: false" in html
    assert "[-.94,-.12,.46,.22]" not in html


def test_cichlid_hornwort_and_algae_interaction():
    with open("jewel-cichlid1 (6).html", "r", encoding="utf-8") as f:
        html = f.read()

    # Cross-window water wake channel
    assert "new BroadcastChannel('ohverlay_water_wake')" in html
    assert "hornwort_stems" in html
    assert "cichlid_wake" in html

    # Live controls for grazing and cruising
    assert "window.graze =" in html
    assert "window.cruise =" in html


def test_cichlid_scale_bounds_inspection_and_bubbles():
    with open("jewel-cichlid1 (6).html", "r", encoding="utf-8") as f:
        html = f.read()

    # 30% scale reduction across all scales
    assert "* 0.70" in html or "*0.70" in html

    # Dual screens wide exploration bounds
    assert "horizontal=Math.min(unit*0.80,80)" in html or "horizontal = Math.min(unit * 0.80, 80)" in html
    assert "vertical=Math.min(unit*0.60,60)" in html or "vertical = Math.min(unit * 0.60, 60)" in html

    # Heavy original DOM controls removed
    assert '<section id="panel"' not in html
    assert '<header class="chrome">' not in html
    assert '<div class="intro chrome"' not in html

    # Front view integrated into living fish movement
    assert "agent.mode==='INSPECT'" in html or "agent.mode === 'INSPECT'" in html
    assert "inspectFront" in html
    assert "ui.studyFish" not in html

    # 2x bigger bubbles
    assert "radius:Math.max(2.4,Math.min(7.0,unit*.028))" in html or "Math.max(2.4, Math.min(7.0, unit * 0.028))" in html
    assert "particles.lineWidth=1.2" in html or "particles.lineWidth = 1.2" in html


def test_cichlid_breeding_and_lifecycle():
    with open("jewel-cichlid1 (6).html", "r", encoding="utf-8") as f:
        html = f.read()

    # 8-hour workday lifecycle duration & persistence
    assert "BREEDING_CYCLE_MS = 8 * 3600 * 1000" in html or "8 * 3600 * 1000" in html
    assert "ohverlay.cichlid.breeding.v1" in html

    # 5 Stages represented in engine
    assert "COURTSHIP" in html
    assert "SPAWNING" in html
    assert "EYED_EGGS" in html
    assert "WRIGGLERS" in html
    assert "FRY" in html

    # Courtship, fanning, guarding, and cleaning modes
    assert "SHIMMY" in html
    assert "FAN_EGGS" in html
    assert "GUARD_NEST" in html
    assert "CLEAN_NEST" in html

    # Egg clump and baby fry flocking rendering
    assert "drawEggClump" in html
    assert "drawFry" in html
    assert "drawBreeding" in html
    assert "EGG_COUNT" in html
    assert "FRY_COUNT" in html
    assert "babyFry" in html


def test_cichlid_side_fins_and_drag_biomechanics():
    with open("jewel-cichlid1 (6).html", "r", encoding="utf-8") as f:
        html = f.read()

    # Dedicated pectoralFin function in JewelMesh
    assert "function pectoralFin(side)" in html
    assert "pectoralFin" in html

    # Shader support for stationary erection ("tatayo") and hydrodynamic drag bending
    assert "uniform float uStationary;" in html
    assert "uniform float uDrag;" in html
    assert "uStationary" in html
    assert "uDrag" in html
    assert "splay=uSide*(.52*uStationary+.68*uBrake)" in html or ".52*uStationary" in html
    assert "delta.x-=uDrag*.16*aUV.y*aUV.y" in html or "uDrag*.16" in html

    # Visible luminous amber-gold membrane with glowing rays
    assert "alpha=.68+.28*ray" in html or ".68+.28*ray" in html





