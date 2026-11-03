<#
.SYNOPSIS
  One-time setup of a NEW workstation: the two MCP servers this package drives.

.DESCRIPTION
  1. Checks prerequisites: git, Python 3.11 (via the py launcher), SOLIDWORKS 2026,
     Ansys v261, and MSBuild (Visual Studio 2022 or Build Tools 2022).
  2. SolidPilot -> C:\solidpilot : clone the pinned upstream commit (mcp/solidpilot/SOURCE.md),
     create .venv from mcp\solidpilot\requirements.lock.txt, write adapters\claude\.env,
     build the .NET execution service.
  3. ansys-agent -> venv at C:\brake-tools\ansys-agent-venv from
     mcp\ansys-agent\requirements.lock.txt (the server source stays in this package).
  4. Creates C:\brake-runs and C:\brake-runs\_ansys-runtime.
  It never deletes anything. An existing C:\solidpilot is verified, not replaced.
  -CheckOnly reports what would be done and changes nothing.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\bootstrap_workstation.ps1
  powershell -ExecutionPolicy Bypass -File scripts\bootstrap_workstation.ps1 -CheckOnly
#>
[CmdletBinding()]
param(
    [string]$Python = "",
    [string]$AwpRoot = "",
    [string]$AnsysVenv = "C:\brake-tools\ansys-agent-venv",
    [string]$SolidPilotBinFrom = "",
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'
$PackageRoot = Split-Path -Parent $PSScriptRoot
$SolidPilotRoot = 'C:\solidpilot'
$SolidPilotUrl = 'https://github.com/eyfel/mcp-server-solidworks.git'
$SolidPilotCommit = 'a81d12ba3752d6282c42a4922e87db8dc26b3f69'
$RunsRoot = 'C:\brake-runs'

function Invoke-Native([scriptblock]$Block, [switch]$Show) {
    $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try {
        $lines = @(& $Block 2>&1 | ForEach-Object { "$_" })
        if ($Show) { $lines | Select-Object -Last 15 | ForEach-Object { Write-Host "    $_" } }
        return @{ Code = $LASTEXITCODE; Text = ($lines -join "`n") }
    } finally { $ErrorActionPreference = $old }
}
function Step([string]$m) { Write-Host ""; Write-Host "== $m" -ForegroundColor Cyan }
function Ok([string]$m) { Write-Host "  ok    $m" }
function Todo([string]$m) { Write-Host "  TODO  $m" -ForegroundColor Yellow }
function Stop-Boot([string]$m) { Write-Host "STOP: $m" -ForegroundColor Red; exit 1 }

# ---- 1. prerequisites ---------------------------------------------------------------
Step 'Prerequisites'
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Stop-Boot 'git is not on PATH (winget install --id Git.Git).' }
Ok 'git'
if (-not $Python) {
    $r = Invoke-Native { & py -3.11 -c "import sys; print(sys.executable)" }
    if ($r.Code -ne 0) { Stop-Boot 'Python 3.11 not found via the py launcher. Install Python 3.11 (python.org) or pass -Python <path to python.exe>.' }
    $Python = ($r.Text -split "`n" | Select-Object -Last 1).Trim()
}
$r = Invoke-Native { & $Python --version }
if ($r.Text -notmatch '3\.11') { Stop-Boot "Python 3.11 required (the lock files were captured on 3.11.9); $Python reports: $($r.Text)" }
Ok "Python $($r.Text.Trim()) at $Python"

