"""
2x4 phased-array MOCKUP generator  (ESPARGOS-style layout)
===========================================================
Builds a NEW, standalone .kicad_pcb from scratch -- it does NOT touch the
existing 1x2 board in ../pcb/.

Layout follows ESPARGOS: 8 antennas on a 2-row x 4-column grid, spaced
lambda/2 = 62.5mm in BOTH dimensions at 2.4 GHz, one ESP32-C3 behind each
antenna, plus a controller/clock strip along the bottom edge.

This is a VISUAL MOCKUP: footprints are placed to scale in the correct
geometry, but nets/routing are intentionally omitted. Not manufacturable.

Run with KiCad's bundled python:
  "C:/Program Files/KiCad/9.0/bin/python.exe" build_2x4_mockup.py
"""
import os
import pcbnew

MM = pcbnew.FromMM
V = pcbnew.VECTOR2I

def ang(deg):
    return pcbnew.EDA_ANGLE(deg, pcbnew.DEGREES_T)

HERE = os.path.dirname(os.path.abspath(__file__))
FPLIB = os.path.normpath(os.path.join(HERE, "..", "footprints", "footprints"))
OUT = os.path.join(HERE, "2x4_array_mockup.kicad_pcb")

# ---------------------------------------------------------------- geometry --
HALF_LAMBDA = 62.5           # lambda/2 @ 2.4 GHz, both axes (ESPARGOS)
COL_X = [42.0, 104.5, 167.0, 229.5]
ROW_Y = [42.0, 104.5]
BOARD = (5.0, 5.0, 267.0, 175.0)   # x1, y1, x2, y2  -> 262 x 170 mm landscape

# 3D model per footprint (paths are relative to this board file)
MODELS = {
    "QFN32_5X5_EXP":      "generic_QFN32_5x5mm.stp",
    "WDP2458254B02":      "WDP.2458.25.4.B.02.stp",
    "RJ-6_ADI":           "RJ-6_ADI.step",
    "CAPC0603X33N":       "generic_C_0603_1608Metric.stp",
    "CAPC1608X90N":       "06032A101FAT2A.stp",
    "INDC0402X26N":       "MHQ0402PSA2N0ST000.stp",
    "RC0402N_YAG":        "generic_R_0402_1005Metric.stp",
    "RC0603N_YAG":        "generic_R_0603_1608Metric.stp",
    "LEDC1608X90N":       "LTST-C190GKT.stp",
    "SOP65P640X120-8N":   "CDCLVC1103PW.stp",
    "FK4000032":          "FK4000032.stp",
    "USB4105_GCT":        "USB4105-GF-A.stp",
    "SOT95P280X145-6N":   "USBLC6-2SC6.stp",
    "TSR22433N":          "TSR_2-2433N.stp",
    "694106301002_1":     "694106301002.stp",
    "PTS645SL43SMTR92LFS_CNK": "generic_SW_PTS645.stp",
}

# Receiver tile, offsets relative to the cell centre (= antenna phase centre
# sits at dy -20 so the lambda/2 grid is measured antenna-to-antenna).
TILE = [
    # (footprint,          ref_suffix, dx,   dy,   rot)
    ("WDP2458254B02",      "ANT",       0.0, -20.0,  0),
    ("CAPC1608X90N",       "CDC",       0.0,  -9.0, 90),   # antenna DC block
    ("RJ-6_ADI",           "URF",       0.0,  -2.0,  0),   # RF switch
    ("CAPC0603X33N",       "CPA",      -4.5,   4.0, 90),   # pi network
    ("INDC0402X26N",       "LPI",       0.0,   4.0, 90),
    ("CAPC0603X33N",       "CPB",       4.5,   4.0, 90),
    ("QFN32_5X5_EXP",      "U",         0.0,  14.0,  0),   # ESP32-C3
    ("RC0402N_YAG",        "RCK",       9.5,  14.0, 90),   # clock series R
    ("LEDC1608X90N",       "LED",       0.0,  26.0,  0),   # debug LED
    ("RC0402N_YAG",        "RLD",       3.5,  26.0,  0),
]
# 8 decoupling caps in two rows under each ESP
DECOUPLE = [(-6.0, 20.0), (-2.0, 20.0), (2.0, 20.0), (6.0, 20.0),
            (-6.0, 23.0), (-2.0, 23.0), (2.0, 23.0), (6.0, 23.0)]

