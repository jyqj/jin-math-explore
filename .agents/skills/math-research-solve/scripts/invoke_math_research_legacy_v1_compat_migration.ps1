[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][ValidateSet('Analyze','Apply','Verify')][string]$Action,
    [Parameter(Mandatory = $true)][string]$RunDirectory,
    [Parameter(Mandatory = $true)][string]$ReceiptFile
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)

$launcherEntry = Join-Path $PSScriptRoot 'launch_math_research_legacy_v1_compat.ps1'
$launcherModule = Join-Path $PSScriptRoot 'MathResearchLauncherLegacyV1Compat.psm1'
$cycleModule = Join-Path $PSScriptRoot 'MathResearchCycleLedgerLegacyV1Compat.psm1'
$cycleCli = Join-Path $PSScriptRoot 'invoke_math_research_cycle_legacy_v1_compat.ps1'
$projectModule = Join-Path $PSScriptRoot 'MathResearchProjectArchive.psm1'
$canaryHost = Join-Path $PSScriptRoot 'invoke_math_research_legacy_v1_compat_canary_host.ps1'
$canaryEntry = Join-Path $PSScriptRoot 'invoke_math_research_canary_v2.ps1'

Import-Module (Join-Path $PSScriptRoot 'MathResearchLegacyV1CompatMigration.psm1') -Force -DisableNameChecking
$result = Invoke-MathResearchLegacyV1CompatMigration -Action $Action -RunDirectory $RunDirectory -ReceiptFile $ReceiptFile -LauncherEntryPath $launcherEntry -LauncherModulePath $launcherModule -CycleModulePath $cycleModule -CycleCliPath $cycleCli -ProjectModulePath $projectModule -CanaryHostPath $canaryHost -CanaryEntryPath $canaryEntry
$result | ConvertTo-Json -Depth 16
