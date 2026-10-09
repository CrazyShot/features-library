import os
GAME_DIR=os.environ.get("GAME_DIR",".")   # folder that contains the game build named index.html
import asyncio,json,math
from playwright.async_api import async_playwright
F="FEATURE_VAMPIRE_ASSET_TEST"
R=[]
def ok(n,c,x=""):
    R.append(bool(c));print(("PASS " if c else "FAIL ")+n+((" — "+str(x)) if x!="" else ""))
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=["--use-gl=swiftshader","--enable-unsafe-swiftshader"])
        pg=await b.new_page(viewport={"width":1400,"height":850});ev=pg.evaluate
        errs=[];pg.on("console",lambda m:errs.append(m.text) if m.type in("error","warning") else None);pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto("file://"+GAME_DIR+"/index.html");await pg.wait_for_timeout(4500)
        cnt=lambda:ev("E.filter(e=>e.vtest).length")
        # ---- 1. every panel scenario button ----
        wE0=await ev("G.wE");await ev("G.speed=0")
        res={}
        for k,exp in(("stand",1),("views",2),("move",1),("chase",1),("attack",1),("group",None)):
            n0=await cnt();await pg.click(f'[data-a={k}]');await pg.wait_for_timeout(150);n1=await cnt();res[k]=n1-n0
        print("   spawned per button:",res)
        ok("panel buttons spawn real enemy objects (stand 1, front+back 2, move 1, chase 1, attack 1, group ≥5)",res["stand"]==1 and res["views"]==2 and res["move"]==1 and res["chase"]==1 and res["attack"]==1 and res["group"]>=5)
        forced=await ev("E.filter(e=>e.vForce).map(e=>e.vForce).sort()")
        ok("'Front+Back' button forces one front and one back view",forced.count('front')>=1 and forced.count('back')==1,forced)
        ok("test vampires are ordinary enemy objects (en:1, hp/dmg from spawnE, in E[])",await ev("E.filter(e=>e.vtest).every(e=>e.en===1&&e.path&&e.bad instanceof Map&&typeof e.dmg==='number')"))
        await pg.screenshot(path="panel_all.png")
        await pg.click('[data-a=clear]');await pg.wait_for_timeout(150)
        ok("'Clear test vampires' removes them and restores the wave counter",await cnt()==0 and await ev("G.wE")==wE0,(await ev("G.wE"),wE0))
        # ---- 2. a real wave arrives in vampire form ----
        await ev("for(const e of E.slice())killQuiet(e);FOGCFG.on=false;G.t=DAYLEN;G.speed=3")
        await pg.wait_for_timeout(2500)
        got=False
        for i in range(120):
            await pg.wait_for_timeout(250)
            n=await ev("E.filter(e=>!e.wl&&!e.vtest).length")
            if n>=3:
                got=True;break
        await ev(f"{F}.stats.vamp=0;{F}.stats.fallback=0")
        pos=await ev("(()=>{const w=E.filter(e=>!e.wl),e=w[0];cam.z=cam.tz=.62;cam.x=cam.tx=X(e.x,e.y);cam.y=cam.ty=Y(e.x,e.y,1)-10;return[w.length,G.wave,G.phase]})()")
        await pg.wait_for_timeout(700)
        st=await ev(f"[{F}.stats.vamp,{F}.stats.fallback]")
        ok("wave enemies (spawned by the game's own waveTick/spawnE) are drawn with the vampire art",got and st[0]>0 and st[1]==0,f"wave {pos[1]} {pos[2]}: {pos[0]} enemies, drawn as vampire={st[0]}, fallback={st[1]}")
        await pg.screenshot(path="wave_vampires.png");await ev("G.speed=0")
        # ---- 3. performance ----
        await ev(f"""(()=>{{for(const e of E.slice())killQuiet(e);FOGCFG.on=true;const hq=B.find(b=>b.type==='hq');cam.z=cam.tz=.62;cam.x=cam.tx=X(hq.x+hq.w/2,hq.y+hq.w/2+6);cam.y=cam.ty=Y(hq.x+hq.w/2,hq.y+hq.w/2+6,1);
          for(let i=0;i<40;i++){{const q=nearestWalk((hq.x+hq.w/2-9+(i%8)*2.4)|0,(hq.y+hq.w+3+(i/8|0)*2)|0);{F}.spawn(q[0]+.5,q[1]+.5,{{hold:1}})}}}})()""")
        async def fps(mode):
            await ev(f"{F}.cfg.mode='{mode}'");await pg.wait_for_timeout(500)
            return await ev("new Promise(r=>{let n=0;const t0=performance.now();(function f(){n++;if(performance.now()-t0<3000)requestAnimationFrame(f);else r(n/((performance.now()-t0)/1000))})()})")
        vis=await ev("E.filter(e=>e.vtest&&fogVis(e.x,e.y)).length")
        a=await fps('all');o=await fps('off');a2=await fps('all')
        print(f"   {vis} vampires visible · fps all={a:.1f} / off={o:.1f} / all again={a2:.1f}  (software-rendered headless; relative only)")
        ok("vampire art costs no more than ~25% frame rate vs the original vector art with dozens on screen",min(a,a2)>=o*.75,f"{min(a,a2):.1f} vs {o:.1f} fps")
        await ev(f"{F}.cfg.mode='all'")
        # ---- 4. regression: control groups still fine, wrappers restore cleanly ----
        await ev("for(const e of E.slice())killQuiet(e);G.speed=0")
        await ev("SU=U.slice(0,3)");await pg.keyboard.press("Control+Digit1");await ev("SU=[]");await pg.keyboard.press("Alt+Digit1")
        ok("CTRLGROUPS feature still works next to this feature",await ev("SU.length")==3)
        ok("no console errors/warnings in the whole panel/wave/perf suite",not errs,errs[:3])
        await b.close()
    print(f"\n{sum(R)}/{len(R)} passed")
asyncio.run(main())
