# Launching Fluent Sessions

**Source:** PyFluent launching docs + hands-on validation.

**Scope:** starting Fluent from Python — local install, container, remote connection. Modes, precision, parallel, retry logic for port conflicts.

---

## The basic call

```python
import ansys.fluent.core as pyfluent

solver = pyfluent.launch_fluent(
    product_version="26.1.0",   # matches your Ansys install
    mode="solver",              # or "meshing" or "pre_post"
    ui_mode="no_gui",           # "no_gui" (fastest), "hidden_gui", "gui"
    precision="double",         # "single" or "double"
    dimension=3,                # 2 or 3
    processor_count=2,          # parallel cores
)
```

Return: a session object (Solver or Meshing).

## Modes

| Mode | Purpose |
|---|---|
| `"solver"` | Solve a case with existing mesh; run the CFD simulation |
| `"meshing"` | Mesh imported geometry via watertight/fault-tolerant/2D workflows |
| `"pre_post"` | Post-processing only, no solve capability |

Meshing sessions have `switch_to_solver()`:
```python
meshing = pyfluent.launch_fluent(mode="meshing")
# ... mesh ...
solver = meshing.switch_to_solver()
```

## Product version detection

`product_version="26.1.0"` matches Ansys 2026 R1. Fluent reads the `AWP_ROOT{version}` environment variable:

- 2024 R2 -> `AWP_ROOT242` -> `"24.2.0"`
- 2025 R1 -> `AWP_ROOT251` -> `"25.1.0"`
- 2025 R2 -> `AWP_ROOT252` -> `"25.2.0"`
- 2026 R1 -> `AWP_ROOT261` -> `"26.1.0"`

Verify: `echo $env:AWP_ROOT261` in PowerShell. Should point to your `ANSYS Inc\v261` directory.

## Alternative launcher methods

`launch_fluent()` covers most cases, but PyFluent also exposes cleaner per-mode classes:

**`from_install()`** — auto-detects install:
```python
solver = pyfluent.Solver.from_install(product_version=pyfluent.FluentVersion.v261)
meshing = pyfluent.Meshing.from_install(...)
```

**`from_container()`** — Docker/Podman:
```python
solver = pyfluent.Solver.from_container(container_dict={...}, use_docker_compose=True)
```

**`from_connection()`** — connect to an already-running session:
```python
solver = pyfluent.Solver.from_connection(ip="localhost", port=63084, password="...")
```

## Retry-with-backoff for port conflicts

Fluent's gRPC port occasionally doesn't release before the next launch (see `11-failure-modes.md` #4). Wrap the launcher:

```python
import time
import ansys.fluent.core as pyfluent

def launch_fluent_with_retry(mode, max_retries=3, retry_wait=15, **kwargs):
    defaults = {
        "product_version": "26.1.0",
        "ui_mode": "no_gui",
        "precision": "double",
        "processor_count": 2,
    }
    defaults.update(kwargs)
    defaults["mode"] = mode

    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            return pyfluent.launch_fluent(**defaults)
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                time.sleep(retry_wait)
    raise RuntimeError(f"Fluent launch failed after {max_retries} attempts: {last_err}")
```

Working implementation: `../examples/_launch.py`.

Also add `time.sleep(10)` in orchestrator code between stages that launch new sessions.

## Parallel — local

```python
solver = pyfluent.launch_fluent(
    product_version="26.1.0",
    mode="solver",
    precision="double",
    processor_count=8,
)
```

Ansys Student cap: 16 cores. Fluent Pro: 4. Full license: whatever your license permits.

## Parallel — distributed (multi-machine)

```python
solver = pyfluent.launch_fluent(
    processor_count=16,
    additional_arguments="-cnf=m1:8,m2:8",  # 8 cores on m1, 8 on m2
)
```

## Precision selection

- `precision="single"` — 4 bytes per float. Faster, uses less RAM. OK for most incompressible flows.
- `precision="double"` — 8 bytes per float. Required for high-Mach, low-velocity, or sensitivity-dependent cases.

Default in PyFluent: single. Explicit double is safer for CFD verification runs.

## Dimension selection

- `dimension=2` — 2D solver (planar or axisymmetric). Faster, fewer cells.
- `dimension=3` — 3D solver. Required for any true 3D geometry.

For "2.5D" cases (thin domain with symmetry front/back), use `dimension=3` — Fluent doesn't have a true 2.5D solver.

## Cleanup

Always exit sessions explicitly:

```python
solver.exit()  # or meshing.exit()
```

Use try/finally to guarantee cleanup on exceptions:

```python
solver = pyfluent.launch_fluent(...)
try:
    # ... work ...
finally:
    solver.exit()
```

## Verifying the session

```python
print(solver.get_fluent_version())   # e.g., "Ansys Fluent 2026 R1"
```

Health check:
```python
solver.health_check.check_health()
```

## Connection troubleshooting

**Symptom:** `RuntimeError: No ANSYS version can be found`
**Fix:** `AWP_ROOT<ver>` env var not set. Usually the Ansys installer sets this — verify in a fresh PowerShell. If still missing, set manually:
```powershell
$env:AWP_ROOT261 = "C:\Program Files\ANSYS Inc\ANSYS Student\v261"
```
And add to system env vars for persistence.

**Symptom:** `Connection refused` / `port 60xxx not available`
**Fix:** See `11-failure-modes.md` #4 — port conflict from prior session. Wait 15-30s or use retry helper.

**Symptom:** license error
**Fix:** Check `ANSYSLMD_LICENSE_FILE` env var or Ansys license utility. If using Student, ensure no other Ansys tool is holding the seat.

## For paper reproduction

If a paper uses a specific Fluent version (e.g., 22.2), install that version and pass `product_version="22.2.0"`. Older versions may have different solver defaults (SIMPLE vs. Coupled, different limiter schemes) that materially affect results.
