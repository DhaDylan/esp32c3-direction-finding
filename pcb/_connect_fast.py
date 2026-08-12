"""Fast per-pad plane connection (spatial-bucketed clearance check).
For every SMD pad on GND / Power2: place a via next to it (short stub) tying it
to the inner plane. Short-aware, keepout/NPTH/edge-aware. ~100x faster than the
brute-force version via a 4mm spatial grid over segments and pads."""
import pcbnew, math, json
PCB="10.28.25 V2 Wifi PCB.kicad_pcb"
b=pcbnew.LoadBoard(PCB)
nm=pcbnew.FromMM; VM=pcbnew.VECTOR2I; mm=pcbnew.ToMM
SMD=pcbnew.PAD_ATTRIB_SMD; NP=pcbnew.PAD_ATTRIB_NPTH
QFN={'U3','U4','U5'}
ni=b.GetNetInfo(); NC={}
for c in range(ni.GetNetCount()):
    n=ni.GetNetItem(c)
    if n and n.GetNetname(): NC[n.GetNetname()]=n.GetNetCode()

CELL=4.0
def cell(x,y): return (int(x//CELL),int(y//CELL))
pad_grid={}; seg_grid={}; via_grid={}
npth=[]; targets=[]; centers={}
def gput(grid,x,y,item):
    grid.setdefault(cell(x,y),[]).append(item)
def gnear(grid,x,y):
    cx,cy=cell(x,y); out=[]
    for i in (cx-1,cx,cx+1):
        for j in (cy-1,cy,cy+1):
            out+=grid.get((i,j),())
    return out

for f in b.GetFootprints():
    r=f.GetReference(); cc=f.GetPosition(); centers[r]=(mm(cc.x),mm(cc.y))
    for p in f.Pads():
        pp=p.GetPosition(); x,y=mm(pp.x),mm(pp.y)
        bb=p.GetBoundingBox(); w=mm(bb.GetWidth()); h=mm(bb.GetHeight()); rad=max(w,h)/2
        net=p.GetNetname(); at=p.GetAttribute()
        if at==NP: npth.append((x,y,rad))
        else: gput(pad_grid,x,y,(x,y,rad,net))
        if net in ('GND','/Power2') and at==SMD:
            targets.append((x,y,net,(r if r in QFN and p.GetPadName() in ('17','18','31','32','33') else None),r,p.GetPadName()))
keeps=json.load(open("_keepouts.json"))
for t in b.GetTracks():
    if t.GetClass()=='PCB_VIA':
        p=t.GetPosition(); gput(via_grid,mm(p.x),mm(p.y),(mm(p.x),mm(p.y)))
    else:
        s=t.GetStart(); e=t.GetEnd(); x1,y1,x2,y2=mm(s.x),mm(s.y),mm(e.x),mm(e.y)
        seg=(x1,y1,x2,y2)
        L=math.hypot(x2-x1,y2-y1); steps=max(1,int(L/2)+1)
        for k in range(steps+1):
            t0=k/steps; gput(seg_grid,x1+(x2-x1)*t0,y1+(y2-y1)*t0,seg)

def sd(x,y,x1,y1,x2,y2):
    dx,dy=x2-x1,y2-y1; L2=dx*dx+dy*dy
    if L2<1e-9: return math.hypot(x-x1,y-y1)
    tt=max(0,min(1,((x-x1)*dx+(y-y1)*dy)/L2)); return math.hypot(x-(x1+tt*dx),y-(y1+tt*dy))
def ccw(ax,ay,bx,by,cx,cy): return (cy-ay)*(bx-ax)>(by-ay)*(cx-ax)
def cross(ax,ay,bx,by,cx,cy,dx,dy):
    return ccw(ax,ay,cx,cy,dx,dy)!=ccw(bx,by,cx,cy,dx,dy) and ccw(ax,ay,bx,by,cx,cy)!=ccw(ax,ay,bx,by,dx,dy)
def clear(x,y,net,px,py):
    if x<8.6 or x>145.4 or y<2.6 or y>118.6: return False
    for (qx,qy,qr,qn) in gnear(pad_grid,x,y):
        if qn!=net and math.hypot(x-qx,y-qy)<qr+0.5: return False
    seen=set()
    for s in gnear(seg_grid,x,y):
        if s in seen: continue
        seen.add(s); x1,y1,x2,y2=s
        if sd(x,y,x1,y1,x2,y2)<0.55: return False
        if cross(px,py,x,y,x1,y1,x2,y2): return False
    for (vx,vy) in gnear(via_grid,x,y):
        if math.hypot(x-vx,y-vy)<0.8: return False
    for (kx0,ky0,kx1,ky1,_) in keeps:
        if kx0-0.4<=x<=kx1+0.4 and ky0-0.4<=y<=ky1+0.4: return False
    for (hx,hy,hr) in npth:
        if math.hypot(x-hx,y-hy)<hr+0.5: return False
    return True

addv=[]; adds=[]; fail=[]
for (x,y,net,qfn,ref,pad) in targets:
    if any(math.hypot(x-vx,y-vy)<0.85 for (vx,vy) in gnear(via_grid,x,y)): continue
    if qfn:
        cx,cy=centers[qfn]; dx,dy=x-cx,y-cy; dd=math.hypot(dx,dy) or 1; base=math.atan2(dy/dd,dx/dd)
        cand=[(d,base+math.radians(a)) for d in (2.2,2.6,3.0,3.4) for a in (0,18,-18,36,-36,54,-54)]
    else:
        cand=[(d,math.radians(a)) for d in (0.55,0.7,0.85,1.0,1.15) for a in range(0,360,24)]
    for dist,ang in cand:
        vx=x+dist*math.cos(ang); vy=y+dist*math.sin(ang)
        if clear(vx,vy,net,x,y):
            addv.append((vx,vy,net)); gput(via_grid,vx,vy,(vx,vy)); adds.append((x,y,vx,vy,net)); break
    else:
        fail.append((ref,pad,net,round(x,1),round(y,1)))

for (vx,vy,net) in addv:
    v=pcbnew.PCB_VIA(b); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu)
    v.SetPosition(VM(nm(vx),nm(vy))); v.SetDrill(nm(0.3)); v.SetWidth(nm(0.6)); v.SetNetCode(NC[net]); b.Add(v)
for (x,y,vx,vy,net) in adds:
    t=pcbnew.PCB_TRACK(b); t.SetStart(VM(nm(x),nm(y))); t.SetEnd(VM(nm(vx),nm(vy)))
    t.SetWidth(nm(0.3)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(NC[net]); b.Add(t)
pcbnew.SaveBoard(PCB,b)
print(f"FAST connect: targets {len(targets)} placed {len(addv)} failed {len(fail)}")
for f in fail: print("  FAIL",f)
