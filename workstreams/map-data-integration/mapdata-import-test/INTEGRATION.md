# Integration — MapData import test

## Target game revision
Prototype "Emberfall — RTS Map Prototype" (single-file index.html) as supplied 2026-10-08; main-repo commit: **to be filled in by the integrator**

## Dependencies
Hard: the 8 hooks below. Coexists with the other features (checked: control groups, vampire panel, repair, unit panel on the imported 256 map).

## Host touch points (edits to the main script — each guarded by `window.BASTION_IMPORT`)
| Hook | Where | What it does |
|---|---|---|
| H1 | `const N=112` | `N` comes from the MapData |
| H2 | `const pf=…` | the procedural dirt-road field is off on imported maps |
| H3 | `gc()` after the road blend | one new line: `terrain.grid` ground tint |
| H4 | first statement of `resF()` | stone/iron painting and `RES/RESI` read the MapData node tiles |
| H5 | resource-generation block | skip random deposits; keep `PATCH.length` truthy so `gc()` still calls `resF` |
| H6 | tree loop | tree count per tile = MapData tree mask (exactly 1) |
| H7 | before `D.sort` | gold ore sprites + glows |
| H8 | `initSurvival()` | HQ at the MapData position (falls back to `pickBase()`) |
Each hook is tagged `/*FEATURE: MAPDATA-IMPORT-TEST hook Hn*/`.
Coordinates: tile (x,y) → world `X=(x−y)·32+OX`, `Y=(x+y)·24+OY`, `OX=N·32`, `OY=150`; tile centres at +0.5; index `y*width+x`. HQ is 4×4 → top-left `floor(hq+0.5−2)`, centre on the generator's HQ tile (half-tile offset unavoidable with an even footprint).

## Integration steps
1. `python3 src/apply_mapdata_import_hooks.py <game index.html> <patched index.html>` (stops if any anchor changed; refuses to double-apply).
2. Open the patched page; use the dev panel or `?map=embedded` / `?map=crop192` / `?map=procedural`.
3. Run the tests.

## Test results (Playwright (Python), headless Chromium, real input, software rendering)
- Procedural boot with the hooks applied is **bit-identical** to the unpatched game (hashes of blocked tiles, trees, resources, deposits, land; same decor count, HQ, dwarves, wild enemies).
- In-game verify (`Verify` button / `FEATURE_MAPDATA_IMPORT_TEST.verify()`): N, TW×TH unchanged, tree tiles 0 missing / 0 extra, stone/iron tile-exact, gold kept out of `RES`, iso round trip 1024/1024, HQ centred, 82 MapData ore deposits → 82 game deposits (0 split). 256×256 ready in ~21–26 s, 192×192 in ~12 s (headless, no GPU).
- Pixel alignment (game's baked terrain with trees/ore removed vs a reference rasterised from the JSON): trees r = +0.80 (flips/transpose ≈ 0), ore ground r = +0.81 (peak at zero shift); per-deposit mean offset −4.4, −1.4 world px over 82 deposits.
- `test_gameplay_camera_units_trees.py` 8/8; `test_economy_fog_minimap.py` 10/10; `test_wave.py` 4/4; `test_bad_input.py` 9/9 (7 malformed files rejected); `test_load_real_file_via_panel.py`: real 13 MB file → world identical to the bundled one; **Procedural** returns to N=112.
- Gameplay on the imported map: camera clamps, units never stand in tree tiles (even when ordered into one), building on a tree is refused, Mine on stone and iron pays, Lumber Camp counts imported trees, fog hides/reveals, minimap click moves camera, wave spawns from 5 walkable perimeter points and advances.

## Limitations / open questions
See `README.md` (mining constants, gold, wilderness placement, tree scale/offset, `terrain.grid` legend).
