import pcbnew
PCB="10.28.25 V2 Wifi PCB.kicad_pcb"
b=pcbnew.LoadBoard(PCB)
nm=pcbnew.FromMM; VM=pcbnew.VECTOR2I
fp={f.GetReference():f for f in b.GetFootprints()}
def mv(ref,x,y,rot=0):
    f=fp[ref]; f.SetOrientationDegrees(rot); f.SetPosition(VM(nm(x),nm(y)))

# Rx1 input pi-network (U1 switch @ (90,44) -> U4.1 LNA_IN @ (87.55,60.25))
mv('C19',101.0,32.0,90)   # ANT1 DC block (between ANT1 and U1)
mv('C27',93.5,49.0,90)    # series /Data1 -> node
mv('C24',96.0,51.0,0)     # shunt to GND
mv('L4', 91.5,52.5,90)    # series -> LNA_IN
mv('C23',94.0,55.5,0)     # shunt to GND
mv('L3', 82.0,61.0,0)     # supply ferrite (Power2 -> U4.2/3)
mv('C22',82.0,64.0,0)     # supply decoupling
# Rx2 input pi-network (U2 @ (50,44) -> U5.1 @ (49.55,60.25))
mv('C42',51.0,32.0,90)    # ANT2 DC block
mv('C37',54.5,49.0,90)
mv('C36',57.0,51.0,0)
mv('L6', 52.5,52.5,90)
mv('C35',55.0,55.5,0)
mv('L5', 45.0,61.0,0)
mv('C34',45.0,64.0,0)
# Calibration chain (U3.1 @ (125.55,60.25) -> /CalLNA -> U1.1/U2.1)
mv('C16',121.5,55.0,0)    # shunt near U3.1
mv('L2', 115.0,53.0,90)   # series
mv('C18',108.0,51.0,0)    # shunt
mv('C17',99.0,49.5,90)    # series -> /CalLNA (toward switches)

pcbnew.SaveBoard(PCB,b)
print("RF pi-networks re-placed (clustered in-path)")
