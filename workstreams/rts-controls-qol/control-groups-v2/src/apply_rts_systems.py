#!/usr/bin/env python3
"""Apply the RTS systems (CONTROL-GROUPS-V2, DOUBLE-CLICK-SELECT, UNIT-INFO-PANEL, BUILDING-REPAIR) to a newer index.html.

usage: python3 apply_rts_systems.py <in index.html> <out index.html>

Every anchor must match EXACTLY ONCE or nothing is written.  Host edits (all are removals / text, no logic added to the host):
  E1  remove the 1/2/3 game-speed keys from the host keydown handler           (1-9 are control groups now; speed = +/- , pause = Space)
  E2  remove 'Equal' (+) from the zoom-in key                                    (+ is game speed now; zoom stays on Q and the wheel)
  E3  remove 'Minus' (-) from the zoom-out key                                   (- is game speed now; zoom stays on E and the wheel)
  E4  help text in the #hud panel
  E5  delete the old FEATURE: CONTROL GROUPS block (CTRLGROUPS-1.0.0) if present - CONTROL-GROUPS-V2 replaces it
Then the four feature files (found anywhere under workstreams/) are inserted before </body> in the order that matters for the clickSel/uiUpdate wrapper chain:
  CONTROL-GROUPS-V2, UNIT-INFO-PANEL, DOUBLE-CLICK-SELECT, BUILDING-REPAIR.
"""
import sys,os,re
here=os.path.dirname(os.path.abspath(__file__));src,dst=sys.argv[1],sys.argv[2]
s=open(src,encoding='utf-8').read()
assert 'CTRLGROUPS-2.0.0' not in s,'already applied'
def rep(old,new,why):
    global s
    n=s.count(old);assert n==1,f'ANCHOR {why}: expected 1 match, found {n}: {old[:100]}'
    s=s.replace(old,new)
rep("else if(!e.shiftKey&&/^Digit[1-3]$/.test(e.code))setSpeed(+e.code[5])}","/*FEATURE: CONTROL-GROUPS-V2 host edit E1: 1/2/3 speed keys removed*/}","E1 speed keys")
rep("if(e.code==='KeyQ'||e.code==='Equal')zoomAt(W/2,H/2,1.3)","if(e.code==='KeyQ'/*E2*/)zoomAt(W/2,H/2,1.3)","E2 zoom in")
rep("if(e.code==='KeyE'||e.code==='Minus')zoomAt(W/2,H/2,1/1.3)","if(e.code==='KeyE'/*E3*/)zoomAt(W/2,H/2,1/1.3)","E3 zoom out")
rep("Left-click or drag-box — select · Right-click — move / attack · F — attack-move · X — stop<br>Shift+1–9 — build · Space — pause · 1 / 2 / 3 — speed<br>",
    "Left-click or drag-box — select · double-click — select same type · Right-click — move / attack · F — attack-move · X — stop<br>1–9 — control groups (Ctrl+1–9 assigns) · Shift+1–9 — build · Space — pause · + / − — game speed<br>","E4 help text")
m=re.search(r"<!-- ===== FEATURE: CONTROL GROUPS START \(id: CTRLGROUPS-1\.0\.0\).*?<!-- ===== FEATURE: CONTROL GROUPS END \(id: CTRLGROUPS-1\.0\.0\) ===== -->\n?",s,re.S)
if m:s=s[:m.start()]+s[m.end():]
else:print('note: no CTRLGROUPS-1.0.0 block found (fine)')
import glob
def find(fn):
    root=os.path.abspath(os.path.join(here,'..','..','..','..'))   # .../workstreams/<ws>/<slug>/src -> repo root
    hits=glob.glob(os.path.join(root,'workstreams','**',fn),recursive=True)
    assert len(hits)==1,f'{fn}: expected exactly one copy in the library, found {len(hits)}'
    return hits[0]
parts=''.join(open(find(f),encoding='utf-8').read()+'\n' for f in('FEATURE_CONTROL-GROUPS-V2.html','FEATURE_UNIT-INFO-PANEL.html','FEATURE_DOUBLE-CLICK-SELECT.html','FEATURE_BUILDING-REPAIR.html'))
i=s.rfind('</body>');assert i>0
s=s[:i]+'\n'+parts+s[i:]
open(dst,'w',encoding='utf-8').write(s);print('wrote',dst,len(s))
