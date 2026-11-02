---
name: fl-meshing
description: "Mesh the 27 brake solids in Fluent and gate the mesh."
version: 3.0.0
author: "sdefibaugh"
license: Apache-2.0
platforms: [windows]
metadata:
  hermes:
    tags: [brake, fluent, meshing]
---

# fl-meshing - PMDB to a gated mesh, first part of Gate 3 (PRD H1.2)

Gate 3 is **one commission**: mesh -> internal mesh gate -> setup -> solve ->
post. This skill is the first part. It ends at the internal mesh gate: on PASS
you continue with `fl-thermal-solve` in the **same Fluent session**; on FAIL you
stop without solving and return `mesh_report.json` to the lead.

Solid-only mesh: 27 solid zones, 0 fluid, no inflation, shared topology.

| Reference | Open it when |
|---|---|
| `references/api-verified.md` | before the first use of any PyFluent name (all three fl- skills use it) |
| `references/persistent-session.md` | before step 1; for the host job, step skeleton, polling and relaunch rules |
| `references/run1-lessons.md` | before step 1, once; after any script error |
| `references/task-sequence-and-gui.md` | steps 3 to 8 and 10 (task arguments, framing, pictures) |
| `references/share-topology.md` | step 6, or when pairs come back short |
| `references/coupled-pair-inventory.md` | step 9 (pairs, zone map, split selections) |
| `references/sizing-and-budget.md` | step 4; cells + nodes near 512 000; friction-face resolution |
| `references/failure-modes.md` | any failure: look up the symptom first |

## Rules for every step

- One Fluent launch for the whole of Gate 3 (the host job). A 2nd only with a
  written reason; never a 3rd.
- Every step is a short `run_ansys_script` (20 to 80 lines): connect with
  `connect_to_fluent(server_info_file_name=SI, start_transcript=False)`, do one
  thing, print compact JSON, `s.exit()` (detach). Only volume meshing and the
  solve run as `submit_ansys_job`.
- Compile each script before sending it. Use names from `api-verified.md` only.
- Every check is written `expected / measured / delta / PASS|FAIL`. Missing is
  `null` with a reason, never PASS.
- Same error twice in a step: stop that step, read the error, fix the cause.
  Never a third identical attempt.

`SI` = `C:\brake-runs\<run-id>\30_fluent\session\server_info.txt`.

## Checklist

**0. Start the clock; preconditions (no Fluent).**
Record `timing.started_at`. In one short script: resolve the PMDB **inner
file** (`20_spaceclaim\brake.pmdb\brake.pmdb`; the outer name is a folder),
SHA-256 it, read `tag_report.json` and `00_lead\case.json`, list running
`fluent.exe` / `cx*.exe` / `SpaceClaim.exe`.
Expected: inner file exists; hash = `tag_report.json.pmdb_sha256`; 27 bodies;
27 body selections plus `wall-vent`, `wall-outer`; 0 Ansys processes.
Done when: all rows PASS in `mesh_report.json.preconditions`, with the resolved
path stored as `pmdb_file`.
On miss: hash, body count or file type wrong -> BLOCKED, back to the lead. An
Ansys process you did not start -> stop and ask. Refuse any `.step`.

**1. Launch the host job (the only launch).**
`submit_ansys_job(HOST, job_name="<run-id>_fluent_host", cwd=...\30_fluent)`
per `persistent-session.md` section 1: meshing mode, double, 3D,
`processor_count=4` (the Student limit, "4-way parallel"), `ui_mode="gui"`,
`cleanup_on_exit=False`. Poll `job_status(wait_seconds=60)` until `READY`.
Done when: `READY`, `server_info.txt` and `session.json` exist;
`app_launches = 1`.
On miss: read the job tail and the newest `fluent-*.trn`; one relaunch with a
written reason.

**2. Probe the connection.**
Connect, print `type(s).__name__`, `s.get_fluent_version()` and the task list.
Expected: `Meshing`, 2026 R1.
Done when: the JSON arrives and Fluent is still up after the detach.
On miss: this is the UNVERIFIED part of the pattern. Follow the fallback in
`persistent-session.md` section 5; do not loop.

**3. Initialize Watertight Geometry; import the PMDB.**
`FileName` = the inner file, `LengthUnit` from the tag report (mm on the
predecessor). Print the imported labels.
Expected: 27 body labels (a `geom-1-` prefix is normal; map, never rename),
`wall-vent` and `wall-outer` present.
On miss: upstream defect; stop and report.

**4. Local sizing.** Cheeks 4 mm (2 labels), vanes 5 mm (20), hat 8 mm (1).
Done when: three children exist with label counts 2 / 20 / 1; record the
argument form that took.
On miss: record rejected forms; a missing local size must be reported.