# Controller / clock / power strip, spread along the bottom edge.
# Power on the left, clock generation centre-left, controller ESP + USB right.
CONTROLLER = [
    # (footprint,               ref,     x,      y,     rot)
    ("694106301002_1",          "J2",     30.0, 155.0,  0),   # DC barrel jack
    ("TSR22433N",               "PS1",    58.0, 146.0,  0),   # 3V3 array rail
    ("TSR22433N",               "PS2",    58.0, 164.0,  0),   # 3V3 controller
    ("LEDC1608X90N",            "LED9",   80.0, 146.0,  0),
    ("RC0603N_YAG",             "R9",     83.5, 146.0,  0),
    ("LEDC1608X90N",            "LED10",  80.0, 164.0,  0),
    ("RC0603N_YAG",             "R10",    83.5, 164.0,  0),
    ("FK4000032",               "Y1",    105.0, 155.0,  0),   # 40 MHz crystal
    ("SOP65P640X120-8N",        "IC1",   126.0, 146.0,  0),   # clock fanout tree
    ("SOP65P640X120-8N",        "IC2",   126.0, 155.0,  0),   # 1:3 cascaded to 9
    ("SOP65P640X120-8N",        "IC3",   126.0, 164.0,  0),
    ("QFN32_5X5_EXP",           "U9",    155.0, 155.0,  0),   # controller ESP32
    ("PTS645SL43SMTR92LFS_CNK", "SW1",   174.0, 147.0,  0),   # EN / BOOT
    ("PTS645SL43SMTR92LFS_CNK", "SW2",   174.0, 163.0,  0),
    ("SOT95P280X145-6N",        "IC4",   193.0, 155.0,  0),   # USB ESD
    ("RC0402N_YAG",             "R11",   204.0, 151.0,  0),   # USB CC pulldowns
    ("RC0402N_YAG",             "R12",   204.0, 159.0,  0),
    ("USB4105_GCT",             "J1",    215.0, 169.5,  0),   # USB-C, board edge
]
# decoupling around the controller ESP, same pattern as a receiver tile
CTRL_DECOUPLE = [(155.0, 143.5), (159.0, 143.5), (163.0, 143.5),
                 (155.0, 166.5), (159.0, 166.5), (163.0, 166.5)]


def attach_model(fp, fpname):
    """Replace whatever the library shipped with our repo-relative model."""
    model_file = MODELS.get(fpname)
    fp.Models().clear()
    if not model_file:
        return
    m = pcbnew.FP_3DMODEL()
    m.m_Filename = "../3dmodels/3dmodels/" + model_file
    m.m_Show = True
    fp.Models().push_back(m)


def place(board, fpname, ref, x, y, rot):
    fp = pcbnew.FootprintLoad(FPLIB, fpname)
    if fp is None:
        print("  !! could not load footprint:", fpname)
        return None
    board.Add(fp)
    fp.SetPosition(V(MM(x), MM(y)))
    if rot:
        fp.SetOrientation(ang(rot))
    fp.SetReference(ref)
    attach_model(fp, fpname)
    # keep the silkscreen readable in the render
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    return fp


def add_outline(board, x1, y1, x2, y2):
    corners = [(x1, y1, x2, y1), (x2, y1, x2, y2),
               (x2, y2, x1, y2), (x1, y2, x1, y1)]
    for (ax, ay, bx, by) in corners:
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(V(MM(ax), MM(ay)))
        seg.SetEnd(V(MM(bx), MM(by)))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(MM(0.15))
        board.Add(seg)


def main():
    board = pcbnew.CreateEmptyBoard()
    add_outline(board, *BOARD)

    n = 0
    ch = 0
    for r, cy in enumerate(ROW_Y):
        for c, cx in enumerate(COL_X):
            ch += 1
            for (fpname, suffix, dx, dy, rot) in TILE:
                ref = "{}{}".format(suffix, ch)
                if place(board, fpname, ref, cx + dx, cy + dy, rot):
                    n += 1
            for i, (dx, dy) in enumerate(DECOUPLE):
                ref = "C{}{:02d}".format(ch, i + 1)
                if place(board, "CAPC0603X33N", ref, cx + dx, cy + dy, 0):
                    n += 1

    for (fpname, ref, x, y, rot) in CONTROLLER:
        if place(board, fpname, ref, x, y, rot):
            n += 1

    for i, (x, y) in enumerate(CTRL_DECOUPLE):
        if place(board, "CAPC0603X33N", "C9{:02d}".format(i + 1), x, y, 0):
            n += 1

    pcbnew.SaveBoard(OUT, board)
    w = BOARD[2] - BOARD[0]
    h = BOARD[3] - BOARD[1]
    print("Placed {} footprints across {} channels.".format(n, ch))
    print("Board {:.1f} x {:.1f} mm, antenna pitch {} mm".format(w, h, HALF_LAMBDA))
    print("Saved:", OUT)


main()
