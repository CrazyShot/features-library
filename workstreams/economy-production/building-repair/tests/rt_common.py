import os
GAME_DIR=os.environ.get("GAME_DIR",".")   # folder that contains the game build named index.html
import asyncio,json,sys
from playwright.async_api import async_playwright
R=[]
def ok(n,c,x=""):
    R.append(bool(c));print(("PASS " if c else "FAIL ")+n+((" — "+str(x)) if x!="" else ""))
async def boot(p,url="index.html",w=1400,h=850):
    b=await p.chromium.launch(args=["--use-gl=swiftshader","--enable-unsafe-swiftshader"])
    pg=await b.new_page(viewport={"width":w,"height":h});errs=[]
    pg.on("pageerror",lambda e:errs.append("[PAGEERROR] "+str(e)));pg.on("console",lambda m:errs.append(f"[{m.type}] {m.text}") if m.type in("error","warning") else None)
    await pg.goto("file://"+GAME_DIR+"/"+url)
    for i in range(500):
        await pg.wait_for_timeout(500)
        if await pg.evaluate("typeof ready!=='undefined'&&ready===1"):break
    await pg.evaluate("G.speed=0;FOGCFG.on=true;document.getElementById('mdi-panel')&&document.getElementById('mdi-panel').classList.add('min');document.getElementById('vt-panel')&&document.getElementById('vt-panel').classList.add('min')")
    return b,pg,errs
SCR="(x,y)=>[(X(x,y)-cam.x)*cam.z+W/2,(Y(x,y,1)-cam.y)*cam.z+H/2]"
