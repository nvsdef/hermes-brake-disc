# Running the package with Claude (Cowork / Claude Desktop)

Runs 3 and 4 (2026-11-02, `docs/VALIDATION.md`) were driven this way: Claude as
the lead, one Claude sub-agent per application, the same SOULs, skills, stage
scripts and gates as the Hermes path. Run 7 (the reference run, 2026-11-25) took
13.5 min end to end.

## 1. One-time setup (after `docs/SETUP.md` section 1, steps 1 to 3)

1. `scripts\bootstrap_workstation.ps1` has installed SolidPilot (`C:\solidpilot`)
   and the ansys-agent venv (`C:\brake-tools\ansys-agent-venv`).
2. `scripts\install_profile.ps1` has written `.local\claude_mcp_servers.json`.
3. Register the two servers. **Claude Desktop:** merge the `mcpServers` block of
   `.local\claude_mcp_servers.json` into
   `%APPDATA%\Claude\claude_desktop_config.json` and restart. **Cowork:** add the
   same two servers (name, command, args, cwd, env) in the MCP server settings and
   restart. The server names must be `solidpilot` and `ansys-agent`.
4. Check: ask "What solidpilot and ansys-agent tools do you see?" Expect 46 and
   10 (`mcp/solidpilot-tools.json`, `mcp/ansys-tools.json`).

## 2. Each run

1. Close any SpaceClaim or Fluent window left from a previous run (the Fluent
   window each run leaves open, for example): pre-opening is skipped and the
   stage scripts block on an unknown session. SolidWorks may stay open.
2. Open a Cowork session on this package folder and give it access to
   `C:\brake-runs`.
3. Paste `examples/prompt-claude.md`.

The lead then follows `agents/lead/skills/brake-lead-run/SKILL.md`: Gate 0 itself,
then one sub-agent per gate from the briefs in
`agents/lead/skills/brake-lead-run/references/commission-templates.md` (B1, B2,
B3) plus the harness notes below, checking every gate's JSON itself.

## 3. Harness notes the lead adds to every brief

- MCP tools are deferred in Claude: load them first with one ToolSearch call
  (`select:mcp__solidpilot__...` for the 17 allowed SolidPilot tools, plus
  `mcp__ansys-agent__submit_ansys_job` for the CAD child's pre-open launch;
  `select:mcp__ansys-agent__submit_ansys_job,mcp__ansys-agent__job_status` for
  the Ansys stages).
- The Ansys server is named `ansys-agent` (Hermes calls it `ansys`); match tools
  on the bare name.
- No Windows terminal: hashing, JSON checks and STEP text counts run in the
  sandbox `python3` on the mounted `C:\brake-runs`.
- The CAD child may close documents left open by an earlier run of this project
  once, with `close_document(close_all=true, save=false)`.
- Children read only their SOUL and skill (and the data cards for CAD); the
  brief carries the gate numbers, so they need not read the PRD.

## 4. Expected timing (run 7, 2026-11-25, FR330V-20261125-1513)

| Step | Clock | Time |
|---|---|---|
| 0 duty cycle (lead) | 15:13:23 | under 1 min |
| 1 CAD, 6 parts + 3 flipped instances (agent, SolidPilot, 102 calls); SpaceClaim and Fluent pre-open in the background (ready 15:15:36 / 15:15:48) | 15:14:01 to 15:21:00 | 7.6 min (STEP written at 15:18:41) |
| lead check G1, commission G2 | | about 40 s |
| 2 SpaceClaim prep (stage script, pre-opened) | 15:21:42 to 15:22:08 | 26 s |
| handoff to G3 | | about 40 s |
| 3 Fluent mesh + full stop (stage script, pre-opened) | 15:22:47 to 15:26:32 | 3.7 min |
| lead final check | 15:26:53 | |
| **total** | | **13.5 min** |

SpaceClaim sits open and idle from about 15:16 until Gate 2 starts: that is
expected. About 4 min of the total is handoffs (the CAD agent writing its
report after the export, gate checks, child start-up). Sub-agent tokens
(measured): G1 158 010, G2 61 847, G3 63 467.
