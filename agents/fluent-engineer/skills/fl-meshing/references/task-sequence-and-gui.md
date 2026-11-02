# Watertight task sequence, API idioms, GUI framing and the transport timeout

Open this before writing the meshing script, when a task or argument name is
rejected, or when a screenshot comes back empty.

The exact, source-verified spellings of every call here are collected in
`api-verified.md`; where this file and that sheet differ, the sheet wins.

## Two API styles exist - probe, do not guess

PyFluent exposes the watertight workflow in two ways, depending on release. Both
drive the same Fluent tasks.

| Style | Access | Seen in |
|---|---|---|
| Task-object, string names | `meshing.workflow.TaskObject["Import Geometry"]` with `.Arguments.set_state({...})` and `.Execute()` | predecessor runs on Fluent 2026 R1 |
| Attribute style | `wt = meshing.watertight_workflow()` (PyFluent 0.41.0 name; there is no `watertight()` on the session), then task attributes | ansys-agent reference sheet `02-watertight-workflow`; never run on this machine - do not use |

Before writing the full script, probe the installed version with a short
`run_ansys_script` call, or print the task list inside the job after every
stage: `print(list(meshing.workflow.TaskObject.get_object_names()), flush=True)`.
The task list changes as you execute, because Describe Geometry rebuilds the
downstream tasks.

The ansys-agent server also ships reference sheets. Read them with
`read_skill_reference(skill="ansys-fluent-cfd", sheet_name="02-watertight-workflow")`
and `sheet_name="11-failure-modes"`. Note that sheet 02 is written for a
**fluid** case; the setup type there is wrong for this model.

## Task sequence measured working on Fluent 2026 R1 (task-object style)

```
InitializeWorkflow(WorkflowType="Watertight Geometry")
  Import Geometry            FileName=<brake.pmdb>, LengthUnit=<unit of the PMDB>
  Add Local Sizing           cheek 4.0 mm (2 labels), vane 5.0 mm (20 labels),
                             hat 8.0 mm (1 label)
  Generate the Surface Mesh  CFDSurfaceMeshControls: MinSize 2.2, MaxSize 20.0,
                             GrowthRate 1.2, CurvatureNormalAngle 18
  Describe Geometry          SetupType "The geometry consists of only solid regions",
                             InvokeShareTopology "Yes",
                             then UpdateChildTasks(SetupTypeChanged=True), Execute
  Apply Share Topology       EXECUTE IT - this is where imprinting happens
  Update Boundaries
  Update Regions             confirm every region type is solid
  Add Boundary Layers        AddChild "no" (no inflation for conduction)
  Generate the Volume Mesh   VolumeFill "poly-hexcore"
```

Then write the mesh and switch to the solver in the same process.

API idiom - import and global sizing (task-object style):
```python
wf = meshing.workflow
wf.InitializeWorkflow(WorkflowType="Watertight Geometry")
imp = wf.TaskObject["Import Geometry"]
imp.Arguments.set_state({"FileName": pmdb, "LengthUnit": "mm"})
imp.Execute()
surf = wf.TaskObject["Generate the Surface Mesh"]
surf.Arguments.set_state({"CFDSurfaceMeshControls": {
    "MinSize": 2.2, "MaxSize": 20.0, "GrowthRate": 1.2,
    "CurvatureNormalAngle": 18}})
surf.Execute()
```

API idiom - local sizing. The argument keys moved between releases; the
predecessor tried these forms in order and recorded which one took:
```python
task = wf.TaskObject["Add Local Sizing"]
task.Arguments.set_state({"AddChild": "yes", "BOIControlName": "cheek-fine",
    "BOIExecution": "Body Size", "BOISize": 4.0,
    "BOIZoneorLabel": "label", "BOIFaceLabelList": ["cheek_out", "cheek_in"]})
task.AddChildAndUpdate()
# fallback forms: drop "BOIZoneorLabel"; or "BOIExecution": "Face Size"
```
Labels are the body names as the workflow sees them after import, which may
carry a prefix. Use the names you printed in step 2, not the PRD names.

API idiom - describe geometry and share topology:
```python
desc = wf.TaskObject["Describe Geometry"]
desc.Arguments.set_state({
    "SetupType": "The geometry consists of only solid regions",
    "InvokeShareTopology": "Yes"})
desc.UpdateChildTasks(SetupTypeChanged=True)
desc.Execute()
names = list(wf.TaskObject.get_object_names())
for t in ("Apply Share Topology", "Share Topology"):
    if t in names:
        wf.TaskObject[t].Execute(); break
```

In the attribute style the equivalents are `wt.describe_geometry.setup_type`
(the reference sheet lists `"fluid"`, `"solid"`, `"fluid-and-solid"`),
`wt.add_local_sizing_wtm` and `wt.create_volume_mesh_wtm`. Only those two tasks
carry the `_wtm` suffix.

