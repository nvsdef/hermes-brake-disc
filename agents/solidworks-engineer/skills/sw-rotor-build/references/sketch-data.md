# Rotor sketch data cards (PRD H1.2)

These are **data, not scripts**. Each card is the exact text of the `segments`
argument of `add_sketch_entities`, in metres, 9 decimals. Pass the card text as
a **JSON string** value: `{"segments": "<card text>"}`. Do not re-type, round,
rotate or re-order the numbers. Do not compute them again. They were generated
once from PRD 3.1 to 3.3 and checked (see "How the cards were checked" at the
end).

`add_sketch_entities` answers with `result_geometry {segment_count, counts per
entity_type}`. The expected counts are given under each card. A different count
means a record failed: the call is not transactional, so read the sketch back
with `analyze_model('sketch', name=...)` before adding anything.

Every extrude and cut answers with `result_geometry {volume, faces, edges}`.
The expected volume after each feature is in the checksum table of each part.
Tolerance on every volume: 1 %.

---

## Card R1 - cheek annulus (use for `cheek_out` and `cheek_in`)

Sketch plane: `Plane1` at offset +0.011 (`cheek_out`) or -0.011 (`cheek_in`).
Expected: segment_count 2, circle 2.

```json
[{"entity_type":"circle","cx":0,"cy":0,"radius":0.165000000},{"entity_type":"circle","cx":0,"cy":0,"radius":0.095000000}]
```

| Feature | Call | Expected `result_geometry.volume` m^3 |
|---|---|---|
| boss, `depth=0.010`, `mid_plane=true` | `extrude_feature` | 5.717699e-4 (faces 4) |

Final checksum, either cheek: volume 5.717699e-4 m^3; centroid (0, 0, +0.011) m
for `cheek_out`, (0, 0, -0.011) m for `cheek_in`.

---

## Cards R2 to R5 - the 20 vanes, extended strips (one sketch, four calls)

Sketch plane: `Front Plane` (frame origin [0, 0, 0], xdir +X, ydir +Y). All
four cards go into the **same** sketch, in order R2, R3, R4, R5. Each line of a
card is one vane: arc about C_k on the R123 flank from r = 80 to r = 172, line
across the r = 172 end, arc about C_k on the R117 flank back to r = 80, line
across the r = 80 end. The flanks run past the trim radii on purpose; the ends
are cut at exactly r = 95 and r = 165 by cards R6a and R6b. No record has a `direction`
key, so every arc is the minor arc (61.97 deg and 64.27 deg about C_k).

Expected for **each** of the four calls: segment_count 20, arc_center 10,
line 10.

