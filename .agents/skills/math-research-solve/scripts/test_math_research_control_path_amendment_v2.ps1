[CmdletBinding()]
param()

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)

function Assert-True { param([bool]$Condition,[string]$Message); if(-not$Condition){throw $Message} }
function Assert-ThrowsLike { param([scriptblock]$Action,[string]$Pattern,[string]$Message);try{&$Action;throw "Expected failure was not raised: $Message"}catch{if($_.Exception.Message-notlike"*$Pattern*"){throw "$Message Actual: $($_.Exception.Message)"}} }
function New-Binding { param([string]$Path);[ordered]@{path=[IO.Path]::GetFullPath($Path);sha256=Get-Sha256HexFromFile -LiteralPath $Path} }

$launcherModule=Join-Path $PSScriptRoot 'MathResearchLauncherLegacyV1Compat.psm1'
$priorMigrationModule=Join-Path $PSScriptRoot 'MathResearchLegacyV1CompatMigration.psm1'
$amendmentModule=Join-Path $PSScriptRoot 'MathResearchLegacyV1ControlPathAmendmentV2.psm1'
$argvModule=Join-Path $PSScriptRoot 'MathResearchApproveForMeArgvCompatV2.psm1'
Import-Module $launcherModule -Force -DisableNameChecking
Import-Module $priorMigrationModule -Force -DisableNameChecking
Import-Module $amendmentModule -Force -DisableNameChecking
Import-Module $argvModule -Force -DisableNameChecking
if(-not(Test-Path -LiteralPath (Get-ManifestKeyPath) -PathType Leaf)){throw 'Control-path regression requires the installed DPAPI manifest key.'}

