# Fluent Materials - Database and Cell Zone Assignment

**Source:** PyFluent docs + hands-on validation.

**Scope:** getting the right fluid material to actually be used by the solver. The two-step process is the #1 gotcha in the whole Fluent CFD workflow.

---

## The critical two-step pattern

Every material assignment is **always two steps**:

1. Copy from Fluent's built-in database into the case's local material library
2. Assign to the fluid cell zone's `material` property

Missing either leaves the case running on air.

```python
# Step 1: copy water into the case's material library
solver.settings.setup.materials.database.copy_by_name(
    type="fluid", name="water-liquid"
)

# Step 2: assign to every fluid cell zone
for zone in solver.settings.setup.cell_zone_conditions.fluid.get_object_names():
    solver.settings.setup.cell_zone_conditions.fluid[zone].general.material = "water-liquid"
```

## What each step does

**Step 1** puts the material's properties (density, viscosity, cp, k, etc.) into the case's local material list. Before this, the material isn't available for assignment.

**Step 2** points a cell zone at a specific material by name. Before this, the zone uses its default (typically air).

## Symptoms of skipping step 2

- Mass flow rate off by ~815x (density ratio water/air)
- Pressure drop tiny (air has less momentum to lose)
- Drag on obstacles suspiciously low
- Convergence still succeeds — Fluent doesn't know you meant water

## Common material names (Fluent built-in database)

| Name | Type | Default density (kg/m^3) | Default viscosity (Pa*s) |
|---|---|---|---|
| `air` | fluid | 1.225 | 1.789e-5 |
| `water-liquid` | fluid | 998.2 | 1.003e-3 |
| `water-vapor` | fluid | 0.5542 | 1.34e-5 |
| `mercury` | fluid | 13529 | 1.523e-3 |
| `aluminum` | solid | 2719 | (n/a) |
| `steel` | solid | 8030 | (n/a) |
| `copper` | solid | 8978 | (n/a) |

Use `solver.settings.setup.materials.fluid.get_object_names()` to see what's already in the case library.

## Creating custom fluid materials (constant properties)

For a non-database fluid (e.g., 40% glycol at 40C):

```python
solver.settings.setup.materials.fluid["glycol-40C"] = {}
mat = solver.settings.setup.materials.fluid["glycol-40C"]
mat.density.value = 1050.0
mat.viscosity.value = 0.005
# For heat transfer:
mat.specific_heat.value = 3800.0
mat.thermal_conductivity.value = 0.28
```

Then assign as normal:

```python
solver.settings.setup.cell_zone_conditions.fluid[zone].general.material = "glycol-40C"
```

## Temperature-dependent properties

For accurate heat transfer over a temperature range, use `piecewise-linear` or `polynomial` options instead of constant:

```python
mat.density.option = "boussinesq"
# or "piecewise-linear" with a table of (T, rho) points
```

For steady incompressible flows without significant temperature variation, constant properties are fine.

## Verifying material assignment

After both steps, read back:

```python
zone = list(solver.settings.setup.cell_zone_conditions.fluid.get_object_names())[0]
mat_name = solver.settings.setup.cell_zone_conditions.fluid[zone].general.material()
print(f"Zone {zone} uses material: {mat_name}")
```

Should print `water-liquid` (or whatever you assigned). If it prints `air`, step 2 didn't take.

## Reference values for coefficient calculations

Set these to match the paper's Re/Cd/Cl/Nu definitions:

```python
solver.settings.setup.reference_values.density  = 998.2       # rho
solver.settings.setup.reference_values.velocity = 0.1         # U_ref
solver.settings.setup.reference_values.length   = 2 * 0.02    # L_ref (e.g., cylinder D)
solver.settings.setup.reference_values.area     = 2 * 0.02 * 0.02  # A_ref (projected)
```

These don't affect the solve — only how Fluent computes `Cd = F / (0.5 * rho * U^2 * A)` in reports.

## For paper reproduction

Papers usually specify:
- Density (kg/m^3)
- Kinematic viscosity nu (m^2/s) OR dynamic viscosity mu (Pa*s)
- Sometimes cp and k for heat transfer

Check which the paper uses in its Re definition: `Re = U*L/nu = rho*U*L/mu`. Match reference values to the paper's conventions.

---

## Out of scope for this reference

- Multiphase materials (VOF, mixture models): different workflow, needs separate skill
- Reacting flows (species transport): separate models module
- Discrete phase model (DPM particles): separate injections module
