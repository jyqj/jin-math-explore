[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ProjectPath,
    [ValidateSet('Auto','Full')][string]$AuditMode = 'Auto'
)
$ErrorActionPreference = 'Stop'
$headPath = Join-Path $ProjectPath 'project.json'
if (-not (Test-Path -LiteralPath $headPath -PathType Leaf)) {
    throw "project.json is absent: $ProjectPath"
}
$head = Get-Content -LiteralPath $headPath -Raw | ConvertFrom-Json
if ($head.schema -eq 'math-research-project/v11') {
    $argv = @((Join-Path $PSScriptRoot 'math_research_state_v11.py'), 'startup', '--project', $ProjectPath)
    if ($AuditMode -eq 'Full') { $argv += '--full' }
    & python @argv
    exit $LASTEXITCODE
}
& (Join-Path $PSScriptRoot 'invoke_math_research_startup_v5.ps1') -ProjectPath $ProjectPath -AuditMode $AuditMode
exit $LASTEXITCODE
