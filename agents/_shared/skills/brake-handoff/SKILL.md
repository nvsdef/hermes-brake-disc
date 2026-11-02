---
name: brake-handoff
description: "Lead's stage contract: artifacts, hashes, areas, timing."
version: 1.2.0
author: "sdefibaugh"
license: Apache-2.0
platforms: [windows]
metadata:
  hermes:
    tags: [brake, handoff, contract, lead]
---

# brake-handoff - the contract between CAD, SpaceClaim and Fluent (PRD H1.2)

**Who loads this skill:** only the **lead**, to write commissions and check gates.
Children do not load it in H1.2; the lead copies the parts they need (input
hashes, output contract, gate numbers, timing block) into each commission, and
each specialist's own skills carry the method. If you are a child and reading
this, you may use it for reference, but your commission and your own skills
govern.

It owns the **boundaries** between stages: which files cross them, what they
must contain, how names survive (or do not survive) each hop, which units each
tool speaks, and the area and volume arithmetic that proves nothing was lost in
transit. It does not teach how to build, tag, mesh or solve.

The authorities are `specs/PRD.md` (numbers) and `specs/handoffs.md` (files,
keys, gates). This skill restates their numbers exactly.

| Reference | Open it when |
|---|---|
| `references/artifact-contract.md` | writing a commission's output contract or reading a stage artifact: common fields, timing, per-gate files, the hash chain |
| `references/naming-chain.md` | a name is missing downstream, a glob matched nothing, or someone proposes relying on a SolidWorks name |
| `references/units-and-scale.md` | a measured size is off by 25.4 or 1000 |
| `references/calliper-removal.md` | the body count is still 28 after Gate 2, or the calliper match is ambiguous |
| `references/area-reconciliation.md` | a wall-vent, wall-outer or contact area gate fails, or you need to know where the predicted areas come from |
| `references/failure-modes.md` | something broke at a stage boundary and you want the symptom and owner table |

## 1. Boundary checklist (lead, at every gate)

- [ ] Input hashes the child reports equal the hashes you put in its commission.
- [ ] Common fields present: `run_id`, `prd_revision` = `"H1.2"`,
      `producing_role`, `started_at`, `finished_at`, `status`, `inputs_sha256`.
- [ ] `timing` block present (`started_at`, `finished_at`, `tool_calls`,
      `app_launches`); copied into `BUILD_STATE.timing`.
- [ ] Body count and total volume match section 3 within 1 % (0.5 % for the
      calliper drop).
- [ ] Face-group areas within 2 % **on the right basis**: before imprint at
      Gate 2, after imprint at Gate 3.
- [ ] 45 contacts (Gate 2) or 45 coupled pairs (Gate 3), with areas within 2 %.
- [ ] Every output file hashed by you; hashes written to `BUILD_STATE.json`.

## 2. The chain at a glance

```
lead        00_lead\case.json                          duty cycle, materials, numerics
   |
solidworks  10_cad\*.SLDPRT (9), brake.SLDASM (9 comp.) 28 bodies, true global position
            10_cad\brake.step                          28 manifold solids, calliper INCLUDED
            10_cad\cad_report.json                     signatures, assembly.component_count,
                                                        step.manifold_solid_count, hashes, timing
                                                        (FROZEN at Gate 1)
   |
spaceclaim  20_spaceclaim\cad_iso.png                  full assembly with calliper (before delete)
            20_spaceclaim\cad_section_9deg.png         GEO-06 section through the vent inlet
            20_spaceclaim\brake.pmdb\brake.pmdb        FOLDER + inner file: 27 bodies, 29 selections
            20_spaceclaim\named_selections.png         wall-vent and wall-outer coloured
            20_spaceclaim\tag_report.json              body map, areas, 45 contacts, timing
   |
fluent      30_fluent\brake.msh.h5, mesh_report.json   27 solid zones, 45 coupled pairs (internal gate)
            30_fluent\setup_report.json, results.json  readback, temperatures, energy audit, timing
            30_fluent\ mesh images, contours, histories\*.csv
   |
lead        50_report\review.json, review.md           the verdict, deliverables, timing table
            50_report\report.pdf, manifest.json        verdict first; drawing listed as DESCOPED
```

**No 2D drawings in H1.2.** There is no `40_drawing` folder, no
`rotor_only.SLDASM`, no Gate 5 and no drawing report. CAD visuals are captured in
SpaceClaim from the imported STEP at Gate 2.

**One geometry.** The STEP exported at Gate 1 is the only geometry. SpaceClaim
removes the calliper from a *simulation copy* and adds names; it never edits a
shape. Fluent meshes what SpaceClaim exported. Nobody repairs another stage's
geometry: a defect goes back to its owner with the measurement that proves it.

## 3. Rules at a boundary

1. **Check the input hash before opening the input.** A mismatch means the wrong
   file: stop.
