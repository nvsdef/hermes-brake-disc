# The calliper: built in SolidWorks, deleted from the simulation copy

The calliper is part of the product and part of the CAD gate (PAD-05 clearance,
zero interference), so it is built, measured and exported in `brake.step`. It is
**not** a thermal zone: THM-06 is deferred and the thermal model has 27 solids.
SpaceClaim removes it from the simulation copy before exporting the PMDB. One
export plus one documented subtraction cannot drift apart; two exports can.

```
SolidWorks   brake.step    28 solids, calliper included
SpaceClaim   identify all 28 -> name and tag the 27 -> delete the calliper LAST -> export PMDB
PMDB         27 solids
Fluent       27 solid cell zones
```

## 1. Identify it by this run's measured signature

Use the calliper row of **this run's** `cad_report.json` (volume, centroid, bbox),
which the lead passes in the commission. The PRD values are:

| Quantity | PRD value |
|---|---|
| volume | 617 081.48 mm^3 = 6.170815e-4 m^3 |
| centroid | (146.143, 0.000, +0.369) mm |
| bbox | x 81.245 to 200.000, y -98.418 to 98.418, z -57 to +57 mm |

**Never use the predecessor's 6.113e-4 m^3 signature.** That calliper had windows
on a different z band than its slot; the PRD aligned them (z = -39 to +38.6), which
changed the volume by about 1 %. A 5 % window around the old value would still
catch the new body, but only by luck.

The calliper is unambiguous against the others: the closest body by volume is a
cheek (571 769.86 mm^3, 7.3 % smaller) but its centroid is on the axis at
z = +/-11, while the calliper's centroid is at x = 146 mm. Match on **volume and
centroid together**, and require **exactly one** match. Report the runner-up and
its distance in `calliper_match` to prove uniqueness. Zero or two matches: stop
and delete nothing. Deleting the wrong body is unrecoverable in the session and
surfaces three stages later as a missing zone.

## 2. Suppression is not deletion

The predecessor verified that `Body.set_suppressed(True)` returns cleanly,
`is_suppressed` reads `True`, and the PMDB export **ignores it**: the suppressed
calliper meshed anyway as an extra cell zone. Suppression is a design-tree state;
the physics export does not consult it. Delete the body from the SpaceClaim
session. That is safe, because the SolidWorks part and the STEP are the source of
truth and the SpaceClaim session is transient.

## 3. Delete it last

Deleting a body can invalidate other body and face handles in the session. The
predecessor's next `body.faces` call died with a Geometry service error (resource
not found) and killed the service. Order:

```
import -> measure all 28 -> identify -> rename -> named selections on the 27
       -> measure areas and contacts -> delete the calliper -> re-read -> export PMDB
```

## 4. Prove removal by volume arithmetic on a re-read design

Neither the API's return value nor a count from a cached body list is proof: a
predecessor case recounted a cached list and reported the wrong number of bodies
after a deletion. Re-read the design from the session, then:

```
28-body total (measured)            2 647 566.01 mm^3   (PRD)
- calliper (measured signature)       617 081.48 mm^3
= expected 27-body total            2 030 484.53 mm^3
  measured 27-body total, re-read   <value>
  residual                          <value>   gate: |drop - calliper| <= 0.5 % of the calliper volume
```

Record in `tag_report.json` -> `after_delete`: `imported_body_count` 28,
`body_count` 27 (re-read), `total_before_mm3`, `total_after_mm3`,
`volume_drop_mm3`, `calliper_volume_mm3`, `drop_error_pct`. Then check again in
Fluent: 27 solid zones and no zone whose volume is near 6.17e-4 m^3.
