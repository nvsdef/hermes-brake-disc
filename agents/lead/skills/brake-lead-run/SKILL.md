---
name: brake-lead-run
description: "Lead checklist: preflight, delegate, gate, summarize."
version: 2.0.0
author: "sdefibaugh"
license: Apache-2.0
platforms: [windows]
metadata:
  hermes:
    tags: [brake, lead, orchestration, delegation]
---

# brake-lead-run - the lead's checklist (PRD H1.2, fast run profile)

You are the lead. You commission three specialists, one at a time, and you judge
their artifacts. You never do their work. Tick the boxes in order. Open a
reference only when a box tells you to.

## 0. Rules that hold for the whole run (read these first, and again after any compaction)

1. **You call no `mcp__solidpilot__*` and no `mcp__ansys__*` tool.** You write no
   CAD, tagging, meshing or solver code, and you never launch a stage script:
   the specialist does. You never load an `sw-`, `sc-` or `fl-` skill.
2. **One child at a time, exact single-task form.** Every commission is:

   ```
   delegate_task(goal="ROLE: <role> - <one-line task>", context="<full context block>")
   ```

   Two arguments, both plain strings. **Never use `tasks=[...]`** for these
   stages. Run 1 lost its first two calls to "tasks must be a JSON array of task
   objects", and a batch of 3 hit `max_concurrent_children = 1`.
3. **WAITING rule.** After `delegate_task` returns its "started" acknowledgement,
   tell the user what is running and **end your turn**. The completion notice is
   your cue. At most one `delegate_task(action="list")` every 10 minutes; never
   read task logs in a loop or poll the run folder.
4. **Failures go to the owner with both numbers** (`references/failure-routing.md`).
   A stage-script error is a package defect: halt and report it, do not patch.
5. **Python:** never type bare `python` or `python3` in a Windows terminal. Use
   `execute_code`, `C:/solidpilot/.venv/Scripts/python.exe`, or a Linux sandbox
   `python3` that mounts `C:\brake-runs`. Gate-check scripts only read, hash and
   compare, and live in `00_lead\checks\`.
6. **After a compaction:** re-read `AGENTS.md` sections 1 and 2,
   `agents/lead/SOUL.md` and this SKILL.md, then `BUILD_STATE.json`.

## 1. Run shape and time budget (measured 2026-11-02)

| Gate | Who | How | Folder | Target |
|---|---|---|---|---|
| Preflight + G0 | lead | `brake-duty-cycle`, one calculation | `00_lead` | 1 to 2 min |
| G1 CAD, build and assemble once | solidworks-engineer | SolidPilot MCP, agentic | `10_cad` | 8 to 13 min |
| G2 SpaceClaim prep | spaceclaim-engineer | runs `scripts/stages/spaceclaim_prep.py` | `20_spaceclaim` | about 1 min app time |
| G3 mesh + heat-up solve | fluent-engineer | runs `scripts/stages/fluent_fast.py` | `30_fluent` | about 2 min app time |
| G4 gate summary | lead | `BUILD_STATE.json`, `gate_log.md`, chat | `00_lead` | 1 to 2 min |

No drawings, no images, no PDF report (PRD section 8). Each lead gate review is
one check script and one message.

## 2. Checklist

**Preflight** (`references/preflight.md`)
- [ ] Run folder `C:\brake-runs\FR330V-<yyyymmdd>-<hhmm>\` with `00_lead`,
      `00_lead\checks`, `10_cad`, `20_spaceclaim`, `30_fluent`.
- [ ] `BUILD_STATE.json` from the template, `prd_revision` "H1.2", profile
      "fast", spec hashes, `project_root`.
- [ ] Delegation available; SolidPilot and Ansys tools visible (look, do not call).
- [ ] No SpaceClaim or Fluent session running (a Fluent window left open by the
      previous fast run holds the Student licence): if one is, ask the user to
      close it. Never kill it yourself.
- [ ] Print the preflight table.

**Gate 0 - duty cycle**
- [ ] Load `brake-duty-cycle`, compute with a tool, write `00_lead\case.json`.
- [ ] ts 3.54068 s, E 243 055.6 J, omega0 -84.1751 rad/s, each within 0.1 %.
- [ ] Hash `case.json`; append `"G0"`.

**Gate 1 - CAD** (template B1)
- [ ] Announce; delegate; end turn.
- [ ] On the notice: open `10_cad\cad_report.json` yourself and run the Gate 1
      checklist (`references/gate-checklists.md`).
- [ ] **`assembly.component_count` == 9 and your own `MANIFOLD_SOLID_BREP` text
      count of `brake.step` == 28** (and 10 PRODUCT).
- [ ] 28 bodies within tolerance, interference 0, vane sweep +1. Recompute and
      freeze the 10 native hashes and the STEP hash.

**Gate 2 - SpaceClaim prep** (template B2)
- [ ] Announce; delegate; end turn.
- [ ] Read `20_spaceclaim\tag_report.json`: `status` PASS, every `checks[]` row
      passes, `inputs_sha256` equals your frozen STEP and cad_report hashes.
- [ ] Recompute the SHA-256 of `brake.pmdb\brake.pmdb`; it equals `pmdb.sha256`.
      Freeze it. `spaceclaim_left_running` is false.

**Gate 3 - Fluent mesh + heat-up** (template B3)
- [ ] Announce; delegate; end turn.
- [ ] Read `30_fluent\results.json`: `status` PASS, every `checks[]` row
      passes (zones 27/0, 45 coupled pairs, areas, volume, materials, energy,
      heating), `inputs_sha256` equals the frozen PMDB and case hashes,
      `history` ends at `settings.end_time_s`.
- [ ] Note that Fluent is open with the contour (that is intended).

**Gate 4 - gate summary**
- [ ] Write `00_lead\gate_log.md` and the final `BUILD_STATE.json`: every gate
      table, the timing table, the Gate 3 `summary`, and the requirement
      dispositions from `specs/handoffs.md` Gate 4 (THM-01 to 04
      `NOT RUN (fast profile)`).
- [ ] Tell the user: status word, total time, the stage timing table, the peak
      and final friction-face temperatures and the energy balance, and that the
      Fluent window shows the contour.

## 3. What to print at each gate

`expected / measured / delta / tolerance / PASS|FAIL` for every checked number,
then one line: `GATE n: PASS` or `GATE n: FAIL -> owner, repair k of 2`. Then
the stage timing row.

## 4. References

| Reference | Open it when |
|---|---|
| `references/preflight.md` | at the start, before Gate 0 |
| `references/commission-templates.md` | before every `delegate_task` call |
| `references/gate-checklists.md` | on every completion notice |
| `references/failure-routing.md` | a gate fails, a child errors, times out or is refused |
| `references/build-state.md` | writing `BUILD_STATE.json`, timing, final status rules |

## Verification

Before you tell the user the run is finished, check all of these yourself:

1. `BUILD_STATE.json` lists every gate you passed, with its numbers and its
   timing, and the final status follows `references/build-state.md`.
2. Every `delegate_task` call used the two-argument single-task form, each goal
   began `ROLE: `, and the number of calls equals `children_used`.
3. You made **zero** SolidPilot or Ansys tool calls, loaded no `sw-`, `sc-` or
   `fl-` skill, and launched no stage script.
4. Gate 1 recorded `assembly.component_count` 9 and your own STEP count of 28.
5. The frozen CAD, STEP and PMDB hashes recomputed now equal `BUILD_STATE.json`.
6. Every PRD section 7 ID and DV item has a disposition in `BUILD_STATE.json`.
