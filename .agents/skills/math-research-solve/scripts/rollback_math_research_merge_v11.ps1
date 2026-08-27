[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$PlanPath,
    [Parameter(Mandatory=$true)][string]$ExpectedPlanSha256,
    [Parameter(Mandatory=$true)][string]$ExpectedCurrentHeadSha256,
    [Parameter(Mandatory=$true)][ValidateSet('active')][string]$GoalStatus
)
$ErrorActionPreference = 'Stop'
& python (Join-Path $PSScriptRoot 'math_research_state_v11.py') rollback-merge `
    --plan $PlanPath `
    --expected-plan-sha256 $ExpectedPlanSha256 `
    --expected-current-head-sha256 $ExpectedCurrentHeadSha256 `
    --goal-status $GoalStatus
exit $LASTEXITCODE
