# Pads, plates and calliper sketch data cards (PRD H1.2)

These are **data, not scripts**. Each card is the exact text of the `segments`
argument of `add_sketch_entities`, in metres, 9 decimals. Pass the card text as
a **JSON string** value: `{"segments": "<card text>"}`. Do not re-type, round,
mirror or re-order the numbers, and do not compute them again. Every sketch is
on `Front Plane` or an offset of it, so sketch x = model X and sketch y =
model Y. Confirm the returned frame origin z before adding entities.

`add_sketch_entities` answers with `result_geometry {segment_count, counts per
entity_type}`; the expected counts are under each card. Every extrude and cut
answers with `result_geometry {volume, faces, edges}`; the expected volume
after each feature is in the tables. Tolerance on every volume: 1 %.

No record has a `direction` key: every arc here is a minor arc (under 180 deg).

---

## Card P1 - pad sector (use for `outerpad` and `innerpad`)

r = 120 to 160 mm, -30 to +30 deg. Outer arc, line, inner arc, line.
Expected: segment_count 4, arc_center 2, line 2.

```json
[
{"entity_type":"arc_center","cx":0,"cy":0,"x1":0.138564065,"y1":-0.080000000,"x2":0.138564065,"y2":0.080000000},
{"entity_type":"line","x1":0.138564065,"y1":0.080000000,"x2":0.103923048,"y2":0.060000000},
{"entity_type":"arc_center","cx":0,"cy":0,"x1":0.103923048,"y1":0.060000000,"x2":0.103923048,"y2":-0.060000000},
{"entity_type":"line","x1":0.103923048,"y1":-0.060000000,"x2":0.138564065,"y2":-0.080000000}
]
```

## Card P2 - backing-plate sector (use for `bp_outer` and `bp_inner`)

r = 115 to 165 mm, -30 to +30 deg. Expected: segment_count 4, arc_center 2,
line 2.

```json
[
{"entity_type":"arc_center","cx":0,"cy":0,"x1":0.142894192,"y1":-0.082500000,"x2":0.142894192,"y2":0.082500000},
{"entity_type":"line","x1":0.142894192,"y1":0.082500000,"x2":0.099592921,"y2":0.057500000},
{"entity_type":"arc_center","cx":0,"cy":0,"x1":0.099592921,"y1":0.057500000,"x2":0.099592921,"y2":-0.057500000},
{"entity_type":"line","x1":0.099592921,"y1":-0.057500000,"x2":0.142894192,"y2":-0.082500000}
]
```

### Pad and plate checksum table

| Part | Plane offset (m) | Card | Extrude | Expected volume m^3 | Expected centroid mm |
|---|---|---|---|---|---|
| `outerpad` | +0.022 | P1 | boss, `depth=0.012`, `mid_plane=true` | 7.037168e-5 | (134.600, 0, +22.000) |
| `innerpad` | -0.022 | P1 | boss, `depth=0.012`, `mid_plane=true` | 7.037168e-5 | (134.600, 0, -22.000) |
| `bp_outer` | +0.031 | P2 | boss, `depth=0.006`, `mid_plane=true` | 4.398230e-5 | (135.111, 0, +31.000) |
| `bp_inner` | -0.031 | P2 | boss, `depth=0.006`, `mid_plane=true` | 4.398230e-5 | (135.111, 0, -31.000) |

Each result has 6 faces. Face areas: pad faces 5 864.31 mm^2, plate faces
7 330.38 mm^2.

---

## Calliper cards (PRD 3.4)

The calliper takes six features. Cards C1 and C2 are single contours that
replace the older seven-sketch method (sector plus three lobe sketches, then
slot and windows separately), which is kept as a fallback in
`calliper-build.md`.

### Card C1 - base outline: sector r 98 to 176 (-34 to +34 deg) united with three R40 lobes at r = 160 (-20, 0, +20 deg)

