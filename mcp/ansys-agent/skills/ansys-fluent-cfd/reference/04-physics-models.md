# Fluent Physics Models

**Source:** PyFluent settings docs + hands-on.

**Scope:** setting up viscous, energy, and species models for common CFD workflows. Multiphase and radiation are noted but out of MVP scope.

---

## Viscous model (turbulence)

Access:
```python
viscous = solver.settings.setup.models.viscous
```

Model selection:
```python
viscous.model = "k-omega"          # sets base model
viscous.k_omega_model = "sst"      # SST variant (best for boundary layers)
```

**Allowed values for `viscous.model`:**

| Value | Notes |
|---|---|
| `"inviscid"` | Euler equations. Aerodynamics only. |
| `"laminar"` | Re < ~2000. Simplest, most stable. |
| `"k-epsilon-standard"` | Robust general-purpose RANS. Wall functions. |
| `"k-omega-standard"` | Better near-wall than k-eps. |
| `"k-omega"` + `k_omega_model="sst"` | Best all-around RANS. **Default recommendation.** |
| `"spalart-allmaras"` | Single-equation. Fast. External aero. |
| `"transition-sst"` | Captures laminar-to-turbulent transition. |
| `"reynolds-stress"` | 7-equation. High-accuracy but expensive. |
| `"large-eddy-simulation"` | Transient. Compute-intensive. |
| `"detached-eddy-simulation"` | Hybrid RANS-LES. |
| `"scale-adaptive-simulation"` | Similar. |

Discover full list at runtime:
```python
viscous.model.allowed_values()
```

## Turbulence model quick-pick for common cases

| Case | Model |
|---|---|
| Internal pipe/duct flow | `k-omega SST` |
| External aero (Re < 10^7) | `k-omega SST` or `spalart-allmaras` |
| Boundary layer separation | `k-omega SST` (better than k-eps) |
| Free stream turbulence | `k-epsilon` OK |
| Vortex shedding, wake dynamics | `SST` steady OR LES transient |
| Heat transfer near walls | `k-omega SST` with wall-resolved mesh |
| Fully developed pipe flow, low Re | `laminar` if Re < 2000 |

## Near-wall treatment (RANS models)

For k-epsilon:
```python
viscous.near_wall_treatment = "standard-wall-fn"      # wall functions (coarser mesh OK)
viscous.near_wall_treatment = "enhanced-wall-treatment"  # y+ resolved
```

For k-omega SST: adaptive; handles both wall-resolved and wall-function meshes automatically.

**Rule:** Use wall-resolved mesh (y+ ~= 1) for accurate wall shear. Use wall functions (y+ 30-300) for faster runs with less mesh.

## Viscous options

```python
viscous.options.viscous_heating = False
viscous.options.curvature_correction = False
viscous.options.production_kato_launder = False
viscous.options.production_limiter = False
```

Rarely change these for standard cases.

## Energy equation

Enable for heat transfer:
```python
solver.settings.setup.models.energy.enabled = True
```

Sub-options:
```python
energy = solver.settings.setup.models.energy
energy.pressure_work = False
energy.viscous_dissipation = False  # Enable for high-speed flow
energy.inlet_diffusion = True
energy.kinetic_energy = False
```

Once enabled:
- Boundary conditions gain `.thermal` sub-object (temperature, heat flux)
- Materials use cp and k properties (see `05-materials.md`)
- Reports can compute average temperature, heat flux integrals

## Species / multi-species

Species transport (for reacting flows, mixing analysis):
```python
species = solver.settings.setup.models.species
# Setup varies significantly — see PyFluent docs for full config
```

Out of MVP scope. Consult docs for combustion, gas mixture, VOF applications.

## Multiphase

Multi-phase (VOF, Mixture, Eulerian):
```python
multiphase = solver.settings.setup.models.multiphase
# multiphase.number_of_phases = 2
```

Out of MVP scope.

## Radiation

Radiation models (P1, discrete ordinates, Rosseland, Monte Carlo):
```python
radiation = solver.settings.setup.models.radiation
```

Enable when radiation heat transfer is significant (>10% of total heat).

## Solver type: pressure-based vs density-based

For incompressible flow (Mach < 0.3), use pressure-based (default):
```python
solver.settings.setup.general.solver.type = "pressure-based"
```

For compressible flow (Mach > 0.3), use density-based:
```python
solver.settings.setup.general.solver.type = "density-based-implicit"
# or "density-based-explicit"
```

## Steady vs. transient

```python
solver.settings.setup.general.solver.time = "steady"
# or "transient"  (also called "unsteady")
```

Transient adds time step and time integration controls (see `07-solver-methods.md`).

## Verifying model state

```python
print(solver.settings.setup.models())
```

Prints the full state of all active models — viscous, energy, multiphase, radiation, species.

## For paper reproduction

Papers usually state:
- Turbulence model (map to `viscous.model` and `k_omega_model`)
- Whether heat transfer / energy equation enabled
- Wall treatment (resolved vs. function)
- Steady vs. transient
- Solver type (usually pressure-based unless compressible/high-Mach)

Match these exactly. Small model differences (k-eps vs. k-omega SST) can change Cd by 10-30% for wake-dominated flows.
