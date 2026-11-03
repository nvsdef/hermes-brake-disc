# Fluent Solver Settings Object Model

**Source:** PyFluent solver settings user guide + hands-on.

**Scope:** understanding how solver settings are organized (Group/NamedObject/ListObject), reading and writing state, using wildcards, checking metadata like allowed values.

---

## Root of the tree

```python
solver.settings.file        # file operations (read, write)
solver.settings.mesh        # mesh operations (check, adaption, scale)
solver.settings.setup       # physics setup (models, materials, boundary conditions)
solver.settings.solution    # solver methods, initialization, run_calculation, report_definitions
solver.settings.results     # graphics, plots, reports (post-processing)
```

Everything lives under `solver.settings.<major_container>`.

## Three types of settings objects

### 1. Group — static container

Predefined child objects accessible as attributes. Names come from `.child_names`.

```python
models = solver.settings.setup.models
print(models.child_names)  # ['viscous', 'energy', 'multiphase', 'radiation', ...]

# Access as attributes
models.viscous.model = "k-omega"
models.energy.enabled = True
```

Examples of Groups:
- `setup.models`
- `setup.models.viscous`
- `solution.initialization`
- `solution.run_calculation`

### 2. NamedObject — dictionary of dynamically-named children

Contains named entries. Access via index operator. Get list via `get_object_names()`.

```python
bc = solver.settings.setup.boundary_conditions
print(bc.velocity_inlet.get_object_names())  # ['inlet', 'inlet_2']

inlet1 = bc.velocity_inlet["inlet"]           # access by name
inlet1.momentum.velocity_magnitude.value = 0.5

# Create new named entry
bc.velocity_inlet["new_inlet"] = {}
```

Examples of NamedObjects:
- `setup.boundary_conditions.velocity_inlet`
- `setup.cell_zone_conditions.fluid`
- `setup.materials.fluid`
- `solution.report_definitions.force`
- `results.graphics.contour`

### 3. ListObject — ordered list of dynamically-added children

Ordered list of children of the same type. Access via index. Size via `get_size()`.

```python
sources = solver.settings.setup.cell_zone_conditions.fluid["fluid_1"].sources.terms["mass"]
print(sources.get_size())      # 3
first_source = sources[0]      # index by position
```

Less common; usually for source terms and list-like configs.

## Reading state

Call an object as a function to get its full state:

```python
viscous = solver.settings.setup.models.viscous
print(viscous())
# {'model': 'k-omega', 'k_omega_model': 'sst', 'near_wall_treatment': 'standard-wall-fn?', ...}
```

Or use `get_state()`:
```python
print(viscous.get_state())
```

Print in readable form:
```python
viscous.print_state()
```

## Writing state

Assign the child attribute directly:

```python
viscous.model = "laminar"
```

Or use `set_state()` with a dict:
```python
viscous.set_state({"model": "k-omega", "k_omega_model": "sst"})
```

**For unit-aware Real settings (velocity, pressure, temperature), use the `.value` accessor:**

```python
inlet.momentum.velocity_magnitude.value = 0.5  # not: velocity_magnitude = 0.5
```

See `11-failure-modes.md` #2 for why.

## Discovering what's available

**Child names of a Group:**
```python
solver.settings.setup.models.child_names
# ['viscous', 'energy', 'multiphase', 'radiation', 'species', ...]
```

**Named children of a NamedObject:**
```python
solver.settings.setup.boundary_conditions.velocity_inlet.get_object_names()
```

**Active only:**
```python
solver.settings.setup.models.get_active_child_names()
# ['energy', 'multiphase', 'viscous']  # excludes inactive children
```

**Allowed values for a string setting:**
```python
solver.settings.setup.models.viscous.model.allowed_values()
# ['inviscid', 'laminar', 'k-epsilon-standard', 'k-omega-standard',
#  'mixing-length', 'spalart-allmaras', 'k-kl-w', 'transition-sst',
#  'reynolds-stress', 'scale-adaptive-simulation',
#  'detached-eddy-simulation', 'large-eddy-simulation']
```

**Min/max for numeric settings:**
```python
inlet.turbulence.turbulent_intensity.min()   # 0
inlet.turbulence.turbulent_intensity.max()   # 1
```

**Whether a setting is currently active:**
```python
inlet.thermal.temperature.is_active()   # True if energy equation enabled
```

## Wildcards for batch access

Access multiple named objects at once:

```python
from ansys.fluent.core.solver import VelocityInlet

# All velocity inlets matching pattern
inlets = VelocityInlet(settings_source=solver, name="*inlet*")
print(inlets.vmag())
# {'velo-inlet_1': {'vmag': {'option': 'value', 'value': 35}},
#  'velo-inlet_2': {'vmag': {'option': 'value', 'value': 50}}}
```

Wildcards:
- `*` — zero or more characters (`'in*'` matches "in1", "in2")
- `?` — single character (`'gr?y'` matches "grey", "gray")
- `[abc]` — character class
- `^` — negation (`'^*in*'` = NOT containing "in")
- `|` — OR (`'*part*|*solid*'`)
- `&` — AND (`'*part*&*solid*'`)

## Constructor-style syntax (2026 R1+)

Alternative to hierarchy-based access:

```python
from ansys.fluent.core.solver import VelocityInlet, Viscous

inlet1 = VelocityInlet(settings_source=solver_session, name="inlet-1")
inlet1.momentum.velocity_magnitude.value = 0.5

viscous = Viscous(settings_source=solver_session)
viscous.model = "k-omega"
```

Cleaner when the hierarchy would be long. Same functional behavior. Traditional hierarchy still fully supported.

## Exposure levels

Some settings are hidden by default (alpha/beta features):

```python
from ansys.fluent.core import ExposureLevel

solver.settings.set_exposure_level(ExposureLevel.BETA)
solver.settings.set_exposure_level(ExposureLevel.ALPHA)   # shows beta + alpha
```

Only call on `settings` root. Session-scoped (resets between sessions).

## Common access patterns

**All fluid cell zones:**
```python
for zone in solver.settings.setup.cell_zone_conditions.fluid.get_object_names():
    solver.settings.setup.cell_zone_conditions.fluid[zone].general.material = "water-liquid"
```

**Query full case setup:**
```python
solver.settings.setup.print_state()   # everything under setup
```

**Iterate over all named boundaries of a specific type:**
```python
for name in solver.settings.setup.boundary_conditions.wall.get_object_names():
    print(name)
```
