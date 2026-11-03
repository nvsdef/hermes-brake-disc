# Verified PyFluent 0.41.0 API sheet (used by scripts/stages/fluent_fast.py; read it to diagnose a failure)

Open this **before the first use of any PyFluent name** in a script. Run 1 lost
an hour in SpaceClaim to invented attribute names (`bounding_box.min`,
`NamedSelection.entities`, `UnitVector3D.direction`). Every name below was read
in the installed source, and most also ran on this machine. If a name you need
is not here, probe it first (section 11); never guess it inside a long script.

Labels used on every row:

- **SRC** - read in the installed source: `ansys-agent\.venv\Lib\site-packages\ansys\fluent\core`,
  ansys-fluent-core **0.41.0**, generated settings `generated\solver\settings_261.py`.
- **RUN** - also executed successfully on this workstation (Fluent 2026 R1
  Student, v261) by the predecessor's mesh and solve scripts.
- **UNVERIFIED** - plausible, not proven. Probe it once with a short script, or
  do not depend on it.

## 1. Machine facts

| Fact | Value | Label |
|---|---|---|
| Fluent | 2026 R1 Student, `AWP_ROOT261 = C:\Program Files\ANSYS Inc\ANSYS Student\v261` (set in the Hermes `ansys` server env) | RUN |
| Processor limit | transcript line "Your license enables 4-way parallel execution". A 4-process run showed nodes n0 to n3 on a 16-core CPU. **Use `processor_count=4`**; more is refused or ignored | RUN |
| Student mesh cap | cells + nodes < 512 000 (PRD section 6). Predecessor mesh: 73 065 cells + 405 411 nodes = 478 476 | RUN |
| `job_status(wait_seconds=...)` | server clamps to **60 s** (`min(wait_seconds, 60)`) | SRC |
| Hermes `ansys` MCP timeout | `timeout: 300` s in `profile/config.template.yaml` | SRC (config), UNVERIFIED in practice |
| `run_ansys_script` working directory | the **ansys-agent source folder in OneDrive** (`cwd=PROJECT_ROOT` in the server), not `C:\brake-runs`. Write nothing relative; use absolute paths | SRC |
| Every `run_ansys_script` / `submit_ansys_job` | a **new** Python process with the ansys-agent venv | SRC |
| Predecessor timings (4 processes) | mesh stage 139 s of meshing; solve 673 s; whole solve stage 795 s | RUN |

## 2. launch_fluent (one call per stage)

Signature (keyword-only), SRC: `launch_fluent(*, product_version=None,
dimension=3, precision="double", processor_count=None, journal_file_names=None,
start_timeout=None, additional_arguments="", env=None, cleanup_on_exit=True,
start_transcript=True, ui_mode=None, graphics_driver=None, case_file_name=None,
mode="solver", cwd=None, start_watchdog=None, ...)`.

API idiom (SRC; the same call without `cleanup_on_exit`/`product_version` is RUN):
```python
import ansys.fluent.core as pyfluent
m = pyfluent.launch_fluent(mode="meshing", precision="double", dimension=3,
        processor_count=4, ui_mode="gui", cwd=fluent_dir,
        product_version="26.1.0", cleanup_on_exit=False,
        start_transcript=False, start_timeout=300)
```

- `ui_mode` values: `"gui"`, `"hidden_gui"`, `"no_gui"`, `"no_graphics"`,
  `"no_gui_or_graphics"` (SRC). `show_gui=` is a deprecated alias converted to
  `ui_mode` (SRC). Use `ui_mode="gui"` (RUN).
- `product_version` accepts `"26.1.0"`, `26.1` or `261` (SRC).
- `start_timeout` default is 100 s (SRC). 300 s gives the GUI room to start.
- `cleanup_on_exit=False`: no watchdog is started and the temporary server-info
  file is **not** deleted (SRC). `session.exit()` then only closes this client.
