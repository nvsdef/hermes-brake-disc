---
name: ansys-fluent-cfd
description: Set up and run Ansys Fluent CFD simulations via PyFluent. Use for meshing imported geometry, configuring physics (turbulence, materials, boundary conditions), running the solver, and extracting results. Primary target: steady incompressible RANS. Turbulence models: k-omega SST, k-epsilon, laminar.
---

# Ansys Fluent CFD Skill

## Purpose

Drive Ansys Fluent programmatically via PyFluent for meshing, solving, and post-processing CFD cases. Primary target: steady incompressible RANS. Well-supported extensions: heat transfer, external aero at low Mach. Out of scope for MVP: UDFs, multiphase, DPM, sliding meshes.

## When to use

- Meshing imported geometry (PMDB from pyansys-geometry, or STEP/CAD from external tools)
- Setting up physics (turbulence models, materials, boundary conditions)
- Running the solver and monitoring convergence
- Extracting numerical reports (mass flow, forces, pressures, temperatures)
- Rendering contours/vectors/streamlines to PNG

## When NOT to use

- Building geometry (spaceclaim-cad skill)
- Cases needing UDFs, multiphase, sliding meshes (out of scope)
- Compressible flow at high Mach (needs specialized setup)

## Reference sheets

| File | Covers |
|---|---|
| `reference/01-launching-sessions.md` | `launch_fluent()` modes, precision, parallel, retry logic |
| `reference/02-watertight-workflow.md` | Import -> local sizing -> surface mesh -> describe -> volume mesh |
| `reference/03-solver-settings-model.md` | Group/NamedObject/ListObject, state getters/setters, wildcards |
| `reference/04-physics-models.md` | viscous options (all turbulence models), energy, species |
| `reference/05-materials.md` | Database copy, cell zone assignment (critical) |
| `reference/06-boundary-conditions.md` | velocity-inlet, pressure-outlet, wall, symmetry, mass-flow-inlet |
| `reference/07-solver-methods.md` | Init methods, iteration, convergence criteria, transient stepping |
| `reference/08-report-definitions.md` | Force/flux/surface reports; parsing compute() output |
| `reference/09-graphics.md` | Contour/vector/streamline, view control, PNG export |
| `reference/10-field-data.md` | Extracting raw field arrays for custom Python post-processing |
| `reference/11-failure-modes.md` | Port conflicts, missing material assignment, unit issues, converged-but-wrong states |

## Standard workflow: steady incompressible RANS

```python
import ansys.fluent.core as pyfluent

# 1. Launch meshing (30-60s)
meshing = pyfluent.launch_fluent(
    product_version="26.1.0", mode="meshing",
    ui_mode="no_gui", precision="double", processor_count=2,
)

# 2. Watertight workflow
wt = meshing.watertight()
wt.import_geometry.file_name = "<geometry.pmdb>"
wt.import_geometry.length_unit = "m"
wt.import_geometry()

wt.add_local_sizing_wtm.add_child_to_task()
wt.add_local_sizing_wtm()

wt.create_surface_mesh.cfd_surface_mesh_controls.min_size = 0.002
wt.create_surface_mesh.cfd_surface_mesh_controls.max_size = 0.02
wt.create_surface_mesh()

wt.describe_geometry.update_child_tasks(setup_type_changed=False)
wt.describe_geometry.setup_type = "fluid"
wt.describe_geometry.update_child_tasks(setup_type_changed=True)
wt.describe_geometry()

wt.update_boundaries()
wt.update_regions()
wt.create_volume_mesh_wtm()

# 3. Switch to solver
solver = meshing.switch_to_solver()

# 4. Physics
solver.settings.setup.models.viscous.model = "k-omega"
solver.settings.setup.models.viscous.k_omega_model = "sst"

# 5. Material (BOTH steps required — see reference/05)
solver.settings.setup.materials.database.copy_by_name(
    type="fluid", name="water-liquid"
)
for zone in solver.settings.setup.cell_zone_conditions.fluid.get_object_names():
    solver.settings.setup.cell_zone_conditions.fluid[zone].general.material = "water-liquid"

# 6. Boundary conditions (use .value accessor)
inlet = solver.settings.setup.boundary_conditions.velocity_inlet["inlet"]
inlet.momentum.velocity_magnitude.value = 0.1

# 7. Reference values (for drag/lift Cd/Cl calculations)
solver.settings.setup.reference_values.area = <ref_area>
solver.settings.setup.reference_values.length = <ref_length>
solver.settings.setup.reference_values.velocity = <ref_velocity>
solver.settings.setup.reference_values.density = <ref_density>

# 8. Solve
solver.settings.solution.initialization.hybrid_initialize()
solver.settings.solution.run_calculation.iterate(iter_count=150)

# 9. Reports (compute() returns [{"name": [value, unit_str]}])
rd = solver.settings.solution.report_definitions
rd.force["drag"] = {}
rd.force["drag"].zones = ["cylinder"]
rd.force["drag"].force_vector = [1.0, 0.0, 0.0]
result = rd.compute(report_defs=["drag"])

# 10. Save + exit
solver.settings.file.write_case_data(file_name="case.cas.h5")
solver.exit()
```

## Hard-won gotchas (each cost us an iteration to find)

**Material assignment is TWO steps.** `copy_by_name()` only adds water to the library — you MUST also assign it to the cell zone. Missing this ran our case on air; mass flow was off by 815× (density ratio ρ_water/ρ_air). See `reference/05-materials.md`.

**`velocity_magnitude.value = X` not `velocity_magnitude = X`.** The direct assignment silently stores in a way Fluent may not read as the actual boundary value.

**Watertight task suffix `_wtm` on two specific tasks:** `add_local_sizing_wtm`, `create_volume_mesh_wtm`. Other watertight tasks don't have it. Introduced in PyFluent 0.40.

**Named selection names -> auto-mapped boundary types.** If you name a selection "inlet" (or containing "inlet"), the watertight describe_geometry step auto-assigns velocity-inlet. Same for "outlet" -> pressure-outlet and "symmetry" -> symmetry. Use these names to skip manual type assignment.

**Fluent gRPC port conflicts on back-to-back launches.** Adding a 10-15s sleep between sessions AND retry-with-backoff handles it robustly. See `reference/01-launching-sessions.md`.

**Report `compute()` return shape is `[{"name": [value, unit_str]}]`.** Not a dict. Not a scalar. Parser must unwrap the outer list.

**Report attribute names differ by kind:**
- `.force["name"].zones = [...]`
- `.flux["name"].boundaries = [...]`
- `.surface["name"].surface_names = [...]`

**Convergence can hide wrong physics.** Residuals hit convergence criteria fine even when wrong material is assigned. Always check mass balance (mass_in + mass_out ~ 0) AND a sanity numerical result against expected physics.

## For paper reproduction

1. Extract physics from paper: turbulence model, fluid properties, BC values
2. Match mesh strategy: paper reports total cell count, y+ target, boundary layer count
3. Iterate to match convergence: paper may report iteration count — match order of magnitude
4. Set reference values matching the paper's coefficient definitions
5. Compare metrics: expect factor-of-2 agreement (Cd, Cl, Nu, pressure drop). Exact match is rare.
6. Common miss: paper uses transient, you use steady RANS. Cd will typically underpredict at Re > 200.

## Available worked examples

- `examples/run_pipeline.py` + `mesh_and_solve.py` + `post_processing.py` — validated end-to-end pipeline for flow around a cylinder in a channel

More examples to be added (Phase D): mixing elbow with heat transfer, external aero, pipe with bend.
