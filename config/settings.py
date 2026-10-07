"""
Configuration management with JSON persistence.
All user settings are stored locally and loaded on startup.

Design notes
------------
* Defaults for per-overlay keys (toggle/count/scale/opacity) are *derived* from
  ``modules.overlay_registry`` so adding an overlay never requires editing this file.
* Unknown keys/sections found in the user's file are **preserved** (previously they were
  silently discarded on load, which wiped sticky notes on every restart).
* Writes are atomic (``os.replace``) and can be debounced so rapid edits (e.g. typing in a
  sticky note) coalesce into one disk write instead of one write per keystroke.
* Sticky notes live in their own ``notes.json`` (auto-migrated from the old
  ``config.json["sticky_notes"]["notes"]`` location) so a settings glitch can't take notes
  with it, and every notes write keeps a ``.bak`` of the previous good copy.
"""

import copy
import json
import os
import secrets
import threading

from modules.overlay_registry import panel_species
from utils.logger import logger

APP_DIR_NAME = ".ohverlay"

# Overlays that were removed from the product; their keys are pruned from old config files.
STALE_OVERLAY_IDS = ("mermaid", "cat", "butterfly_mix", "cosmos", "lumen", "jellyfish")

DEFAULT_TELEGRAMA_PORT = 54321


def get_app_data_dir():
    """Return the application directory, respecting OHVERLAY_HOME if set."""
    env_dir = os.environ.get("OHVERLAY_HOME")
    if env_dir:
        os.makedirs(env_dir, exist_ok=True)
        return env_dir
    app_dir = os.path.join(os.path.expanduser("~"), APP_DIR_NAME)
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


def _build_overlay_defaults():
    overlays = {}
    species = panel_species()
    for item in species:
        overlays[item["id"]] = item["id"] == "fireflies"
    for item in species:
        overlays[f"{item['id']}_count"] = int(item.get("count") or 1)
    for item in species:
        overlays[f"{item['id']}_scale"] = 1.0
    for item in species:
        overlays[f"{item['id']}_opacity"] = float(item.get("opacity", 1.0))
    overlays.update({
        "dragonflies_palette": "mixed",
        "dragonflies_style": "percher",
        "dandelions_style": "cyan",
        "orchid_color": "fuchsia",
        "moon_latitude": None,
        "moon_longitude": None,
        "betta_fish_breed": "buttercup",
        "hornwort_growth_speed": 1.0,
        "hornwort_xmas_lights": False,
        "hornwort_xmas_mode": "twinkle",
        "hornwort_xmas_theme": "multicolor",
    })
    return overlays


DEFAULT_CONFIG = {
    "overlays": _build_overlay_defaults(),
    "nature": {
        "render_mode": "standalone_compatibility",
        "physics_preset": "lively",
        "interaction_strength": 1.0,
    },
    "control_center": {
        "pinned": False,
    },
    "onboarding": {
        "welcome_completed": False,
    },
    "hotkeys": {
        "toggle_visibility": "ctrl+alt+h",
    },
    "rest_mode": {
        "auto_rotate": True,
        "rotation_interval_minutes": 5,
        "restore_on_exit": True,
    },
    "performance": {
        # Hide (and freeze) overlays while another app is fullscreen (games, video, slides).
        "pause_on_fullscreen": True,
    },
    "telegrama": {
        # Opt-in: nothing listens on the network until the user turns this on.
        "enabled": False,
        # False = loopback only. True = reachable from phones on the same Wi-Fi (token required).
        "allow_lan": False,
        "port": DEFAULT_TELEGRAMA_PORT,
        "token": "",
        "notify": True,
    },
    "app": {
        "version": "1.0.0",
    },
}


def _atomic_write_json(path, data, *, indent=4, keep_backup=False):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    if keep_backup and os.path.exists(path):
        try:
            with open(path, "rb") as src, open(path + ".bak", "wb") as dst:
                dst.write(src.read())
        except OSError as exc:  # a failed backup must never block the real save
            logger.warning(f"Could not refresh backup for {path}: {exc}")
    os.replace(tmp_path, path)


