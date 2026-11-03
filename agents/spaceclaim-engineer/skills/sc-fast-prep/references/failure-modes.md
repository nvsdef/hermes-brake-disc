# Failure modes - symptom, cause, action

Open this when something in the stage does not look right. "Upstream" means
the defect belongs to solidworks-engineer: stop the session, and report
expected, measured and delta through the lead. "Mine" means a defect in your
own code or method. A crash of your own step script is fixed and rerun in the
running session (crash budget: 3 per step, 12 per stage); a measured gate miss
gets at most two repairs (HALT protocol).

## Session and transport

| Symptom | Likely cause | Action |
|---|---|---|
| You are about to launch SpaceClaim a second time | a step crashed | Mine. Do not relaunch. Fix the step and rerun it against the running session (`persistent-session.md`). |
| `ValueError: Transport mode must be specified` | `Modeler(host, port)` without `transport_mode` | Mine. `transport_mode="wnua"` from `session.json`. |
| `TimeoutError` or connection refused in a step, holder PID alive | server refuses a second client (UNVERIFIED case) | Use the fallback in `persistent-session.md`; launch #2 with a written reason. |
| Step connects but `read_existing_design` raises "No existing design" | the import step has not run, or SpaceClaim restarted | Check `session.json` and the holder job; run the import step. |
| All named selections and the import gone after a step | the step called `m.close()` or `m.exit()`, which close the design on the server | Mine. Step scripts end with `m.client.close()` only. Restart from the import step. |
| `session.json` state `died`, PID gone | SpaceClaim crashed | Launch #2 with the reason; restart from the import step. A third launch is a HALT. |
| Holder job `failed` before `ready` | error in the holder text | Mine. Read stderr, fix, syntax-check with `compile(...)`, then launch #2 with the reason. |
| `run_ansys_script` returns "Request timed out" | the step took longer than the transport allows | Mine. Check the step's JSON file first: it may have finished. Split the step, or submit it as a job (it still only connects). |
| Files appear in the OneDrive ansys-agent folder | relative paths: `run_ansys_script` runs there | Mine. `os.chdir(STAGE)` and absolute paths; move the files out and record it. |
| `submit_ansys_job` returns `{"error": "cwd does not exist"}` | stage folder not created | Create it in the preflight. |
| Job state `lost` | runner killed or machine restarted | Not proof of failure. Inspect `session.json`, the stage folder and processes first. |
| `job_status` call lost | `wait_seconds` too large | 45 to 50. |
| Launch fails with `10054` or a licence error | another SpaceClaim or Fluent holds the licence | Stop and report the PID from the preflight. Do not kill it. |
| SpaceClaim still running after `STOP` | shutdown failed (logged at debug level only) | Terminate **your** recorded PID only; record it. |

## API names (run 1)

| Symptom | Correct call |
|---|---|
| `'BoundingBox' object has no attribute 'min'` | `.min_corner`, `.max_corner`, `.center` |
| `DimensionalityError ... 'meter ** 2' to 'dimensionless'` | `.m_as("mm**2")`, never `float()` |
| `'NamedSelection' object has no attribute 'entities'` | `ns.bodies`, `ns.faces` |
| `'UnitVector3D' object has no attribute 'direction'` | `face.normal().z` (plain float) |
| `'Face' object is not subscriptable` | keep Face objects and record dicts apart |
| `module 'ansys.geometry.core' has no attribute 'BackendType'` | `from ansys.geometry.core.connection import BackendType` |
| `ImportError: Graphics are required for this method` | `body.tessellate()`/`plot()` need packages that are not installed; use `body.get_raw_tessellation()` |
| `KeyError` on your own dict | one constants block with fixed keys, reused in every step |

## Import and scale

