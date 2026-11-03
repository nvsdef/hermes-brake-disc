# Commission templates - goal and context for every child (PRD H1.2, fast run profile)

There are **three** commissions and one repair template:

| Template | Role | Gate | Stage folder |
|---|---|---|---|
| B1 | solidworks-engineer | Gate 1 CAD | `10_cad` |
| B2 | spaceclaim-engineer | Gate 2 SpaceClaim prep (runs `spaceclaim_prep.py`) | `20_spaceclaim` |
| B3 | fluent-engineer | Gate 3 mesh + heat-up solve (runs `fluent_fast.py`) | `30_fluent` |
| B4 | the owner of the defect | repair of any gate | the owner's folder |

There is no drawing commission in H1.2.

Children receive `AGENTS.md` in their system prompt but **no** SOUL.md, and they
**do not see your conversation**. Whatever is not in the `goal` and `context`
does not exist for them. Copy the template, replace every `<...>` placeholder,
and send it. Do not shorten the context to pointers: the H1 run failed because
commissions carried pointers instead of numbers.

Placeholders used everywhere:

| Placeholder | Value |
|---|---|
| `<PROJECT>` | absolute project path from `BUILD_STATE.json` -> `project_root` |
| `<RUN>` | `C:\brake-runs\<run-id>` |
| `<RUN_ID>` | the run id |
| `<N>` / `<BUDGET>` | this child's number and the total budget (or "unlimited") |
| `<sha:...>` | the SHA-256 you recomputed yourself, lower-case hex |

---

## 0. The call - exact shape

API idiom (the only form used in this package):

```
delegate_task(
    goal="ROLE: solidworks-engineer - Gate 1 CAD build for run FR330V-20261001-0930. ...",
    context="<preamble A + the stage block, as one string>"
)
```

- **Two keyword arguments, `goal` and `context`, both plain strings.** Nothing
  else.
- **Never use `tasks=[...]`** for these stages, not even with one element. Run 1's
  first two calls were rejected with "tasks must be a JSON array of task
  objects", and its readiness check's batch of 3 hit
  `max_concurrent_children = 1`.
- `goal` starts with exactly `ROLE: <role>` (for example
  `ROLE: spaceclaim-engineer`). `AGENTS.md` section 1 uses that prefix to tell the
  child who it is.
- Build the context string in full before the call. If the call is rejected,
  read the error, fix the argument shape, and retry **once**; do not fall back to
  `tasks`.

**After the call** (interactive session): the call returns at once with a
started acknowledgement and a handle. Record the handle and `commissioned_at` in
`BUILD_STATE.json`, tell the user the stage, owner and expected duration, and
**end your turn**. Hermes delivers a completion notice when the child finishes.
At most one `delegate_task(action="list")` every 10 minutes if you must check;
never read `task-*.log` in a loop. In a finite (one-shot) session the call
blocks until the child returns; announce before calling.

**The handback.** The context asks the child to end its final reply with a JSON
block (preamble A, last paragraph). It tells you where to look. It is never the
evidence: you open the artifacts yourself.

---

## A. Common preamble (put this at the top of EVERY context)