### Card R2 - vanes 01 to 05
```json
[
{"entity_type":"arc_center","cx":0.020722000,"cy":0.094249000,"x1":0.078726970,"y1":-0.014214927,"x2":0.143721767,"y2":0.094488379},{"entity_type":"line","x1":0.143721767,"y1":0.094488379,"x2":0.137353481,"y2":0.103527876},{"entity_type":"arc_center","cx":0.020722000,"cy":0.094249000,"x1":0.137353481,"y1":0.103527876,"x2":0.079711160,"y2":-0.006791977},{"entity_type":"line","x1":0.079711160,"y1":-0.006791977,"x2":0.078726970,"y2":-0.014214927},
{"entity_type":"arc_center","cx":-0.009416750,"cy":0.096039576,"x1":0.079266452,"y1":0.010808773,"x2":0.107489008,"y2":0.134276257},{"entity_type":"line","x1":0.107489008,"y1":0.134276257,"x2":0.098639050,"y2":0.140905421},{"entity_type":"arc_center","cx":-0.009416750,"cy":0.096039576,"x1":0.098639050,"y1":0.140905421,"x2":0.077908655,"y2":0.018172549},{"entity_type":"line","x1":0.077908655,"y1":0.018172549,"x2":0.079266452,"y2":0.010808773},
{"entity_type":"arc_center","cx":-0.038633722,"cy":0.088429129,"x1":0.072046781,"y1":0.034774435,"x2":0.060734477,"y2":0.160920239},{"entity_type":"line","x1":0.060734477,"y1":0.160920239,"x2":0.050269142,"y2":0.164490162},{"entity_type":"arc_center","cx":-0.038633722,"cy":0.088429129,"x1":0.050269142,"y1":0.164490162,"x2":0.068479907,"y2":0.041358220},{"entity_type":"line","x1":0.068479907,"y1":0.041358220,"x2":0.072046781,"y2":0.034774435},
{"entity_type":"arc_center","cx":-0.064068957,"cy":0.072162622,"x1":0.057774669,"y1":0.055336133,"x2":0.008034831,"y2":0.171812227},{"entity_type":"line","x1":0.008034831,"y1":0.171812227,"x2":-0.003021460,"y2":0.171973460},{"entity_type":"arc_center","cx":-0.064068957,"cy":0.072162622,"x1":-0.003021460,"y1":0.171973460,"x2":0.052347869,"y2":0.060495459},{"entity_type":"line","x1":0.052347869,"y1":0.060495459,"x2":0.057774669,"y2":0.055336133},
{"entity_type":"arc_center","cx":-0.083232675,"cy":0.048832336,"x1":0.037847171,"y1":0.070481144,"x2":-0.045451320,"y2":0.165886038},{"entity_type":"line","x1":-0.045451320,"y1":0.165886038,"x2":-0.056016301,"y2":0.162622797},{"entity_type":"arc_center","cx":-0.083232675,"cy":0.048832336,"x1":-0.056016301,"y1":0.162622797,"x2":0.031091657,"y2":0.073710982},{"entity_type":"line","x1":0.031091657,"y1":0.073710982,"x2":0.037847171,"y2":0.070481144}
]
```

### Card R3 - vanes 06 to 10
```json
[
{"entity_type":"arc_center","cx":-0.094249000,"cy":0.020722000,"x1":0.014214927,"y1":0.078726970,"x2":-0.094488379,"y2":0.143721767},{"entity_type":"line","x1":-0.094488379,"y1":0.143721767,"x2":-0.103527876,"y2":0.137353481},{"entity_type":"arc_center","cx":-0.094249000,"cy":0.020722000,"x1":-0.103527876,"y1":0.137353481,"x2":0.006791977,"y2":0.079711160},{"entity_type":"line","x1":0.006791977,"y1":0.079711160,"x2":0.014214927,"y2":0.078726970},
{"entity_type":"arc_center","cx":-0.096039576,"cy":-0.009416750,"x1":-0.010808773,"y1":0.079266452,"x2":-0.134276257,"y2":0.107489008},{"entity_type":"line","x1":-0.134276257,"y1":0.107489008,"x2":-0.140905421,"y2":0.098639050},{"entity_type":"arc_center","cx":-0.096039576,"cy":-0.009416750,"x1":-0.140905421,"y1":0.098639050,"x2":-0.018172549,"y2":0.077908655},{"entity_type":"line","x1":-0.018172549,"y1":0.077908655,"x2":-0.010808773,"y2":0.079266452},
{"entity_type":"arc_center","cx":-0.088429129,"cy":-0.038633722,"x1":-0.034774435,"y1":0.072046781,"x2":-0.160920239,"y2":0.060734477},{"entity_type":"line","x1":-0.160920239,"y1":0.060734477,"x2":-0.164490162,"y2":0.050269142},{"entity_type":"arc_center","cx":-0.088429129,"cy":-0.038633722,"x1":-0.164490162,"y1":0.050269142,"x2":-0.041358220,"y2":0.068479907},{"entity_type":"line","x1":-0.041358220,"y1":0.068479907,"x2":-0.034774435,"y2":0.072046781},
{"entity_type":"arc_center","cx":-0.072162622,"cy":-0.064068957,"x1":-0.055336133,"y1":0.057774669,"x2":-0.171812227,"y2":0.008034831},{"entity_type":"line","x1":-0.171812227,"y1":0.008034831,"x2":-0.171973460,"y2":-0.003021460},{"entity_type":"arc_center","cx":-0.072162622,"cy":-0.064068957,"x1":-0.171973460,"y1":-0.003021460,"x2":-0.060495459,"y2":0.052347869},{"entity_type":"line","x1":-0.060495459,"y1":0.052347869,"x2":-0.055336133,"y2":0.057774669},
{"entity_type":"arc_center","cx":-0.048832336,"cy":-0.083232675,"x1":-0.070481144,"y1":0.037847171,"x2":-0.165886038,"y2":-0.045451320},{"entity_type":"line","x1":-0.165886038,"y1":-0.045451320,"x2":-0.162622797,"y2":-0.056016301},{"entity_type":"arc_center","cx":-0.048832336,"cy":-0.083232675,"x1":-0.162622797,"y1":-0.056016301,"x2":-0.073710982,"y2":0.031091657},{"entity_type":"line","x1":-0.073710982,"y1":0.031091657,"x2":-0.070481144,"y2":0.037847171}
]
```

