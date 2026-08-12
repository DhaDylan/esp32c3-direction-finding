# PCB Agent Handoff — ESP32-C3 WiFi Sensing / Direction-Finding Board

**Date:** 2026-06-20 (symmetric rebuild)
**Status:** **Symmetric copy-paste channel architecture** — the two receiver channels are now IDENTICAL tiles (CH1 = CH2 translated +62.5mm), hub centered between them, clock source centered. **Antenna feeds are exactly equal (CH1 = CH2 = 13.30mm, 0.00mm diff).** 0 shorts, 0 crossings. ~18 hard power/GND pads + clock length-tuning remain as interactive items.

## Symmetric architecture (this session — the big rework)
Per the user's request: the two ESP receiver channels should be copy-paste identical (matched timing), the hub centered between them, important traces equal, and the whole thing tileable for a future 4×2.

- **CH2 (U5) @ x=52, CH1 (U4) @ x=114.5** — pure translation (+62.5mm = λ/2), same orientation → every CH1 trace has an identical CH2 counterpart. Tileable for 4×2.
- **Hub (U3) centered @ x=83.25**, crystal Y1 + clock buffer IC1 centered directly above it for symmetric fan-out.
- **Antennas** directly above each receiver (52 / 114.5, 62.5mm apart). **RF feed lengths now identical: CH1=CH2=13.30mm (0.00mm diff)** — was the user's main complaint. Most RF chain segments match within <1mm (LNA_in differs 4mm — FreeRouting artifact, interactive-tunable).
- **USB-C** one per ESP along the bottom edge (CH2 left / hub center / CH1 right); **power section** bottom-left corner.
- Each channel tile = {antenna, RF switch, RF π-network, ESP, 8 decoupling, 2 boot buttons, debug LED, clock-R, USB-C + ESD + CC resistors}. Defined in `pcb/_symmetry_place.py`.

### Plane fix (critical)
The old In2 split (Power2 left / Power1 right) no longer matched the new placement (both receivers use Power2 but sit at opposite ends; hub uses Power1 in the center). **In2 is now a solid Power2 plane** (perfect, identical for both receivers — the symmetry goal); **Power1 (hub only, low-power) routes as normal traces.** This fixed all the dangling-via / wrong-plane errors.

### 2026-06-22 update #2: component respacing (clash cleanup)
Found real crowding (decoupling caps hugging the ESPs, CC resistors against the USB connectors, packed power corner). Respaced via `_respace.py`: decoupling caps pushed off each QFN (+6.5/+10) and widened to 5mm pitch; CC resistors backed off the USB (+44); power corner spread; debug LEDs/boot caps cleared. Re-routed + re-fanned-out. **Result: courtyard overlaps 18 → 2, total DRC 70 → 44, 0 shorts. Snapshot `*.RESPACE44_*` / `*.RESPACED_*`.**
- Remaining 44 = ~26 inherent/cosmetic (RF inductor/cap pads at 0.10mm + USB-C fine pitch = footprint-locked solder-mask/clearance; silk text/outlines) + 2 boot-cap courtyard touches (C21/C44, C6/C48) + 2 C1 edge + 1 option-R keepout stub + 10 unconnected (QFN power pins for push-and-shove).
- NOTE: `ExportSpecctraDSN` is intermittent — sometimes hangs even with zones present and a clean process table. When it works it's ~6s; when it hangs, kill + retry or export from the GUI. This blocked a v2 re-route (boot-cap/C1 nudges), so those 4 minor violations remain.

