# Assembly, clearances, interference and `cad_report.json` (PRD H1.2)

This is the tail of Gate 1. The contract is `specs/handoffs.md` Gate 1; the
numbers are PRD section 4 and section 7. The procedure (steps A1 to A8) is in
`SKILL.md`; this sheet holds the reasons, the measurement methods and the
report schema.

## 1. Why the assembly is gated before export (run 1)

Run 1 built and gated all nine parts perfectly, then exported `brake.step` from
an assembly holding only `cheek_out`, `cheek_in`, `vanes` and `hat`. The STEP
held 23 `MANIFOLD_SOLID_BREP`. The report said PASS, SpaceClaim received a
23-solid file, and the lead had to commission a repair (a fresh assembly,
nine inserts, re-export): about 30 minutes lost. Nothing had read the
component count before the export.

So the order is fixed: insert 9 -> `analyze_assembly('components')` shows 9
(A3) -> save -> export -> count 25 solids, 7 products and 9 occurrences in the
file (A7) -> only then write
the report. The lead re-checks `step.manifold_solid_count` itself.

## 2. Assembly checks (A3)

| Check | Expected |
|---|---|
| `component_count` | 9 |
| names | `cheek_out-1`, `cheek_in-1`, `vanes-1`, `hat-1`, `outerpad-1`, `innerpad-1`, `bp_outer-1`, `bp_inner-1`, `calliper-1` (instance numbers may differ) |
| each transform | exactly `[1,0,0, 0,1,0, 0,0,1, 0,0,0, 1]` |
| each `fixed` | true |
| source paths | all in `C:\brake-runs\<run-id>\10_cad\` |

A translation equal to a bbox centre (for example `[..., 0, 0, 0.0135, 1]` on
the hat) means `x, y, z` insertion was used. Delete the component and re-insert
with the identity string.

SolidPilot has no mass-property read for an assembly. The placement spot check
(A4) therefore reads planar faces of three components with
`analyze_assembly('faces', component=...)` and applies the payload transform.
The full proof of placement is SpaceClaim's Gate 2 import: 28 bodies with global
centroids, compared with PRD section 4.

## 3. Clearances (PRD section 4), measured

SolidPilot has no distance tool. Take positions from the A4 faces read (z) and
from the part geometry (radii), subtract, and record both positions and the
difference.

| Key in `clearances_mm` | Measure | Expected |
|---|---|---|
| `pad_stack_to_slot_outboard` | calliper face z = +38.6 minus `bp_outer` top face z = +34 | 4.6 |
| `pad_stack_to_slot_inboard` | `bp_inner` bottom face z = -34 minus calliper face z = -39 | 5.0 |
| `slot_height` | 38.6 - (-39) | 77.6 |
| `pad_stack_height` | 34 - (-34) | 68.0 |
| `slot_minus_stack` | 77.6 - 68.0 (PAD-05 needs >= 4) | 9.6 |
| `rotor_od_to_bridge` | calliper bridge inner cylinder r = 178 minus cheek outer r = 165 | 13.0 |
| `hat_wall_to_calliper_end_wall` | calliper base inner r = 98 minus hat outer wall r at z = +38.6 (86.18) | 11.8 |

The hat wall radius at z = +38.6 comes from the hat cone r = 86 at z = +43 and
r = 88 at z = -6: 86 + (43 - 38.6) / 49 x 2 = 86.18 mm.

## 4. Contact areas (PRD section 4)

| Contact | Measure | Expected mm^2 |
|---|---|---|
| outerpad / cheek_out, innerpad / cheek_in | pad face at z = +/-16 | 5 864.31 each |
| outerpad / bp_outer, innerpad / bp_inner | pad face at z = +/-28 | 5 864.31 each |
| each vane / cheek_out and / cheek_in | vane faces at z = +/-6 (A4 and A8 faces) | 604.30 each, 40 contacts |
| hat / cheek_in | cylinder r = 95, z = -16 to -6 | 5 969.03 |
| hat / vanes | edge only at r = 95, z = -6 | **no face contact** |

These are the 45 thermal interfaces the mesh gate counts (2 + 2 + 40 + 1).

## 5. Interference - by envelope separation

SolidPilot has no interference tool (`analyze_assembly` offers `components`,
`components_flat`, `mates`, `faces`, `edges`). Interference is derived and the
method recorded. A pair passes if the gap is positive, or zero on a shared face
or edge with the bodies on opposite sides.

| Pair | Measured quantity | Expected |
|---|---|---|
| cheek_out / vanes | cheek_out low face z vs vane top faces z | both +6.000: face contact |
| cheek_in / vanes | cheek_in high face z vs vane bottom faces z | both -6.000: face contact |
| cheek_in / hat | cheek_in bore r vs hat max r (z = -16 to -6) | both 95.000: face contact |
| cheek_out / hat | hat outer wall r over z = +6 to +16 (at most 87.51) vs 95 | gap 7.49 |
| vanes / hat | vane inner r = 95 vs hat r for z > -6 (below 88) | edge contact at r = 95, z = -6 only |
| pads / cheeks | pad face z vs cheek outer face z | +/-16.000: face contact |
| pads / plates | pad back z vs plate face z | +/-28.000: face contact |
| pads, plates / hat | pad min r 120, plate min r 115 vs hat max r 95 | gap 20 or more |
| calliper / pad stack | slot faces +38.6 and -39 vs stack +34 and -34; bridges r > 178 vs plate max r 165 | gaps 4.6, 5.0, 13.0 |
| calliper / rotor | bridges r > 178 vs rotor r 165 in the slot band | gap 13.0 |
| calliper / hat | calliper r >= 98 vs hat r <= 86.18 for z >= +38.6 | gap 11.8 |
| cheek_out / cheek_in | z +6 vs -6 | gap 12.0 |

If every row holds, write `"interference_mm3": 0.0` and
`"interference_method": "pairwise envelope separation from measured face z and
radii; SolidPilot has no interference tool"`. If a row cannot be measured,
write `null` with the reason and mark PAD-05 OPEN. SpaceClaim's contact graph
at Gate 2 is an independent second check.

