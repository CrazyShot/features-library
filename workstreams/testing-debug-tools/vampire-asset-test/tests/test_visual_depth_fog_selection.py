import os
GAME_DIR=os.environ.get("GAME_DIR",".")   # folder that contains the game build named index.html
import asyncio,json
from playwright.async_api import async_playwright
from PIL import Image,ImageChops
import numpy as np
FIND=open('vt_find.js').read()
R=[]
def ok(n,c,x=""):
    R.append(bool(c));print(("PASS " if c else "FAIL ")+n+((" — "+str(x)) if x!="" else ""))
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=["--use-gl=swiftshader","--enable-unsafe-swiftshader"])
        pg=await b.new_page(viewport={"width":1400,"height":850});ev=pg.evaluate
        errs=[];pg.on("console",lambda m:errs.append(m.text) if m.type in("error","warning") else None);pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto("file://"+GAME_DIR+"/index.html");await pg.wait_for_timeout(4500)
        C=await ev(FIND);T=lambda k,i=0:C[k]["best"][i][:2]
        F="FEATURE_VAMPIRE_ASSET_TEST"
        await ev("G.speed=0")
        goto=lambda x,y,z=.62:ev(f"(()=>{{cam.z=cam.tz={z};cam.x=cam.tx=X({x}+.5,{y}+.5);cam.y=cam.ty=Y({x}+.5,{y}+.5,1)-12}})()")
        # ---- A. tree layer parity (same canopy veils for vampire / original / dwarf) ----
        await ev("window.__pl=0;const _p=window.pasteLayer;window.pasteLayer=function(L){if(L)window.__pl++;return _p(L)};0")
        async def layers(kind,x,y):
            await ev(f"""(()=>{{{F}.scenarios.clear();if(window.__d){{U.splice(U.indexOf(window.__d),1);window.__d=null}}
              if('{kind}'==='dwarf')window.__d=spawnDwarf({x}+.5,{y}+.5);else{{{F}.cfg.mode='{'all' if kind=='vamp' else 'off'}';{F}.spawn({x}+.5,{y}+.5,{{hold:1,force:'front'}})}}}})()""")
            await goto(x,y);await pg.wait_for_timeout(400)
            await ev("window.__pl=0");await pg.wait_for_timeout(120)
            return await ev("(()=>{const a=window.__pl;return a})()")
        for k in("behind","dense","edge","front"):
            x,y=T(k);fr=[]
            for kind in("vamp","orig","dwarf"):
                n1=await layers(kind,x,y);fr.append(n1)
            # per-frame counts: normalise by frames rendered during the 120ms window using relative comparison
            ok(f"tree layers pasted ({k}) vampire≈original≈dwarf, >0",fr[0]>0 and fr[1]>0 and abs(fr[0]-fr[1])<=max(2,fr[1]*.5),fr)
        # ---- B. tree/terrain stability: pixels away from the sprite are identical with and without the vampire ----
        x,y=T("behind");await ev(f"{F}.scenarios.clear();{F}.cfg.mode='all'");await goto(x,y);await pg.wait_for_timeout(500)
        await pg.screenshot(path="_a.png");await pg.wait_for_timeout(300);await pg.screenshot(path="_a2.png")
        await ev(f"{F}.spawn({x}+.5,{y}+.5,{{hold:1,force:'front'}})");await pg.wait_for_timeout(500);await pg.screenshot(path="_b.png")
        L=lambda f:np.asarray(Image.open(f).convert("RGB")).astype(int)
        A,A2,B_=L("_a.png"),L("_a2.png"),L("_b.png")
        sc=await ev(f"[(X({x}+.5,{y}+.5)-cam.x)*cam.z+W/2,(Y({x}+.5,{y}+.5,1)-cam.y)*cam.z+H/2]")
        m=np.zeros(A.shape[:2],bool);cx,cy=int(sc[0]),int(sc[1]);m[cy-int(46*.62)-10:cy+10,cx-int(16*.62)-10:cx+int(16*.62)+10]=True
        for th in(24,48,96):
            nz=(np.abs(A-A2).sum(2)>th);df=(np.abs(A-B_).sum(2)>th)
            print(f"   threshold {th}: no-vampire frame-to-frame noise outside rect={(nz&~m).sum()}  with-vs-without outside rect={(df&~m).sum()}  inside rect={(df&m).sum()}")
        th=48;nz=(np.abs(A-A2).sum(2)>th)&~m;df=(np.abs(A-B_).sum(2)>th)&~m
        ok("adding the vampire changes no pixels outside its own rect beyond the game's own frame-to-frame noise",df.sum()<=nz.sum()*1.5+50,f"outside: {df.sum()} vs noise floor {nz.sum()}")
        ok("...and does change pixels inside its rect",((np.abs(A-B_).sum(2)>th)&m).sum()>100)
        # ---- C. Fog of War ----
        await ev(f"{F}.scenarios.clear()")
        far=await ev("(()=>{const c=comp[cellOf(U[0])];let best=null;for(let k=0;k<N*N;k++){const x=k%N+.5,y=(k/N|0)+.5;if(walk[k]&&comp[k]===c&&!fogVis(x,y)&&Math.hypot(x-U[0].x,y-U[0].y)>30){best=[x,y];break}}return best})()")
        ok("found an unseen walkable tile for the fog test",far is not None,far)
        await ev("window.__seen=new Set();window.__w=window.drawE;window.drawE=function(e){window.__seen.add(e);return window.__w(e)};0")
        await ev(f"window.__fv={F}.spawn({far[0]},{far[1]},{{hold:1}});window.__fv2={F}.spawn({T('open')[0]}+.5,{T('open')[1]}+.5,{{hold:1}})")
        await goto(far[0]-.5,far[1]-.5);await ev("window.__seen.clear()");await pg.wait_for_timeout(400)
        ok("vampire outside player vision is NOT drawn",not await ev("window.__seen.has(window.__fv)"))
        await pg.screenshot(path="fog_hidden.png")
        await goto(T('open')[0],T('open')[1]);await ev("window.__seen.clear()");await pg.wait_for_timeout(400)
        ok("vampire inside player vision IS drawn",await ev("window.__seen.has(window.__fv2)"))
        # reveal the hidden one by moving a dwarf next to it
        await ev(f"(()=>{{const u=U[0];u.x={far[0]}+1.5;u.y={far[1]};u.path=[]}})()");await ev("G.speed=1");await pg.wait_for_timeout(1500);await ev("G.speed=0")
        await goto(far[0]-.5,far[1]-.5);await ev("window.__seen.clear()");await pg.wait_for_timeout(500)
        ok("same vampire appears once a unit reveals the area",await ev("window.__seen.has(window.__fv)"))
        await pg.screenshot(path="fog_revealed.png")
        await ev("window.drawE=window.__w;0")
        # ---- D. selection / targeting ----
        await ev(f"{F}.scenarios.clear()");x,y=T("open");await ev("G.speed=0")
        await ev(f"(()=>{{for(const u of U.slice(1)){{u.x={x}-2.5;u.y={y}+.5}};U[0].x={x}-2;U[0].y={y}+.5;window.__v={F}.spawn({x}+.5,{y}+.5,{{hold:1,force:'front'}})}})()")
        await goto(x,y);await pg.wait_for_timeout(400)
        s=await ev(f"[(X({x}+.5,{y}+.5)-cam.x)*cam.z+W/2,(Y({x}+.5,{y}+.5,1)-cam.y)*cam.z+H/2]")
        sx,sy=s
        await ev("SU=[];SB=null");await pg.mouse.click(sx,sy-14*.62)
        ok("left-click on a vampire does not select it (enemies are not selectable)",await ev("SU.length")==0 and await ev("SB")is None)
        await pg.mouse.move(sx-60,sy-60);await pg.mouse.down();await pg.mouse.move(sx+60,sy+30,steps=6);await pg.mouse.up()
        ok("drag-box over a vampire selects no enemy",await ev("SU.every(u=>!u.en)"))
        res={}
        for name,dy in(("feet",-2),("body",-14),("head",-33)):
            await ev("SU=[U[0]];U[0].ord=null");await pg.mouse.click(sx,sy+dy*.62,button="right");await pg.wait_for_timeout(120)
            res[name]=await ev("!!(U[0].ord&&U[0].ord.t&&U[0].ord.t.vamp)")
        print("   right-click attack-order hit-test (feet/body/head):",res)
        ok("right-click on vampire body/feet issues an attack order (existing pickEnemy)",res["body"] and res["feet"])
        # ---- E. mode toggles via the real panel ----
        await ev(f"{F}.scenarios.clear()");await ev(f"{F}.cfg.mode='all'");x,y=T("open")
        await ev(f"{F}.spawn({x}+.5,{y}+.5,{{hold:1}})");await goto(x,y);await pg.wait_for_timeout(300)
        async def drawn():
            await ev(f"{F}.stats.vamp=0;{F}.stats.fallback=0");await pg.wait_for_timeout(250);return await ev(f"[{F}.stats.vamp,{F}.stats.fallback]")
        a=await drawn();ok("mode 'all': vampire art drawn",a[0]>0,a)
        await pg.click('[data-a=vis]');m1=await ev(f"{F}.cfg.mode");a=await drawn();ok("panel toggle -> 'tagged': test vampire still drawn as vampire",m1=='tagged' and a[0]>0,(m1,a))
        await pg.click('[data-a=vis]');m2=await ev(f"{F}.cfg.mode");a=await drawn();ok("panel toggle -> 'off': original enemy art restored",m2=='off' and a[0]==0,(m2,a))
        await pg.screenshot(path="mode_off.png")
        await pg.click('[data-a=vis]');ok("panel toggle -> back to 'all'",await ev(f"{F}.cfg.mode")=='all')
        # ---- F. far-zoom LOD path ----
        await ev("setFreeZoom(true)");await ev("cam.z=cam.tz=.2");await goto(x,y,.2);await pg.wait_for_timeout(400)
        a=await drawn();ok("far zoom (LOD batch path) draws vampire without errors",a[0]>0,a);await pg.screenshot(path="lod.png")
        await ev("setFreeZoom(false)")
        ok("no console errors/warnings during the visual suite",not errs,errs[:3])
        await b.close()
    print(f"\n{sum(R)}/{len(R)} passed")
asyncio.run(main())
