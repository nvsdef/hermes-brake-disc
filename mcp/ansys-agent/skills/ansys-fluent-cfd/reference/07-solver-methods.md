# Fluent Solver Methods, Initialization, and Iteration

**Source:** PyFluent solution docs + hands-on.

**Scope:** discretization schemes, initialization (hybrid vs. standard), running iterations, convergence criteria, transient time stepping, under-relaxation.

---

## Access

```python
sol = solver.settings.solution
```

Contains:
- `sol.methods` — discretization schemes, gradient scheme, coupling
- `sol.controls` — under-relaxation factors
- `sol.initialization` — hybrid_initialize, standard_initialize
- `sol.run_calculation` — iterate, dual_time_iterate

## Discretization schemes

For steady incompressible RANS, defaults usually work. To override:

```python
methods = sol.methods
methods.p_v_coupling.flow_scheme = "SIMPLE"   # or "SIMPLEC", "PISO", "Coupled"
methods.discretization_scheme["pressure"] = "second-order"
methods.discretization_scheme["mom"] = "second-order-upwind"       # momentum
methods.discretization_scheme["k"] = "second-order-upwind"          # turbulence k
methods.discretization_scheme["omega"] = "second-order-upwind"      # omega
methods.gradient_scheme = "least-squares-cell-based"
```

Second-order is more accurate but harder to converge. First-order is a good bootstrap for cases that diverge with second-order.

## p_v_coupling schemes

| Scheme | When to use |
|---|---|
| `"SIMPLE"` | Robust default for steady, incompressible |
| `"SIMPLEC"` | Slightly faster than SIMPLE. Same accuracy. |
| `"PISO"` | Transient with big time steps |
| `"Coupled"` | Best for large mesh, higher CPU per iter but faster overall |

## Under-relaxation factors

For stubborn convergence (bouncing residuals), lower these:

```python
controls = sol.controls
controls.under_relaxation["pressure"] = 0.3
controls.under_relaxation["momentum"] = 0.7
controls.under_relaxation["k"] = 0.8
controls.under_relaxation["omega"] = 0.8
```

Defaults are usually fine. Halve them if the case oscillates.

## Initialization

Two methods:

### Hybrid initialization (preferred)

Runs a potential-flow solve for ~10 iterations to get a decent initial guess, then hands off to the main solver.

```python
sol.initialization.hybrid_initialize()
```

Best for most cases. Fast and produces sensible initial fields.

### Standard initialization

Sets all cells to specified values. Useful if you know the initial condition (e.g., freestream velocity):

```python
sol.initialization.standard_initialize()
# But usually you want to set values first:
sol.initialization.compute_defaults_from = "inlet"   # copy from inlet BC
sol.initialization.standard_initialize()
```

Or manually:
```python
sol.initialization.set_default_values_from_dict({
    "x-velocity": 0.1,
    "y-velocity": 0.0,
    "z-velocity": 0.0,
    "pressure": 0.0,
    "k": 1e-3,
    "omega": 100,
})
sol.initialization.standard_initialize()
```

## Running iterations — steady

```python
sol.run_calculation.iterate(iter_count=150)
```

Fluent iterates. Convergence stops early if residuals fall below the criteria (default 1e-3 for each field). See below.

## Convergence criteria

Default: all residuals below 1e-3. Override:

```python
sol.monitor.residual.equations["continuity"].absolute_criteria = 1e-4
sol.monitor.residual.equations["x-velocity"].absolute_criteria = 1e-4
# etc for other fields
```

Or disable convergence stopping (iterate the full count regardless):
```python
sol.monitor.residual.convergence_criterion = "none"
```

## Interpretation of residuals

- `1e-3`: usually converged for engineering purposes
- `1e-4`: high-accuracy convergence (drag/lift within 1%)
- `1e-6`: research-grade

Residuals plateau — no further reduction — means you've reached the numerical noise floor. Iterating more won't help; check the actual physics (see `11-failure-modes.md` #9).

## Running iterations — transient

```python
sol.run_calculation.transient_controls.time_step_size = 0.001
sol.run_calculation.transient_controls.max_iter_per_time_step = 20
sol.run_calculation.dual_time_iterate(time_step_count=100, max_iter_per_step=20)
```

Time step should resolve the smallest timescale of interest. For vortex shedding at frequency f: `dt = 1 / (20 * f)` or smaller.

## Convergence monitoring

Watch specific report definitions (drag, mass flow) as convergence indicators, not just residuals:

```python
sol.monitor.report_plots["drag_monitor"] = {}
sol.monitor.report_plots["drag_monitor"].report_defs = ["drag"]
sol.monitor.report_plots["drag_monitor"].print_state = True
```

A case is "engineering converged" when the report of interest (Cd, mass flow, pressure drop) stops changing to 3-4 significant figures, regardless of residuals.

## When residuals grow (divergence)

**Symptoms:** residuals rise, or solver reports NaN/floating point exceptions.

**Causes:**
1. Bad initial condition — reinitialize with hybrid
2. Time step too big (transient) — halve it
3. Under-relaxation too high — halve all
4. Mesh has bad cells — check `mesh.check()` output
5. BCs are physically inconsistent — verify inlet/outlet balance

**Recovery:** re-init, lower under-relaxation, drop to first-order for 100 iters, then go back to second-order.

## Solution animation

Save frames as it iterates:
```python
sol.calculation_activities.solution_animation["drag_history"] = {}
# Record report over iterations
```

Post-hoc: use monitor plots to see convergence history.

## Reading residual history

After the solver runs, get the residuals series:
```python
sol.monitor.residual.equations["continuity"].get_residuals()
```

Not needed for typical workflows but useful for research/analysis.

## For paper reproduction

Match the paper's:
- Solver type (usually pressure-based SIMPLE for incompressible)
- Discretization order (usually second-order upwind for accuracy)
- Convergence criteria (papers often report iterations to convergence)
- Time step for transient cases (must resolve the paper's reported frequencies)
- Under-relaxation if unusual (papers rarely change from defaults; if they mention it, match)
