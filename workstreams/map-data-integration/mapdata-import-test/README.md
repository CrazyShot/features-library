# MapData import test (Terrain Generator → game world)

| Field | Value |
|---|---|
| Feature ID | `MAPDATA-IMPORT-TEST-1.0.0` |
| Workstream | `map-data-integration` |
| Issue / Project | [#5](https://github.com/CrazyShot/features-library/issues/5) · status is tracked in the [Project](https://github.com/users/CrazyShot/projects/1) |
| Target game revision | Prototype "Emberfall — RTS Map Prototype" (single-file index.html) as supplied 2026-10-08; main-repo commit: **to be filled in by the integrator** |
| Depends on | 8 guarded hooks in the main game script (patcher asserts every anchor) |

## What it does
Builds the real game world from a Terrain Generator `MapData.json` (square maps; tested 192×192 and 256×256) instead of generating terrain: map size `N`, trees (exactly one per MapData tree tile), stone/iron deposits (tile-exact `RES/RESI`), gold nodes (visual ore + glow), `terrain.grid` ground tint, HQ position, wave-perimeter/ground overlays. A dev panel offers **Load MapData…** (real file), **Bundled 256**, **Crop 192** (synthetic test crop, not a generator output) and **Procedural**. The world is built at load, so choosing a map stages it (`sessionStorage`) and reloads the page. With no import active the game is byte-for-byte unchanged in behaviour.

## Files
- `src/FEATURE_MAPDATA-IMPORT-TEST-1.0.0_part1_boot.html` — BOOT block, **must stay before the main game `<script>`**; includes the bundled compact test map
- `src/FEATURE_MAPDATA-IMPORT-TEST-1.0.0_part2_ui.html` — dev panel, hover inspector, overlay, in-game verify
- `src/apply_mapdata_import_hooks.py` — applies the 8 hooks and inserts both parts
- `src/fixtures/bundled_compact_256.json` — compact test fixture (47 KB) derived from generator output `bastion-001`; the 13 MB full export is **not** committed
- `tests/`

## Limitations
- **Economy mismatch:** under the current mining constants (`MMIN = 6`) only 39 of 82 imported stone/iron deposits can host a Mine — all 22 medium and 17 large ones; **none of the 43 small deposits**, including the generator's guaranteed starter stone (4 nodes). Tune `MMIN` or `amountToIntensity`.
- **Gold** has no mining mechanic in the game: gold nodes are visual-only.
- Wilderness enemies are still placed by the game's own logic, not by MapData `enemyPopulation`.
- Trees: one per tile (the game's own forests had up to 3), only the tile is known (no scale/offset), all `type 1`; wood income per forest is lower.
- `terrain.grid` legend is not in the file; it is treated as an alternate-ground tint. `buildable`, `regions`, `forest.*`, `startingResources` are not consumed.
- A page reload is required to switch maps; not tested inside a published/iframe sandbox.
