# Hermes brake-disc

A fictional brake-disc engineering demo. One Hermes **lead** delegates to three
specialist subagents, one per application:

1. **solidworks-engineer** builds and assembles 9 parts (28 bodies) once in
   SolidWorks through the SolidPilot MCP.
2. **spaceclaim-engineer** runs `scripts/stages/spaceclaim_prep.py`: deletes the
   calliper, names bodies and faces, exports a PMDB (about 1 min).
3. **fluent-engineer** runs `scripts/stages/fluent_fast.py`: coarse mesh and the
   whole braking stop (3.54 s), leaving Fluent open on the temperature contour
   (about 4 min).

The lead derives the duty cycle, checks every gate against measured numbers and
ends with a gate summary. No report and no images (PRD section 6A, fast run
profile).

## What you need

Full list, checks and setup order for people and agents: **`REQUIREMENTS.md`**.

- **You install (licensed, not in this repo):** SOLIDWORKS 2026, Ansys 2026 R1
  (v261, Student is fine), Hermes or Claude Desktop/Cowork, and a model endpoint
  with its API key in an environment variable.
- **One `winget` command:** Git, Python 3.11, VS 2022 Build Tools (MSBuild).
- **Installed from this repo** by `scripts/bootstrap_workstation.ps1`: the
  SolidPilot MCP (SolidWorks; pinned upstream commit) and the ansys-agent MCP
  (SpaceClaim and Fluent; vendored source), each from exact lock files.
- **Ready when** `scripts/preflight.ps1 -McpTest` ends with `0 FAIL`.

**Status (revision H1.2, updated 2026-11-25):**
- `specs/PRD.md` is the single authority, with independently computed checksums
  for every body.
- Run 1 (H1.1 profile) built all 28 CAD bodies to the checksums but stalled in
  SpaceClaim. H1.2 fixes those failures and descopes 2D drawings. See
  `docs/VALIDATION.md`.
- The package is portable: the Hermes profile is rendered per workstation from
  `profile/`, and `scripts/preflight.ps1` checks a machine against the pinned
  environment. On 2026-11-02 it passed 29/29 checks against a freshly rendered
  profile, with live MCP connections.
- **Reference run: run 7, 2026-11-25** (Claude agents, SpaceClaim and Fluent
  pre-opened during the CAD build): all gates PASS first time, no repairs, in
  **13.5 min** (CAD 7.6, SpaceClaim 0.9, Fluent 4.2, handoffs and checks the
  rest); 283k sub-agent tokens measured. Runs 4 to 7 all passed (12.3 to 15.0
  min). Not yet run under Hermes.
- **Self-contained:** both MCP servers install from this repo
  (`scripts/bootstrap_workstation.ps1`), see `docs/SETUP.md` section 1.

## Layout
| Path | What |
|---|---|
| `REQUIREMENTS.md` | What a new workstation needs, how to check each item, setup order (for people and agents). |
| `AGENTS.md` | Loaded into the lead **and every subagent**. Role table, ownership, evidence rules. |
| `specs/PRD.md` | Geometry, checksums, duty cycle, analysis, requirements, deliverables. The only authority. |
| `specs/handoffs.md` | Gate-by-gate artifact contracts and JSON keys. |
| `agents/<role>/SOUL.md` | Each agent's identity and habits. A child reads it itself, because Hermes doesn't inject it. |
| `agents/<role>/skills/*` | Role skills: detailed guidance, traps and checks, with `references/` loaded on demand. |
| `agents/_shared/skills/brake-handoff` | The cross-stage contract, loaded by the lead. |
| `profile/config.template.yaml` | The complete `brake` profile `config.yaml`, with 3 machine placeholders. |
| `profile/SOUL.md` | The lead's profile SOUL (system prompt; survives compaction). |
| `profile/environment.json` | Pinned versions, paths and tool counts that preflight checks. |
| `mcp/ansys-agent/` | The Ansys MCP server (vendored source + `requirements.lock.txt`). |
| `mcp/solidpilot/` | SolidPilot pin (`SOURCE.md`: upstream + commit), `requirements.lock.txt`, `.env` template. |
| `mcp/*-tools.json` | Tool inventories (names and argument schemas) of the SolidPilot (46) and Ansys (10) servers. |
| `profile/claude_mcp_servers.template.json` | MCP registration for Claude Desktop / Cowork. |
| `scripts/bootstrap_workstation.ps1` | New machine: installs both MCP servers from the pins and locks. |
| `docs/RUN_WITH_CLAUDE.md`, `examples/prompt-claude.md` | Running with Claude as the lead (how runs 3 to 7 ran). |
| `scripts/stages/*.py` | The two vetted stage scripts (SpaceClaim prep, Fluent mesh + heat-up), launched by their specialist. |
| `scripts/install_profile.ps1` | Renders the profile for this workstation. |
| `scripts/preflight.ps1` | Read-only machine check: PASS/WARN/FAIL per item. |
| `scripts/publish_github.ps1` | Pushes to GitHub (public by default) after safety checks. |
| `scripts/mcp_client.py` | Diagnostic MCP client (not the run path). |
| `examples/prompt.md` | The 3-line run prompt. |
| `examples/readiness-prompt.md` | A check that all four roles start with their tools and skills. |
| `docs/SETUP.md` | Step-by-step setup and launch. |
| `docs/SKILL_STYLE.md` | Rules for writing skills in this package. |
| `docs/DECISIONS.md` | Why H1/H1.1/H1.2 differ from the CTS and the predecessor. |
| `docs/source/` | The original CTS. Background only. |

## Quick start (any workstation)
```powershell
git clone https://github.com/nvsdef/hermes-brake-disc.git; cd hermes-brake-disc
powershell -ExecutionPolicy Bypass -File scripts\bootstrap_workstation.ps1   # SolidPilot + ansys-agent MCPs
hermes profile create brake --clone                                            # Hermes only, once
powershell -ExecutionPolicy Bypass -File scripts\install_profile.ps1
powershell -ExecutionPolicy Bypass -File scripts\preflight.ps1 -McpTest       # must end "0 FAIL"
```
Then either `hermes -p brake chat` from this folder and paste `examples/prompt.md`,
or open Claude Cowork on this folder and paste `examples/prompt-claude.md`
(`docs/RUN_WITH_CLAUDE.md`). Prerequisites: `REQUIREMENTS.md`; details: `docs/SETUP.md`.

Run output goes to `C:\brake-runs\<run-id>\`. Tests:
`C:/solidpilot/.venv/Scripts/python.exe -B -m unittest discover -s tests -v`.

## Scope
The model is the FR-330V vented rotor, pads, backing plates and a clearance
calliper, analysed as single-stop transient solid conduction with prescribed
convection.

Two items are deferred, with report rows but no geometry or model:
- Cross-drilling (GEO-05).
- Calliper and fluid temperature (THM-06).

This is a teaching case, not a certified brake.
