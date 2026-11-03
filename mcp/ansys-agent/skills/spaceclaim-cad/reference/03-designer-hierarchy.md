# PyAnsys Geometry Designer Hierarchy

**Source:** PyAnsys Geometry designer docs + hands-on.

**Scope:** the Design/Component/Body assembly model, when to use each, multi-body assemblies for conjugate heat transfer and multi-domain CFD.

---

## The hierarchy

```
Design (root)
├── Component
│   ├── Body
│   ├── Component (nested)
│   │   └── Body
│   ├── CoordinateSystem
│   ├── DatumPlane
│   └── DesignPoint
├── Body                (design can hold bodies directly at root)
├── Material
└── NamedSelection
```

**Design** is the root container. It extends Component, so anything you can do on Component you can do on Design.

**Component** is a sub-assembly. Groups related bodies. Can nest components arbitrarily.

**Body** is a 3D solid (or surface) primitive — the actual geometry.

## Typical workflow — flat structure (most CFD cases)

For most CFD cases, keep it flat — one design, one component, one body:

```python
from ansys.geometry.core import launch_modeler
from ansys.geometry.core.sketch import Sketch
from ansys.geometry.core.math import Point2D
from ansys.geometry.core.misc import UNITS, Distance

modeler = launch_modeler()

# Create a design
design = modeler.create_design("MyCase")

# Extrude a sketch to make a body (attached to design's root)
sketch = Sketch()
sketch.box(
    center=Point2D([0.3, 0], UNITS.m),
    width=Distance(0.6, UNITS.m),
    height=Distance(0.2, UNITS.m),
)
body = design.extrude_sketch("fluid_domain", sketch, Distance(0.02, UNITS.m))

# design.bodies now contains [body]
```

## When to use components — multi-body assemblies

Group related bodies with named containers:

```python
# Design with two components
design = modeler.create_design("MultiBody")

fluid_comp = design.add_component("FluidRegion")
solid_comp = design.add_component("SolidRegion")

# Extrude bodies into their respective components
fluid_body = fluid_comp.extrude_sketch("fluid", fluid_sketch, Distance(0.02, UNITS.m))
solid_body = solid_comp.extrude_sketch("solid", solid_sketch, Distance(0.02, UNITS.m))
```

Downstream in Fluent, you can identify the fluid vs solid regions by their component paths.

## Accessing bodies

**All bodies in design (flat, includes nested):**
```python
for body in design.bodies:
    print(body.name, body.volume.m_as(UNITS.m**3))
```

**Bodies of a specific component:**
```python
for body in fluid_comp.bodies:
    print(body.name)
```

**IMPORTANT:** Never cache `design.bodies` — it's a snapshot at call time. See `08-failure-modes.md` #5.

## Named selections at design level

Named selections tag faces, edges, or bodies for downstream reference. Live at the Design level (not component-scoped):

```python
design.create_named_selection("inlet", faces=[face1, face2])
design.create_named_selection("fluid_body", bodies=[body])
```

Retrieval:
```python
ns = design.get_named_selection("inlet")
faces = ns.faces
```

Named selections persist through PMDB and SCDOCX exports. See `06-named-selections.md`.

## Coordinate systems and datum planes

For complex geometries, add reference frames to design or component:

```python
from ansys.geometry.core.math import Point3D, UnitVector3D, Plane

# Custom coordinate system
cs = design.add_coordinate_system(
    name="body_frame",
    origin=Point3D([0.5, 0, 0]),
    direction_x=UnitVector3D([0, 1, 0]),
    direction_y=UnitVector3D([0, 0, 1]),
)

# Datum plane (for sketches on non-default planes)
plane = design.add_datum_plane(
    name="offset_plane",
    plane=Plane(
        origin=Point3D([0.5, 0, 0]),
        direction_x=UnitVector3D([1, 0, 0]),
        direction_y=UnitVector3D([0, 1, 0]),
    )
)
```

## Multi-body pattern for conjugate heat transfer

If a paper describes a fluid volume with a solid body inside (e.g., heated cylinder in flow, with heat conducting through the cylinder):

```python
design = modeler.create_design("HeatedCylinder")

# Fluid region (rectangle with hole -> annular)
fluid_sketch = Sketch()
fluid_sketch.box(...)                    # outer boundary
fluid_sketch.circle(...)                 # hole where the solid goes
fluid_body = design.extrude_sketch("fluid_domain", fluid_sketch, ...)

# Solid region (just the circle, extruded separately, same location)
solid_sketch = Sketch()
solid_sketch.circle(...)
solid_body = design.extrude_sketch("cylinder_solid", solid_sketch, ...)
```

Now the case has two bodies. Named selections distinguish them:
```python
# Fluid boundaries
design.create_named_selection("inlet", faces=[...])
design.create_named_selection("outlet", faces=[...])

# Interface between fluid and solid (shared cylinder surface — key for CHT)
design.create_named_selection("fluid_solid_interface", faces=[...])

# Solid body itself (for setting material properties in Fluent)
design.create_named_selection("cylinder_solid", bodies=[solid_body])
```

Fluent's watertight workflow with `setup_type="fluid-and-solid"` handles this as conjugate heat transfer.

## Closing designs

Close a design when moving to the next one on the same modeler:
```python
design1 = modeler.create_design("case_1")
# ... work ...
design1.close()

design2 = modeler.create_design("case_2")
```

Or use `DISABLE_ACTIVE_DESIGN_CHECK = True` to allow multiple simultaneous designs (advanced). See `08-failure-modes.md` #9.

## Exporting

Design-level operations:
```python
pmdb_path = design.export_to_pmdb()      # for Fluent
scdocx_path = design.export_to_scdocx()  # for SpaceClaim/Discovery
step_path = design.export_to_step()      # neutral CAD
```

See `07-export-formats.md`.

## Body-level operations

Once a body exists, you can modify it directly:

```python
body.translate(direction_vector, distance)   # move
body.rotate(...)                              # rotate
body.scale(factor)                            # scale uniformly
body.subtract(other_body)                     # boolean subtract
body.unite([other_body])                      # boolean union
body.intersect([other_body])                  # boolean intersect
```

See `04-modeling-operations.md`.

## For paper reproduction

Papers describe geometry as either:
- **Single-body** (fluid domain with obstacle as a hole) — use the flat pattern
- **Multi-body** (fluid + solid regions for CHT, or fluid + porous media) — use components + named selections

Component nesting rarely matters for CFD downstream. Keep it as flat as possible while distinguishing fluid vs. solid regions with named selections.
