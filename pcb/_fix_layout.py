import pcbnew, math
PCB = "10.28.25 V2 Wifi PCB.kicad_pcb"
b = pcbnew.LoadBoard(PCB)
mm = pcbnew.ToMM; nm = pcbnew.FromMM; VM = pcbnew.VECTOR2I

# ── PASS 1: collect all data before any mutations ──────────────────────────
ni = b.GetNetInfo()
netcodes = {}
for c in range(ni.GetNetCount()):
    n = ni.GetNetItem(c)
    if n and n.GetNetname(): netcodes[n.GetNetname()] = n.GetNetCode()

fdict = {}
old_pad_pos = {}  # (ref, padname) -> (x_nm, y_nm)
for f in b.GetFootprints():
    r = f.GetReference()
    fdict[r] = f
    for p in f.Pads():
        pp = p.GetPosition()
        old_pad_pos[(r, p.GetPadName())] = (pp.x, pp.y)

# ── what to move ───────────────────────────────────────────────────────────
# USB-C connectors → board bottom edge (bbox_bottom = 120.17 → Δy ≈ +8 mm)
# R1/R3/R5 (directly below connectors) → above connectors at y=102
# R11 (overlapping PS1 bbox) → shift right to x=46
MOVES = {
    'J2':  (128,    116),
    'J3':  (90,     116),
    'J4':  (52,     116),
    'R1':  (128.35, 102),
    'R3':  (90.35,  102),
    'R5':  (52.35,  102),
    'R11': (46,     88),
}

# ── build set of old pad positions for moved footprints ───────────────────
moved_old_pads = []
for (r, _), (px, py) in old_pad_pos.items():
    if r in MOVES:
        moved_old_pads.append((px, py))

# ── PASS 2: identify tracks to delete ─────────────────────────────────────
ANT2_FEED_NET = 'Net-(ANT2-RF_FEED)'
RADIUS = nm(3)   # 3 mm radius to catch track endpoints at old pad positions
to_del = []
for t in b.GetTracks():
    if t.GetNetname() == ANT2_FEED_NET:
        to_del.append(t); continue          # replace with serpentine
    if t.GetClass() == 'PCB_VIA': continue  # keep vias
    s = t.GetStart(); e = t.GetEnd()
    for (px, py) in moved_old_pads:
        if (abs(s.x-px)<RADIUS and abs(s.y-py)<RADIUS) or \
           (abs(e.x-px)<RADIUS and abs(e.y-py)<RADIUS):
            to_del.append(t); break

print(f"Removing {len(to_del)} stale tracks")

# ── PASS 3: move footprints ───────────────────────────────────────────────
for ref, (nx, ny) in MOVES.items():
    if ref in fdict:
        fdict[ref].SetPosition(VM(nm(nx), nm(ny)))
        print(f"  Moved {ref} → ({nx}, {ny})")

# ── PASS 4: delete stale tracks ───────────────────────────────────────────
for t in to_del:
    b.Remove(t)

# ── PASS 5: add ANT2 serpentine meander ───────────────────────────────────
# ANT1 total path: 23.62 (RF_FEED) + 15.54 (U1-RF1) = 39.16 mm
# ANT2 target  : U2-RF1 stays 7.52 mm, so RF_FEED needs to be 39.16-7.52=31.64 mm
# Serpentine ANT2(52,20)→(58.7,20)→(58.7,27.3)→(51,27.3)→(51,37.3)=C42.2
# Lengths: 6.7 + 7.3 + 7.7 + 10.0 = 31.7 mm  (Δ from original 17.71 = +13.99 mm)
ant2_nc = netcodes.get(ANT2_FEED_NET, 0)
pts = [(52,20),(58.7,20),(58.7,27.3),(51,27.3),(51,37.3)]
total = 0.0
for i in range(len(pts)-1):
    x1,y1 = pts[i]; x2,y2 = pts[i+1]
    seg = math.hypot(x2-x1, y2-y1); total += seg
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(VM(nm(x1),nm(y1))); t.SetEnd(VM(nm(x2),nm(y2)))
    t.SetWidth(nm(0.35)); t.SetLayer(pcbnew.F_Cu)
    t.SetNetCode(ant2_nc); b.Add(t)
print(f"  ANT2 serpentine total = {total:.2f} mm  (target 31.64 mm)")
print(f"  ANT2 new total path   = {total+7.52:.2f} mm  (ANT1 = 39.16 mm)")

# ── PASS 6: fill zones and save ───────────────────────────────────────────
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB, b)
print("Board saved.")
