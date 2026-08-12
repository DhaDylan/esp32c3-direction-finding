import pcbnew, json
PCB="10.28.25 V2 Wifi PCB.kicad_pcb"
b=pcbnew.LoadBoard(PCB)
nm=pcbnew.FromMM; VM=pcbnew.VECTOR2I; mm=pcbnew.ToMM
plan=json.load(open("_fanout.json"))

# net codes FIRST (right after load)
_ni=b.GetNetInfo(); NC={}
for c in range(_ni.GetNetCount()):
    n=_ni.GetNetItem(c)
    if n and n.GetNetname(): NC[n.GetNetname()]=n.GetNetCode()

# remove bad 0.25-drill vias
rm=0
for t in list(b.GetTracks()):
    if t.GetClass()=='PCB_VIA' and abs(mm(t.GetDrillValue())-0.25)<0.02:
        b.Remove(t); rm+=1

for x,y,net in plan["vias"]:
    v=pcbnew.PCB_VIA(b); v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu)
    v.SetPosition(VM(nm(x),nm(y))); v.SetDrill(nm(0.3)); v.SetWidth(nm(0.6))
    v.SetNetCode(NC[net]); b.Add(v)
for x1,y1,x2,y2,net in plan["stubs"]:
    t=pcbnew.PCB_TRACK(b); t.SetStart(VM(nm(x1),nm(y1))); t.SetEnd(VM(nm(x2),nm(y2)))
    t.SetWidth(nm(0.3)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(NC[net]); b.Add(t)

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB,b)
print(f"removed {rm} bad vias; applied {len(plan['vias'])} fanout vias + {len(plan['stubs'])} stubs")
