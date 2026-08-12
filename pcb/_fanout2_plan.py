import pcbnew, math, json
b=pcbnew.LoadBoard("10.28.25 V2 Wifi PCB.kicad_pcb")
mm=pcbnew.ToMM
SMD=pcbnew.PAD_ATTRIB_SMD; NPTH=pcbnew.PAD_ATTRIB_NPTH
QFN={'U3','U4','U5'}
centers={}
allpads=[]; targets=[]; npth=[]
for f in b.GetFootprints():
    r=f.GetReference()
    c=f.GetPosition(); centers[r]=(mm(c.x),mm(c.y))
    for p in f.Pads():
        pp=p.GetPosition(); x,y=mm(pp.x),mm(pp.y)
        bb=p.GetBoundingBox(); rad=max(mm(bb.GetWidth()),mm(bb.GetHeight()))/2
        net=p.GetNetname(); at=p.GetAttribute()
        allpads.append((x,y,rad,net))
        if at==NPTH: npth.append((x,y,rad))
        if net in ('/Power1','/Power2') and at==SMD:
            qfn = r if (r in QFN and p.GetPadName() in ('17','18','31','32')) else None
            targets.append((x,y,net,qfn,r))
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
def ccw(ax,ay,bx,by,cx,cy): return (cy-ay)*(bx-ax) > (by-ay)*(cx-ax)
def cross(ax,ay,bx,by,cx,cy,dx,dy):  # segments AB, CD intersect?
    return ccw(ax,ay,cx,cy,dx,dy)!=ccw(bx,by,cx,cy,dx,dy) and ccw(ax,ay,bx,by,cx,cy)!=ccw(ax,ay,bx,by,dx,dy)
def clear(x,y,net,px0=None,py0=None):
    for (px,py,pr,pn) in allpads:
        if pn!=net and math.hypot(x-px,y-py)<pr+0.5: return False
    for (x1,y1,x2,y2) in segs:
        if sd(x,y,x1,y1,x2,y2)<0.55: return False
        # stub (pad->via) must not cross a trace
        if px0 is not None and cross(px0,py0,x,y,x1,y1,x2,y2): return False
    for v in vias:
        if math.hypot(x-v[0],y-v[1])<0.78: return False
    for (kx0,ky0,kx1,ky1,_) in keeps:
        if kx0-0.4<=x<=kx1+0.4 and ky0-0.4<=y<=ky1+0.4: return False
    for (hx,hy,hr) in npth:
        if math.hypot(x-hx,y-hy)<hr+0.5: return False
    return True
pv=[]; ps=[]
for (x,y,net,qfn,ref) in targets:
    if any(math.hypot(x-v[0],y-v[1])<0.85 for v in vias): continue
    done=False
    if qfn:
        cx,cy=centers[qfn]; dx,dy=x-cx,y-cy; dd=math.hypot(dx,dy) or 1
        base=math.atan2(dy/dd,dx/dd)
        cand=[(d,base+math.radians(a)) for d in (2.4,2.8,3.2,3.6) for a in (0,20,-20,40,-40)]
    else:
        cand=[(d,math.radians(a)) for d in (0.55,0.7,0.9,1.1) for a in range(0,360,30)]
    for dist,ang in cand:
        vx=x+dist*math.cos(ang); vy=y+dist*math.sin(ang)
        if clear(vx,vy,net,x,y):
            pv.append([round(vx,3),round(vy,3),net]); vias.append([vx,vy])
            ps.append([round(x,3),round(y,3),round(vx,3),round(vy,3),net]); done=True; break
    # (if none clear, leave unconnected)
json.dump({"vias":pv,"stubs":ps},open("_fanout.json","w"))
print(f"targets {len(targets)}; planned {len(pv)} clean fanout vias (keepout/NPTH/QFN-aware)")
