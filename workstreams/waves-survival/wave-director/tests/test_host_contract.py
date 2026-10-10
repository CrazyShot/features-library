"""Host-contract PREFLIGHT for the Wave Director. Run it on any game build BEFORE integrating (the build may or may not already contain the director).

  GAME_DIR=<dir containing the game's index.html> python3 test_host_contract.py

Part 1 (static) checks the source text for the anchors the director wraps / calls.  Part 2 (runtime) checks the behaviours it relies on, using only host functions.
Every FAIL line says what to fix or which director assumption breaks.  This file never modifies the game.
"""
import os, re, sys, asyncio
from rt_common import *   # ok(), R, GAME_DIR, async_playwright

# Fingerprints (sha1[:12] of the function text) of the host functions the director replaces / calls, taken from the build it was written against
# ("Emberfall" prototype supplied 2026-10-10, sha256 119f565650b7c0f7...).  A mismatch is only a WARNING: re-read INTEGRATION.md "Host contracts" for that function.
EXPECTED_FN_HASH = {'waveTick': 'bbaf3de7cf75', 'startNight': 'edaa9001042c', 'planWave': 'c1441837f795', 'spawnE': '132f04acafb9', 'endGame': '1e72e7279918', 'callNight': '3838fd7e635c', 'pickSpawns': '15336010a456'}
def fn_text(src, n):
    m = re.search(r"^function " + n + r"\(", src, re.M)
    if not m: return None
    j = src.find("\nfunction ", m.start() + 10)
    return src[m.start():j]

def drift_warnings(src):
    import hashlib
    print("== Part 0: host function drift vs the build the director was written against (warnings only) ==")
    drift = []
    for n, exp in EXPECTED_FN_HASH.items():
        t = fn_text(src, n); got = hashlib.sha1(t.encode()).hexdigest()[:12] if t else None
        if got != exp: drift.append(n)
        print(("   same    " if got == exp else "   CHANGED ") + f"{n}  (expected {exp}, found {got})")
    print("   WARNING: changed host function(s): " + ", ".join(drift) + "  -> review each against INTEGRATION.md 'Host contracts' before trusting the director" if drift else "   host wave functions are byte-identical to the reference build")
    return drift

