import os
GAME_DIR=os.environ.get("GAME_DIR",".")   # folder that contains the game build named index.html
import asyncio
from playwright.async_api import async_playwright
from rt_common import *
async def main():
    async with async_playwright() as p:
        b,pg,errs=await boot(p);ev=pg.evaluate
        scr=lambda x,y:ev(f"({SCR})({x},{y})")
        hqc=await ev("(()=>{const h=B.find(b=>b.type==='hq');return[h.x+h.w/2,h.y+h.w/2]})()")
        # world: 6 dwarves (existing) + 4 rangers + 5 vampires (3 visible, 1 fogged-on-screen, 1 far) -- game paused so everything is static
        await ev("""(()=>{const hq=B.find(b=>b.type==='hq');for(let i=0;i<4;i++)spawnRanger(hq);
          const at=(dx,dy)=>{const q=nearestWalk((hq.x+hq.w/2+dx)|0,(hq.y+hq.w+dy)|0);return[q[0],q[1]]};
          window.__vamp=[at(-5,6),at(-3,7),at(4,6)].map(p=>{spawnE(p);return E[E.length-1]});
          for(const e of window.__vamp){e.tg=null;e.cd=99}   /* static scenery for a UI test */
          cam.z=cam.tz=.62;cam.x=cam.tx=X(hq.x+hq.w/2,hq.y+hq.w/2+3);cam.y=cam.ty=Y(hq.x+hq.w/2,hq.y+hq.w/2+3,1)+40;let fp=null;
          for(let dx=8;dx<=30&&!fp;dx+=2)for(let dy=-30;dy<=30&&!fp;dy+=2){const x=hq.x+hq.w/2+dx,y=hq.y+hq.w/2+dy;if(x<2||y<2||x>109||y>109||!walk[(y|0)*N+(x|0)])continue;const sx=(X(x,y)-cam.x)*cam.z+W/2,sy=(Y(x,y,1)-14-cam.y)*cam.z+H/2;if(sx>150&&sx<1250&&sy>150&&sy<650&&!fogVis(x,y))fp=[x|0,y|0]}
          spawnE(fp);window.__fog=E[E.length-1];
          const far=nearestWalk(hq.x+1,5);spawnE(far);window.__far=E[E.length-1]})()""")
        await ev("(()=>{cam.z=cam.tz=.62;cam.x=cam.tx=X(%f,%f);cam.y=cam.ty=Y(%f,%f,1)+40})()"%(hqc[0],hqc[1]+3,hqc[0],hqc[1]+3));await pg.wait_for_timeout(600)
        st=await ev("({fogVisible:[...__vamp].map(e=>fogVis(e.x,e.y)),fogHidden:fogVis(__fog.x,__fog.y),farHidden:fogVis(__far.x,__far.y),fogOnScreen:(()=>{const sx=(X(__fog.x,__fog.y)-cam.x)*cam.z+W/2,sy=(Y(__fog.x,__fog.y,1)-cam.y)*cam.z+H/2;return sx>0&&sx<W&&sy>0&&sy<H})()})")
        print("   setup:",st)
        pos=lambda u:scr(u['x'],u['y'])
        async def clickAt(x,y,dbl=False,shift=False):
            if shift:await pg.keyboard.down("Shift")
            (pg.mouse.dblclick if dbl else pg.mouse.click)
            if dbl:await pg.mouse.dblclick(x,y)
            else:await pg.mouse.click(x,y)
            if shift:await pg.keyboard.up("Shift")
            await pg.wait_for_timeout(250)
        async def unit_screen(expr):
            p=await ev(f"(()=>{{const u={expr};return ({SCR})(u.x,u.y)}})()");return p[0],p[1]-14*.62
        # ---------------- double-click selection ----------------
        x,y=await unit_screen("U.find(u=>u.kind==='dwarf')");await ev("SU=[];SB=null");await clickAt(x,y,dbl=True)
        k=await ev("SU.map(u=>u.kind)");ok("double-click a Dwarf Warrior → all nearby Dwarf Warriors (and only them)",len(k)==6 and set(k)=={'dwarf'},k)
        x,y=await unit_screen("U.find(u=>u.kind==='ranger')");await clickAt(x,y,dbl=True)
        k=await ev("SU.map(u=>u.kind)");ok("double-click a Ranger → all Rangers only",len(k)==4 and set(k)=={'ranger'},k)
        await ev("SU=[];SB=null");x,y=await unit_screen("U.find(u=>u.kind==='ranger')");await clickAt(x,y)
        ok("a single click selects only one unit",await ev("SU.length")==1)
        await pg.wait_for_timeout(700);await clickAt(x,y)
        ok("two clicks too far apart in time are NOT a double-click",await ev("SU.length")==1)
        await ev("SU=[];SB=null");x,y=await unit_screen("U.find(u=>u.kind==='dwarf')");await clickAt(x,y,dbl=True)
        await ev("window.__n=SU.length");x2,y2=await unit_screen("U.find(u=>u.kind==='ranger')");await clickAt(x2,y2,dbl=True,shift=True)
        ok("shift+double-click adds the same-type group to the current selection",await ev("SU.length")==10 and await ev("SU.filter(u=>u.kind==='ranger').length")==4)
        # radius: nothing beyond cfg.maxTiles
        await ev("FEATURE_DBLCLICK_SELECT.cfg.maxTiles=0.5;SU=[];SB=null");x,y=await unit_screen("U.find(u=>u.kind==='dwarf')");await clickAt(x,y,dbl=True)
        n=await ev("SU.length");ok("'nearby' is bounded by cfg.maxTiles (0.5 → just the clicked unit/neighbours)",1<=n<6,n);await ev("FEATURE_DBLCLICK_SELECT.cfg.maxTiles=30")
        # off-screen same-type unit is not taken
        await ev("window.__d=spawnDwarf(%f,%f)"%(hqc[0]+40,hqc[1]+35));await ev("SU=[];SB=null");x,y=await unit_screen("U.find(u=>u.kind==='dwarf')");await clickAt(x,y,dbl=True)
        ok("a dwarf far off-screen is not swept in",await ev("SU.length")==6 and not await ev("SU.includes(window.__d)"),await ev("SU.length"))
        # enemies: inspect-only selection with fog respected
        await ev("SU=[];SB=null");vx,vy=await ev("({SCR})(__vamp[0].x,__vamp[0].y)".replace("{SCR}",SCR))
        await pg.mouse.click(vx,vy-14*.62);await pg.wait_for_timeout(250)
        ok("single click on a visible enemy inspects it (not added to SU)",await ev("FEATURE_UNIT_INFO.inspect().length")==1 and await ev("SU.length")==0)
        await pg.mouse.dblclick(vx,vy-14*.62);await pg.wait_for_timeout(300)
        ins=await ev("FEATURE_UNIT_INFO.inspect()");nvis=await ev("__vamp.length")
        exp=await ev("E.filter(e=>!e.dead&&fogVis(e.x,e.y)&&Math.hypot(e.x-__vamp[0].x,e.y-__vamp[0].y)<=30&&(()=>{const sx=(X(e.x,e.y)-cam.x)*cam.z+W/2,sy=(Y(e.x,e.y,1)-14-cam.y)*cam.z+H/2;return sx>=0&&sx<=W&&sy>=0&&sy<=H})()).length")
        ok("double-click a Vampire → exactly the visible, on-screen, nearby Vampires (own + wild ones in view)",len(ins)==exp and exp>=3 and await ev("__vamp.every(v=>FEATURE_UNIT_INFO.inspect().includes(v))"),f"selected {len(ins)}, independently computed {exp}")
        ok("every inspected vampire is currently visible (fog respected)",await ev("FEATURE_UNIT_INFO.inspect().every(e=>fogVis(e.x,e.y))"))
        ok("far hidden vampire not selected",await ev("!FEATURE_UNIT_INFO.inspect().includes(__far)"))
        ok("enemies never enter your selection list (SU) → no command can reach them",await ev("SU.length")==0 and await ev("SU.every(u=>!u.en)"))
        ok("PRECONDITION: the fogged vampire really is on screen and hidden by fog",st["fogOnScreen"] and not st["fogHidden"],st)
        ok("a fogged enemy is excluded even though it is on screen",await ev("!FEATURE_UNIT_INFO.inspect().includes(__fog)"))
        # ---------------- information panel ----------------
        txt=lambda:ev("document.getElementById('pn').innerText.replace(/\\n+/g,' | ')")
        await ev("SU=[];SB=null");x,y=await unit_screen("U.find(u=>u.kind==='dwarf')");await clickAt(x,y);t=await txt();print("   dwarf panel :",t)
        c=await ev("({n:'Dwarf Warrior',hp:DW.hp,dmg:DW.dmg,cd:DW.cd,reach:DW.reach,spd:DW.spd})")
        ok("Dwarf panel: name, HP, attack, range/type, speed, category — all equal the game constants",all(s in t for s in["Dwarf Warrior selected",f"{c['hp']} / {c['hp']}",f"{c['dmg']} damage",f"every {c['cd']} s","Melee · "+str(c['reach'])+" tiles",f"{c['spd']} tiles/s","Melee infantry"]),t[:60])
        x,y=await unit_screen("U.find(u=>u.kind==='ranger')");await clickAt(x,y);t=await txt();print("   ranger panel:",t)
        ok("Ranger panel: 9 damage, ranged, RANGE tiles, SPD",all(s in t for s in["Ranger selected","60 / 60","9 damage","Ranged · "+str(await ev("RANGE"))+" tiles",str(await ev("SPD"))+" tiles/s","Ranged infantry"]))
        await ev("U.find(u=>u.kind==='dwarf').hp=100");x,y=await unit_screen("U.find(u=>u.kind==='dwarf')");await clickAt(x,y);t=await txt();ok("panel shows live damaged HP (100 / 130)","100 / 130" in t)
        await ev("SU=[];SB=null");await pg.mouse.click(vx,vy-14*.62);await pg.wait_for_timeout(300);t=await txt();print("   enemy panel :",t)
        e=await ev("({dmg:__vamp[0].dmg,hp:Math.ceil(__vamp[0].hp),mh:Math.ceil(__vamp[0].mh),reach:REACH,spd:ESPD})")
        ok("Enemy panel: Vampire, HP, damage, melee range, speed, wave/category — real values",all(s in t for s in["Vampire","Enemy — inspect only",f"{e['hp']} / {e['mh']}",f"{e['dmg']} damage","Melee · "+str(e['reach'])+" tiles",f"{e['spd']} tiles/s","Attacker"]),t[:70])
        ok("no invented stats: there is no Armor row (the game has no armor stat)","Armor" not in t and "Defense" not in t)
        await ev("hurt(__vamp[0],12)");await pg.wait_for_timeout(300);t2=await txt();ok("enemy HP updates live when damaged",f"{e['hp']-12} / {e['mh']}" in t2,t2[:90])
        await ev("window.__w=E.find(e=>e.wl);__w.x=__vamp[1].x+2;__w.y=__vamp[1].y;__w.sx=__w.x;__w.sy=__w.y");await pg.wait_for_timeout(300)
        wx,wy=await ev("({SCR})(__w.x,__w.y)".replace("{SCR}",SCR));await ev("SU=[];SB=null");await pg.mouse.click(wx,wy-14*.62);await pg.wait_for_timeout(300);t=await txt();print("   wild panel  :",t[:130])
        ok("wilderness enemy panel shows 'Wilderness group of N' with its own stats (wild dmg 4)","Wilderness group of" in t and "4 damage" in t)
        await pg.screenshot(path="r_enemy_panel.png",clip={"x":0,"y":520,"width":520,"height":330})
        # attack order still works exactly as before (right-click with friendly units selected)
        await ev("SU=[U.find(u=>u.kind==='dwarf')];SB=null");vx,vy=await ev("({SCR})(__vamp[2].x,__vamp[2].y)".replace("{SCR}",SCR));await pg.mouse.click(vx,vy-14*.62,button="right");await pg.wait_for_timeout(200)
        ok("right-click attack order on an enemy still works (host behaviour unchanged)",await ev("SU[0].ord&&SU[0].ord.t===__vamp[2]"))
        # dead enemy leaves the panel
        await ev("SU=[];SB=null");await pg.mouse.click(vx,vy-14*.62);await pg.wait_for_timeout(250);await ev("hurt(__vamp[2],1e6)");await pg.wait_for_timeout(300)
        ok("killing the inspected enemy clears its panel",await ev("FEATURE_UNIT_INFO.inspect().length")==0 and await ev("getComputedStyle(document.getElementById('pn')).display")=='none')
        # mixed panel
        await ev("SU=U.slice(0,3);SB=B.find(b=>b.type==='hq')");await pg.wait_for_timeout(300);t=await txt();ok("mixed selection panel is labelled and shows the units' stats","Mixed selection: 3 units + building" in t and "Dwarf Warrior" in t or "Melee infantry" in t,t[:80])
        ok("no console errors/warnings",not errs,errs[:3]);await b.close()
    print(f"{sum(R)}/{len(R)} passed (double-click + info panel)")
asyncio.run(main())
