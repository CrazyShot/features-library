(()=>{
const u0=U[0],c=comp[cellOf(u0)],hq=B.find(b=>b.type==='hq'),hx=hq.x+hq.w/2,hy=hq.y+hq.w/2;
const okc=(x,y)=>x>=1&&y>=1&&x<N-1&&y<N-1&&walk[y*N+x]&&comp[y*N+x]===c&&!blk[y*N+x]&&!occ[y*N+x];
const nb=(x,y,r)=>{let n=0;for(let j=-r;j<=r;j++)for(let i=-r;i<=r;i++){const a=x+i,b=y+j;if(a<0||b<0||a>=N||b>=N||blk[b*N+a])n++}return n};
const wn=(x,y)=>{let n=0;for(let j=-1;j<=1;j++)for(let i=-1;i<=1;i++)if((i||j)&&okc(x+i,y+j))n++;return n};
const treeRel=(x,y,front)=>{const px=X(x+.5,y+.5),k=x+y+1;let best=null;for(let b=y-4;b<=y+4;b++)for(let a=x-4;a<=x+4;a++){if(a<0||b<0||a>=N||b>=N)continue;const l=TT[b*N+a];if(!l)continue;for(const t of l){const d=(t.fx+t.fy)-k;if(front?(d>.7&&d<3.2):(d<-.7&&d>-3.2)){if(Math.abs(X(t.fx,t.fy)-px)<10){const q=Math.abs(d);if(!best||q<best.q)best={q,t}}}}}return best};
const cand={open:[],edge:[],dense:[],behind:[],front:[]};
for(let y=Math.max(2,hy-38|0);y<Math.min(N-2,hy+38);y++)for(let x=Math.max(2,hx-38|0);x<Math.min(N-2,hx+38);x++){
 if(!okc(x,y)||!fogVis(x+.5,y+.5))continue;const d=Math.hypot(x-hx,y-hy);
 const n3=nb(x,y,3),n1=nb(x,y,1);
 if(n3===0&&d>4)cand.open.push([x,y,d]);
 if(n1>=3&&n1<=5&&wn(x,y)>=3)cand.edge.push([x,y,d]);
 if(n3/49>=.3&&wn(x,y)>=2)cand.dense.push([x,y,d]);
 if(treeRel(x,y,true))cand.behind.push([x,y,d]);      /* a tree stands in FRONT of this tile -> vampire is behind the tree */
 if(treeRel(x,y,false))cand.front.push([x,y,d]);}      /* a tree stands BEHIND this tile -> vampire is in front of the tree */
const out={};for(const k in cand){cand[k].sort((a,b)=>a[2]-b[2]);out[k]={n:cand[k].length,best:cand[k].slice(0,4)}}
return out})()
