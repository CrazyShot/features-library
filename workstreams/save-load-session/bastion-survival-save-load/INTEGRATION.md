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

1. Inside the existing `#rs` toolbar, keep or add the following controls after the wave button. When upgrading the 1.0.0 draft, do not add duplicate `saveBtn`/`loadBtn` controls:

   ```html
   <button id="saveBtn" type="button" title="Save this Survival session">Save</button>
   <button id="loadBtn" type="button" title="Load the last manual save (or autosave)">Load</button>
   <label for="saveSlotSelect">Slot</label>
   <select id="saveSlotSelect" aria-label="Save slot"><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4</option><option value="5">5</option></select>
   <button id="saveSlotBtn" type="button" title="Save this Survival session to the selected slot">Save slot</button>
   <button id="loadSlotBtn" type="button" title="Load the selected save slot">Load slot</button>
   <label for="autosaveSelect">Autosave</label>
   <select id="autosaveSelect" aria-label="Autosave interval"><option value="0">Off</option><option value="60">1 min</option><option value="180">3 min</option><option value="300">5 min</option><option value="600">10 min</option></select>
   ```

2. In the existing toolbar CSS, add the following declarations so the controls stay above the canvas and the selects match the game theme:

   ```css
   #rs{pointer-events:auto;display:flex;align-items:center;gap:12px;z-index:8}
   #rs select{box-sizing:border-box;max-width:70px;padding:3px 6px;border:1px solid var(--edge);border-radius:6px;background:rgba(40,28,18,.9);color:var(--ink);font:12px Georgia,serif}
   #rs select option{background:#1a1208;color:var(--ink)}
   ```

3. Replace the existing `gridCell(i)` helper with this form. It keeps the host placement rule and lets a full-grid rebuild invalidate the derived grids once:

   ```js
   function gridCell(i,invalidate=true){const f=L[i]>=1&&!blk[i]&&!occ[i]?1:0;walk[i]=f;GRID.buildable[i]=f;if(invalidate){compDirty=true;GRIDV++}}
   function rebuildPlacementGrid(){for(let i=0;i<N*N;i++)gridCell(i,false);compDirty=true;GRIDV++}
   ```

   Add these helpers beside `nearestWalk` and `stepSim`:

   ```js
   function groupComponent(g){const c=nearestWalk(g.hx|0,g.hy|0);return c?comp[c[1]*N+c[0]]:0}
   function buildingIncome(){const inc={wood:0,stone:0,iron:0,gold:0};for(const b of B){if(b.p<1||!b.out)continue;for(const k of RESN)inc[k]+=b.out[k]}return inc}
   ```

   Replace the old inline building-income calculation in `stepSim(dt)` with this exact line:

   ```js
   G.inc=buildingIncome();/* G.inc = derived output from finished active buildings per 8 h */
   ```

   Loading clears occupancy and rebuilds the complete placement/path grid before refreshing UI. Keep the host terrain, obstacle, and occupancy rule inside `gridCell` unchanged.

4. Insert the marked source block after `initSurvival()` in the same script scope. It registers the controls and adds a one-second autosave scheduler; it does not add a second simulation loop.

5. Open the game with `?saveLoadTest=1`. Confirm the result panel reports all 21 checks passed.

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
