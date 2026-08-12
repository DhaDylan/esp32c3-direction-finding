"""Symmetric copy-paste floorplan: 2 identical receiver channels + centered hub.
CH2 @ x=52, CH1 = CH2 + 62.5mm @ x=114.5, hub U3 centered @ x=83.25.
Receiver tiles are pure translations -> matched trace lengths by construction.
Clock buffer IC1 + crystal Y1 centered above hub for symmetric clock fan-out.
Tactile switches (PTS645, ~10x5.5mm) get a clear band at the bottom of each tile.
"""
import pcbnew
PCB = "10.28.25 V2 Wifi PCB.kicad_pcb"
b = pcbnew.LoadBoard(PCB)
nm = pcbnew.FromMM; VM = pcbnew.VECTOR2I
def ang(d): return pcbnew.EDA_ANGLE(d, pcbnew.DEGREES_T)

U5_X, U4_X, U3_X = 52.0, 114.5, 83.25   # CH2, CH1, hub centerlines
ESP_Y = 62.0

# ── Receiver RF tile (above ESP): role -> (dx,dy,rot) rel ESP ─────────────
RF_TILE = {
    'ant':  ( 0.00, -42.00,  0),   # antenna directly above ESP
    'dcb':  ( 0.00, -28.00, 90),   # antenna DC block (straight vertical feed)
    'sw':   ( 0.00, -18.00,  0),   # RF switch
    'ca':   ( 4.75, -13.43, 90),
    'cb':   ( 4.50, -11.00,  0),
    'lm':   ( 2.00, -10.00, 90),
    'clna': ( 5.00,  -3.00,  0),
    'csh':  (-3.00, -12.20,  0),
    'lsh':  (-2.75,  -9.63,  0),
}
# Support tile (below ESP). Switches in a clear band at the bottom.
SUP_TILE = {
    'rclk': ( 7.5,  0.0, 0),                                   # clock series R, right of ESP
    'd0': (-6.0, 4.5, 0), 'd1': (-2.0, 4.5, 0), 'd2': ( 2.0, 4.5, 0), 'd3': ( 6.0, 4.5, 0),
    'd4': (-6.0, 8.0, 0), 'd5': (-2.0, 8.0, 0), 'd6': ( 2.0, 8.0, 0), 'd7': ( 6.0, 8.0, 0),
    'led': ( 0.0, 11.5, 0), 'rled': ( 0.0, 13.2, 0),          # debug LED + R (center)
    'cen': (-9.0, 12.5, 0), 'swen': (-9.0, 17.5, 0),          # CHIP_EN cap + button (left)
    'cio': ( 9.0, 12.5, 0), 'swio': ( 9.0, 17.5, 0),          # GPIO9  cap + button (right)
    'esd': ( 0.0, 30.0, 0),                                    # USB ESD
    'ccl': (-5.0, 49.0, 0), 'ccr': ( 5.0, 49.0, 0),           # USB-C CC resistors
    'usb': ( 0.0, 54.0, 0),                                    # USB-C (board edge)
}

