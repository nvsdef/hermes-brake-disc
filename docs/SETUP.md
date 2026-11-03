# Setup - Hermes, native MCP, per-agent skills

Everything below happens in a dedicated Hermes **profile** called `brake`. Your
default profile and global settings are not touched. The same steps work on any
Windows workstation: nothing in the repository depends on the author's paths.

## 0. Prerequisites
These are pinned in `profile/environment.json`. `scripts/preflight.ps1` checks each one.

| Item | Required | Notes |
|---|---|---|
| Windows 11, Windows PowerShell 5.1 | yes | the scripts avoid PowerShell 7-only syntax |
| SOLIDWORKS 2026 (major version 34), licensed | yes | validated on 34.3.2 (SP3.2) |
| SolidPilot MCP at **`C:\solidpilot`** | yes, at that exact path | the skills call `C:/solidpilot/.venv/Scripts/python.exe` for arithmetic; validated at commit `a81d12ba` |
| Ansys 2026 R1 (v261), Student is fine | yes | default root `C:\Program Files\ANSYS Inc\ANSYS Student\v261` |
| `ansys-agent` MCP server with its `.venv` | yes | any folder; default is a sibling of this package. Pins: `ansys-geometry-core` 0.15.5, `ansys-fluent-core` 0.41.0, Python 3.11.9 |
| Hermes, with a provider configured | yes | the template uses the NVIDIA inference endpoint; the API key comes from the env var named in `custom_providers.key_env`, never from this repo |
| `C:\brake-runs\` | created by the installer | all run output goes there, never into OneDrive |
| Git and GitHub CLI (`gh`) | only to clone/publish | `winget install Git.Git GitHub.cli` |

The pyansys pins are exact on purpose: `api-verified.md` in the SpaceClaim and
Fluent skills was built from those library versions.

## 1. New workstation, start to finish
```powershell
# 1. Get the package (anywhere; OneDrive is fine for the SOURCE, never for run output)
gh repo clone <owner>/hermes-brake-disc
cd hermes-brake-disc

# 2. Create the profile once (this clones your default profile's provider + credentials)
hermes profile create brake --clone

# 3. Render the profile for this machine (backs up any existing config.yaml / SOUL.md)
powershell -ExecutionPolicy Bypass -File scripts\install_profile.ps1 -AnsysAgentRoot "<path-to>\ansys-agent"

# 4. Check the machine. Must end "0 FAIL". -McpTest starts each MCP server once to list tools.
powershell -ExecutionPolicy Bypass -File scripts\preflight.ps1 -McpTest
```
`install_profile.ps1` options: `-AnsysAgentRoot` (default `..\ansys-agent`),
`-AwpRoot` (default `$env:AWP_ROOT261`, then the Student path) and `-ProfileDir`
(default `%LOCALAPPDATA%\hermes\profiles\brake`, or `HERMES_HOME` when it names
`brake`). It checks every input path first and writes nothing if one is missing.
It writes exactly three files: `<profile>\config.yaml`, `<profile>\SOUL.md` and
the git-ignored `.local\servers.json` for the diagnostic client. To look at the
result without touching a real profile, pass
`-ProfileDir "$env:TEMP\brake-test" -CreateProfileDir`.

Then go to section 5 (Launch).

## 2. What the profile contains, and why
The single source is `profile/config.template.yaml`, a complete Hermes
`config.yaml` with three placeholders: `{{PACKAGE_ROOT}}`, `{{ANSYS_AGENT_ROOT}}`
and `{{AWP_ROOT261}}`. Lines marked `# BRAKE` differ from a default profile.

**Native MCP servers (`mcp_servers`).** Hermes keeps one stdio process alive per
server and puts every tool straight into the model's tool list, as
`mcp_solidpilot_<tool>` / `mcp_ansys_<tool>` (some builds use
`mcp__server__tool`; the skills match on the suffix). Before this, agents reached
SolidWorks through `scripts/mcp_client.py`: every call spawned a new Python
process, re-initialised the adapter and re-downloaded 96 KB of tool schemas, so
about 200 CAD calls cost 400+ model turns of overhead, and the model had to guess
argument names.

**SolidPilot `tools.include` (17 tools).** The live server exposes 46 tools
(`mcp/solidpilot-tools.json`). The skills use 17; the rest are either measured
broken (`submit_feature_graph`, `rebuild_from_ir`, `auto_dimension_drawing`) or
not needed. See `sw-solidpilot/references/tools-used.md`. The Ansys server's 10
tools are in `mcp/ansys-tools.json`.

**Skill folders (`skills.external_dirs`).** One folder per agent, plus `_shared`:
8 skills in total.
- `brake-lead-run`, `brake-duty-cycle`, `brake-handoff`
- `sw-solidpilot`, `sw-rotor-build`, `sw-pads-calliper`
- `sc-fast-prep` (runs `scripts/stages/spaceclaim_prep.py`)
- `fl-fast-run` (runs `scripts/stages/fluent_fast.py`)

Check discovery with:
```powershell
hermes -p brake chat -q "List your skills whose names start with brake-, sw-, sc- or fl-." --oneshot
```