### 2026-06-22 update: R11 clash fixed + Power2 re-architected
- **R11/J1 clash FIXED.** R11 (`PWR8030W1002FE`, an 18mm-pad-span power resistor) overlapped J1 by 11.6mm. Moved R11 → (28,109) and LED1 → (38,101), both verified clear. Cost: 4 trivial power-LED ratlines to redraw.
- **Export-hang root cause FOUND:** `ExportSpecctraDSN` hangs when an inner copper layer has **no zone** (and also on script-placed vias). Keep a zone on every inner layer → export works in ~6s.
- **Power2 re-architected:** In1 stays the solid GND plane (RF reference). In2 changed from a rigid Power2 plane → **signal layer carrying a GND zone**, so Power2 routes as a normal net. This let FreeRouting fan out the power pins itself: **stuck QFN Power2 pins 8 → 4.** Receivers still matched (GND plane solid + copy-paste placement).
- **Current: 70 DRC, 16 unconnected, 0 shorts/crossings.** Unconnected = 3 VBUS + 2 Power1 + 1 ControlA + 1 LED1 (all **easy open short-traces, not blocked**) + 4 Power2 QFN pins + 5 GND (tight — need push-and-shove, which *moves* blocking traces). Snapshot: `*.V4_*`.
- **Why "by hand" works where the autorouter didn't:** KiCad's interactive router uses push-and-shove — dropping a via/trace *relocates* the obstructing traces. FreeRouting (batch) and Python scripts can't move existing traces; that's the whole gap. Each QFN power pin has its decoupling cap (same net) ~1mm away.

