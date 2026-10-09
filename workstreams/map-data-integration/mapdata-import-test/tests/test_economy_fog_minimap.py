import os
GAME_DIR=os.environ.get("GAME_DIR",".")   # folder that contains the game build named index.html
import asyncio,json,math,sys,time
from playwright.async_api import async_playwright
from PIL import Image
URL=sys.argv[1] if len(sys.argv)>1 else "index.html?map=embedded";TAG=sys.argv[2] if len(sys.argv)>2 else "g256"
R=[]
def ok(n,c,x=""):
    R.append(bool(c));print(("PASS " if c else "FAIL ")+n+((" — "+str(x)) if x!="" else ""))
FINDMINE="""(()=>{const byDep=new Map(),hq=B.find(b=>b.type==='hq'),hx=hq.x+2,hy=hq.y+2;
 for(const q of BASTION_IMPORT.raw.nodes){if(q.t!==1&&q.t!==2)continue;for(let dy=-4;dy<=2;dy++)for(let dx=-4;dx<=2;dx++){const tx=q.x+dx,ty=q.y+dy;const c=check('mine',tx,ty);if(!c.ok&&!c.afford)continue;if(!c.ok)continue;const m=mineYield(tx+1.5,ty+1.5),s=m[0]+m[1];const cur=byDep.get(q.dep);if(!cur||s>cur.s)byDep.set(q.dep,{s,tx,ty,t:q.t,d:Math.hypot(tx-hx,ty-hy)})}}
 const rows=[...byDep.entries()].map(([id,v])=>({id,...v})).filter(r=>r.s>=MMIN).sort((a,b)=>a.d-b.d);return{stone:rows.find(r=>r.t===1),iron:rows.find(r=>r.t===2)}})()"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=["--use-gl=swiftshader","--enable-unsafe-swiftshader"])
        pg=await b.new_page(viewport={"width":1400,"height":850});ev=pg.evaluate
        errs=[];pg.on("console",lambda m:errs.append(m.text) if m.type in("error","warning") else None);pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto("file://"+GAME_DIR+"/"+URL)
        for i in range(500):
            await pg.wait_for_timeout(500)
            if await pg.evaluate("typeof ready!=='undefined'&&ready===1"):break
        N=await ev("N");print(f"[{TAG}] N={N}")
        look=lambda x,y,z=.62:ev(f"(()=>{{cam.z=cam.tz={z};cam.x=cam.tx=X({x},{y});cam.y=cam.ty=Y({x},{y},1)-10}})()")
        # ---------- economy: Mine on stone + iron deposits, Lumber Camp ----------
        await ev('for(const e of E.slice())killQuiet(e)');await ev('G.t=0')
        sites=await ev(FINDMINE);print("   nearest mineable deposits:",json.dumps(sites))
        ok("mineable stone and iron deposits exist on the imported map",bool(sites["stone"]) and bool(sites["iron"]))
        st0=await ev("({...G.res})")
        ids={}
        for k in("stone","iron"):
            s=sites[k];r=await ev(f"(()=>{{const b=place('mine',{s['tx']},{s['ty']});return b?{{id:b.id,ms:b.ms,mi:b.mi,dep:b.dep,out:econOut(b)}}:null}})()")
            ids[k]=r;ok(f"Mine placed on a MapData {k} deposit (existing check/place rules)",r is not None and ((r["ms"]>0) if k=='stone' else (r["mi"]>0)),r)
        # which MapData deposit does the mine's game deposit correspond to?
        for k in("stone","iron"):
            s=sites[k];md=await ev(f"BASTION_IMPORT.depId[{s['ty']+1}*N+{s['tx']+1}]")
        # lumber camp at the forest edge nearest the HQ
        lum=await ev("""(()=>{const hq=B.find(b=>b.type==='hq');let best=null;for(let ty=hq.y-14;ty<hq.y+18;ty++)for(let tx=hq.x-14;tx<hq.x+18;tx++){const c=check('lumber',tx,ty);if(!c.ok)continue;const n=treesIn(tx+1.5,ty+1.5);if(n>=60&&(!best||Math.hypot(tx-hq.x,ty-hq.y)<best.d))best={tx,ty,n,d:Math.hypot(tx-hq.x,ty-hq.y)}}return best})()""")
        lr=await ev(f"(()=>{{const b=place('lumber',{lum['tx']},{lum['ty']});return b?{{id:b.id,trees:b.trees,out:econOut(b)}}:null}})()")
        ok("Lumber Camp counts the imported trees (1 per tree tile)",lr and lr["trees"]==lum["n"] and lr["out"]["wood"]>0,f"{lr['trees']} trees in radius -> {lr['out']['wood']} wood / 8h")
        # starter stone (generator's guaranteed deposit) -- can a Mine be built on it?
        ss=await ev("""(()=>{let ok=0,tot=0;for(let ty=94;ty<=106;ty++)for(let tx=118;tx<=134;tx++){const c=check('mine',tx,ty);tot++;if(c.ok||c.why.indexOf('Not enough')>=0)ok++}return[ok,tot]})()""")
        print(f"   starter stone deposit #114 (127,101): mine placements allowed = {ss[0]} of {ss[1]} candidate spots (game MMIN={await ev('MMIN')})")
        # complete construction and let one economic tick pass
        await ev("G.speed=3");pre=await ev("({...G.res})")
        t0=await ev("G.tick?G.tick.n:0");nt=None
        for i in range(300):
            await pg.wait_for_timeout(250);await ev('G.t=Math.min(G.t,15)')
            if await ev("B.filter(b=>b.type!=='hq'&&b.p>=1).length")>=3:
                if nt is None:nt=await ev("G.tick?G.tick.n:0")
                elif await ev("G.tick?G.tick.n:0")>=nt+2:break
        post=await ev("({...G.res})");gain=await ev("G.tick&&G.tick.gain")
        print("   resources before/after:",pre,post,"tick gain",gain)
        dres={k:post[k]-pre[k] for k in post};ok("economic ticks pay stone, iron and wood from the imported deposits/trees",dres["stone"]>0 and dres["iron"]>0 and dres["wood"]>0,dres)
        await ev("G.speed=0")
        # ---------- fog of war ----------
        far=await ev("""(()=>{const c=comp[cellOf(U[0])];for(let k=0;k<N*N;k++){const x=k%N+.5,y=(k/N|0)+.5;if(walk[k]&&comp[k]===c&&Math.hypot(x-128,y-128)>70&&!fogVis(x,y))return[x,y]}return null})()""")
        ok("fog hides distant imported terrain (unexplored)",far is not None and await ev(f"!fogVis({far[0]},{far[1]})") and await ev("fogVis(128.5,128.5)"),far)
        await look(far[0],far[1]);await pg.wait_for_timeout(400);await pg.screenshot(path=f"{TAG}_fog_hidden.png")
        await ev(f"(()=>{{const u=U[0];u.x={far[0]}+1;u.y={far[1]};u.path=[]}})()");await ev("G.speed=1");await pg.wait_for_timeout(1500);await ev("G.speed=0")
        ok("a unit standing there reveals it (Fog of War works on the imported map)",await ev(f"fogVis({far[0]},{far[1]})"))
        await look(far[0],far[1]);await pg.wait_for_timeout(500);await pg.screenshot(path=f"{TAG}_fog_revealed.png")
        # ---------- minimap ----------
        await look(128.5,128.5);await ev("G.speed=0");await pg.wait_for_timeout(600)
        box=await pg.locator('#mc').bounding_box();await pg.screenshot(path=f"{TAG}_minimap_fog.png",clip=box);await ev("FOGCFG.on=false");await pg.wait_for_timeout(700);await pg.screenshot(path=f"{TAG}_minimap.png",clip=box)
        im=Image.open(f"{TAG}_minimap.png").convert("RGB");px=im.load();nb=sum(1 for y in range(im.height) for x in range(im.width) if sum(px[x,y])>60)
        ok("minimap renders the whole imported map (fog off)",nb/(im.width*im.height)>.25,f"{nb/(im.width*im.height):.0%} lit pixels, canvas {im.size}")
        # click the minimap -> camera goes to that place on the 256 map
        c0=await ev("[cam.tx,cam.ty]");await pg.mouse.click(box["x"]+box["width"]*.3,box["y"]+box["height"]*.5);await pg.wait_for_timeout(500);c1=await ev("[cam.tx,cam.ty]")
        ok("clicking the minimap moves the camera",abs(c1[0]-c0[0])>500,[round(c0[0]),round(c1[0])])
        fps=await ev("document.getElementById('st').textContent");print("   HUD:",fps.split('·')[-1].strip())
        await ev("G.speed=0")
        ok("no console errors/warnings during gameplay part B",not errs,errs[:3])
        await b.close()
    print(f"\n{sum(R)}/{len(R)} passed (part B)")
asyncio.run(main())
