# Component Technical Specification

> ### ILLUSTRATIVE DOCUMENT — NOT A REAL PROGRAM
>
> This specification is **fictional**, written to demonstrate an agentic CAE
> workflow. The part, the programme, the document number and the vehicle do not
> exist and correspond to no manufacturer's product. Nothing here is derived
> from, or contains, any company's proprietary or confidential information.
>
> The format follows real automotive practice so the demonstration is
> meaningful, and the thermal limits are sourced from open literature (§3.2).
> It is **not** engineering guidance and must not be used to design a real
> brake: a production rotor is sized by repeated-stop duty cycles, not by the
> single stop analysed here (§6).


## FR-330V Front Brake Rotor — Performance Variant

| | |
|---|---|
| **Document** | CTS-BRK-0117 rev C |
| **Program** | S-Platform MY28 Performance Pack *(fictional)* |
| **Part** | Front brake rotor, vented, Ø330 |
| **APQP phase** | Phase 2 — Product Design & Development |
| **Owner** | Chassis / Foundation Brake |
| **Status** | Released for design *(illustrative — see banner)* |
| **Supersedes** | CTS-BRK-0117 rev B (Ø320 solid, carryover) |

---

> **Document type.** This is a **component technical specification** — the
> bottom tier of the automotive requirements cascade
> (**vehicle → subsystem → component**) — paired with a **DVP&R extract**
> (Section 5) naming how each requirement is proven. The requirements below are
> numbered, individually verifiable, and each carries the method that closes it.
>
> **Naming varies by OEM and there is no standards-body term for the document
> itself.** GM calls this tier a Component Technical Specification (CTS), under
> a Subsystem Technical Specification (SSTS) and a Vehicle Technical
> Specification (VTS). Ford's equivalents are the System Design Specification
> (SDS) and Engineering Specification (ES); Stellantis issues a Statement of
> Requirements (SoR); VW Group and other German OEMs use a component
> *Lastenheft*, rendered officially in English as a performance specification.
> IATF 16949 §8.3.3.1 mandates the **content** — "product design input
> requirements" — and deliberately names no carrier document; AIAG PPAP §2.2.1
> calls the resulting controlled artefact the **design record**.
>
> What this document is **not** is a Product Requirements Document. "PRD" does
> not appear anywhere in IATF 16949 or the AIAG core manuals; it is software,
> consumer-product and medical-device vocabulary.

## 1. Scope and application

The S-Platform currently ships a Ø320 **solid** front rotor carried over from the
outgoing car. It is adequate for the base powertrain but has been the limiting
component in two places:

1. Press fade testing on the base car reported pedal lengthening on the third
   consecutive high-speed stop.
2. The Performance Pack adds 90 kW and 140 kg over base, which the carryover
   foundation brake was never sized for.

This specification releases a **vented, cross-drilled Ø330 rotor** for the Performance
Pack only. Base trim retains the carryover part; there is no common-part
requirement between them beyond the hub interface.

**The hub interface is frozen.** The wheel bearing, knuckle and wheel are all
carryover. Any change to PCD, centre bore or mounting-face offset re-opens three
other subsystems and is out of scope for this program.

---

## 2. Vehicle and duty cycle

These numbers are the design point. Everything downstream traces to them.

| Parameter | Value | Source |
|---|---|---|
| Kerb mass + driver | **1800 kg** | Vehicle mass study VMS-114 |
| Design entry speed | **100 km/h** | Worst routine stop, customer usage study |
| Design deceleration | **0.8 g** (7.848 m/s²) | Severest *routine* stop; tyres reach 1.0–1.2 g |
| Front axle bias | **0.70** | Static + dynamic weight transfer at 0.8 g |
| Tyre rolling radius | **0.33 m** | 245/40 R19 |
| Front rotors | 2 | |

**Derived duty, per front rotor** — the single stop this program is sized around:

| Quantity | Value |
|---|---|
| Stop duration | 3.54 s |
| Stopping distance | 49.2 m |
| Energy absorbed | **243 kJ** |
| Mean power | **68.6 kW** |
| Wheel speed at entry | 84.2 rad/s (804 rpm) |

