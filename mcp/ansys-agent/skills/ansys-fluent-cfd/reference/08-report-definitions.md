# Fluent Report Definitions

**Source:** hands-on + PyFluent docs.

**Scope:** creating report definitions, computing them, parsing return values. Covers force, flux, surface, and volume reports.

---

## Report types

Fluent has four main report definition kinds:

| Kind | Purpose | Target attribute |
|---|---|---|
| `force` | Force on walls (drag, lift) | `.zones = [wall_name]` |
| `flux` | Mass/heat flow through boundaries | `.boundaries = [boundary_name]` |
| `surface` | Field values on surfaces (avg pressure, max velocity) | `.surface_names = [surface_name]` |
| `volume` | Field values in cell zones (avg temp, integrated mass) | `.cell_zones = [zone_name]` |

Access them under `solver.settings.solution.report_definitions.<kind>`.

## Creating a report definition

Pattern is: assign empty dict, then set attributes:

```python
rd = solver.settings.solution.report_definitions

# Force report (drag on a wall)
rd.force["drag"] = {}
rd.force["drag"].zones = ["cylinder"]
rd.force["drag"].force_vector = [1.0, 0.0, 0.0]

# Flux report (mass flow at inlet)
rd.flux["mflow_inlet"] = {}
rd.flux["mflow_inlet"].boundaries = ["inlet"]

# Surface report (area-averaged pressure)
rd.surface["p_inlet"] = {}
rd.surface["p_inlet"].surface_names = ["inlet"]
rd.surface["p_inlet"].report_type = "surface-areaavg"
rd.surface["p_inlet"].field = "pressure"
```

## Computing a report

```python
result = rd.compute(report_defs=["drag"])
```

## Return shape (critical)

`compute()` returns:

```python
[{"drag": [6.836e-06, "N"]}]
```

That's:
- Outer list (single element)
- Dict keyed by report name
- Value is a two-element list: `[numeric_value, unit_string]`

**Parser template:**

```python
def unwrap(name, result):
    """Extract numeric value from compute() result."""
    if isinstance(result, list) and result:
        result = result[0]  # unwrap outer list
    if isinstance(result, dict) and name in result:
        v = result[name]
        if isinstance(v, list) and v and isinstance(v[0], (int, float)):
            return float(v[0])
    return None
```

## Batch vs. individual compute

`compute(report_defs=["a", "b", "c"])` runs multiple at once. **But** if ANY report is malformed, the entire batch fails with a cryptic Scheme error (`CDR: invalid argument`). Prefer looping with try/except:

```python
results = {}
for name in ["drag", "mflow_inlet", "mflow_outlet", "p_inlet", "p_outlet"]:
    try:
        r = rd.compute(report_defs=[name])
        results[name] = unwrap(name, r)
    except Exception as e:
        print(f"{name}: compute failed: {e}")
        results[name] = None
```

## Force reports

`.zones` accepts a list of wall zone names. Force is computed as the integral of (pressure + viscous) forces projected onto `.force_vector`.

```python
rd.force["drag"] = {}
rd.force["drag"].zones = ["cylinder"]
rd.force["drag"].force_vector = [1.0, 0.0, 0.0]  # X = drag direction
```

For lift, use the perpendicular axis:
```python
rd.force["lift"] = {}
rd.force["lift"].zones = ["airfoil"]
rd.force["lift"].force_vector = [0.0, 1.0, 0.0]  # Y = lift direction
```

**Drag coefficient calculation** requires reference values to be set:
```python
solver.settings.setup.reference_values.area = 2 * R * D  # projected area
solver.settings.setup.reference_values.length = 2 * R
solver.settings.setup.reference_values.velocity = U_inlet
solver.settings.setup.reference_values.density = fluid_density
```

Then `Cd = drag_N / (0.5 * rho * U^2 * A_ref)`.

## Flux reports (mass flow, heat flow)

`.boundaries` accepts a list of boundary zone names. Default computes mass flow rate.

```python
rd.flux["mflow_inlet"] = {}
rd.flux["mflow_inlet"].boundaries = ["inlet"]
# Result: mass flow through named boundary (positive = into domain by convention)
```

Multiple boundaries in one report sum. To get per-boundary values, create one report per boundary.

**Mass balance check:** `abs(mflow_inlet + mflow_outlet)` should be near zero (< 0.001 * expected mass flow).

## Surface reports

Field values on surfaces (planes, boundaries, isosurfaces). Common `report_type` values:

- `"surface-areaavg"` — area-weighted average
- `"surface-massavg"` — mass-weighted average
- `"surface-vertexmax"` / `"surface-vertexmin"` — max/min at vertices
- `"surface-integral"` — surface integral
- `"surface-facetavg"` — facet-weighted average

`.field` values are Fluent field names:
- `"pressure"`, `"velocity-magnitude"`, `"temperature"`
- `"x-velocity"`, `"y-velocity"`, `"z-velocity"`
- `"total-pressure"`, `"dynamic-pressure"`
- Full list depends on physics enabled. Query with `rd.surface["x"].field.allowed_values()`.

## Volume reports

Field values integrated or averaged over cell zones. Same shape as surface but with `.cell_zones`.

```python
rd.volume["avg_p_fluid"] = {}
rd.volume["avg_p_fluid"].cell_zones = ["fluid_domain"]
rd.volume["avg_p_fluid"].report_type = "volume-average"
rd.volume["avg_p_fluid"].field = "pressure"
```

`report_type` for volume: `"volume-average"`, `"volume-integral"`, `"volume-max"`, `"volume-min"`.

## Deleting report definitions

Between iterations or when parametrizing:

```python
if "drag" in rd.force.get_object_names():
    del rd.force["drag"]
```

## Standard sanity-check report set

For any converged case, compute these to verify physics:

```python
report_set = {
    "mflow_inlet":   ("flux",    {"boundaries": ["inlet"]}),
    "mflow_outlet":  ("flux",    {"boundaries": ["outlet"]}),
    "p_inlet":       ("surface", {"surface_names": ["inlet"],  "report_type": "surface-areaavg", "field": "pressure"}),
    "p_outlet":      ("surface", {"surface_names": ["outlet"], "report_type": "surface-areaavg", "field": "pressure"}),
    "v_avg_inlet":   ("surface", {"surface_names": ["inlet"],  "report_type": "surface-areaavg", "field": "velocity-magnitude"}),
    "v_max_domain":  ("surface", {"surface_names": ["symmetry"], "report_type": "surface-vertexmax", "field": "velocity-magnitude"}),
}
```

Sanity checks against results:
- `mflow_inlet + mflow_outlet ~= 0` -> mass conserves
- `v_avg_inlet ~= inlet BC velocity` -> BC applied correctly
- `mflow_inlet ~= v * rho * area` -> geometry scale correct
