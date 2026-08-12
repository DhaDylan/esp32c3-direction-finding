"""Respace the tight clusters to clear courtyard overlaps (manufacturing clearance):
 - decoupling caps: push off each ESP (+6.5/+10) and widen pitch (5mm)
 - USB CC resistors: back off the connectors (+44)
 - power corner: spread the regulators / option resistors / input caps
Keeps the symmetric architecture; everything re-routes after."""
import pcbnew
PCB="10.28.25 V2 Wifi PCB.kicad_pcb"
b=pcbnew.LoadBoard(PCB)
nm=pcbnew.FromMM; VM=pcbnew.VECTOR2I; mm=pcbnew.ToMM
def ang(d): return pcbnew.EDA_ANGLE(d,pcbnew.DEGREES_T)
fp={f.GetReference():f for f in b.GetFootprints()}
def padcenter(f):
    xs=[];ys=[]
    for p in f.Pads():
        bb=p.GetBoundingBox(); xs+=[mm(bb.GetLeft()),mm(bb.GetRight())];ys+=[mm(bb.GetTop()),mm(bb.GetBottom())]
    return ((min(xs)+max(xs))/2,(min(ys)+max(ys))/2)
def place(ref,tx,ty,rot=0):
    f=fp.get(ref)
    if not f: return
    f.SetOrientation(ang(rot)); f.SetPosition(VM(nm(tx),nm(ty)))
    cx,cy=padcenter(f); o=f.GetPosition(); f.SetPosition(VM(o.x+nm(tx-cx),o.y+nm(ty-cy)))

ESP={'U4':(114.5,62.0),'U5':(52.0,62.0),'U3':(83.25,62.0)}
# 8 decoupling caps per ESP: 2 rows of 4, 5mm pitch, pushed down off the QFN
DOFF=[(-7.5,6.5),(-2.5,6.5),(2.5,6.5),(7.5,6.5),(-7.5,10.0),(-2.5,10.0),(2.5,10.0),(7.5,10.0)]
DECOUP={'U4':['C12','C13','C14','C20','C21','C28','C29','C30'],
        'U5':['C31','C32','C33','C38','C39','C40','C41','C6'],
        'U3':['C7','C8','C9','C10','C11','C15','C25','C26']}
for esp,caps in DECOUP.items():
    ex,ey=ESP[esp]
    for cap,(dx,dy) in zip(caps,DOFF): place(cap, ex+dx, ey+dy)

# debug LED + R pushed down clear of decoupling row2
DBG={'U4':('LED5','R17'),'U5':('LED6','R18'),'U3':('LED4','R13')}
for esp,(led,r) in DBG.items():
    ex,ey=ESP[esp]; place(led, ex, ey+14.0); place(r, ex, ey+15.6)

# boot caps + switches pushed out to clear the widened decoupling row
BOOT={'U4':('C44','SW2','C47','SW5'),'U5':('C45','SW3','C48','SW6'),'U3':('C43','SW1','C46','SW4')}
for esp,(cen,swen,cio,swio) in BOOT.items():
    ex,ey=ESP[esp]
    place(cen, ex-9.5, ey+14.0); place(swen, ex-9.0, ey+18.0)   # caps dropped clear of decoupling
    place(cio, ex+9.5, ey+14.0); place(swio, ex+9.0, ey+18.0)   # switches stay ±9 (no inter-channel clash)

# CC resistors backed off the USB connectors (was +49 -> +44)
CC={'U4':('R3','R4'),'U5':('R5','R6'),'U3':('R2','R1')}
for esp,(rl,rr) in CC.items():
    ex,ey=ESP[esp]; place(rl, ex-5.5, ey+44); place(rr, ex+5.5, ey+44)

# Power corner — spread out (pad-center placement)
P={
 'J1':(16,59), 'C1':(11,71),'C2':(15,71),'C4':(20,71),'C5':(25,71),
 'PS2':(15,81), 'PS1':(15,95), 'C3':(29,95),
 'R14':(28,79),'R22':(31,79),                       # Power1 option R (by PS2)
 'R12':(28,90),'R15':(31,90),'R16':(28,93),'R19':(31,93),   # Power2 option R (by PS1)
 'LED7':(35,79),'R20':(35,81),                       # Power1 rail LED
 'LED2':(35,93),'R7':(35,95),                        # Power2 rail LED
 'R11':(28,109),'LED1':(38,101),                     # input power LED (already-fixed spot)
}
for ref,(x,y) in P.items(): place(ref,x,y)
pcbnew.SaveBoard(PCB,b)
print("respaced decoupling + CC resistors + power corner")
