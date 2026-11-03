# SolidPilot MCP - pinned, not vendored

SolidPilot (the SolidWorks MCP server) is third-party code under **AGPL-3.0**:
<https://github.com/eyfel/mcp-server-solidworks>. This package does not copy it.
`scripts/bootstrap_workstation.ps1` clones it to **`C:\solidpilot`** (the skills
call `C:/solidpilot/.venv/Scripts/python.exe`, so the path is fixed) at the
commit below, builds its .NET execution service, and installs the Python venv
from `requirements.lock.txt`.

| Item | Value |
|---|---|
| Upstream | `https://github.com/eyfel/mcp-server-solidworks.git` |
| Commit | `a81d12ba3752d6282c42a4922e87db8dc26b3f69` ("chore: ignore the local test/ scratch folder") |
| Local changes on the author's machine | none (verified 2026-11-02 with CRLF normalisation; the only untracked file is `adapters/claude/.env`) |
| Python | 3.11.9, packages in `requirements.lock.txt` (`mcp==2.0.0`) |
| Execution service | `execution\solidworks\SolidworksExecution.sln`, .NET Framework 4.8, built with MSBuild (Visual Studio 2022 or Build Tools 2022). It references the SolidWorks interop assembly from the local SolidWorks install, which is why no binaries are shipped here |
| `.env` | `adapters\claude\.env` from `env.template` (two timeouts, no secrets) |
| Tools | 46 (`mcp/solidpilot-tools.json`); the H1.2 profile allows 17 |

`ensure_ready` starts `SolidworksExecution.exe` (http://localhost:5000) and
SolidWorks if they are not running.