def static_checks(src):
    print("== Part 1: static anchors (source text) ==")
    m = lambda p, f=0: re.search(p, src, f)
    ok("waveTick is a plain top-level function declaration (a later `window.waveTick = …` wrapper is only seen by callers if it is a global function)", m(r"^function waveTick\(dt\)", re.M))
    ok("stepSim calls waveTick(dt) by global name", m(r"if\(G\.state==='play'\)\{waveTick\(dt\)"))
    ok("uiUpdate is a plain top-level function declaration", m(r"^function uiUpdate\(\)", re.M))
    ok("the frame loop calls uiUpdate() by global name (HUD + pause detection run every frame, also while paused)", m(r"update\(dt\);drain\(\);uiUpdate\(\)"))
    ok("spawnE(p) pushes exactly one enemy onto E and counts G.wE (director takes E[E.length-1])", m(r"function spawnE\(p\)\{G\.wE\+\+;.*?E\.push\(\{en:1", re.S))
    ok("killT marks t.dead=true, splices E and decrements G.wE (death tracking relies on e.dead / removal from E)", m(r"function killT\(t\)\{t\.dead=true;.*?else if\(t\.en\)\{E\.splice\(E\.indexOf\(t\),1\);G\.kills\+\+;if\(t\.wl\)G\.wN--;else G\.wE--", re.S))
    ok("killQuiet marks dead and decrements G.wE", m(r"function killQuiet\(e\)\{e\.dead=true;.*?G\.wE--", re.S))
    for fn in ("startNight", "planWave", "endGame", "callNight", "pickSpawns", "dirName", "hurt"):
        ok(f"function {fn} exists as a declaration", m(rf"^function {fn}\(", re.M))
    for c in ("DAYLEN", "WARN", "WAVES", "COUNTS"):
        ok(f"constant {c} is defined at top level", m(rf"\b{c}=") )
    ok("startNight does phase='night', G.t=0, G.wave++ (the director relies on exactly these side effects)", m(r"function startNight\(\)\{G\.phase='night';G\.t=0;G\.wave\+\+;"))
    ok("endGame sets G.state to 'won'/'lost' and emits ev('end')", m(r"function endGame\(win\)\{G\.state=win\?'won':'lost';ev\('end',win\)\}"))
    ok("victory text still contains 'You survived all '+WAVES+' nights' (the director rewrites it only when finalWave != WAVES)", "'You survived all '+WAVES+' nights.'" in src)
    ok("restart is a full page reload (the director keeps no state across restarts)", "location.reload()" in src)
    for i in ("wv", "rp", "rz", "nb", "ts"):
        ok(f'DOM id "{i}" present', f'id="{i}"' in src)
    # a SECOND wave controller would fight the director: who else writes the wave fields?
    writers = {k: len(re.findall(p, src)) for k, p in {
        "G.phase=": r"G\.phase\s*=[^=]", "G.wave++/=": r"G\.wave\s*(\+\+|=[^=])", "startNight(": r"\bstartNight\(", "planWave(": r"\bplanWave\(", "G.sq.shift": r"G\.sq\.shift", "callNight(": r"\bcallNight\("}.items()}
    print("   writers of wave state in the host:", writers)
    ok("no extra writers of the wave state beyond the known ones (phase: startNight+waveTick; startNight: waveTick+def; planWave: waveTick+def; sq.shift: waveTick)", writers["G.phase="] <= 3 and writers["startNight("] <= 2 and writers["planWave("] <= 2 and writers["G.sq.shift"] <= 1, writers)
    others = [ln for ln in src.splitlines() if re.search(r"\bG\.t\b", ln) and "function waveTick" not in ln and "function startNight" not in ln]
    print(f"   G.t is also touched outside waveTick/startNight on {len(others)} line(s):", [l.strip()[:70] for l in others][:4])

