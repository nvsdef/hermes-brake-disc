# SolidPilot failure modes - the full record

Open this when a call does something unexpected, times out, or when you are
tempted to try a shortcut. Every entry was measured by the predecessor package
on this brake. Predecessor numbers illustrate the trap; they are never
acceptance values. The PRD section 4 checksums are the acceptance values.

## Architecture - where errors really come from

SolidPilot is three layers, not one server:

| Layer | Process | Notes |
|---|---|---|
| Adapter | Python MCP server (`adapters/claude/server.py`) | What Hermes talks to. Holds the fixed 30 s ceiling |
| Execution | `SolidworksExecution.exe` on `localhost:5000` | The only layer that touches SolidWorks COM. The adapter starts it |
| Compiler | `compiler/solidworks/pycompiler` | Feature-graph IR to SolidWorks operations |

When a call fails, the useful traceback is usually in the adapter, not in
SolidWorks. The C# layer targets SolidWorks **2026** interop; an older install
gives interop errors on load.

## Symptom table

| Symptom | What is really happening | What to do |
|---|---|---|
| A tool hangs with no error | A modal dialog is open in SolidWorks | You cannot dismiss it. Tell the lead; a human must look at the screen |
| `analyze_*` never returns | Same. Analysis calls are the most dialog-prone | Same |
| `Request to solidworks-execution timed out after 30.0s` | The fixed 30 s ceiling, no override | Inspect state (`verify_state`, `analyze_model('features')`) before any retry |
| Every later call also times out | The execution server is wedged | Report it. `close_document(close_all=true)` may clear it only if every open document is yours; if that times out too, a human must restart SolidWorks |
| `EXTRUSION_FAILED` on a sketch that looks valid | Two or more closed loops in it overlap, or a contour is open by a rounding gap | One sketch per overlapping loop. Pass 9-decimal coordinates with identical shared endpoints |
| Extrude makes nothing or a partial body | Contour not closed (arc end not on the adjacent line) | `analyze_model('sketch', name=...)`, find the gap, rebuild the sketch |
| A face-sketched feature lands mirrored | The face frame's `xdir` came back `[-1, 0, 0]` | Negate x, or better, sketch on an offset plane instead of a face |
| A part's volume is right and its centroid is off | Wrong plane, wrong offset sign, or wrong extrude direction | Read the sketch frame; use mid-plane about the band centre |
| Rotor comes back as one body | Bodies built in one part, or `create_pattern` used for vanes | One part per body; vanes from rotated coordinates |
| `vanes` totals about 1.93e-4 m^3 | Vane extrude 16 mm (overlapping 2 mm into each cheek) instead of 12 mm | Mid-plane depth 0.012 |
| Hat volume near 0 | Revolve profile not closed, or axis not selected | Close the polygon; put the construction line on sketch y = 0 and pass its end points as the axis |
| Hat volume about 5.43e-4 m^3 | You built the retired hat (r = 97, web top z = -3) | Use the PRD 3.3 polygon exactly |
| Assembly STL writes no file | STL on an assembly reports `COMPLETED` and writes nothing | Use STEP |
| Concatenated part STLs pile up | STL translates each part, not uniformly (see frames reference) | Do not use STL for placement |
| `insert_component` misplaces parts | x/y/z centres the bounding box | Identity `transform_json`, `fixed=true` |
| `compare_parts` reports a wild delta (-100 %) | Mixed document units | Keep every document in the same units |
| STEP import gives virtual components | 3D Interconnect on assembly import | Use the classic import (the default in `open_document`); it flattens to a multibody part, which is what the check wants |

## The heavy-part timeout wall

Measured on a 16-body production part with about 1 400 faces and deep fillet
history. Only one call succeeded:

| Call | Result |
|---|---|
| `analyze_model('bodies')` | OK |
| `analyze_model('features')` | timeout |
| `analyze_model('feature_map')` | timeout |
| `export_document('STL')` | timeout twice, no file |
| `save_body_as_part` | timeout |

Afterwards `open_new_part`, `close_document(close_all=true)` and even
`ensure_ready` timed out. The brake parts are small (6 to about 40 faces, the
vanes part about 120), so this should not happen here. If it does, stop and
report. Do not open unfamiliar heavy parts during a build.

