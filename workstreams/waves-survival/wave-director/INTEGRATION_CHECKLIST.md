# Wave Director — integration checklist for Main Claude

Module: `WAVE-DIRECTOR-1.1.0` · `src/FEATURE_WAVE-DIRECTOR.html` (one block: `<style>` + `<script>`, no host edits) · details and risk table: `INTEGRATION.md`.
**Status of this document:** everything below was verified only against the supplied 2026-10-10 prototype. **Not integrated into the latest game, not manually playtested.**

## 0. Before touching anything
1. Run the preflight on the **latest** build (pure game, director not needed):
   `GAME_DIR=<dir containing the game's index.html> python3 tests/test_host_contract.py` → expect `40/40`, and Part 0 should say *"byte-identical"*.
2. Part 0 prints `CHANGED <fn>` for any of `waveTick startNight planWave spawnE endGame callNight pickSpawns` that differ from the reference build. **Each CHANGED function must be read against `INTEGRATION.md → Host contracts` before continuing** (the director replaces `waveTick`'s scheduling and mirrors three of its lines).
3. Any `FAIL` in Part 1/2 names the broken assumption. Do not integrate until fixed; do not edit the director to "make it pass".

## 1. Insertion order
1. Host main `<script>` (including Save/Load if it is merged there — it lives inside the script scope).
2. After-body feature blocks, any order among themselves (RTS blocks keep their own order: CONTROL-GROUPS-V2 → UNIT-INFO-PANEL → DOUBLE-CLICK-SELECT → BUILDING-REPAIR).
3. **`FEATURE_WAVE-DIRECTOR.html` last**, immediately before `</body>` (its `uiUpdate` wrapper then writes `#wv` after everyone else; both orders were tested for behaviour).
Insert once. Keep the `FEATURE: WAVE-DIRECTOR START/END` markers. Never add a second wave controller; do not call `startNight`/`planWave` yourself.

## 2. Glue (none mandatory in 1.1.0)
| When | Do | Why |
|---|---|---|
| After a `BASTION-SAVE-LOAD` restore | **Nothing required** — the director auto-resyncs when it sees a replaced world (new HQ object, or tracked enemies gone without `dead=true`) and emits `resync`. | Verified against the real PR #12 code (`test_real_saveload.py`). Cost without the adapter: a recovery-period save resumes as a fresh preparation; per-wave counters after a mid-wave load are approximate. |
| *Recommended* exact-continuation adapter | In the save: `data.waveDirector = FEATURE_WAVE_DIRECTOR.snapshot()`. After a successful load: `if(data.waveDirector) FEATURE_WAVE_DIRECTOR.restore(data.waveDirector)` (returns `false` → the automatic resync stays in effect). Guard both with `window.FEATURE_WAVE_DIRECTOR`. | Keeps preparation/recovery timers, countdown state, queue types and kill counters. Tested (`test_state_restore.py`, `test_v11_final.py`). Needs a one-key extension of the save format — an integrator decision. |
| Any code that writes a larger `G.t` *in place* | Call `FEATURE_WAVE_DIRECTOR.resync()` right after | An in-place forward jump > 1 s in preparation is read as "call wave" (the host's `callNight` does exactly that). |
| Save validator | Keep `cfg.finalWave ≤ WAVES` (default) **or** raise the validator's `wave > WAVES` limit | PR #12 refuses saves with `wave > WAVES` (confirmed by `test_real_saveload.py`) |
| Host changes `WAVES` | Nothing; `cfg.finalWave` defaults to `WAVES` at load. Set it explicitly afterwards to override | |

Optional hooks (no action needed): `FEATURE_WAVE_DIRECTOR.on('spawn'|'enemyDown'|'waveStart'|'waveCleared'|'finalWaveDefeated', fn)`; `e.wtype` / `e.wnum` on wave enemies; full API in `INTEGRATION.md`.

## 3. Compatibility requirements (what the director assumes of the host)
- `waveTick`, `uiUpdate` are **top-level function declarations** called by global name (`stepSim`→`waveTick(dt)`, frame loop→`uiUpdate()`).
- `spawnE(p)` pushes **exactly one** wave enemy at the end of `E` and does `G.wE++`; enemies have `en,hp,mh,dmg`, no `wl`.
- Death sets `e.dead=true`, removes from `E`, `G.wE--` (`killT`, `killQuiet`). `steer()` multiplies enemy speed by `e.sm`.
- `startNight()`: `phase='night'`, `G.t=0`, `G.wave++`, validates `G.pts`. `endGame(win)` sets `G.state` and emits `end`.
- `G.t` is the phase timer; **nobody may add > 1 s to `G.t` during preparation** (that is the "call wave" signal).
- DOM: `#wv #rp #rz #nb #ts`. Restart is `location.reload()`.
- No other code writes `G.phase / G.wave / G.sq / G.pts / G.warned` (preflight prints the writer counts).

## 4. Regression tests to run after integration
Build/point `GAME_DIR` at the **integrated** game (director present):
```
python3 tests/test_wave_director.py          # expect 82/82   (needs a game WITHOUT other features' console warnings; see note)
python3 tests/test_integration_regression.py # expect 18/18
python3 tests/test_state_restore.py          # expect 7/7 and one KNOWN LIMITATION line (in-place larger G.t)
python3 tests/test_v11_final.py              # expect 24/24   (auto-resync, snapshot/restore, timeout, banner, sounds)
# if Save/Load is merged: build with tests/build_saveload_game.py, then
python3 tests/test_real_saveload.py          # expect 18/18
```
Note: `test_wave_director.py` removes the defenders in parts A–C, and its "no console errors/warnings" checks fail if another block prints a warning (on the supplied build `BUILDING-REPAIR` does — 4 checks, unrelated). Triage by name before concluding anything.
Then the host's own regression and each integrated feature's own tests. For Save/Load, add one **real** round-trip by hand: save mid-wave → load → the wave continues and completes (with the adapter the counters are exact); save in preparation → load → the preparation timer is kept.
For `test_host_contract.py` on the integrated build, Part 2's "host-only phase start" is skipped automatically when the director is present.

## 5. Manual smoke list (NOT done by me — please run it)
- [ ] HQ placed → HUD shows "Preparation · wave 1/5 in …"; warning toast + red markers on the map **and** minimap at ~22 s; banner (below the host toolbar) counts down the last 10 s.
- [ ] Wave 1 spawns over ~5 s, HUD shows enemies left; kill them → "Wave 1 cleared", recovery, next preparation.
- [ ] `N` / "Call wave" starts the wave at once; Space pause freezes everything; 1×/2×/3× speed scales it.
- [ ] Waves 3–5: swifts (fast, fragile) and brutes (slow, tanky) appear; the final wave is labelled FINAL; defeating it shows the host victory screen.
- [ ] Banner and the Save/Load-widened `#rs` toolbar do not overlap at your usual window sizes.
- [ ] Save/Load mid-wave, in preparation and in recovery (with and without the optional adapter).
- [ ] A stuck enemy: after `waveTimeout` (240 s) the wave closes with a toast/`waveTimeout` event instead of hanging.
- [ ] Sound cues (warning, cleared, final wave) are audible and not annoying.
- [ ] Kill switch: console `FEATURE_WAVE_DIRECTOR.disable()` returns the original host waves (tested headless).

## 6. Rollback
`FEATURE_WAVE_DIRECTOR.disable()` at runtime (tested: the host runs a full wave by itself) or remove the block. There are no host edits to revert.

## 7. Known issues outside the director (report to their owners)
- `BUILDING-REPAIR-1.1.0` disables itself on the supplied build (host has no `#tr`; there is a `#sl` sell button).
- `apply_rts_systems.py` fails its E4 help-text anchor on the supplied build.

## 8. Decisions for the owner
1. Adopt the optional `snapshot()/restore()` adapter in Save/Load (exact continuation) or rely on auto-resync only.
2. `finalWave` vs the Save/Load `wave > WAVES` validator (only matters for runs longer than 5 waves).
3. Balance is untested: knobs for the playtest are `cfg.counts / countMult / hpGrowth / types / mixFor / prepFirst / prepBetween / recovery / warnLead / spawnInterval / maxSpawnSpan / waveTimeout`.