```
You are a specialist child in the Hermes brake-disc package. You do not see the
lead's conversation. Everything you need is in this goal and context.

BEFORE ANY OTHER TOOL CALL:
1. Read <PROJECT>\agents\<ROLE>\SOUL.md in full with the file tool.
2. skill_view each skill listed for your role in the AGENTS.md section 1 table:
   <SKILL LIST>. If skill_view cannot find one, read
   <PROJECT>\agents\<ROLE>\skills\<skill>\SKILL.md. Open a skill's references
   only when a step tells you to or a check fails.
3. Read <PROJECT>\specs\PRD.md sections <SECTIONS> and <PROJECT>\specs\handoffs.md
   section <GATE>. The PRD is the only authority for numbers.

Project root: <PROJECT>
Run id:       <RUN_ID>   (prd_revision "H1.2")
Run folder:   <RUN>      (write ONLY inside <RUN>\<STAGE_FOLDER>\; never inside OneDrive)

TOOLS: use the native MCP tools (servers solidpilot and ansys - named
ansys-agent in Claude; names are prefixed mcp_solidpilot_ / mcp_ansys_ or
mcp__solidpilot__ / mcp__ansys-agent__; match on the bare tool name; in Claude
load deferred tool schemas with ToolSearch first). Do not use scripts\mcp_client.py unless this context
says native MCP is unavailable. Pass an explicit absolute path for every file
you write, and cwd=<RUN>\<STAGE_FOLDER> to submit_ansys_job. You cannot call
delegate_task, clarify, memory, send_message or cronjob. If you need a decision,
stop and put the question in open_questions.

PYTHON: never type bare python or python3 in a Windows terminal (it opens a
Windows Store installer). Use the execute_code tool if you have it, otherwise
C:/solidpilot/.venv/Scripts/python.exe, or a Linux sandbox python3 that mounts
C:\brake-runs (hashes, JSON checks, STEP text counts).

APPLICATION SESSIONS: SolidWorks is driven call by call and kept alive.
SpaceClaim and Fluent are driven by ONE run of the stage's vetted script
(scripts/stages/); never write your own replacement, never launch them to test
a call. Count every launch.

HALT RULE: after every body or step, measure and print
expected / measured / delta / tolerance / PASS|FAIL in the same step. On a FAIL,
fix only the failing item and re-measure. Two repairs at most per body or check.
On the third FAIL stop the stage, save what exists, and return status HALTED
with both numbers. Never build on a failed body. Never change a PRD number.
After a timeout, inspect state before retrying; never replay a mutation
blindly. A tool saying COMPLETED is not evidence; a measurement is.

ARTIFACT RULES: every JSON artifact carries run_id, prd_revision ("H1.2"),
producing_role, started_at, finished_at, status (PASS, FAIL, HALTED or BLOCKED)
and inputs_sha256 for each upstream file. Units go in key names (volume_m3,
centroid_mm, area_mm2). Missing values are null with a reason, never 0 and never
PASS.

TIMING: your stage report carries a "timing" block:
  {"started_at": ISO time of your first tool call,
   "finished_at": ISO time when you wrote the report,
   "tool_calls": approximate count of your tool calls,
   "app_launches": {"solidworks_documents": n, "spaceclaim_sessions": n,
                    "fluent_sessions": n}}   (only the keys that apply)

Keep your application visible on screen and framed on the model. Never close or
overwrite a document or process you did not create. A denied approval stops you.

WHEN YOU FINISH (PASS, FAIL or HALTED): close or release only what you opened.
End your final reply with one JSON block:
  {"role": "...", "gate": "...", "status": "PASS|FAIL|HALTED|BLOCKED",
   "artifacts": [{"path": "...", "sha256": "..."}],
   "gate_numbers": [{"check": "...", "expected": ..., "measured": ...,
                     "delta": ..., "tolerance": ..., "pass": true}],
   "failures": ["..."], "repairs_used": n, "open_questions": ["..."],
   "timing": {...}, "processes_left_running": ["..."]}
```

---

## B1. Gate 1 - solidworks-engineer - CAD build

**goal**

```
ROLE: solidworks-engineer - Gate 1 CAD build for run <RUN_ID>. Build the nine
FR-330V parts (28 solid bodies) at true global position in SolidWorks, assemble
all 9 with identity transforms, measure every body against PRD section 4, export
brake.step (28 solids), and write cad_report.json in <RUN>\10_cad\. No drawings.
Child <N> of <BUDGET>.
```

**context** = preamble A with `<ROLE>` = `solidworks-engineer`, `<SKILL LIST>` =
`sw-solidpilot, sw-rotor-build, sw-pads-calliper`, `<SECTIONS>` = `1 to 4`,
`<GATE>` = `Gate 1`, `<STAGE_FOLDER>` = `10_cad`, then:

