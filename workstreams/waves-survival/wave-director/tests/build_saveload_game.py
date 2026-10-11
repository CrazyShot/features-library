"""Builds a TEMPORARY test game = main game + the REAL Bastion Save/Load block (PR #12 / BASTION-SAVE-LOAD-1.1.0) [+ optionally the Wave Director].
usage: python3 build_saveload_game.py <game index.html> <FEATURE_BASTION-SAVE-LOAD.js> <out_dir> [--director]
Applies the host edits that feature's INTEGRATION.md documents (toolbar controls + css, gridCell/rebuildPlacementGrid, groupComponent/buildingIncome, G.inc line)
and inserts its block before the host frame loop. Every anchor must match exactly once or nothing is written. Output is scratch: never commit it."""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
CTRL = '''<button id="saveBtn" type="button" title="Save this Survival session">Save</button>
   <button id="loadBtn" type="button" title="Load the last manual save (or autosave)">Load</button>
   <label for="saveSlotSelect">Slot</label>
   <select id="saveSlotSelect" aria-label="Save slot"><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4</option><option value="5">5</option></select>
   <button id="saveSlotBtn" type="button" title="Save this Survival session to the selected slot">Save slot</button>
   <button id="loadSlotBtn" type="button" title="Load the selected save slot">Load slot</button>
   <label for="autosaveSelect">Autosave</label>
   <select id="autosaveSelect" aria-label="Autosave interval"><option value="0">Off</option><option value="60">1 min</option><option value="180">3 min</option><option value="300">5 min</option><option value="600">10 min</option></select>'''
CSS = '#rs{pointer-events:auto;display:flex;align-items:center;gap:12px;z-index:8}\n#rs select{box-sizing:border-box;max-width:70px;padding:3px 6px;border:1px solid var(--edge);border-radius:6px;background:rgba(40,28,18,.9);color:var(--ink);font:12px Georgia,serif}\n'

def build(game, sl, out, director=False):
    g = open(game, encoding="utf-8").read(); b = open(sl, encoding="utf-8").read()
    def rep(old, new, why):
        nonlocal g
        n = g.count(old)
        if n != 1: raise SystemExit(f"ANCHOR {why}: expected 1 match, found {n}")
        g = g.replace(old, new)
    rep('<button id="nb">Call wave [N]</button>', '<button id="nb">Call wave [N]</button>' + CTRL, "toolbar")
    i = g.index("</style>"); g = g[:i] + CSS + g[i:]
    rep("function gridCell(i){const f=L[i]>=1&&!blk[i]&&!occ[i]?1:0;walk[i]=f;GRID.buildable[i]=f;compDirty=true;GRIDV++}\nfor(let i=0;i<N*N;i++)gridCell(i);",
        "function gridCell(i,invalidate=true){const f=L[i]>=1&&!blk[i]&&!occ[i]?1:0;walk[i]=f;GRID.buildable[i]=f;if(invalidate){compDirty=true;GRIDV++}}\nfunction rebuildPlacementGrid(){for(let i=0;i<N*N;i++)gridCell(i,false);compDirty=true;GRIDV++}\nfor(let i=0;i<N*N;i++)gridCell(i);", "gridCell")
    rep("function nearestWalk(", "function groupComponent(g){const c=nearestWalk(g.hx|0,g.hy|0);return c?comp[c[1]*N+c[0]]:0}\nfunction buildingIncome(){const inc={wood:0,stone:0,iron:0,gold:0};for(const b of B){if(b.p<1||!b.out)continue;for(const k of RESN)inc[k]+=b.out[k]}return inc}\nfunction nearestWalk(", "helpers")
    m = re.search(r" \{const inc=\{wood:0,stone:0,iron:0,gold:0\};for\(const b of B\)\{if\(b.p<1\|\|!b.out\)continue;for\(const k of RESN\)inc\[k\]\+=b.out\[k\]\}G.inc=inc\}/\* G.inc = what the finished buildings deliver per 8 h \*/", g)
    if not m: raise SystemExit("ANCHOR G.inc line not found")
    g = g[:m.start()] + " G.inc=buildingIncome();/* G.inc = derived output from finished active buildings per 8 h */" + g[m.end():]
    rep("function frame(t)", "\x00SL\x00\nfunction frame(t)", "frame loop"); g = g.replace("\x00SL\x00", b)
    if director:
        d = open(os.path.join(HERE, "..", "src", "FEATURE_WAVE-DIRECTOR.html"), encoding="utf-8").read()
        j = g.rfind("</body>"); g = g[:j] + d + "\n" + g[j:]
    os.makedirs(out, exist_ok=True); open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(g)

if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) != 3: raise SystemExit(__doc__)
    build(a[0], a[1], a[2], "--director" in sys.argv); print(a[2])
