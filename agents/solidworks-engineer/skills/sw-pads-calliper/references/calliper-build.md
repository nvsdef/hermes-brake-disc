# Calliper build detail (PRD H1.2)

PRD 3.4 is the authority. The paste-ready cards (C1 to C4) are in
`sketch-data.md`; use them. This sheet gives the corner coordinates behind the
cards, the fallback base method, the band structure, how to localise a volume
miss, and the predecessor's calliper lessons.

## 0. Fallback base method (only if card C1 fails)

Card C1 draws the union of the sector and the three lobes as one contour, so
the base is one sketch and one boss. If that boss returns `EXTRUSION_FAILED`
or more than 1 body, delete it and build the base the older way, one feature per
overlapping region, each a boss with `depth=0.114`, `mid_plane=true` on
`Front Plane`:

| Row | Sketch | Total volume after (m^3) |
|---|---|---|
| 1 | sector r 98 to 176, -34 to +34 deg (corners below) | 1.445794e-3 |
| 2 | circle R 0.040 at (0.160000000, 0) | 1.601814e-3 |
| 3 | circle R 0.040 at (0.150350819, -0.054723223) | 1.749591e-3 |
| 4 | circle R 0.040 at (0.150350819, 0.054723223) | 1.897369e-3, 1 body |

Overlapping loops must never share a sketch: three overlapping R40 circles in
one sketch returned `EXTRUSION_FAILED` for the predecessor. After row 4, carry
on with card C2. The fallback costs 9 extra calls.

The slot and windows can likewise fall back to two cuts on the -0.0002 plane:
slot sector first (expect 8.794881e-4), then the three window sectors in one
sketch (expect 7.851263e-4).

## 1. Sketch coordinates (metres, 9 decimals)

A point at radius r (mm) and angle theta (deg) is
(r cos theta / 1000, r sin theta / 1000). All sketches are on `Front Plane` or
an offset of it, so sketch x = model X and sketch y = model Y. Confirm from the
returned frame.

### Base sector: r = 98 to 176, -34 to +34 deg (fallback row 1; corners of card C1)

| Corner | x | y |
|---|---|---|
| r 176, +34 deg | 0.145910613 | 0.098417951 |
| r 176, -34 deg | 0.145910613 | -0.098417951 |
| r 98, +34 deg | 0.081245682 | 0.054800905 |
| r 98, -34 deg | 0.081245682 | -0.054800905 |

Contour: arc about (0, 0) from (r 176, -34) to (r 176, +34); line to
(r 98, +34); arc about (0, 0) to (r 98, -34); line back. Both arcs are 68 deg,
so omit `direction`.

The corner (0.081245682, 0.054800905) is the calliper's x min (81.245 mm). The
corner (0.145910613, 0.098417951) is its y max (98.418 mm).

### Lobes: R 40 mm at r = 160 mm (fallback rows 2 to 4)

| Lobe | cx | cy |
|---|---|---|
| 0 deg | 0.160000000 | 0.000000000 |
| -20 deg | 0.150350819 | -0.054723223 |
| +20 deg | 0.150350819 | 0.054723223 |

One circle per sketch (they overlap each other and the sector). The 0 deg lobe
reaches x = 200.000 mm: the calliper's x max, mid-arc, not a vertex.

### Pad slot: r = 90 to 178, -42 to +42 deg (part of card C2)

| Corner | x | y |
|---|---|---|
| r 178, +/-42 deg | 0.132279779 | +/-0.119105248 |
| r 90, +/-42 deg | 0.066883034 | +/-0.060221755 |

### Windows: r = 90 to 215 (part of card C2), three disjoint sectors in one sketch

| Window | Corners at r 90 | Corners at r 215 |
|---|---|---|
| -42 to -27 deg | (0.066883034, -0.060221755), (0.080190587, -0.040859145) | (0.159776137, -0.143863080), (0.191566403, -0.097607957) |
| -7 to +7 deg | (0.089329154, -0.010968241), (0.089329154, 0.010968241) | (0.213397423, -0.026201909), (0.213397423, 0.026201909) |
| +27 to +42 deg | (0.080190587, 0.040859145), (0.066883034, 0.060221755) | (0.191566403, 0.097607957), (0.159776137, 0.143863080) |

Each window: two arcs about the origin (r 90 and r 215) and two radial lines.
12 records in one `add_sketch_entities` call.

### Outer-bridge step: annulus r = 172 to 215 (card C3, SKILL steps 4 and 5)

Two circles about the origin, radius 0.172 and 0.215, on the plane at +0.0495
(step 4) and on a separate plane at -0.0495 (step 5).

### Piston bores: R 13 mm at r = 140 mm (card C4, SKILL steps 6 and 7)

| Bore | cx | cy |
|---|---|---|
| -20 deg | 0.131556967 | -0.047882820 |
| 0 deg | 0.140000000 | 0.000000000 |
| +20 deg | 0.131556967 | 0.047882820 |

Three disjoint circles in one sketch, on the plane at +0.0426 (outboard, z =
+38.6 to +46.6) and again on the plane at -0.043 (inboard, z = -47 to -39).

## 2. The band structure (PRD section 4 section areas)

