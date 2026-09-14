# Ohverlay Marketplace Overlays

Finished and in-progress nature overlays created for the Ohverlay marketplace live here.

## Production overlays

- `moon-overlay.html` — local Moon with real phase, altitude, distance variation, atmospheric appearance, and occasional clouds
- `cosmos-overlay.html` — one branching Cosmos plant at the right edge; flowers and buds share the main stem and side shoots, with coupled cursor motion and an eight-hour bloom-and-shed cycle. The count setting adjusts flower sites on that plant, and its separate bloom slider defaults to about two inches. Sulphur Cosmos uses the transparent botanical bloom asset in `assets/`.
- `orchid-overlay.html` — living Phalaenopsis with an arching raceme, waxy flowers, subtle cursor physics, and an eight-hour succession cycle
- `butterflies-blue-overlay.html` — blue photo-textured butterfly
- `butterflies-yellow-overlay.html` — yellow photo-textured butterfly
- `butterflies-orange-overlay.html` — orange photo-textured butterfly
- `butterflies-overlay.html` — base butterfly implementation

## Supporting material

- `docs/` contains research notes.
- `butterfly-studies/` contains butterfly development studies and combined demonstrations.

Runtime paths are registered in `modules/overlay_manager.py` and packaged through `ohverlay.spec`.
