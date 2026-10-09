# Integration — Bastion Survival Save / Load (`BASTION-SAVE-LOAD-1.1.0`)

## Target game revision

Bastion Survival single-file prototype supplied 2026-10-10; source build SHA-256 starts `119f565650b7c0f7`. The feature was first implemented against local save/load commit `60be474`; the main-game repository commit is unavailable in this library. Retest on the current private main-game revision before integration.

## Dependencies

No other feature-library module is required. This block is tightly coupled to the host’s lexical simulation variables; it cannot be loaded as a separate after-body script. Save format version 2 migrates version 1 saves.

## Host touch points

**Insert location:** place `src/FEATURE_BASTION-SAVE-LOAD.js` inside the main game’s existing script after simulation globals/functions and `initSurvival()` are defined, before the frame loop is declared. Insert it once. Keep the feature markers.

**Host state read/written:** `B`, `U`, `E`, `WG`, `PR`, `G`, `Clock`, `_s`, `nid`, `cam`, terrain/map arrays (`L`, `GRID.height`, `blk`, `TREEG`, `RES`, `RESI`, `FOG`), placement/path/fog/spatial-hash caches, and existing HUD/UI state.

**Host functions reused:** `gridCell`, `rebuildPlacementGrid`, `labelComps`, `groupComponent`, `buildingIncome`, `fogUpdate`, `shBuild`, and the existing placement, construction, production, combat, projectile, wave, economy, and UI update systems. The feature does not replace these gameplay systems.

**DOM ids required:** `saveBtn`, `loadBtn`, `saveSlotSelect`, `saveSlotBtn`, `loadSlotBtn`, `autosaveSelect`. The controls belong in the existing `#rs` toolbar. Do not duplicate existing Save/Load controls when upgrading the 1.0.0 draft; add the slot selector/buttons and autosave selector only if absent.

## Integration steps

1. Add or retain the manual buttons in `#rs`: `Save` (`#saveBtn`) and `Load` (`#loadBtn`).
2. Add a slot selector (`#saveSlotSelect`, values 1–5), `Save slot` (`#saveSlotBtn`), and `Load slot` (`#loadSlotBtn`).
3. Add `#autosaveSelect` with values 0, 60, 180, 300, and 600 seconds (Off, 1, 3, 5, or 10 minutes). The default is 5 minutes. These controls use local browser storage.
4. Keep the toolbar above the canvas and style its selects, for example with `#rs{z-index:8}` and `#rs select{box-sizing:border-box;max-width:70px;padding:3px 6px;border:1px solid var(--edge);border-radius:6px;background:rgba(40,28,18,.9);color:var(--ink);font:12px Georgia,serif}`.
5. Apply these small host helper changes so load can refresh the full grid without leaving old occupied cells cached:

   - Change `gridCell(i)` to accept an optional `invalidate=true` argument and update `compDirty`/`GRIDV` only when true.
   - Add `rebuildPlacementGrid()`, looping over all `N*N` cells with `gridCell(i,false)`, then setting `compDirty=true` and incrementing `GRIDV` once.
   - Add `groupComponent(g)` using `nearestWalk(g.hx|0,g.hy|0)` and the resulting `comp` cell.
   - Extract the existing finished-building output calculation into `buildingIncome()`; call it from `stepSim(dt)` to update `G.inc`.

   Keep the existing terrain, obstacle, and occupancy rules inside `gridCell`. Loading clears occupancy and rebuilds the complete placement/path grid before refreshing UI.
6. Insert the marked source block after `initSurvival()` in the same script scope. It registers existing buttons and adds a one-second autosave scheduler; it does not add a second simulation loop.
7. Open the game with `?saveLoadTest=1`. Confirm the result panel reports all 21 checks passed.

## Ordering notes

Insert after the host definitions and initial world setup, but before the host frame loop starts. The module expects the existing `waveTick` and combat/economy/production handlers to keep owning gameplay. It snapshots the host’s wave fields and queued host spawns. If the optional `WAVE-DIRECTOR-1.0.0` feature is also enabled, its private director timers and tracked-enemy set are not included; an explicit adapter is required for complete director-specific continuation.

## Test results

**Actual run:** the local working build based on `60be474`, with the current 1.1.0 block and slot/grid fixes, opened in the Codex in-app browser with `?saveLoadTest=1`. Result: **21/21 passed**. This was an in-app browser run, not a headless Chromium run.

Coverage included idle entities; units targeting and fighting; enemies pursuing units and attacking buildings; movement orders; active projectiles; construction and production queues; mixed wilderness/wave enemies and continued gameplay during an active wave; removed/dead entities and stable references; v1 migration; five-slot switching across different building sets; building IDs, unfinished construction, destroyed footprints, mine limits, derived income/UI; transient DOM/Canvas/function filtering; malformed references/IDs/versions/footprints; and rejected loads leaving the live session unchanged.

Static inline JavaScript parsing and `git diff --check` also passed on the local working build. The main-game regression suite must be rerun by the integrator after applying this package.

## Limitations / open questions

- There is no research/research-progression system in the target build. Research cannot be saved until that system and its state contract exist.
- Current map dimensions are fixed at 112×112; other dimensions are rejected until a migration is defined.
- Selection, input/drag mode, notifications, and pending visual/audio effects are transient. DOM, Canvas, rendering objects, and functions are intentionally excluded.
- Current enemy AI and wilderness-group fields round trip. Their future fields must be explicitly added to validation and the save schema.
- The optional Wave Director keeps private state beyond mirrored host fields; see ordering notes.
- Browser storage may be unavailable or full; the save reports the failure and keeps the running session intact.
