# Verified API sheet - ansys-geometry-core 0.15.5 on SpaceClaim 2026 R1

Every call below was read in the installed source of the ansys-agent venv
(`.venv\Lib\site-packages\ansys\geometry\core`, version 0.15.5). File and line
references are to that source. Run 1 measured the backend as
`BackendType.SPACECLAIM 26.1.0`. Anything not visible in the client source is
marked **UNVERIFIED**. If a name is not on this sheet, do not use it: run 1 lost
about 25 SpaceClaim launches to names that do not exist.

Blocks marked "API idiom" show an exact call shape. None of them is a stage
script.

## 1. Imports that exist

API idiom:

```python
from ansys.geometry.core import launch_modeler_with_spaceclaim, Modeler
from ansys.geometry.core.connection import BackendType       # agc.BackendType does NOT exist
from ansys.geometry.core.misc import UNITS, TessellationOptions
from ansys.geometry.core.designer import SurfaceType, CurveType
from ansys.geometry.core.designer.body import CollisionType
```

`Modeler(...)` has no `backend_type` argument. Run 1 died on
`Modeler(backend_type=agc.BackendType.SPACECLAIM)` with
`AttributeError: module 'ansys.geometry.core' has no attribute 'BackendType'`.

## 2. Launch (launch process only)

`connection/launcher.py` line 822:

```
launch_modeler_with_spaceclaim(version=None, host="localhost", port=None,
    api_version=ApiVersions.LATEST, timeout=150, manifest_path=None, hidden=False,
    server_log_level=2, client_log_level=logging.INFO, client_log_file=None,
    server_working_dir=None, transport_mode=None, uds_dir=None, uds_id=None,
    certs_dir=None, proto_version=None, **kwargs) -> Modeler
```

What the source shows (`connection/product_instance.py`):

- `version` is converted with `int()`; `261` or `"261"` both work. If only a
  Student install exists, it retries with the negative version automatically.
- `port=None` picks a free port (`_check_port_or_get_one`). A given port that
  is busy raises `ConnectionError`.
- `transport_mode=None` on Windows with host `localhost` selects `"wnua"`
  (Windows named-user authentication, loopback only). Pass it explicitly so the
  value you write into `session.json` is the value in use.
- SpaceClaim.exe is started with `subprocess.Popen` by **this** Python process.
  Its PID is kept in `modeler.client._product_instance._pid` (private). Prefer a
  `psutil` before/after difference of `SpaceClaim.exe` PIDs and cross-check.
- `server_working_dir` sets SpaceClaim's working directory. Use the stage folder.
- The address in use: `modeler.client.get_name()` returns `"localhost:<port>"`.
- `modeler.client.backend_type`, `modeler.client.backend_version` (semver),
  `modeler.client.healthy` (bool, one server call).

## 3. Connect a new client to the running SpaceClaim

`modeler.py` line 108: `Modeler(host="127.0.0.1", port=50051, channel=None,
remote_instance=None, docker_instance=None, product_instance=None, timeout=120,
logging_level=INFO, logging_file=None, proto_version=None, transport_mode=None,
uds_dir=None, uds_id=None, certs_dir=None)`.

API idiom:

```python
m = Modeler(host="localhost", port=PORT, transport_mode="wnua", timeout=20)
design = m.read_existing_design()
```

- `transport_mode` is **required** when no channel is passed:
  `connection/client.py` line 173 raises `ValueError("Transport mode must be
  specified...")`.
- `wnua` accepts only `localhost` or `127.0.0.1` (`ansys/tools/common/cyberchannel.py`
  line 313). The MCP subprocess runs as the same Windows user, which WNUA needs.
- `timeout` is the health-check wait. 20 s makes a dead session fail fast.
- `proto_version=None` negotiates the newest protocol the server supports, the
  same rule the launcher used.

## 4. Disconnect without closing SpaceClaim

API idiom:

```python
m.client.close()          # step scripts: closes the gRPC channel only
```

`GrpcClient.close()` (`client.py` line 445) shuts the server down **only** when
the client holds a `product_instance`, `docker_instance` or `remote_instance`.
A client made with `Modeler(host, port, ...)` holds none, so `close()` only
closes the channel. The client also registers `atexit.register(self.close)`,
which is equally harmless in a step script.

**Never call `m.close()` or `m.exit()` in a step script.** `Modeler.close(close_design=True)`
(`modeler.py` line 241) first calls `design.close()`, which closes the design
**on the server**. Every import, deletion and named selection is then gone.
`m.close(close_design=False)` is equivalent to `m.client.close()`.

## 5. Stop SpaceClaim (launch process only)

`modeler.close()` in the process that launched: `admin.close()` (server
shutdown; a failure is logged only at debug level), then
`ProductInstance.close()` = `os.kill(pid, SIGTERM)`. Because of the `atexit`
hook, the launch process also kills its SpaceClaim whenever that Python exits,
including on an exception or `job_cancel` (which runs `taskkill /F /T`).