```
INPUT
- <RUN>\00_lead\case.json  sha256 <sha:case.json>  (for reference only; the
  vane hand and omega sign in it must agree with what you build)

WHAT TO BUILD (PRD sections 2 and 3; mm in the PRD, METRES in SolidPilot:
divide by 1000 once, at the call)
- 9 part files, exact names: cheek_out, cheek_in, vanes, hat, outerpad,
  innerpad, bp_outer, bp_inner, calliper. One part per file. Only 'vanes' has
  more than one body (20). Never merge cheeks, vanes and hat.
- Z is the shaft axis, origin at the vent mid-plane, +Z outboard. Pads centred
  on +X. Angles from +X towards +Y.
- Build every part at its true global position. Assemble brake.SLDASM with ALL
  9 parts at identity transforms. Nothing is moved after it is built.
- Build innerpad and bp_inner independently at their own negative z bands; do
  not copy-and-edit the outboard parts.
- Vanes: region between circles R117 and R123 about C = (20.722, 94.249),
  branch whose angle INCREASES with r (about -2.3 to +2.3 deg at r = 95, +29.8 to
  +33.4 deg at r = 165), trimmed to exact r = 95 and r = 165 cylinders, extruded
  mid-plane z = -6 to +6. Vane k is vane 1 rotated (k - 1) x 18 deg: rotate the
  sketch coordinates, one closed profile per vane. DO NOT use a circular-pattern
  feature (it reports 20 and makes 1).
- Hat: revolve (z, r) polygon (43,35) (43,86) (-6,88) (-6,95) (-16,95) (-16,78)
  (33,74) (33,35) 360 deg about Z, then five dia 14 through-holes on PCD 115 at
  0, 72, 144, 216, 288 deg through z = +33 to +43. Verify z = -16 to +43 by
  measuring; do not trust a reverse flag.
- Calliper: PRD section 3.4 steps 1 to 6 exactly. Windows use the SAME z band as
  the slot, z = -39 to +38.6. Piston bores dia 26 at r = 140, angles -20, 0, +20:
  three from z = +38.6 to +46.6, three from z = -39 to -47. No fillets.

GATE NUMBERS YOU WILL BE CHECKED AGAINST (PRD section 4; tolerance volume 1 %,
centroid 0.1 mm, bbox 0.05 mm)
  body        volume m^3     centroid mm (x, y, z)        z band mm
  cheek_out   5.717699e-4    (0, 0, +11.000)              +6 to +16    x,y -165 to 165
  cheek_in    5.717699e-4    (0, 0, -11.000)              -16 to -6    x,y -165 to 165
  vane each   7.251627e-6    vane_01 (123.842, 40.040, 0) -6 to +6
              vane_01 bbox x 94.922 to 143.121, y -3.850 to 90.942
              vane_k centroid at r = 130.154, angle 17.917 + (k-1) x 18 deg
  vanes (20)  1.450325e-4    (0, 0, 0)
  hat         5.132043e-4    (0, 0, +18.095)              -16 to +43   x,y -95 to 95
              (before holes 5.209012e-4; polygon area 1139.0 mm^2)
  outerpad    7.037168e-5    (134.600, 0, +22.000)        +16 to +28
  innerpad    7.037168e-5    (134.600, 0, -22.000)        -28 to -16
  bp_outer    4.398230e-5    (135.111, 0, +31.000)        +28 to +34
  bp_inner    4.398230e-5    (135.111, 0, -31.000)        -34 to -28
  calliper    6.170815e-4    (146.143, 0.000, +0.369)     -57 to +57
              x 81.245 to 200.000, y -98.418 to 98.418
  rotor (cheeks + vanes + hat) 1.801777e-3 m^3 -> 12.973 kg at 7200 kg/m^3
  Calliper band section areas (to localise a miss): 11 891.10 mm^2 for
  z -57 to -47 and +46.6 to +57; 10 298.32 for -47 to -42 and +42 to +46.6;
  15 050.62 for -42 to -39 and +38.6 to +42; 2 310.76 for -39 to +38.6.
  Interference anywhere: 0 mm^3.
  Clearances: pad stack to slot axial 4.6 mm outboard (34 vs 38.6) and 5.0 mm
  inboard (-34 vs -39); slot height 77.6 vs stack 68 -> +9.6 mm; rotor OD to
  bridge inner radius 13.0 mm (165 vs 178); hat wall to calliper end wall
  11.8 mm (r 86.18 at z = +38.6 vs r = 98).

ASSEMBLY AND STEP GATE (the lead checks these first; run 1 exported a 23-solid
STEP from an assembly missing 5 parts)
- BEFORE export: analyze_assembly must list 9 components (cheek_out, cheek_in,
  vanes, hat, outerpad, innerpad, bp_outer, bp_inner, calliper). If it lists
  fewer, insert the missing parts and re-read. Do not export an 8-component
  assembly.
- AFTER export: count MANIFOLD_SOLID_BREP in brake.step with a text scan: 28.
  Count PRODUCT entities with the pattern "= ?PRODUCT ?\(": 10.
  If either is wrong, fix the assembly and re-export (HALT rule applies).

OUTPUT CONTRACT (specs/handoffs.md Gate 1), all in <RUN>\10_cad\
- cheek_out.SLDPRT, cheek_in.SLDPRT, vanes.SLDPRT, hat.SLDPRT, outerpad.SLDPRT,
  innerpad.SLDPRT, bp_outer.SLDPRT, bp_inner.SLDPRT, calliper.SLDPRT
- brake.SLDASM (all 9 components)
- brake.step (one export, calliper included, 28 manifold solids)
- cad_report.json with:
  bodies[] 28 rows {name, part, volume_m3, expected_volume_m3,
    volume_delta_pct, centroid_mm, expected_centroid_mm, bbox_mm,
    expected_bbox_mm, bbox_method, pass}; vanes as vane_01 to vane_20 in
    angular order. SolidPilot has no bbox call: derive the bbox from measured
    face positions, edge radii and vertices, and name the method.
  assembly {component_count, components[]} read from analyze_assembly BEFORE
    the export
  interference_mm3 and interference_method (pairwise gap and coincident-face
    check; SpaceClaim's Gate 2 contact graph is the independent cross-check)
  clearances_mm {each PRD section 4 clearance, measured}
  requirements {PKG-01..05, MAS-01, GEO-01..04, GEO-06, PAD-01..05: measured
    value, unit, how measured}
  vane_hand {theta_at_r95_deg, theta_at_r165_deg, rotation_viewed_from_plus_z}
  step {path, sha256, manifold_solid_count, product_count, ap_schema}
  native_hashes {file name: sha256} for all 9 SLDPRT and the SLDASM
  timing (preamble A)

DO NOT
- make any drawing, drawing view, rotor_only assembly, render or image (H1.2
  has no drawings and no images)
- re-open brake.step in SolidWorks (no re-import: SpaceClaim re-measures all 28
  bodies at Gate 2)
- build cross-drilled holes (GEO-05 is deferred) or any second/display model
- trust volume alone: check centroid and bbox for every body
- use submit_feature_graph for placement (it ignores every placement key while
  reporting COMPLETED)
- write anything outside <RUN>\10_cad\
```

