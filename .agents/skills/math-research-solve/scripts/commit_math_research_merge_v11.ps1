[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$PlanPath,
    [Parameter(Mandatory=$true)][string]$ExpectedPlanSha256,
    [Parameter(Mandatory=$true)][string]$VerificationPath,
    [Parameter(Mandatory=$true)][ValidateSet('active')][string]$GoalStatus
)
$ErrorActionPreference = 'Stop'
& python (Join-Path $PSScriptRoot 'math_research_state_v11.py') commit-merge `
    --plan $PlanPath `
    --expected-plan-sha256 $ExpectedPlanSha256 `
    --verification $VerificationPath `
    --goal-status $GoalStatus
exit $LASTEXITCODE
