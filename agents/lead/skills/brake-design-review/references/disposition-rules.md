# Disposition rules - requirement by requirement

For each PRD section 7 row: where the evidence lives, the target, the PRD
prediction, and the rule that produces the disposition. "Key" means the dotted
JSON path you actually found; the names below are what the commissions asked for.
If a child wrote a different key, use the key it wrote and name it exactly.

Nominal product dimensions carry no invented manufacturing tolerance (DECISIONS
item 12). A CAD dimension PASSES when the measured value equals the PRD value
within the CAD measurement tolerance used at Gate 1 (0.05 mm for extents, 1 % for
volumes). Record the measured value to 0.001 mm so a reader can see the
precision.

## 1. CAD rows (evidence `10_cad\cad_report.json`)

| ID | Target | Class | Key (as commissioned) | PRD prediction | Rule | Owner if not PASS |
|---|---|---|---|---|---|---|
| PKG-01 | rotor OD <= 330 mm | M | `requirements.PKG-01` | 330.0 | PASS if <= 330.00 + 0.05 | solidworks-engineer |
| PKG-02 | friction ring thickness 32 mm nominal | M | `requirements.PKG-02` | 32.0 (z -16 to +16) | PASS if 32.00 +/- 0.05 | solidworks-engineer |
| PKG-03 | 5 x dia 14 on PCD 115 | M | `requirements.PKG-03` | as built | PASS if 5 holes, dia 14.00 +/- 0.05, centres at r = 57.50 +/- 0.05, angles 0/72/144/216/288 | solidworks-engineer |
| PKG-04 | centre bore dia 70 | M | `requirements.PKG-04` | 70.0 | PASS if 70.00 +/- 0.05 | solidworks-engineer |
| PKG-05 | mounting face z = +43 | M | `requirements.PKG-05` | 43.0 | PASS if +43.00 +/- 0.05 | solidworks-engineer |
| PKG-06 | wheel rim clearance >= 6 mm radial | S | none | OPEN | **OPEN**: no wheel geometry in scope | Chassis / Foundation Brake (supply wheel envelope) |
| MAS-01 | rotor mass <= 13.5 kg | M | rotor volume sum from `bodies[]` x 7200 | 12.973 kg | PASS if <= 13.5 kg; also report the solver-side mass if read back, and their agreement computed from both keys | solidworks-engineer |
| GEO-01 | two cheeks + vanes present | M | `bodies[]` | yes | PASS if cheek_out, cheek_in and 20 vanes pass Gate 1 | solidworks-engineer |
| GEO-02 | cheek thickness 10 mm each | S | cheek bbox z | 10.0 | PASS if 10.00 +/- 0.05 each | solidworks-engineer |
| GEO-03 | vent gap 12 mm | S | vane bbox z, cheek inner faces | 12.0 | PASS if 12.00 +/- 0.05 | solidworks-engineer |
| GEO-04 | curved vanes >= 18 | S | count of vane rows passing | 20 | PASS if >= 18 **curved** vanes (curvature evidenced by `vane_sweep`) | solidworks-engineer |
| GEO-05 | cross-drilled holes >= 30 | C | none | DEFERRED | **DEFERRED** Phase 3, owner Chassis / Foundation Brake: holes break the axisymmetry the solid-motion model needs; no display model is built | Chassis / Foundation Brake |
| GEO-06 | hat on inboard cheek, vent inlet open | M | `requirements.GEO-06`, hat/cheek_in contact in `tag_report.json`, `20_spaceclaim/cad_section_9deg.png` | yes, about 7 mm inlet gap | PASS if the hat/cheek_in contact is the r = 95, z -16 to -6 cylinder (5 969.03 mm^2 +/- 2 %), no hat/vane face contact, and the SpaceClaim 9 deg section shows the open inlet | solidworks-engineer |
| PAD-01 | pad sector 60 deg | M | `requirements.PAD-01` | 60 | PASS if 60.0 deg (bbox y +/- 80.000 at r = 160 confirms) | solidworks-engineer |
| PAD-02 | pad radii 120 to 160 mm | M | `requirements.PAD-02` | yes | PASS if 120.00 and 160.00 +/- 0.05 | solidworks-engineer |
| PAD-03 | pad thickness 12 mm | S | pad bbox z | 12 | PASS if 12.00 +/- 0.05 each | solidworks-engineer |
| PAD-04 | backing 6 mm steel, r 115 to 165 | S | backing bbox, radii | yes | PASS if 6.00, 115.00, 165.00 +/- 0.05 and material MAT-03 | solidworks-engineer |
| PAD-05 | calliper clears pad stack: slot >= stack + 4 mm, 0 interference | M | `clearances_mm`, `interference_mm3` | +9.6 mm, 0 | PASS if slot minus stack >= +4.0 mm **and** interference = 0 mm^3 | solidworks-engineer |

