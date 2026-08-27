[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$PlanPath,
    [Parameter(Mandatory=$true)][ValidateSet('none','active','paused','complete','blocked')][string]$GoalStatus
)
$ErrorActionPreference='Stop'
$env:PYTHONUTF8='1'
& python -B (Join-Path $PSScriptRoot 'math_research_state_v9.py') commit --plan $PlanPath --goal-status $GoalStatus
exit $LASTEXITCODE
