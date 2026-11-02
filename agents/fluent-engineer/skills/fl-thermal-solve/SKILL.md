---
name: fl-thermal-solve
description: "Set up and run the transient brake conduction solve."
version: 3.0.0
author: "sdefibaugh"
license: Apache-2.0
platforms: [windows]
metadata:
  hermes:
    tags: [brake, fluent, thermal, solver]
---

# fl-thermal-solve - setup and solve, second part of Gate 3 (PRD H1.2)

Start this only after the internal mesh gate in `fl-meshing` passed, in the
**same Fluent session** (now in solver mode). No new launch. Setup is a series
of short steps; the transient solve is one long job. Monitors from
`fl-postprocess-energy` step 1 are created here, before the first time step.

API names: use only the verified sheet in the fl-meshing skill,
`agents\fluent-engineer\skills\fl-meshing\references\api-verified.md` (load it
with `skill_view("fl-meshing", ...)` or read the file). Session, polling and
relaunch rules are in the fl-meshing file `persistent-session.md`.

| Reference | Open it when |
|---|---|
| `references/time-varying-physics.md` | step 9: windows, interval averages, the final short step |
| `references/rotating-zone-physics.md` | step 6: motion and the tangential-velocity check |
| `references/wall-layer-and-convection.md` | steps 5, 7, 8: friction pairs, source, layer, h groups |
| `references/solver-api-idioms.md` | any settings call; round-trip pricing; the solve job |
| `references/upstream-example-traps.md` | before borrowing anything from the PyFluent brake example |

## The model (from case.json; PRD sections 5 to 7)

27 solid zones, energy on, flow off, double precision, transient, 300 K start.
MAT-01 grey iron (rho 7200, cp 447, k 52) on 23 rotor zones; MAT-02 pad
(2500, 900, 1.2) on 2 pads; MAT-03 steel (8030, 502, 16.3) on 2 backing plates.
Solid motion only on `cheek_out`, `cheek_in`: axis (0, 0, 1) through the
origin, `omega(t) = -84.1751 x max(0, 1 - t/3.54068)` rad/s. Source
`q'''(t) = P(t) / (2 A d)`, P(t) = (2E/ts)(1 - t/ts), E = 243 055.6 J,
A = 5.864306e-3 m^2, d = 0.002 m, peak 5.8529e9 W/m^3. Convection
`h(t) = max(7, h_ref x (abs(omega)/56.1167)^0.8)` with h_ref 130 (vent), 85
(outer), 40 (pad/backing), against 300 K. dt = 0.01 s for 354 steps, then one
step of 0.000681 s.

## Rules

Short steps: connect, one change, **read it back**, print compact JSON, detach.
Each settings call is a round trip (about 2.5 s measured): set a wall's three
convection fields in one call. Readback keys are canonical names:
`heat_generation_rate` (not `q_dot`), `thermal_condition` (not `thermal_bc`).

## Checklist

**1. Preconditions.** In `execute_code` (no Fluent): recompute ts, E, omega0,
omega_ref and peak q''' from case.json inputs; validate every key you read;
confirm `mesh_report.json` gates all PASS; delete stale `30_fluent\*.out`.
Expected: each within 0.1 % of PRD section 5.
On miss: BLOCKED, back to the lead.

**2. Probe.** Connect; expect `Solver`; list cell zones and walls.
Expected: 27 solid, 0 fluid, 45 coupled pairs, as in `mesh_report.json`.
On miss: stop; the loaded mesh is not the gated mesh.

**3. General settings.** Transient `unsteady-2nd-order-bounded` (or first
order, stated), energy on, flow off.
Done when: readback shows all three.

**4. Materials.** Create `grey-iron`, `pad-compound`, `backing-steel`; assign
all 27 zones; read back each zone's material and its rho, cp, k.
Expected: 27 of 27 correct within 0.01 %.
On miss: fix and re-read. A default zone material gives a smooth, wrong field.

**5. Friction pairs and sides.** Find the two coupled pad/cheek pairs; measure
each area and which zone is the pad side (area-average of cp: 900 pad, 447
iron). Never infer the side from a name.
Expected: 2 pairs, 5 864.31 mm^2 each within 2 %, z = +/-0.016 m.
On miss: stop; 0, 1 or 3 pairs means the mesh changed.

**6. Solid motion, cheeks only; tangential-velocity check.**
Enable on the two cheeks with the first window's omega; disable on 25 zones;
read back all 27. Compute the integral of abs((ez x r) . n) dA over the cheek
boundaries per rad/s.
Expected: exactly 2 enabled, axis (0, 0, 1), origin (0, 0, 0), omega -82.99
rad/s (first 10-step window average); integral <= 1.592987e-4 m^3/s per rad/s.
On miss: do not solve.

**7. Friction source, one side of each pair.** On one zone per pair:
`wall_thickness` 0.002 m, `q_dot` = first-window q''', layer
`thermal.material = "grey-iron"`. The other zone gets no source.
Done when: readback of `heat_generation_rate`, `wall_thickness` and `material`
answers (record the path that answered). A blind source readback is recorded as
blind; step 9's energy integral then stands in. Aluminium layer = FAIL.

