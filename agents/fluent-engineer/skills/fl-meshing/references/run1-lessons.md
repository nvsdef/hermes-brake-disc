# Run 1 lessons: how the SpaceClaim stage failed, and how Fluent avoids each

Run 1 (FR330V-20260930-1012) never reached Fluent. The Gate 2 stage submitted
about 25 `spaceclaim-gate2_*` jobs between 11:55 and 12:41, each a new 730 to
1 150 line script that launched SpaceClaim, imported the STEP, and died.
Evidence: `C:\brake-runs\_ansys-runtime\jobs\spaceclaim-gate2_*\stderr.log`.
Every failure class below will repeat in Fluent unless the habit changes.

## Failure classes, with counts from the job logs

| # | Class | Run 1 evidence | Jobs lost |
|---|---|---|---|
| 1 | Invented API names | `'BoundingBox' object has no attribute 'min'`; `'NamedSelection' object has no attribute 'entities'`; `'UnitVector3D' object has no attribute 'direction'`; `pint DimensionalityError` from `float()` on an area | 4 |
| 2 | The script's own bookkeeping | `KeyError: 'centroid_mm'`, `'bbox_mm'`, `'imported_index'`, `'bbox_center_mm'`; `TypeError: 'Face' object is not subscriptable` | 5 |
| 3 | A folder opened as a file | `PermissionError: [Errno 13] Permission denied: ...\20_spaceclaim\brake.pmdb` - the export makes a folder `brake.pmdb\` holding the file `brake.pmdb` | 13, in a row |
| 4 | Identification logic that did not converge | "Calliper match not unique: 2 candidates", then "0 candidates" | 2 |
| 5 | Relaunch per attempt | every job printed `Launching SpaceClaim...` and `SpaceClaim closed`; roughly 1 to 2 min of launch and import per attempt | all 25 (the 25th had no exit code when read) |

The worst single fact: the same `PermissionError` at the same line ran 13
times. Nobody read the error between attempts; each retry changed something
else and relaunched.

## How the Fluent stage avoids each class

### 1. Invented API names -> use the verified sheet, probe the rest

- Before the first use of any PyFluent name, find it in `api-verified.md`. Use
  the exact spelling shown there. If it is marked UNVERIFIED, or absent, run a
  probe step first: connect, print `child_names`, `command_names`,
  `get_object_names()` or `allowed_values()`, detach. That costs 15 seconds.
- Remember the v261 renames that look like invented names but are real:
  `heat_generation_rate` (alias `q_dot`), `thermal_condition` (alias
  `thermal_bc`), `run_calculation.parameters.time_step_size` (there is no
  `transient_controls.time_step_size`).
- An `AttributeError` is never fixed by trying a second guess in a long job.
  It is fixed by a probe.

### 2. Own bookkeeping errors -> short steps, compiled first

- Steps are 20 to 80 lines. Dictionaries you build are built and read in the
  same short step; there is no 400-line distance between writing `"volume_m3"`
  and reading `"volume_mm3"`.
- Compile every script before submitting it (`compile(text, "step", "exec")`
  in `execute_code`, or the solidpilot venv's `python.exe -m py_compile`).
- Use `.get(key)` and print what is missing rather than `[key]` for any value
  read from JSON written by another stage. A near-miss key in `case.json` once
  assigned 0 of 27 materials silently.

### 3. The PMDB folder -> resolve the inner file once

- `brake.pmdb` is a folder. The file Fluent imports and the file you hash is
  `20_spaceclaim\brake.pmdb\brake.pmdb`. Resolve it in the precondition step
  (`p / p.name if p.is_dir() else p`), assert `is_file()`, and write the
  resolved path into `mesh_report.json.preconditions.pmdb_file`. Every later
  step reads that path; nobody re-derives it.
- The same trap exists for anything a tool "exports": check `is_file()` before
  `open()`.

### 4. Logic that does not converge -> stop after two repairs

- The HALT rule applies to scripts, not only to gates: the same error twice
  means stop and think; a third attempt at the same step is not allowed. Return
  to the lead with the two error messages.
- Identification in Fluent is by **measurement**: zone volume against PRD
  section 4, pair area against the contacts table, cp or k to find the pad side.
  Never by a name pattern that can match 0 or 2 items.

### 5. Relaunch per attempt -> one persistent session

- One `submit_ansys_job` launches Fluent once and keeps it up
  (`persistent-session.md`). Every step connects, acts, detaches. A failed step
  costs seconds and leaves the session and all earlier work in place.
- Budget: 1 Fluent launch per stage; 2 only with a written reason; never 3.
- Read the error of the step that failed **before** writing the next script.
  Put the error text in `steps.jsonl` so a retry can be compared with it.

## A checklist before any submit

1. Every PyFluent name used is in `api-verified.md`, or was probed this run.
2. The script compiled.
3. Paths are absolute; the PMDB path is the inner file.
4. The script prints compact JSON and ends with `s.exit()` (detach).
5. The step is not a replay of a mutation that may already have happened.
6. This is attempt 1 or 2 of this step, not 3.
