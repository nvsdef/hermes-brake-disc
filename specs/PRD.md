---
document: PRD-FR330V-H1
title: FR-330V vented front brake - product and analysis requirements
revision: H1.2
derived_from: CTS-BRK-0117 rev C (fictional, illustrative)
status: authoritative for every run of this package
---

# FR-330V vented front brake - PRD (revision H1.2)

> **Fictional, educational design.** Not a real vehicle, product or safety
> certification. This PRD is the **only** authority for geometry, loads and
> acceptance in a run. The CTS in `docs/source/` is background: where it and
> this PRD differ, **this PRD wins** (the differences are listed in section 10).

**Conventions used everywhere in this document**

- Lengths are **millimetres** unless a unit says otherwise. SolidPilot works in
  **metres**: convert once, at the tool call (`mm / 1000`).
- Ranges are written `a to b` with ASCII minus signs: `z = -16 to -6` means the
  interval from minus sixteen to minus six.
- **Z is the shaft axis.** Origin at the vent mid-plane. **+Z points outboard**
  (towards the wheel and the mounting face). Pads are centred on **+X**.
- Angles are **degrees**, measured from +X towards +Y (counter-clockwise viewed
  from +Z).
- "Checksum" = an independently computed number the built CAD must match. Every
  checksum in section 4 was computed from the geometry in section 3 by two
  independent methods that agree within 0.01 %.

---

## 1. What is being built

A vented Ø330 mm grey-iron brake rotor with an integral hat, one pair of pads with
steel backing plates, and a scalloped calliper that clears the pad stack. The
assembly is **9 components (6 part files, 3 of them used twice) containing 28
solid bodies**, built in SolidWorks,
prepared in SpaceClaim, and solved in Fluent as a transient solid-conduction
model of **one** braking stop.

```
   side section (r horizontal, z vertical, not to scale)

   z=+43  ___________  mounting face, bore Ø70, 5 x Ø14 on Ø115 PCD
         |   HAT     |
         |  flange   |  z = +33 to +43
         |___   _____|
             | |  hat wall (r ~ 74 to 88)           calliper end wall z +38.6 to +57
             | |                               ____________________
   z=+34     | |                    bp_outer  |______________|     |
   z=+28     | |                    outerpad  |______________|     |
   z=+16     | |  ________________cheek_out___________________     |
   z=+6      | | |________________________________________    |    |
   z=-6      | | |  20 curved vanes (vent gap 12)         |   |    |
   z=-16     |_|_|________________cheek_in________________|   |    |
             hat web lands on INBOARD cheek at r = 95        |    |
   z=-28                            innerpad  |______________|     |
   z=-34                            bp_inner  |______________|_____|
                                                calliper end wall z -39 to -57
            r=35   r=95                         r=165   r=178 slot   r=200 lobes
```

---

## 2. Parts, bodies and placement

Build every part file **at its true global position**. The six outboard-built
parts are assembled with **identity transforms**. The three inboard bodies are
**instances of their outboard twin rotated 180 deg about +X** (transform
`[1,0,0,0,-1,0,0,0,-1,0,0,0,1]`): the rotation maps (x, y, z) to (x, -y, -z), and the
cheek (an annulus) and the pad and plate (sectors symmetric about y = 0) land
exactly on their inboard bands. Nothing is moved after it is built.