async def runtime_checks(p):
    print("== Part 2: runtime behaviours ==")
    b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
    pg = await b.new_page(viewport={"width": 1400, "height": 850}); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto("file://" + GAME_DIR + "/index.html")
    for i in range(500):
        await pg.wait_for_timeout(500)
        if await pg.evaluate("typeof ready!=='undefined'&&ready===1"): break
    ev = pg.evaluate
    await ev("G.speed=0")
    has_dir = await ev("!!window.FEATURE_WAVE_DIRECTOR")
    print("   director already present in this build:", has_dir)
    ok("globals reachable from a later script: G E B waveTick uiUpdate spawnE startNight planWave endGame killQuiet pickSpawns dirName", await ev("typeof G+typeof E+typeof B+typeof waveTick+typeof uiUpdate+typeof spawnE+typeof startNight+typeof planWave+typeof endGame+typeof killQuiet+typeof pickSpawns+typeof dirName")=="objectobjectobjectfunctionfunctionfunctionfunctionfunctionfunctionfunctionfunctionfunction")
    ok("waveTick / uiUpdate are writable global properties (wrappers can be installed)", await ev("(()=>{const a=Object.getOwnPropertyDescriptor(window,'waveTick'),b=Object.getOwnPropertyDescriptor(window,'uiUpdate');return !!(a&&b&&a.writable&&b.writable)})()"))
    ok("game starts with an HQ and G.started=true (survival start)", await ev("G.started&&B.some(b=>b.type==='hq')"))
    await ev("for(const e of E.slice())killQuiet(e)")
    r = await ev("""(()=>{const pts=pickSpawns();if(!pts.length)return{err:'no spawn points'};const n0=E.length,w0=G.wE;spawnE(pts[0]);const e=E[E.length-1];
      return{dn:E.length-n0,dw:G.wE-w0,en:e.en,hp:e.hp,mh:e.mh,dmg:e.dmg,wl:e.wl===undefined,dead:!!e.dead,npts:pts.length}})()""")
    ok("spawnE adds exactly one enemy at the END of E, counts G.wE, enemy has en/hp/mh/dmg and no .wl (not wilderness)", r.get("dn")==1 and r.get("dw")==1 and r.get("en")==1 and r.get("hp")>0 and r.get("hp")==r.get("mh") and r.get("dmg")>0 and r.get("wl") and not r.get("dead"), r)
    r = await ev("(()=>{const e=E[E.length-1];hurt(e,1e9);return{dead:e.dead,inE:E.includes(e),wE:G.wE}})()")
    ok("hurt() to 0 -> dead=true, removed from E, G.wE back down", r["dead"] and not r["inE"] and r["wE"]==0, r)
    r = await ev("(()=>{spawnE(pickSpawns()[0]);const e=E[E.length-1];killQuiet(e);return{dead:e.dead,inE:E.includes(e),wE:G.wE}})()")
    ok("killQuiet -> dead=true, removed, G.wE down", r["dead"] and not r["inE"] and r["wE"]==0, r)
    r = await ev("""(()=>{const mk=sm=>{const u={en:1,x:0,y:0,path:[[50,0]],ph:0,f:1,mv:0};if(sm!==undefined)u.sm=sm;steer(u,1);return u.x};return{base:mk(),x2:mk(2),x13:mk(1.35)}})()""")
    ok("steer() honours e.sm as a speed multiplier on enemies (the director's swift/brute use it)", abs(r["x2"]/r["base"]-2)<1e-6 and abs(r["x13"]/r["base"]-1.35)<1e-6, r)
    r = await ev("""(()=>{let n=0;const o=window.waveTick;window.waveTick=function(d){n++;return o(d)};stepSim(.05);window.waveTick=o;return n})()""")
    ok("stepSim(dt) reaches waveTick through the global name (wrapper is called exactly once per step)", r==1, r)
    r = await ev("""(async()=>{let n=0;const o=window.uiUpdate;window.uiUpdate=function(){n++;return o.apply(this,arguments)};await new Promise(r=>setTimeout(r,600));window.uiUpdate=o;return n})()""")
    ok("the frame loop calls uiUpdate through the global name every frame, even with G.speed=0", r>=3, r)
    if has_dir:
        print("   (director is present: skipping the host-only phase check below, it would run the director's waveTick)")
    else:
        r = await ev("""(()=>{G.t=DAYLEN;stepSim(.05);return{phase:G.phase,wave:G.wave,sq:G.sq.length,counts0:COUNTS[0],warned:G.warned,pts:G.pts.length}})()""")
        ok("host-only: G.t>=DAYLEN starts night, wave 1, builds COUNTS[0] queued {t,p} spawns", r["phase"]=="night" and r["wave"]==1 and r["sq"]==r["counts0"], r)
    await ev("G.state='play'")
    r = await ev("""(()=>{const rp=document.getElementById('rp');endGame(true);const t=rp.textContent;return t})()""")
    r2 = await ev("(()=>{drain();return document.getElementById('rp').textContent})()")
    ok("endGame(true) -> G.state 'won' and the victory text is rendered by drain() with the 'all N nights' wording", await ev("G.state")=="won" and ("all "+str(await ev("WAVES"))+" nights") in r2, r2)
    ok("no page errors during the preflight", not errs, errs[:2])
    await b.close()

async def main():
    src = open(os.path.join(GAME_DIR, "index.html"), encoding="utf-8").read()
    drift_warnings(src)
    static_checks(src)
    if os.environ.get("STATIC_ONLY") != "1":
        async with async_playwright() as p:
            await runtime_checks(p)
    print(f"{sum(R)}/{len(R)} passed (host contract)")
    sys.exit(0 if all(R) else 1)
asyncio.run(main())
