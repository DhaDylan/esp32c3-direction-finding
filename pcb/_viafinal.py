import pcbnew, math
PCB="10.28.25 V2 Wifi PCB.kicad_pcb"
b=pcbnew.LoadBoard(PCB)
nm=pcbnew.FromMM; VM=pcbnew.VECTOR2I; mm=pcbnew.ToMM
NPTH=pcbnew.PAD_ATTRIB_NPTH
TGT={('U3','33'),('C6','1'),('IC1','6'),('U1','2'),('U2','2')}
# single footprint pass: pad pos + netcode (from pad), npth
targets=[]; npth=[]
for f in b.GetFootprints():
    r=f.GetReference()
    for p in f.Pads():
        pp=p.GetPosition(); x,y=mm(pp.x),mm(pp.y)
        if p.GetAttribute()==NPTH:
            bb=p.GetBoundingBox(); npth.append((x,y,max(mm(bb.GetWidth()),mm(bb.GetHeight()))/2))
        if (r,p.GetPadName()) in TGT:
            targets.append((x,y,p.GetNet().GetNetCode(),p.GetNetname()))
# existing vias
vias=[]
for t in b.GetTracks():
    if t.GetClass()=='PCB_VIA':
        pp=t.GetPosition(); vias.append((mm(pp.x),mm(pp.y)))
def ok(x,y):
    if any(math.hypot(x-vx,y-vy)<0.62 for vx,vy in vias): return False
    if any(math.hypot(x-hx,y-hy)<hr+0.45 for hx,hy,hr in npth): return False
    return True
n=0
for (x,y,nc,net) in targets:
    for dx,dy in [(0,0),(0.35,0),(-0.35,0),(0,0.35),(0,-0.35),(0.4,0.4),(-0.4,-0.4)]:
        if ok(x+dx,y+dy):
            v=pcbnew.PCB_VIA(b); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu)
            v.SetPosition(VM(nm(x+dx),nm(y+dy))); v.SetWidth(nm(0.6)); v.SetDrill(nm(0.3))
            v.SetNetCode(nc); b.Add(v); vias.append((x+dx,y+dy)); n+=1; break
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB,b)
print("added",n,"clean via-in-pad (0.6/0.3)")
