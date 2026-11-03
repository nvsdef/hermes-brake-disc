# Hermes brake-disc

A fictional brake-disc engineering demo. One Hermes **lead** delegates to three
specialist subagents, one per application:

1. **solidworks-engineer** builds and assembles 9 parts (28 bodies) once in
   SolidWorks through the SolidPilot MCP.
2. **spaceclaim-engineer** runs `scripts/stages/spaceclaim_prep.py`: deletes the
   calliper, names bodies and faces, exports a PMDB (about 1 min).
3. **fluent-engineer** runs `scripts/stages/fluent_fast.py`: coarse mesh and the
   first second of the braking stop, leaving Fluent open on the temperature
   contour (about 2 min).

The lead derives the duty cycle, checks every gate against measured numbers and
ends with a gate summary. No report and no images (PRD section 6A, fast run
profile).

**Status (revision H1.2, 2026-11-02):**
- `specs/PRD.md` is the single authority, with independently computed checksums
  for every body.
- Run 1 (H1.1 profile) built all 28 CAD bodies to the checksums but stalled in
  SpaceClaim. H1.2 fixes those failures and descopes 2D drawings. See
  `docs/VALIDATION.md`.
- The package is portable: the Hermes profile is rendered per workstation from
  `profile/`, and `scripts/preflight.ps1` checks a machine against the pinned
  environment. On 2026-11-02 it passed 29/29 checks against a freshly rendered
  profile, with live MCP connections. **H1.2 has not yet been run end to end.**

## Layout
| Path | What |
|---|---|
| `AGENTS.md` | Loaded into the lead **and every subagent**. Role table, ownership, evidence rules. |
| `specs/PRD.md` | Geometry, checksums, duty cycle, analysis, requirements, deliverables. The only authority. |
| `specs/handoffs.md` | Gate-by-gate artifact contracts and JSON keys. |
| `agents/<role>/SOUL.md` | Each agent's identity and habits. A child reads it itself, because Hermes doesn't inject it. |
| `agents/<role>/skills/*` | Role skills: detailed guidance, traps and checks, with `references/` loaded on demand. |
| `agents/_shared/skills/brake-handoff` | The cross-stage contract, loaded by the lead. |
| `profile/config.template.yaml` | The complete `brake` profile `config.yaml`, with 3 machine placeholders. |
| `profile/SOUL.md` | The lead's profile SOUL (system prompt; survives compaction). |
| `profile/environment.json` | Pinned versions, paths and tool counts that preflight checks. |
| `mcp/*-tools.json` | Tool inventories (names and argument schemas) of the SolidPilot (46) and Ansys (10) servers. |
| `scripts/stages/*.py` | The two vetted stage scripts (SpaceClaim prep, Fluent mesh + heat-up), launched by their specialist. |
| `scripts/install_profile.ps1` | Renders the profile for this workstation. |
| `scripts/preflight.ps1` | Read-only machine check: PASS/WARN/FAIL per item. |
| `scripts/publish_github.ps1` | Pushes to a private GitHub repo after safety checks. |
| `scripts/mcp_client.py` | Diagnostic MCP client (not the run path). |
| `examples/prompt.md` | The 3-line run prompt. |
| `examples/readiness-prompt.md` | A check that all four roles start with their tools and skills. |
| `docs/SETUP.md` | Step-by-step setup and launch. |
| `docs/SKILL_STYLE.md` | Rules for writing skills in this package. |
| `docs/DECISIONS.md` | Why H1/H1.1/H1.2 differ from the CTS and the predecessor. |
| `docs/source/` | The original CTS. Background only. |

## Quick start (any workstation)
```powershell
gh repo clone <owner>/hermes-brake-disc; cd hermes-brake-disc
hermes profile create brake --clone            # once per machine
powershell -ExecutionPolicy Bypass -File scripts\install_profile.ps1 -AnsysAgentRoot "<path>\ansys-agent"
powershell -ExecutionPolicy Bypass -File scripts\preflight.ps1 -McpTest   # must end "0 FAIL"
hermes -p brake chat                           # from this folder, no -t flag
```
Then paste `examples/readiness-prompt.md`, then `examples/prompt.md`. Details
and prerequisites are in `docs/SETUP.md`.

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
