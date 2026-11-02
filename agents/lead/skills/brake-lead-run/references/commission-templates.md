# Commission templates - goal and context for every child (PRD H1.2)

There are **three** commissions and one repair template:

| Template | Role | Gate | Stage folder |
|---|---|---|---|
| B1 | solidworks-engineer | Gate 1 CAD | `10_cad` |
| B2 | spaceclaim-engineer | Gate 2 geometry prep + CAD screenshots | `20_spaceclaim` |
| B3 | fluent-engineer | Gate 3 mesh + setup + solve + post (one commission) | `30_fluent` |
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

TOOLS: use the native MCP tools (servers solidpilot and ansys; names are
prefixed mcp_solidpilot_ / mcp_ansys_ or mcp__solidpilot__ / mcp__ansys__; match
on the bare tool name). Do not use scripts\mcp_client.py unless this context
says native MCP is unavailable. Pass an explicit absolute path for every file
you write, and cwd=<RUN>\<STAGE_FOLDER> to submit_ansys_job. You cannot call
delegate_task, clarify, memory, send_message or cronjob. If you need a decision,
stop and put the question in open_questions.

PYTHON: never type bare python or python3 in the terminal (it opens a Windows
Store installer). Use the execute_code tool if you have it, otherwise
C:/solidpilot/.venv/Scripts/python.exe.

APPLICATION SESSIONS: start your application once for the stage and keep it
alive; connect to it with short scripts or calls. Never launch SpaceClaim or
Fluent just to test one call. Count every launch.

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
- make any drawing, drawing view, rotor_only assembly or render (H1.2 has no
  2D drawings; CAD screenshots are taken in SpaceClaim at Gate 2)
- build cross-drilled holes (GEO-05 is deferred) or any second/display model
- trust volume alone: check centroid and bbox for every body
- use submit_feature_graph for placement (it ignores every placement key while
  reporting COMPLETED)
- write anything outside <RUN>\10_cad\
```

---

## B2. Gate 2 - spaceclaim-engineer - geometry prep and CAD screenshots

**goal**

```
ROLE: spaceclaim-engineer - Gate 2 geometry preparation for run <RUN_ID>. In ONE
SpaceClaim session: import the frozen brake.step, identify all 28 bodies by
measured signature, capture cad_iso.png and cad_section_9deg.png, delete the
calliper, name 27 bodies plus wall-vent and wall-outer, capture
named_selections.png, export brake.pmdb and write tag_report.json to
<RUN>\20_spaceclaim\. Child <N> of <BUDGET>.
```

**context** = preamble A with `<ROLE>` = `spaceclaim-engineer`, `<SKILL LIST>` =
`sc-geometry-tagging`, `<SECTIONS>` = `2 to 4 and 6`, `<GATE>` = `Gate 2`,
`<STAGE_FOLDER>` = `20_spaceclaim`, then:

```
INPUTS (frozen at Gate 1; refuse to proceed if a hash differs)
- <RUN>\10_cad\brake.step        sha256 <sha:brake.step>
    (lead-verified: 28 MANIFOLD_SOLID_BREP, assembly 9 components)
- <RUN>\10_cad\cad_report.json   sha256 <sha:cad_report.json>
Use the MEASURED signatures in cad_report.json bodies[] (volume, centroid, bbox)
to identify bodies. The calliper signature to match is the measured one:
  calliper volume <cad_report calliper volume_m3> m^3, centroid <...> mm
  (PRD value 6.170815e-4 m^3, centroid (146.143, 0.000, +0.369) mm, bbox x max
  200.0 mm). Never use the predecessor's 6.113e-4 m^3 signature.

SESSION: one SpaceClaim launch job (submit_ansys_job, cwd=<RUN>\20_spaceclaim)
kept alive for the whole stage; short scripts connect to it. Record the PID and
the number of connect calls in tag_report.json -> session. Close it when done.

ORDER OF WORK
1. Import; import_scale_check; body_map (28).
2. SCREENSHOTS BEFORE DELETION, framed on the model:
   cad_iso.png - isometric of the full assembly INCLUDING the calliper.
   cad_section_9deg.png - section through the vent inlet on a plane at 9 deg
   (mid-passage between vanes): GEO-06 evidence, showing the hat web on the
   inboard cheek and the open inlet of about 7 mm. A 0 deg cut passes through
   vane roots and makes the inlet look blocked.
3. calliper_match (unique), delete, after_delete (27, re-read design).
4. Named selections, areas, contact_graph.
5. named_selections.png - wall-vent and wall-outer in distinct colours, framed.
6. Export brake.pmdb, hash, write tag_report.json.

GATE NUMBERS YOU WILL BE CHECKED AGAINST
- import_scale_check: rotor OD 330 mm (r = 165), z extents -57 to +57 mm, total
  volume of 28 bodies 2 647 566.01 mm^3, rotor 23 bodies 1.801777e-3 m^3.
  Tolerance 1 %. Do NOT scale the import: if 25.4x or 1000x off, stop.
- body_map: 28 bodies, each matched to exactly one PRD name by measured volume
  and centroid. If fewer than 28 arrive, STOP and return the count: the owner
  is solidworks-engineer. Do not repair CAD.