| Symptom | Likely cause | Action |
|---|---|---|
| 0 bodies | `design.bodies` on an assembly STEP | Mine. `design.get_all_bodies()`. |
| 23, 27, 29 or any count but 28 | STEP or assembly incomplete (run 1: 23) | Upstream HALT with the count and the component list. |
| Total volume off by about 1.6e4x or 1e9x | length unit resolved differently | Upstream with all three scale numbers. Never rescale. |
| Total volume off by 0.5 to 5 % | one body is wrong | Identify it in step 5, then upstream. |
| Radius of 215 or 236 mm appears | radius from `face.point()` (uv box, untrimmed) or a stale text | Mine. Radius from tessellation vertices or edges. True maximum 200 mm. |
| Sliver or zero-area face | flush boolean or a mismatched calliper band | Upstream with body, area and location. |
| Bodies named `Cut-Extrude2[n]`, `Boss-Extrude1` | normal (run 1) | Identify by signature, then rename. |

## Identification and calliper

| Symptom | Likely cause | Action |
|---|---|---|
| Calliper candidates 2 or 0 | centroid from the bbox centre (run 1) | Mine. Tessellated mass centroid; volume AND centroid z AND bbox x max. |
| Tessellated volume misses `body.volume` by more than 0.5 % | mixed winding or coarse tessellation | Refine once; else centroid `null`, row OPEN. |
| Hat centroid z +13.5 instead of +18.095 | bbox centre used | Mine. |
| Both cheeks match both rows | volume-only matching | Add bbox z and centroid z. |
| Volume within 1 % but centroid z near 0 | calliper built with a symmetric slot | Upstream finding with both numbers. |
| 28 bodies after "deletion" | `set_suppressed`, or `delete_body` did not find the body | Mine. Delete the re-identified body; re-read; prove by volume. |
| `Resource '0:31/0:38' not found` | a pre-deletion handle or id was used | Mine. Re-read and re-identify in a new step. |
| 28 solid zones in Fluent at Gate 3 | the calliper survived into the PMDB | Rerun this stage. |

## Contacts and faces

| Symptom | Likely cause | Action |
|---|---|---|
| `wall-vent` about 52 684 mm^2 | cheek inner faces treated as contact because vanes touch them (run 1) | Mine. Partial contact is tagged in full. |
| pad/backing about 28 337 mm^2 | backing front faces treated as contact (run 1) | Mine. Same rule. |
| `wall-outer` about 125 852 to 128 836 mm^2 | friction faces treated as contact | Mine. Same rule. |
| `wall-outer` far too high (run 1: 276 316) | full-contact faces leaked in | Mine. Full contact is never tagged. |
| 46 or more contacts | edge-only pairs (overlap exactly zero), or neighbouring vane flanks paired | Strictly positive overlap; same-axis test for cylinders. |
| Hat paired with 20 vanes | hat step face matched on bbox | Radius-range overlap test. |
| Fewer than 45 contacts | real gap or tolerance too tight | `min_distance_between_objects`; a real gap is upstream. |
| `INTERSECT` between two bodies | interference | Upstream. |
| `wall-vent` 16.9 % high against 142 865.51 | before-imprint area compared with the after-imprint value | Compare with 167 037.60. |
| `wall-vent` about 2.4 % high | hat step face in vent | It is `wall-outer` by decision. |
| `wall-outer` includes every rotor face | two `body.faces` reads compared by `id()` | Face ids from one snapshot. |
| Face id from `faces.json` not found | the design changed after the snapshot | Rerun the snapshot step, then the selection step. |
| `create_named_selection` raises `ValueError` | an empty list | The classifier found nothing; check the query. |
| A selection named with `inlet` | renaming | Never. |

## Evidence

| Symptom | Likely cause | Action |
|---|---|---|
| `PermissionError: [Errno 13]` on `brake.pmdb` | the export wrote a folder; the folder was opened as a file (run 1, 13 launches) | Hash the returned inner file. |
| Window capture shows only the top-left part | no `SetProcessDpiAwareness(2)` | Set it before any window query. |
| `open_file` on the PMDB raises | PMDB reading needs 27.1 | Expected. Fluent's import at Gate 3 is the proof. |
