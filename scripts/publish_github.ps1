<#
.SYNOPSIS
  Publish this package to GitHub (github.com) with the gh CLI; public by default (-Visibility private to keep it private).

.DESCRIPTION
  Refuses to push when any of these holds:
    - git or gh is missing, or gh is not logged in
    - the working tree has uncommitted changes
    - a file under .local/ (machine settings) is tracked
    - the unit tests fail (skip with -SkipTests)
  Then either creates <Owner>/<Repo> (public by default) and pushes, or, when an
  "origin" remote already exists, pushes the current branch to it.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\publish_github.ps1
  powershell -ExecutionPolicy Bypass -File scripts\publish_github.ps1 -Owner my-org -Repo hermes-brake-disc
#>
[CmdletBinding()]
param(
    [string]$Owner = "",
    [string]$Repo = "hermes-brake-disc",
    [ValidateSet('public', 'private')][string]$Visibility = 'public',
    [switch]$SkipTests
)

$ErrorActionPreference = 'Stop'
$PackageRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $PackageRoot

function Stop-Publish([string]$msg) { Write-Host "STOP: $msg Nothing was pushed." -ForegroundColor Red; exit 1 }
# git, gh and python write progress to stderr; under Windows PowerShell 5.1 with
# ErrorActionPreference=Stop that would abort the script. Run them through here.
function Invoke-Native([scriptblock]$Block, [switch]$Show) {
    $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try {
        $lines = @(& $Block 2>&1 | ForEach-Object { "$_" })
        if ($Show) { $lines | ForEach-Object { Write-Host $_ } }
        return @{ Code = $LASTEXITCODE; Text = ($lines -join "`n") }
    } finally { $ErrorActionPreference = $old }
}

foreach ($tool in @('git', 'gh')) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { Stop-Publish "$tool is not on PATH (winget install --id GitHub.cli / Git.Git)." }
}
if ((Invoke-Native { & gh auth status --hostname github.com }).Code -ne 0) { Stop-Publish 'gh is not logged in. Run: gh auth login --hostname github.com' }

$r = Invoke-Native { & git rev-parse --short HEAD }
if ($r.Code -ne 0) { Stop-Publish 'no commit yet (git rev-parse HEAD failed).' }
$head = $r.Text.Trim()
$branch = (Invoke-Native { & git rev-parse --abbrev-ref HEAD }).Text.Trim()
$dirty = (Invoke-Native { & git status --porcelain }).Text.Trim()
if ($dirty) { Stop-Publish "uncommitted changes:`n$dirty" }
$tracked = (Invoke-Native { & git ls-files -- .local }).Text.Trim()
if ($tracked) { Stop-Publish ".local/ files are tracked: $tracked" }

if (-not $SkipTests) {
    $py = 'C:/solidpilot/.venv/Scripts/python.exe'
    if (-not (Test-Path -LiteralPath $py)) { Stop-Publish "no $py to run the unit tests (or pass -SkipTests)." }
    if ((Invoke-Native { & $py -B -m unittest discover -s tests } -Show).Code -ne 0) { Stop-Publish 'unit tests failed.' }
}

$r = Invoke-Native { & git remote get-url origin }
if ($r.Code -eq 0 -and $r.Text.Trim()) {
    Write-Host "Pushing $branch ($head) to existing origin $($r.Text.Trim())"
    if ((Invoke-Native { & git push -u origin $branch } -Show).Code -ne 0) { Stop-Publish 'git push failed.' }
} else {
    $target = $Repo
    if ($Owner) { $target = "$Owner/$Repo" }
    Write-Host "Creating $($Visibility.ToUpper()) github.com repo $target and pushing $branch ($head)"
    $desc = 'FR-330V brake: Hermes lead + SolidWorks/SpaceClaim/Fluent specialist agents over MCP (PRD H1.2)'
    if ((Invoke-Native { & gh repo create $target "--$Visibility" --source . --remote origin --push --description $desc } -Show).Code -ne 0) { Stop-Publish 'gh repo create failed.' }
}
$url = (Invoke-Native { & gh repo view --json url -q .url }).Text.Trim()
$vis = (Invoke-Native { & gh repo view --json visibility -q .visibility }).Text.Trim()
if ($vis -and $vis -ne $Visibility.ToUpper()) {
    Write-Host "Changing visibility $vis -> $($Visibility.ToUpper())"
    if ((Invoke-Native { & gh repo edit --visibility $Visibility --accept-visibility-change-consequences } -Show).Code -ne 0) { Stop-Publish 'gh repo edit --visibility failed.' }
    $vis = (Invoke-Native { & gh repo view --json visibility -q .visibility }).Text.Trim()
}
Write-Host "Published: $url  visibility=$vis  commit=$head"
if ($vis -ne $Visibility.ToUpper()) { Write-Host "WARNING: repository visibility is $vis, expected $($Visibility.ToUpper())." -ForegroundColor Yellow }
exit 0
