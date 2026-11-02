# Sizing, the Student cell cap, and friction-face resolution

Open this when choosing or changing mesh sizes, when cells + nodes approach
512 000, or when measuring and explaining the friction-face resolution.

## The starting recipe (PRD section 6)

| Control | Value |
|---|---|
| Global min size | 2.2 mm |
| Global max size | 20 mm |
| Growth rate | 1.2 |
| Curvature normal angle | 18 deg |
| Local size, cheeks (2 bodies) | 4 mm |
| Local size, vanes (20 bodies) | 5 mm |
| Local size, hat (1 body) | 8 mm |
| Volume fill | poly-hexcore |
| Inflation layers | none |
| Region type | all solid |

The PRD calls this a **starting point, not evidence**. The global max is loose on
purpose: the local controls spend the budget where the answer lives.

## The licence ceiling comes first

Ansys Student caps **cells + nodes** at 512 000. It is the sum, not cells. On a
poly-hexcore mesh nodes outnumber cells by roughly 5 to 6 times. The predecessor
measured 72 980 cells and 404 958 nodes, a sum of 477 938 (93.4 % of the cap),
with a similar recipe. That is an illustration of how tight it is, not a target.

Before relying on the cap, confirm which licence is installed. The PRD gate
applies "if running Ansys Student". Record the product name from the Fluent
banner in `mesh_report.json`. A commercial licence has no such cap, but a mesh
built to exceed 512 000 cannot be rerun on Student.

## Budget priority

**Friction face first, then the cheeks, then the vanes and the hat.** The bulk
rotor rise is about 42 K (PRD section 5) while the friction surface rises by
hundreds of kelvin. The steep gradient at the friction face is the answer.

If cells + nodes go over the cap, coarsen in this order and re-measure after
each change:

1. hat local size (8 mm upward);
2. vane local size (5 mm upward, but see the next section);
3. global max size.

**Never coarsen the global min size, the cheek size or the pads to hide a
licence overrun.** Do not coarsen critical friction faces to conceal a licence
failure: PRD section 7 makes a friction-face cell coarser than the penetration
depth NOT ADJUDICABLE. Every change is a documented deviation from
the PRD section 6 starting recipe, recorded with the before and after counts.

The 12 mm vane web and the 6 mm-wide vane section set a floor: volume fill can
fail on the vanes if the min size is too coarse. If it does, report the error
and the sizes; the fix is a smaller local vane size and a re-budget elsewhere.

## Measuring the friction-face resolution

`mesh_report.json.friction_face_resolution` is read by the postprocessing
skill and by the lead's temperature disposition. **Without it every thermal
requirement becomes NOT ADJUDICABLE by default.** Measure it here, per run, for
four sides: the cheek side and the pad side of each of the two friction pairs.

For each side:

- **In-plane edge**: `sqrt(facet-average face area)` on the friction wall, or the
  face-area average reported as an edge.
- **Wall-normal cell size**: (area-average of the adjacent `cell-volume` on
  that wall side) / (mean face area). On anisotropic poly-hexcore near-wall
  cells this is often about half the in-plane edge.

Report **both** numbers. The wall-normal size is the one that sets how well the
through-thickness gradient is resolved, but it is also the flattering one. Leaving
out the worse number hides a choice the reader cannot see.

API idiom - two pooled surface reports on one friction side:
```python
rd = solver.settings.solution.report_definitions.surface
rd["rp-facearea"] = {}; rd["rp-facearea"].report_type = "surface-facetavg"
rd["rp-facearea"] = {"field": "face-area-magnitude", "surface_names": [side]}
rd["rp-cellvol"] = {}; rd["rp-cellvol"].report_type = "surface-areaavg"
rd["rp-cellvol"] = {"field": "cell-volume", "surface_names": [side]}
```
Field names vary by version (`face-area-magnitude`, `cell-volume`). If a field
is refused, record the refusal and try the documented alternative. Never fill the
key with a number from another run.

Also record `cell_size_by_zone` for all 27 zones: the equivalent edge
`(volume-average of cell-volume)^(1/3)` and the maximum cell volume, from pooled
volume reports.

## What the resolution can and cannot support

The thermal penetration depth at time t is `delta = sqrt(alpha x t)`, with
`alpha = k / (rho x cp)` from PRD section 7:

| Material | alpha, m^2/s | delta at 0.1 s | delta at 1.77 s (ts / 2) | delta at 3.54 s (ts) |
|---|---|---|---|---|
| grey iron (MAT-01) | 1.6157e-5 | 1.27 mm | 5.35 mm | 7.56 mm |
| pad compound (MAT-02) | 5.3333e-7 | 0.23 mm | 0.97 mm | 1.37 mm |
| backing steel (MAT-03) | 4.0436e-6 | 0.64 mm | 2.68 mm | 3.78 mm |

Write the ratio `delta / wall-normal cell size` for both friction sides at the
three times into the report. When the ratio is below 1, the whole gradient lies
inside one cell, and the cell value reads **below** the true surface temperature.

The predecessor measured a pad-side wall-normal cell of 1.90 mm against a pad
penetration of 1.37 mm at the end of the stop: 0.72 cells across. Under the
Student cap that is typical. The consequence is set by the PRD: if the
friction-face cell is coarser than the penetration depth, the pad temperature
requirement is **NOT ADJUDICABLE** from this mesh.

## Deriving a resolution target

If the lead asks what it would take, derive the target from a stated criterion,
and show the arithmetic. For "at least N cells across delta", the target
wall-normal size is `delta / N`. For N = 5 on the pad at the end of the stop:
1.37 mm / 5 = 0.27 mm. The predecessor once printed a 0.14 mm target beside a
5-cell criterion; 0.14 mm is about 10 cells. Two numbers on one line that do not
agree are a defect. Compute the target from the criterion every time.

A target like 0.27 mm at the two friction patches does not fit the full assembly
under the Student cap. The route the predecessor identified is a **60 deg
pad-and-cheek submodel**: one sector of pad, backing plate and cheek with the far
field truncated. That is a new analysis for the lead to commission, not something
to attempt inside this stage.