2. **PMDB is a folder.** The SpaceClaim export creates `brake.pmdb\` containing
   the file `brake.pmdb`. Hash and import the **inner file**. Opening the folder
   as a file gives `PermissionError: [Errno 13]` on Windows; that is a path
   error, not a bad export.
3. **Units in key names** (`volume_m3`, `centroid_mm`, `area_mm2`, `peak_k`,
   `E_applied_j`). Unavailable values are `null` with a `reason`, and the status
   is then FAIL, OPEN or BLOCKED, never PASS.
4. **Identify bodies by measured signature, never by name.** STEP carries no
   face names, and the importer's body names are feature-derived
   (`CirPattern1`). Volume plus centroid plus bbox identifies each of the 28.
5. **PMDB or nothing into Fluent.** Meshing the STEP loses every named selection;
   the solve then finishes "successfully" flat at 300 K.
6. **Never tag a contact face.** Pad/cheek, pad/backing, the 40 vane/cheek faces
   and the hat/cheek_in cylinder become coupled interfaces through shared
   topology. A named selection on any of them makes an uncoupled wall. Nothing
   warns you.
7. **One Ansys session at a time, kept alive per stage.** SpaceClaim and Fluent
   share the licence. One launch per stage; each Ansys role closes what it
   opened before handing back.
8. **Assert areas, not counts** (`references/area-reconciliation.md`).
9. **Count at the source.** Gate 1 is not passed until the lead has read
   `assembly.component_count` 9 and `step.manifold_solid_count` 28 and counted
   the STEP text itself. Run 1 sent a 23-solid STEP downstream.

## 4. The numbers that cross the boundaries (PRD sections 4 and 6)

| Quantity | Value | Checked at |
|---|---|---|
| assembly components | 9 | Gate 1 |
| bodies in STEP | 28 manifold solids (9 parts; `vanes` holds 20); 10 PRODUCT entities | Gate 1, Gate 2 import |
| rotor volume (cheeks + vanes + hat) | 1.801777e-3 m^3 = 1 801 776.57 mm^3 | Gate 1, Gate 2 scale |
| all 28 bodies | 2 647 566.01 mm^3 | Gate 2 scale |
| calliper | 617 081.48 mm^3, centroid (146.143, 0.000, +0.369) mm, bbox x max 200.0 mm | Gate 1, Gate 2 match |
| 27 bodies after calliper deletion | 2 030 484.53 mm^3 | Gate 2 |
| rotor OD / z extents of the 28-body model | 330 mm / -57 to +57 mm | Gate 2 scale |
| named selections | 27 bodies + `wall-vent` + `wall-outer` = 29 | Gate 2 |
| wall-vent / wall-outer / pad-backing exposed, before imprint | 167 037.60 / 240 205.78 / 42 997.28 mm^2 (each +/- 2 %) | Gate 2 (SpaceClaim) |
| wall-vent / wall-outer / pad-backing exposed, after imprint | 142 865.51 / 228 477.17 / 31 268.67 mm^2 (each +/- 2 %) | Gate 3 (Fluent mesh) |
| contacts / coupled pairs | 45: 2 pad/cheek, 2 pad/backing, 40 vane/cheek, 1 hat/cheek_in | Gate 2, Gate 3 |
| contact areas | 5 864.31 (pad faces), 604.30 (vane), 5 969.03 (hat) mm^2 | Gate 2, Gate 3 |
| hat/vanes | edge only at r = 95, z = -6: **no** face contact | Gate 2 |
| solid / fluid zones | 27 / 0 | Gate 3 |
| rotating zones | `cheek_out`, `cheek_in` only, axis +Z through the origin | Gate 3 |
| screenshots | `cad_iso.png`, `cad_section_9deg.png`, `named_selections.png`, each > 20 kB | Gate 2 |

## 5. Axis, frame and direction

Z is the shaft axis, origin at the vent mid-plane, +Z outboard (towards the wheel
and the mounting face at z = +43). Pads are centred on +X. Angles are measured
from +X towards +Y. The rotor turns **clockwise viewed from +Z**:
omega0 = -84.1751 rad/s about +Z. Nothing is moved or re-oriented at any hop.
The published PyFluent example's rotation axis `[0, 1, 0]` through
`[-0.035, -0.821, 0.045]` belongs to a different mesh and rotates about a line
outside this part without any error message.

## Verification

At every boundary the lead can answer yes to all of these before commissioning
the next stage:

1. The input hashes equal the hashes in the commission, and the PMDB hash is of
   the inner file `brake.pmdb\brake.pmdb`.
2. Gate 1: 9 assembly components and 28 STEP solids, read from the report and
   counted by the lead.
3. The body count and the total volume match section 4 within 1 % (0.5 % for
   the calliper drop), and the calliper match was unique.
4. The face-group areas match within 2 % on the right basis, and no contact face
   carries a named selection.
5. The 45 contacts (Gate 2) or coupled pairs (Gate 3) exist with areas within 2 %.
6. Every JSON artifact carries the common fields with `prd_revision` "H1.2", a
   `timing` block, and units in the key names.
7. No folder or commission creates a drawing stage; the review lists the drawing as DESCOPED.
