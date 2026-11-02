---
name: sc-geometry-tagging
description: "Tag the brake STEP in SpaceClaim and export PMDB."
version: 2.0.0
author: "sdefibaugh"
license: Apache-2.0
platforms: [windows]
metadata:
  hermes:
    tags: [brake, spaceclaim, pyansys-geometry, gate-2]
---

# SpaceClaim geometry tagging (Gate 2, PRD H1.2)

Turn the accepted `10_cad\brake.step` (28 solids) into `20_spaceclaim\brake.pmdb`
(27 solids, 29 named selections) plus three screenshots and
`tag_report.json`. Numbers are PRD section 4; tolerances: volume 1 %, centroid
0.1 mm, bbox 0.05 mm, group areas 2 %, contact areas 1 %.

**How to work.** SpaceClaim is launched **once** by a holder job and stays
alive. Every step below is a short script (20 to 80 lines) that connects,
does one thing, prints one JSON line, writes its JSON file and disconnects with
`m.client.close()`. A crash costs seconds: fix that step and rerun it. Never
relaunch for a code error. Use only calls on `references/api-verified.md`.
Run 1 launched SpaceClaim about 25 times and never passed
(`references/run1-lessons.md`).

## Checklist

**1. Inputs.** `read_json_file` on `10_cad\cad_report.json`.
Expect 28 passing bodies, `step.manifold_solid_count` = 28, and note
`step.sha256`. On miss: stop; Gate 1 is not accepted.

**2. Preflight** (`run_ansys_script`, no SpaceClaim). Create the stage folder,
hash the STEP, list Ansys processes, check library 0.15.5, syntax-check the
holder text. Done when the hash matches and no foreign Ansys process runs.
On miss: hash mismatch is an upstream HALT; a foreign process is reported,
never killed. See `references/mcp-transport.md`.

