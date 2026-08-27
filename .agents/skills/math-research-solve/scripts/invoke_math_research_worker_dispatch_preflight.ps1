[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ProjectPath,
    [Parameter(Mandatory=$true)][string]$TicketPath,
    [Parameter(Mandatory=$true)][string[]]$HostWorkspaceRoot,
    [Parameter(Mandatory=$true)][ValidateSet('collaboration','project-root-exec')][string]$Transport,
    [string]$ExecutionWorkspaceRoot
)

$ErrorActionPreference='Stop'
$env:PYTHONUTF8='1'
$argv=@(
    '-B',
    (Join-Path $PSScriptRoot 'math_research_worker_dispatch_preflight.py'),
    '--project',$ProjectPath,
    '--ticket',$TicketPath,
    '--transport',$Transport
)
foreach($root in $HostWorkspaceRoot){$argv+=@('--host-workspace-root',$root)}
if($ExecutionWorkspaceRoot){$argv+=@('--execution-workspace-root',$ExecutionWorkspaceRoot)}
& python @argv
exit $LASTEXITCODE
