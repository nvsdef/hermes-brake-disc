# Stage contracts (PRD H1.2)

Flow: **Gate 0 duty cycle (lead) -> Gate 1 CAD (solidworks-engineer) -> Gate 2
geometry prep (spaceclaim-engineer) -> Gate 3 mesh + setup + solve
(fluent-engineer, one commission) -> Gate 4 review and report (lead).** There
are no 2D drawings in H1.2. CAD visuals come from SpaceClaim at Gate 2.

Every artifact carries: `run_id`, `prd_revision` ("H1.2"), `producing_role`,
`started_at`, `finished_at`, `status`, and SHA-256 hashes of its upstream inputs.
JSON numbers carry their unit in the key name, for example `volume_m3` or
`centroid_mm`. Unavailable values are `null`, with a `reason`. Only the **lead**
advances `BUILD_STATE.json`, and only after reading the artifact itself.

Run folder layout: `C:\brake-runs\<run-id>\` with sub-folders `00_lead`, `10_cad`,
`20_spaceclaim`, `30_fluent`, `50_report`.

Every stage report also carries `timing`: `started_at`, `finished_at`,
`tool_calls` (approximate count) and `app_launches` (SolidWorks documents opened,
SpaceClaim or Fluent sessions started). The lead copies these into
`BUILD_STATE.json` so run time can be tracked.

---

## Gate 0 - lead: duty cycle
**Produces:** `00_lead/case.json`. It holds the PRD section 5 table, recomputed
with every input, formula, value and unit; the material table; the numerical
settings; and the list of deferred requirements.

**Passes when** ts = 3.54068 s, E = 243 055.6 J and omega0 = -84.1751 rad/s, each
within 0.1 %.

---

## Gate 1 - solidworks-engineer -> lead: CAD
**Produces in `10_cad/`:**
- `cheek_out.SLDPRT`, `cheek_in.SLDPRT`, `vanes.SLDPRT`, `hat.SLDPRT`,
  `outerpad.SLDPRT`, `innerpad.SLDPRT`, `bp_outer.SLDPRT`, `bp_inner.SLDPRT`,
  `calliper.SLDPRT`
- `brake.SLDASM` with **all 9** components
- `brake.step`
- `cad_report.json`

No drawing sheets and no view PDFs.

**`cad_report.json` must contain:**
- `bodies[]`, 28 rows. Each row has `name`, `part`, `volume_m3`,
  `expected_volume_m3`, `volume_delta_pct`, `centroid_mm`, `expected_centroid_mm`,
  `bbox_mm`, `expected_bbox_mm`, `bbox_method` and `pass`.
- The 20 vanes appear as `vane_01` to `vane_20`, in angular order.
- `assembly`: `component_count` (expected **9**) and the list of component names,
  read back from `analyze_assembly` **before** the STEP export.
- `interference_mm3` (expected 0) with `interference_method`.
- `clearances_mm`, with each PRD section 4 clearance, measured.
- `requirements`, with the measured values for PKG-01 to 05, MAS-01, GEO-01 to 04,
  GEO-06 and PAD-01 to 05.
- `step`: `path`, `sha256`, `manifold_solid_count` (expected **28**),
  `product_count` (expected 10) and `ap_schema`.
- `native_hashes`: SHA-256 of every `.SLDPRT` and `.SLDASM`. These freeze the
  geometry.
- `vane_hand`.

**Passes when** all 28 bodies are within PRD tolerance, the assembly has 9
components, interference is 0, and the STEP holds 28 solids. The lead checks
`step.manifold_solid_count` itself before commissioning Gate 2 (run 1 passed a
23-solid STEP to SpaceClaim because the assembly was missing 5 parts).

---

## Gate 2 - spaceclaim-engineer -> lead: tagged geometry and CAD visuals
**Consumes:** `brake.step` (its hash must match Gate 1) and `cad_report.json`.

**Produces in `20_spaceclaim/`:**
- `brake.pmdb` - **note: the export creates a folder `brake.pmdb\` containing the
  file `brake.pmdb`.** Hash the inner file. Opening the folder as a file gives
  `PermissionError: [Errno 13]` on Windows.
- `tag_report.json`
- `cad_iso.png` (isometric of the full assembly including the calliper, taken
  before the calliper is deleted), `cad_section_9deg.png` (section through the
  vent inlet on a plane at 9 deg: GEO-06 evidence) and `named_selections.png`.

**`tag_report.json` must contain:**
- `step_sha256`, `session`: one SpaceClaim launch, its PID, and the
  number of connect calls made to it.
- `import_scale_check`: measured rotor OD, z extents and total volume vs PRD.
- `body_map`: 28 imported bodies, each identified by measured signature.
- `calliper_match`: exactly one body matching the PRD calliper signature
  (volume AND centroid z = +0.369 AND bbox x max = 200.0).
- `after_delete`: 27 bodies; volume drop equals the calliper volume within 0.5 %.
- `named_selections`: 27 body selections plus `wall-vent` and `wall-outer`, with
  areas and the predicted values.
- `contact_graph`: 45 contacts, each with its measured area.
- `pmdb_sha256` (of the inner file) and `screenshots`.

**Passes when** there are 27 bodies, the calliper is gone, the before-imprint
areas hold within 2 % (wall-vent 167 037.60, wall-outer 240 205.78, pad/backing
42 997.28 mm^2), all 45 contacts are found, and the three screenshots exist and
show the model framed. PMDB cannot be re-opened by pyansys-geometry on 2026 R1;
Fluent's import at Gate 3 is the proof.

---

## Gate 3 - fluent-engineer: mesh, setup and solve (one commission)
The child runs mesh -> **internal mesh gate** -> setup -> solve -> post-process in
one Fluent session. If the mesh gate fails it stops and returns without solving.

**Produces in `30_fluent/`:** `brake.msh.h5`, `mesh_report.json`, case and data
files, `setup_report.json`, `results.json`, `histories/*.csv`, mesh images (full
view and vent close-up) and temperature contours.

**`mesh_report.json`**: zone map; 27 solid / 0 fluid zones; `coupled_pairs[]` (45
rows with areas); max surface skewness, min orthogonal quality, negative-volume
count; cells, nodes and their sum; per-zone volumes; `wall-vent` meshed area vs
142 865.51 mm^2; wall-normal cell size at the friction faces; `mesh_sha256`.

**`setup_report.json`** is a readback: zone materials, motion on the two cheeks
only, the h schedules, the wall layer (grey iron), time step and count, and the
planned applied-energy integral.

**`results.json`** (full schema in `fl-postprocess-energy`):
- `peaks[]`: `rotor_friction_cell_max`, `rotor_friction_wall_layer_max`,
  `pad_friction_cell_max`, `pad_friction_wall_layer_max`, `rotor_all_cell_max`,
  `rotor_all_surface_max`, each with `peak_k`, `peak_time_s`, `end_of_stop_k`.
- `requirements_data` rows for THM-01 to THM-04.
- `rotor_bulk_rise_k`.
- `energy_audit`: `E_applied_j`, `E_stored_j`, `E_conv_j`, `ratio_pct`,
  `residual_j`, `E_applied_over_vehicle_pct`.
- `coverage.covers_full_stop`.

**Passes when** all PRD section 6 mesh gates hold, the energy ratio is 90 to
110 %, applied energy is within +/-2 % of E, and the solve covers the full ts.

---

## Gate 4 - lead: review and report
The lead writes `50_report/review.json`, `review.md` and `report.pdf` (verdict
first). One row per PRD section 7 requirement and DV item: `required`,
`measured` (or null), `unit`, `evidence_file`, `json_key`, `disposition` (PASS,
FAIL, NOT ADJUDICABLE, OPEN or DEFERRED), `rationale`, `owner`, `next_step`. The
report names the **first change** with its quantified expected effect, includes
visuals from every stage (SpaceClaim CAD views, mesh images, contours), the energy
audit, the limitations, the per-stage timing table and `manifest.json`.

The final status is `complete`, `complete_with_findings` or `halted`.
