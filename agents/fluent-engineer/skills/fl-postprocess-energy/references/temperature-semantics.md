# Which temperature is which, and when it can be judged

Open this when deciding what a temperature number means, when comparing
resolution with penetration depth, or when a result looks wrong before you call
it a bug.

## Four different numbers people call "the surface temperature"

| Name in results.json | What it is | What it is not |
|---|---|---|
| cell max (`kind: "cell max"`) | the hottest cell temperature in the zones next to the friction face (volume-max over the cheeks, or over the pads) | the surface temperature, when the cell is thicker than the penetration depth |
| wall-layer max (`kind: "wall-layer max"`) | the hottest facet temperature Fluent reports on the friction wall zone, which carries the virtual 2 mm heat-generating layer | a resolved physical contact temperature |
| surface area-average | the mean over a wall | a maximum |
| end-of-stop value | the value at t = ts | a peak |

Report cell max and wall-layer max as a **range**, each with its peak time. PRD
section 7 requires both. DECISIONS item 11 says neither end of that range is a
certified bound on the true interface temperature.

Why the two differ: the heat is generated **inside** the layer, so the layer's
face sits above the adjacent solid by an offset that scales with the applied
flux and the layer's own resistance (thickness divided by the layer material's
k). The predecessor fitted that offset on its own run as `gap(t) =
9.149e-9 x q'''(t) + 0.54 K` with R^2 = 0.9992: it tracked the flux, peaked at
t = 0 and fell to under 1 K at the end. So the wall-layer maximum depends on the
declared thickness and layer material as well as on the brake. Record both in
`results.json.wall_layer`.

Why the cell max can under-read: a finite-volume cell reports its average. If the
steep near-surface gradient lies inside one cell, the cell average is below the
face temperature.

## Which zones each requirement looks at

| Requirement | Limit | Cell max from | Wall-layer max from |
|---|---|---|---|
| THM-01 rotor friction-surface peak | 923 K | volume-max over `cheek_out`, `cheek_in` | facet-max over the rotor-side zones of the 2 friction pairs |
| THM-02 pad friction-surface peak | 623 K | volume-max over the 2 pad zones | facet-max over the pad-side zones of the 2 friction pairs |
| THM-04 no rotor surface above | 1143 K | volume-max over all 23 rotor zones | facet-max over every rotor wall (vent, outer, rotor-side friction and interface walls) |
| THM-03 rotor bulk rise | 60 K | volume-weighted average over 23 rotor zones minus 300 K | not applicable |

For THM-04 the only virtual layer is at the friction faces; on other rotor walls
the "wall-layer" column is the ordinary wall facet temperature. Say so in the
row.

Which zone of a friction pair is the pad side is measured, by area-average
`specific-heat-cp` or `thermal-conductivity-lam` (900 / 1.2 pad, 447 / 52 iron).
The predecessor's naming convention inverted between builds, and a name-based
rule swapped the rotor and pad headline numbers.

## Resolution against penetration depth

```
alpha = k / (rho x cp)         delta(t) = sqrt(alpha x t)
```

| Material | alpha, m^2/s | delta at 0.1 s | delta at 1.77 s | delta at ts = 3.54 s |
|---|---|---|---|---|
| grey iron | 1.6157e-5 | 1.27 mm | 5.35 mm | 7.56 mm |
| pad compound | 5.3333e-7 | 0.23 mm | 0.97 mm | 1.37 mm |

Evaluate delta at the **peak time of that monitor**, and also at ts. Take the
wall-normal and in-plane cell sizes for that side from this run's
`mesh_report.json.friction_face_resolution`. Never use a literal from a previous
run: the predecessor quoted "a 3.788 mm friction-face cell" for three runs, and it
was another case's in-plane edge compared with a wall-normal depth.

Write, per friction side: `wall_normal_cell_mm`, `in_plane_edge_mm`,
`penetration_mm_at_peak`, `penetration_mm_at_ts`, `cells_across_at_peak`,
`cells_across_at_ts`. If the wall-normal cell is larger than delta at the peak
time, set `resolution_coarser_than_penetration: true`.

## The NOT ADJUDICABLE rule (PRD section 7)

For each of THM-01, THM-02 and THM-04, set `adjudicable: false` when any of these
holds, and state which:

1. The limit lies inside the [cell max, wall-layer max] range.
2. The friction-face wall-normal cell is coarser than the penetration depth at
   the peak time.
3. Either end of the range, or the resolution, is `null`.

Also set `cell_max_exceeds_limit: true` when the cell maximum alone is above the
limit: PRD section 7 makes that a **FAIL**, because the lower bound is already
over the limit. Always publish `cells_across_at_peak`; fewer than 5 cells across
the penetration depth is a **finding** the lead records. The absence of a
mesh-sensitivity study alone is also a finding, not a reason for NOT
ADJUDICABLE.

You publish the flags and the numbers. The lead writes NOT ADJUDICABLE, PASS or
FAIL. A lower bound cannot show a limit is met, and a declared layer cannot
show it is exceeded.

Predecessor illustration only: its pad ranges were [470.7, 630.7] K and
[471.7, 642.3] K against the 623 K limit, with a pad wall-normal cell of 1.90 mm
against a 1.37 mm penetration. Both conditions held. Expect the pad to be the
governing and least resolved requirement (PRD section 7 says THM-02 is expected
to govern).

## Sensitivity runs are diagnostic

If the lead asks for a layer-thickness sensitivity, it must hold the heat per
area q''' x d constant (so q''' scales by d_primary / d_leg) and therefore the
applied energy constant. Halving d at constant heat per area should roughly halve
the offset if it is a layer resistance. That tells you about the constant, not
about the brake: a range narrowed by declaring a thinner layer does not make a
requirement adjudicable (PRD section 7 judges adjudicability on the wall-normal
cell size against the penetration depth). The resolution route the predecessor
identified is a 60 deg pad-and-cheek submodel, which the lead would commission
separately.

## Results that look wrong and are right

- **Pad hotter than rotor.** Expected. Pad compound conducts 43 times worse
  than iron, so heat piles up at its face.
- **Pad peaks earlier than rotor.** Expected, same reason.
- **Wall-layer maxima peak in the first 0.1 to 0.2 s.** Expected; the applied
  flux is largest at t = 0.
- **Rotor circumferentially smeared.** That is the solid motion working. Check
  it: on rings through the swept band the predecessor measured coldest-facet rise
  / hottest-facet rise of 0.369 at r = 128 mm, 0.486 at 140 mm and 0.635 at
  155 mm. A stationary hot spot gives a ratio near zero.
- **Hat near 300 K.** Correct. Heat needs tens of seconds to reach the hat
  junction; the stop lasts 3.54 s.

## Results that look plausible and are wrong

| Symptom | Cause |
|---|---|
| Everything at 300 K | source on a wall that touches nothing; or a STEP was meshed |
| Friction peak at exactly ts | source not ramped |
| Temperatures rising without bound on outer or vent faces | convection landed on 1 of 22 zones |
| Energy ratio far below 90 % | non-axisymmetric zone rotating |
| Pad and rotor numbers swapped | side taken from a zone name; or monitor columns mapped by position |
| Any value exactly at the clip limit | clipping; the run's temperatures are junk |
| A "peak" equal to the end-of-stop value to every digit | the peak was read from the final snapshot |
