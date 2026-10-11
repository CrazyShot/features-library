"""Wave Director 1.1.0 additions: auto-resync, snapshot/restore, wave timeout, adaptive banner, sound cues, cleared stats.
  GAME_DIR=<dir with the game + director> python3 test_v11_final.py"""
import asyncio,json
from rt_common import *
J=json.dumps

async def main():
    async with async_playwright() as p:
        # ---------- A: world replacement (what a Load does): new HQ + new enemy objects ----------
        b,pg,errs=await boot(p);ev=pg.evaluate
        REPLACE="""(()=>{const nb=B.map(x=>Object.assign({},x));B.length=0;for(const x of nb)B.push(x);                       /* new building objects incl. a NEW HQ object */
          const ne=E.map(e=>Object.assign({},e,{bad:new Map(),path:(e.path||[]).slice()}));E.length=0;for(const e of ne)E.push(e);G.wE=E.filter(e=>!e.wl).length})()"""
        await ev("FEATURE_WAVE_DIRECTOR.callWave();sim(.1);sim(6)");await ev("(()=>{const l=waveEnemies();hurt(l[0],1e9)})()")
        s0=await ev("FEATURE_WAVE_DIRECTOR.status()");alive=len(await ev("waveEnemies()"))
        await ev(REPLACE);await ev("sim(.1)");s=await ev("FEATURE_WAVE_DIRECTOR.status()")
        ok("world replaced mid-wave (new HQ + enemy objects): one 'resync', wave continues with the restored enemies tracked",len(await ev("evs('resync')"))==1 and s["state"]=="wave" and s["alive"]==alive and s["wave"]==1,[s["state"],s["alive"],alive])
        await ev("sim(5)");ok("...and is NOT cleared while they live",(await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="wave" and len(await ev("evs('waveCleared')"))==0)
        await ev("killAll();sim(2.5)");ok("...completes when they are killed",(await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="recovery")
        await b.close()
        b,pg,errs=await boot(p);ev=pg.evaluate
        await ev("sim(40)");w=len(await ev("evs('warning')"));t0=await ev("G.t")
        await ev(REPLACE);await ev("sim(.1)");s=await ev("FEATURE_WAVE_DIRECTOR.status()")
        ok("world replaced in preparation (G.t=40, already warned): timer preserved, no wave started, no second warning, countdown continues",s["state"]=="prep" and abs(s["timer"]-t0-.1)<.3 and len(await ev("evs('warning')"))==w==1 and await ev("G.wave")==0 and await ev("G.warned") and len(await ev("evs('resync')"))==1,[s["state"],s["timer"],t0])
        await ev("sim(16)");ok("...and the wave starts at the normal time (55 s)",(await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="wave")
        await b.close()
        # ---------- B: snapshot / restore ----------
        b,pg,errs=await boot(p);ev=pg.evaluate
        await ev("FEATURE_WAVE_DIRECTOR.callWave();sim(.1);sim(3)");await ev("(()=>{const l=waveEnemies();hurt(l[0],1e9)})()")
        snap=await ev("JSON.parse(JSON.stringify(FEATURE_WAVE_DIRECTOR.snapshot()))")
        ok("snapshot() is plain JSON (v1) with state, counters and queue types",snap["v"]==1 and snap["state"]=="wave" and snap["spawned"]>=2 and snap["killed"]==1 and len(snap["queueTypes"])==await ev("G.sq.length"),snap)
        await ev(REPLACE)
        ok("restore(snapshot) after the host restored its world: accepted",await ev(f"FEATURE_WAVE_DIRECTOR.restore({J(snap)})"))
        s=await ev("FEATURE_WAVE_DIRECTOR.status()");ok("restore keeps the exact wave counters (spawned/total/killed) and tracks the restored enemies",s["spawned"]==snap["spawned"] and s["total"]==snap["total"] and s["killedThisWave"]==snap["killed"] and s["alive"]==len(await ev("waveEnemies()")),s)
        await ev("sim(.2)");ok("restore() installed the new HQ identity: no extra resync fired afterwards",len(await ev("evs('resync')"))==0 and len(await ev("evs('restored')"))==1)
        ok("restore() rejects a snapshot that disagrees with the host state (state wave but host phase day) and garbage",await ev("(()=>{const s=FEATURE_WAVE_DIRECTOR.snapshot();G.phase='day';const a=FEATURE_WAVE_DIRECTOR.restore(s);G.phase='night';return a})()")==False and await ev("FEATURE_WAVE_DIRECTOR.restore(null)")==False and await ev("FEATURE_WAVE_DIRECTOR.restore({v:1,state:'wave',next:-1})")==False)
        await ev("sim(12);killAll();sim(2.5)")   # let the restored queue finish spawning, then clear -> recovery
        ok("in recovery after the clear",(await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="recovery")
        await ev("sim(4)");snap=await ev("JSON.parse(JSON.stringify(FEATURE_WAVE_DIRECTOR.snapshot()))");t=await ev("G.t");await ev(REPLACE)
        ok("RECOVERY survives a load with a snapshot (without one it would resume as preparation)",await ev(f"FEATURE_WAVE_DIRECTOR.restore({J(snap)})")and (await ev("FEATURE_WAVE_DIRECTOR.status()"))["state"]=="recovery" and abs((await ev("G.t"))-t)<1e-9)
        await ev("FEATURE_WAVE_DIRECTOR.pause()");snap=await ev("JSON.parse(JSON.stringify(FEATURE_WAVE_DIRECTOR.snapshot()))");ok("a held schedule is part of the snapshot",snap["held"]==True)
        await ev("FEATURE_WAVE_DIRECTOR.resume()")
        await b.close()
        # final-wave flag in a snapshot
        b,pg,errs=await boot(p);ev=pg.evaluate
        await ev("Object.assign(FEATURE_WAVE_DIRECTOR.cfg,{finalWave:1,prepFirst:2,recovery:1,onFinalDefeated:'signal'});FEATURE_WAVE_DIRECTOR.jumpTo(1);sim(2.1);sim(12);killAll();sim(2)")
        snap=await ev("JSON.parse(JSON.stringify(FEATURE_WAVE_DIRECTOR.snapshot()))");await ev(REPLACE);await ev("FEATURE_WAVE_DIRECTOR.resync();FEATURE_WAVE_DIRECTOR.restore("+J(snap)+")");await ev("sim(120)")
        ok("finished (final wave defeated, 'signal' mode) survives restore: finalDefeated stays true and nothing new is scheduled",snap["finalDefeated"] and (await ev("FEATURE_WAVE_DIRECTOR.status()"))["finalDefeated"] and await ev("G.wave")==1 and await ev("waveEnemies().length")==0,snap["state"])
        await b.close()
        # ---------- C: wave timeout ----------
        b,pg,errs=await boot(p);ev=pg.evaluate
        await ev("FEATURE_WAVE_DIRECTOR.cfg.waveTimeout=30;FEATURE_WAVE_DIRECTOR.callWave();sim(.1)")
        await ev("sim(14);(()=>{for(const e of waveEnemies()){e.path=[];e.tg=null;e.hp=e.mh=1e9;e.sx=e.x;e.sy=e.y;e.x=e.sx;e.y=e.sy}})()")   # everything spawned; freeze nothing, just keep them alive
        await ev("(()=>{window.__keep=waveEnemies().slice(0,2);for(const e of waveEnemies())if(!window.__keep.includes(e))hurt(e,1e9)})()")
        s=await ev("FEATURE_WAVE_DIRECTOR.status()");ok("two stragglers left alive (immortal) after the rest died: wave still open",s["alive"]==2 and s["state"]=="wave",[s["alive"],s["state"]])
        await ev("sim(10)");ok("before the timeout (t<30 s) the wave is still open",(await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="wave")
        await ev("sim(8)")
        ev_t=await ev("evs('waveTimeout')");ok("timeout: event with alive=2 and action 'kill'",len(ev_t)==1 and ev_t[0]["alive"]==2 and ev_t[0]["action"]=="kill",ev_t)
        await ev("sim(2)");s=await ev("FEATURE_WAVE_DIRECTOR.status()");ok("stragglers removed quietly (host killQuiet, G.wE back to 0) and the wave clears -> recovery, no soft-lock",s["state"]=="recovery" and await ev("G.wE")==0 and await ev("waveEnemies().length")==0,[s["state"],await ev("G.wE")])
        await b.close()
        b,pg,errs=await boot(p);ev=pg.evaluate
        await ev("Object.assign(FEATURE_WAVE_DIRECTOR.cfg,{waveTimeout:25,timeoutAction:'orphan'});FEATURE_WAVE_DIRECTOR.callWave();sim(.1);sim(14)")
        await ev("(()=>{for(const e of waveEnemies()){e.hp=e.mh=1e9}const k=waveEnemies().slice(0,2);for(const e of waveEnemies())if(!k.includes(e))hurt(e,1e9)})()");await ev("sim(14)")
        s=await ev("FEATURE_WAVE_DIRECTOR.status()");ok("'orphan' action: wave clears, the 2 stragglers stay alive in the world (untracked)",s["state"]=="recovery" and len(await ev("waveEnemies()"))==2,[s["state"],len(await ev("waveEnemies()"))])
        await b.close()
        # ---------- D: banner placement, sounds, cleared stats ----------
        b,pg,errs=await boot(p);ev=pg.evaluate
        await ev("""(()=>{const rs=document.getElementById('rs');for(let i=0;i<14;i++){const x=document.createElement('button');x.textContent='Save slot '+i;x.style.margin='2px';rs.appendChild(x)}rs.style.flexWrap='wrap'})()""")
        await ev("sim(46)");await pg.wait_for_timeout(500)
        r=await ev("(()=>{const rs=document.getElementById('rs').getBoundingClientRect(),bn=document.getElementById('wavedir-banner').getBoundingClientRect();return{rsBottom:rs.bottom,bnTop:bn.top,vis:getComputedStyle(document.getElementById('wavedir-banner')).display}})()")
        ok("banner sits BELOW the host toolbar even when the toolbar is made much taller (Save/Load adds controls)",r["vis"]!="none" and r["bnTop"]>=r["rsBottom"]-0.5,r)
        await pg.screenshot(path=os.environ.get("SHOT","/tmp/wd_tall_toolbar.png"))
        await b.close()
        b,pg,errs=await boot(p);ev=pg.evaluate
        snd=await ev("""(()=>{sim(34);const a=EV.filter(e=>e[0]==='snd').map(e=>e[1]);EV.length=0;sim(21.5);const c=EV.filter(e=>e[0]==='snd').map(e=>e[1]);return{warn:a,tail:c}})()""")
        ok("sound cues through the host's ev('snd'): 'done' at the warning, 'cmd' ticks for the last 3 countdown seconds (+ host horn at wave start)","done" in snd["warn"] and snd["tail"].count("cmd")==3 and "horn" in snd["tail"],snd)
        txt=await ev("""(()=>{EV.length=0;sim(25);killAll();sim(2);return EV.filter(e=>e[0]==='toast').map(e=>e[1])})()""")
        ok("cleared toast carries kills and duration ('Wave 1 cleared · 5 slain in 26s …')",any("Wave 1 cleared · 5 slain in" in x for x in txt),txt)
        await ev("FEATURE_WAVE_DIRECTOR.cfg.sounds=false;FEATURE_WAVE_DIRECTOR.jumpTo(2);EV.length=0;sim(48)")
        ok("cfg.sounds=false silences the director's own cues (no 'done'/'cmd' from it)",await ev("EV.filter(e=>e[0]==='snd'&&(e[1]==='cmd'||e[1]==='done')).length")==0)
        ok("no console errors/warnings",not [e for e in errs if "loaded" not in e],errs[:2]);await b.close()
    print(f"{sum(R)}/{len(R)} passed (v1.1.0 final)")
    sys.exit(0 if all(R) else 1)
asyncio.run(main())
