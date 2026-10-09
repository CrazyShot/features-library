import os
GAME_DIR=os.environ.get("GAME_DIR",".")   # folder that contains the TEST build named index.html (game + Wave Director; see build_test_game.py)
import asyncio,json,sys
from playwright.async_api import async_playwright
R=[]
def ok(n,c,x=""):
    R.append(bool(c));print(("PASS " if c else "FAIL ")+n+((" — "+str(x)) if x!="" else ""))
HELPERS="""
window.sim=(sec,dt=.05)=>{const n=Math.round(sec/dt);for(let i=0;i<n;i++)stepSim(dt)};
window.killAll=()=>{for(const e of Array.from(E))if(!e.wl)hurt(e,1e9)};
window.waveEnemies=()=>E.filter(e=>!e.wl&&!e.dead);
window.simUntil=(expr,max=400,dt=.05)=>{const f=new Function('return ('+expr+')');let t=0;while(!f()&&t<max){stepSim(dt);t+=dt}return +t.toFixed(2)};
window.__ev=[];FEATURE_WAVE_DIRECTOR.on('*',d=>{const c={};for(const k in d)if(k!=='enemy'&&k!=='points')c[k]=d[k];if(d.type==='spawn'){c.hp=d.enemy.mh;c.dmg=d.enemy.dmg;c.sm=d.enemy.sm||1}c.T=+G.T.toFixed(2);window.__ev.push(c)});
window.evs=t=>window.__ev.filter(e=>e.type===t);
"""
async def boot(p,w=1400,h=850,deterministic=True):
    b=await p.chromium.launch(args=["--use-gl=swiftshader","--enable-unsafe-swiftshader"])
    pg=await b.new_page(viewport={"width":w,"height":h});errs=[]
    pg.on("pageerror",lambda e:errs.append("[PAGEERROR] "+str(e)));pg.on("console",lambda m:errs.append(f"[{m.type}] {m.text}") if m.type in("error","warning") else None)
    await pg.goto("file://"+GAME_DIR+"/index.html")
    for i in range(500):
        await pg.wait_for_timeout(500)
        if await pg.evaluate("typeof ready!=='undefined'&&ready===1"):break
    await pg.evaluate("G.speed=0")                         # tests drive stepSim by hand; real-time speed is tested separately
    await pg.evaluate("for(const e of E.slice())killQuiet(e)")   # clear the passive wilderness: it is not part of the wave system
    await pg.evaluate(HELPERS)
    if deterministic:   # take the host's defenders out of the picture so enemy counts are exact; the real-combat test (part D) leaves them on
        await pg.evaluate("U.length=0;for(const b of B){b.hp=b.mh=1e7;if(b.type==='tower')b.cd=1e12}")
    return b,pg,errs
