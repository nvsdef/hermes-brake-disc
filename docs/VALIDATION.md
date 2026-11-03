# Validation status

## Run 4, fast profile with flipped twins (2026-11-02, FR330V-20261102-2227) - complete_with_findings

Package commit a82b8ca. Same harness as run 3 (Claude lead, one Claude
specialist per application). **12.3 min end to end** (22:27:08 to 22:39:27), every
gate PASS on the first attempt, no repairs.

| Gate | Result | Time |
|---|---|---|
| 0 duty cycle | PASS (3 values within 0.00003 %) | < 1 min |
| 1 CAD, 6 parts + 3 flipped instances | PASS: 28/28 bodies, 9 components (6 identity, 3 flip), STEP 25 / 7 / 9 | 5.4 min, 104 calls (run 3: 6.5 min, 130 calls) |
| 2 SpaceClaim prep | PASS 15/15; 28 bodies imported, areas 0.00 % | 62 s app, 85 s with agent |
| 3 Fluent, full stop | PASS 18/18; stored/applied 98.84 %, applied 100.09 % of E | 192 s app, 221 s with agent |
| 4 gate summary | lead | < 1 min |

Friction-face peaks (coarse mesh, dt 0.05 s): 729 K rotor, 930 K pad; end of stop
384 K / 388 K. Fluent left open with the contour.


## Run 3, fast run profile (2026-11-02, FR330V-20261102-2152) - complete_with_findings

End-to-end with agents: Claude lead plus one Claude specialist per application,
following `AGENTS.md`, the role SOULs and skills (package commits 572c388 to
c4c8b8b). Wall time **20.5 min** (21:52:20 to 22:12:50), including two repair
cycles that each found a package defect.

| Gate | Owner | Result | Time |
|---|---|---|---|
| 0 duty cycle | lead | PASS: ts 3.540681 s, E 243 055.56 J, omega0 -84.175084 rad/s | < 1 min |
| 1 CAD, build + assemble once | solidworks-engineer (SolidPilot) | PASS: 28/28 bodies (worst calliper -0.0015 %), 9 components, STEP 28 solids / 10 PRODUCT, 0 repairs | 6.5 min, 130 calls |
| 2 SpaceClaim prep | spaceclaim-engineer (`spaceclaim_prep.py`) | attempt 1 FAIL (script KeyError on z-only vane boxes); repair PASS 15/15, areas 0.00 % | 56 s app time |
| 3 mesh + full-stop solve | fluent-engineer (`fluent_fast.py`) | attempt 1 FAIL (stored-energy gate too strict: -1.41 J at the last 0.04 s); repair PASS 18/18 | 198 s app time (solve 60 s) |
| 4 gate summary | lead | 37 dispositions; THM-01 to 04 NOT RUN (fast profile) | < 1 min |

Gate 3 physics (coarse mesh, dt 0.05 s, whole stop): applied 243 280.8 J
(100.09 % of E), stored 240 301.4 J (98.78 %); friction-face peaks 682 K rotor and
878 K pad at 0.2 s, 384 K and 388 K at the end of the stop. Fluent was left open
with the temperature contour.

Clean-path estimate with both fixes in place: about 13 to 14 min (Gate 1 CAD
6.5 min is now the bottleneck; Gates 2 and 3 about 1 and 3.5 min of application
time plus agent overhead).


## Workstation readiness for H1.2 (2026-11-02) - PASS, no engineering run

This was a package and live-MCP readiness pass. No geometry, mesh or solve was
produced.

| Check | Expected | Measured | Result |
|---|---|---|---|
| Unit tests (Linux sandbox and Windows SolidPilot venv) | OK | 20 tests OK (Linux); 10 tests OK in the Windows preflight run, before the portability tests were added | PASS |
| SolidPilot MCP `ensure_ready` | attached | `com_attached=True`, `sw_version=34.3.2` | PASS |
| SolidPilot tool names | 46 = `mcp/solidpilot-tools.json` | 46, identical names | PASS |
| SolidPilot argument schemas, 17 included tools | unchanged since 2026-09-21 | property names and required lists identical | PASS |
| SolidPilot source commit | `a81d12ba` | `a81d12ba` | PASS |
| Ansys MCP tool names and argument schemas | 10 = `mcp/ansys-tools.json` | 10, identical | PASS |
| ansys-agent Python / pyansys pins | 3.11.9, geometry-core 0.15.5, fluent-core 0.41.0 | same | PASS |
| Ansys v261 Fluent and SpaceClaim executables | exist | exist (Student v261) | PASS |
| Skills vs `tools.include` | every SolidPilot tool a skill tells the agent to call is included | the tools outside the filter appear only as "do not use" (unit test) | PASS |
| `install_profile.ps1` render vs the H1.2 config authored after run 1 | identical | YAML-equal, apart from the removed disabled `fusion360` block | PASS |
| `preflight.ps1` (Windows PowerShell 5.1) on a freshly rendered profile | 0 FAIL | 29 checks, 0 FAIL, 0 WARN | PASS |

Findings:
1. **The author's live `brake` profile is still H1.1** (SolidPilot `tools.exclude`,
   no `code_execution` toolset). SETUP step 7 had not been applied, so the H1.2
   profile has never been used in a run. Fix: run `scripts/install_profile.ps1`.
   The preflight now fails on this condition.
2. The profile `SOUL.md` and the complete profile config existed only in the
   git-ignored `.local/`, so a fresh clone could not be set up. They now live in
   `profile/`.
3. `hermes -p brake mcp test` with the H1.2 include filter was not exercised in
   this pass, because it reads the live profile (finding 1). Run
   `preflight.ps1 -McpTest` after installing.

