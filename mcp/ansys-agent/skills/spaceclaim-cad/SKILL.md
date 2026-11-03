---
name: spaceclaim-cad
description: Build parametric 3D geometry via pyansys-geometry driving SpaceClaim (or Discovery/Geometry Service). Use when the user needs to construct CAD geometry programmatically for CFD/FEA — extrude sketches, boolean operations, named boundary tagging, export for downstream simulation.
---

# SpaceClaim CAD Modeling Skill

## Purpose

Build parametric 3D geometry programmatically using `pyansys-geometry`, which drives one of three backends automatically: Ansys Geometry Service, Ansys Discovery, or Ansys SpaceClaim. Ansys Student ships with SpaceClaim as the effective backend.

## When to use

- Building CAD geometry from parameters for CFD/FEA workflows
- Modifying an existing parametric design (change dimensions, re-run downstream)
- Exporting geometry with tagged boundaries for Fluent/Mechanical
- Any workflow where "geometry as code" is preferable to manual GUI editing

## When NOT to use

- Manual repair of dirty imported CAD (SpaceClaim GUI first, then import)
- Direct STEP/IGES manipulation without a modeler backend
- Meshing (that lives in the ansys-fluent-cfd skill)

## Reference sheets

Read as needed for the workflow you're implementing:

| File | Covers |
|---|---|
| `reference/01-launching-connecting.md` | `launch_modeler()`, backend selection, common launch failures |
| `reference/02-sketch-api.md` | Sketch class, Point2D, primitives (box, circle, segment, arc, ellipse) |
| `reference/03-designer-hierarchy.md` | Design/Component/Body assembly model |
| `reference/04-modeling-operations.md` | extrude, revolve, sweep, boolean, fillet, chamfer, shell |
| `reference/05-face-edge-queries.md` | Face.surface_type, normal, area, centroid, bounding_box |
| `reference/06-named-selections.md` | Tagging faces/bodies for downstream Fluent boundary conditions |
| `reference/07-export-formats.md` | PMDB (Fluent-preferred) vs SCDOCX vs STEP tradeoffs |
| `reference/08-failure-modes.md` | Common errors + validated fixes |

## Standard workflow: fluid domain from parameters

```python
from ansys.geometry.core import launch_modeler
from ansys.geometry.core.sketch import Sketch
from ansys.geometry.core.math import Point2D
from ansys.geometry.core.misc import UNITS, Distance
from ansys.geometry.core.designer.face import SurfaceType

# 1. Connect (30-60s on Ansys Student — SpaceClaim boots)
modeler = launch_modeler()

# 2. Build sketch (2D on default XY plane)
sketch = Sketch()
sketch.box(center=Point2D([L/2, 0], UNITS.m),
           width=Distance(L, UNITS.m),
           height=Distance(H, UNITS.m))
sketch.circle(Point2D([cx, cy], UNITS.m), Distance(R, UNITS.m))

# 3. Extrude to 3D
design = modeler.create_design("case_name")
body = design.extrude_sketch("fluid_domain", sketch, Distance(D, UNITS.m))

# 4. Classify faces (use surface_type for curved surfaces — see reference/05)
for face in body.faces:
    if face.surface_type == SurfaceType.SURFACETYPE_CYLINDER:
        cylinder_faces.append(face)
    else:
        n = face.normal()  # Only reliable on planar faces
        # classify by direction

# 5. Tag boundaries (Fluent will auto-map names — see reference/06)
design.create_named_selection("inlet",    faces=inlet_faces)
design.create_named_selection("outlet",   faces=outlet_faces)
design.create_named_selection("walls",    faces=wall_faces)
design.create_named_selection("symmetry", faces=sym_faces)
design.create_named_selection("cylinder", faces=cylinder_faces)

# 6. Export for Fluent watertight workflow
pmdb_path = design.export_to_pmdb()

# 7. Clean up
modeler.close()
```

## Hard-won gotchas

- **Docker + Geometry Core + DMS attempts precede SpaceClaim fallback.** On Ansys Student, all three warnings are normal; SpaceClaim eventually launches (~30-60s).
- **Curved surfaces need `SurfaceType.SURFACETYPE_CYLINDER` check**, not normal-based classification. `Face.normal()` samples at UV=(0.5, 0.5); on a cylinder that point can be aligned with any axis.
- **`export_to_pmdb()` writes to CWD**, returns absolute path. Use `shutil.move()` for a different output directory.
- **`modeler.close()` is required.** Leaked SpaceClaim processes eat license slots and RAM.
- **PMDB is Fluent-friendly** because it preserves named selections through the CAD -> mesh handoff. STEP loses them; SCDOCX preserves them but is Ansys-only.

## For paper reproduction

When reproducing published geometry:
1. Read paper for exact dimensions; watch unit systems (mixed mm and m is common)
2. If paper uses non-standard axes (e.g., streamwise = Z), transform to Fluent's expected frame at export time
3. Multi-body geometries (solid inside fluid domain) use two separate bodies with distinct named selections — see `reference/03-designer-hierarchy.md`

## Available worked examples

- `examples/channel_with_obstacle.py` — validated 2.5D flow-around-cylinder geometry generation

More examples to be added (Phase D): external aero domain, pipe with bend, airfoil in freestream.
