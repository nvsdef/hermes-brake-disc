# Requirements - what a new workstation needs

Read this before setting up a machine to run the FR-330V brake workflow
(SolidWorks -> SpaceClaim -> Fluent, driven by agents). It is written for both a
person and an AI agent. The machine-readable pins are in `profile/environment.json`;
`scripts/preflight.ps1` checks a machine against them.

There are three kinds of dependency:

| Kind | Who provides it | In this repo? |
|---|---|---|
| **A. Licensed applications and the model** | you, before setup | no, and they cannot be |
| **B. Build tools** | you, one `winget` command | no |
| **C. MCP servers, Python environments, agents, skills, scripts** | `scripts/bootstrap_workstation.ps1` and `scripts/install_profile.ps1` | yes (source, pins and lock files) |

## A. Install yourself first (licensed or account-bound)

| ID | Item | Version | Check (PowerShell) | Expected |
|---|---|---|---|---|
| A1 | Windows 11 with Windows PowerShell 5.1 | - | `$PSVersionTable.PSVersion.Major` | `5` |
| A2 | SOLIDWORKS 2026, licensed, opened once by hand | major 34 (tested 34.3.2 / SP3.2) | `(Get-ItemProperty "HKLM:\SOFTWARE\SolidWorks\SOLIDWORKS 2026\Setup").'SolidWorks Folder'` | the install folder; preflight confirms version 34 |
| A3 | Ansys 2026 R1 with SpaceClaim and Fluent | v261; **Ansys Student is fine** (SpaceClaim and Fluent run together on it) | `Test-Path "C:\Program Files\ANSYS Inc\ANSYS Student\v261\fluent\ntbin\win64\fluent.exe"` (or under `$env:AWP_ROOT261`) | `True` |
| A4 | An agent runtime: **Hermes** (lead + 3 subagents) **or** Claude Desktop / Cowork | Hermes: any with `delegate_task`; Claude: tested on Opus | Hermes: `Get-Command hermes` | a path |
| A5 | A model endpoint and its API key in an environment variable | OpenAI-compatible; default NVIDIA inference API, a local model works (`docs/SETUP.md` 1b) | `[bool]$env:HERMES_CUSTOM_INFERENCE_API_NVIDIA_COM_API_KEY` (or your `-ModelKeyEnv` name) | `True` |

Never put an API key, licence file or password in this repository.

## B. Build tools (one command)

```powershell
winget install Git.Git GitHub.cli Python.Python.3.11 Microsoft.VisualStudio.2022.BuildTools
```

| ID | Item | Why | Check | Expected |
|---|---|---|---|---|
| B1 | Git | clones the pinned SolidPilot | `git --version` | `git version 2.x` |
| B2 | Python 3.11 with the `py` launcher | both MCP venvs (pinned to 3.11.9) | `py -3.11 --version` | `Python 3.11.x` |
| B3 | Visual Studio 2022 Build Tools, MSBuild + .NET Framework 4.8 targeting pack | builds SolidPilot's execution service against the local SolidWorks | `& "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.Component.MSBuild -property installationPath` | a path |
| B4 | GitHub CLI | optional: only for publishing | `gh --version` | any |

About 2 GB free disk for the venvs; run output goes to `C:\brake-runs` (never OneDrive).

## C. Installed from this repository

| ID | Item | Source in repo | Installed to | By |
|---|---|---|---|---|
| C1 | **SolidPilot MCP** (drives SolidWorks; 46 tools, 17 used) | `mcp/solidpilot/SOURCE.md` (upstream URL + commit `a81d12ba`, AGPL-3.0, cloned not copied), `requirements.lock.txt`, `env.template` | `C:\solidpilot` (exact path; the skills call it) | `bootstrap_workstation.ps1` |
| C2 | **ansys-agent MCP** (drives SpaceClaim via ansys-geometry-core 0.15.5 and Fluent via ansys-fluent-core 0.41.0; 10 tools) | `mcp/ansys-agent/` (full source) + `requirements.lock.txt` | venv `C:\brake-tools\ansys-agent-venv` | `bootstrap_workstation.ps1` |
| C3 | Agent configs: Hermes `brake` profile, `.local/servers.json`, `.local/claude_mcp_servers.json` | `profile/*.template.*` | Hermes profile folder, `.local/` | `install_profile.ps1` |
| C4 | Agents, skills, PRD, stage scripts, tests | `agents/`, `specs/`, `scripts/stages/`, `tests/` | used in place | - |
| C5 | Run folder | - | `C:\brake-runs` | bootstrap |

There is no separate SpaceClaim MCP: C2 covers SpaceClaim and Fluent.

## Setup sequence

Each step must succeed before the next.

| Step | Command (from the repo root) | Done when |
|---|---|---|
| 1 | `git clone https://github.com/nvsdef/hermes-brake-disc.git; cd hermes-brake-disc` | folder exists |
| 2 | `powershell -ExecutionPolicy Bypass -File scripts\bootstrap_workstation.ps1 -CheckOnly` | prints `ok` / `TODO` lines and changes nothing; it stops with `STOP:` at the first missing A2, A3, B1 or B2 item (fix it and rerun) |
| 3 | `powershell -ExecutionPolicy Bypass -File scripts\bootstrap_workstation.ps1` | exits 0; C1, C2, C5 exist |
| 4 | Hermes only: `hermes profile create brake --clone` | profile exists |
| 5 | `powershell -ExecutionPolicy Bypass -File scripts\install_profile.ps1` (add `-ModelName`, `-ModelBaseUrl`, `-ModelProvider`, `-ModelKeyEnv` for another model) | configs written, no missing-path error |
| 6 | Claude only: merge `.local\claude_mcp_servers.json` into the Claude MCP settings (servers `solidpilot`, `ansys-agent`) and restart | the client lists 46 + 10 tools |
| 7 | `powershell -ExecutionPolicy Bypass -File scripts\preflight.ps1 -McpTest` | **ends with `0 FAIL`** |
| 8 | Run: Hermes `hermes -p brake chat` + `examples/prompt.md`, or Claude Cowork on this folder + `examples/prompt-claude.md` | all gates PASS in about 13 to 15 min (`docs/VALIDATION.md`, run 7) |

Before each run: close any SpaceClaim or Fluent window left from a previous run.
SolidWorks may stay open.

## If you are an AI agent setting up a machine

- Check part A with the commands above and report each as PRESENT or MISSING
  with the measured value. **Do not install, license or download A2, A3 or A4
  yourself**; they need the user's licence or account. Stop and list what is
  missing.
- You may run the part B `winget` command only with the user's approval.
- Always run step 2 (`-CheckOnly`) before step 3, and show the user its output.
- Never write a key, password or licence into the repo, a config template or a
  log. Keys are read from the environment variable named by `-ModelKeyEnv`.
- Do not edit `profile/environment.json`, the lock files or the SolidPilot pin to
  make a check pass; a mismatch is a finding to report.
- The machine is ready only when preflight ends with `0 FAIL`. Report the
  PASS / WARN / FAIL counts and every WARN.

Details and troubleshooting: `docs/SETUP.md`. Running with Claude:
`docs/RUN_WITH_CLAUDE.md`.
