# Fluent Boundary Conditions

**Source:** PyFluent docs + hands-on validation.

**Scope:** the boundary condition types most common in steady incompressible CFD — how to set them, override types, verify state.

---

## The BC assignment pattern

Boundary conditions live at:
```python
bc = solver.settings.setup.boundary_conditions
```

Sub-containers by type:
```python
bc.velocity_inlet["name"]
bc.pressure_outlet["name"]
bc.mass_flow_inlet["name"]
bc.pressure_inlet["name"]
bc.wall["name"]
bc.symmetry["name"]
bc.periodic["name"]
bc.interior["name"]
```

## Velocity inlet

Most common inlet for incompressible flow.

```python
inlet = solver.settings.setup.boundary_conditions.velocity_inlet["inlet"]

# Magnitude, normal to boundary (default spec method)
inlet.momentum.velocity_magnitude.value = 0.5  # m/s

# Turbulence (if k-omega SST or k-epsilon)
inlet.turbulence.turbulence_specification = "Intensity and Viscosity Ratio"
inlet.turbulence.turbulent_intensity = 0.05  # 5%
inlet.turbulence.turbulent_viscosity_ratio = 10

# Alternative: Intensity and Hydraulic Diameter
inlet.turbulence.turbulence_specification = "Intensity and Hydraulic Diameter"
inlet.turbulence.turbulent_intensity = 0.05
inlet.turbulence.hydraulic_diameter = 0.1  # m

# For heat transfer (if energy equation enabled)
inlet.thermal.temperature.value = 293.15  # K
```

**CRITICAL: use `.value = X`** on velocity_magnitude, temperature, etc. Direct assignment `velocity_magnitude = X` may not persist. See `11-failure-modes.md` #2.

**Velocity specification methods:**
- `"Magnitude, Normal to Boundary"` (default)
- `"Magnitude and Direction"` — requires setting `flow_direction`
- `"Components"` — set `x_velocity`, `y_velocity`, `z_velocity` individually

## Pressure outlet

```python
outlet = solver.settings.setup.boundary_conditions.pressure_outlet["outlet"]

# Gauge pressure at outlet (default: 0 Pa)
outlet.momentum.gauge_pressure.value = 0

# Backflow turbulence (in case flow reverses)
outlet.turbulence.turbulence_specification = "Intensity and Viscosity Ratio"
outlet.turbulence.backflow_turbulent_intensity = 0.05
outlet.turbulence.turbulent_viscosity_ratio = 4

# Backflow temperature
outlet.thermal.backflow_total_temperature = 293.15
```

## Mass flow inlet

For compressible flow, or when specifying flow rate instead of velocity.

```python
mfi = solver.settings.setup.boundary_conditions.mass_flow_inlet["inlet"]
mfi.momentum.mass_flow_rate.value = 0.5  # kg/s
mfi.turbulence.turbulence_specification = "Intensity and Viscosity Ratio"
```

## Wall

Default type for solid boundaries. Most walls need no configuration beyond defaults (no-slip, adiabatic).

For a moving wall:
```python
wall = solver.settings.setup.boundary_conditions.wall["moving_wall"]
wall.momentum.wall_translation = True
wall.momentum.velocity_magnitude.value = 1.0
```

For a heated wall (with energy equation):
```python
wall.thermal.thermal_bc = "Temperature"
wall.thermal.temperature.value = 350.0

# Or fixed heat flux
wall.thermal.thermal_bc = "Heat Flux"
wall.thermal.heat_flux.value = 100.0  # W/m^2
```

Wall roughness (rare for CFD; important for pipe flow):
```python
wall.momentum.roughness_height = 0.001
wall.momentum.roughness_constant = 0.5
```

## Symmetry

No parameters — Fluent treats the plane as a mirror. Auto-mapped by named selection containing "symmetry".

Useful for reducing 3D problems to 2.5D (thin slab with symmetry on front/back faces).

## Periodic

Enforces matching flow between two identical faces. Requires the mesh to have periodic connections (set up during meshing).

```python
periodic = solver.settings.setup.boundary_conditions.periodic["periodic_1"]
periodic.type = "translational"  # or "rotational"
```

## Changing a zone's type after import

If a zone got the wrong type (rare — usually named-selection auto-mapping is right):

```python
solver.settings.setup.boundary_conditions.set_zone_type(
    zone_list=["misnamed_zone"],
    new_type="velocity-inlet"
)
```

`new_type` string values (Fluent-native):
- `"velocity-inlet"`, `"pressure-outlet"`, `"pressure-inlet"`
- `"mass-flow-inlet"`, `"outflow"`
- `"wall"`, `"symmetry"`, `"periodic"`
- `"interior"`, `"axis"` (for axisymmetric)

## Verifying BC state

Print full BC state:
```python
print(solver.settings.setup.boundary_conditions.velocity_inlet["inlet"]())
```

Expected structure:
```python
{
    "name": "inlet",
    "momentum": {"velocity_specification_method": "Magnitude, Normal to Boundary",
                 "velocity_magnitude": {"option": "value", "value": 0.1}, ...},
    "turbulence": {...},
    "thermal": {...},
}
```

If `momentum.velocity_magnitude.value` is not what you set: setter didn't take (see `11-failure-modes.md` #2).

## Turbulence intensity guidance

| Application | Intensity |
|---|---|
| Highly turbulent (jets, elbows) | 5-10% |
| Medium (ducted flow) | 3-5% |
| Low (external aero, quiet inlets) | 0.5-1% |
| Free stream | 0.1-1% |

Turbulent viscosity ratio: typically 1-10. Higher = more diffusion, generally OK for initial setup.

## Common paper-reproduction BCs

**Backward-facing step:** velocity-inlet upstream, pressure-outlet downstream, walls no-slip, symmetry on front/back (if 2.5D).

**Flow past cylinder (Ahmed body, cylinder in freestream):** velocity-inlet at freestream, pressure-outlet at far boundary, symmetry on ground/sides depending on setup, wall on the body.

**Pipe flow (fully developed):** velocity-inlet OR periodic (for infinitely long), pressure-outlet at end, wall on pipe.

**Heated cavity:** wall with fixed temperature on hot side, wall with fixed temperature on cold side, symmetry or wall on the other sides depending on the problem.

**Impinging jet:** velocity-inlet at jet nozzle, pressure-outlet at ambient far boundary, wall at target surface.

## Verifying BCs match what you meant

After solve, compute area-averaged inlet velocity report (see `08-report-definitions.md`) and compare to your set BC value. Should match within numerical tolerance.

If it doesn't:
- Setter didn't take (use `.value = X`)
- Wrong zone name
- Named selection auto-mapping tagged a wall as inlet (rename the wall)
