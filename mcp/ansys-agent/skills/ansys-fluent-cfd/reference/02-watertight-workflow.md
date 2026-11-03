# Watertight Meshing Workflow

**Source:** PyFluent user guide + hands-on validation.

**Scope:** the watertight geometry meshing workflow — for clean CAD geometries (from SpaceClaim/Discovery via PMDB, or clean STEP/IGES). If your geometry has gaps or is dirty, use fault-tolerant instead.

---

## Task sequence (in required order)

```python
import ansys.fluent.core as pyfluent

meshing = pyfluent.launch_fluent(mode="meshing", product_version="26.1.0")
wt = meshing.watertight()

# 1. Import geometry
wt.import_geometry.file_name = "path/to/geom.pmdb"
wt.import_geometry.length_unit = "m"
wt.import_geometry()

# 2. Local sizing (accept defaults, or add rules)
wt.add_local_sizing_wtm.add_child_to_task()
wt.add_local_sizing_wtm()

# 3. Surface mesh
wt.create_surface_mesh.cfd_surface_mesh_controls.min_size = 0.002
wt.create_surface_mesh.cfd_surface_mesh_controls.max_size = 0.02
wt.create_surface_mesh.cfd_surface_mesh_controls.growth_rate = 1.2
wt.create_surface_mesh()

# 4. Describe geometry (fluid-only, no voids)
wt.describe_geometry.update_child_tasks(setup_type_changed=False)
wt.describe_geometry.setup_type = "fluid"
wt.describe_geometry.update_child_tasks(setup_type_changed=True)
wt.describe_geometry()

# 5. Update boundaries (auto-assigns types by name)
wt.update_boundaries()

# 6. Update regions
wt.update_regions()

# 7. Volume mesh
wt.create_volume_mesh_wtm()

# 8. Switch to solver
solver = meshing.switch_to_solver()
```

## Task attribute names (2026 R1 / PyFluent 0.40+)

| Task | Attribute |
|---|---|
| Import geometry | `wt.import_geometry` |
| Add local sizing | `wt.add_local_sizing_wtm` |
| Create surface mesh | `wt.create_surface_mesh` |
| Describe geometry | `wt.describe_geometry` |
| Update boundaries | `wt.update_boundaries` |
| Update regions | `wt.update_regions` |
| Add boundary layers | `wt.add_boundary_layers` (optional) |
| Create volume mesh | `wt.create_volume_mesh_wtm` |

Only `add_local_sizing_wtm` and `create_volume_mesh_wtm` have the `_wtm` suffix. See `11-failure-modes.md` #3.

## Sizing controls

Global sizing on `create_surface_mesh.cfd_surface_mesh_controls`:

- `min_size` — smallest element edge (m)
- `max_size` — largest element edge (m)
- `growth_rate` — max ratio between adjacent elements (typical 1.15-1.25)
- `curvature_normal_angle` — max angle deviation on curves (default 18 deg, lower = finer on curves)

**Rule of thumb.** For a domain of characteristic length L with feature of interest of size d:
- `max_size ~= L/30 to L/50`
- `min_size ~= d/10 to d/20`
- `growth_rate = 1.2`

## Local sizing (fine control on specific features)

Skip during first setup. To refine on a named face/edge:

```python
wt.add_local_sizing_wtm.add_child_to_task()
wt.add_local_sizing_wtm.boi_control_name = "cylinder_refine"
wt.add_local_sizing_wtm.boi_face_label_list = ["cylinder"]
wt.add_local_sizing_wtm.boi_size = 0.001
wt.add_local_sizing_wtm.add_child_and_update(defer_update=False)
```

## describe_geometry setup_type options

- `"fluid"` — geometry is fluid-only (no solid to subtract from). Most CFD cases.
- `"solid"` — for FEA (uncommon in watertight workflow).
- `"fluid-and-solid"` — coupled solid and fluid regions (conjugate heat transfer).

## Boundary layers (optional but recommended for wall shear/drag)

Insert AFTER `describe_geometry`, BEFORE `create_volume_mesh`:

```python
wt.add_boundary_layers.control_name = "smooth_transition_1"
wt.add_boundary_layers.insert_compound_child_task()
wt.add_boundary_layers_child_1()
```

Boundary layer controls (via `add_boundary_layers.<attr>`):
- `first_height` — first cell height (m). Target y+ ~= 1 for wall-resolved, y+ 30-300 for wall functions
- `number_of_layers` — typically 5-15
- `growth_rate` — layer growth (1.1-1.3)

## Volume mesh options

Default: polyhedra. Options via `create_volume_mesh_wtm.volume_fill`:
- `"tetrahedral"` — fast, coarser
- `"polyhedral"` — high quality, medium cost (default)
- `"poly-hexcore"` — polys near walls + hex core (best quality per cell)

```python
wt.create_volume_mesh_wtm.volume_fill = "poly-hexcore"
wt.create_volume_mesh_wtm.volume_fill_controls.hex_max_cell_length = 0.02
wt.create_volume_mesh_wtm()
```

## Estimating cell count before running

For a rectangular domain of L*H*D:
- Tet: `~5 * (L*H*D) / max_size^3`
- Poly: `~2 * (L*H*D) / max_size^3` (fewer, larger cells)

Ansys Student cap: 512k cells. If estimate > 400k, coarsen.

## After meshing

Named selections from your geometry become face zones with the same names. Fluent auto-assigns boundary types by name substring in `describe_geometry`:
- Contains `inlet` -> velocity-inlet
- Contains `outlet` -> pressure-outlet
- Contains `symmetry` -> symmetry

Other zones default to `wall`. See `06-boundary-conditions.md` for overriding types.

## Diagnostic: what came through?

After `switch_to_solver()`:
```python
solver.settings.setup.boundary_conditions.wall.get_object_names()
solver.settings.setup.boundary_conditions.velocity_inlet.get_object_names()
solver.settings.setup.boundary_conditions.pressure_outlet.get_object_names()
solver.settings.setup.boundary_conditions.symmetry.get_object_names()
solver.settings.setup.cell_zone_conditions.fluid.get_object_names()
```

Print these before iterating to confirm your named selections landed as expected.

## Mesh quality check

After volume mesh, Fluent reports skewness and orthogonal quality per cell zone. Target:
- Max skewness < 0.85 (worst cells)
- Min orthogonal quality > 0.1 (worst cells)

Anything worse: refine problem regions with local sizing, or coarsen globally.

## Fault-tolerant vs. watertight — when to switch

Use `meshing.fault_tolerant()` instead if:
- Geometry has small gaps, overlaps, or holes
- CAD is dirty (imported STEP/IGES from another tool)
- You need enclosure/capping to close open geometry

Fault-tolerant has more tasks (capping, edge extraction, region identification) and different attribute names (`create_volume_mesh_ftm`).

## 2D workflow — when to use

For 2D CAD (not thin 3D domain), use `meshing.two_dimensional_meshing()`. Skips volume meshing, produces face-based mesh.

Not applicable for our 2.5D approach (thin 3D domain with symmetry BCs).