- `cwd` is the Fluent process working directory. Fluent writes its
  `fluent-*.trn` transcript and `cleanup-fluent-<HOST>-<PID>.bat` there (RUN).
- `mode="meshing"` returns a `Meshing` object; `mode="solver"` a `Solver` (SRC).

## 3. The server-info file (how later scripts find the session)

`launch_fluent` always writes its own server-info file to `%TEMP%` via
`-sifile=`; there is no argument to choose the path (SRC). The env var
`SERVER_INFO_DIR` changes the directory but passes Fluent only a **relative**
name, so do not use it (SRC). Write your own file from the connection
properties. Format read by `connect_to_fluent`: line 1 `ip:port`, line 2
password (SRC, `session._parse_server_info_file`).

API idiom (SRC):
```python
cp = m.connection_properties        # ip, port, password, cortex_pwd, cortex_pid, fluent_host_pid
assert cp.ip and cp.port and cp.password
(session_dir / "server_info.txt").write_text(f"{cp.ip}:{cp.port}\n{cp.password}\n")
```

## 4. connect_to_fluent (every short step and every long job)

Signature, SRC: `connect_to_fluent(*, ip=None, port=None, address=None,
cleanup_on_exit=False, start_transcript=True, server_info_file_name=None,
password=None, allow_remote_host=False, ...)`.

- It detects the running mode itself and returns `Meshing` or `Solver`
  (`_get_running_session_mode` asks the server) (SRC).
- On Windows a local connection uses the `wnua` transport, no certificates (SRC).
- **Default `cleanup_on_exit=False`**: `s.exit()` closes the channel and leaves
  Fluent running. Only `cleanup_on_exit=True` sends `exit_server` (SRC,
  `FluentConnection._exit`). Never pass `cleanup_on_exit=True` in a step script.
- Pass `start_transcript=False` in short steps so the transcript does not flood
  the JSON you print. Long jobs may keep it `True` for progress lines.

API idiom (SRC):
```python
s = pyfluent.connect_to_fluent(server_info_file_name=SI, start_transcript=False)
kind = type(s).__name__             # "Meshing" or "Solver"
...
s.exit()                            # detach only; Fluent stays up
```

To end Fluent deliberately: `s.application_runtime.exit()` (SRC; public
attribute on every session). If processes survive, `s.force_exit()` runs the
cleanup script and loses unsaved data (SRC). Neither is RUN yet.

## 5. switch_to_solver keeps the same server-info file

`Meshing.switch_to_solver()` calls `tui.switch_to_solution_mode("yes")` and
returns `Solver(fluent_connection=self._fluent_connection, ...)`: the **same**
connection object, so the same ip, port and password (SRC). The meshing object
is dead afterwards (its `_fluent_connection` is `None`). The same Fluent
process continues (RUN: one process, one transcript). Therefore the file written
in section 3 stays valid, and the next `connect_to_fluent` returns a `Solver`.
Proof at runtime: the first post-switch connect prints `kind == "Solver"`.

## 6. Watertight meshing, task-object style (RUN on 2026 R1)

```python
wf = m.workflow
wf.InitializeWorkflow(WorkflowType="Watertight Geometry")
imp = wf.TaskObject["Import Geometry"]
imp.Arguments.set_state({"FileName": pmdb_inner, "LengthUnit": "mm", "AppendMesh": False})
imp.Execute()
print(list(wf.TaskObject.get_object_names()))
```
`pmdb_inner` is the **file** `...\20_spaceclaim\brake.pmdb\brake.pmdb`, never
the folder (section 10). Task names measured after Describe Geometry (RUN):
`Import Geometry`, `Add Local Sizing`, `Generate the Surface Mesh`,
`Describe Geometry`, `Apply Share Topology`, `Enclose Fluid Regions (Capping)`,
`Update Boundaries`, `Create Regions`, `Update Regions`, `Add Boundary Layers`,
`Generate the Volume Mesh`, plus one child per local size.

