import pcbnew, re, math
from collections import defaultdict, Counter

PCB="10.28.25 V2 Wifi PCB.kicad_pcb"
b=pcbnew.LoadBoard(PCB)
fp={f.GetReference():f for f in b.GetFootprints()}
VM=pcbnew.VECTOR2I
def nm(x): return pcbnew.FromMM(x)
def mm(x): return pcbnew.ToMM(x)

# ---- component size: prefer courtyard extent, else pad bbox + margin ----
def size_mm(ref):
    f=fp[ref]
    try:
        cy=f.GetCourtyard(pcbnew.F_CrtYd)
        if cy and cy.OutlineCount()>0:
            bb=cy.BBox()
            return mm(bb.GetWidth()), mm(bb.GetHeight())
    except Exception:
        pass
    pads=list(f.Pads())
    if not pads:
        bb=f.GetBoundingBox(False,False); return mm(bb.GetWidth()),mm(bb.GetHeight())
    xs=[];ys=[]
    for p in pads:
        bb=p.GetBoundingBox()
        xs+=[mm(bb.GetLeft()),mm(bb.GetRight())]; ys+=[mm(bb.GetTop()),mm(bb.GetBottom())]
    return (max(xs)-min(xs))+1.0, (max(ys)-min(ys))+1.0

placed_boxes=[]  # list of (x0,y0,x1,y1) mm
def collide(x0,y0,x1,y1):
    for (a0,b0,a1,b1) in placed_boxes:
        if not (x1<=a0 or x0>=a1 or y1<=b0 or y0>=b1):
            return True
    return False

def place(ref,cx,cy,rot=0,flip=False,clear=0.9,register=True):
    f=fp[ref]
    if flip and not f.IsFlipped(): f.Flip(VM(nm(cx),nm(cy)),False)
    f.SetOrientationDegrees(rot)
    f.SetPosition(VM(nm(cx),nm(cy)))
    if register:
        w,h=size_mm(ref)
        placed_boxes.append((cx-w/2-clear, cy-h/2-clear, cx+w/2+clear, cy+h/2+clear))

# ===================== MAJOR ANCHORS (center x,y,rot) =====================
# Receiver/Hub columns (left->right): U5(Rx2), U4(Rx1), U3(Hub). Shifted right
# to leave a left-edge column for the power section (USB owns the bottom edge).
CX5,CX4,CX3 = 52.0, 90.0, 128.0
# Antennas on top edge, lambda/2 = 62.5mm spacing (per user)
place('ANT2', CX5, 20.0, 0)
place('ANT1', CX5+62.5, 20.0, 0)
# RF switches below each antenna (U2->Rx2 chain, U1->Rx1 chain)
place('U2', CX5, 44.0, 0)
place('U1', CX4, 44.0, 0)
# Receivers below switches
place('U5', CX5, 62.0, 0)     # Rx2
place('U4', CX4, 62.0, 0)     # Rx1
# Hub to the right of receivers
place('U3', CX3, 62.0, 0)
# Clock oscillator + buffer, centered under the 3 ESP row (equidistant in x)
place('IC1', CX4, 84.0, 0)    # buffer (centroid of U3/U4/U5 = 90)
place('Y1', CX4-15, 84.0, 0)  # 40MHz osc, left of buffer
# USB-C connectors on bottom edge (J2->U3, J3->U4, J4->U5)
place('J4', CX5, 108.0, 0)
place('J3', CX4, 108.0, 0)
place('J2', CX3, 108.0, 0)
# USB ESD ICs between connector and ESP
place('IC4', CX5, 96.0, 0)
place('IC3', CX4, 96.0, 0)
place('IC2', CX3, 96.0, 0)
# Power section: LEFT-edge column (barrel jack on left edge, regulators stacked).
# Kept away from the antennas (top) per RF-isolation constraint.
place('J1', 15.0, 58.0, 0)     # barrel jack, left edge
place('PS1', 16.0, 80.0, 0)    # -> /Power2 (receivers)
place('PS2', 16.0, 98.0, 0)    # -> /Power1 (hub)
place('R11', 30.0, 64.0, 90)   # 24V input resistor