| # | Body (PRD name) | Built as | Bodies | Cross-section | Axial band (z) | Material |
|---|---|---|---|---|---|---|
| 1 | `cheek_out` | part `cheek_out` | 1 | annulus r = 95 to 165 | +6 to +16 | MAT-01 grey iron |
| 2 | `cheek_in` | instance of `cheek_out`, flipped | 1 | annulus r = 95 to 165 | -16 to -6 | MAT-01 grey iron |
| 3 | `vanes` | part `vanes` | **20** | curved strips, section 3.2 | -6 to +6 | MAT-01 grey iron |
| 4 | `hat` | part `hat` | 1 | revolved polygon + 5 bolt holes, section 3.3 | -16 to +43 | MAT-01 grey iron |
| 5 | `outerpad` | part `outerpad` | 1 | sector r = 120 to 160, angle -30 to +30 | +16 to +28 | MAT-02 pad |
| 6 | `innerpad` | instance of `outerpad`, flipped | 1 | sector r = 120 to 160, angle -30 to +30 | -28 to -16 | MAT-02 pad |
| 7 | `bp_outer` | part `bp_outer` | 1 | sector r = 115 to 165, angle -30 to +30 | +28 to +34 | MAT-03 steel |
| 8 | `bp_inner` | instance of `bp_outer`, flipped | 1 | sector r = 115 to 165, angle -30 to +30 | -34 to -28 | MAT-03 steel |
| 9 | `calliper` | part `calliper` | 1 | scalloped body, section 3.4 | -57 to +57 | (not solved) |
| | **Total** | 6 part files, 9 components | **28** | | | |

`brake.step` therefore holds **25** `MANIFOLD_SOLID_BREP` (one per unique body:
cheek 1, vanes 20, hat 1, pad 1, plate 1, calliper 1), **7** PRODUCT (6 parts +
the assembly) and **9** `NEXT_ASSEMBLY_USAGE_OCCURRENCE`; SpaceClaim expands the
occurrences to **28** bodies. Verified on 2026-11-02 (SolidWorks transform
readback, STEP counts, SpaceClaim placement, Fluent zone names).

Rules that apply to every part:

- **One part file per built part.** Only `vanes` holds more than one body. The
  rotor parts stay **separate bodies** - never merge cheeks, vanes and hat.
- Touching parts **abut exactly** (shared faces, zero overlap volume). These
  contacts become the solver's thermal interfaces.
- Make the inboard bodies only by the flipped instance above. Never copy a file
  and edit its plane offset (`modify_dimension` drops the sign), and never use a
  mirror feature (it makes a second body inside one file).
- In SpaceClaim, an instanced body shares its master: renaming one renames both,
  and **deleting one deletes both**. Only the calliper (not instanced) is ever
  deleted. Names reach Fluent through named selections, not body names.

---

## 3. Geometry definitions

### 3.1 Cheeks
Two flat annuli, r = 95 to 165, each 10 mm thick: `cheek_out` z = +6 to +16,
`cheek_in` z = -16 to -6. Both must be **exactly axisymmetric** (no holes, no
features): the solver spins them with a solid-motion model that is only valid for
axisymmetric bodies.

### 3.2 Vanes (20 bodies)
Each vane is the region **between two concentric circles** of radius 117 and 123
centred at **C = (20.722, 94.249)**, trimmed radially to **r = 95 to 165**.

- The circle band crosses the rotor annulus on two branches. Keep the branch whose
  polar angle **increases** with radius: about **-2.3 to +2.3 deg at r = 95**,
  **+29.8 to +33.4 deg at r = 165**. The other branch (about 153 to 158 deg at
  r = 95) is wrong.
- Vane k (k = 1 to 20) is vane 1 rotated by **(k - 1) x 18 deg** about Z: one
  closed profile per vane, with the rotated coordinates pre-computed in the
  SolidWorks skill's sketch cards R2 to R5 (never computed by hand in a run). **Do not use a
  circular-pattern feature** (see the SolidWorks skill: it reports 20 and makes 1).
- Extrude 12 mm **mid-plane** about z = 0 (z = -6 to +6), then trim to the exact
  r = 95 and r = 165 cylinders so the vane ends are true cylindrical faces that sit
  conformally against nothing but air.
- Handedness: the vanes sweep towards +theta as r increases. The rotor therefore
  runs **clockwise viewed from +Z** (negative omega about +Z). See section 5.

### 3.3 Hat
Revolve this closed polygon, given as (z, r) pairs, 360 deg about Z:

`(43, 35) -> (43, 86) -> (-6, 88) -> (-6, 95) -> (-16, 95) -> (-16, 78) -> (33, 74) -> (33, 35) -> close`

Then cut **five Ø14 through-holes** on a **Ø115 PCD** (hole centres at r = 57.5,
angles 0, 72, 144, 216, 288 deg) through the mounting flange z = +33 to +43.