$swDir = $null
try { $swDir = (Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\SolidWorks\SOLIDWORKS 2026\Setup' -ErrorAction Stop).'SolidWorks Folder' } catch { }
if ($swDir) { Ok "SOLIDWORKS 2026 at $swDir" } else { Stop-Boot 'SOLIDWORKS 2026 not found (registry HKLM:\SOFTWARE\SolidWorks\SOLIDWORKS 2026\Setup).' }

if (-not $AwpRoot) { if ($env:AWP_ROOT261) { $AwpRoot = $env:AWP_ROOT261 } else { $AwpRoot = 'C:\Program Files\ANSYS Inc\ANSYS Student\v261' } }
if (Test-Path -LiteralPath (Join-Path $AwpRoot 'fluent\ntbin\win64\fluent.exe')) { Ok "Ansys v261 at $AwpRoot" }
else { Stop-Boot "Ansys 2026 R1 (v261) not found at $AwpRoot (pass -AwpRoot)." }

$msbuild = $null
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
if (Test-Path -LiteralPath $vswhere) {
    $r = Invoke-Native { & $vswhere -latest -products * -requires Microsoft.Component.MSBuild -find 'MSBuild\**\Bin\MSBuild.exe' }
    $cand = ($r.Text -split "`n" | Where-Object { $_ -match 'MSBuild\.exe$' } | Select-Object -First 1)
    if ($cand) { $msbuild = $cand.Trim() }
}
if ($msbuild) { Ok "MSBuild $msbuild" } else { Todo 'MSBuild not found (needed only if the SolidPilot execution service is not built yet)' }

# ---- 2. SolidPilot -------------------------------------------------------------------
Step "SolidPilot at $SolidPilotRoot (pinned $($SolidPilotCommit.Substring(0,8)))"
if (-not (Test-Path -LiteralPath $SolidPilotRoot)) {
    if ($CheckOnly) { Todo "clone $SolidPilotUrl -> $SolidPilotRoot and check out the pinned commit" }
    else {
        if ((Invoke-Native { & git clone $SolidPilotUrl $SolidPilotRoot } -Show).Code -ne 0) { Stop-Boot 'git clone of SolidPilot failed.' }
        if ((Invoke-Native { & git -C $SolidPilotRoot checkout --quiet $SolidPilotCommit } -Show).Code -ne 0) { Stop-Boot 'checkout of the pinned SolidPilot commit failed.' }
        Ok 'cloned and checked out'
    }
} else {
    $head = (Invoke-Native { & git -C $SolidPilotRoot rev-parse HEAD }).Text.Trim()
    if ($head -eq $SolidPilotCommit) { Ok "existing checkout at the pinned commit" }
    else { Todo "existing $SolidPilotRoot is at $head, not the pinned commit; tool schemas may differ (compare with mcp\solidpilot-tools.json). Left unchanged." }
}
$spPython = Join-Path $SolidPilotRoot '.venv\Scripts\python.exe'
if (Test-Path -LiteralPath $spPython) { Ok 'SolidPilot venv exists' }
elseif ($CheckOnly) { Todo "create $SolidPilotRoot\.venv and install mcp\solidpilot\requirements.lock.txt" }
else {
    if ((Invoke-Native { & $Python -m venv (Join-Path $SolidPilotRoot '.venv') } -Show).Code -ne 0) { Stop-Boot 'creating the SolidPilot venv failed.' }
    $lock = Join-Path $PackageRoot 'mcp\solidpilot\requirements.lock.txt'
    if ((Invoke-Native { & $spPython -m pip install --disable-pip-version-check -r $lock } -Show).Code -ne 0) { Stop-Boot 'pip install of the SolidPilot lock file failed.' }
    Ok 'SolidPilot venv installed from the lock file'
}
$envFile = Join-Path $SolidPilotRoot 'adapters\claude\.env'
if (Test-Path -LiteralPath $envFile) { Ok '.env exists' }
elseif ($CheckOnly) { Todo "write $envFile from mcp\solidpilot\env.template" }
elseif (Test-Path -LiteralPath (Join-Path $SolidPilotRoot 'adapters\claude')) { Copy-Item (Join-Path $PackageRoot 'mcp\solidpilot\env.template') $envFile; Ok '.env written' }

$exe = Join-Path $SolidPilotRoot 'execution\solidworks\SolidworksExecution\bin\Debug\SolidworksExecution.exe'
if (Test-Path -LiteralPath $exe) { Ok 'execution service already built' }
elseif ($CheckOnly) { Todo 'build the SolidPilot execution service (MSBuild) or pass -SolidPilotBinFrom <bin\Debug folder of another install>' }
elseif ($SolidPilotBinFrom) {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $exe) | Out-Null
    Copy-Item -Path (Join-Path $SolidPilotBinFrom '*') -Destination (Split-Path -Parent $exe) -Recurse
    if (Test-Path -LiteralPath $exe) { Ok "execution service copied from $SolidPilotBinFrom" } else { Stop-Boot "no SolidworksExecution.exe in $SolidPilotBinFrom" }
}
elseif ($msbuild) {
    $sln = Join-Path $SolidPilotRoot 'execution\solidworks\SolidworksExecution.sln'
    if ((Invoke-Native { & $msbuild $sln /t:Restore /p:Configuration=Debug /nologo /v:minimal } -Show).Code -ne 0) { Todo 'NuGet restore reported errors; trying the build anyway' }
    if ((Invoke-Native { & $msbuild $sln /t:Build /p:Configuration=Debug /nologo /v:minimal } -Show).Code -ne 0) { Stop-Boot 'MSBuild of the SolidPilot execution service failed (needs the .NET Framework 4.8 targeting pack).' }
    if (Test-Path -LiteralPath $exe) { Ok 'execution service built' } else { Stop-Boot 'build reported success but SolidworksExecution.exe is missing.' }
}
else { Stop-Boot 'the SolidPilot execution service is not built and MSBuild was not found. Install "Visual Studio Build Tools 2022" with the .NET desktop build tools (and .NET Framework 4.8 targeting pack), or pass -SolidPilotBinFrom.' }

# ---- 3. ansys-agent venv ---------------------------------------------------------------
Step "ansys-agent venv at $AnsysVenv"
$aaPython = Join-Path $AnsysVenv 'Scripts\python.exe'
if (Test-Path -LiteralPath $aaPython) { Ok 'venv exists (not reinstalled)' }
elseif ($CheckOnly) { Todo "create $AnsysVenv and install mcp\ansys-agent\requirements.lock.txt (several hundred MB)" }
else {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $AnsysVenv) | Out-Null
    if ((Invoke-Native { & $Python -m venv $AnsysVenv } -Show).Code -ne 0) { Stop-Boot 'creating the ansys-agent venv failed.' }
    $lock = Join-Path $PackageRoot 'mcp\ansys-agent\requirements.lock.txt'
    if ((Invoke-Native { & $aaPython -m pip install --disable-pip-version-check -r $lock } -Show).Code -ne 0) { Stop-Boot 'pip install of the ansys-agent lock file failed.' }
    Ok 'ansys-agent venv installed from the lock file'
}

# ---- 4. run folders --------------------------------------------------------------------
Step 'Run folders'
foreach ($d in @($RunsRoot, (Join-Path $RunsRoot '_ansys-runtime'))) {
    if (Test-Path -LiteralPath $d) { Ok "$d exists" }
    elseif ($CheckOnly) { Todo "create $d" }
    else { New-Item -ItemType Directory -Force -Path $d | Out-Null; Ok "created $d" }
}

Write-Host ""
Write-Host "Next:" -ForegroundColor Cyan
Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\install_profile.ps1 -AnsysAgentPython `"$aaPython`""
Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\preflight.ps1 -McpTest"
Write-Host "  (Claude Desktop / Cowork: register the servers from .local\claude_mcp_servers.json; see docs\RUN_WITH_CLAUDE.md)"
exit 0
