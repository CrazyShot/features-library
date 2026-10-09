import os
GAME_DIR=os.environ.get("GAME_DIR",".")   # folder that contains the game build named index.html
import asyncio
from playwright.async_api import async_playwright
from rt_common import *
API="FEATURE_BUILDING_REPAIR"
async def main():
    async with async_playwright() as p:
        b,pg,errs=await boot(p);ev=pg.evaluate
        await ev("for(const e of E.slice())killQuiet(e)")        # keep the wilderness out of a UI test
        hq=await ev("(()=>{const h=B.find(b=>b.type==='hq');return[h.x+h.w/2,h.y+h.w/2]})()")
        await ev("(()=>{cam.z=cam.tz=.8;cam.x=cam.tx=X(%f,%f);cam.y=cam.ty=Y(%f,%f,1)+30})()"%(hq[0],hq[1]+4,hq[0],hq[1]+4));await pg.wait_for_timeout(400)
        spots=await ev("""(()=>{const q=[];for(let ty=(B[0].y+5);ty<B[0].y+22&&q.length<5;ty+=3)for(let tx=B[0].x-9;tx<B[0].x+10&&q.length<5;tx+=3)if(check('house',tx,ty).ok)q.push([tx,ty]);return q})()""")
        async def mk(type_,i,done=True):
            r=await ev(f"(()=>{{const b=place('{type_}',{spots[i][0]},{spots[i][1]});if(!b)return null;if({str(done).lower()})b.t0=G.T-100;return b.id}})()")
            if done:
                await ev("G.speed=1");await pg.wait_for_timeout(250);await ev("G.speed=0")
            return r
        B_=lambda i:f"B.find(b=>b.id=={i})"
        async def click_building(i):
            p=await ev(f"(()=>{{const b={B_(i)};return ({SCR})(b.x+b.w/2,b.y+b.w/2)}})()");await ev("SU=[];SB=null")
            await pg.mouse.click(p[0],p[1]-18);await pg.wait_for_timeout(300)
        h1=await mk('house',0)
        ok("a new house is built and at full HP: no Repair action offered",await ev(f"{API}.canRepair({B_(h1)})")==False)
        await click_building(h1);ok("full-HP building: panel has no Repair button",await ev("getComputedStyle(document.getElementById('repair-btn')).display")=='none')
        ok("start() refuses a full-HP building ('Already at full HP')",await ev(f"{API}.start({B_(h1)})")==False and await ev(f"{API}.why({B_(h1)})")=='Already at full HP')
        # ---- damage -> repair -> full ----
        await ev(f"hurt({B_(h1)},150)");mh=await ev(f"{B_(h1)}.mh");hp0=await ev(f"{B_(h1)}.hp");print(f"   house hp after damage: {hp0}/{mh}")
        await pg.wait_for_timeout(300);btn=(await pg.inner_text('#repair-btn')).strip();print("   button:",btn)
        ok("damaged building: panel shows a Repair button with the cost",btn.startswith("Repair")and"wood"in btn,btn)
        res0=await ev("({...G.res})");await pg.click('#repair-btn');await pg.wait_for_timeout(100)
        ok("clicking Repair starts a repair (existing building system, flagged active)",await ev(f"{API}.repairing().length")==1)
        ok("button turns into 'Stop repair'","Stop repair" in (await pg.inner_text('#repair-btn')))
        await ev("G.speed=3");hs=[];rs=[]
        for i in range(120):
            await pg.wait_for_timeout(250);hs.append(await ev(f"{B_(h1)}.hp"));rs.append(await ev("G.res.wood"))
            if not await ev(f"{API}.repairing().length"):break
        await ev("G.speed=0");hpend=await ev(f"{B_(h1)}.hp")
        d=[b_-a for a,b_ in zip(hs,hs[1:])]
        ok("HP is restored gradually (many intermediate values, no instant heal)",len(set(round(x) for x in hs))>=8 and max(d)<mh*.2 and hs[0]<mh,f"{len(hs)} samples {round(hs[0])}→{round(hs[-1])}, biggest step {max(d):.1f}")
        ok("repair reaches exactly full HP and stops by itself",hpend==mh and await ev(f"{API}.repairing().length")==0,hpend)
        res1=await ev("({...G.res})");exp_w=40*.4*150/mh;exp_s=10*.4*150/mh
        ok("cost was paid from the existing resources, proportional to HP restored",res0["wood"]-res1["wood"] in(int(exp_w),int(exp_w)+1) and res0["stone"]-res1["stone"] in(int(exp_s),int(exp_s)+1) and res0["iron"]==res1["iron"],f"wood −{res0['wood']-res1['wood']} (≈{exp_w:.1f}), stone −{res0['stone']-res1['stone']} (≈{exp_s:.1f})")
        ok("wood fell gradually while repairing, not all at once",len(set(rs))>=3,sorted(set(rs),reverse=True)[:5])
        ok("after full HP the Repair button is gone again",await ev("getComputedStyle(document.getElementById('repair-btn')).display")=='none')
        # ---- pause ----
        await ev(f"hurt({B_(h1)},100)");await pg.wait_for_timeout(300);await pg.click('#repair-btn');await ev("G.speed=1");await pg.wait_for_timeout(700);await pg.keyboard.press("Space");await pg.wait_for_timeout(250);a=await ev(f"{B_(h1)}.hp");await pg.wait_for_timeout(900);c=await ev(f"{B_(h1)}.hp")
        ok("repair does nothing while the game is paused",abs(a-c)<1e-9 and await ev("G.speed")==0,(a,c))
        await pg.keyboard.press("Space");await pg.wait_for_timeout(1200);ok("…and continues when unpaused",await ev(f"{B_(h1)}.hp")>c)
        # ---- manual cancel ----
        await pg.click('#repair-btn');ok("pressing Stop repair cancels cleanly (HP stays where it is, no longer active)",await ev(f"{API}.repairing().length")==0 and await ev(f"{B_(h1)}.hp")<mh)
        await pg.wait_for_timeout(500);x=await ev(f"{B_(h1)}.hp");await pg.wait_for_timeout(500);ok("a cancelled repair no longer heals",abs(x-await ev(f"{B_(h1)}.hp"))<1e-9)
        # ---- damage while repairing keeps working ----
        await pg.click('#repair-btn');await ev("G.speed=1");await pg.wait_for_timeout(400);y=await ev(f"{B_(h1)}.hp");await ev(f"hurt({B_(h1)},40)");z=await ev(f"{B_(h1)}.hp");await pg.wait_for_timeout(800)
        ok("new damage during repair lowers HP and repair carries on",z<y and await ev(f"{B_(h1)}.hp")>z and await ev(f"{API}.repairing().length")==1,(round(y),round(z),round(await ev(f'{B_(h1)}.hp'))))
        # ---- destroyed while repairing ----
        await ev("G.speed=1");await ev(f"window.__dead={B_(h1)}");await ev("hurt(__dead,1e6)");await pg.wait_for_timeout(500)
        ok("destroyed while repairing: repair stops and is forgotten, nothing left behind",await ev(f"{API}.repairing().length")==0 and await ev(f"!B.some(b=>b.id=={h1})"))
        ok("a destroyed building cannot be repaired (start() refuses it too)",await ev(f"{API}.canRepair(__dead)")==False and await ev(f"{API}.start(__dead)")==False and await ev("__dead.dead===true"))
        # ---- removed from the world while repairing (what a future sell/demolish does) ----
        h2=await mk('house',1);await ev(f"hurt({B_(h2)},120)");await ev(f"window.__b2={B_(h2)}");await ev(f"{API}.start(__b2)");await ev("G.speed=1");await pg.wait_for_timeout(400)
        ok("(setup) repair is running",await ev(f"{API}.repairing().length")==1)
        await ev("{const i=B.indexOf(__b2);B.splice(i,1)}");await pg.wait_for_timeout(500)
        ok("building removed from the world (sell-like): repair is cancelled cleanly",await ev(f"{API}.repairing().length")==0 and await ev(f"{API}.canRepair(__b2)")==False)
        ok("…and a removed/destroyed building reports it cannot be repaired",await ev(f"{API}.why(__b2)")=='This building no longer exists')
        # ---- under construction ----
        await ev("G.speed=0");h3=await mk('house',2,done=False);await ev(f"hurt({B_(h3)},100)")
        ok("a building under construction cannot be repaired ('Finish construction first')",await ev(f"{API}.start({B_(h3)})")==False and await ev(f"{API}.why({B_(h3)})")=='Finish construction first')
        await click_building(h3);bt=(await pg.inner_text('#repair-btn')).strip();ok("panel shows the disabled 'finish construction first' state",'finish construction' in bt.lower() and 'dis' in await ev("document.getElementById('repair-btn').className"),bt)
        await ev(f"{B_(h3)}.t0=G.T-100");await ev("G.speed=1");await pg.wait_for_timeout(300);await ev("G.speed=0");await pg.wait_for_timeout(200)
        ok("once construction completes the same building can be repaired",await ev(f"{API}.canRepair({B_(h3)})")==True and (await pg.inner_text('#repair-btn')).strip().startswith("Repair"))
        # ---- not enough resources ----
        await ev(f"window.__b3={B_(h3)}");await ev("G.res.wood=0");ok("cannot start without the resources",await ev(f"{API}.start(__b3)")==False)
        await ev("G.res.wood=200");ok("…can with them",await ev(f"{API}.start(__b3)")==True);await ev("G.speed=3;G.res.wood=0");await pg.wait_for_timeout(5000)
        ok("running out of a resource mid-repair stops it cleanly (no negative resources)",await ev(f"{API}.repairing().length")==0 and await ev("G.res.wood")>=0 and await ev("__b3.hp<__b3.mh"),await ev("G.res.wood"))
        # ---- multi-building (mixed selection) ----
        await ev("G.speed=0;G.res.wood=300;FEATURE_BUILDING_REPAIR.repairing().forEach(b=>FEATURE_BUILDING_REPAIR.stop(b))");h4=await mk('house',3);await ev(f"hurt({B_(h3)},50);hurt({B_(h4)},90)")
        await click_building(h3);p=await ev(f"(()=>{{const b={B_(h4)};return ({SCR})(b.x+b.w/2,b.y+b.w/2)}})()")
        await pg.keyboard.down("Shift");await pg.mouse.click(p[0],p[1]-18);await pg.keyboard.up("Shift");await ev("SU=[U[0]]");await pg.wait_for_timeout(300)
        bt=(await pg.inner_text('#repair-btn')).strip();ok("units + two damaged buildings selected: one Repair button for both",bt.startswith("Repair (2)"),bt)
        await pg.click('#repair-btn');ok("…starts both repairs",await ev(f"{API}.repairing().length")==2)
        await pg.screenshot(path="r_repair_ui.png",clip={"x":0,"y":470,"width":560,"height":380})
        ok("no console errors/warnings",not errs,errs[:3]);await b.close()
    print(f"{sum(R)}/{len(R)} passed (repair)")
asyncio.run(main())
