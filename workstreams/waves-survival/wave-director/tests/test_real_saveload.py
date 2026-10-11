"""Wave Director 1.1.0 + the REAL Bastion Save/Load code (PR #12, BASTION-SAVE-LOAD-1.1.0).
  python3 build_saveload_game.py <game index.html> <FEATURE_BASTION-SAVE-LOAD.js> <dir> --director
  GAME_DIR=<dir> python3 test_real_saveload.py
Uses BASTION_SAVE_API.save()/load(). The 'adapter' scenarios do what an integrator would add: store FEATURE_WAVE_DIRECTOR.snapshot() next to the save, call restore() after load."""
import asyncio,json,re
from rt_common import *
J=json.dumps

async def part0(p):
    print("== 0: the Save/Load feature's own regression panel with the director loaded ==")
    b=await p.chromium.launch(args=["--use-gl=swiftshader","--enable-unsafe-swiftshader"]);pg=await b.new_page(viewport={"width":1400,"height":850});errs=[]
    pg.on("pageerror",lambda e:errs.append(str(e)))
    await pg.goto("file://"+GAME_DIR+"/index.html?saveLoadTest=1")
    for i in range(300):
        await pg.wait_for_timeout(500)
        if await pg.evaluate("typeof ready!=='undefined'&&ready===1"):break
    txt=""
    for i in range(40):
        await pg.wait_for_timeout(1000);txt=await pg.evaluate("document.getElementById('saveLoadTestResults')?document.getElementById('saveLoadTestResults').textContent:''")
        if re.search(r"\d+\s*/\s*\d+|passed",txt,re.I) and txt.count("PASS")+txt.count("FAIL")>=15:break
    npass,nfail=txt.count("PASS "),txt.count("FAIL")
    print("   panel:",txt[:90].replace("\n"," | "),"... PASS lines:",npass,"FAIL lines:",nfail)
    ok("Save/Load's own self-test panel: no FAIL lines with the director present, >= 15 PASS lines",nfail==0 and npass>=15,[npass,nfail])
    ok("no page errors",not errs,errs[:2]);await b.close()

