[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RunDirectory,
    [Parameter(Mandatory = $true)][string]$ManifestPath
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)

$launcherEntry = Join-Path $PSScriptRoot 'launch_math_research_legacy_v1_compat.ps1'
$launcherModule = Join-Path $PSScriptRoot 'MathResearchLauncherLegacyV1Compat.psm1'
$canaryEntry = Join-Path $PSScriptRoot 'invoke_math_research_canary_v2.ps1'
$cycleCli = Join-Path $PSScriptRoot 'invoke_math_research_cycle_legacy_v1_compat.ps1'
Import-Module (Join-Path $PSScriptRoot 'MathResearchLauncherV2.psm1') -Force -DisableNameChecking

$read = Read-SignedJsonPayload -LiteralPath $ManifestPath
$manifest = $read.Payload
if ([string]$manifest.prompt_version -cne 'v6' -or [string]$manifest.config.approval_mode -cne 'approve_for_me') { throw 'Compatibility canary requires an applied Prompt v6 approval amendment.' }
$attestation = Select-TrustedCodexExecutable -WorkingDirectory $RunDirectory
if ([string]$attestation.version -cne [string]$manifest.executable.version -or [string]$attestation.sha256 -cne [string]$manifest.executable.sha256) { throw 'Compatibility canary executable attestation differs from the signed manifest.' }
$result = Invoke-MathResearchLauncherCanaryV2 -Attestation $attestation -RunDirectory $RunDirectory -ManifestPath $ManifestPath -LauncherEntryPath $launcherEntry -LauncherModulePath $launcherModule -CanaryEntryPath $canaryEntry -CycleCliPath $cycleCli -ApprovalMode approve_for_me -Model ([string]$manifest.config.model) -ReasoningEffort ([string]$manifest.config.reasoning_effort) -WebSearch ([string]$manifest.config.web_search) -MaxChildAgents ([int]$manifest.config.max_child_agents)
$result | ConvertTo-Json -Depth 16
