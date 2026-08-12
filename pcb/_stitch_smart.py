"""Smart GND stitching: place GND vias on a grid, but ONLY where the F.Cu GND
zone actually fills (so the via isn't dangling) AND the In1 GND plane fills
(so it stitches to the solid plane). Avoids antenna keepouts, footprint
keepout rule-areas, NPTH holes, and existing traces/vias."""
import pcbnew, math, json
PCB="10.28.25 V2 Wifi PCB.kicad_pcb"
b=pcbnew.LoadBoard(PCB)
nm=pcbnew.FromMM; VM=pcbnew.VECTOR2I; mm=pcbnew.ToMM
GND=b.FindNet("GND").GetNetCode()
fp={f.GetReference():f for f in b.GetFootprints()}

# zones
fcu_gnd=[z for z in b.Zones() if z.GetNetname()=='GND' and z.GetLayer()==pcbnew.F_Cu]
in1_gnd=[z for z in b.Zones() if z.GetNetname()=='GND' and z.GetLayer()==pcbnew.In1_Cu]
def in_gnd(x,y):
    pt=VM(nm(x),nm(y))
    f=any(z.HitTestFilledArea(pcbnew.F_Cu,pt) for z in fcu_gnd)
    i=any(z.HitTestFilledArea(pcbnew.In1_Cu,pt) for z in in1_gnd)
    return f and i

# antenna keepouts
ant=[]
for r in ('ANT1','ANT2'):
    c=fp[r].GetPosition(); ant.append((mm(c.x),mm(c.y)))
keeps=json.load(open("_keepouts.json"))

# NPTH + traces + existing vias
npth=[]; segs=[]; vias=[]
NP=pcbnew.PAD_ATTRIB_NPTH
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetAttribute()==NP:
            pp=p.GetPosition(); bb=p.GetBoundingBox()
            npth.append((mm(pp.x),mm(pp.y),max(mm(bb.GetWidth()),mm(bb.GetHeight()))/2))
for t in b.GetTracks():
    if t.GetClass()=='PCB_VIA':
        p=t.GetPosition(); vias.append((mm(p.x),mm(p.y)))
    else:
        s=t.GetStart(); e=t.GetEnd(); segs.append((mm(s.x),mm(s.y),mm(e.x),mm(e.y)))
def sd(x,y,x1,y1,x2,y2):
    dx,dy=x2-x1,y2-y1; L2=dx*dx+dy*dy
    if L2<1e-9: return math.hypot(x-x1,y-y1)
    tt=max(0,min(1,((x-x1)*dx+(y-y1)*dy)/L2)); return math.hypot(x-(x1+tt*dx),y-(y1+tt*dy))
def ok(x,y):
    if not in_gnd(x,y): return False
    for ax,ay in ant:
        if abs(x-ax)<15 and abs(y-ay)<15: return False
    for (kx0,ky0,kx1,ky1,_) in keeps:
        if kx0-0.5<=x<=kx1+0.5 and ky0-0.5<=y<=ky1+0.5: return False
    for (hx,hy,hr) in npth:
        if math.hypot(x-hx,y-hy)<hr+0.6: return False
    for (x1,y1,x2,y2) in segs:
        if sd(x,y,x1,y1,x2,y2)<0.65: return False
    for vx,vy in vias:
        if math.hypot(x-vx,y-vy)<1.2: return False
    return True

L,T,R,Bm=8,3,146,119
n=0; x=L
while x<R:
    y=T
    while y<Bm:
        if ok(x,y):
            v=pcbnew.PCB_VIA(b); v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu)
            v.SetPosition(VM(nm(x),nm(y))); v.SetDrill(nm(0.3)); v.SetWidth(nm(0.6))
            v.SetNetCode(GND); b.Add(v); vias.append((x,y)); n+=1
        y+=6.0
    x+=6.0
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB,b)
print(f"smart GND stitch vias: {n}")
