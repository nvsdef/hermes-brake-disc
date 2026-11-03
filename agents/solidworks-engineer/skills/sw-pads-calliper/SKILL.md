---
name: sw-pads-calliper
description: "Build pads, plates, calliper; assemble; export STEP."
version: 1.2.0
author: "sdefibaugh"
license: Apache-2.0
platforms: [windows]
metadata:
  hermes:
    tags: [brake, solidworks, calliper, assembly]
---

# Pads, plates, calliper, assembly, STEP and Gate 1 (PRD H1.2)

This skill covers five parts, then `brake.SLDASM` with **all 9** components,
`brake.step` and `cad_report.json`. The geometry authority is PRD sections 3.4,
3.5 and 4, and the contract is `specs/handoffs.md` Gate 1. Build the rotor
first (`sw-rotor-build`). Every sketch comes from a card in
`references/sketch-data.md`: copy it and do not compute. Run 1 exported an
assembly with 4 of the 9 parts (a 23-solid STEP) and needed a repair
commission. Steps A3 and A7 below make that impossible.

Budget: about **28 calls for pads and plates, 26 for the calliper and 23 for
assembly, export and report**.

## When to use

When building or checking `outerpad`, `innerpad`, `bp_outer`, `bp_inner` or
`calliper`, when assembling, and when writing Gate 1.

## Parts 5 to 8: pads and plates - 7 calls each

Build each one independently in a new part. Never copy `outerpad` to make
`innerpad`: a copied plane offset was measured to keep its old sign.

| Part | Plane offset | Card | Depth (mid-plane) | Volume m^3 | Centroid mm |
|---|---|---|---|---|---|
| `outerpad` | +0.022 | P1 | 0.012 | 7.037168e-5 | (134.600, 0, +22.000) |
| `innerpad` | -0.022 | P1 | 0.012 | 7.037168e-5 | (134.600, 0, -22.000) |
| `bp_outer` | +0.031 | P2 | 0.006 | 4.398230e-5 | (135.111, 0, +31.000) |
| `bp_inner` | -0.031 | P2 | 0.006 | 4.398230e-5 | (135.111, 0, -31.000) |

1. `open_new_part`.
2. `add_reference_geometry(type='plane', ref_plane_name='Front Plane', offset=<table>)`.
3. `create_sketch(plane=<returned name>)`. The frame origin z must equal the
   offset.
4. `add_sketch_entities(segments=<card>)`. Expect arc_center 2 and line 2.
5. `extrude_feature(feature_type='boss', depth=<table>, mid_plane=true)`. The
   volume must match the table.
6. `analyze_model('mass_properties')`. Volume and centroid must match the
   table.
7. `save_document(file_path='...\10_cad\<part>.SLDPRT')`.

On-miss: if the volume is right and the centroid z has the wrong sign, the
plane is wrong. Delete the plane and the extrude, and rebuild. Do not assign a
material. MAT-02 has no SolidWorks equivalent.

## Part 9: `calliper` - 26 calls

1. `open_new_part`.
2. Base: `create_sketch(plane='Front Plane')`, then
   `add_sketch_entities(segments=<card C1>)` (arc_center 8, line 4), then
   `extrude_feature(feature_type='boss', depth=0.114, mid_plane=true)`. Expect
   **1.897369e-3 m^3** and **1 body**.
3. Slot and windows: plane at **-0.0002**, then `create_sketch`, then card C2
   (arc_center 6, line 6), then
   `extrude_feature(feature_type='cut', depth=0.0776, mid_plane=true)`. Expect
   **7.851263e-4**.
4. Outboard step: plane at **+0.0495**, then sketch, then card C3 (circle 2),
   then cut with `depth=0.015`, `mid_plane=true`. Expect **7.138413e-4**.
5. Inboard step: plane at **-0.0495**, then sketch, then card C3, then the same
   cut. Expect **6.425562e-4**.
6. Outboard bores: plane at **+0.0426**, then sketch, then card C4 (circle 3),
   then cut with `depth=0.008`, `mid_plane=true`. Expect **6.298139e-4**.
7. Inboard bores: plane at **-0.043**, then sketch, then card C4, then the same
   cut. Expect **6.170815e-4**.
8. `analyze_model('mass_properties')`. Expect 6.170815e-4 m^3 and centroid
   (146.143, 0.000, **+0.369**) mm.
9. `save_document(file_path='...\10_cad\calliper.SLDPRT')`.

The gate is the PRD signature. SpaceClaim deletes the calliper by it: volume
6.170815e-4 m^3, centroid (146.143, 0.000, +0.369) mm, bbox x = 81.245 to
200.000, y = -98.418 to 98.418, z = -57 to +57 mm, and 1 body. A centroid z of
0.000 means the calliper was built symmetric, which is wrong. To localise a
volume miss by band, use the face-area table in
`references/calliper-build.md`. If card C1 returns `EXTRUSION_FAILED`, fall
back to the four-sketch base described in that file.

