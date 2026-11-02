# The friction wall layer and the three convection groups

Open this when setting the friction source or the convection walls, or when a
readback comes back empty.

## The virtual wall layer is an assumption, and you say so

The PRD puts the frictional heat into a virtual wall layer of thickness
d = 0.002 m on each pad/cheek contact. It is a modelling device, not the pad
thickness, not a measured interface and not a physical third body. Fluent treats
a coupled wall with a thickness as a thin conducting layer between the two
adjacent cells, and the heat generation rate you set is a volumetric rate inside
that layer. The heat per unit area it delivers is `q''' x d`.

What you must record in `setup_report.json.wall_layer`:

| Item | Why |
|---|---|
| zone that carries the source, per pair | proves one side only |
| zone that does not, per pair | proves no double deposit |
| thickness readback, m | 0.002 expected |
| layer material name and its k, rho, cp, read back | PRD section 6 specifies grey iron with MAT-01 values (rho 7200, cp 447, k 52); Fluent often defaults a wall to aluminium, which is a FAIL; the layer's k sets how far the wall-layer temperature sits above the solid |
| q''' readback per window, or "blind" plus the readback path tried | proves the schedule took |
| measured contact area per pair, m^2 | used for the applied-energy integral (q''' itself is scaled with the closed-form A = 5.864306e-3 m^2; the integral with measured areas must be within +/-2 % of E, PRD section 6) |

**Do not change the layer material or thickness to move a temperature.** If the
lead wants a sensitivity to d, it must hold the heat per area `q''' x d` (and so
the applied energy) constant, and it is diagnostic only (the layer is a
modelling assumption, PRD section 6).

## One side only

Set the source on **one** zone of each friction pair. The predecessor set it on
the primary of each pair and left the shadow alone, and its energy audit closed
at 100.02 %. If both sides carry the source, the audit reads about 200 %. Read
the other zone back to show it has no source.

API idiom - source and thickness on one wall:
```python
bc = solver.settings.setup.boundary_conditions.wall
bc[w_src] = {"thermal": {"q_dot": {"value": q_w},
                         "wall_thickness": {"value": 0.002}}}
```

## The readback that goes blind

On the predecessor's build, `bc[w].thermal.get_state()` omitted `q_dot` on a
coupled wall, while the solid motion readback on the same windows worked.

**Likely cause, found in the 0.41.0 source (H1.2):** in the v261 settings class
for wall `thermal`, `q_dot` is only an **alias**. The canonical child is
`heat_generation_rate`, and `get_state()` returns canonical keys only
(`Group.to_python_keys` iterates `child_names`). The same holds for
`thermal_bc` -> `thermal_condition`, `h` -> `heat_transfer_coeff`, `tinf` ->
`free_stream_temp`, `d` -> `wall_thickness`. Setting through the alias works;
reading by the alias key finds nothing. Try this cascade and record which path
answered (the first two are UNVERIFIED at runtime):

1. `bc[w].thermal.get_state()["heat_generation_rate"]["value"]`
2. `bc[w].thermal.heat_generation_rate.value()`
3. `bc[w].thermal.q_dot.get_state()` (alias attribute)
4. `bc[w].get_state()["thermal"]["heat_generation_rate"]`

The layer material sits on the same object: `bc[w].thermal.material =
"grey-iron"` (SRC path, UNVERIFIED at runtime); read it back with
`bc[w].thermal.material()`. A material name that is not a defined solid
material is a FAIL; so is `aluminum`.

If none answers, say so **once**, with the wall list, and let the run stand on
two independent pieces of evidence instead: the pre-solve applied-energy integral
(step 9 of the skill) and the per-interval energy check in
`fl-postprocess-energy`. A blind readback is not a passing readback.

Some settings return scalars as `{"option": "value", "value": x}` or as
`[value, unit]`. Unwrap carefully. A readback that returns a dict you did not
parse is not a number.

## Finding the friction pairs

Do not tag them and do not guess them from names. Scan the wall list for pairs
(`X` and `X-shadow`) whose adjacent cells are a pad on one side and a cheek on the
other, both reading `Coupled`. There must be exactly two. Confirm each area
against 5 864.31 mm^2 within 2 % and the location (z = +0.016 m and
z = -0.016 m). If you find 0, 1 or 3, stop: the mesh is not the gated mesh.

Identify which zone of each pair is the pad side by measurement: area-average
`specific-heat-cp` or `thermal-conductivity-lam` on each zone (900 / 1.2 pad,
447 / 52 iron). Density reads 0.0 on a solid with flow off and cannot tell you.

## The three convection groups

| Group | Zones | h_ref, W/(m^2 K) | Area check |
|---|---|---|---|
| vent | every expanded `wall-vent*` zone (about 22) | 130 | 142 865.51 mm^2, and equal to `mesh_report.json` within 0.1 % |
| outer | every expanded `wall-outer*` zone (about 3) | 85 | equal to `mesh_report.json` within 0.1 % |
| pad/backing | every wall that is neither a named-selection zone nor part of a coupled pair | 40 | equal to `mesh_report.json` within 0.1 % |

Build the pad/backing list **by subtraction**: all walls, minus the vent and
outer lists, minus every coupled wall (primary and shadow). Auto-named leftovers
carry the cell-zone name (`geom-1-outerpad:1`), so a glob such as `wall-pad*`
matches nothing.

Then check completeness: every wall is either convective or coupled. A wall in
neither list is adiabatic by default and a silent modelling change.

THM-05 requires the vent cooling to be modelled explicitly. The evidence is the
readback: every vent zone carries the vent h schedule, distinct from outer.

API idiom - all three thermal fields in one call per wall:
```python
bc[w] = {"thermal": {"thermal_bc": "Convection",
                     "heat_transfer_coeff": {"value": h},
                     "free_stream_temp": {"value": 300.0}}}
```
Setting them in one call matters. The predecessor first used a TUI command that
had no free-stream token, then a second call per wall to fix T_inf, which doubled
the round trips. A TUI fallback exists
(`tui.define.boundary_conditions.set.wall(w, "()", "thermal-bc", "yes",
"convection", "convective-heat-transfer-coefficient", "no", h, "q")`); a wall
that takes the fallback still needs its free-stream temperature set and read
back.

Read back `thermal_bc`, `heat_transfer_coeff` and `free_stream_temp` on every
convection wall at the first h block and at one later block. Store per wall in
`setup_report.json.convection`: group, h schedule, T_inf readback, area.

## Why these h values are inputs, not results

There is no air domain. The three h_ref values are prescribed assumptions
(PRD section 6), scaled with speed by an exponent of 0.8. The vent value of 130
presumes vanes that pump air; its basis depends on the rotation sign. Report
them as inputs in `setup_report.json`. They are the largest modelling assumption
in the case, and nobody in this workflow computes them.
