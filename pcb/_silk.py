import pcbnew
PCB="10.28.25 V2 Wifi PCB.kicad_pcb"
b=pcbnew.LoadBoard(PCB)
nm=pcbnew.FromMM
n=0
for f in b.GetFootprints():
    ref=f.Reference()
    # move reference designator to F.Fab (off silk) + shrink
    ref.SetLayer(pcbnew.F_Fab)
    ref.SetTextSize(pcbnew.VECTOR2I(nm(0.6),nm(0.6)))
    ref.SetTextThickness(nm(0.1))
    # value: keep off silk too (to Fab, usually already hidden)
    val=f.Value()
    if val.IsOnLayer(pcbnew.F_SilkS):
        val.SetLayer(pcbnew.F_Fab)
    n+=1
pcbnew.SaveBoard(PCB,b)
print(f"moved {n} reference designators to F.Fab (off silkscreen)")
