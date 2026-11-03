# SpaceClaim CAD Failure Modes and Recovery

**Source:** hands-on iteration during the flow-around-cylinder build.

**Scope:** what goes wrong with pyansys-geometry and how to recover.

---

## 1. Backend selection warnings during launch

**Symptom.**
```
WARNING - launcher - The local Docker container could not be started.
WARNING - launcher - The Geometry Core service could not be started locally.
WARNING - launcher - The Geometry DMS service could not be started locally.
WARNING - launcher - Trying to start Ansys SpaceClaim locally.
```
followed by 30-60s silence, then successful connection.

**Root cause.** `launch_modeler()` tries backends in order: Docker -> Geometry Core -> Geometry DMS -> SpaceClaim. On Ansys Student, only SpaceClaim is available.

**Fix.** Nothing needed — the warnings are informational. The connection eventually succeeds via SpaceClaim (Backend: `BackendType.SPACECLAIM`).

**If you want to skip the noise:**

```python
from ansys.geometry.core import launch_modeler_with_spaceclaim
modeler = launch_modeler_with_spaceclaim()
```

**Cost.** Each launch takes 30-60s because SpaceClaim boots its full engine. For many cases in a loop, reuse one modeler session across designs.

---

## 2. Curved face misclassified when using normal-based classification

**Symptom.** Face count assertions fail. A cylinder's side face is tagged as "outlet" or "wall" because its normal at (u=0.5, v=0.5) happens to point along an axis.

**Root cause.** `Face.normal()` samples at UV=(0.5, 0.5) by default. For a cylinder, that specific point can point in any axis direction. Normal-based classification is unreliable for curved surfaces.

**Fix.** Check `Face.surface_type` first, only fall back to normal for planar faces:

```python
from ansys.geometry.core.designer.face import SurfaceType

for face in body.faces:
    if face.surface_type == SurfaceType.SURFACETYPE_CYLINDER:
        cylinder_faces.append(face)
        continue  # skip normal-based classification
    # Planar faces only reach here
    n = face.normal()
    if abs(n.x) > 0.99 and n.x < 0:
        inlet_faces.append(face)
    # ... etc
```

**SurfaceType enum values:**
- `SURFACETYPE_PLANE`
- `SURFACETYPE_CYLINDER`
- `SURFACETYPE_CONE`
- `SURFACETYPE_TORUS`
- `SURFACETYPE_SPHERE`
- `SURFACETYPE_NURBS` (freeform)
- `SURFACETYPE_PROCEDURAL`
- `SURFACETYPE_UNKNOWN`

---

## 3. `export_to_pmdb()` writes to CWD, not your output dir

**Symptom.** You expected the PMDB in `results/` but it landed in the script's current working directory with the design name.

**Root cause.** `design.export_to_pmdb()` uses CWD as its output location.

**Fix.** Move the file after export:

```python
from pathlib import Path
import shutil

pmdb_temp = Path(design.export_to_pmdb())
target = Path(out_dir) / f"{case_name}.pmdb"
if pmdb_temp.resolve() != target.resolve():
    shutil.move(str(pmdb_temp), str(target))
```

---

## 4. Modeler doesn't close, license slot leaks

**Symptom.** After a script crashes or exits without cleanup, SpaceClaim keeps running in the background. Next `launch_modeler()` hangs or fails with license error.

**Root cause.** `modeler.close()` was never called.

**Fix.** Always try/finally:

```python
modeler = launch_modeler()
try:
    # ... build geometry ...
finally:
    modeler.close()
```

**Emergency cleanup.** `taskkill /F /IM SpaceClaim.exe` on Windows.

---

## 5. Design objects go stale after modification

**Symptom.** You cached `bodies = design.bodies` early, then modified the design. Now `bodies` doesn't reflect changes.

**Root cause.** `design.bodies` returns a snapshot at call time. Design mutations after are not reflected.

**Fix.** Never cache. Access properties fresh:

```python
# BAD
bodies = design.bodies
design.extrude_sketch(...)
# bodies is stale

# GOOD
design.extrude_sketch(...)
for body in design.bodies:  # fresh each iteration
    ...
```

Same rule applies to `component.bodies`, `body.faces`, `face.edges`, etc.

