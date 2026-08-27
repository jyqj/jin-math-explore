[CmdletBinding()]
param()

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)

function Assert-True {
    param([Parameter(Mandatory = $true)][bool]$Condition, [Parameter(Mandatory = $true)][string]$Message)
    if (-not $Condition) { throw $Message }
}

function Assert-ThrowsLike {
    param([Parameter(Mandatory = $true)][scriptblock]$Action, [Parameter(Mandatory = $true)][string]$Pattern, [Parameter(Mandatory = $true)][string]$Message)
    try { & $Action; throw "Expected failure was not raised: $Message" }
    catch { if ($_.Exception.Message -notlike "*$Pattern*") { throw "$Message Actual: $($_.Exception.Message)" } }
}

function New-Binding {
    param([Parameter(Mandatory = $true)][string]$Path)
    return [ordered]@{ path=[IO.Path]::GetFullPath($Path); sha256=Get-Sha256HexFromFile -LiteralPath $Path }
}

$launcherModule = Join-Path $PSScriptRoot 'MathResearchLauncherLegacyV1Compat.psm1'
$migrationModule = Join-Path $PSScriptRoot 'MathResearchLegacyV1CompatMigration.psm1'
Import-Module $launcherModule -Force -DisableNameChecking
Import-Module $migrationModule -Force -DisableNameChecking
if (-not (Test-Path -LiteralPath (Get-ManifestKeyPath) -PathType Leaf)) { throw 'Compatibility regression requires the installed DPAPI manifest key.' }

