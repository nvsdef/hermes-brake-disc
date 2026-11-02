# Recommendation levers - what you would change first, with numbers

Every recommendation names the **parameter, the direction, the expected magnitude
with a unit, the arithmetic, the cost, and the PRD requirement it touches**. "Improve
cooling" is not a recommendation. Most design levers change a PRD requirement
(PAD-01 fixes the pad at 60 deg, PKG-01 fixes the OD), so say which one, and say
that the change needs the PRD owner's agreement.

Scaling used below (single stop, semi-infinite skin): the surface rise follows
dT ~ q'' x sqrt(t) / e, with e = sqrt(k rho cp). At fixed heat partition, the
pad peak rise is linear in the pad face flux q''.

## 0. Choosing the first change

| Situation after the review | First change |
|---|---|
| THM-02 (or any thermal M row) is NOT ADJUDICABLE for resolution or straddle | **Lever A: resolve the pad friction face.** Nothing else can be ranked honestly against a number that is not yet a measurement |
| energy audit did not close | fix the solve (owner fluent-engineer); no design lever applies |
| THM-02 is FAIL on a resolved face | **Lever C: more pad area**, sized from the required reduction |
| all thermal rows PASS | **Lever H: record the rotor hand in the report (and on any future drawing) and run DV-10**; the single-stop case has margin, and the next risk is the repeated-stop case |

Quantify the first change from **this run's** numbers. Required reduction for a
failing pad, with p = pad peak (upper end, K):

```
required fractional cut in pad rise = (p - 623) / (p - 300)
e.g. p = 660 K -> (660 - 623) / (660 - 300) = 10.3 % less pad flux
```

## 1. The levers

| # | Lever | Parameter change | Expected effect (arithmetic) | Cost / side effects | Touches |
|---|---|---|---|---|---|
| A | **Resolve the pad face** (verification, not design) | pad-side wall-normal cell from this run's value to <= 1.374 mm (PRD minimum, 1 cell) and preferably <= 0.275 mm (1.374 / 5, 5 cells) on the two pad contact faces only | converts THM-02 from NOT ADJUDICABLE to PASS or FAIL; the range [cell max, layer max] narrows as the near-surface cell approaches the surface value | one mesh plus one solve; a full-rotor mesh at 0.275 mm will not fit the Ansys Student cap of 512 000 cells + nodes (the predecessor's mesh sat at 93 % of the cap with a 1.9 mm pad cell), so use local refinement on the pad faces or a 60 deg pad-and-cheek sector submodel | THM-02, THM-01, THM-04 credibility |
| B | **Layer-thickness sweep** (verification) | d = 0.002 -> 0.001 -> 0.0005 m, holding applied energy (q''' scales as 1/d) | if the upper end falls roughly in proportion to d, the gap between the two ends is the layer's own resistance (flux x d / k), not a material temperature; the predecessor found the gap tracked flux, not iteration count | three short solves (or three windows of the early stop, where the flux is highest); more iterations per step do **not** move a flux-proportional offset | THM-01, 02, 04 |
| C | **More pad area** | pad sector 60 -> 75 deg (A 5.864306e-3 -> 7.330383e-3 m^2) | face flux -20 % (1.1706e7 -> 9.3647e6 W/m^2 at t = 0); pad peak rise -20 % at fixed partition, e.g. 330 K rise -> 264 K | calliper slot is +/- 42 deg: a +/- 37.5 deg pad plus backing still fits but window clearances must be rechecked; more sliding mass; new calliper | **PAD-01 (60 deg, M)**, PAD-05 |
| D | **Wider pad radially** | r = 120 to 160 -> 115 to 162 mm | A +16.2 % ((162^2 - 115^2) / (160^2 - 120^2) = 13 019 / 11 200 = 1.162), flux -14.0 %, pad peak rise -14 % at fixed partition; stays inside the cheek r = 95 to 165 | backing plate and calliper must grow; rotor swept band changes | **PAD-02 (M)**, PAD-04 |
| E | **Higher-conductivity pad** | k_pad 1.2 -> 2.0 W/(m K) | pad effusivity 1 643 -> 2 121; the zero-resistance contact estimate falls by (12 937 + 1 643) / (12 937 + 2 121) = 0.968, i.e. about -3 % of the rise; more heat goes into the pad and backing | more heat towards the calliper and fluid (THM-06, deferred); friction and wear behaviour change | **MAT-02** |
| F | **Thicker cheeks** | 10 -> 12 mm each | rotor mass +1.647 kg (2 x 0.2 x 571 769.86 mm^3 x 7200) -> 14.62 kg; bulk rise upper estimate 41.9 -> 37.2 K; surface peak barely moves (the iron penetration depth over the stop is 7.6 mm, less than the cheek) | **violates MAS-01 (13.5 kg)**; not recommended | MAS-01, GEO-02, PKG-02 |
| G | **More vanes, ducted air, higher vent h, cross-drilling** | e.g. vent h 130 -> 250, 20 -> 30 vanes, GEO-05 holes | negligible over one stop: convection is about 1 % of E (quote this run's fraction); even doubling every h moves the peak by well under 1 % | casting complexity, packaging; cross-drilling breaks the solid-motion model | THM-05, GEO-04, GEO-05; belongs to DV-10 |
| H | **Record the rotor hand** (report now; drawing when drawings return to scope) | note "rotates clockwise viewed from +Z (outboard); omega0 = -84.1751 rad/s" | no temperature change; prevents a mirror-image casting, which would invalidate the vent coefficient's basis | a note | THM-05 premise |
| I | **Larger rotor OD** | 330 -> 360 mm | more swept area and a longer torque arm | **violates PKG-01 (<= 330, M)**; not available | PKG-01 |

Lever C and D percentages are for the example changes shown. For any other
proposal compute the area yourself, for example (pi/6)(0.162^2 - 0.115^2) =
6.817e-3 m^2 for lever D, and quote the flux change as A_old / A_new - 1.

## 2. Single stop versus repeated stops

Levers C, D and E act on the single-stop peak because the single stop is a
thermal-mass problem: the energy goes into the first millimetres of the pad and
cheek faster than any air can remove it. Levers G act on the repeated-stop and
long-descent cases, where the rotor approaches a steady state and only h x A x dT
matters. If the user asks about fade resistance or mountain descents, the honest
answer is "this case cannot tell you; DV-10 (repeated stops) and DV-07 (fade) are
deferred to Phase 3", and then offer to define that case.

## 3. Writing the first change into review.json

```json
"first_change": {
  "lever": "A",
  "text": "Refine the pad-side wall-normal cell at both pad/cheek contacts from 1.90 mm to <= 0.275 mm using a local size on the pad faces, then re-solve",
  "parameter": "mesh.friction_face.pad_wall_normal_mm",
  "from": 1.90,
  "to": 0.275,
  "expected_effect": "THM-02 becomes adjudicable (cells across 1.374 mm penetration depth: 0.72 -> 5.0)",
  "quantified": {"cells_across_from": 0.72, "cells_across_to": 5.0},
  "arithmetic": "1.374 mm / 1.90 mm = 0.72; 1.374 / 0.275 = 5.0",
  "cost": "one mesh + one solve; check the Student cap",
  "touches": ["THM-02", "THM-01", "THM-04"],
  "needs_prd_change": false
}
```

The numbers in that example are illustrative; yours come from `mesh_report.json`.
