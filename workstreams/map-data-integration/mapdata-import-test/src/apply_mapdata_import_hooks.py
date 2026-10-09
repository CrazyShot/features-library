#!/usr/bin/env python3
"""Apply FEATURE: MAPDATA-IMPORT-TEST (id MAPDATA-IMPORT-TEST-1.0.0) to a newer index.html.

usage:  python3 apply_mapdata_import_hooks.py  <in index.html>  <out index.html>

What it does (every step asserts that the anchor text exists EXACTLY ONCE, otherwise it stops and writes nothing):
  1. patches the 8 guarded hooks inside the main game script   (each tagged  /*FEATURE: MAPDATA-IMPORT-TEST hook Hn*/)
  2. inserts part 1 (BOOT) immediately BEFORE the main game <script>   (marker below)
  3. inserts part 2 (UI)   immediately BEFORE </body>
If an anchor changed in the newer game, fix the anchor/hook by hand: the intent of each hook is written next to it.
Every hook is wrapped in `window.BASTION_IMPORT` so, with no import active, the game is byte-for-byte the same behaviour.
"""
import sys,os
here=os.path.dirname(os.path.abspath(__file__))
src,dst=sys.argv[1],sys.argv[2]
s=open(src,encoding='utf-8').read()
assert 'MAPDATA-IMPORT-TEST' not in s,'already applied'
def rep(old,new,why):
    global s
    n=s.count(old)
    assert n==1,f'ANCHOR for {why}: expected exactly 1 match, found {n}:\n  {old[:120]}'
    s=s.replace(old,new)
H=lambda n:f"/*FEATURE: MAPDATA-IMPORT-TEST hook {n}*/"
# H1  map size comes from the MapData (N was the const 112)
rep("const N=112,TW=32,","const N=(window.BASTION_IMPORT&&BASTION_IMPORT.w)||112"+H('H1')+",TW=32,","H1 map size N")
# H2  the procedural dirt-road field is switched off on imported maps (MapData has no roads)
rep("const pf=(x,y)=>cl(1-Math.abs(fb(x*.035+50,y*.035+80,30,3)-.5)/.018);","const pf=(x,y)=>window.BASTION_IMPORT?0:cl(1-Math.abs(fb(x*.035+50,y*.035+80,30,3)-.5)/.018);"+H('H2'),"H2 pf()")
# H3  terrain.grid ground variant tint, one new line inside gc() right after the road blend
rep(" if(l===1){const p=pf(x,y);if(p>0)c=mx(c,PTH,cl(p*2))}\n"," if(l===1){const p=pf(x,y);if(p>0)c=mx(c,PTH,cl(p*2))}\n if(window.BASTION_IMPORT)c=BASTION_IMPORT.ground_(c,x,y);"+H('H3')+"\n","H3 gc() ground variant")
# H4  resF(): stone/iron painting + RES/RESI fill read the MapData node tiles instead of random PATCH blobs
rep("function resF(x,y){let best=0;resT=0;","function resF(x,y){if(window.BASTION_IMPORT){const I=BASTION_IMPORT.resF(x,y);resT=BASTION_IMPORT.rt;return I}"+H('H4')+"let best=0;resT=0;","H4 resF()")
# H5  skip the random deposit placement; PATCH.length must stay truthy so gc() still calls resF()
rep("{const R=mb(7771),groups=[];let tries=0;","{const R=mb(7771),groups=[];let tries=0;if(window.BASTION_IMPORT){tries=1e9;PATCH.push({x:0,y:0,r:0,t:0,s:0})}"+H('H5'),"H5 random deposits")
# H6  exactly one logical tree on each MapData tree tile (original: f*2.4 trees per tile from noise)
rep("for(let n=f>=.36?f*2.4:0;n>0;n--)if(r()<Math.min(1,n))","for(let n=window.BASTION_IMPORT?BASTION_IMPORT.tm[y*N+x]:(f>=.36?f*2.4:0)"+H('H6')+";n>0;n--)if(r()<Math.min(1,n))","H6 tree count per tile")
# H7  gold ore nodes (visual-only) + glows, added before the decor list is sorted
rep("D.sort((a,b)=>a.y-b.y);\n/* TT:","if(window.BASTION_IMPORT)BASTION_IMPORT.decor({add,GLD,X,Y,mb,rock,poly,SS});"+H('H7')+"\nD.sort((a,b)=>a.y-b.y);\n/* TT:","H7 decor/gold")
# H8  HQ at the MapData start position (falls back to pickBase())
rep("function initSurvival(){const s=pickBase();","function initSurvival(){const s=(window.BASTION_IMPORT&&BASTION_IMPORT.hqTL)||pickBase();"+H('H8'),"H8 HQ site")
# parts 1 and 2
p1=open(os.path.join(here,'FEATURE_MAPDATA-IMPORT-TEST-1.0.0_part1_boot.html'),encoding='utf-8').read()
p2=open(os.path.join(here,'FEATURE_MAPDATA-IMPORT-TEST-1.0.0_part2_ui.html'),encoding='utf-8').read()
MAIN="<script>\n/* CAMERA ANGLE:"          # <-- first line of the main game script (anchor)
rep(MAIN,p1+MAIN,"main <script> start (boot block goes right before it)")
i=s.rfind('</body>');assert i>0,'no </body>'
s=s[:i]+'\n'+p2+s[i:]
open(dst,'w',encoding='utf-8').write(s);print('wrote',dst,len(s),'bytes; 8 hooks + 2 parts applied')
