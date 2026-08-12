import pcbnew, json
PCB="10.28.25 V2 Wifi PCB.kicad_pcb"
b=pcbnew.LoadBoard(PCB)
nm=pcbnew.FromMM; VM=pcbnew.VECTOR2I
plan=json.load(open("_connect.json"))
_ni=b.GetNetInfo(); NC={}
for c in range(_ni.GetNetCount()):
    n=_ni.GetNetItem(c)
    if n and n.GetNetname(): NC[n.GetNetname()]=n.GetNetCode()
nv=ns=0
for item in plan["vias"]:
    if item[0]=='STUB':
        _,x1,y1,x2,y2,net=item
        t=pcbnew.PCB_TRACK(b); t.SetStart(VM(nm(x1),nm(y1))); t.SetEnd(VM(nm(x2),nm(y2)))
        t.SetWidth(nm(0.3)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(NC[net]); b.Add(t); ns+=1
    else:
        x,y,net,dia=item
        v=pcbnew.PCB_VIA(b); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu)
        v.SetPosition(VM(nm(x),nm(y))); v.SetWidth(nm(dia)); v.SetDrill(nm(max(0.2,dia-0.25)))
        v.SetNetCode(NC[net]); b.Add(v); nv+=1
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB,b)
print(f"added {nv} vias, {ns} stubs")