## 2. Material rows (evidence `30_fluent\setup_report.json`)

| ID | Declared | Rule |
|---|---|---|
| MAT-01 | grey iron rho 7200, cp 447, k 52 on 23 rotor zones | PASS if every rotor zone reads back exactly these values; FAIL if any zone differs (name the zone); OPEN if no readback |
| MAT-02 | pad rho 2500, cp 900, k 1.2 on outerpad, innerpad | same |
| MAT-03 | steel rho 8030, cp 502, k 16.3 on bp_outer, bp_inner | same |

A material readback of `density = 0` on a solid with flow equations off is a
known solver artefact (the predecessor saw it); the child should have read back
cp and k and the density from the material definition. If density is 0 in the
readback, the row is NOT ADJUDICABLE until the child explains the source.

## 3. Thermal rows (evidence `30_fluent\results.json`, `mesh_report.json`)

### Algorithm for THM-01, THM-02 and THM-04

```
precondition:  energy ratio in 90 to 110 %, E_applied within +/-2 %, final time 3.540681 s,
               no clipped value                       -> else NOT ADJUDICABLE (cite the audit)
range:         lower = cell maximum over the run (key A, time)
               upper = wall-layer maximum over the run (key B, time)
               (THM-04: cell max and wall-facet max over ALL rotor walls; the
                layer exists only at the friction faces, PRD section 7)
               either missing                         -> NOT ADJUDICABLE ("range incomplete")
resolution:    c = wall-normal cell size at the friction face (mesh_report)
               delta = sqrt(alpha x t_peak), at the time of the peak (PRD
                       section 7); for scale, at ts: pad 1.374 mm, iron 7.564 mm
               cells_across = delta / c
decide:        lower > limit                          -> FAIL (a cell average under a surface-heated
                                                         gradient reads below the surface value)
               c > delta                              -> NOT ADJUDICABLE (PRD section 7)
               lower <= limit <= upper                -> NOT ADJUDICABLE (range straddles)
               upper < limit                          -> PASS
margin:        only for PASS or FAIL: (limit - upper) for PASS, (lower - limit) for FAIL, in K
```

Always also record `cells_across`. The NOT ADJUDICABLE criterion is "cell no
coarser than the penetration depth at the peak" (cells_across >= 1). PRD
section 7 also makes **fewer than 5 cells across a finding**: when
1 <= cells_across < 5 the rationale says "resolution-limited: <n> cells across
the penetration depth", a finding is recorded, and the `next_step` asks for a
refinement check. DECISIONS item 11 asks for mesh sensitivity before signoff; if
none was run, record that as a finding in the rationale. A missing
mesh-sensitivity study alone is **not** a reason for NOT ADJUDICABLE (PRD
section 7).
The range is diagnostic, not a rigorous bound (DECISIONS item 11): the upper end
is the outer face of a declared 2 mm heat-generating layer, and its height above
the cell value scales with the flux times the layer thickness.

