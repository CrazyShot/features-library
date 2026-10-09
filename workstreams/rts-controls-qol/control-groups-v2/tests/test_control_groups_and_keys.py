import os
GAME_DIR=os.environ.get("GAME_DIR",".")   # folder that contains the game build named index.html
import asyncio
from playwright.async_api import async_playwright
from rt_common import *
API="FEATURE_CTRLGROUPS_V2"
async def main():
    async with async_playwright() as p:
        b,pg,errs=await boot(p);ev=pg.evaluate
        scr=lambda x,y:ev(f"({SCR})({x},{y})")
        await ev("(()=>{const u=U[0];cam.z=cam.tz=.9;cam.x=cam.tx=X(u.x,u.y);cam.y=cam.ty=Y(u.x,u.y,1)-20})()");await pg.wait_for_timeout(500)
        # ---------------- speed keys: 1/2/3 no longer change speed, +/- do ----------------
        await ev("G.speed=1;G.prevSpeed=1")
        for k in("Digit1","Digit2","Digit3"):await pg.keyboard.press(k)
        ok("1/2/3 no longer change game speed",await ev("G.speed")==1,await ev("G.speed"))
        await pg.keyboard.press("Equal");s1=await ev("G.speed");await pg.keyboard.press("Shift+Equal");s2=await ev("G.speed");await pg.keyboard.press("Equal");s3=await ev("G.speed")
        ok("+ raises speed 1→2→3 and caps at 3",(s1,s2,s3)==(2,3,3),(s1,s2,s3))
        await pg.keyboard.press("Minus");m1=await ev("G.speed");await pg.keyboard.press("Minus");m2=await ev("G.speed");await pg.keyboard.press("Minus");m3=await ev("G.speed")
        ok("− lowers speed 3→2→1 and stops at 1",(m1,m2,m3)==(2,1,1),(m1,m2,m3))
        await pg.keyboard.press("NumpadAdd");ok("numpad + works",await ev("G.speed")==2);await pg.keyboard.press("NumpadSubtract");ok("numpad − works",await ev("G.speed")==1)
        z=await ev("cam.tz");await pg.keyboard.press("Equal");await pg.keyboard.press("Minus");ok("+ / − no longer zoom the camera (zoom stays on Q/E + wheel)",abs(await ev("cam.tz")-z)<1e-9);
        await pg.keyboard.press("KeyQ");ok("Q still zooms in",await ev("cam.tz")>z)
        await ev("cam.z=cam.tz=.9")
        await pg.keyboard.press("Space");ok("Space pauses",await ev("G.speed")==0)
        await pg.keyboard.press("Equal");ok("+ while paused changes the resume speed, stays paused",await ev("G.speed")==0 and await ev("G.prevSpeed")==2,await ev("[G.speed,G.prevSpeed]"))
        await pg.keyboard.press("Space");ok("Space resumes at that speed",await ev("G.speed")==2);await ev("G.speed=0")
        ok("speed buttons still visible (PAUSE 1× 2× 3×)",await ev("[...document.querySelectorAll('#sp button')].every(b=>b.offsetParent!==null)"))
        await pg.click('#sp button[data-s="3"]');ok("speed buttons still work",await ev("G.speed")==3);await ev("G.speed=0")
        await pg.keyboard.press("Shift+Digit2");ok("Shift+2 still selects the House build shortcut",await ev("sel")=='house',await ev("sel"));await pg.keyboard.press("Shift+Digit7");ok("Shift+7 → Tower",await ev("sel")=='tower');await pg.keyboard.press("Escape")
        # ---------------- group 1 / mixed / exclusivity ----------------
        await ev("SU=[];SB=null");await pg.keyboard.press("Digit9");ok("recalling an empty group changes nothing",await ev("SU.length")==0 and await ev("SB")is None)
        # real drag-box over the dwarves
        pts=[await scr(u['x'],u['y']) for u in await ev("U.map(u=>({x:u.x,y:u.y}))")]
        x0=min(q[0] for q in pts)-25;x1=max(q[0] for q in pts)+25;y0=min(q[1] for q in pts)-60;y1=max(q[1] for q in pts)+20
        await pg.mouse.move(x0,y0);await pg.mouse.down();await pg.mouse.move(x1,y1,steps=6);await pg.mouse.up()
        ok("drag-box selects the dwarves",await ev("SU.length")==6,await ev("SU.length"))
        await pg.keyboard.press("Control+Digit1");g1=await ev(f"{API}.get(1).length")
        ok("Ctrl+1 stores the 6 units",g1==6,g1)
        await pg.keyboard.press("Escape");ok("Esc deselects",await ev("SU.length")==0)
        await pg.keyboard.press("Digit1");ok("1 recalls group 1",await ev("SU.length")==6 and await ev("SB")is None)
        # move one unit from group 1 to group 2
        await ev("SU=[U[0]]");await pg.keyboard.press("Control+Digit2")
        ok("moving a unit 1→2: now in group 2 only",await ev(f"{API}.groupOf(U[0])")==2 and await ev(f"{API}.get(1).includes(U[0])")==False and await ev(f"{API}.get(2).length")==1,await ev(f"[{API}.get(1).length,{API}.get(2).length]"))
        await ev("SU=[U[0],U[1]]");await pg.keyboard.press("Control+Digit3")
        ok("assigning units already in other groups moves them (1 and 2 lose them)",await ev(f"{API}.get(3).length")==2 and await ev(f"{API}.get(2).length")==0 and await ev(f"{API}.get(1).length")==4)
        own=await ev(f"(()=>{{const c=new Map();for(let n=1;n<10;n++)for(const e of {API}.get(n))c.set(e,(c.get(e)||0)+1);return Math.max(0,...c.values())}})()")
        ok("no entity is ever in more than one group",own<=1,own)
        # mixed: units + building via shift-click
        hq=await ev("(()=>{const h=B.find(b=>b.type==='hq');return[h.x+h.w/2,h.y+h.w/2,h.w]})()")
        await pg.mouse.move(x0,y0);await pg.mouse.down();await pg.mouse.move(x1,y1,steps=6);await pg.mouse.up()
        hs=await ev(f"(()=>{{const h=B.find(b=>b.type==='hq');return ({SCR})(h.x+2,h.y+2)}})()")
        await pg.keyboard.down("Shift");await pg.mouse.click(hs[0],hs[1]-34);await pg.keyboard.up("Shift")
        ok("shift-click adds the HQ to the unit selection (mixed selection)",await ev("SU.length")==6 and await ev("SB&&SB.type")=='hq',await ev("[SU.length,SB&&SB.type]"))
        await pg.keyboard.press("Control+Digit4");mg=await ev(f"{API}.get(4).map(e=>e.type||e.kind)")
        ok("mixed group 4 holds 6 units + the HQ",len(mg)==7 and mg.count('hq')==1,mg)
        ok("units left groups 1/3 when re-assigned to the mixed group",await ev(f"{API}.get(1).length+{API}.get(3).length")==0)
        await pg.keyboard.press("Escape");await pg.keyboard.press("Digit4")
        ok("recalling the mixed group restores units AND the building",await ev("SU.length")==6 and await ev("SB&&SB.type")=='hq')
        chip=await ev("[...document.querySelectorAll('#cg-bar button')].map(b=>b.innerText.replace(/\\n/g,' '))");print("   chips:",chip)
        # building moves between groups
        await ev("SU=[];SB=B.find(b=>b.type==='hq')");await pg.keyboard.press("Control+Digit5")
        ok("HQ moved from group 4 to group 5",await ev(f"{API}.groupOf(B.find(b=>b.type==='hq'))")==5 and await ev(f"{API}.get(4).length")==6 and await ev(f"{API}.get(5).length")==1)
        # destroyed entities vanish
        await ev("SU=[U[2]];SB=null");await pg.keyboard.press("Control+Digit6")
        pl=await ev("(()=>{const q=[];for(let ty=40;ty<80&&q.length<1;ty+=3)for(let tx=40;tx<80&&q.length<1;tx+=3)if(check('house',tx,ty).ok)q.push([tx,ty]);return q[0]})()")
        hb=await ev(f"(()=>{{const b=place('house',{pl[0]},{pl[1]});b.t0=G.T-100;return b.id}})()");await ev("G.speed=1");await pg.wait_for_timeout(300);await ev("G.speed=0")
        await ev(f"SU=[U[2]];SB=B.find(b=>b.id=={hb});{API}.selectedBuildings()");await pg.keyboard.press("Control+Digit7")
        ok("house + unit stored in group 7",await ev(f"{API}.get(7).length")==2 and await ev(f"{API}.get(6).length")==0)
        await ev(f"hurt(B.find(b=>b.id=={hb}),1e6)");await pg.wait_for_timeout(250)
        ok("destroyed building disappears from its group",await ev(f"{API}.get(7).length")==1,await ev(f"{API}.get(7).map(e=>e.type||e.kind)"))
        await ev("hurt(U[2],1e6)");await pg.wait_for_timeout(250)
        ok("killed unit disappears; group empties",await ev(f"{API}.get(7).length")==0)
        await ev("SU=[];SB=null");await pg.keyboard.press("Digit7");ok("pressing the now-empty group does nothing",await ev("SU.length")==0 and await ev("SB")is None)
        # camera: recall again centres
        await ev("SU=[U[3]];SB=null");await pg.keyboard.press("Control+Digit8");await ev("cam.tx=cam.x=cam.x+1500;cam.ty=cam.y=cam.y+700");await ev("SU=[]")
        await pg.keyboard.press("Digit8");await pg.wait_for_timeout(100);t1=await ev("(()=>{const u=U[3];return Math.hypot(cam.tx-X(u.x,u.y),cam.ty-(Y(u.x,u.y,1)-10))})()")
        ok("recalling an off-screen group moves the camera to it",t1<5,round(t1,1))
        await pg.wait_for_timeout(600);await ev("cam.tx=cam.x=cam.x+60;cam.ty=cam.y=cam.y+30")   # nudge, still on screen
        await pg.keyboard.press("Digit8");t2=await ev("(()=>{const u=U[3];return Math.hypot(cam.tx-X(u.x,u.y),cam.ty-(Y(u.x,u.y,1)-10))})()")
        ok("pressing the already-selected group again centres the camera",t2<5,round(t2,1))
        # chip click
        await ev("SU=[];SB=null");await pg.click('#cg-bar button:has-text("8")');ok("clicking a group chip selects it",await ev("SU.length")==1)
        await pg.screenshot(path="r_t1.png")
        ok("no console errors/warnings",not errs,errs[:3]);await b.close()
    print(f"{sum(R)}/{len(R)} passed (control groups + keys)")
asyncio.run(main())
