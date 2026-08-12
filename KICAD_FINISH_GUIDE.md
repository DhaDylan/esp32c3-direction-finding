# KiCad Interactive Finish Guide — WiFi Sensing PCB

Goal: take the board from **18 unconnected + 69 DRC** to **0 unconnected + 0 errors**, length-match the clocks, and export manufacturing files. Budget ~45–60 min. No prior KiCad routing experience assumed.

The board file: `pcb/10.28.25 V2 Wifi PCB.kicad_pcb`

---

## 0. One-time setup (2 min)

1. Open the board: in the KiCad project manager, double-click the `.kicad_pcb`, **or** open `pcbnew` and File → Open.
2. Open the live error list: **Inspect → Design Rules Checker → Run DRC.** Leave this window open and docked — every fix you make, click **Run DRC** again to watch the count drop.
3. Turn on the airwires (the thin white "rubber band" lines that show every missing connection): they're on by default. **Each white line = one thing you need to connect.** Your job is to make them all disappear.
4. Useful keys you'll use constantly:
   - **`X`** = start routing a track. Click a start point, click an end point, **`Esc`** to finish.
   - **`V`** = while routing, drop a via (connects to inner layers).
   - **`B`** = re-fill all the copper pours (do this after a batch of edits).
   - **`` ` ``** (backtick) on a pad = highlight that whole net so you can see where it goes.
   - **Ctrl+F** = find a component by name (type `U5`, Enter — it zooms to it).
   - **Ctrl+S** = save.

> **How to connect a power/ground pad to an inner plane:** press `X`, click the pad, move the cursor ~0.5 mm, press **`V`** to drop a via, then **`Esc`**. The via punches down to the GND (In1) or Power2 (In2) plane automatically — same net, so it just connects. That's the whole trick.

---

## 1. The three VBUS pads — easiest, do first (3 min)

Each USB-C connector has two VBUS pads side by side; one is wired, its twin isn't. Just bridge them.

| Find (Ctrl+F) | Pad | Action |
|---|---|---|
| **J2** | B4-A9 | Press `X`, click pad **B4-A9**, click the neighboring **A4-B9** pad (same VBUS, right next to it). `Esc`. |
| **J3** | B4-A9 | Same — bridge B4-A9 → A4-B9. |
| **J4** | B4-A9 | Same — bridge B4-A9 → A4-B9. |

Run DRC → 3 fewer unconnected. ✅

---

## 2. Power2 pad connections (10 min)

These pads need a short trace and/or a via down to the **Power2 plane (In2)**.

| Find | Pad | Action |
|---|---|---|
| **U5** | 17 | Airwire points to a nearby Power2 stub. `X`, click pad **17**, route the ~3 mm to the stub/via, `Esc`. If no via is there: route 1 mm out and press **`V`**. |
| **C14** | 1 | `X`, click **C14 pad 1**, route to the Power2 via just left of it (~3 mm), `Esc`. |
| **R12** | 1 | `X`, click **R12 pad 1**, route to the via at its corner, `Esc`. (R12 is in the bottom-left power cluster.) |
| Two short Power2 gaps near **U4** and **U5** | — | Look for short white airwires hugging the lower edge of each ESP; `X`, click one stub end, click the other. `Esc`. |

After these, press **`B`** to re-fill, Run DRC. ✅

---

## 3. Power1 — R20 (3 min)

**R20 pad 1** (`/Power1`, bottom-left power area) has no path to the hub's Power1.
- `X`, click **R20 pad 1**, follow its airwire and route to the nearest `/Power1` track. `Esc`.
- Power1 is routed as traces (not a plane), so this is just a normal trace — width auto-sets to 0.5 mm.

---

## 4. Two signals: /ControlA and /CS_RX2 (5 min)

| Net | Action |
|---|---|
| **/ControlA** (U3 pad 14) | `X`, click **U3 pad 14**, follow the airwire up to the existing `/ControlA` track near the hub (~(87, 53)), click it. `Esc`. |
| **/CS_RX2** (near U5) | Two `/CS_RX2` segments don't meet near (56, 60). `X`, click one open end, click the other. `Esc`. |

---

## 5. The 5 GND "islands" (5 min)

The top-layer ground pour got chopped into a few small patches that aren't tied to the main ground plane. Each shows as a short white GND airwire.
- For each one: hover over the **isolated copper patch**, press `X`, click once inside it, immediately press **`V`** to drop a via, `Esc`. The via ties that patch to the solid In1 ground plane.
- Then press **`B`** to re-fill. Run DRC — the GND unconnected should clear.

> If you can't see them: in the DRC window, click each "Unconnected items → GND" entry; KiCad zooms to it. Drop a via there.

**At this point: 0 unconnected.** Save (Ctrl+S).

---

## 6. Clearance cleanup (~19 items, 10 min)

These are mostly fanout vias sitting ~0.1 mm too close to a trace. In the DRC window, double-click each **"clearance"** entry to jump to it, then:
- **Click the via** and nudge it 0.3–0.5 mm away from the trace (drag, or arrow keys), OR
- Click the **trace** and drag that segment over slightly.

The push-and-shove router will keep things legal as you drag. Re-run DRC after a few. Most clear instantly.

---

## 7. Length-match the clocks (10 min) — the part FreeRouting can't do

Current lengths (IC1 → ESP pin 30):
- **Hub /Clock1 = 34.5 mm**
- **CH1 /Clock2 = 82.0 mm**  ← the autorouter took a detour
- **CH2 /Clock3 = 51.4 mm**

**Step A — fix the CH1 detour first.** Click a `/Clock2` segment, press `Delete` to rip up that net, then re-route it directly: `X` from **IC1 pin 8 → R8 → U4 pin 30**. It should come out ~35 mm.

**Step B — tune all three to the same length.** Pick **target = 52 mm** (the longest clean one).
1. Route menu → **"Tune length of a single track"** (or the meander icon in the right toolbar).
2. **Right-click → Length Tuning Settings**, set **Target length = 52 mm**.
3. Click the `/Clock1` track and drag along it — KiCad adds accordion wiggles and shows a live readout (turns green at target). Do the same for `/Clock2` and `/Clock3`.

All three now ≈ 52 mm → matched clock skew across the three ESPs. (The antenna feeds are already exactly equal, so this completes the timing match.)

Press `B`, Ctrl+S.

---

## 8. Optional cosmetic polish (skip if short on time)

These are **warnings, not fab-blockers** — JLCPCB will build the board with them. Fix only if you want a clean DRC:
- **Silk overlaps (~20):** ref-designator/outline text touching. Select the silk text, nudge it, or hide it (right-click → Properties → uncheck Visible).
- **Courtyard touches (18 pairs):** parts whose keep-out zones overlap by a hair (they don't physically collide). Nudge one part 0.3 mm if you care. Pairs to check: `C1/C2`, `C21/C28`, `C33/C38`, `C4/C2`, `C4/C5` (decoupling rows), `R5/J4`, `R6/J4`, `R3/J3`, `R4/J3`, `R1/J2`, `R2/J2` (CC resistors by USB), `C14/U4`, `C9/U3`, `C33/U5` (caps by the ESPs), `PS1/R12`, `PS1/R15`, `C3/PS2`, `PS2/R14` (power corner).
- **USB-C solder-mask bridges (7):** inherent to the connector footprint's fine pitch — **leave them**, the manufacturer handles it.

---

## 9. Export for manufacturing (5 min)

Once DRC shows **0 errors** (warnings OK):
1. **File → Fabrication Outputs → Gerbers (.gbr)** → select all copper + silk + mask + edge layers → Plot.
2. In the same dialog: **Generate Drill Files** → Excellon.
3. **File → Fabrication Outputs → Component Placement (.pos)** for assembly.
4. **Tools → Generate Bill of Materials** for the BOM.
5. Zip the Gerbers + drill and upload to JLCPCB/PCBWay for a quote.

Your board is 4-layer, 0.15 mm clearance, 0.3 mm min drill — all within standard/cheap fab limits.

---

## Quick reference — what each unconnected item is

| # | Item | Section |
|---|---|---|
| 1–5 | GND zone islands | §5 — drop a via in each |
| 6,7,9 | R12.1, C14.1 (Power2) | §2 — trace to via |
| 8,10,11 | U5.17 + Power2 stub gaps | §2 |
| 12,13,14 | J2/J3/J4 B4-A9 (VBUS) | §1 — bridge to twin pad |
| 15 | U3.14 /ControlA | §4 |
| 16 | /CS_RX2 gap | §4 |
| 17,18 | R20.1 /Power1 | §3 |

When all white airwires are gone and DRC = 0 errors, you're production-ready.
