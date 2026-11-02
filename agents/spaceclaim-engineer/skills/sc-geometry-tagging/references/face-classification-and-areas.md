# Face classification, wall-vent and wall-outer, and every predicted area

Open this before steps 9 to 11 of SKILL.md, when an area gate fails, or when
someone asks where 167 037.60 or 142 865.51 mm^2 comes from.

## What the groups are for

PRD section 6 prescribes three convection coefficients at omega_ref: vent faces
130, outer rotor and hat faces 85, exposed pad and backing faces
40 W/(m^2 K). `wall-vent` is the only place where the vanes do anything thermal
beyond conduction, and THM-05 ("vent cooling modelled explicitly") depends on
it. Only two face selections are created: `wall-vent` and `wall-outer`. Pad and
backing faces are measured and reported, not tagged; Fluent collects them as
the remaining walls. Contact faces are never tagged.

## The rule that run 1 got wrong

Every face gets exactly one of three **contact states**, from the contact graph
(`contact-graph.md`):

| State | Test | Treatment before imprint |
|---|---|---|
| **full contact** | the face has a coincident partner face on another body, and the face lies **entirely inside** that partner (radius range and xy bbox inside, 0.01 mm) | untagged; it becomes a coupled interface |
| **partial contact** (containing) | the face has one or more coincident partners, but it is **not** inside any of them | tagged **in full** with its group; the mesher cuts the footprints out later |
| **free** | no coincident partner | tagged with its group |

Run 1 treated "has a partner" as "is a contact face". That excluded the two
cheek inner faces (114 354 mm^2) from `wall-vent`, the two friction faces from
`wall-outer`, and the two backing front faces (14 660.8 mm^2) from pad/backing.
Measured: `wall-vent` 52 683.6, pad/backing 28 336.5 mm^2
(`run1-lessons.md`).

The partial-contact faces in this model, all tagged or counted in full:

| Face | Partners on it | Why it is not full contact |
|---|---|---|
| `cheek_out` z = +6, `cheek_in` z = -6 (inner faces) | 20 vane faces each | the annulus is much larger than any vane footprint |
| `cheek_out` z = +16, `cheek_in` z = -16 (friction faces) | 1 pad face each | the pad sector covers 5 864.31 of 57 176.99 mm^2 |
| `bp_outer` z = +28, `bp_inner` z = -28 (backing front faces) | 1 pad back face each | backing r = 115 to 165 is larger than the pad r = 120 to 160 |

The full-contact faces: 40 vane faces at z = +/-6, the 2 pad friction faces,
the 2 pad back faces, the `cheek_in` bore r = 95 and the hat cylinder r = 95
(each lies inside the other).

## Group assignment

| Body | Face (geometric definition) | Contact state | Group |
|---|---|---|---|
| `cheek_out` | plane z = +6, normal -z, r = 95 to 165 | partial | **wall-vent** |
| `cheek_in` | plane z = -6, normal +z, r = 95 to 165 | partial | **wall-vent** |
| each vane | two flanks (arcs of r = 117 and 123 about C) and two ends (r = 95 and 165) | free | **wall-vent** |
| each vane | planes z = +6 and z = -6 | full | untagged |
| `cheek_out`, `cheek_in` | friction planes z = +16 and z = -16 | partial | **wall-outer** |
| both cheeks | OD cylinder r = 165 | free | **wall-outer** |
| `cheek_out` | bore r = 95, z = +6 to +16 | free (faces the hat across air) | **wall-outer** |
| `cheek_in` | bore r = 95, z = -16 to -6 | full | untagged |
| `hat` | cylinder r = 95, z = -16 to -6 | full | untagged |
| `hat` | every other face, including the step face z = -6, r = 88 to 95 | free | **wall-outer** |
| pads | friction face and back face | full | untagged |
| pads | two arcs and two flats | free | pad/backing (measured) |
| backing plates | front face | partial | pad/backing (measured) |
| backing plates | back face, two arcs, two flats | free | pad/backing (measured) |

Test the normal **and** the position for the cheek planes: `cheek_out`'s inner
face is the plane at its body's z minimum (+6), `cheek_in`'s at its body's z
maximum (-6).

### The hat step face is not vent

The hat has a planar annulus at z = -6, r = 88 to 95, facing +z, coplanar with
`cheek_in`'s vent face. PRD section 4 puts it in `wall-outer` by decision.
Including it in vent adds 4 024.38 mm^2: `wall-vent` becomes 171 062.0 mm^2
(+2.41 %, fails the 2 % band). Vent planes are only the two cheek inner faces.

## Predicted areas (mm^2, derived from PRD section 3)

