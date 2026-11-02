---
name: brake-duty-cycle
description: "Gate 0: derive the duty cycle (PRD 5), write case.json."
version: 1.0.0
author: "sdefibaugh"
license: Apache-2.0
platforms: [windows]
metadata:
  hermes:
    tags: [brake, lead, physics, duty-cycle]
---

# brake-duty-cycle - from "100 km/h" to solver inputs

"A car braking from 100 km/h" is not a Fluent input. This skill turns the PRD
section 5 vehicle block into the time-varying heat source, rotor speed and
convection schedule that the fluent-engineer will apply, and writes them to
`00_lead\case.json`. It is Gate 0, it is yours, and it comes **before any CAD is
commissioned**, because everything downstream inherits it.

**Derive everything; inherit nothing.** Compute every number with a calculation
tool, not in your head, and print the arithmetic. Use `execute_code` if you have
it, otherwise `C:/solidpilot/.venv/Scripts/python.exe`; never bare `python` or
`python3` (it opens a Windows Store installer). Keep it to one calculation call.
Then compare against the PRD section 5 table. The PRD values are the check, not
the source.

| Reference | Open it when |
|---|---|
| `references/worked-arithmetic.md` | while computing: every row worked out to full precision, plus the h schedule table and the energy-per-window table |
| `references/case-json-schema.md` | when writing `case.json`: every field, unit and meaning |
| `references/traps-and-priors.md` | if a number from a published example appears, if someone proposes a constant source, or if a disc/pad split or closed-form pad temperature is about to be used as evidence |

## 1. Inputs (PRD section 5)

| Symbol | Value | Unit |
|---|---|---|
| m | 1800 | kg |
| v_entry | 100 | km/h |
| deceleration | 0.8 g | - |
| g | **9.80665** | m/s^2 (never 9.81; one convention everywhere) |
| front axle bias | 0.70 | - |
| front rotors | 2 | - |
| rolling radius R | 0.33 | m |
| pad sector | 60 deg, r = 120 to 160 mm | - |
| layer thickness d | 0.002 | m |
| dt | 0.01 | s |

## 2. Procedure

Each step ends with its check. Print `expected / computed / delta` for every row.

1. **Speed and deceleration.** v0 = 100 / 3.6 = 27.7778 m/s.
   a = 0.8 x 9.80665 = 7.84532 m/s^2. Check against PRD: exact.
2. **Stop time and distance.** ts = v0 / a = **3.54068 s**. Distance
   v0^2 / (2a) = **49.176 m**. The distance is a feel check: a hard stop from
   100 km/h in about 49 m is right; 4.9 m or 490 m means a unit slip.
   Gate: ts within 0.1 %.
3. **Energy per front rotor.** KE = 0.5 x 1800 x 27.7778^2 = 694 444.4 J.
   E = KE x 0.70 / 2 = **243 055.6 J**. Gate: within 0.1 %.
4. **Power.** Mean E / ts = 68 646.6 W. The true power is force times speed,
   so it starts at twice the mean and falls linearly to zero:
   P(t) = (2E / ts)(1 - t/ts) for 0 <= t <= ts, then 0. Peak P(0) = 137 293.1 W.
5. **Wheel speed and its sign.** abs(omega0) = v0 / R = 84.1751 rad/s
   (803.8 rpm). The **sign is derived from the vane hand**, section 3 below:
   omega0 = **-84.1751 rad/s** about +Z. Gate: within 0.1 % and negative.
   omega(t) = omega0 x max(0, 1 - t/ts).
6. **Reference speed for h.** omega_ref = (2/3) abs(omega0) = 56.1167 rad/s.
   This is the energy-weighted mean speed: both omega and power fall linearly,
   so the power-weighted mean of omega is omega0 x (1/3)/(1/2) = (2/3) omega0.
