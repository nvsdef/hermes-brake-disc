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
| Solid bodies | `MANIFOLD_SOLID_BREP` | **28** |
| Products | regex `= ?PRODUCT ?\(` | **10** (9 parts + the assembly) |
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
it. Prove scale by measuring the re-import.

If the `MANIFOLD_SOLID_BREP` count is not 28:

| Count | Likely cause |
|---|---|
| 9 | `vanes` exported as one body: the vanes fused or were patterned |
| 27 | the calliper, or one vane, is missing |
| 8 PRODUCT parts | two parts were merged into one file |
| more than 28 | a part carries an extra body (a failed cut left a fragment) |

Each of these is a CAD defect: find the part, repair it, re-export. Two repairs,
then HALT.

## 4. Re-import and measure

API idiom:

```json
{"file_path": "C:\\brake-runs\\<run-id>\\10_cad\\brake.step"}
```

`open_document` imports a STEP through the classic translator, which **flattens
the assembly into one multibody part**. That is exactly what this check wants.
Then `analyze_model('bodies')` returns one row per body: volume, area,
centroid, face-index range.

Match the 28 rows to PRD section 4 by signature, not by name:

| Signature | Body |
|---|---|
| volume 5.717699e-4 m^3, centroid z = +11.000 mm | cheek_out |
| volume 5.717699e-4 m^3, centroid z = -11.000 mm | cheek_in |
| volume 7.251627e-6 m^3, centroid r = 130.154 mm, z = 0 | a vane; its angle atan2(cy, cx) = 17.917 + (k - 1) x 18 deg gives k |
| volume 5.132043e-4 m^3, centroid z = +18.095 mm | hat |
| volume 7.037168e-5 m^3, centroid z = +22.000 mm | outerpad |
| volume 7.037168e-5 m^3, centroid z = -22.000 mm | innerpad |
| volume 4.398230e-5 m^3, centroid z = +31.000 mm | bp_outer |
| volume 4.398230e-5 m^3, centroid z = -31.000 mm | bp_inner |
| volume 6.170815e-4 m^3, centroid (146.143, 0, +0.369) mm | calliper |

Every body must match within the PRD tolerances (volume 1 %, centroid 0.1 mm).
A body that matches its part-level measurement but not this re-import was moved
by the assembly or the export: report it as a placement defect.

Close the imported document without saving: `close_document(save=false)`. It is
a check, not a deliverable. Do not save it anywhere.

If the import times out, inspect with `verify_state` before retrying. If it
cannot be done, report `step.reimport_check: null` with the reason; the STEP
counts in section 3 still stand, but the row is OPEN, not PASS.

## 5. What goes in `cad_report.json`

```json
"step": {
  "path": "C:\\brake-runs\\<run-id>\\10_cad\\brake.step",
  "sha256": "<hex>",
  "manifold_solid_count": 28,
  "product_count": 10,
  "ap_schema": "<FILE_SCHEMA as read>",
  "unit_context": "<as read>",
  "reimport_check": {"bodies": 28, "all_within_tolerance": true, "max_volume_delta_pct": 0.0, "max_centroid_delta_mm": 0.0}
}
```

Fill the numbers from the measurement. Never copy these example values.