| z band (mm) | Width (mm) | What is left | Section area mm^2 |
|---|---|---|---|
| -57 to -47 and +46.6 to +57 | 10 + 10.4 | base with r > 172 removed, no bores | 11 891.10 |
| -47 to -42 and +42 to +46.6 | 5 + 4.6 | stepped base minus 3 bores | 10 298.32 |
| -42 to -39 and +38.6 to +42 | 3 + 3.4 | full base minus 3 bores | 15 050.62 |
| -39 to +38.6 | 77.6 | two bridges at r > 178, between the windows | 2 310.76 |

Derived from these: the full base section is 15 050.62 + 3 x pi x 13^2 =
16 643.41 mm^2; the three bores are 1 592.79 mm^2 together (530.93 mm^2 each).

Volume check: 20.4 x 11 891.10 + 9.6 x 10 298.32 + 6.4 x 15 050.62 + 77.6 x
2 310.76 = 617 081 mm^3. PRD section 4: 617 081.48 mm^3.

## 3. Localising a miss with planar face areas

`analyze_model('faces', axis='[0,0,1]')` lists planar faces normal to Z with
their area and a point (so their z). Sum the areas at each z level and compare:

| Face z (mm) | What it is | Expected total area mm^2 |
|---|---|---|
| +57.0 | outboard outer face (stepped section) | 11 891.10 |
| -57.0 | inboard outer face | 11 891.10 |
| +46.6 | 3 outboard bore bottoms | 1 592.79 (530.93 each) |
| -47.0 | 3 inboard bore bottoms | 1 592.79 |
| +42.0 | outboard step shoulder (base at r > 172) | 4 752.31 |
| -42.0 | inboard step shoulder | 4 752.31 |
| +38.6 | outboard slot end wall (bores band less bridges) | 12 739.86 |
| -39.0 | inboard slot end wall | 12 739.86 |

How to read a miss:

| Symptom | Feature to repair |
|---|---|
| no faces at +38.6 or -39, volume about 1.897e-3 | slot cut did nothing |
| end walls at +/-38.8, or slot faces at the wrong z | slot plane or depth wrong (must be -0.0002 and 0.0776) |
| extra planar faces at z = +/-39.0 near the windows, or 0.4 mm steps | windows cut with a different band from the slot (the predecessor defect) |
| face at +42 missing, +57 area 16 643 | outboard step missing |
| a bore cut changes the volume by less than 1.2742e-5 m^3 (3 bores x 8 mm), or leaves no faces at +46.6 / -47 | the bore cut went (partly) into the empty slot instead of outward; plane or depth wrong |
| centroid z near 0.000 | the build was made symmetric; slot face must be +38.6, bores to +46.6 |
| 2 or more bodies | a lobe did not merge, or a cut split the part |

## 4. Why the calliper looks the way it does (predecessor lessons)

1. **The outer bridge is stepped in.** A constant-width outer band across the
   full 114 mm depth renders as a drum, not a calliper. Stepping r > 172 in by
   15 mm per side makes the bridge 84 mm deep and was the single biggest visual
   change. PRD 3.4 item 4 keeps it.
2. **The inner radius is set by the hat, not the pad.** The calliper base starts
   at r = 98. The PRD hat wall at the calliper end-wall height (z = +38.6) is at
   r = 86.18, so the clearance is 11.8 mm (PRD section 4). The predecessor's
   "1.0 mm hat clearance" came from a retired hat at r = 97 and does not apply.
   Measure it against the hat you built; if the hat ever grows, this is the
   clearance that closes first.
3. **Overlapping lobes need one sketch and one extrude each.** Three
   overlapping circles in one sketch returned `EXTRUSION_FAILED`. Separately they
   merged into the scalloped union. Disjoint loops (windows, bores) are fine in
   one sketch.
4. **Draw it; do not import one.** The predecessor measured three real
   callipers. None fitted a 68 mm stack (their slots were 19 mm or less). One
   imported cleanly but, after guessed transforms, landed at r = 123 to 164,
   entirely inside the rotor ring, where it rendered as nothing.
   `transform_json` cannot scale, either. Drawing the parametric calliper took
   fewer calls than three placement attempts.
5. **No fillets in H1.2.** PRD 3.4 item 6. Fillets change the volume and move the
   signature SpaceClaim deletes by. The predecessor once listed R8 and R5
   fillets in its feature table; they were never built, and its own measured
   signature did not include them.

## 5. The predecessor's calliper defects, now closed by the PRD

| Predecessor | PRD H1.2 |
|---|---|
| Windows cut mid-plane 78 mm (z = -39 to +39) while the slot was z = -39 to +38.6. Four 0.400 mm steps at the window edges, shortest chord 0.400 mm against a 3.000 mm gate | Windows use exactly z = -39 to +38.6 |
| Signature literal 6.113384269e-4 m^3; as-built 6.146340e-4 (+0.54 %); older 6.36e-4 +/-5 % | 6.170815e-4 m^3, centroid (146.143, 0, +0.369) mm, bbox as PRD section 4 |
| Name `caliper` | Name `calliper` (PRD section 2); the STEP PRODUCT name must match |

The predecessor also learned that a gate's reference value must come from an
independent derivation checked against a build, never from a build alone. The
PRD signature was computed by two independent methods. If your build disagrees
with it by more than 1 %, the build is wrong until proven otherwise: localise
with section 3, repair, and report.
