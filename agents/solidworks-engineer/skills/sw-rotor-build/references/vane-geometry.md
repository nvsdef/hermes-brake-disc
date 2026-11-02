# Vane geometry - derivation, profiles and check tables

PRD 3.2 defines each vane as the region between two concentric circles of radius
117 and 123 mm centred at C = (20.722, 94.249) mm, trimmed to r = 95 to 165 mm,
12 mm thick about z = 0, and repeated at 18 deg pitch by rotating coordinates.
This sheet derives the numbers behind the data cards. **During a build, do not
recompute anything: paste cards R2 to R6 from `sketch-data.md`.** Run 1
rotated the coordinates by hand in the loop, got crossed and mis-paired arcs on
vanes 17 to 20, then wrote a helper script and hit the Windows Store `python`
stub: about 15 minutes lost. This sheet is for auditing a card or diagnosing a
miss.

## 1. Where a flank circle crosses a rotor radius

Let d = |C| and phi_C = atan2(Cy, Cx):

```
d     = sqrt(20.722^2 + 94.249^2) = 96.500 mm
phi_C = atan2(94.249, 20.722)     = 77.600 deg
```

A point at polar radius r on the circle of radius R about C sits at polar angle
theta with

```
cos(a) = (r^2 + d^2 - R^2) / (2 r d)
theta  = phi_C - a      (the branch we keep)
theta  = phi_C + a      (the other branch - wrong)
```

This is the law of cosines in the triangle origin - C - point. Each circle meets
each rotor radius twice. The branch `phi_C - a` is the one whose polar angle
**increases** with r. It is the branch PRD 3.2 keeps.

Worked values (degrees):

| R (mm) | r = 80 | r = 95 | r = 165 | r = 172 |
|---|---|---|---|---|
| 123, kept branch | -10.2350 | **-2.3225** | **+29.8420** | +33.3225 |
| 117, kept branch | -4.8703 | **+2.2858** | **+33.4470** | +37.0065 |
| 123, wrong branch | 165.4350 | 157.5225 | 125.3580 | 121.8775 |
| 117, wrong branch | 160.0702 | 152.9142 | 121.7529 | 118.1934 |

At r = 95 the vane spans -2.3225 to +2.2858 deg; at r = 165 it spans +29.8420
to +33.4470 deg. PRD 3.2 quotes "about -2.3 to +2.3 deg at r = 95, +29.8 to
+33.4 deg at r = 165". They agree.

The mean line (R = 120) runs from +0.0003 deg at r = 95 to +31.640 deg at
r = 165: a sweep of about +31.6 deg towards +theta.

## 2. Vane 1 corners and the PRD bbox

Cartesian corners at the trim radii, mm:

| Corner | x | y |
|---|---|---|
| R123 at r = 95 | 94.922 | -3.850 |
| R117 at r = 95 | 94.924 | 3.789 |
| R123 at r = 165 | 143.121 | 82.106 |
| R117 at r = 165 | 137.675 | 90.942 |

The vane_01 bbox is set by these corners: x min 94.922 (R123 at r = 95), x max
143.121 (R123 at r = 165), y min -3.850, y max 90.942. The r = 95 end arc passes
through theta = 0 at x = 95.000, which is inside the corner x min, so the corners
really are the extremes. PRD section 4: x = 94.922 to 143.121, y = -3.850 to
90.942. They agree.

## 3. Section area and centroid, by polar integration

The vane section at radius r is the arc from theta_123(r) to theta_117(r), so

```
A    = integral from 95 to 165 of r * (theta_117 - theta_123) dr
A*x  = integral of r^2 * (sin theta_117 - sin theta_123) dr
A*y  = integral of r^2 * (cos theta_123 - cos theta_117) dr
```

Simpson's rule with 20 000 intervals gives:

| Quantity | Value | PRD section 4 |
|---|---|---|
| section area | 604.302 mm^2 | 604.302 |
| vane volume (x 12 mm) | 7 251.63 mm^3 = 7.251627e-6 m^3 | same |
| 20 vanes | 145 032.55 mm^3 = 1.450325e-4 m^3 | same |
| vane_01 centroid | (123.842, 40.040) mm | same |
| centroid radius, angle | 130.154 mm at 17.917 deg | same |

The older value 604.2333 mm^2 (and 7.25080e-6 m^3 per vane) came from a
polygonal approximation of the arcs. Both are inside the 1 % tolerance. The
PRD value is the one to print as expected.

Flank arc lengths between the trim radii: R117 about 100.10 mm (49.02 deg about
C), R123 about 101.39 mm (47.23 deg about C).

## 4. The extended profile you actually sketch

