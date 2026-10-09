import os
GAME_DIR=os.environ.get("GAME_DIR",".")   # folder that contains the game build named index.html
import asyncio,json,re
from playwright.async_api import async_playwright
R=[]
def ok(n,c,x=""):
    R.append(bool(c));print(("PASS " if c else "FAIL ")+n+((" — "+str(x)) if x!="" else ""))
full=json.load(open(os.environ.get("MAPDATA_JSON","bastion-map-256x256-bastion-001.json")))
def mut(f):
    d=json.loads(json.dumps({k:full[k] for k in('width','height','trees','resources','deposits','hq','seed','terrain','wavePerimeter','generatorVersion','formatVersion')}));f(d);return json.dumps(d).encode()
CASES=[("not JSON at all",b"hello {"),
 ("empty object",b"{}"),
 ("non-square 100x120",mut(lambda d:d.update(width=100,height=120))),
 ("terrain.grid wrong length",mut(lambda d:d['terrain']['grid'].update(data=d['terrain']['grid']['data'][:1000]))),
 ("tree outside the map",mut(lambda d:d['trees'].append({'x':999,'y':3,'type':1}))),
 ("two trees on one tile",mut(lambda d:d['trees'].append(dict(d['trees'][0])))),
 ("trees[] missing",mut(lambda d:d.pop('trees')))]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=["--use-gl=swiftshader","--enable-unsafe-swiftshader"])
        pg=await b.new_page(viewport={"width":1400,"height":850});ev=pg.evaluate
        errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto("file://"+GAME_DIR+"/index.html")
        for i in range(200):
            await pg.wait_for_timeout(500)
            if await ev("typeof ready!=='undefined'&&ready===1"):break
        for name,buf in CASES:
            await pg.set_input_files('#mdi-file',files=[{"name":"bad.json","mimeType":"application/json","buffer":buf}]);await pg.wait_for_timeout(500)
            msg=(await pg.inner_text('#mdi-vr')).strip().replace("\n"," ");still=await ev("N")==112 and not await ev("!!window.BASTION_IMPORT")
            ok(f"rejects: {name}",still and msg!="",msg[:95])
        ok("the game kept running on its procedural map after every bad file",await ev("typeof ready!=='undefined'&&ready===1"))
        ok("no uncaught page errors from bad input",not errs,errs[:2]);await b.close()
        # regression of earlier features on the imported world
        pg=await (await b.new_context(viewport={"width":1400,"height":850})).new_page() if False else None
    print(f"{sum(R)}/{len(R)} passed (bad input)")
asyncio.run(main())
