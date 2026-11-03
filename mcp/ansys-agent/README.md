# ansys-agent MCP server (vendored)

The Ansys MCP server used by the SpaceClaim and Fluent stages, copied from the
author's `ansys-agent` project on 2026-11-02 (source only: no venv, jobs,
results, journals or the unrelated Kit-CAE viewer). It exposes 10 tools:
`run_ansys_script`, `submit_ansys_job`, `job_status`, `job_log`, `job_cancel`,
`job_list`, `read_json_file`, `list_case_results`, `read_skill_reference`,
`list_skill_reference_sheets` (inventory: `mcp/ansys-tools.json`).

| Item | Value |
|---|---|
| Entry point | `ansys_mcp_server.py` (stdio MCP) |
| Python | 3.11.9; exact packages in `requirements.lock.txt` (ansys-geometry-core 0.15.5, ansys-fluent-core 0.41.0, mcp 1.28.1) |
| Venv | created by `scripts/bootstrap_workstation.ps1` at `C:\brake-tools\ansys-agent-venv` (outside OneDrive and git) |
| Environment | `ANSYS_RUNTIME_DIR=C:/brake-runs/_ansys-runtime` (jobs, scripts, results; keeps mutable state out of the repo), `ANSYS_VENV_PYTHON=<venv python>`, `AWP_ROOT261=<Ansys v261 root>` |
| Ansys | 2026 R1 (v261); Student is fine |

`profile/config.template.yaml` (Hermes) and `profile/claude_mcp_servers.template.json`
(Claude Desktop / Cowork) register it; `scripts/install_profile.ps1` fills in
the paths.
