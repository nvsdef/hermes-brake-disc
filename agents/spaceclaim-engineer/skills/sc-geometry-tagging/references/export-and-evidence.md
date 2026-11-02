# PMDB export, the three screenshots, and tag_report.json

Open this before steps 6, 13, 14 and 15 of SKILL.md.

## PMDB or nothing

Only PMDB (or SCDOCX) carries named selections into Fluent. A STEP handed to
the mesher loses every face name; the predecessor's solve then ran flat at
300 K with no error. The fluent-engineer refuses a STEP; you never offer one.

## Before the export: read back what you are about to write

In the export step, on the freshly read design:

| Check | Expected |
|---|---|
| `len(design.get_all_bodies())` | 27 |
| `len(design.named_selections)` | 29 |
| body selections | the 27 handoff names, one body each, volume matching its row |
| `wall-vent`, `wall-outer` | face counts and summed areas equal to the classification |
| names containing `inlet`, `outlet`, `symmetry` | none |

## Export: the PMDB is a folder

`design.export_to_pmdb(location)` treats `location` as a **folder** and writes
`location\<design.name>.pmdb` (`api-verified.md` section 11). The Gate 2
contract (`specs/handoffs.md`) keeps that layout: `20_spaceclaim\brake.pmdb\`
is a folder and the file inside it is the PMDB.

API idiom:

```python
import hashlib
from pathlib import Path
p = Path(design.export_to_pmdb(STAGE / "brake.pmdb"))   # -> ...\brake.pmdb\brake.pmdb
assert p.is_file() and p.stat().st_size > 0, p
sha = hashlib.sha256(p.read_bytes()).hexdigest()
```

- Hash `p`, the returned inner file. `open()` on the folder raises
  `PermissionError: [Errno 13]`: run 1 spent 13 launches on that line.
- If `design.name` is not `brake`, the inner file has that name: always use the
  returned path, and record `pmdb_file` (absolute path of the inner file) and
  `pmdb_folder` in the report so the fluent-engineer imports the right thing.
- Do not reopen the PMDB: `open_file` of PMDB needs 27.1, and `open_file` of
  anything would close the working design. Fluent's import at Gate 3 is the
  proof.

## The three screenshots

There is no image call in the Geometry client, and `design.plot()` is
graphics-gated (`api-verified.md` section 14). The verified route: draw the
raw tessellation with matplotlib on the `Agg` backend (no window, no GPU). The
drawing steps are pure Python: they read `.npz` files and never connect.

| File | Data | Taken | Shows |
|---|---|---|---|
| `cad_iso.png` | `tess_pre.npz` (28 bodies, saved in step 5) | before the calliper deletion | full assembly including the calliper, one colour per part, iso view |
| `cad_section_9deg.png` | `tess_pre.npz` | before the deletion | the cut on the plane through the Z axis at 9 deg, in (s, z) with s = x cos 9 + y sin 9 |
| `named_selections.png` | `tess_post.npz` (27 bodies, face ids) plus `faces.json` | after the selections exist | `wall-vent` red, `wall-outer` blue, pad/backing grey, full-contact faces not drawn |

API idiom (iso):

```python
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
fig = plt.figure(figsize=(10, 8), dpi=150); ax = fig.add_subplot(projection="3d")
for name, tris in parts.items():              # tris: (n, 3, 3) array in mm
    ax.add_collection3d(Poly3DCollection(tris, facecolors=COLOURS[name], shade=True, linewidths=0))