The flanks are drawn past both trim radii, to r = 80 and r = 172 mm, and closed
with straight lines there. The trim cuts then remove everything below r = 95 and
above r = 165, so the lines and the extra arc never reach the finished body.

Checks on the extended profile:

- The chord at r = 172 has its midpoint at r = 171.9 mm, well outside 165. The
  chord at r = 80 is entirely inside r = 95. Neither survives the trims.
- The vane is at most 5.4 deg wide (at r = 80) and 3.7 deg wide at r = 172. The
  pitch is 18 deg. So the 20 extended profiles are disjoint and can share one
  sketch.
- About C, the extended R123 flank sweeps 61.97 deg and the R117 flank
  64.27 deg. Both are minor arcs, so `arc_center` without `direction` draws the
  right one.
- Extended area per vane: 792.372 mm^2. After the boss (12 mm, 20 vanes):
  1.901692e-4 m^3. After the single trim cut of card R6 (both ends at once):
  1.450325e-4 m^3. If only the outer ring is cut: 1.723384e-4 m^3.
- Smallest gap between neighbouring extended profiles: 15.07 mm.

## 5. All 20 extended profiles (metres, 9 decimals)

The same numbers, already written as `add_sketch_entities` records in batches
of five, are cards R2 to R5 in `sketch-data.md`. The table below is for
auditing only.

Vane k = vane 1 rotated by phi = (k - 1) x 18 deg:
`x' = x cos(phi) - y sin(phi)`, `y' = x sin(phi) + y cos(phi)`. Rotate C too.

Contour order per vane: arc about C_k from A to B; line B to Cp; arc about C_k
from Cp to D; line D to A. A and B are on the R123 flank (r = 80, r = 172); Cp
and D are on the R117 flank (r = 172, r = 80).

| k | centre C_k | A: R123, r 80 | B: R123, r 172 | Cp: R117, r 172 | D: R117, r 80 |
|---|---|---|---|---|---|
| 01 | 0.020722000, 0.094249000 | 0.078726970, -0.014214927 | 0.143721767, 0.094488379 | 0.137353481, 0.103527876 | 0.079711160, -0.006791977 |
| 02 | -0.009416750, 0.096039576 | 0.079266452, 0.010808773 | 0.107489008, 0.134276257 | 0.098639050, 0.140905421 | 0.077908655, 0.018172549 |
| 03 | -0.038633722, 0.088429129 | 0.072046781, 0.034774435 | 0.060734477, 0.160920239 | 0.050269142, 0.164490162 | 0.068479907, 0.041358220 |
| 04 | -0.064068957, 0.072162622 | 0.057774669, 0.055336133 | 0.008034831, 0.171812227 | -0.003021460, 0.171973460 | 0.052347869, 0.060495459 |
| 05 | -0.083232675, 0.048832336 | 0.037847171, 0.070481144 | -0.045451320, 0.165886038 | -0.056016301, 0.162622797 | 0.031091657, 0.073710982 |
| 06 | -0.094249000, 0.020722000 | 0.014214927, 0.078726970 | -0.094488379, 0.143721767 | -0.103527876, 0.137353481 | 0.006791977, 0.079711160 |
| 07 | -0.096039576, -0.009416750 | -0.010808773, 0.079266452 | -0.134276257, 0.107489008 | -0.140905421, 0.098639050 | -0.018172549, 0.077908655 |
| 08 | -0.088429129, -0.038633722 | -0.034774435, 0.072046781 | -0.160920239, 0.060734477 | -0.164490162, 0.050269142 | -0.041358220, 0.068479907 |
| 09 | -0.072162622, -0.064068957 | -0.055336133, 0.057774669 | -0.171812227, 0.008034831 | -0.171973460, -0.003021460 | -0.060495459, 0.052347869 |
| 10 | -0.048832336, -0.083232675 | -0.070481144, 0.037847171 | -0.165886038, -0.045451320 | -0.162622797, -0.056016301 | -0.073710982, 0.031091657 |
| 11 | -0.020722000, -0.094249000 | -0.078726970, 0.014214927 | -0.143721767, -0.094488379 | -0.137353481, -0.103527876 | -0.079711160, 0.006791977 |
| 12 | 0.009416750, -0.096039576 | -0.079266452, -0.010808773 | -0.107489008, -0.134276257 | -0.098639050, -0.140905421 | -0.077908655, -0.018172549 |
| 13 | 0.038633722, -0.088429129 | -0.072046781, -0.034774435 | -0.060734477, -0.160920239 | -0.050269142, -0.164490162 | -0.068479907, -0.041358220 |
| 14 | 0.064068957, -0.072162622 | -0.057774669, -0.055336133 | -0.008034831, -0.171812227 | 0.003021460, -0.171973460 | -0.052347869, -0.060495459 |
| 15 | 0.083232675, -0.048832336 | -0.037847171, -0.070481144 | 0.045451320, -0.165886038 | 0.056016301, -0.162622797 | -0.031091657, -0.073710982 |
| 16 | 0.094249000, -0.020722000 | -0.014214927, -0.078726970 | 0.094488379, -0.143721767 | 0.103527876, -0.137353481 | -0.006791977, -0.079711160 |
| 17 | 0.096039576, 0.009416750 | 0.010808773, -0.079266452 | 0.134276257, -0.107489008 | 0.140905421, -0.098639050 | 0.018172549, -0.077908655 |
| 18 | 0.088429129, 0.038633722 | 0.034774435, -0.072046781 | 0.160920239, -0.060734477 | 0.164490162, -0.050269142 | 0.041358220, -0.068479907 |
| 19 | 0.072162622, 0.064068957 | 0.055336133, -0.057774669 | 0.171812227, -0.008034831 | 0.171973460, 0.003021460 | 0.060495459, -0.052347869 |
| 20 | 0.048832336, 0.083232675 | 0.070481144, -0.037847171 | 0.165886038, 0.045451320 | 0.162622797, 0.056016301 | 0.073710982, -0.031091657 |

