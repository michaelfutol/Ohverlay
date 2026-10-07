import os
import sys
import pytest
from PySide6.QtWidgets import QApplication, QScrollArea
from modules.overlay_manager import OVERLAY_REGISTRY, OverlayManager
from config.settings import Settings, DEFAULT_CONFIG
from ui.control_center import ControlCenter, XMAS_THEMES, BETTA_BREEDS

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

def test_preserved_files_and_active_registry():
    # Verify betta file exists; retired cat/mermaid overlay pages were removed
    assert os.path.isfile("beta7.html")
    assert not os.path.isfile("cat-overlay.html")
    assert not os.path.isfile("mermaid-overlay.html")

    # Verify active overlays in registry
    registry_ids = [o["id"] for o in OVERLAY_REGISTRY]
    assert "betta_fish" in registry_ids
    assert "hornwort" in registry_ids
    assert "neon_tetra" in registry_ids
    assert "butterfly_blue" in registry_ids
    assert "butterfly_yellow" in registry_ids
    assert "butterfly_orange" in registry_ids
    assert "fireflies" in registry_ids

    # Verify cat and mermaid are temporarily removed from active registry
    assert "cat" not in registry_ids
    assert "mermaid" not in registry_ids

def test_new_settings_defaults(tmp_path):
    config_file = tmp_path / "test_config.json"
    settings = Settings(config_path=str(config_file))
    
    assert "betta_fish" in settings.get("overlays")
    assert "hornwort" in settings.get("overlays")
    assert "hornwort_xmas_lights" in settings.get("overlays")
    assert "hornwort_xmas_mode" in settings.get("overlays")
    assert "hornwort_xmas_theme" in settings.get("overlays")
    assert settings.get("overlays", "hornwort_xmas_theme") == "multicolor"
    assert settings.get("overlays", "betta_fish_breed") == "buttercup"

def test_control_center_scroll_and_widgets(qapp, tmp_path):
    config_file = tmp_path / "test_cc_config.json"
    settings = Settings(config_path=str(config_file))
    cc = ControlCenter(config=settings)

    # Check scroll area is present
    scroll_areas = cc.findChildren(QScrollArea)
    assert len(scroll_areas) >= 1

    # Check active species widgets exist including betta_fish
    assert "betta_fish" in cc._species_widgets
    assert "hornwort" in cc._species_widgets
    assert "neon_tetra" in cc._species_widgets
    assert "butterfly_blue" in cc._species_widgets

    # Check cat and mermaid are temporarily removed from dashboard widgets
    assert "cat" not in cc._species_widgets
    assert "mermaid" not in cc._species_widgets

    # Check hornwort xmas widgets exist
    hw = cc._species_widgets["hornwort"]
    assert "xmas_toggle" in hw and hw["xmas_toggle"] is not None
    assert "xmas_mode" in hw and hw["xmas_mode"] is not None
    assert "xmas_theme" in hw and hw["xmas_theme"] is not None

    # Test cycling theme through all 5 palettes
    theme_keys = [k for k, _ in XMAS_THEMES]
    expected_themes = ["warm_gold", "candy_cane", "winter_frost", "mistletoe", "multicolor"]
    for exp in expected_themes:
        cc._on_hornwort_xmas_theme_clicked()
        assert settings.get("overlays", "hornwort_xmas_theme") == exp

    # Check betta breed dropdown widget
    bf = cc._species_widgets["betta_fish"]
    assert "betta_breed" in bf and bf["betta_breed"] is not None
    assert bf["betta_breed"].count() == len(BETTA_BREEDS) == 10

    # Test changing betta breed
    bf["betta_breed"].setCurrentIndex(0)  # sunburst
    assert settings.get("overlays", "betta_fish_breed") == "sunburst"

    bf["betta_breed"].setCurrentIndex(1)  # buttercup
    assert settings.get("overlays", "betta_fish_breed") == "buttercup"

    bf["betta_breed"].setCurrentIndex(2)  # mustard_gas
    assert settings.get("overlays", "betta_fish_breed") == "mustard_gas"

    bf["betta_breed"].setCurrentIndex(8)  # abyssal_glass
    assert settings.get("overlays", "betta_fish_breed") == "abyssal_glass"

def test_betta_fullscreen_exploration_parameters():
    with open("beta7.html", "r", encoding="utf-8") as f:
        content = f.read()

    # Verify boundary margins allow full screen coverage
    assert "Math.min(50,Math.max(20,scale*0.60))" in content
    assert "Math.min(30,Math.max(15,scale*0.35))" in content
    assert "Math.min(35,Math.max(18,scale*0.40))" in content

    # Verify drive speed and vertical agility
    assert "fish.mode==='cruise'?52" in content
    assert "clamp(vertical*.18,-38,38)" in content

    # Verify full screen target picking and sector diversity
    assert "Math.hypot(targetX-fish.x,targetY-fish.y)<260" in content
    assert "{length:16}" in content
    assert "Math.min(55,scale*0.85)" in content
    assert "state.time+6.0" in content

def test_betta_pointer_poke_and_dart():
    with open("beta7.html", "r", encoding="utf-8") as f:
        content = f.read()

    # Verify poke detection and dartAway functions
    assert "function dartAway(fish,pokePoint)" in content
    assert "function checkPoke(point)" in content

    # Verify dart kinematics and high speed burst propulsion
    assert "fish.targetKind='dart'" in content
    assert "burstPower=fish.targetKind==='dart'?580:440" in content
    assert "fish.targetKind==='dart'?96:fish.mode==='cruise'?52" in content

    # Verify water shockwave ripple on poke
    assert "state.ripples.push({x:clamp(fish.x/state.width,0,1)" in content

    # Verify integration with pointer moves and canvas clicks
    assert "if(checkPoke(point))return;" in content
    assert "window.pokeFish = function(x, y)" in content

def test_betta_sunburst_butterfly_breed():
    with open("beta7.html", "r", encoding="utf-8") as f:
        content = f.read()

    # Verify breed map and shader support for sunburst
    assert "'sunburst':7" in content
    assert "isSunburst =step(6.5,uBreed)" in content
    assert "bSunburst=" in content
    assert "rimSunburst" in content

    # Verify tri-band fin zoning: root cyan, scarlet red sunburst, midnight smoke rim
    assert "cSunRoot=" in content
    assert "cSunRed=" in content
    assert "cSunSmoke=" in content
    assert "cobaltSunburst=" in content

def test_betta_abyssal_glass_breed():
    with open("beta7.html", "r", encoding="utf-8") as f:
        content = f.read()

    # Verify breed map and shader activation for abyssal_glass
    assert "'abyssal_glass':8" in content
    assert "isGlass    =step(7.5,uBreed)" in content

    # Verify bioluminescent internal skeleton & viscera organs
    assert "spineMask=" in content
    assert "spineGlow=" in content
    assert "visceraColor=" in content
    assert "visceraPulse=" in content

    # Verify lateral photophore nodes and ctenophore iridescent diffraction
    assert "latNodes=" in content
    assert "photophoreColor=" in content
    assert "bodyCtenoPhase=" in content
    assert "ctenoWave=" in content

    # Verify crystal glass translucent body and fin optics
    assert "glassFresnel=" in content
    assert "glassAlpha=" in content
    assert "bodyAlpha=mix(uOpacity,glassAlpha*uOpacity,isGlass)" in content
    assert "glassFinAlpha=" in content







