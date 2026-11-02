# Artifact contract - files, fields and the hash chain

This page restates `specs/handoffs.md` in one place, with the reasons. If the two
ever disagree, `specs/handoffs.md` wins; report the difference to the lead.

## 1. Run folder

`C:\brake-runs\<run-id>\` with `00_lead`, `10_cad`, `20_spaceclaim`, `30_fluent`,
`50_report`. There is no `40_drawing` folder in H1.2 (2D drawings are descoped).
Each role writes only into its own stage folder. Nothing
is written inside the OneDrive source folder: sync locks break SolidWorks and
Fluent writes and look like permission errors.

## 2. Common fields in every JSON artifact

```json
{
  "run_id": "FR330V-20261001-0930",
  "prd_revision": "H1.2",
  "producing_role": "spaceclaim-engineer",
  "started_at": "2026-10-01T10:12:40+02:00",
  "finished_at": "2026-10-01T10:19:05+02:00",
  "status": "PASS",
  "inputs_sha256": {
    "10_cad/brake.step": "3f9a...",
    "10_cad/cad_report.json": "b1c0..."
  },
  "timing": {
    "started_at": "2026-10-01T10:12:40+02:00",
    "finished_at": "2026-10-01T10:19:05+02:00",
    "tool_calls": 41,
    "app_launches": {"spaceclaim_sessions": 1}
  }
}
```

`timing` is required in every stage report (`cad_report.json`,
`tag_report.json`, `mesh_report.json`, `results.json`). `tool_calls` is an
approximate count; `app_launches` counts SolidWorks documents opened and
SpaceClaim or Fluent sessions started. The lead copies it into
`BUILD_STATE.json` -> `timing`.

`status` is one of PASS, FAIL, HALTED, BLOCKED. A missing measurement is `null`
with a sibling `"<key>_reason"` (or a `reason` field in the object), and makes the
status FAIL or BLOCKED.

## 3. Per stage (from handoffs.md)

| Gate | Folder | Files | Key JSON content |
|---|---|---|---|
| 0 | `00_lead` | `case.json` | PRD section 5 with formulas, materials, numerics, deferred list |
| 1 | `10_cad` | 9 `.SLDPRT` (cheek_out, cheek_in, vanes, hat, outerpad, innerpad, bp_outer, bp_inner, calliper), `brake.SLDASM` (all 9 components), `brake.step`, `cad_report.json` | `bodies[]` 28 rows with volume, centroid, bbox, expected values, delta, `bbox_method`, pass; `assembly {component_count: 9, components}` read before export; `interference_mm3` with `interference_method`; `clearances_mm`; `requirements`; `step {path, sha256, manifold_solid_count: 28, product_count: 10, ap_schema}`; `native_hashes`; `timing`. No drawings or views |
| 2 | `20_spaceclaim` | `brake.pmdb\brake.pmdb` (a folder holding the file), `tag_report.json`, `cad_iso.png`, `cad_section_9deg.png`, `named_selections.png` | `step_sha256`, `session` (1 launch, PID, connect calls), `import_scale_check`, `body_map`, `calliper_match`, `after_delete`, `named_selections` with before-imprint areas and predictions (wall-vent 167 037.60, wall-outer 240 205.78, pad/backing exposed 42 997.28 mm^2, each 2 %), `contact_graph` (45), `pmdb_sha256` of the inner file, `screenshots`, `timing` |
| 3 | `30_fluent` | one commission: `brake.msh.h5`, `mesh_report.json`, mesh images (full + vent close-up), then `setup_report.json`, case and data, `results.json`, `histories\*.csv`, contours | mesh: zone map, 27 solid / 0 fluid, `coupled_pairs[]` (45 with areas), quality (max surface skewness; volumetric skewness null with reason), cells and nodes, per-zone volumes, after-imprint areas (wall-vent 142 865.51, wall-outer 228 477.17, pad/backing 31 268.67 mm^2, each 2 %), friction-face wall-normal cell size, `mesh_sha256`; the child stops before setup if this internal mesh gate fails. Setup readback; `peaks[]` (cell and wall-layer maxima); bulk rise; `energy_audit`; `timing` |
| 4 | `50_report` | `review.json`, `review.md`, `report.pdf`, `manifest.json` | one row per requirement and DV item; `deliverables` (2D drawing DESCOPED); per-stage `timing` table; verdict first, visuals, energy audit, limitations, manifest |

## 4. The hash chain

Each artifact records the hashes of what it consumed. Reading the chain backwards
from the report proves every number came from the frozen geometry.

```
case.json ---------------------------------------------+
                                                       |
*.SLDPRT, brake.SLDASM --native_hashes--> cad_report.json --step.sha256--+
brake.step ------------------------------------------------------------ |
                                                                        v
                                   tag_report.json.step_sha256 == step.sha256
brake.pmdb\brake.pmdb ----------> tag_report.json.pmdb_sha256   (inner file, not the folder)
                                                                        |
                                   mesh_report.json.inputs_sha256[brake.pmdb\brake.pmdb] == pmdb_sha256
brake.msh.h5 --------------------> mesh_report.json.mesh_sha256
                                                                        |
                                   results.json.mesh_sha256 == mesh_sha256
                                   setup_report.json.inputs_sha256[case.json] == case hash
                                                                        |
                                   review.json.inputs_sha256 (all of the above)
manifest.json: every file of the run with its hash
```

Rules:

- **Gate 1 freezes the geometry.** From then on the 9 part files, the assembly and
  `brake.step` are read-only for everybody. A changed hash is a gate failure, not
  a rebuild.
- **A repair upstream voids everything downstream.** A new `brake.step` means a new
  PMDB, a new mesh and a new solve.
- **Hash on the file you actually used**, after it was written and closed. Hashing
  a file that SolidWorks or Fluent still holds open can give a value that changes
  when the application flushes.

API idiom (PowerShell, lower-case hex):

```
(Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLower()
```

API idiom (Python, in `execute_code` or `C:/solidpilot/.venv/Scripts/python.exe`;
never bare `python`):

```python
import hashlib
h = hashlib.sha256(open(p, "rb").read()).hexdigest()
```

## 5. STEP content checks (read-only text scan)

| Check | Expected | Note |
|---|---|---|
| `MANIFOLD_SOLID_BREP` count | 28 | the vanes part contributes 20; run 1 exported 23 from an assembly missing 5 parts |
| `PRODUCT` entities, pattern `= ?PRODUCT ?\(` | 9 parts + 1 assembly = 10 on the predecessor's SolidWorks export | the pattern `^#[0-9]*=PRODUCT` returns 0 on a real SolidWorks file (it writes `#123 = PRODUCT ( ... )` with spaces) and "passes" by failing to match |
| schema | `ap_schema` recorded as found in `FILE_SCHEMA` | SolidPilot's export has no AP-version argument |
| units | **not** checked by text | see `units-and-scale.md`: scale is proven by measurement at import |
