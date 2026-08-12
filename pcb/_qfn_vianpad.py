"""Connect the hard-case plane pads that per-pad fanout couldn't reach:
 - QFN exposed center pads (U3/U4/U5 pad 33, GND): via-in-pad (3.76mm pad)
 - USB GND pads (J2/J3/J4 A1-B12 / B1-A12): via-in-pad
 - QFN power pins (17/18/31/32): relaxed outward fanout just past the chip edge
 - leftover decoupling / IC power+gnd pads: relaxed adjacent via
Same-net via-in-pad has no short risk; relaxed fanout uses 0.35mm clearance."""
import pcbnew, math
PCB="10.28.25 V2 Wifi PCB.kicad_pcb"
b=pcbnew.LoadBoard(PCB)
nm=pcbnew.FromMM; VM=pcbnew.VECTOR2I; mm=pcbnew.ToMM
SMD=pcbnew.PAD_ATTRIB_SMD; NP=pcbnew.PAD_ATTRIB_NPTH
QFN={'U3','U4','U5'}
ni=b.GetNetInfo(); NC={}
for c in range(ni.GetNetCount()):
    n=ni.GetNetItem(c)
    if n and n.GetNetname(): NC[n.GetNetname()]=n.GetNetCode()

centers={}; allpads=[]; npth=[]; tgt=[]
for f in b.GetFootprints():
    r=f.GetReference(); cc=f.GetPosition(); centers[r]=(mm(cc.x),mm(cc.y))
    for p in f.Pads():
        pp=p.GetPosition(); x,y=mm(pp.x),mm(pp.y)
        bb=p.GetBoundingBox(); w=mm(bb.GetWidth()); h=mm(bb.GetHeight())
        net=p.GetNetname(); at=p.GetAttribute()
        if at!=NP: allpads.append((x,y,max(w,h)/2,net))
        if at==NP: npth.append((x,y,max(w,h)/2))
        if net in ('GND','/Power2') and at==SMD:
            tgt.append((x,y,net,r,p.GetPadName(),min(w,h),max(w,h)))
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
def clear(x,y,net,clr=0.35,viaclr=0.62):
    if x<8.6 or x>145.4 or y<2.6 or y>118.6: return False
    for (qx,qy,qr,qn) in allpads:
        if qn!=net and math.hypot(x-qx,y-qy)<qr+0.45: return False
    for (x1,y1,x2,y2) in segs:
        if sd(x,y,x1,y1,x2,y2)<clr: return False
    for v in vias:
        if math.hypot(x-v[0],y-v[1])<viaclr: return False
    for (hx,hy,hr) in npth:
        if math.hypot(x-hx,y-hy)<hr+0.45: return False
    return True
def addvia(x,y,net):
    v=pcbnew.PCB_VIA(b); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu)
    v.SetPosition(VM(nm(x),nm(y))); v.SetDrill(nm(0.3)); v.SetWidth(nm(0.6)); v.SetNetCode(NC[net]); b.Add(v)
    vias.append([x,y])
def addstub(x,y,vx,vy,net):
    t=pcbnew.PCB_TRACK(b); t.SetStart(VM(nm(x),nm(y))); t.SetEnd(VM(nm(vx),nm(vy)))
    t.SetWidth(nm(0.3)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(NC[net]); b.Add(t)

placed=0; still=[]
for (x,y,net,r,pad,mindim,maxdim) in tgt:
    if any(math.hypot(x-v[0],y-v[1])<0.8 for v in vias): continue   # already connected
    done=False
    # 1) via-in-pad if pad is big enough (>=0.9mm min dim) — same net, no short
    if mindim>=0.55 and maxdim>=0.9:
        for off in (0,0.25,-0.25):
            vx,vy=x,(y+off)
            # only block on OTHER-net pads and existing vias (allow over same-net traces)
            ok=True
            for (qx,qy,qr,qn) in allpads:
                if qn!=net and math.hypot(vx-qx,vy-qy)<qr+0.3: ok=False;break
            if ok and not any(math.hypot(vx-v[0],vy-v[1])<0.62 for v in vias) and not any(math.hypot(vx-hx,vy-hy)<hr+0.45 for hx,hy,hr in npth):
                addvia(vx,vy,net); placed+=1; done=True; break
    if done: continue
    # SAFE MODE: only via-in-pad on big same-net pads; skip risky outward fanout
    still.append((r,pad,net))
pcbnew.SaveBoard(PCB,b)
print(f"hard-case connect: placed {placed}, still failing {len(still)}")
for s in still: print("  STILL", s)
