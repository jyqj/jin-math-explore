[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ProjectPath,
    [Parameter(Mandatory=$true)][ValidateSet('ATTEMPT_START','SOLVER_COMPLETE','VERIFIER_COMPLETE','ATTEMPT_END','CHECKPOINT_COMMIT','RESEARCH_CHECKPOINT')][string]$Transition,
    [Parameter(Mandatory=$true)][string]$PayloadPath,
    [Parameter(Mandatory=$true)][string]$OutputPath,
    [ValidateSet('Auto','Full')][string]$AuditMode='Auto'
)
$ErrorActionPreference='Stop'
$env:PYTHONUTF8='1'
& python -B (Join-Path $PSScriptRoot 'math_research_state_v10.py') prepare --project $ProjectPath --transition $Transition --payload $PayloadPath --output $OutputPath --audit-mode $AuditMode
exit $LASTEXITCODE

