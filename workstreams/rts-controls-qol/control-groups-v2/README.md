# Control Groups v2

| Field | Value |
|---|---|
| Feature ID | `CTRLGROUPS-2.0.0` |
| Workstream | `rts-controls-qol` |
| Issue / Project | [#1](https://github.com/CrazyShot/features-library/issues/1) · status is tracked in the [Project](https://github.com/users/CrazyShot/projects/1) |
| Target game revision | Prototype "Emberfall — RTS Map Prototype" (single-file index.html) as supplied 2026-10-08; main-repo commit: **to be filled in by the integrator** |
| Depends on | none |
| Supersedes | `CTRLGROUPS-1.0.0` ([folder](../control-groups-v1-superseded/)) |

## What it does
- **Ctrl/Cmd+1–9** assigns the current selection to a group; **1–9** recalls it. Pressing the already-selected group again (or a group that is off-screen) also centres the camera.
- A unit **or building** belongs to **at most one group**; assigning moves it from its old group. Dead/destroyed entities drop out automatically. Empty/invalid groups do nothing.
- **Mixed selections** (units + buildings): Shift+click a building adds it to the current selection (the host only ever held units *or* one building).
- **Keys:** 1/2/3 are no longer game speed; **+ / −** change game speed (1×–3×); Space = pause (host); Shift+1–9 build shortcuts untouched. The on-screen speed buttons stay.
- Chip column at the left edge shows each group (count, `u+b` for mixed groups); click = select, click again / double-click = centre.

## Files
- `src/FEATURE_CONTROL-GROUPS-V2.html` — the feature block (style + script)
- `src/apply_rts_systems.py` — patcher that applies the host edits E1–E5 and inserts **all four RTS-systems blocks** (control groups, unit info panel, double-click, building repair) into a game `index.html`
- `tests/` — see `tests/README.md`

## Limitations
- Some browsers use Ctrl+1–9 for tab switching; the handler calls `preventDefault`/`stopImmediatePropagation` but this was **not tested in a desktop browser** (headless only). Cmd works on Mac.
- Ctrl+n with nothing selected **empties** group n (config `clearOnEmptyAssign`; set `false` to do nothing).
- Multi-building selection lives in this feature (`SELB`, with `SB = SELB[0]`); the host's own panel still sees one building.