- Centre bore Ø70 (r = 35). Mounting face at **z = +43**.
- The web lands on the **inboard** cheek: the hat's cylindrical face r = 95,
  z = -16 to -6 abuts the bore of `cheek_in`.
- The hat stops at z = -6 below r = 95, so the vent inlet (r = 95, z = -6 to +6)
  is open. The radial gap between the hat wall (r ~ 88) and the vane roots (r = 95)
  is about 7 mm.
- SolidPilot revolves with `extrude_feature(feature_type='revolve', ...)`. Verify
  the hat lands at z = -16 to +43 by measuring. Do not trust a reverse flag.

### 3.4 Calliper (1 body)
1. **Base** (z = -57 to +57): union of a sector r = 98 to 176, angle -34 to +34,
   and three R40 circles centred at r = 160, angles -20, 0, +20 deg.
2. **Pad slot** (z = -39 to +38.6): remove sector r = 90 to 178, angle -42 to +42.
3. **Windows** (the **same** z = -39 to +38.6): remove r = 90 to 215 over the angle
   ranges -42 to -27, -7 to +7 and +27 to +42.
4. **Outer-bridge step**: remove r = 172 to 215 (full circle) for z = +42 to +57
   and z = -57 to -42. That is 15 mm in from each axial face.
5. **Piston bores**: six Ø26 blind bores centred at r = 140, angles -20, 0, +20.
   Three go from the slot face z = +38.6 **outward** to z = +46.6. Three go from
   z = -39 outward to z = -47. Each is 8 mm deep.
6. No fillets, no chamfers.

The result is **one connected solid**. In the slot band (z = -39 to +38.6) the only
material left is two bridges at r > 178, between the windows.

### 3.5 Pads and backing plates
Sectors centred on +X, angle -30 to +30 deg. Pad friction faces sit **exactly** on
the cheek faces (z = +16 and z = -16). Backing plates sit exactly on the pad backs
(z = +28 and z = -28).

---

## 4. Checksums - the numbers the CAD must hit

Tolerance: **volume within 1 %**, **centroid within 0.1 mm**, **bbox within
0.05 mm**. If any number misses, the part is wrong: stop, repair it, and re-measure.
Never proceed on a miss. SolidPilot reports m^3 and m. Values here are mm^3 and mm.

| Body | Volume mm^3 | Volume m^3 | Centroid (x, y, z) mm | Bounding box / extents mm |
|---|---|---|---|---|
| cheek_out | 571 769.86 | 5.717699e-4 | (0, 0, +11.000) | x,y = -165 to 165; z = +6 to +16 |
| cheek_in | 571 769.86 | 5.717699e-4 | (0, 0, -11.000) | x,y = -165 to 165; z = -16 to -6 |
| vane (each) | 7 251.63 | 7.251627e-6 | vane_01: (123.842, 40.040, 0) | vane_01: x = 94.922 to 143.121, y = -3.850 to 90.942, z = -6 to +6 |
| vanes (all 20) | 145 032.55 | 1.450325e-4 | (0, 0, 0) | each vane centroid at r = 130.154, angle 17.917 + (k-1) x 18 deg |
| hat (after holes) | 513 204.29 | 5.132043e-4 | (0, 0, +18.095) | x,y = -95 to 95; z = -16 to +43 |
| hat (before holes) | 520 901.19 | 5.209012e-4 | | polygon area 1139.0 mm^2 |
| outerpad | 70 371.68 | 7.037168e-5 | (134.600, 0, +22.000) | z = +16 to +28 |
| innerpad | 70 371.68 | 7.037168e-5 | (134.600, 0, -22.000) | z = -28 to -16 |
| bp_outer | 43 982.30 | 4.398230e-5 | (135.111, 0, +31.000) | z = +28 to +34 |
| bp_inner | 43 982.30 | 4.398230e-5 | (135.111, 0, -31.000) | z = -34 to -28 |
| calliper | 617 081.48 | 6.170815e-4 | (146.143, 0.000, +0.369) | x = 81.245 to 200.000; y = -98.418 to 98.418; z = -57 to +57 |
| **rotor** (cheeks + vanes + hat) | 1 801 776.57 | 1.801777e-3 | | mass at 7200 kg/m^3 = **12.973 kg** |

