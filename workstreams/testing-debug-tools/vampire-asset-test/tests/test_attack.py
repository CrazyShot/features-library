import os
GAME_DIR=os.environ.get("GAME_DIR",".")   # folder that contains the game build named index.html
import asyncio,json,math
from playwright.async_api import async_playwright
from PIL import Image
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
        C=await ev(FIND);op=[q for q in C["open"]["best"] if 14<=q[2]<=22];op=op[len(op)//2]
        # victim dwarf alone in the open (fog stays ON); the other dwarves wait at the HQ
        await ev(f"""(()=>{{for(const e of E.slice())killQuiet(e);U.length=0;window.__vic=spawnDwarf({op[0]}+.5,{op[1]}+.5);__vic.hp=13;
          const c=comp[cellOf(__vic)];let best=null,bd=-1;for(let y=3;y<N-3;y+=2)for(let x=3;x<N-3;x+=2){{const k=y*N+x;if(!walk[k]||comp[k]!==c||blk[k]||occ[k])continue;const m=Math.hypot(x-__vic.x,y-__vic.y);if(m>bd){{bd=m;best=[x+.5,y+.5]}}}}
          for(let i=0;i<5;i++)spawnDwarf(best[0]+(i%3)*.8,best[1]+(i/3|0)*.8);
          {F}.scenarios.chase();window.__e=E.find(e=>e.vtest);__e.hp=__e.mh=900;cam.z=cam.tz=1.0;cam.x=cam.tx=X(__vic.x,__vic.y);cam.y=cam.ty=Y(__vic.x,__vic.y,1)-14;G.speed=2}})()""")
        info=await ev("({vampire:{x:__e.x.toFixed(1),y:__e.y.toFixed(1),dmg:__e.dmg,hp:__e.hp},victim:{x:__vic.x.toFixed(1),y:__vic.y.toFixed(1),hp:__vic.hp},d:Math.hypot(__e.x-__vic.x,__e.y-__vic.y).toFixed(1)})")
        print("setup:",info)
        ev_={"detect":None,"reach":None,"hits":[],"death":None,"retarget":None};last=dict(hp=13,atk=None);shots=0;atks=[]
        for i in range(400):
            await pg.wait_for_timeout(60)
            s=await ev("""(()=>{const e=__e,v=__vic;const tg=e.tg;return{T:G.T,tg:tg===v?'victim':tg?(tg.type?'B:'+tg.type:'U'):null,tgdead:tg?!!tg.dead:null,d:Math.hypot(e.x-v.x,e.y-v.y),vhp:v.hp,vdead:!!v.dead||U.indexOf(v)<0,atk:e.atk,cd:e.cd,view:e.vView,nU:U.length,
              tdir:tg?(()=>{const p=tpos(tg);return[(p[0]-e.x),(p[1]-e.y)]})():null,path:e.path.length,ehp:e.hp,dead:!!e.dead}})()""")
            if s["dead"]:break
            if s["atk"] is not None and s["atk"]>0 and (not atks or abs(atks[-1]-s["atk"])>1e-6):atks.append(s["atk"])
            if ev_["detect"] is None and s["tg"]=="victim":ev_["detect"]=s["T"]
            if ev_["reach"] is None and s["d"]<=.95+.02:ev_["reach"]=s["T"]
            if s["vhp"]<last["hp"] and not s["vdead"]:ev_["hits"].append((s["T"],last["hp"]-s["vhp"]))
            last["hp"]=s["vhp"] if not s["vdead"] else last["hp"]
            if ev_["reach"] and shots<1 and s["atk"] is not None and s["T"]-s["atk"]<.15 and not s["vdead"]:
                await pg.screenshot(path="attack_frame.png");shots+=1;ev_["frame"]=dict(view=s["view"],tdir=s["tdir"])
            if s["vdead"] and ev_["death"] is None:ev_["death"]=s["T"];ev_["tg_at_death"]=s["tg"]
            if ev_["death"] is not None and s["tg"] not in("victim",None) and not s["tgdead"] and ev_["retarget"] is None:ev_["retarget"]=(s["T"],s["tg"])
            if ev_["retarget"] and s["T"]>ev_["retarget"][0]+3:break
        await ev("G.speed=0")
        print("timeline (sim seconds):",{k:(round(v,2) if isinstance(v,float) else v) for k,v in ev_.items() if k!="hits"},"hits:",[(round(t,2),d) for t,d in ev_["hits"]])
        ok("detection: the existing AI picks the dwarf as its target",ev_["detect"] is not None)
        ok("chase: closes distance to attack reach (REACH .95)",ev_["reach"] is not None,f"after {ev_['reach']-ev_['detect']:.1f}s" if ev_["reach"] else "")
        dm=await ev("__e.dmg")
        ok("attack triggers and deals the enemy's normal damage per hit",len(ev_["hits"])>=2 and all(d==dm for _,d in ev_["hits"]),f"hits={len(ev_['hits'])}, dmg/hit={[d for _,d in ev_['hits']]} (e.dmg={dm})")
        gaps=[atks[i]-atks[i-1] for i in range(1,len(atks))]
        ok("attack cadence matches the existing cooldown (1.05s), from the game's own e.atk stamps",len(atks)>=3 and all(abs(g-1.05)<.08 for g in gaps),f"attacks at {[round(a,2) for a in atks]} gaps={[round(g,3) for g in gaps]}")
        ok("target death: victim dwarf is removed by the existing combat",ev_["death"] is not None)
        ok("retargeting: afterwards it picks a new live target and keeps going",ev_["retarget"] is not None,ev_["retarget"])
        if ev_.get("frame"):
            f=ev_["frame"];dx,dy=f["tdir"];c=(dx+dy)*24/max(1e-6,math.hypot((dx-dy)*32,(dx+dy)*24))
            exp='front' if c>.22 else 'back' if c<-.22 else None
            ok("view while attacking faces the target (static sprite, no animation)",exp is None or f["view"]==exp,f"view={f['view']} target-heading c={c:.2f}")
        ok("no console errors/warnings during combat test",not errs,errs[:3])
        await b.close()
    print(f"\n{sum(R)}/{len(R)} passed")
asyncio.run(main())
