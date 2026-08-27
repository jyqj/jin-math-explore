[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$CanonicalProjectPath,
    [Parameter(Mandatory=$true)][string[]]$ImportProjectPath,
    [Parameter(Mandatory=$true)][string]$ExternalZipPath,
    [Parameter(Mandatory=$true)][string]$OutputPath
)
$ErrorActionPreference = 'Stop'
$argv = @((Join-Path $PSScriptRoot 'math_research_state_v11.py'), 'prepare-merge', '--canonical', $CanonicalProjectPath)
foreach ($item in $ImportProjectPath) { $argv += @('--import-project', $item) }
$argv += @('--zip', $ExternalZipPath, '--output', $OutputPath)
& python @argv
exit $LASTEXITCODE