| ID | Quantity | Limit | Face for resolution | Penetration depth at ts (evaluate at t_peak) | PRD prediction |
|---|---|---|---|---|---|
| THM-01 | rotor friction-surface peak | 923 K | cheek side of pad/cheek contact | 7.564 mm (iron) | solve |
| THM-02 | pad friction-surface peak | 623 K | pad side of pad/cheek contact | 1.374 mm (pad) | solve; **expected to govern** |
| THM-04 | peak of all rotor surfaces: cell max and wall-facet max over all rotor walls | 1143 K | where the peak occurs (normally the cheek friction face) | 7.564 mm | solve |

The predecessor's pad range was [470.69, 630.66] K against 623 K with a pad
wall-normal cell of about 1.9 mm (0.72 cells across 1.374 mm). If this run looks
similar, THM-02 is NOT ADJUDICABLE for two reasons (straddle and resolution), and
the first change is to resolve the pad face, not to redesign the brake. These are
illustrations; your numbers come from this run.

### THM-03 rotor bulk temperature rise <= 60 K

Evidence: `results.json` bulk-rise key (mass-weighted mean over the 23 rotor
zones minus 300 K, at the end of the stop or its maximum; name which).
Precondition: energy audit closed. Rule: PASS if <= 60 K. Bulk rise is not
sensitive to friction-face resolution. Compare with the 41.9 K upper estimate:
a solved value above 41.9 K means more energy is in the rotor than was applied,
which is an audit failure, not a thermal result.

### THM-05 vent cooling modelled explicitly

Evidence: `setup_report.json` convection groups. PASS if `wall-vent` exists with
h_ref 130 W/(m^2 K) and its own schedule distinct from `wall-outer` (85), and its
resolved area is 142 865.51 mm^2 +/- 2 %. The rationale must say that this proves
the vent is **modelled**, not that 130 W/(m^2 K) is **validated**: h is a
prescribed input, and its 1.5 x outer basis presumes vanes pumping in the
direction of rotation (clockwise viewed from +Z for this geometry).

### THM-06 calliper / brake fluid <= 428 K

**DEFERRED**: the calliper is deleted from the thermal model (DV-09). Owner
Chassis / Foundation Brake, Phase 3. Soak-back after the vehicle stops is the
governing case for brake fluid and is entirely outside a single-stop conduction
model.

## 4. DV items

| DV | Composed from | Rule |
|---|---|---|
| DV-01 package | PKG-01 to PKG-06 | worst of the rows; with PKG-06 OPEN the item is OPEN, and the rationale says PKG-01 to PKG-05 passed |
| DV-02 mass | MAS-01 | same as MAS-01 |
| DV-03 inlet open | GEO-06 | same as GEO-06 |
| DV-04 thermal | THM-01 to THM-05 | worst of the rows (FAIL > NOT ADJUDICABLE > OPEN > PASS) |
| DV-05 energy within +/-2 % | `energy_audit.E_applied_j` / 243 055.6 J (or `energy_audit.E_applied_over_vehicle_pct`) | PASS if within +/-2 %; this is the boundary check, necessary but not sufficient (the predecessor passed it at +0.102 % while 92 % of the energy vanished inside the solver; the 90 to 110 % ratio is the check with teeth) |
| DV-06 interference | PAD-05 interference part, `interference_mm3` | PASS if 0 mm^3 |
| DV-07 fade / dyno | - | DEFERRED, Chassis / Foundation Brake, Phase 3 |
| DV-08 cracking | - | DEFERRED, same |
| DV-09 calliper / fluid | - | DEFERRED, same |
| DV-10 repeated stops | - | DEFERRED, same |

## 5. Run-level status from the rows

- Workflow status and engineering verdict are separate (PRD section 9). An
  M-class row that is FAIL or NOT ADJUDICABLE sets the engineering verdict
  (for example "not verified" or "does not meet"), not the workflow status.
- `complete` needs all PRD section 9 conditions: 28 bodies passed, 45
  interfaces, audit closed, every row dispositioned. A row that is NOT
  ADJUDICABLE still has a disposition, so a run can be `complete` at the workflow
  level while the design verdict is "not yet verified". Say both plainly: the
  workflow status and the engineering verdict are different sentences.