**5. Surface mesh.** Min 2.2 mm, max 20 mm, growth 1.2, curvature 18 deg.
Parse max surface skewness from the newest `30_fluent\fluent-*.trn`.
Expected: <= 0.90 (unparsed = FAIL).
On miss: zone and location to `failure-modes.md`.

**6. Describe Geometry (only solid regions, share topology Yes), then EXECUTE
Apply Share Topology.**
Done when: the task exists in the rebuilt list and executed; transcript shows
shared faces. The real proof is step 9.
On miss: bare "error during task update" -> `share-topology.md`.

**7. Update Boundaries, Update Regions, no boundary layers.**
Expected: 27 regions, all solid, 0 fluid, 0 dead.
On miss: set the type to solid; never delete a region.

**8. Volume mesh as a long job.**
`submit_ansys_job` that connects, runs `Generate the Volume Mesh` with
`poly-hexcore`, writes `30_fluent\brake.msh.h5`, hashes it, calls
`switch_to_solver()`, reads the file back with `file.read_case`, prints zone
counts, detaches. Poll with `wait_seconds=60`; expect 1 to 3 min.
Done when: file > 100 kB, `mesh_sha256` recorded, next connect returns `Solver`
with the same `server_info.txt`.
On miss: inspect the folder before any retry; a lost job once wrote the mesh.

**9. Measure in the solver (2 to 4 short steps).**
Zone inventory and map (confirm by volume); coupled pairs by presence and class;
split selections expanded by prefix; per-zone volumes (`volume-sum` of
`cell-volume`); quality (`tui.mesh.check()`, `tui.mesh.quality()`, parsed
from the transcript); cells and nodes; wall-normal cell size at the four
friction-face sides. Keep at most about 24 report definitions and mutate them.
Expected: see the table below.

**10. Mesh images.** `mesh_full.png` (isometric, all walls) and
`mesh_vent.png` (vanes and the 12 mm gap), delete-then-save, framed.
Done when: both exist with a fresh mtime and the model fills the frame.

**11. Write `mesh_report.json` and run the internal mesh gate.**
Header (`run_id`, `prd_revision` "H1.2", `producing_role`, times, `status`,
upstream hashes), all measurements, `session` (job ids, PIDs, connect count,
`relaunch_reason` or null), `timing`, and `gates[]`. Read it back with
`read_json_file`.
**PASS** (every gate PASS): continue to `fl-thermal-solve`; the session stays
up. **FAIL, OPEN or null on any gate**: HALT rule (two repairs of your own
defects, none of upstream ones), then write the report, create
`session\STOP`, wait for `STOPPED`, count processes, and return to the lead.
Never solve on a failed mesh.

## Numbers this stage must hit (PRD sections 4 and 6)

| Gate | Expected | Tolerance |
|---|---|---|
| Solid / fluid zones | 27 / 0 | exact |
| Coupled pairs, both sides `Coupled` | 45 = 2 cheek/pad + 2 pad/backing + 40 cheek/vane + 1 hat/cheek_in | exact |
| Pad/cheek and pad/backing area, each | 5 864.31 mm^2 | 2 % |
| Cheek/vane area, each | 604.30 mm^2 | 2 % |
| Hat/cheek_in area | 5 969.03 mm^2 | 2 % |
| Hat/vane face pair | none | a pair is FAIL |
| Max surface skewness | <= 0.90 | parsed |
| Volumetric skewness | `null`, "not reported by Fluent 2026 R1"; does not block | |
| Min orthogonal quality | >= 0.10 | |
| Cells with volume <= 0 | 0 | exact |
| Per-zone volume | PRD section 4 (cheek 5.717699e-4, vane 7.251627e-6, hat 5.132043e-4, pad 7.037168e-5, backing 4.398230e-5 m^3) | 2 % |
| Cells + nodes | < 512 000 | strict |
| `wall-vent` / `wall-outer` / pad-backing exposed | 142 865.51 / 228 477.17 / 31 268.67 mm^2 | 2 % |

## Verification

The internal mesh gate is PASS only when `mesh_report.json`, read back from
disk, shows:

| Check | Expected |
|---|---|
| `timing.app_launches` | 1 (2 only with `relaunch_reason`) |
| PMDB hash of the inner file | equals Gate 2 `pmdb_sha256` |
| Every row of the table above | PASS, none `null` without a reason |
| Zone map | 27 PRD names, each confirmed by volume |
| Friction-face wall-normal cell size | measured, 4 sides |
| Images | 2 files, fresh mtime |
| `mesh_sha256` | re-hash matches |
| `timing` | `started_at`, `finished_at`, `tool_calls`, `app_launches` present |

On PASS the session is still running and `fl-thermal-solve` starts at its step
1. On FAIL, owned Fluent processes after `STOPPED` must be 0.
