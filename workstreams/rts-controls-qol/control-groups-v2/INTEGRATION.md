# Integration — Control Groups v2

## Target game revision
Prototype "Emberfall — RTS Map Prototype" (single-file index.html) as supplied 2026-10-08; main-repo commit: **to be filled in by the integrator**

## Dependencies
Hard: none. Other RTS-systems blocks use its API softly (`FEATURE_CTRLGROUPS_V2.selectedBuildings()` in BUILDING-REPAIR).

## Host touch points
**Wraps at load time** (no host function is edited): `clickSel`, `boxSel`, `uiUpdate`.
**Host names read/written:** `SU SB U B G cam X Y W H toast setSpeed bHit`, DOM `#sp button[data-s]` (tooltips only).
**Required host edits** (done by `src/apply_rts_systems.py`; each anchor must match exactly once):
- **E1** remove the 1/2/3 speed keys from the keydown handler: `else if(!e.shiftKey&&/^Digit[1-3]$/.test(e.code))setSpeed(+e.code[5])`
- **E2** zoom-in: `if(e.code==='KeyQ'||e.code==='Equal')…` → `if(e.code==='KeyQ')…` (the host bound `+` to zoom)
- **E3** zoom-out: `if(e.code==='KeyE'||e.code==='Minus')…` → `if(e.code==='KeyE')…`
- **E4** help text in `#hud`: control groups, double-click, `+ / −` speed
- **E5** delete the old `FEATURE: CONTROL GROUPS` block (`CTRLGROUPS-1.0.0`) — both cannot run together

The feature also swallows digit and `+/−` keydowns in the capture phase, so a host that still has E1–E3 cannot double-handle them.

## Integration steps
1. `python3 src/apply_rts_systems.py <game index.html> <patched index.html>` (applies E1–E5 and inserts the four RTS blocks in the correct order), **or** apply E1–E5 by hand and paste the block before `</body>`.
2. Insert order matters for the wrapper chain: CONTROL-GROUPS-V2, UNIT-INFO-PANEL, DOUBLE-CLICK-SELECT, BUILDING-REPAIR.
3. Run the tests against the patched build.

## Test results (Playwright (Python), headless Chromium, real input, software rendering)
- `test_control_groups_and_keys.py`: **35/35** — 1/2/3 no longer change speed; `+`/`−`/numpad change speed 1–3 and cap; Space pause/resume; Shift+2/Shift+7 build shortcuts; drag-box → Ctrl+1 → Esc → 1; moving a unit group 1→2; exclusivity (no entity in two groups); mixed group of 6 units + HQ; HQ moved 4→5; destroyed building/unit drop out; empty group no-op; camera centres on off-screen / re-pressed group; chip click.
- `test_cross_feature_imported_map.py`: **7/7** with the MapData import and vampire panel on the 256×256 map.

## Limitations / open questions
See `README.md` (browser tab-switching with Ctrl+digit untested on a real desktop browser; empty-assign semantics).
