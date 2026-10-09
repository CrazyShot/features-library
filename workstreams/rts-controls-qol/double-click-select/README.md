# Double-click select

| Field | Value |
|---|---|
| Feature ID | `DBLCLICK-SELECT-1.0.0` |
| Workstream | `rts-controls-qol` |
| Issue / Project | [#2](https://github.com/CrazyShot/features-library/issues/2) · status is tracked in the [Project](https://github.com/users/CrazyShot/projects/1) |
| Target game revision | Prototype "Emberfall — RTS Map Prototype" (single-file index.html) as supplied 2026-10-08; main-repo commit: **to be filled in by the integrator** |
| Depends on | soft: `UNIT-INFO-PANEL-1.1.0` (enemy double-click) |

## What it does
Double-click a unit → select the **nearby units of the same type and owner**: Dwarf Warrior → Dwarf Warriors, Ranger → Rangers, Vampire (enemy) → visible Vampires (inspect-only).
"Nearby" = on screen **and** within `cfg.maxTiles` (30) of the clicked unit — never the whole map. Shift+double-click adds to the selection. Enemies are only picked if the host's `pickEnemy()`/`fogVis()` lets you see them (fog of war respected). The normal single click always happens first.

## Files
- `src/FEATURE_DOUBLE-CLICK-SELECT.html`
- `tests/test_double_click_and_info_panel.py`

## Limitations
- The double-click window is 380 ms / 10 px. Enemy double-click needs UNIT-INFO-PANEL; without it enemy double-clicks are ignored.
- "Same owner" is implied by the array a unit lives in (`U` = yours, `E` = enemy); there is no faction field in the host.
