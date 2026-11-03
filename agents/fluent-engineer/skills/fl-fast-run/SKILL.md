---
name: fl-fast-run
description: "Gate 3 fast: run fluent_fast.py and judge it."
version: 2.0.0
author: "sdefibaugh"
license: Apache-2.0
platforms: [windows]
metadata:
  hermes:
    tags: [brake, fluent, meshing, transient, fast]
---

# fl-fast-run - mesh and heat-up solve in one job (PRD H1.2, fast run profile)

Gate 3 meshes the PMDB, sets up the transient conduction case from `case.json`,
and solves the whole stop on a coarse mesh, enough to show the rotor and pads
heating up with a closed energy balance. The work is done by a vetted stage
script, `scripts/stages/fluent_fast.py`, built from the calls that worked on run
FR330V-20261102-0936. You check the preconditions, launch it once, judge
`results.json` and route a failure. You do not rewrite the script during a run.

Measured on 2026-11-02 for the first second: about **126 s** (launch 32, mesh
34, mesh gate 15, setup 26, solve 14, contour 3). The full stop adds about 35 s.

## Fast run profile (PRD section 6A)

| Setting | Fast value | PRD full value |
|---|---|---|
| Mesh | global 4 to 20 mm, growth 1.2, curvature 18 deg; cheeks 8, vanes 8, hat 12 mm | 2.2 to 20 mm; 4 / 5 / 8 mm |
| Simulated time | 0 to 3.540681 s, the full stop (70 x 0.05 s + one short step) | 0 to 3.540681 s |
| Time step | 0.05 s, 71 steps | 0.01 s, 355 steps |
| Iterations per step | 3 | 5 |
| Load windows | q''' and omega every 4 steps (interval average), h every 24 steps | every 10 / 25 steps |
| Outputs | `results.json`, mesh, case and data; a live contour in the Fluent window | plus images, histories, report |

Loads, materials, the one-sided grey-iron wall layer, rotation of the two cheeks
only, and the three convection groups are the PRD values read from `case.json`.
Override a setting only when the lead's commission says so, with the env vars
`FAST_END_TIME_S`, `FAST_DT_S`, `FAST_ITERS`, `FAST_WINDOW_STEPS`,
`FAST_MESH_MIN_MM` set in the launcher.

## What the script checks (all must pass)

| Check | Expected |
|---|---|
| solid zones / fluid zones | 27 / 0, names equal to the PRD body names |
| coupled pairs (walls ending `-shadow`) | 45 |
| friction contact areas (mesh) | 5 864.31 mm^2 each, within 2 % |
| zone materials read back | 27 correct |
| friction layer material read back | `grey-iron` on both friction walls |
| meshed volume of 27 zones | 2 030 484.53 mm^3 within 2 % |
| applied energy vs closed form q''' x d x A_mesh integral | within 2 % |
| stored / applied energy (convection is about 1 % over 1 s) | 90 to 110 % |
| stored energy | rises in every window (a fall below 0.01 % is allowed at the very end, where convection outweighs the vanishing input) |
| full stop covered; applied vs vehicle energy E | t = 3.540681 s; within 2 % of 243 055.6 J |
| friction-face temperatures | above 300 K, below 1500 K |

The friction-face temperature peaks early (about 0.2 s) and then eases as the
power ramps down. That is the expected physics, not a failure.

On PASS the script leaves **Fluent open** with a temperature contour on the
external walls: that is the visual. On any FAIL it closes the Fluent processes it
started.

## Procedure

1. **Preconditions** (one bash call, through the `C:\brake-runs` mount):
   `20_spaceclaim\brake.pmdb\brake.pmdb` and `00_lead\case.json` exist and their
   SHA-256 equal your commission. Refuse to proceed on a mismatch.
2. **Launch** with `submit_ansys_job`, `cwd = <RUN>\30_fluent`, job name
   `g3_fluent_fast`, and exactly this script text:

   ```python
   import os, runpy
   os.environ["BRAKE_RUN"] = r"C:\brake-runs\<run-id>"
   runpy.run_path(r"<PROJECT>\scripts\stages\fluent_fast.py", run_name="__main__")
   ```

3. **Wait** with `job_status(job_id, wait_seconds=55)`, about three polls. A
   `ValueError: invalid literal for int()` traceback in stderr comes from a
   pyfluent event-stream thread and is harmless; judge only `results.json`.
4. **Judge** `<RUN>\30_fluent\results.json` yourself: `status` is `PASS`, every
   `checks[]` row passes, `history` has one row per window ending at
   3.540681 s, and `live_contour.displayed` is true.
5. **Report** to the lead with the handback JSON: every check as expected /
   measured / PASS|FAIL, the `summary` block (peak and final friction-face
   temperatures, applied and stored energy), `timing.seconds` and
   `phase_seconds`. Say plainly that Fluent is left open for viewing.

## When it does not pass

| Symptom (from `results.json`) | Owner | What to return |
|---|---|---|
| `status: BLOCKED` | the user | the PIDs of the running Ansys processes |
| zones, pairs or volume gate fails | spaceclaim-engineer (tagging) or solidworks-engineer (geometry) | the failing row and the mesh sha256 |
| energy gate fails | lead (package defect) | applied, stored, ratio and the history rows |
| `error` / `traceback` set | lead (package defect) | the last traceback lines |

One relaunch for an infrastructure failure (Fluent died, licence busy), with
the reason recorded; never a third. For diagnosis: `references/api-verified.md`
(ansys-fluent-core 0.41.0 calls that work), `references/coupled-pair-inventory.md`,
`references/wall-layer-and-convection.md` and `references/failure-modes.md`.

## Verification

- `results.json` exists, `status` is `PASS`, every `checks[]` row passes.
- `inputs_sha256` equals the hashes in your commission.
- `history` ends at `settings.end_time_s`; stored over applied is 90 to 110 %.
- On PASS, Fluent is running with the contour shown; on FAIL, no Fluent process
  started by this job is left.
- Your handback lists `timing.seconds` and the phase breakdown.
