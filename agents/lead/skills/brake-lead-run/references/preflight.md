# Preflight - before Gate 0

Preflight proves that the run *can* succeed before anything irreversible happens.
It should take about 3 minutes: batch the terminal checks into one or two calls.
Every check below ends with a PASS or a STOP. A STOP ends the run with
`status: halted` and a message to the user; it is never "noted and continued".

## 1. Run folder

1. Run id: `FR330V-<yyyymmdd>-<hhmm>` in local time, for example
   `FR330V-20261001-0930`. Add a suffix `-b`, `-c` if the folder already exists.
   Never reuse a folder.
2. Create, with the terminal or file tool:

   ```
   C:\brake-runs\<run-id>\00_lead
   C:\brake-runs\<run-id>\00_lead\checks
   C:\brake-runs\<run-id>\10_cad
   C:\brake-runs\<run-id>\20_spaceclaim
   C:\brake-runs\<run-id>\30_fluent
   C:\brake-runs\<run-id>\30_fluent\histories
   C:\brake-runs\<run-id>\50_report
   ```

   There is **no** `40_drawing` folder: 2D drawings are descoped in H1.2.
3. Check the path is **not** under OneDrive (it must not contain `OneDrive`).
   Sync locks break Fluent and SolidWorks writes, and the failure looks like a
   permissions bug.

**PASS** when the seven folders exist and are empty.

## 2. BUILD_STATE.json

Copy `<project>\examples\BUILD_STATE.template.json` to
`C:\brake-runs\<run-id>\BUILD_STATE.json`. The template already carries
`"prd_revision": "H1.2"` (the revision every artifact must carry per
`specs/handoffs.md`); confirm it reads `"H1.2"` and do not add a second revision
key. Set:

| Key | Value |
|---|---|
| `run_id` | the run id |
| `status` | `running` |
| `model` | the **LLM** you are running on, as the provider reports it (for example `nvidia/nemotron-3-ultra`), not the product name |
| `profile` | the Hermes profile name, and whether the session is interactive or finite |
| `stage` | `preflight` |
| `lead_session_id` | the Hermes session id if the runtime shows it, otherwise `null` with a note |
| `python_route` | `execute_code` or `C:/solidpilot/.venv/Scripts/python.exe` (section 4) |
| `measurements.preflight` | the table below, filled |
| `artifacts.specs` | SHA-256 of `specs\PRD.md`, `specs\handoffs.md`, `AGENTS.md` |
| `timing.run_started_at` | now |

API idiom (hash a file, PowerShell):

```
(Get-FileHash -Algorithm SHA256 -LiteralPath "C:\brake-runs\<run-id>\10_cad\brake.step").Hash.ToLower()
```

## 3. Project path

Resolve the absolute project path once and write it into `BUILD_STATE.json`
(`project_root`). It is the folder that holds this `AGENTS.md`, and it differs
between workstations, so read it on this machine; never copy one from an old
run or a document:

```
(Resolve-Path .).Path      # run in the brake chat terminal, which starts in the package folder
```

Every commission quotes this path verbatim, because children do not know where
the project is unless you tell them.

## 4. Your own toolset (look, do not call)

| Must be in your tool list | Why | If missing |
|---|---|---|
| `delegate_task` (toolset `delegation`) | the only way you get work done | **STOP**: "delegate_task is not available to the lead; enable the `delegation` toolset in the profile's `platform_toolsets.cli`. No work was started." |
| `skill_view`, file tools, terminal, `todo` | skills, artifacts, hashing, stage list | STOP |
| `vision_analyze` (toolset `vision`) | screenshot and figure checks | warn; figure checks become findings |
| `execute_code` (toolset `code_execution`) | arithmetic without a script file | not a stop: use `C:/solidpilot/.venv/Scripts/python.exe` and record `python_route` |

Never type bare `python` or `python3` in the terminal: on this machine it opens
a Windows Store installer and the call hangs.

## 5. Specialist tools visible (look, do not call)

List your available tools and confirm these suffixes are present. Hermes exposes
MCP tools with a server prefix (`mcp_solidpilot_...` or `mcp__solidpilot__...`),
so match on the suffix.

| Server | Suffixes that must be visible |
|---|---|
| solidpilot | `ensure_ready`, `open_new_part`, `create_sketch`, `add_sketch_entities`, `extrude_feature`, `analyze_model`, `open_new_assembly`, `insert_component`, `analyze_assembly`, `export_document` |
| ansys | `run_ansys_script`, `submit_ansys_job`, `job_status`, `job_log`, `job_cancel`, `job_list`, `read_json_file` |

These tools are visible to you only because children inherit your toolsets.
Seeing them is not permission to call them. If a server's tools are missing,
the children will not have them either. STOP with:

> Preflight STOP: SolidPilot (or Ansys) MCP tools are not visible in the lead
> session. Children inherit the lead's toolsets, so the specialists would have no
> CAD/CAE tools. Relaunch the lead with the mcp-solidpilot and mcp-ansys toolsets
> enabled (see docs/SETUP.md). No work was started.

Do **not** fall back to `scripts/mcp_client.py` on your own initiative. It is a
slow diagnostic fallback that the children may use only if you tell them native
MCP is unavailable, and that decision needs the user's agreement.