### Production-readiness status & the fanout-first finding
Current symmetric board: **0 shorts, 0 crossings, 18 unconnected (hard QFN power pins + USB GND pads), 69 DRC (mostly cosmetic: silk outlines, USB-C mask, courtyard touches, ~19 minor clearance).**
- **Fanout-first works:** on the BARE placement, the power/GND fanout places **112/115 vias including ALL the QFN power pins** that were unreachable after routing (`_connect_fast.py` on bare board). The professional order is vias-first → route signals around them.
- **BUT** `ExportSpecctraDSN` HANGS on script-placed vias (KiCad-9 `PCB_VIA::SetWidth called without a layer argument` → malformed for the Specctra exporter). So the fanout-first board can't be pushed back through FreeRouting. Next session: fix the via construction (KiCad-9 correct width/layer API) so it exports, then fanout-first → route → ~0 unconnected.
- The remaining production finish (18 pads, clock tune, DRC polish) is otherwise **KiCad interactive-router** work (push-and-shove + length tuner), which is the right tool anyway (FreeRouting can't length-match or diff-pair tune).

### Clock length-matching — interactive step
Placement supports equal clocks (IC1 centered, R8/R9 symmetric-capable, U4/U5 symmetric). FreeRouting does NOT length-match (routed 34/82/51mm). A script-based re-route+serpentine got 33.5/33.6/39.8mm but crossed other traces on the dense board → reverted. **Final equalization belongs in KiCad's interactive length-tuner** (push-and-shove), target ≈ the longest path. The matched antenna feeds (the more critical AoA path) are already done.

## Prior status (pre-symmetry, for reference): DRC 527 → 25, USB-C at edge, R11/PS1 clash resolved.

## Final DRC: 25 violations + 12 unconnected (from 527)
- **0 shorts, 0 crossings, 0 keepout, 0 dangling, 0 starved-thermal.**
- **12 unconnected** — all pre-existing: 2 GND zone corner stitching, IC1.6 (/Power2), /MTCK U3.12↔U4.12, /Power1 C9/U3 pads. Each needs a via or short trace (interactive router).
- **11 silk_overlap** — component outline graphics on dense board (cosmetic).
- **6 solder_mask_bridge** — USB-C fine-pitch pads (footprint-inherent).
- **5 clearance** — 3 inductor terminal gaps (footprint-inherent 0.10mm), 2 tight routing spots.
- **3 silk_over_copper** — cosmetic.

## Layout fixes applied (2026-06-20)
1. **USB-C connectors at board edge** — J2/J3/J4 moved from y=108→y=116 (bbox_bottom now flush with board bottom at y=120.17). Cables plug in from the outside cleanly.
2. **Blocking resistors cleared** — R1/R3/R5 moved from y=115.41 (directly in front of port mouth) to y=102 (above connectors, clear of USB access).
3. **R11/PS1 clash resolved** — R11 moved from x=34→x=46 (bbox no longer overlaps PS1; gap now 4mm).
4. **Antenna traces equalized** — ANT2 path had a serpentine meander added (31.70mm vs ANT1 23.62mm feed), making total path lengths equal: ANT1=39.16mm, ANT2=39.22mm (Δ=0.06mm). Critical for AoA direction-finding accuracy.
5. **Full re-route** — FreeRouting re-ran after component moves to reconnect all USB signals (CC, VBUS, D+/D- from J2/J3/J4 to IC2/IC3/IC4). Serpentine preserved by FreeRouting.

## Key fixes this session (the big one in **bold**)
1. **Root cause: re-routed with In1.Cu/In2.Cu marked `(type power)` in the DSN.** FreeRouting had been routing ~176 signal segments (incl. RF feeds & USB pairs) *through* the GND/power planes, swiss-cheesing the reference planes and causing most of the clearance. Now planes are solid; signals only on F.Cu (665) + B.Cu (108).
2. Fixed footprint library path (both fp-lib-tables → `footprints/footprints`, NOT a `.pretty` subdir): 105 lib warnings → 0.
3. Consistent 0.15 mm clearance across net classes (cleared ~136 marginal 0.19 mm FreeRouting artifacts; still > JLC min).
4. Power/GND fanout vias — keepout/NPTH/QFN-outward aware, with stub-crossing checks.
5. Reference designators → F.Fab layer: silk 189 → 17.
6. Zones set to solid pad-connection (killed 7 starved-thermal); min_hole_clearance 0.15 (killed 12 USB hole-clearances).

---

## TL;DR of this session

Took the board from a **broken, non-functional state** (2-layer, no board outline, 1076 DRC violations incl. 148 shorts, and a **dead Hub**) to a properly-architected 4-layer board, mostly routed.

### Critical bug found & fixed
**The Hub ESP32 (U3) had no 3.3 V supply.** Its VDD pins (17/18/31/32) were tied to GND, PS2's output was tied to GND, and the `/Power1` net didn't exist in the PCB netlist. The schematic was actually **correct** (it has `/Power1` wired to PS2.3 + U3 VDD + L1); the PCB had simply never been updated from the schematic. Fixed by re-syncing pad nets from `kicad-cli sch export netlist`. `/Power1` now has 17 pads, Hub is powered. (Two prior agents mislabeled this as a "routing short.")

---

## What was done

1. **Reset** all old routing (1016 trk / 68 via / 5 zones).
2. **4-layer stackup:** F.Cu (sig) / In1.Cu (GND plane) / In2.Cu (split power: /Power2 left, /Power1 right) / B.Cu (sig). F/B have GND pours.
3. **Re-placement:** clean channel floorplan — antennas top (λ/2 = 62.5 mm spacing), RF switches → receivers, Hub right, clock buffer centered (equidistant), USB-C on bottom edge, power isolated bottom-left. Courtyard-clean.
4. **Board outline:** auto-sized rectangle ~139 × 119 mm.
5. **Design rules / net classes:** RF (0.35 mm = 50 Ω microstrip over In1 GND), Clock (0.25 mm), USB (diff), Power (0.5 mm). Default clearance 0.15 mm (JLCPCB-friendly). Project `fp-lib-table` added (footprints embedded anyway).
6. **Routing:** FreeRouting 1.9.0 (Java-17-compatible; jar at `pcb/freerouting19.jar`). GND + Power1 + Power2 exported as **planes** so only signals are routed. Power/GND pads connected to planes via fanout vias + GND stitching.
   - Shorts 148 → 7, crossings 32 → 0.

---

## Remaining work (NOT done — for next agent / interactive KiCad)

**Current DRC: 486 violations = 304 cosmetic + 182 real.**
- **304 cosmetic:** 105 footprint-library-path (stale global `fp-lib-table` → `C:/Users/li107/Downloads/...`; footprints are embedded so the board is fine), 92 silk_overlap + 88 silk_over_copper (ref-designator collisions — run Edit→"Spread reference designators" or hide), 13 USB-connector solder-mask bridges, 6 text_height.
- **182 real:**
  - **31 unconnected** — mostly the **RF nets** (see flaw below) + a few misc (`/MTDO`, `/VBUS3`, `Net-(J2-CC2)`, `Net-(LED1-Pad1)`, `/DebugLED3`, the 3 `/Clock*`).
  - **147 clearance** — many from the 123 power **fanout vias/stubs** placed in tight spots, plus FreeRouting traces routed ~0.13–0.19 mm. Re-route locally or widen.
  - **15 hole_clearance, 11 items_not_allowed (copper in antenna keepouts), 7 shorting_items, 2 starved_thermal.**

### RF pi-network placement — FIXED this session
The auto-clustering had scattered the RF pi-networks; they were re-placed tight & in-path (`_rf_place2.py`): Rx1 `U1→C27→C24→L4→C23→U4.1`, Rx2 `U2→C37→C36→L6→C35→U5.1`, calib `U3.1→C16→L2→C18→C17→/CalLNA`. This let FreeRouting route most RF; ~6 short RF gaps remain (finish in GUI).

### Finishing checklist (interactive KiCad recommended)
1. **Connect remaining 28 ratlines** — QFN power pins to In2 plane (drop a via just outside each pin, away from the center GND pad), the ~6 short RF gaps, `/VBUS2`, and re-place R11 in the power corner clear of J1 then route its `J1-POWER`/`LED1` pads.
2. **Clear the 174 clearance** — push-and-shove re-route the tight FreeRouting traces, or relax board clearance to 0.13 mm (still > JLC min).
3. **Length-match clocks** — FreeRouting routed `/Clock1/2/3` cleanly but unmatched (≈47/36/55 mm). Use the length tuner (target ≈55 mm). NOTE: the calibration path (Hub→switch→each Rx) compensates fixed per-channel skew, so this is a refinement, not a blocker. (My zigzag attempt created crossings in the dense area — `_clock_*` scripts; left direct/clean instead.)
4. **Silk** — Edit → "Spread reference designators" to clear the 183 silk overlaps; fix global `fp-lib-table` to clear the 105 lib-path warnings (footprints are embedded, so cosmetic).

### Then: length-match the clocks
FreeRouting does **not** length-match. `/Clock1/2/3` (IC1 buffer → R10/R8/R9 → U3/U4/U5 pin 30) need equalizing in KiCad's length tuner (target ~the longest, ≈55 mm). Note: the board's calibration path (Hub → switches → each Rx) is designed to calibrate out fixed per-channel offsets, so this is important but not make-or-break.

---

## How to work with this board (important — pcbnew SWIG is flaky)

- KiCad 9.0 Python: `"/c/Program Files/KiCad/9.0/bin/python.exe"`; CLI: `kicad-cli.exe`.
- **SWIG instability:** chained calls (`b.FindNet(n).GetNetCode()`, `z.Outline().NewOutline()`) and mixing `GetFootprints()`/`GetNetInfo()`/`GetTracks()` in one process intermittently return un-typed `SwigPyObject`. Workarounds used: build net-code maps at module top; iterate footprints first right after `LoadBoard`; split read (plan→JSON) and write (apply) into separate processes. See `_fanout_plan.py` / `_fanout_apply.py`.
- **FreeRouting flow:** `python -c "import pcbnew;b=pcbnew.LoadBoard(P);pcbnew.ExportSpecctraDSN(b,'board.dsn')"` → `java -jar freerouting19.jar -de board.dsn -do board.ses -mp 10` → `pcbnew.ImportSpecctraSES(b,'board.ses')`. GND/Power are planes in the DSN (good).
- DRC: `kicad-cli pcb drc --format json -o out.json <pcb>`.
- Render to PNG (no GUI): `kicad-cli pcb render --side top -o x.png <pcb>`.

## Files
- `pcb/10.28.25 V2 Wifi PCB.kicad_pcb` — MAIN (current).
- `pcb/*.kicad_pcb.FRROUTED_*`, `.RFCLK_*`, `.PLACED_*`, `.SAFETY_*` — staged snapshots (newest = most complete).
- `pcb/_*.py` — the rebuild scripts (place / outline / planes / fanout / route).
- `pcb/board.dsn`, `pcb/board.ses` — FreeRouting I/O. `pcb/freerouting19.jar`.
- `DRC*.rpt` (old), `pcb/_drc_*.json` (this session).