| Face | Area each |
|---|---|
| cheek friction face or inner face (annulus r = 95 to 165) | 57 176.99 |
| cheek OD cylinder r = 165, 10 mm | 10 367.26 |
| cheek bore r = 95, 10 mm | 5 969.03 |
| vane z face | 604.30 |
| vane flanks plus ends (one vane) | 2 634.18 (all 20: 52 683.63) |
| hat mounting face z = +43 less 5 holes | 18 617.08 |
| hat outer wall (cone r = 86 to 88) | 26 807.52 |
| hat step face z = -6, r = 88 to 95 | 4 024.38 |
| hat cylinder r = 95 (contact) | 5 969.03 |
| hat bottom z = -16, r = 78 to 95 | 9 239.42 |
| hat inner wall (cone r = 78 to 74) | 23 476.42 |
| hat flange underside z = +33 less holes | 12 585.22 |
| hat centre bore r = 35 | 2 199.11 |
| hat 5 bolt-hole bores, total | 2 199.11 |
| hat exposed total | 99 148.27 |
| pad friction face, pad back face | 5 864.31 |
| pad arcs and flats (one pad) | 4 478.58 |
| backing front face, backing back face | 7 330.38 |
| backing arcs and flats (one plate) | 2 359.30 |

The hat walls are cones (`SURFACETYPE_CONE`); they are `wall-outer`.

## Group totals

| Group | Composition | Before imprint (Gate 2) | Removed by imprint | After imprint (Gate 3) |
|---|---|---|---|---|
| `wall-vent` | 2 x 57 176.99 + 20 x 2 634.18 | **167 037.60** | 40 vane footprints, 24 172.08 | 142 865.51 |
| `wall-outer` | 2 x 57 176.99 + 2 x 10 367.26 + 5 969.03 + 99 148.27 | **240 205.78** | 2 pad footprints, 11 728.61 | 228 477.17 |
| pad/backing exposed | 2 x 4 478.58 + 4 x 7 330.38 + 2 x 2 359.30 | **42 997.28** | 2 pad footprints on the backing, 11 728.61 | 31 268.67 |
| untagged full contact (rotor and pads) | 40 x 604.30 + 2 x 5 969.03 + 4 x 5 864.31 | 59 567.3 | | |

## Gate 2 checks and the after-imprint prediction

Gate 2 checks the **before-imprint** areas, each within 2 %. Then report the
predicted after-imprint values from **measured** contact areas:

```
wall-vent after   = wall-vent measured   - sum of the 40 measured vane/cheek contact areas
wall-outer after  = wall-outer measured  - sum of the 2 measured pad/cheek contact areas
pad/backing after = pad/backing measured - sum of the 2 measured pad/backing contact areas
```

Never compare a before-imprint area with an after-imprint value: 167 037.60
against 142 865.51 reads as +16.9 %, a method error.

## Partition gate

- Every face of the 27 bodies has exactly one state and at most one group.
- Rotor faces: `count(vent) + count(outer) + count(full contact) = count(rotor faces)`,
  and the same by area with a residual below 1e-6 relative.
- No face id is in two groups; no full-contact face is in any group.
- Gate on area, not on face count. Run 1 had 183 faces on the 27 bodies; the
  count depends on how the STEP splits surfaces.

## Build the selections from face ids

`body.faces` makes new objects on every access, so never compare faces by
Python `id()` across two reads (the predecessor's `wall-outer` absorbed every
rotor face that way). The classification step writes `faces.json` with
`face_id`, `body`, `state`, `group`, `area_mm2`. The selection step re-reads the
design, builds `{f.id: f for b in bodies for f in b.faces}`, takes the Face
objects for the listed ids, and fails if any id is missing.

## What Fluent does with the groups

- A selection spanning several bodies arrives **split per body**: `wall-vent`
  as 22 zones, `wall-outer` as 3. Record per-body face counts and areas.
- Fluent assigns boundary types by substring (`inlet`, `outlet`, `symmetry`).
  `wall-vent` is safe; `vent-inlet` would become a velocity inlet.
- At Gate 3 a meshed `wall-vent` equal to the tagged 167 037.60 means shared
  topology carved nothing: that is a failure. Say so in the handback.

## Record in tag_report.json

`named_selections.faces` holds, for `wall-vent` and `wall-outer`: `face_count`,
`per_body`, `area_tagged_mm2`, `predicted_tagged_mm2`, `delta_tagged_pct`,
`tolerance_pct` 2.0, `pass`, `area_after_imprint_mm2`,
`predicted_after_imprint_mm2`, `delta_after_pct`. `diagnostics` holds
`face_partition` and `pad_backing_exposed` (before and after, with `pass`).
