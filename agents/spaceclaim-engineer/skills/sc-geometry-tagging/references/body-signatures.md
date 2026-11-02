# Body signatures - identifying 28 bodies by measurement

Open this before step 5 of SKILL.md, and whenever a body matches nothing or
matches twice.

## The rule

A body is identified when its **measured** volume, bounding box and mass
centroid all fall inside PRD section 4 tolerance for exactly one PRD row, and
no other body does. Imported names and list order are ignored: run 1 died with
`StopIteration` looking for a body named `cheek_out` on a fresh import.
Component names (`vanes`, `cheek_in`, `cheek_out`, `hat` in run 1) are a hint
you may print, never an identity. Tolerances (PRD section 4): volume within
1 %, centroid within 0.1 mm, bbox within 0.05 mm.

## Signature table (mm, mm^3)

Values from PRD section 4. Bbox cells marked "derived" come from the PRD
section 2 and 3 sector definitions.

| Name | Volume | Centroid (x, y, z) | Bbox x | Bbox y | Bbox z |
|---|---|---|---|---|---|
| `cheek_out` | 571 769.86 | (0, 0, +11.000) | -165 to 165 | -165 to 165 | +6 to +16 |
| `cheek_in` | 571 769.86 | (0, 0, -11.000) | -165 to 165 | -165 to 165 | -16 to -6 |
| `hat` | 513 204.29 | (0, 0, +18.095) | -95 to 95 | -95 to 95 | -16 to +43 |
| `outerpad` | 70 371.68 | (134.600, 0, +22.000) | 103.923 to 160.000 (derived) | -80.000 to 80.000 (derived) | +16 to +28 |
| `innerpad` | 70 371.68 | (134.600, 0, -22.000) | 103.923 to 160.000 (derived) | -80.000 to 80.000 (derived) | -28 to -16 |
| `bp_outer` | 43 982.30 | (135.111, 0, +31.000) | 99.593 to 165.000 (derived) | -82.500 to 82.500 (derived) | +28 to +34 |
| `bp_inner` | 43 982.30 | (135.111, 0, -31.000) | 99.593 to 165.000 (derived) | -82.500 to 82.500 (derived) | -34 to -28 |
| `vane_01` | 7 251.63 | (123.842, 40.040, 0) | 94.922 to 143.121 | -3.850 to 90.942 | -6 to +6 |
| `vane_k`, k = 2 to 20 | 7 251.63 | r = 130.154 at 17.917 + (k - 1) x 18 deg, z = 0 | not given | not given | -6 to +6 |
| calliper | 617 081.48 | (146.143, 0.000, +0.369) | 81.245 to 200.000 | -98.418 to 98.418 | -57 to +57 |

Pad sector r = 120 to 160 over -30 to +30 deg: x min = 120 cos 30 = 103.923,
y max = 160 sin 30 = 80.000. Backing r = 115 to 165: 99.593 and 82.500.

Write this table **once** as a constants block with fixed key names
(`volume_mm3`, `centroid_mm`, `bbox_mm` as `[xmin, ymin, zmin, xmax, ymax, zmax]`)
and paste the same block into every step that needs it. Run 1 crashed four
times on its own renamed keys (`centroid_mm`, `bbox_mm`, `imported_index`,
`bbox_center_mm`).

## Near-collisions

| Pair | Separated by | Trap |
|---|---|---|
| `cheek_out` / `cheek_in` | z only | identical volume |
| pads, backing plates | z only | identical volume within the pair |
| calliper / cheek | 617 081.48 vs 571 769.86 (7.9 %) | a 5 % window overlaps both |
| 20 vanes | centroid angle only | identical volume and z band |

Build the full match matrix and assert it is a permutation (20 vane rows as one
class). Report each body's second-best row and its largest delta.

## Mass centroid on 26.1: from the raw tessellation

