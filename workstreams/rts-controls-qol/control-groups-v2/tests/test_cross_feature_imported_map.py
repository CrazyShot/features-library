import os
GAME_DIR=os.environ.get("GAME_DIR",".")   # folder that contains the game build named index.html
import asyncio
from playwright.async_api import async_playwright
from rt_common import *
async def main():
    async with async_playwright() as p:
        b,pg,errs=await boot(p,url="index.html?map=embedded");ev=pg.evaluate
        ok("running on the imported 256×256 MapData world",await ev("N")==256 and await ev("!!BASTION_IMPORT"))
        v=await ev("FEATURE_MAPDATA_IMPORT_TEST.verify()");ok("MAPDATA-IMPORT-TEST self-verification still passes",v['all'],v['res']['hq'])
        await ev("for(const e of E.slice())killQuiet(e)")
        await ev("SU=U.slice(0,4);SB=null");await pg.keyboard.press("Control+Digit1");await ev("SU=[];SB=null");await pg.keyboard.press("Digit1")
        ok("control groups work on the imported map",await ev("SU.length")==4 and await ev("FEATURE_CTRLGROUPS_V2.get(1).length")==4)
        hq=await ev("B.find(b=>b.type==='hq')");await ev("hurt(B.find(b=>b.type==='hq'),200);SU=[];SB=B.find(b=>b.type==='hq')");await pg.wait_for_timeout(400)
        await pg.click('#repair-btn');await ev("G.speed=3");await pg.wait_for_timeout(2500);await ev("G.speed=0")
        ok("HQ repair works on the imported map (HP rising, resources paid)",await ev("B.find(b=>b.type==='hq').hp")>700 and await ev("FEATURE_BUILDING_REPAIR.repairing().length")==1,await ev("B.find(b=>b.type==='hq').hp"))
        # vampire feature + enemy inspect together
        await ev('FEATURE_VAMPIRE_ASSET_TEST.scenarios.chase()')
        await ev("FEATURE_VAMPIRE_ASSET_TEST.cfg.mode='all'");n=await ev("E.filter(e=>e.vtest).length")
        ok("VAMPIRE-ASSET-TEST panel still spawns real enemies",n>=1,n)
        await ev("(()=>{const e=E.find(e=>e.vtest);const hq=B.find(b=>b.type==='hq');e.x=hq.x+hq.w/2+5;e.y=hq.y+hq.w+3;e.sx=e.x;e.sy=e.y;e.vHold=1;cam.z=cam.tz=.7;cam.x=cam.tx=X(e.x,e.y);cam.y=cam.ty=Y(e.x,e.y,1)-10;window.__e=e})()");await pg.wait_for_timeout(600)
        p_=await ev(f"({SCR})(__e.x,__e.y)");await pg.mouse.click(p_[0],p_[1]-14*.7);await pg.wait_for_timeout(400)
        t=await ev("document.getElementById('pn').innerText.replace(/\\n+/g,' | ')");ok("clicking a vampire (vampire art) shows its info panel",'Vampire' in t and 'damage' in t,t[:70])
        await pg.screenshot(path="r_final_256.png")
        ok("no console errors/warnings",not errs,errs[:3]);await b.close()
    print(f"{sum(R)}/{len(R)} passed (imported-map + earlier-feature regression)")
asyncio.run(main())
