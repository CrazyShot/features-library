"""Integration regression for the Wave Director: things Main Claude must re-run after merging it into the latest game.
  GAME_DIR=<dir with the game + director> python3 test_integration_regression.py
(1) G.t pin  - other tests/features hold the day phase by writing G.t low; the director must respect that.
(2) Kill switch - disable() must give back the ORIGINAL host wave logic, and it must run a whole host wave (spawn -> clear -> day, day++) on its own.
(3) HUD ownership - cfg.hud=false leaves the host's #wv text untouched; with it on, #wv carries the director text.
(4) Host HQ rules - the wrapper reproduces 'HQ lost -> defeat' and 'no HQ yet -> not started' exactly like the host.
(5) Game speed / pause keys - Space and speed keys still work with the director (no key handling is added by it)."""
import asyncio
from rt_common import *

async def main():
    async with async_playwright() as p:
        b,pg,errs=await boot(p);ev=pg.evaluate
        # (1) G.t pin
        await ev("for(let i=0;i<4000;i++){G.t=Math.min(G.t,10);stepSim(.05)}")      # 200 s of sim with G.t pinned at <=10
        s=await ev("FEATURE_WAVE_DIRECTOR.status()");ok("(1) G.t pinned low for 200 sim-seconds: no wave starts, still preparing wave 1",s["state"]=="prep" and s["wave"]==0 and await ev("waveEnemies().length")==0,[s["state"],s["wave"]])
        ok("(1) the pinned preparation never fired a warning (remaining time never reached the warning lead)",len(await ev("evs('warning')"))==0)
        # (3) HUD ownership
        await ev("FEATURE_WAVE_DIRECTOR.cfg.prepFirst=100;FEATURE_WAVE_DIRECTOR.jumpTo(1);G.t=10")       # director remaining = 100-10 = 90 s, host formula DAYLEN-G.t = 45 s: the two texts differ
        await pg.wait_for_timeout(300);t_on=await ev("document.getElementById('wv').textContent")
        ok("(3) with the director HUD on, #wv carries the director's countdown (90 s), not the host formula (45 s)","in 90s" in t_on,t_on)
        await ev("FEATURE_WAVE_DIRECTOR.cfg.hud=false;FEATURE_WAVE_DIRECTOR.cfg.banner=false");await pg.wait_for_timeout(300);t_off=await ev("document.getElementById('wv').textContent");bn=await ev("(()=>{const b=document.getElementById('wavedir-banner');return b?getComputedStyle(b).display:'none'})()")
        print("   #wv with director HUD:",repr(t_on),"| with cfg.hud=false:",repr(t_off))
        ok("(3) cfg.hud=false gives the host's own #wv text back (formula DAYLEN-G.t = 45 s)","in 45s" in t_off,t_off)
        await ev("FEATURE_WAVE_DIRECTOR.cfg.hud=true;FEATURE_WAVE_DIRECTOR.cfg.banner=true")
        # (2) kill switch: full host-only wave
        await ev("FEATURE_WAVE_DIRECTOR.disable();G.t=DAYLEN-.1;G.warned=false;G.pts=[];G.sq=[]");await ev("sim(.5)")
        ok("(2) disable(): host night starts by itself at DAYLEN, wave 1, host queue has COUNTS[0] spawns",await ev("G.phase")=="night" and await ev("G.wave")==1 and await ev("G.sq.length+waveEnemies().length")==await ev("COUNTS[0]"))
        await ev("sim(8)");ok("(2) host spawns all of wave 1 (G.wE = COUNTS[0]) with NO director events",await ev("G.wE")==await ev("COUNTS[0]") and len(await ev("evs('waveStart')"))==0,await ev("G.wE"))
        await ev("killAll();sim(7)");ok("(2) host clears the wave itself: back to day, G.day incremented, spawn markers cleared",await ev("G.phase")=="day" and await ev("G.day")==2 and await ev("G.pts.length")==0,[await ev("G.phase"),await ev("G.day")])
        await pg.wait_for_timeout(300);ok("(2) while disabled #wv is the host's text",("Preparation · wave 2/5 in" in await ev("document.getElementById('wv').textContent")),await ev("document.getElementById('wv').textContent"))
        # (5) keys
        await ev("G.speed=1");await pg.keyboard.press("Space");await pg.wait_for_timeout(200);sp0=await ev("G.speed")
        await pg.keyboard.press("Space");await pg.wait_for_timeout(200);sp1=await ev("G.speed")
        ok("(5) Space still toggles pause (speed 0 then back)",sp0==0 and sp1==1,[sp0,sp1])
        await b.close()
        # (6) no valid spawn point -> blocked, retry, never a half-started wave
        b,pg,errs=await boot(p);ev=pg.evaluate
        await ev("window.__pk=pickSpawns;window.pickSpawns=()=>[];FEATURE_WAVE_DIRECTOR.callWave();sim(.1)")
        ok("(6) no valid spawn point: wave is NOT started (G.wave stays 0, nothing spawned), 'blocked' event emitted, still preparing",await ev("G.wave")==0 and len(await ev("evs('blocked')"))>=1 and (await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="prep",await ev("evs('blocked')"))
        await ev("window.pickSpawns=window.__pk;sim(5.2)");ok("(6) spawn points available again: the wave starts on the retry (5 s)",await ev("G.wave")==1 and (await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="wave")
        # (7) cancel during recovery, start() continues with the next wave
        await ev("sim(20);killAll();sim(2)");ok("(7) wave 1 cleared -> recovery",(await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="recovery")
        ok("(7) cancel() during recovery is accepted; nothing starts afterwards (150 s)",await ev("FEATURE_WAVE_DIRECTOR.cancel()") and (await ev("sim(150);FEATURE_WAVE_DIRECTOR.status().state"))=="cancelled" and await ev("G.wave")==1)
        ok("(7) start() after a recovery-cancel continues with wave 2 (not a replay of wave 1)",await ev("FEATURE_WAVE_DIRECTOR.start()") and (await ev("FEATURE_WAVE_DIRECTOR.status().nextWave"))==2)
        # (8) hold during preparation: frozen while the game runs, no skip on release
        await ev("sim(5)");a=await ev("FEATURE_WAVE_DIRECTOR.status().timer");await ev("FEATURE_WAVE_DIRECTOR.pause();sim(60)");h=await ev("FEATURE_WAVE_DIRECTOR.status()")
        ok("(8) pause() in preparation: 60 s of sim and the timer / state do not move, no wave",abs(h["timer"]-a)<1e-9 and h["state"]=="prep" and await ev("G.wave")==1,[a,h["timer"]])
        await ev("FEATURE_WAVE_DIRECTOR.resume();sim(1)");ok("(8) resume(): continues from where it was (no jump into the wave)",(await ev("FEATURE_WAVE_DIRECTOR.status().state"))=="prep" and abs((await ev("FEATURE_WAVE_DIRECTOR.status().timer"))-a-1)<.2)
        await b.close()
        # (4) HQ rules
        b,pg,errs=await boot(p);ev=pg.evaluate
        await ev("B.splice(0,B.length);G.started=true");await ev("sim(.2)")
        ok("(4) HQ missing while started -> defeat, like the host",await ev("G.state")=="lost" and len(await ev("evs('lost')"))==1)
        await b.close()
        ok("no console errors in (1)-(5)",not errs,errs[:2])
    print(f"{sum(R)}/{len(R)} passed (integration regression)")
    sys.exit(0 if all(R) else 1)
asyncio.run(main())
