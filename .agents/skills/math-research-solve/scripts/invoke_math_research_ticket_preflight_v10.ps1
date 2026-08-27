[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ProjectPath,
    [Parameter(Mandatory=$true)][string]$TicketPath,
    [string]$AccessLogPath
)
$ErrorActionPreference='Stop'
$env:PYTHONUTF8='1'
$argsList=@('-B',(Join-Path $PSScriptRoot 'math_research_state_v10.py'),'ticket-preflight-v10','--project',$ProjectPath,'--ticket',$TicketPath)
if($AccessLogPath){$argsList+=@('--access-log',$AccessLogPath)}
& python @argsList
exit $LASTEXITCODE

