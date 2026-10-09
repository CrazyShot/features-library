# Integration — Vampire asset test

## Target game revision
Prototype "Emberfall — RTS Map Prototype" (single-file index.html) as supplied 2026-10-08; main-repo commit: **to be filled in by the integrator**

## Dependencies
None.

## Host touch points
Wraps `drawE`, `drawELOD`, `stepEnemy` (debug "hold" only), `pickEnemy` (extends the head hit-area by 8 world px, only for vampire-art enemies). Tags enemy objects with `vamp / vtest / vHold / vForce`. Reads `E U B G g X Y cam spawnE walk comp cellOf nearestWalk toast killQuiet N tpos fogVis TW TH OX OY dpr`. Self-disables with a console warning if a host name is missing. No host edits.

## Integration steps
1. `python3 src/embed_sprites.py <front.png> <back.png> FEATURE_VAMPIRE-ASSET-TEST-1.0.0.html` (private PNGs).
2. Insert the produced block before `</body>`. Remove it (or `cfg.mode='off'`) for release builds.

## Test results (Playwright (Python), headless Chromium, real input, software rendering)
- `test_movement_front_back.py`: **12/12** — ~100-tile walks from open ground / forest edge / behind a tree / dense forest reach a dwarf via the existing pathfinding, never on a blocked tile; front/back matches heading (0 mismatches over ~280 samples); `viewOf` unit tests.
- `test_attack.py`: **8/8** — detect, chase, reach, damage = `e.dmg`, 1.05 s cadence, target death, retarget.
- `test_tree_layers_and_hit_test.py`: tree-layer count per frame identical for vampire / original enemy / dwarf in all four terrain cases; head right-clickable at zoom 0.62–2.2.
- `test_visual_depth_fog_selection.py`: **18/19** — the single failure is the frame-window layer-count check noted in `tests/README.md` (exact per-frame version passes). `test_panel_wave_perf.py`: **7/8** — the failure is the obsolete control-groups-v1 check.
- Embedding check: re-embedding the original PNGs into the template reproduces the original block byte-for-byte.

## Limitations / open questions
See `README.md`.