Self-checks while you generate these: |C_k| = 0.096500131 for every k; |A| and
|D| = 0.080000000; |B| and |Cp| = 0.172000000; |A - C_k| = |B - C_k| =
0.123000000; |Cp - C_k| = |D - C_k| = 0.117000000. A row that fails any of these
has a rotation error.

## 6. Per-vane centroid table (mm) - the naming key

After the build, `analyze_model('bodies')` returns 20 bodies in SolidWorks'
order. Assign names by centroid angle:

| Name | Centroid angle (deg) | Centroid (x, y, z) mm |
|---|---|---|
| vane_01 | 17.917 | (123.842, 40.040, 0) |
| vane_02 | 35.917 | (105.407, 76.350, 0) |
| vane_03 | 53.917 | (76.655, 105.186, 0) |
| vane_04 | 71.917 | (40.399, 123.725, 0) |
| vane_05 | 89.917 | (0.189, 130.154, 0) |
| vane_06 | 107.917 | (-40.040, 123.842, 0) |
| vane_07 | 125.917 | (-76.350, 105.407, 0) |
| vane_08 | 143.917 | (-105.186, 76.655, 0) |
| vane_09 | 161.917 | (-123.725, 40.399, 0) |
| vane_10 | 179.917 | (-130.154, 0.189, 0) |
| vane_11 | 197.917 | (-123.842, -40.040, 0) |
| vane_12 | 215.917 | (-105.407, -76.350, 0) |
| vane_13 | 233.917 | (-76.655, -105.186, 0) |
| vane_14 | 251.917 | (-40.399, -123.725, 0) |
| vane_15 | 269.917 | (-0.189, -130.154, 0) |
| vane_16 | 287.917 | (40.040, -123.842, 0) |
| vane_17 | 305.917 | (76.350, -105.407, 0) |
| vane_18 | 323.917 | (105.186, -76.655, 0) |
| vane_19 | 341.917 | (123.725, -40.399, 0) |
| vane_20 | 359.917 | (130.154, -0.189, 0) |

Tolerance 0.1 mm on each coordinate. A vane whose centroid radius is right but
whose angle is off by a multiple of 18 deg is a naming slip; a vane whose
radius is off is a geometry defect.

## 7. Where a radial section cuts a vane (background for the Gate 2 screenshot)

A radial plane at angle 0 deg passes through vane_01 from r = 95.00 to 99.75 mm
(the vane root sits across theta = 0), and through vane_20 from r = 131.06 to
139.39 mm. On the opposite ray (180 deg) it passes through vane_11 at r = 95.00
to 99.75 and vane_10 at 131.06 to 139.39. So a 0 deg section shows the vent inlet
**blocked** at r = 95 on both sides.

A plane at 9 deg (and 189 deg) passes mid-passage at r = 95 on both sides, and
crosses vane_01 and vane_11 at r = 110.16 to 119.21 mm and vane_20 and vane_10 at
r = 151.41 to 159.07 mm. That is the section that shows GEO-06 (inlet open).
SpaceClaim takes that section screenshot at Gate 2 (`cad_section_9deg.png`);
there are no SolidWorks drawings in H1.2.

## 8. Handedness

theta increases with r on the kept branch (d theta / d r > 0). The rotor runs
clockwise viewed from +Z (PRD 3.2 and section 5, omega0 = -84.1751 rad/s). The
CTS intent "pumps under +theta" is reported as unmet (PRD section 10). Put the
measured flank angles in `cad_report.json` beside the hand so the lead can check
the derivation.