### Card R4 - vanes 11 to 15
```json
[
{"entity_type":"arc_center","cx":-0.020722000,"cy":-0.094249000,"x1":-0.078726970,"y1":0.014214927,"x2":-0.143721767,"y2":-0.094488379},{"entity_type":"line","x1":-0.143721767,"y1":-0.094488379,"x2":-0.137353481,"y2":-0.103527876},{"entity_type":"arc_center","cx":-0.020722000,"cy":-0.094249000,"x1":-0.137353481,"y1":-0.103527876,"x2":-0.079711160,"y2":0.006791977},{"entity_type":"line","x1":-0.079711160,"y1":0.006791977,"x2":-0.078726970,"y2":0.014214927},
{"entity_type":"arc_center","cx":0.009416750,"cy":-0.096039576,"x1":-0.079266452,"y1":-0.010808773,"x2":-0.107489008,"y2":-0.134276257},{"entity_type":"line","x1":-0.107489008,"y1":-0.134276257,"x2":-0.098639050,"y2":-0.140905421},{"entity_type":"arc_center","cx":0.009416750,"cy":-0.096039576,"x1":-0.098639050,"y1":-0.140905421,"x2":-0.077908655,"y2":-0.018172549},{"entity_type":"line","x1":-0.077908655,"y1":-0.018172549,"x2":-0.079266452,"y2":-0.010808773},
{"entity_type":"arc_center","cx":0.038633722,"cy":-0.088429129,"x1":-0.072046781,"y1":-0.034774435,"x2":-0.060734477,"y2":-0.160920239},{"entity_type":"line","x1":-0.060734477,"y1":-0.160920239,"x2":-0.050269142,"y2":-0.164490162},{"entity_type":"arc_center","cx":0.038633722,"cy":-0.088429129,"x1":-0.050269142,"y1":-0.164490162,"x2":-0.068479907,"y2":-0.041358220},{"entity_type":"line","x1":-0.068479907,"y1":-0.041358220,"x2":-0.072046781,"y2":-0.034774435},
{"entity_type":"arc_center","cx":0.064068957,"cy":-0.072162622,"x1":-0.057774669,"y1":-0.055336133,"x2":-0.008034831,"y2":-0.171812227},{"entity_type":"line","x1":-0.008034831,"y1":-0.171812227,"x2":0.003021460,"y2":-0.171973460},{"entity_type":"arc_center","cx":0.064068957,"cy":-0.072162622,"x1":0.003021460,"y1":-0.171973460,"x2":-0.052347869,"y2":-0.060495459},{"entity_type":"line","x1":-0.052347869,"y1":-0.060495459,"x2":-0.057774669,"y2":-0.055336133},
{"entity_type":"arc_center","cx":0.083232675,"cy":-0.048832336,"x1":-0.037847171,"y1":-0.070481144,"x2":0.045451320,"y2":-0.165886038},{"entity_type":"line","x1":0.045451320,"y1":-0.165886038,"x2":0.056016301,"y2":-0.162622797},{"entity_type":"arc_center","cx":0.083232675,"cy":-0.048832336,"x1":0.056016301,"y1":-0.162622797,"x2":-0.031091657,"y2":-0.073710982},{"entity_type":"line","x1":-0.031091657,"y1":-0.073710982,"x2":-0.037847171,"y2":-0.070481144}
]
```

