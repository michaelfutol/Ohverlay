import time
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRect

from config.settings import Settings
from modules.rest_mode import RestModeController, RestBackdropWindow
from ui.control_center import ControlCenter


def _get_app():
    return QApplication.instance() or QApplication([])


def test_rest_mode_controller_init(tmp_path):
    _get_app()
    settings = Settings(config_path=str(tmp_path / "config.json"))
    mgr = MagicMock()
    mgr._get_combined_screen_geometry.return_value = QRect(0, 0, 1920, 1080)
    mgr.get_active_ids.return_value = []
    mgr._active = {}

    controller = RestModeController(mgr, config=settings)
    assert not controller.is_active()
    assert controller.auto_rotate is True
    assert controller.interval_minutes == 5
    assert controller.get_eligible_species()


def test_rest_mode_enter_and_exit(tmp_path):
    _get_app()
    settings = Settings(config_path=str(tmp_path / "config.json"))
    mgr = MagicMock()
    mgr._get_combined_screen_geometry.return_value = QRect(0, 0, 1920, 1080)
    mgr.get_active_ids.return_value = ["fireflies"]
    mgr._active = {}

    controller = RestModeController(mgr, config=settings)
    assert not controller.is_active()

    controller.enter_rest_mode()
    assert controller.is_active()
    assert controller.backdrop_window is not None
    assert controller.backdrop_window.isVisible()
    assert controller.saved_overlays == ["fireflies"]

    controller.exit_rest_mode()
    assert not controller.is_active()
    assert not controller.backdrop_window.isVisible()


def test_double_escape_detection(tmp_path):
    _get_app()
    settings = Settings(config_path=str(tmp_path / "config.json"))
    mgr = MagicMock()
    mgr._get_combined_screen_geometry.return_value = QRect(0, 0, 1920, 1080)
    mgr.get_active_ids.return_value = []
    mgr._active = {}

    controller = RestModeController(mgr, config=settings)
    controller.enter_rest_mode()
    assert controller.is_active()

    # First Escape press -> should return False and stay in Rest Mode
    res1 = controller.handle_escape()
    assert res1 is False
    assert controller.is_active()
    assert controller.backdrop_window.toast.isVisible()

    # Second Escape press immediately (< 750ms) -> should exit Rest Mode
    res2 = controller.handle_escape()
    assert res2 is True
    assert not controller.is_active()


def test_escape_timeout_resets(tmp_path):
    _get_app()
    settings = Settings(config_path=str(tmp_path / "config.json"))
    mgr = MagicMock()
    mgr._get_combined_screen_geometry.return_value = QRect(0, 0, 1920, 1080)
    mgr.get_active_ids.return_value = []
    mgr._active = {}

    controller = RestModeController(mgr, config=settings)
    controller.enter_rest_mode()

    # First press
    controller.handle_escape()
    # Simulate gap greater than threshold
    controller.last_escape_time = time.time() - 1.5

    # Second press after delay -> treated as new first press
    res = controller.handle_escape()
    assert res is False
    assert controller.is_active()
    controller.exit_rest_mode()


def test_auto_rotation_interval_and_clamping(tmp_path):
    _get_app()
    settings = Settings(config_path=str(tmp_path / "config.json"))
    mgr = MagicMock()
    mgr._get_combined_screen_geometry.return_value = QRect(0, 0, 1920, 1080)
    mgr.get_active_ids.return_value = []
    mgr._active = {}

    controller = RestModeController(mgr, config=settings)
    controller.set_rotation_interval(15)
    assert controller.interval_minutes == 15
    assert settings.get("rest_mode", "rotation_interval_minutes") == 15

    # Clamping
    controller.set_rotation_interval(999)
    assert controller.interval_minutes == 60

    controller.set_rotation_interval(-5)
    assert controller.interval_minutes == 1

    # Toggle rotate
    controller.set_auto_rotate(False)
    assert controller.auto_rotate is False
    assert settings.get("rest_mode", "auto_rotate") is False


def test_species_rotation_cycle(tmp_path):
    _get_app()
    settings = Settings(config_path=str(tmp_path / "config.json"))
    mgr = MagicMock()
    mgr._get_combined_screen_geometry.return_value = QRect(0, 0, 1920, 1080)
    mgr.get_active_ids.return_value = ["fireflies"]
    mgr._active = {}

    rotated_species = []
    controller = RestModeController(mgr, config=settings)
    controller.species_rotated.connect(lambda s: rotated_species.append(s))

    controller.enter_rest_mode()
    controller._on_rotate_timeout()

    assert len(rotated_species) == 1
    assert rotated_species[0] in controller.get_eligible_species()
    # Verified old species closed and new one opened
    mgr.close_overlay.assert_called_with("fireflies", save_state=False)
    mgr.open_overlay.assert_called_with(rotated_species[0], save_state=False)
    controller.exit_rest_mode()


def test_control_center_rest_mode_ui(tmp_path):
    _get_app()
    settings = Settings(config_path=str(tmp_path / "config.json"))
    mgr = MagicMock()
    mgr._get_combined_screen_geometry.return_value = QRect(0, 0, 1920, 1080)
    mgr.get_active_ids.return_value = []
    mgr._active = {}
    mgr.is_rest_mode_active.return_value = False

    ctrl = ControlCenter(config=settings, overlay_manager=mgr)
    assert hasattr(ctrl, "enter_rest_btn")
    assert hasattr(ctrl, "rotate_toggle_btn")
    assert hasattr(ctrl, "rotate_slider")
    assert hasattr(ctrl, "rotate_val_lbl")

    # Enter button click invokes toggle_rest_mode
    ctrl.enter_rest_btn.click()
    mgr.toggle_rest_mode.assert_called_once()

    # Slider changes interval
    ctrl.rotate_slider.setValue(20)
    assert ctrl.rotate_val_lbl.text() == "20 mins"
    assert settings.get("rest_mode", "rotation_interval_minutes") == 20

    # Slider at max 60 shows 1 hr
    ctrl.rotate_slider.setValue(60)
    assert ctrl.rotate_val_lbl.text() == "1 hr"

    ctrl.close()