| Task | Arguments that ran (RUN) |
|---|---|
| Add Local Sizing | `{"AddChild": "yes", "BOIControlName": name, "BOIExecution": "Body Size", "BOISize": 4.0, "BOIZoneorLabel": "label", "BOIFaceLabelList": labels}` then `AddChildAndUpdate()` |
| Generate the Surface Mesh | `{"CFDSurfaceMeshControls": {"MinSize": 2.2, "MaxSize": 20.0, "GrowthRate": 1.2, "CurvatureNormalAngle": 18}}` then `Execute()` |
| Describe Geometry | `{"SetupType": "The geometry consists of only solid regions", "InvokeShareTopology": "Yes"}`, then `UpdateChildTasks(SetupTypeChanged=True)`, `Execute()` |
| Apply Share Topology | `Execute()` (must be run explicitly) |
| Add Boundary Layers | `{"AddChild": "no"}` then `Execute()` |
| Generate the Volume Mesh | `{"VolumeFill": "poly-hexcore"}` then `Execute()` |
| Write | `m.meshing.File.WriteMesh(FileName=mesh_path)` |

The workflow state lives in the Fluent server, so a later `connect_to_fluent`
sees the same `TaskObject` list (SRC by design of the datamodel proxy;
UNVERIFIED across clients on this machine - the step 2 probe proves it).
`m.watertight_workflow()` (new-style API, 26R1+) exists (SRC) but was never
run here: do not mix the two styles.

Meshing-session graphics that worked (RUN): `m.tui.display.all_grid()`,
`m.tui.display.update_scene.draw_frame("yes")`. `m.tui.views` does not exist in
meshing (RUN failure).

## 7. Solver settings paths (settings_261, SRC; RUN where marked)

| Purpose | Path and form |
|---|---|
| Read mesh | `s.settings.file.read_case(file_name=mesh_path)` (RUN on `.msh.h5`) |
| Transient | `s.settings.setup.general.solver.time = "unsteady-2nd-order-bounded"` (allowed: `steady`, `transient`, `unsteady-1st-order`, `unsteady-2nd-order`, `unsteady-2nd-order-bounded`) (RUN) |
| Energy | `s.settings.setup.models.energy = {"enabled": True}` (RUN) |
| Flow off | `s.tui.solve.set.equations("flow", "no", "kw", "no")` (RUN). Settings form `s.settings.solution.controls.equations["flow"] = False` is SRC, key name UNVERIFIED |
| Material | `mats = s.settings.setup.materials.solid; mats.create(name)`; `mats[name] = {"density": {"option": "constant", "value": 7200.0}, "specific_heat": {...}, "thermal_conductivity": {...}}` (RUN) |
| Zone material | `s.settings.setup.cell_zone_conditions.solid[z].material = name` (RUN; alias of `general.material`) ; readback `...solid[z].material()` (RUN) |
| Solid motion | `solid[z] = {"solid_motion": {"enable": True, "solid_omega": w, "solid_motion_axis_direction": [0, 0, 1], "solid_motion_axis_origin": [0, 0, 0], "solid_motion_velocity": [0, 0, 0], "solid_relative_to_thread": "absolute", "solid_motion_zone_motion_function": "none"}}` (RUN; readback `solid[z].solid_motion.get_state()["solid_omega"]` gave -82.986 rad/s) |
| Wall thermal children | `thermal_condition` (alias `thermal_bc`; values `Temperature`, `Heat Flux`, `Convection`, `Coupled`, ...), `material`, `heat_transfer_coeff` (alias `h`), `free_stream_temp` (alias `tinf`), `wall_thickness` (alias `d`), `heat_generation_rate` (alias `q_dot`) (SRC) |
| Convection | `s.settings.setup.boundary_conditions.wall[w] = {"thermal": {"thermal_bc": "Convection", "heat_transfer_coeff": {"value": h}, "free_stream_temp": {"value": 300.0}}}` (RUN, one call per wall) |
| Friction source | `wall[w] = {"thermal": {"q_dot": {"value": q}, "wall_thickness": {"value": 0.002}}}` (RUN) |
| Layer material | `wall[w].thermal.material = "grey-iron"` (SRC path; runtime UNVERIFIED - read it back) |
| Initialize | `init = s.settings.solution.initialization; init.initialization_type = "standard"; init.defaults["temperature"] = 300.0; init.standard_initialize()` (RUN) |
| Time step | `s.settings.solution.run_calculation.parameters.time_step_size = 0.01` (RUN). `transient_controls.time_step_size` **does not exist** in v261 (SRC) |
| Advance | `s.settings.solution.run_calculation.dual_time_iterate(time_step_count=n, max_iter_per_step=5)` (RUN) |
| Energy residual | `s.settings.solution.monitor.residual.equations["energy"].absolute_criteria = 1e-8` (path SRC; key `"energy"` UNVERIFIED) |
| Autosave / commands | `s.settings.solution.calculation_activity.auto_save` (children `data_frequency`, `root_name`, ...), `.execute_commands[name]` (SRC). There is no `autosave` (SRC) |
| Write | `s.settings.file.write(file_type="case-data", file_name=path)`; `file_type` one of `case`, `case-data`, `data` (RUN) |
| Mesh info | `s.tui.mesh.size_info()`, `s.tui.mesh.check()`, `s.tui.mesh.quality()` (RUN, output goes to the transcript); settings `s.settings.mesh.check()` etc. exist (SRC) |

