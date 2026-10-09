# Integration — Wave Director (`WAVE-DIRECTOR-1.0.0`)

## Target game revision
"Emberfall — RTS Map Prototype" single-file build supplied 2026-10-10 as `index (2).html` (1698 lines, sha256 `119f565650b7c0f7…`). Main-repo commit: **to be filled in by the integrator.**

## Dependencies
None (hard or soft). No other library feature wraps `waveTick`, so no wrapper conflict is expected, but it has **not** been tested together with them (see Limitations). `BUILDING-REPAIR`'s tests pin `G.t` to hold the day phase; the director reads `G.t` the same way (see *Host contracts*), also untested together.

## Host touch points
**Wrapped (no host line edited):** `waveTick(dt)` (replaced while the director is enabled, original called when `disable()`d), `uiUpdate()` (HUD text + banner, after the host's own).
**Called (host functions reused, unchanged):** `planWave()`, `startNight()`, `spawnE(p)`, `endGame(win)`, `pickSpawns()`, `killQuiet(e)`, `dirName(p)`, `ev(...)`.
**Read / written globals:** `G` (`started t phase day wave warned pts sq night wE state speed`), `B`, `E`, `DAYLEN`, `WARN`, `WAVES`, `COUNTS`; enemy fields written on the object `spawnE` just created: `mh hp dmg sm` + new tags `wtype wnum`.
**DOM ids added:** `wavedir-banner`, style `wavedir-css`. **DOM written:** `#wv` text every frame, `#rp` text on victory when `finalWave ≠ WAVES`. Reads `#ts`/`#rp` only in tests.

## Integration steps
1. Insert `src/FEATURE_WAVE-DIRECTOR.html` before the final `</body>` (after the main `<script>`). Order relative to other features does not matter; it must come after the host script.
2. Nothing else is required. The existing "Call wave [N]" button / `N` key keep working.
3. Optional: pick the run length with `FEATURE_WAVE_DIRECTOR.cfg.finalWave = 8` (or `Infinity`) right after load, and tune `counts / prepFirst / prepBetween / recovery / warnLead / types / mixFor`.
4. Optional (cosmetic): the game's `WAVES` constant is used by the host victory text; the director patches `#rp` when `finalWave ≠ WAVES`. If you make `WAVES` configurable in the host, drop that patch (one line in `hud()`).

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

## Test results
Command: `python3 tests/build_test_game.py "<index (2).html>" <dir> && GAME_DIR=<dir> python3 tests/test_wave_director.py` — Playwright (Python), headless Chromium, software rendering, build = the supplied 2026-10-10 prototype + this block.
**82/82, three consecutive runs.** The game's own `stepSim(dt)` is stepped by hand (real `waveTick`, `spawnE`, `hurt→killT`, `endGame`); pause/speed checks use the real render loop and `G.speed`.
- A (boot, tables, first attack, five waves): counts 5/8/11/14/18/22/26; warning once at ~22 s, host toast + markers; countdown 10/5/4/3/2/1 once each; HUD + banner; first spawn at 2.0 s, spacing 0.8 s; 5 host enemies, hp 40/dmg 6 unchanged; 2 kills → alive 3, `G.wE` agrees; clear delay; recovery 10 s then 45 s preparation; waves 2–5 sizes 8/11/14/18, compositions (swifts from 3, brutes from 4), total hp strictly rising, multipliers exact, host hp curve intact; final-wave start/defeat signals once; victory; nothing scheduled after.
- B: pause freezes the timer; 3× speed ≈ 3× progress; pause mid-spawn → no skip/duplicate/burst (spawn indices 1..5); `pause()` hold ignores kills until released; `callNight()` starts a wave; `devClear()` still completes the wave; cancel mid-wave (spawned enemies stay, queue gone, nothing spawns for 200 s), `cancel` twice is a no-op, `start()` replays the cancelled wave, `cancel({killEnemies})` leaves `G.wE=0`, cancel during preparation.
- C: configurable `finalWave=2` (HUD "1/2", final flag, signal + DOM event once, victory text uses 2); `onFinalDefeated:'signal'` keeps the game in play and stops scheduling; endless mode (wave 7 = 26 enemies, recovery 0, 120-enemy wave compressed to the span cap); HQ destroyed → `lost` + defeat; `disable()/enable()` hand-off.
- D: real combat left on (6 host units): wave 1 resolved by the host's own defenders, 5/5 down seen by the director, `G.wE=0`.
Parts A–C remove defenders and harden buildings (`U.length=0`, hp 1e7) so enemy counts are exact — that is a test choice, not a game change.

## Limitations / open questions
- **Assumption:** the host has **one** wave enemy (`spawnE`). "Different compositions" are therefore stat variants (hp / dmg / speed multipliers) with the *same sprite*; `e.wtype` is available for a renderer.
- Balance numbers (variant multipliers, mix curve, 45 s preparation, 10 s recovery, +4 enemies/wave) are my choices, not tuned in play. Only the host's 5-wave counts and 55 s/22 s timings are preserved exactly. The research tree is untouched.
- Not tested in a long manual playthrough, on touch/mobile, or with the host's Visual Lab open. Not tested with any other library feature loaded together.
- No save/load exists in the host, so the director has none (state lives in `D` + `G`).
- The wilderness population (`wl` enemies) is outside the wave system and ignored.
- `hud()` overwrites `#wv` every frame while enabled (`cfg.hud=false` to keep the host text).
