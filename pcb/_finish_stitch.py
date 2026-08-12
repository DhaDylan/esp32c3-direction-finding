import pcbnew, math
PCB="10.28.25 V2 Wifi PCB.kicad_pcb"
b=pcbnew.LoadBoard(PCB)
nm=pcbnew.FromMM; VM=pcbnew.VECTOR2I; mm=pcbnew.ToMM
GNDC=b.FindNet("GND").GetNetCode()
fp={f.GetReference():f for f in b.GetFootprints()}

# obstacles: footprint courtyards + antenna keepouts
occ=[]
for f in b.GetFootprints():
    bb=f.GetBoundingBox(False,False)
    occ.append((mm(bb.GetLeft())-0.7,mm(bb.GetTop())-0.7,mm(bb.GetRight())+0.7,mm(bb.GetBottom())+0.7))
for r in ['ANT1','ANT2']:
    c=fp[r].GetPosition(); cx,cy=mm(c.x),mm(c.y)
    occ.append((cx-15,cy-15,cx+15,cy+15))
def blocked(x,y):
    for (x0,y0,x1,y1) in occ:
        if x0<=x<=x1 and y0<=y<=y1: return True
    return False

# existing track segments (F & B) to avoid (point-to-segment distance)
segs=[]
for t in b.GetTracks():
    if t.GetClass()=='PCB_TRACK':
        s=t.GetStart(); e=t.GetEnd()
        segs.append((mm(s.x),mm(s.y),mm(e.x),mm(e.y)))
def near_trace(x,y,clr=0.9):
    for (x1,y1,x2,y2) in segs:
        dx,dy=x2-x1,y2-y1
        L2=dx*dx+dy*dy
        if L2<1e-9:
            d=math.hypot(x-x1,y-y1)
        else:
            t=max(0,min(1,((x-x1)*dx+(y-y1)*dy)/L2))
            d=math.hypot(x-(x1+t*dx),y-(y1+t*dy))
        if d<clr: return True
    return False

# board extent for grid
L,T,R,Bm=7.5,1.6,146.4,120.1
def via(x,y):
    v=pcbnew.PCB_VIA(b)
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu)
    v.SetPosition(VM(nm(x),nm(y)))
    v.SetDrill(nm(0.3)); v.SetWidth(nm(0.6))
    v.SetNetCode(GNDC); b.Add(v)

n=0; x=L+4
while x<R-4:
    y=T+4
    while y<Bm-4:
        if not blocked(x,y) and not near_trace(x,y):
            via(x,y); n+=1
        y+=8.0
    x+=8.0
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB,b)
print("stitching vias added:",n)
