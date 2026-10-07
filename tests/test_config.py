import json

import config.settings as settings_module
from config.settings import (
    DEFAULT_CONFIG,
    Settings,
    get_app_data_dir,
)

def test_default_config_structure():
    assert "overlays" in DEFAULT_CONFIG
    assert "hotkeys" in DEFAULT_CONFIG
    assert "app" in DEFAULT_CONFIG

def test_settings_merge(tmp_path):
    settings = Settings(config_path=str(tmp_path / "config.json"))
    base = {"a": {"b": 1, "c": 2}, "d": 3}
    override = {"a": {"b": 10}, "e": 5}
    settings._merge(base, override)
    assert base["a"]["b"] == 10
    assert base["a"]["c"] == 2
    assert base["d"] == 3
    # Unknown keys are preserved: dropping them silently wiped sticky notes on every restart.
    assert base["e"] == 5


def test_unknown_sections_survive_load_and_save(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({
        "bubbles": {"note_theme": "sticky_paper_yellow"},
        "overlays": {"fireflies": False, "future_key": 7},
    }), encoding="utf-8")
    settings = Settings(config_path=str(path))
    settings.set("overlays", "moon", True)
    reloaded = Settings(config_path=str(path))
    assert reloaded.get("bubbles", "note_theme") == "sticky_paper_yellow"
    assert reloaded.get("overlays", "future_key") == 7
    assert reloaded.get("overlays", "moon") is True
    assert reloaded.get("overlays", "fireflies") is False


def test_legacy_sticky_notes_migrate_to_notes_json(tmp_path):
    path = tmp_path / "config.json"
    notes = [{"id": "n1", "text": "buy gamot", "x": 10, "y": 20}]
    path.write_text(json.dumps({"sticky_notes": {"notes": notes}}), encoding="utf-8")

    settings = Settings(config_path=str(path))
    assert settings.get_notes() == notes
    assert json.loads((tmp_path / "notes.json").read_text(encoding="utf-8")) == notes
    assert "notes" not in json.loads(path.read_text(encoding="utf-8")).get("sticky_notes", {})

    # Survives a restart (this is the path that used to lose every note)
    assert Settings(config_path=str(path)).get_notes() == notes


def test_notes_keep_backup_and_recover_from_corruption(tmp_path):
    path = tmp_path / "config.json"
    settings = Settings(config_path=str(path))
    settings.set_notes([{"id": "a", "text": "one"}])
    settings.set_notes([{"id": "a", "text": "two"}])
    assert (tmp_path / "notes.json.bak").exists()

    (tmp_path / "notes.json").write_text("{ not json", encoding="utf-8")
    recovered = Settings(config_path=str(path)).get_notes()
    assert recovered and recovered[0]["id"] == "a"


def test_corrupt_config_is_quarantined_not_overwritten(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{ broken", encoding="utf-8")
    settings = Settings(config_path=str(path))
    assert settings.get("overlays", "fireflies") is True  # defaults restored
    assert (tmp_path / "config.json.corrupt").exists()


def test_stale_overlay_keys_are_pruned(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"overlays": {"cat": True, "cat_count": 3, "mermaid_scale": 2.0}}), encoding="utf-8")
    overlays = Settings(config_path=str(path)).get("overlays")
    assert "cat" not in overlays and "cat_count" not in overlays and "mermaid_scale" not in overlays


def test_defaults_are_derived_from_registry():
    from modules.overlay_registry import panel_species

    overlays = DEFAULT_CONFIG["overlays"]
    for item in panel_species():
        oid = item["id"]
        assert oid in overlays
        assert overlays[f"{oid}_count"] == int(item["count"])
        assert f"{oid}_scale" in overlays and f"{oid}_opacity" in overlays


def test_debounced_saves_coalesce(tmp_path, qapp):
    from PySide6.QtTest import QTest

    path = tmp_path / "config.json"
    settings = Settings(config_path=str(path), debounce_ms=60)
    writes = []
    original = settings.save
    settings.save = lambda: (writes.append(1), original())[1]

    for i in range(25):
        settings.set("overlays", "moon_opacity", 0.5 + (i % 5) / 10)
    assert writes == []  # nothing written yet — edits are coalesced
    QTest.qWait(200)
    assert len(writes) == 1
    assert Settings(config_path=str(path)).get("overlays", "moon_opacity") == 0.9

    settings.set("overlays", "moon_opacity", 0.3)
    settings.flush()  # quit path writes immediately
    assert Settings(config_path=str(path)).get("overlays", "moon_opacity") == 0.3


def test_telegrama_is_opt_in_with_generated_token(tmp_path):
    settings = Settings(config_path=str(tmp_path / "config.json"))
    assert settings.get("telegrama", "enabled") is False
    assert settings.get("telegrama", "allow_lan") is False
    token = settings.ensure_telegrama_token()
    assert len(token) >= 12
    assert settings.ensure_telegrama_token() == token


def test_settings_get_set(tmp_path):
    config_file = tmp_path / ".ohverlay" / "config.json"
    settings = Settings(config_path=str(config_file))
    settings.set("overlays", "fireflies", True)
    assert settings.get("overlays", "fireflies") is True
    assert config_file.exists()

def test_app_data_helpers_respect_env_override(tmp_path, monkeypatch):
    app_home = tmp_path / "custom-ohverlay-home"
    monkeypatch.setenv("OHVERLAY_HOME", str(app_home))
    assert get_app_data_dir() == str(app_home)