ax.set_xlim(-210, 210); ax.set_ylim(-210, 210); ax.set_zlim(-60, 60)
ax.set_box_aspect((420, 420, 120)); ax.view_init(elev=30, azim=-60); ax.set_axis_off()
fig.savefig(STAGE / "cad_iso.png", bbox_inches="tight")
```

API idiom (9 deg section; pyvista's `slice` is a VTK filter and needs no
rendering):

```python
import numpy as np, pyvista as pv
a = np.radians(9.0); n = (-np.sin(a), np.cos(a), 0.0)
cut = pv.PolyData(points_mm, faces_padded).slice(normal=n, origin=(0.0, 0.0, 0.0))
seg = cut.lines.reshape(-1, 3)[:, 1:]        # line cells [2, i, j]
s = cut.points[:, 0] * np.cos(a) + cut.points[:, 1] * np.sin(a)
# plot each (s[i], z[i]) -> (s[j], z[j]) per body in 2D, equal aspect
```

`lines` holds only 2-point cells after a slice of triangles; assert that.
Label the plot with the measured vent-inlet gap: in the band z = -6 to +6 on
the s > 0 side, the smallest s of any cheek or vane segment minus the largest s
of any hat segment. PRD 3.3 says about 7 mm (hat wall r ~ 88, vane roots
r = 95). Report it as the GEO-06 evidence number.

Checks for every image: the file exists, is larger than 20 kB, and is not one
colour (standard deviation of the pixel values above 5 on a 0 to 255 scale).
The model is framed by construction because the axis limits come from the PRD
extents. Record the image size and the check in `screenshots`.

Fallbacks, in order, if matplotlib fails: `pyvista.Plotter(off_screen=True)`
with `.screenshot(path)` (installed, not yet run on this workstation), then a
capture of the SpaceClaim window of **your** PID with
`PIL.ImageGrab.grab(bbox=rect, all_screens=True)` after
`ctypes.windll.shcore.SetProcessDpiAwareness(2)` (without it the predecessor's
captures were cropped to the top-left 44 %). Never launch SpaceClaim again for
a picture.

## tag_report.json

Written by a pure-Python step from the step JSON files. Keys required by
`specs/handoffs.md` are top level with exactly these names; everything else is
under `diagnostics`. Units in key names. Missing values are `null` with a
sibling `*_reason`.

```
{
  "run_id": "...", "prd_revision": "H1.2", "producing_role": "spaceclaim-engineer",
  "started_at": "...", "finished_at": "...", "status": "PASS | FAIL | OPEN | BLOCKED | halted",
  "upstream": {"brake_step_sha256": "...", "cad_report_sha256": "..."},
  "step_sha256": "...",
  "session": {"launch_count": 1, "relaunch_reason": null, "holder_job_id": "...",
              "spaceclaim_pid": 12345, "port": 50xxx, "transport_mode": "wnua",
              "connect_calls": 11, "backend_version": "26.1.0",
              "released": true, "released_at": "..."},
  "timing": {"started_at": "...", "finished_at": "...", "tool_calls": 40, "app_launches": 1},
  "import_scale_check": {...}, "body_map": [...28 rows...],
  "calliper_match": {...}, "after_delete": {...},
  "named_selections": {...}, "contact_graph": [...45 rows...],
  "pmdb_sha256": "...",
  "screenshots": {"cad_iso": {...}, "cad_section_9deg": {..., "vent_inlet_gap_mm": ...},
                  "named_selections": {...}},
  "gate2_checks": [{"check": "wall_vent_before_imprint_mm2", "expected": 167037.60,
                    "measured": ..., "delta_pct": ..., "tolerance_pct": 2.0, "pass": true}, ...],
  "artifacts": {"pmdb_folder": "...\\brake.pmdb", "pmdb_file": "...\\brake.pmdb\\brake.pmdb",
                "pmdb_bytes": ..., "tag_report": "..."},
  "diagnostics": {"face_partition": {...}, "pad_backing_exposed": {...},
                  "edge_only_contacts": [...], "step_crashes": [...], "findings": [...]}
}
```

`status` is PASS only if every Gate 2 check passed. A null in a Gate 2 check
makes it FAIL, OPEN or BLOCKED, never PASS. `diagnostics.step_crashes` lists
each rerun step with its exception line, so the lead sees the cost.

## The handback (to the lead)

Short and numeric, for example:

```
Gate 2 spaceclaim-engineer, run <id>. 1 SpaceClaim launch (job <id>, PID 12345), 11 connects, 2 step reruns.
step_sha256 matches Gate 1. 28 solids, 0 sliver faces. OD 330.000 / 330.0 mm; z -57 to 57; total +0.000x %.
Calliper: 1 candidate (volume -0.00x %, centroid z 0.36x / 0.369, x max 200.000). After delete 27, drop/calliper -0.000x %.
Contacts 45/45. wall-vent 167 0xx / 167 037.60 (-0.0x %); wall-outer 240 2xx / 240 205.78; pad/backing 42 9xx / 42 997.28.
Predicted after imprint 142 8xx / 228 4xx / 31 2xx for Gate 3.
PMDB ...\brake.pmdb\brake.pmdb, 0.5 MB, sha256 ab12... Screenshots: cad_iso, cad_section_9deg (inlet gap 7.x mm), named_selections.
Session closed, PID gone at 12:34:56. Open: PMDB verified by Fluent at Gate 3.
```
