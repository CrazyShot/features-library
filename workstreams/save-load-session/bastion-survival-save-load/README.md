# Bastion Survival Save / Load

| Field | Value |
|---|---|
| Feature ID | `BASTION-SAVE-LOAD-1.1.0` |
| Workstream | `save-load-session` |
| Issue / Project | [#11](https://github.com/CrazyShot/features-library/issues/11) · status belongs in the [Project](https://github.com/users/CrazyShot/projects/1) |
| Target game revision | Bastion Survival single-file prototype supplied 2026-10-10 (source build SHA-256 starts `119f565650b7c0f7`); local save/load base `60be474` |
| Depends on | none |
| Supersedes | none |

## What it does

Adds versioned Survival saves, manual save/load, configurable autosave, and five independent save slots. It serializes entity links as stable IDs, keeps detached dead entities that are still referenced, validates a complete save before applying it, and rebuilds placement and other derived indexes from the restored world.

The implementation reuses the game’s existing simulation, combat, economy, construction, production, and wave state. It does not add a second gameplay system or change balance.

## Files

- `src/FEATURE_BASTION-SAVE-LOAD.js` — the marked save/load block to insert inside the host script.
- `tests/README.md` — how to run the in-game regression suite and what was checked.
- `INTEGRATION.md` — exact host touch points, required markup/helpers, test evidence, and limitations.

## Limitations

- Research is not implemented in this game build, so no research state is included.
- The current schema accepts the existing 112×112 map only.
- Transient UI/input state and visual/audio objects reset on load.
- The optional Wave Director feature has private timer/tracking state outside the host Survival state; this save block does not yet snapshot that private state.
- Enemy pathfinding and wilderness-group AI remain under development; fields present in the current build are preserved, but future state needs schema updates.
