"""Characterisation of what the Wave Director does when the host's state is REPLACED underneath it (what a Save/Load feature does), plus a cost measurement.
Run on the director test build:  GAME_DIR=<dir> python3 test_state_restore.py

Lines starting 'KNOWN LIMITATION' document behaviour that is NOT fixed in 1.0.0 (they are not counted as pass/fail; the integrator must read them).
Lines PASS/FAIL are real expectations (the mitigation and the cost bound)."""
import asyncio
from rt_common import *

def info(msg, c): print(("KNOWN LIMITATION reproduced: " if c else "NOT reproduced (behaviour changed — update INTEGRATION.md): ") + msg)

LOAD = """(snapKeys=>{
  /* what a Load does to the host: new enemy OBJECTS, G wave fields restored, G.wE recounted (as the save/load feature does) */
  const old=E.slice();E.length=0;for(const e of old)E.push(Object.assign({},e,{bad:new Map(),path:(e.path||[]).slice()}));
  G.wE=E.filter(e=>!e.wl).length;return E.length})"""

async def main():
    async with async_playwright() as p:
        # ---- R1/R2: load in the middle of a wave ----
        b,pg,errs=await boot(p);ev=pg.evaluate
        await ev("FEATURE_WAVE_DIRECTOR.callWave();sim(.1);sim(6)");await ev("(()=>{const l=waveEnemies();hurt(l[0],1e9);hurt(l[1],1e9)})()")
        s=await ev("FEATURE_WAVE_DIRECTOR.status()");alive=len(await ev("waveEnemies()"))
        print(f"   before load: wave {s['wave']} spawned {s['spawned']}/{s['total']} alive {s['alive']} queued {s['queued']}")
        await ev(f"({LOAD})()");await ev("sim(4)")
        s2=await ev("FEATURE_WAVE_DIRECTOR.status()");cleared=len(await ev("evs('waveCleared')"));aliveE=len(await ev("waveEnemies()"))
        print(f"   after naive load + 4 s: state={s2['state']} waveCleared events={cleared} enemies still alive in E={aliveE} G.wE={await ev('G.wE')}")
        info("loading mid-wave WITHOUT re-adoption: tracked enemy objects vanish from E, so the wave is declared cleared while the restored enemies are still alive",cleared==1 and aliveE>0)
        await b.close()
        b,pg,errs=await boot(p);ev=pg.evaluate
        await ev("FEATURE_WAVE_DIRECTOR.callWave();sim(.1);sim(6)");await ev("(()=>{const l=waveEnemies();hurt(l[0],1e9);hurt(l[1],1e9)})()")
        alive=len(await ev("waveEnemies()"))
        await ev(f"({LOAD})()");await ev("FEATURE_WAVE_DIRECTOR.disable();FEATURE_WAVE_DIRECTOR.enable()");await ev("sim(.1)")
        s=await ev("FEATURE_WAVE_DIRECTOR.status()")
        ok("MITIGATION disable()+enable() after a mid-wave load: director adopts the restored wave (state wave, same wave number, alive = restored enemies, still queued kept)",s["state"]=="wave" and s["wave"]==1 and s["alive"]==alive and s["alive"]>0,s)
        await ev("sim(3)");ok("...and does NOT clear the wave while they live",(await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="wave" and len(await ev("evs('waveCleared')"))==0)
        await ev("killAll();sim(2.5)");ok("...completes normally once the restored enemies are killed",(await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="recovery" and len(await ev("evs('waveCleared')"))==1)
        await b.close()
        # ---- R3: load into a preparation / recovery in a fresh session ----
        b,pg,errs=await boot(p);ev=pg.evaluate
        await ev("FEATURE_WAVE_DIRECTOR.disable();G.wave=2;G.day=3;G.phase='day';G.t=30;G.warned=true;G.pts=pickSpawns();G.sq=[]");await ev("FEATURE_WAVE_DIRECTOR.enable();sim(.1)")
        s=await ev("FEATURE_WAVE_DIRECTOR.status()")
        print(f"   restored prep (wave 2 done, G.t=30, warned) -> director: state={s['state']} nextWave={s['nextWave']} timer={s['timer']:.2f} G.warned={await ev('G.warned')} markers={await ev('G.pts.length')}")
        ok("adoption of a day-phase save resumes preparation for the right wave (wave 3)",s["state"]=="prep" and s["nextWave"]==3,s)
        info("the preparation timer restarts from 0, G.warned/G.pts are cleared (a save made at G.t=30 loses its progress; a save made in the recovery period resumes as preparation)",s["timer"]<1 and await ev("G.warned")==False and await ev("G.pts.length")==0)
        await b.close()
        # ---- R4: restoring a LATER G.t in place during preparation ----
        b,pg,errs=await boot(p);ev=pg.evaluate
        await ev("sim(2)");await ev("G.t=30;sim(.1)")     # what an in-place Load of a save taken at G.t=30 does to the host
        s=await ev("FEATURE_WAVE_DIRECTOR.status()")
        print(f"   in-place restore of G.t=2 -> 30 during preparation, then one step: state={s['state']} wave={s['wave']}")
        info("restoring a larger G.t in place without re-adoption looks like a 'call wave' jump (> 1 s forward) and starts the wave immediately",s["state"]=="wave" and s["wave"]==1)
        await b.close()
        # ---- P1: cost of death tracking ----
        b,pg,errs=await boot(p,deterministic=True);ev=pg.evaluate
        await ev("FEATURE_WAVE_DIRECTOR.cfg.countMult=8;FEATURE_WAVE_DIRECTOR.cfg.maxSpawnSpan=4;FEATURE_WAVE_DIRECTOR.jumpTo(5);sim(56);sim(8)")
        await ev("E.unshift(...Array.from({length:700},()=>({en:1,wl:1,x:5,y:5,hp:50,mh:50,dead:false})))")   # inert filler IN FRONT (as the real wilderness is): indexOf must scan past it; the sim is not stepped again
        s=await ev("FEATURE_WAVE_DIRECTOR.status()");print(f"   tracked enemies: {s['alive']} (wave {s['wave']}), E length {await ev('E.length')}")
        ms=await ev("(()=>{const t=performance.now();for(let i=0;i<500;i++)FEATURE_WAVE_DIRECTOR.status();return (performance.now()-t)/500})()")
        print(f"   one prune pass (status()) = {ms:.3f} ms with {s['alive']} tracked / {await ev('E.length')} in E")
        ok("death-tracking cost stays far below one frame budget (< 1 ms per pass at ~150 tracked + 700 other enemies; it runs once per sim step and once per frame)",ms<1.0 and s["alive"]>=100,round(ms,3))
        await b.close()
    print(f"{sum(R)}/{len(R)} passed (state restore / cost)")
    sys.exit(0 if all(R) else 1)
asyncio.run(main())
