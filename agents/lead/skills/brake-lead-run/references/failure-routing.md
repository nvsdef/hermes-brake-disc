# Failure routing - when a gate fails or a child does not return

A failure is routed to the agent that **owns the defect**, with the measurement
that proves it: expected and measured, both numbers, the artifact and the JSON
key. The lead never repairs, never asks a downstream agent to work around an
upstream miss, and never does a specialist's work itself.

**Run 1 lesson.** After a Gate 2 area failure and a context compaction, the lead
wrote a 741-line `00_lead\spaceclaim_gate2_fixed.py` and called `mcp__ansys__`
tools itself. That is the failure this page exists to prevent. The fix for a
failing SpaceClaim gate is a B4 repair commission to the spaceclaim-engineer
carrying the failing areas, never a script from the lead.

## 1. Who owns what

| Symptom (where you saw it) | Owner | Why |
|---|---|---|
| body volume, centroid or bbox miss (Gate 1) | solidworks-engineer | CAD geometry |
| `assembly.component_count` not 9, or STEP solids not 28 (Gate 1) | solidworks-engineer | CAD assembly and export |
| interference or clearance miss (Gate 1) | solidworks-engineer | CAD assembly |
| fewer than 28 bodies imported, import scale wrong (Gate 2) | solidworks-engineer if the STEP text count or `cad_report.json` shows it; otherwise spaceclaim-engineer | the STEP is the evidence: recount it yourself |
| calliper not unique, 28 bodies after delete (Gate 2) | solidworks-engineer if the signatures in `cad_report.json` are wrong; else lead (stage-script defect) | the script matches on measured signatures |
| named selection missing or an area off (Gate 2) | lead: stage-script defect in `spaceclaim_prep.py` | the face rule is in the script; halt and report, never patch mid-run |
| `error` / `traceback` in `tag_report.json` or `results.json` | lead: stage-script defect | halt with the traceback; fix the package after the run |
| `status: BLOCKED` (an Ansys session already running) | the user | ask them to close it; never kill it |
| PMDB hash mismatch (Gate 2) | spaceclaim-engineer, unless you hashed the folder instead of `brake.pmdb\brake.pmdb` | check your own path first |
| sliver or zero-area face found by SpaceClaim or the mesher | solidworks-engineer | the face exists in the CAD |
| contact count below 45 because a contact does not touch in CAD | solidworks-engineer | abutment is a CAD property |
| contact count below 45 because shared topology was not applied | fluent-engineer (mesh) or spaceclaim-engineer (a contact face was tagged) | read which |
| mesh gate failed: zones, pairs, areas, volume (Gate 3) | spaceclaim-engineer (tagging) or solidworks-engineer (geometry); the script itself if neither | read which |
| readback wrong, energy or heating gate failed (Gate 3) | lead: stage-script defect in `fluent_fast.py` | halt with the history rows |
| `case.json` arithmetic wrong (found at any gate) | lead | Gate 0 is yours: fix it, re-hash, and re-commission Gate 3 |
| frozen CAD hash changed after Gate 1 | whoever last opened the files | the run halts unless the owner restores the Gate 1 files |
| missing `timing` block | the stage owner | a finding, not a gate failure |

## 2. The repair loop

```
gate fails
  -> print the failing rows (expected / measured / delta / tolerance)
  -> write a finding in BUILD_STATE.json with owner, evidence file and key
  -> rename the failed report to <name>.attempt<k>.json
  -> repairs_used[gate] < 2 and budget left?
       yes -> commission the owner with template B4, repair k of 2
              -> end your turn and wait for the completion notice
              -> review again with the same checklist
       no  -> HALT
```

- **Two repair commissions per gate, at most**, on top of the two tries the
  child makes internally under the HALT rule.
- **A repair of an upstream stage invalidates every downstream freeze.** A Gate 1
  repair produces a new `brake.step` hash, so Gate 2 and Gate 3 must be
  re-commissioned. If the budget cannot cover the repair plus the downstream
  re-runs, halt instead and say so.
- **Your diagnosis is a hypothesis.** Put it in the repair context labelled as
  such, with the numbers. Do not write code for the child.

## 3. Halting

1. Set `BUILD_STATE.json` -> `status: "halted"`, `stage: "<gate>"`, and a
   `halt` block: `{gate, check, expected, measured, delta, tolerance, owner,
   repairs_used, evidence_file, json_key}`.
2. Tell the user, in one message:

   ```
   RUN HALTED at Gate 1 (CAD).
   check: step.manifold_solid_count
   expected 28, measured 23, delta -5, tolerance 0
   owner: solidworks-engineer, repairs used 2 of 2
   evidence: C:\brake-runs\FR330V-20261001-0930\10_cad\cad_report.json -> step.manifold_solid_count
   Artifacts kept. No downstream stage was started.
   ```

3. If Gate 0 passed, still write `gate_log.md` and the requirement dispositions
   in `BUILD_STATE.json`: rows with evidence get their disposition, the rest are
   OPEN with "stage not reached", deferred items stay DEFERRED. No PDF.

## 4. Delegation failures

| What happened | What you do |
|---|---|
| `delegate_task` rejected for argument shape (for example "tasks must be a JSON array of task objects") | you passed `tasks` or a non-string. Re-issue once as `delegate_task(goal="ROLE: ...", context="...")`. Never switch to `tasks=[...]` |
| rejected by `max_concurrent_children` | a child is still running. Wait for its completion notice; never start a second child |
| refused: budget exhausted ("Delegation budget for this one-shot run is exhausted") | HALT. Do **not** follow the runtime's suggestion to do the remaining work yourself. Report the budget value and the gate reached |
| child returns an error before reading its role | re-commission once with the same template if budget allows; if it fails again, HALT |
| child returns HALTED or FAIL with numbers | normal repair loop above |
| child returns BLOCKED (licence, approval, application not ready) | HALT and bring the blocker to the user; a missing approval is not yours to grant |
| child returns PASS but the artifact is missing or disagrees | FAIL of the gate; the artifact is the evidence |
| child timed out or hit `max_iterations` | inspect first: list the stage folder, hash what exists, check `Get-Process`. Do not call any Ansys or SolidPilot tool. Then commission a B4 repair whose context says a previous child stopped mid-stage |
| child left an application process running | ask the user to close it, or commission the owner to close its own session; never kill it yourself |
| you notice you are about to call an `mcp__solidpilot__` or `mcp__ansys__` tool, or write a stage script | stop. Re-read `AGENTS.md` sections 1 and 2 and `agents/lead/SOUL.md`. Commission the owner instead |

## 5. Waiting, not polling

In an interactive session `delegate_task` returns at once and the child runs in
the background. Hermes posts a completion notice when it finishes. Between the
two you do nothing: tell the user the stage and expected duration, then end your
turn. A CAD build takes about 12 to 18 min, geometry prep 8 to 12 min, and the
Fluent commission longer.

- At most one `delegate_task(action="list")` every 10 minutes, and only if the
  expected duration has clearly passed. Record each in
  `BUILD_STATE.timing.<gate>.list_checks`.
- Never read `task-*.log` in a loop, never list the stage folder repeatedly, and
  never query an application on the child's behalf.
- If the expected duration is exceeded by more than 2 times with no notice, do
  one `list` call. If the child is still running, tell the user and keep waiting.
  If it is gone with no notice, treat it as a timeout (section 4).

In a finite (one-shot) session `delegate_task` blocks until the child returns;
announce the expected duration before the call. Never start a second child while
one is running.