## 6. Requirement values

| ID | Measured value | From |
|---|---|---|
| PKG-01 | rotor OD = 2 x 165.000 (expected 330.0 mm) | cheek geometry |
| PKG-02 | cheek_out top z - cheek_in bottom z (expected 32.0 mm) | A8 faces |
| PKG-03 | hole count 5, diameter 14.0, PCD 115.0 | hat card R8 and hat volume delta |
| PKG-04 | bore diameter 70.0 | hat |
| PKG-05 | mounting face z (expected +43.0) | hat faces |
| MAS-01 | (cheeks + vanes + hat measured volume) x 7200 (expected 12.973 kg) | mass properties |
| GEO-01 | 2 cheeks and 20 vanes present as separate bodies | A8 bodies |
| GEO-02 | each cheek thickness (10.0) | A8 faces |
| GEO-03 | vent gap = cheek_out low face - cheek_in high face (12.0) | A8 faces |
| GEO-04 | vane count (20, curved) | vanes bodies |
| GEO-06 | hat contact cylinder r 95, z -16 to -6; ledge at z = -6, r 88 to 95; inlet gap 7.0 | hat faces |
| PAD-01 | 60 deg | card P1 corners |
| PAD-02 | inner 120.0 and outer 160.0, two keys | card P1 |
| PAD-03 | 12.0 | A8 faces |
| PAD-04 | thickness 6.0, inner 115.0, outer 165.0, three keys | A8 faces, card P2 |
| PAD-05 | slot 77.6, stack 68.0, margin 9.6 (>= 4), interference value and method | sections 3 and 5 |

One number per key. Keep expected and measured as two keys, never one prose
string: run 1 wrote `"120 to 160"` as one value and the reader could not use
it.

## 7. `cad_report.json` layout

