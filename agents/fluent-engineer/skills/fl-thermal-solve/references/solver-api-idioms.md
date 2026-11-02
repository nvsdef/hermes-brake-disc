# PyFluent solver idioms, cost rules and job handling

Open this when writing any solver settings call, when a readback returns nothing
useful, or when planning how long the stage will take. These are short idioms,
not a script. Settings paths move between releases: before setting an unfamiliar
object, print `obj.get_state()`, `obj.child_names` or `obj.allowed_values()`
and adapt. The official reference is https://fluent.docs.pyansys.com/ and the
ansys-agent server ships sheets you can read with
`read_skill_reference(skill="ansys-fluent-cfd", sheet_name=...)`: 03 settings
model, 04 physics models, 05 materials, 06 boundary conditions, 07 solver
methods, 08 report definitions, 10 field data, 11 failure modes.

**H1.2: the verified sheet wins.** The spellings in the fl-meshing API sheet
(`agents\fluent-engineer\skills\fl-meshing\references\api-verified.md`) were
checked against the installed ansys-fluent-core 0.41.0 source and the v261
settings classes. Where this file differs, follow the sheet.

## Connect (no launch in this skill)

The solver is the same Fluent process that meshed: `fl-meshing` step 8 called
`switch_to_solver()` and read `brake.msh.h5` back. Every setup step connects
to it and detaches; nothing launches.

API idiom (SRC):
```python
import ansys.fluent.core as pyfluent
solver = pyfluent.connect_to_fluent(server_info_file_name=SI, start_transcript=False)
assert type(solver).__name__ == "Solver"
...
solver.exit()      # detach only (connect default cleanup_on_exit=False)
```
`AWP_ROOT261` is set by the Hermes `ansys` server environment.

## Models

API idiom:
```python
s = solver.settings
s.setup.general.solver.time = "unsteady-2nd-order-bounded"   # or unsteady-1st-order
s.setup.models.energy = {"enabled": True}
solver.tui.solve.set.equations("flow", "no")                 # add turbulence "no" if listed
print(s.setup.general.solver.time(), s.setup.models.energy(), flush=True)
```
Read back after setting. `equations` takes pairs of (equation, yes/no); if the
installed version lists a turbulence equation, turn it off in the same call.

## Materials: define, then assign, then read back

API idiom:
```python
mats = s.setup.materials.solid
mats.create("grey-iron")                      # or mats["grey-iron"] = {} on some versions
mats["grey-iron"] = {"density": {"option": "constant", "value": 7200.0},
                     "specific_heat": {"option": "constant", "value": 447.0},
                     "thermal_conductivity": {"option": "constant", "value": 52.0}}
s.setup.cell_zone_conditions.solid["cheek_out"].material = "grey-iron"
```
On some versions the zone material sits under `.general.material`. Read back the
zone's material name, then the material's three properties. A material in the
library is not an assignment: the ansys-agent failure sheet records a case where
a fluid silently stayed air because only the copy step was done.

## Solid motion

API idiom:
```python
czc = s.setup.cell_zone_conditions.solid
czc["cheek_out"] = {"solid_motion": {
    "enable": True, "solid_omega": omega_w,
    "solid_motion_axis_direction": [0, 0, 1],
    "solid_motion_axis_origin": [0, 0, 0],
    "solid_motion_velocity": [0, 0, 0],
    "solid_relative_to_thread": "absolute",
    "solid_motion_zone_motion_function": "none"}}
state = czc["cheek_out"].solid_motion.get_state()
```
For the 25 other zones set `{"solid_motion": {"enable": False}}` and read back.

## Boundary conditions

See `wall-layer-and-convection.md` for the source and convection idioms. Some
scalar settings persist only when set with `.value = x` rather than direct
assignment (ansys-agent failure sheet item 2). If a readback shows the old value,
use the `.value` form and read again.

## Time stepping

API idiom:
```python
rc = s.solution.run_calculation
rc.parameters.time_step_size = 0.01              # v261 path (RUN)
rc.dual_time_iterate(time_step_count=n_steps_in_window, max_iter_per_step=5)
```
`rc.transient_controls.time_step_size` does **not** exist in v261 (it is not
a child of `transient_controls`); do not wrap it in a try as a first attempt.
For the final window set the step size to 0.000681 s, read it back with
`rc.parameters.time_step_size()`, and iterate one step. Store
`rc.parameters.get_state()`.

Residual criterion (path varies; verify):
```python
s.solution.monitor.residual.equations["energy"].absolute_criteria = 1e-8
```