**8. Convection groups.** Vent (all expanded `wall-vent*`), outer (all
`wall-outer*`), pad/backing (remaining non-coupled walls, by subtraction). One
settings call per wall: Convection, h of the first h block, 300 K.
Expected: group areas equal `mesh_report.json` within 0.1 %; all walls =
convection walls + 90 coupled walls; no coupled wall convective.

**9. Schedule and planned energy (execute_code).** Windows of at most 10 steps
for q''' and omega, h blocks of at most 25 steps, exact interval averages, the
final 0.000681 s step. `E_planned = sum(q'''_w x dt_w) x d x (A_out + A_in)`
with the **measured** pair areas.
Expected: E_planned within +/-2 % of 243 055.6 J; schedule covers 0 to
3.540681 s. Print the round-trip projection.
On miss: do not solve.

**10. Initialize, monitors, controls, setup_report.** Initialize 300 K; create
the 12 monitors and the one report file of `fl-postprocess-energy` step 1;
energy residual 1e-8; dt 0.01 s; 5 iterations per step. Write
`setup_report.json` from readbacks (header with `prd_revision` "H1.2", zone
materials, motion, friction pairs, h schedule, layer, time step and count,
E_planned, `timing`) and hash it.
Done when: every zone's volume-average T reads 300 K.

**11. Solve as one long job.** `submit_ansys_job(job_name="<run-id>_solve")`
that connects to the same session and, per window: applies q''' and omega (and
h at a new block), reads back at a stated cadence, runs
`dual_time_iterate(time_step_count=n, max_iter_per_step=5)`, takes the energy
sample of `fl-postprocess-energy` step 2, appends one progress line
(`flush=True`) and a progress JSON. At the planned peak instants (about 0.1 s
and 1.8 s) it writes a data file for the peak-time contours
(`fl-postprocess-energy` reference `monitors-and-contours.md`). It ends with
`file.write(file_type="case-data", ...)` as `brake-final.cas.h5` and detaches.
Wait with the 240 s wait script (about 4 waits for 11 to 15 min), not a
tight poll.
Abort inside the job (write data, write histories, detach) on: T at the clip
limit (5000 K); growth above the adiabatic bound; zero rise after window 1;
(stored + convected) / applied outside 80 to 120 % after 0.2 s; wrong motion
readback.

**12. Check completion.** Final flow time 3.540681 s within 1e-6 s; case and
data hashed; monitor file covers 0 to ts. Continue with
`fl-postprocess-energy` in the same session.

## Traps (details in the references)

- Only the cheeks rotate: a merged rotor lost 92 % of its energy and converged.
- q''' on both sides of a pair doubles the heat (audit about 200 %).
- A bare `wall-vent` reaches one of about 22 zones.
- A near-miss case.json key reads as absent and a default wins.
- `transient_controls.time_step_size` does not exist in v261; use
  `run_calculation.parameters.time_step_size`.

## Verification

| Check | Expected | Tolerance |
|---|---|---|
| Fluent launches in Gate 3 | 1 (the host job) | exact |
| Mesh hash | equals `mesh_report.json.mesh_sha256` | exact |
| Zones with correct material and rho, cp, k | 27 of 27 | 0.01 % |
| Motion enabled | exactly `cheek_out`, `cheek_in` | exact |
| omega, first window | -82.99 rad/s | 0.1 % |
| Axis / origin | (0, 0, 1) / (0, 0, 0) | exact |
| Tangential-velocity integral | <= 1.592987e-4 m^3/s per rad/s | |
| Source zones / thickness / layer material | 2 / 0.002 m / grey iron, not aluminium | exact |
| Convection walls | 3 groups, areas match mesh report | 0.1 % |
| E_planned vs 243 055.6 J | within +/-2 % | |
| Cadence | load <= 10 steps, h <= 25 steps | |
| Final flow time | 3.540681 s | 1e-6 s |
| Case, data, setup_report hashes | recorded | |
| `timing` in `setup_report.json` | present | |

Any FAIL follows the HALT protocol in `SOUL.md`.