```json
{
  "run_id": "<run-id>",
  "prd_revision": "H1.2",
  "producing_role": "solidworks-engineer",
  "started_at": "<iso>", "finished_at": "<iso>",
  "status": "PASS | FAIL | HALTED",
  "inputs_sha256": {"00_lead/case.json": "<sha256>"},
  "timing": {"started_at": "<iso>", "finished_at": "<iso>", "tool_calls": null,
             "app_launches": {"solidworks_documents": null, "solidworks_sessions_started": null},
             "per_part_min": {"cheek_out": null, "vanes": null, "calliper": null, "assembly_and_step": null}},
  "bodies": [
    {"name": "cheek_out", "part": "cheek_out",
     "volume_m3": null, "expected_volume_m3": 5.717699e-4, "volume_delta_pct": null,
     "centroid_mm": [null, null, null], "expected_centroid_mm": [0, 0, 11.000],
     "bbox_mm": {"x": [null, null], "y": [null, null], "z": [null, null]},
     "expected_bbox_mm": {"x": [-165, 165], "y": [-165, 165], "z": [6, 16]},
     "bbox_method": "<how>", "pass": null}
  ],
  "vane_hand": {"theta_at_r95_deg": [-2.3225, 2.2858], "theta_at_r165_deg": [29.8420, 33.4470],
                "rotation_viewed_from_plus_z": "clockwise"},
  "assembly": {"path": "<...\\brake.SLDASM>", "component_count": null, "expected_component_count": 9,
               "components": [], "all_identity": null, "read_before_step_export": true,
               "spot_check": {"cheek_out-1": null, "calliper-1": null}},
  "interference_mm3": null, "interference_method": "<method>",
  "clearances_mm": {"pad_stack_to_slot_outboard": null, "pad_stack_to_slot_inboard": null,
                    "slot_height": null, "pad_stack_height": null, "slot_minus_stack": null,
                    "rotor_od_to_bridge": null, "hat_wall_to_calliper_end_wall": null},
  "contacts_mm2": {},
  "requirements": {"PKG-01": {"measured": null, "unit": "mm", "expected": 330.0, "source": "<key>"}},
  "cad_material": {"all": {"name": null, "reason": "not assigned; mass from PRD density"}},
  "step": {"path": "<path>", "sha256": null, "manifold_solid_count": null, "product_count": null,
           "occurrence_count": null, "ap_schema": null, "unit_context": null},
  "native_hashes": {"cheek_out.SLDPRT": null, "brake.SLDASM": null},
  "limitations": []
}
```

The `null` values are placeholders to be replaced by measurements. A `null`
that stays needs a `reason` beside it, and it makes the status FAIL or HALTED,
never PASS. The 28 body rows are `cheek_out`, `cheek_in`, `vane_01` to
`vane_20` (angular order), `hat`, `outerpad`, `innerpad`, `bp_outer`,
`bp_inner` and `calliper`. The `cheek_in`, `innerpad` and `bp_inner` rows carry
`"source": "flip of <part>"`: centroid and bbox are the source part's measured
values with y and z negated, confirmed by the component transform read back in
A3. `assembly.components` holds the nine names and transforms read back in A3.
`native_hashes` has exactly 7 entries: the 6 part files and `brake.SLDASM`. There are no `views` and no helper assemblies.

`timing.tool_calls` is your running count, which is approximate. Count
`app_launches.solidworks_documents` as 6 parts + 1 assembly = 7. `solidworks_sessions_started` is 1 if `ensure_ready` had to
launch SolidWorks, and 0 if it attached to a running session.

## 8. Handing back Gate 1

Return to the lead, in this order:

1. Status. If halted, give the two numbers that stopped you first.
2. `assembly.component_count` (9) and the STEP counts (28 / 10).
3. A 28-row table: name, volume expected / measured / delta %, centroid delta
   mm, bbox PASS or FAIL.
4. Clearances and interference, with the method.
5. `timing` (started, finished, tool calls), the file list with hashes, and
   every limitation.
