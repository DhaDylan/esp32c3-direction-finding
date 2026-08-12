import pcbnew, math, json
b=pcbnew.LoadBoard("10.28.25 V2 Wifi PCB.kicad_pcb")
mm=pcbnew.ToMM
NPTH=pcbnew.PAD_ATTRIB_NPTH
# targets: (ref,pad) -> via-in-pad (GND/Power) or outward (QFN power pins)
VIA_IN=[('C36','2'),('J3','A6'),('J3','B6'),('J4','B6'),('U1','2'),('U2','2'),('U3','33'),('C6','1'),('IC1','6')]
QFN_OUT=[('U3','18'),('U3','31')]
allpads=[]; npth=[]; tpos={}; ucenter=None
for f in b.GetFootprints():
    r=f.GetReference()
    if r=='U3': ucenter=(mm(f.GetPosition().x),mm(f.GetPosition().y))
    for p in f.Pads():
        pp=p.GetPosition(); x,y=mm(pp.x),mm(pp.y)
        bb=p.GetBoundingBox(); w=mm(bb.GetWidth()); h=mm(bb.GetHeight())
        net=p.GetNetname()
        allpads.append((x,y,max(w,h)/2,net))
        if p.GetAttribute()==NPTH: npth.append((x,y,max(w,h)/2))
        tpos[(r,p.GetPadName())]=(x,y,net,w,h)
keeps=json.load(open("_keepouts.json"))
segs=[];vias=[]
for t in b.GetTracks():
    if t.GetClass()=='PCB_VIA':
        p=t.GetPosition(); vias.append((mm(p.x),mm(p.y)))
    else:
        s=t.GetStart();e=t.GetEnd(); segs.append((mm(s.x),mm(s.y),mm(e.x),mm(e.y)))
def sd(x,y,x1,y1,x2,y2):
    dx,dy=x2-x1,y2-y1;L2=dx*dx+dy*dy
    if L2<1e-9: return math.hypot(x-x1,y-y1)
    tt=max(0,min(1,((x-x1)*dx+(y-y1)*dy)/L2)); return math.hypot(x-(x1+tt*dx),y-(y1+tt*dy))
def clear(x,y,net,vr):
    for (px,py,pr,pn) in allpads:
        if pn!=net and math.hypot(x-px,y-py)<pr+vr+0.13: return False
    for (x1,y1,x2,y2) in segs:
        if sd(x,y,x1,y1,x2,y2)<vr+0.16: return False
    for v in vias:
        if math.hypot(x-v[0],y-v[1])<vr+0.35: return False
    for (hx,hy,hr) in npth:
        if math.hypot(x-hx,y-hy)<hr+vr+0.1: return False
    for (kx0,ky0,kx1,ky1,_) in keeps:
        if kx0-0.3<=x<=kx1+0.3 and ky0-0.3<=y<=ky1+0.3: return False
    return True
pv=[]
# via-in-pad (0.45mm via), only for pads >=1.0mm so the via sits inside cleanly
for (r,pad) in VIA_IN:
    if (r,pad) not in tpos: continue
    x,y,net,w,h=tpos[(r,pad)]
    if min(w,h)<0.95: continue   # too small for a 0.45 via-in-pad; skip
    vr=0.225
    for dx,dy in [(0,0),(0.2,0),(-0.2,0),(0,0.2),(0,-0.2),(0.2,0.2),(-0.2,-0.2)]:
        if clear(x+dx,y+dy,net,vr):
            pv.append([round(x+dx,3),round(y+dy,3),net,0.45]); vias.append((x+dx,y+dy)); break
# QFN outward
for (r,pad) in QFN_OUT:
    if (r,pad) not in tpos: continue
    x,y,net,w,h=tpos[(r,pad)]; cx,cy=ucenter
    dd=math.hypot(x-cx,y-cy) or 1; base=math.atan2((y-cy)/dd,(x-cx)/dd)
    for dist in (2.4,2.8,3.2):
        ok=False
        for a in (0,20,-20,40,-40):
            ang=base+math.radians(a); vx=x+dist*math.cos(ang); vy=y+dist*math.sin(ang)
            # stub must not cross trace
            cross=False
            for (x1,y1,x2,y2) in segs:
                def ccw(ax,ay,bx,by,cx2,cy2): return (cy2-ay)*(bx-ax)>(by-ay)*(cx2-ax)
                if ccw(x,y,x1,y1,x2,y2)!=ccw(vx,vy,x1,y1,x2,y2) and ccw(x,y,vx,vy,x1,y1)!=ccw(x,y,vx,vy,x2,y2): cross=True;break
            if not cross and clear(vx,vy,net,0.3):
                pv.append([round(vx,3),round(vy,3),net,0.6]); vias.append((vx,vy))
                pv.append(['STUB',round(x,3),round(y,3),round(vx,3),round(vy,3),net]); ok=True;break
        if ok: break
json.dump({"vias":pv},open("_connect.json","w"))
print("planned",len([v for v in pv if v[0]!='STUB']),"vias")
