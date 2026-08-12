import pcbnew, math
PCB="10.28.25 V2 Wifi PCB.kicad_pcb"
b=pcbnew.LoadBoard(PCB)
nm=pcbnew.FromMM; VM=pcbnew.VECTOR2I; mm=pcbnew.ToMM

RF=['C19','C27','C24','L4','C23','L3','C22','C42','C37','C36','L6','C35','L5','C34','C16','L2','C18','C17']
fp={f.GetReference():f for f in b.GetFootprints()}

# obstacle courtyard boxes for all NON-RF footprints (collected first, plain data)
obst=[]
for f in b.GetFootprints():
    if f.GetReference() in RF: continue
    bb=f.GetBoundingBox(False,False)
    obst.append((mm(bb.GetLeft())-0.4,mm(bb.GetTop())-0.4,mm(bb.GetRight())+0.4,mm(bb.GetBottom())+0.4))
# antenna keepouts
for r in ['ANT1','ANT2']:
    c=fp[r].GetPosition(); cx,cy=mm(c.x),mm(c.y)
    obst.append((cx-14,cy-14,cx+14,cy+14))

def size(ref):
    f=fp[ref]; bb=f.GetBoundingBox(False,False)
    return mm(bb.GetWidth()), mm(bb.GetHeight())
placed=[]  # boxes of RF placed so far
def collide(x,y,w,h):
    box=(x-w/2-0.4,y-h/2-0.4,x+w/2+0.4,y+h/2+0.4)
    for bx in obst+placed:
        if not (box[2]<=bx[0] or box[0]>=bx[2] or box[3]<=bx[1] or box[1]>=bx[3]): return True
    return False
def place(ref,ix,iy,rot=0):
    w,h=size(ref)
    if rot in (90,270): w,h=h,w
    for r in [0]+[d*0.5 for d in range(1,40)]:
        for ang in range(0,360,30) if r>0 else [0]:
            x=ix+r*math.cos(math.radians(ang)); y=iy+r*math.sin(math.radians(ang))
            if not collide(x,y,w,h):
                f=fp[ref]; f.SetOrientationDegrees(rot); f.SetPosition(VM(nm(round(x,2)),nm(round(y,2))))
                placed.append((x-w/2-0.4,y-h/2-0.4,x+w/2+0.4,y+h/2+0.4)); return
# ideal positions (clear-ish corridors); collision search finds nearest free spot
IDEAL=[('C19',98,37,90),('C42',51,38,90),
       ('C27',95,49,90),('C24',97,51,0),('L4',93,52,90),('C23',95,55,0),('L3',84,58,0),('C22',84,55,0),
       ('C37',56,49,90),('C36',58,51,0),('L6',54,52,90),('C35',56,55,0),('L5',45,58,0),('C34',45,55,0),
       ('C16',122,55,0),('L2',116,53,90),('C18',109,51,0),('C17',100,49,90)]
for ref,ix,iy,rot in IDEAL: place(ref,ix,iy,rot)
pcbnew.SaveBoard(PCB,b)
print("RF re-placed (collision-aware):",len(IDEAL),"parts")
