import os
GAME_DIR=os.environ.get("GAME_DIR",".")   # folder that contains the game build named index.html
import asyncio,json,math,sys,time
from playwright.async_api import async_playwright
URL=sys.argv[1] if len(sys.argv)>1 else "index.html?map=embedded";TAG=sys.argv[2] if len(sys.argv)>2 else "g256"
R=[]
def ok(n,c,x=""):
    R.append(bool(c));print(("PASS " if c else "FAIL ")+n+((" — "+str(x)) if x!="" else ""))
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=["--use-gl=swiftshader","--enable-unsafe-swiftshader"])
        pg=await b.new_page(viewport={"width":1400,"height":850});ev=pg.evaluate
        errs=[];pg.on("console",lambda m:errs.append(m.text) if m.type in("error","warning") else None);pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto("file://"+GAME_DIR+"/"+URL)
        for i in range(500):
            await pg.wait_for_timeout(500)
            if await pg.evaluate("typeof ready!=='undefined'&&ready===1"):break
        N=await ev("N");print(f"[{TAG}] N={N} map={await ev('BASTION_IMPORT.seedText')}")
        scr=lambda x,y:ev(f"[(X({x},{y})-cam.x)*cam.z+W/2,(Y({x},{y},1)-cam.y)*cam.z+H/2]")
        look=lambda x,y,z=.62:ev(f"(()=>{{cam.z=cam.tz={z};cam.x=cam.tx=X({x},{y});cam.y=cam.ty=Y({x},{y},1)-10}})()")
        # ---------- camera ----------
        c0=await ev("[cam.x,cam.y,cam.z]")
        await pg.keyboard.down("KeyD");await pg.wait_for_timeout(900);await pg.keyboard.up("KeyD")
        await pg.keyboard.down("KeyS");await pg.wait_for_timeout(700);await pg.keyboard.up("KeyS")
        c1=await ev("[cam.x,cam.y]");ok("camera pans with WASD on the imported map",c1[0]>c0[0]+100 and c1[1]>c0[1]+50,[round(c1[0]-c0[0]),round(c1[1]-c0[1])])
        await ev("cam.tx=1e9;cam.ty=1e9");await pg.wait_for_timeout(1200);c2=await ev("[cam.x,cam.y,WW,WH]")
        ok("camera clamps at the far corner of the 256 map",c2[0]<=c2[2]+1 and c2[1]<=c2[3],[round(c2[0]),round(c2[1]),c2[2],c2[3]])
        await ev("cam.tx=-1e9;cam.ty=-1e9");await pg.wait_for_timeout(1200);c3=await ev("[cam.x,cam.y]");ok("camera clamps at the origin corner",c3[0]>=-1 and c3[1]>=149,[round(c3[0]),round(c3[1])])
        hq=await ev("(()=>{const h=B.find(b=>b.type==='hq');return[h.x+h.w/2,h.y+h.w/2]})()");await look(hq[0],hq[1])
        z0=await ev("cam.tz");await pg.mouse.move(700,420);await pg.mouse.wheel(0,-400);await pg.wait_for_timeout(500);z1=await ev("cam.tz");ok("mouse-wheel zoom works",z1>z0,[z0,z1]);await look(hq[0],hq[1])
        # ---------- movement across imported terrain ----------
        await ev("G.speed=3;SU=U.slice()")
        tgt=await ev("""(()=>{const c=comp[cellOf(U[0])],hx=B.find(b=>b.type==='hq');let best=null;for(let a=0;a<360;a+=15){for(let r=13;r<20;r++){const x=(128+Math.cos(a*Math.PI/180)*r)|0,y=(128+Math.sin(a*Math.PI/180)*r)|0;const k=y*N+x;if(walk[k]&&comp[k]===c&&!blk[k]){let open=0;for(let j=-1;j<=1;j++)for(let i=-1;i<=1;i++)if(walk[(y+j)*N+x+i])open++;if(open===9){best=[x+.5,y+.5];break}}}if(best)break}return best})()""")
        s=await scr(*tgt);await pg.mouse.click(s[0],s[1],button="right")
        viol=0;hist=[]
        for i in range(70):
            await pg.wait_for_timeout(120)
            st=await ev("(()=>{let v=0,d=1e9;for(const u of U){if(blk[(u.y|0)*N+(u.x|0)])v++;d=Math.min(d,Math.hypot(u.x-%f,u.y-%f))}return[v,d]})()"%(tgt[0],tgt[1]))
            viol+=st[0];hist.append(st[1])
            if st[1]<2:break
        ok("dwarves walk to an open target across the imported terrain",hist[-1]<2.5,f"target {tgt}, closest dwarf {hist[-1]:.1f} tiles after {len(hist)*.12*3:.0f} sim-s")
        ok("no unit ever stood inside a tree (blocked) tile while walking",viol==0,viol)
        # tree tile as target: units may not enter it
        tree=await ev("""(()=>{const c=comp[cellOf(U[0])];let best=null,bd=1e9;for(let i=0;i<N*N;i++){if(!blk[i])continue;const x=i%N,y=i/N|0,d=Math.hypot(x-U[0].x,y-U[0].y);if(d<bd&&d>6&&d<24){let adj=0;for(const[dx,dy]of[[1,0],[-1,0],[0,1],[0,-1]]){const k=(y+dy)*N+x+dx;if(walk[k]&&comp[k]===c)adj++}if(adj>=1){bd=d;best=[x+.5,y+.5]}}}return best})()""")
        await ev("SU=U.slice()");s=await scr(*tree);await pg.mouse.click(s[0],s[1],button="right");v2=0
        for i in range(60):
            await pg.wait_for_timeout(120);v2+=await ev("U.filter(u=>blk[(u.y|0)*N+(u.x|0)]).length")
        ok("ordering a move INTO a tree tile never puts a unit inside it",v2==0,f"tree tile {tree}")
        # forest placement rule
        tt=await ev("(()=>{const i=blk.indexOf(1);return[i%N,i/N|0]})()")
        ok("a building cannot be placed on a tree tile ('Space is blocked')",await ev(f"check('house',{tt[0]},{tt[1]}).ok")==False and 'blocked' in await ev(f"check('house',{tt[0]},{tt[1]}).why"))
        # detour around a forest: path length vs straight line
        pr=await ev("""(()=>{const c=comp[cellOf(U[0])];const s=[U[0].x|0,U[0].y|0];let best=null,bs=0;for(let k=0;k<4000;k++){const x=(rnd()*N)|0,y=(rnd()*N)|0,i=y*N+x;if(!walk[i]||comp[i]!==c)continue;const d=Math.hypot(x-s[0],y-s[1]);if(d<30||d>46)continue;let tr=0;const n=24;for(let q=1;q<n;q++){const xx=Math.round(s[0]+(x-s[0])*q/n),yy=Math.round(s[1]+(y-s[1])*q/n);if(blk[yy*N+xx])tr++}if(tr>bs){bs=tr;best=[x+.5,y+.5,tr]}}return best})()""")
        if pr:
            await ev("SU=U.slice()");s=await scr(pr[0],pr[1]);await look(pr[0],pr[1],.62);s=await scr(pr[0],pr[1]);await look(U0:=None) if False else None
        await b.close()
    print(f"\n{sum(R)}/{len(R)} passed (part A)");print("errors:",errs or "none")
asyncio.run(main())
