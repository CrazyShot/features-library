# Tests

Playwright (Python) scripts that run the **game in headless Chromium** with real keyboard/mouse input.
They need the game build **you want to test**, saved as `index.html` in a folder you point to; the full game is deliberately *not* in this repository.

```
pip install playwright && playwright install chromium
GAME_DIR=/path/to/folder-containing-index.html python3 <script>.py
```
Results in this repo's `INTEGRATION.md` files were produced in headless Chromium with software rendering (no GPU), so frame-rate figures are relative only.

The tests look for helper files `vt_find.js` / `vt_find_all.js` in the current directory: run them from this `tests/` folder.
`test_visual_depth_fog_selection.py` has one known-unreliable check (tree-layer counts over a fixed 120 ms window depend on how many frames render); `test_tree_layers_and_hit_test.py` is the exact per-frame version. `test_panel_wave_perf.py` contains one obsolete check (control groups v1 Alt+1 recall, replaced by CTRLGROUPS-2.0.0).