Vane section area is 604.302 mm^2. The older quoted value, 604.2333, is from a
polygonal approximation. Both are inside tolerance.

**Calliper section-area checks.** Use these to localize a calliper miss by band:

| Section area mm^2 | z band | What is cut in this band |
|---|---|---|
| 11 891.10 | -57 to -47 and +46.6 to +57 | outer-bridge step |
| 10 298.32 | -47 to -42 and +42 to +46.6 | step + piston bores |
| 15 050.62 | -42 to -39 and +38.6 to +42 | piston bores only |
| 2 310.76 | -39 to +38.6 | pad slot + windows |

**Contacts and clearances (checks, not choices)**

| Pair | Contact type | Expected area / clearance |
|---|---|---|
| outerpad / cheek_out, innerpad / cheek_in | face, z = +/-16 | 5 864.31 mm^2 each |
| outerpad / bp_outer, innerpad / bp_inner | face, z = +/-28 | 5 864.31 mm^2 each (the pad face) |
| each vane / cheek_out and / cheek_in | face, z = +/-6 | 604.30 mm^2 each, 40 contacts |
| hat / cheek_in | cylinder r = 95, z = -16 to -6 | 5 969.03 mm^2 |
| hat / vanes | edge only at r = 95, z = -6 | **no face contact** |
| pad stack / calliper slot, axial | 34 vs 38.6 and -34 vs -39 | 4.6 mm outboard, 5.0 mm inboard |
| pad stack / slot height | slot 77.6 vs stack 68 | +9.6 mm (PAD-05 needs >= +4) |
| rotor OD / slot inner radius of bridges | 165 vs 178 | 13.0 mm |
| hat wall / calliper end wall | r 86.18 at z = +38.6 vs r = 98 | 11.8 mm |
| interference anywhere | | **0 mm^3** |

**Expected thermal surface groups** (SpaceClaim uses these to check its work):

| Group | Composition | Before imprint mm^2 (SpaceClaim, Gate 2) | After imprint mm^2 (Fluent mesh, Gate 3) |
|---|---|---|---|
| wall-vent | 2 cheek inner faces (z = +/-6) + 20 vane flanks and ends | **167 037.60** | **142 865.51** (less 40 vane footprints) |
| wall-outer | cheek outer faces, OD, cheek_out bore, all exposed hat faces incl. the hat step face z = -6, r = 88 to 95 | **240 205.78** | **228 477.17** (less 2 pad footprints) |
| pad/backing exposed | pad arcs and sides, both backing faces, arcs and sides | **42 997.28** | **31 268.67** (less 2 pad footprints) |

SpaceClaim tags whole faces, so a face that is partly a contact is tagged in full
(the "before" column). Contact faces that are **entirely** contact (hat r = 95
cylinder, cheek_in bore, pad friction and back faces) are left untagged. Shared
topology in Fluent Meshing cuts the footprints out (the "after" column). The hat
step face at z = -6 belongs to `wall-outer`, by decision.

---

## 5. Duty cycle - derive it first, show the arithmetic

Inputs: mass **1800 kg**; entry speed **100 km/h**; deceleration **0.8 g** with
**g = 9.80665 m/s^2**; front axle bias **0.70**; **two** front rotors; rolling
radius **0.33 m**.