# Explicit homes for GND-only / weakly-connected parts so nothing floats
STRAY={'C3':'U3','C7':'U3','C8':'U3','C9':'U3','C10':'U3','C11':'U3','C15':'U3','C18':'U3',
       'C24':'U4','C36':'U5','C25':'J1','C26':'J1','LED1':'J1',
       'LED4':'U3','LED5':'U4','LED6':'U5','LED2':'U3','LED7':'U5',
       'R14':'U3','R20':'U5','R22':'U3'}

MAJORS=set(['ANT1','ANT2','U1','U2','U3','U4','U5','IC1','Y1','J1','J2','J3','J4','IC2','IC3','IC4','PS1','PS2','R11'])

# ===================== CLUSTER ASSOCIATION =====================
net_pads=defaultdict(list)
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetNetname(): net_pads[p.GetNetname()].append((f.GetReference(),p.GetPadName()))
anchor_pos={r:(mm(fp[r].GetPosition().x),mm(fp[r].GetPosition().y)) for r in MAJORS}
def nearest_anchor(ref):
    p=fp[ref].GetPosition(); x,y=mm(p.x),mm(p.y)
    return min(anchor_pos,key=lambda a:(anchor_pos[a][0]-x)**2+(anchor_pos[a][1]-y)**2)
def parent_of(ref):
    f=fp[ref]; cnt=Counter()
    for p in f.Pads():
        n=p.GetNetname()
        if not n or n=='GND' or n.startswith('unconnected'): continue
        for (r2,_) in net_pads[n]:
            if r2!=ref and r2 in MAJORS: cnt[r2]+=1
    if cnt: return cnt.most_common(1)[0][0]
    if ref in STRAY: return STRAY[ref]
    return nearest_anchor(ref)

clusters=defaultdict(list)
for ref in fp:
    if ref in MAJORS: continue
    clusters[parent_of(ref)].append(ref)

# ===================== PACK PASSIVES AROUND PARENTS =====================
def pack_around(parent, members):
    if parent is None: return
    pf=fp[parent]; pc=pf.GetPosition(); pcx,pcy=mm(pc.x),mm(pc.y)
    pw,ph=size_mm(parent)
    # sort biggest first
    members=sorted(members,key=lambda r:-(size_mm(r)[0]*size_mm(r)[1]))
    ring=max(pw,ph)/2+1.2
    for ref in members:
        w,h=size_mm(ref)
        placed=False
        r=ring
        while not placed and r<40:
            steps=max(8,int(2*math.pi*r/1.4))
            for i in range(steps):
                ang=2*math.pi*i/steps
                cx=pcx+r*math.cos(ang); cy=pcy+r*math.sin(ang)
                x0,y0,x1,y1=cx-w/2-0.85,cy-h/2-0.85,cx+w/2+0.85,cy+h/2+0.85
                if not collide(x0,y0,x1,y1):
                    place(ref,round(cx,2),round(cy,2),0)
                    placed=True; break
            r+=1.0
        if not placed:
            place(ref,pcx,pcy+r,0)

# order parents so RF/critical ones pack first
order=['U1','U2','U5','U4','U3','IC1','Y1','J1','J2','J3','J4','IC2','IC3','IC4','PS1','PS2','ANT1','ANT2','R11',None]
for par in order:
    if par in clusters:
        pack_around(par, clusters[par])

pcbnew.SaveBoard(PCB,b)
# report extent
xs=[];ys=[]
for f in b.GetFootprints():
    bb=f.GetBoundingBox(False,False)
    xs+=[mm(bb.GetLeft()),mm(bb.GetRight())]; ys+=[mm(bb.GetTop()),mm(bb.GetBottom())]
print("Placed. Component extent: x %.1f..%.1f  y %.1f..%.1f"%(min(xs),max(xs),min(ys),max(ys)))
print("Cluster sizes:", {k:len(v) for k,v in clusters.items()})
