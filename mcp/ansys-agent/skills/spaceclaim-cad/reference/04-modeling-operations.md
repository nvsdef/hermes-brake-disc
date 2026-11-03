# PyAnsys Geometry Modeling Operations

**Source:** PyAnsys Geometry Design/Body/Component API + hands-on.

**Scope:** creating 3D bodies from 2D sketches (extrude, revolve, sweep), modifying bodies with boolean/transform ops, and edge/face-level feature operations (fillet, chamfer, shell).

---

## Body creation from sketches

### `extrude_sketch` — extrude 2D → 3D linearly

The workhorse operation.

```python
body = design.extrude_sketch(
    name="fluid_domain",
    sketch=my_sketch,
    distance=Distance(0.02, UNITS.m),
    direction=None,          # optional; defaults to sketch plane normal
)
```

If your sketch is a simple rectangle, the body is a box. If the sketch has an outer boundary with an inner circle, the body is a rectangle with a cylindrical hole.

### `extrude_face` — extrude an existing face further

Modify an existing body by extruding one of its faces:

```python
extended_body = design.extrude_face(
    name="extension",
    face=some_face,
    distance=Distance(0.05, UNITS.m),
)
```

Useful for iterative construction (extend a duct, add a boss to a plate).

### `revolve_sketch` — rotate around an axis

For axisymmetric bodies (spheres, torus, pipes):

```python
body = design.revolve_sketch(
    name="revolved",
    sketch=profile_sketch,
    axis=UnitVector3D([0, 0, 1]),   # Z-axis
    angle=Quantity(360, UNITS.degree),
)
```

Half-revolve (180°) for symmetry-reduced problems.

### `sweep_sketch` — sweep a profile along a curve

For pipes with bends, complex ducts:

```python
body = design.sweep_sketch(
    name="pipe_with_bend",
    profile=cross_section_sketch,
    path=path_curve,
)
```

More complex to set up — needs a path curve as well as the profile.

### `sweep_chain` — sweep along multiple linked segments

For sequential bends:

```python
body = design.sweep_chain(
    name="multi_bend_pipe",
    profile=cross_section_sketch,
    path_chain=[segment1, segment2, arc1, segment3],
)
```

## Body-level modification

Once a body exists, you can transform or combine it:

### `translate` — move

```python
body.translate(
    direction=UnitVector3D([1, 0, 0]),
    distance=Quantity(0.1, UNITS.m),
)
```

### `rotate` — spin around an axis

```python
body.rotate(
    axis_origin=Point3D([0, 0, 0]),
    axis_direction=UnitVector3D([0, 0, 1]),
    angle=Quantity(45, UNITS.degree),
)
```

### `scale` — uniform scaling

```python
body.scale(factor=2.0)   # doubles all dimensions
```

## Boolean operations

Combine or subtract bodies:

### `subtract` — cut

```python
body1.subtract(body2)   # body2 is consumed; body1 = body1 - body2
```

### `unite` — combine

```python
body1.unite([body2, body3])   # combines all into body1
```

### `intersect` — keep overlap only

```python
body1.intersect([body2])   # body1 = body1 AND body2
```

**Note:** Booleans on non-overlapping bodies fail silently. For "fluid domain with obstacle," prefer sketch-with-hole approach (see `08-failure-modes.md` #8).

## Feature operations

### `fillet` — round an edge

```python
body.fillet(
    edges=[edge1, edge2],
    radius=Distance(0.005, UNITS.m),
)
```

Round sharp edges to improve mesh quality near corners.

### `chamfer` — flat bevel on an edge

```python
body.chamfer(
    edges=[edge1],
    distance=Distance(0.003, UNITS.m),
)
```

### `shell` — hollow a solid body

```python
body.shell(
    faces_to_remove=[opening_face],
    thickness=Distance(0.002, UNITS.m),
)
```

Turns a solid into a shell (like a cup — hollow with an opening). Useful for thin-walled structures.

## Feature detection helpers

Find edges to fillet or chamfer:

```python
# All edges of the body
all_edges = body.edges

# Edges of a specific face
face_edges = my_face.edges

# Filter by curve type
from ansys.geometry.core.designer.edge import CurveType
circular_edges = [e for e in body.edges if e.curve_type == CurveType.CIRCLE]
```

## Copy and duplicate

Duplicate a body (for parametric variations):

```python
duplicate = body.copy(component=design)   # copy into design root
# Or move to a component
duplicate = body.copy(component=my_component)
```

## Delete a body

```python
body.delete()
```

Removes from the design. Useful when generating many bodies and filtering.

## Common modeling patterns for CFD

### Pattern 1: fluid domain with hole (single body)

Cleanest for cylinder-in-channel or airfoil-in-freestream:

```python
sketch = Sketch()
sketch.box(...)      # outer domain
sketch.circle(...)   # hole for obstacle
body = design.extrude_sketch("fluid", sketch, distance)
```

### Pattern 2: fluid + solid (two bodies for CHT)

```python
# Fluid
fluid_sketch = Sketch()
fluid_sketch.box(...)
fluid_sketch.circle(...)   # cylinder hole
fluid = design.extrude_sketch("fluid", fluid_sketch, distance)

# Solid (fills the hole)
solid_sketch = Sketch()
solid_sketch.circle(...)   # same position/size
solid = design.extrude_sketch("cylinder_solid", solid_sketch, distance)
```

### Pattern 3: extruded profile with rounded corners

```python
sketch = Sketch()
# ... build a rectangle sketch ...
body = design.extrude_sketch("profile", sketch, distance)

# Fillet corner edges after extrude
corner_edges = [e for e in body.edges if is_corner(e)]
body.fillet(edges=corner_edges, radius=Distance(0.005, UNITS.m))
```

### Pattern 4: revolved axisymmetric geometry

```python
# 2D profile in XY plane
profile = Sketch()
profile.segment_to_point(...)
# ... more segments defining half of the axisymmetric shape ...

# Revolve around Y-axis
body = design.revolve_sketch(
    "axisymmetric",
    profile,
    axis=UnitVector3D([0, 1, 0]),
    angle=Quantity(360, UNITS.degree),
)
```

## For paper reproduction

Papers specify geometry as either:
- **Simple parametric** (rectangle, cylinder, sphere) — extrude_sketch or revolve_sketch
- **Complex profile** (NACA airfoil, pipe with bend) — sketch with segments/arcs, then extrude/sweep
- **Multi-body** (fluid + solid) — two extrudes, two bodies

Match the paper's construction sequence, especially:
- Corner treatment (sharp vs. filleted)
- Extrusion depth for 2.5D vs. full 3D
- Coordinate origin (paper's origin might differ from your convention)

Reproduction accuracy depends on matching dimensions AND small details like fillets.