API idiom - volume mesh, write, switch:
```python
vol = wf.TaskObject["Generate the Volume Mesh"]
vol.Arguments.set_state({"VolumeFill": "poly-hexcore"})
vol.Execute()
meshing.meshing.File.WriteMesh(FileName=mesh_path)
solver = meshing.switch_to_solver()          # same process, same licence
solver.settings.file.read_case(file_name=mesh_path)
```

## Why watertight, and why not fault-tolerant

The watertight workflow is normally used for a **fluid** domain: cap openings,
extract the flow volume, add inflation layers. None of that applies here. Every
region is a solid, the CAD bodies are the mesh domain, and there is no velocity
gradient to inflate for. Use watertight with the setup type "only solid
regions". **Fault-tolerant meshing** exists to wrap leaky fluid domains, and
will happily wrap 27 bodies into one. Do not use it.

## The transport timeout and the persistent session (H1.2)

Meshing on a smoke case exceeded the MCP call timeout: Fluent finished and wrote
the mesh, but the blocking tool call returned "Request timed out" and no report
was written. `timeout_seconds` on `run_ansys_script` does not help, because the
transport gives up first. In H1.2 this is solved by the persistent session in
`persistent-session.md`, not by one giant script:

- One host job launches Fluent once, with `cwd` = the run's `30_fluent`
  folder, so the Fluent transcript lands there.
- Import, sizing, surface mesh, describe geometry and share topology are short
  `run_ansys_script` steps that connect to that session. Each finishes in
  seconds to about a minute.
- The volume mesh, the write, `switch_to_solver()` and the read-back run as one
  `submit_ansys_job` that connects to the same session.
- `run_ansys_script` runs in the ansys-agent **source** folder (the server sets
  `cwd=PROJECT_ROOT`); the Hermes `cwd: C:/brake-runs` applies to the server
  process only. Use absolute paths for every file you write. The predecessor
  left dozens of `fluent-*.trn` files in that OneDrive folder.
- Print progress lines with `flush=True`. The job's stdout goes to a file and
  is block-buffered otherwise, so `job_status` shows an empty tail.
- Poll with `job_status(job_id, tail_lines=12, wait_seconds=60)`. The server
  clamps the wait to 60 s; 90 once exceeded a client's transport limit.
- On state `lost` (runner gone, no exit code), list the case folder before
  anything else. A lost job once had already written a 28 MB mesh.
- The PMDB to import is the inner file `brake.pmdb\brake.pmdb`.

## GUI: visible is not framed

The user watches. `ui_mode="gui"` puts a window on screen, but a window whose
camera was never zoomed shows an empty viewport and proves nothing.

The display API differs by session, measured on 2026 R1:

| Call | Meshing session | Solver session |
|---|---|---|
| `tui.display.all_grid()`, `draw_frame` | works | not the route |
| `display.objects.mesh` | fails (no attribute `display`) | - |
| `tui.views.auto_scale()`, `restore_view("isometric")` | fails (no attribute `views`) | works |
| `settings.results.graphics.mesh[...].display()` | - | works, needs an explicit object name |

In the solver: create a mesh graphics object over the walls you want, display
it, restore a view, then set the camera.

API idiom - mesh object in the solver session:
```python
g = solver.settings.results.graphics
walls = list(solver.settings.setup.boundary_conditions.wall.get_object_names())
g.mesh["mesh-all"] = {"surfaces_list": walls}
g.mesh["mesh-all"].display()
solver.tui.views.restore_view("isometric")
solver.tui.views.auto_scale()
```

### Framing a subset (the vent close-up)

- Fluent 2026 R1 draws a grid-plane backdrop sized to the whole case, and
  `auto_scale` fits **that**, not the surfaces displayed. A subset figure came
  out at about 3 % of the frame.
- `grid-plane-enabled? no` and `simple-shadows-enabled? no` return `True` and
  change nothing.
- What works: restore a named view (it carries orientation and lighting), then
  set `views/camera/target` and `views/camera/field` from the bounding box of the
  surfaces you displayed. For the vent: target (0, 0, 0), field about 0.36 m.
- **Do not also set `camera/position`**; the model renders unlit and near-black.
- `views.camera.orbit` does not exist in this build. It raises while the
  surrounding calls report success.

### Saving pictures

- `save_picture` **does not overwrite** an existing PNG and raises nothing, so a
  stale file from an earlier run passes a size check. Delete the target first.
  Record each image's size and mtime in the report.
- `x_resolution` and `y_resolution` are accepted and ignored; the PNG comes out
  at the graphics-window size.

API idiom:
```python
if os.path.exists(png): os.remove(png)
solver.tui.display.set.picture.driver.png()
solver.settings.results.graphics.picture.save_picture(file_name=png)
```

### Window capture

Take **one** framed window capture per stage. The predecessor wrote 46 full-
screen captures, many 2 to 4 MB each. Call `ctypes.windll.shcore.
SetProcessDpiAwareness(2)` before enumerating or capturing windows; without it
captures cropped to the top-left 44 % on the user's monitor. Prove the window
exists with a ctypes window enumeration; a PowerShell `EnumWindows` scriptblock
once returned zero windows while the window was plainly on screen.