## 6. Designs

| Call | Returns | Notes |
|---|---|---|
| `modeler.open_file(file_path, upload_to_server=True, import_options=ImportOptions(), import_options_definitions=...)` | `Design` | closes this client's active design first; ends with `read_existing_design()`. Run 1 used the default upload and imported 28 bodies. |
| `modeler.open_file("<x>.pmdb")` | raises `GeometryRuntimeError` | needs backend 27.1 **and** protocol v1 |
| `modeler.read_existing_design()` | `Design` | reads the server's active design: components, bodies, materials, named selections. Raises `RuntimeError("No existing design available at service level.")` when SpaceClaim has none. |
| `design.name` | `str` | from the server; run 1: `"brake"` |
| `design.get_all_bodies()` | `list[Body]` | recursive (`component.py` line 407) |
| `design.bodies` | `list[Body]` | root only: **0** on the assembly STEP in run 1 |
| `design.components`, `comp.name`, `comp.bodies` | | run 1 component names: `vanes`, `cheek_in`, `cheek_out`, `hat` (a hint only) |
| `design.delete_body(body_or_id)` | `None` | searches the tree; a body not found only logs a warning |
| `design.tree_print()` | prints | diagnostic |

## 7. Bodies

| Member | Type and unit | Gate |
|---|---|---|
| `body.id`, `body.name` (setter calls `set_name`) | `str` | set_name 25.1 |
| `body.volume` | pint Quantity, m^3 (0 for a surface body) | |
| `body.is_surface`, `body.is_alive` | `bool` | |
| `body.bounding_box` | `BoundingBox` with **`.min_corner`, `.max_corner`, `.center`** (Point3D) | 25.2; there is no `.min` or `.max` |
| `body.faces`, `body.edges` | new Python objects on **every** access | |
| `body.parent_component` | `Component` | |
| `body.get_collision(other)` | `CollisionType.NONE/TOUCH/INTERSECT/CONTAINED/CONTAINEDTOUCH` | 24.2 |
| `body.get_raw_tessellation(tess_options=None, reset_cache=False, include_faces=True, include_edges=False)` | `dict` face id -> `{"vertices": [x, y, z, ...] in m, world transform applied, "faces": [3, i, j, k, 3, ...], "is_edge": False}` | **26.1**, not graphics-gated |

**Not available on this machine:** `body.centroid` and `body.get_bounding_box(tight=True)`
(27.1), and `body.tessellate()`, `body.plot()`, `design.plot()`,
`get_vtk_tessellation()`, `face.tessellate()` - these carry `@graphics_required`,
which imports `ansys.tools.visualization_interface`, `pygltflib` and `trame`.
None of the three is installed (pyvista 0.48.4 and vtk 9.6.2 are), so they
raise `ImportError`. Run 1 logged "tessellation unavailable" for this reason and
then matched on bbox centres, which produced 2 and then 0 calliper candidates.

`Point3D` is a numpy array stored in metres: `np.asarray(p)` is metres, and
`p.x`, `p.y`, `p.z` are Quantities (`p.z.m_as("mm")`).

## 8. Faces

| Member | Type and unit | Gate |
|---|---|---|
| `face.id` | `str` | |
| `face.surface_type` | `SurfaceType.SURFACETYPE_PLANE`, `_CYLINDER`, `_CONE`, `_TORUS`, `_SPHERE`, `_NURBS` (no server call) | |
| `face.area` | Quantity, m^2 | |
| `face.bounding_box` | `.min_corner`, `.max_corner`, `.center` | 25.2 |
| `face.normal(u=0.5, v=0.5)` | a **method** returning `UnitVector3D`: a numpy array with plain-float `.x .y .z`; there is no `.direction` and no unit. Outward: reversed faces are handled. | 24.2 |
| `face.shape.geometry` | `PlaneSurface` (`.origin`, `.dir_z`) or `Cylinder`/`Cone` (`.radius` Quantity, `.origin`, `.dir_z`) | 24.2 |
| `face.point(u, v)` | `shape.evaluate_proportion(u, v).position`: a point on the **uv box**, not the trimmed face. For an annulus, (0.5, 0.5) is in the hole. | |
| `face.edges`, `face.body`, `face.is_reversed` | | |

A `Face` is an object, not a dict: `face["surface_type"]` raises
`TypeError: 'Face' object is not subscriptable` (run 1). `face.centroid` is 27.1.

## 9. Edges

`edge.id`, `edge.curve_type` (`CurveType.CURVETYPE_LINE`, `_CIRCLE`, ...),
`edge.length` (Quantity), `edge.start`, `edge.end` (Point3D),
`edge.shape.evaluate_proportion(t).position`, `edge.shape.geometry` (for a
circle `.radius`, `.origin`), `edge.bounding_box` (25.2), `edge.faces`.
`edge.centroid` is 27.1.

