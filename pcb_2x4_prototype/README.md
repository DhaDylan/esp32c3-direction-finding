# 2×4 Array Prototype — VISUAL MOCKUP ONLY

An ESPARGOS-style 2-row × 4-column phased array, built to see how the scaled-up
board would look. **This is not a manufacturable design.**

This directory is fully self-contained. The working 1×2 design in [`../pcb/`](../pcb/)
is untouched and remains the reference design.

## What this is

| | |
|---|---|
| Array | 8 antennas, 2 rows × 4 columns |
| Spacing | 62.5 mm (λ/2 @ 2.4 GHz) in **both** axes — verified exact |
| Board | 262 × 170 mm, landscape |
| Per channel | Chip antenna, DC block, RF switch, π-network, ESP32-C3, 8 decoupling caps, clock series R, debug LED |
| Controller strip | Bottom edge — controller ESP32, 40 MHz crystal, clock fanout, USB-C + ESD, barrel jack, 2× 3V3 regulator |
| Footprints placed | 168 |

## What this is NOT

- **No nets, no routing, no copper pours.** Footprints are placed to scale in the
  correct geometry; nothing is electrically connected.
- **No DRC.** It will not pass, and is not meant to.
- The clock fanout is drawn as three cascaded 1:3 buffers (`IC1`–`IC3`) purely to
  occupy the right area. A real build wants a **single-die 1:8/1:10 fanout** so all
  outputs are skew-matched by construction — cascading adds per-stage delay that
  varies with part, temperature, and voltage.
- The controller needs **8 chip selects** and the ESP32-C3 does not have the free
  GPIOs. A real build wants a 74HC138 3→8 decoder.

## Regenerating

The board file is generated, not hand-edited. Edit the geometry constants at the
top of the script and re-run:

```sh
"C:/Program Files/KiCad/9.0/bin/python.exe" build_2x4_mockup.py
```

Renders (written to [`../renders/`](../renders/)):

```sh
kicad-cli pcb render -o ../renders/proto2x4_top.png --side top \
    --quality high --floor --width 2400 --height 1600 2x4_array_mockup.kicad_pcb

kicad-cli pcb render -o ../renders/proto2x4_iso.png --rotate=315,0,45 --perspective \
    --quality high --floor --width 2400 --height 1600 2x4_array_mockup.kicad_pcb
```

3D models resolve via `../3dmodels/3dmodels/`, so the paths work on any machine
that clones the repo.

## Before this becomes real

The riskiest assumption in the architecture — driving the ESP32's `XTAL_P` from a
clock buffer — is still unvalidated on hardware and is not an Espressif-supported
configuration. That should be proven on the existing 3-chip board before
committing to a 9-chip board this size. See `../AGENT_HANDOFF.md`.
