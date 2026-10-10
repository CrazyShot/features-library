# Integration — Wave Director (`WAVE-DIRECTOR-1.0.0`)

## Target game revision
"Emberfall — RTS Map Prototype" single-file build supplied 2026-10-10 as `index (2).html` (1698 lines, sha256 `119f565650b7c0f7…`). Main-repo commit: **to be filled in by the integrator.**

## Dependencies
Hard: none. Soft / cross-feature (see `INTEGRATION_CHECKLIST.md`): **`BASTION-SAVE-LOAD-1.1.0` (PR #12) needs a one-line adapter call** after every load (below, *Fragile points* F1). No other library feature wraps `waveTick`. Director + the four RTS blocks (CONTROL-GROUPS-V2, UNIT-INFO-PANEL, DOUBLE-CLICK-SELECT, BUILDING-REPAIR) were loaded together in both orders and the director's behaviour tests pass; those features' own tests were **not** re-run with the director (BUILDING-REPAIR cannot even start on the supplied build, see F9).

## Host touch points
**Wrapped (no host line edited):** `waveTick(dt)` (replaced while the director is enabled, original called when `disable()`d), `uiUpdate()` (HUD text + banner, after the host's own).
**Called (host functions reused, unchanged):** `planWave()`, `startNight()`, `spawnE(p)`, `endGame(win)`, `pickSpawns()`, `killQuiet(e)`, `dirName(p)`, `ev(...)`.
**Read / written globals:** `G` (`started t phase day wave warned pts sq night wE state speed`), `B`, `E`, `DAYLEN`, `WARN`, `WAVES`, `COUNTS`; enemy fields written on the object `spawnE` just created: `mh hp dmg sm` + new tags `wtype wnum`.
**DOM ids added:** `wavedir-banner`, style `wavedir-css`. **DOM written:** `#wv` text every frame, `#rp` text on victory when `finalWave ≠ WAVES`. Reads `#ts`/`#rp` only in tests.

## Integration steps
Short form — the full ordered list with commands is **`INTEGRATION_CHECKLIST.md`**.
1. Run `tests/test_host_contract.py` on the target build first (it needs no director).
2. Insert `src/FEATURE_WAVE-DIRECTOR.html` before the final `</body>` (after the main `<script>`), preferably after the other after-body blocks.
3. **If Save/Load is integrated:** call `FEATURE_WAVE_DIRECTOR.disable(); FEATURE_WAVE_DIRECTOR.enable();` right after every successful load (F1).
4. Optional: pick the run length with `FEATURE_WAVE_DIRECTOR.cfg.finalWave = N` (default = host `WAVES`; keep ≤ `WAVES` while Save/Load rejects larger waves) and tune `counts / prepFirst / prepBetween / recovery / warnLead / types / mixFor`.
5. Optional (cosmetic): the director patches the victory text when `finalWave ≠ WAVES`; if `WAVES` becomes configurable in the host, drop that patch (one line in `hud()`).
6. Run the regression set in the checklist.

## Hooks Main Claude (combat / enemy AI) can use — all optional
- `FEATURE_WAVE_DIRECTOR.on('spawn', d => …)` — `d.enemy` is the host enemy object right after `spawnE`; `d.kind` is `grunt|swift|brute`; `d.wave`. Attach AI traits / visuals here, or read `e.wtype`.
- `on('enemyDown')`, `on('waveStart')`, `on('waveCleared')`, `on('finalWaveDefeated')` — e.g. rewards, music, achievements.
- Stat variants are plain multipliers in `cfg.types`; add a type + a fraction in `cfg.mixFor` for new compositions. If you later add real enemy kinds, replace the body of `spawnOne()` to call your spawner and keep `D.tracked.add(e)`.

## Public API — `window.FEATURE_WAVE_DIRECTOR`
`cfg` · `on(evt, fn)→off` (`'*'` = all) · `status()` · `callWave()` · `pause()` / `resume()` (hold the schedule) · `cancel({killEnemies})` · `start({wave})` · `jumpTo(n)` · `enable()` / `disable()` · `countFor(w)` · `composition(w)` · `planList(w)` · `version`.
`status()` → `{state, wave, nextWave, finalWave, isFinal, timer, remaining, queued, spawned, total, alive, killedThisWave, totalKilled, finalDefeated, held, gamePaused, phase, enabled}`; `state` ∈ `idle prep wave recovery finished cancelled lost`.
**Events** (callback + window `CustomEvent 'wavedirector'` with `detail.type`): `prepStart warning countdown waveStart finalWaveStart spawn enemyDown waveCleared recoveryStart recoveryEnd finalWaveDefeated held released cancelled started blocked lost pause resume`.
**Final-wave signal:** `on('finalWaveDefeated')`, window event `bastion:final-wave-defeated`, `status().finalDefeated===true`; then `endGame(true)` unless `cfg.onFinalDefeated === 'signal'`.

## Host contracts / ordering notes
- **One controller.** While enabled, the host's original `waveTick` body never runs. The few host lines it contained that are *not* scheduling are reproduced inside the wrapper: HQ placed → `G.started=true; G.t=0`; HQ gone → `endGame(false)`; the `G.night` darkness blend. **If those lines change in the host, mirror them in `window.waveTick = …`.**
- The director keeps the host's wave state mirrored (`G.phase` day/night, `G.wave`, `G.day`, `G.t` = time in the current phase, `G.warned`, `G.pts`, `G.sq` = queue of `{t,p,type}`), so the host HUD, spawn-point markers, minimap markers, `devSpawn`, `callNight` and `disable()` hand-back all keep working. `disable()` then `enable()` adopts a running wave.
- `G.t` is read, not owned privately: pinning it low (as the repair test does) holds the preparation; a forward jump larger than the step (what `callNight()` does) is treated as "call the wave now".
- `startNight()` is called for the host's wave bookkeeping (phase, `wave++`, spawn-point validation, horn, toast) and its own `COUNTS` queue is immediately replaced. For waves beyond `COUNTS` the host function builds an empty queue (no error).
- Completion uses the enemies the director spawned, not `G.wE`: enemies created elsewhere (`devSpawn`, other features) do not hold a wave open. An unreachable enemy is removed by the host's own 300 s age-out (`killQuiet`).

## Fragile points (ranked) — what can break, how it fails, how it is guarded
| # | Where | Risk | Failure mode | Guard / action |
|---|---|---|---|---|
| F1 | **Save/Load (PR #12)** | Load replaces `G` fields and the enemy objects in `E`; the director's private state (`D.tracked`, timers) is not saved | **Reproduced:** naive load mid-wave → tracked objects are gone from `E` → wave declared *cleared* while the restored enemies are alive; load in preparation restores `G.t` upward → looks like "call wave" → wave starts at once (**reproduced**); a prep/recovery save resumes as a fresh preparation (timer 0, markers cleared) | Call `FEATURE_WAVE_DIRECTOR.disable(); FEATURE_WAVE_DIRECTOR.enable();` synchronously right after a successful restore (before the next sim step). Mid-wave adoption is **tested** (`test_state_restore.py`). A proper `snapshot()/restore()` pair is a recommended follow-up, **not implemented** (kept the module stable as asked) |
| F2 | `waveTick` wrapper | It replaces the host body and re-implements three non-scheduling lines (HQ placed → start; HQ gone → `endGame(false)`; `G.night` blend) | If the host edits `waveTick` (new rule, new win/lose condition, new hook) the director silently skips it | `test_host_contract.py` Part 0 fingerprints `waveTick/startNight/planWave/spawnE/endGame/callNight/pickSpawns` and **warns** on any change; the global-function + `stepSim` call anchors are hard checks |
| F3 | `uiUpdate` wrapper / HUD | Overwrites `#wv` every frame; fixed-position banner at `top:180px`; `try{hud()}catch{}` hides HUD errors; victory-text patch is a string match | Another feature writing `#wv` loses; Save/Load adds ~10 controls to `#rs` (toolbar may grow/wrap) and could overlap the banner — **not checked visually**; if the overlay text changes the `all N nights` patch silently does nothing (cosmetic) | `cfg.hud=false` / `cfg.banner=false` hand the host text back (**tested**); visual check listed in the manual smoke list |
| F4 | Enemy spawning | Takes `E[E.length-1]` right after `spawnE(p)`; requires exactly one new element | If the host's `spawnE` ever adds 0 or ≥2 objects, pools objects or returns early, the spawn is skipped **without tracking** → `D.spawned` stays 0 → the wave never completes (stall) | Preflight runtime check `spawnE adds exactly one enemy at the end of E`; enemy variants rely on `steer()` reading `e.sm` (checked) |
| F5 | Death tracking | An enemy counts as down when `e.dead` or it left `E` | Enemy stuck/unreachable: wave stays open until the host's 300 s age-out (`killQuiet`); there is **no director-side wave timeout** | Host age-out; balance item for the playtest (`waveTimeout` would be a follow-up). Cost: 0.012 ms per pass at 144 tracked / 844 in `E` (O(tracked × E)) |
| F6 | Victory handling | `endGame(true)` is called from inside `waveTick`; `onFinalDefeated:'signal'` skips it | A host that wants an epilogue before victory must use `'signal'` and call `endGame` itself | Signal events + `status().finalDefeated` (**tested**, both modes) |
| F7 | `G.t` ownership | `G.t` is the phase timer *and* the "call wave" channel (forward jump > 1 s) | Any code adding > 1 s to `G.t` in preparation starts the wave (Save/Load, a future "skip day") | Pin-low is respected (**tested**); never write a larger `G.t` without re-adopting |
| F8 | `startNight()` reuse | Called for its side effects, its own queue (`COUNTS`) is then replaced | A host change in `startNight` (e.g. a different queue shape or an early return) breaks the schedule | Static anchor `startNight does phase='night', G.t=0, G.wave++` + fingerprint warning |
| F9 | **Other features on the supplied build** (not the director) | `BUILDING-REPAIR` self-disables (host has no `#tr`; it has a `#sl` sell button instead); `apply_rts_systems.py` fails its E4 help-text anchor | Those features do not run on this build | Reported to their owners; irrelevant to the director but it means *their* tests cannot serve as the director's `G.t`-pin regression — `test_integration_regression.py` covers the pin directly |

## Host contracts / ordering notes
- **One controller.** While enabled, the host's original `waveTick` body never runs. If the three mirrored lines in F2 change in the host, mirror them in `window.waveTick = …`.
- The director keeps the host's wave state mirrored (`G.phase` day/night, `G.wave`, `G.day`, `G.t` = time in the current phase, `G.warned`, `G.pts`, `G.sq` = queue of `{t,p,type}`), so the host HUD, spawn-point markers, minimap markers, `devSpawn`, `callNight` and `disable()` hand-back keep working (**hand-back tested end to end: a full host wave runs and clears by itself after `disable()`**).
- Insertion order: after the host script; relative to other after-body blocks either order works (both tested for the director's behaviour). **Recommended: last**, so its `#wv` write is the final one.
- `startNight()` is called for the host's wave bookkeeping (phase, `wave++`, spawn-point validation, horn, toast) and its own `COUNTS` queue is immediately replaced. Beyond `COUNTS` the host function builds an empty queue (no error).
- Completion uses the enemies the director spawned, not `G.wE`: enemies created elsewhere (`devSpawn`, other features) do not hold a wave open.

## Test results — exactly what was run
Environment for all of it: Playwright (Python) + headless Chromium, software rendering, **the supplied 2026-10-10 prototype** (sha256 `119f565650b7c0f7…`) with the module injected by `tests/build_test_game.py`; the host's own `stepSim(dt)` is stepped by hand with `G.speed=0` (real `waveTick`, `spawnE`, `hurt→killT`, `endGame`), except where a test says it uses the real render loop. Parts A–C of the main suite remove the defenders and harden buildings (`U.length=0`, hp 1e7) so enemy counts are exact; **that is a test choice, not a game change**.

| File | Result | Covers |
|---|---|---|
| `test_wave_director.py` | **82/82** (3 consecutive runs at 1.0.0; re-run after review) | A: tables 5/8/11/14/18/22/26, compositions, warning once ~22 s + host toast + markers, countdown 10/5/4/3/2/1, HUD + banner text, first spawn at 2.0 s / spacing 0.8 s, 5 host enemies unmodified (hp 40, dmg 6), kills → alive/`G.wE` agree, clear delay, recovery 10 s, preparation 45 s, waves 2–5 sizes + composition + rising total hp + exact multipliers + host hp curve, final-wave start/defeat signal once + host victory, nothing after victory. B: game pause freezes timer (real loop), 3× ≈ 3× progress (real loop), pause mid-spawn no skip/dup/burst, `pause()` hold, `callNight()`, `devClear()` completes the wave, cancel mid-wave (queue gone, spawned enemies left, 200 s quiet), cancel twice, `start()` replay, `cancel({killEnemies})`, `jumpTo`, cancel in preparation. C: `finalWave=2` (HUD 1/2, signal + DOM event once, victory text), `'signal'` mode, endless, wave 7 = 26, recovery 0, 120-enemy wave span cap, HQ lost, `disable()/enable()` adoption. D: real host combat on wave 1 (6 default units, no towers) |
| `test_host_contract.py` | **40/40** on the supplied build (pure game, no director); 25/28 static on a deliberately broken copy (detects it, exit 1) | Part 0 fingerprints (warn-only; proven to trigger on a mutated `waveTick`), Part 1 static anchors, Part 2 runtime: globals reachable/writable, `spawnE` contract, death flags, `steer` honours `e.sm`, `stepSim→waveTick` and frame→`uiUpdate` through global names, host-only phase start, victory text |
| `test_integration_regression.py` | **18/18** | `G.t` pinned 200 s, HUD ownership (director vs host text differ and are asserted), kill switch (full host wave after `disable()`), Space pause, HQ-lost rule, no-spawn-point `blocked` + retry, cancel in recovery then `start()` = next wave, hold during preparation |
| `test_state_restore.py` | **5/5** + 3 *KNOWN LIMITATION* lines reproduced (F1) | naive mid-wave load → premature clear (reproduced), `disable()+enable()` mitigation (tested), prep timer restart (reproduced), larger `G.t` in place → wave starts (reproduced), prune cost 0.012 ms |
| Combined builds (RTS blocks + director, both orders; ad-hoc, not committed) | director behaviour **78/78** in each order; the 4 remaining "no console warnings" checks fail only because `BUILDING-REPAIR` prints its own "disabled" warning (F9) | wrapper chain on `uiUpdate` with CONTROL-GROUPS-V2, UNIT-INFO-PANEL, DOUBLE-CLICK-SELECT |

## NOT tested (do not assume these work)
- **The latest private main game.** Only the supplied 2026-10-10 prototype was available; run the preflight on the real build first.
- **Any manual playtest.** Nothing here was played by a person. Balance (variant multipliers, mix curve, 45 s preparation, 10 s recovery, +4/wave) is unvalidated.
- Real combat beyond wave 1; waves 2–5 were only run with defenders removed. Whether five waves are winnable/too easy is unknown.
- **Save/Load with the real `FEATURE_BASTION-SAVE-LOAD` code** — only simulated by replacing `E` objects and `G` fields. Whether the saved queue keeps the `type` field is unverified (if dropped, restored queued spawns become grunts; no error).
- Director together with *their* UI tests (RTS features), the Visual Lab, mapdata import, or the sprite test feature.
- Visual layout beyond the two screenshots (other resolutions, the Save/Load-widened toolbar, mobile/touch).
- Long soak (many waves at 3× speed), background-tab throttling, very large `E` render cost.
- `adopt()` with a non-empty restored queue; `finalWave` changed *during* a wave; `countdownAt` customisation.

## Limitations / open questions
- **Assumption:** the host has **one** wave enemy (`spawnE`). "Different compositions" are stat variants (hp / dmg / speed) with the *same sprite*; `e.wtype` is available for a renderer.
- The Save/Load validator rejects `wave > WAVES` (read from its source, not run): keep `cfg.finalWave ≤ WAVES` until that limit is raised, or endless/long runs cannot be saved.
- No save/load of the director's own state (F1). The research tree is untouched.
- The wilderness population (`wl` enemies) is outside the wave system and ignored.
- `hud()` overwrites `#wv` every frame while enabled (`cfg.hud=false` to keep the host text).