---

## B2. Gate 2 - spaceclaim-engineer - SpaceClaim prep (stage script)

**goal**

```
ROLE: spaceclaim-engineer - Gate 2 for run <RUN_ID>. Run the vetted stage script
scripts/stages/spaceclaim_prep.py once on the frozen brake.step (import, identify
28 bodies, delete the calliper, name 27 bodies plus wall-vent and wall-outer,
export brake.pmdb), then judge <RUN>\20_spaceclaim\tag_report.json against the
gates. Child <N> of <BUDGET>.
```

**context** = preamble A with `<ROLE>` = `spaceclaim-engineer`, `<SKILL LIST>` =
`sc-fast-prep`, `<SECTIONS>` = `2 to 4`, `<GATE>` = `Gate 2`, `<STAGE_FOLDER>` =
`20_spaceclaim`, then:

```
INPUTS (frozen at Gate 1; refuse to proceed if a hash differs)
- <RUN>\10_cad\brake.step        sha256 <sha:brake.step>
    (lead-verified: 28 MANIFOLD_SOLID_BREP, 10 PRODUCT, assembly 9 components)
- <RUN>\10_cad\cad_report.json   sha256 <sha:cad_report.json>

LAUNCH (once) with submit_ansys_job, cwd=<RUN>\20_spaceclaim, job_name g2_sc_prep,
script_text exactly:
  import os, runpy
  os.environ["BRAKE_RUN"] = r"<RUN>"
  runpy.run_path(r"<PROJECT>\scripts\stages\spaceclaim_prep.py", run_name="__main__")
Poll job_status(job_id, wait_seconds=55). Expected about 60 to 120 s.
Do not edit, copy or replace the script. If it reports BLOCKED, return the PIDs.

JUDGE <RUN>\20_spaceclaim\tag_report.json yourself (not the log): status PASS,
every checks[] row passes, inputs_sha256 equal the two hashes above, 29 named
selections, before-imprint areas within 2 % (wall-vent 167 037.60, wall-outer
240 205.78, pad/backing 42 997.28 mm^2), your own SHA-256 of
brake.pmdb\brake.pmdb equals pmdb.sha256, spaceclaim_left_running false.
Print every check as expected / measured / delta / tolerance / PASS|FAIL.
```

