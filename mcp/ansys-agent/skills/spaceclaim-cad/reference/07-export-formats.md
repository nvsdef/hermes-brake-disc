# Export Formats — PMDB vs SCDOCX vs STEP

**Source:** PyAnsys Geometry Design API + hands-on.

**Scope:** which export format to use for Fluent, Mechanical, or interchange with external tools. Named selection persistence matrix. File location handling.

---

## Format comparison

| Format | Extension | Named selections | Best for | Notes |
|---|---|---|---|---|
| **PMDB** | `.pmdb` | Preserved | Fluent (meshing + solver) | Fluent-preferred; smaller than SCDOCX |
| **SCDOCX** | `.scdocx` | Preserved | SpaceClaim GUI, Discovery, Mechanical | Ansys-native |
| **STEP** | `.step` / `.stp` | LOST | Interchange with non-Ansys CAD | Standard neutral format |
| **IGES** | `.iges` / `.igs` | LOST | Legacy interchange | Older; STEP preferred |
| **Parasolid** | `.x_t` | LOST | Native modeling engine format | For direct Parasolid use |

## For CFD workflows: use PMDB

```python
pmdb_path = design.export_to_pmdb()
# Returns absolute path to <design_name>.pmdb in CWD
```

**Why PMDB:**
- Fluent's watertight workflow reads it natively
- Named selections come through as face zones with matching names
- Fluent auto-classifies boundary types by name (see `06-named-selections.md`)
- Fastest export/import combo

## For Mechanical or SpaceClaim GUI review: SCDOCX

```python
scdocx_path = design.export_to_scdocx()
```

Useful for:
- Opening the geometry in SpaceClaim GUI for manual inspection
- Handing off to a Mechanical user for FEA
- Round-tripping edits through the GUI

## For non-Ansys interchange: STEP

```python
step_path = design.export_to_step()
```

Loses named selections. Manual re-tagging required after import into destination CAD.

## Handling the export path

`export_to_pmdb()` and similar write to the CWD by default with the design name as filename. To land in a specific directory:

```python
import shutil
from pathlib import Path

# Export to CWD (returns path)
pmdb_temp = Path(design.export_to_pmdb())

# Move to desired location
target = Path("results") / "my_case" / "geometry.pmdb"
target.parent.mkdir(parents=True, exist_ok=True)
if pmdb_temp.resolve() != target.resolve():
    shutil.move(str(pmdb_temp), str(target))
```

Some newer API versions accept `file_location`:
```python
pmdb_path = design.export_to_pmdb(file_location="results/my_case/geometry.pmdb")
```

Check your pyansys-geometry version.

## Import back into pyansys-geometry

Round-trip: export, then re-import (e.g., for modification):

```python
design = modeler.open_file("existing_geometry.scdocx")
# or
design = modeler.open_file("existing_geometry.pmdb")
```

Named selections and topology are preserved.

## What breaks in STEP conversion

- Named selections (all lost)
- Colors and appearances
- Coordinate systems
- Materials
- Some parametric features

If Fluent is your destination, always use PMDB or SCDOCX.

## What Fluent accepts for import

Fluent's watertight workflow accepts:
- `.pmdb` (best)
- `.scdocx` (works, named selections preserved)
- `.step` / `.stp` (loses names, need manual re-tagging)
- `.iges` (loses names)
- `.x_t` (Parasolid; loses names)

## Verifying export succeeded

```python
from pathlib import Path
p = Path(design.export_to_pmdb())
assert p.exists() and p.stat().st_size > 1000
print(f"PMDB: {p} ({p.stat().st_size} bytes)")
```

Empty or tiny files usually indicate an export failure — check the modeler session is still alive and the design has bodies.

## Round-trip strategy for design loop

For iterative geometry modification (e.g., change a dimension, re-run CFD):

```python
# Option A: rebuild from scratch each iteration (deterministic)
for iteration in iterations:
    design = modeler.create_design(f"iter_{iteration.id}")
    # ... rebuild geometry from parameters ...
    design.export_to_pmdb()
    design.close()

# Option B: mutate one persistent design (faster but risks state accumulation)
design = modeler.create_design("base")
for iteration in iterations:
    # ... modify body via body.translate(), body.scale(), etc. ...
    design.export_to_pmdb()
```

Option A is preferred for reproducibility. Option B may be faster if you're doing tight parametric sweeps.

## For paper reproduction

Reproducing a paper's geometry means:
1. Build parametric geometry matching the paper's dimensions
2. Export to PMDB
3. Fluent meshes and solves
4. Compare results

If the paper's geometry is complex and you want to verify visually against the paper's figures, also export SCDOCX and open in SpaceClaim GUI before running Fluent.

If the paper provides its geometry as a STEP or Parasolid file, import it via `modeler.open_file(...)`. You'll lose their named selections (if any) and need to re-tag boundaries yourself.
