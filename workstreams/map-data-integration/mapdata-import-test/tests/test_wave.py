import os
GAME_DIR=os.environ.get("GAME_DIR",".")   # folder that contains the game build named index.html
import asyncio,json,sys
from playwright.async_api import async_playwright
URL=sys.argv[1] if len(sys.argv)>1 else "index.html?map=embedded";R=[]
def ok(n,c,x=""):
    R.append(bool(c));print(("PASS " if c else "FAIL ")+n+((" — "+str(x)) if x!="" else ""))
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=["--use-gl=swiftshader","--enable-unsafe-swiftshader"])
        pg=await b.new_page(viewport={"width":1400,"height":850});ev=pg.evaluate;errs=[]
        pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("console",lambda m:errs.append(m.text) if m.type in("error","warning") else None)
        await pg.goto("file://"+GAME_DIR+"/"+URL)
        for i in range(500):
            await pg.wait_for_timeout(500)
            if await ev("typeof ready!=='undefined'&&ready===1"):break
        N=await ev("N");imp=await ev("!!window.BASTION_IMPORT")
        pts=await ev("(()=>{const p=pickSpawns(),per=imp=>0;return p})()")
        info=await ev("""(()=>{const p=pickSpawns(),per=window.BASTION_IMPORT?BASTION_IMPORT.perim:null;return{n:p.length,walk:p.filter(q=>walk[(q[1]|0)*N+(q[0]|0)]).length,sameComp:p.filter(q=>comp[(q[1]|0)*N+(q[0]|0)]===comp[cellOf(U[0])]).length,inBand:per?p.filter(q=>per[(q[1]|0)*N+(q[0]|0)]).length:null,pts:p.map(q=>[+q[0].toFixed(0),+q[1].toFixed(0)])}})()""")
        print(f"   N={N} import={imp} spawn points: {json.dumps(info)}")
        ok("wave spawn points are walkable and connected to the base",info["n"]>0 and info["walk"]==info["n"] and info["sameComp"]==info["n"])
        await ev("G.t=DAYLEN;G.speed=3")
        for i in range(80):
            await pg.wait_for_timeout(250)
            if await ev("E.filter(e=>!e.wl).length")>=info["n"]:break
        n=await ev("E.filter(e=>!e.wl).length");ok("a real wave spawns (game's own waveTick/spawnE)",n>=3,f"{n} enemies, wave {await ev('G.wave')}")
        d0=await ev("E.filter(e=>!e.wl).map(q=>Math.hypot(q.x-128,q.y-128))");await pg.wait_for_timeout(7000)
        d1=await ev("E.filter(e=>!e.wl).map(q=>Math.hypot(q.x-128,q.y-128))")
        ok("wave enemies path toward the base across the terrain",len(d0)>0 and len(d1)>0 and sum(d1)/len(d1)<sum(d0)/len(d0)-2,f"mean distance {sum(d0)/max(1,len(d0)):.0f} -> {sum(d1)/max(1,len(d1)):.0f} tiles")
        ok("no console errors/warnings",not errs,errs[:3]);await b.close()
    print(f"{sum(R)}/{len(R)} passed (wave)")
asyncio.run(main())
