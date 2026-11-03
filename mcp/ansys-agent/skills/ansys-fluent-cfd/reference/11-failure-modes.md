# Fluent CFD Failure Modes and Recovery

**Source:** hands-on iteration during the flow-around-cylinder build (Ansys 2026 R1 Student v261, PyFluent 0.40.x). Every fix here was reached the hard way.

**Scope:** the ways Fluent silently or loudly fails, ordered by frequency and impact.

---

## 1. Fluid material silently defaults to air

**Symptom.** Solver runs and converges. Mass flow, drag, and pressure drop are all off by ~815x lower than expected for water.

**Root cause.** `materials.database.copy_by_name(type="fluid", name="water-liquid")` only ADDS water to the case's material library. It does NOT set water as the active fluid for the cell zone. The default cell zone material stays air.

**Fix.** Two steps required:

```python
# Step 1: copy material to library
solver.settings.setup.materials.database.copy_by_name(
    type="fluid", name="water-liquid"
)

# Step 2: ASSIGN to every fluid cell zone
for zone in solver.settings.setup.cell_zone_conditions.fluid.get_object_names():
    solver.settings.setup.cell_zone_conditions.fluid[zone].general.material = "water-liquid"
```

**Sanity check.** After solve, `mass_flow_inlet` should equal `velocity * density * area`. If off by ratio 998/1.225 = 815, you skipped step 2.

**See also:** `05-materials.md`.

---

## 2. `velocity_magnitude = X` doesn't apply

**Symptom.** BC readback shows `{'option': 'value', 'value': 0.1}`, but actual flow at inlet is ~zero.

**Root cause.** For unit-aware Real settings objects, direct assignment `velocity_magnitude = 0.1` may not persist through to the solver. The canonical setter is `.value = X`.

**Fix.**

```python
inlet = solver.settings.setup.boundary_conditions.velocity_inlet["inlet"]
inlet.momentum.velocity_magnitude.value = 0.1  # NOT: inlet.momentum.velocity_magnitude = 0.1
```

**Verify.** Read back: `inlet.momentum.velocity_magnitude()` should return `{'option': 'value', 'value': 0.1}`.

**Rule of thumb.** For scalar Real settings that own units, always use `.value = X`.

---

## 3. Watertight task `_wtm` suffix on two specific tasks

**Symptom.**
```
AttributeError: 'WatertightMeshingWorkflow' has no attribute 'add_local_sizing'.
The most similar names are: add_local_sizing_wtm
```

**Root cause.** PyFluent 0.40+ renamed two watertight tasks with `_wtm` suffix. Others did not rename.

**Fix.** Use exactly these names:

- `wt.import_geometry` (no suffix)
- `wt.add_local_sizing_wtm` (renamed)
- `wt.create_surface_mesh` (no suffix)
- `wt.describe_geometry` (no suffix)
- `wt.update_boundaries` (no suffix)
- `wt.update_regions` (no suffix)
- `wt.create_volume_mesh_wtm` (renamed)

**Note.** Fault-tolerant workflow uses `_ftm` suffix on volume mesh (`create_volume_mesh_ftm`). 2D meshing uses `add_local_sizing_wtm` too.

---

## 4. Fluent gRPC port conflict on back-to-back launches

**Symptom.**
```
grpc._channel._MultiThreadedRendezvous: StatusCode.UNAVAILABLE
"failed to connect to all addresses; ipv4:127.0.0.1:60102: Connection refused"
```

**Root cause.** Previous Fluent process's RPC port hasn't fully released before a new session launches. Common when running mesh+solve then post in one script.

**Fix.** Retry-with-backoff. Wrap `launch_fluent()`:

```python
import time
import ansys.fluent.core as pyfluent

def launch_fluent_with_retry(mode, max_retries=3, retry_wait=15, **kwargs):
    for attempt in range(1, max_retries + 1):
        try:
            return pyfluent.launch_fluent(mode=mode, **kwargs)
        except Exception:
            if attempt < max_retries:
                time.sleep(retry_wait)
    raise RuntimeError(f"Fluent launch failed after {max_retries} attempts")
```

Also add `time.sleep(10)` between stages in orchestrator code.

**See working implementation:** `../examples/_launch.py`.

---

## 5. Report `compute()` return shape misparse

**Symptom.** Report values come back as `None`.

**Root cause.** `rd.compute(report_defs=["name"])` returns:

```python
[{"name": [value, unit_str]}]
```

Outer list of dicts, each dict's value is a two-element list `[number, unit_string]`. Not a scalar. Not a plain dict.

