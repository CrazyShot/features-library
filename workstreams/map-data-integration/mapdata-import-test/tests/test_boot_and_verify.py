import os
GAME_DIR=os.environ.get("GAME_DIR",".")   # folder that contains the game build named index.html
import asyncio,json,time,sys
from playwright.async_api import async_playwright
URL=sys.argv[1] if len(sys.argv)>1 else "index.html?map=embedded"
TAG=sys.argv[2] if len(sys.argv)>2 else "m1"
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=["--use-gl=swiftshader","--enable-unsafe-swiftshader"])
        pg=await b.new_page(viewport={"width":1400,"height":850})
        errs=[];pg.on("console",lambda m:errs.append(f"[{m.type}] {m.text}") if m.type in("error","warning") else None);pg.on("pageerror",lambda e:errs.append("[PAGEERROR] "+str(e)))
        t0=time.time();await pg.goto("file://"+GAME_DIR+"/"+URL)
        for i in range(400):
            await pg.wait_for_timeout(500)
            if await pg.evaluate("typeof ready!=='undefined'&&ready===1"):break
        print(f"ready after {time.time()-t0:.1f}s; errors: {errs[:5] or 'none'}")
        print("N,TW,TH:",await pg.evaluate("[N,TW,TH,WW,WH]"),"pages",await pg.evaluate("pages.length"),"import:",await pg.evaluate("!!window.BASTION_IMPORT&&[BASTION_IMPORT.w,BASTION_IMPORT.seedText,BASTION_IMPORT.fp]"))
        await pg.wait_for_timeout(1500)
        v=await pg.evaluate("FEATURE_MAPDATA_IMPORT_TEST.verify()")
        print(json.dumps(v,indent=1)[:1500])
        print(await pg.inner_text('#mdi-vr'))
        await pg.screenshot(path=f"{TAG}_start.png")
        await b.close()
asyncio.run(main())