**3. Start the session** (`submit_ansys_job`, `cwd` = stage folder; launch #1).
The holder from `references/persistent-session.md` writes `session.json`
(host, port, `transport_mode` "wnua", PID). Poll until `state` = `ready`, then
run a connect probe: `Modeler(host=..., port=..., transport_mode="wnua", timeout=20)`,
print `backend_version` (26.1.0), `m.client.close()`. On miss: follow the
fallback in `persistent-session.md`. Launch budget: 1; 2 only with a written
reason; never 3.

**4. Import and count.** `design = m.open_file(<absolute STEP path>)`,
`bodies = design.get_all_bodies()`. Expect 28 solids, 0 faces below
1e-3 mm^2, OD 330.0 mm, z = -57 to +57 mm, total 2 647 566.05 mm^3.
On miss: any count but 28 is an upstream HALT with the component list
(run 1 saw 23). See `references/step-import-and-scale.md`.

**5. Signature map and calliper match.** Per body: `volume`, `bounding_box`
(`.min_corner`/`.max_corner`), and the mass centroid from
`body.get_raw_tessellation()`; save all triangles to `tess_pre.npz`. Match the
28 PRD rows one to one; order vanes by centroid angle from 17.917 deg. The
calliper is the one body with volume 617 081.48 mm^3 AND centroid z = +0.369 mm
AND bbox x max = 200.000 mm. Done when the match matrix is a permutation and
calliper candidates = 1. On miss: 0 or 2 candidates, delete nothing and report.
See `references/body-signatures.md`, `references/calliper-removal.md`.

**6. CAD screenshots, before the deletion** (pure Python, no connection). From
`tess_pre.npz`: `cad_iso.png` (all 28 bodies) and `cad_section_9deg.png`
(plane through Z at 9 deg; measure the vent-inlet gap, about 7 mm, GEO-06).
Done when both exist, exceed 20 kB and are not one colour. See
`references/export-and-evidence.md`.

**7. Delete the calliper.** Re-identify it on a fresh read,
`design.delete_body(calliper)`, then `design = m.read_existing_design()`.
Expect 27 bodies, volume drop = calliper volume within 0.5 %, total
2 030 484.57 mm^3, z = -34 to +43 mm, no calliper survivor. If 27 bodies and no
calliper already, prove instead of deleting again.

**8. Name the 27 bodies.** Re-identify by signature, set `body.name`, and
`design.create_named_selection(name, bodies=[body])` for `cheek_out`,
`cheek_in`, `hat`, `vane_01` to `vane_20`, `outerpad`, `innerpad`, `bp_outer`,
`bp_inner`. Done when 27 selections read back, one body each.

**9. Contact graph.** One face snapshot (area, bbox, plane z and normal,
cylinder radius and axis, radius range from tessellation). Expect exactly 45
contacts: 2 pad/cheek and 2 pad/backing at 5 864.31, 40 vane/cheek at 604.30,
1 hat/cheek_in at 5 969.03 mm^2. See `references/contact-graph.md`.

**10. Classify faces.** A face is **contact** only if its **whole** area lies
inside a coincident partner face. A face that is only **partly** covered is
tagged **in full**. Write `faces.json` (face id, body, state, group, area).

| Face | State | Group | Area mm^2 |
|---|---|---|---|
| cheek inner faces z = +/-6 (20 vane footprints each) | partial | wall-vent | 2 x 57 176.99 |
| vane flanks and ends | free | wall-vent | 20 x 2 634.18 |
| vane faces z = +/-6 | full | untagged | 40 x 604.30 |
| cheek friction faces z = +/-16 (pad footprint) | partial | wall-outer | 2 x 57 176.99 |
| cheek OD, `cheek_out` bore | free | wall-outer | 2 x 10 367.26 + 5 969.03 |
| hat, all but r = 95 (step face z = -6 included) | free | wall-outer | 99 148.27 |
| `cheek_in` bore, hat r = 95 cylinder | full | untagged | 2 x 5 969.03 |
| pad friction and back faces | full | untagged | 4 x 5 864.31 |
| backing front faces (pad footprint) | partial | pad/backing | 2 x 7 330.38 |
| backing back faces, arcs, flats; pad arcs, flats | free | pad/backing | 14 660.76 + 4 718.60 + 8 957.16 |

See `references/face-classification-and-areas.md`.

**11. Before-imprint areas.** Expect `wall-vent` 167 037.60, `wall-outer`
240 205.78, pad/backing 42 997.28 mm^2, each within 2 %; report predicted
after-imprint values (142 865.51, 228 477.17, 31 268.67) from measured contact
areas. On miss: run 1 measured 52 683.6 and 28 336.5 by treating partial faces
as contact; fix the classification, not the numbers.

**12. Face selections.** Re-read, map `faces.json` ids to `f.id` of fresh faces,
`create_named_selection("wall-vent", faces=[...])` and `"wall-outer"`. Read
back: 29 selections, member areas equal to step 11 within 1e-6 relative,
disjoint, no full-contact face.

**13. Export.** `p = design.export_to_pmdb(STAGE / "brake.pmdb")`. This creates the
folder `brake.pmdb\` with the file inside; `p` is the inner file. Check
`p.is_file()`, size > 0, SHA-256 of `p`. Never open the folder.

**14. Named-selection screenshot.** Save 27-body triangles to `tess_post.npz`
(connected step), then draw `named_selections.png` coloured by `faces.json`.

**15. tag_report.json** (pure Python) with every Gate 2 key from
`specs/handoffs.md`, `prd_revision` "H1.2", `session` (launch count, PID,
port, connect calls from `connects.log`) and `timing`.

**16. Stop the session.** Write `STOP`, poll the holder to `succeeded`,
`session.json` `closed`, PID gone within 30 s (else terminate that PID only).

**17. Hand back to the lead**: checks as expected / measured / delta, paths,
hashes, launches, open findings. Not "done".

## HALT and budgets

Upstream defects (count, scale, interference, missing contact, hash): stop the
session and report; never repair CAD. A gate miss of your own: two repairs,
then HALT with both numbers. Step crashes: 3 reruns per step, 12 per stage.
Symptoms: `references/failure-modes.md`.

## Verification

Gate 2 passes only when `tag_report.json` shows, with expected, measured and
delta:

- `step_sha256` equals Gate 1; 28 solids imported; scale checks pass.
- `body_map` 28 rows, permutation, tessellated centroids checked.
- `calliper_match` exactly 1 candidate on volume, centroid z and bbox x max.
- `after_delete` 27 bodies, drop within 0.5 % of the calliper volume.
- `contact_graph` 45 rows within 1 %; no full-contact face tagged.
- `wall-vent`, `wall-outer`, pad/backing within 2 % of 167 037.60,
  240 205.78, 42 997.28 mm^2.
- 29 named selections read back.
- `pmdb_sha256` of the inner file; `cad_iso.png`, `cad_section_9deg.png`,
  `named_selections.png` exist and pass the image check.
- `session.launch_count` 1 (or 2 with a reason), PID gone before the handback.
