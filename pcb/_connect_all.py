"""Single-pass plane connection: for every SMD pad on GND / Power1 / Power2,
place ONE through-via next to the pad (with a short stub) tying it to the
inner plane. Short-aware (no other-net pad/trace), keepout/NPTH/edge-aware.
GND pads also de-island the fragmented F.Cu pour. Replaces grid stitching."""
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

centers={}; allpads=[]; targets=[]; npth=[]
for f in b.GetFootprints():
    r=f.GetReference(); cc=f.GetPosition(); centers[r]=(mm(cc.x),mm(cc.y))
    for p in f.Pads():
        pp=p.GetPosition(); x,y=mm(pp.x),mm(pp.y)
        bb=p.GetBoundingBox(); rad=max(mm(bb.GetWidth()),mm(bb.GetHeight()))/2
        net=p.GetNetname(); at=p.GetAttribute()
        allpads.append((x,y,rad,net))
        if at==NP: npth.append((x,y,rad))
        if net in ('GND','/Power2') and at==SMD:
            qfn = r if (r in QFN and p.GetPadName() in ('17','18','31','32','33')) else None
            targets.append((x,y,net,qfn,r,rad,p.GetPadName()))
keeps=json.load(open("_keepouts.json"))
segs=[]; vias=[]
for t in b.GetTracks():
    if t.GetClass()=='PCB_VIA':
        p=t.GetPosition(); vias.append([mm(p.x),mm(p.y)])
    else:
        s=t.GetStart(); e=t.GetEnd(); segs.append((mm(s.x),mm(s.y),mm(e.x),mm(e.y)))
def sd(x,y,x1,y1,x2,y2):
    dx,dy=x2-x1,y2-y1; L2=dx*dx+dy*dy
    if L2<1e-9: return math.hypot(x-x1,y-y1)
    tt=max(0,min(1,((x-x1)*dx+(y-y1)*dy)/L2)); return math.hypot(x-(x1+tt*dx),y-(y1+tt*dy))
def ccw(ax,ay,bx,by,cx,cy): return (cy-ay)*(bx-ax)>(by-ay)*(cx-ax)
def cross(ax,ay,bx,by,cx,cy,dx,dy):
    return ccw(ax,ay,cx,cy,dx,dy)!=ccw(bx,by,cx,cy,dx,dy) and ccw(ax,ay,bx,by,cx,cy)!=ccw(ax,ay,bx,by,dx,dy)
def clear(x,y,net,px,py):
    if x<8.6 or x>145.4 or y<2.6 or y>118.6: return False     # board edge
    for (qx,qy,qr,qn) in allpads:
        if qn!=net and math.hypot(x-qx,y-qy)<qr+0.5: return False
    for (x1,y1,x2,y2) in segs:
        if sd(x,y,x1,y1,x2,y2)<0.55: return False
        if cross(px,py,x,y,x1,y1,x2,y2): return False
    for v in vias:
        if math.hypot(x-v[0],y-v[1])<0.8: return False
    for (kx0,ky0,kx1,ky1,_) in keeps:
        if kx0-0.4<=x<=kx1+0.4 and ky0-0.4<=y<=ky1+0.4: return False
    for (hx,hy,hr) in npth:
        if math.hypot(x-hx,y-hy)<hr+0.5: return False
    return True

addv=[]; adds=[]; fail=[]
for (x,y,net,qfn,ref,rad,pad) in targets:
    if any(math.hypot(x-v[0],y-v[1])<0.85 for v in vias): continue   # already has a via
    if qfn:                                   # QFN power/gnd pin: fan outward from chip center
        cx,cy=centers[qfn]; dx,dy=x-cx,y-cy; dd=math.hypot(dx,dy) or 1
        base=math.atan2(dy/dd,dx/dd)
        cand=[(d,base+math.radians(a)) for d in (2.2,2.6,3.0,3.4) for a in (0,18,-18,36,-36,54,-54)]
    else:
        cand=[(d,math.radians(a)) for d in (0.55,0.7,0.85,1.0,1.15) for a in range(0,360,24)]
    placed=False
    for dist,ang in cand:
        vx=x+dist*math.cos(ang); vy=y+dist*math.sin(ang)
        if clear(vx,vy,net,x,y):
            addv.append((vx,vy,net)); vias.append([vx,vy]); adds.append((x,y,vx,vy,net)); placed=True; break
    if not placed: fail.append((ref,pad,net,round(x,1),round(y,1)))

for (vx,vy,net) in addv:
    v=pcbnew.PCB_VIA(b); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu)
    v.SetPosition(VM(nm(vx),nm(vy))); v.SetDrill(nm(0.3)); v.SetWidth(nm(0.6)); v.SetNetCode(NC[net]); b.Add(v)
for (x,y,vx,vy,net) in adds:
    t=pcbnew.PCB_TRACK(b); t.SetStart(VM(nm(x),nm(y))); t.SetEnd(VM(nm(vx),nm(vy)))
    t.SetWidth(nm(0.3)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(NC[net]); b.Add(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB,b)
print(f"targets {len(targets)}  placed {len(addv)}  failed {len(fail)}")
for f in fail: print("  FAIL", f)