$testRoot = Join-Path ([IO.Path]::GetTempPath()) ('math-research-legacy-v1-compat-' + [Guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($testRoot) | Out-Null
try {
    $run = Join-Path $testRoot 'run'
    [IO.Directory]::CreateDirectory($run) | Out-Null
    $sourceLauncherEntry = Join-Path $PSScriptRoot 'launch_math_research.ps1'
    $sourceLauncherModule = Join-Path $PSScriptRoot 'MathResearchLauncher.psm1'
    $sourceCycleModule = Join-Path $PSScriptRoot 'MathResearchCycleLedger.psm1'
    $sourceCycleCli = Join-Path $PSScriptRoot 'invoke_math_research_cycle.ps1'
    $projectModule = Join-Path $PSScriptRoot 'MathResearchProjectArchive.psm1'
    $targetLauncherEntry = Join-Path $PSScriptRoot 'launch_math_research_legacy_v1_compat.ps1'
    $targetCycleModule = Join-Path $PSScriptRoot 'MathResearchCycleLedgerLegacyV1Compat.psm1'
    $targetCycleCli = Join-Path $PSScriptRoot 'invoke_math_research_cycle_legacy_v1_compat.ps1'
    $canaryHost = Join-Path $PSScriptRoot 'invoke_math_research_legacy_v1_compat_canary_host.ps1'
    $canaryEntry = Join-Path $PSScriptRoot 'invoke_math_research_canary_v2.ps1'
    $threadId = [Guid]::NewGuid().ToString('D')
    $binding = ('a' * 64)
    $goalHash = ('b' * 64)
    $headHash = ('c' * 64)
    $checkpoint = [ordered]@{
        ledger_schema_version=1; head_sequence=0; head_payload_sha256=$headHash
        attempt_count=0; audit_count=0; total_round_count=0; attempts_since_last_audit=0
        audit_due=$false; clean_return=$true; completion_authorized=$false
    }
    $manifest = [ordered]@{
        schema_version=1; run_id='synthetic-compat-run'; revision=3
        created_at_utc='2026-08-08T12:34:56.1200000Z'; updated_at_utc='2026-08-08T12:35:56.1200000Z'
        prompt_version='v6'; contract_version='v1'; run_directory=$run; status='failed'; exit_reason='synthetic operational failure'
        thread_id=$threadId
        project=[ordered]@{project_id='synthetic-project';directory=$testRoot;directory_name='synthetic-project';archive_schema=1;identity_sha256=('d' * 64)}
        config=[ordered]@{approval_policy='never';model='gpt-5.6-sol';reasoning_effort='xhigh';web_search='allowed';total_round_budget=33;attempt_budget=24;audit_interval_attempts=4;round_budget_enforcement='cycle_controller';max_runtime_minutes=0;max_child_agents=3;max_total_agents=4;agent_stages=@(3)}
        goal=[ordered]@{objective_sha256=$goalHash;confirmation='model_reported_via_nonce_marker';persistence_verified=$false}
        cycle_ledger=[ordered]@{
            contract_binding_sha256=$binding
            module=New-Binding $sourceCycleModule
            cli=New-Binding $sourceCycleCli
            project_module=New-Binding $projectModule
            checkpoint=$checkpoint
        }
        process=$null
    }
    $manifestPath = Join-Path $run 'run.json'
    Write-SignedJsonPayload -LiteralPath $manifestPath -Payload $manifest
    Copy-Item -LiteralPath $manifestPath -Destination "$manifestPath.bak"
    $primaryHash = Get-Sha256HexFromFile -LiteralPath $manifestPath
    $backupHash = Get-Sha256HexFromFile -LiteralPath "$manifestPath.bak"
    $receipt = [ordered]@{
        schema_version=1; protocol='math-research-legacy-v1-compat-migration/v1'; migration_id='synthetic-migration'; action='resume_prompt_v6_with_compat_bundle'; archive_directory_name='compat-migration-v1'
        project=[ordered]@{project_id='synthetic-project';directory=$testRoot}
        run=[ordered]@{id='synthetic-compat-run';directory=$run;thread_id=$threadId}
        contract=[ordered]@{version='v1';binding_sha256=$binding}
        goal=[ordered]@{objective_sha256=$goalHash}
        source=[ordered]@{
            status='failed';manifest_primary_sha256=$primaryHash;manifest_backup_sha256=$backupHash
            launcher_entry=New-Binding $sourceLauncherEntry;launcher_module=New-Binding $sourceLauncherModule
            cycle_module=New-Binding $sourceCycleModule;cycle_cli=New-Binding $sourceCycleCli;project_module=New-Binding $projectModule
            counters=$checkpoint
        }
        target=[ordered]@{
            launcher_entry=New-Binding $targetLauncherEntry;launcher_module=New-Binding $launcherModule
            cycle_module=New-Binding $targetCycleModule;cycle_cli=New-Binding $targetCycleCli;project_module=New-Binding $projectModule
            canary_host=New-Binding $canaryHost;canary_entry=New-Binding $canaryEntry
        }
        authorization=[ordered]@{approval_mode_from='never';approval_mode_to='approve_for_me';objective_changed=$false;quantifiers_changed=$false;counters_reset=$false}
    }
    $receiptPath = Join-Path $testRoot 'receipt.json'
    [IO.File]::WriteAllText($receiptPath, ($receipt | ConvertTo-Json -Depth 32), [Text.UTF8Encoding]::new($false))
    $badReceipt = ($receipt | ConvertTo-Json -Depth 32) | ConvertFrom-Json -AsHashtable -Depth 32 -DateKind String
    $badReceipt.target.cycle_cli.sha256 = ('0' * 64)
    $badReceiptPath = Join-Path $testRoot 'bad-receipt.json'
    [IO.File]::WriteAllText($badReceiptPath, ($badReceipt | ConvertTo-Json -Depth 32), [Text.UTF8Encoding]::new($false))

    $common = @{
        RunDirectory=$run; LauncherEntryPath=$targetLauncherEntry; LauncherModulePath=$launcherModule
        CycleModulePath=$targetCycleModule; CycleCliPath=$targetCycleCli; ProjectModulePath=$projectModule
        CanaryHostPath=$canaryHost; CanaryEntryPath=$canaryEntry
    }
    Assert-ThrowsLike { Invoke-MathResearchLegacyV1CompatMigration -Action Analyze -ReceiptFile $badReceiptPath @common } 'bytes differ from the receipt' 'A target-bundle hash mismatch was accepted.'
    Assert-True ((Get-Sha256HexFromFile -LiteralPath $manifestPath) -ceq $primaryHash) 'Blocked analysis changed the source manifest.'
    $analysis = Invoke-MathResearchLegacyV1CompatMigration -Action Analyze -ReceiptFile $receiptPath @common
    Assert-True ([string]$analysis.Status -ceq 'ready_to_apply') 'Valid compatibility analysis did not report ready_to_apply.'
    $applied = Invoke-MathResearchLegacyV1CompatMigration -Action Apply -ReceiptFile $receiptPath @common
    Assert-True ([string]$applied.Status -ceq 'applied') 'Compatibility migration did not apply.'
    $verified = Invoke-MathResearchLegacyV1CompatMigration -Action Verify -ReceiptFile $receiptPath @common
    Assert-True ([string]$verified.Status -ceq 'already_applied') 'Compatibility migration did not verify idempotently.'
    $readBack = Read-SignedJsonPayload -LiteralPath $manifestPath
    Assert-True ([string]$readBack.Payload.thread_id -ceq $threadId) 'Compatibility migration changed the thread id.'
    Assert-True ([string]$readBack.Payload.cycle_ledger.contract_binding_sha256 -ceq $binding) 'Compatibility migration changed the contract binding.'
    Assert-True ([int]$readBack.Payload.cycle_ledger.checkpoint.attempt_count -eq 0 -and [int]$readBack.Payload.cycle_ledger.checkpoint.total_round_count -eq 0) 'Compatibility migration changed counters.'
    Assert-True ([string]$readBack.Payload.config.approval_mode -ceq 'approve_for_me') 'Compatibility migration did not bind approve_for_me.'
    $args = New-CodexGlobalArguments -RunDirectory $run -Model 'gpt-5.6-sol' -ReasoningEffort xhigh -Sandbox workspace-write -AllowWebSearch:$false -EnableMultiAgent:$false -MaxChildAgents 1
    Assert-True ($args -contains '--approve-for-me') 'Compatibility launcher does not emit literal --approve-for-me.'
    Assert-True (-not (($args -join ' ') -match '(?:^|\s)-a\s+never(?:\s|$)')) 'Compatibility launcher silently retained approval=never.'
    [pscustomobject]@{ ok=$true; tests=10; blocked_paths=1; attempt_count=0; total_round_count=0 } | ConvertTo-Json
}
finally {
    $full = [IO.Path]::GetFullPath($testRoot)
    $temp = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if ($full.StartsWith($temp, [StringComparison]::OrdinalIgnoreCase) -and (Test-Path -LiteralPath $full)) { Remove-Item -LiteralPath $full -Recurse -Force }
}
