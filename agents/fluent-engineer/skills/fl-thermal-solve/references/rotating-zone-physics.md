# Solid motion: why only the cheeks rotate, and the pre-solve check

Open this before setting solid motion, and whenever the energy audit comes back
low.

## What solid motion does

Solid motion in Fluent does **not** move the mesh. It adds an advection term to
the energy equation inside the solid:

```
rho cp (dT/dt + v . grad T) = div(k grad T),     v = omega x r
```

This carries heat around the circumference, which is what a spinning disc does
under a stationary pad. It conserves energy **only if v . n = 0 on every
boundary of the rotating zone**. On a body of revolution about the rotation axis
this holds exactly: the velocity is tangent to every face. On anything else,
the imposed velocity flows through walls, and the enthalpy it carries out
disappears. **There is no error message, and the solve converges.**

That is why the rotor is built as separate bodies (PRD section 2) and why
`cheek_out` and `cheek_in` must be exact annuli with no holes (PRD section 3.1).
The vanes and the hat are not axisymmetric and never get solid motion.

## The measurement that predicts conservation

Before solving, compute over every boundary face of both rotating zones
(including their coupled interfaces):

```
I = sum over faces of abs( (e_z x r) . n ) x area         [m^3/s per rad/s]
```

where r is the face centroid position relative to the axis origin and n is the
unit face normal. Multiply by abs(omega) to get the spurious volume flux.

Gate: **I <= 1.592987e-4 m^3/s per rad/s** (PRD section 6). That threshold is the
value measured on the upstream PyFluent example, which conserved 94 to 96 %.
The predecessor's measured values illustrate the scale:

| Rotating zone | I, m^3/s per rad/s | Energy accounted |
|---|---|---|
| merged rotor, rejected | 5.65e-3 | 7.95 % |
| upstream example | 1.59e-4 | 94 to 96 % |
| split cheeks | 3.79e-6 | 99.86 % |

For two exact annuli the analytic value is zero; a faceted mesh gives a small
non-zero value from facet normals on the cylindrical faces (r = 95 and r = 165).

How to get the faces: request surface field data for the boundary zones of each
cheek (face centroids, face normals or vertices plus connectivity, and areas)
and integrate in Python. Cheek boundaries include the named-selection pieces that
belong to the cheek, the coupled walls on the cheek side, and any leftover wall.
Filter by the cheek band (r = 0.095 to 0.165 m, abs(z) = 0.006 to 0.016 m) if a
zone spans more than one body.

API idiom (class names vary by PyFluent release; check the installed module):
```python
from ansys.fluent.core import SurfaceFieldDataRequest, SurfaceDataType as SDT
req = SurfaceFieldDataRequest(surfaces=names,
        data_types=[SDT.FacesCentroid, SDT.FacesNormal])
data = solver.fields.field_data.get_field_data(req)
```
Fetch in chunks of about 20 surfaces, validate every array length, and build a
new cache for each measurement. A module-level cache once leaked between
sessions in the predecessor and integrated the wrong mesh.

Also check the zone-level sum against the areas you already have: the summed
face areas per zone must match the mesh report within 0.1 %.

## Fluent's warning points at the worst angle, not the worst flux

Fluent may print a warning like "significant normal component on N faces of face
zone Z ... maximum angle 89.4 deg at (x, y, z)". On the predecessor's merged
rotor that pointed at the hat bolt circle, which was 1.5 % of the problem; 98.3 %
of the spurious flux was on the vent faces. **Read the integral, not the
warning.** Report the warning text, but gate on I.

## The axis and the sign

- Axis direction (0, 0, 1), origin (0, 0, 0). The upstream example uses
  direction (0, 1, 0) and origin (-0.035, -0.821, 0.045); those belong to its
  mesh. Pasting them rotates this rotor about a line outside the part. It
  converges and the answer is wrong, silently.
- omega0 = -84.1751 rad/s: clockwise viewed from +Z. The sign comes from the
  vane geometry (PRD sections 3.2 and 10): the vanes sweep towards +theta as r
  increases, and a backward-curved vane then needs clockwise rotation. The
  predecessor's sign was flipped twice between runs; the correction went the
  wrong way once. Use the PRD sign.
- Thermally the sign only mirrors the field (no air domain; h is an input). It
  still matters: it decides the justification of the 130 W/(m^2 K) vent h and
  the handedness on the drawing.

## Setting it and reading it back

Set solid motion on the two cheeks, and **explicitly disable** it on the other
25 zones, then read back all 27. The readback record for each zone is: `enable`,
`solid_omega`, axis direction, axis origin, translational velocity (must be
zero), relative-to setting (absolute).

Store in `setup_report.json.solid_motion`:

- `zones_enabled`: must be exactly [`cheek_in`, `cheek_out`] (Fluent names).
- `omega_readback_rad_s` per enabled zone for the first window and at each
  verified window.
- `tangential_velocity_integral_m3_per_s_per_rad_s`, per cheek and total, with
  the threshold and PASS/FAIL.

If energy conservation later comes back far below 90 %, check this record and
the integral before touching any numerical setting.
