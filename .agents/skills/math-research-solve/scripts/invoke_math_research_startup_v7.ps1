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
if ($project.schema -eq 'math-research-project/v12') {
    $args = @((Join-Path $PSScriptRoot 'math_research_state_v12.py'), 'startup', '--project', $ProjectPath)
    if ($AuditMode -eq 'Full') { $args += '--full' }
    & python @args
    if ($LASTEXITCODE -ne 0) { throw "Startup v7 failed with exit code $LASTEXITCODE" }
    exit 0
}
$legacy = Join-Path $PSScriptRoot 'invoke_math_research_startup_v6.ps1'
if (-not (Test-Path -LiteralPath $legacy -PathType Leaf)) { throw "Legacy Startup v6 is unavailable." }
& $legacy -ProjectPath $ProjectPath -AuditMode $AuditMode
exit $LASTEXITCODE
