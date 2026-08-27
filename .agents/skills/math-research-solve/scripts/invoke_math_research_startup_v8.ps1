[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ProjectPath,
    [ValidateSet('Auto','Full')][string]$AuditMode = 'Auto',
    [string]$GoalStatus = 'none'
)
$ErrorActionPreference = 'Stop'
$head = Join-Path $ProjectPath 'project.json'
if (-not (Test-Path -LiteralPath $head -PathType Leaf)) { throw "project.json is absent: $ProjectPath" }
$project = Get-Content -Raw -LiteralPath $head | ConvertFrom-Json
if ($project.schema -eq 'math-research-project/v13') {
    $args = @((Join-Path $PSScriptRoot 'math_research_state_v13.py'), 'startup', '--project', $ProjectPath)
    if ($AuditMode -eq 'Full') { $args += '--full' }
    & python @args
    if ($LASTEXITCODE -ne 0) { throw "Startup v8 failed with exit code $LASTEXITCODE" }
    exit 0
}
$frozen = Join-Path $PSScriptRoot 'invoke_math_research_startup_v7.ps1'
if (-not (Test-Path -LiteralPath $frozen -PathType Leaf)) { throw "Frozen Startup v7 is unavailable." }
& $frozen -ProjectPath $ProjectPath -AuditMode $AuditMode -GoalStatus $GoalStatus
exit $LASTEXITCODE