async def main():
    async with async_playwright() as p:
        await part0(p)
        # ---------- 1: mid-wave, NO glue ----------
        b,pg,errs=await boot(p);ev=pg.evaluate
        await ev("FEATURE_WAVE_DIRECTOR.callWave();sim(.1);sim(4)");await ev("(()=>{const l=waveEnemies();hurt(l[0],1e9)})()")
        pre=await ev("({alive:waveEnemies().length,q:G.sq.length,wE:G.wE})")
        ok("BASTION_SAVE_API.save() succeeds mid-wave",await ev("BASTION_SAVE_API.save()")=="Manual save saved")
        await ev("killAll();sim(25)");await ev("BASTION_SAVE_API.load()")
        ok("load() restores the host wave (night, wave 1, same enemies and queued spawns)",await ev("G.phase")=="night" and await ev("G.wave")==1 and len(await ev("waveEnemies()"))==pre["alive"] and await ev("G.sq.length")==pre["q"],pre)
        await ev("sim(.1)");s=await ev("FEATURE_WAVE_DIRECTOR.status()")
        ok("WITHOUT any glue: director auto-resyncs once and continues the wave (tracked = restored enemies, queue kept)",len(await ev("evs('resync')"))==1 and s["state"]=="wave" and s["alive"]==pre["alive"] and s["queued"]==pre["q"],s)
        ok("the saved queue kept its enemy types through the real save format",await ev("G.sq.every(q=>q.type==='grunt')"))
        await ev("sim(6)");ok("not cleared while restored enemies live",(await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="wave" and len(await ev("evs('waveCleared')"))==0)
        ok("no console errors/warnings during the real round trip",not [e for e in errs if "loaded" not in e],errs[:2])
        await ev("sim(12);killAll();sim(2.5)");ok("wave completes normally afterwards (all queued spawns arrive, one waveCleared)",(await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="recovery" and len(await ev("evs('waveCleared')"))==1)
        await b.close()
        # ---------- 2: mid-wave WITH the snapshot adapter ----------
        b,pg,errs=await boot(p);ev=pg.evaluate
        await ev("FEATURE_WAVE_DIRECTOR.callWave();sim(.1);sim(4)");await ev("(()=>{const l=waveEnemies();hurt(l[0],1e9)})()")
        snap=await ev("(()=>{window.__snap=JSON.parse(JSON.stringify(FEATURE_WAVE_DIRECTOR.snapshot()));BASTION_SAVE_API.save();return window.__snap})()")
        await ev("killAll();sim(25)");await ev("BASTION_SAVE_API.load();FEATURE_WAVE_DIRECTOR.restore(window.__snap)");await ev("sim(.1)")
        s=await ev("FEATURE_WAVE_DIRECTOR.status()")
        ok("with the adapter: exact counters (spawned/total/killed) survive the real load and NO resync was needed",s["spawned"]==snap["spawned"] and s["total"]==snap["total"] and s["killedThisWave"]==snap["killed"] and len(await ev("evs('resync')"))==0 and len(await ev("evs('restored')"))==1,s)
        await b.close()
        # ---------- 3: preparation ----------
        b,pg,errs=await boot(p);ev=pg.evaluate
        await ev("sim(40)");t=await ev("G.t");w=await ev("G.warned")
        ok("save() in preparation (G.t=40, already warned)",await ev("BASTION_SAVE_API.save()")=="Manual save saved" and w)
        await ev("sim(10)");await ev("BASTION_SAVE_API.load()");await ev("sim(.1)");s=await ev("FEATURE_WAVE_DIRECTOR.status()")
        ok("load() in preparation (no glue): timer back at the saved 40 s, still preparing wave 1, warning flag + markers kept, wave NOT started",s["state"]=="prep" and abs(s["timer"]-t)<.5 and s["wave"]==0 and await ev("G.warned")==True and await ev("showPts().length")>0,[s["state"],s["timer"],t])
        await ev("sim(14)");ok("...the wave then starts at the normal time (55 s), not early",(await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="prep");await ev("sim(1.5)")
        ok("...and starts when preparation ends",(await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="wave")
        await b.close()
        # ---------- 4: recovery ----------
        b,pg,errs=await boot(p);ev=pg.evaluate
        await ev("FEATURE_WAVE_DIRECTOR.callWave();sim(.1);sim(16);killAll();sim(2);sim(3)")
        ok("in recovery before saving",(await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="recovery")
        snap=await ev("(()=>{window.__snap=JSON.parse(JSON.stringify(FEATURE_WAVE_DIRECTOR.snapshot()));BASTION_SAVE_API.save();return window.__snap})()")
        await ev("sim(20)");await ev("BASTION_SAVE_API.load()");await ev("sim(.1)")
        print("   without adapter, a recovery save resumes as:",await ev("FEATURE_WAVE_DIRECTOR.status().state"))
        ok("recovery save, NO adapter: resumes as preparation for the right wave (documented degradation, no wave skipped, no error)",(await ev("FEATURE_WAVE_DIRECTOR.status()"))["state"]=="prep" and (await ev("FEATURE_WAVE_DIRECTOR.status().nextWave"))==2)
        await ev("sim(15);BASTION_SAVE_API.load();FEATURE_WAVE_DIRECTOR.restore(window.__snap);sim(.1)")
        ok("recovery save, WITH adapter: resumes as recovery",(await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="recovery")
        await b.close()
        # ---------- 5: save limit beyond the host's WAVES ----------
        b,pg,errs=await boot(p);ev=pg.evaluate
        await ev("Object.assign(FEATURE_WAVE_DIRECTOR.cfg,{finalWave:Infinity,prepFirst:1,prepBetween:1,recovery:0});FEATURE_WAVE_DIRECTOR.jumpTo(6);sim(1.1);sim(3)")
        w=await ev("G.wave");r=await ev("(()=>{try{return String(BASTION_SAVE_API.save())}catch(e){return 'THROWS '+e.message}})()")
        print(f"   save() at G.wave={w} (host WAVES=5) ->",r)
        ok("KNOWN: Save/Load refuses to save beyond the host's WAVES (wave 6 here) — endless / longer runs cannot be saved until its validator limit is raised",w==6 and "saved" not in r.lower().replace("not saved","").replace("cannot be saved",""),r)
        await b.close()
    print(f"{sum(R)}/{len(R)} passed (real save/load)")
    sys.exit(0 if all(R) else 1)
asyncio.run(main())
