"""
Configuration management with JSON persistence.
All user settings are stored locally and loaded on startup.
"""

import json
import os
import shutil
import copy
from utils.logger import logger

APP_DIR_NAME = ".ohverlay"


def get_app_data_dir():
    """Return the application directory, respecting OHVERLAY_HOME if set."""
    env_dir = os.environ.get("OHVERLAY_HOME")
    if env_dir:
        return env_dir
    app_dir = os.path.join(os.path.expanduser("~"), APP_DIR_NAME)
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


DEFAULT_CONFIG = {
    "overlays": {
        "fireflies": True,
        "dragonflies": False,
        "dandelions": False,
        "orchid": False,
        "moon": False,
        "butterfly_blue": False,
        "butterfly_yellow": False,
        "butterfly_orange": False,
        "butterfly_mix": False,
        "hornwort": False,
        "neon_tetra": False,
        "mermaid": False,
        "telegrama": False,
        "betta_fish": False,
        "cat": False,
        "cichlid": False,
        "fireflies_count": 6,
        "dragonflies_count": 2,
        "dandelions_count": 3,
        "orchid_count": 1,
        "moon_count": 1,
        "butterfly_blue_count": 1,
        "butterfly_yellow_count": 1,
        "butterfly_orange_count": 1,
        "butterfly_mix_count": 3,
        "hornwort_count": 4,
        "neon_tetra_count": 2,
        "mermaid_count": 1,
        "telegrama_count": 1,
        "betta_fish_count": 1,
        "cat_count": 1,
        "cichlid_count": 1,
        "fireflies_scale": 1.0,
        "dragonflies_scale": 1.0,
        "dandelions_scale": 1.0,
        "orchid_scale": 1.0,
        "moon_scale": 1.0,
        "butterfly_blue_scale": 1.0,
        "butterfly_yellow_scale": 1.0,
        "butterfly_orange_scale": 1.0,
        "butterfly_mix_scale": 1.0,
        "hornwort_scale": 1.0,
        "neon_tetra_scale": 1.0,
        "mermaid_scale": 1.0,
        "telegrama_scale": 1.0,
        "betta_fish_scale": 1.0,
        "cat_scale": 1.0,
        "cichlid_scale": 1.0,
        "fireflies_opacity": 1.0,
        "dragonflies_opacity": 1.0,
        "dragonflies_palette": "mixed",
        "dragonflies_style": "percher",
        "dandelions_opacity": 1.0,
        "dandelions_style": "cyan",
        "orchid_opacity": 0.94,
        "orchid_color": "fuchsia",
        "moon_opacity": 1.0,
        "moon_latitude": None,
        "moon_longitude": None,
        "butterfly_blue_opacity": 1.0,
        "butterfly_yellow_opacity": 1.0,
        "butterfly_orange_opacity": 1.0,
        "hornwort_opacity": 1.0,
        "neon_tetra_opacity": 1.0,
        "mermaid_opacity": 1.0,
        "telegrama_opacity": 1.0,
        "betta_fish_opacity": 1.0,
        "betta_fish_breed": "buttercup",
        "cat_opacity": 1.0,
        "cichlid_opacity": 1.0,
        "hornwort_growth_speed": 1.0,
        "hornwort_xmas_lights": False,
        "hornwort_xmas_mode": "twinkle",
        "hornwort_xmas_theme": "multicolor",
    },
    "nature": {
        "render_mode": "standalone_compatibility",
        "physics_preset": "lively",
        "interaction_strength": 1.0
    },
    "control_center": {
        "pinned": False
    },
    "onboarding": {
        "welcome_completed": False
    },
    "hotkeys": {
        "toggle_visibility": "ctrl+alt+h"
    },
    "app": {
        "version": "1.0.0"
    }
}


class Settings:
    """Handles loading, saving, and querying configuration values."""

    def __init__(self, config_path=None):
        if config_path:
            self.config_path = config_path
        else:
            self.config_path = os.path.join(get_app_data_dir(), "config.json")

        self.data = copy.deepcopy(DEFAULT_CONFIG)
        self.load()

    def load(self):
        """Load settings from JSON file, falling back to defaults on error."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_data = json.load(f)
                self._merge(self.data, user_data)
                self._validate()
                logger.info(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {self.config_path}: {e}. Using defaults.")
                self.data = copy.deepcopy(DEFAULT_CONFIG)
        else:
            logger.info("No configuration file found. Creating with defaults.")
            self.save()

    def _validate(self):
        """Ensure critical values are within safe boundaries."""
        overlays = self.data.get("overlays", {})

        species_defaults = {
            "fireflies_count": 6,
            "dragonflies_count": 2,
            "dandelions_count": 3,
                "orchid_count": 1,
            "moon_count": 1,
            "butterfly_blue_count": 1,
            "butterfly_yellow_count": 1,
            "butterfly_orange_count": 1,
            "butterfly_mix_count": 3,
            "hornwort_count": 4,
            "neon_tetra_count": 2,
            "mermaid_count": 1,
            "telegrama_count": 1,
            "betta_fish_count": 1,
            "cat_count": 1,
            "cichlid_count": 1,
        }

        for key, default_val in species_defaults.items():
            val = overlays.get(key)
            try:
                val_int = int(val)
                if not (1 <= val_int <= 12):
                    overlays[key] = default_val
                else:
                    overlays[key] = val_int
            except (ValueError, TypeError):
                overlays[key] = default_val

        for k in list(overlays.keys()):
            if k.endswith("_opacity"):
                try:
                    op = float(overlays[k])
                    overlays[k] = max(0.1, min(1.0, op))
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

        valid_breeds = {"mustard_gas", "koi", "samurai", "super_red", "royal_blue", "copper", "buttercup", "sunburst", "abyssal_glass", "mix"}
        if overlays.get("betta_fish_breed") not in valid_breeds:
            overlays["betta_fish_breed"] = "buttercup"

        valid_palettes = {
            "mixed", "reference", "emperor-male", "emperor-female",
            "ruddy-male", "ruddy-female", "skimmer-male", "skimmer-female",
            "keeled-male", "keeled-female"
        }
        if overlays.get("dragonflies_palette") not in valid_palettes:
            overlays["dragonflies_palette"] = "mixed"

        valid_styles = {"percher", "patrol"}
        if overlays.get("dragonflies_style") not in valid_styles:
            overlays["dragonflies_style"] = "percher"

        valid_dandelion_styles = {"classic", "cyan", "violet", "emerald", "mix"}
        if overlays.get("dandelions_style") not in valid_dandelion_styles:
            overlays["dandelions_style"] = "cyan"

    def save(self):
        """Write the current settings back to disk atomically."""
        try:
            parent_dir = os.path.dirname(self.config_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            temp_path = self.config_path + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
            shutil.move(temp_path, self.config_path)
            logger.debug("Settings saved.")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def _merge(self, default_dict, user_dict):
        """Recursively merge user settings into the default structure."""
        for key, value in default_dict.items():
            if key in user_dict:
                if isinstance(value, dict) and isinstance(user_dict[key], dict):
                    self._merge(value, user_dict[key])
                else:
                    default_dict[key] = user_dict[key]

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
        self.save()
