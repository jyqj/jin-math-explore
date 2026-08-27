[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)][ValidateSet('scan','validate','export-plan','export')][string]$Command,
    [Parameter(Mandatory=$true)][string]$Project,
    [Parameter(Mandatory=$true)][string]$Index,
    [string]$Output,
    [ValidateSet('private','public')][string]$Visibility = 'private',
    [switch]$AllowUnregistered
)
$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot 'math_research_assets.py'
$arguments = @('-B', $script, $Command, '--project', $Project, '--index', $Index)
if ($Output) { $arguments += @('--output', $Output) }
if ($Command -eq 'export') { $arguments += @('--visibility', $Visibility) }
if ($AllowUnregistered -and $Command -eq 'validate') { $arguments += '--allow-unregistered' }
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONUTF8 = '1'
& python @arguments
exit $LASTEXITCODE
