<#
.SYNOPSIS
  Render the Hermes "brake" profile for THIS workstation from profile/*.template.*

.DESCRIPTION
  Writes, in this order, and nothing else:
    1. <ProfileDir>\config.yaml   rendered from profile\config.template.yaml
    2. <ProfileDir>\SOUL.md       copied from profile\SOUL.md
    3. <package>\.local\servers.json  (diagnostic client config, git-ignored)
  Any existing config.yaml / SOUL.md is backed up first as *.backup-<timestamp>.
  Creates C:\brake-runs and C:\brake-runs\_ansys-runtime if they are missing.
  Every input path is checked before anything is written; on any miss it stops
  and writes nothing.

  Run "hermes profile create brake --clone" once before this script so the
  profile folder (and its provider credentials) exists.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\install_profile.ps1 -AnsysAgentRoot "D:\tools\ansys-agent"

.EXAMPLE
  # Render into a scratch folder to inspect it, touching no real profile
  powershell -ExecutionPolicy Bypass -File scripts\install_profile.ps1 -ProfileDir "$env:TEMP\brake-test" -CreateProfileDir
#>
[CmdletBinding()]
param(
    [string]$ProfileDir = "",
    [string]$AnsysAgentRoot = "",
    [string]$AwpRoot = "",
    [switch]$CreateProfileDir
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

function To-Fwd([string]$p) { return ([IO.Path]::GetFullPath($p)).TrimEnd('\', '/').Replace('\', '/') }
function Write-Utf8NoBom([string]$path, [string]$text) {
    $enc = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($path, $text, $enc)
}
function Sha256([string]$path) { return (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLower() }

$PackageRoot = Split-Path -Parent $PSScriptRoot
$SolidPilotRoot = 'C:\solidpilot'
$RunsRoot = 'C:\brake-runs'

# ---- resolve defaults ---------------------------------------------------------
if (-not $ProfileDir) {
    if ($env:HERMES_HOME -and (Split-Path -Leaf $env:HERMES_HOME) -eq 'brake') { $ProfileDir = $env:HERMES_HOME }
    else { $ProfileDir = Join-Path $env:LOCALAPPDATA 'hermes\profiles\brake' }
}
if (-not $AnsysAgentRoot) { $AnsysAgentRoot = Join-Path (Split-Path -Parent $PackageRoot) 'ansys-agent' }
if (-not $AwpRoot) {
    if ($env:AWP_ROOT261) { $AwpRoot = $env:AWP_ROOT261 }
    else { $AwpRoot = 'C:\Program Files\ANSYS Inc\ANSYS Student\v261' }
}

# ---- check every input before writing anything --------------------------------
$checks = @(
    @{ what = 'package template';        path = (Join-Path $PackageRoot 'profile\config.template.yaml') },
    @{ what = 'package SOUL';            path = (Join-Path $PackageRoot 'profile\SOUL.md') },
    @{ what = 'servers template';        path = (Join-Path $PackageRoot 'profile\servers.template.json') },
    @{ what = 'lead skills dir';         path = (Join-Path $PackageRoot 'agents\lead\skills') },
    @{ what = 'SolidPilot python';       path = (Join-Path $SolidPilotRoot '.venv\Scripts\python.exe') },
    @{ what = 'SolidPilot server';       path = (Join-Path $SolidPilotRoot 'adapters\claude\server.py') },
    @{ what = 'ansys-agent python';      path = (Join-Path $AnsysAgentRoot '.venv\Scripts\python.exe') },
    @{ what = 'ansys-agent server';      path = (Join-Path $AnsysAgentRoot 'ansys_mcp_server.py') },
    @{ what = 'Ansys v261 root';         path = $AwpRoot }
)
$missing = @()
foreach ($c in $checks) {
    if (Test-Path -LiteralPath $c.path) { Write-Host ("  ok       {0,-20} {1}" -f $c.what, $c.path) }
    else { Write-Host ("  MISSING  {0,-20} {1}" -f $c.what, $c.path) -ForegroundColor Red; $missing += $c.what }
}
if (-not (Test-Path -LiteralPath $ProfileDir)) {
    if ($CreateProfileDir) { New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null }
    else { Write-Host "  MISSING  profile dir           $ProfileDir  (run: hermes profile create brake --clone)" -ForegroundColor Red; $missing += 'profile dir' }
}
if ($missing.Count -gt 0) {
    Write-Host "STOP: $($missing.Count) input(s) missing: $($missing -join ', '). Nothing was written." -ForegroundColor Red
    exit 2
}

# ---- render -------------------------------------------------------------------
$values = @{
    '{{PACKAGE_ROOT}}'     = (To-Fwd $PackageRoot)
    '{{ANSYS_AGENT_ROOT}}' = (To-Fwd $AnsysAgentRoot)
    '{{AWP_ROOT261}}'      = (To-Fwd $AwpRoot)
}
function Render([string]$templatePath) {
    $text = [IO.File]::ReadAllText($templatePath)
    foreach ($k in $values.Keys) { $text = $text.Replace($k, $values[$k]) }
    $left = [regex]::Matches($text, '\{\{[A-Z0-9_]+\}\}')
    if ($left.Count -gt 0) { throw "Unresolved placeholder(s) in ${templatePath}: $(($left | ForEach-Object { $_.Value }) -join ', ')" }
    return $text
}
$config  = Render (Join-Path $PackageRoot 'profile\config.template.yaml')
$servers = Render (Join-Path $PackageRoot 'profile\servers.template.json')
$null = $servers | ConvertFrom-Json   # throws if the JSON is malformed

# ---- write --------------------------------------------------------------------
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
foreach ($name in @('config.yaml', 'SOUL.md')) {
    $dst = Join-Path $ProfileDir $name
    if (Test-Path -LiteralPath $dst) {
        $bak = Join-Path $ProfileDir ("{0}.backup-{1}{2}" -f [IO.Path]::GetFileNameWithoutExtension($name), $stamp, [IO.Path]::GetExtension($name))
        Copy-Item -LiteralPath $dst -Destination $bak
        Write-Host "  backup   $bak"
    }
}
$cfgPath  = Join-Path $ProfileDir 'config.yaml'
$soulPath = Join-Path $ProfileDir 'SOUL.md'
Write-Utf8NoBom $cfgPath $config
Copy-Item -LiteralPath (Join-Path $PackageRoot 'profile\SOUL.md') -Destination $soulPath -Force

$localDir = Join-Path $PackageRoot '.local'
New-Item -ItemType Directory -Force -Path $localDir | Out-Null
$srvPath = Join-Path $localDir 'servers.json'
if (Test-Path -LiteralPath $srvPath) {
    $bak = Join-Path $localDir "servers.backup-$stamp.json"
    Copy-Item -LiteralPath $srvPath -Destination $bak
    Write-Host "  backup   $bak"
}
Write-Utf8NoBom $srvPath $servers

foreach ($d in @($RunsRoot, (Join-Path $RunsRoot '_ansys-runtime'))) {
    if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null; Write-Host "  created  $d" }
}

# ---- report -------------------------------------------------------------------
Write-Host ""
Write-Host "Profile rendered for this workstation:"
foreach ($k in $values.Keys) { Write-Host ("  {0,-20} = {1}" -f $k, $values[$k]) }
Write-Host ("  config.yaml  sha256 {0}  {1}" -f (Sha256 $cfgPath), $cfgPath)
Write-Host ("  SOUL.md      sha256 {0}  {1}" -f (Sha256 $soulPath), $soulPath)
Write-Host ("  servers.json sha256 {0}  {1}" -f (Sha256 $srvPath), $srvPath)
Write-Host ""
Write-Host "Next: powershell -ExecutionPolicy Bypass -File scripts\preflight.ps1 -McpTest"
exit 0
