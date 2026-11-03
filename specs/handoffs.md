# Stage contracts (PRD H1.2, fast run profile)

Flow: **Gate 0 duty cycle (lead) -> Gate 1 CAD, built and assembled once
(solidworks-engineer) -> Gate 2 SpaceClaim prep (spaceclaim-engineer, stage
script `scripts/stages/spaceclaim_prep.py`) -> Gate 3 coarse mesh + short
transient (fluent-engineer, stage script `scripts/stages/fluent_fast.py`) ->
Gate 4 gate summary (lead).** No drawings, no image files, no PDF report.

Every artifact carries: `run_id`, `prd_revision` ("H1.2"), `producing_role`,
`started_at`, `finished_at`, `status`, and `inputs_sha256` (SHA-256 of its
upstream inputs). JSON numbers carry their unit in the key name, for example
`volume_m3` or `centroid_mm`. Unavailable values are `null`, with a `reason`.
Only the **lead** advances `BUILD_STATE.json`, and only after reading the
artifact itself.

Run folder layout: `C:\brake-runs\<run-id>\` with sub-folders `00_lead`,
`10_cad`, `20_spaceclaim`, `30_fluent`.

Every stage report carries `timing`: `started_at`, `finished_at`, `tool_calls`
(approximate, agent stages) or `seconds` and `phase_seconds` (stage scripts),
and `app_launches` (`solidworks_documents`, `spaceclaim_sessions`,
`fluent_sessions`). The lead copies these into `BUILD_STATE.json`.

Measured budget (2026-11-02): Gate 0 about 1 min, Gate 1 about 8 to 13 min
(agentic CAD), Gate 2 about 1 min, Gate 3 about 2 min.

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

No drawing sheets, no view PDFs and no STEP re-import in SolidWorks.

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

## Gate 2 - spaceclaim-engineer -> lead: SpaceClaim prep (stage script)
**Consumes:** `10_cad\brake.step` and `10_cad\cad_report.json`, hashes equal to
Gate 1.

**Runs:** `scripts/stages/spaceclaim_prep.py` once through `submit_ansys_job`
(cwd `20_spaceclaim`), launcher sets `BRAKE_RUN`. One SpaceClaim launch.

**Produces in `20_spaceclaim/`:**
- `brake.pmdb\brake.pmdb` - **the export creates a folder `brake.pmdb\`
  containing the file `brake.pmdb`.** Hash the inner file.
- `tag_report.json`: `inputs_sha256`, `session`, `checks[]` (every gate row),
  `body_map` (28 rows), `calliper_match`, `named_selections` (count, before-imprint
  areas, predicted after-imprint values), `pmdb` {path, bytes, sha256},
  `pmdb_sha256`, `spaceclaim_left_running`, `phase_seconds`, `timing`.

**Passes when** `status` is PASS and every `checks[]` row passes: 28 imported
solids, OD 330 mm, z = -57 to +57 mm, 28-body volume within 1 %; a unique body
map (score <= 1.0 of tolerance); one calliper match; 27 bodies after deletion
with the volume drop equal to the calliper within 0.5 %; 29 named selections;
before-imprint areas within 2 % (wall-vent 167 037.60, wall-outer 240 205.78,
pad/backing 42 997.28 mm^2); the PMDB inner file hash recomputed by the child
equals `pmdb.sha256`; no SpaceClaim process left. The 45 contacts are proven at
Gate 3 by Fluent's coupled-pair count.

---

## Gate 3 - fluent-engineer -> lead: mesh + heat-up solve (stage script)
**Consumes:** `20_spaceclaim\brake.pmdb\brake.pmdb` and `00_lead\case.json`,
hashes equal to Gates 2 and 0.

**Runs:** `scripts/stages/fluent_fast.py` once through `submit_ansys_job` (cwd
`30_fluent`). One Fluent launch, meshing then solver in the same process. Fast
profile settings (PRD section 6A); overrides only through the `FAST_*`
variables, and only when the lead's commission says so.

**Produces in `30_fluent/`:** `brake.msh.h5`, `brake-fast.cas.h5`,
`brake-fast.dat.h5`, `results.json`: `inputs_sha256`, `settings`, `mesh`
(zones, walls, coupled pairs, friction areas, sha256), `checks[]`,
`layer_material_readback`, `convection_walls`, `history[]` (one row per load
window: time, q''', omega, friction-face and bulk maxima, applied and stored
energy), `summary`, `live_contour`, `phase_seconds`, `timing`.

**Passes when** `status` is PASS and every `checks[]` row passes: 27 solid / 0
fluid zones with PRD names; 45 coupled pairs; friction contact areas within 2 %
of 5 864.31 mm^2; meshed volume within 2 % of 2 030 484.53 mm^3; 27 zone
materials and the grey-iron layer read back; applied energy within 2 % of the
closed form; stored / applied 90 to 110 %; stored energy and bulk rotor and pad
maxima rising in every window; friction faces between 300 and 1500 K. On PASS
Fluent is left open with the temperature contour; on FAIL the script closes the
Fluent processes it started.

---

## Gate 4 - lead: gate summary
The lead writes `00_lead\gate_log.md` and the final `BUILD_STATE.json`: every
gate's expected / measured / delta / tolerance / PASS|FAIL rows, the per-stage
timing table, and the Gate 3 `summary` (peak and final friction-face
temperatures, applied and stored energy). Requirements: the CAD rows (PKG-01 to
05, MAS-01, GEO-01 to 04 and 06, PAD-01 to 05) from `cad_report.json`; MAT-01 to
03 from the Gate 3 readback; THM-01 to THM-04 `NOT RUN (fast profile)`;
THM-05 from the convection groups; GEO-05, THM-06, DV-07 to DV-10 DEFERRED;
PKG-06 OPEN. No PDF, no images.

The final status is `complete`, `complete_with_findings` or `halted`.
