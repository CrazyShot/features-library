# Tests — Wave Director

```
pip install playwright && playwright install chromium          # headless Chromium, software rendering
python3 tests/build_test_game.py "<main game index.html>" /tmp/wd-test      # TEMPORARY copy with the director injected (never commit it)
GAME_DIR=/tmp/wd-test python3 tests/test_wave_director.py           # 82/82   behaviour: schedule, waves, deaths, pause/speed, cancel, final wave
GAME_DIR=/tmp/wd-test python3 tests/test_integration_regression.py  # 18/18   G.t pin, HUD ownership, kill switch, blocked spawn, recovery cancel, hold
GAME_DIR=/tmp/wd-test python3 tests/test_state_restore.py           # 7/7 (+1 KNOWN LIMITATION line)  save/load: auto-resync, snapshot/restore, cost
GAME_DIR=/tmp/wd-test python3 tests/test_v11_final.py               # 24/24  1.1.0: resync, snapshot, wave timeout, banner vs toolbar, sounds
python3 tests/build_saveload_game.py <game index.html> <FEATURE_BASTION-SAVE-LOAD.js from PR #12> /tmp/wd-sl --director  # scratch build: game + REAL Save/Load (+ director)
GAME_DIR=/tmp/wd-sl python3 tests/test_real_saveload.py             # 18/18  real PR #12 Save/Load + director
GAME_DIR=<dir with the PURE game's index.html> python3 tests/test_host_contract.py   # 40/40  preflight: run this on a new game build FIRST
STATIC_ONLY=1 GAME_DIR=<dir> python3 tests/test_host_contract.py    # source-text checks only (no browser)
```
`build_test_game.py` output and any `index.html` are scratch files — the repo guard rejects them. What each file covers and what is **not** covered: `../INTEGRATION.md` ("Test results" / "NOT tested"). Checklist for integrators: `../INTEGRATION_CHECKLIST.md`.
