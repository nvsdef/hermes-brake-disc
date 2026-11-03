---
name: sw-rotor-build
description: "Build and gate the 23 rotor bodies in SolidWorks."
version: 1.2.0
author: "sdefibaugh"
license: Apache-2.0
platforms: [windows]
metadata:
  hermes:
    tags: [brake, solidworks, rotor]
---

# Building the rotor: two cheeks, twenty vanes, one hat (PRD H1.2)

The rotor is **four part files and 23 bodies**. The geometry authority is PRD
sections 3.1 to 3.3, and the acceptance numbers are in PRD section 4. The tool
mechanics are in `sw-solidpilot`. Every sketch comes from a card in
`references/sketch-data.md`. Copy the card text. Never compute, rotate or
re-type coordinates. In run 1, hand-rotated vane coordinates gave crossed arcs
on vanes 17 to 20 and cost about 15 minutes.

Budget: about **36 tool calls, 5 to 6 minutes** for all four parts.

## When to use

When a commission asks you to build, rebuild or check `cheek_out`, `cheek_in`,
`vanes` or `hat`.

## Rules (reasons are in `references/rotor-lessons.md`)

- One part per file: touching bodies in one part fuse silently.
- Cheeks get one extrude and nothing else. They are the only bodies the
  solver rotates.
- No cross-drilled holes (GEO-05 is DEFERRED), no fillets, and no second rotor
  model.
- `cheek_in` is a flipped instance of `cheek_out` (assembly step A2). Never copy
  the file and edit its offset.
- Vanes come from the extended-strip cards and are trimmed by a cut. Never fit
  a curve to r = 95 or r = 165, and never use `create_pattern`.
- HALT: two repairs per failing check, then stop and return both numbers.

## Part 1: `cheek_out` - 7 calls

1. `open_new_part`.
2. `add_reference_geometry(type='plane', ref_plane_name='Front Plane', offset=0.011)`.
3. `create_sketch(plane=<returned name>)`. Done when the frame origin is
   [0, 0, 0.011].
4. `add_sketch_entities(segments=<card R1>)`. Expect circle 2.
5. `extrude_feature(feature_type='boss', depth=0.010, mid_plane=true)`. Expect a
   volume of 5.717699e-4 m^3 and 4 faces.
6. `analyze_model('mass_properties')`. Expect 5.717699e-4 m^3 and centroid
   (0, 0, +11.000) mm.
7. `save_document(file_path='...\10_cad\cheek_out.SLDPRT')`.

On-miss: right volume with a wrong centroid means a wrong plane. Delete the
plane and the extrude, and rebuild.

## Part 2: `cheek_in` - 0 calls (not built)

`cheek_in` is not a part file. It is a second instance of `cheek_out.SLDPRT`,
inserted in the assembly rotated 180 deg about +X (`sw-pads-calliper` A2). Its
expected centroid (0, 0, -11.000) mm and z band -16 to -6 follow from the
cheek_out measurement and the read-back transform.

## Part 3: `vanes` - 15 calls

1. `open_new_part`.
2. `create_sketch(plane='Front Plane')`. Expect frame origin [0, 0, 0], xdir +X,
   ydir +Y.
3. to 6. Four `add_sketch_entities` calls, all in the **same** sketch, with
   cards R2, R3, R4 and R5 in that order (vanes 01-05, 06-10, 11-15, 16-20).
   Each call must return segment_count 20, arc_center 10 and line 10.
7. `extrude_feature(feature_type='boss', depth=0.012, mid_plane=true)`. Expect
   **1.901692e-4 m^3** in 20 bodies.
8. `create_sketch(plane='Front Plane')`, `add_sketch_entities(segments=<card R6a>)`
   (circle 2), `extrude_feature(feature_type='cut', depth=0.020, mid_plane=true)`.
   Expect about 1.72e-4 m^3 in 20 bodies.
9. `create_sketch(plane='Front Plane')`, `add_sketch_entities(segments=<card R6b>)`
   (circle 2), `extrude_feature(feature_type='cut', depth=0.020, mid_plane=true)`.
   Expect about **1.45e-4 m^3** in 20 bodies (the returned volume is coarse).
10. `analyze_model('bodies')`. This is the binding measurement for the part.
    Expect 20 rows, each 7.251627e-6 m^3 within 1 %. Each centroid should sit at
    r = 130.154 mm and z = 0.
11. `save_document(file_path='...\10_cad\vanes.SLDPRT')`.

**Name the bodies by angle:** the body at atan2(cy, cx) = 17.917 + (k - 1) x
18 deg (mod 360) is `vane_k`. Use `execute_code`, never bare `python`. The
20-row table is in `references/vane-geometry.md` section 6.

On-miss:

