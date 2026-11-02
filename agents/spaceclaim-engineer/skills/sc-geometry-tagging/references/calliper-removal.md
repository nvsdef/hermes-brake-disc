# Removing the calliper from the working copy

Open this before steps 5 and 7 of SKILL.md, when the calliper match is not
unique, when the count is still 28 after deletion, or when the geometry service
reports a missing resource.

## Why it goes, and where

The calliper stays in the CAD and in `brake.step`: Gate 1 checks it, and it
appears in `cad_iso.png`, which is taken **before** the deletion. It is not a
thermal zone: PRD section 6 solves 27 solid zones, and THM-06 (calliper and
fluid temperature) is deferred. It is deleted from the SpaceClaim design only,
never from the STEP or the native files.

## The signature: PRD, not history

| Source | Value | Status |
|---|---|---|
| PRD section 4 | 617 081.48 mm^3; centroid (146.143, 0.000, +0.369); bbox x = 81.245 to 200.000, y = -98.418 to 98.418, z = -57 to +57 | **acceptance value** |
| Gate 1 `cad_report.json` calliper row | this run's SolidWorks measurement | cross-check |
| Run 1 SpaceClaim measurement | 617 071.6 mm^3, bbox centre x = 140.6228 | illustration only |
| Predecessor `tag.py` | 6.113384e-4 m^3 with a 5 % band | retired geometry, never use |

The predecessor value is 0.93 % below the PRD, so a 1 % volume test cannot tell
the geometries apart, and its 5 % band overlaps the cheek volume.

## Unique match: three tests, all required

A body is the calliper when **all three** hold (handoffs Gate 2):

| Test | Expected | Tolerance |
|---|---|---|
| volume | 617 081.48 mm^3 | 1 % |
| mass centroid z | +0.369 mm | 0.1 mm |
| bbox x max | 200.000 mm | 0.05 mm |

Also report the full centroid, the full bbox and the Gate 1 deltas. The centroid
z comes from the tessellated mass centroid (`body-signatures.md`): the
asymmetric slot (z = -39 to +38.6) and piston bores put it at +0.369, while the
bbox centre is 0.0. Run 1 used the bbox centre and got 2 candidates, then 0.

- **Exactly one candidate:** proceed.
- **Zero or two or more:** delete nothing, never pick the closest. Report every
  body with volume within 5 % of the PRD calliper or bbox x max above 190 mm,
  with its full signature. If the centroid could not be computed, the match is
  OPEN: report, do not delete.

## Deleting, in its own step

The deletion is one short step script with its own connect and disconnect
(`persistent-session.md`). It:

1. Re-reads the design and re-identifies the calliper by the three tests on
   the **fresh** objects (the ids from step 5 are a cross-check only).
2. If no candidate exists **and** 27 bodies are present, the deletion already
   happened in an earlier try: skip to the proof. Never delete twice.
3. Records the total volume of all bodies, then `design.delete_body(calliper)`.
4. Re-reads with `design = m.read_existing_design()` and proves the result.

Why the call proves nothing: `delete_body` searches the component tree and,
when the body is not found, only logs a warning and returns `None`.
`body.set_suppressed(True)` is **not** removal: `export_to_pmdb()` ignores
suppression, and the predecessor's suppressed calliper meshed as a 28th zone.
Do not call it.

## Stale handles

After a deletion every older body, face and edge object is invalid. The
predecessor's next `body.faces` on an old handle ended the session with
`GeometryExitedError ... Resource '0:31/0:38' not found`. The step design
avoids this naturally: every later step starts a new process, re-reads the
design and re-identifies bodies by signature. Never carry face ids from before
the deletion into a later step.

## The proof, on the re-read design

| Check | Expected | Gate |
|---|---|---|
| body count | 27 | exact |
| (total before - total after) / calliper volume - 1 | 0 | within 0.5 % |
| total after | 2 030 484.57 mm^3 | within 1 % |
| surviving body matching the calliper tests | none | exact |
| global z extent after | -34 to +43 mm | 0.05 mm |

Run 1 measured 27 bodies, 2 030 484.52 mm^3 and z = -34 to +43 after the
deletion: the call and the re-read work on 26.1. A count on a cached list is
not proof (the predecessor reported 6 bodies from a stale list), and a count
alone is not proof (a wrong body deleted also leaves 27). If
`read_existing_design()` raises, removal is unproven: FAIL, do not export.

## Record in tag_report.json

```
"calliper_match": {"candidates": 1, "body_id": "...", "volume_mm3": ...,
  "expected_volume_mm3": 617081.48, "volume_delta_pct": ...,
  "centroid_mm": [...], "expected_centroid_z_mm": 0.369, "centroid_z_delta_mm": ...,
  "bbox_mm": [...], "expected_bbox_x_max_mm": 200.0, "bbox_x_max_delta_mm": ...,
  "gate1_volume_delta_pct": ..., "unique": true, "pass": true},
"after_delete": {"refresh_method": "modeler.read_existing_design", "body_count": 27,
  "total_before_mm3": ..., "total_after_mm3": ..., "drop_vs_calliper_pct": ...,
  "expected_total_after_mm3": 2030484.57, "calliper_survivors": 0,
  "z_extent_mm": [-34.0, 43.0], "pass": true}
```

If the mesh at Gate 3 shows 28 solid zones, this stage failed whatever the
report says. Rerun it; never delete the zone in the mesher.
