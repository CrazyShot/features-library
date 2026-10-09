# Save/load regression suite

The regression suite is included in `src/FEATURE_BASTION-SAVE-LOAD.js` and runs against the real game scope. Add the feature to a temporary game build, open it with the query string `?saveLoadTest=1`, then inspect the on-screen `Save/load regression checks` results. It restores its initial test snapshot after each assertion.

The documented run used the local build based on `60be474` in the Codex in-app browser: **21/21 passed**. It was not a headless Chromium run.

Coverage: active and idle buildings/units/enemies; attack targets and orders; movement paths; active projectiles; construction progress and production queues; active mixed waves and post-load simulation; removed/dead entity links; format-v1 migration; manual/autosave and numbered slot round trips; repeated switching between saves with different buildings; building IDs; destroyed building footprint release; mine placement limits; income/UI derivation; transient DOM/Canvas/function omission; field/type error reporting; invalid references, IDs, version, footprints, and slot numbers; and unchanged session state after rejected loads.

No separate game copy or generated full-page fixture is included in this feature folder.