| Symptom | Cause | Repair |
|---|---|---|
| step 7 gives 1 body or `EXTRUSION_FAILED` | a card was altered or a record failed | `analyze_model('sketch', name=...)`, delete the sketch, re-send the cards unchanged |
| step 9 still gives about 1.72e-4 | the inner cut did not apply | `analyze_model('sketch')`, delete the cut, re-send card R6b unchanged |
| about 1.93e-4 total | depth 0.016 was used, not 0.012 | rebuild the boss |
| centroids near 155 deg + (k - 1) x 18 | wrong branch; the cards were not used | rebuild from the cards |

## Part 4: `hat` - 10 calls

1. `open_new_part`.
2. `create_sketch(plane='Right Plane')`. Read `xdir`. If it is [0, 0, -1] (the
   measured value), use card R7. If it is [0, 0, 1], use card R7-alt.
3. `add_sketch_entities(segments=<card R7>)`. Expect line 9 (8 profile lines and
   1 construction line on the axis).
4. `extrude_feature(feature_type='revolve', angle=360, axis_x1=-0.060, axis_y1=0, axis_x2=0.030, axis_y2=0)`.
   Card R7-alt uses the mirrored axis given with that card. Expect
   **5.209012e-4 m^3**.
5. `create_sketch(plane='Front Plane')`.
6. `add_sketch_entities(segments=<card R8>)`. Expect circle 5.
7. `extrude_feature(feature_type='cut', depth=0.100, mid_plane=true)`. Expect
   **5.132043e-4 m^3** (a change of -7.6969e-6). The cut is exact: the only
   material at r = 50.5 to 64.5 mm is the flange.
8. `analyze_model('mass_properties')`. Expect centroid (0, 0, **+18.095**) mm.
9. `analyze_model('faces', axis='[0,0,1]')`. This is the hat's one risky-feature
   read, because the revolve direction is only proven by faces. Expect planar
   faces at z = +43 (area 18 617.08 mm^2), +33, -6 (4 024.38 mm^2) and -16 mm.
10. `save_document(file_path='...\10_cad\hat.SLDPRT')`.

On-miss: a centroid of -18.1 mm or faces at z = -43 mean the Right Plane mapping
was inverted. Delete the revolve and the sketch, and redo with the other card.
A volume of about 5.43e-4 m^3 is the retired r = 97 hat, so the card was not
used. A volume of 5.209e-4 after step 7 means the hole cut did nothing.

## Rotor gate (PRD section 4)

| Body | Volume m^3 | Centroid mm | Bbox mm |
|---|---|---|---|
| `cheek_out` | 5.717699e-4 | (0, 0, +11.000) | x, y -165 to 165; z +6 to +16 |
| `cheek_in` | 5.717699e-4 | (0, 0, -11.000) | x, y -165 to 165; z -16 to -6 |
| each vane | 7.251627e-6 | r 130.154 at 17.917 + (k - 1) x 18 deg, z 0 | z -6 to +6 |
| `vane_01` | | (123.842, 40.040, 0) | x 94.922 to 143.121; y -3.850 to 90.942 |
| `hat` | 5.132043e-4 | (0, 0, +18.095) | x, y -95 to 95; z -16 to +43 |

Tolerances: volume 1 %, centroid 0.1 mm, bbox 0.05 mm. The z extents are
the extrude bands on the data cards, confirmed by volume and centroid; the hat's
z = -16 and +43 faces are read once with `analyze_model('faces', axis='[0,0,1]')`. For x and y,
`bbox_method` is "data-card vertices, confirmed by volume and centroid".

Rotor total 1.801777e-3 m^3, mass **12.973 kg** at 7200 kg/m^3 (MAS-01 <= 13.5).
Closed forms and symptoms: `references/volume-derivations.md`.

**Handedness:** the vanes sweep towards +theta as r grows (-2.3225 to +2.2858
deg at r = 95, +29.8420 to +33.4470 deg at r = 165): clockwise viewed from +Z,
omega0 = -84.1751 rad/s. Write these in `vane_hand`.

## References

- `references/sketch-data.md` - cards R1 to R8 with expected counts and
  checksums. **Use these.**
- `references/vane-geometry.md` - the two-circle derivation, the corner
  table and the per-vane centroid naming table.
- `references/volume-derivations.md` - closed-form volumes, Pappus for the hat,
  symptom table.
- `references/rotor-lessons.md` - the sliver post-mortem, why the rotor is four
  bodies, and the run-1 timing lessons.

## Verification

The rotor is done only when all of these are printed with measured values:

- `cheek_out` and `cheek_in`: 5.717699e-4 m^3, centroid z +11.000 and -11.000
  mm, PASS.
- `vanes`: 20 bodies, each 7.251627e-6 m^3 within 1 %. Each centroid sits
  within 0.1 mm of its table value and is named `vane_01` to `vane_20` by
  angle.
- `hat`: 5.132043e-4 m^3, centroid (0, 0, +18.095) mm, planar faces at +43,
  +33, -6 and -16 mm.
- Every `add_sketch_entities` call used a card unchanged, and its counts
  matched.
- About 36 calls in total, with one `analyze_model` per part (two for the hat).
- No hole, fillet, pattern or second rotor model exists in the run folder.
