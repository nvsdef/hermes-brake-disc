# The 45 coupled pairs, the zone map and the split selections

Open this at step 9 of the meshing procedure, or whenever a pair count, a zone
name or a selection area comes back wrong.

## Zone names: map them, never rename them

Fluent builds cell-zone names from the PMDB body names, and it may add a prefix
or a suffix. The predecessor saw `cheek_out`, `cheek_in`, `hat`, `vane_01` to
`vane_20` unchanged, but the pads and backing plates arrived as
`geom-1-outerpad`, `geom-1-innerpad`, `geom-1-bp_outer`, `geom-1-bp_inner`.
Another build may differ.

Build `zone_map` in two passes:

1. **By name**: a Fluent zone maps to a PRD name if the PRD name is a substring
   of it and no other PRD name is. Watch `vane_1` versus `vane_10`: match the
   full two-digit `vane_NN`.
2. **By volume**: confirm every mapping against the PRD section 4 volume within
   2 %. The 20 vanes share one volume, so for vanes also check the centroid angle
   (vane k at 17.917 + (k - 1) x 18 deg, r = 130.154 mm) if a mapping is in
   doubt.

A Fluent zone that maps to nothing, or a PRD body with no zone, is an upstream
defect. A 28th zone with a volume near 6.17e-4 m^3 is the calliper, which
SpaceClaim should have deleted. Report it; **do not delete it here**.

API idiom - inventory:
```python
s = solver.settings
solids = sorted(s.setup.cell_zone_conditions.solid.get_object_names())
try:
    fluids = sorted(s.setup.cell_zone_conditions.fluid.get_object_names())
except Exception:
    fluids = []
walls = sorted(s.setup.boundary_conditions.wall.get_object_names())
```

## Counting pairs by presence

A coupled interface appears as two wall zones: a primary `X` and its twin
`X-shadow`. Count pairs as: every `X-shadow` whose `X` also exists. Then check
**both** sides read `Coupled`:

API idiom:
```python
pairs = {}
for w in walls:
    if w.endswith("-shadow") and w[:-7] in walls:
        prim = w[:-7]
        tc_p = str(s.setup.boundary_conditions.wall[prim].thermal.thermal_condition())
        tc_s = str(s.setup.boundary_conditions.wall[w].thermal.thermal_condition())
        pairs[prim] = {"shadow": w, "primary_tc": tc_p, "shadow_tc": tc_s}
```

The predecessor's first version keyed the loop by primary name and read the
primary twice; the shadow's condition was stored and never tested. **Test both.**
A pair whose shadow is not `Coupled` is exactly the uncoupled interface this gate
exists to catch.

Some releases expose the thermal condition under `thermal_bc` instead of
`thermal_condition`. Try both and record which answered. Density reads 0.0 on a
solid with flow off, so it cannot identify anything.

## Classifying each pair

Name patterns are not stable across builds. The predecessor saw
`cheek_out-geom-1-outerpad` in one build and `<pad>-<rotor>` in another.
Classify each pair by **which two cell zones it joins**, using the names that
appear in the wall name, then confirm by area and location:

| Class | Joins | Count | Area each | Where |
|---|---|---|---|---|
| friction | a cheek and a pad | 2 | 5 864.31 mm^2 | z = +16 and z = -16, r = 120 to 160, theta = -30 to +30 deg |
| pad/backing | a pad and a backing plate | 2 | 5 864.31 mm^2 | z = +28 and z = -28 |
| cheek/vane | a cheek and a vane | 40 | 604.30 mm^2 | z = +6 (20) and z = -6 (20) |
| hat/cheek_in | the hat and cheek_in | 1 | 5 969.03 mm^2 | cylinder r = 95, z = -16 to -6 |

Any pair that fits no class is a FAIL, listed by name. Check the class counts
separately: a total of 45 made of 41 cheek/vane pairs and 0 hat pairs is wrong.