**How role-specific skills work in Hermes.** `delegate_task` has no skills or
SOUL parameter, but every child receives the project `AGENTS.md`. So `AGENTS.md`
carries a role table, the lead starts every commission with `ROLE: <role>`, and
the child reads its own `agents/<role>/SOUL.md` and calls `skill_view` on its own
skills before any tool call. The commission templates are in
`agents/lead/skills/brake-lead-run/references/commission-templates.md`.

**Lead SOUL (`profile/SOUL.md`).** Hermes puts the profile's `SOUL.md` into the
**lead's** system prompt only, so the lead rules survive context compaction.
Children never receive it.

**Toolsets (`platform_toolsets.cli`).** Adds `delegation` (for `delegate_task`)
and `code_execution` (arithmetic without the Windows Store `python` stub).

## 3. Updating the profile after a package change
Edit `profile/config.template.yaml` or `profile/SOUL.md`, never the rendered
copy, then re-run `install_profile.ps1` and `preflight.ps1`. The preflight fails
if the profile's `SOUL.md` differs from the package's, if a placeholder is left,
or if the skill folders point at a different checkout.

## 4. Delegation limits
Set in the template's `delegation:` and `agent:` blocks:
- `oneshot_max_children` defaults to **2**. That default is what blocked the
  third specialist in the September readiness test. `0` means unlimited.
- `max_iterations` defaults to **250 turns per child**, too few for the
  SolidWorks build; the template sets 600.
- `max_concurrent_children: 1` runs the stages one after another, which suits
  Ansys Student (one session at a time).

## 5. Launch
Open a terminal **in this package folder**, so Hermes loads `AGENTS.md`, and run:
```powershell
hermes -p brake chat
```
Do **not** pass `--toolsets`/`-t`. Children inherit the lead's toolsets, and an
explicit list that omits `mcp-solidpilot` and `mcp-ansys` hides the CAD and CAE
tools from every specialist. That is part of why the earlier runs fell back to
the terminal client.

First paste `examples/readiness-prompt.md`. When all four roles report in with
their skills and MCP tools, paste `examples/prompt.md`, attaching or pointing to
`specs/PRD.md` (or `docs/PRD-FR330V-H1.2.pdf`).

**Do not attach the CTS.** If you do, `AGENTS.md` tells the agents that the PRD
wins, but a second specification is still a distraction.

## 6. Troubleshooting
| Symptom | Check |
|---|---|
| `preflight.ps1` FAIL on `pin ansys-...` | The ansys-agent venv has a different pyansys version. Install the pinned one (`pip install ansys-geometry-core==0.15.5 ansys-fluent-core==0.41.0` in that venv) or re-verify the `api-verified.md` sheets against the new version before running |
| `preflight.ps1` WARN on SolidPilot source commit | SolidPilot was updated. Compare its live tool list with `mcp/solidpilot-tools.json` before a run; a changed argument name breaks the skills silently |
| `preflight.ps1` FAIL on `profile SOUL.md == package` or `code_execution` | The profile is older than the package. Re-run `install_profile.ps1` |
| Child says it has no `mcp_solidpilot_*` tools | You launched with `-t` and left out the MCP toolsets, or `hermes mcp test` fails |
| `Delegation budget ... exhausted` | `delegation.oneshot_max_children` in the **brake** profile |
| Child never loads its skills | `skills.external_dirs` paths (missing paths are skipped silently); repeat the step 3 check |
| Fluent or SpaceClaim writes into OneDrive | The ansys server `cwd`/`ANSYS_RUNTIME_DIR`; agents must pass absolute paths |
| Agent quotes a different AGENTS.md (e.g. "# Workspace guidance") | A parent folder is a Git repo with its own AGENTS.md, and Hermes loads the repo root's file. Run `git init` in this package folder so it is its own root (fixed 2026-09-30) |
| App chat shows the wrong folder, no brake skills or no `delegate_task` | The app chat is on the default profile or a remembered folder. Use `brake chat` from this folder, or pick **brake** in the profile rail and open a new chat |
| A single solid disc with holes appears (the old failure) | The agent designed from the CTS. Confirm the prompt names `specs/PRD.md` and the child read `sw-rotor-build` |

`scripts/mcp_client.py` remains as a **diagnostic** only, for listing or calling
one tool when native registration is broken:
```powershell
python scripts/mcp_client.py --server solidpilot list
```

## 7. Refreshing a workstation that ran H1.1
Run 1 used an H1.1 profile (SolidPilot `tools.exclude`, no `code_execution`).
`install_profile.ps1` replaces it with H1.2 and keeps the old files as
`config.backup-<timestamp>.yaml` and `SOUL.backup-<timestamp>.md` in the profile
folder. The preflight row `profile toolset code_execution (H1.2)` fails until
this is done.

## 8. Stopping a run completely
`/stop` ends the lead's turn but a background child keeps running. To stop
everything: Ctrl+C twice in the `brake chat` window (or close it), then
```powershell
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'hermes.*chat|brake chat|ansys-agent.*_runner' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Get-Process SpaceClaim, fluent -ErrorAction SilentlyContinue | Stop-Process -Force
```