**Readback keys are canonical names, not aliases.** `get_state()` returns keys
from `child_names` (SRC, `Group.to_python_keys`): `heat_generation_rate`, not
`q_dot`; `thermal_condition`, not `thermal_bc`; `heat_transfer_coeff`, not `h`.
This is the likely reason the predecessor's `q_dot` readback was "blind". Read
`wall[w].thermal.get_state()["heat_generation_rate"]` first (UNVERIFIED at
runtime; record which path answered).

## 8. Report definitions, report files, monitors

| Purpose | Form |
|---|---|
| Volume report | `rv = s.settings.solution.report_definitions.volume; rv[n] = {}; rv[n].report_type = "volume-max"; rv[n] = {"field": "temperature", "cell_zones": zones}` (RUN) |
| Surface report | `...report_definitions.surface[n]`, `report_type = "surface-facetmax"`, `{"field": "temperature", "surface_names": walls}` (RUN) |
| Compute | `s.settings.solution.report_definitions.compute(report_defs=[n])` (RUN; unwrap the returned structure) |
| Volume types | `volume-max`, `volume-min`, `volume-average`, `volume-integral`, `volume-sum`, `volume-zonevol`, `volume-mass` (SRC). `volume-zonevol` returned "unbound variable" (RUN failure); use `volume-sum` of `cell-volume` (RUN) |
| Area | `surface-integral` / `surface-areaavg` of temperature (RUN). `surface-area` type exists (SRC, UNVERIFIED) |
| Report file | `rf = s.settings.solution.monitor.report_files; rf.create(name=stem); rf[stem] = {"report_defs": defs + ["flow-time"], "file_name": stem + ".out"}` (RUN) |
| Reductions | `s.fields.reduction.area(locations=[...])`, `.volume(...)`, `.maximum(expression="Temperature", locations=[...])` (SRC, UNVERIFIED) |

## 9. Field data and graphics (solver)

- Surface geometry (RUN): `from ansys.fluent.core import SurfaceFieldDataRequest, SurfaceDataType`;
  `s.fields.field_data.get_field_data(SurfaceFieldDataRequest(surfaces=names, data_types=[SurfaceDataType.Vertices, SurfaceDataType.FacesConnectivity], flatten_connectivity=True))`.
