---
name: sw-solidpilot
description: "Drive SolidWorks through SolidPilot: calls, traps, checks."
version: 1.2.0
author: "sdefibaugh"
license: Apache-2.0
platforms: [windows]
metadata:
  hermes:
    tags: [brake, solidworks, solidpilot]
---

# Driving SolidWorks through SolidPilot (PRD H1.2)

SolidPilot drives a live SolidWorks 2026 GUI over COM. This skill is the tool
checklist that `sw-rotor-build` and `sw-pads-calliper` both use. Run 1 built
perfect geometry but took about 90 minutes. The time went on hand-computed
coordinates, per-feature measuring and a missing assembly check. The target is
**12 to 15 minutes and about 115 tool calls** for the whole CAD stage.

## When to use

Every time you call a SolidPilot tool.

## Checklist

**1. Match tool names on the suffix.** Hermes exposes `create_sketch` as
`mcp_solidpilot_create_sketch` or `mcp__solidpilot__create_sketch`. The only
tools this stage needs are listed in `references/tools-used.md`. Never call
`submit_feature_graph`, `rebuild_from_ir`, `create_pattern`, `modify_dimension`,
`save_body_as_part` or `add_mate`. Each one reported success on this brake
while producing wrong geometry (`references/tool-traps.md`).

**2. Start the session: 2 calls.**
- `ensure_ready` once. A cold launch takes 30 to 60 s. Do not call it twice
  during launch.
- `verify_state`. Record the documents already open. They are not yours: never
  close, save over or edit them.
- Write down `started_at` and start a running tool-call count for `timing`.
- Done when: SolidWorks is visible and ready.

**3. Use these planes. Never guess a basis.** `create_sketch` returns the frame
(`origin`, `xdir`, `ydir`). Check it against this table before adding entities.

| Plane | origin | xdir | ydir | Used for |
|---|---|---|---|---|
| `Front Plane` | [0, 0, 0] | +X | +Y | vanes, vane trim, hat holes, calliper base |
| offset of `Front Plane` by d | [0, 0, d] | +X | +Y | cheeks, pads, plates, calliper cuts |
| `Right Plane` | [0, 0, 0] | [0, 0, -1] | +Y | hat polygon (sketch x = -z) |

API idiom (offset plane, returns its name, for example `Plane1`):
`add_reference_geometry(type='plane', ref_plane_name='Front Plane', offset=-0.022)`.
A negative offset works. Use the returned name in `create_sketch(plane=...)`.
On-miss: if `origin[2]` differs from the offset by more than 1e-9 m, delete the
plane with `edit_feature(action='delete')` and create it again.

**4. Every body is a mid-plane extrude about its band centre.** Put the plane at
(a + b) / 2 and use `mid_plane=true`, `depth` = b - a (the total width). Never
use `reverse` or a blind one-sided extrude for a body. Band table:

| Part | Plane offset (m) | Mid-plane depth (m) |
|---|---|---|
| `cheek_out` / `cheek_in` | +0.011 / -0.011 | 0.010 |
| `vanes` | `Front Plane` | 0.012 |
| `outerpad` / `innerpad` | +0.022 / -0.022 | 0.012 |
| `bp_outer` / `bp_inner` | +0.031 / -0.031 | 0.006 |
| `calliper` base | `Front Plane` | 0.114 |

**5. Copy sketch data from the data cards. Never compute or rotate coordinates
in the loop.** The cards are in the `sketch-data.md` reference of
`sw-rotor-build` (R1 to R8) and of `sw-pads-calliper` (P1, P2, C1 to C4). Pass a card's text as the
`segments` **string**: `{"segments": "[{...},{...}]"}`, not a raw array.
- Keep one call to 20 records or fewer (the 30 s ceiling).
- Compare the returned `segment_count` and per-type counts with the card.
- On-miss: the call is not transactional. Read the sketch with
  `analyze_model('sketch', name=...)`, then delete the sketch and re-send the
  card. Never add constraints.

