# Integration — Unit / enemy information panel

## Target game revision
Prototype "Emberfall — RTS Map Prototype" (single-file index.html) as supplied 2026-10-08; main-repo commit: **to be filled in by the integrator**

## Dependencies
None. Insert after CONTROL-GROUPS-V2 and before DOUBLE-CLICK-SELECT.

## Host touch points
Wraps `clickSel` (enemy inspect), `uiUpdate` (renders into a new `#uip` block inside `#pn`), `drawWorld` (red ring under inspected enemies).
Reads `SU SB U E G cam X Y W H pickEnemy fogVis BT DW RANGE REACH SPD ESPD g dpr`; DOM `#pn #pt #pi #tr #am #sx #bar`.
CSS added: `#pn{box-sizing:border-box}`; the panel's `max-width` is **fitted at runtime to the left edge of `#bar`** (so it never overlaps the build bar). No host edits.

## Integration steps
Insert `src/FEATURE_UNIT-INFO-PANEL.html` before `</body>` (or use the patcher in `../control-groups-v2/src/`).

## Test results (Playwright (Python), headless Chromium, real input)
- `test_double_click_and_info_panel.py`: **25/25** (panel values equal the game constants; enemy panel; HP updates live; killed enemy clears the panel; mixed panel).
- `test_followup_multi_hp_and_repair.py` (multi-unit part): several dwarves / rangers / mixed / vampires show **no combined HP value and no HP bar**; a single unit/enemy still shows its own HP; wave+wilderness mix shows "4–6 damage". Whole script **51/51**, three consecutive runs.
- Layout measured: panel does not overlap `#bar` at 1400 px and 1100 px viewports.

## Limitations / open questions
Drift risk for the 3 mirrored AI literals (see README). The ring is drawn in the world pass, so it can draw over canopy for an enemy standing under trees.