**Fix.**

```python
def unwrap(name, result):
    if isinstance(result, list) and result:
        result = result[0]
    if isinstance(result, dict) and name in result:
        v = result[name]
        if isinstance(v, list) and v and isinstance(v[0], (int, float)):
            return float(v[0])
    return None
```

---

## 6. Report attribute names differ by report type

**Symptom.**
```
AttributeError: 'force_child' object has no attribute 'zone_names'
The most similar names are: zones
```

**Root cause.** Each report type uses a different attribute for its target zones:

| Report type | Target attribute |
|---|---|
| `report_definitions.force["name"]` | `.zones = ["wall"]` |
| `report_definitions.flux["name"]` | `.boundaries = ["inlet"]` |
| `report_definitions.surface["name"]` | `.surface_names = ["inlet"]` |
| `report_definitions.volume["name"]` | `.cell_zones = ["fluid"]` |

Surface reports also need `.report_type` and `.field`.

**Fix.** Use the right attribute per type. See `08-report-definitions.md`.

---

## 7. Named-selection auto-mapping is helpful but implicit

**Behavior.** In watertight `describe_geometry`, Fluent auto-assigns boundary types based on named selection name substrings:

- Contains `inlet` -> velocity-inlet
- Contains `outlet` -> pressure-outlet
- Contains `symmetry` -> symmetry

**Implication.** A wall named "elbow-inlet-wall" gets mapped to velocity-inlet, incorrectly.

**Fix.** Standardize names to short slugs: `inlet`, `outlet`, `symmetry`, `walls`, `cylinder`. Avoid these keywords in wall names.

---

## 8. PMDB `length_unit` mismatch silently scales geometry

**Symptom.** Mesh bounding box is 1000x too large or too small.

**Root cause.** PMDB stores geometry in the source CAD's units. Fluent scales based on `length_unit` at import. Mismatch silently scales.

**Fix.** Always set to match the sketch units:

```python
wt.import_geometry.length_unit = "m"  # matches UNITS.m in pyansys-geometry
```

Verify by checking the bounding box in the mesh import log against your design intent.

---

## 9. Residuals converge but physics is wrong

**Symptom.** Solver reports "solution is converged" with all residuals below tolerance, but numerical results don't match physical expectations.

**Root cause.** Convergence means "residuals stopped decreasing." A case with wrong material, wrong BC, or missing turbulence setting can converge to a wrong steady state.

**Fix.** Always check two sanity metrics post-solve:

1. **Mass balance:** `abs(mflow_inlet + mflow_outlet) < 0.001 * expected_mflow`
2. **One numerical result vs. hand calc:** `mflow_inlet ~= velocity * density * area` (within 1%)

If either fails, the case is running wrong physics regardless of residuals.

---

## 10. `compute()` batch fails on any bad report

**Symptom.** One malformed report definition makes the whole compute() call fail with:
```
Error: CDR: invalid argument [1]: wrong type [not a pair]
```

**Fix.** Compute individually:

```python
results = {}
for name in report_names:
    try:
        r = rd.compute(report_defs=[name])
        results[name] = unwrap(name, r)
    except Exception as e:
        print(f"{name}: {e}")
        results[name] = None
```

---

## 11. `solver.exit()` not called, port leaks

**Symptom.** Fluent process visible in task manager after script exits. Next launch fails with port conflict.

**Fix.** Always use try/finally:

```python
solver = pyfluent.launch_fluent(...)
try:
    # ... work ...
finally:
    solver.exit()
```

Emergency cleanup: `taskkill /F /IM fluent.exe` on Windows.

---

## 12. Deprecated `show_gui` argument

**Symptom.**
```
PyFluentDeprecationWarning: Argument 'show_gui' is deprecated; use 'ui_mode' instead.
```

**Fix.** Use `ui_mode="no_gui"` (or `"hidden_gui"` for offscreen rendering).

---

## Debugging checklist

When a case runs but produces wrong numbers, in order:

1. Print the full BC state: `print(solver.settings.setup.boundary_conditions.velocity_inlet["inlet"]())`
2. Print the cell zone material: `print(solver.settings.setup.cell_zone_conditions.fluid[zone]())`
3. Print the viscous model: `print(solver.settings.setup.models.viscous())`
4. Compute area-averaged inlet velocity — compare to your set BC value
5. Compute inlet area — compare to expected (H * D or equivalent)
6. Check mass balance — should be near zero

If BC value differs from what you set: symptom 2 above.
If area differs by 1000x: symptom 8 above.
If mass flow off by 815x: symptom 1 above.
