# Integration — Double-click select

## Target game revision
Prototype "Emberfall — RTS Map Prototype" (single-file index.html) as supplied 2026-10-08; main-repo commit: **to be filled in by the integrator**

## Dependencies
Soft: `UNIT-INFO-PANEL-1.1.0` (`FEATURE_UNIT_INFO.setInspect/inspect`). Insert **after** UNIT-INFO-PANEL so its enemy-inspect click runs first.

## Host touch points
Wraps `clickSel`. Reads `SU SB U E cam X Y W H fogVis pickEnemy`. Re-implements the host's unit hit-test (radius `max(16,12/zoom)` around the point 14 px above the feet) — if the host changes unit picking, update `pickFriendly`. No host edits.

## Integration steps
Insert `src/FEATURE_DOUBLE-CLICK-SELECT.html` before `</body>`, after UNIT-INFO-PANEL (or use the patcher in `../control-groups-v2/src/`).

## Test results (Playwright (Python), headless Chromium, real input)
- `test_double_click_and_info_panel.py`: **25/25** — double-click Dwarf Warrior → all 6 dwarves only; Ranger → all 4 rangers only; slow second click is not a double-click; Shift adds; `maxTiles` bounds the radius; an off-screen dwarf is not swept in; visible vampires only (independently computed expected set), a fogged on-screen vampire is excluded (precondition asserted), enemies never enter `SU`.

## Limitations / open questions
Wilderness vampires in view are included in an enemy double-click (they are visible Vampires of the same owner).
