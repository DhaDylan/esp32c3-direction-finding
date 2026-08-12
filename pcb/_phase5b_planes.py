import pcbnew
PCB="10.28.25 V2 Wifi PCB.kicad_pcb"
b=pcbnew.LoadBoard(PCB)
nm=pcbnew.FromMM
# build name->code map at module level (avoids SWIG chained-call quirk)
_ni=b.GetNetInfo()
NETCODE={}
for c in range(_ni.GetNetCount()):
    n=_ni.GetNetItem(c)
    if n and n.GetNetname(): NETCODE[n.GetNetname()]=n.GetNetCode()
def code(n): return NETCODE[n]

for z in list(b.Zones()): b.Remove(z)

L,T,R,Bm=7.5,1.6,146.4,120.1

def zone(layer, netname, corners, clr=0.25, prio=0):
    poly=pcbnew.SHAPE_POLY_SET()
    poly.NewOutline()
    for x,y in corners: poly.Append(nm(x),nm(y))
    z=pcbnew.ZONE(b)
    z.SetOutline(poly)
    z.SetLayer(layer)
    z.SetNetCode(code(netname))
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(nm(clr))
    z.SetMinThickness(nm(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(nm(0.3))
    z.SetThermalReliefSpokeWidth(nm(0.4))
    b.Add(z)

rect=[(L,T),(R,T),(R,Bm),(L,Bm)]
# F.Cu, In1.Cu, B.Cu = GND
zone(pcbnew.F_Cu, "GND", rect)
zone(pcbnew.In1_Cu,"GND", rect)
zone(pcbnew.B_Cu, "GND", rect)
# In2.Cu = split power: Power2 (left/center) + Power1 (right)
SPLIT_L=109.0; SPLIT_R=113.0
zone(pcbnew.In2_Cu,"/Power2", [(L,T),(SPLIT_L,T),(SPLIT_L,Bm),(L,Bm)])
zone(pcbnew.In2_Cu,"/Power1", [(SPLIT_R,T),(R,T),(R,Bm),(SPLIT_R,Bm)])

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB,b)
print("zones:",len(list(b.Zones())),"(F/In1/B=GND, In2=Power2|Power1 split)")
