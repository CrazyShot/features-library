# Tests

Playwright (Python) scripts that run the **game in headless Chromium** with real keyboard/mouse input.
They need the game build **you want to test**, saved as `index.html` in a folder you point to; the full game is deliberately *not* in this repository.

```
pip install playwright && playwright install chromium
GAME_DIR=/path/to/folder-containing-index.html python3 <script>.py
```
Results in this repo's `INTEGRATION.md` files were produced in headless Chromium with software rendering (no GPU), so frame-rate figures are relative only.

Extra inputs: `MAPDATA_JSON=/path/to/bastion-map-256x256-bastion-001.json` (the **full Terrain Generator export is not in this repo**; scripts that load it need your copy).
`test_boot_and_verify.py` takes the page URL (`index.html?map=embedded` or `?map=crop192`) and a tag; `test_pixel_alignment.py` takes URL, tag and an optional crop size (see the script header).
