import os
GAME_DIR=os.environ.get("GAME_DIR",".")   # folder that contains the game build named index.html
import asyncio,json,math
from playwright.async_api import async_playwright
FIND=open('vt_find_all.js').read();F="FEATURE_VAMPIRE_ASSET_TEST"
R=[]
def ok(n,c,x=""):
    R.append(bool(c));print(("PASS " if c else "FAIL ")+n+((" — "+str(x)) if x!="" else ""))
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=["--use-gl=swiftshader","--enable-unsafe-swiftshader"])
        pg=await b.new_page(viewport={"width":1400,"height":850});ev=pg.evaluate
        errs=[];pg.on("console",lambda m:errs.append(m.text) if m.type in("error","warning") else None);pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto("file://"+GAME_DIR+"/index.html");await pg.wait_for_timeout(4500)
        C=await ev(FIND)
        def pick(k,lo,hi):
            c=[q for q in C[k]["best"] if lo<=q[2]<=hi];return c[len(c)//2] if c else None
        spots={"open terrain":pick("open",12,24),"forest edge":pick("edge",10,24),"behind a tree":pick("behind",10,24),"dense forest":pick("dense",10,24)}
        print("start tiles:",{k:(v[:2] if v else None) for k,v in spots.items()})
        await ev("G.speed=0;FOGCFG.on=false")
        pts=[v[:2] for v in spots.values() if v]
        rally=await ev("""(pts)=>{const c=comp[cellOf(U[0])];let best=null,bd=-1;for(let y=3;y<N-3;y+=2)for(let x=3;x<N-3;x+=2){const k=y*N+x;if(!walk[k]||comp[k]!==c||blk[k]||occ[k])continue;let m=1e9;for(const p of pts)m=Math.min(m,Math.hypot(x-p[0],y-p[1]));if(m>bd){bd=m;best=[x+.5,y+.5,m]}}return best}""",pts)
        print("dwarf rally point (far side):",rally)
        for name,sp in spots.items():
            if not sp: ok(f"movement: {name}",False,"no candidate tile");continue
            x,y=sp[0]+.5,sp[1]+.5
            await ev(f"(()=>{{U.length=0;for(let i=0;i<6;i++)spawnDwarf({rally[0]}+(i%3)*.8,{rally[1]}+(i/3|0)*.8)}})()")
            await ev(f"{F}.scenarios.clear();window.__e={F}.spawn({x},{y},{{lure:1}});__e.hp=__e.mh=900")
            await ev(f"cam.z=cam.tz=.62;cam.x=cam.tx=X({x},{y});cam.y=cam.ty=Y({x},{y},1)-12");await ev("G.speed=3")
            S=[];t0=await ev("G.T")
            for i in range(260):
                await pg.wait_for_timeout(100)
                await ev('(()=>{const e=window.__e;if(e&&!e.dead){cam.tx=e.x*0+X(e.x,e.y);cam.ty=Y(e.x,e.y,1)-12}})()')
                s=await ev("""(()=>{const e=window.__e;if(e.dead)return{dead:1};let bd=1e9;for(const u of U){const d=Math.hypot(u.x-e.x,u.y-e.y);if(d<bd)bd=d}
                  return{x:e.x,y:e.y,view:e.vView,path:e.path.length,walk:walk[(e.y|0)*N+(e.x|0)]?1:0,blk:blk[(e.y|0)*N+(e.x|0)]?1:0,mv:e.mv,tg:e.tg?(e.tg.type?'B:'+e.tg.type:'U'):null,d:bd,T:G.T,st:e.st}})()""")
                S.append(s)
                if s.get("dead"):break
                if s["d"]<=1.2:break
            await ev("G.speed=0")
            S=[s for s in S if not s.get("dead")]
            if not S: ok(f"movement: {name}",False,"vampire died");continue
            trav=sum(math.hypot(S[i]["x"]-S[i-1]["x"],S[i]["y"]-S[i-1]["y"]) for i in range(1,len(S)))
            straight=math.hypot(S[0]["x"]-S[-1]["x"],S[0]["y"]-S[-1]["y"])
            bad=sum(1 for s in S if not s["walk"] or s["blk"]);hadpath=any(s["path"]>0 for s in S);moved=trav>3
            # front/back consistency on real movement
            mism=0;n=0
            for i in range(1,len(S)):
                dx=S[i]["x"]-S[i-1]["x"];dy=S[i]["y"]-S[i-1]["y"];m=math.hypot((dx-dy)*32,(dx+dy)*24)
                if m<2:continue
                c=(dx+dy)*24/m
                if abs(c)>.32:
                    n+=1;exp='front' if c>0 else 'back'
                    if S[i]["view"]!=exp and S[min(i+1,len(S)-1)]["view"]!=exp:mism+=1
            views=sorted({s["view"] for s in S if s.get("view")})
            ok(f"movement ({name}): real pathfinding walks it toward a unit",hadpath and trav>8 and bad==0 and S[-1]["d"]<S[0]["d"]-8,
               f"dist {S[0]['d']:.1f}→{S[-1]['d']:.1f}, walked {trav:.1f} tiles (straight {straight:.1f}, detour x{trav/max(.1,straight):.2f}), never on blocked/unwalkable cell={bad==0}, target={S[-1]['tg']}, sim {S[-1]['T']-t0:.0f}s")
            ok(f"front/back follows heading ({name})",mism==0,f"{n} clear-heading samples, {mism} mismatches, views used={views}")
            await pg.screenshot(path=f"mv_{name.split()[0]}.png")
        await ev(f"{F}.scenarios.clear()")
        T=await ev("""(()=>{const V=FEATURE_VAMPIRE_ASSET_TEST.viewOf,out={};
          const run=(start,dx,dy)=>V({x:10,y:10,mv:1,path:[[10+dx,10+dy]],vView:start});
          out.down=run('back',1,1);out.up=run('front',-1,-1);out.right_keeps_front=run('front',1,-1);out.right_keeps_back=run('back',1,-1);out.left_keeps_front=run('front',-1,1);out.left_keeps_back=run('back',-1,1);
          out.down_right=run('back',1,0);out.up_right=run('front',0,-1);out.down_left=run('back',0,1);out.up_left=run('front',-1,0);
          const tgt=(x,y,start)=>V({x:10,y:10,mv:0,path:[],vView:start,tg:{x,y,hp:1}});out.target_below=tgt(12,12,'back');out.target_above=tgt(8,8,'front');
          out.forced=V({x:10,y:10,vForce:'back',vView:'front'});return out})()""")
        print("   viewOf unit test:",T)
        ok("front/back: screen-down->front, screen-up->back, diagonals by vertical component",T["down"]=="front" and T["up"]=="back" and T["down_right"]=="front" and T["down_left"]=="front" and T["up_right"]=="back" and T["up_left"]=="back")
        ok("front/back: pure sideways keeps the previous view (no flicker)",T["right_keeps_front"]=="front" and T["right_keeps_back"]=="back" and T["left_keeps_front"]=="front" and T["left_keeps_back"]=="back")
        ok("front/back: standing/attacking faces the target; forced view wins",T["target_below"]=="front" and T["target_above"]=="back" and T["forced"]=="back")
        ok("no console errors/warnings during movement tests",not errs,errs[:3])
        await b.close()
    print(f"\n{sum(R)}/{len(R)} passed")
asyncio.run(main())