CH1 = {  # U4 right, ANT1
    'esp':'U4','sw':'U1','dcb':'C19','ca':'C27','cb':'C24','lm':'L4','clna':'C23',
    'csh':'C22','lsh':'L3','ant':'ANT1','rclk':'R8',
    'd0':'C12','d1':'C13','d2':'C14','d3':'C20','d4':'C21','d5':'C28','d6':'C29','d7':'C30',
    'cen':'C44','swen':'SW2','cio':'C47','swio':'SW5','led':'LED5','rled':'R17',
    'esd':'IC3','usb':'J3','ccl':'R3','ccr':'R4',
}
CH2 = {  # U5 left, ANT2
    'esp':'U5','sw':'U2','dcb':'C42','ca':'C37','cb':'C36','lm':'L6','clna':'C35',
    'csh':'C34','lsh':'L5','ant':'ANT2','rclk':'R9',
    'd0':'C31','d1':'C32','d2':'C33','d3':'C38','d4':'C39','d5':'C40','d6':'C41','d7':'C6',
    'cen':'C45','swen':'SW3','cio':'C48','swio':'SW6','led':'LED6','rled':'R18',
    'esd':'IC4','usb':'J4','ccl':'R5','ccr':'R6',
}
# Hub uses the same support tile + a cal-RX network + the clock source on top
HUB_SUP = {  # role -> ref (hub variant)
    'rclk':'R10','d0':'C7','d1':'C8','d2':'C9','d3':'C10','d4':'C11','d5':'C15','d6':'C25','d7':'C26',
    'cen':'C43','swen':'SW1','cio':'C46','swio':'SW4','led':'LED4','rled':'R13',
    'esd':'IC2','usb':'J2','ccl':'R2','ccr':'R1',
}
HUB_EXTRA = {  # clock source + cal RX, rel U3
    'IC1':( 0.0,-18.0, 0), 'Y1':( 0.0,-22.5, 0),          # clock buffer + crystal (centered above)
    'C16':(-3.5,-4.0, 0), 'L2':(-3.5,-7.0,90), 'C18':( 3.5,-4.0, 0), 'C17':( 3.5,-7.0,90),  # cal RX
    'L1':( 9.0, 4.5, 0),                                   # hub power ferrite
}

# ── Power section (bottom-left corner), absolute positions ───────────────
POWER = {
    'J1': (16.0, 60.0, 0),                                  # power input
    'PS2':(16.0, 80.0, 0),                                  # Power1 (hub) regulator
    'PS1':(16.0, 96.0, 0),                                  # Power2 (rx)  regulator
    'C1':(10.0, 69.0, 0), 'C2':(13.5, 69.0, 0), 'C4':(19.0, 69.0, 0), 'C5':(22.5, 69.0, 0),
    'C3':(26.0, 80.0, 0),
    'LED1':(28.0, 60.0, 0), 'R11':(28.0, 62.0, 0),         # input power LED
    'LED7':(28.0, 80.0, 0), 'R20':(28.0, 82.0, 0),         # Power1 rail LED
    'LED2':(28.0, 96.0, 0), 'R7':(28.0, 98.0, 0),          # Power2 rail LED
    'R14':(10.0, 85.0, 0), 'R22':(13.0, 85.0, 0),          # Power1 option R
    'R12':(8.5, 100.0, 0), 'R15':(11.5,100.0, 0), 'R16':(8.5,103.0, 0), 'R19':(11.5,103.0, 0),  # Power2 option R
}

# ── apply ────────────────────────────────────────────────────────────────
fp = {f.GetReference(): f for f in b.GetFootprints()}
moved=0; missing=[]
def place(ref, x, y, rot):
    global moved
    f=fp.get(ref)
    if not f: missing.append(ref); return
    f.SetPosition(VM(nm(x),nm(y))); f.SetOrientation(ang(rot)); moved+=1

for chan, X in ((CH1,U4_X),(CH2,U5_X)):
    place(chan['esp'], X, ESP_Y, 0)
    for role,(dx,dy,rot) in RF_TILE.items(): place(chan[role], X+dx, ESP_Y+dy, rot)
    for role,(dx,dy,rot) in SUP_TILE.items(): place(chan[role], X+dx, ESP_Y+dy, rot)

# hub
place('U3', U3_X, ESP_Y, 0)
for role,(dx,dy,rot) in SUP_TILE.items(): place(HUB_SUP[role], U3_X+dx, ESP_Y+dy, rot)
for ref,(dx,dy,rot) in HUB_EXTRA.items(): place(ref, U3_X+dx, ESP_Y+dy, rot)

# power
for ref,(x,y,rot) in POWER.items(): place(ref, x, y, rot)

print(f"Placed {moved} footprints.  Missing refs: {missing if missing else 'none'}")
pcbnew.SaveBoard(PCB,b)
print("Saved.")