## 6. Delegation settings

First find the profile this session runs in. A bare `hermes config get` reads the
**default** profile, which is usually not the `brake` profile, so you would read
the wrong numbers. Run `hermes profile list` (the active one is marked). If you
cannot tell, check the `HERMES_HOME` environment variable in the terminal: a path
ending in `profiles\<name>` names the profile. Then read the settings **with
`-p <profile>`**, in one terminal call:

```
hermes -p <profile> config get delegation.oneshot_max_children
hermes -p <profile> config get delegation.max_concurrent_children
hermes -p <profile> config get delegation.max_iterations
hermes -p <profile> config get delegation.child_timeout_seconds
```

Record the profile name next to each value in BUILD_STATE.

`max_concurrent_children`: expect 1. It is correct for this package (one Ansys
licence, sequential stages). It is also why a `tasks=[...]` batch fails: you
never batch, so a value of 1 never blocks you.

Decide whether the run is finite or interactive, and record which and why:
- **Finite:** started with `hermes chat -q`, `--oneshot`, `hermes -z`, or non-TTY
  input (which implies finite mode even without the flag). `delegate_task`
  blocks until the child returns.
- **Interactive:** a `hermes chat` TUI session, or a chat in the **Hermes
  Desktop app**. The child runs in the background and Hermes posts a completion
  notice. The `oneshot_max_children` budget does **not** apply; record it and
  move on.

The table below applies to finite runs only. The H1.2 plan needs **3 children**
(CAD, SpaceClaim, Fluent); each repair adds one.

| Budget (finite runs) | Decision |
|---|---|
| 0 | unlimited: 3 children plus up to 2 repairs per gate |
| 1 or 2 | **STOP.** The chain needs at least 3 children |
| 3 | no repair headroom. Tell the user that any gate failure will halt the run |
| 4 or 5 | one or two repairs in total; say so |
| 6 or more | normal plan with repair headroom |

STOP message for 1 or 2:

> Preflight STOP: delegation.oneshot_max_children = 2 in this finite session.
> This package needs at least 3 separate specialist children (SolidWorks CAD,
> SpaceClaim geometry prep, Fluent mesh and solve) and 6 or more with repair
> headroom. I will not do a specialist's work myself. Please relaunch with a
> profile that sets delegation.oneshot_max_children to 8 (or 0), or run
> interactively. No CAD or CAE work was started.

`max_iterations`: record it. If it is below 300, **STOP before commissioning
the SolidWorks child**. A cold build of 28 bodies needs a few hundred tool
calls, so a child capped lower is cut off half-way and leaves a partial model.
Ask the user to set it to about 600 in the profile. If it is 300 to 599, warn
the user; this is a warning, not a stop.

`child_timeout_seconds`: 0 means no wall cap. Record it. If it is non-zero and
below 7200 s, warn that the Fluent child may be cut off.

**Never change these settings yourself.** Report and let the user decide.

## 7. No stray Ansys processes

API idiom (PowerShell):

```
Get-Process | Where-Object { $_.ProcessName -match '^(fluent|fl\d+|cx\d+|SpaceClaim|Discovery)' } |
  Select-Object Id, ProcessName, StartTime
```

Ansys Student allows one session, and SpaceClaim and Fluent share it. An open
Fluent or SpaceClaim window holds the licence and the child's next launch dies
(the predecessor saw error `10054`). If any process is listed, STOP and ask the
user to close it. Do not kill it: it is not yours.

Record the SolidWorks state the same way (`SLDWORKS`). SolidWorks being open is
fine; the solidworks-engineer inventories its documents before mutating anything.

## 8. No drawing stage

Confirm the plan has exactly Gates 0 to 4 and three commissions. There is no
Gate 5 drawing commission, no `rotor_only.SLDASM`, no `40_drawing` folder, and no
`sw-drawing-visuals` skill in any commission. CAD visuals come from SpaceClaim
at Gate 2 (`cad_iso.png`, `cad_section_9deg.png`, `named_selections.png`).

## 9. Package tests (optional, skip when time matters)

`C:/solidpilot/.venv/Scripts/python.exe -B -m unittest discover -s tests -v`
from the project root. A failure here is a package defect, not an engineering
one. Report it; it is not a STOP unless the failing test concerns role or skill
files the children need.

## 10. Print the preflight table

```
PREFLIGHT - run FR330V-20261001-0930
check                              result
run folder (not OneDrive)          PASS  C:\brake-runs\FR330V-20261001-0930
BUILD_STATE.json created           PASS  prd_revision H1.2
spec hashes recorded               PASS  PRD 9c1e..., handoffs 41aa..., AGENTS 07d2...
delegate_task in lead toolset      PASS
python route                       PASS  C:/solidpilot/.venv/Scripts/python.exe
SolidPilot tools visible           PASS  10/10 suffixes
Ansys tools visible                PASS  7/7 suffixes
mode / budget                      PASS  interactive; oneshot budget n/a
max_concurrent / max_iter / timeout PASS 1 / 600 / 0
stray Ansys processes              PASS  none
drawing stage                      PASS  none (descoped in H1.2)
PREFLIGHT: PASS
```

Then set `stage: gate0`, record `timing.preflight`, and continue to
`brake-duty-cycle`.
