# STEP export and verification

`brake.step` is the only geometry that leaves SolidWorks. SpaceClaim imports
it, identifies every body by its measured signature, deletes the calliper and
names the rest. Face names never survive STEP, and body names only survive as
PRODUCT names, so the counts and signatures below are the contract.

## 1. Before exporting

- All nine parts passed their own gates (volume, centroid, bbox).
- `analyze_assembly('components')` shows **nine** components, read **before**
  the export (`sw-pads-calliper` step A3), each with transform
  `[1,0,0, 0,1,0, 0,0,1, 0,0,0, 1]`. Run 1 skipped this read and exported 4 of
  9 parts: 23 solids, one repair commission, about 30 minutes lost.
- `brake.SLDASM` is saved.
- The assembly document is active (`activate_document(title='brake')` if not).

## 2. Export

API idiom:

```json
{"format": "STEP", "file_path": "C:\\brake-runs\\<run-id>\\10_cad\\brake.step"}
```

There is no AP-version and no unit argument. `COMPLETED` only means the call
returned. Everything below is the actual check.

## 3. Count what is in the file

Do this with one `execute_code` call. Without that tool, use PowerShell or
`C:/solidpilot/.venv/Scripts/python.exe`. **Never type bare `python`**: it opens
the Windows Store stub. Count **before** `cad_report.json` is written.

API idiom (`execute_code`, one call, all counts and the hash):

```python
import re, hashlib
p = r"C:\brake-runs\<run-id>\10_cad\brake.step"
t = open(p, encoding="latin-1").read()
print(t.count("MANIFOLD_SOLID_BREP"), len(re.findall(r"= ?PRODUCT ?\(", t)))
print(re.search(r"FILE_SCHEMA\s*\(\s*\(\s*'([^']+)'", t).group(1))
print(hashlib.sha256(open(p, "rb").read()).hexdigest())
```

PowerShell equivalents: `(Select-String -Path <p> -Pattern 'MANIFOLD_SOLID_BREP').Count`
and `Get-FileHash <p> -Algorithm SHA256`.

| Check | Pattern | Expected |
|---|---|---|
| Solid bodies | `MANIFOLD_SOLID_BREP` | **25** (one per unique body; the 3 flipped instances share theirs) |
| Products | regex `= ?PRODUCT ?\(` | **7** (6 part files + the assembly) |
| Occurrences | `NEXT_ASSEMBLY_USAGE_OCCURRENCE` | **9** (SpaceClaim expands these to 28 bodies) |
| Schema | the `FILE_SCHEMA` line | record as read; the predecessor got `CONFIG_CONTROL_DESIGN` (AP203) |
| Units | `CONVERSION_BASED_UNIT` or `SI_UNIT` lines | record as read |
| Hash | SHA-256 of the file | goes in `step.sha256` |

Two counting traps the predecessor fell into:

- `grep -c '^#[0-9]*=PRODUCT'` returns **0** on a real file, because the writer
  puts spaces around `=` (`#123 = PRODUCT ( ...`). A pattern that cannot match
  is a gate that always fails open. Use `= ?PRODUCT ?\(`.
- `grep "SI_UNIT ( $, .METRE. )"` matches an **inch** file too: the METRE entity
  is the SI base of the 0.0254 conversion factor. It proves nothing about scale.

The predecessor's STEP was written in an inch unit context
(`CONVERSION_BASED_UNIT('INCH')`) and imported at true scale. Do not try to fix
it. Scale is proven at Gate 2: SpaceClaim measures the rotor OD and z extents.

If the `MANIFOLD_SOLID_BREP` count is not 25 (or occurrences not 9):

| Count | Likely cause |
|---|---|
| 6 | `vanes` exported as one body: the vanes fused or were patterned |
| 24 | the calliper, or one vane, is missing |
| 28 solids, 10 PRODUCT | the inboard parts were built as separate files (allowed only in the old flow) |
| occurrences below 9 | a component (often a flipped instance) was not inserted |
| more than 25 | a part carries an extra body (a failed cut left a fragment) |

Each of these is a CAD defect: find the part, repair it, re-export. Two repairs,
then HALT.

## 4. No re-import in SolidWorks

Do not reopen `brake.step` in SolidWorks. Run 2 (2026-11-02) measured it: with
`brake.SLDASM` open, `open_document` only re-activated the assembly (same title
"brake"); after closing it, SolidWorks imported the STEP as a 9-part assembly,
not a flattened multibody part, and the check cost about 22 calls for no new
evidence. Placement is proven by the per-part centroids (parts are built at
their global position, identity transforms) and, independently, by SpaceClaim's
Gate 2 import, which re-measures all 28 bodies against `cad_report.json`.

## 5. What goes in `cad_report.json`

```json
"step": {
  "path": "C:\\brake-runs\\<run-id>\\10_cad\\brake.step",
  "sha256": "<hex>",
  "manifold_solid_count": 25,
  "occurrence_count": 9,
  "product_count": 7,
  "ap_schema": "<FILE_SCHEMA as read>",
  "unit_context": "<as read>"
}
```

Fill the numbers from the measurement. Never copy these example values.