## Assembly, STEP and report - 23 calls

**A1.** `open_new_assembly`.

**A2.** Nine `insert_component` calls, in this order: `cheek_out`, `cheek_in`,
`vanes`, `hat`, `outerpad`, `innerpad`, `bp_outer`, `bp_inner`, `calliper`.
Each call uses `file_path='C:\\brake-runs\\<run-id>\\10_cad\\<part>.SLDPRT'`,
`transform_json='[1,0,0,0,1,0,0,0,1,0,0,0,1]'` and `fixed=true`. Never use x, y
and z: they centre the bounding box. Tick each part off a written list of 9 as
its call returns.

**A3. Component gate, before anything is saved or exported.**
`analyze_assembly(analysis_type='components')`.
- `component_count` = **9**.
- The names are `cheek_out-1`, `cheek_in-1`, `vanes-1`, `hat-1`,
  `outerpad-1`, `innerpad-1`, `bp_outer-1`, `bp_inner-1` and `calliper-1`.
  Instance numbers may differ.
- Every transform is exactly `[1,0,0, 0,1,0, 0,0,1, 0,0,0, 1]`. (This
  SolidPilot build returns no `children` field; nothing to check there.)
- On-miss: insert the missing parts and repeat A3. **Do not go on to A5 with
  fewer than 9.** A transform that is not identity: delete that component and
  re-insert it.

**A4. Placement spot check in assembly context: 2 calls.** SolidPilot has no
centroid read for an assembly, so check faces. Call
`analyze_assembly(analysis_type='faces', component=...)` for `cheek_out-1`
and `calliper-1`. Skip `vanes-1`: there is no axis filter and it dumps all 120
faces; the vanes' per-body centroids already place them. Apply the returned transform (identity, so local
equals global). Expect:
- `cheek_out-1`: planar faces at z = 0.006 and 0.016.
- `calliper-1`: planar faces at z = +/-0.057, +0.0386 and -0.039.

Every part was built at its true global position and the transforms are
identity, so each part's own `mass_properties` centroid (and `bodies` for the
vanes) is already the global centroid. There is no STEP re-import in H1.2 fast:
SpaceClaim's Gate 2 import re-measures all 28 bodies independently. The axial
clearances come from the `calliper-1` faces here and the pad and plate bands:
38.6 - 34 = 4.6 and -34 - (-39) = 5.0.

**A5.** `save_document(file_path='...\10_cad\brake.SLDASM')`.

**A6.** `export_document(format='STEP', file_path='...\10_cad\brake.step')`.

**A7. Count the file, before any report is written: 1 call.** Use
`execute_code`, or PowerShell `Select-String`. Never type bare `python`.
- `MANIFOLD_SOLID_BREP` = **28**.
- PRODUCT (regex `= ?PRODUCT ?\(`) = **10**.
- Record the `FILE_SCHEMA` value and the SHA-256.
- On-miss: 23 means the pads, plates and calliper are missing (run 1). Go back
  to A3.

**A8. Hashes and report: 2 calls.** Do **not** re-open `brake.step` in
SolidWorks: run 2 measured that step at about 22 calls (SolidWorks imports it as
an assembly, and its title collides with the open `brake.SLDASM`), and it proves
nothing that the per-part reads and SpaceClaim's Gate 2 import do not. Use `execute_code` to compute the SHA-256
of the 9 `.SLDPRT` files and `brake.SLDASM`. Then write `cad_report.json` with
the file tool. The schema is in `references/assembly-and-report.md`. It
includes the `assembly` and `timing` blocks, and it contains no views.

## HALT

Each failing check gets two repairs: delete the feature, rebuild it from the
card, and re-measure. On the third FAIL, stop and return the part, the
quantity, the expected value and both measured values. Never adjust a PRD
number or a tolerance.

## References

- `references/sketch-data.md` - cards P1, P2 and C1 to C4, with counts and
  running checksums. **Use these.**
- `references/calliper-build.md` - band structure, face-area localisation,
  the fallback base method and calliper lessons.
- `references/assembly-and-report.md` - clearances, interference by envelope
  separation, requirement keys and the `cad_report.json` schema.

## Verification

Gate 1 is ready only when:

- The four pads and plates each print volume and centroid PASS lines against
  the table above.
- The calliper prints 6.170815e-4 m^3 and (146.143, 0.000, +0.369) mm as 1 body.
- A3 printed `component_count` 9 with the 9 names and identity transforms
  **before** A5.
- A7 counted 28 `MANIFOLD_SOLID_BREP` and 10 PRODUCT in the file **before**
  `cad_report.json` was written.
- Every one of the 28 bodies has a per-part volume and centroid PASS line, and
  no STEP re-import was done.
- `cad_report.json` has `assembly`, `timing`, `step`, `native_hashes`
  (10 files), 28 body rows with `vane_01` to `vane_20` in angular order, and no
  view or drawing keys.
