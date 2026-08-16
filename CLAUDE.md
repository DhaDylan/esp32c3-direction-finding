# CLAUDE.md — ESP32-C3 WiFi Sensing / Direction-Finding

Guidance for agents working in this repo. Read this before touching a board file.

## What this project is

A **phase-coherent WiFi channel sounder** built from multiple ESP32-C3 chips. Each
chip extracts Channel State Information (CSI) from received WiFi packets. Because
all chips share one clock reference, the *phase differences* between their antennas
are meaningful — which is what makes angle-of-arrival (AoA) direction finding and
WiFi sensing possible.

The project closely follows **[ESPARGOS](https://espargos.net/)** (Univ. Stuttgart —
[paper](https://arxiv.org/pdf/2502.09405)), which is a 2×4 array of ESP32-S2 chips.
This project uses **ESP32-C3** instead.

**The core physical idea:** two antennas spaced λ/2 apart see the same incoming
signal at slightly different times. That time difference shows up as a phase
difference, and the phase difference tells you the arrival angle. Everything in the
hardware exists to make sure the *only* phase difference you measure is the real
one from the air — not one accidentally introduced by mismatched clocks or traces.

- λ @ 2.4 GHz = 125 mm → **λ/2 = 62.5 mm**. This number sets antenna spacing on
  every board here and is not negotiable.

## The two PCB designs — different goals, keep them separate

| | [`pcb/`](pcb/) | [`pcb_2x4_prototype/`](pcb_2x4_prototype/) |
|---|---|---|
| **Name** | `10.28.25 V2 Wifi PCB.kicad_pcb` | `2x4_array_mockup.kicad_pcb` |
| **Goal** | **Reference design.** Real, near-fabricable board to validate the architecture | **Visual mockup.** See how the scaled array looks |
| **Array** | 1×2 (2 receivers + hub) | 2×4 (8 receivers + controller) |
| **Size** | 139 × 119 mm portrait-ish | 262 × 170 mm landscape |
| **Routed?** | Yes — 4-layer, 23 DRC violations, 3 unconnected | **No.** No nets, no routing, no pours |
| **Status** | Close to fabricable | Not manufacturable, not meant to be |

**These are independent. Do not merge them.** `pcb/` is the fallback the user wants
preserved. If asked to change the array, work in `pcb_2x4_prototype/` (or a new
directory) and leave `pcb/` untouched.

---

## Board 1 — `pcb/` (1×2 reference design)

The working design. 3× ESP32-C3 (QFN32 5×5): one **hub** (U3) and two **receivers**
(U4 = CH1, U5 = CH2).

**Stackup (4-layer):** `F.Cu` signal / `In1.Cu` solid GND plane (RF reference) /
`In2.Cu` signal + GND zone / `B.Cu` signal.

**Net classes:** Default 0.2 mm · Clock 0.25 · RF 0.35 (50 Ω microstrip over In1) ·
USB 0.25 diff · Power 0.5. Clearance 0.15 mm throughout (JLCPCB-friendly).

**Symmetry is the whole point.** CH2 (U5) @ x=52 and CH1 (U4) @ x=114.5 are a *pure
+62.5 mm translation* — every CH1 trace has an identical CH2 counterpart, so channel
timing matches by construction. Hub centered at x=83.25, clock source centered above
it. Defined in [`pcb/_symmetry_place.py`](pcb/_symmetry_place.py). **Antenna feeds are
length-matched to 0.00 mm.** Preserve this symmetry in any edit.

### Key components

| Ref | Part | Role |
|---|---|---|
| U3 | ESP32-C3 | Hub / controller |
| U4, U5 | ESP32-C3 | Receiver CH1, CH2 |
| U1, U2 | HMC221BE (`RJ-6_ADI`) | RF switch per channel (antenna ↔ cal path) |
| IC1 | CDCLVC1103PW | 1:3 clock fanout buffer |
| Y1 | 40 MHz crystal | Clock source |
| R8/R9/R10 | 22 Ω | Clock series termination |
| PS1 / PS2 | TSR_2-2433N (2 A) | 3V3 for receivers / for hub |
| ANT1, ANT2 | WDP.2458.25.4.B.02 | Chip antennas, 62.5 mm apart |

---

## Board 2 — `pcb_2x4_prototype/` (2×4 array mockup)

**Generated, not hand-edited.** Edit the constants at the top of
[`build_2x4_mockup.py`](pcb_2x4_prototype/build_2x4_mockup.py) and re-run it with
KiCad's bundled Python. Hand-editing the `.kicad_pcb` will be overwritten.

### Physical specifications

| Property | Value |
|---|---|
| **PCB size** | **262 × 170 mm**, landscape |
| **Array** | 8 antennas, **2 rows × 4 columns** |
| **Antenna spacing** | **62.5 mm (λ/2 @ 2.4 GHz) in BOTH axes** — verified exact |
| Antenna grid | Columns x = 42, 104.5, 167, 229.5 · Rows y = 22, 84.5 |
| Footprints | 168 placed |
| Per channel | Antenna, DC block, RF switch, π-network, ESP32-C3, 8 decoupling caps, clock series R, debug LED |
| Controller strip | Bottom edge, y ≈ 140–172 |

Each receiver occupies a 62.5 × 62.5 mm cell with its antenna at the top of the cell
and its ESP32-C3 directly behind it.

### How everything communicates

Four independent signal domains. Understanding these is the key to the whole design:

```
                    ┌──────────── 40 MHz crystal (Y1)
                    ↓
              ┌─ clock fanout buffer ─┐         (1) CLOCK / PHASE REFERENCE
              ↓    ↓    ↓  ...  ↓     ↓         one clock, all 9 chips
           22Ω  22Ω  22Ω      22Ω   22Ω
            ↓    ↓    ↓        ↓     ↓
         XTAL_P of RX1..RX8 + controller

  CONTROLLER ──── SPI: MTCK/MTDO/MISO shared ────┐  (2) CSI DATA BACKHAUL
      │           + one chip-select per RX       │  controller = master
      │              (needs 74HC138 3→8)         ↓
      │                                    RX1 .. RX8
      │
      ├──── ControlA / ControlB ──→ all 8 RF switches   (3) RF SWITCH CONTROL
      │                                                 flips antenna ↔ cal
      │
      └──── /CalLNA ──→ shared into every RF switch     (4) CALIBRATION PATH
                                                        common known-length ref
```

**(1) Clock / phase reference.** One 40 MHz crystal feeds a fanout buffer, which
drives the `XTAL_P` pin of every ESP32 through a 22 Ω series resistor. This makes all
chips *frequency*-synchronous. Clock trace lengths must be matched — any skew appears
directly as a phase offset in the AoA math.

**(2) CSI data backhaul.** The controller is SPI master. `MTCK`/`MTDO`/`MISO` are a
shared bus; each receiver gets its own chip-select. The controller triggers the
receivers to sample together and collects their CSI.

**(3) RF switch control.** Two GPIOs (`ControlA`, `ControlB`) drive *all* RF switches
simultaneously, flipping every channel between "listen to my antenna" and "listen to
the shared calibration signal."

**(4) Calibration path.** `/CalLNA` is a common signal fed to the second input of
every RF switch over a known, matched path. Switch all channels onto it and any
measured phase difference is *pure hardware skew*, not a real angle — record it,
switch back to antennas, subtract. This is what corrects PLL phase ambiguity (which
is random on every boot) and residual channel mismatch.

### Two things the mockup stubs — fix before this is real

1. **Clock fanout.** Drawn as three cascaded 1:3 buffers to occupy the area.
   Cascading adds per-stage propagation delay that varies with part, temperature, and
   voltage — exactly the skew this design fights. Use a **single-die 1:8 or 1:10
   fanout** (e.g. CDCLVC1310) so all outputs are matched by construction.
2. **Chip selects.** 8 receivers need 8 chip-selects; the ESP32-C3 controller does not
   have the free GPIOs (pads 19–24 are embedded-flash SPI and off-limits). Use a
   **74HC138 3→8 decoder**.

---

## Open issues and risks

**Architectural risk (unresolved, blocks everything):** driving `XTAL_P` from a clock
buffer is **not an Espressif-supported configuration** — that pin normally drives a
crystal oscillator inverter, not accepts a 3.3 V logic-level clock. The 22 Ω series
resistors may not tame it enough. **This must be validated on a scope on the existing
3-chip board before committing to a 9-chip board.** If it fails, the fallback is
per-chip crystals, which destroys the shared-clock premise and changes the entire
array architecture.

**Open items on `pcb/`** (from `Schematic_Review_ESP32C3_DirectionFinding.docx`, state
verified against the current netlist):

- `C46`/`C47`/`C48` (100 nF) still sit on **GPIO9**, a boot strapping pin. Espressif
  explicitly warns against capacitance here — risks the chips entering download mode
  on every power-up. Should be removed.
- `C43`/`C44`/`C45` on `CHIP_EN` are 100 nF; Espressif recommends **1 µF** for the RC
  reset delay.
- `U3` pad 11 (`VDD3P3_RTC`) reads as unconnected. That is a supply pin, not a GPIO —
  worth confirming against the datasheet.
- Net labels `/ControlA` and `/ControlB` are **inverted** relative to the HMC221BE
  datasheet pin names (A/B). No functional impact; will confuse firmware.
- Clock traces `/Clock1/2/3` are **not length-matched** yet. Needs KiCad's interactive
  length tuner (FreeRouting cannot length-match).

Already fixed — do not "re-fix" these: the `/Power1` hub supply short, U3's VDD pins,
the shared `/SPICLK` bus, and U5's dangling SPID/SPIQ.

## Tooling

```sh
KiCad CLI     "C:/Program Files/KiCad/9.0/bin/kicad-cli.exe"
KiCad Python  "C:/Program Files/KiCad/9.0/bin/python.exe"   # NOT system python
```

```sh
# DRC
kicad-cli pcb drc --format json -o out.json <pcb>

# 3D render (populates component models)
kicad-cli pcb render -o x.png --side top --quality high --floor <pcb>
kicad-cli pcb render -o x.png --rotate=315,0,45 --perspective --quality high --floor <pcb>
```

Note `--rotate` needs `=` (`--rotate=315,0,45`); a space makes the parser reject a
leading-minus value.

**3D models** live in [`3dmodels/3dmodels/`](3dmodels/3dmodels/) and are referenced as
`../3dmodels/3dmodels/<file>` so they resolve on any clone. Files named `generic_*`
are KiCad standard-library stand-ins where no manufacturer model was available —
visually correct, not mechanically authoritative.

### Gotchas that will waste your time

- **pcbnew SWIG is flaky.** Chained calls (`b.FindNet(n).GetNetCode()`) intermittently
  return untyped `SwigPyObject`. Build lookup maps at module top; iterate footprints
  immediately after `LoadBoard`; split read (plan→JSON) and write (apply) into
  separate processes.
- **`ExportSpecctraDSN` hangs** when an inner copper layer has no zone, and on
  script-placed vias. Keep a zone on every inner layer.
- **FreeRouting cannot length-match or tune diff pairs.** Final clock equalization is
  interactive KiCad work (push-and-shove length tuner).
- The `.kicad_pcb` files use **CRLF** line endings — match them when patching text.

## Files

- [`AGENT_HANDOFF.md`](AGENT_HANDOFF.md) — detailed session history of the `pcb/`
  rebuild, and why specific decisions were made. Read for deep layout context.
- `Schematic_Review_ESP32C3_DirectionFinding.docx` — automated netlist review
  (June 2026). Some findings are now stale; see "Open issues" above for current state.
- [`pcb/_*.py`](pcb/) — the placement/routing/fanout scripts that built the 1×2 board.
- [`renders/`](renders/) — 3D renders of both boards.