> **Design point rationale.** 0.8 g is not the tyre limit — it is the severest
> stop a normal driver produces repeatedly. Sizing to 1.2 g would add unsprung
> mass for a condition customers reach a handful of times in a vehicle life;
> sizing to 0.5 g would fail the press fade test that started this program.

---

## 3. Requirements

**M** = mandatory (gate blocker) · **S** = should · **C** = could

### 3.1 Package and interface

| ID | Req | Value | Class | Verification |
|---|---|---|---|---|
| PKG-01 | Outer diameter | 330 mm max | M | CAD measure |
| PKG-02 | Overall thickness | 32 mm nominal | M | CAD measure |
| PKG-03 | Bolt circle diameter | **115 mm (5 × Ø14)** — carryover, frozen | M | CAD measure |
| PKG-04 | Centre bore | **Ø70** — carryover, frozen | M | CAD measure |
| PKG-05 | Mounting face offset | +43 mm from rotor mid-plane | M | CAD measure |
| PKG-06 | Wheel clearance | ≥ 6 mm radial to 19″ rim inner | S | Package check |

### 3.2 Thermal — the reason this program exists

| ID | Req | Value | Class | Verification |
|---|---|---|---|---|
| THM-01 | Peak rotor **friction-surface** temperature, single design stop | ≤ 923 K (650 °C) | M | **CFD** |
| THM-02 | Peak pad friction-surface temperature, single design stop | ≤ 623 K (350 °C) | M | CFD |
| THM-03 | Rotor bulk temperature rise, single design stop | ≤ 60 K | S | CFD |
| THM-04 | No rotor surface region above 1143 K (870 °C) | — | M | CFD |
| THM-05 | Vent passages must contribute measurable cooling | modelled explicitly | M | CFD, distinct vent HTC |
| THM-06 | Caliper / brake fluid temperature | ≤ 428 K (155 °C) | M | **Deferred — see §6** |

**Basis of the thermal limits.** These are not round numbers picked for
convenience; each has a named failure mode:

| ID | Failure mode it guards against | Where the number comes from |
|---|---|---|
| THM-01 | Heat checking, hot judder, thermo-mechanical fatigue | Industry **Single-Stop Temperature Rise (SSTR)** design practice: 350–400 °C drum, 550 °C solid disc, **600–650 °C vented disc**. This part is a vented disc, so it takes the top band. |
| THM-02 | Fade — phenolic binder decomposition and outgassing in the friction material | First-stage thermal fade for organic and low-metallic compounds is consistently reported at ~350 °C |
| THM-04 | Loss of iron material capability | Grey cast iron is reported serviceable to ~870 °C. **Between THM-01 and THM-04 the mechanism is fatigue and heat checking, not yield** — exceeding 650 °C degrades life, it does not fail the part in one stop |
| THM-06 | Vapour lock — fluid boils, pedal goes long | DOT 4 minimum **wet** boiling point, 155 °C. Alpine-descent fluid temperatures of 150–200 °C are documented, so this is a live constraint, not a formality |

> **SSTR is a temperature *rise*, not an absolute.** THM-01 is written as an
> absolute because the design stop starts from an initial brake temperature of
> 300 K; rise and absolute differ by 27 K here. On a duty cycle with a hot
> starting temperature they do not, and the limit must be re-derived.

> **THM-01 and THM-02 are the gate, and THM-02 is expected to govern.** Pad
> compound conductivity is ~40× lower than iron, so the pad runs hotter against
> a limit 300 K lower. A review that concludes "the rotor is fine" has answered
> the wrong question.

> **This specification sizes a SINGLE STOP.** It is not a duty cycle. Repeated
> stops (AMS 10-stop, Alpine descent, autobahn stop) drive the thermal design
> of a production rotor and are **not** covered here — see §6.

### 3.3 Mass and geometry

| ID | Req | Value | Class | Verification |
|---|---|---|---|---|
| MAS-01 | Rotor mass | ≤ 13.5 kg | M | CAD mass properties |
| GEO-01 | Vented construction, two cheeks + vanes | — | M | CAD |
| GEO-02 | Cheek thickness | 10 mm each | S | CAD |
| GEO-03 | Vent gap | 12 mm | S | CAD |
| GEO-04 | Curved (directional) vanes | ≥ 18 vanes | S | CAD |
| GEO-05 | Cross-drilled cooling holes through the swept band | ≥ 30 holes | C | CAD |
| GEO-06 | Hat attaches to the **inboard** cheek, vent inlet unobstructed | — | M | CAD section |

