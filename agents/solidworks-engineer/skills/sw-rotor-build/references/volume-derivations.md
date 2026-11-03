# Rotor volumes - closed forms, intermediate checks, symptoms

Verify against arithmetic, not against SolidWorks' own numbers. Build the total
up term by term so a wrong term is identifiable, not just a wrong total. Every
final value here equals PRD section 4; the intermediate values are derived from
PRD section 3 geometry for step-by-step checking.

## 1. Term by term

```
cheek_out  pi (165^2 - 95^2) x 10          = 571 769.86 mm^3 = 5.717699e-4 m^3
cheek_in   same                            = 571 769.86 mm^3 = 5.717699e-4 m^3
vanes      20 x 604.302 mm^2 x 12 mm       = 145 032.55 mm^3 = 1.450325e-4 m^3
hat        2 pi x 1139.0 mm^2 x 72.787 mm  = 520 901.19 mm^3 (before holes)
           less 5 x pi x 7^2 x 10          =  -7 696.90 mm^3
                                           = 513 204.29 mm^3 = 5.132043e-4 m^3
                                             -----------------
rotor total                                  1 801 776.57 mm^3 = 1.801777e-3 m^3
rotor mass at 7200 kg/m^3                    12.973 kg   (MAS-01 limit 13.5 kg)
```

Tolerance is 1 % per body. A larger miss is a build error, not rounding.

Mass is always measured volume x 7200 kg/m^3. `analyze_model` returns no mass,
and a CAD material density is not the PRD density.

The PRD rotor is heavier than a typical production Ø330 vented rotor (9 to
11 kg) because the hat is iron and integral. Say so if asked; it is the PRD
design, not a build error.

## 2. The hat by Pappus

Polygon (z, r) in mm, closed:

```
(43, 35) -> (43, 86) -> (-6, 88) -> (-6, 95) -> (-16, 95) -> (-16, 78) -> (33, 74) -> (33, 35) -> close
```

Reading it: a 10 mm mounting flange at z = +33 to +43 from r = 35 to 86; an
outer wall tapering from r = 86 at z = +43 to r = 88 at z = -6; a web whose
outer face is the r = 95 cylinder from z = -16 to -6; an inner wall from r = 78
at z = -16 to r = 74 at z = +33; a Ø70 bore.

Shoelace on (z, r):

| Quantity | Value |
|---|---|
| area | 1 139.0 mm^2 |
| r centroid | 72.787 mm |
| revolved volume 2 pi A r_bar | 520 901.19 mm^3 = 5.209012e-4 m^3 |
| z centroid of the revolved solid (before holes) | +18.389 mm |
| bolt holes, 5 x pi x 7^2 x 10, centred at z = +38 | 7 696.90 mm^3 |
| z centroid after holes | **+18.095 mm** (PRD section 4) |

The after-holes centroid follows from moments: (520 901.19 x 18.389 -
7 696.90 x 38) / 513 204.29 = 18.095 mm.

Three facts about the profile are load-bearing:

- **r = 95, not 97.** The retired hat reached r = 97 and overlapped `cheek_in`
  by 2 mm radially, putting hat material inside a body that must be a perfect
  body of revolution.
- **z = -6, not -3.** The retired web top at z = -3 was a lip standing 3 mm into
  the vent gap and blocked 25 % of the inlet height. The PRD hat stops at
  z = -6, so the inlet (r = 95, z = -6 to +6) is fully open.
- The hat wall at the calliper end wall height (z = +38.6) is at
  r = 86 + (43 - 38.6) / 49 x 2 = 86.18 mm. The calliper's inner radius there is
  98 mm, so the hat-to-calliper clearance is 11.8 mm (PRD section 4). The old
  "1 mm clearance" belonged to the retired r = 97 hat.

Hat faces you can check directly:

| Face | Expected |
|---|---|
| mounting face z = +43, annulus r = 35 to 86 less 5 holes | 18 617.08 mm^2 |
| ledge z = -6, annulus r = 88 to 95 | 4 024.38 mm^2 |
| contact cylinder r = 95, z = -16 to -6 | 5 969.03 mm^2 (equals the `cheek_in` bore face) |

## 3. Cheeks

Annulus volume `pi (Ro^2 - Ri^2) t` with Ro = 165, Ri = 95, t = 10 mm. Each flat
face is 57 176.99 mm^2. Each bore face is 2 pi x 95 x 10 = 5 969.03 mm^2. Each
outer face is 2 pi x 165 x 10 = 10 367.26 mm^2.

Contacts that come out of this geometry (PRD section 4):

- 40 vane/cheek contacts, 604.30 mm^2 each.
- Cheek inner faces less the 40 contacts: 2 x (57 176.99 - 20 x 604.30) =
  90 181.88 mm^2 of vent-side cheek face.

## 4. Vanes, step by step

| After | Expected total volume |
|---|---|
| boss of 20 extended profiles (r = 80 to 172), 12 mm | 1.901692e-4 m^3 |
| outer trim, card R6a (r > 165) | 1.723384e-4 m^3 |
| inner trim, card R6b (r < 95) | 1.450325e-4 m^3 (7.251627e-6 each) |

Section area and centroid derivation: `vane-geometry.md`. Paste-ready cards: `sketch-data.md`.

## 5. Symptom table

| Symptom | Cause |
|---|---|
| The rotor is one body | Two or more rotor parts built in one file, or a pattern fused the vanes |
| About 2.4e-3 m^3 for "the rotor" | A solid ring: no vent gap and no vanes. This is the H1 failure (a solid disc with axial holes) |
| A cheek volume about 5.72e-4 minus a few percent | Holes were cut in it. Cheeks carry no holes |
| `vanes` total about 1.93e-4 m^3 | Vane extrude 16 mm instead of 12 (2 mm into each cheek) |
| `vanes` total about 1.90e-4 m^3 | The trim cuts did not happen |
| `vanes` total about 1.72e-4 m^3 | Only the outer trim happened |
| A vane's z span is not exactly -6 to +6 | Wrong depth, or not mid-plane |
| Vane volume above 7.33e-6 m^3 each (more than 1 % high) | Profile left the flank band (chords instead of arcs) or the wrong branch |
| Vane centroids near angle 155 deg + (k - 1) x 18 | The wrong branch (`phi_C + a`) |
| Hat volume near 0 | Profile not closed, or the axis not selected |
| Hat centroid z = -18.4 mm, z span -43 to +16 | Right Plane mapping inverted (sketch x = +z) |
| Hat volume about 5.43e-4 m^3 | The retired hat (r = 97, web top at z = -3) |
| Hat volume 5.209e-4 after the hole step | The bolt-hole cut did nothing (wrong plane or depth) |
| Hat volume below 5.13e-4 by a multiple of 1.54e-6 | Extra holes (one Ø14 x 10 mm hole is 1.539e-6 m^3) |
