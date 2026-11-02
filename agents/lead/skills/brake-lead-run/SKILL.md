---
name: brake-lead-run
description: "Lead checklist: preflight, delegate, wait, gate, report."
version: 1.2.0
author: "sdefibaugh"
license: Apache-2.0
platforms: [windows]
metadata:
  hermes:
    tags: [brake, lead, orchestration, delegation]
---

# brake-lead-run - the lead's checklist (PRD H1.2)

You are the lead. You commission three specialists, one at a time, and you judge
their artifacts. You never do their work. Tick the boxes in order. Open a
reference only when a box tells you to.

## 0. Rules that hold for the whole run (read these first, and again after any compaction)

1. **You call no `mcp__solidpilot__*` and no `mcp__ansys__*` tool.** You write no
   CAD, tagging, meshing, solver or post-processing script. You never load an
   `sw-`, `sc-` or `fl-` skill. Seeing a tool is not permission to call it.
2. **One child at a time, exact single-task form.** Every commission is:

   ```
   delegate_task(goal="ROLE: <role> - <one-line task>", context="<full context block>")
   ```

   Two arguments, both plain strings. **Never use `tasks=[...]`** for these
   stages. Run 1 lost its first two calls to "tasks must be a JSON array of task
   objects", and a batch of 3 hit `max_concurrent_children = 1`.
3. **WAITING rule.** After `delegate_task` returns its "started" acknowledgement,
   tell the user what is running and **end your turn**. Hermes runs the child in
   the background and delivers a completion notice into your conversation when
   it finishes. That notice is your cue to act. If you truly must check, make at
   most **one** `delegate_task(action="list")` call every **10 minutes**. Never
   read `task-*.log` files in a loop, never poll the run folder, never "just
   check" an application. Run 1 burned dozens of full model turns this way.
4. **Failures go to the owner with both numbers** (`references/failure-routing.md`).
   The lead never repairs.
5. **Python:** never type bare `python` or `python3` (it opens a Windows Store
   installer). Use `execute_code` if you have it, otherwise
   `C:/solidpilot/.venv/Scripts/python.exe`. Gate-check scripts may only read,
   hash and compare, and live in `00_lead\checks\`.
6. **After a compaction** (a summary replaces earlier turns, or you are unsure
   what you are doing): re-read `AGENTS.md` sections 1 and 2,
   `agents/lead/SOUL.md` and this SKILL.md, then read `BUILD_STATE.json` to find
   the stage. Resume as the lead. If a stage is failing, re-commission its owner.

## 1. Run shape and time budget

| Gate | Who | Output folder | Target wall time |
|---|---|---|---|
| Preflight + G0 | lead | `00_lead` | 5 min |
| G1 CAD | solidworks-engineer | `10_cad` | 12 to 18 min |
| G2 geometry prep + CAD screenshots | spaceclaim-engineer | `20_spaceclaim` | 8 to 12 min |
| G3 mesh + setup + solve + post (one commission) | fluent-engineer | `30_fluent` | record it |
| G4 review + report | lead | `50_report` | 15 min |

Target: **Gate 2 passed within 25 to 35 min** of the user's prompt (run 1 took
about 2.5 h). Each lead gate review should take one check script and one
message. Three children is the plan; each repair adds one.

## 2. Checklist

**Preflight** (`references/preflight.md`)
- [ ] Run folder `C:\brake-runs\FR330V-<yyyymmdd>-<hhmm>\` with `00_lead`,
      `00_lead\checks`, `10_cad`, `20_spaceclaim`, `30_fluent`,
      `30_fluent\histories`, `50_report`. No `40_drawing`.
- [ ] `BUILD_STATE.json` from the template, `prd_revision` "H1.2", spec hashes.
- [ ] `delegate_task` is in **your** tool list (toolset `delegation`). If not: STOP.
- [ ] SolidPilot and Ansys tools visible (look, do not call).
- [ ] Profile delegation settings read with `-p <profile>`; interactive or finite.
- [ ] No stray Ansys processes. No drawing stage in the plan.
- [ ] Print the preflight table. `timing.preflight` recorded.

**Gate 0 - duty cycle**
- [ ] Load `brake-duty-cycle`, compute with a tool, write `00_lead\case.json`.
- [ ] ts 3.54068 s, E 243 055.6 J, omega0 -84.1751 rad/s, each within 0.1 %.
- [ ] Hash `case.json`; append `"G0"`.

**Gate 1 - CAD**
- [ ] Fill template B1 (`references/commission-templates.md`); announce; delegate; end turn.
- [ ] On the completion notice: open `10_cad\cad_report.json` yourself and run
      the Gate 1 checklist (`references/gate-checklists.md`).
- [ ] **`step.manifold_solid_count` == 28 and `assembly.component_count` == 9**,
      plus your own `MANIFOLD_SOLID_BREP` text count == 28. Run 1 passed a
      23-solid STEP here; SpaceClaim caught it one stage late.
- [ ] 28 bodies within tolerance, interference 0, hashes recomputed. Freeze 11 hashes.
- [ ] Copy `timing` into `BUILD_STATE.timing.G1`.

**Gate 2 - geometry prep and CAD visuals**
- [ ] Template B2; announce; delegate; end turn.
- [ ] 27 bodies, unique calliper match, 45 contacts, **before-imprint** areas
      within 2 % (167 037.60 / 240 205.78 / 42 997.28 mm^2).
- [ ] `brake.pmdb\brake.pmdb` inner-file hash equals `pmdb_sha256`.
- [ ] `cad_iso.png`, `cad_section_9deg.png`, `named_selections.png` exist,
      are larger than 20 kB, and show a framed model (vision check).
- [ ] No SpaceClaim process left running. Copy `timing`.

**Gate 3 - Fluent, one commission**
- [ ] Template B3; announce; delegate; end turn.
- [ ] Mesh gate rows (27 solid / 0 fluid, 45 pairs, quality, after-imprint
      areas) and energy rows (applied within 2 %, ratio 90 to 110 %, full ts).
- [ ] Mesh images and contours exist. No Fluent process left. Copy `timing`.

**Gate 4 - review and report**
- [ ] Load `brake-design-review`: `review.json`, `review.md` (37 rows, drawing
      listed as descoped, timing table).
- [ ] Load `brake-report`: `report.pdf`, `manifest.json`.
- [ ] Final status and `timing.total`; tell the user.

## 3. What to print at each gate

`expected / measured / delta / tolerance / PASS|FAIL` for every checked number,
then one line: `GATE n: PASS` or `GATE n: FAIL -> owner, repair k of 2`. Then
the stage timing row: `started_at`, `finished_at`, minutes, `tool_calls`,
`app_launches`.

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
   `timing` block, and the final status follows `references/build-state.md`.
2. Every `delegate_task` call used the two-argument single-task form, each goal
   began `ROLE: `, and the number of calls equals `children_used`.
3. You made **zero** SolidPilot or Ansys tool calls, loaded no `sw-`, `sc-` or
   `fl-` skill, and wrote no stage script (scan your own tool history and
   `00_lead\`).
4. You made no more than one `delegate_task(action="list")` per 10 minutes of
   child run time, and read no task log in a loop.
5. Gate 1 recorded `step.manifold_solid_count` 28 and
   `assembly.component_count` 9 as read by you.
6. The 11 frozen CAD hashes and the PMDB inner-file hash recomputed now equal
   the values in `BUILD_STATE.json`.
7. Every PRD section 7 ID and DV item has a row in `review.json`, and the report
   lists the drawing as descoped.
