import os
GAME_DIR=os.environ.get("GAME_DIR",".")   # folder that contains the game build named index.html
import asyncio,json,time
from playwright.async_api import async_playwright
STATE="""(()=>{const h=a=>{let x=2166136261;for(let i=0;i<a.length;i++){x^=(a[i]*1000|0);x=Math.imul(x,16777619)}return x>>>0};const hq=B.find(b=>b.type==='hq');
 return{N,blk:h(blk),TREEG:h(TREEG),RES:h(RES),RESI:h(RESI),DEP:h(DEP),NDEP,D:D.length,GLD:GLD.length,hq:[hq.x,hq.y],label:BASTION_IMPORT.label,seed:BASTION_IMPORT.seedText,fp:BASTION_IMPORT.fp}})()"""
async def boot(pg,url):
    await pg.goto(url)
    for i in range(400):
        await pg.wait_for_timeout(500)
        try:
            if await pg.evaluate("typeof ready!=='undefined'&&ready===1"):return
        except Exception:pass   # navigation in flight
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=["--use-gl=swiftshader","--enable-unsafe-swiftshader"])
        ctx=await b.new_context(viewport={"width":1400,"height":850});pg=await ctx.new_page()
        errs=[];pg.on("console",lambda m:errs.append(m.text) if m.type in("error","warning") else None);pg.on("pageerror",lambda e:errs.append(str(e)))
        t0=time.time();await boot(pg,"file://"+GAME_DIR+"/index.html")
        print("1) procedural boot: N =",await pg.evaluate("N"),"| import active:",await pg.evaluate("!!window.BASTION_IMPORT"),"|",(await pg.inner_text('#mdi-st')).split('\n')[0])
        # real user flow: pick the real 13 MB file with the panel's hidden file input -> stage -> reload
        t1=time.time()
        await pg.set_input_files('#mdi-file',os.environ.get("MAPDATA_JSON","bastion-map-256x256-bastion-001.json"))
        for i in range(600):
            await pg.wait_for_timeout(500)
            try:
                if await pg.evaluate("typeof ready!=='undefined'&&ready===1&&!!window.BASTION_IMPORT"):break
            except Exception:pass
        print(f"2) after 'Load MapData…' with the real JSON (parse+compact+stage+reload+build): {time.time()-t1:.1f}s")
        f=await pg.evaluate(STATE);print("   file-loaded :",json.dumps(f))
        v=await pg.evaluate("FEATURE_MAPDATA_IMPORT_TEST.verify().all");print("   in-game verify all checks:",v)
        # back to procedural via the panel
        await pg.click('[data-a=proc]')
        for i in range(400):
            await pg.wait_for_timeout(500)
            try:
                if await pg.evaluate("typeof ready!=='undefined'&&ready===1"):break
            except Exception:pass
        print("3) after 'Procedural' button: N =",await pg.evaluate("N"),"| import active:",await pg.evaluate("!!window.BASTION_IMPORT"))
        # bundled map for comparison in a fresh context
        ctx2=await b.new_context(viewport={"width":1400,"height":850});pg2=await ctx2.new_page()
        await boot(pg2,"file://"+GAME_DIR+"/index.html?map=embedded");e=await pg2.evaluate(STATE);print("   embedded    :",json.dumps(e))
        same={k:(f[k]==e[k]) for k in("N","blk","TREEG","RES","RESI","DEP","NDEP","D","GLD","hq")}
        print("4) file-loaded world == bundled world:",all(same.values()),same)
        print("errors:",errs or "none")
        await b.close()
asyncio.run(main())
