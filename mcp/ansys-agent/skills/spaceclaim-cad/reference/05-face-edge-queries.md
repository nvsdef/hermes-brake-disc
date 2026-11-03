# Face, Edge, and Vertex Queries

**Source:** PyAnsys Geometry Face API docs + hands-on.

**Scope:** inspecting geometry topology after building — for classifying faces (inlet vs. wall vs. cylinder), extracting normals, areas, and locations.

---

## Face queries

Access faces of a body:
```python
for face in body.faces:
    print(face.id, face.surface_type, face.area.m_as(UNITS.m**2))
```

**IMPORTANT:** `body.faces` returns a snapshot. Don't cache. See `08-failure-modes.md` #5.

## `Face.surface_type` — the reliable topology check

Returns a `SurfaceType` enum. Use this FIRST for classification, especially with curved surfaces:

```python
from ansys.geometry.core.designer.face import SurfaceType

for face in body.faces:
    if face.surface_type == SurfaceType.SURFACETYPE_CYLINDER:
        cylinder_faces.append(face)
        continue
    # planar faces only reach here
    n = face.normal()
    # classify by normal direction
```

**SurfaceType enum values:**
- `SURFACETYPE_UNKNOWN`
- `SURFACETYPE_PLANE` — flat, normal is well-defined everywhere
- `SURFACETYPE_CYLINDER` — cylindrical (side of extruded circle)
- `SURFACETYPE_CONE` — conical
- `SURFACETYPE_TORUS` — toroidal
- `SURFACETYPE_SPHERE` — spherical
- `SURFACETYPE_NURBS` — freeform (splined)
- `SURFACETYPE_PROCEDURAL` — procedurally-defined

## `Face.normal(u=0.5, v=0.5)` — unit normal vector

Returns a `UnitVector3D` (3-component unit vector). By default, at UV midpoint. For planar faces, the normal is constant so the default is fine.

**For curved faces, the normal at (0.5, 0.5) can point in any direction.** Don't use it for classification of curved surfaces — check `surface_type` first.

```python
n = face.normal()
print(n.x, n.y, n.z)   # e.g., (1.0, 0.0, 0.0) for a +X-facing planar face
```

Get normal at a specific UV:
```python
n = face.normal(u=0.25, v=0.5)
```

## `Face.area` — surface area

Returns a Pint Quantity (has value + units).

```python
area_m2 = face.area.m_as(UNITS.m**2)
```

Useful for:
- Identifying "big" vs "small" faces (inlets, walls, cylinders often have distinct areas)
- Computing flow-through areas for BC pre-checks

## `Face.bounding_box` — axis-aligned bounding box

Available Ansys 25R2+. Returns a `BoundingBox` object.

```python
bb = face.bounding_box
print(bb.min, bb.max)   # Point3D objects
print(bb.min.x, bb.max.x)
```

Useful for locating faces spatially: e.g., "the face closest to X=0" for identifying the inlet.

## `Face.centroid` — geometric center

Available Ansys 27R1+. Returns Point3D.

```python
c = face.centroid
print(c.x, c.y, c.z)
```

Use for classification when `surface_type` and `normal()` are ambiguous:
```python
# Distinguish "left inlet" and "right inlet" of identical size
if face.centroid.x < 0.1:
    left_inlet.append(face)
else:
    right_inlet.append(face)
```

## `Face.point(u, v)` — evaluate 3D point on surface

Returns the 3D point at UV coordinates:
```python
p = face.point(u=0.5, v=0.5)   # midpoint of face
```

Advanced use — usually you want `centroid` or `bounding_box` instead.

## `Face.edges` — bounding edges

```python
for edge in face.edges:
    print(edge.length.m_as(UNITS.m), edge.curve_type)
```

Edges have their own properties: curve type, length, endpoints.

## `Face.vertices` — corner points

```python
for v in face.vertices:
    print(v.position)   # Point3D
```

For planar rectangular faces, 4 vertices at corners.

## `Face.plot()` — visual debug

```python
face.plot()
```

Opens a viewer showing just that face. Useful for sanity-checking a specific face during classification.

## Standard classification pattern (planar + curved)

```python
from ansys.geometry.core.designer.face import SurfaceType

inlet_faces, outlet_faces = [], []
top_bottom_walls, symmetry_faces = [], []
cylinder_walls = []

for face in body.faces:
    # Step 1: curved surface check
    if face.surface_type == SurfaceType.SURFACETYPE_CYLINDER:
        cylinder_walls.append(face)
        continue

    # Step 2: planar face — classify by normal direction
    n = face.normal()
    if abs(n.x) > 0.99 and n.x < 0:
        inlet_faces.append(face)
    elif abs(n.x) > 0.99 and n.x > 0:
        outlet_faces.append(face)
    elif abs(n.y) > 0.99:
        top_bottom_walls.append(face)
    elif abs(n.z) > 0.99:
        symmetry_faces.append(face)
```

## When classification by normal isn't enough

Two faces can have the same normal direction if they're on opposite sides (top and bottom, or left and right). Distinguish them by centroid location:

```python
for face in body.faces:
    if face.surface_type != SurfaceType.SURFACETYPE_PLANE:
        continue
    n = face.normal()
    if abs(n.y) < 0.99:
        continue   # not a horizontal face

    c = face.centroid   # or use face.bounding_box for older versions
    if c.y > 0:
        top_wall.append(face)
    else:
        bottom_wall.append(face)
```

## Edge queries

```python
for edge in body.edges:
    print(edge.length.m_as(UNITS.m), edge.curve_type)
```

`edge.curve_type` values: `LINE`, `CIRCLE`, `ARC`, `ELLIPSE`, `SPLINE`, ...

Useful for identifying feature edges (e.g., finding the perimeter of an inlet face for sizing controls in Fluent).

## Vertex queries

```python
for v in body.vertices:
    print(v.position)   # Point3D
```

Usually less useful than face-level queries for CFD boundary tagging.

## Face selection helpers

Find the face with maximum/minimum area:
```python
biggest = max(body.faces, key=lambda f: f.area.m_as(UNITS.m**2))
```

Find faces at a specific location:
```python
inlet = next(
    f for f in body.faces
    if f.surface_type == SurfaceType.SURFACETYPE_PLANE
    and abs(f.centroid.x) < 1e-6   # at X=0
)
```

## For paper reproduction

Papers usually specify boundaries by geometric position ("left face", "cylinder surface"). Map to your face-classification logic:
- "Left face" -> normal in -X direction
- "Top wall" -> normal in +Y direction
- "Cylinder surface" -> `surface_type == SURFACETYPE_CYLINDER`
- "Ground plane" -> distinguished by centroid Y position

Build the classification logic to match the paper's naming convention.