| Quantity | Formula | Expected value |
|---|---|---|
| v0 | 100 / 3.6 | 27.7778 m/s |
| a | 0.8 g | 7.84532 m/s^2 |
| stop time ts | v0 / a | **3.54068 s** |
| stopping distance | v0^2 / (2a) | 49.176 m |
| energy per front rotor E | 0.5 m v0^2 x 0.70 / 2 | **243 055.6 J** |
| mean power | E / ts | 68 646.6 W |
| peak power (t = 0) | 2E / ts | 137 293.1 W |
| wheel speed | v0 / 0.33 | 84.1751 rad/s (803.8 rpm) |
| omega0 (signed, about +Z) | clockwise viewed from +Z | **-84.1751 rad/s** |
| omega_ref for h scaling | (2/3) abs(omega0) | 56.1167 rad/s |
| pad contact area A (each) | (pi/6)(0.160^2 - 0.120^2) | 5.864306e-3 m^2 |
| layer heat source, peak | P(0) / (2 A d), d = 0.002 m | 5.8529e9 W/m^3 |
| layer heat source, mean | Pmean / (2 A d) | 2.9265e9 W/m^3 |
| time steps at dt = 0.01 s | ts / dt | 354 full steps **plus** a final 0.000681 s step (ts - 3.54) |
| sanity: bulk rotor rise if all E stayed in the rotor | E / (m_rotor x cp) | about 41.9 K |

Power history: `P(t) = (2E/ts)(1 - t/ts)` for `0 <= t <= ts`, then zero.
Speed: `omega(t) = omega0 x max(0, 1 - t/ts)`.

---

## 6. Analysis definition

- **Physics.** Transient heat conduction in **27 solid zones** (the calliper is
  deleted from the simulation copy). Energy equation on, flow equations off, no
  fluid domain. Double precision. Initial and ambient temperature 300 K.
- **Heat input.** A frictional heat source in a virtual wall layer of thickness
  d = 0.002 m, on **one side only** of each of the two pad/cheek contacts. The
  layer material is **grey iron (MAT-01 values)**; never Fluent's default
  aluminium. Scale q''' with the closed-form A of section 5, then integrate the
  applied power with the **measured** mesh contact areas: that integral must equal
  E within **+/-2 %** (DV-05). The layer is a modelling assumption, not a physical
  interface.
- **Rotation.** Only `cheek_out` and `cheek_in` get solid motion,
  omega(t) about +Z through the origin. **Never** rotate the vanes or the hat with
  this model (they are not axisymmetric). Pre-solve check: the integral of
  abs((ez x r) . n) dA over the rotating boundaries must be <= 1.592987e-4 m^3/s
  per rad/s (it is zero for a true axisymmetric cheek).
- **Convection (prescribed inputs, not solved airflow).** Reference h at
  omega_ref: vent faces 130, outer rotor/hat faces 85, exposed pad/backing faces
  40 W/(m^2 K). Scale with speed:
  `h(t) = max(7, h_ref x (abs(omega(t)) / omega_ref)^0.8)`.
- **Mesh starting point.** Global size 2.2 to 20 mm, growth 1.2, curvature angle
  18 deg. Local sizes: cheeks 4 mm, vanes 5 mm, hat 8 mm. Poly-hexcore, no
  inflation, shared topology, all regions solid.
- **Mesh gates.** 27 solid zones, 0 fluid zones, **45 coupled interface pairs**
  (2 cheek/pad, 2 pad/backing, 40 cheek/vane, 1 hat/cheek_in). Max **surface**
  skewness <= 0.90 (volumetric skewness is not reported by Fluent 2026 R1: record
  it as null with that reason; it does not block), min orthogonal quality >= 0.10,
  no negative volumes. `wall-vent` meshed area within 2 % of 142 865.51 mm^2. Per-body volume
  within 2 % of section 4. **Cells + nodes < 512 000** if running Ansys Student.
- **Solve.** dt = 0.01 s through the **full** ts including the final 0.000681 s
  step. No more than 10 steps between load/speed updates and no more than 25
  between h updates; use the exact interval-average of each ramp. Start with 5
  iterations per step; the energy residual must reach 1e-8 each step.
- **Energy audit.** (stored + convected) / applied must fall in **90 to 110 %**.
  Report the residual. Applied / vehicle energy must be within +/-2 %.

---

## 6A. Fast run profile (default for a run, amended 2026-11-02)

The user's run is a pipeline demonstration: build and assemble once in
SolidWorks, prepare in SpaceClaim, mesh and solve a short transient in Fluent,
and see the model heat up. Section 6 stays the full analysis definition; this
profile overrides only the rows below. Everything else (materials, loads,
rotation, convection, the one-sided grey-iron wall layer, the mesh topology
gates) is unchanged.

| Item | Fast profile | Section 6 full value |
|---|---|---|
| Mesh sizes | global 4 to 20 mm, growth 1.2, curvature 18 deg; local cheeks 8, vanes 8, hat 12 mm | 2.2 to 20 mm; 4 / 5 / 8 mm |
| Simulated time | 0 to 3.540681 s, the full stop (70 steps of 0.05 s plus one short final step) | 0 to 3.540681 s |
| Time step / iterations | 0.05 s, 3 iterations per step | 0.01 s, 5 iterations per step |
| Load updates | q''' and omega every 4 steps (interval average); h every 24 steps | every 10 / 25 steps |
| Energy gate | applied within 2 % of the closed-form integral and of E; stored / applied 90 to 110 %; the full ts covered | applied within 2 % of E; ratio 90 to 110 % |
| Heating gate | stored energy rises in every window; friction faces above 300 K and below 1500 K | - |
| Outputs | `results.json`, mesh, case and data; Fluent left open with a temperature contour | plus histories, images, report |

