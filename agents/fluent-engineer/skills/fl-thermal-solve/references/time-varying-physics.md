# Time-varying physics: the three ramps, the schedule and the final step

Open this when building the window schedule, when checking a ramp value, or
when a temperature peak lands at the end of the stop.

## The three time laws (PRD sections 5 and 6)

```
P(t)      = (2E/ts) x (1 - t/ts)                     0 <= t <= ts, then 0
q'''(t)   = P(t) / (2 A d)                           per friction layer
omega(t)  = omega0 x max(0, 1 - t/ts)                cheek_out, cheek_in only
h_g(t)    = max(7, h_ref,g x (abs(omega(t)) / omega_ref)^0.8)
```

| Symbol | Value | Source |
|---|---|---|
| E | 243 055.6 J per front rotor | PRD 5 |
| ts | 3.54068 s (3.540681 s to 7 figures) | PRD 5 |
| 2E/ts (peak power) | 137 293.1 W | PRD 5 |
| A (each contact) | 5.864306e-3 m^2 | PRD 5 |
| d | 0.002 m | PRD 6 |
| q'''(0) | 5.8529e9 W/m^3 | PRD 5 |
| omega0 | -84.1751 rad/s about +Z | PRD 5 |
| omega_ref | 56.1167 rad/s = (2/3) abs(omega0) | PRD 5 |
| h_ref | vent 130, outer 85, pad/backing 40 W/(m^2 K) | PRD 6 |

At t = 0 the h values are h_ref x 1.5^0.8 = h_ref x 1.3832: vent 179.8, outer
117.6, pad/backing 55.3 W/(m^2 K). The 7 W/(m^2 K) floor takes over at about
t = 3.274 s (pad/backing), 3.437 s (outer) and 3.479 s (vent).

## Why everything ramps

Braking power is force times speed. At constant deceleration it starts at twice
the mean and falls linearly to zero. The predecessor's semi-infinite-solid
estimate illustrates the consequence:

| Source model | Pad surface peak rise | Time of peak |
|---|---|---|
| constant power | 378.2 K | at the end, 3.54 s |
| linear ramp | 356.5 K | near 1.77 s |

A constant source peaks at the end of the stop and cannot produce the right
shape. The ramp peaks well before the end and the surface is cooling when the car
stops. The wall-layer temperature peaks even earlier, because the flux into the
layer is largest at t = 0; the predecessor saw its wall-layer monitors peak at
0.1 s (pad) and 0.2 s (rotor).

**A cell-maximum peak at exactly ts is the signature of a source that did not
ramp.** Check the peak times after the run.

## Exact interval averages

Fluent holds a boundary value constant over each time step. The load is changed
once per window of n steps. Use the **exact average** of each law over the
window so the integral is preserved exactly, whatever n is.

For a window from t_a to t_b with t_b <= ts:

```
q'''_w  = q'''(0) x (1 - (t_a + t_b) / (2 ts))      exact, because q''' is linear
omega_w = omega0  x (1 - (t_a + t_b) / (2 ts))      exact, because omega is linear
```

For h, which is nonlinear and floored, compute the average over the h block
numerically (for example 1 000 sub-samples) or in closed form using
`integral (1 - t/ts)^0.8 dt = -(ts / 1.8) (1 - t/ts)^1.8`, handling the floor
piecewise. Record the method.

Because each window carries its exact average, the sum `sum(q'''_w x dt_w)` equals
the closed-form integral to rounding error at any window length. The predecessor
measured the sum bit-identical at windows of 5, 10, 25, 50 and 354 steps. That
is a check you can print: compute it both ways and show the ratio is 1 within
1e-9.

## Cadence (PRD section 6)

- Load (q''') and speed (omega): a new value at least every 10 steps.
- Convection h: a new value at least every 25 steps.

The predecessor measured what the h cadence costs in accuracy, on its own run:

| h update stride | Applications | Mean-h error | Energy change | Bulk-rise change |
|---|---|---|---|---|
| 5 steps | 71 | 0.000 % | 0.00 J | 0.00000 K |
| 10 steps | 36 | +0.005 % | 0.11 J | 0.00002 K |
| 25 steps | 15 | +0.036 % | 0.79 J | 0.00012 K |
| 354 steps | 1 | +3.329 % | 73.67 J | 0.01138 K |

