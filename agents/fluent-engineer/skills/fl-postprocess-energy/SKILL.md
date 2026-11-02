---
name: fl-postprocess-energy
description: "Extract peaks, energy audit and contours from the solve."
version: 3.0.0
author: "sdefibaugh"
license: Apache-2.0
platforms: [windows]
metadata:
  hermes:
    tags: [brake, fluent, postprocessing, energy]
---

# fl-postprocess-energy - temperatures, energy audit and contours, end of Gate 3 (PRD H1.2)

Used together with `fl-thermal-solve`, in the **same Fluent session**. Step 1
runs before the first time step (inside `fl-thermal-solve` step 10). Step 2
runs inside the solve job. Steps 3 to 9 run after the solve while the data is
in memory, as short steps. Step 10 closes the session and the commission.

API names: only from the verified sheet in the fl-meshing skill,
`agents\fluent-engineer\skills\fl-meshing\references\api-verified.md`.
Session and polling rules: the fl-meshing file `persistent-session.md`.

| Reference | Open it when |
|---|---|
| `references/energy-audit.md` | steps 2 and 7; the ratio looks wrong |
| `references/temperature-semantics.md` | steps 4 and 5; a number looks wrong |
| `references/monitors-and-contours.md` | steps 1, 3 and 8 |
| `references/results-schema.md` | step 9: `results.json` and the history CSVs |

Limits the lead will judge (PRD section 7): THM-01 rotor friction surface
<= 923 K; THM-02 pad friction surface <= 623 K; THM-03 rotor bulk rise <= 60 K;
THM-04 no rotor surface above 1143 K. You publish numbers and flags; the lead
writes dispositions.

## Checklist

**1. Monitors, before the first step (one short step).**
Create 12 report definitions and one report file written every time step with
`flow-time`:

| Monitor | Type | Scope |
|---|---|---|
| `t-cell-max-rotor-fric` | volume-max T | `cheek_out`, `cheek_in` |
| `t-cell-max-pad-fric` | volume-max T | 2 pads |
| `t-cell-max-rotor-all` | volume-max T | 23 rotor zones |
| `t-wall-max-rotor-fric` | surface-facetmax T | 2 rotor-side friction walls |
| `t-wall-max-pad-fric` | surface-facetmax T | 2 pad-side friction walls |
| `t-wall-max-rotor-all` | surface-facetmax T | every rotor wall incl. rotor-side interfaces |
| `t-vavg-iron`, `t-vavg-pad`, `t-vavg-steel` | volume-average T | 3 material groups |
| `t-aavg-vent`, `t-aavg-outer`, `t-aavg-padstack` | surface-areaavg T | 3 convection groups |

Done when: the report file lists all 12 plus flow time, stale `.out` files are
gone, and a compute returns 300 K for every temperature monitor.
On miss: a refused definition returns `None`; that is a failure, not zero.

**2. Energy samples, inside the solve job.**
Sample at t = 0, every window to 0.3 s, every second window after, and the
final window. Each sample: `t_s`, `E_applied_j`, `E_stored_j`, `E_conv_j`,
`ratio_pct`, `max_T_k`, printed with `flush=True` and appended to the progress
JSON. Stored energy uses the three material groups (identity with the per-zone
sum; cross-check once at the end within 1e-6 relative).
Done when: at least 3 early, a regular series and 1 final sample exist.

**3. Histories (no Fluent needed).**
Parse the `.out` file by its **quoted header names**, never by column number.
Write `30_fluent\histories\temperatures.csv`.
Expected: 355 rows after t = 0; last flow time 3.540681 s within 1e-6 s.
Done when: `column_mapping` recorded.

**4. Temporal peaks.**
For each of the six max monitors: `peak_k`, `peak_time_s`, `end_of_stop_k`,
`scope`, `kind` ("cell max" or "wall-layer max").
On miss: a friction peak exactly at ts means the source did not ramp;
investigate before publishing.

