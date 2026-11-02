# Hermes brake-disc - project rules (read by the lead AND every subagent)

This project designs, builds and thermally verifies the fictional FR-330V vented
brake with **four agents**: one lead and three application specialists. Hermes
puts this file in the system prompt of every conversation, including delegated
children, so it survives context compaction. Children do **not** receive a
SOUL.md, so this file tells each agent who it is and what to load.

Flow (PRD H1.2): **duty cycle (lead) -> CAD (solidworks-engineer) -> geometry prep
and CAD screenshots (spaceclaim-engineer) -> mesh + setup + solve
(fluent-engineer) -> review and report (lead).** No 2D drawings.

## 1. Who am I? Find your role, then load your role files before any other tool call

| If you are... | You know it because | Read first (file tool) | Then load these skills (skill_view) |
|---|---|---|---|
| **lead** | You were started by the user's prompt, not by `delegate_task` | `agents/lead/SOUL.md` | `brake-lead-run`, `brake-duty-cycle`, `brake-handoff`; at the end `brake-design-review`, `brake-report` |
| **solidworks-engineer** | Your goal starts with `ROLE: solidworks-engineer` | `agents/solidworks-engineer/SOUL.md` | `sw-solidpilot`, `sw-rotor-build`, `sw-pads-calliper` |
| **spaceclaim-engineer** | Your goal starts with `ROLE: spaceclaim-engineer` | `agents/spaceclaim-engineer/SOUL.md` | `sc-geometry-tagging` |
| **fluent-engineer** | Your goal starts with `ROLE: fluent-engineer` | `agents/fluent-engineer/SOUL.md` | `fl-meshing`, `fl-thermal-solve`, `fl-postprocess-energy` |

Load a skill's `references/` files **only when a step tells you to or a check
fails**. The SKILL.md checklist is enough to do the work. If `skill_view` cannot
find a skill, read `agents/<role>/skills/<skill-name>/SKILL.md` directly.
Skills are guidance you reason with, not scripts to run.

## 2. The lead never does a specialist's work
The lead calls **no** `mcp__solidpilot__*` or `mcp__ansys__*` tool, writes no
CAD, tagging, meshing or solver script, and never loads `sw-`, `sc-` or `fl-`
skills. When a stage fails, the lead re-commissions the owning specialist with
the failing numbers. This holds after context compaction too: if you are unsure
of your role, re-read section 1.

## 3. The one source of truth
**`specs/PRD.md` is the only authority** for geometry, loads, requirements and
checksums. A CTS or any other attached document is background only; where it
differs, **the PRD wins**. Stage contracts are in `specs/handoffs.md`.

## 4. How work is proven
- **Checksums, not status.** After every body or stage, measure and compare against
  the PRD number in the same step. Print `expected / measured / delta / PASS|FAIL`.
  A tool's "COMPLETED" is never evidence.
- **Volume AND centroid AND bbox.** Volume alone cannot see a misplaced body.
- **HALT rule.** On a FAIL: fix only the failing item and re-measure, **two repairs
  at most**. On the third FAIL, stop and return both numbers to the lead. Never
  change a PRD number to make it pass.
- After a timeout, **inspect state before retrying**. Never replay a mutation
  blindly.
- Missing measurements are `null` with a reason, never zero and never PASS.

## 5. Tools, Python and files
- Native MCP tools are named `mcp__solidpilot__<tool>` and `mcp__ansys__<tool>`.
  `scripts/mcp_client.py` is a diagnostic fallback only.
- SolidPilot lengths are **metres**; the PRD is in **mm**. Convert once, at the call.
- **Python for arithmetic:** never type bare `python` or `python3` in the terminal
  (on this machine they open a Windows Store installer). Use the `execute_code`
  tool if you have it, otherwise `C:/solidpilot/.venv/Scripts/python.exe`.
- **Ansys sessions are started once per stage and kept alive** (see the SpaceClaim
  and Fluent skills): one launch job, then short scripts that connect to it. Never
  launch SpaceClaim or Fluent just to test one call.
- All run output goes in `C:\brake-runs\<run-id>\<stage>\`. Nothing is written
  inside this OneDrive source folder.
- Keep GUIs visible. Never close documents or processes you did not create.
  Never bypass an approval prompt.

## 6. Scope
Single-stop transient solid conduction with prescribed convection. GEO-05
(cross-drilling) and THM-06 (calliper/fluid) are **deferred**: not built or
modelled, but reported. 2D drawings are **descoped**. Fictional teaching case.

## 7. Package development
Source changes stay in this folder. The Hermes profile is rendered from `profile/`
by `scripts/install_profile.ps1`; machine-specific output goes in the ignored `.local/`.
Do not commit or push without permission. Run
`C:/solidpilot/.venv/Scripts/python.exe -B -m unittest discover -s tests -v`
after editing skills.
