[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('prepare-batch','commit-batch','rollback-batch','repair-views','restore-tree','export')][string]$Action,
    [string]$SpecPath,
    [string]$OutputPath,
    [string]$PlanPath,
    [string]$ExpectedPlanSha256,
    [string]$JournalPath,
    [string]$ProjectPath,
    [string]$SourceId,
    [ValidateSet('none','active','paused','complete','blocked')][string]$GoalStatus = 'none',
    [ValidateSet('intermediate','final','full-private')][string]$Profile = 'intermediate'
)
$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot 'math_research_state_v12.py'
$args = @($script, $Action)
switch ($Action) {
    'prepare-batch' { $args += @('--spec',$SpecPath,'--output',$OutputPath) }
    'commit-batch' { $args += @('--plan',$PlanPath,'--expected-plan-sha256',$ExpectedPlanSha256,'--goal-status',$GoalStatus) }
    'rollback-batch' { $args += @('--journal',$JournalPath,'--goal-status',$GoalStatus) }
    'repair-views' { $args += @('--project',$ProjectPath,'--goal-status',$GoalStatus) }
    'restore-tree' { $args += @('--project',$ProjectPath,'--source-id',$SourceId,'--output',$OutputPath) }
    'export' { $args += @('--project',$ProjectPath,'--profile',$Profile,'--output',$OutputPath) }
}
& python @args
if ($LASTEXITCODE -ne 0) { throw "v12 action failed with exit code $LASTEXITCODE" }