Convection removes only about 1 % of the energy over one stop, so the h cadence
barely moves the result. Over a 10-step window omega changes by 84.18 x 0.1 /
3.5407 = 2.4 rad/s, 2.8 % of omega0, and never changes sign.

## The schedule for this run

Step edges: t_i = 0.01 x i for i = 0 to 354, then ts. Using 10-step windows
gives 35 windows of 0.1 s, one window from 3.50 to 3.54 s (4 steps), and one
final window from 3.54 s to ts (1 step of 0.000681 s): 37 windows.

Check values the schedule must reproduce (computed from the PRD numbers):

| Window | t_a to t_b, s | q'''_w, W/m^3 | omega_w, rad/s |
|---|---|---|---|
| 1 | 0.000 to 0.100 | 5.770261e9 | -82.9864 |
| 2 | 0.100 to 0.200 | 5.604956e9 | -80.6090 |
| 3 | 0.200 to 0.300 | 5.439651e9 | -78.2317 |
| 35 | 3.400 to 3.500 | 1.499005e8 | -2.1558 |
| 36 | 3.500 to 3.540 | 3.418716e7 | -0.4917 |
| 37 | 3.540 to 3.540681 | 5.631064e5 | -0.0081 |

With 25-step h blocks (0.25 s), the block-average h values are:

| Block, s | vent | outer | pad/backing |
|---|---|---|---|
| 0.00 to 0.25 | 174.71 | 114.23 | 53.76 |
| 0.25 to 0.50 | 164.40 | 107.49 | 50.58 |
| 1.00 to 1.25 | 132.42 | 86.58 | 40.74 |
| 1.75 to 2.00 | 98.35 | 64.30 | 30.26 |
| 2.50 to 2.75 | 60.92 | 39.83 | 18.74 |
| 3.25 to 3.50 | 15.34 | 10.44 | 7.02 |
| 3.50 to ts | 7.00 | 7.00 | 7.00 |

`sum(q'''_w x dt_w) x d x 2A` over the 37 windows = 243 055.6 J with the PRD
area. With the measured areas it differs from E only by the area difference.

## The final short step

`354 x 0.01 s = 3.54 s`, which is 0.000681 s short of ts. The PRD requires the
whole stop, so run one more step with dt = 0.000681 s. It carries only about
0.009 J, but the requirement is coverage, and a run labelled "354 x 0.01 s" is
not the full stop (DECISIONS item 8, PRD sections 5 and 6).

Set the new step size explicitly before the last step and read it back. Record
the final flow time; it must equal 3.540681 s within 1e-6 s.

## Iterations per step and convergence

Start with 5 iterations per step and the energy residual criterion at 1e-8
(PRD section 6). Record for every step whether the criterion was met before the
iteration limit. Increase iterations only with evidence (steps that hit the limit
with the residual still falling). Iteration count alone does not prove
convergence, and more iterations cannot fix a wrong setup: the predecessor's
merged-rotor run got **worse** with 30 iterations per step (conservation 49.5 %
to 26.6 %) and with dt / 5 (49.5 % to 41.3 %). That is the signature of a
defective operator, not an under-resolved one.

## Sanity bounds for abort decisions

- **Adiabatic step bound.** In one step the most a near-wall cell can rise is
  about `q'' x dt / (rho x cp x h_n)`, where q'' = P / (2A) is the flux per
  contact (1.1706e7 W/m^2 at t = 0) and h_n the wall-normal cell size. For a
  1.9 mm pad cell and dt = 0.01 s that is about 27 K per step even if all the
  heat went into the pad; for a 1.85 mm iron cell about 20 K. A cell
  temperature rising far faster than this is nonphysical.
- **Heat partition.** The split between pad and rotor is an output, set by
  the two materials. A semi-infinite estimate uses the effusivities
  sqrt(k rho cp): iron 12 940, pad 1 643 W s^0.5/(m^2 K), so roughly 89 % of
  the heat enters the rotor. A rotor share far outside roughly 80 to 95 % is a
  question to investigate, not a gate.
- **Bulk rise.** If all of E stayed in the rotor, the bulk rise would be
  E / (m_rotor x cp) = 41.9 K (PRD section 5). The solved rotor bulk rise must be
  below that.
- **The hat stays near 300 K.** The diffusion length in iron over the stop is
  about 7.6 mm. Heat needs tens of seconds to reach the hat junction. A cold hat
  after one stop is correct.
