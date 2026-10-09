import os
GAME_DIR=os.environ.get("GAME_DIR",".")   # folder that contains the game build named index.html
import asyncio,json,sys,base64,io,time
import numpy as np
from PIL import Image,ImageDraw
from playwright.async_api import async_playwright
URL=sys.argv[1];TAG=sys.argv[2];CROP=int(sys.argv[3]) if len(sys.argv)>3 else 0
full=json.load(open(os.environ.get("MAPDATA_JSON","bastion-map-256x256-bastion-001.json")))
W0=full['width']
if CROP:
    x0=y0=(W0-CROP)//2;N=CROP
    tr=[(t['x']-x0,t['y']-y0) for t in full['trees'] if x0<=t['x']<x0+N and y0<=t['y']<y0+N]
    ore=[(r['x']-x0,r['y']-y0) for r in full['resources'] if r['type'] in(1,2) and x0<=r['x']<x0+N and y0<=r['y']<y0+N]
else:
    N=W0;tr=[(t['x'],t['y']) for t in full['trees']];ore=[(r['x'],r['y']) for r in full['resources'] if r['type'] in(1,2)]
TW,TH,OX,OY=32,24,N*32,150;WW,WH=2*N*TW,2*N*TH+OY+60;SC=8
iso=lambda x,y:(((x-y)*TW+OX)/SC,((x+y)*TH+OY)/SC)
def ref(tiles,wh=None):
    im=Image.new('L',(wh[1],wh[0]) if wh else (WW//SC+3,WH//SC+3),0);dr=ImageDraw.Draw(im)
    for x,y in tiles:dr.polygon([iso(x,y),iso(x+1,y),iso(x+1,y+1),iso(x,y+1)],fill=255)
    return np.asarray(im).astype(float)/255
JS="""(()=>{const s=1/8,mkc=()=>{const c=document.createElement('canvas');c.width=Math.ceil(WW*s)+3;c.height=Math.ceil(WH*s)+3;const q=c.getContext('2d');q.imageSmoothingEnabled=true;q.imageSmoothingQuality='high';q.fillStyle='#000';q.fillRect(0,0,c.width,c.height);return[c,q]};
 const comp=(fn)=>{const[c,q]=mkc();for(let j=0;j<NQ;j++)for(let i=0;i<NP;i++){const o=fn(i,j);q.drawImage(o.cv,o.x*s,o.y*s,S*s,S*s)}return c.toDataURL('image/png')};
 const A=comp((i,j)=>render(i,j,1.0001));
 const saved=D.slice(),keep=D.filter(e=>!e.sp.tree);D.length=0;for(const e of keep)D.push(e);const B=comp((i,j)=>render(i,j,1.0001));D.length=0;for(const e of saved)D.push(e);
 const rf=BASTION_IMPORT.resF;BASTION_IMPORT.resF=function(){this.rt=0;return 0};const C=comp((i,j)=>render(i,j,1.0001));BASTION_IMPORT.resF=rf;
 return[A,B,C]})()"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=["--use-gl=swiftshader","--enable-unsafe-swiftshader"])
        pg=await b.new_page(viewport={"width":1400,"height":850});errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto("file://"+GAME_DIR+"/"+URL)
        for i in range(600):
            await pg.wait_for_timeout(500)
            if await pg.evaluate("typeof ready!=='undefined'&&ready===1"):break
        assert await pg.evaluate("N")==N,(await pg.evaluate("N"),N)
        out=await pg.evaluate(JS);await b.close()
    im=[np.asarray(Image.open(io.BytesIO(base64.b64decode(u.split(',')[1]))).convert('RGB')).astype(float) for u in out]
    A,B,C=im;tdiff=np.abs(A-B).sum(2)>30;odiff=np.abs(A-C).sum(2)>24
    h,w=tdiff.shape;rt=ref(tr,(h,w));ro=ref(ore,(h,w))
    ys,xs=np.indices((h,w));inside=(np.abs(xs-OX/SC)/(N*TW/SC)+np.abs(ys-(OY+N*TH)/SC)/(N*TH/SC))<0.98
    def corr(a,b):a=a[inside].astype(float);b=b[inside].astype(float);return float(np.corrcoef(a,b)[0,1])
    print(f"[{TAG}] N={N} errors={errs or 'none'}  tree-pixels={tdiff.sum()}  ore-pixels={odiff.sum()}")
    print("  TREES: corr(game tree pixels, reference tree tiles), best vertical offset for canopy overhang:")
    sh=lambda a,dx,dy:np.roll(np.roll(a,dy,0),dx,1)
    best=max(((corr(tdiff,sh(rt,0,-dy)),dy) for dy in range(0,16)));print(f"    identity (canopy shifted up {best[1]} px@1/8): r = {best[0]:+.3f}")
    for name,a in(('flip horizontal',np.fliplr(rt)),('flip vertical',np.flipud(rt)),('transpose x<->y (mirror in iso)',np.fliplr(rt))):
        bb=max(((corr(tdiff,sh(a,0,-dy)),dy) for dy in range(0,16)));print(f"    {name:34s} r = {bb[0]:+.3f}")
    for dx in(-6,6):
        bb=max(((corr(tdiff,sh(rt,dx,-dy)),dy) for dy in range(0,16)));print(f"    shifted {dx*SC:+d}px horizontally ({dx:+d}@1/8)   r = {bb[0]:+.3f}")
    print("  ORE GROUND: corr(game ore-ground pixels, reference stone/iron tiles):")
    print(f"    identity                            r = {corr(odiff,ro):+.3f}")
    for name,a in(('flip horizontal',np.fliplr(ro)),('flip vertical',np.flipud(ro))):print(f"    {name:34s} r = {corr(odiff,a):+.3f}")
    for dx,dy in((3,0),(-3,0),(0,3),(0,-3)):print(f"    shifted {dx*SC:+d},{dy*SC:+d}px                    r = {corr(odiff,sh(ro,dx,dy)):+.3f}")
    # centroid offsets (pixels @1/8 -> tiles): where is the game's ore ground relative to the reference?
    def cen(m):yy,xx=np.nonzero(m&inside);return xx.mean(),yy.mean()
    gx,gy=cen(odiff);rx,ry=cen(ro>.5);print(f"  ore centroid offset game-ref: dx={ (gx-rx)*SC:+.1f}px dy={(gy-ry)*SC:+.1f}px (world px; 1 tile = {TW}x{TH})")
    np.savez_compressed(f'{TAG}_masks.npz',tdiff=tdiff,odiff=odiff,rt=rt,ro=ro)
    Image.fromarray((tdiff*255).astype(np.uint8)).save(f"{TAG}_gametrees.png");Image.fromarray((rt*255).astype(np.uint8)).save(f"{TAG}_reftrees.png")
asyncio.run(main())
