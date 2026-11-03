---
name: sc-fast-prep
description: "Gate 2 fast: run spaceclaim_prep.py and judge it."
version: 2.0.0
author: "sdefibaugh"
license: Apache-2.0
platforms: [windows]
metadata:
  hermes:
    tags: [brake, spaceclaim, geometry, fast]
---

# sc-fast-prep - SpaceClaim prep in one job (PRD H1.2, fast run profile)

Gate 2 turns the frozen `brake.step` (28 solids) into `brake.pmdb` (27 named
solids plus two face groups) that Fluent can mesh. The work is done by a vetted
stage script, `scripts/stages/spaceclaim_prep.py`, built from the code that
passed Gate 2 on run FR330V-20261102-0936. Your job is to check the
preconditions, launch it once, judge its report against the PRD numbers, and
route a failure to its owner. You do not rewrite the script during a run.

Measured on 2026-11-02: the whole stage takes about **62 s** (SpaceClaim boot
about 45 s, import 4 s, everything else under 5 s).

## What the script does

1. Refuses to start (status `BLOCKED`, exit 3) if SpaceClaim, Discovery or
   Fluent is already running. Ansys Student allows one session.
2. Launches one visible SpaceClaim and imports `<RUN>\10_cad\brake.step`.
3. Checks the import: 28 solids, rotor OD 330 mm, z = -57 to +57 mm, total
   volume 2 647 566.01 mm^3 within 1 %.
4. Identifies all 28 bodies by **measured volume and bounding box** against
   `cad_report.json` (score in units of tolerance; every body must match exactly
   one name with a score of 1.0 or less).
5. Deletes the calliper (unique match) and re-reads the design: 27 bodies, the
   volume drop equal to the calliper volume within 0.5 %, 27-body total
   2 030 484.53 mm^3 within 1 %.
6. Names the 27 bodies (one body named selection each).
7. Tags rotor faces by geometric rule, the PRD section 4 surface groups:
   - `wall-vent` = cheek inner faces (z = +6 and -6) plus every vane face except
     the vane faces at z = +/-6 (those are vane/cheek contacts).
   - `wall-outer` = every other rotor and hat face, except the hat r = 95
     cylinder and the cheek_in r = 95 bore (the hat/cheek_in contact).
   - Pad and backing exposed faces stay untagged; the pad friction faces
     (z = +/-16) and pad backs (z = +/-28) are full contacts and are excluded.
   Gates, **before imprint**, 2 % each: wall-vent 167 037.60, wall-outer
   240 205.78, pad/backing exposed 42 997.28 mm^2.
8. Exports `brake.pmdb` (a FOLDER holding `brake.pmdb`), hashes the inner file,
   writes `tag_report.json`, closes SpaceClaim and records whether it is gone.

No screenshots: images are descoped in the fast profile.

## Procedure

1. **Preconditions** (one bash call, through the `C:\brake-runs` mount):
   `10_cad\brake.step` and `10_cad\cad_report.json` exist and their SHA-256
   equal the hashes in your commission. Refuse to proceed on a mismatch.
2. **Launch** with `submit_ansys_job`, `cwd = <RUN>\20_spaceclaim`, job name
   `g2_sc_prep`, and exactly this script text (fill in the run folder):

   ```python
   import os, runpy
   os.environ["BRAKE_RUN"] = r"C:\brake-runs\<run-id>"
   runpy.run_path(r"<PROJECT>\scripts\stages\spaceclaim_prep.py", run_name="__main__")
   ```

3. **Wait** with `job_status(job_id, wait_seconds=55)`: two or three polls.
   The stdout tail prints one `CHECK` line per gate and a final `STATUS` line.
4. **Judge** `<RUN>\20_spaceclaim\tag_report.json` yourself (read the file, do
   not trust the tail):
   - `status` is `PASS` and every row of `checks[]` has `pass: true`;
   - `body_map` has 28 rows and 28 distinct names; `calliper_match` is present;
   - `named_selections.count` is 29 and the three areas are within 2 %;
   - `pmdb.sha256` equals the SHA-256 of `20_spaceclaim\brake.pmdb\brake.pmdb`
     that you compute yourself;
   - `spaceclaim_left_running` is `false`.
5. **Report** to the lead with the handback JSON (preamble A), listing every
   check as expected / measured / delta / tolerance / PASS|FAIL, plus
   `timing.seconds` and `phase_seconds` from the report.

**Done when** all checks pass, the PMDB inner-file hash is recorded and no
SpaceClaim process is left.

## When it does not pass

| Symptom (from `tag_report.json`) | Owner | What to return |
|---|---|---|
| `status: BLOCKED`, `blocked_by` lists processes | the user | the PIDs; never kill a process you did not start |
| import gate fails (count, OD, z, volume) | solidworks-engineer | the failing row; never repair CAD here |
| `body_map` not unique or a score above 1.0 | solidworks-engineer | the body, its score and runner-up |
| an area outside 2 % | lead (package defect) | the three areas; the face rule may not fit the geometry |
| `error` / `traceback` set | lead (package defect) | the last traceback lines; do not edit the script |
| SpaceClaim left running | you | report it; close it only if `session.pid` is the process you launched |

One relaunch is allowed for an infrastructure failure (SpaceClaim died, the
licence was busy and is now free), with the reason recorded. Never a third
launch. For a deeper diagnosis, `references/api-verified.md` lists the Geometry
API calls that work on ansys-geometry-core 0.15.5, and
`references/failure-modes.md` the traps seen in runs 1 and 2.

## Verification

- `tag_report.json` exists, `status` is `PASS`, and every `checks[]` row passes.
- Your own SHA-256 of `20_spaceclaim\brake.pmdb\brake.pmdb` equals
  `pmdb.sha256`, and the input hashes in `inputs_sha256` equal your commission.
- 29 named selections: 27 bodies, `wall-vent`, `wall-outer`.
- No SpaceClaim process is left running.
- Your handback lists `timing.seconds` and the phase breakdown.
