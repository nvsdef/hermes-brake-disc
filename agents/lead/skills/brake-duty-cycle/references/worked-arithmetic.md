# Worked arithmetic - PRD section 5 reproduced to full precision

Use this to check your own tool output line by line. Every value below was
computed with g = 9.80665 m/s^2 and reproduces the PRD section 5 table. Your
numbers must come from your own calculation in this session; this page is the
answer key, not the source.

## 1. Kinematics

```
v0        = 100 / 3.6                        = 27.777778 m/s
a         = 0.8 x 9.80665                    = 7.845320 m/s^2
ts        = v0 / a = 27.777778 / 7.845320    = 3.540681 s        (PRD 3.54068)
distance  = v0^2 / (2 a) = 771.6049 / 15.69064 = 49.1761 m       (PRD 49.176)
```

## 2. Energy and power

```
KE        = 0.5 x 1800 x 27.777778^2         = 694 444.44 J
E         = KE x 0.70 / 2                    = 243 055.56 J      (PRD 243 055.6)
P_mean    = E / ts = 243 055.56 / 3.540681   = 68 646.55 W       (PRD 68 646.6)
P_peak    = 2 E / ts                         = 137 293.10 W      (PRD 137 293.1)
P(t)      = 137 293.10 x (1 - t / 3.540681) W,  0 <= t <= ts;  0 after
check     : integral of P(t) dt from 0 to ts = P_peak x ts / 2 = 243 055.56 J
```

## 3. Rotation

```
|omega0|  = v0 / 0.33 = 27.777778 / 0.33     = 84.175084 rad/s   = 803.81 rpm
omega0    = -84.175084 rad/s about +Z (sign from the vane hand: d(theta)/dr > 0)
omega_ref = (2/3) x 84.175084                = 56.116723 rad/s   (PRD 56.1167)
omega(t)  = -84.175084 x max(0, 1 - t / 3.540681) rad/s
revolutions over the stop = |omega0| x ts / 2 / (2 pi) = 23.72 rev
```

Why 2/3: power and speed both fall linearly, so the power-weighted mean speed is
omega0 x integral((1 - tau)^2) / integral(1 - tau) = omega0 x (1/3) / (1/2).

## 4. Heat source

```
A (each pad)  = (pi / 6) x (0.160^2 - 0.120^2)   = (pi / 6) x 0.0112 = 5.864306e-3 m^2
d             = 0.002 m (declared virtual layer; a modelling assumption)
V_source      = 2 x A x d                         = 2.345723e-5 m^3
q'''_peak     = 137 293.10 / 2.345723e-5          = 5.852913e9 W/m^3  (PRD 5.8529e9)
q'''_mean     = 68 646.55 / 2.345723e-5           = 2.926457e9 W/m^3  (PRD 2.9265e9)
q''_peak/face = 137 293.10 / (2 x 5.864306e-3)    = 1.170583e7 W/m^2
q'''(t)       = 5.852913e9 x (1 - t / 3.540681) W/m^3
```

