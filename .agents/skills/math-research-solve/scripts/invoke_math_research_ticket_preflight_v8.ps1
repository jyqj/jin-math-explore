[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ProjectPath,
    [Parameter(Mandatory=$true)][string]$TicketPath,
    [Parameter(Mandatory=$true)][string]$SourceRequirementsPath,
    [string]$AccessLogPath
)
$ErrorActionPreference='Stop'
$env:PYTHONUTF8='1'
$engine=Join-Path $PSScriptRoot 'math_research_state_v9.py'
$argv=@('-B',$engine,'ticket-preflight-v8','--project',$ProjectPath,'--ticket',$TicketPath,'--source-requirements',$SourceRequirementsPath)
if($AccessLogPath){$argv+=@('--access-log',$AccessLogPath)}
& python @argv
exit $LASTEXITCODE

