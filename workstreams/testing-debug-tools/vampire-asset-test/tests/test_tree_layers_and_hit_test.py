import os
GAME_DIR=os.environ.get("GAME_DIR",".")   # folder that contains the game build named index.html
import asyncio
from playwright.async_api import async_playwright
FIND=open('vt_find.js').read();F="FEATURE_VAMPIRE_ASSET_TEST"
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=["--use-gl=swiftshader","--enable-unsafe-swiftshader"])
        pg=await b.new_page(viewport={"width":1400,"height":850});ev=pg.evaluate
        await pg.goto("file://"+GAME_DIR+"/index.html");await pg.wait_for_timeout(4500)
        C=await ev(FIND);T=lambda k:C[k]["best"][0][:2]
        await ev("G.speed=0")
        goto=lambda x,y,z=.62:ev(f"(()=>{{cam.z=cam.tz={z};cam.x=cam.tx=X({x}+.5,{y}+.5);cam.y=cam.ty=Y({x}+.5,{y}+.5,1)-12}})()")
        # exact per-frame tree-layer count: wrap drawItems (called once per frame)
        await ev("window.__lay=[];window.__n=0;const pl=window.pasteLayer;window.pasteLayer=function(L){if(L)window.__n++;return pl(L)};const di=window.drawItems;window.drawItems=function(){window.__n=0;di();window.__lay.push(window.__n)};0")
        async def perframe(kind,x,y):
            await ev(f"""(()=>{{{F}.scenarios.clear();if(window.__d){{U.splice(U.indexOf(window.__d),1);window.__d=null}}
              if('{kind}'==='dwarf')window.__d=spawnDwarf({x}+.5,{y}+.5);else{{{F}.cfg.mode='{'all' if kind=='vamp' else 'off'}';{F}.spawn({x}+.5,{y}+.5,{{hold:1,force:'front'}})}}}})()""")
            await goto(x,y);await pg.wait_for_timeout(300);await ev("window.__lay=[]");await pg.wait_for_timeout(300)
            return sorted(set(await ev("window.__lay")))
        print("tree layers per frame (vampire | original | dwarf):")
        allok=True
        for k in("behind","front","edge","dense"):
            x,y=T(k);r=[await perframe(kind,x,y) for kind in("vamp","orig","dwarf")]
            same=r[0]==r[1];allok&=same;print(f"  {k:7s} {r}  vampire==original: {same}")
        print("ALL EQUAL" if allok else "MISMATCH")
        # hit-test at close zoom
        x,y=T("open");await ev(f"{F}.scenarios.clear();{F}.cfg.mode='all'")
        await ev(f"(()=>{{for(const u of U){{u.x={x}-3;u.y={y}+.5}};window.__v={F}.spawn({x}+.5,{y}+.5,{{hold:1,force:'front'}})}})()")
        for z in(.62,1.0,1.5,2.2):
            await goto(x,y,z);await pg.wait_for_timeout(350)
            sx,sy=await ev(f"[(X({x}+.5,{y}+.5)-cam.x)*cam.z+W/2,(Y({x}+.5,{y}+.5,1)-cam.y)*cam.z+H/2]")
            out={}
            for name,dy in(("feet",-2),("body",-14),("chest",-24),("head",-33)):
                await ev("SU=[U[0]];U[0].ord=null");await pg.mouse.click(sx,sy+dy*z,button="right");await pg.wait_for_timeout(100)
                out[name]=await ev("!!(U[0].ord&&U[0].ord.t&&U[0].ord.t.vamp)")
            print(f"  zoom {z}: right-click attack order hit  {out}")
        await b.close()
asyncio.run(main())
