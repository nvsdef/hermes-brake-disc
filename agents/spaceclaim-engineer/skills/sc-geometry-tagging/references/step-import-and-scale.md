# STEP import, the naming chain, and scale by measurement

Open this before step 4 of SKILL.md, when the imported body count is wrong,
when bodies arrive with strange names, or when a scale check fails. The import
is one short step script connected to the running session
(`persistent-session.md`); a wrong count stops the stage before anything else
is spent.

## What survives which hop

```
SolidWorks part name   --STEP-->  PRODUCT name  --SpaceClaim-->  body name (NOT the part name)
SolidWorks face name   --STEP-->  nothing at all
                                   SpaceClaim named selection  --PMDB-->  Fluent zone   OK
```

| Format | Carries named selections |
|---|---|
| PMDB | yes |
| SCDOCX | yes |
| STEP, IGES, Parasolid | **no** |

Measured in the predecessor:

- `disc1.step` contained `PRODUCT ( 'disc1' )`, and the body imported into
  SpaceClaim as `CirPattern1`, the name of the last feature in the SolidWorks
  tree. The PRODUCT name was ignored.
- The 20 vanes shared one PRODUCT and imported as `Cut-Extrude2[1]` to `[20]`.
- The STEP held 236 `ADVANCED_FACE` entities and not one carried a name.

So: imported names and list order are hints at best. Identity comes from
measured geometry (`body-signatures.md`). The SolidWorks side of this project
builds 9 parts, and `vanes` holds 20 solids in one part, so the STEP has **28
`MANIFOLD_SOLID_BREP` under 9 part PRODUCTs plus 1 assembly PRODUCT**.

## Collecting bodies

`design.bodies` returns root-level bodies only. A single-part STEP puts its
solid at the root, which is why a single-disc test once worked and hid the
problem. An assembly STEP nests each solid in a component, and
`design.bodies` came back **empty** on the predecessor's `brake.step`. The
silent failure is expensive: the 60 s boot is spent, nothing is tagged, and a
useless PMDB may be handed on.

Use `design.get_all_bodies()`, which recurses through `design.components`. If
it ever returns fewer than 28, walk `components` yourself as a cross-check
before concluding the STEP is short, and print the component tree
(`design.tree_print()` exists on 0.15.5) into the log.

**Gate:** 28 solids. Also confirm none is a surface body (`body.is_surface`
False, volume > 0).

Run 1 proved this HALT: the first import of `FR330V-20260930-1012` found **23**
solids in the components `vanes` (20), `cheek_in`, `cheek_out` and `hat`; the
pads, backing plates and calliper were missing from the assembly. The script
stopped with `Upstream HALT: expected 28 solids ... got 23` and nothing was
tagged. Report the count and the component list (`comp.name`, `len(comp.bodies)`)
to the lead. Never tag a partial model.

Import call: `design = m.open_file(r"C:\brake-runs\<run-id>\10_cad\brake.step")`.
The default `upload_to_server=True` imported 28 bodies in run 1. `open_file`
closes the design this client has open, so run it only in the import step.

## Sliver and zero-area faces

Count faces with area below 1e-3 mm^2 (1e-9 m^2) over all 28 bodies and record
the smallest face area with its body. Expected: 0 sliver faces.

Why it matters, measured in the predecessor: a flush boolean union left 72
zero-area faces (2 per vane). Every mesh quality gate passed, and 1 to 2 cells
then oscillated between Fluent's 1 K floor and its 5000 K ceiling three stages
later. A body volume check passed at 0.002 % on a part carrying micron slivers.
Volume agreement does not see slivers.

The PRD's calliper windows now use exactly the slot band z = -39 to +38.6 to
remove the sliver faces a mismatched band created. That correction was **not**
demonstrated in the predecessor's evidence (DECISIONS.md item 5), so the
calliper is the most likely place for a sliver. The calliper is deleted before
export, but a sliver on it is still an upstream finding: report it.

A sliver face on any body is an upstream HALT. Do not remove it here.

## Why the STEP header is not a unit check

The old contract said: grep the STEP for `SI_UNIT ( $, .METRE. )`. Measured on
a real SolidWorks export in this chain:

```
GLOBAL_UNIT_ASSIGNED_CONTEXT   10
CONVERSION_BASED_UNIT('INCH')  10     <- the actual length unit context
SI_UNIT entities               30     <- what the grep matches
```

The `.METRE.` entities exist **because** the file is in inches: they are the SI
base of the 0.0254 conversion factor. The grep passes on an inch file. Its
sibling, `grep -c '^#[0-9]*=PRODUCT'`, returns 0 on a real file because SwSTEP
2.0 writes `#123 = PRODUCT ( ... )` with spaces. The working form is
`grep -cE "= ?PRODUCT ?\(" brake.step`, which returns 10 (9 parts plus the
assembly). Both old gates were patterns that could not fail, or could not
match, reported as passes.

Do not "fix" units by scaling anything. The importer resolves the declared
context. The measurement tells you whether it did so the way you assumed. The
predecessor's inch-context file imported at true scale.

## Scale by measurement (step 5)

Three independent quantities, each a function of length. Run them on the 28
imported bodies **before** any identification, using geometry classes only:

| Check | How | Expected | Tolerance |
|---|---|---|---|
| Rotor OD | the two bodies whose bbox is x, y = -165 to +165 (the cheeks): 2 x max radius from trimmed edges of their outer cylinder, or 2 x bbox half-width | 330.0 mm (PKG-01) | 0.05 mm on radius |
| Global z extent | min and max z over all 28 bboxes | -57.000 to +57.000 mm | 0.05 mm each end |
| Total volume | sum of all 28 `body.volume` | 2 647 566.05 mm^3 | 1 % |

The total is the sum of the PRD section 4 rows: 2 x 571 769.86 + 20 x
7 251.63 + 513 204.29 + 2 x 70 371.68 + 2 x 43 982.30 + 617 081.48. After
identification (step 7), also report the rotor sum (cheeks, 20 vanes, hat)
against 1 801 776.57 mm^3.

A wrong scale cannot hide in these. A 25.4x length error is a 16 387x volume
error, and 1000x is 1e9x. A 1 % volume miss is not a unit problem: it is a
body problem, and step 7 will find which body.

## The "polar radius" trap

The predecessor's model reached r = 200 mm (the calliper lobes) while an old
text quoted 215 mm, a -6.98 % "discrepancy" that was a property of the
calliper outline, not of scale. Its first attempt also compared a polar radius
with a bbox half-extent, which produced a fake 7 % scale error. Rules:

- Radius comes from trimmed edge samples or tessellation vertices,
  `sqrt(x^2 + y^2)`. Never from `Face.point(u, v)` (untrimmed, gave 236 mm).
- A bbox half-width is a Cartesian extent. It equals the radius only for a
  full body of revolution such as a cheek.
- In this PRD the calliper bbox is x = 81.245 to 200.000,
  y = -98.418 to 98.418. Its polar maximum is 200 mm at the lobes. None of
  that is the rotor OD. Use the cheeks for OD.

## Record in `tag_report.json`

`import_scale_check` holds, for each of the three checks: `expected`,
`measured`, `delta`, `tolerance`, `method` and `pass`, with units in the key
names (for example `rotor_od_mm`, `z_extent_mm`, `total_volume_mm3`). Also
record `imported_solid_count`, `zero_area_face_count`,
`smallest_face_area_mm2` and the body that owns it.
