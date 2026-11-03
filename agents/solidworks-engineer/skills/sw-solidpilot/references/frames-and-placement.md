# Frames, placement and transforms

Everything on this sheet is avoidable by sketching every part at its true global
position and inserting it with an identity transform. Read it before the first
sketch of a session, and again if a body lands somewhere you did not expect.

## The model frame

PRD conventions: **Z is the shaft axis**, origin at the vent mid-plane, **+Z
points outboard** (towards the wheel and the mounting face at z = +43 mm), pads
centred on **+X**, angles measured from +X towards +Y (counter-clockwise viewed
from +Z).

## Default plane frames

`create_sketch(plane=...)` returns the sketch frame. The mapping from sketch
coordinates (x, y) to the model is always

```
p_model = origin + x * xdir + y * ydir
```

Measured by the predecessor:

| Plane | `origin` | `xdir` | `ydir` | Normal |
|---|---|---|---|---|
| `Front Plane` | `[0, 0, 0]` | `[1, 0, 0]` | `[0, 1, 0]` | +Z |
| offset of `Front Plane` by d | `[0, 0, d]` | `[1, 0, 0]` | `[0, 1, 0]` | +Z |
| `Right Plane` | `[0, 0, 0]` | `[0, 0, -1]` | `[0, 1, 0]` | +X |

So on `Right Plane`, sketch x maps to **-Z** and sketch y maps to **+Y**. The hat
polygon is given as (z, r). With r drawn along +Y, the sketch point is

```
x = -z / 1000     y = r / 1000        (z and r in mm)
```

Example: PRD point (z = 43, r = 35) becomes sketch (-0.043, 0.035). Get this
backwards (x = +z) and the hat revolves upside down: the mounting face lands at
z = -43 and the centroid at z = -18.4 mm instead of +18.4. The volume is still
correct, which is exactly why the centroid gate exists.

If the returned frame differs from the table, **the frame wins**. Solve for x
and y from the returned `xdir` and `ydir`; do not force the table.

## Offset planes

```json
{"type": "plane", "ref_plane_name": "Front Plane", "offset": -0.022}
```

- Returns the plane name (`Plane1`, `Plane2`, ...). Use the returned name.
- The predecessor measured that a negative `offset` is honoured by this tool
  (frame origin `[0, 0, -0.016]`). `modify_dimension` on the same plane later
  dropped the sign, so do not edit plane offsets after creation. If a plane is
  wrong, delete it and create a new one.
- Check the sketch frame's `origin[2]` equals the offset you asked for, to
  1e-9 m, before you add entities.

## Extrude directions

- A **boss** on a plane parallel to `Front Plane` extrudes along the plane
  normal (+Z) by default. `reverse=true` flips it.
- A **cut** direction on a plane in the middle of material is not something to
  remember. Avoid the question with `mid_plane=true` about the band centre
  (table in `SKILL.md` section 4).
- `mid_plane=true`: `depth` is the total width, symmetric about the plane.
- `through=true`: through-all in one direction; `depth` is ignored.
- Every direction question is settled by the volume change and the z extents
  after the feature, never by the flag you passed.

## Sketching on a model face (avoid it)

`create_sketch(on_face=true, face_index=...)` echoes a frame. On a face whose
normal is -Z it came back as

```
"frame": {"origin": [0, 0, -0.057], "xdir": [-1, 0, 0], "ydir": [0, 1, 0]}
```

`xdir` is negated, so every x in the profile must be negated or the feature
lands mirrored on the far side of the part. `reverse=true` is usually needed for
a cut sketched on a face. This brake never needs a face sketch: every feature
can sit on `Front Plane`, `Right Plane` or an offset plane.

## Assembly placement

Insert every part with an identity transform, fixed:

```json
{"file_path": "C:\\brake-runs\\<run-id>\\10_cad\\cheek_out.SLDPRT",
 "transform_json": "[1,0,0,0,1,0,0,0,1,0,0,0,1]",
 "fixed": true}
```

The 13 numbers are a 3 x 3 rotation (row-major), a translation in metres, and a
scale. That is the same layout `analyze_assembly('components')` reports, so the
readback for every component must be exactly
`[1,0,0, 0,1,0, 0,0,1, 0,0,0, 1]`.

Measured quirks you avoid by using identity:

1. **`x=0, y=0, z=0` centres the bounding box.** A rotor spanning z = -16 to +43
   mm came back with translation -0.0135 m, its bbox centre.
2. **The rotation is applied transposed.** Supplying M places the part by M^T.
   Supplying `[[0,1,0],[0,0,1],[1,0,0]]` (meaning X to Z, Y to X, Z to Y)
   produced X to Y, Y to Z, Z to X.
3. **The scale element is ignored.** Passing 2.0 left volume unchanged.

With those, placement is `p' = M^T p + t`. Predictions that way matched
measurement within 3 mm, which is not good enough for PRD tolerances (0.05 mm
bbox). That is why every part is built at global coordinates and M is identity.

The three sessions of transform arithmetic before the predecessor switched to
global coordinates produced one calliper buried inside the rotor ring
(r = 123 to 164), where it rendered as nothing and looked right on its own.

## Verifying placement after assembly

The transform readback proves the assembly did not move anything. It does not
prove each part was built in the right place. Two checks together do:

1. Each part's own centroid and z extents, measured when it was built.
2. SpaceClaim's Gate 2 import (independent of SolidWorks): 28 bodies, each centroid in
   the global frame, compared with PRD section 4.

## STL translation (for the record)

Measured on an earlier calliper with true bounds x = 89.5 to 197.9, y = -98 to
98, z = -68 to 68 mm: the exported STL read x = 89.5 to 197.9, y = 0.1 to 195.9,
z = 0 to 136. **y and z were shifted to zero; x was not.** Do not assume "bbox
minimum goes to the origin" on all axes, and do not use STL for placement.

## Mirror features inside one part

`create_pattern(pattern_type='mirror', features_json='["Cut-Extrude1"]',
plane='Front Plane')` is a valid way to mirror features inside one part. This
brake does not use it: the calliper is asymmetric in z (slot face at +38.6 but
-39); the inboard twins are flipped instances (`tool-traps.md`), never mirror features.