Initialize:
```python
s.solution.initialization.defaults["temperature"] = 300.0
s.solution.initialization.initialization_type = "standard"
s.solution.initialization.standard_initialize()
```
Then check with a volume-average report that every zone reads 300 K.

## Report definitions: pool them

Creating a report definition is O(n^2) in a session: about 9 s each at 50,
about 25 s each at 200. **Computing** one that already exists is cheap. So
create one definition per (report type, field) and change its zone or surface
list for each measurement. Cap the session at about 24 definitions including
the permanent monitors. The predecessor's stage 5 used 15 pooled plus 4
monitors. A refused definition returns `None`, and later measurements go missing
rather than to zero: treat any refusal as a failure.

API idiom - pooled volume report:
```python
rv = s.solution.report_definitions.volume
rv["rp-vavg-T"] = {}; rv["rp-vavg-T"].report_type = "volume-average"
rv["rp-vavg-T"] = {"field": "temperature", "cell_zones": zones}
out = s.solution.report_definitions.compute(report_defs=["rp-vavg-T"])
```
Report types by kind: volume reports take `cell_zones`; surface reports take
`surface_names`; flux reports take `boundaries`. Validate the return shape and
unit every time.

## Round trips cost wall-clock time

Each settings call through PyFluent is a round trip. The predecessor measured
about 2.5 s per round trip on its transport. Its first solve stage took 4 h 33 min
against a 45 min budget: 71 windows x (62 settings calls + 31 sample calls).
58.9 % of the stage was re-applying convection on 29 walls every window. After
the fixes (h every 25 steps, one call per wall, 10-step windows, energy summed
over 3 material groups instead of 27 zones, a lighter sampling cadence), the
next run projected 812 round trips and measured 812, and finished the stage in
795 s.

**Price the loop before you run it**, and print the projection before step 1:

```
windows x (friction walls + cheeks)            load and motion
h blocks x convection walls                    convection
samples x reports per sample                   energy and temperature samples
graphics refreshes x calls per refresh         live contour
verified windows x readback calls              readbacks (never cut these)
```

Count every bucket, not only the one you just optimised. The predecessor's first
estimate counted only the settings calls and missed the sample calls in the same
loop.

Material-group energy sums are an identity, not an approximation: within one
material, rho and cp are constant and volume-average is volume-weighted, so
`sum over zones rho cp V_z (T_z - T0) = rho cp V_group (Tavg_group - T0)`.
Check the group is homogeneous, and cross-check once at the end against a
per-zone sum (1e-6 relative).

## Detached job handling

- The solve job **connects** to the running session (no launch). Submit with
  `submit_ansys_job(script_text=..., job_name="<run-id>_solve",
  cwd=r"C:\brake-runs\<run-id>\30_fluent")`. Record the returned `job_id` and
  `job_dir`. Send no other step while it runs: one client at a time.
- Wait with the 240 s wait script from the fl-meshing file
  `persistent-session.md` (one turn per 4 minutes), or with
  `job_status(job_id, tail_lines=12, wait_seconds=60)`; the server clamps the
  wait at 60 s. States: `running`, `succeeded`, `failed`, `cancelled` (exit
  code -15), `lost`.
- The job's stdout is a file. `print(..., flush=True)` or the tail stays empty.
  Print one line per window: window number, flow time, q'''_w, omega_w, max T,
  stored/applied ratio, elapsed seconds.
- Read the whole log with `job_log(job_id, stream="stdout")` and the errors with
  `stream="stderr"`.
- `job_cancel(job_id)` kills the runner and child trees. Fluent can survive it.
  Count Fluent processes afterwards.
- After any timeout or `lost`: inspect the folder and the progress file first.
  Never start a second solve because the client stopped waiting.
- Read JSON outputs with `read_json_file(file_path)`. `list_case_results
  (results_root=r"C:\brake-runs\<run-id>")` lists the stage sub-folders and
  finds a `results.json` in each. Always pass `results_root`: its default root
  is the server's runtime folder, not the run folder.

## Leaving the session clean

In H1.2 a step's `solver.exit()` only detaches; Fluent keeps running for the
next step. Fluent is ended once, at the end of the commission, by creating
`30_fluent\session\STOP`: the host job then calls
`application_runtime.exit()` and reports surviving PIDs. After `STOPPED`,
count the `fluent.exe` and `cx*.exe` processes you launched. The predecessor recorded one
of each still running after a clean exit, holding the Student licence, and the
next launch failed with `10054`. Reap only processes you started (match by the
PID or start time you recorded) and record the before and after counts.