**6. One part = one short fixed sequence (about 7 calls).**
```
open_new_part
add_reference_geometry(type='plane', ...)     # only if the band needs it
create_sketch(plane=...)                      # check the frame
add_sketch_entities(segments=<card>)          # check the counts
extrude_feature(...)                          # check result_geometry.volume
analyze_model('mass_properties')              # ONE measurement per part
save_document(file_path='C:\\brake-runs\\<run-id>\\10_cad\\<part>.SLDPRT')
```
Extra features add `create_sketch`, `add_sketch_entities` and `extrude_feature`.
Leave the saved part open. Do not close and reopen it.

**7. Measure once per part.** Check every feature against its card with
`result_geometry.volume`, because that read costs no call. Call
`analyze_model('mass_properties')` **once**, after the last feature of the part.
Print:
```
<part> volume_m3   expected <PRD>  measured <v>  delta <pct> %  PASS|FAIL
<part> centroid_mm expected (x, y, z)  measured (x, y, z)  max delta <mm>  PASS|FAIL
```
Multiply m^3 by 1e9 to get mm^3 and m by 1e3 to get mm. There is no mass in the
answer: mass = volume x PRD density. The vanes use `analyze_model('bodies')`
instead, because they are 20 bodies. The z extents of all 28 bodies are
measured once, at the STEP re-import (`sw-pads-calliper` step A8). Methods for
the other bbox components are in `references/measuring.md`.

**8. Timeouts: inspect first, then retry.** Every call has a fixed 30 s ceiling.
A timeout means "unknown". Call `verify_state`, then
`analyze_model('features')`. Repeat the call only if its feature is missing. A
call that hangs with no error means a modal dialog is open: tell the lead that a
human must look at the screen.

**9. HALT.** On a FAIL, delete the failing feature
(`edit_feature(feature_name=..., action='delete')`), rebuild it from the same
card and re-measure. You get two repairs. On the third FAIL, stop and return
both measured numbers to the lead. Never change a PRD number.

**10. STEP export and counting.** Details are in `references/step-export.md`.
- Export only after `analyze_assembly` shows 9 components.
- Count `MANIFOLD_SOLID_BREP` in the file, then count PRODUCT with the regex
  `= ?PRODUCT ?\(`. Expect 28 and 10. The export status is not a count.

**11. Python and the terminal.** Never type bare `python` or `python3`, because
it opens a Windows Store installer on this machine (run 1 lost time here). For
arithmetic, hashes or counts, use the `execute_code` tool. Without it, use
`C:/solidpilot/.venv/Scripts/python.exe`. PowerShell also works:
`(Select-String -Path <file> -Pattern 'MANIFOLD_SOLID_BREP').Count` and
`Get-FileHash <file> -Algorithm SHA256`.

## Units

Every SolidPilot length is **metres**, and every volume is m^3. The PRD is in
mm: convert once, at the call. `extrude_feature(angle=...)` takes degrees. If a
cheek volume comes back as 571 769.86, the document is in mm. Stop and find out
why.

## Materials

Do not call `set_part_material`. It costs a call per part, and material in CAD
is cosmetic here: mass = measured volume x PRD density. In `cad_report.json`,
record `cad_material: null` with the reason "mass from PRD density".

## References

- `references/tools-used.md` - the tool include list and the tools that stay
  excluded.
- `references/tool-traps.md` - every "reports success, did something else"
  finding, with measured evidence.
- `references/frames-and-placement.md` - plane frames, offset planes,
  identity transforms.
- `references/measuring.md` - bbox methods, face-area checks, sliver checks.
- `references/step-export.md` - export, counting, re-import.

## Verification

This skill was followed if all of these are true:

- `ensure_ready` appears once. The documents that were open before you started
  are untouched.
- The transcript has no `submit_feature_graph`, `rebuild_from_ir`,
  `create_pattern`, `auto_dimension_drawing` or drawing call.
- Every `add_sketch_entities` call used a data card as a string, and its counts
  matched the card.
- Each part has exactly one `analyze_model` measurement (`bodies` for the
  vanes), with printed expected / measured / delta / PASS lines.
- Every timeout was followed by an inspection before any retry.
- The STEP was counted in the file: 28 `MANIFOLD_SOLID_BREP` and 10 PRODUCT.
- No bare `python` was typed in the terminal.
