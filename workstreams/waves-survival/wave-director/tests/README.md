# Tests — Wave Director
```
python3 tests/build_test_game.py "<path to main game index.html>" /tmp/wd-test     # writes a TEMPORARY copy with the feature injected
GAME_DIR=/tmp/wd-test python3 tests/test_wave_director.py                         # needs: pip install playwright + Chromium
```
`build_test_game.py` output is a scratch file — **never commit it** (the repo guard rejects `index.html`). Expected: `82/82 passed`.
