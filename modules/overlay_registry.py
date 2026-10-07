"""
Single source of truth for every overlay Ohverlay can run.

This module is intentionally Qt-free so ``config.settings``, the PyInstaller spec,
the Control Center, and the tests can all import it without pulling in WebEngine.

Entry keys
----------
id, name, file, category, description     identity + asset
extra_params                              fixed URL query params for the page
interactive / window_size                 accepts input / fixed-size window
count                                     default instance count (None = not user countable)
panel_label                               label shown in the Control Center species list
                                          (entries without it are not listed there)
"""

from __future__ import annotations

from typing import Dict, Iterable, List

_AMBIENT_PARAMS = {"transparent": "1", "controls": "0"}

OVERLAY_REGISTRY: List[dict] = [
    {
        "id": "moon",
        "name": "Local Moon",
        "file": "marketplace-overlays/moon-overlay.html",
        "category": "ambient",
        "description": "Local Moon with current phase, orientation, distance, true sky altitude, and occasional drifting clouds",
        "extra_params": dict(_AMBIENT_PARAMS),
        "count": 1,
        "panel_label": "Local Moon",
    },
    {
        "id": "orchid",
        "name": "Living Moth Orchid",
        "file": "marketplace-overlays/orchid-overlay.html",
        "category": "ambient",
        "description": "Waxy Phalaenopsis with an arching flower spike, cursor physics, and an eight-hour bloom succession",
        "extra_params": dict(_AMBIENT_PARAMS),
        "count": 1,
        "opacity": 0.94,
        "panel_label": "Living Orchid",
    },
    {
        "id": "butterfly_blue",
        "name": "Blue Butterfly",
        "file": "marketplace-overlays/butterflies-blue-overlay.html",
        "category": "ambient",
        "description": "Photo-textured 3D Blue Butterfly with realistic flight and landing",
        "extra_params": dict(_AMBIENT_PARAMS),
        "count": 1,
        "panel_label": "Blue Butterfly",
    },
    {
        "id": "butterfly_yellow",
        "name": "Yellow Butterfly",
        "file": "marketplace-overlays/butterflies-yellow-overlay.html",
        "category": "ambient",
        "description": "Photo-textured 3D Yellow Butterfly with realistic flight and landing",
        "extra_params": dict(_AMBIENT_PARAMS),
        "count": 1,
        "panel_label": "Yellow Butterfly",
    },
    {
        "id": "butterfly_orange",
        "name": "Orange Butterfly",
        "file": "marketplace-overlays/butterflies-orange-overlay.html",
        "category": "ambient",
        "description": "Photo-textured 3D Orange Butterfly with realistic flight and landing",
        "extra_params": dict(_AMBIENT_PARAMS),
        "count": 1,
        "panel_label": "Orange Butterfly",
    },
    {
        "id": "hornwort",
        "name": "Hornwort Plant",
        "file": "ohverlay-hornwort.html",
        "category": "ambient",
        "description": "Eight-hour growing hornwort plant with gentle water physics",
        "extra_params": dict(_AMBIENT_PARAMS),
        "count": 4,
        "panel_label": "Hornwort Plant",
    },
    {
        "id": "neon_tetra",
        "name": "Neon Tetra",
        "file": "tetra-overlay.html",
        "category": "ambient",
        "description": "Realistic 3D WebGL Neon Tetra with volumetric head-led turns and translucent fins",
        "extra_params": dict(_AMBIENT_PARAMS),
        "count": 2,
        "panel_label": "Neon Tetra",
    },
    {
        "id": "betta_fish",
        "name": "Betta Fish",
        "file": "beta7.html",
        "category": "ambient",
        "description": "Hyperrealistic Canary-Gold & Cobalt Blue Halfmoon Betta Fish with procedural fins and view-dependent highlights",
        "extra_params": dict(_AMBIENT_PARAMS),
        "count": 1,
        "panel_label": "Betta Fish",
    },
    {
        "id": "cichlid",
        "name": "Jewel Cichlid",
        "file": "jewel-cichlid1 (6).html",
        "category": "ambient",
        "description": "Three-dimensional red-orange Jewel Cichlid with cyan reflective speckles, front-view inspection and gill cover respiration",
        "extra_params": dict(_AMBIENT_PARAMS),
        "count": 1,
        "panel_label": "Jewel Cichlid",
    },
    {
        "id": "nature_world",
        "name": "Unified Nature World",
        "file": "nature-world-overlay.html",
        "category": "ambient",
        "description": "Unified single-canvas nature world with dragonflies, fireflies, and dandelions",
        "count": None,
    },
    {
        "id": "fireflies",
        "name": "Fireflies",
        "file": "fireflies-overlay.html",
        "category": "ambient",
        "description": "Six realistic fireflies flying and flashing independently",
        "count": 6,
        "panel_label": "Fireflies",
    },
    {
        "id": "dandelions",
        "name": "Dandelion Seeds",
        "file": "dandelions-overlay.html",
        "category": "ambient",
        "description": "Dandelion seeds floating and drifting",
        "count": 3,
        "panel_label": "Dandelions",
    },
    {
        "id": "dragonflies",
        "name": "Realistic Dragonflies",
        "file": "dragonflies-overlay.html",
        "category": "ambient",
        "description": "High-fidelity WebGL dragonfly flight study with species presets, aerodynamic steering, and interactive reactions",
        "extra_params": dict(_AMBIENT_PARAMS),
        "count": 2,
        "panel_label": "Dragonflies",
    },
    {
        "id": "sticky_note",
        "name": "Vintage Sticky Note",
        "file": "sticky-note-overlay.html",
        "category": "office",
        "description": "Persistent technical instruction note with task deadline countdown, pin/tape styles, and drag-and-drop",
        "count": None,
    },
    {
        "id": "exam_reviewer",
        "name": "Exam & Study Reviewer",
        "file": "exam-reviewer-overlay.html",
        "category": "learning",
        "description": "Spaced repetition exam study flashcard overlay",
        "count": None,
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
        "count": 1,
        "panel_label": "Telegrama Card",
    },
]

# Non-HTML assets that must ship next to the overlays (PyInstaller `datas`).
EXTRA_BUNDLED_ASSETS = [
    ("modules/telegrama_mobile.html", "modules"),
]


def get_overlay_info(overlay_id: str):
    return next((item for item in OVERLAY_REGISTRY if item["id"] == overlay_id), None)


def panel_species() -> List[dict]:
    """Entries that appear in the Control Center species list, in display order."""
    return [item for item in OVERLAY_REGISTRY if item.get("panel_label")]


def species_count_defaults() -> Dict[str, int]:
    return {item["id"]: int(item["count"]) for item in OVERLAY_REGISTRY if item.get("count")}


def bundled_data_files(extra: Iterable[tuple] = EXTRA_BUNDLED_ASSETS) -> List[tuple]:
    """(source, dest_dir) pairs used by ``ohverlay.spec`` so the spec cannot drift from the registry."""
    seen, files = set(), []
    for item in OVERLAY_REGISTRY:
        src = item["file"]
        if src in seen:
            continue
        seen.add(src)
        dest = src.rsplit("/", 1)[0] if "/" in src else "."
        files.append((src, dest))
    for src, dest in extra:
        if src not in seen:
            seen.add(src)
            files.append((src, dest))
    return files