> **GEO-06 is not cosmetic.** A hat that spans the full height at the ring bore
> blocks the vent inlet, and the cooling result is then quietly wrong. Reference
> teardown of a comparable Ø380 rotor confirms the web lands on the inboard
> cheek. See `docs/HAT_ATTACHMENT_EVIDENCE.md`.

### 3.4 Friction pair

| ID | Req | Value | Class | Verification |
|---|---|---|---|---|
| PAD-01 | Pad sector angle | 60° | M | CAD |
| PAD-02 | Pad radial span | r 120–160 mm | M | CAD |
| PAD-03 | Pad thickness (friction material) | 12 mm | S | CAD |
| PAD-04 | Backing plate | 6 mm steel, r 115–165 | S | CAD |
| PAD-05 | Caliper must clear the full pad stack | slot ≥ stack + 4 mm | M | CAD interference |

### 3.5 Materials

| ID | Component | Material | ρ | c_p | k |
|---|---|---|---|---|---|
| MAT-01 | Rotor | Grey cast iron | 7200 | 447 | 52 |
| MAT-02 | Pad | Low-metallic compound | 2500 | 900 | 1.2 |
| MAT-03 | Backing plate | Steel | 8030 | 502 | 16.3 |

---

## 4. Concept sketch

See `concept_sketch.png`. Meridional section, dimensions in millimetres.

```
                    ← 43 →|
   ┌───────────────┐      |         MOUNTING FACE  z = +43
   │  HAT / HUB    │      |         5 × Ø14 on Ø115 PCD
   │               │      |         centre bore Ø70
   └──────┐        │      |
          │  bell wall    |
          └────┐          |
      ┌────────┴──────────────────────┐   OUTBOARD CHEEK  10
      │ ▓▓▓▓▓▓▓▓ cheek ▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │   z = +6 .. +16
      │  ○     ○     ○     ○   holes  │
      ├───┐   ┌───┐   ┌───┐   ┌───────┤   VENT GAP 12
      │   │   │   │   │   │   │ vanes │   z = -6 .. +6
      ├───┘   └───┘   └───┘   └───────┤
      │ ▓▓▓▓▓▓▓▓ cheek ▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │   INBOARD CHEEK  10
      └───────────────────────────────┘   z = -16 .. -6
      |←── 95 ──→|                   165
      bore                            OD
```

Vanes are **curved**, swept ~32° from bore to OD, **intended** to run the same
direction as forward rotation so they pump outward. Cooling-hole rows follow the
vane spiral, offset half a pitch so a hole never breaks into a vane.

> **Deviation — intent above vs geometry as built.** The built flank arcs
> (R123.0 / R117.0 mm about a common centre C = (20.722, 94.249) mm) give a mean
> line from **−0.0183° at r = 95** to **+31.6445° at r = 165**, so `dθ/dr > 0`.
> With no inlet swirl, shockless entry needs the vane to lean **opposite** to
> rotation as radius increases — `sign(ω) == −sign(dθ/dr)` — so this rotor pumps
> under **−θ about +Z**, clockwise viewed from +Z, the opposite sense to the
> intent stated above. Under +θ the outer tip **leads**, at ~**52°** inlet
> incidence: a forward-curved impeller, not the backward-curved standard.
>
> **The geometry won.** Nothing was rebuilt: the analysis runs at
> `omega_0 = −84.175 rad/s` / `omega_eff = −56.117 rad/s` about `[0,0,1]`, and
> the drawing carries the hand **derived from the arcs**. Two consequences to
> carry forward — the intent as written is **unmet as built**, and **THM-05's
> 130 W/m²K vent coefficient has an open basis**, because its 1.5×-outer
> justification presumes vanes that pump and at ~52° incidence they would
> separate. Thermally nothing moves: reversing ω mirrors the conduction field
> with identical peaks and there is no air domain, so `h` is an input either way.
> **No temperature and no gate moves.**

