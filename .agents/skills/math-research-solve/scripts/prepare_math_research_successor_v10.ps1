[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$PredecessorProjectPath,
    [Parameter(Mandatory=$true)][string]$SuccessorProjectPath,
    [Parameter(Mandatory=$true)][string]$SpecPath,
    [Parameter(Mandatory=$true)][string]$OutputPath
)
$ErrorActionPreference='Stop'
$env:PYTHONUTF8='1'
& python -B (Join-Path $PSScriptRoot 'math_research_state_v10.py') prepare-successor --predecessor-project $PredecessorProjectPath --successor-project $SuccessorProjectPath --spec $SpecPath --output $OutputPath
exit $LASTEXITCODE