## 10. Named selections

| Call | Notes |
|---|---|
| `design.create_named_selection(name, bodies=None, faces=None, edges=None, beams=None, design_points=None, components=None, vertices=None, design_curves=None)` | returns `NamedSelection`; `ValueError` if every argument is empty; pass **lists** |
| `design.named_selections` | `list[NamedSelection]` as read by `read_existing_design()` |
| `ns.name`, `ns.id`, `ns.bodies`, `ns.faces`, `ns.edges`, `ns.components` | members re-read from the server (consistent from backend 25.2). There is **no** `ns.entities`. |
| `design.delete_named_selection(ns_or_name)` | |
| `ns.add_members(...)`, `ns.remove_members(...)` | return a **new** NamedSelection |
| `body.get_named_selections()`, `face.get_named_selections()` | reverse lookup |

## 11. Export

`design.export_to_pmdb(location=None, options=None) -> Path` (`design.py` line 762).
`location` is a **folder**: the file is `location / f"{design.name}.pmdb"`
(`__build_export_file_location`, line 517), and `download()` creates the parent
folder. Passing `...\20_spaceclaim\brake.pmdb` therefore creates the folder
`brake.pmdb\` with `brake.pmdb` inside. The returned `Path` is the inner file:
hash that. Opening the folder with `open(..., "rb")` raises
`PermissionError: [Errno 13]` on Windows (9 failed launches in run 1).
`export_to_scdocx(location=None, write_body_facets=False)` follows the same rule.
PMDB `options` are ignored below 27.1.

## 12. Units

The service returns pint Quantities in SI. Convert once with `.m_as(...)`:
`body.volume.m_as("mm**3")`, `face.area.m_as("mm**2")`, `p.x.m_as("mm")`.
`float(quantity)` on a dimensioned value raises
`DimensionalityError: Cannot convert from 'meter ** 2' to 'dimensionless'` (run 1).

## 13. Scripts and tools

- `modeler.run_script_file(file_path, script_args=None, import_design=False, api_version=None)`
  returns `(values_dict, Design_or_None)` and raises `GeometryRuntimeError` when
  the server reports failure. The script receives `argsDict` and returns what it
  puts in a dict named `result`. `run_discovery_script_file` is deprecated.
  The SpaceClaim-side names used inside such a script (for example
  `Window.ActiveWindow.ZoomExtents()`) are **not** in this source: UNVERIFIED.
- `modeler.measurement_tools.min_distance_between_objects(object1, object2)`
  returns `Gap` with `.distance` (24.2).
- `modeler.prepare_tools.share_topology(...)` exists (24.2). Do not use it on
  the export design.

## 14. Confirmed on 2026-11-02 (run FR330V-20261102-0936 and the fast-profile test)

- `launch_modeler_with_spaceclaim(version=261, hidden=False, transport_mode="wnua",
  server_working_dir=..., timeout=300)`: boot measured 45 s and 115 s; 150 s is too
  tight (RUN).
- Body and face `bounding_box.min_corner` / `.max_corner` convert with
  `np.asarray(...)` to metres (RUN).
- `design.delete_body(body)`, `body.name = n`, `design.create_named_selection(n,
  bodies=[b])` / `(n, faces=[...])`, `design.export_to_pmdb(folder)` (RUN).
- `body.get_raw_tessellation()` keys equal `face.id.split('/')[-1]` on an assembly
  import, not `face.id` (RUN).
- STEP splits every full cylinder into two half faces; classify by surface type,
  radius and plane z, never by face count (RUN).

## 15. Backend-version gates

| Available on 26.1 | Not available on 26.1 (27.1 or later) |
|---|---|
| `body.bounding_box`, `face.bounding_box`, `edge.bounding_box` (25.2), `set_name` (25.1), `get_collision` (24.2), `get_raw_tessellation` on body and design (26.1), `edge.vertices`, `face.vertices`, `body.vertices` (26.1), `NamedSelection.name` setter (26.1), `min_distance_between_objects` (24.2), `share_topology` (24.2) | `centroid` on body, face and edge; `get_bounding_box(tight=...)`; `body.detach_faces`; `face.detach`; `component.create_block`, `create_datum_plane`, `copy_faces`; `prepare_tools.find_mappable_faces`; `open_file` of PMDB; PMDB export options |

## 16. UNVERIFIED (not provable from the client source)

1. That SpaceClaim's API server accepts a second client while the launch
   process keeps its own channel open. Step 3 of SKILL.md proves or disproves it
   in seconds.
2. That the server keeps the active design between client connections. Proven
   by the first `read_existing_design()` after the import step.
3. That the face-tessellation triangles are wound consistently outward. Proven
   per body by comparing the divergence-theorem volume with `body.volume`.
4. That the keys of `get_raw_tessellation()` equal `face.id` strings. Check the
   two sets once.
5. Off-screen pyvista rendering, and every SpaceClaim-side scripting name.
