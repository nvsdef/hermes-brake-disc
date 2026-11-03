# PyAnsys Geometry Sketch API

**Source:** PyAnsys Geometry sketch subpackage docs + hands-on.

**Scope:** creating 2D sketches with primitives, chaining, and preparing sketches for 3D extrusion/revolution/sweeping.

---

## Sketch fundamentals

A sketch is a 2D drawing that lives on a plane. It contains:

- **Edges** — open curves (segments, arcs)
- **Faces** — closed regions bounded by edges (circles, boxes, triangles, polygons)

Sketches are used as input to 3D operations like `extrude_sketch`, `revolve_sketch`, `sweep_sketch`.

## Creating a sketch

Default plane (XY plane at origin):
```python
from ansys.geometry.core.sketch import Sketch
sketch = Sketch()
```

On a specific plane:
```python
from ansys.geometry.core.math import Plane, Point3D, UnitVector3D

plane = Plane(
    origin=Point3D([0, 0, 0.5]),
    direction_x=UnitVector3D([1, 0, 0]),
    direction_y=UnitVector3D([0, 1, 0]),
)
sketch = Sketch(plane)
```

**Note:** sketch coordinates are in the plane's LOCAL 2D frame, not global 3D. Extrusion direction is normal to the sketch plane.

## Primitives (direct API)

### Circle
```python
from ansys.geometry.core.math import Point2D
from ansys.geometry.core.misc import UNITS, Distance

sketch.circle(Point2D([0.1, 0.05], unit=UNITS.m), Distance(0.02, UNITS.m))
```

### Box (rectangle)
```python
sketch.box(
    center=Point2D([0.3, 0], unit=UNITS.m),
    width=Distance(0.6, UNITS.m),
    height=Distance(0.2, UNITS.m),
)
```

### Ellipse
```python
sketch.ellipse(
    Point2D([0, 0], unit=UNITS.m),
    semi_major_axis=Distance(0.1, UNITS.m),
    semi_minor_axis=Distance(0.05, UNITS.m),
)
```

### Triangle
```python
sketch.triangle(
    Point2D([-1, 0], unit=UNITS.m),
    Point2D([1, 0], unit=UNITS.m),
    Point2D([0, 1], unit=UNITS.m),
)
```

### Polygon (regular N-sided)
```python
sketch.polygon(
    center=Point2D([0, 0], unit=UNITS.m),
    inner_radius=Distance(0.1, UNITS.m),
    sides=6,  # hexagon
)
```

### Segment (straight edge)
```python
sketch.segment(
    Point2D([0, 0], unit=UNITS.m),
    Point2D([1, 0], unit=UNITS.m),
)
```

### Arc
```python
sketch.arc(
    Point2D([0, 0], unit=UNITS.m),      # start
    Point2D([1, 1], unit=UNITS.m),      # end
    Point2D([0.5, 0], unit=UNITS.m),    # center
)
```

## Functional-style chaining

Sketches return themselves, allowing method chaining. Each `segment_to_point` continues from the last endpoint.

```python
sketch = Sketch()
(sketch
    .segment(Point2D([0, 0], UNITS.m), Point2D([1, 0], UNITS.m))
    .segment_to_point(Point2D([1, 1], UNITS.m))
    .segment_to_point(Point2D([0, 1], UNITS.m))
    .segment_to_point(Point2D([0, 0], UNITS.m))   # closes the loop
)
```

This creates a closed square boundary.

## Labeling elements for later reference

Tag a shape with `tag=`:
```python
sketch.circle(Point2D([0, 0], UNITS.m), Distance(1, UNITS.m), tag="my_circle")
sketch.get("my_circle")   # retrieve by tag
```

## Composite sketches (multiple shapes = boolean-like regions)

A sketch with multiple closed shapes:
- **Outer rectangle + inner circle** -> extrude gives an annular body (fluid domain with hole)
- **Two disjoint rectangles** -> extrude gives two separate bodies in one design

Example: rectangle with circular hole for CFD fluid domain:
```python
sketch = Sketch()
sketch.box(center=Point2D([0.3, 0], UNITS.m), width=Distance(0.6, UNITS.m), height=Distance(0.2, UNITS.m))
sketch.circle(Point2D([0.15, 0], UNITS.m), Distance(0.02, UNITS.m))

# Extrude: single body, annular region
body = design.extrude_sketch("fluid", sketch, Distance(0.02, UNITS.m))
```

## Plotting the sketch (visual debugging)

```python
sketch.plot()   # opens a viewer
```

Useful before extruding to confirm geometry looks right.

## Units — always be explicit

Every Point2D and Distance should specify units:
```python
Point2D([0.1, 0.05], unit=UNITS.m)     # NOT Point2D([0.1, 0.05])
Distance(0.02, UNITS.m)                # NOT Distance(0.02)
```

Mixing UNITS.m and UNITS.mm in one sketch is possible but error-prone. Stick to one system per sketch.

## Common available units

```python
from ansys.geometry.core.misc import UNITS
UNITS.m     # meters
UNITS.cm    # centimeters
UNITS.mm    # millimeters
UNITS.inch  # inches
UNITS.ft    # feet
```

## For paper reproduction

Papers usually give dimensions in mm or inches with a specific coordinate origin. Map their origin to a Point2D and use their units directly:

```python
# Paper says: rectangle 200mm x 100mm, hole at (50mm, 0), radius 10mm
sketch.box(
    center=Point2D([100, 0], UNITS.mm),
    width=Distance(200, UNITS.mm),
    height=Distance(100, UNITS.mm),
)
sketch.circle(Point2D([50, 0], UNITS.mm), Distance(10, UNITS.mm))
```

PyAnsys Geometry handles unit conversion internally; downstream Fluent import can be told the length_unit ("mm" in this case).

## What sketches CAN'T do

- 3D operations (that's the Design/Body layer)
- Boolean subtract on 2D shapes (workaround: use enclosed loops as above)
- Filleting sketch corners (use arc segments as workaround)
- Constrained/parametric geometry (all dimensions are absolute)

For advanced parametric geometry, use pyansys-geometry's `design_parameters` API.