`body.centroid` is gated at 27.1, and `body.tessellate()` needs graphics
packages that are not installed (`api-verified.md` section 7). The bbox centre
is not a mass centroid: hat bbox centre z = +13.5 against the PRD +18.095, and
the calliper bbox centre z = 0.0 against +0.369. Run 1 matched on bbox centres
and got 2, then 0 calliper candidates.

`body.get_raw_tessellation()` (26.1, not graphics-gated) returns, per face id,
`"vertices"` (flat x, y, z list in metres, world transform applied) and
`"faces"` (`[3, i, j, k, 3, ...]`). Apply the divergence theorem over all faces
of the body.

API idiom:

```python
import numpy as np
V6 = 0.0; M = np.zeros(3)
for t in body.get_raw_tessellation().values():
    p = np.asarray(t["vertices"], float).reshape(-1, 3) * 1000.0     # mm
    f = np.asarray(t["faces"], int).reshape(-1, 4); assert (f[:, 0] == 3).all()
    a, b, c = p[f[:, 1]], p[f[:, 2]], p[f[:, 3]]
    v6 = np.einsum("ij,ij->i", a, np.cross(b, c))
    V6 += v6.sum(); M += ((a + b + c) * v6[:, None]).sum(axis=0)
vol_mm3, centroid_mm = V6 / 6.0, M / (4.0 * V6)
```

Checks that make it trustworthy:

- `abs(vol_mm3)` within 0.5 % of `body.volume.m_as("mm**3")`. This proves the
  triangles close the surface with one orientation (UNVERIFIED until you see
  it). A negative volume with good agreement is fine: the centroid is a ratio.
- On a miss, re-tessellate once with
  `TessellationOptions(surface_deviation=..., angle_deviation=...)` and
  `reset_cache=True`. If it still misses, record `centroid_mm: null` with the
  reason, match on volume plus bbox, and mark the row `centroid_checked: false`
  (OPEN, never PASS).
- Save the triangles of all 28 bodies to `20_spaceclaim\tess_pre.npz` in the
  same step. The CAD screenshots use them; no second tessellation is needed.

## Bounding box

`body.bounding_box` returns `.min_corner`, `.max_corner`, `.center`.
`get_bounding_box(tight=True)` is 27.1. Run 1 measured the calliper bbox
centre at x = 140.6228 (PRD (81.245 + 200.000) / 2 = 140.6225) and vane bbox
centres matching the PRD `vane_01` bbox, so the box looked tight on 26.1. If a
curved body still misses by a fraction of a millimetre, measure the extents
from its tessellation vertices too and record both methods.

## Ordering the vanes

1. Centroid angle `theta = degrees(atan2(cy, cx)) mod 360`.
2. Sort ascending: `vane_01` at 17.917 deg, `vane_k` at 17.917 + (k - 1) x 18.
3. Each within 0.05 deg of its slot and within 0.1 mm of r = 130.154.
4. `vane_01` also against the PRD bbox.

Handedness: `vane_01` tessellation vertices at r = 95 sit near -2.3 to +2.3 deg
and at r = 165 near +29.8 to +33.4 deg (PRD 3.2). Inverted is an upstream
finding.

## Cross-check with Gate 1

Compare each SpaceClaim row with the `cad_report.json` row of the same name. A
body that passes the PRD but differs from Gate 1 by more than 0.1 % in volume or
0.05 mm in centroid is a translation finding: report both numbers.

## Record in tag_report.json

`body_map`: 28 rows with `name`, `body_id`, `component`, `volume_mm3`,
`volume_m3`, `expected_volume_mm3`, `volume_delta_pct`, `centroid_mm`,
`expected_centroid_mm`, `centroid_delta_mm`, `centroid_method`
("raw tessellation, divergence theorem"), `tess_volume_delta_pct`, `bbox_mm`,
`expected_bbox_mm`, `bbox_delta_mm`, `second_best`, `gate1_volume_delta_pct`,
`pass`.
