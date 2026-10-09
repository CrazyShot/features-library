"""Builds a TEMPORARY test copy of the game with the Wave Director injected.

usage: python3 build_test_game.py <path/to/main-game/index.html> <out_dir>
Writes <out_dir>/index.html (game + feature) and prints the out_dir. The output is a scratch file:
NEVER commit it to the library (tools/check-repo.sh rejects index.html).
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
FEATURE = os.path.join(HERE, "..", "src", "FEATURE_WAVE-DIRECTOR.html")

def build(game_path, out_dir):
    game = open(game_path, encoding="utf-8").read()
    feat = open(FEATURE, encoding="utf-8").read()
    if "FEATURE: WAVE-DIRECTOR START" in game:
        raise SystemExit("game already contains the Wave Director")
    i = game.rfind("</body>")
    if i < 0:
        raise SystemExit("no </body> found in the game file")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "index.html")
    open(out, "w", encoding="utf-8").write(game[:i] + feat + "\n" + game[i:])
    return out

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    build(sys.argv[1], sys.argv[2]); print(sys.argv[2])
