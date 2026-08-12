"""Reposition the 3 clock series resistors symmetrically between IC1 and each
ESP, re-route the clock paths directly on F.Cu, and add serpentine meanders so
all three IC1->ESP.30 paths are equal length. All footprint/pad reads happen in
one pass BEFORE any mutation (SWIG proxies invalidate after Remove/SetPosition)."""
import pcbnew, math
PCB="10.28.25 V2 Wifi PCB.kicad_pcb"
b=pcbnew.LoadBoard(PCB)
nm=pcbnew.FromMM; VM=pcbnew.VECTOR2I; mm=pcbnew.ToMM
def ang(d): return pcbnew.EDA_ANGLE(d,pcbnew.DEGREES_T)
ni=b.GetNetInfo(); NC={}
for c in range(ni.GetNetCount()):
    n=ni.GetNetItem(c)
    if n and n.GetNetname(): NC[n.GetNetname()]=n.GetNetCode()

# ---- single read pass ----
fp={}; padpos={}; padlocal={}; padcenter_off={}
for f in b.GetFootprints():
    r=f.GetReference(); fp[r]=f
    cx,cy=mm(f.GetPosition().x),mm(f.GetPosition().y)
    xs=[];ys=[]
    locs={}
    for p in f.Pads():
        pp=p.GetPosition(); x,y=mm(pp.x),mm(pp.y)
        padpos[(r,p.GetPadName())]=(x,y)
        locs[p.GetPadName()]=(x-cx,y-cy)            # pad offset from fp origin
        bb=p.GetBoundingBox(); xs+=[mm(bb.GetLeft()),mm(bb.GetRight())];ys+=[mm(bb.GetTop()),mm(bb.GetBottom())]
    padlocal[r]=locs
    if xs: padcenter_off[r]=(( (min(xs)+max(xs))/2 - cx),((min(ys)+max(ys))/2 - cy))

IC1={'Y0':padpos[('IC1','3')],'Y1':padpos[('IC1','8')],'Y2':padpos[('IC1','5')]}
ESP={'U3':padpos[('U3','30')],'U4':padpos[('U4','30')],'U5':padpos[('U5','30')]}

# ---- move clock resistors to symmetric pad-centers, compute new pad positions ----
def move_pc(ref,tx,ty):
    ox,oy=padcenter_off[ref]                        # pad-center offset from origin (rot 0)
    fp[ref].SetOrientation(ang(0)); fp[ref].SetPosition(VM(nm(tx-ox),nm(ty-oy)))
    nx,ny=tx-ox,ty-oy
    return {pn:(nx+lx,ny+ly) for pn,(lx,ly) in padlocal[ref].items()}
R10p=move_pc('R10',84.0,51.0); R8p=move_pc('R8',100.0,51.0); R9p=move_pc('R9',66.5,51.0)

# ---- rip up old clock tracks ----
CLK={'Net-(IC1-Y0)','Net-(IC1-Y1)','Net-(IC1-Y2)','/Clock1','/Clock2','/Clock3'}
for t in [t for t in b.GetTracks()]:
    if t.GetClass()!='PCB_VIA' and t.GetNetname() in CLK: b.Remove(t)

def track(x1,y1,x2,y2,net):
    t=pcbnew.PCB_TRACK(b); t.SetStart(VM(nm(x1),nm(y1))); t.SetEnd(VM(nm(x2),nm(y2)))
    t.SetWidth(nm(0.25)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(NC[net]); b.Add(t)
def dist(a,c): return math.hypot(a[0]-c[0],a[1]-c[1])

# chains: feed IC1->R.1 ; clock R.2->ESP.30
chains=[('Net-(IC1-Y0)',IC1['Y0'],R10p['1'],R10p['2'],'/Clock1',ESP['U3']),
        ('Net-(IC1-Y1)',IC1['Y1'],R8p['1'], R8p['2'], '/Clock2',ESP['U4']),
        ('Net-(IC1-Y2)',IC1['Y2'],R9p['1'], R9p['2'], '/Clock3',ESP['U5'])]
for feed,s,r1,r2,clk,esp in chains:
    track(s[0],s[1],r1[0],r1[1],feed)               # feed segment

feedlen={c[4]:dist(c[1],c[2]) for c in chains}
clkbase={c[4]:dist(c[3],c[5]) for c in chains}
total={c[4]:feedlen[c[4]]+clkbase[c[4]] for c in chains}
target=max(total.values())+1.0
print("pre-match:",{k:round(v,2) for k,v in total.items()},"-> target",round(target,2))

def serpentine(r2,esp,net,want):
    x1,y1=r2; x2,y2=esp; base=math.hypot(x2-x1,y2-y1)
    extra=max(0.0,want-base)
    if extra<0.4: track(x1,y1,x2,y2,net); return base
    ux,uy=(x2-x1)/base,(y2-y1)/base; px,py=-uy,ux
    N=max(1,int(extra/3.0)+1); amp=min(2.2,extra/(2*N))
    pts=[(x1,y1)]
    for i in range(N):
        t0=(i+0.5)/N; s=1 if i%2==0 else -1
        pts.append((x1+ux*base*t0+px*amp*s, y1+uy*base*t0+py*amp*s))
    pts.append((x2,y2)); L=0
    for i in range(len(pts)-1):
        track(*pts[i],*pts[i+1],net); L+=math.hypot(pts[i+1][0]-pts[i][0],pts[i+1][1]-pts[i][1])
    return L
for feed,s,r1,r2,clk,esp in chains:
    got=serpentine(r2,esp,clk,target-feedlen[clk])
    print(f"  {clk}: {feedlen[clk]+got:.1f} mm")
pcbnew.SaveBoard(PCB,b)
print("clock tree length-matched & saved")
