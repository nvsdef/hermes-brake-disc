<#
.SYNOPSIS
  Read-only workstation check against profile\environment.json (PRD H1.2).

.DESCRIPTION
  Prints one row per check: PASS, WARN or FAIL, with expected and measured values.
  Exit code 0 = no FAIL, 1 = at least one FAIL.
  It writes nothing except a temporary probe script in %TEMP% (deleted after use).
  It does not launch SolidWorks, SpaceClaim or Fluent.
  -McpTest also runs "hermes -p brake mcp test solidpilot|ansys", which starts each
  MCP server process just long enough to list its tools.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\preflight.ps1
  powershell -ExecutionPolicy Bypass -File scripts\preflight.ps1 -McpTest
#>
[CmdletBinding()]
param(
    [string]$ProfileDir = "",
    [string]$AnsysAgentRoot = "",
    [string]$AwpRoot = "",
    [switch]$McpTest,
    [switch]$SkipUnitTests
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$PackageRoot = Split-Path -Parent $PSScriptRoot
$envSpec = Get-Content -Raw -LiteralPath (Join-Path $PackageRoot 'profile\environment.json') | ConvertFrom-Json
$SolidPilotRoot = $envSpec.conventions.solidpilot_root.Replace('/', '\')
$RunsRoot = $envSpec.conventions.runs_root.Replace('/', '\')

if (-not $ProfileDir) {
    if ($env:HERMES_HOME -and (Split-Path -Leaf $env:HERMES_HOME) -eq 'brake') { $ProfileDir = $env:HERMES_HOME }
    else { $ProfileDir = Join-Path $env:LOCALAPPDATA 'hermes\profiles\brake' }
}
if (-not $AnsysAgentRoot) { $AnsysAgentRoot = Join-Path (Split-Path -Parent $PackageRoot) 'ansys-agent' }
if (-not $AwpRoot) {
    if ($env:AWP_ROOT261) { $AwpRoot = $env:AWP_ROOT261 } else { $AwpRoot = $envSpec.ansys.awp_root_default.Replace('/', '\') }
}

$rows = New-Object System.Collections.ArrayList
function Add-Row([string]$status, [string]$check, [string]$expected, [string]$measured) {
    [void]$rows.Add([pscustomobject]@{ Status = $status; Check = $check; Expected = $expected; Measured = $measured })
}
function Check-Path([string]$check, [string]$path, [string]$failStatus = 'FAIL') {
    if (Test-Path -LiteralPath $path) { Add-Row 'PASS' $check 'exists' $path } else { Add-Row $failStatus $check 'exists' "missing: $path" }
}
function Sha256([string]$path) { return (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLower() }
# Native commands write progress to stderr; under Windows PowerShell 5.1 with
# ErrorActionPreference=Stop that stderr becomes a terminating error. Run them here.
function Invoke-Native([scriptblock]$Block) {
    $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { $text = (& $Block 2>&1 | ForEach-Object { "$_" }) -join "`n"; return @{ Code = $LASTEXITCODE; Text = $text } }
    finally { $ErrorActionPreference = $old }
}

# 1. Package --------------------------------------------------------------------
foreach ($rel in @('AGENTS.md', 'specs\PRD.md', 'specs\handoffs.md', 'profile\config.template.yaml', 'profile\SOUL.md', 'mcp\solidpilot-tools.json', 'mcp\ansys-tools.json')) {
    Check-Path "package: $rel" (Join-Path $PackageRoot $rel)
}
$skillCount = @(Get-ChildItem -Path (Join-Path $PackageRoot 'agents') -Recurse -Filter 'SKILL.md').Count
if ($skillCount -eq 8) { Add-Row 'PASS' 'package: SKILL.md count' '8' "$skillCount" } else { Add-Row 'FAIL' 'package: SKILL.md count' '8' "$skillCount" }
foreach ($rel in @('scripts\stages\spaceclaim_prep.py', 'scripts\stages\fluent_fast.py')) { Check-Path "package: $rel" (Join-Path $PackageRoot $rel) }

# 2. SolidWorks + SolidPilot ----------------------------------------------------
$swKey = 'HKLM:\SOFTWARE\SolidWorks\SOLIDWORKS 2026\Setup'
$swDir = $null
try { $swDir = (Get-ItemProperty -LiteralPath $swKey -ErrorAction Stop).'SolidWorks Folder' } catch { }
if ($swDir -and (Test-Path -LiteralPath (Join-Path $swDir 'SLDWORKS.exe'))) {
    $ver = (Get-Item -LiteralPath (Join-Path $swDir 'SLDWORKS.exe')).VersionInfo.ProductVersion
    Add-Row 'PASS' 'SolidWorks 2026 installed' $envSpec.solidworks.product "$swDir (file version $ver)"
} else { Add-Row 'FAIL' 'SolidWorks 2026 installed' "registry $swKey" 'not found' }
Check-Path 'SolidPilot python' (Join-Path $SolidPilotRoot '.venv\Scripts\python.exe')
Check-Path 'SolidPilot server' (Join-Path $SolidPilotRoot 'adapters\claude\server.py')
$spHeadFile = Join-Path $SolidPilotRoot '.git\HEAD'
if (Test-Path -LiteralPath $spHeadFile) {
    $ref = (Get-Content -Raw -LiteralPath $spHeadFile).Trim()
    $sha = $ref
    if ($ref.StartsWith('ref: ')) { $rp = Join-Path $SolidPilotRoot ('.git\' + $ref.Substring(5).Replace('/', '\')); if (Test-Path -LiteralPath $rp) { $sha = (Get-Content -Raw -LiteralPath $rp).Trim() } }
    if ($sha -eq $envSpec.solidpilot.observed_source_head) { Add-Row 'PASS' 'SolidPilot source commit' $envSpec.solidpilot.observed_source_head $sha }
    else { Add-Row 'WARN' 'SolidPilot source commit' $envSpec.solidpilot.observed_source_head "$sha (tool schemas may differ: re-check mcp\solidpilot-tools.json)" }
} else { Add-Row 'WARN' 'SolidPilot source commit' $envSpec.solidpilot.observed_source_head 'no .git folder; cannot compare' }

# 3. Ansys + ansys-agent --------------------------------------------------------
Check-Path 'Ansys v261 root' $AwpRoot
foreach ($p in $envSpec.ansys.executables.PSObject.Properties) { Check-Path "Ansys $($p.Name) executable" (Join-Path $AwpRoot $p.Value.Replace('/', '\')) }
$aaPy = Join-Path $AnsysAgentRoot '.venv\Scripts\python.exe'
Check-Path 'ansys-agent python' $aaPy
Check-Path 'ansys-agent server' (Join-Path $AnsysAgentRoot 'ansys_mcp_server.py')
if (Test-Path -LiteralPath $aaPy) {
    $probe = Join-Path $env:TEMP ("brake_preflight_{0}.py" -f [guid]::NewGuid().ToString('N'))
    $names = @($envSpec.ansys_agent.required_packages.PSObject.Properties | ForEach-Object { $_.Name })
    $py = "import json, sys, importlib.metadata as m`nout = {'python': sys.version.split()[0]}`nfor n in $(ConvertTo-Json -Compress -InputObject $names):`n    try: out[n] = m.version(n)`n    except Exception: out[n] = None`nprint(json.dumps(out))"
    [IO.File]::WriteAllText($probe, $py, (New-Object System.Text.UTF8Encoding($false)))
    try {
        $res = Invoke-Native { & $aaPy -I $probe }
        if ($res.Code -ne 0) { throw "probe exit $($res.Code): $($res.Text)" }
        $got = ($res.Text -split "`n" | Where-Object { $_.Trim().StartsWith('{') } | Select-Object -Last 1) | ConvertFrom-Json
        if ($got.python -eq $envSpec.ansys_agent.observed_python) { Add-Row 'PASS' 'ansys-agent Python' $envSpec.ansys_agent.observed_python $got.python }
        else { Add-Row 'WARN' 'ansys-agent Python' $envSpec.ansys_agent.observed_python $got.python }
        foreach ($p in $envSpec.ansys_agent.required_packages.PSObject.Properties) {
            $have = $got.($p.Name)
            if ($have -eq $p.Value) { Add-Row 'PASS' "pin $($p.Name)" $p.Value $have }
            else { Add-Row 'FAIL' "pin $($p.Name)" $p.Value "$have (api-verified.md sheets were built against the pinned version)" }
        }
    } catch { Add-Row 'FAIL' 'ansys-agent package probe' 'JSON from probe' "error: $($_.Exception.Message)" }
    finally { Remove-Item -LiteralPath $probe -ErrorAction SilentlyContinue }
}

# 4. Run folder -----------------------------------------------------------------
if (Test-Path -LiteralPath $RunsRoot) {
    if ($RunsRoot -match 'OneDrive') { Add-Row 'FAIL' 'run folder not in OneDrive' $RunsRoot 'path contains OneDrive' } else { Add-Row 'PASS' 'run folder exists, not in OneDrive' $RunsRoot $RunsRoot }
    $probeFile = Join-Path $RunsRoot ('.preflight_' + [guid]::NewGuid().ToString('N'))
    try { [IO.File]::WriteAllText($probeFile, 'x'); Remove-Item -LiteralPath $probeFile; Add-Row 'PASS' 'run folder writable' 'writable' 'writable' }
    catch { Add-Row 'FAIL' 'run folder writable' 'writable' $_.Exception.Message }
} else { Add-Row 'FAIL' 'run folder exists' $RunsRoot 'missing (install_profile.ps1 creates it)' }

# 5. Hermes profile -------------------------------------------------------------
$hermes = Get-Command hermes -ErrorAction SilentlyContinue
if ($hermes) { Add-Row 'PASS' 'hermes on PATH' 'found' $hermes.Source } else { Add-Row 'FAIL' 'hermes on PATH' 'found' 'not found' }
$cfg = Join-Path $ProfileDir 'config.yaml'
if (Test-Path -LiteralPath $cfg) {
    $text = [IO.File]::ReadAllText($cfg)
    $left = [regex]::Matches($text, '\{\{[A-Z0-9_]+\}\}').Count
    if ($left -eq 0) { Add-Row 'PASS' 'profile config rendered' '0 placeholders' '0' } else { Add-Row 'FAIL' 'profile config rendered' '0 placeholders' "$left" }
    $pkgFwd = ([IO.Path]::GetFullPath($PackageRoot)).TrimEnd('\').Replace('\', '/')
    if ($text.Contains("$pkgFwd/agents/lead/skills")) { Add-Row 'PASS' 'profile skill dirs -> this package' 'this package path' $pkgFwd }
    else { Add-Row 'FAIL' 'profile skill dirs -> this package' $pkgFwd 'skills.external_dirs points elsewhere; re-run install_profile.ps1' }
    $inc = ([regex]::Match($text, '(?s)include:\s*\n((?:\s+- [a-z_]+\s*\n)+)')).Groups[1].Value
    $incCount = @([regex]::Matches($inc, '- [a-z_]+')).Count
    $expInc = [string]$envSpec.solidpilot.include_count
    if ("$incCount" -eq $expInc) { Add-Row 'PASS' 'SolidPilot tools.include' $expInc "$incCount" } else { Add-Row 'FAIL' 'SolidPilot tools.include' $expInc "$incCount" }
    if ($text -match '(?m)^\s+- code_execution') { Add-Row 'PASS' 'profile toolset code_execution (H1.2)' 'present' 'present' } else { Add-Row 'FAIL' 'profile toolset code_execution (H1.2)' 'present' 'absent: profile predates H1.2; re-run install_profile.ps1' }
} else { Add-Row 'FAIL' 'profile config.yaml' 'exists' "missing: $cfg" }
$soul = Join-Path $ProfileDir 'SOUL.md'
if (Test-Path -LiteralPath $soul) {
    if ((Sha256 $soul) -eq (Sha256 (Join-Path $PackageRoot 'profile\SOUL.md'))) { Add-Row 'PASS' 'profile SOUL.md == package' 'same sha256' 'same' }
    else { Add-Row 'FAIL' 'profile SOUL.md == package' 'same sha256' 'differs; re-run install_profile.ps1' }
} else { Add-Row 'FAIL' 'profile SOUL.md' 'exists' "missing: $soul" }

# 6. Optional live MCP connect --------------------------------------------------
if ($McpTest -and $hermes) {
    foreach ($srv in @('solidpilot', 'ansys')) {
        $res = Invoke-Native { & hermes -p brake mcp test $srv }
        $last = ($res.Text.Trim() -split "`n" | Select-Object -Last 1)
        if ($res.Code -eq 0) { Add-Row 'PASS' "hermes mcp test $srv" 'exit 0' "exit 0 : $last" }
        else { Add-Row 'FAIL' "hermes mcp test $srv" 'exit 0' "exit $($res.Code) : $last" }
    }
}

# 7. Package unit tests ---------------------------------------------------------
if (-not $SkipUnitTests) {
    $spPy = Join-Path $SolidPilotRoot '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $spPy) {
        Push-Location $PackageRoot
        try { $res = Invoke-Native { & $spPy -B -m unittest discover -s tests } } finally { Pop-Location }
        $tail = @($res.Text.Trim() -split "`n" | Where-Object { $_ -match '^(Ran |OK|FAILED)' }) -join '; '
        $last = $tail
        if ($res.Code -eq 0) { Add-Row 'PASS' 'package unit tests' 'OK' $last } else { Add-Row 'FAIL' 'package unit tests' 'OK' $last }
    } else { Add-Row 'FAIL' 'package unit tests' 'OK' 'no SolidPilot python to run them' }
}

# ---- report -------------------------------------------------------------------
foreach ($r in $rows) { Write-Host ("{0,-4}  {1,-38}  expected: {2}`n      {3,-38}  measured: {4}" -f $r.Status, $r.Check, $r.Expected, '', $r.Measured) }
$fails = @($rows | Where-Object { $_.Status -eq 'FAIL' }).Count
$warns = @($rows | Where-Object { $_.Status -eq 'WARN' }).Count
Write-Host ("Preflight: {0} checks, {1} FAIL, {2} WARN" -f $rows.Count, $fails, $warns)
if ($fails -gt 0) { exit 1 } else { exit 0 }