### Card R5 - vanes 16 to 20
```json
[
{"entity_type":"arc_center","cx":0.094249000,"cy":-0.020722000,"x1":-0.014214927,"y1":-0.078726970,"x2":0.094488379,"y2":-0.143721767},{"entity_type":"line","x1":0.094488379,"y1":-0.143721767,"x2":0.103527876,"y2":-0.137353481},{"entity_type":"arc_center","cx":0.094249000,"cy":-0.020722000,"x1":0.103527876,"y1":-0.137353481,"x2":-0.006791977,"y2":-0.079711160},{"entity_type":"line","x1":-0.006791977,"y1":-0.079711160,"x2":-0.014214927,"y2":-0.078726970},
{"entity_type":"arc_center","cx":0.096039576,"cy":0.009416750,"x1":0.010808773,"y1":-0.079266452,"x2":0.134276257,"y2":-0.107489008},{"entity_type":"line","x1":0.134276257,"y1":-0.107489008,"x2":0.140905421,"y2":-0.098639050},{"entity_type":"arc_center","cx":0.096039576,"cy":0.009416750,"x1":0.140905421,"y1":-0.098639050,"x2":0.018172549,"y2":-0.077908655},{"entity_type":"line","x1":0.018172549,"y1":-0.077908655,"x2":0.010808773,"y2":-0.079266452},
{"entity_type":"arc_center","cx":0.088429129,"cy":0.038633722,"x1":0.034774435,"y1":-0.072046781,"x2":0.160920239,"y2":-0.060734477},{"entity_type":"line","x1":0.160920239,"y1":-0.060734477,"x2":0.164490162,"y2":-0.050269142},{"entity_type":"arc_center","cx":0.088429129,"cy":0.038633722,"x1":0.164490162,"y1":-0.050269142,"x2":0.041358220,"y2":-0.068479907},{"entity_type":"line","x1":0.041358220,"y1":-0.068479907,"x2":0.034774435,"y2":-0.072046781},
{"entity_type":"arc_center","cx":0.072162622,"cy":0.064068957,"x1":0.055336133,"y1":-0.057774669,"x2":0.171812227,"y2":-0.008034831},{"entity_type":"line","x1":0.171812227,"y1":-0.008034831,"x2":0.171973460,"y2":0.003021460},{"entity_type":"arc_center","cx":0.072162622,"cy":0.064068957,"x1":0.171973460,"y1":0.003021460,"x2":0.060495459,"y2":-0.052347869},{"entity_type":"line","x1":0.060495459,"y1":-0.052347869,"x2":0.055336133,"y2":-0.057774669},
{"entity_type":"arc_center","cx":0.048832336,"cy":0.083232675,"x1":0.070481144,"y1":-0.037847171,"x2":0.165886038,"y2":0.045451320},{"entity_type":"line","x1":0.165886038,"y1":0.045451320,"x2":0.162622797,"y2":0.056016301},{"entity_type":"arc_center","cx":0.048832336,"cy":0.083232675,"x1":0.162622797,"y1":0.056016301,"x2":0.073710982,"y2":-0.031091657},{"entity_type":"line","x1":0.073710982,"y1":-0.031091657,"x2":0.070481144,"y2":-0.037847171}
]
```

## Cards R6a and R6b - vane trim (two cuts)

