[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RealProjectDirectory
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)

$script:assertions=0
function Assert-True([bool]$Condition,[string]$Message){$script:assertions++;if(-not$Condition){throw "ASSERT: $Message"}}
function Assert-Equal($Actual,$Expected,[string]$Message){$script:assertions++;if([string]$Actual-cne[string]$Expected){throw "ASSERT: $Message (actual='$Actual', expected='$Expected')"}}
function Get-Hash([string]$Path){return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
function Get-TextHash([string]$Text){return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.UTF8Encoding]::new($false).GetBytes($Text))).ToLowerInvariant()}
function Read-Json([string]$Path){return Get-Content -LiteralPath $Path -Raw -Encoding UTF8|ConvertFrom-Json -AsHashtable -Depth 100 -DateKind String}
function Get-TreeHash([string]$Root){
    $full=[IO.Path]::GetFullPath($Root).TrimEnd('\','/');$lines=[Collections.Generic.List[string]]::new()
    foreach($file in @(Get-ChildItem -LiteralPath $full -Recurse -File -Force|Sort-Object FullName)){$relative=$file.FullName.Substring($full.Length+1).Replace('\','/');$lines.Add("$relative`t$(Get-Hash $file.FullName)")}
    return Get-TextHash (($lines-join"`n")+"`n")
}
function ConvertTo-CanonicalJson($Value){return (($Value|ConvertTo-Json -Depth 100 -Compress)+"`n")}
function Write-Json([string]$Path,$Value){[IO.File]::WriteAllText($Path,(ConvertTo-CanonicalJson $Value),[Text.UTF8Encoding]::new($false))}
function Write-IntegrityEnvelope([string]$Path,$Payload){
    $stable=(ConvertTo-CanonicalJson $Payload)|ConvertFrom-Json -AsHashtable -Depth 100 -DateKind String
    $payloadHash=Get-TextHash ($stable|ConvertTo-Json -Depth 100 -Compress)
    $envelope=[ordered]@{integrity_schema=1;payload=$stable;integrity=[ordered]@{algorithm='HMAC-SHA256';key_protection='test-fixture-not-authenticated';payload_sha256=$payloadHash;hmac_sha256=('0'*64)}}
    Write-Json $Path $envelope
    return $payloadHash
}
function Copy-Fixture([string]$Source,[string]$Destination){
    New-Item -ItemType Directory -Path $Destination|Out-Null
    foreach($item in @(Get-ChildItem -LiteralPath $Source -Force)){Copy-Item -LiteralPath $item.FullName -Destination $Destination -Recurse -Force}
}
function Get-FixtureRun([string]$Project){
    $head=Read-Json (Join-Path $Project 'project.json')
    return Join-Path $Project ([string]$head.active_run.path).Replace('/',[IO.Path]::DirectorySeparatorChar)
}
function Update-PrimaryManifest([string]$Project,[scriptblock]$Mutator){
    $run=Get-FixtureRun $Project;$path=Join-Path $run 'run.json';$envelope=Read-Json $path
    & $Mutator $envelope.payload
    [void](Write-IntegrityEnvelope $path $envelope.payload)
}
function Add-ClosedAttemptAuditLedger([string]$Project){
    $run=Get-FixtureRun $Project;$ledgerDir=Join-Path $run 'cycle-ledger';$genesis=Read-Json (Join-Path $ledgerDir '00000000.json')
    $previous=[string]$genesis.integrity.payload_sha256;$runId=[string]$genesis.payload.run_id
    $events=@(
        [ordered]@{event_type='ATTEMPT_START';data=[ordered]@{attempt_id='fixture-attempt-1'}},
        [ordered]@{event_type='ATTEMPT_END';data=[ordered]@{attempt_id='fixture-attempt-1';outcome='failed'}},
        [ordered]@{event_type='AUDIT_START';data=[ordered]@{audit_id='fixture-audit-1'}},
        [ordered]@{event_type='AUDIT_END';data=[ordered]@{audit_id='fixture-audit-1';completion_authorized=$false}}
    )
    for($i=1;$i-le$events.Count;$i++){
        $payload=[ordered]@{ledger_schema_version=1;sequence=$i;run_id=$runId;event_type=[string]$events[$i-1].event_type;previous_payload_sha256=$previous;recorded_at_utc=('2026-08-09T12:00:{0:D2}Z'-f$i);data=$events[$i-1].data}
        $previous=Write-IntegrityEnvelope (Join-Path $ledgerDir ('{0:D8}.json'-f$i)) $payload
    }
    Update-PrimaryManifest $Project {param($payload)
        $checkpoint=$payload.cycle_ledger.checkpoint
        $checkpoint.head_sequence=4;$checkpoint.head_payload_sha256=$previous
        $checkpoint.attempt_count=1;$checkpoint.audit_count=1;$checkpoint.total_round_count=2;$checkpoint.attempts_since_last_audit=0;$checkpoint.audit_due=$false
        if($checkpoint.Contains('clean_return')){$checkpoint.clean_return=$true}
    }
}
function Rebind-BadCompatibilityReceiptPrefix([string]$Project){
    $run=Get-FixtureRun $Project
    $compatPath=Join-Path $run 'compat-migration-v1\migration-receipt.json';$compat=Read-Json $compatPath;$compat.source.counters.attempt_count=1;$compat.source.counters.total_round_count=1;$compat.source.counters.attempts_since_last_audit=1;Write-Json $compatPath $compat;$compatHash=Get-Hash $compatPath
    $controlPath=Join-Path $run 'control-path-amendment-v2\control-path-receipt.json';$control=Read-Json $controlPath;$control.prior_migration.receipt_sha256=$compatHash;Write-Json $controlPath $control;$controlHash=Get-Hash $controlPath
    Update-PrimaryManifest $Project {param($payload)$payload.compatibility_migration.receipt_sha256=$compatHash;$payload.control_path_amendment_v2.receipt_sha256=$controlHash}
}
function Set-WebDeniedFixture([string]$Project){
    $headPath=Join-Path $Project 'project.json';$head=Read-Json $headPath
    $contractPath=Join-Path $Project ([string]$head.active_contract.path).Replace('/',[IO.Path]::DirectorySeparatorChar)
    $contract=[IO.File]::ReadAllText($contractPath,[Text.UTF8Encoding]::new($false,$true))
    if(([regex]::Matches($contract,'(?m)^web_search:\s*allowed\s*$')).Count-ne1){throw 'Web-denied fixture could not identify one Contract metadata line.'}
    $contract=[regex]::Replace($contract,'(?m)^web_search:\s*allowed\s*$','web_search: denied')
    [IO.File]::WriteAllText($contractPath,$contract,[Text.UTF8Encoding]::new($false));$contractHash=Get-Hash $contractPath
    $head.active_contract.sha256=$contractHash;Write-Json $headPath $head
    $run=Get-FixtureRun $Project;$genesisPath=Join-Path $run 'cycle-ledger\00000000.json';$genesis=Read-Json $genesisPath;$genesis.payload.data.contract_binding_sha256=$contractHash;$headHash=Write-IntegrityEnvelope $genesisPath $genesis.payload
    Update-PrimaryManifest $Project {param($payload)
        $payload.config.web_search='denied';$payload.inputs.prompt.contract_binding_sha256=$contractHash;$payload.cycle_ledger.contract_binding_sha256=$contractHash
        $payload.cycle_ledger.checkpoint.head_payload_sha256=$headHash
        [void]$payload.Remove('compatibility_migration');[void]$payload.Remove('control_path_amendment_v2')
    }
}
function Invoke-PwshJson([string]$Script,[string[]]$Arguments,[int]$ExpectedExit=0){
    $psi=[Diagnostics.ProcessStartInfo]::new();$psi.FileName=(Get-Process -Id $PID).Path;$psi.UseShellExecute=$false;$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true;$psi.CreateNoWindow=$true
    foreach($arg in @('-NoProfile','-NonInteractive','-File',$Script)+$Arguments){[void]$psi.ArgumentList.Add($arg)}
    $process=[Diagnostics.Process]::Start($psi);$stdout=$process.StandardOutput.ReadToEnd();$stderr=$process.StandardError.ReadToEnd();$process.WaitForExit()
    if($process.ExitCode-ne$ExpectedExit){throw "Unexpected exit $($process.ExitCode), expected $ExpectedExit. stderr=$stderr stdout=$stdout"}
    if([string]::IsNullOrWhiteSpace($stdout)){throw "Script emitted no JSON. stderr=$stderr"}
    return ($stdout.Trim()|ConvertFrom-Json -AsHashtable -Depth 100 -DateKind String)
}

$builder=Join-Path $PSScriptRoot 'build_math_research_legacy_successor_v8.ps1'
$helper=Join-Path $PSScriptRoot 'commit_math_research_head_v8.ps1'
$startup=Join-Path $PSScriptRoot 'invoke_math_research_startup_v3.ps1'
$temp=Join-Path ([IO.Path]::GetTempPath()) ('math-research-legacy-successor-v8-test-'+[guid]::NewGuid().ToString('N'))
$goalRaw='Continue the exact inherited research project under this current Goal Host.'
$goalHash=Get-TextHash $goalRaw

try{
    if(-not(Test-Path -LiteralPath $RealProjectDirectory -PathType Container)){throw "Real read-only fixture is missing: $RealProjectDirectory"}
    New-Item -ItemType Directory -Path $temp|Out-Null
    $sourceHash=Get-TreeHash $RealProjectDirectory
    $sourceHeadHash=Get-Hash (Join-Path $RealProjectDirectory 'project.json')

    # Hash mismatch fails before any project write.
    $bad=Invoke-PwshJson $builder @('-ProjectDirectory',$RealProjectDirectory,'-GoalObjectiveRaw',$goalRaw,'-GoalObjectiveSha256',('0'*64),'-DryRun') 1
    Assert-Equal $bad.reason 'goal_objective_hash_mismatch' 'wrong current-Goal hash fails closed'
    Assert-Equal (Get-TreeHash $RealProjectDirectory) $sourceHash 'wrong Goal hash leaves source unchanged'

    # Read-only discovery over the complete real archive.
    $dry=Invoke-PwshJson $builder @('-ProjectDirectory',$RealProjectDirectory,'-GoalObjectiveRaw',$goalRaw,'-GoalObjectiveSha256',$goalHash,'-DryRun')
    Assert-Equal $dry.reason 'dry_run_verified' 'real archive dry-run passes'
    Assert-True ([long]$dry.inherited_artifact_count-ge600) 'real archive inventory covers 600+ artifacts'
    Assert-Equal $dry.source_project_tree_sha256_before $sourceHash 'builder and independent tree hash agree before dry-run'
    Assert-Equal $dry.source_project_tree_sha256_after $sourceHash 'dry-run source tree remains unchanged'

    # A receipt may bind an earlier prefix: replay all later closed events and derive counters from the ledger head.
    $progress=Join-Path $temp 'ledger-progress';Copy-Fixture $RealProjectDirectory $progress;Add-ClosedAttemptAuditLedger $progress
    $progressOut=Join-Path $temp 'ledger-progress-output'
    $progressBuild=Invoke-PwshJson $builder @('-ProjectDirectory',$progress,'-GoalObjectiveRaw',$goalRaw,'-GoalObjectiveSha256',$goalHash,'-OutputDirectory',$progressOut)
    Assert-True ([bool]$progressBuild.built) 'strict replay accepts a valid closed seq>0 ledger with receipts at an earlier prefix'
    $progressEnvelope=Read-Json (Join-Path $progressOut ([string]$progressBuild.effective_envelope.path).Replace('/',[IO.Path]::DirectorySeparatorChar))
    Assert-Equal $progressEnvelope.counters.attempt_count 1 'strict replay derives attempt_count from events'
    Assert-Equal $progressEnvelope.counters.audit_count 1 'strict replay derives audit_count from events'
    Assert-Equal $progressEnvelope.counters.total_round_count 2 'strict replay derives total_round_count from events'
    Assert-Equal $progressEnvelope.counters.attempts_since_last_audit 0 'strict replay applies AUDIT_END reset'
    Assert-Equal $progressEnvelope.counters.audit_due $false 'strict replay clears audit_due at AUDIT_END'

    $gap=Join-Path $temp 'ledger-gap';Copy-Fixture $progress $gap;$gapLedger=Join-Path (Get-FixtureRun $gap) 'cycle-ledger';Move-Item -LiteralPath (Join-Path $gapLedger '00000003.json') -Destination (Join-Path $gapLedger '00000005.json')
    $gapResult=Invoke-PwshJson $builder @('-ProjectDirectory',$gap,'-GoalObjectiveRaw',$goalRaw,'-GoalObjectiveSha256',$goalHash,'-DryRun') 1
    Assert-Equal $gapResult.reason 'ledger_sequence_invalid' 'ledger gap/extra numeric JSON fails closed'

    $chain=Join-Path $temp 'ledger-chain';Copy-Fixture $progress $chain;$chainEventPath=Join-Path (Get-FixtureRun $chain) 'cycle-ledger\00000004.json';$chainEvent=Read-Json $chainEventPath;$chainEvent.payload.previous_payload_sha256=('f'*64);[void](Write-IntegrityEnvelope $chainEventPath $chainEvent.payload)
    $chainResult=Invoke-PwshJson $builder @('-ProjectDirectory',$chain,'-GoalObjectiveRaw',$goalRaw,'-GoalObjectiveSha256',$goalHash,'-DryRun') 1
    Assert-Equal $chainResult.reason 'ledger_chain_invalid' 'broken previous-payload hash chain fails closed'

    $counter=Join-Path $temp 'ledger-counter';Copy-Fixture $progress $counter;Update-PrimaryManifest $counter {param($payload)$payload.cycle_ledger.checkpoint.attempt_count=2;$payload.cycle_ledger.checkpoint.total_round_count=3}
    $counterResult=Invoke-PwshJson $builder @('-ProjectDirectory',$counter,'-GoalObjectiveRaw',$goalRaw,'-GoalObjectiveSha256',$goalHash,'-DryRun') 1
    Assert-Equal $counterResult.reason 'counter_conflict' 'manifest counter that differs from strict replay fails closed'

    $badReceipt=Join-Path $temp 'ledger-receipt-prefix';Copy-Fixture $progress $badReceipt;Rebind-BadCompatibilityReceiptPrefix $badReceipt
    $receiptResult=Invoke-PwshJson $builder @('-ProjectDirectory',$badReceipt,'-GoalObjectiveRaw',$goalRaw,'-GoalObjectiveSha256',$goalHash,'-DryRun') 1
    Assert-Equal $receiptResult.reason 'counter_conflict' 'cross-bound receipt counters that differ from their ledger prefix fail closed'

    # Build only in a copied archive; authoritative project.json remains legacy until helper CAS.
    $copy=Join-Path $temp 'five-sixth-powers-copy'
    $build=Invoke-PwshJson $builder @('-ProjectDirectory',$RealProjectDirectory,'-GoalObjectiveRaw',$goalRaw,'-GoalObjectiveSha256',$goalHash,'-OutputDirectory',$copy)
    Assert-True ([bool]$build.built) 'copied real archive successor build succeeds'
    Assert-Equal $build.reason 'staged_successor_ready_for_goal_gated_commit' 'builder reports staging-only readiness'
    Assert-Equal (Get-Hash (Join-Path $copy 'project.json')) $sourceHeadHash 'copied project head is unchanged before helper'
    Assert-Equal (Get-TreeHash $RealProjectDirectory) $sourceHash 'real source tree unchanged after copied build'
    Assert-True ([long]$build.inherited_artifact_count-ge600) 'copied build retains full inventory'

    $candidate=Read-Json $build.candidate_head_file
    Assert-Equal $candidate.schema 'math-research-project/v8' 'candidate head schema'
    Assert-Equal $candidate.control_generation 1 'generationless legacy activates g1'
    Assert-Equal $candidate.active_run.id 'successor-g0001' 'successor run is additive and distinct'
    $envelopePath=Join-Path $copy ([string]$build.effective_envelope.path).Replace('/',[IO.Path]::DirectorySeparatorChar)
    $mappingPath=Join-Path $copy ([string]$build.migration_map.path).Replace('/',[IO.Path]::DirectorySeparatorChar)
    Assert-Equal (Get-Hash $envelopePath) $build.effective_envelope.sha256 'effective envelope pointer hashes exact bytes'
    Assert-Equal (Get-Hash $mappingPath) $build.migration_map.sha256 'migration map pointer hashes exact bytes'
    $envelope=Read-Json $envelopePath;$mapping=Read-Json $mappingPath
    Assert-Equal $envelope.schema 'math-research-effective-predecessor-envelope/v8' 'effective envelope schema'
    Assert-Equal $envelope.permissions.approval_mode 'approve_for_me' 'applied receipt precedence yields effective approval mode'
    Assert-Equal $envelope.budgets.attempt_budget 24 'attempt ceiling preserved'
    Assert-Equal $envelope.budgets.total_round_budget 33 'total-round ceiling preserved'
    Assert-Equal $envelope.counters.attempt_count 0 'attempt consumption preserved'
    Assert-Equal $envelope.counters.total_round_count 0 'round consumption preserved'
    Assert-Equal @($envelope.amendments).Count 2 'compatibility and control-v2 receipt chain recorded'
    Assert-Equal $mapping.schema 'math-research-control-migration-map/v8' 'migration map schema'
    Assert-True (@($mapping.retired_bindings|Where-Object{$_.name-eq'child_goal_created_inside_codex_exec'}).Count-eq1) 'child Goal control is explicitly retired'
    Assert-True (@($mapping.control_mapping|Where-Object{$_.mapping-eq'replace_with_goal_host_v8'}).Count-ge3) 'control mechanisms map to Goal Host v8'
    Assert-True (@($mapping.unresolved_gaps|Where-Object{$_.mapping-eq'fail_closed_unimplemented'}).Count-eq1) 'future v8 envelope expansion is fail-closed'
    $contractPath=Join-Path $copy ([string]$candidate.active_contract.path).Replace('/',[IO.Path]::DirectorySeparatorChar)
    $contractText=[IO.File]::ReadAllText($contractPath,[Text.UTF8Encoding]::new($false,$true))-replace"`r`n","`n"
    $policyMatch=[regex]::Match($contractText,'(?s)<!-- math-research-cycle-policy\n(?<json>.*?)\n-->')
    $ticketMatch=[regex]::Match($contractText,'(?s)<!-- math-research-initial-tickets\n(?<json>.*?)\n-->')
    Assert-True $policyMatch.Success 'Contract exposes exact cycle-policy block'
    Assert-True $ticketMatch.Success 'Contract exposes exact initial-ticket block'
    $v8Policy=$policyMatch.Groups['json'].Value|ConvertFrom-Json -AsHashtable -Depth 100 -DateKind String
    $v8Ticket=(($ticketMatch.Groups['json'].Value|ConvertFrom-Json -AsHashtable -Depth 100 -DateKind String).tickets)[0]
    Assert-Equal $v8Policy.max_ticket_tool_calls 32 'cycle policy freezes ticket tool-call cap'
    Assert-Equal $v8Policy.max_ticket_output_bytes 8388608 'cycle policy freezes ticket output-byte cap'
    Assert-Equal (@($v8Policy.allowed_worker_tools)-join'|') 'apply_patch|collaboration.spawn_agent|collaboration.send_message|collaboration.wait_agent|shell_command|web__run' 'web-allowed policy publishes the exact global worker-tool set'
    Assert-True ('apply_patch'-cin@($v8Policy.allowed_worker_tools)) 'cycle policy includes guarded file editing'
    Assert-True ('collaboration.spawn_agent'-cin@($v8Policy.allowed_worker_tools)) 'cycle policy includes collaboration worker dispatch'
    Assert-Equal @($v8Policy.allowed_worker_tools|Select-Object -Unique).Count @($v8Policy.allowed_worker_tools).Count 'worker-tool allowlist is duplicate-free'
    Assert-True (@($v8Ticket.allowed_tools|Where-Object{$_-cnotin@($v8Policy.allowed_worker_tools)}).Count-eq0) 'initial ticket tools are a policy subset'
    Assert-True ([long]$v8Ticket.resource_caps.tool_calls-le[long]$v8Policy.max_ticket_tool_calls) 'initial ticket tool cap is within policy'
    Assert-True ([long]$v8Ticket.resource_caps.max_output_bytes-le[long]$v8Policy.max_ticket_output_bytes) 'initial ticket output cap is within policy'

    $deniedSource=Join-Path $temp 'web-denied-source';Copy-Fixture $RealProjectDirectory $deniedSource;Set-WebDeniedFixture $deniedSource
    $deniedOutput=Join-Path $temp 'web-denied-output';$deniedBuild=Invoke-PwshJson $builder @('-ProjectDirectory',$deniedSource,'-GoalObjectiveRaw',$goalRaw,'-GoalObjectiveSha256',$goalHash,'-OutputDirectory',$deniedOutput)
    Assert-True ([bool]$deniedBuild.built) 'web-denied successor build succeeds'
    $deniedCandidate=Read-Json $deniedBuild.candidate_head_file;$deniedContractPath=Join-Path $deniedOutput ([string]$deniedCandidate.active_contract.path).Replace('/',[IO.Path]::DirectorySeparatorChar)
    $deniedText=[IO.File]::ReadAllText($deniedContractPath,[Text.UTF8Encoding]::new($false,$true));$deniedPolicyMatch=[regex]::Match($deniedText,'(?s)<!-- math-research-cycle-policy\n(?<json>.*?)\n-->');Assert-True $deniedPolicyMatch.Success 'web-denied Contract exposes cycle policy'
    $deniedPolicy=$deniedPolicyMatch.Groups['json'].Value|ConvertFrom-Json -AsHashtable -Depth 100 -DateKind String
    Assert-Equal (@($deniedPolicy.allowed_worker_tools)-join'|') 'apply_patch|collaboration.spawn_agent|collaboration.send_message|collaboration.wait_agent|shell_command' 'web-denied policy publishes the exact non-web global worker-tool set'
    Assert-True ('web__run'-cnotin@($deniedPolicy.allowed_worker_tools)) 'web-denied policy excludes web__run'

    # The actual live-mode route stages additively in the selected project. Exercise it on a second byte copy.
    $sameCopy=Join-Path $temp 'five-sixth-powers-same-project-copy';New-Item -ItemType Directory -Path $sameCopy|Out-Null
    foreach($item in @(Get-ChildItem -LiteralPath $RealProjectDirectory -Force)){Copy-Item -LiteralPath $item.FullName -Destination $sameCopy -Recurse -Force}
    Assert-Equal (Get-TreeHash $sameCopy) $sourceHash 'same-project fixture begins as exact byte copy'
    $interruptedIntentTemp=Join-Path $sameCopy 'state\build-intents\g0001.json.build-v8.tmp';New-Item -ItemType Directory -Path (Split-Path -Parent $interruptedIntentTemp) -Force|Out-Null;[IO.File]::WriteAllBytes($interruptedIntentTemp,[byte[]](1,2,3,4,5))
    $sameBuild=Invoke-PwshJson $builder @('-ProjectDirectory',$sameCopy,'-GoalObjectiveRaw',$goalRaw,'-GoalObjectiveSha256',$goalHash)
    Assert-True ([bool]$sameBuild.built) 'same-project additive staging succeeds on real archive copy'
    Assert-Equal $sameBuild.reason 'staged_successor_ready_for_goal_gated_commit' 'first same-project build is new staging'
    Assert-True (-not(Test-Path -LiteralPath $interruptedIntentTemp)) 'partial deterministic temp is safely replaced and consumed'
    Assert-Equal (Get-Hash (Join-Path $sameCopy 'project.json')) $sourceHeadHash 'same-project staging leaves authoritative head unchanged'
    Assert-Equal (Get-TreeHash $RealProjectDirectory) $sourceHash 'same-project staging copy leaves real source unchanged'

    # Simulate interruption before helper: remove one generated leaf, then retry same intent.
    $firstCandidateHash=[string]$sameBuild.candidate_head_sha256
    $candidateFull=[IO.Path]::GetFullPath([string]$sameBuild.candidate_head_file)
    if(-not$candidateFull.StartsWith(([IO.Path]::GetFullPath($sameCopy).TrimEnd('\','/')+[IO.Path]::DirectorySeparatorChar),[StringComparison]::OrdinalIgnoreCase)-or(Split-Path -Leaf $candidateFull)-cne'legacy-successor-g0001.json'){throw 'Unsafe candidate interruption target.'}
    Remove-Item -LiteralPath $candidateFull
    $repair=Invoke-PwshJson $builder @('-ProjectDirectory',$sameCopy,'-GoalObjectiveRaw',$goalRaw,'-GoalObjectiveSha256',$goalHash)
    Assert-Equal $repair.reason 'reused_staging_ready_for_goal_gated_commit' 'partial retry reuses intent and repairs missing file'
    Assert-Equal $repair.candidate_head_sha256 $firstCandidateHash 'repaired candidate hash equals first deterministic build'
    $reuse=Invoke-PwshJson $builder @('-ProjectDirectory',$sameCopy,'-GoalObjectiveRaw',$goalRaw,'-GoalObjectiveSha256',$goalHash)
    Assert-Equal $reuse.reason 'reused_staging_ready_for_goal_gated_commit' 'fully materialized retry reuses exact staging'
    Assert-Equal $reuse.candidate_head_sha256 $firstCandidateHash 'fully reused candidate hash is stable'

    $changedGoal='A materially different current Goal must not reuse this staging intent.';$changedHash=Get-TextHash $changedGoal
    $changed=Invoke-PwshJson $builder @('-ProjectDirectory',$sameCopy,'-GoalObjectiveRaw',$changedGoal,'-GoalObjectiveSha256',$changedHash) 1
    Assert-Equal $changed.reason 'build_intent_mismatch' 'different Goal cannot reuse staged successor'
    Assert-Equal (Get-Hash $candidateFull) $firstCandidateHash 'different Goal leaves candidate unchanged'

    $tamperPath=Join-Path $sameCopy 'runs\successor-g0001\evidence\control-migration-map.json';$tamperBytes=[IO.File]::ReadAllBytes($tamperPath)
    try{[IO.File]::WriteAllBytes($tamperPath,($tamperBytes+[byte]0x20));$tampered=Invoke-PwshJson $builder @('-ProjectDirectory',$sameCopy,'-GoalObjectiveRaw',$goalRaw,'-GoalObjectiveSha256',$goalHash) 1;Assert-Equal $tampered.reason 'staging_artifact_mismatch' 'different staged bytes fail closed without overwrite'}finally{[IO.File]::WriteAllBytes($tamperPath,$tamperBytes)}
    $postRestore=Invoke-PwshJson $builder @('-ProjectDirectory',$sameCopy,'-GoalObjectiveRaw',$goalRaw,'-GoalObjectiveSha256',$goalHash)
    Assert-Equal $postRestore.candidate_head_sha256 $firstCandidateHash 'restored exact staging remains reusable'

    # The production helper accepts the exact same-project staged graph and alone switches the head.
    $commit=Invoke-PwshJson $helper @('-ProjectDirectory',$sameCopy,'-CandidateHeadFile',[string]$postRestore.candidate_head_file,'-ExpectedOldSha256',[string]$postRestore.expected_old_sha256,'-ExpectedOldControlGeneration',[string]$postRestore.expected_old_control_generation,'-ExpectedNewControlGeneration',[string]$postRestore.expected_new_control_generation)
    Assert-True ([bool]$commit.committed) "helper commits builder graph ($($commit.reason): $($commit.detail))"
    Assert-Equal (Get-Hash (Join-Path $sameCopy 'project.json')) $commit.new_sha256 'helper commit exact readback hash'

    # Startup accepts the helper-committed real successor and selects the current Goal Host path.
    $start=Invoke-PwshJson $startup @('-ProjectDirectory',$sameCopy,'-GoalStatus','active')
    Assert-Equal $start.startup_class 'goal_host_ready' "startup accepts builder→helper graph ($($start.recovery_reason))"
    Assert-True ([bool]$start.legacy_archive_detected) 'startup reports inherited legacy archive'
    Assert-True (-not[bool]$start.successor_v8_requires_explicit_new_active_goal) 'activated successor does not demand another Goal'
    Assert-Equal (Get-TreeHash $RealProjectDirectory) $sourceHash 'real source tree remains byte-identical after full copied e2e'

    foreach($path in @($builder,$PSCommandPath)){$tokens=$null;$errors=$null;[Management.Automation.Language.Parser]::ParseFile($path,[ref]$tokens,[ref]$errors)|Out-Null;Assert-Equal @($errors).Count 0 "AST parses: $path"}
    [ordered]@{schema='math-research-legacy-successor-tests/v8';status='passed';assertions=$script:assertions;real_fixture_source_tree_sha256=$sourceHash;inherited_artifact_count=[long]$build.inherited_artifact_count;builder_sha256=Get-Hash $builder;test_sha256=Get-Hash $PSCommandPath;helper_sha256=Get-Hash $helper;startup_sha256=Get-Hash $startup}|ConvertTo-Json -Compress
}
finally{
    if(Test-Path -LiteralPath $temp){
        $tempRoot=[IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\','/')
        $resolved=[IO.Path]::GetFullPath($temp).TrimEnd('\','/')
        $leaf=Split-Path -Leaf $resolved;$parent=Split-Path -Parent $resolved;$item=Get-Item -LiteralPath $resolved -Force
        if($parent-cne$tempRoot-or$leaf-cnotmatch'^math-research-legacy-successor-v8-test-[0-9a-f]{32}$'-or($item.Attributes-band[IO.FileAttributes]::ReparsePoint)-ne0){throw "Unsafe test cleanup target refused: $resolved"}
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}