One closed contour of the union, counter-clockwise from the inner corner at
-34 deg. Where each side lobe crosses the 34 deg radial edge (r = 145.161 to
165.333 mm) the outline follows the lobe arc; the outer boundary is r 176 arc,
lobe -20 arc, lobe 0 arc (through x = 200.000), lobe +20 arc, r 176 arc. The
lobes meet each other at r = 186.345 mm on the +/-10 deg rays. Sketch on
`Front Plane`. Expected: segment_count 12, arc_center 8, line 4.

```json
[
{"entity_type":"line","x1":0.081245682,"y1":-0.054800905,"x2":0.120344112,"y2":-0.081173128},
{"entity_type":"arc_center","cx":0.150350819,"cy":-0.054723223,"x1":0.120344112,"y1":-0.081173128,"x2":0.137067605,"y2":-0.092453267},
{"entity_type":"line","x1":0.137067605,"y1":-0.092453267,"x2":0.145910613,"y2":-0.098417951},
{"entity_type":"arc_center","cx":0,"cy":0,"x1":0.145910613,"y1":-0.098417951,"x2":0.148367220,"y2":-0.094674009},
{"entity_type":"arc_center","cx":0.150350819,"cy":-0.054723223,"x1":0.148367220,"y1":-0.094674009,"x2":0.183514364,"y2":-0.032358534},
{"entity_type":"arc_center","cx":0.160000000,"cy":0,"x1":0.183514364,"y1":-0.032358534,"x2":0.183514364,"y2":0.032358534},
{"entity_type":"arc_center","cx":0.150350819,"cy":0.054723223,"x1":0.183514364,"y1":0.032358534,"x2":0.148367220,"y2":0.094674009},
{"entity_type":"arc_center","cx":0,"cy":0,"x1":0.148367220,"y1":0.094674009,"x2":0.145910613,"y2":0.098417951},
{"entity_type":"line","x1":0.145910613,"y1":0.098417951,"x2":0.137067605,"y2":0.092453267},
{"entity_type":"arc_center","cx":0.150350819,"cy":0.054723223,"x1":0.137067605,"y1":0.092453267,"x2":0.120344112,"y2":0.081173128},
{"entity_type":"line","x1":0.120344112,"y1":0.081173128,"x2":0.081245682,"y2":0.054800905},
{"entity_type":"arc_center","cx":0,"cy":0,"x1":0.081245682,"y1":0.054800905,"x2":0.081245682,"y2":-0.054800905}
]
```

### Card C2 - pad slot and three windows as one contour

Union of the slot (r 90 to 178, -42 to +42 deg) and the windows (r 90 to 215 at
-42 to -27, -7 to +7, +27 to +42 deg), cut in the same band z = -39 to +38.6.
What is left in that band is the two bridges at r > 178 between the windows.
Sketch on the plane at offset -0.0002. Expected: segment_count 12,
arc_center 6, line 6.

```json
[
{"entity_type":"line","x1":0.066883034,"y1":-0.060221755,"x2":0.159776137,"y2":-0.143863080},
{"entity_type":"arc_center","cx":0,"cy":0,"x1":0.159776137,"y1":-0.143863080,"x2":0.191566403,"y2":-0.097607957},
{"entity_type":"line","x1":0.191566403,"y1":-0.097607957,"x2":0.158599161,"y2":-0.080810309},
{"entity_type":"arc_center","cx":0,"cy":0,"x1":0.158599161,"y1":-0.080810309,"x2":0.176673215,"y2":-0.021692743},
{"entity_type":"line","x1":0.176673215,"y1":-0.021692743,"x2":0.213397423,"y2":-0.026201909},
{"entity_type":"arc_center","cx":0,"cy":0,"x1":0.213397423,"y1":-0.026201909,"x2":0.213397423,"y2":0.026201909},
{"entity_type":"line","x1":0.213397423,"y1":0.026201909,"x2":0.176673215,"y2":0.021692743},
{"entity_type":"arc_center","cx":0,"cy":0,"x1":0.176673215,"y1":0.021692743,"x2":0.158599161,"y2":0.080810309},
{"entity_type":"line","x1":0.158599161,"y1":0.080810309,"x2":0.191566403,"y2":0.097607957},
{"entity_type":"arc_center","cx":0,"cy":0,"x1":0.191566403,"y1":0.097607957,"x2":0.159776137,"y2":0.143863080},
{"entity_type":"line","x1":0.159776137,"y1":0.143863080,"x2":0.066883034,"y2":0.060221755},
{"entity_type":"arc_center","cx":0,"cy":0,"x1":0.066883034,"y1":0.060221755,"x2":0.066883034,"y2":-0.060221755}
]
```

