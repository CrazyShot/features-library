import os
GAME_DIR=os.environ.get("GAME_DIR",".")   # folder that contains the game build named index.html
import asyncio
from playwright.async_api import async_playwright
from rt_common import *
R_="FEATURE_BUILDING_REPAIR"
async def main():
    async with async_playwright() as p:
        b,pg,errs=await boot(p);ev=pg.evaluate
        scr=lambda x,y:ev(f"({SCR})({x},{y})")
        async def wt(ms):
            await pg.wait_for_timeout(ms);await ev("G.t=Math.min(G.t,15)")   # keep the day phase: a real wave mid-test would (correctly) block repairs
        # =============== 1. NO COMBINED HP ===============
        hqc=await ev("(()=>{const h=B.find(b=>b.type==='hq');return[h.x+h.w/2,h.y+h.w/2]})()")
        await ev("""(()=>{const hq=B.find(b=>b.type==='hq');for(let i=0;i<4;i++)spawnRanger(hq);
          const at=(dx,dy)=>{const q=nearestWalk((hq.x+hq.w/2+dx)|0,(hq.y+hq.w+dy)|0);return[q[0],q[1]]};
          window.__vamp=[at(-5,6),at(-3,7),at(4,6)].map(p=>{spawnE(p);return E[E.length-1]});for(const e of __vamp){e.tg=null;e.cd=99;e.vHold=1}
          const w=E.find(e=>e.wl);w.x=w.sx=__vamp[0].x+3;w.y=w.sy=__vamp[0].y;window.__wild=w;
          U[0].hp=50;U[1].hp=90})()""")
        await ev("(()=>{cam.z=cam.tz=.62;cam.x=cam.tx=X(%f,%f);cam.y=cam.ty=Y(%f,%f,1)+40})()"%(hqc[0],hqc[1]+3,hqc[0],hqc[1]+3));await wt(600)
        async def unit_screen(expr):
            p_=await ev(f"(()=>{{const u={expr};return ({SCR})(u.x,u.y)}})()");return p_[0],p_[1]-14*.62
        uip=lambda:ev("document.getElementById('uip').innerText.replace(/\\n+/g,' | ')")
        has_bar=lambda:ev("!!document.querySelector('#uip .hb')")
        await ev("SU=[];SB=null");x,y=await unit_screen("U.find(u=>u.kind==='dwarf')");await pg.mouse.dblclick(x,y);await wt(300)
        t=await uip();print("   6 dwarves  :",t)
        ok("double-click selects the dwarves (selection behaviour unchanged)",await ev("SU.length")==6 and await ev("SU.every(u=>u.kind==='dwarf')"))
        sumhp=await ev("Math.ceil(SU.reduce((a,u)=>a+u.hp,0))");sumx=await ev("SU.reduce((a,u)=>a+u.mh,0)")
        ok("several dwarves: NO combined HP value or bar",not await has_bar() and f"{sumhp} / {sumx}" not in t and str(sumx) not in t and "HP" not in t.replace("select a single unit to see its HP",""),t[:80])
        ok("…shows the selection count and a clear summary instead","6 selected" in t and "6× Dwarf Warrior" in t and "Attack (each)" in t)
        ok("…and the host title still shows the count (6 Dwarf Warriors selected)","6 Dwarf Warriors selected" in await ev("document.getElementById('pt').textContent"))
        await ev("SU=[]");await pg.mouse.click(*(await unit_screen("U[0]")));await wt(300);t=await uip()
        ok("a SINGLE unit still shows its own HP bar and value (50 / 130)",await has_bar() and "50 / 130" in t,t[:50])
        x,y=await unit_screen("U.find(u=>u.kind==='ranger')");await ev("SU=[];SB=null");await pg.mouse.dblclick(x,y);await wt(300);t=await uip()
        ok("several rangers: no combined HP (no 240 total, no bar)",await ev("SU.length")==4 and not await has_bar() and "240" not in t and "4× Ranger" in t,t[:70])
        await ev("SU=U.slice(0,6).concat(U.filter(u=>u.kind==='ranger'));SB=null");await wt(300);t=await uip()
        ok("mixed dwarves + rangers: one summary block per type, no HP anywhere",not await has_bar() and "6× Dwarf Warrior" in t and "4× Ranger" in t and "HP" not in t.replace("select a single unit to see its HP",""),t[:90])
        # enemies
        await ev("SU=[];SB=null");vx,vy=await ev("({SCR})(__vamp[0].x,__vamp[0].y)".replace("{SCR}",SCR));await pg.mouse.click(vx,vy-14*.62);await wt(300);t=await uip()
        ok("a SINGLE enemy shows its own HP bar and value",await has_bar() and "HP" in t and f"{await ev('Math.ceil(__vamp[0].hp)')} / {await ev('Math.ceil(__vamp[0].mh)')}" in t,t[:60])
        await pg.mouse.dblclick(vx,vy-14*.62);await wt(350);t=await uip();n=await ev("FEATURE_UNIT_INFO.inspect().length");print("   vampires   :",t[:170])
        ok("double-click selects several visible vampires (fog rules unchanged)",n>=3 and await ev("FEATURE_UNIT_INFO.inspect().every(e=>fogVis(e.x,e.y))"),n)
        ok("several vampires: NO combined HP value or bar",not await has_bar() and "HP" not in t.replace("select a single unit to see its HP","") and str(await ev("Math.ceil(FEATURE_UNIT_INFO.inspect().reduce((a,e)=>a+e.hp,0))")) not in t.split("1×")[0],t[:90])
        ok("…title and summary show the count",f"{n} Vampires selected" in await ev("document.getElementById('pt').textContent") and f"{n}× Vampire" in t)
        ok("…and a wave+wilderness mix is summarised honestly (damage range, no single misleading value)",await ev("FEATURE_UNIT_INFO.inspect().some(e=>e.wl)") and "Wave + wilderness" in t and "4–6 damage" in t,t[:140])
        await pg.screenshot(path="r_multi_hp.png",clip={"x":0,"y":470,"width":420,"height":380})
        # =============== 2. REPAIR NEAR ENEMIES ===============
        await ev("for(const e of E.slice())killQuiet(e);SU=[];SB=null;FEATURE_UNIT_INFO.clearInspect()")
        spots=await ev("""(()=>{const hq=B.find(b=>b.type==='hq'),cx=hq.x+2,cy=hq.y+2,sp=[];for(let ty=2;ty<N-4;ty+=3)for(let tx=2;tx<N-4;tx+=3)if(check('house',tx,ty).ok)sp.push([tx,ty,Math.hypot(tx-cx,ty-cy)]);
          const near=sp.filter(s=>s[2]>7&&s[2]<17).sort((a,b)=>a[2]-b[2]).slice(0,7);let iso=null,bd=0;for(const s of sp){const d=Math.min(...near.map(n=>Math.hypot(n[0]-s[0],n[1]-s[1])),Math.hypot(cx-s[0],cy-s[1]));if(d>bd){bd=d;iso=s}}
          return{near,iso,isoDist:bd}})()""")
        print("   spots: cluster",len(spots['near']),"isolated",spots['iso'][:2],"min distance to anything",round(spots['isoDist'],1))
        ok("test layout: an isolated building site >24 tiles from everything else exists",spots['isoDist']>24,round(spots['isoDist'],1))
        async def mk(tx,ty,done=True):
            i=await ev(f"(()=>{{const b=place('house',{tx},{ty});if(!b)return null;if({str(done).lower()})b.t0=G.T-100;return b.id}})()");return i
        B_=lambda i:f"B.find(b=>b.id=={i})"
        A=await mk(spots['iso'][0],spots['iso'][1]);Bc=await mk(*spots['near'][0][:2])
        await ev("G.speed=1");await wt(300);await ev("G.speed=0")
        await ev(f"hurt({B_(A)},120);hurt({B_(Bc)},150)")
        await ev("window.__mkE=(x,y)=>{spawnE([x|0,y|0]);const e=E[E.length-1];e.x=e.sx=x;e.y=e.sy=y;e.tg=null;e.cd=99;e.vHold=1;e.hp=e.mh=1e9;return e}")
        ctr=lambda i:ev(f"(()=>{{const b={B_(i)};return[b.x+b.w/2,b.y+b.w/2]}})()")
        cA=await ctr(A)
        print("   threat radius:",await ev(f"{R_}.cfg.threatRadius"),"tiles")
        res={}
        for d in(14,10.5,10,9.9,6,2):
            await ev("for(const e of E.slice())killQuiet(e)");await ev(f"__mkE({cA[0]+d},{cA[1]})")
            res[d]=(await ev(f"{R_}.canRepair({B_(A)})"),await ev(f"{R_}.threat({B_(A)})"))
        print("   canRepair by enemy distance:",res)
        ok("enemy at 14 / 10.5 tiles: repair allowed",res[14][0] and res[10.5][0])
        ok("enemy at exactly 10 / 9.9 / 6 / 2 tiles: repair blocked (radius 10)",not any(res[d][0] for d in(10,9.9,6,2)))
        # UI explanation
        await ev("for(const e of E.slice())killQuiet(e)");e1=await ev(f"(()=>{{window.__e1=__mkE({cA[0]+5},{cA[1]});return 1}})()")
        await ev(f"SB={B_(A)};SU=[]");await wt(400)
        bt=(await pg.inner_text('#repair-btn')).strip();nt=(await pg.inner_text('#repair-note')).strip();print("   button:",bt,"| note:",nt)
        ok("panel explains why repair is unavailable (button + note)","unavailable" in bt.lower() and "enemies" in bt.lower() and "within 10 tiles" in nt and 'dis' in await ev("document.getElementById('repair-btn').className"))
        ok("start() refuses and says enemies are nearby",await ev(f"{R_}.start({B_(A)})")==False and "Enemies nearby" in await ev(f"{R_}.why({B_(A)})"))
        ok("toast explains it too","Enemies nearby" in await ev("document.getElementById('ts').textContent"),await ev("document.getElementById('ts').textContent"))
        # per-building: a distant enemy blocks only the building it is near
        ok("per building: A (enemy 5 tiles away) blocked, B (far away) repairable at the same time",await ev(f"{R_}.canRepair({B_(A)})")==False and await ev(f"{R_}.canRepair({B_(Bc)})")==True,await ev(f"[{R_}.threat({B_(A)}),{R_}.threat({B_(Bc)})]"))
        await ev(f"SB={B_(Bc)}");await wt(300);ok("…B's panel offers a normal Repair",(await pg.inner_text('#repair-btn')).strip().startswith("Repair —"))
        # enemy approaches DURING repair
        await ev("G.speed=0");await pg.click('#repair-btn');await ev("G.speed=3");hs=[]
        for i in range(5):await wt(300);hs.append(await ev(f"{B_(Bc)}.hp"))
        ok("(setup) B is repairing while the enemy stays near A only",hs[-1]>hs[0] and await ev(f"{R_}.repairing().length")==1,[round(h) for h in hs])
        cB=await ctr(Bc);hp_before=await ev(f"{B_(Bc)}.hp");res_before=await ev("({...G.res})")
        await ev(f"window.__e2=__mkE({cB[0]+6},{cB[1]})");await wt(300);hp0=await ev(f"{B_(Bc)}.hp");r0=await ev("({...G.res})")
        toast=await ev("document.getElementById('ts').textContent");await wt(1500);hp1=await ev(f"{B_(Bc)}.hp");r1=await ev("({...G.res})")
        ok("enemy approaches during repair: healing PAUSES (HP frozen)",abs(hp1-hp0)<1e-9 and await ev(f"{B_(Bc)}._rp.paused")==True,(round(hp0,2),round(hp1,2)))
        ok("…and nothing is charged while paused",r0==r1,(r0['wood'],r1['wood']))
        ok("…the player is told (toast)","paused" in toast and "enemies" in toast.lower(),toast)
        bt=(await pg.inner_text('#repair-btn')).strip();nt=(await pg.inner_text('#repair-note')).strip();ok("…panel shows the paused state with an explanation","paused" in bt.lower() and "clear" in nt.lower(),bt)
        ok("…the repair is kept (still active), not cancelled",await ev(f"{R_}.repairing().length")==1)
        await ev("G.speed=1;for(const e of E.filter(e=>e===__e2))killQuiet(e)");await wt(350);hp2=await ev(f"{B_(Bc)}.hp");paused_now=await ev(f"{B_(Bc)}._rp.paused")
        ok("area just cleared but the 1 s resume delay has not elapsed: still paused (no flapping)",abs(hp2-hp1)<1e-9 and paused_now==True,(round(hp1,2),round(hp2,2),paused_now))
        await ev("G.speed=3");await wt(2500);hp3=await ev(f"{B_(Bc)}.hp")
        ok("enemy gone: repair resumes by itself and heals again",hp3>hp1 and await ev(f"{B_(Bc)}._rp.paused")==False,(round(hp1,1),round(hp3,1)))
        # manual cancel while paused
        await ev(f"window.__e3=__mkE({cB[0]+4},{cB[1]})");await wt(500)
        ok("(setup) paused again",await ev(f"{B_(Bc)}._rp.paused")==True)
        await pg.click('#repair-btn');ok("Stop works while paused (existing cancellation behaviour kept)",await ev(f"{R_}.repairing().length")==0)
        await ev("G.speed=0;for(const e of E.slice())killQuiet(e)")
        # wilderness enemy counts too
        w=await ev("(()=>{const e=__mkE(%f,%f);e.wl={m:[e]};return 1})()"%(cB[0]+8,cB[1]));ok("a wilderness-type enemy inside the radius also blocks repair",await ev(f"{R_}.canRepair({B_(Bc)})")==False)
        await ev("for(const e of E.slice())killQuiet(e)")
        await pg.screenshot(path="r_repair_blocked.png",clip={"x":0,"y":470,"width":560,"height":380})
        # =============== 3. REPAIR ALL ===============
        await ev("G.speed=0;G.res.wood=400;G.res.stone=200;G.res.iron=60;G.res.gold=100")
        # fresh set of buildings: clear previous test houses
        await ev("for(const q of B.filter(b=>b.type==='house').slice())hurt(q,1e6)");await wt(200)
        near=spots['near'];iso=spots['iso']
        ids={}
        for name,(tx,ty),done in(("b1",near[0][:2],True),("b2",near[1][:2],True),("b3",near[2][:2],True),("b4",near[3][:2],False),("b5",iso[:2],True),("b6",near[4][:2],True),("b7",near[5][:2],True)):
            ids[name]=await mk(tx,ty,done)
        await ev("G.speed=1");await wt(350);await ev("G.speed=0")
        for n_ in("b1","b2","b5","b7"):await ev(f"hurt({B_(ids[n_])},110)")
        await ev(f"hurt({B_(ids['b4'])},80)")            # under construction + damaged
        await ev(f"hurt({B_(ids['b6'])},1e6)")           # destroyed
        await ev(f"{R_}.start({B_(ids['b7'])})")         # already repairing
        c5=await ctr(ids['b5']);await ev(f"__mkE({c5[0]+4},{c5[1]})")
        await ev("SU=[];SB=null");await wt(500)
        st=await ev(f"{R_}.status()");lab=(await pg.inner_text('#repair-all')).replace("\n"," | ");print("   status:",st,"| button:",lab)
        ok("Repair All button is shown above the build bar, outside #bar (host loop over bar.children stays safe)",await ev("getComputedStyle(document.getElementById('repair-all')).display")!='none' and await ev("document.getElementById('repair-all').parentElement===document.body"))
        ok("button reports counts: repairing / ready / blocked by enemies / under construction","1 repairing" in lab and "2 ready" in lab and "1 blocked by enemies" in lab and "1 under construction" in lab,lab)
        ok("status() matches the real states (b1,b2 eligible; b7 repairing; b5 blocked; b3 full; b4 building; b6 gone)",st['eligible']==2 and st['repairing']==1 and st['blocked']==1 and st['building']==1 and not await ev(f"B.some(b=>b.id=={ids['b6']})"),st)
        hp_b1=await ev(f"{B_(ids['b1'])}.hp");res_a=await ev("({...G.res})")
        await pg.click('#repair-all');await wt(150)
        act=await ev(f"{R_}.repairing().map(b=>b.id)")
        ok("click: repairs started for b1, b2 (+ b7 already running) only",set(act)=={ids['b1'],ids['b2'],ids['b7']},act)
        ok("not started: b3 (full HP), b4 (under construction), b5 (enemy near), b6 (destroyed)",not({ids['b3'],ids['b4'],ids['b5'],ids['b6']}&set(act)))
        ok("NOTHING healed or charged at the click (no instant heal, no bypass)",await ev(f"{B_(ids['b1'])}.hp")==hp_b1 and await ev("({...G.res})")==res_a)
        tt=await ev("document.getElementById('ts').textContent");ok("summary toast: started / already repairing / blocked by nearby enemies","started 2 repairs" in tt and "1 already repairing" in tt and "1 blocked by nearby enemies" in tt,tt)
        await ev("G.speed=3");hs=[]
        for i in range(60):
            await wt(250);hs.append(await ev(f"{B_(ids['b1'])}.hp"))
            if hs[-1]>=await ev(f"{B_(ids['b1'])}.mh"):break
        ok("healing is gradual",len(set(round(h) for h in hs))>=6 and max(b_-a_ for a_,b_ in zip(hs,hs[1:]))<40,f"{len(hs)} samples, {round(hs[0])}→{round(hs[-1])}")
        await wt(800)
        ok("b1, b2 and b7 reach full HP and their repairs end",(await ev("["+",".join(f"{B_(ids[n_])}.hp=={B_(ids[n_])}.mh" for n_ in("b1","b2","b7"))+"].every(Boolean)")) and await ev(f"{R_}.repairing().length")==0)
        res_b=await ev("({...G.res})");exp_w=3*40*.4*110/220
        ok("cost = existing economy: ≈40% of house cost per HP restored, for three houses",abs((res_a['wood']-res_b['wood'])-exp_w)<=3,f"wood −{res_a['wood']-res_b['wood']} (≈{exp_w:.0f})")
        ok("the blocked building b5 stayed damaged and the under-construction b4 was untouched",await ev(f"{B_(ids['b5'])}.hp<{B_(ids['b5'])}.mh") and await ev(f"{B_(ids['b4'])}.hp")==await ev(f"{B_(ids['b4'])}.mh-80"))
        await wt(300);lab=(await pg.inner_text('#repair-all')).replace("\n"," | ");print("   button now:",lab)
        ok("after the repairs the button shows what is left (1 blocked by enemies)","1 blocked by enemies" in lab)
        await ev("G.speed=0;for(const e of E.slice())killQuiet(e)");await wt(400);await pg.click('#repair-all');await ev("G.speed=3")
        for i in range(60):
            await wt(250)
            if await ev(f"{B_(ids['b5'])}.hp=={B_(ids['b5'])}.mh"):break
        ok("enemy gone: Repair All now includes b5 and finishes it",await ev(f"{B_(ids['b5'])}.hp=={B_(ids['b5'])}.mh"))
        # b4 was under construction when Repair All ran the first time; it finished building during the run, so the second Repair All repaired it too
        await wt(300)
        ok("b4 (under construction at the first click) finished building and was repaired by the second Repair All",await ev(f"{B_(ids['b4'])}.p")==1 and await ev(f"{B_(ids['b4'])}.hp=={B_(ids['b4'])}.mh"))
        await ev("G.speed=0");await wt(500)
        ok("everything repaired: no damaged buildings left, Repair All hides itself",(await ev(f"{R_}.status()"))['damaged']==0 and await ev("getComputedStyle(document.getElementById('repair-all')).display")=='none')
        # insufficient resources
        await ev(f"hurt({B_(ids['b3'])},1e6)");await wt(200)
        await ev('G.res.wood=300;G.res.stone=200')
        fs=await ev("(()=>{const hq=B.find(b=>b.type==='hq'),o=[];for(let ty=hq.y+4;ty<hq.y+22&&o.length<3;ty+=3)for(let tx=hq.x-12;tx<hq.x+14&&o.length<3;tx+=3)if(check('house',tx,ty).ok)o.push([tx,ty]);return o})()")
        print('   free spots',fs,'res',await ev('({...G.res})'),'state',await ev('G.state'))
        hs_=[]
        for f_ in fs:
            r_=await mk(*f_);hs_.append(r_)
            if r_ is None:print('   place failed at',f_,await ev(f"check('house',{f_[0]},{f_[1]})"))
        assert all(h is not None for h in hs_),hs_
        await ev("G.speed=1");await wt(350);await ev("G.speed=0")
        for h in hs_:await ev(f"hurt({B_(h)},200)")
        await ev("G.res.wood=0;G.res.stone=0");await wt(400)
        await pg.click('#repair-all');tt=await ev("document.getElementById('ts').textContent")
        ok("no resources at all: Repair All starts nothing and says why",await ev(f"{R_}.repairing().length")==0 and "not enough resources" in tt and "3 skipped" in tt,tt)
        await ev("G.res.wood=2;G.res.stone=2");await wt(300);await pg.click('#repair-all');tt=await ev("document.getElementById('ts').textContent")
        ok("a shared shortage is detected up front: only as many repairs start as the stockpile can start (2 of 3)",await ev(f"{R_}.repairing().length")==2 and "started 2 repairs" in tt and "1 skipped: not enough resources" in tt,tt)
        await ev("G.speed=3");seen=[]
        for i in range(28):
            await wt(250);seen.append(await ev("document.getElementById('ts').textContent"))
        await ev("G.speed=0")
        ok("running dry mid-repair stops those repairs cleanly: no negative resources, no free healing",await ev("G.res.wood>=0&&G.res.stone>=0") and await ev(f"{R_}.repairing().length")==0 and await ev(f"{R_}.status().damaged")>=1,await ev("[G.res.wood,G.res.stone]"))
        ok("…and the player is told once that repairs stopped for lack of resources",any("Repair stopped: not enough resources" in s for s in seen),[s for s in seen if "stopped" in s][:1])
        ok("no console errors/warnings",not errs,errs[:3]);await b.close()
    print(f"{sum(R)}/{len(R)} passed (follow-up fixes)")
asyncio.run(main())
