[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('inspect','prepare','freeze','verify')][string]$Action,
    [Parameter(Mandatory=$true)][string]$PredecessorProject,
    [string]$SuccessorProject,
    [string]$Bootstrap,
    [string]$Output,
    [string]$Plan
)
$ErrorActionPreference='Stop'
$env:PYTHONUTF8='1'
$engine=Join-Path $PSScriptRoot 'math_research_migrate_v8_to_v10.py'
$arguments=@('-B',$engine,$Action,'--predecessor',$PredecessorProject)
if($Action-ceq'prepare'){
    if([string]::IsNullOrWhiteSpace($SuccessorProject)-or[string]::IsNullOrWhiteSpace($Bootstrap)-or[string]::IsNullOrWhiteSpace($Output)){throw 'prepare requires SuccessorProject, Bootstrap, and Output.'}
    $arguments+=@('--successor',$SuccessorProject,'--bootstrap',$Bootstrap,'--output',$Output)
}
elseif($Action-ceq'freeze'){
    if([string]::IsNullOrWhiteSpace($Plan)){throw 'freeze requires Plan.'}
    $arguments+=@('--plan',$Plan)
}
elseif($Action-ceq'verify'){
    if([string]::IsNullOrWhiteSpace($SuccessorProject)-or[string]::IsNullOrWhiteSpace($Plan)){throw 'verify requires SuccessorProject and Plan.'}
    $arguments+=@('--successor',$SuccessorProject,'--plan',$Plan)
}
& python @arguments
exit $LASTEXITCODE