If the wall name does not contain both zone names, identify the adjacent cells.
The pairs must be classified by fact, not by guess. Two robust methods:

- Read the wall's adjacent cell zone from the zone's settings or from the
  transcript line printed when the mesh is read.
- Assign the three materials in this throwaway session (grey iron, pad compound,
  steel from `case.json`) and probe `specific-heat-cp` and
  `thermal-conductivity-lam` as area averages on each side: 447 / 52 is iron,
  900 / 1.2 is pad, 502 / 16.3 is steel. This also tells you which side of each
  friction pair is the pad, which the solve and postprocessing need. Do not write
  a case file from this session.

## Measuring 45 areas without creating 90 report definitions

Area = `surface-integral` of any field divided by `surface-areaavg` of the same
field. Temperature works even before initialization if you initialize to 300 K
first; a field of all 300 K gives integral = 300 x area.

Create **one** `surface-integral` and **one** `surface-areaavg` definition and
change their `surface_names` for each pair. Creating definitions is O(n^2) in a
Fluent session (about 9 s each at 50, about 25 s each at 200). The predecessor's
per-pair definitions turned a 2 m 45 s mesh into a 39 m 39 s measurement.

API idiom - one pooled surface report:
```python
rd = solver.settings.solution.report_definitions.surface
rd["rp-int"] = {}
rd["rp-int"].report_type = "surface-integral"
rd["rp-int"] = {"field": "temperature", "surface_names": [prim]}
val = solver.settings.solution.report_definitions.compute(report_defs=["rp-int"])
```

The return shape of `compute` varies by version. One observed shape is
`[{"rp-int": [value, unit]}]`. Validate the shape and the numeric type. A missing
value is `None`, never zero.

Also measure each pair's shadow area and check primary and shadow agree within
0.1 %. A large mismatch means a non-conformal or partial interface.

The `volume-zonevol` report type returned "access: unbound variable" for every
zone in the predecessor's build. Use `volume-sum` of the `cell-volume` field for
zone volumes.

## Named selections arrive split per body

`wall-vent` and `wall-outer` were created in SpaceClaim and ride in on the
PMDB. Fluent splits each one per body. The predecessor saw:

| Selection | Face zones | Bodies it spans |
|---|---|---|
| `wall-vent` | 22: `wall-vent`, `wall-vent.1` to `wall-vent.21` | 2 cheeks + 20 vanes |
| `wall-outer` | 3: `wall-outer`, `wall-outer.1`, `wall-outer.2` | 2 cheeks + hat |

The suffix format may differ in your build (`:1`, `.1`, `-1`). Expand by
prefix, record the list, and check:

- `wall-vent` summed area = 142 865.51 mm^2 within 2 % (PRD section 4, after
  shared topology).
- `wall-outer` summed area = 228 477.17 mm^2 within 2 % (PRD section 4, after
  shared topology). SpaceClaim reports it before imprint (240 205.78 mm^2 at
  Gate 2); the meshed value is lower by the two pad footprints,
  2 x 5 864.31 = 11 728.61 mm^2. The hat step face (z = -6, r = 88 to 95) is in
  `wall-outer` by decision.
- Exposed pad and backing-plate walls: every wall that is neither a named
  selection zone nor part of a coupled pair. Fluent names these after the cell
  zone (`geom-1-outerpad:1`), so a `wall-*` glob misses them. Build this list
  **by subtraction** and report its summed area against 31 268.67 mm^2 within
  2 % (PRD section 4, pad/backing exposed, after imprint).

Addressing the bare string `wall-vent` reaches one zone of 22 and leaves 21 with
no convection at all, silently. Globbing a name Fluent never created matches
nothing, silently. **The summed area is the only check that tells "found the
zones" from "found some zones".**

## Reserved substrings

Fluent assigns boundary types by substring. A zone name containing `inlet`,
`outlet` or `symmetry` can change type on read. None of the PRD names do. If you
see a wall typed as anything other than `wall` or an interface, report it.
