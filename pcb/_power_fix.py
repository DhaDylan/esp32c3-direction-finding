"""Re-place the bottom-left power section by PAD-CENTER (auto-correcting for
footprint origin offsets). Accounts for real part widths: J1 power connector
(10.6mm), R11 LED series-R (22mm wide), PS1/PS2 regulators."""
import pcbnew
PCB="10.28.25 V2 Wifi PCB.kicad_pcb"
b=pcbnew.LoadBoard(PCB)
nm=pcbnew.FromMM; VM=pcbnew.VECTOR2I; mm=pcbnew.ToMM
def ang(d): return pcbnew.EDA_ANGLE(d, pcbnew.DEGREES_T)
fp={f.GetReference():f for f in b.GetFootprints()}

def padcenter(f):
    xs=[];ys=[]
    for p in f.Pads():
        bb=p.GetBoundingBox(); xs+=[mm(bb.GetLeft()),mm(bb.GetRight())]; ys+=[mm(bb.GetTop()),mm(bb.GetBottom())]
    return ((min(xs)+max(xs))/2,(min(ys)+max(ys))/2)

def place_pc(ref,tx,ty,rot=0):
    """place so the pad-center lands on (tx,ty)"""
    f=fp.get(ref)
    if not f: print("  missing",ref); return
    f.SetOrientation(ang(rot))
    f.SetPosition(VM(nm(tx),nm(ty)))
    cx,cy=padcenter(f)                       # measure offset at this rotation
    o=f.GetPosition()
    f.SetPosition(VM(o.x+nm(tx-cx), o.y+nm(ty-cy)))

# pad-center targets, kept within x:[9,35]  y:[55,107]  (clear of CH2 at x>=38)
LAYOUT={
 'J1':(14,59,0),
 'R11':(22,67,0), 'LED1':(33,67,0),
 'C1':(10,74,0),'C2':(13,74,0),'C4':(16,74,0),'C5':(19,74,0),
 'PS2':(15,81,0), 'LED7':(33,79,0),'R20':(33,81,0), 'C3':(24,80,0),
 'PS1':(15,93,0), 'LED2':(33,91,0),'R7':(33,93,0),
 'R14':(23,86,0),'R22':(26,86,0),
 'R12':(10,100,0),'R15':(13,100,0),'R16':(10,103,0),'R19':(13,103,0),
}
for ref,(x,y,r) in LAYOUT.items(): place_pc(ref,x,y,r)
pcbnew.SaveBoard(PCB,b)
print("Power section re-placed by pad-center.")