**What the fast profile does not do.** It does not adjudicate THM-01 to THM-04:
the mesh and the 0.05 s step are too coarse at the friction faces to resolve
the surface peak, so the temperatures are observations, not a verdict. In the fast profile those rows are `NOT RUN (fast profile)`.
Images, the 2D drawing and the PDF report are descoped.

The vetted stage scripts `scripts/stages/spaceclaim_prep.py` and
`scripts/stages/fluent_fast.py` implement Gates 2 and 3 of this profile.

---

## 7. Requirements (every one gets a disposition in the lead's gate summary)

M = mandatory, S = should, C = could.

| ID | Requirement | Target | Class | Evidence expected | Prediction from section 4/5 |
|---|---|---|---|---|---|
| PKG-01 | rotor outer diameter | <= 330 mm | M | CAD measure | 330.0 |
| PKG-02 | friction ring thickness | 32 mm nominal | M | CAD measure | 32.0 |
| PKG-03 | bolt pattern | 5 x Ø14 on Ø115 PCD | M | CAD measure | as built |
| PKG-04 | centre bore | Ø70 | M | CAD measure | 70.0 |
| PKG-05 | mounting face offset | z = +43 | M | CAD measure | 43.0 |
| PKG-06 | wheel rim clearance | >= 6 mm radial | S | package check | **OPEN** - no wheel geometry |
| MAS-01 | rotor mass | <= 13.5 kg | M | volume x 7200 | 12.973 kg |
| GEO-01 | two cheeks + vanes | present | M | CAD | yes |
| GEO-02 | cheek thickness | 10 mm each | S | CAD | 10.0 |
| GEO-03 | vent gap | 12 mm | S | CAD | 12.0 |
| GEO-04 | curved vanes | >= 18 | S | CAD | 20 |
| GEO-05 | cross-drilled holes | >= 30 | C | - | **DEFERRED** to Phase 3: holes break the axisymmetry the solid-motion model needs. Do **not** build them, not even as a display model |
| GEO-06 | hat on inboard cheek, vent inlet open | yes | M | CAD section | yes, 7 mm inlet gap |
| PAD-01 | pad sector angle | 60 deg | M | CAD | 60 |
| PAD-02 | pad radii | 120 to 160 mm | M | CAD | yes |
| PAD-03 | pad thickness | 12 mm | S | CAD | 12 |
| PAD-04 | backing plate | 6 mm steel, r 115 to 165 | S | CAD | yes |
| PAD-05 | calliper clears pad stack | slot >= stack + 4 mm, 0 interference | M | CAD interference | +9.6 mm, 0 |
| MAT-01 | rotor grey iron | rho 7200, cp 447, k 52 | declared | solver readback | |
| MAT-02 | pad compound | rho 2500, cp 900, k 1.2 | declared | solver readback | |
| MAT-03 | backing steel | rho 8030, cp 502, k 16.3 | declared | solver readback | |
| THM-01 | rotor friction-surface peak | <= 923 K | M | Fluent | solve |
| THM-02 | pad friction-surface peak | <= 623 K | M | Fluent | solve; **expected to govern** |
| THM-03 | rotor bulk temperature rise | <= 60 K | S | Fluent | about 42 K upper estimate |
| THM-04 | no rotor surface above | 1143 K | M | Fluent | solve |
| THM-05 | vent cooling modelled explicitly | distinct vent h | M | Fluent setup readback | yes |
| THM-06 | calliper / brake fluid temperature | <= 428 K | M | - | **DEFERRED**: calliper not in thermal model (DV-09) |