---

## 6. Unit mismatches silently scale geometry

**Symptom.** Fluent reports mesh bounding box 1000x smaller or larger than expected.

**Root cause.** Mixing units within a sketch (m and mm), or forgetting to specify units on Point2D/Distance.

**Fix.** ALWAYS specify units:

```python
sketch.box(
    center=Point2D([0.3, 0], unit=UNITS.m),
    width=Distance(0.6, UNITS.m),
    height=Distance(0.2, UNITS.m),
)
```

When reading back volumes/areas, convert to SI:

```python
vol_m3 = body.volume.m_as(UNITS.m**3)
area_m2 = face.area.m_as(UNITS.m**2)
```

---

## 7. Cylinder splits into multiple face zones after meshing

**Symptom.** Watertight workflow produces more "cylinder" face zones than you tagged.

**Root cause.** SpaceClaim sometimes splits a cylindrical surface at a seam (u=0 line, or where the cylinder edge coincides with a plane). Topologically it's one face, but the meshing conversion may split it into 2+.

**Fix.** Group all curved-surface faces under one named selection:

```python
cyl_faces = [f for f in body.faces if f.surface_type == SurfaceType.SURFACETYPE_CYLINDER]
design.create_named_selection("cylinder", faces=cyl_faces)
```

Fluent's downstream BC assignment sees the group as one boundary.

---

## 8. Boolean subtract on overlapping bodies fails silently

**Symptom.** After a boolean subtract, both bodies remain instead of one being consumed.

**Root cause.** Bodies don't actually intersect (gap from numerical precision), or target/tool arguments swapped.

**Fix.** For "solid inside fluid" pattern, prefer the sketch-with-hole approach — put the hole in the 2D sketch before extruding. Cleaner topology than 3D boolean subtract:

```python
# GOOD: cylinder hole in the sketch before extruding
sketch = Sketch()
sketch.box(...)         # outer rectangle
sketch.circle(...)      # inner circle = hole
body = design.extrude_sketch("fluid", sketch, ...)   # single body, annular region

# WORKS BUT MORE FRAGILE: extrude two bodies, boolean subtract
outer = design.extrude_sketch("outer", rect_sketch, ...)
inner = design.extrude_sketch("inner", circle_sketch, ...)
outer.subtract(inner)   # relies on intersection working
```

---

## 9. Multiple designs on one modeler session

**Symptom.** Creating a second `design` on the same modeler errors out.

**Root cause.** By default the modeler enforces one active design at a time.

**Fix.** Close the previous design first:

```python
design1 = modeler.create_design("case_1")
# ... work ...
design1.close()

design2 = modeler.create_design("case_2")
```

Or bypass the check (advanced):

```python
import ansys.geometry.core as pyansys_geometry
pyansys_geometry.DISABLE_ACTIVE_DESIGN_CHECK = True
```

For a design loop, safe pattern is: one modeler session, iterate over designs by close/reopen, close modeler at end.

---

## 10. Sketch plane confusion when not on default XY

**Symptom.** Extrude direction or feature orientation is wrong.

**Root cause.** Sketch defaults to XY plane at origin. When you construct on a non-default plane, all sketch coords are IN THAT PLANE's local 2D frame — not global 3D.

**Fix.** Be explicit about planes:

```python
from ansys.geometry.core.math import Plane, Point3D, UnitVector3D

# Sketch on YZ plane offset in X by 0.5
plane = Plane(
    origin=Point3D([0.5, 0, 0]),
    direction_x=UnitVector3D([0, 1, 0]),  # local X = global Y
    direction_y=UnitVector3D([0, 0, 1]),  # local Y = global Z
)
sketch = Sketch(plane)
```

Sketch primitives use the plane's local 2D coords. Extrusion direction is normal to the plane.

---

## Debugging checklist

When geometry doesn't look right:

1. `design.plot()` — visual check
2. `body.volume.m_as(UNITS.m**3)` — vs. expected volume
3. `body.bounding_box` — dimensions match design intent
4. Face count by surface type: `from collections import Counter; Counter(f.surface_type for f in body.faces)`
5. If exporting: open the PMDB in SpaceClaim GUI to manually inspect before running Fluent
