[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][ValidateSet('Analyze','Apply','Verify')][string]$Action,
    [Parameter(Mandatory = $true)][string]$RunDirectory,
    [Parameter(Mandatory = $true)][string]$ReceiptFile,
    [Parameter(Mandatory = $true)][string]$PriorMigrationReceiptFile
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)

$paths = @{
    PriorLauncherEntry = Join-Path $PSScriptRoot 'launch_math_research_legacy_v1_compat.ps1'
    LauncherEntry = Join-Path $PSScriptRoot 'launch_math_research_legacy_v1_compat_v2.ps1'
    LauncherModule = Join-Path $PSScriptRoot 'MathResearchLauncherLegacyV1Compat.psm1'
    ArgvCompatModule = Join-Path $PSScriptRoot 'MathResearchApproveForMeArgvCompatV2.psm1'
    PriorCanaryHost = Join-Path $PSScriptRoot 'invoke_math_research_legacy_v1_compat_canary_host.ps1'
    CanaryHost = Join-Path $PSScriptRoot 'invoke_math_research_legacy_v1_compat_canary_host_v2.ps1'
    CanaryModule = Join-Path $PSScriptRoot 'MathResearchLauncherV2.psm1'
    CanaryEntry = Join-Path $PSScriptRoot 'invoke_math_research_canary_v2.ps1'
    CycleModule = Join-Path $PSScriptRoot 'MathResearchCycleLedgerLegacyV1Compat.psm1'
    CycleCli = Join-Path $PSScriptRoot 'invoke_math_research_cycle_legacy_v1_compat.ps1'
    ProjectModule = Join-Path $PSScriptRoot 'MathResearchProjectArchive.psm1'
    AmendmentModule = Join-Path $PSScriptRoot 'MathResearchLegacyV1ControlPathAmendmentV2.psm1'
    AmendmentCli = $PSCommandPath
}
Import-Module (Join-Path $PSScriptRoot 'MathResearchLauncherLegacyV1Compat.psm1') -Force -DisableNameChecking
Import-Module (Join-Path $PSScriptRoot 'MathResearchLegacyV1CompatMigration.psm1') -Force -DisableNameChecking
Import-Module $paths.AmendmentModule -Force -DisableNameChecking
$result = Invoke-MathResearchLegacyV1ControlPathAmendmentV2 -Action $Action -RunDirectory $RunDirectory -ReceiptFile $ReceiptFile -PriorReceiptFile $PriorMigrationReceiptFile -Paths $paths
$result | ConvertTo-Json -Depth 16