**5. Ranges and adjudicability.**
For THM-01, THM-02 and THM-04: range [min, max] of cell max and wall-layer max
peaks; the limit; wall-normal cell size from **this run's**
`mesh_report.json.friction_face_resolution`; penetration depth
`sqrt(alpha x t)` at the peak time and at ts; flags
`range_straddles_limit`, `resolution_coarser_than_penetration`,
`cell_max_exceeds_limit`, `adjudicable`, and `cells_across_at_peak`
(fewer than 5 is a finding).
Done when: each requirement has its numbers and all flags.

**6. Rotor bulk rise.** Volume-weighted over 23 rotor zones: end-of-stop rise
and maximum rise.
Expected: both below the 41.9 K all-energy-in-rotor bound.

**7. Energy audit.** `E_applied`, `E_stored`, `E_conv`, ratio
(E_stored + E_conv) / E_applied, residual in J and %, applied / 243 055.6 J,
and the per-interval check.
Expected: ratio 90 to 110 %; applied within +/-2 %.
On miss: record both numbers; follow HALT.

**8. Contours (short steps, one or two images per step).**
Banded manual range, **all** walls including every `-shadow`, units K, flow
time and range in the caption. At least: rotor outboard friction face and pad
friction face at a planned peak instant AND at end of stop, plus vent
passages. End-of-stop fields are captioned
"end-of-stop field, NOT the peak". Delete each PNG before saving.
Done when: each PNG has a fresh mtime and a row in `results.json.contours[]`.

**9. results.json.** Per `results-schema.md`: header (`prd_revision` "H1.2"),
`upstream_sha256`, `peaks`, `requirements_data`, `rotor_bulk_rise_k`,
`energy_audit`, `coverage.covers_full_stop`, `contours`, `session`
(job ids, connect count, launches) and `timing`. Read it back with
`read_json_file`; every Gate 3 key numeric or `null` with a reason.

**10. Close the session and hand back.**
Create `30_fluent\session\STOP`; poll the host job until `STOPPED`; count owned
`fluent.exe` and `cx*.exe` (expected 0). Record `timing.finished_at`,
`tool_calls` and `app_launches`. Return to the lead: artifact paths, job ids,
every non-PASS row, the adjudicability flags, the limitations, and the timing.

## Traps (details in the references)

- The end-of-stop snapshot is not a peak; peaks come from the per-step history.
- A contour of the final field is not the peak; its caption must say so.
- Volume maximum and surface maximum are different numbers; label both.
- The pad side is found by cp or k; density reads 0.0 with flow off.
- Monitor files and PNGs are never overwritten; delete stale ones first.
- A temperature at exactly the clip limit (commonly 5000 K) is clipping; do not
  report it as a result.
- Do not glob `wall*` for contours and do not drop shadows.

## Verification

| Check | Expected | Tolerance |
|---|---|---|
| Final flow time | 3.540681 s | 1e-6 s |
| History rows after t = 0 | 355 | exact |
| Six peak rows | value, time, end-of-stop, scope, kind | none `null` without reason |
| THM-01, THM-02, THM-04 | range, limit, both flags, `adjudicable` | present |
| Friction-face resolution | from this run's `mesh_report.json` | not a literal |
| Rotor bulk rise | end and max, both < 41.9 K | |
| E_applied / 243 055.6 J | 98 to 102 % | |
| (E_stored + E_conv) / E_applied | 90 to 110 % | |
| Contours | exist, fresh mtime, instant, band, caption, units | |
| `mesh_sha256`, `setup_report_sha256` | match upstream | exact |
| `timing` | `started_at`, `finished_at`, `tool_calls`, `app_launches` | present |
| Owned Fluent processes after `STOPPED` | 0 | exact |

A NOT ADJUDICABLE flag is a finding, not a stage failure. Any FAIL follows the
HALT protocol in `SOUL.md`.
