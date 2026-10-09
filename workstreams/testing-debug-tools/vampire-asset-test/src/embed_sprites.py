#!/usr/bin/env python3
"""Re-embed the (private) vampire sprites into the feature block.
usage: python3 embed_sprites.py <front.png> <back.png> <out FEATURE_VAMPIRE-ASSET-TEST-1.0.0.html>
The sprite PNGs are NOT committed to this public library; keep them in the private main-game repository."""
import sys,base64,os
here=os.path.dirname(os.path.abspath(__file__))
t=open(os.path.join(here,'FEATURE_VAMPIRE-ASSET-TEST-1.0.0.template.html'),encoding='utf-8').read()
b=lambda p:base64.b64encode(open(p,'rb').read()).decode()
assert '@@FRONT_PNG_BASE64@@' in t and '@@BACK_PNG_BASE64@@' in t
open(sys.argv[3],'w',encoding='utf-8').write(t.replace('@@FRONT_PNG_BASE64@@',b(sys.argv[1])).replace('@@BACK_PNG_BASE64@@',b(sys.argv[2])))
print('wrote',sys.argv[3])