Integrate to check: q'''(t) x V_source integrated from 0 to ts equals E.

## 5. Time steps

```
ts / dt       = 3.540681 / 0.01                   = 354.0681
full steps    = 354  (ending at t = 3.54 s)
final step    = 3.540681 - 3.54                   = 0.000681 s (6.81e-4 s)
total steps   = 355, ending at t = 3.540681 s
energy that truncation at 3.54 s would miss = P_peak x (ts - 3.54)^2 / (2 ts) = 0.009 J
```

This matches PRD section 5 (final step 0.000681 s).

## 6. Energy per load window (update every 10 steps = 0.1 s)

Each window applies the ramp value at the window mid-time, which is the exact
interval average for a linear ramp, so the windowed sum equals E exactly.

| window | t start s | t end s | P applied W | energy J | cumulative J | omega at mid rad/s |
|---|---|---|---|---|---|---|
| 0 | 0.0 | 0.1 | 135 354.3 | 13 535.43 | 13 535.43 | -82.9864 |
| 1 | 0.1 | 0.2 | 131 476.7 | 13 147.67 | 26 683.10 | -80.6090 |
| 2 | 0.2 | 0.3 | 127 599.1 | 12 759.91 | 39 443.01 | -78.2317 |
| 17 | 1.7 | 1.8 | 69 435.3 | 6 943.53 | 184 310.62 | -42.5711 |
| 32 | 3.2 | 3.3 | 11 271.4 | 1 127.14 | 241 932.46 | -6.9106 |
| 33 | 3.3 | 3.4 | 7 393.8 | 739.38 | 242 671.84 | -4.5332 |
| 34 | 3.4 | 3.5 | 3 516.2 | 351.62 | 243 023.47 | -2.1558 |
| 35 | 3.5 | 3.540681 | 788.7 | 32.09 | 243 055.56 | -0.4836 |

The last window is only 0.040681 s long (4 full steps plus the short step). A
schedule that applies the window 35 power (788.7 W) for a full 0.1 s
over-applies 46.8 J; a
schedule that stops at window 34 misses 32.09 J. Both are small, and both are
defects.

Use this table to audit the solver: the fluent-engineer's pre-solve applied-energy
integral must be 243 055.6 J +/- 2 % (238 194.4 to 247 916.7 J), and its first
window must apply about 13 535 J.

## 7. Convection schedule

h(t) = max(7, h_ref x (|omega(t)| / 56.116723)^0.8), T_inf = 300 K.

Instantaneous values:

| t s | |omega| rad/s | vent (130) | outer (85) | pad/backing (40) |
|---|---|---|---|---|
| 0.0 | 84.175 | 179.81 | 117.57 | 55.33 |
| 0.5 | 72.288 | 159.19 | 104.09 | 48.98 |
| 1.0 | 60.401 | 137.88 | 90.15 | 42.43 |
| 1.5 | 48.515 | 115.71 | 75.66 | 35.60 |
| 1.7703 (ts/2) | 42.088 | 103.28 | 67.53 | 31.78 |
| 2.0 | 36.628 | 92.41 | 60.42 | 28.43 |
| 2.5 | 24.741 | 67.52 | 44.14 | 20.77 |
| 3.0 | 12.854 | 39.99 | 26.14 | 12.30 |
| 3.3 | 5.722 | 20.93 | 13.68 | 7.00 |
| 3.5 | 0.967 | 7.00 | 7.00 | 7.00 |

Floor reached at: vent t = 3.479 s (|omega| 1.456), outer t = 3.437 s (2.476),
pad/backing t = 3.274 s (6.352).

h at 25-step windows (0.25 s), evaluated at the window mid-time:

| window | t s | vent | outer | pad/backing |
|---|---|---|---|---|
| 0 | 0.00 to 0.25 | 174.71 | 114.24 | 53.76 |
| 1 | 0.25 to 0.50 | 164.41 | 107.50 | 50.59 |
| 4 | 1.00 to 1.25 | 132.43 | 86.59 | 40.75 |
| 7 | 1.75 to 2.00 | 98.36 | 64.31 | 30.26 |
| 10 | 2.50 to 2.75 | 60.95 | 39.85 | 18.75 |
| 13 | 3.25 to 3.50 | 15.52 | 10.15 | 7.00 |
| 14 | 3.50 to 3.540681 | 7.00 | 7.00 | 7.00 |

At omega_ref the value equals h_ref, which is why the (2/3) choice matters: it
makes the reference coefficients the energy-weighted averages over the stop.

## 8. Material diffusivity and penetration depth over the stop

| Material | k W/(m K) | rho kg/m^3 | cp J/(kg K) | alpha m^2/s | sqrt(alpha ts) mm | effusivity sqrt(k rho cp) |
|---|---|---|---|---|---|---|
| MAT-01 grey iron | 52 | 7200 | 447 | 1.6157e-5 | 7.564 | 12 937 |
| MAT-02 pad | 1.2 | 2500 | 900 | 5.3333e-7 | 1.374 | 1 643 |
| MAT-03 steel | 16.3 | 8030 | 502 | 4.0436e-6 | 3.784 | 8 106 |

These depths are what the review compares with the measured wall-normal cell size
at the friction faces (PRD section 7, temperature honesty).

## 9. Bulk sanity

```
m_rotor   = 1 801 776.57e-9 m^3 x 7200 kg/m^3 = 12.9728 kg   (PRD 12.973)
dT_bulk   = 243 055.56 / (12.9728 x 447)      = 41.91 K      (upper estimate, THM-03 <= 60 K)
```

It is an upper estimate because some energy goes into the pads and some leaves by
convection. A solved bulk rise above 41.9 K means the energy audit is wrong.
