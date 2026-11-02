# results.json and the history files

Open this when writing `results.json`, `setup_report.json` cross-references or
the history CSVs. Key names carry their unit (`_k`, `_s`, `_j`, `_m2`,
`_pct`). Unavailable values are `null` with a sibling `reason`. The header
fields, hash rules and the `timing` block come from `specs/handoffs.md`
(fluent-engineer does not load `brake-handoff` in H1.2).

## results.json - top level

| Key | Content |
|---|---|
| `run_id`, `prd_revision` ("H1.2"), `producing_role` ("fluent-engineer"), `started_at`, `finished_at`, `status` | header |
| `upstream_sha256` | `mesh_sha256`, `setup_report_sha256`, `case_json_sha256`, `pmdb_sha256` (of the inner file `brake.pmdb\brake.pmdb`) |
| `mesh_sha256` | also at the top level (same value): the lead's Gate 3 check reads `results.json.mesh_sha256` |
| `job` | solve `job_id`, `job_name`, `final_state`, `processes_after_exit` |
| `session` | host `job_id`, Fluent PIDs, `connect_count`, `launch_fluent_calls` (1; 2 only with `relaunch_reason`), `relaunch_reason` or null |
| `timing` | `started_at`, `finished_at`, `tool_calls` (approximate), `app_launches` - for the whole Gate 3 commission |
| `fluent` | version string, precision, processor count, transient formulation |
| `settings` | dt, final step, step count, windows, h blocks, iterations per step, residual criterion, cadences |
| `coverage` | `final_flow_time_s`, `ts_s`, `covers_full_stop` (true only if equal within 1e-6 s), `history_rows` |
| `peaks` | six rows, below |
| `requirements_data` | THM-01, THM-02, THM-03, THM-04 rows, below |
| `rotor_bulk_rise_k` | `end_of_stop`, `max_over_stop`, `sanity_bound` 41.9 |
| `energy_audit` | see `energy-audit.md` |
| `friction_face_resolution` | copied from this run's mesh report, plus penetration depths and ratios |
| `wall_layer` | thickness, material, k, source zones, readback path |
| `column_mapping` | monitor name to column index, and how it was found |
| `contours[]` | file, surfaces, `field_instant_s`, `contour_band_k`, `caption`, mtime |
| `histories` | paths and SHA-256 of each CSV |
| `warnings[]`, `gates[]` | every check as expected / measured / delta / tolerance / PASS or FAIL |

## peaks - six rows

| `id` | `kind` | `scope` |
|---|---|---|
| `rotor_friction_cell_max` | cell max | `cheek_out`, `cheek_in` |
| `rotor_friction_wall_layer_max` | wall-layer max | rotor-side friction walls |
| `pad_friction_cell_max` | cell max | 2 pad zones |
| `pad_friction_wall_layer_max` | wall-layer max | pad-side friction walls |
| `rotor_all_cell_max` | cell max | 23 rotor zones |
| `rotor_all_surface_max` | wall facet max | every rotor wall |

Each row: `peak_k`, `peak_time_s`, `end_of_stop_k`, `location_zone`,
`monitor_name`.

## requirements_data - rows for the lead

For THM-01, THM-02 and THM-04:

```
{"id": "THM-02", "limit_k": 623.0,
 "range_k": [cell_max_peak, wall_layer_max_peak],
 "range_peak_times_s": [..., ...],
 "range_straddles_limit": true|false,
 "wall_normal_cell_mm": ..., "penetration_mm_at_peak": ...,
 "cells_across_at_peak": ...,
 "resolution_coarser_than_penetration": true|false,
 "cell_max_exceeds_limit": true|false,
 "adjudicable": true|false, "why": "..."}
```

For THM-03: `limit_k` 60, `measured_k` (maximum bulk rise over the stop),
`end_of_stop_k`.

For THM-05: point to `setup_report.json.convection` (the vent group and its
schedule). For DV-05: point to `energy_audit.E_applied_over_vehicle_pct`.

No `disposition` key. The lead writes dispositions at Gate 4.

## History files in `30_fluent\histories\`

| File | Rows | Columns |
|---|---|---|
| `temperatures.csv` | one per time step, 355 | `step`, `flow_time_s`, the six max monitors in K, the three group volume averages in K, the three convection-group area averages in K |
| `energy.csv` | one per sample, plus the final | `t_s`, `E_applied_j`, `E_stored_j`, `E_conv_j`, `ratio_pct`, `E_stored_iron_j`, `E_stored_pad_j`, `E_stored_steel_j`, `qconv_w` |
| `schedule.csv` | one per window | `window`, `t_start_s`, `t_end_s`, `n_steps`, `dt_s`, `q_w_m3`, `omega_rad_s`, `h_vent`, `h_outer`, `h_padstack` in W/(m^2 K), `readback_verified` |
| `per_interval_energy.csv` | one per sample interval | `t_a_s`, `t_b_s`, `dE_applied_j`, `dE_stored_j`, `dE_conv_j`, `interval_ratio_pct`, `trimmed` |

Hash each file and list it in `results.json.histories`.

## setup_report.json - what the solve stage already wrote

Cross-check that `results.json` agrees with it: `zone_materials` (27 rows of
rho, cp, k readback), `solid_motion` (enabled zones, axis, origin, omega
readbacks, tangential-velocity integral), `friction_pairs` (2 rows with measured
side and area), `wall_layer`, `convection` (3 groups, zone lists, areas, h
schedule, T_inf), `time` (dt, steps, final step, windows), `E_applied_planned_j`,
and the header. A disagreement between the two files is a FAIL you report.

## Before you hand back

1. Read `results.json` back with `read_json_file`.
2. Check every Gate 3 key from `specs/handoffs.md` is present.
3. Check no number was copied from a skill or from a previous run: every value
   has a source in this run's files.
4. List every `null` and every FAIL in your message to the lead.
