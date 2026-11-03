# Launching and Connecting to a Modeler Instance

**Source:** PyAnsys Geometry connection docs + hands-on validation.

**Scope:** how `launch_modeler()` starts a CAD backend (Docker/Geometry Service/Discovery/SpaceClaim), what to expect on Ansys Student, connection lifecycle.

---

## The one-liner

```python
from ansys.geometry.core import launch_modeler
modeler = launch_modeler()
```

Return: a `Modeler` object connected to a CAD backend. Use it to create designs.

## Backend selection order

`launch_modeler()` tries these backends in order:

1. **Docker container** (needs Docker installed + Geometry Service image)
2. **Local Geometry Core Service** (needs standalone Geometry Service install)
3. **Local Geometry DMS Service** (older Discovery service variant)
4. **Ansys SpaceClaim** (fallback — available with any Ansys install)

On **Ansys Student**, only #4 works. The first three attempts fail visibly with WARNING messages, then SpaceClaim launches. Expect 30-60s startup for SpaceClaim to boot its engine.

## Explicit backend selection

Skip the fallback dance:

```python
from ansys.geometry.core import (
    launch_modeler_with_spaceclaim,
    launch_modeler_with_discovery,
    launch_modeler_with_geometry_service,
)

modeler = launch_modeler_with_spaceclaim()   # Ansys Student uses this
```

## Which backend am I on?

```python
print(modeler.client.backend_type)
# BackendType.SPACECLAIM
# BackendType.DISCOVERY
# BackendType.WINDOWS_SERVICE (Geometry Core)
# BackendType.LINUX_SERVICE
```

## Reusing sessions in a design loop

Each launch costs 30-60s. For iterative workflows, reuse ONE session:

```python
modeler = launch_modeler()   # once
try:
    for i, params in enumerate(iterations):
        design = modeler.create_design(f"iter_{i}")
        # ... build, extrude, export ...
        design.close()  # close before next design
finally:
    modeler.close()
```

## Connecting to a remote instance

If someone else runs the CAD service on a remote machine:

```python
from ansys.geometry.core import Modeler

modeler = Modeler(
    host="remote.host.example",
    port=12345,
    transport_mode="mtls",
    certs_dir="path/to/certs",
)
```

## Transport modes

Applicable when running against a remote or containerized backend:

| Mode | When to use |
|---|---|
| `"mtls"` | Default for remote. Requires certificates. |
| `"uds"` | Unix Domain Sockets. Local Linux only. |
| `"wnua"` | Windows Named User Auth. Local Windows only. |
| `"insecure"` | Dev/testing only. Never in production. |

`launch_modeler()` auto-selects sensible defaults for local backends. `Modeler(...)` requires explicit `transport_mode`.

## Cleanup

ALWAYS close explicitly:

```python
modeler.close()
```

Use try/finally:

```python
modeler = launch_modeler()
try:
    # ... work ...
finally:
    modeler.close()
```

**Leaked SpaceClaim processes** hog license slots and RAM. Kill with `taskkill /F /IM SpaceClaim.exe` on Windows if needed.

## Verifying the connection

After `launch_modeler()`:

```python
print(modeler.client.get_geometry_version())   # ansys version
```

## Common failure modes

**"No backend could be started"** — likely you don't have any CAD product installed. Verify `AWP_ROOT<ver>` env var points to Ansys install with SpaceClaim/Discovery.

**License checkout error** — another SpaceClaim/Discovery process holds the license. Kill it or wait for it to release.

**30+ seconds hang** — SpaceClaim boot is slow on Ansys Student. Normal. Wait it out.

**Docker warnings on Ansys Student** — expected. First three backend attempts (Docker/Core/DMS) always fail on Student. SpaceClaim eventually launches.

## Ansys release compatibility

Secure connections (mTLS, UDS, WNUA) require Ansys 24R2 or later. Earlier versions need insecure connections.

Starting 26R1, secure connections work out-of-the-box without service packs.

## For paper reproduction

Papers rarely specify CAD software (they usually give geometry as dimensions in a figure). Use whatever backend your license permits — SpaceClaim on Student, Geometry Service on cloud, etc. The pyansys-geometry API is backend-independent, so the same script works everywhere.
