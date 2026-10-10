# Tests — Wave Director

```
pip install playwright && playwright install chromium          # headless Chromium, software rendering
python3 tests/build_test_game.py "<main game index.html>" /tmp/wd-test      # TEMPORARY copy with the director injected (never commit it)
GAME_DIR=/tmp/wd-test python3 tests/test_wave_director.py           # 82/82   behaviour: schedule, waves, deaths, pause/speed, cancel, final wave
GAME_DIR=/tmp/wd-test python3 tests/test_integration_regression.py  # 18/18   G.t pin, HUD ownership, kill switch, blocked spawn, recovery cancel, hold
GAME_DIR=/tmp/wd-test python3 tests/test_state_restore.py           # 5/5 (+3 KNOWN LIMITATION lines)  save/load hazards + cost
GAME_DIR=<dir with the PURE game's index.html> python3 tests/test_host_contract.py   # 40/40  preflight: run this on a new game build FIRST
STATIC_ONLY=1 GAME_DIR=<dir> python3 tests/test_host_contract.py    # source-text checks only (no browser)
```
`build_test_game.py` output and any `index.html` are scratch files — the repo guard rejects them. What each file covers and what is **not** covered: `../INTEGRATION.md` ("Test results" / "NOT tested"). Checklist for integrators: `../INTEGRATION_CHECKLIST.md`.
