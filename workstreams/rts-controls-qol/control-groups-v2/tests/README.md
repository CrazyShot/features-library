# Tests

Playwright (Python) scripts that run the **game in headless Chromium** with real keyboard/mouse input.
They need the game build **you want to test**, saved as `index.html` in a folder you point to; the full game is deliberately *not* in this repository.

```
pip install playwright && playwright install chromium
GAME_DIR=/path/to/folder-containing-index.html python3 <script>.py
```
Results in this repo's `INTEGRATION.md` files were produced in headless Chromium with software rendering (no GPU), so frame-rate figures are relative only.

`test_cross_feature_imported_map.py` additionally needs the game started with `?map=embedded` (the MAPDATA-IMPORT-TEST feature) and tests control groups, repair and the vampire panel together.