- calliper_match: exactly one body matches (volume AND centroid z = +0.369 AND
  bbox x max = 200.0); report the runner-up and its distance.
- after_delete: 27 bodies on a RE-READ design. Volume drop equals the calliper
  volume within 0.5 %. Expected 27-body total 2 030 484.53 mm^3.
  set_suppressed() is not deletion.
- named_selections: 27 body selections named exactly cheek_out, cheek_in, hat,
  vane_01 to vane_20 (same angular order as cad_report.json), outerpad, innerpad,
  bp_outer, bp_inner; plus wall-vent and wall-outer.
  wall-vent = 2 cheek inner faces (z = +6 and z = -6) + 20 vane flanks and
  radial ends. BEFORE-IMPRINT area 167 037.60 mm^2 +/- 2 %.
  wall-outer = every other exposed rotor and hat face, including the hat step
  face z = -6, r = 88 to 95: 240 205.78 mm^2 +/- 2 % before imprint.
  Pad and backing exposed faces (no named selection): 42 997.28 mm^2 +/- 2 %.
  Also report the predicted after-imprint values for Gate 3: wall-vent
  142 865.51, wall-outer 228 477.17, pad/backing 31 268.67 mm^2.
- NEVER tag a contact face (pad/cheek, pad/backing, vane/cheek, hat/cheek_in):
  a named selection turns a coupled interface into an uncoupled wall.
- contact_graph: 45 contacts, each with measured area:
    outerpad/cheek_out, innerpad/cheek_in           5 864.31 mm^2 each
    outerpad/bp_outer, innerpad/bp_inner            5 864.31 mm^2 each
    vane_k/cheek_out and vane_k/cheek_in (40)       604.30 mm^2 each
    hat/cheek_in (cylinder r = 95, z -16 to -6)     5 969.03 mm^2
    hat/vanes: edge only, NO face contact (report it, do not count it)

PMDB NOTE: the export creates a FOLDER <RUN>\20_spaceclaim\brake.pmdb\ that
contains the file brake.pmdb. Hash the INNER file
(<RUN>\20_spaceclaim\brake.pmdb\brake.pmdb). Opening the folder as a file gives
PermissionError [Errno 13]. PMDB cannot be re-opened by pyansys-geometry on
2026 R1; Fluent's import at Gate 3 is the proof.

OUTPUT CONTRACT (specs/handoffs.md Gate 2), in <RUN>\20_spaceclaim\
- brake.pmdb\brake.pmdb
- tag_report.json with step_sha256, session, import_scale_check, body_map,
  calliper_match, after_delete, named_selections (before-imprint areas and
  predicted values), contact_graph, pmdb_sha256 (inner file), screenshots
  (three paths), job ids, timing
- cad_iso.png, cad_section_9deg.png, named_selections.png (each framed, > 20 kB)
```

---

## B3. Gate 3 - fluent-engineer - mesh, setup, solve and post (one commission)

**goal**

```
ROLE: fluent-engineer - Gate 3 for run <RUN_ID>. In ONE Fluent session: mesh the
frozen brake.pmdb as 27 solid zones with shared topology, run the internal mesh
gate (stop without solving if it fails), then set up transient solid conduction
per case.json, read the setup back, solve the full stop ts = 3.540681 s, and
post-process temperatures, histories, contours and the energy audit into
<RUN>\30_fluent\. Child <N> of <BUDGET>.
```

**context** = preamble A with `<ROLE>` = `fluent-engineer`, `<SKILL LIST>` =
`fl-meshing, fl-thermal-solve, fl-postprocess-energy`, `<SECTIONS>` = `4 to 7`,
`<GATE>` = `Gate 3`, `<STAGE_FOLDER>` = `30_fluent`, then:

```
INPUTS (frozen; refuse if a hash differs)
- <RUN>\20_spaceclaim\brake.pmdb\brake.pmdb   sha256 <sha:pmdb inner file>
    (brake.pmdb is a FOLDER; import the inner file)
- <RUN>\20_spaceclaim\tag_report.json         sha256 <sha:tag_report.json>
- <RUN>\10_cad\cad_report.json                sha256 <sha:cad_report.json>
- <RUN>\00_lead\case.json                     sha256 <sha:case.json>
Mesh from the PMDB only. Never from brake.step: STEP carries no face names and
the solve would run flat at 300 K with no error.

SESSION: one Fluent launch (meshing mode), switched to the solver in the same
process. A second launch only if Fluent died or connect-to-existing was
refused, with relaunch_reason recorded; never a third. Close it before returning.

PART 1 - MESH (PRD section 6; recipe is a starting point, not evidence)
Global size 2.2 to 20 mm, growth 1.2, curvature angle 18 deg. Local sizes:
cheeks 4 mm, vanes 5 mm, hat 8 mm. Poly-hexcore, no inflation, shared topology,
all regions solid.

INTERNAL MESH GATE (fail-closed). Write mesh_report.json, then print this table:
- 27 solid cell zones, 0 fluid zones. Zone map: Fluent name -> PRD name.
- 45 coupled pairs: 2 cheek/pad, 2 pad/backing, 40 cheek/vane, 1 hat/cheek_in;
  areas 5 864.31, 5 864.31, 604.30, 5 969.03 mm^2, each within 2 %.