class Settings:
    """Handles loading, saving, and querying configuration values."""

    def __init__(self, config_path=None, debounce_ms=0):
        if config_path:
            self.config_path = config_path
        else:
            self.config_path = os.path.join(get_app_data_dir(), "config.json")
        self.notes_path = os.path.join(os.path.dirname(os.path.abspath(self.config_path)), "notes.json")

        self._debounce_ms = max(0, int(debounce_ms))
        self._timer = None
        self._lock = threading.RLock()
        self._dirty = False
        self._notes_dirty = False
        self._notes = []

        self.data = copy.deepcopy(DEFAULT_CONFIG)
        self.load()

    # ------------------------------------------------------------------ load
    def load(self):
        """Load settings from JSON file, falling back to defaults on error."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_data = json.load(f)
                if not isinstance(user_data, dict):
                    raise ValueError("config root must be an object")
                self._merge(self.data, user_data)
                self._prune_stale()
                self._validate()
                logger.info(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {self.config_path}: {e}. Using defaults.")
                self._quarantine_corrupt_config()
                self.data = copy.deepcopy(DEFAULT_CONFIG)
        else:
            logger.info("No configuration file found. Creating with defaults.")
            self.save()
        self._load_notes()

    def _quarantine_corrupt_config(self):
        """Keep an unreadable config for inspection instead of silently overwriting it."""
        try:
            if os.path.exists(self.config_path):
                os.replace(self.config_path, self.config_path + ".corrupt")
        except OSError:
            pass

    def _prune_stale(self):
        overlays = self.data.get("overlays", {})
        for stale in STALE_OVERLAY_IDS:
            for key in (stale, f"{stale}_count", f"{stale}_scale", f"{stale}_opacity"):
                overlays.pop(key, None)

    def _validate(self):
        """Ensure critical values are within safe boundaries."""
        overlays = self.data.get("overlays", {})

        for item in panel_species():
            key = f"{item['id']}_count"
            default_val = int(item.get("count") or 1)
            try:
                val_int = int(overlays.get(key))
                overlays[key] = val_int if 1 <= val_int <= 12 else default_val
            except (ValueError, TypeError):
                overlays[key] = default_val

        for k in list(overlays.keys()):
            if k.endswith("_opacity"):
                try:
                    overlays[k] = max(0.1, min(1.0, float(overlays[k])))
                except (ValueError, TypeError):
                    overlays[k] = 1.0

        for key, low, high in (("moon_latitude", -90.0, 90.0), ("moon_longitude", -180.0, 180.0)):
            value = overlays.get(key)
            if value in (None, ""):
                overlays[key] = None
                continue
            try:
                overlays[key] = max(low, min(high, float(value)))
            except (ValueError, TypeError):
                overlays[key] = None

        try:
            spd = float(overlays.get("hornwort_growth_speed", 1.0))
            overlays["hornwort_growth_speed"] = max(1.0, min(5.0, spd))
        except (ValueError, TypeError):
            overlays["hornwort_growth_speed"] = 1.0

        valid_breeds = {"mustard_gas", "koi", "samurai", "super_red", "royal_blue", "copper",
                        "buttercup", "sunburst", "abyssal_glass", "mix"}
        if overlays.get("betta_fish_breed") not in valid_breeds:
            overlays["betta_fish_breed"] = "buttercup"

        valid_palettes = {
            "mixed", "reference", "emperor-male", "emperor-female",
            "ruddy-male", "ruddy-female", "skimmer-male", "skimmer-female",
            "keeled-male", "keeled-female",
        }
        if overlays.get("dragonflies_palette") not in valid_palettes:
            overlays["dragonflies_palette"] = "mixed"

        if overlays.get("dragonflies_style") not in {"percher", "patrol"}:
            overlays["dragonflies_style"] = "percher"

        if overlays.get("dandelions_style") not in {"classic", "cyan", "violet", "emerald", "mix"}:
            overlays["dandelions_style"] = "cyan"

        if overlays.get("orchid_color") not in {"fuchsia", "blush", "white", "violet", "sunset"}:
            overlays["orchid_color"] = "fuchsia"

        rest_cfg = self.data.setdefault("rest_mode", {})
        rest_cfg.setdefault("auto_rotate", True)
        rest_cfg.setdefault("restore_on_exit", True)
        try:
            val = int(rest_cfg.get("rotation_interval_minutes", 5))
            rest_cfg["rotation_interval_minutes"] = max(1, min(60, val))
        except (ValueError, TypeError):
            rest_cfg["rotation_interval_minutes"] = 5

        perf = self.data.setdefault("performance", {})
        perf["pause_on_fullscreen"] = bool(perf.get("pause_on_fullscreen", True))

        tg = self.data.setdefault("telegrama", {})
        tg["enabled"] = bool(tg.get("enabled", False))
        tg["allow_lan"] = bool(tg.get("allow_lan", False))
        tg["notify"] = bool(tg.get("notify", True))
        try:
            port = int(tg.get("port", DEFAULT_TELEGRAMA_PORT))
            tg["port"] = port if 1024 <= port <= 65535 else DEFAULT_TELEGRAMA_PORT
        except (ValueError, TypeError):
            tg["port"] = DEFAULT_TELEGRAMA_PORT
        if not isinstance(tg.get("token"), str):
            tg["token"] = ""

    # ----------------------------------------------------------------- notes
    def _load_notes(self):
        """Load sticky notes from notes.json, migrating from the legacy config location."""
        legacy = (self.data.get("sticky_notes") or {}).get("notes") if isinstance(self.data.get("sticky_notes"), dict) else None

        notes = None
        for candidate in (self.notes_path, self.notes_path + ".bak"):
            if os.path.exists(candidate):
                try:
                    with open(candidate, "r", encoding="utf-8") as f:
                        loaded = json.load(f)
                    if isinstance(loaded, list):
                        notes = loaded
                        if candidate.endswith(".bak"):
                            logger.warning("notes.json unreadable — restored from notes.json.bak")
                        break
                except Exception as exc:
                    logger.warning(f"Failed to read {candidate}: {exc}")

        if notes is None:
            notes = list(legacy) if isinstance(legacy, list) else []
            if notes:
                logger.info(f"Migrating {len(notes)} sticky note(s) to {self.notes_path}")
                self._notes = notes
                try:
                    _atomic_write_json(self.notes_path, notes, keep_backup=True)
                except Exception as exc:
                    logger.error(f"Notes migration write failed: {exc}")
                    return  # keep legacy copy in config until the write succeeds

        self._notes = notes
        if isinstance(self.data.get("sticky_notes"), dict) and "notes" in self.data["sticky_notes"] and os.path.exists(self.notes_path):
            # The authoritative copy is notes.json now; drop the duplicate from config.json.
            self.data["sticky_notes"].pop("notes", None)
            self._dirty = True
            self.flush()

    def get_notes(self):
        return copy.deepcopy(self._notes)

    def set_notes(self, notes):
        with self._lock:
            self._notes = copy.deepcopy(list(notes))
            self._notes_dirty = True
        self.request_save()

    # ------------------------------------------------------------------ save
    def save(self):
        """Write pending settings (and notes, if changed) to disk atomically."""
        with self._lock:
            try:
                _atomic_write_json(self.config_path, self.data)
                self._dirty = False
                if self._notes_dirty:
                    _atomic_write_json(self.notes_path, self._notes, keep_backup=True)
                    self._notes_dirty = False
                logger.debug("Settings saved.")
            except Exception as e:
                logger.error(f"Failed to save settings: {e}")

    def flush(self):
        """Write immediately if anything is pending (call on quit)."""
        with self._lock:
            pending = self._dirty or self._notes_dirty
        if self._timer is not None:
            try:
                self._timer.stop()
            except RuntimeError:
                pass
        if pending:
            self.save()

    def request_save(self):
        """Save now, or coalesce rapid calls into one write when debouncing is enabled."""
        self._dirty = True
        if self._debounce_ms <= 0 or not self._start_debounce():
            self.save()

    def _start_debounce(self):
        try:
            from PySide6.QtCore import QCoreApplication, QThread, QTimer
        except ImportError:
            return False
        app = QCoreApplication.instance()
        if app is None or QThread.currentThread() is not app.thread():
            return False
        if self._timer is None:
            self._timer = QTimer()
            self._timer.setSingleShot(True)
            self._timer.timeout.connect(self.flush)
        self._timer.start(self._debounce_ms)
        return True

    # ----------------------------------------------------------------- access
    def _merge(self, default_dict, user_dict):
        """Deep-merge user settings over defaults, preserving unknown user keys/sections."""
        for key, value in user_dict.items():
            if isinstance(default_dict.get(key), dict) and isinstance(value, dict):
                self._merge(default_dict[key], value)
            else:
                default_dict[key] = value

    def get(self, section, key=None):
        """Retrieve a section or a specific key within a section."""
        if key is None:
            return self.data.get(section, {})
        return self.data.get(section, {}).get(key)

    def set(self, section, key, value):
        """Update a specific key within a section and save to disk."""
        if section not in self.data:
            self.data[section] = {}
        self.data[section][key] = value
        self.request_save()

    def ensure_telegrama_token(self):
        """Return the Telegrama pairing token, generating a strong one on first use."""
        token = self.get("telegrama", "token")
        if not token:
            token = secrets.token_urlsafe(12)
            self.set("telegrama", "token", token)
        return token