7. **Heat source in the virtual layer.** Pad contact area, each pad:
   A = (pi/6)(0.160^2 - 0.120^2) = 5.864306e-3 m^2. The source sits in a layer of
   thickness d = 0.002 m on one side of each of the two contacts, so the source
   volume is 2 A d = 2.345723e-5 m^3.
   q'''_peak = P(0) / (2 A d) = **5.8529e9 W/m^3**; q'''_mean = **2.9265e9 W/m^3**.
   Per-face heat flux at peak: P(0) / (2A) = 1.17058e7 W/m^2.
   Check by **integrating**, not multiplying: the integral of
   q'''(t) x 2 A d over 0 to ts must return 243 055.6 J.
8. **Convection schedule.** h(t) = max(7, h_ref x (abs(omega(t)) / omega_ref)^0.8)
   with h_ref = 130 (vent faces), 85 (outer rotor and hat faces), 40 (exposed pad
   and backing faces) W/(m^2 K). At t = 0 these are 179.81, 117.57 and 55.33.
   They reach the 7 W/(m^2 K) floor at t = 3.479 s, 3.437 s and 3.274 s.
9. **Time steps.** ts / dt = 354.068. That is **354 full steps plus one final
   step of 0.000681 s** (6.81e-4 s), 355 steps in all, ending at t = 3.540681 s.
   Do not label 354 x 0.01 = 3.54 s as the full stop (PRD sections 5 and 6).
10. **Update cadence.** Load and speed at least every 10 steps; h at least every
    25 (PRD section 6). Each window applies the exact interval average of the ramp (for a linear
    ramp this is the value at the window mid-time), so the windowed integral
    still equals E exactly.
11. **Sanity: bulk rise.** If all of E stayed in the rotor:
    E / (m_rotor x cp) = 243 055.6 / (12.973 x 447) = **41.9 K**. This is an upper
    estimate for THM-03 (<= 60 K), not a result.
12. **Write `case.json`** per `references/case-json-schema.md`, hash it, and
    record the hash in `BUILD_STATE.json`.

**Done when** every row of PRD section 5 reproduces, the three Gate 0 numbers are
within 0.1 %, and `case.json` validates against the schema reference (every
field present, every unit in its key name).

## 3. The rotation sign - derive it from the vane hand

The PRD vanes keep the circle branch whose polar angle **increases** with radius:
about -2.3 to +2.3 deg at r = 95 and +29.8 to +33.4 deg at r = 165. So
d(theta)/dr > 0 (the mean line sweeps about +32 deg from bore to rim).

The rule is **sign(omega) = -sign(d(theta)/dr)**. With no inlet swirl, the air
entering the vent at the bore sees a relative velocity
W = V_r r_hat - omega r theta_hat. Clean (shockless) entry needs the vane to lean
**opposite** to the direction of rotation as radius increases. A vane whose angle
increases with r therefore wants omega < 0: **clockwise viewed from +Z**,
omega0 = -84.1751 rad/s.

What the sign changes, and what it does not:

- **Thermally, nothing.** There is no air domain; h is a prescribed input.
  Reversing omega mirrors the conduction field with identical peaks. No gate moves.
- **The justification of the 130 W/(m^2 K) vent coefficient.** Its basis (about
  1.5 times the outer faces) presumes vanes that pump. Run the other way, the vanes
  meet the air at roughly 52 deg incidence and separate.
- **The casting hand.** It is a real manufacturing property. H1.2 has no 2D
  drawing, so the report (Gate 4) states "rotates clockwise viewed from +Z
  (outboard)" in the geometry section.

The predecessor flipped this sign twice (-56.12, then "corrected" to +56.117 the
wrong way, and a whole case ran on it). **Check it against the geometry, not
against memory.** At Gate 1, `cad_report.json` -> `vane_sweep.dtheta_dr_sign` must
be +1. If the built vanes sweep the other way, the CAD is wrong (the PRD fixes the
branch), not the sign rule: route to solidworks-engineer.

The CTS intent "pumps under +theta" is **unmet** by the PRD geometry (PRD
section 10). Report that as a finding; do not "fix" it by flipping omega.

## 4. What to print at Gate 0

```
GATE 0 - duty cycle (00_lead\case.json)
quantity                   formula                   computed        PRD            delta
v0 m/s                     100/3.6                   27.7778         27.7778        0.000 %
a m/s^2                    0.8 x 9.80665             7.84532         7.84532        0.000 %
ts s                       v0/a                      3.540681        3.54068        +0.00004 %
stopping distance m        v0^2/(2a)                 49.176          49.176         0.000 %
E per front rotor J        0.5 m v0^2 x 0.70/2       243 055.56      243 055.6      0.000 %
mean power W               E/ts                      68 646.55       68 646.6       0.000 %
peak power W               2E/ts                     137 293.10      137 293.1      0.000 %
omega0 rad/s               -(v0/0.33), sign by hand  -84.17508       -84.1751       0.000 %
omega_ref rad/s            (2/3) abs(omega0)         56.11672        56.1167        0.000 %
A pad m^2                  (pi/6)(0.16^2-0.12^2)     5.864306e-3     5.864306e-3    0.000 %
q''' peak W/m^3            P(0)/(2 A d)              5.852913e9      5.8529e9       0.000 %
q''' mean W/m^3            Pmean/(2 A d)             2.926457e9      2.9265e9       0.000 %
steps                      ts/dt                     354 + 0.000681 s  354 + 0.000681 s  exact
bulk rise K (upper est.)   E/(12.973 x 447)          41.91           about 41.9     -
integral of P dt J         windowed, 10-step         243 055.56      243 055.6      0.000 %
GATE 0: PASS (ts, E, omega0 within 0.1 %)
```

## 5. Traps (short form; detail in `references/traps-and-priors.md`)

- **Published example numbers.** The PyFluent brake example uses
  q''' = 2.0e9 W/m^3 (about 94 kJ per rotor here, a much lighter car) and passes -15.79 to a rad/s
  argument (it is rev/s, 2 pi too slow). Neither appears in this run.
- **Constant source.** A constant q''' puts the peak at the end of the stop, which
  a real brake never does, and lands about 5.7 % low on the peak. The ramp is the
  model.
- **9.81.** g = 9.80665 everywhere. With 9.81, ts = 3.5395 s and every
  downstream number shifts by 0.03 %.
- **Truncation.** 354 steps of 0.01 s stop at 3.54 s and miss 0.000681 s. The
  energy missed is only 0.009 J, but the rule is to cover the full stop, and the
  histories must end at 3.540681 s.
- **Disc/pad split as evidence.** A heat-partition assumption (for example 95/5)
  cannot pass or fail THM-02. It moves the closed-form pad peak from about 485 K to
  about 1106 K across its plausible range.

## Verification

- Every number in `case.json` was computed by a tool in this session, and the
  printed table shows the formula next to the value.
- ts = 3.54068 s, E = 243 055.6 J and omega0 = -84.1751 rad/s reproduce within
  0.1 %; omega0 is negative, and `case.json` records the rule and the vane-hand
  evidence it came from.
- The windowed integral of applied power equals E (to better than 0.01 %).
- `case.json` contains every field listed in `references/case-json-schema.md`,
  its SHA-256 is in `BUILD_STATE.json`, and `completed_gates` contains `"G0"`.