---

## B3. Gate 3 - fluent-engineer - mesh + heat-up solve (stage script)

**goal**

```
ROLE: fluent-engineer - Gate 3 for run <RUN_ID>. Run the vetted stage script
scripts/stages/fluent_fast.py once on the frozen brake.pmdb (coarse mesh, mesh
gate, PRD setup from case.json, first 1.0 s of the stop), then judge
<RUN>\30_fluent\results.json. Fluent stays open with the temperature contour on
PASS. Child <N> of <BUDGET>.
```

**context** = preamble A with `<ROLE>` = `fluent-engineer`, `<SKILL LIST>` =
`fl-fast-run`, `<SECTIONS>` = `4 to 6A`, `<GATE>` = `Gate 3`, `<STAGE_FOLDER>` =
`30_fluent`, then:

```
INPUTS (frozen; refuse if a hash differs)
- <RUN>\20_spaceclaim\brake.pmdb\brake.pmdb   sha256 <sha:pmdb inner file>
- <RUN>\00_lead\case.json                     sha256 <sha:case.json>

LAUNCH (once) with submit_ansys_job, cwd=<RUN>\30_fluent, job_name g3_fluent_fast,
script_text exactly:
  import os, runpy
  os.environ["BRAKE_RUN"] = r"<RUN>"
  runpy.run_path(r"<PROJECT>\scripts\stages\fluent_fast.py", run_name="__main__")
(Fast profile defaults, PRD section 6A. Add FAST_* overrides only if this
commission lists them: <none>.)
Poll job_status(job_id, wait_seconds=55). Expected about 2 to 3 min. A
"ValueError: invalid literal for int()" traceback in stderr is a harmless
pyfluent event-thread error. Do not edit, copy or replace the script.

JUDGE <RUN>\30_fluent\results.json yourself: status PASS, every checks[] row
passes (27 solid / 0 fluid zones, 45 coupled pairs, friction areas 5 864.31 mm^2
within 2 %, meshed volume 2 030 484.53 mm^3 within 2 %, materials and grey-iron
layer read back, applied energy within 2 % of the closed form, stored/applied
90 to 110 %, stored energy and bulk maxima rising every window), inputs_sha256
equal the hashes above, history ends at settings.end_time_s, live_contour
displayed. Report the summary block (peak and final friction-face temperatures,
applied and stored energy). This is a heating demonstration, not a THM verdict.
```

---

## B4. Repair commission (any gate)

A repair is a **new child**; it knows nothing about the first attempt. Give it
the failing numbers and the exact scope. Use the owner's preamble A and skill
list from the table at the top of this page.

**goal**

```
ROLE: <owner-role> - REPAIR <k> of 2 for Gate <G> in run <RUN_ID>. Fix only
<the failing body / check>. Everything that passed is frozen. Child <N> of
<BUDGET>.
```

**context** = preamble A for the owner role, then:

```
WHAT FAILED (read by the lead from <artifact>, key <json key>)
  check: <e.g. step.manifold_solid_count>
  expected <PRD value>, measured <value>, delta <value>, tolerance <value>
  lead's diagnosis (a hypothesis, verify it): <e.g. analyze_assembly lists 4
  components; outerpad, innerpad, bp_outer, bp_inner and calliper were never
  inserted>

STATE YOU INHERIT
- A previous child worked in <RUN>\<STAGE_FOLDER>\. Inventory the folder and the
  application state (open documents, running session) before changing anything.
- The failed report was renamed <name>.attempt<k>.json by the lead; keep it.

SCOPE
- Repair only <part or step>. Do not touch <list of passed items>; their hashes
  are <hashes> and must be unchanged when you finish (check them).
- After the repair, RE-MEASURE everything the gate checks (not only the repaired
  item) and RE-EXPORT <brake.step / brake.pmdb / mesh>.
- Rewrite <cad_report.json> (Gates 2 and 3 are re-run by their stage script, which rewrites its own report)
  completely, with a "repair" block {k, failing_check, root_cause, change_made}
  and a fresh timing block.
- HALT rule applies inside this commission (two tries). If still failing,
  return HALTED with both numbers.
```

After a Gate 1 repair every downstream frozen hash is void: Gate 2 onward is
re-commissioned with the new STEP hash. Say so to the user.
