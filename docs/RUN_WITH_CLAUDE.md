# Running the package with Claude (Cowork / Claude Desktop)

Runs 3 and 4 (2026-11-02, `docs/VALIDATION.md`) were driven this way: Claude as
the lead, one Claude sub-agent per application, the same SOULs, skills, stage
scripts and gates as the Hermes path. Run 4 took 12.3 min end to end.

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

1. Close any SpaceClaim or Fluent window (the Student licence allows one
   session; a Fluent window left open by the previous run holds it). SolidWorks
   may stay open.
2. Open a Cowork session on this package folder and give it access to
   `C:\brake-runs`.
3. Paste `examples/prompt-claude.md`.

The lead then follows `agents/lead/skills/brake-lead-run/SKILL.md`: Gate 0 itself,
then one sub-agent per gate from the briefs in
`agents/lead/skills/brake-lead-run/references/commission-templates.md` (B1, B2,
B3) plus the harness notes below, checking every gate's JSON itself.

## 3. Harness notes the lead adds to every brief

- MCP tools are deferred in Claude: load them first with one ToolSearch call
  (`select:mcp__solidpilot__...` for the 17 allowed SolidPilot tools;
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

## 4. Expected timing (run 4)

| Gate | Time |
|---|---|
| 0 duty cycle (lead) | under 1 min |
| 1 CAD, 6 parts + 3 flipped instances (agent, SolidPilot) | about 5.5 min, about 105 calls |
| 2 SpaceClaim prep (stage script) | about 1.5 min |
| 3 Fluent mesh + full stop (stage script) | about 3.7 min |
| lead checks | about 1 min |
| **total** | **about 12 min** |
