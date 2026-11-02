# Run 1 (FR330V-20260930-1012) - what failed at Gate 2 and why

Open this when you are tempted to write one long script, to guess an API name,
or to decide by eye which faces are contact faces. The evidence is in
`C:\brake-runs\FR330V-20260930-1012\20_spaceclaim\` and in the job folders
`C:\brake-runs\_ansys-runtime\jobs\spaceclaim-gate2_*` and `debug_import_*`
(each holds `script.py`, `stdout.log`, `stderr.log`, `exit_code.txt`).
These numbers illustrate traps. They are never acceptance values.

## The shape of the failure

About 25 SpaceClaim launches in 60 minutes (11:27 to 12:53). Every attempt was a
full script of 650 to 1 150 lines that launched SpaceClaim, imported the STEP,
measured for about a minute, and then died on one line. Each fix cost a new
launch, a new import and the same minute again. The stage never passed.

The fix is structural: one launch that stays alive, and short step scripts that
connect to it (`persistent-session.md`). A crash then costs seconds.

## Crash table, in order

| # | Crash | Cause | Correct call (`api-verified.md`) |
|---|---|---|---|
| 1 | `AttributeError: 'BoundingBox' object has no attribute 'min'` | guessed attribute | `bb.min_corner`, `bb.max_corner`, `bb.center` |
| 2 | `DimensionalityError: Cannot convert from 'meter ** 2' to 'dimensionless'` | `float()` on a pint area | `face.area.m_as("mm**2")` |
| 3 | `KeyError: 'centroid_mm'`, then `'bbox_mm'` | own PRD dict keys renamed between edits | one constants block, printed once, reused |
| 4 | `Calliper match not unique: 2 candidates`, then `0 candidates` | centroid taken from the bbox centre because `body.tessellate()` needs graphics packages that are not installed | tessellated mass centroid from `body.get_raw_tessellation()`; unique match on volume AND centroid z AND bbox x max |
| 5 | `KeyError: 'imported_index'`, then `'bbox_center_mm'` | own dict keys again | same as 3 |
| 6 | `AttributeError: 'NamedSelection' object has no attribute 'entities'` | guessed attribute | `ns.bodies`, `ns.faces`, `ns.edges` |
| 7 | `AttributeError: 'UnitVector3D' object has no attribute 'direction'` | guessed attribute | `n = face.normal(); n.z` (plain float) |
| 8 | `TypeError: 'Face' object is not subscriptable` | a Face object used where a record dict was meant | keep Face objects and plain-dict records in separate names |
| 9 | `PermissionError: [Errno 13] Permission denied: '...\20_spaceclaim\brake.pmdb'` (13 attempts, 12 of them in a row, each a full launch) | `export_to_pmdb(location)` treats `location` as a folder and writes `location\brake.pmdb`; the script then did `open(folder, "rb")` to hash it | hash the returned path (the inner file) |
| 10 | `AttributeError: module 'ansys.geometry.core' has no attribute 'BackendType'` | an attempt to connect instead of launching, with a guessed import and a `Modeler(backend_type=...)` argument that does not exist | `from ansys.geometry.core.connection import BackendType`; `Modeler(host=, port=, transport_mode=)` |
| 11 | `StopIteration` looking up a body named `cheek_out` | body names were never set on this fresh import | identify by signature, never by name |

Measured facts from the same logs that are still useful:

- Backend `BackendType.SPACECLAIM 26.1.0`; one new SpaceClaim PID per launch.
- 28 bodies imported; zero sliver faces; scale checks passed: OD 330.0 mm,
  z = -57.0 to +57.0 mm, total 2 647 556.15 mm^3 against 2 647 566.05 mm^3.
- The calliper measured 617 071.6 mm^3 with bbox centre x = 140.6228 mm, which
  is the PRD bbox (81.245 to 200.000) exactly. Vane bbox centres matched the PRD
  vane_01 bbox to 0.001 mm, so `body.bounding_box` looked tight on 26.1.
- After deleting the calliper: 27 bodies, 2 030 484.52 mm^3 (PRD 2 030 484.57),
  z = -34 to +43 mm. Deletion plus re-read worked.
- 183 faces on the 27 bodies; 45 contacts found; 29 named selections read back.

## The face-classification bug

The last complete attempt (job `spaceclaim-gate2_20260930_123949`) found all 45
contacts and then classified any face that **touches** a contact as a contact
face:

| Group | Measured | PRD before imprint | What was wrongly excluded |
|---|---|---|---|
| `wall-vent` | 52 683.6 mm^2 | 167 037.60 | both cheek inner faces (z = +/-6), 2 x 57 176.99 = 114 354 mm^2, because the 40 vane footprints sit on them |
| `wall-outer` | 128 836 mm^2 (276 316 in another attempt) | 240 205.78 | the two friction faces (pad footprints); in one version all 45 contact faces leaked in instead |
| pad/backing exposed | 28 336.5 mm^2 | 42 997.28 | both backing front faces, 2 x 7 330.4 = 14 660.8 mm^2, because the pads sit on them |

The rule that fixes it: a face is a **contact face** only if its **whole** area
coincides with a partner face. Faces that are only **partly** covered (cheek
inner faces with 40 vane footprints, cheek friction faces with a pad footprint,
backing front faces with a pad footprint) are tagged **in full** before imprint;
shared topology cuts the footprints out in Fluent. The pad friction face and
the pad back face are wholly contact; the cheek friction face and the backing
front face are not. See `face-classification-and-areas.md`.

## The HALT that worked

The first import (job `spaceclaim_tagging_FR330V_20260930_112758`) found 23
solids: the STEP carried only `vanes`, `cheek_in`, `cheek_out` and `hat`. The
script stopped with `Upstream HALT: expected 28 solids ... got 23` and no
tagging happened. Keep that check exactly: a count other than 28 goes back to
the lead with the component list.

## Rules that follow

1. One launch, short steps (`persistent-session.md`).
2. Only names on `api-verified.md`. A name you have not seen there is checked
   with a 5-line probe in the running session, not in a new launch.
3. PRD constants in one block with fixed key names; print them in the first
   step and reuse the same block in every step.
4. Contact means whole-area coincidence. Partly covered faces are tagged whole.
5. The PMDB is a folder; hash the inner file.
6. The 28-solid HALT stays.
