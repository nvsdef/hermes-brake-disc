# BUILD_STATE.json, timing and final status

Only the lead writes `C:\brake-runs\<run-id>\BUILD_STATE.json`, and only after it
has read the artifact itself. Update it after every gate, never before.

## 1. Fields the lead maintains

```json
{
  "run_id": "FR330V-20261001-0930",
  "prd_revision": "H1.2",
  "status": "running",
  "stage": "gate2",
  "model": "nvidia/nemotron-3-ultra",
  "profile": {"name": "brake", "mode": "interactive"},
  "delegation_budget": {"oneshot_max_children": 0, "max_concurrent_children": 1,
                        "max_iterations": 600, "child_timeout_seconds": 0,
                        "children_used": 2},
  "python_route": "execute_code | C:/solidpilot/.venv/Scripts/python.exe",
  "specialist_sessions": {"G1": {"role": "solidworks-engineer",
                                 "trace_or_session_id": "deleg_72716ea6/task-0.log"}},
  "completed_gates": ["G0", "G1"],
  "measurements": {"G1": {"bodies_pass": 28, "step_manifold_solid_count": 25,
                          "assembly_component_count": 9, "interference_mm3": 0.0}},
  "frozen_hashes": {"brake.step": "<sha256>", "hat.SLDPRT": "<sha256>"},
  "artifacts": {"pmdb_inner_sha256": "<sha256>"},
  "repairs": {"G2": 0},
  "findings": [{"gate": "G1", "text": "...", "owner": "solidworks-engineer"}],
  "timing": {}
}
```

A child's trace handle (for example `deleg_72716ea6/task-0.log`) is **not** a
session id. Record what the runtime returned and label it; leave a field `null`
rather than inventing an identifier. You record the handle; you do not read the
log it points to while the child is running.

## 2. The timing block

Every stage report (`cad_report.json`, `tag_report.json`, `results.json`)
carries `timing`: `started_at`, `finished_at`, `tool_calls` (agent stage) or
`seconds` and `phase_seconds` (stage scripts), and `app_launches` (SolidWorks documents opened, SpaceClaim or
Fluent sessions started). Copy it verbatim into `BUILD_STATE.timing.<gate>` and
add your own fields:

```json
"timing": {
  "run_started_at": "2026-10-01T09:30:05+02:00",
  "preflight": {"started_at": "...", "finished_at": "...", "minutes": 3.1},
  "G0": {"started_at": "...", "finished_at": "...", "minutes": 1.4},
  "G1": {"commissioned_at": "...", "notice_at": "...", "reviewed_at": "...",
         "child": {"started_at": "...", "finished_at": "...",
                   "tool_calls": 212, "app_launches": {"solidworks_documents": 10}},
         "child_minutes": 14.8, "lead_review_minutes": 2.2, "list_checks": 1},
  "G2": {"...": "..."},
  "G3": {"...": "..."},
  "G4": {"started_at": "...", "finished_at": "...", "minutes": 12.0},
  "total_minutes": 0.0,
  "minutes_to_gate2_pass": 31.5
}
```

- `commissioned_at`: the moment your `delegate_task` call returned.
- `notice_at`: the moment the completion notice arrived.
- `list_checks`: how many `delegate_task(action="list")` calls you made while
  the child ran. Expect 0 to 2. More than one per 10 minutes breaks the WAITING
  rule; record it as a finding against the lead.
- If a report has no `timing` block, write `null` with the reason and raise a
  finding against the owner; it is not a gate failure on its own.
- `minutes_to_gate2_pass` is measured from `run_started_at`. The target is 25 to
  35 min. Exceeding it is a finding, not a failure.

The Gate 4 summary prints the per-stage table from this block (stage, owner, minutes,
tool calls, app launches, repairs).

## 3. Final status rules (PRD section 9)

| Status | When |
|---|---|
| `complete` | all 28 bodies passed PRD section 4, the 45 interfaces exist, the Gate 3 energy and heating gates closed (stored/applied 90 to 110 %, applied within 2 % of the closed form), and every requirement has a disposition |
| `complete_with_findings` | the chain reached Gate 4 but at least one of the above is not met |
| `halted` | a gate failed after two repairs, delegation was refused or the budget ran out, an approval was denied, or preflight failed. The final message names the gate and gives expected and measured |

The missing 2D drawing is **descoped** (PRD H1.2 section 8) and never lowers the
status.

Workflow completion is separate from the engineering verdict. A requirement
that is FAIL or NOT ADJUDICABLE still has a disposition, so it does not by
itself stop a run being `complete`; the engineering verdict (how many
requirements PASS) is reported in its own sentence.

A halted run still gets `review.md` and a short report if Gate 0 passed: write
what exists, mark every downstream requirement `OPEN` with the reason "stage not
reached", and never call it complete.
