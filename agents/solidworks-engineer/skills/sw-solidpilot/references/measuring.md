# Measuring bodies with SolidPilot

SolidPilot gives volume, area and centroid directly. It does not give a bounding
box, an interference volume or a section area. This sheet says how to derive
each PRD section 4 quantity from what the tools do return, and how to record the
method so the lead can audit it.

## What each read returns

| Call | Returns | Units |
|---|---|---|
| `analyze_model('mass_properties')` | volume, surface_area, centroid (cx, cy, cz) of the whole part | m^3, m^2, m |
| `analyze_model('bodies')` | per body: volume, area, centroid, edge and vertex counts, face-index range | same |
| `analyze_model('faces')` | every face with a stable index `i`; planar faces add normal, area and a point on the plane | m, m^2 |
| `analyze_model('faces', axis='[0,0,1]')` | only planar faces whose normal is parallel to Z | same |
| `analyze_model('edges', near='[x,y,z]', k=8)` | the 8 edges nearest the point, each with start, end, midpoint, length for closed curves, and `dist` | m |
| `analyze_model('geometry')` | body, face, edge and vertex counts | - |
| `extrude_feature` result | `result_geometry {volume, faces, edges}` after the feature | m^3 |

`mass_properties` on a multibody part (the vanes) gives the combined volume and
the combined centroid. For 20 equal vanes the combined centroid is on the axis,
(0, 0, 0). Use `bodies` for the per-vane numbers.

## Volume and centroid

Compare directly with PRD section 4 after converting: m^3 x 1e9 = mm^3,
m x 1e3 = mm. Tolerances: volume within 1 %, centroid within 0.1 mm (each
component).

Volume delta in percent: `100 * (measured - expected) / expected`.

## Bounding box - derive it and say how

| Extent | How |
|---|---|
| z min and z max | Planar faces normal to Z (`faces`, `axis='[0,0,1]'`): the lowest and highest face z. Every body in this brake has flat end faces at its band limits |
| Radius of a round face | A circular edge: `length / (2 pi)`. Check its midpoint lies at that radius from the axis |
| x, y extents of an axisymmetric body | +/- the outer radius (cheeks: 165 mm; hat: 95 mm) |
| x, y extents of a vane | Its vertices. The PRD corners (94.922, -3.850) and (143.121, 82.106) and y max 90.942 are all vertices on the r = 95 and r = 165 ends |
| x, y extents of a pad or backing plate | Vertices at the 30 deg corners give x min and |y| max; x max is the outer arc at 0 deg (160 or 165 mm), which is mid-arc, not a vertex |
| x, y extents of the calliper | x min 81.245 is a vertex (r = 98 at +/-34 deg). y max 98.418 is a vertex (r = 176 at 34 deg). x max 200.000 is the middle of the 0 deg lobe arc in the z bands where that lobe survives |

For a mid-arc extreme, find the arc with `edges` near the expected point and
compute the extreme from its centre and radius (circle length / (2 pi)).
Tolerance is 0.05 mm per bbox value.

Record `bbox_method` per body, for example
`"z from planar faces; r from circular edge lengths; x,y from vertices"`. If a
value cannot be derived, write `null` with a reason; the row is then OPEN.

## Face areas as a second derivation

Planar face areas give independent checks that do not depend on the volume
integration. Examples (PRD section 4 and values derived from PRD geometry):

| Face | Expected area mm^2 |
|---|---|
| each cheek flat face, full annulus r = 95 to 165 | 57 176.99 |
| vane top or bottom face (the vane section) | 604.30 |
| pad face (sector r = 120 to 160, 60 deg) | 5 864.31 |
| backing-plate face (sector r = 115 to 165, 60 deg) | 7 330.38 |
| hat mounting face z = +43 (annulus r = 35 to 86 less 5 holes) | 18 617.08 |
| hat ledge z = -6 (annulus r = 88 to 95) | 4 024.38 |
| calliper faces: see `sw-pads-calliper` -> `references/calliper-build.md` | |

Cylindrical face areas: if `faces` does not report an area for a non-planar face,
compute it from the edge circles (2 pi r h). The hat/cheek_in contact cylinder
is 2 pi x 95 x 10 = 5 969.03 mm^2.

## Counting slivers

A micron sliver passes a volume gate at 0.002 % and a zero-area-face gate (a
2 um x 12 mm face is 2.4e-8 m^2, not zero). Look for them directly:

- Any planar face area below 1 mm^2 on this brake is a defect. The intended
  planar faces are hundreds of mm^2 or more (a piston-bore bottom is
  530.93 mm^2, a vane face 604.30 mm^2).
- Any edge shorter than 3 mm is suspect. The predecessor's good build had a
  shortest vertex-to-vertex chord of 3.000 mm; a defective calliper had
  0.400 mm steps.
- Face counts that differ from the expected topology (for example a cheek with
  more than 4 faces in SolidWorks) mean something was added.

## Contacts and clearances

SolidPilot has no interference or distance tool. Use measured positions:

- **Axial clearance:** difference of measured planar-face z values (for example
  calliper slot face z = +38.6 against `bp_outer` top face z = +34 gives 4.6 mm).
- **Radial clearance:** difference of measured radii (calliper bridge inner
  cylinder r = 178 against rotor outer r = 165 gives 13.0 mm).
- **Contact area:** the smaller of the two coincident planar faces when one lies
  wholly inside the other (pad face 5 864.31 mm^2 on the cheek face).
- **Interference:** there is no direct measurement. Derive it from the pairwise
  envelope check in `sw-pads-calliper` -> `references/assembly-and-report.md`,
  record the method, and never write 0 without it.

## Printing the comparison

One line per quantity, in the same step as the measurement:

```
hat volume_m3   expected 5.132043e-4  measured 5.132040e-4  delta -0.000 %  PASS
hat centroid_mm expected (0, 0, 18.095)  measured (0.000, 0.000, 18.095)  max delta 0.000  PASS
hat z_mm        expected -16.000 to 43.000  measured -16.000 to 43.000  PASS
hat r_max_mm    expected 95.000  measured 95.000  PASS
```

A line without an expected value is not a check.
