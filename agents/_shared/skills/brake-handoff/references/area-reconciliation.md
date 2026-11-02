# Face-group areas - where the predicted areas come from

A face count tells you a query returned faces. An area tells you it returned the
right ones. Every face-group and contact gate in this package is an area gate with
a 2 % band.

## 1. wall-vent (PRD section 4)

`wall-vent` is every rotor face that bounds the vent passages: the two cheek inner
faces (z = +6 on `cheek_out`, z = -6 on `cheek_in`) and the 20 vanes' flanks and
radial ends. It carries h_ref = 130 W/(m^2 K) and is the only place the vanes do
anything thermal (THM-05). There are no hole bores: the model has no
cross-drilling.

```
cheek inner face, one annulus r = 95 to 165     pi (165^2 - 95^2)  =  57 176.99 mm^2
two cheek inner faces                                               = 114 353.97 mm^2
40 vane footprints (20 vanes x 2 faces x 604.302)                   =  24 172.08 mm^2
cheek inner faces after the footprints are carved out               =  90 181.88 mm^2   (PRD)
20 vane flanks and radial ends (12 mm tall)                         =  52 683.63 mm^2   (PRD)

wall-vent BEFORE imprint (full cheek faces + vane sides)            = 167 037.60 mm^2   (Gate 2, SpaceClaim, +/- 2 %)
wall-vent AFTER shared-topology imprint                             = 142 865.51 mm^2   (Gate 3, Fluent mesh, +/- 2 %)
```

Why two numbers: before shared topology, the cheek inner face is one whole annulus
and the vanes simply sit on it. Imprinting splits off the 40 footprints, which
become coupled interfaces (not walls), so the exposed wall area drops by exactly the
footprint area. SpaceClaim tags whole faces before imprint (imprinting is not
applied in the PMDB; Fluent creates the shared faces after surface meshing), so
**Gate 2 checks the before-imprint column and Gate 3 checks the after-imprint
column** (PRD section 4, handoffs Gates 2 and 3).

| Where | Measured | Meaning | Action |
|---|---|---|---|
| SpaceClaim (Gate 2) | about 167 037.6 (+/- 2 %) | tagged faces, before imprint | PASS |
| SpaceClaim (Gate 2) | about 171 062 (+2.4 %) | hat step face (z = -6, r = 88 to 95) put in vent; it is `wall-outer` by decision | FAIL; reclassify |
| Fluent (Gate 3) | about 142 865.5 (+/- 2 %) | after imprint | PASS |
| Fluent (Gate 3) | about 167 037.6 | shared topology carved nothing: the vanes and cheeks are not coupled | FAIL; the assembly is thermally disconnected |
| either | anything else | wrong faces selected | FAIL; list the faces and their areas |

## 2. Contacts (PRD section 4)

| Pair | Surface | Area mm^2 | Count |
|---|---|---|---|
| outerpad / cheek_out | z = +16, pad sector r 120 to 160, 60 deg | 5 864.31 | 1 |
| innerpad / cheek_in | z = -16, same sector | 5 864.31 | 1 |
| outerpad / bp_outer | z = +28, the pad back face | 5 864.31 | 1 |
| innerpad / bp_inner | z = -28 | 5 864.31 | 1 |
| vane_k / cheek_out | z = +6, vane section | 604.30 | 20 |
| vane_k / cheek_in | z = -6, vane section | 604.30 | 20 |
| hat / cheek_in | cylinder r = 95, z = -16 to -6 (2 pi x 95 x 10) | 5 969.03 | 1 |
| hat / vanes | edge only at r = 95, z = -6 | 0 (no face contact) | - |
| **total** | | | **45** |

A pad/cheek contact that measures about 57 177 mm^2 (the whole cheek face) means
the pad outline was not imprinted: the contact is the full annulus and the heat
source would be spread over the whole face. FAIL, and fix the imprint.

A pad/backing contact is the pad's back face (5 864.31 mm^2), not the backing
plate's larger face (sector r 115 to 165: (pi/6)(165^2 - 115^2) = 7 330.38 mm^2).

## 3. Exposed faces carved by the pads (wall-outer)

`wall-outer` is every other exposed rotor and hat face, including the hat step
face at z = -6, r = 88 to 95 (by decision). PRD section 4 predicts
**240 205.78 mm^2 before imprint** (Gate 2) and **228 477.17 mm^2 after imprint**
(Gate 3, less the two pad footprints), each within 2 %. The cheek part is easy
to check by hand:

```
each cheek outer face (z = +16, z = -16), full annulus    57 176.99 mm^2
less the pad footprint                                     -5 864.31 mm^2
= exposed cheek outer face after imprint                   51 312.68 mm^2 each
cheek OD cylinders, r = 165, 10 mm tall                    10 367.26 mm^2 each
cheek_out bore, r = 95, z = +6 to +16 (exposed)             5 969.03 mm^2
(cheek_in bore is the hat contact, not exposed)
cheek contribution to wall-outer after imprint            129 328.90 mm^2
hat exposed faces (incl. step face 4 024.38)                99 148.27 mm^2
wall-outer after imprint                                  228 477.17 mm^2
```

The same before/after rule applies: before imprint the cheek contribution is
141 057.52 mm^2 (the two pad footprints not yet removed).

## 4. Pad and backing exposed faces

Given h_ref = 40 W/(m^2 K). No named selection: the fluent-engineer builds the
list at runtime from the pad and backing zones minus the contact faces (each
pad's exposed sides plus each backing plate's back and sides, plus the backing
annulus strip r 115 to 120 and 160 to 165 not covered by the pad). PRD section 4
predicts **42 997.28 mm^2 before imprint** (SpaceClaim measures it at Gate 2)
and **31 268.67 mm^2 after imprint** (Fluent at Gate 3), each within 2 %.

## 5. Asserting in Fluent

API idiom (the check, not a stage script):

```python
vent = [z for z in wall_zones if z == "wall-vent" or z.startswith("wall-vent")]
total_mm2 = sum(area_m2(z) for z in vent) * 1e6
assert abs(total_mm2 - 142865.51) / 142865.51 < 0.02, (len(vent), total_mm2)
```

Report `len(vent)` too (expect up to 22 pieces), but the area is the gate.