Still to do, in this order:
1. `install_profile.ps1`, then `preflight.ps1 -McpTest` (expect 31 checks, 0 FAIL).
2. `examples/readiness-prompt.md`.
3. A full H1.2 run with `examples/prompt.md`; record the model, session IDs, gate
   numbers and elapsed time here.


## Run 1 on H1.1 (2026-09-30, FR330V-20260930-1012) - halted at Gate 2

| Stage | Result | Time |
|---|---|---|
| Preflight + Gate 0 | PASS; duty cycle within 0.00004 % of PRD | 10:12-10:15 |
| Gate 1 CAD | 28/28 bodies PASS (calliper -0.002 %), interference 0, STEP 28 solids after one repair (assembly had 4/9 parts) | 10:15-11:51 |
| Gate 2 SpaceClaim | FAIL; ~35 launches; see DECISIONS 24-32 | 11:53-13:14 |
| Gate 3 Fluent | not reached | - |

Readiness (all three children started, loaded SOUL and skills) passed before the run.


## H1.1 (2026-09-29): package rebuilt, NOT yet run live

Package checks:
- Unit tests cover role folders, SKILL.md frontmatter (description of 60 characters or fewer, `name` matching the folder), `## Verification` sections, reference-file existence, every CTS requirement ID present in the PRD, the absence of stage scripts, and a clean checkpoint template.
- PRD checksums were computed two ways: exact polar-interval integration and a 0.1 mm Cartesian raster. The two agree within 0.01 % for the calliper band areas.
- Hermes configuration keys (`mcp_servers`, `skills.external_dirs`, `delegation.*`) come from the Hermes documentation pages, retrieved 2026-09-29. `hermes mcp add` flag syntax beyond the documented examples is unconfirmed; editing `config.yaml` directly is the reliable path.

Still to do, in this order:
1. `hermes -p brake mcp test solidpilot` and `... ansys`.
2. `examples/readiness-prompt.md`: all four roles start, load their skills and see their MCP tools.
3. A full run with `examples/prompt.md`.
4. Record the model, session IDs, gate numbers and elapsed time here.

---

## Previous result (H1, 2026-09-21): BLOCKED before engineering execution



The source package exists and its five unit tests pass. Live stdio MCP initialization and tool discovery succeeded for SolidPilot (46 tools) and Ansys (10 tools). These checks do not prove CAD application readiness, license availability, geometry correctness or solver readiness.

No fresh native CAD, STEP, PMDB, mesh, case/data, thermal result or engineering report was produced. The end-to-end demo is NOT complete.

## Executed checks

- `python -B -m unittest discover -s tests -v`: five tests, OK. Coverage includes server lookup/config preservation, MCP timeout compatibility, role/skill files, linked references, clean checkpoint, absence of prebuilt engineering scripts and retained CTS requirement identifiers. This is package validation, not engineering validation.
- MCP SDK observed in the client environment: 2.0.0. Its ClientSession timeout accepts float seconds. The original timedelta payload failed during initialization; the client now selects float seconds for major version 2 and timedelta for major version 1. Regression test went red before repair, then green; live discovery subsequently passed. MCP 1 compatibility is unit-tested, not live-tested here.
- Tool inventories saved under `.local/solidpilot-tools.json` and `.local/ansys-tools.json`. No geometry tools were invoked by this readiness check.
- A real Hermes lead commissioned two real children sequentially, then the third commission returned a tool error. The lead did not substitute role-play for the rejected specialist.

## Readiness evidence

Lead session: `20260921_220109_01a6be`.
Terminal process record: `proc_4786ab686193` (exited).
Observed model identifier: `nvidia/nvidia/nemotron-3-ultra` (from stream initialization, not assumed from the parent desktop chat).

| Specialist | Observed result | Trace identity |
|---|---|---|
| solidworks-engineer | Child read its role/skill and returned readiness information | `deleg_72716ea6/task-0.log` |
| spaceclaim-engineer | Child read its role/skill and returned readiness information | `deleg_6d88a148/task-0.log` |
| fluent-engineer | Spawn rejected; no child executed | unavailable |

The first two traces are under the active Hermes home's `cache/delegation/live/`. They are delegation transcript handles, NOT child session IDs. Child session IDs were unavailable in the returned results; none have been fabricated. Cache artifacts may expire.

Exact rejection:

> Delegation budget for this one-shot run is exhausted (2/2 subagents used; delegation.oneshot_max_children). Do the remaining work yourself in this session — reviewing your own diff and running the tests inline is expected here, not a delegated review.

The package requires three separate specialists, so the suggestion to do remaining work inline was not followed. `hermes config get delegation.oneshot_max_children` returned `2`. Installed runtime source confirms a finite-session total-spawn budget in `tools/delegate_tool.py::_oneshot_spawn_budget`, independent of concurrent-child limits. CLI help confirms non-TTY input implies finite mode even without `--oneshot`.

## Remaining work

1. Verify an approved launch path capable of commissioning all three specialists and supporting later repair commissions. A supported interactive session is a candidate, not yet tested here. No global configuration change is authorized or applied by this package.
2. Establish traceable child session identities and an approval channel; unavailable approval must stop the run.
3. Run application/license/document preflight, then the gated CAD → SpaceClaim → Fluent chain.
4. Produce and independently review all engineering evidence, including geometry, mesh, readback physics, full-stop energy/temperature histories and artifacts.

The specs are H1 draft engineering instructions with explicit departures from historical evidence in DECISIONS.md, not a validated brake design. The new calliper correction and numerical acceptance gates remain unexercised.