- max SURFACE skewness <= 0.90; min orthogonal quality >= 0.10; 0 negative
  volumes. Volumetric skewness null with reason "not reported by Fluent 2026 R1".
- per-zone volume within 2 % of PRD section 4 (cheeks 5.717699e-4, each vane
  7.251627e-6, hat 5.132043e-4, pads 7.037168e-5, backing 4.398230e-5 m^3).
- cells + nodes < 512 000 if the licence is Ansys Student (state which).
- AFTER-imprint areas within 2 %: wall-vent 142 865.51, wall-outer 228 477.17,
  pad/backing exposed 31 268.67 mm^2. Sum every per-body piece.
- wall-normal and in-plane cell size at BOTH friction faces (pad side, cheek
  side); compare with penetration depths 1.374 mm (pad) and 7.564 mm (iron).
  Recorded, not gated.
If any gated row fails after two repairs, STOP: do not set up or solve. Return
status FAIL with mesh_report.json and the failing numbers.
Write mesh images: full view and vent close-up (framed, readable).

PART 2 - SETUP (PRD sections 5 and 6; all values are in case.json)
- Energy on, flow off, double precision, transient. Initial and ambient 300 K.
- Materials: MAT-01 iron rho 7200, cp 447, k 52 on cheek_out, cheek_in,
  vane_01..20, hat. MAT-02 pad rho 2500, cp 900, k 1.2 on outerpad, innerpad.
  MAT-03 steel rho 8030, cp 502, k 16.3 on bp_outer, bp_inner.
- Heat source: virtual wall layer d = 0.002 m on ONE side only of each of the two
  pad/cheek contacts. Layer material grey iron (MAT-01 values), never Fluent's
  default aluminium; read it back.
  q'''(t) = 5.8529e9 x (1 - t/ts) W/m^3 for 0 <= t <= ts, then 0, scaled with
  the closed-form A = 5.864306e-3 m^2. The applied-energy integral with the
  MEASURED mesh contact areas must equal 243 055.6 J within 2 %.
- Rotation: solid motion on cheek_out and cheek_in ONLY, axis +Z through the
  origin, omega(t) = -84.1751 x max(0, 1 - t/ts) rad/s. Never rotate vanes or hat.
- Convection: wall-vent h_ref 130, wall-outer h_ref 85, exposed pad and backing
  h_ref 40 W/(m^2 K), T_inf 300 K, omega_ref 56.1167 rad/s:
  h(t) = max(7, h_ref x (abs(omega(t)) / 56.1167)^0.8). At t = 0: 179.81,
  117.57, 55.33. Resolve split named selections to every piece.
- Time: dt = 0.01 s, 354 full steps plus one final step of 0.000681 s to reach
  t = 3.540681 s. Update q''' and omega at least every 10 steps and h at least
  every 25 (exact interval average). Energy residual 1e-8 each step.
READBACK BEFORE SOLVING -> setup_report.json (materials per zone, motion list =
exactly the two cheeks, h schedules and resolved areas, layer side and material,
dt and step count, pre-solve applied-energy integral, tangential-velocity check
<= 1.592987e-4 m^3/s per rad/s). Fix a wrong readback before solving; two tries.

PART 3 - SOLVE AND POST
- Solve to t = 3.540681 s including the short step.
- results.json (schema in fl-postprocess-energy): peaks[] with
  rotor_friction_cell_max, rotor_friction_wall_layer_max, pad_friction_cell_max,
  pad_friction_wall_layer_max, rotor_all_cell_max, rotor_all_surface_max (each
  peak_k, peak_time_s, end_of_stop_k); requirements_data THM-01 to THM-04;
  rotor_bulk_rise_k; energy_audit {E_applied_j, E_stored_j, E_conv_j, ratio_pct,
  residual_j, E_applied_over_vehicle_pct}; coverage.covers_full_stop; mesh_sha256;
  timing.
- histories\*.csv (time s, temperature K, one row per step, ending 3.540681).
- contours: rotor and pad friction faces at the time of peak and at end of stop,
  legend in K, time and range printed on the image.
GATE: E_applied within 2 % of 243 055.6 J; (E_stored + E_conv) / E_applied 90 to
110 %; full ts covered; nothing clipped at a solver temperature limit.

OUTPUT CONTRACT (specs/handoffs.md Gate 3), in <RUN>\30_fluent\
brake.msh.h5, mesh_report.json (with timing), mesh images, case and data files,
setup_report.json, results.json (with timing covering the whole commission),
histories\*.csv, contour images.
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
- Rewrite <cad_report.json / tag_report.json / mesh_report.json + results.json>
  completely, with a "repair" block {k, failing_check, root_cause, change_made}
  and a fresh timing block.
- HALT rule applies inside this commission (two tries). If still failing,
  return HALTED with both numbers.
```

After a Gate 1 repair every downstream frozen hash is void: Gate 2 onward is
re-commissioned with the new STEP hash. Say so to the user.
