[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RunDirectory,
    [Parameter(Mandatory = $true)][string]$ManifestPath,
    [Parameter(Mandatory = $true)][string]$MigrationReceiptFile,
    [Parameter(Mandatory = $true)][string]$ControlPathReceiptFile
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
    CanaryHost = $PSCommandPath
    CanaryModule = Join-Path $PSScriptRoot 'MathResearchLauncherV2.psm1'
    CanaryEntry = Join-Path $PSScriptRoot 'invoke_math_research_canary_v2.ps1'
    CycleModule = Join-Path $PSScriptRoot 'MathResearchCycleLedgerLegacyV1Compat.psm1'
    CycleCli = Join-Path $PSScriptRoot 'invoke_math_research_cycle_legacy_v1_compat.ps1'
    ProjectModule = Join-Path $PSScriptRoot 'MathResearchProjectArchive.psm1'
    AmendmentModule = Join-Path $PSScriptRoot 'MathResearchLegacyV1ControlPathAmendmentV2.psm1'
    AmendmentCli = Join-Path $PSScriptRoot 'invoke_math_research_legacy_v1_control_path_amendment_v2.ps1'
}

Import-Module $paths.LauncherModule -Force -DisableNameChecking
Import-Module (Join-Path $PSScriptRoot 'MathResearchLegacyV1CompatMigration.psm1') -Force -DisableNameChecking
Import-Module $paths.AmendmentModule -Force -DisableNameChecking
$v2Module = Import-Module $paths.CanaryModule -Force -DisableNameChecking -PassThru
Import-Module $paths.ArgvCompatModule -Force -DisableNameChecking
Enable-MathResearchApproveForMeArgvCompatV2 -TargetModule $v2Module -Flavor launcher-v2

$read = Read-SignedJsonPayload -LiteralPath $ManifestPath
$manifest = $read.Payload
$prior = Read-MathResearchLegacyV1CompatReceipt -LiteralPath $MigrationReceiptFile
$amendment = Read-MathResearchLegacyV1ControlPathReceiptV2 -LiteralPath $ControlPathReceiptFile
Assert-MathResearchLegacyV1ControlPathAmendmentV2State -Manifest $manifest -RunPath $RunDirectory -ReceiptRead $amendment -PriorReceiptRead $prior -Paths $paths -RequireApplied | Out-Null
if ([string]$manifest.prompt_version -cne 'v6' -or [string]$manifest.config.approval_mode -cne 'approve_for_me') { throw 'Compatibility canary v2 requires the applied Prompt v6 approval amendment.' }
$attestation = Select-TrustedCodexExecutable -WorkingDirectory $RunDirectory
if ([string]$attestation.version -cne [string]$manifest.executable.version -or [string]$attestation.sha256 -cne [string]$manifest.executable.sha256) { throw 'Compatibility canary v2 executable attestation differs from the signed manifest.' }
$probe = New-CodexExecArguments -RunDirectory $RunDirectory -Model ([string]$manifest.config.model) -ReasoningEffort 'low' -Sandbox 'workspace-write' -ApprovalMode approve_for_me -AllowWebSearch:$false -EnableMultiAgent:$false -MaxChildAgents 1 -LastMessagePath (Join-Path $RunDirectory 'launcher-canary-last-message-v2.json') -Ephemeral
Assert-MathResearchApproveForMeArgvCompatV2 -Arguments $probe | Out-Null
$result = Invoke-MathResearchLauncherCanaryV2 -Attestation $attestation -RunDirectory $RunDirectory -ManifestPath $ManifestPath -LauncherEntryPath $paths.LauncherEntry -LauncherModulePath $paths.LauncherModule -CanaryEntryPath $paths.CanaryEntry -CycleCliPath $paths.CycleCli -ApprovalMode approve_for_me -Model ([string]$manifest.config.model) -ReasoningEffort ([string]$manifest.config.reasoning_effort) -WebSearch ([string]$manifest.config.web_search) -MaxChildAgents ([int]$manifest.config.max_child_agents)
$result | ConvertTo-Json -Depth 16