The single three-circle cut (the old card R6, relying on nested-loop parity)
returned `EXTRUSION_FAILED` through SolidPilot on 2026-11-02. Two annular cuts
are the method. Each is a new sketch on `Front Plane` with two concentric
circles (expected: segment_count 2, circle 2), cut with `depth=0.020`,
`mid_plane=true`.

Card R6a, outer ring r = 165 to 260:
```json
[{"entity_type":"circle","cx":0,"cy":0,"radius":0.260000000},{"entity_type":"circle","cx":0,"cy":0,"radius":0.165000000}]
```

Card R6b, inner disc r = 10 to 95 (the 10 mm hole only keeps the profile an annulus):
```json
[{"entity_type":"circle","cx":0,"cy":0,"radius":0.095000000},{"entity_type":"circle","cx":0,"cy":0,"radius":0.010000000}]
```

### Vanes checksum table

| After | Call | Expected total volume m^3 | Bodies |
|---|---|---|---|
| boss of cards R2 to R5, `depth=0.012`, `mid_plane=true` | `extrude_feature` | 1.901692e-4 (792.372 mm^2 x 12 mm x 20) | 20 |
| cut of card R6a | `extrude_feature(feature_type='cut')` | 1.723384e-4 | 20 |
| cut of card R6b | `extrude_feature(feature_type='cut')` | **1.450325e-4** (604.302 mm^2 x 12 mm x 20) | 20 |

`extrude_feature` returns `result_geometry.volume` to only 2 to 3 significant
figures: treat it as a sanity check. The binding check is
`analyze_model('bodies')` after the last cut.

Per vane: 7.251627e-6 m^3; centroid r = 130.154 mm at 17.917 + (k - 1) x 18 deg,
z = 0. The full naming table is in `references/vane-geometry.md` section 6.

---

## Card R7 - hat (z, r) polygon on `Right Plane`

PRD 3.3 polygon `(43, 35) -> (43, 86) -> (-6, 88) -> (-6, 95) -> (-16, 95) ->
(-16, 78) -> (33, 74) -> (33, 35) -> close`, mapped with the measured Right
Plane frame `xdir = [0, 0, -1]`, `ydir = [0, 1, 0]`: sketch x = -z / 1000,
sketch y = r / 1000. The last record is the construction line on the axis
(sketch y = 0). Expected: segment_count 9, line 9.

**Use this card only if `create_sketch` returned `xdir = [0, 0, -1]`.** If it
returned `xdir = [0, 0, 1]`, use card R7-alt.

```json
[
{"entity_type":"line","x1":-0.043000000,"y1":0.035000000,"x2":-0.043000000,"y2":0.086000000},
{"entity_type":"line","x1":-0.043000000,"y1":0.086000000,"x2":0.006000000,"y2":0.088000000},
{"entity_type":"line","x1":0.006000000,"y1":0.088000000,"x2":0.006000000,"y2":0.095000000},
{"entity_type":"line","x1":0.006000000,"y1":0.095000000,"x2":0.016000000,"y2":0.095000000},
{"entity_type":"line","x1":0.016000000,"y1":0.095000000,"x2":0.016000000,"y2":0.078000000},
{"entity_type":"line","x1":0.016000000,"y1":0.078000000,"x2":-0.033000000,"y2":0.074000000},
{"entity_type":"line","x1":-0.033000000,"y1":0.074000000,"x2":-0.033000000,"y2":0.035000000},
{"entity_type":"line","x1":-0.033000000,"y1":0.035000000,"x2":-0.043000000,"y2":0.035000000},
{"entity_type":"line","x1":-0.060000000,"y1":0,"x2":0.030000000,"y2":0,"construction":true}
]
```

Revolve: `extrude_feature(feature_type='revolve', angle=360, axis_x1=-0.060,
axis_y1=0, axis_x2=0.030, axis_y2=0)`.

