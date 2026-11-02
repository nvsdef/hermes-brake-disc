# review.json and review.md - the one verdict source

`specs/handoffs.md` Gate 4 fixes the row fields. This page fixes the rest of the
file so the report can consume it without recomputing anything.

## Top level

```json
{
  "run_id": "FR330V-20261001-0930",
  "prd_revision": "H1.2",
  "producing_role": "lead",
  "started_at": "...", "finished_at": "...",
  "status": "PASS",
  "inputs_sha256": {
    "10_cad/cad_report.json": "<sha>", "20_spaceclaim/tag_report.json": "<sha>",
    "30_fluent/mesh_report.json": "<sha>", "30_fluent/setup_report.json": "<sha>",
    "30_fluent/results.json": "<sha>", "00_lead/case.json": "<sha>"
  },
  "dispositions_allowed": ["PASS", "FAIL", "NOT ADJUDICABLE", "OPEN", "DEFERRED"],
  "roster": ["PKG-01", "...", "THM-06", "DV-01", "...", "DV-10"],
  "headline": { ... },
  "energy_audit": { ... },
  "resolution": [ ... ],
  "rows": [ ... ],
  "derived": { ... },
  "first_change": { ... },
  "recommendations": [ ... ],
  "limitations": [ ... ],
  "coverage": {"expected": 37, "present": 37, "missing": []},
  "deliverables": [ ... ],
  "timing": [ ... ],
  "workflow_status": "complete | complete_with_findings | halted",
  "engineering_verdict": "one sentence"
}
```

## A row (every field from handoffs Gate 4, plus identity)

```json
{
  "id": "THM-02",
  "class": "M",
  "title": "pad friction-surface peak",
  "required": "<= 623 K",
  "measured": {"lower_K": 468.2, "upper_K": 641.7, "lower_time_s": 1.60, "upper_time_s": 0.10},
  "unit": "K",
  "evidence_file": "30_fluent/results.json",
  "json_key": ["peaks[id=pad_friction_cell_max].peak_k", "peaks[id=pad_friction_wall_layer_max].peak_k"],
  "resolution": {"face": "pad side", "wall_normal_cell_mm": 1.90, "in_plane_cell_mm": 3.4,
                 "penetration_depth_mm": 1.374, "cells_across": 0.72,
                 "evidence": "30_fluent/mesh_report.json -> friction_face.pad_wall_normal_mm"},
  "disposition": "NOT ADJUDICABLE",
  "margin_K": null,
  "rationale": "Range straddles 623 K and the pad-side wall-normal cell (1.90 mm) is coarser than the penetration depth (1.374 mm). Energy audit closed (ratio 99.8 %).",
  "owner": "fluent-engineer",
  "next_step": "Refine pad-face wall-normal cell to <= 0.275 mm and re-solve (first_change A)"
}
```

The numbers above are an illustration of the format, not a prediction.

Field rules:

- `measured` is a number, an object (for ranges and multi-part checks), or `null`.
  If `null`, `rationale` says why.
- `json_key` is the exact dotted key (or list of keys) in `evidence_file`.
- `owner` is who acts next: a role name for in-scope rows, "Chassis / Foundation
  Brake" for deferred and open rows.
- `next_step` is concrete ("none" is allowed for a PASS).
- For DEFERRED rows add `"target_phase": "Phase 3"`.
- For DV rows add `"composed_from": ["THM-01", "..."]`.

## headline, energy_audit, resolution, derived

```json
"headline": {
  "governing": "THM-02",
  "pad_range_K": [468.2, 641.7], "rotor_range_K": [410.3, 577.0],
  "sentence": "Single-stop pad temperature is not yet adjudicable against 623 K; rotor passes with margin."
},
"energy_audit": {
  "E_vehicle_J": 243055.56, "E_applied_J": 243120.4, "applied_vs_vehicle_pct": 0.027,
  "E_stored_J": 240710.2, "E_conv_J": 2290.8, "ratio_pct": 99.95, "residual_J": -119.4,
  "convected_fraction_pct": 0.942,
  "keys": {"E_applied_J": "energy_audit.E_applied_j", "...": "..."}
},
"resolution": [
  {"face": "pad", "penetration_depth_mm": 1.374, "wall_normal_cell_mm": 1.90, "cells_across": 0.72},
  {"face": "cheek", "penetration_depth_mm": 7.564, "wall_normal_cell_mm": 1.85, "cells_across": 4.09}
],
"derived": {
  "mas01_agreement_pct": {"value": 0.033, "arithmetic": "(12.9771 - 12.9728) / 12.9728 x 100",
                          "provenance": ["10_cad/cad_report.json -> ...", "30_fluent/setup_report.json -> ..."]},
  "convected_fraction_pct": {"value": 0.942, "arithmetic": "E_conv_J / E_applied_J x 100", "provenance": ["..."]}
}
```

Every number that appears in `review.md` or the report and is not a raw artifact
value lives in `derived` with its arithmetic and provenance.


## deliverables and timing (H1.2)

```json
"deliverables": [
  {"item": "2D drawing", "status": "DESCOPED",
   "rationale": "Descoped by the user in PRD H1.2 section 8 item 5; CAD visuals come from SpaceClaim (cad_iso.png, cad_section_9deg.png, named_selections.png)."},
  {"item": "CAD screenshots", "status": "DELIVERED",
   "files": ["20_spaceclaim/cad_iso.png", "20_spaceclaim/cad_section_9deg.png", "20_spaceclaim/named_selections.png"]}
],
"timing": [
  {"stage": "G1", "owner": "solidworks-engineer", "minutes": 14.8, "tool_calls": 212,
   "app_launches": {"solidworks_documents": 10}, "repairs": 0,
   "source": "BUILD_STATE.json -> timing.G1"},
  {"stage": "total", "minutes": 0.0, "minutes_to_gate2_pass": 31.5}
]
```

`deliverables` status words are `DELIVERED`, `MISSING` or `DESCOPED`. They are
not requirement dispositions and never appear in `rows`. A drawing row inside
`rows`, or a drawing marked MISSING, is a review defect.

## review.md

Render it **from** `review.json` (a short inline script or careful manual
transcription, then a check). Sections, in this order:

1. Verdict (the section 1 block of the SKILL, filled).
2. Requirement table: ID, class, required, measured (ranges as `[a, b]`),
   disposition, evidence key.
3. DV table.
4. Thermal credibility: energy audit, resolution table, range explanation.
5. First change and ranked recommendations.
6. Limitations (from `model-blind-spots.md`, conditional on this run).
7. Deliverables (the 2D drawing listed as DESCOPED) and the per-stage timing
   table.
8. Findings (spec contradictions, package defects, anything a child reported).

After rendering, compare every disposition in `review.md` against `review.json`
(a simple text scan of the table rows). A mismatch is a Gate 4 failure.
