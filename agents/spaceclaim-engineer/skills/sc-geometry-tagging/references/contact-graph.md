# The contact graph - 45 interfaces, found by geometry

Open this before step 9 of SKILL.md, and whenever the contact count is not 45.

## Why it matters

Every contact becomes a coupled thermal interface in Fluent. It only exists if
both sides are plain faces. A named selection on a face that is **entirely** a
contact turns it into an uncoupled wall. Measured in the predecessor: the pad
patches were tagged, nothing warned, and the solve reached Fluent's 5000 K
ceiling within 0.1 s of simulated time. So contacts are found **before**
classification, and a full-contact face never enters a group. The opposite
mistake is just as real: run 1 dropped partly covered faces from their groups
(`face-classification-and-areas.md`).

## The 45 expected contacts (PRD section 4)

| # | Bodies | Where | Area mm^2 | Full-contact side | Partial-contact side |
|---|---|---|---|---|---|
| 1 | `outerpad` / `cheek_out` | plane z = +16 | 5 864.31 | pad friction face | cheek friction face (57 176.99) |
| 2 | `innerpad` / `cheek_in` | plane z = -16 | 5 864.31 | pad friction face | cheek friction face |
| 3 | `outerpad` / `bp_outer` | plane z = +28 | 5 864.31 | pad back face | backing front face (7 330.38) |
| 4 | `innerpad` / `bp_inner` | plane z = -28 | 5 864.31 | pad back face | backing front face |
| 5 to 24 | `vane_k` / `cheek_out` | plane z = +6 | 604.30 each | vane top face | cheek inner face |
| 25 to 44 | `vane_k` / `cheek_in` | plane z = -6 | 604.30 each | vane bottom face | cheek inner face |
| 45 | `hat` / `cheek_in` | cylinder r = 95, z = -16 to -6 | 5 969.03 | both faces | none |

Total contact area: 4 x 5 864.31 + 40 x 604.30 + 5 969.03 = 53 598.3 mm^2.
Body degrees: `cheek_out` 21, `cheek_in` 22, each vane 2, `hat` 1, each pad 2,
each backing plate 1; sum 90 = 2 x 45.

**Not contacts** (edge-only or disjoint; they must not appear):

| Pair | Why |
|---|---|
| `hat` / any vane | hat cylinder stops at z = -6 where the vane ends start: an edge |
| hat step face z = -6 (r = 88 to 95) / vane bottom faces | same plane, radii only touch at r = 95 |
| hat bottom z = -16 (r = 78 to 95) / `innerpad` z = -16 | radii 78 to 95 and 120 to 160 do not overlap |
| `cheek_out` bore / vane inner ends (r = 95) | z ranges only touch at z = +6 |
| cheek OD / vane outer ends (r = 165) | z ranges only touch at z = +/-6 |

## One face snapshot (cheap)

In one step, for every body: `faces = body.faces` once, and
`tess = body.get_raw_tessellation()` once (face id -> vertices). Then per face:

| Field | Source | Server calls |
|---|---|---|
| `face_id`, `surface_type` | `face.id`, `face.surface_type` | 0 |
| `area_mm2` | `face.area.m_as("mm**2")` | 1 |
| bbox in mm | `face.bounding_box.min_corner / max_corner` | 1 |
| plane: `z_mm`, `nz` | bbox z (min equals max); `face.normal().z` | 2 |
| cylinder or cone: `radius_mm`, `axis_xy_mm` | `g = face.shape.geometry`; `g.radius.m_as("mm")`; `g.origin.x`, `g.origin.y` in mm (cone: record, not used for contacts) | 2 |
| `r_min_mm`, `r_max_mm` | `hypot(x, y)` over that face's tessellation vertices | 0 |

About 183 faces x 4 calls plus 2 per body: well under a minute. If it runs
longer, submit the step as a job (it still only connects). Check once that the
tessellation keys equal the set of `face.id` values (UNVERIFIED otherwise).

## The coincidence test (a partner)

Two faces F and G on **different** bodies are coincident when:

- **Planes:** `|zF - zG| < 0.001 mm`; `nzF * nzG < -0.9` (opposed); radius
  ranges overlap by **more than** 0.001 mm; xy bboxes overlap by more than
  0.001 mm in both x and y.
- **Cylinders:** same axis (`axis_xy_mm` within 0.02 mm); radii equal within
  0.02 mm; z ranges overlap by **more than** 0.001 mm; xy bboxes overlap by
  more than 0.001 mm. The axis test keeps the r = 117 and r = 123 flanks of
  neighbouring vanes (same radius, different centres) apart.

"More than" matters: every pair in the not-a-contact table has an overlap of
exactly zero. The radius test matters too: without it the hat step face (bbox
x, y = -95 to 95) paired with all 20 vane bottom faces and 4 024.38 mm^2 of hat
surface vanished from `wall-outer` (predecessor).

## Full or partial (the containment test)

For a face F with at least one partner G:

- F is **full contact** if, for some partner G, F lies inside G: radius range
  of F inside that of G and xy bbox of F inside that of G, each within 0.01 mm
  (cylinders: z range inside instead of radius range).
- Otherwise F is **partial contact**: tagged in full with its group.

Worked check: a vane top face (r = 95 to 165, x = 94.9 to 143.1) is inside the
cheek inner face (r = 95 to 165, x = -165 to 165): full. The cheek inner face
is not inside any vane: partial. The pad back face (x = 103.9 to 160,
y = -80 to 80) is inside the backing front face (x = 99.6 to 165,
y = -82.5 to 82.5): full; the backing front face is partial.

## Contact area and the gate

The contact area of a body pair is the summed area of the **full-contact**
faces of that pair (for `hat` / `cheek_in` both sides are full and equal: take
one side). Gate: exactly 45 body pairs, each in the expected table and each
within 1 % of its PRD area, and every pair has a full-contact side.

- 46 or more pairs: an edge-only pair was accepted; require strictly positive
  overlap.
- Fewer than 45: measure the gap with
  `modeler.measurement_tools.min_distance_between_objects(a, b)`. A real gap is
  an upstream finding for the lead.
- `body.get_collision(other)` giving `INTERSECT` or `CONTAINED` for any pair is
  interference (Gate 1 promised 0 mm^3): upstream HALT. `TOUCH` cannot tell a
  face contact from an edge contact; do not count contacts with it.

## Record in tag_report.json

`contact_graph`: 45 rows of
`{"pair": ["outerpad", "cheek_out"], "kind": "plane z=+16.000",
"expected_area_mm2": 5864.31, "measured_area_mm2": ..., "delta_pct": ...,
"full_face_ids": [...], "partial_face_ids": [...], "pass": true}`,
plus `contact_count` and `contact_total_area_mm2` (53 598.3 derived), and
`diagnostics.edge_only_contacts` with the rejected zero-overlap pairs.
