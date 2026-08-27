[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ProjectPath,
    [ValidateSet('Auto','Full')][string]$AuditMode='Auto',
    [ValidateSet('none','active','paused','complete','blocked')][string]$GoalStatus='none'
)
$ErrorActionPreference='Stop'
$env:PYTHONUTF8='1'
$engine=Join-Path $PSScriptRoot 'math_research_state_v9.py'
$raw=& python -B $engine startup --project $ProjectPath --audit-mode $AuditMode --legacy-goal-status $GoalStatus | Out-String
$code=$LASTEXITCODE
if($code-ne0){$raw.TrimEnd();exit $code}
$parsed=$raw|ConvertFrom-Json -AsHashtable -DateKind String
if($parsed.ok-and$parsed.data.classification-ceq'delegate_startup_v3'){
    & (Join-Path $PSScriptRoot 'invoke_math_research_startup_v3.ps1') -ProjectDirectory $ProjectPath -GoalStatus $GoalStatus
    if(-not $?){exit 1}
    exit 0
}
$raw.TrimEnd()
exit 0
