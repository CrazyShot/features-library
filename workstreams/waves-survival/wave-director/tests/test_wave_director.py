"""Wave Director tests. Run:  GAME_DIR=<dir with test build> python3 test_wave_director.py
Build the test build first:  python3 build_test_game.py <main-game index.html> <dir>
Drives the game's OWN stepSim(dt) (so waveTick / spawnE / hurt->killT / endGame are the real host code) with G.speed=0 and hand-stepped time."""
import asyncio
from rt_common import *

async def part_a(p):
    print("== A: boot, tables, warning, countdown, consecutive waves, deaths, completion, recovery ==")
    b,pg,errs=await boot(p);ev=pg.evaluate
    st=await ev("FEATURE_WAVE_DIRECTOR.status()")
    ok("module loaded; starts in preparation for wave 1 (final wave = host WAVES = 5)",st["state"]=="prep" and st["nextWave"]==1 and st["finalWave"]==5 and st["phase"]=="day",st)
    ok("no wave enemies before the first attack",await ev("waveEnemies().length")==0)
    counts=await ev("[1,2,3,4,5,6,7].map(FEATURE_WAVE_DIRECTOR.countFor)")
    ok("counts follow the host table 5,8,11,14,18 then +4/wave",counts==[5,8,11,14,18,22,26],counts)
    comp=await ev("[1,2,3,4,5,6].map(w=>FEATURE_WAVE_DIRECTOR.composition(w))")
    ok("compositions sum to the counts and vary with the wave",all(sum(c.values())==n for c,n in zip(comp,[5,8,11,14,18,22])) and comp[0]=={"grunt":5} and comp[1]=={"grunt":8} and comp[2].get("swift",0)>=1 and comp[3].get("brute",0)>=1 and comp[4].get("brute",0)>comp[3].get("brute",0),comp)
    # --- warning + countdown
    await ev("sim(30)");rem=await ev("FEATURE_WAVE_DIRECTOR.status().remaining")
    ok("no warning yet 25 s before the wave",await ev("evs('warning').length")==0 and await ev("G.warned")==False,round(rem,1))
    await ev("sim(4)")    # remaining ~21 (<22)
    w=await ev("evs('warning')");ok("warning fires once, ~22 s before wave 1, with spawn points marked",len(w)==1 and 20<=w[0]["seconds"]<=22 and await ev("G.warned&&G.pts.length>0&&showPts().length>0"),w)
    await pg.wait_for_timeout(400);ok("the host's own warning path ran (toast 'Attack expected from ...')","Attack expected" in await ev("document.getElementById('ts').textContent"),await ev("document.getElementById('ts').textContent"))
    await ev("sim(12)")   # ~9 s left
    await pg.wait_for_timeout(400);txt=await ev("document.getElementById('wv').textContent");bn=await ev("(()=>{const b=document.getElementById('wavedir-banner');return b?[getComputedStyle(b).display,b.textContent]:null})()")
    ok("HUD line + banner show the countdown",("Preparation" in txt and "wave 1/5" in txt and "attack from" in txt) and bn and bn[0]!="none" and "WAVE 1 IN" in bn[1],[txt,bn])
    await ev("sim(8.5)")
    cd=[e["seconds"] for e in await ev("evs('countdown')")]
    ok("countdown events 10,5,4,3,2,1 each exactly once, in order",cd==[10,5,4,3,2,1],cd)
    await ev("simUntil(\"G.phase==='night'\")")
    st=await ev("FEATURE_WAVE_DIRECTOR.status()")
    ok("wave 1 starts when preparation ends: host phase night, G.wave=1",st["state"]=="wave" and st["wave"]==1 and await ev("G.phase")=="night",st)
    await pg.wait_for_timeout(400);ok("wave-start toast came from the host startNight ('Wave 1 — the horde approaches')","horde approaches" in await ev("document.getElementById('ts').textContent"),await ev("document.getElementById('ts').textContent"))
    ok("no enemy yet at wave start",await ev("waveEnemies().length")==0)
    await ev("sim(1.5)");n0=await ev("waveEnemies().length")
    await ev("sim(.9)");n1=await ev("waveEnemies().length")
    ok("spawning is scheduled (nothing at 1.5 s, first at 2 s)",n0==0 and n1==1,[n0,n1])
    await ev("sim(8)")
    st=await ev("FEATURE_WAVE_DIRECTOR.status()");we=await ev("waveEnemies().length");gwe=await ev("G.wE")
    ok("all 5 enemies of wave 1 spawned through the host spawnE; tracked = host counters",st["spawned"]==5 and st["total"]==5 and we==5 and gwe==5 and st["alive"]==5 and st["queued"]==0,[st["spawned"],we,gwe])
    info=await ev("waveEnemies().map(e=>[e.hp,e.mh,e.dmg,e.sm||1,e.wtype,e.en])")
    ok("wave 1 enemies are unmodified host enemies (hp 40, dmg 6, speed x1)",all(i[0]==40 and i[1]==40 and i[2]==6 and i[3]==1 and i[4]=="grunt" and i[5]==1 for i in info),info[:2])
    ok("spawn events carry index/total",[e["index"] for e in await ev("evs('spawn')")]==[1,2,3,4,5])
    sp=[e["T"] for e in await ev("evs('spawn')")];ok("spawn spacing ~0.8 s",all(.6<=b_-a<=1.0 for a,b_ in zip(sp,sp[1:])),sp)
    # --- deaths
    await ev("(()=>{const l=waveEnemies();hurt(l[0],1e9);hurt(l[1],1e9)})()")
    st=await ev("FEATURE_WAVE_DIRECTOR.status()")
    ok("two kills: alive 3, killed 2, host G.wE agrees, wave NOT complete",st["alive"]==3 and st["killedThisWave"]==2 and await ev("G.wE")==3 and st["state"]=="wave")
    await ev("sim(3)");ok("wave still running while enemies remain",(await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="wave")
    await ev("killAll()");await ev("sim(.5)");ok("not cleared before the clear delay (1 s)",(await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="wave")
    await ev("sim(1)")
    st=await ev("FEATURE_WAVE_DIRECTOR.status()")
    ok("wave 1 cleared: waveCleared emitted once, recovery started, host phase back to day",len(await ev("evs('waveCleared')"))==1 and st["state"]=="recovery" and await ev("G.phase")=="day" and await ev("G.day")==2,st["state"])
    ok("no spawn markers / warning during recovery",await ev("showPts().length")==0 and await ev("G.warned")==False)
    await pg.wait_for_timeout(300);ok("HUD says recovering",("recover" in (await ev("document.getElementById('wv').textContent")).lower()))
    await ev("sim(9)");ok("recovery lasts 10 s",(await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="recovery")
    await ev("sim(1.5)");st=await ev("FEATURE_WAVE_DIRECTOR.status()")
    ok("then preparation for wave 2 (45 s)",st["state"]=="prep" and st["nextWave"]==2 and 43<=st["remaining"]<=45,round(st["remaining"],1))
    # --- consecutive waves 2..5
    stats={}
    for wv in (2,3,4,5):
        await ev("simUntil(\"G.phase==='night'\")")
        await ev("sim(20)")
        st=await ev("FEATURE_WAVE_DIRECTOR.status()")
        stats[wv]=await ev(f"evs('spawn').filter(e=>e.wave=={wv})")
        ok(f"wave {wv}: {FEATURE_N[wv]} enemies scheduled, spawned and tracked (host G.wE agrees)",st["wave"]==wv and st["spawned"]==FEATURE_N[wv] and st["total"]==FEATURE_N[wv] and len(stats[wv])==FEATURE_N[wv] and await ev("G.wE")==FEATURE_N[wv] and await ev("waveEnemies().length")==FEATURE_N[wv],[st["wave"],st["spawned"],len(stats[wv])])
        await ev("killAll()");await ev("sim(2)")
        st=await ev("FEATURE_WAVE_DIRECTOR.status()")
        if wv<5:
            ok(f"wave {wv} cleared -> recovery",st["state"]=="recovery" and len(await ev("evs('waveCleared')"))==wv,st["state"])
            await ev("simUntil(\"G.phase==='night'||FEATURE_WAVE_DIRECTOR.status().state==='prep'\")")
    kinds={w:{} for w in stats}
    for w,l in stats.items():
        for i in l:kinds[w][i["kind"]]=kinds[w].get(i["kind"],0)+1
    ok("compositions match the table in the live waves (3 has swifts, 4-5 have brutes)",kinds[3].get("swift",0)>=1 and kinds[4].get("brute",0)>=1 and kinds[5].get("brute",0)>kinds[4].get("brute",0) and "brute" not in kinds[2] and "swift" not in kinds[2],kinds)
    tot=[sum(i["hp"] for i in stats[w]) for w in (2,3,4,5)]
    ok("total enemy hp rises every wave (difficulty increases)",tot[0]<tot[1]<tot[2]<tot[3],[round(t) for t in tot])
    gr=[i for i in stats[5] if i["kind"]=="grunt"][0];sw=[i for i in stats[5] if i["kind"]=="swift"][0];br=[i for i in stats[5] if i["kind"]=="brute"][0]
    ok("types use the host's own fields: brute hp x2.4 dmg x1.6 speed .8; swift hp x.6 speed 1.35",abs(br["hp"]/gr["hp"]-2.4)<.01 and abs(sw["hp"]/gr["hp"]-.6)<.01 and br["sm"]==.8 and sw["sm"]==1.35 and br["dmg"]>gr["dmg"],[gr,sw,br])
    ok("host hp curve preserved: grunt hp = 40*(1+.12*(wave-1)) in wave 5",abs(gr["hp"]-40*(1+.12*4))<.01,gr["hp"])
    ok("final wave (5) announced: finalWaveStart emitted exactly once",len(await ev("evs('finalWaveStart')"))==1 and (await ev("evs('waveStart')[4].final")))
    ok("final wave defeated: signal emitted once, finalDefeated flag set, host victory reached",len(await ev("evs('finalWaveDefeated')"))==1 and await ev("FEATURE_WAVE_DIRECTOR.status().finalDefeated") and await ev("G.state")=="won",await ev("G.state"))
    await ev("sim(200)");ok("nothing else is scheduled after victory",await ev("waveEnemies().length")==0 and await ev("G.wave")==5)
    ok("A: no console errors/warnings",not [e for e in errs if "WAVE-DIRECTOR-1.0.0] loaded" not in e],errs[:3]);await b.close()
FEATURE_N={2:8,3:11,4:14,5:18}

async def part_b(p):
    print("== B: pause/resume, speed, hold, call wave, cancel/restart, dev removal ==")
    b,pg,errs=await boot(p);ev=pg.evaluate
    # game pause during preparation (rAF keeps running)
    await ev("G.speed=1");await pg.wait_for_timeout(1200);await ev("G.speed=0")
    t0=await ev("G.t");await pg.wait_for_timeout(1500);t1=await ev("G.t")
    ok("game paused (speed 0): preparation timer frozen for 1.5 real seconds",abs(t1-t0)<1e-9 and t0>0.5,[t0,t1])
    await ev("G.speed=1");await pg.wait_for_timeout(2000);a=await ev("G.t");await ev("G.speed=0")
    await ev("G.speed=3");await pg.wait_for_timeout(2000);c=await ev("G.t");await ev("G.speed=0")
    r1=a-t1;r3=c-a
    ok("resume continues from the same point; 3x speed runs ~3x faster",r1>1.0 and 2.2<=r3/r1<=3.9,[round(r1,2),round(r3,2)])
    # pause mid-spawn
    await ev("jumpFast=FEATURE_WAVE_DIRECTOR.callWave()");await ev("sim(.1)");await ev("sim(3.5)")
    s1=await ev("FEATURE_WAVE_DIRECTOR.status()");ok("wave 1 running, partly spawned",s1["state"]=="wave" and 0<s1["spawned"]<5,[s1["spawned"],s1["total"]])
    await ev("G.speed=0");await pg.wait_for_timeout(1500);s2=await ev("FEATURE_WAVE_DIRECTOR.status()")
    ok("pause mid-spawn: no spawns, timer frozen",s2["spawned"]==s1["spawned"] and s2["timer"]==s1["timer"])
    await ev("G.speed=2");await pg.wait_for_timeout(5000);await ev("G.speed=0");s3=await ev("FEATURE_WAVE_DIRECTOR.status()")
    idx=[e["index"] for e in await ev("evs('spawn')")]
    ok("resume: remaining spawns arrive exactly once each, in order (no skip, no burst, no duplicates)",s3["spawned"]==5 and idx==[1,2,3,4,5] and await ev("G.wE")==5,idx)
    ok("pause / resume events were emitted",len(await ev("evs('pause')"))>=1 and len(await ev("evs('resume')"))>=1)
    # director hold while the game runs
    await ev("FEATURE_WAVE_DIRECTOR.pause()");await ev("killAll()");await ev("sim(5)")
    ok("hold(): killing everything does not complete the wave while held",(await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="wave" and (await ev("FEATURE_WAVE_DIRECTOR.status().held")))
    await pg.wait_for_timeout(300);ok("HUD shows HELD","HELD" in await ev("document.getElementById('wv').textContent"))
    await ev("FEATURE_WAVE_DIRECTOR.resume()");await ev("sim(2)");ok("release(): the wave completes normally",(await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="recovery")
    # host callNight (N key / button)
    await ev("sim(11)");ok("in prep for wave 2",(await ev("FEATURE_WAVE_DIRECTOR.status()"))["state"]=="prep" and (await ev("FEATURE_WAVE_DIRECTOR.status().nextWave"))==2)
    await ev("callNight();sim(.1)");s=await ev("FEATURE_WAVE_DIRECTOR.status()")
    ok("the host's callNight() (N key / Call wave button) starts the wave immediately",s["state"]=="wave" and s["wave"]==2,[s["state"],s["wave"]])
    # dev tool removal + quiet removal count as down
    await ev("sim(30)");await ev("devClear()");await ev("sim(1.5)")
    ok("devClear() / quiet removals: wave still completes (tracked by enemy object, not only by G.wE)",(await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="recovery")
    # cancel mid wave keeping enemies
    await ev("sim(11)");await ev("FEATURE_WAVE_DIRECTOR.callWave();sim(.1);sim(4)");s=await ev("FEATURE_WAVE_DIRECTOR.status()")
    ok("wave 3 running with enemies out",s["state"]=="wave" and s["wave"]==3 and s["alive"]>=1,[s["wave"],s["alive"],s["queued"]])
    alive=await ev("waveEnemies().length")
    ok("cancel() returns true",await ev("FEATURE_WAVE_DIRECTOR.cancel()")==True)
    s=await ev("FEATURE_WAVE_DIRECTOR.status()")
    ok("cancel mid-wave: unspawned enemies discarded, queue empty, phase day, markers gone, spawned enemies left alone",s["state"]=="cancelled" and s["queued"]==0 and await ev("G.phase")=="day" and await ev("showPts().length")==0 and await ev("waveEnemies().length")==alive,[s["state"],alive])
    ev_c=await ev("evs('cancelled')");ok("cancelled event reports midWave and surviving enemies",len(ev_c)==1 and ev_c[0]["midWave"] and ev_c[0]["enemiesLeftAlive"]==alive,ev_c)
    await ev("killAll()");await ev("sim(200)");ok("nothing spawns or starts after cancel (200 s)",await ev("waveEnemies().length")==0 and (await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="cancelled" and await ev("G.wave")==3)
    ok("cancel when already cancelled is a no-op (false)",await ev("FEATURE_WAVE_DIRECTOR.cancel()")==False)
    ok("start() restarts the cancelled wave number (3) from a fresh preparation",await ev("FEATURE_WAVE_DIRECTOR.start()") and (await ev("FEATURE_WAVE_DIRECTOR.status().nextWave"))==3 and (await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="prep")
    await ev("sim(46)");await ev("sim(4)");s=await ev("FEATURE_WAVE_DIRECTOR.status()");ok("restarted wave 3 runs with its full 11 enemies",s["state"]=="wave" and s["wave"]==3 and s["total"]==11)
    ok("cancel with killEnemies: all tracked enemies removed, host G.wE back to 0",await ev("FEATURE_WAVE_DIRECTOR.cancel({killEnemies:true})") and await ev("waveEnemies().length")==0 and await ev("G.wE")==0)
    await ev("FEATURE_WAVE_DIRECTOR.jumpTo(4)");s=await ev("FEATURE_WAVE_DIRECTOR.status()");ok("jumpTo(4) -> preparation for wave 4",s["state"]=="prep" and s["nextWave"]==4)
    ok("cancel during preparation: no wave ever starts",await ev("FEATURE_WAVE_DIRECTOR.cancel()") and (await ev("sim(300);FEATURE_WAVE_DIRECTOR.status().state"))=="cancelled" and await ev("G.wave")==3)
    ok("B: no console errors/warnings",not [e for e in errs if "loaded" not in e],errs[:3]);await b.close()

async def part_c(p):
    print("== C: configurable final wave, signal-only mode, endless, HQ loss, handoff ==")
    b,pg,errs=await boot(p);ev=pg.evaluate
    await ev("FEATURE_WAVE_DIRECTOR.cfg.finalWave=2;FEATURE_WAVE_DIRECTOR.cfg.prepFirst=5;FEATURE_WAVE_DIRECTOR.cfg.prepBetween=5;FEATURE_WAVE_DIRECTOR.cfg.recovery=2;FEATURE_WAVE_DIRECTOR.jumpTo(1)")
    await ev("window.__sig=0;window.addEventListener('bastion:final-wave-defeated',()=>window.__sig++)")
    await ev("sim(5.1);sim(15)");ok("wave 1 of 2 running; not final",(await ev("FEATURE_WAVE_DIRECTOR.status()"))["wave"]==1 and not (await ev("FEATURE_WAVE_DIRECTOR.status().isFinal")))
    await pg.wait_for_timeout(300);ok("HUD shows wave 1/2","WAVE 1/2" in await ev("document.getElementById('wv').textContent"),await ev("document.getElementById('wv').textContent"))
    await ev("killAll();sim(2);sim(2.5)");ok("-> recovery -> prep for wave 2 flagged FINAL",(await ev("FEATURE_WAVE_DIRECTOR.status()"))["state"]=="prep" and (await ev("FEATURE_WAVE_DIRECTOR.status().isFinal")) and (await ev("evs('prepStart')[1].final")))
    await ev("sim(6)");ok("final wave started: finalWaveStart emitted, 8 enemies planned",len(await ev("evs('finalWaveStart')"))==1 and (await ev("FEATURE_WAVE_DIRECTOR.status().total"))==8)
    await ev("sim(12)");await ev("killAll();sim(2)")
    ok("final wave defeated -> one signal (callback + DOM event) and host victory",len(await ev("evs('finalWaveDefeated')"))==1 and await ev("window.__sig")==1 and await ev("G.state")=="won" and (await ev("FEATURE_WAVE_DIRECTOR.status().finalDefeated")))
    await pg.wait_for_timeout(300);ok("victory text uses the configured final wave (2) not the host constant",("all 2 waves" in await ev("document.getElementById('rp').textContent")),await ev("document.getElementById('rp').textContent"))
    await b.close()
    # --- signal-only
    b,pg,errs2=await boot(p);ev=pg.evaluate
    await ev("Object.assign(FEATURE_WAVE_DIRECTOR.cfg,{finalWave:1,prepFirst:3,prepBetween:3,recovery:1,onFinalDefeated:'signal'});FEATURE_WAVE_DIRECTOR.jumpTo(1)")
    await ev("sim(3.1);sim(12)");await ev("killAll();sim(2)")
    s=await ev("FEATURE_WAVE_DIRECTOR.status()")
    ok("onFinalDefeated:'signal': signal emitted but the game stays in play (caller decides)",len(await ev("evs('finalWaveDefeated')"))==1 and await ev("G.state")=="play" and s["state"]=="finished" and s["finalDefeated"],s["state"])
    await ev("sim(120)");ok("no further wave is scheduled after the final one",await ev("waveEnemies().length")==0 and await ev("G.wave")==1)
    ok("start({wave}) can continue afterwards (e.g. a custom epilogue / endless)",await ev("FEATURE_WAVE_DIRECTOR.cfg.finalWave=Infinity;FEATURE_WAVE_DIRECTOR.start({wave:2})") and (await ev("FEATURE_WAVE_DIRECTOR.status().nextWave"))==2 and not await ev("FEATURE_WAVE_DIRECTOR.status().finalDefeated"))
    await b.close()
    # --- endless + counts beyond table
    b,pg,errs3=await boot(p);ev=pg.evaluate
    await ev("Object.assign(FEATURE_WAVE_DIRECTOR.cfg,{finalWave:Infinity,prepFirst:2,prepBetween:2,recovery:0});FEATURE_WAVE_DIRECTOR.jumpTo(7)")
    await ev("sim(2.1);sim(40)");s=await ev("FEATURE_WAVE_DIRECTOR.status()")
    ok("endless: wave 7 is not final, size 26 (table extrapolated), all spawned within the span cap",s["wave"]==7 and not s["isFinal"] and s["finalWave"] is None and s["total"]==26 and s["spawned"]==26,[s["wave"],s["total"],s["spawned"]])
    await ev("killAll();sim(1.2)");s=await ev("FEATURE_WAVE_DIRECTOR.status()");ok("endless: recovery 0 -> straight to preparation of wave 8",s["state"]=="prep" and s["nextWave"]==8,[s["state"],s["nextWave"]])
    # huge wave compression
    await ev("FEATURE_WAVE_DIRECTOR.cfg.countMult=4;FEATURE_WAVE_DIRECTOR.cfg.maxSpawnSpan=10;FEATURE_WAVE_DIRECTOR.jumpTo(8)");await ev("sim(2.1)");await ev("sim(12.5)");s=await ev("FEATURE_WAVE_DIRECTOR.status()")
    ok("a very large wave (120) is compressed to the span cap (all arrive within ~12 s)",s["total"]==120 and s["spawned"]==120,[s["total"],s["spawned"]])
    await ev("killAll()");await b.close()
    # --- HQ loss + handoff
    b,pg,errs4=await boot(p);ev=pg.evaluate
    await ev("hurt(B.find(b=>b.type==='hq'),1e9);sim(1)")
    ok("HQ destroyed: lost event, host defeat screen",await ev("G.state")=="lost" and len(await ev("evs('lost')"))==1)
    await b.close()
    b,pg,errs5=await boot(p);ev=pg.evaluate
    await ev("sim(10);FEATURE_WAVE_DIRECTOR.disable();G.t=DAYLEN;sim(.2)")
    ok("disable(): hands control back to the host's original waveTick (host night starts at DAYLEN)",await ev("G.phase")=="night" and await ev("G.wave")==1 and await ev("G.sq.length")>0)
    await ev("FEATURE_WAVE_DIRECTOR.enable();sim(.1)");s=await ev("FEATURE_WAVE_DIRECTOR.status()")
    ok("enable(): adopts the running host wave without errors",s["state"]=="wave" and s["wave"]==1 and s["total"]==5,[s["state"],s["total"]])
    ok("C: no console errors/warnings",not [e for e in errs+errs2+errs3+errs4+errs5 if "loaded" not in e],(errs+errs2+errs3+errs4+errs5)[:3]);await b.close()

async def part_d(p):
    print("== D: real combat left ON (host defenders / towers), wave 1 resolves on its own ==")
    b,pg,errs=await boot(p,deterministic=False);ev=pg.evaluate
    hq0=await ev("B.find(b=>b.type==='hq').hp");print("   defenders:",await ev("U.length"),"units, towers:",await ev("B.filter(b=>b.type==='tower').length"))
    await ev("callNight?FEATURE_WAVE_DIRECTOR.callWave():0");t=await ev("sim(.1);simUntil(\"FEATURE_WAVE_DIRECTOR.status().state!=='wave'\",240)")
    s=await ev("FEATURE_WAVE_DIRECTOR.status()");hq1=await ev("B.find(b=>b.type==='hq')?B.find(b=>b.type==='hq').hp:0")
    print(f"   wave 1 resolved after {t}s sim: state={s['state']} killed={s['killedThisWave']}/{s['total']} HQ hp {hq0}->{round(hq1)} G.wE={await ev('G.wE')}")
    ok("with the host's own combat the wave resolves by itself (director sees every death) and G.wE is back to 0",s["state"] in("recovery",) and s["killedThisWave"]==5 and await ev("G.wE")==0,[s["state"],s["killedThisWave"]])
    ok("D: no console errors/warnings",not [e for e in errs if "loaded" not in e],errs[:3]);await b.close()

async def main():
    async with async_playwright() as p:
        await part_a(p);await part_b(p);await part_c(p);await part_d(p)
    print(f"{sum(R)}/{len(R)} passed (wave director)")
    sys.exit(0 if all(R) else 1)
asyncio.run(main())
