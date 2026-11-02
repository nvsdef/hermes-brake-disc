# Traps and priors - numbers that look right and are not

Open this when a number appears that you did not compute, when someone argues a
constant source is "close enough", or before a heat-partition figure or a
closed-form pad temperature is used as evidence.

## 1. The published PyFluent brake example

The upstream example that most brake tutorials start from carries a different
vehicle **and** a units bug. Nothing from it enters this run.

| In the example | What it really is |
|---|---|
| `solid_omega = -15.79` with the comment "15.79 rps corresponds to 100 km/h with 0.28 m axis height" | 100 km/h / 0.28 m = 99.21 rad/s = 15.79 **rev/s**. The argument takes **rad/s**, so the example spins 2 pi too slow, equivalent to 15.9 km/h. It turns 5 revolutions in its 2 s where a real stop from 100 km/h turns about 24 (this geometry, 3.54 s) |
| `q''' = 2.0e9 W/m^3` over 2.0 s | applied for 2.0 s in this pad area and layer it deposits about 93.8 kJ per rotor, well under the 243 055.6 J this vehicle needs: it is a different (lighter) car, not this one |
| one h = 100 W/(m^2 K) on everything | erases the vent/outer/pad distinction; `wall-vent` is the only place the vanes do anything thermal (THM-05) |
| all zones aluminium | pads and backing plates are not aluminium; the heat partition is then wrong |
| volume monitors | THM-01, 02 and 04 are surface requirements; volume maxima read about 100 K low |
| 2.0 s of a 3.54 s stop | truncates the event |
| rotation axis `[0, 1, 0]` at `[-0.035, -0.821, 0.045]` | a property of the Ansys-shipped mesh; on this geometry it rotates about a line outside the part, converges, and gives a wrong answer with no error |

What the example does get right: it rotates only two plain annular discs and keeps
its vanes as separate non-rotating zones. That is exactly why this PRD splits the
rotor into cheeks, vanes and hat.

## 2. Constant source versus the ramp

Semi-infinite solid, same energy, pad side (effusivity 1 643), measured on the
predecessor's geometry:

| Source | Pad surface peak rise | When |
|---|---|---|
| constant q''' | about 378 K | at the end of the stop |
| linear ramp (this PRD) | about 357 K | at about half the stop (t = ts/2 = 1.77 s) |

A constant source is about 5.7 % low on the peak and, worse, has the wrong shape:
it rises monotonically and peaks at t = ts. A real brake peaks near mid-stop and is
already cooling when the car halts, because the input falls faster than conduction
carries heat away. **A reported peak at t = ts is the tell that the ramp did not
take.**

For a ramp q''(t) = q0 (1 - t/ts) on a semi-infinite solid of effusivity e, the
surface rise is:

```
dT(t) = (2 q0 / (e sqrt(pi))) x sqrt(t) x (1 - (2/3) t/ts)
peak at t = ts/2:  dT_peak = (4/3) x q0 x sqrt(ts/2) / (e sqrt(pi))
```

## 3. The disc/pad split is a prior, not evidence

The heat divides between disc and pad roughly by effusivity. Static split from
the PRD materials:

```
e_iron = sqrt(52 x 7200 x 447)   = 12 937
e_pad  = sqrt(1.2 x 2500 x 900)  =  1 643
pad share (static) = 1 643 / (12 937 + 1 643) = 11.3 %
```

Rotation moves the split towards the disc, but by how much is not derivable
without the solve. The closed-form pad peak is governed entirely by that one
coefficient (ramp formula above, ts = 3.540681 s, P(0) = 137 293.1 W over two
faces of 5.864306e-3 m^2):

| Assumed pad share | Pad face flux at t = 0 W/m^2 | Closed-form pad peak rise | Absolute | vs THM-02 623 K |
|---|---|---|---|---|
| 11.3 % (static effusivity) | 1.32e6 | 806 K | 1 106 K | fails by 483 K |
| 5.0 % (an often-quoted "rotation-corrected" value) | 5.85e5 | 357 K | 657 K | fails by 34 K |
| 2.6 % (the predecessor's measured partition) | 3.04e5 | 185 K | 485 K | passes by 138 K |

One undocumented coefficient moves the answer across 600 K and across the limit.
**It cannot pass or fail THM-02.** A predecessor review used the 5 % figure as
"independent evidence" that THM-02 failed, and had to withdraw the claim. If you
need the partition, measure it from the solve: the sum of rho cp V (T_avg - 300)
over the pad zones against the same sum over all zones.

The disc side is much less sensitive (the rotor peak rise from the same formula,
smeared over both swept faces of 0.07037 m^2, moves only from 134 K to 147 K
across the same range), which is why the rotor number is the trustworthy
closed-form check and the pad number is not.

## 4. The rotation sign has been flipped before

The predecessor ran with -56.12, then "corrected" it to +56.117 on the belief that
the vanes pump under +theta, and that correction went the wrong way. Derive the
sign from the vane hand every run (SKILL.md section 3). Thermally it changes no
temperature; it changes the casting-hand note in the report and the vent coefficient's
justification.

## 5. g = 9.81

With g = 9.81, ts = 3.5395 s, the mean power becomes 68 670 W, and the
predecessor's "354 steps" looks like a full stop. H1.2 uses g = 9.80665
everywhere (PRD section 10). If you see 3.5395, 68 670 or 49.16 m in any artifact,
the wrong g was used.

## 6. Convection is about 1 % of a single stop

Over 3.54 s the predecessor measured convection removing between 0.65 % and 1.1 %
of the injected energy. That is why h barely moves a single-stop peak, and why the
vent coefficient, cross-drilling and more vanes are not single-stop levers. Quote
**this run's** fraction from `results.json` -> `energy_audit`, never a remembered
number.
