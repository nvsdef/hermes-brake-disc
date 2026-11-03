# PyAnsys Geometry Named Selections

**Source:** PyAnsys Geometry NamedSelection API + hands-on.

**Scope:** tagging faces, bodies, and edges for downstream reference in Fluent (or Mechanical). Naming conventions that trigger Fluent's automatic boundary-type assignment. Persistence through export formats.

---

## Creating a named selection

Design-level operation. Accepts any combination of entity types:

```python
design.create_named_selection(
    name="inlet",
    faces=[face1, face2],
    # optionally: bodies=[...], edges=[...], vertices=[...],
    # components=[...], design_points=[...], design_curves=[...]
)
```

Returns a `NamedSelection` object with these properties:
- `id`, `name`
- `.faces`, `.bodies`, `.edges`, `.beams`, `.vertices`, `.components`, `.design_points`, `.design_curves`

## Naming conventions that Fluent auto-recognizes

**Critical:** in the watertight `describe_geometry` step, Fluent auto-assigns boundary types based on named selection name substrings:

| Name contains | Auto-assigned type |
|---|---|
| `inlet` | `velocity-inlet` |
| `outlet` | `pressure-outlet` |
| `symmetry` | `symmetry` |
| (anything else, on a face) | `wall` |

**Implications:**
- Standardize inlet/outlet/symmetry names to short slugs
- **Avoid these keywords in wall names** (a wall named "inlet-wall" gets misclassified as an inlet)
- Cylinder or obstacle walls: name simply `"cylinder"`, `"obstacle"`, etc.

**Recommended vocabulary:**
- `inlet`, `outlet`, `symmetry` — reserved names
- `walls` — top/bottom walls of a channel
- `cylinder`, `airfoil`, `body` — obstacle names
- `fluid_solid_interface` — for conjugate heat transfer

## Retrieving a named selection

```python
inlet_ns = design.get_named_selection("inlet")
print(inlet_ns.faces)   # list of Face objects
```

## Modifying membership

Named selections are **immutable** — `add_members` and `remove_members` return a NEW selection with the same name:

```python
inlet_ns = inlet_ns.add_members(faces=[new_face])
# inlet_ns is now the new named selection; the original is superseded
```

```python
inlet_ns = inlet_ns.remove_members(members=[old_face])
```

## Common patterns

### CFD standard boundary tagging

```python
inlet_faces = [f for f in body.faces if is_inlet_face(f)]
outlet_faces = [f for f in body.faces if is_outlet_face(f)]
top_bottom_walls = [f for f in body.faces if is_horizontal_wall(f)]
symmetry_faces = [f for f in body.faces if is_symmetry_face(f)]
cylinder_faces = [f for f in body.faces if f.surface_type == SurfaceType.SURFACETYPE_CYLINDER]

design.create_named_selection("inlet",    faces=inlet_faces)
design.create_named_selection("outlet",   faces=outlet_faces)
design.create_named_selection("walls",    faces=top_bottom_walls)
design.create_named_selection("symmetry", faces=symmetry_faces)
design.create_named_selection("cylinder", faces=cylinder_faces)
```

### Tagging a whole body (for material assignment in Fluent)

```python
design.create_named_selection("fluid_domain", bodies=[fluid_body])
design.create_named_selection("cylinder_solid", bodies=[solid_body])
```

Fluent will map body-level named selections to cell zones (`solver.settings.setup.cell_zone_conditions.fluid[...]`).

### CHT / multi-body interface

For conjugate heat transfer, the interface between fluid and solid needs a named selection:

```python
# Find faces on the shared cylinder surface
interface_faces = [
    f for f in fluid_body.faces
    if f.surface_type == SurfaceType.SURFACETYPE_CYLINDER
]

design.create_named_selection("fluid_solid_interface", faces=interface_faces)
```

Fluent will pair this with the matching face on the solid body during meshing.

## Persistence through export

Named selections are preserved in:
- **PMDB** (Fluent-preferred) — all names come through as face zones
- **SCDOCX** (Ansys-native) — preserved
- **STEP** / IGES / Parasolid — **NOT preserved**, retag manually after import

## Deleting a named selection

```python
design.delete_named_selection("some_name")
```

Or via the object:
```python
ns.delete()
```

Useful when regenerating a design in a loop and the previous named selection is stale.

## Multi-face selections and Fluent face zone splitting

Sometimes SpaceClaim splits a cylindrical face into multiple face zones during meshing (at seams). Group all curved-surface faces into ONE named selection:

```python
cylinder_faces = [
    f for f in body.faces
    if f.surface_type == SurfaceType.SURFACETYPE_CYLINDER
]
design.create_named_selection("cylinder", faces=cylinder_faces)
```

Downstream, Fluent sees "cylinder" as one boundary regardless of underlying face splits. See `08-failure-modes.md` #7.

## Retrieving via design.named_selections

Iterate all named selections:

```python
for ns in design.named_selections:
    print(ns.name, len(ns.faces), len(ns.bodies))
```

## What to include in named selections

For CFD:
- **Faces** — for boundary conditions (inlet, outlet, wall, symmetry)
- **Bodies** — for cell zone / material assignment

For FEA (Mechanical):
- **Faces** — for load application
- **Edges** — for constrained supports
- **Vertices** — for point loads

For most CFD workflows, you'll only need faces (BC tagging) and bodies (material tagging). Don't over-engineer with edge/vertex selections unless downstream needs them.

## For paper reproduction

Papers describe boundaries by location or role ("inlet at left face", "cylinder wall at center", "top and bottom walls"). Map to named selections:

1. Identify each face using surface_type + normal + centroid
2. Group into named selections following the reserved-vocabulary convention
3. Export to PMDB
4. Fluent auto-maps inlet/outlet/symmetry; you manually configure others

**Common mistake:** using `"inlet_bc"` or `"my_inlet"` — Fluent's substring auto-detection will still catch it, but stick to plain `"inlet"` for clarity.