Design-verification items: DV-01 package, DV-02 mass, DV-03 inlet open, DV-04
thermal, DV-05 energy within +/-2 %, DV-06 interference - all **in scope**.
DV-07 fade/dyno, DV-08 cracking, DV-09 calliper/fluid, DV-10 repeated stops - all
**deferred**, with the owner Chassis / Foundation Brake and the target phase
Phase 3.

**Temperature honesty.** Report cell-maximum and wall-layer-maximum temperatures
as a range (for THM-04, cell max and wall-facet max over all rotor walls; the
layer exists only at the friction faces). If that range straddles a limit, or the
wall-normal cell size at the friction face is coarser than the thermal
penetration depth sqrt(alpha x t) at the time of the peak, the disposition is
**NOT ADJUDICABLE**, not PASS. If the cell maximum alone exceeds the limit, it is
**FAIL**. Always record the number of cells across the penetration depth; fewer
than 5 is a finding. Lack of a mesh-sensitivity study alone is a finding, not a
reason for NOT ADJUDICABLE.

---

## 8. Deliverables (fast run profile)

1. `case.json`: the section 5 derivation with every value and unit.
2. SolidWorks: 9 `.SLDPRT`, `brake.SLDASM`, `brake.step`, and `cad_report.json`
   (each body's measured volume, centroid, bbox and checksum comparison).
3. SpaceClaim: `brake.pmdb` and `tag_report.json` (27 bodies, named selections,
   areas).
4. Fluent: mesh, case and data, and `results.json` (mesh gate, setup readback,
   heating history, energy balance). Fluent is left open with a temperature
   contour so the heating can be seen.
5. The lead's gate summary in `BUILD_STATE.json` and in chat.

**Descoped in H1.2:** 2D drawings, every image file (CAD views, mesh pictures,
contour PNGs) and the PDF report.

All run artifacts go in a fresh folder `C:\brake-runs\<run-id>\` (never inside
OneDrive).

---

## 9. Acceptance of the workflow itself

A run is **complete** only if all 28 bodies passed section 4, the 45 interfaces
exist, and the energy balance and heating gates of the active profile closed
(section 6 for a full run, section 6A for a fast run). The
engineering verdict (how many requirements PASS) is reported separately from
workflow completion. Otherwise
it is **complete_with_findings** or **halted**, and the report says exactly which
gate stopped it and with what two numbers (expected vs measured).

---

## 10. Differences from CTS-BRK-0117 rev C

| CTS says | This PRD says | Why |
|---|---|---|
| GEO-05 >= 30 cross-drilled holes (C) | Deferred, not built | Holes break the axisymmetric solid-motion model. One geometry is built and solved. |
| hat bore radius 97 mm, 1 mm calliper clearance (older text) | Hat reaches r = 95 at the cheek bore only; hat-to-calliper clearance 11.8 mm | Retired geometry |
| calliper windows z band not matched to slot | Windows use exactly the slot band z = -39 to +38.6 | Removes the sliver faces a mismatched band creates |
| g = 9.81 in places | g = 9.80665 everywhere | One convention |
| 354 steps x 0.01 s | full ts = 3.54068 s including a final short step | Covers the whole stop |
| vane intent "pumps under +theta" | vanes as built pump under -theta (clockwise from +Z), omega0 = -84.175 | The geometry governs; the intent is reported as unmet |