### Card R7-alt - same polygon for `xdir = [0, 0, 1]` (sketch x = +z / 1000)

Revolve axis for this card: `axis_x1=0.060, axis_y1=0, axis_x2=-0.030,
axis_y2=0`.

```json
[
{"entity_type":"line","x1":0.043000000,"y1":0.035000000,"x2":0.043000000,"y2":0.086000000},
{"entity_type":"line","x1":0.043000000,"y1":0.086000000,"x2":-0.006000000,"y2":0.088000000},
{"entity_type":"line","x1":-0.006000000,"y1":0.088000000,"x2":-0.006000000,"y2":0.095000000},
{"entity_type":"line","x1":-0.006000000,"y1":0.095000000,"x2":-0.016000000,"y2":0.095000000},
{"entity_type":"line","x1":-0.016000000,"y1":0.095000000,"x2":-0.016000000,"y2":0.078000000},
{"entity_type":"line","x1":-0.016000000,"y1":0.078000000,"x2":0.033000000,"y2":0.074000000},
{"entity_type":"line","x1":0.033000000,"y1":0.074000000,"x2":0.033000000,"y2":0.035000000},
{"entity_type":"line","x1":0.033000000,"y1":0.035000000,"x2":0.043000000,"y2":0.035000000},
{"entity_type":"line","x1":0.060000000,"y1":0,"x2":-0.030000000,"y2":0,"construction":true}
]
```

## Card R8 - five bolt holes (Ø14 on Ø115 PCD)

New sketch on `Front Plane` (no offset plane needed). Cut `depth=0.100`,
`mid_plane=true` (z = -50 to +50 mm). This is exact because the only hat
material at r = 50.5 to 64.5 mm is the flange z = +33 to +43; the hat wall
below the flange is at r >= 74. Expected: segment_count 5, circle 5.

```json
[
{"entity_type":"circle","cx":0.057500000,"cy":0,"radius":0.007000000},
{"entity_type":"circle","cx":0.017768477,"cy":0.054685750,"radius":0.007000000},
{"entity_type":"circle","cx":-0.046518477,"cy":0.033797652,"radius":0.007000000},
{"entity_type":"circle","cx":-0.046518477,"cy":-0.033797652,"radius":0.007000000},
{"entity_type":"circle","cx":0.017768477,"cy":-0.054685750,"radius":0.007000000}
]
```

### Hat checksum table

| After | Expected volume m^3 | Expected centroid z |
|---|---|---|
| revolve of card R7 | 5.209012e-4 (polygon area 1 139.0 mm^2, r_bar 72.787 mm) | +18.389 mm |
| cut of card R8 | **5.132043e-4** (delta -7.6969e-6) | **+18.095 mm** |

A revolve centroid at z = -18.389 mm means the mapping was inverted: delete
the revolve and the sketch, and redo with the other card.

---

## How the cards were checked

The cards were generated in the sandbox from the PRD numbers only. Checks run
on the rounded (9-decimal) values:

- Every shared endpoint is identical text in both records, so each contour
  closes exactly.
- Every vane arc endpoint lies on its circle (R = 0.123 or 0.117 about C_k)
  and on its radius (r = 0.080 or 0.172) within 1.2e-9 m.
- Arc sweeps about C_k are 61.97 deg and 64.27 deg: minor arcs, so no
  `direction` key is needed.
- No two extended vane profiles intersect: the smallest gap between
  neighbours is 15.07 mm, and no vertex of any vane lies inside another.
- The extended profile area is 792.372 mm^2. Integrating the trimmed vane in
  polar form from r = 95 to 165 gives **604.302 mm^2**, centroid
  (123.842, 40.040) mm, r = 130.154 mm at 17.917 deg: PRD section 4 exactly.
- Hat: shoelace area 1 139.0 mm^2, Pappus volume 520 901.19 mm^3, centroid
  z = +18.389 mm; after holes 513 204.29 mm^3 at z = +18.095 mm.
