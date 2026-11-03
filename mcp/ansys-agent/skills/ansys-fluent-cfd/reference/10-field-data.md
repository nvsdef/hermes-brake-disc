# Fluent Field Data Extraction

**Source:** PyFluent fields user guide + API docs.

**Scope:** extracting raw field arrays (velocity, pressure, temperature) from a solved case for custom Python post-processing. Alternative to graphics-based export.

---

## When to use field data (vs. report definitions or graphics)

- **Report definitions** — good for scalar values (mass flow, drag, area-avg pressure)
- **Graphics contours** — good for visualization (PNG output)
- **Field data** — when you need the raw numeric arrays: to compute a custom metric, plot with matplotlib, or feed into ML training data

Every solver and meshing session has:
```python
solver.fields
```

Which contains:
- `fields.field_data` — surface-centric field access
- `fields.solution_variable_data` — zone-centric (advanced, for R/W)
- `fields.reduction` — aggregation operations (min, max, sum, avg)

## Field data — scalar field on a surface

```python
inlet_pressure = solver.fields.field_data.get_scalar_field_data(
    field_name="pressure",
    surfaces=["inlet"],
)
# Returns a dict keyed by surface name, values are numpy arrays of nodal values
```

Example use:
```python
import numpy as np

data = solver.fields.field_data.get_scalar_field_data(
    field_name="pressure",
    surfaces=["inlet"],
)
p_values = data["inlet"]
print(f"Inlet pressure: min={p_values.min():.2f}, max={p_values.max():.2f}, mean={p_values.mean():.2f} Pa")
```

## Field data — vector field on a surface

```python
velocity = solver.fields.field_data.get_vector_field_data(
    field_name="velocity",
    surfaces=["cold-inlet"],
)
# Returns dict of surface_name -> array of shape (N, 3) for (vx, vy, vz)
```

## Available field names

Same set as graphics contours (see `09-graphics.md`):
- `"pressure"`, `"velocity-magnitude"`, `"x-velocity"`, etc.
- `"temperature"` (if energy enabled)
- `"turb-kinetic-energy"`, `"turb-diss-rate"` (if turbulence enabled)
- Discovery via `solver.fields.field_data.get_field_info()`

## Reduction — aggregate over surfaces

Instead of pulling nodal arrays and computing yourself:

```python
red = solver.fields.reduction

# Area-average pressure over inlet
avg_p = red.area_average(expression="AbsolutePressure", surface_names=["inlet"])

# Min velocity over a surface
min_v = red.minimum(expression="VelocityMagnitude", surface_names=["inlet"])

# Max velocity over a surface
max_v = red.maximum(expression="VelocityMagnitude", surface_names=["symmetry"])

# Volume-average pressure over a cell zone
avg_p_vol = red.volume_average(expression="AbsolutePressure", zone_names=["fluid_domain"])
```

Alternatives to `report_definitions` when you want inline computation without creating a persistent report.

## Solution variable data (zone-centric)

For raw cell-by-cell access (advanced):

```python
sv = solver.fields.solution_variable_data
data = sv.get_data(variable_name="SV_P", zone_names=["fluid_domain"])
# Returns cell-indexed array
```

Use for:
- Custom cell-based computations
- Modifying the solution in-place (advanced — read/write)
- Machine learning training data

Not needed for typical workflows.

## FileSession — offline field data access

Read a case+data file without launching Fluent:

```python
from ansys.fluent.core import FileSession

session = FileSession()
session.read_case(case_file_name="case.cas.h5")
session.read_data(data_file_name="case.dat.h5")

# Now use fields interface as if it were a live session
pressure = session.fields.field_data.get_scalar_field_data(
    field_name="pressure",
    surfaces=["inlet"],
)
```

Fast — no Fluent process needed. Good for batch post-processing of many cases.

## Example: extract pressure vs. arc-length along a wall

```python
import numpy as np
import matplotlib.pyplot as plt

# Get vertex coordinates and pressure on the cylinder surface
verts = solver.fields.field_data.get_vertices(surfaces=["cylinder"])
press = solver.fields.field_data.get_scalar_field_data(
    field_name="pressure",
    surfaces=["cylinder"],
)

cylinder_verts = verts["cylinder"]   # (N, 3)
cylinder_p     = press["cylinder"]    # (N,)

# Compute angle from center for each vertex (assumes cylinder axis = Z)
x = cylinder_verts[:, 0] - x_center
y = cylinder_verts[:, 1] - y_center
theta = np.arctan2(y, x)

# Sort by theta
order = np.argsort(theta)
plt.plot(np.degrees(theta[order]), cylinder_p[order])
plt.xlabel("Angle (deg)"); plt.ylabel("Pressure (Pa)")
plt.savefig("cp_curve.png")
```

Use case: pressure coefficient vs. angle, a standard cylinder-flow benchmark.

## Example: velocity profile at outlet

```python
outlet_verts = solver.fields.field_data.get_vertices(surfaces=["outlet"])["outlet"]
outlet_vel = solver.fields.field_data.get_vector_field_data(
    field_name="velocity",
    surfaces=["outlet"],
)["outlet"]

# Sort by Y coordinate for profile
y = outlet_verts[:, 1]
vx = outlet_vel[:, 0]
order = np.argsort(y)

plt.plot(vx[order], y[order])
plt.xlabel("x-velocity (m/s)"); plt.ylabel("Y (m)")
```

## Streaming for large fields

For huge fields (multi-million cell cases), use `field_data_streaming`:
```python
stream = solver.fields.field_data_streaming
for chunk in stream.get_scalar_field_data_chunks(field_name="pressure", surfaces=["walls"]):
    # process chunk-by-chunk
    ...
```

Rarely needed on Ansys Student (512k cell cap).

## For paper reproduction

Papers often report:
- Pressure coefficient (Cp) vs. angle around cylinders
- Velocity profiles at specific stations
- Wall shear stress distributions
- Nusselt number vs. distance

Compute these from field_data:
1. Extract vertices + field values for the surface
2. Compute the geometric coordinate you need (angle, distance)
3. Non-dimensionalize (Cp = (p - p_ref) / (0.5*rho*U^2))
4. Plot vs. the paper's figure

Match:
- Same surface (e.g., cylinder wall, not full domain)
- Same normalization
- Same coordinate convention (angle from stagnation vs. angle from top)