---

## 5. Design Verification Plan & Report (DVP&R) — extract

| ID | Requirement | Method | Stage | Acceptance |
|---|---|---|---|---|
| DV-01 | PKG-01..05 | CAD measurement | Design | Within tolerance |
| DV-02 | MAS-01 | CAD mass properties, cross-checked against closed-form volume | Design | ≤ 13.5 kg, arithmetic agrees within 1% |
| DV-03 | GEO-06 | CAD section view | Design | Vent inlet open |
| DV-04 | THM-01..05 | **Transient conduction CFD**, rotating rotor, vehicle-derived duty | Analysis | Section 3.2 limits |
| DV-05 | Energy conservation of the CFD model | Injected power vs vehicle kinetic energy | Analysis | Within ±2% |
| DV-06 | PAD-05 | CAD interference check | Design | Zero interference |
| DV-07 | Fade resistance, repeated stops | Dyno, AK-Master | Validation | **Not in this phase** |
| DV-08 | Thermal cracking, thermal shock | Dyno | Validation | **Not in this phase** |
| DV-09 | THM-06 caliper / fluid temperature | Thermal model including caliper, or dyno thermocouple | Analysis + Test | **Not in this phase** — the caliper is drawn but deliberately excluded from the thermal model (§6) |
| DV-10 | Repeated-stop duty cycle (AMS 10-stop, Alpine descent) | Transient thermal, multi-event | Analysis | **Not in this phase** — see §6 |

> **DV-04 is what this analysis delivers.** DV-07 through DV-10 need physical
> test, a caliper in the thermal model, or a repeated-stop duty cycle. A
> single-stop conduction model cannot answer them and must not be presented as
> if it can.

---

## 6. Out of scope

Explicitly excluded from this phase, and from the analysis that supports it:

- Structural stress, coning, thermal-crack prediction
- Pad wear, transfer-film stability
- Fade from binder outgassing
- Disc thickness variation / judder
- Airflow solution — the convection coefficients are **inputs**, not solved
- NVH, corrosion, manufacturing process design (APQP Phase 3)

Two exclusions worth naming explicitly, because a brake engineer will look for
them and their absence is a scope decision rather than an oversight:

- **Repeated-stop duty cycles.** A production rotor is thermally sized by
  repeated events — the AMS 10-stop press evaluation (10 consecutive stops from
  100 km/h at GVW), Alpine descent (conventionally ~10 miles at 10% gradient),
  and the autobahn stop — not by one stop from 100 km/h. Disc temperatures in
  those events reach 600–700 °C, where this single stop does not. **This
  specification sizes the single stop only** (DV-10).
- **Caliper and brake fluid temperature.** THM-06 is a real constraint —
  Alpine-descent fluid temperatures of 150–200 °C sit at or above the DOT 4
  minimum wet boiling point of 155 °C, and soak-back after the vehicle stops is
  the governing case. The caliper is drawn in CAD but **suppressed before
  meshing**, so this model cannot answer it (DV-09).

---

## 7. Gate criteria — Phase 2 exit

Phase 2 exits to Phase 3 when:

1. All **M** requirements verified or dispositioned with a written rationale
2. DV-01..DV-06 complete with recorded evidence
3. Design review package issued: drawing, 3D model, CFD report, recommendations
4. Open items carry an owner and a target phase

---

## 8. Traceability to the analysis inputs

Every number the CFD uses comes from Section 2, not from a solver example.
This is the check that stops an inherited parameter set producing a confident
answer for the wrong vehicle.

| CTS | Analysis input | Value |
|---|---|---|
| §2 mass, speed, decel, bias | `q_dot` | 2.93e9 W/m³ |
| §2 speed, tyre radius | `omega` | −56.12 rad/s (energy-weighted mean) |
| §2 decel | `n_steps` | 354 at 0.01 s |
| §3.2 THM-05 | `htc_vent` | 130 W/m²K, distinct from outer |
| §3.5 | Per-zone materials | MAT-01..03 |

`solve.py` recomputes `q_dot`, `omega` and `n_steps` from the vehicle block and
**fails the run** if the stated values disagree by more than 1%.