- Scalar field: `ScalarFieldDataRequest(field_name="temperature", surfaces=names, node_value=True, boundary_value=True)` (SRC, UNVERIFIED).
- Mesh object (RUN): `g = s.settings.results.graphics; g.mesh["mesh-all"] = {"surfaces_list": walls}; g.mesh["mesh-all"].display()`, then `s.tui.views.auto_scale()`, `g.views.restore_view(view_name="isometric")`, `g.views.camera.zoom(factor=1.3)`.
- Contour (RUN): `g.contour[n] = {"field": "temperature", "surfaces_list": walls, "boundary_values": True, "node_values": True, "filled": True, "coloring": {"smooth": False}}`; banded range `g.contour[n].range_option.option = "auto-range-off"`, `.range_option.auto_range_off.minimum = lo`, `.maximum = hi`; `g.contour[n].display()`.
- `views.camera.orbit` raised on this build although it is in the schema (RUN failure).

## 10. Files that are not what they look like

- **`brake.pmdb` from SpaceClaim is a folder.** The file is
  `20_spaceclaim\brake.pmdb\brake.pmdb`. `open()` on the folder raised
  `PermissionError: [Errno 13]` 13 times in run 1. Resolve once:
  `p = Path(x); inner = p / p.name if p.is_dir() else p; assert inner.is_file()`.
- Hash with `hashlib.sha256(inner.read_bytes())`; compare with
  `tag_report.json.pmdb_sha256` (Gate 2 hashes the inner file).

## 11. Probing a name instead of guessing it

API idiom (SRC: `child_names`, `command_names`, `get_object_names()`,
`allowed_values()` exist on settings objects):
```python
th = s.settings.setup.boundary_conditions.wall[w].thermal
print(json.dumps({"children": th.child_names,
                  "cond_allowed": th.thermal_condition.allowed_values()}))
```
Run it as one short step. Put the answer in your notes, then write the real call.

## 12. UNVERIFIED items, in one place

1. Attaching a second client with `connect_to_fluent` to the session launched in
   another process, and the workflow state being visible to it (source says yes;
   never run here). The fast stage script's mesh gate is the runtime proof.
2. `application_runtime.exit()` and `force_exit()` from a connected client.
3. Fluent's idle-timeout preference (`preferences.General.IdleTimeout`) after the
   launching client detaches: the launcher resets it to the preference value.
   Record the value; if it is non-zero, raise it with the lead.
4. Wall-layer `thermal.material` assignment and its readback.
5. `get_state()["heat_generation_rate"]` as the working source readback.
6. `solution.controls.equations["flow"]`, residual key `"energy"`,
   `fields.reduction`, `ScalarFieldDataRequest`, `surface-area` reports.
7. A 240 s `run_ansys_script` wait under Hermes (300 s configured timeout).

## 12. Confirmed on 2026-11-02 (runs FR330V-20261102-0936 and the fast-profile test)

- `s.switch_to_solver()` from the meshing session transfers the mesh: 27 solid
  zones are present without `read_case` (RUN).
- `report_definitions.compute(...)` is **inactive until the solution is
  initialized**; call it after `standard_initialize()` (RUN failure, then RUN).
- `compute(report_defs=[a, b, ...])` returns a **list with one `{name: [value, ...]}`
  dict per definition**, not one dict (RUN).
- `bc[w].thermal.get_state()` returns canonical keys: `heat_generation_rate`,
  `thermal_condition`, `material`, `wall_thickness`; the friction layer material
  reads back `grey-iron`, and the value set on `cheek_out-outerpad` also reads on
  its `-shadow` (RUN).
- Coupled pair names are `<zoneA>-<zoneB>` and `-shadow`; name order is not
  adjacency (RUN). Exposed pad and backing walls are named `<body>:1` (RUN).
- `pyfluent.launch_fluent(..., cleanup_on_exit=False)` leaves Fluent running after
  the Python job exits; `s.exit()` on a failure path may not stop every process,
  so terminate the Fluent processes the job started, by PID (RUN).
- A background `ValueError: invalid literal for int() with base 10: ''` from
  `streaming_services/_events_info_store.py` appears on every launch; it is a
  pyfluent event-thread error and does not affect the session (RUN).