`analyze_model('bodies')` is the cheapest informative read. `feature_map` is the
slowest mode; you do not need it for this brake.

## `submit_feature_graph` and `rebuild_from_ir`

The live schema calls `submit_feature_graph` the "PRIMARY BUILD PATH" and tells
you to prefer it over the individual tools. **Do not.** On this brake (v0.5 IR)
it returned `COMPLETED | IR built 12/12 nodes` and placed **every** body on the
same plane extruding +Y. These placement inputs were all accepted and all
ignored:

- `plane` as `Front`, `Top`, `Right`, `Front Plane`, `Top Plane`, `Right Plane`
- `plane_offset`, `offset_distance`, `offset`
- `midplane`, `reverse`, `flip`, `end_condition`

The first `cheek_out` built that way had a perfect 5.7177e-4 m^3 and a centroid
at y = 5 mm. The volume gate alone would have passed it. The predecessor spent
about 10 minutes and twelve probe bodies rediscovering this before going
incremental.

The only way the lever returns is if the vendor fixes placement. The probe that
proves it is **one body off the origin, checked by centroid**, and only when the
lead asks for it. Not a whole part, and never inside a production build.

## The twin-part shortcut (why negative-side parts are built from scratch)

`cheek_out`/`cheek_in`, `outerpad`/`innerpad` and `bp_outer`/`bp_inner` have
identical volumes and differ only in z. The predecessor tried: copy the file,
open it, change the plane offset with `modify_dimension`.

```
modify_dimension('D1@Plane1@cheek_in.Part', -0.016)
  -> COMPLETED, result_geometry {requested: -0.016, effective: 0.006}
```

The geometry did not move. Only reading `effective` caught it. All three pairs
are sign flips, so the route fails for all three. It cost +14 calls against a
projected saving of 11. Meanwhile `add_reference_geometry(offset=-0.016)` **does**
honour the sign (frame origin `[0, 0, -0.016]`), so the two APIs disagree.

Two more routes that look right and are not:

- `create_pattern(pattern_type='mirror')` mirrors features **inside one part**,
  giving a second body in the same file. The twin needs its own part file and
  STEP PRODUCT name, or `brake.step` has 8 PRODUCTs and SpaceClaim cannot name it.
- `save_body_as_part` keeps the body in its **source coordinates** and is a
  measured timeout risk. It cannot move a body.

PRD section 2 settles it: build the negative-side parts independently.

## `modify_dimension` in general

It is the documented universal parametric edit and returns
`result_geometry {dimension, requested, effective}` after rebuild. **Read
`effective`.** A requested value is not an effective one. It is **not** in this
profile's tool list; do not use it: if a feature is wrong, delete it and
rebuild it, then measure.

## STL

- Export STL only from a **freshly reopened** document. Straight after a build it
  wrote 484 bytes / 8 triangles and said `COMPLETED`; after `close_document` and
  `open_document`, 30 084 bytes / 600 triangles.
- STL on an assembly writes nothing.
- STL output is translated, and not uniformly (see
  `references/frames-and-placement.md`).
- STL is not part of any gate in this package. The CAD-to-SpaceClaim transfer is
  STEP only.

## Drawing tools (descoped in H1.2)

Drawings are not produced in H1.2; SpaceClaim takes the CAD screenshots at
Gate 2. The drawing tools stay out of the tool list
(`tools-used.md`). For the record: `auto_dimension_drawing` stacked all its
dimensions in one view with no way to delete or move them, and
`add_drawing_view(display_mode='shaded_edges')` produced unshaded line art.

## Things that are true and inconvenient

- 46 tools is a lot of tool-list tokens on every turn. Filter them to the 17 in
  `tools-used.md`.
- SolidPilot is AGPL-3.0. Do not patch it in place.
- Curved vanes are fine to build from scratch because circular arcs are in the
  vocabulary. Imported B-spline vanes from a donor part would not be.
- Do not try to reuse a donor calliper. The predecessor measured three real
  callipers; none fitted a 68 mm pad stack, and one imported cleanly but landed
  entirely inside the rotor ring where it rendered as nothing.
