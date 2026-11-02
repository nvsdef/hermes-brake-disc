# The energy audit - what each term is, how to compute it, how to read it

Open this when building the energy samples, computing the audit, or when the
ratio looks wrong.

## Three terms from three independent sources

| Term | Built from | Never built from |
|---|---|---|
| E_applied | the schedule you actually applied: q'''_w, dt_w, d, and the **measured** friction-pair areas | the vehicle energy |
| E_stored | solver readback: rho and cp per material, measured volume per group, volume-average temperature per group | the applied energy |
| E_conv | the h in force, measured group areas, and area-average temperature per convection group, integrated in time | anything on the applied side |

The audit has teeth because the two sides share no inputs. Agreement is two
independent derivations meeting, not a tautology.

## E_applied

```
E_applied = sum over windows w of  q'''_w x dt_w x d x (A_pair1 + A_pair2)
```

- q'''_w and dt_w: the values you set, read back where the readback works.
- d = 0.002 m, read back.
- A_pair: the measured area of the zone carrying the source, from the mesh report
  or a fresh area report in this session.

Then compare with the vehicle energy: `E_applied / 243 055.6 J` must be within
+/-2 % (DV-05). The predecessor measured +0.111 % using meshed contact areas.
PRD section 6 fixes the basis: q''' is scaled with the closed-form A
(5.864306e-3 m^2 each, from case.json) and the applied-energy integral uses the
measured mesh contact areas. Report both areas; `area_basis` records exactly
that split.

**This boundary check is necessary, not sufficient.** It audits what Fluent was
told to inject. It has no view of what happens afterwards. A predecessor run
passed it at +0.102 % while destroying 92 % of the energy through a
non-axisymmetric rotating zone.

## E_stored

```
E_stored(t) = sum over material groups g of rho_g x cp_g x V_g x (Tavg_g(t) - 300 K)
```

- Groups: grey iron (23 zones), pad (2 zones), steel (2 zones).
- rho_g, cp_g: **read back from the solver**, not copied from case.json.
- V_g: measured `volume-sum` of `cell-volume` over the group's zones.
- Tavg_g: `volume-average` of temperature over the group's zones.

Grouping is an identity, not an approximation: inside one material rho and cp
are constant and volume-average is volume-weighted, so the group sum equals the
per-zone sum exactly. Check the group is homogeneous (27 of 27 materials read
back in the setup). Once at the end, compute the per-zone sum as well and compare
at 1e-6 relative; a disagreement means a zone belongs to no group or a group has
mixed properties.

Record the split by group and also by body family (cheeks, vanes, hat, pads,
backing plates). The predecessor found the cheeks held about 90 % of the stored
energy and the hat about 0.3 %. That split is a physics sanity check, not a gate.

## E_conv

```
qconv_g(t) = h_g(t) x A_g x (Taavg_g(t) - 300 K)      exact, since h and T_inf are uniform on a group
E_conv     = integral from 0 to ts of  sum over g of qconv_g(t) dt
```

- h_g(t): the value **in force** during that step (the block value you set), not
  the smooth law.
- A_g: measured summed area of the group.
- Taavg_g: `surface-areaavg` of temperature over the group's walls.

With the three area-average monitors in the per-step report file, integrate per
step (trapezoid) with no round trips. Cross-check once against Fluent's own
heat transfer rate on the convection walls (a flux report of total heat transfer
rate). Mind the sign: Fluent reports heat entering the domain as positive, so
convective loss usually appears negative. E_conv is reported as a positive loss.

If you only have sampled values, integrate them by trapezoid and state the
sample spacing. The predecessor measured that keeping every second sample changed
E_conv by -0.038 % and the ratio by -0.0003 percentage points.

Over one stop, convection removes only about 1 % of the energy (the predecessor
measured 2 214 to 2 714 J). A value near zero means convection landed on
nothing; a value above about 10 % of E means h or an area is wrong.

## The ratio and the residual

```
ratio    = (E_stored + E_conv) / E_applied               band 90 to 110 %
residual = E_applied - E_stored - E_conv                 J and % of E_applied
```

Report **both** loss and excess (DECISIONS item 10). The 90 to 110 % band is a
fault screen, not proof of numerical accuracy, and it does not relax DV-05's
+/-2 % on the applied energy. Report the residual with its sign.

How to read an out-of-band ratio:

| Symptom | Most likely cause | Check |
|---|---|---|
| well below 90 % | something rotating that is not a body of revolution | solid-motion readback; the tangential-velocity integral |
| about 50 % | source on the wrong wall, or half the contact uncoupled | friction-pair readback and areas |
| about 200 % | source on both sides of a coupled pair | which zones carry q''' |
| drifting down over time | a leak that scales with rotation or temperature | per-interval check below |
| above 110 % | stored energy counted twice (overlapping groups) or wrong cp | group membership and material readback |

**Numerics are not the fix for a low ratio.** On the predecessor's merged
rotor, dt / 5 took conservation from 49.5 % to 41.3 % and 30 iterations per step
took it to 26.6 %. Refining helps an under-resolved solution and hurts a
defective operator.

## Early, regular and final samples

The accounting trend is what shows a broken setup within the first second of
simulated time instead of at the end of a 30 minute job. Sample:

- t = 0 (everything zero; T = 300 K everywhere);
- every window up to 0.3 s (early);
- every second window after that (regular);
- the final window, at ts (final; this is the audit's value).

The predecessor's early ratios were 90.4 % at 0.05 s, 96.7 % at 0.15 s, 98.0 %
at 0.25 s and 98.8 % at 0.45 s, rising towards its final 99.9 %. A low first
sample alone is not an abort. A ratio outside 80 to 120 % after 0.2 s, or one
moving away from 100 % over several samples, is.

## The per-interval check

Between consecutive samples a and b:

```
interval_ratio = (dE_stored + dE_conv) / dE_applied
```

It catches a source that stops being re-applied part way through a run whose
whole-run ratio still looks fine. Declare the trim rule **before** looking at the
numbers: exclude the first interval (initialisation transient) and any interval
whose applied power is below 5 % of peak (the denominator vanishes near ts)
from the headline band, but list every interval in `results.json`. The
predecessor's published method gave 0.158 % to 1.469 % absolute error, median
0.274 %, over 17 trimmed intervals of 20; its untrimmed tail interval read
45.8 %. Those are illustrations of the shape, not targets.

This check also stands in for a blind q''' readback on coupled walls: if the
readback cascade cannot see the source, the per-interval ratio shows whether each
window's heat arrived.

## What goes in results.json

`energy_audit`: `E_vehicle_j` (243 055.6), `E_applied_j`,
`E_applied_over_vehicle_pct`, `E_stored_j`, `E_stored_by_group_j`, `E_conv_j`,
`E_conv_by_group_j`, `ratio_pct`, `residual_j`, `residual_pct`,
`band_pct` [90, 110], `pass_ratio`, `pass_applied`, `area_basis`
("measured" or "closed form"), `samples[]`, `per_interval[]`,
`trim_rule`, `grouping_crosscheck_rel`.