$testRoot=Join-Path ([IO.Path]::GetTempPath()) ('math-research-control-path-v2-'+[Guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($testRoot)|Out-Null
try{
    $run=Join-Path $testRoot 'run';[IO.Directory]::CreateDirectory($run)|Out-Null
    $sourceLauncherEntry=Join-Path $PSScriptRoot 'launch_math_research.ps1'
    $sourceLauncherModule=Join-Path $PSScriptRoot 'MathResearchLauncher.psm1'
    $sourceCycleModule=Join-Path $PSScriptRoot 'MathResearchCycleLedger.psm1'
    $sourceCycleCli=Join-Path $PSScriptRoot 'invoke_math_research_cycle.ps1'
    $projectModule=Join-Path $PSScriptRoot 'MathResearchProjectArchive.psm1'
    $priorLauncherEntry=Join-Path $PSScriptRoot 'launch_math_research_legacy_v1_compat.ps1'
    $targetLauncherEntry=Join-Path $PSScriptRoot 'launch_math_research_legacy_v1_compat_v2.ps1'
    $targetCycleModule=Join-Path $PSScriptRoot 'MathResearchCycleLedgerLegacyV1Compat.psm1'
    $targetCycleCli=Join-Path $PSScriptRoot 'invoke_math_research_cycle_legacy_v1_compat.ps1'
    $priorCanaryHost=Join-Path $PSScriptRoot 'invoke_math_research_legacy_v1_compat_canary_host.ps1'
    $targetCanaryHost=Join-Path $PSScriptRoot 'invoke_math_research_legacy_v1_compat_canary_host_v2.ps1'
    $canaryModule=Join-Path $PSScriptRoot 'MathResearchLauncherV2.psm1'
    $canaryEntry=Join-Path $PSScriptRoot 'invoke_math_research_canary_v2.ps1'
    $amendmentCli=Join-Path $PSScriptRoot 'invoke_math_research_legacy_v1_control_path_amendment_v2.ps1'
    $threadId=[Guid]::NewGuid().ToString('D');$binding=('a'*64);$goalHash=('b'*64);$headHash=('c'*64)
    $checkpoint=[ordered]@{ledger_schema_version=1;head_sequence=0;head_payload_sha256=$headHash;attempt_count=0;audit_count=0;total_round_count=0;attempts_since_last_audit=0;audit_due=$false;clean_return=$true;completion_authorized=$false}
    $manifest=[ordered]@{
        schema_version=1;run_id='synthetic-control-path-run';revision=3;created_at_utc='2026-01-01T00:00:00.1200000Z';updated_at_utc='2026-01-01T00:00:01.1200000Z';prompt_version='v6';contract_version='v1';run_directory=$run;status='failed';exit_reason='synthetic operational failure';thread_id=$threadId
        project=[ordered]@{project_id='synthetic-project';directory=$testRoot;directory_name='synthetic-project';archive_schema=1;identity_sha256=('d'*64)}
        config=[ordered]@{approval_policy='never';model='gpt-5.6-sol';reasoning_effort='xhigh';web_search='allowed';total_round_budget=9;attempt_budget=6;audit_interval_attempts=2;round_budget_enforcement='cycle_controller';max_runtime_minutes=0;max_child_agents=2;max_total_agents=3;agent_stages=@(2)}
        goal=[ordered]@{objective_sha256=$goalHash;confirmation='model_reported_via_nonce_marker';persistence_verified=$false}
        cycle_ledger=[ordered]@{contract_binding_sha256=$binding;module=New-Binding $sourceCycleModule;cli=New-Binding $sourceCycleCli;project_module=New-Binding $projectModule;checkpoint=$checkpoint};process=$null
    }
    $manifestPath=Join-Path $run 'run.json';Write-SignedJsonPayload -LiteralPath $manifestPath -Payload $manifest;Copy-Item -LiteralPath $manifestPath -Destination "$manifestPath.bak"
    $priorReceipt=[ordered]@{
        schema_version=1;protocol='math-research-legacy-v1-compat-migration/v1';migration_id='synthetic-prior-migration';action='resume_prompt_v6_with_compat_bundle';archive_directory_name='compat-migration-v1'
        project=[ordered]@{project_id='synthetic-project';directory=$testRoot};run=[ordered]@{id='synthetic-control-path-run';directory=$run;thread_id=$threadId};contract=[ordered]@{version='v1';binding_sha256=$binding};goal=[ordered]@{objective_sha256=$goalHash}
        source=[ordered]@{status='failed';manifest_primary_sha256=Get-Sha256HexFromFile $manifestPath;manifest_backup_sha256=Get-Sha256HexFromFile "$manifestPath.bak";launcher_entry=New-Binding $sourceLauncherEntry;launcher_module=New-Binding $sourceLauncherModule;cycle_module=New-Binding $sourceCycleModule;cycle_cli=New-Binding $sourceCycleCli;project_module=New-Binding $projectModule;counters=$checkpoint}
        target=[ordered]@{launcher_entry=New-Binding $priorLauncherEntry;launcher_module=New-Binding $launcherModule;cycle_module=New-Binding $targetCycleModule;cycle_cli=New-Binding $targetCycleCli;project_module=New-Binding $projectModule;canary_host=New-Binding $priorCanaryHost;canary_entry=New-Binding $canaryEntry}
        authorization=[ordered]@{approval_mode_from='never';approval_mode_to='approve_for_me';objective_changed=$false;quantifiers_changed=$false;counters_reset=$false}
    }
    $priorReceiptPath=Join-Path $testRoot 'prior-receipt.json';[IO.File]::WriteAllText($priorReceiptPath,($priorReceipt|ConvertTo-Json -Depth 32),[Text.UTF8Encoding]::new($false))
    $priorCommon=@{RunDirectory=$run;LauncherEntryPath=$priorLauncherEntry;LauncherModulePath=$launcherModule;CycleModulePath=$targetCycleModule;CycleCliPath=$targetCycleCli;ProjectModulePath=$projectModule;CanaryHostPath=$priorCanaryHost;CanaryEntryPath=$canaryEntry}
    Invoke-MathResearchLegacyV1CompatMigration -Action Apply -ReceiptFile $priorReceiptPath @priorCommon|Out-Null
    $sourcePrimary=Get-Sha256HexFromFile $manifestPath;$sourceBackup=Get-Sha256HexFromFile "$manifestPath.bak"
    $paths=@{PriorLauncherEntry=$priorLauncherEntry;LauncherEntry=$targetLauncherEntry;LauncherModule=$launcherModule;ArgvCompatModule=$argvModule;PriorCanaryHost=$priorCanaryHost;CanaryHost=$targetCanaryHost;CanaryModule=$canaryModule;CanaryEntry=$canaryEntry;CycleModule=$targetCycleModule;CycleCli=$targetCycleCli;ProjectModule=$projectModule;AmendmentModule=$amendmentModule;AmendmentCli=$amendmentCli}
    $receipt=[ordered]@{
        schema_version=1;protocol='math-research-legacy-v1-control-path-amendment/v2';amendment_id='synthetic-control-path-v2';action='omit_explicit_sandbox_with_approve_for_me';archive_directory_name='compat-control-path-v2'
        project=[ordered]@{project_id='synthetic-project';directory=$testRoot};run=[ordered]@{id='synthetic-control-path-run';directory=$run;thread_id=$threadId};contract=[ordered]@{version='v1';binding_sha256=$binding};goal=[ordered]@{objective_sha256=$goalHash};prior_migration=[ordered]@{receipt_sha256=Get-Sha256HexFromFile $priorReceiptPath}
        source=[ordered]@{status='failed';manifest_primary_sha256=$sourcePrimary;manifest_backup_sha256=$sourceBackup;counters=$checkpoint}
        target=[ordered]@{launcher_entry=New-Binding $targetLauncherEntry;launcher_module=New-Binding $launcherModule;argv_compat_module=New-Binding $argvModule;canary_host=New-Binding $targetCanaryHost;canary_module=New-Binding $canaryModule;canary_entry=New-Binding $canaryEntry;cycle_cli=New-Binding $targetCycleCli;amendment_module=New-Binding $amendmentModule;amendment_cli=New-Binding $amendmentCli}
        authorization=[ordered]@{approval_mode='approve_for_me';effective_sandbox='workspace-write';explicit_sandbox_argument_omitted=$true;objective_changed=$false;quantifiers_changed=$false;counters_reset=$false;permission_scope_expanded=$false}
    }
    $receiptPath=Join-Path $testRoot 'control-path-receipt.json';[IO.File]::WriteAllText($receiptPath,($receipt|ConvertTo-Json -Depth 32),[Text.UTF8Encoding]::new($false))
    $bad=($receipt|ConvertTo-Json -Depth 32)|ConvertFrom-Json -AsHashtable -Depth 32 -DateKind String;$bad.target.argv_compat_module.sha256=('0'*64);$badPath=Join-Path $testRoot 'bad-control-path-receipt.json';[IO.File]::WriteAllText($badPath,($bad|ConvertTo-Json -Depth 32),[Text.UTF8Encoding]::new($false))
    Assert-ThrowsLike {Invoke-MathResearchLegacyV1ControlPathAmendmentV2 -Action Analyze -RunDirectory $run -ReceiptFile $badPath -PriorReceiptFile $priorReceiptPath -Paths $paths} 'bytes differ from the receipt' 'A control-path target hash mismatch was accepted.'
    Assert-True ((Get-Sha256HexFromFile $manifestPath)-ceq$sourcePrimary) 'Blocked control-path analysis changed the source manifest.'
    Assert-True ([string](Invoke-MathResearchLegacyV1ControlPathAmendmentV2 -Action Analyze -RunDirectory $run -ReceiptFile $receiptPath -PriorReceiptFile $priorReceiptPath -Paths $paths).Status-ceq'ready_to_apply') 'Control-path Analyze was not ready.'
    Assert-True ([string](Invoke-MathResearchLegacyV1ControlPathAmendmentV2 -Action Apply -RunDirectory $run -ReceiptFile $receiptPath -PriorReceiptFile $priorReceiptPath -Paths $paths).Status-ceq'applied') 'Control-path Apply failed.'
    Assert-True ([string](Invoke-MathResearchLegacyV1ControlPathAmendmentV2 -Action Verify -RunDirectory $run -ReceiptFile $receiptPath -PriorReceiptFile $priorReceiptPath -Paths $paths).Status-ceq'already_applied') 'Control-path Verify was not idempotent.'
    $readBack=(Read-SignedJsonPayload $manifestPath).Payload;Assert-True ([string]$readBack.thread_id-ceq$threadId) 'Control-path amendment changed thread.';Assert-True ([string]$readBack.cycle_ledger.contract_binding_sha256-ceq$binding) 'Control-path amendment changed contract.';Assert-True ([int]$readBack.cycle_ledger.checkpoint.attempt_count-eq0-and[int]$readBack.cycle_ledger.checkpoint.total_round_count-eq0) 'Control-path amendment changed counters.'
    $legacy=Import-Module $launcherModule -Force -DisableNameChecking -PassThru;Enable-MathResearchApproveForMeArgvCompatV2 -TargetModule $legacy -Flavor legacy-v1-compat;$argv=& $legacy { param($d) New-CodexGlobalArguments -RunDirectory $d -Model 'gpt-5.6-sol' -ReasoningEffort xhigh -Sandbox workspace-write -AllowWebSearch:$false -EnableMultiAgent:$false -MaxChildAgents 1 } $run;Assert-MathResearchApproveForMeArgvCompatV2 -Arguments $argv|Out-Null
    [pscustomobject]@{ok=$true;tests=12;blocked_paths=1;explicit_sandbox_arguments=0;attempt_count=0;total_round_count=0}|ConvertTo-Json
}
finally{$full=[IO.Path]::GetFullPath($testRoot);$temp=[IO.Path]::GetFullPath([IO.Path]::GetTempPath());if($full.StartsWith($temp,[StringComparison]::OrdinalIgnoreCase)-and(Test-Path -LiteralPath $full)){Remove-Item -LiteralPath $full -Recurse -Force}}