### Card C3 - outer-bridge step annulus r 172 to 215 (use twice)

Sketch on the plane at +0.0495, then again on a new plane at -0.0495.
Expected: segment_count 2, circle 2.

```json
[{"entity_type":"circle","cx":0,"cy":0,"radius":0.215000000},{"entity_type":"circle","cx":0,"cy":0,"radius":0.172000000}]
```

### Card C4 - three piston bores Ø26 at r = 140 (-20, 0, +20 deg) (use twice)

Sketch on the plane at +0.0426 (z = +38.6 to +46.6), then again on a new plane
at -0.043 (z = -47 to -39). Expected: segment_count 3, circle 3.

```json
[
{"entity_type":"circle","cx":0.131556967,"cy":-0.047882820,"radius":0.013000000},
{"entity_type":"circle","cx":0.140000000,"cy":0,"radius":0.013000000},
{"entity_type":"circle","cx":0.131556967,"cy":0.047882820,"radius":0.013000000}
]
```

### Calliper checksum table

Every feature is a mid-plane extrude about its plane, so no direction flag
matters. Running values from polar integration of PRD 3.4 (they agree with the
PRD section-area table within 0.01 %). y centroid is 0 throughout.

| # | Plane offset (m) | Card | Extrude | Volume after m^3 | Centroid x, z mm |
|---|---|---|---|---|---|
| 1 | `Front Plane` | C1 | boss, `depth=0.114` | 1.897369e-3 | 143.215, 0.000 |
| 2 | -0.0002 | C2 | cut, `depth=0.0776` | 7.851263e-4 | 151.053, +0.283 |
| 3 | +0.0495 | C3 | cut, `depth=0.015` | 7.138413e-4 | 148.632, -4.632 |
| 4 | -0.0495 | C3 | cut, `depth=0.015` | 6.425562e-4 | 145.675, +0.346 |
| 5 | +0.0426 | C4 | cut, `depth=0.008` | 6.298139e-4 | 145.903, -0.509 |
| 6 | -0.043 | C4 | cut, `depth=0.008` | **6.170815e-4** (PRD) | **146.143, +0.369** (PRD) |

The binding values are the PRD section 4 signature in row 6: volume
6.170815e-4 m^3, centroid (146.143, 0.000, +0.369) mm, bbox x = 81.245 to
200.000, y = -98.418 to 98.418, z = -57 to +57 mm, 1 body. The step-3 centroid
z of -4.632 mm is a direction check: a positive value there means the
outboard step was cut on the inboard side.

---

## How the cards were checked

Generated in the sandbox from PRD 3.4 and 3.5 only, and checked on the rounded
values:

- Shared endpoints are identical text, so every contour closes (largest
  endpoint mismatch 8e-10 m, from rounding the arc radius).
- Card C1 polygonised area 16 643.58 mm^2 equals the polar integral of the
  union of the sector and the three lobes; x 200.000 mm is the mid-point of
  the lobe 0 arc. Arc sweeps are 29.2, 1.5, 126.8, 108.0, 126.8, 1.5, 29.2 and
  68.0 deg: all minor.
- Card C2 arc sweeps are 15, 20, 14, 20, 15 and 84 deg: all minor.
- Pads: area 5 864.31 mm^2, centroid x 134.600 mm; plates: area
  7 330.38 mm^2, centroid x 135.111 mm (PRD section 4).
- The PRD corners are reproduced: base x min 81.245 mm at (r 98, +/-34 deg),
  y max 98.418 mm at (r 176, +/-34 deg).
