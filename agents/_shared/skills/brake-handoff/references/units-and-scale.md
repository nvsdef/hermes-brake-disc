# Units and scale

| Tool / document | Length unit | Convert |
|---|---|---|
| `specs/PRD.md` | mm (volumes mm^3 and m^3 both given) | - |
| SolidPilot MCP arguments and measurements | **m** (m^3 for volume) | mm / 1000 once, at the tool call |
| STEP file | whatever unit context the exporter wrote (SolidWorks may write an inch context) | none: the importer resolves it |
| SpaceClaim / pyansys-geometry | m | m -> mm x 1000 when comparing with the PRD |
| Fluent | SI (m, m^2, m^3, K, W, J) | report in mm and mm^2 alongside if you compare with PRD section 4 |
| JSON artifacts | whatever unit the key name says | `volume_m3`, `centroid_mm`, `area_mm2` |

## 1. Convert once, at the boundary

Convert at the moment a PRD number becomes a tool argument, and at the moment a
tool measurement becomes a JSON value. Never keep a mixed-unit variable in between.
Write the conversion into the comparison line:
`expected 571 769.86 mm^3 = 5.717699e-4 m^3 / measured 5.717702e-4 m^3 / delta +0.00005 %`.

## 2. Never gate scale on unit text

A predecessor gate grepped the STEP for `SI_UNIT(.METRE.)`. On a real SolidWorks
export the unit context was `CONVERSION_BASED_UNIT('INCH')`, and the `.METRE.`
entities it matched were only the SI base of the 0.0254 conversion factor. **The
grep passed on an inch file**, and the wrong-scale import then made every
geometric query return zero faces three stages later, where it looked like a query
bug.

Prove scale by **measuring three independent dimensional quantities** at import:

| Check | Expected (28 bodies) | Tolerance | What a unit error looks like |
|---|---|---|---|
| total volume | 2 647 566.01 mm^3 = 2.647566e-3 m^3 | 1 % | x 16 387 (inch^3), x 1e9 (mm read as m) |
| rotor volume (23 bodies) | 1 801 776.57 mm^3 | 1 % | same |
| rotor OD | 330 mm (r = 165) | 1 % | 8 382 mm or 0.33 mm |
| z extents | -57 to +57 mm | 1 % | same |

Volume is the sharpest check: it scales with length cubed.

**Do not "fix" a scale by scaling bodies.** If the measurement is off by 25.4 or
1000, stop and report to the lead: either the export or the import option is
wrong, and the owner fixes it at the source.

## 3. Radius sampling trap

When classifying faces by radius in SpaceClaim, sample trimmed **edges**, not
`Face.point(u, v)` on the underlying surface: the predecessor found that face
evaluation used the untrimmed surface and returned a model radius of 0.236 m on a
model that reaches 0.200 m. The 28-body model's largest radius is the calliper
lobe at 200 mm (x up to 200.000 mm on the +X axis); the rotor stops at 165 mm.

## 4. Mixed-unit comparison tools

SolidPilot's `compare_parts` does not normalise between a millimetre document and
a metre document and can return a confident, wrong answer (the predecessor saw a
-100 % volume delta). Compare numbers you converted yourself.

## 5. Temperatures and energy

All temperatures in K (300 K initial and ambient). Energies in J, powers in W,
heat sources in W/m^3, fluxes in W/m^2, h in W/(m^2 K). If a tool reports degC,
convert with + 273.15 and say so in the key name.
