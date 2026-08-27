[CmdletBinding()]
param()

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
$script:assertions = 0

function Assert-Equal {
    param($Actual, $Expected, [string]$Label)
    $script:assertions++
    if ($Actual -cne $Expected) { throw "$Label expected '$Expected' but got '$Actual'." }
}

function Assert-True {
    param([bool]$Condition, [string]$Label)
    $script:assertions++
    if (-not $Condition) { throw "$Label expected true." }
}

function Get-RawSha256 {
    param([string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-NormalizedSha256 {
    param([string]$Path)
    $text = [IO.File]::ReadAllText($Path, [Text.UTF8Encoding]::new($false, $true)) -replace "`r`n", "`n"
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.UTF8Encoding]::new($false).GetBytes($text))).ToLowerInvariant()
}

function Get-TextSha256 {
    param([string]$Text)
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.UTF8Encoding]::new($false).GetBytes($Text))).ToLowerInvariant()
}

function Get-TreeSnapshot {
    param([string]$Root)
    $parts = foreach ($file in Get-ChildItem -LiteralPath $Root -File -Recurse -Force | Sort-Object FullName) {
        $relative = [IO.Path]::GetRelativePath($Root, $file.FullName)
        "$relative|$(Get-RawSha256 $file.FullName)"
    }
    return Get-TextSha256 -Text ($parts -join "`n")
}

function Write-JsonObject {
    param([string]$Path, [Collections.IDictionary]$Value)
    $parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    [IO.File]::WriteAllText($Path, (($Value | ConvertTo-Json -Depth 64) + "`n"), [Text.UTF8Encoding]::new($false))
}

function New-AdvisoryEnvelope {
    param([Collections.IDictionary]$Payload)
    $canonical = $Payload | ConvertTo-Json -Depth 64 -Compress
    return [ordered]@{
        integrity_schema = 1
        payload = $Payload
        integrity = [ordered]@{
            algorithm = 'HMAC-SHA256'
            key_protection = 'Windows-DPAPI-CurrentUser'
            payload_sha256 = Get-TextSha256 -Text $canonical
            hmac_sha256 = ('0' * 64)
        }
    }
}

function Invoke-Router {
    param([string]$ProjectPath, [string]$GoalStatus = 'active')
    $output = & $script:router -ProjectDirectory $ProjectPath -GoalStatus $GoalStatus
    return ($output | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String)
}

function Set-LegacyFixture {
    param()
    $stateFile = Join-Path $script:projectPath 'state\goal-host-v8.json'
    if (Test-Path -LiteralPath $stateFile) { Remove-Item -LiteralPath $stateFile -Force }
    foreach ($backup in @('run.json.bak','run.json.backup')) {
        $path = Join-Path $script:runPath $backup
        if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force }
    }
    Write-JsonObject -Path (Join-Path $script:projectPath 'project.json') -Value ([ordered]@{
        schema=1; project_id=$script:projectId; status='contract_registered'
        active_contract=[ordered]@{version='v1';path='contracts\v1-prompt.md';sha256=$script:binding;status='confirmed'}
        active_run=[ordered]@{id=$script:runId;path="runs\$($script:runId)";status='preparing'}
    })
    Write-JsonObject -Path (Join-Path $script:projectPath 'state\checkpoint.json') -Value ([ordered]@{
        schema=1; project_id=$script:projectId; project_status='contract_registered'
        contract=[ordered]@{path='contracts\v1-prompt.md';sha256=$script:binding;status='confirmed';version='v1'}
        run=[ordered]@{id=$script:runId;path="runs\$($script:runId)";status='preparing'}
        last_sealed_attempt=$null;last_completed_audit=$null;attempt_count=0;attempts_since_last_audit=0;audit_due=$false;active_ticket=$null
        dirty=$true;recovery_required=$false;migration=[ordered]@{status='complete'}
    })
}

function New-LegacyPayload {
    param(
        [string]$Status = 'failed',
        [string]$ExitReason = 'The in-thread Goal continuity gate reported a missing or mismatched Goal.',
        [string]$LastStatus = 'goal_continuity_failed',
        [string]$ProjectId = $script:projectId
    )
    return [ordered]@{
        schema_version = 1
        run_id = $script:runId
        revision = 7
        updated_at_utc = [DateTime]::UtcNow.ToString('o')
        contract_version = 'v1'
        run_directory = $script:runPath
        project = [ordered]@{ project_id=$ProjectId }
        status = $Status
        exit_reason = $ExitReason
        inputs = [ordered]@{
            prompt = [ordered]@{ file='Prompt-v1.md'; sha256=$script:promptRaw; contract_binding_sha256=$script:binding }
            goal_objective = [ordered]@{ file='GoalObjective.txt'; file_sha256=$script:goalRaw }
        }
        segments = @(
            [ordered]@{ index=0; kind='goal'; status='turn_completed' },
            [ordered]@{ index=1; kind='resume'; status=$LastStatus }
        )
    }
}

function Write-LegacyManifest {
    param([Collections.IDictionary]$Payload, [string]$Name = 'run.json')
    Write-JsonObject -Path (Join-Path $script:runPath $Name) -Value (New-AdvisoryEnvelope -Payload $Payload)
}

function Set-V8Contract {
    param(
        [ValidateSet('fresh','legacy_successor')][string]$RunOrigin = 'fresh',
        [AllowNull()][string]$BaselineSha256 = $null
    )
    $baselineValue = if ($RunOrigin -ceq 'fresh') { 'null' } else { $BaselineSha256 }
    if ($RunOrigin -ceq 'legacy_successor' -and $baselineValue -cnotmatch '^[0-9a-f]{64}$') { throw 'Successor fixture requires a baseline SHA-256.' }
    $lines = @(
        '# Math Research Goal-Host Contract v8',
        '<!-- math-research-goal-host',
        'schema: 8',
        'goal_host_protocol: direct-current-task/v8',
        'goal_binding_policy: direct-current-task/v8',
        'goal_rebind_policy: external-host-bind-chain/v8',
        'contract_version: v8',
        'project_archive_schema: math-research-project/v8',
        "project_id: $($script:projectId)",
        "project_directory_name: $(Split-Path -Leaf $script:projectPath)",
        "project_identity_sha256: $($script:projectIdentity)",
        'model: gpt-5.6-sol',
        'reasoning_effort: xhigh',
        'approval_mode: approve_for_me',
        'web_search: allowed',
        'audit_interval_attempts: 2',
        'attempt_budget: 24',
        'total_round_budget: 36',
        'max_child_agents: 3',
        'max_total_agents: 4',
        'max_runtime_minutes: 60',
        "run_origin: $RunOrigin",
        "inherited_counter_budget_baseline_sha256: $baselineValue",
        "problem_statement_sha256: $($script:problemHash)",
        "cycle_policy_sha256: $($script:policyHash)",
        "initial_tickets_sha256: $($script:ticketsHash)",
        '-->',
        '',
        '<!-- math-research-cycle-policy',
        $script:policyBody,
        '-->',
        '',
        '<!-- math-research-initial-tickets',
        $script:ticketsBody,
        '-->',
        '',
        '## Launch intent',
        '',
        'Synthetic direct-current-task fixture.'
    )
    $script:v8Text = ($lines -join "`n") + "`n"
    [IO.File]::WriteAllText($script:v8ContractPath, $script:v8Text, [Text.UTF8Encoding]::new($false))
    $script:v8Binding = Get-NormalizedSha256 $script:v8ContractPath
}

function Set-DirectHostFixture {
    param(
        [ValidateSet('not_started','preparing','attempt_running','audit_due','auditing','completion_candidate','awaiting_input','paused','goal_continuity_terminal','superseded','closed')][string]$Status,
        [int]$AttemptCount = 0,
        [int]$AuditCount = 0,
        [int]$TotalRoundCount = 0,
        [int]$AttemptsSinceLastAudit = 0,
        [bool]$AuditDue = $false,
        [switch]$WithTicket,
        [ValidateSet('fresh','legacy_successor')][string]$ContractOrigin = 'fresh',
        [AllowNull()][string]$BaselineSha256 = $null
    )
    Set-V8Contract -RunOrigin $ContractOrigin -BaselineSha256 $BaselineSha256
    $runManifest=Join-Path $script:runPath 'run.json';foreach($name in @('run.json','run.json.bak','run.json.backup')){$path=Join-Path $script:runPath $name;if(Test-Path -LiteralPath $path){Remove-Item -LiteralPath $path -Force}}
    $hostGoal=[ordered]@{thread_id_available=$false;thread_id=$null;objective_raw_sha256=Get-TextSha256 'fixture raw Goal objective'}
    $contractPointer=[ordered]@{path='contracts/v8-prompt.md';version='v8';binding_sha256=$script:v8Binding}
    $runIdentity=[ordered]@{id=$script:runId;path="runs/$($script:runId)"}
    $runPointer=[ordered]@{id=$script:runId;path=$runIdentity.path;status=$Status}
    $counters=[ordered]@{attempt_count=$AttemptCount;audit_count=$AuditCount;total_round_count=$TotalRoundCount;attempts_since_last_audit=$AttemptsSinceLastAudit;audit_due=$AuditDue}
    $script:directCompletionCandidatePointer=$null;$completionOutcomePointer=$null
    $isActivation=($Status-cin@('not_started','preparing')-and($ContractOrigin-ceq'legacy_successor'-or($AttemptCount-eq0-and$AuditCount-eq0-and$TotalRoundCount-eq0-and$AttemptsSinceLastAudit-eq0-and-not$AuditDue)))
    $generation=if($isActivation){1}else{2}

    $hostBindRelative="runs/$($script:runId)/host-bindings/host-bind-g0001.json";$hostBindPath=Join-Path $script:projectPath $hostBindRelative
    Write-JsonObject $hostBindPath ([ordered]@{schema='math-research-host-binding/v8';project_id=$script:projectId;control_generation=1;event_type='HOST_BIND';prior_host_binding=$null;retirement=$null;contract=$contractPointer;run=$runIdentity;host_goal=$hostGoal})
    $hostBindPointer=[ordered]@{path=$hostBindRelative;sha256=Get-RawSha256 $hostBindPath}
    $genesisRunPointer=[ordered]@{id=$script:runId;path=$runIdentity.path;status=if($isActivation){$Status}else{'not_started'}}
    Write-JsonObject $runManifest ([ordered]@{schema='math-research-run-genesis/v8';project_id=$script:projectId;control_generation=1;contract=$contractPointer;run=$genesisRunPointer;host_binding=$hostBindPointer;host_goal=$hostGoal})

    $genesisCounters=[ordered]@{attempt_count=0;audit_count=0;total_round_count=0;attempts_since_last_audit=0;audit_due=$false}
    $activationEventType=if($ContractOrigin-ceq'legacy_successor'){'LEGACY_SUCCESSOR'}else{'RUN_GENESIS'}
    $genesisEventRelative='state/project-events/g0001.json';$genesisEventPath=Join-Path $script:projectPath $genesisEventRelative
    Write-JsonObject $genesisEventPath ([ordered]@{schema='math-research-project-event/v8';project_id=$script:projectId;control_generation=1;event_id=$activationEventType;event_type=$activationEventType;updated_at_utc=[DateTime]::UtcNow.ToString('o');previous_event_sha256=$null;contract=$contractPointer;run=$genesisRunPointer;counters=if($isActivation){$counters}else{$genesisCounters};referenced_artifacts=@()})
    $genesisEventHash=Get-RawSha256 $genesisEventPath

    $ticket=$null;$currentLifecycle=$null;$ticketBody=$null
    if($WithTicket){
        $initialPhase=$Status-cin@('not_started','preparing')
        $ticketBody=($script:initialTicket|ConvertTo-Json -Depth 64|ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String)
        if($Status-ceq'auditing'){$ticketBody.ticket_id='ticket-audit-quantifiers';$ticketBody.role='skeptic_quantifiers';$ticketBody.planned_lifecycle_slot='cycle_audit'}
        if($Status-ceq'completion_candidate'){
            $candidateRelative='evidence/direct-completion-candidate-g0002.json';$candidatePath=Join-Path $script:projectPath $candidateRelative
            Write-JsonObject $candidatePath ([ordered]@{schema='fixture-completion-candidate/v1';claim='verifier-bound terminal candidate'})
            $candidatePointer=[ordered]@{path=$candidateRelative;sha256=Get-RawSha256 $candidatePath};$script:directCompletionCandidatePointer=$candidatePointer
            $solverOutputRelative='evidence/direct-solver-output-g0002.json';$solverOutputPath=Join-Path $script:projectPath $solverOutputRelative;Write-JsonObject $solverOutputPath ([ordered]@{schema='fixture-solver-output/v1';status='closed'})
            $solverOutput=[ordered]@{path=$solverOutputRelative;sha256=Get-RawSha256 $solverOutputPath}
            $solverCompletionRelative='evidence/direct-solver-completion-g0002.json';$solverCompletionPath=Join-Path $script:projectPath $solverCompletionRelative
            Write-JsonObject $solverCompletionPath ([ordered]@{schema='math-research-ticket-completion/v8';project_id=$script:projectId;contract=$contractPointer;run=$runIdentity;ticket_id='direct-solver-ticket';role='solver';status='closed';output=$solverOutput;candidate_artifact=$candidatePointer;completed_at_utc=[DateTime]::UtcNow.ToString('o')})
            $ticketBody.ticket_id='direct-verifier-ticket';$ticketBody.role='verifier';$ticketBody.planned_lifecycle_slot='candidate_verification';$ticketBody.candidate_artifact=$candidatePointer
            $ticketBody.input_artifacts=@($candidatePointer)+@($ticketBody.input_artifacts);$ticketBody.dependencies=@([ordered]@{ticket_id='direct-solver-ticket';path=$solverCompletionRelative;sha256=Get-RawSha256 $solverCompletionPath})
        }
        $ticketId=[string]$ticketBody.ticket_id;$ticketRelative="runs/$($script:runId)/tickets/$ticketId-g$('{0:D4}'-f$generation).json";$ticketPath=Join-Path $script:projectPath $ticketRelative
        Write-JsonObject $ticketPath ([ordered]@{schema='math-research-frozen-ticket/v8';project_id=$script:projectId;control_generation=$generation;contract=$contractPointer;run=$runPointer;cycle_id='cycle-1';contract_initial_tickets_sha256=$script:ticketsHash;counter_snapshot=$counters;ticket=$ticketBody})
        $ticketHash=Get-RawSha256 $ticketPath;$sourceEventPointer=$null
        if(-not$initialPhase){
            $ticketEventRelative="runs/$($script:runId)/ticket-events/$ticketId-g$('{0:D4}'-f$generation)-event.json";$ticketEventPath=Join-Path $script:projectPath $ticketEventRelative
            Write-JsonObject $ticketEventPath ([ordered]@{schema='math-research-ticket-event/v8';project_id=$script:projectId;control_generation=$generation;event_id=("$ticketId-g$generation-event");ticket_id=$ticketId;ticket=[ordered]@{path=$ticketRelative;sha256=$ticketHash};role=[string]$ticketBody.role;contract=$contractPointer;run=$runIdentity;counters=$counters;input_artifacts=$ticketBody.input_artifacts;dependencies=$ticketBody.dependencies;updated_at_utc=[DateTime]::UtcNow.ToString('o')})
            $sourceEventPointer=[ordered]@{path=$ticketEventRelative;sha256=Get-RawSha256 $ticketEventPath}
        }
        if($Status-ceq'completion_candidate'){
            $verifierRelative='evidence/direct-verifier-result-g0002.json';$verifierPath=Join-Path $script:projectPath $verifierRelative
            Write-JsonObject $verifierPath ([ordered]@{schema='math-research-verifier-result/v8';project_id=$script:projectId;contract=$contractPointer;run=$runIdentity;ticket_id=$ticketId;role='verifier';candidate_artifact=$script:directCompletionCandidatePointer;verdict='PASS';checked_at_utc=[DateTime]::UtcNow.ToString('o')})
            $verifierPointer=[ordered]@{path=$verifierRelative;sha256=Get-RawSha256 $verifierPath}
            $outcomeRelative='evidence/direct-attempt-outcome-g0002.json';$outcomePath=Join-Path $script:projectPath $outcomeRelative
            Write-JsonObject $outcomePath ([ordered]@{schema='math-research-attempt-outcome/v8';project_id=$script:projectId;contract=$contractPointer;run=$runIdentity;attempt_id='direct-attempt-g0002';outcome='candidate_found';candidate=$script:directCompletionCandidatePointer;verifier_completion=$verifierPointer;completed_at_utc=[DateTime]::UtcNow.ToString('o')})
            $completionOutcomePointer=[ordered]@{path=$outcomeRelative;sha256=Get-RawSha256 $outcomePath}
        }
        $ticketStatus=switch($Status){{$_-cin@('not_started','preparing','audit_due')}{'ready';break}{$_-cin@('attempt_running','auditing','awaiting_input','paused')}{'active';break}'completion_candidate'{'awaiting_verification';break}default{'closed'}}
        $ticket=[ordered]@{id=$ticketId;path=$ticketRelative;sha256=$ticketHash;status=$ticketStatus;contract_initial_tickets_sha256=$script:ticketsHash;counter_snapshot=[ordered]@{attempt_count=$AttemptCount;audit_count=$AuditCount;total_round_count=$TotalRoundCount};source_event=$sourceEventPointer}
        $currentLifecycle=[ordered]@{kind=if($initialPhase){'initial_ticket'}else{'frozen_ticket'};id=$ticketId;path=$ticketRelative;sha256=$ticketHash}
    }

    $projectEventRelative=$genesisEventRelative;$projectEventPath=$genesisEventPath;$projectEventHash=$genesisEventHash;$eventId=$activationEventType
    if($generation-eq2){
        $eventType=switch($Status){'attempt_running'{'ATTEMPT_START';break}'completion_candidate'{'ATTEMPT_END';break}'paused'{'PAUSE';break}default{'CHECKPOINT_COMMIT'}}
        $referenced=@();if($Status-ceq'completion_candidate'){$referenced=@($completionOutcomePointer)}
        if($Status-ceq'paused'){
            $capsuleRelative="state/resume-capsules/pause-g0002.json";$capsulePath=Join-Path $script:projectPath $capsuleRelative
            Write-JsonObject $capsulePath ([ordered]@{schema='math-research-resume-capsule/v8';project_id=$script:projectId;contract=$contractPointer;run=$runIdentity;prior_status='attempt_running';ticket=$ticket;lifecycle=$currentLifecycle;counters=$counters;created_at_utc=[DateTime]::UtcNow.ToString('o')})
            $referenced=@([ordered]@{path=$capsuleRelative;sha256=Get-RawSha256 $capsulePath})
        }
        $projectEventRelative='state/project-events/g0002.json';$projectEventPath=Join-Path $script:projectPath $projectEventRelative;$eventId=$eventType
        Write-JsonObject $projectEventPath ([ordered]@{schema='math-research-project-event/v8';project_id=$script:projectId;control_generation=2;event_id=$eventId;event_type=$eventType;updated_at_utc=[DateTime]::UtcNow.ToString('o');previous_event_sha256=$genesisEventHash;contract=$contractPointer;run=$runPointer;counters=$counters;referenced_artifacts=$referenced})
        $projectEventHash=Get-RawSha256 $projectEventPath
    }

    $script:directCheckpointRelative=('state/generations/g{0:D4}/checkpoint.json'-f$generation);$script:directStateRelative=('state/generations/g{0:D4}/goal-host-v8.json'-f$generation)
    $script:directCheckpointPath=Join-Path $script:projectPath $script:directCheckpointRelative;$script:directStatePath=Join-Path $script:projectPath $script:directStateRelative
    Write-JsonObject $script:directCheckpointPath ([ordered]@{schema='math-research-checkpoint/v8';project_id=$script:projectId;control_generation=$generation;contract=$contractPointer;run=$runPointer;problem_statement_sha256=$script:problemHash;host_goal=$hostGoal;host_binding_head=$hostBindPointer;counters=$counters;current_lifecycle=$currentLifecycle;successor=$null;completion_ready=$false;pending_goal_update=$false;last_run_event=[ordered]@{id=$eventId;sha256=$projectEventHash};updated_at_utc=[DateTime]::UtcNow.ToString('o')})
    $state=[ordered]@{schema='math-research-goal-host-state/v8';project_id=$script:projectId;control_generation=$generation;contract=$contractPointer;run=$runPointer;host_goal=$hostGoal;problem_statement_sha256=$script:problemHash;successor=$null;counters=$counters;current_ticket=$ticket;updated_at_utc=[DateTime]::UtcNow.ToString('o')}
    Write-JsonObject $script:directStatePath $state
    Write-JsonObject (Join-Path $script:projectPath 'project.json') ([ordered]@{schema='math-research-project/v8';project_id=$script:projectId;control_generation=$generation;problem_statement_sha256=$script:problemHash;project_identity_sha256=$script:projectIdentity;active_contract=$contractPointer;active_run=$runPointer;active_checkpoint=[ordered]@{path=$script:directCheckpointRelative;sha256=Get-RawSha256 $script:directCheckpointPath;control_generation=$generation};goal_host_state=[ordered]@{path=$script:directStateRelative;sha256=Get-RawSha256 $script:directStatePath;control_generation=$generation};project_event_head=[ordered]@{path=$projectEventRelative;sha256=$projectEventHash;control_generation=$generation};host_binding_head=[ordered]@{path=$hostBindRelative;sha256=Get-RawSha256 $hostBindPath;control_generation=1};legacy_successor=$null})
    return $state
}

function Update-DirectHeadHashes {
    $project = Get-Content -LiteralPath (Join-Path $script:projectPath 'project.json') -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $project.active_checkpoint.sha256 = Get-RawSha256 $script:directCheckpointPath
    $project.goal_host_state.sha256 = Get-RawSha256 $script:directStatePath
    Write-JsonObject -Path (Join-Path $script:projectPath 'project.json') -Value $project
}

function Sync-ActiveContractBinding {
    $script:v8Binding = Get-NormalizedSha256 $script:v8ContractPath
    $state = Get-Content -LiteralPath $script:directStatePath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $state.contract.binding_sha256 = $script:v8Binding
    if ($null -ne $state.current_ticket) {
        $ticketPath = Join-Path $script:projectPath ([string]$state.current_ticket.path)
        $ticketRecord = Get-Content -LiteralPath $ticketPath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
        $ticketRecord.contract.binding_sha256 = $script:v8Binding
        Write-JsonObject -Path $ticketPath -Value $ticketRecord
        $state.current_ticket.sha256 = Get-RawSha256 $ticketPath
        if ($null -ne $state.current_ticket.source_event) {
            $eventPath = Join-Path $script:projectPath ([string]$state.current_ticket.source_event.path)
            $event = Get-Content -LiteralPath $eventPath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
            $event.contract.binding_sha256 = $script:v8Binding
            $event.ticket.sha256 = [string]$state.current_ticket.sha256
            Write-JsonObject -Path $eventPath -Value $event
            $state.current_ticket.source_event.sha256 = Get-RawSha256 $eventPath
        }
    }
    Write-JsonObject -Path $script:directStatePath -Value $state

    $checkpoint = Get-Content -LiteralPath $script:directCheckpointPath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $checkpoint.contract.binding_sha256 = $script:v8Binding
    if ($null -ne $checkpoint.current_lifecycle) { $checkpoint.current_lifecycle.sha256 = [string]$state.current_ticket.sha256 }
    $project = Get-Content -LiteralPath (Join-Path $script:projectPath 'project.json') -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $project.active_contract.binding_sha256 = $script:v8Binding
    $eventPath = Join-Path $script:projectPath ([string]$project.project_event_head.path)
    $event = Get-Content -LiteralPath $eventPath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $event.contract.binding_sha256 = $script:v8Binding
    Write-JsonObject -Path $eventPath -Value $event
    $project.project_event_head.sha256 = Get-RawSha256 $eventPath
    $checkpoint.last_run_event.sha256 = [string]$project.project_event_head.sha256
    Write-JsonObject -Path $script:directCheckpointPath -Value $checkpoint
    $project.active_checkpoint.sha256 = Get-RawSha256 $script:directCheckpointPath
    $project.goal_host_state.sha256 = Get-RawSha256 $script:directStatePath
    Write-JsonObject -Path (Join-Path $script:projectPath 'project.json') -Value $project
}

function Sync-CurrentTicketHash {
    $state = Get-Content -LiteralPath $script:directStatePath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $ticketPath = Join-Path $script:projectPath ([string]$state.current_ticket.path)
    $state.current_ticket.sha256 = Get-RawSha256 $ticketPath
    Write-JsonObject -Path $script:directStatePath -Value $state
    $checkpoint = Get-Content -LiteralPath $script:directCheckpointPath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $checkpoint.current_lifecycle.sha256 = [string]$state.current_ticket.sha256
    Write-JsonObject -Path $script:directCheckpointPath -Value $checkpoint
    Update-DirectHeadHashes
}

function Add-LegacySuccessorFixture {
    param([Collections.IDictionary]$BaselineCounters)
    $originalState = Get-Content -LiteralPath $script:directStatePath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    if ($null -eq $BaselineCounters) { $BaselineCounters = $originalState.counters }
    $legacyRunId = 'legacy-run-0001'
    $legacyRunRelative = "runs\$legacyRunId"
    $legacyRunPath = Join-Path $script:projectPath $legacyRunRelative
    $legacyContractRelative = 'contracts\legacy-v7.md'
    $legacyManifestRelative = "$legacyRunRelative\run.json"
    $legacyBackupManifestRelative = "$legacyRunRelative\run.json.bak"
    $legacyCheckpointRelative = 'state\legacy\checkpoint.json'
    $handoffRelative = "$legacyRunRelative\handoff.md"
    $legacyIndexRelative = 'indexes\legacy-authoritative-index.json'
    $problemRelative = 'evidence\legacy-problem.md'
    $snapshotRelative = 'state\successors\g0001-predecessor-project.json'
    $baselineRelative = 'state\successor-baselines\g0001.json'
    New-Item -ItemType Directory -Path $legacyRunPath -Force | Out-Null
    [IO.File]::WriteAllText((Join-Path $script:projectPath $legacyContractRelative), "# immutable predecessor contract`n", [Text.UTF8Encoding]::new($false))
    Write-JsonObject -Path (Join-Path $script:projectPath $legacyManifestRelative) -Value ([ordered]@{schema='legacy-run/v7';run_id=$legacyRunId})
    Write-JsonObject -Path (Join-Path $script:projectPath $legacyBackupManifestRelative) -Value ([ordered]@{schema='legacy-run/v7';run_id=$legacyRunId;backup=$true})
    Write-JsonObject -Path (Join-Path $script:projectPath $legacyCheckpointRelative) -Value ([ordered]@{schema='legacy-checkpoint/v1';run_id=$legacyRunId})
    [IO.File]::WriteAllText((Join-Path $script:projectPath $handoffRelative), "legacy handoff`n", [Text.UTF8Encoding]::new($false))
    Write-JsonObject -Path (Join-Path $script:projectPath $legacyIndexRelative) -Value ([ordered]@{schema='legacy-authoritative-index/v1';entries=@()})
    New-Item -ItemType Directory -Path (Split-Path -Parent (Join-Path $script:projectPath $problemRelative)) -Force | Out-Null
    [IO.File]::WriteAllText((Join-Path $script:projectPath $problemRelative), "canonical predecessor problem`n", [Text.UTF8Encoding]::new($false))
    Write-JsonObject -Path (Join-Path $script:projectPath $snapshotRelative) -Value ([ordered]@{
        schema=1;project_id=$script:projectId;status='contract_registered'
        active_contract=[ordered]@{version='v7';path=$legacyContractRelative;sha256=Get-RawSha256 (Join-Path $script:projectPath $legacyContractRelative);status='confirmed'}
        active_run=[ordered]@{id=$legacyRunId;path=$legacyRunRelative;status='preparing'}
    })
    $budget = [ordered]@{attempt_budget_ceiling=24;attempts_spent=$BaselineCounters.attempt_count;total_round_budget_ceiling=36;total_rounds_spent=$BaselineCounters.total_round_count;runtime_or_other_cumulative=[ordered]@{runtime_minutes_spent=15}}
    Write-JsonObject -Path (Join-Path $script:projectPath $baselineRelative) -Value ([ordered]@{
        schema='math-research-counter-budget-baseline/v8';project_id=$script:projectId;predecessor_run_id=$legacyRunId
        attempt_count=$BaselineCounters.attempt_count;audit_count=$BaselineCounters.audit_count;total_round_count=$BaselineCounters.total_round_count
        attempts_since_last_audit=$BaselineCounters.attempts_since_last_audit;audit_due=$BaselineCounters.audit_due;budget_consumption=$budget
    })
    $baselineHash = Get-RawSha256 (Join-Path $script:projectPath $baselineRelative)

    $withTicket = $null -ne $originalState.current_ticket
    $fixtureParams = @{
        Status=[string]$originalState.run.status;AttemptCount=[int]$originalState.counters.attempt_count;AuditCount=[int]$originalState.counters.audit_count
        TotalRoundCount=[int]$originalState.counters.total_round_count;AttemptsSinceLastAudit=[int]$originalState.counters.attempts_since_last_audit
        AuditDue=[bool]$originalState.counters.audit_due;ContractOrigin='legacy_successor';BaselineSha256=$baselineHash
    }
    if ($withTicket) { $fixtureParams.WithTicket = $true }
    Set-DirectHostFixture @fixtureParams | Out-Null
    $state = Get-Content -LiteralPath $script:directStatePath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String

    $artifactIndexRelative = "runs\$($script:runId)\evidence\inherited-artifacts.json"
    $coverage = @('problem','verified_partial_results','attempts','failures','evidence','routes','audits','handoff','source_artifacts','computation_artifacts','intermediate_artifacts')
    $counts = [ordered]@{}; foreach ($category in $coverage) { $counts[$category] = 0 }; $counts.problem = 1
    Write-JsonObject -Path (Join-Path $script:projectPath $artifactIndexRelative) -Value ([ordered]@{
        schema='math-research-inherited-artifact-index/v8';project_id=$script:projectId;predecessor_run_id=$legacyRunId
        source_snapshot=[ordered]@{
            primary_manifest_sha256=Get-RawSha256 (Join-Path $script:projectPath $legacyManifestRelative)
            backup_manifest_sha256=Get-RawSha256 (Join-Path $script:projectPath $legacyBackupManifestRelative)
            checkpoint_sha256=Get-RawSha256 (Join-Path $script:projectPath $legacyCheckpointRelative)
            handoff_sha256=Get-RawSha256 (Join-Path $script:projectPath $handoffRelative)
            authoritative_index_heads=@([ordered]@{path=$legacyIndexRelative;sha256=Get-RawSha256 (Join-Path $script:projectPath $legacyIndexRelative)})
        }
        inventory_algorithm='union every predecessor authoritative index entry and every artifact transitively referenced; sort by category path and hash; reject duplicates'
        covers=$coverage
        entries=@([ordered]@{category='problem';path=$problemRelative;sha256=Get-RawSha256 (Join-Path $script:projectPath $problemRelative);evidence_grade='not_applicable'})
        category_counts=$counts;entry_count=1;complete_source_inventory=$true
    })
    $pointer = { param([string]$relative) [ordered]@{path=$relative;sha256=Get-RawSha256 (Join-Path $script:projectPath $relative)} }
    $lineage = [ordered]@{
        schema='math-research-legacy-successor-lineage/v8';project_id=$script:projectId;control_generation=1;legacy_goal_bindings_obsolete=$true
        predecessor=[ordered]@{
            project_head_snapshot=(& $pointer $snapshotRelative);run_id=$legacyRunId;run_path=$legacyRunRelative
            contract=(& $pointer $legacyContractRelative);primary_manifest=(& $pointer $legacyManifestRelative);backup_manifest=(& $pointer $legacyBackupManifestRelative)
            checkpoint=(& $pointer $legacyCheckpointRelative);handoff=(& $pointer $handoffRelative)
        }
        inherited_artifact_index=(& $pointer $artifactIndexRelative)
        inherited_counter_budget_baseline=(& $pointer $baselineRelative)
        successor=[ordered]@{
            contract=[ordered]@{path=[string]$state.contract.path;binding_sha256=[string]$state.contract.binding_sha256};run_id=[string]$state.run.id;run_path=[string]$state.run.path
            run_genesis=(& $pointer "runs\$($script:runId)\run.json")
            host_bind=(& $pointer "runs\$($script:runId)\host-bindings\host-bind-g0001.json")
        }
    }
    $script:lineageRelative = 'state\successors\g0001.json'
    $script:lineagePath = Join-Path $script:projectPath $script:lineageRelative
    Write-JsonObject -Path $script:lineagePath -Value $lineage
    $successorSummary = [ordered]@{
        lineage=(& $pointer $script:lineageRelative);inherited_artifact_index=(& $pointer $artifactIndexRelative);counter_budget_baseline=(& $pointer $baselineRelative)
    }
    $state = Get-Content -LiteralPath $script:directStatePath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $state.successor = $successorSummary
    Write-JsonObject -Path $script:directStatePath -Value $state
    $checkpoint = Get-Content -LiteralPath $script:directCheckpointPath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $checkpoint.successor = $successorSummary
    Write-JsonObject -Path $script:directCheckpointPath -Value $checkpoint
    $project = Get-Content -LiteralPath (Join-Path $script:projectPath 'project.json') -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $project.legacy_successor = [ordered]@{path=$script:lineageRelative;sha256=Get-RawSha256 $script:lineagePath;control_generation=1}
    $project.active_checkpoint.sha256 = Get-RawSha256 $script:directCheckpointPath
    $project.goal_host_state.sha256 = Get-RawSha256 $script:directStatePath
    Write-JsonObject -Path (Join-Path $script:projectPath 'project.json') -Value $project
    $script:legacyManifestPath = Join-Path $script:projectPath $legacyManifestRelative
    $script:legacyBackupManifestPath = Join-Path $script:projectPath $legacyBackupManifestRelative
    $script:legacyArtifactIndexPath = Join-Path $script:projectPath $artifactIndexRelative
    $script:legacySnapshotPath = Join-Path $script:projectPath $snapshotRelative
    $script:legacyBaselinePath = Join-Path $script:projectPath $baselineRelative
    return $lineage
}

function Update-LineagePointerHash {
    $project = Get-Content -LiteralPath (Join-Path $script:projectPath 'project.json') -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $project.legacy_successor.sha256 = Get-RawSha256 $script:lineagePath
    Write-JsonObject -Path (Join-Path $script:projectPath 'project.json') -Value $project
}

function Advance-SuccessorToGeneration2 {
    $projectPath = Join-Path $script:projectPath 'project.json'
    $project = Get-Content -LiteralPath $projectPath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $state = Get-Content -LiteralPath $script:directStatePath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $checkpoint = Get-Content -LiteralPath $script:directCheckpointPath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $runPointer = [ordered]@{id=$script:runId;path="runs/$($script:runId)";status='attempt_running'}
    $nextAttemptsSinceAudit = [int64]$state.counters.attempts_since_last_audit + 1
    $counters = [ordered]@{
        attempt_count=[int64]$state.counters.attempt_count + 1
        audit_count=[int64]$state.counters.audit_count
        total_round_count=[int64]$state.counters.total_round_count + 1
        attempts_since_last_audit=$nextAttemptsSinceAudit
        audit_due=($nextAttemptsSinceAudit -eq 2)
    }
    $ticketEventRelative = "runs/$($script:runId)/ticket-events/ticket-0001-g0002-event.json"
    $ticketRelative = "runs/$($script:runId)/tickets/ticket-0001-g0002.json"
    $ticketPath = Join-Path $script:projectPath $ticketRelative
    Write-JsonObject -Path $ticketPath -Value ([ordered]@{
        schema='math-research-frozen-ticket/v8';project_id=$script:projectId;control_generation=2;contract=$state.contract;run=$runPointer
        cycle_id='cycle-1';contract_initial_tickets_sha256=$script:ticketsHash;counter_snapshot=$counters;ticket=$script:initialTicket
    })
    $ticketHash = Get-RawSha256 $ticketPath
    $ticketEventPath = Join-Path $script:projectPath $ticketEventRelative
    Write-JsonObject -Path $ticketEventPath -Value ([ordered]@{
        schema='math-research-ticket-event/v8';project_id=$script:projectId;control_generation=2;event_id='TICKET-EVENT-G0002';ticket_id='ticket-0001'
        ticket=[ordered]@{path=$ticketRelative;sha256=$ticketHash};role=[string]$script:initialTicket.role;contract=$state.contract;run=[ordered]@{id=$script:runId;path="runs/$($script:runId)"}
        counters=$counters;input_artifacts=$script:initialTicket.input_artifacts;dependencies=@();updated_at_utc=[DateTime]::UtcNow.ToString('o')
    })
    $state.control_generation = 2; $state.run = $runPointer; $state.counters = $counters
    $state.current_ticket = [ordered]@{
        id='ticket-0001';path=$ticketRelative;sha256=$ticketHash;status='active';contract_initial_tickets_sha256=$script:ticketsHash
        counter_snapshot=[ordered]@{attempt_count=$counters.attempt_count;audit_count=$counters.audit_count;total_round_count=$counters.total_round_count};source_event=[ordered]@{path=$ticketEventRelative;sha256=Get-RawSha256 $ticketEventPath}
    }
    $state.updated_at_utc = [DateTime]::UtcNow.ToString('o')
    $checkpoint.control_generation = 2; $checkpoint.run = $runPointer; $checkpoint.counters = $counters
    $checkpoint.current_lifecycle = [ordered]@{kind='frozen_ticket';id='ticket-0001';path=$ticketRelative;sha256=$ticketHash}
    $checkpoint.updated_at_utc = [DateTime]::UtcNow.ToString('o')
    $eventRelative = 'state/project-events/g0002.json'
    $eventPath = Join-Path $script:projectPath $eventRelative
    Write-JsonObject -Path $eventPath -Value ([ordered]@{
        schema='math-research-project-event/v8';project_id=$script:projectId;control_generation=2;event_id='ATTEMPT_START';event_type='ATTEMPT_START';updated_at_utc=[DateTime]::UtcNow.ToString('o')
        previous_event_sha256=[string]$project.project_event_head.sha256;contract=$state.contract;run=$runPointer;counters=$counters;referenced_artifacts=@()
    })
    $eventHash = Get-RawSha256 $eventPath
    $checkpoint.last_run_event = [ordered]@{id='ATTEMPT_START';sha256=$eventHash}
    $script:directCheckpointRelative = 'state/generations/g0002/checkpoint.json'
    $script:directStateRelative = 'state/generations/g0002/goal-host-v8.json'
    $script:directCheckpointPath = Join-Path $script:projectPath $script:directCheckpointRelative
    $script:directStatePath = Join-Path $script:projectPath $script:directStateRelative
    Write-JsonObject -Path $script:directCheckpointPath -Value $checkpoint
    Write-JsonObject -Path $script:directStatePath -Value $state
    $project.control_generation = 2; $project.active_run = $runPointer
    $project.active_checkpoint = [ordered]@{path=$script:directCheckpointRelative;sha256=Get-RawSha256 $script:directCheckpointPath;control_generation=2}
    $project.goal_host_state = [ordered]@{path=$script:directStateRelative;sha256=Get-RawSha256 $script:directStatePath;control_generation=2}
    $project.project_event_head = [ordered]@{path=$eventRelative;sha256=$eventHash;control_generation=2}
    Write-JsonObject -Path $projectPath -Value $project
}

function Advance-SuccessorToNoncandidatePreparingGeneration3 {
    $projectPath = Join-Path $script:projectPath 'project.json'
    $project = Get-Content -LiteralPath $projectPath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $state = Get-Content -LiteralPath $script:directStatePath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $checkpoint = Get-Content -LiteralPath $script:directCheckpointPath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    if ([string]$state.run.status -cne 'attempt_running' -or [bool]$state.counters.audit_due) { throw 'Generation-3 fixture requires one completed non-audit-due attempt.' }

    $runIdentity = [ordered]@{id=$script:runId;path="runs/$($script:runId)"}
    $runPointer = [ordered]@{id=$script:runId;path=$runIdentity.path;status='preparing'}
    $counters = $state.counters
    $ticketBody = $script:initialTicket | ConvertTo-Json -Depth 64 | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $ticketId = [string]$ticketBody.ticket_id
    $ticketRelative = "runs/$($script:runId)/tickets/$ticketId-g0003-ready.json"
    $ticketPath = Join-Path $script:projectPath $ticketRelative
    Write-JsonObject -Path $ticketPath -Value ([ordered]@{
        schema='math-research-frozen-ticket/v8';project_id=$script:projectId;control_generation=3;contract=$state.contract;run=$runPointer
        cycle_id='cycle-1';contract_initial_tickets_sha256=$script:ticketsHash;counter_snapshot=$counters;ticket=$ticketBody
    })
    $ticketHash = Get-RawSha256 $ticketPath
    $currentTicket = [ordered]@{
        id=$ticketId;path=$ticketRelative;sha256=$ticketHash;status='ready';contract_initial_tickets_sha256=$script:ticketsHash
        counter_snapshot=[ordered]@{attempt_count=$counters.attempt_count;audit_count=$counters.audit_count;total_round_count=$counters.total_round_count};source_event=$null
    }
    $currentLifecycle = [ordered]@{kind='initial_ticket';id=$ticketId;path=$ticketRelative;sha256=$ticketHash}

    $outcomeRelative = "runs/$($script:runId)/attempts/attempt-0001/outcome-g0003.json"
    $outcomePath = Join-Path $script:projectPath $outcomeRelative
    Write-JsonObject -Path $outcomePath -Value ([ordered]@{
        schema='math-research-attempt-outcome/v8';project_id=$script:projectId;contract=$state.contract;run=$runIdentity
        attempt_id='attempt-0001';outcome='no_candidate';candidate=$null;verifier_completion=$null;completed_at_utc=[DateTime]::UtcNow.ToString('o')
    })
    $outcomePointer = [ordered]@{path=$outcomeRelative;sha256=Get-RawSha256 $outcomePath}
    $eventRelative = 'state/project-events/g0003.json'
    $eventPath = Join-Path $script:projectPath $eventRelative
    Write-JsonObject -Path $eventPath -Value ([ordered]@{
        schema='math-research-project-event/v8';project_id=$script:projectId;control_generation=3;event_id='ATTEMPT-END-G0003';event_type='ATTEMPT_END';updated_at_utc=[DateTime]::UtcNow.ToString('o')
        previous_event_sha256=[string]$project.project_event_head.sha256;contract=$state.contract;run=$runPointer;counters=$counters;referenced_artifacts=@($outcomePointer)
    })
    $eventHash = Get-RawSha256 $eventPath

    $state.control_generation = 3; $state.run = $runPointer; $state.counters = $counters; $state.current_ticket = $currentTicket
    $state.updated_at_utc = [DateTime]::UtcNow.ToString('o')
    $checkpoint.control_generation = 3; $checkpoint.run = $runPointer; $checkpoint.counters = $counters
    $checkpoint.current_lifecycle = $currentLifecycle; $checkpoint.last_run_event = [ordered]@{id='ATTEMPT-END-G0003';sha256=$eventHash}
    $checkpoint.updated_at_utc = [DateTime]::UtcNow.ToString('o')
    $script:directCheckpointRelative = 'state/generations/g0003/checkpoint.json'
    $script:directStateRelative = 'state/generations/g0003/goal-host-v8.json'
    $script:directCheckpointPath = Join-Path $script:projectPath $script:directCheckpointRelative
    $script:directStatePath = Join-Path $script:projectPath $script:directStateRelative
    Write-JsonObject -Path $script:directCheckpointPath -Value $checkpoint
    Write-JsonObject -Path $script:directStatePath -Value $state
    $project.control_generation = 3; $project.active_run = $runPointer
    $project.active_checkpoint = [ordered]@{path=$script:directCheckpointRelative;sha256=Get-RawSha256 $script:directCheckpointPath;control_generation=3}
    $project.goal_host_state = [ordered]@{path=$script:directStateRelative;sha256=Get-RawSha256 $script:directStatePath;control_generation=3}
    $project.project_event_head = [ordered]@{path=$eventRelative;sha256=$eventHash;control_generation=3}
    Write-JsonObject -Path $projectPath -Value $project
}

$sourceRouter = Join-Path $PSScriptRoot 'invoke_math_research_startup_v3.ps1'
$temp = Join-Path ([IO.Path]::GetTempPath()) ('math-research-startup-v3-' + [guid]::NewGuid().ToString('N'))
$scriptRoot = Join-Path $temp 'skill\scripts'
$script:projectPath = Join-Path $temp 'project'
$script:runId = 'fixture-run-0001'
$script:runPath = Join-Path $script:projectPath "runs\$($script:runId)"
$contractPath = Join-Path $script:projectPath 'contracts\v1-prompt.md'
$script:v8ContractPath = Join-Path $script:projectPath 'contracts\v8-prompt.md'
$promptPath = Join-Path $script:runPath 'Prompt-v1.md'
$goalPath = Join-Path $script:runPath 'GoalObjective.txt'
$manifestPath = Join-Path $script:runPath 'run.json'

New-Item -ItemType Directory -Path $scriptRoot,$script:runPath,(Split-Path -Parent $contractPath),(Join-Path $script:projectPath 'state') -Force | Out-Null

try {
    Copy-Item -LiteralPath $sourceRouter -Destination $scriptRoot
    $script:router = Join-Path $scriptRoot 'invoke_math_research_startup_v3.ps1'

    $controllerCanary = @'
param([string]$Action,[string]$ProjectDirectory)
[IO.File]::WriteAllText((Join-Path $ProjectDirectory 'legacy-controller-was-called.txt'), 'unsafe legacy controller invocation')
throw 'Retired legacy controller canary was invoked.'
'@
    [IO.File]::WriteAllText((Join-Path $scriptRoot 'invoke_math_research_project_v2.ps1'), $controllerCanary, [Text.UTF8Encoding]::new($false))

    $script:projectId = 'fixture-project-0001'
    $script:projectIdentity = Get-TextSha256 ("project|" + [IO.Path]::GetFullPath($script:projectPath))
    $promptText = "# generic synthetic legacy contract`n"
    $goalText = "generic synthetic objective`n"
    $script:problemHash = Get-TextSha256 'fixture canonical problem'
    $policyObject = [ordered]@{
        schema_version=3;protocol='math-research-cycle-policy/v3';total_round_budget=36;attempt_budget=24;audit_interval_attempts=2
        max_route_family_attempts_per_cycle=2;max_repair_batches_per_attempt=1;allowed_worker_tools=@('apply_patch','collaboration.spawn_agent','web__run','shell_command');max_ticket_tool_calls=32;max_ticket_output_bytes=8388608
        audit_roles=@('skeptic_quantifiers','skeptic_strategy','theory_tool_scout')
    }
    $script:policyBody = $policyObject | ConvertTo-Json -Depth 16 -Compress
    $script:initialTicket = [ordered]@{
        ticket_id='ticket-0001';role='solver';planned_lifecycle_slot='first_attempt';route_id='route-modular-001'
        route_fingerprint_sha256=Get-TextSha256 'route-modular-001';attempt_kind='route_execution';route_family_id='modular-obstruction'
        mechanism_id='residue-cover';bottleneck_id='global-lift';decision_question='Does the bounded residue route produce a proved global obstruction?'
        input_artifacts=@([ordered]@{path='contracts/v1-prompt.md';sha256=Get-TextSha256 $promptText})
        search_domain='Residue moduli 2 through 64 with an explicit lift proof';success_signal='A checked lemma and independent verifier-ready candidate'
        stop_signal='The bounded modulus family is exhausted without a lift';allowed_tools=@('apply_patch','collaboration.spawn_agent','web__run')
        source_network_policy=[ordered]@{web='allowed';allowed_source_classes=@('primary_source');network_destinations=@()}
        filesystem_scope=[ordered]@{read_paths=@('contracts/v1-prompt.md');writable_staging_path="runs/$($script:runId)/staging/ticket-0001/solver-1"}
        resource_caps=[ordered]@{child_agents=1;tool_calls=20;runtime_minutes=10;max_output_bytes=100000}
        dependencies=@();evidence_grade_required='proved_or_exact_computation'
        required_outputs=@([ordered]@{path='solver-report.md';schema='math-research-solver-report/v1';sha256_on_return='required'})
        failure_return=[ordered]@{schema='math-research-ticket-failure/v1';required_fields=@('status','failed_step','reason','partial_artifact_hashes','reopen_condition')}
        reopen_condition='A new modulus family or a proved global lift lemma is registered'
    }
    $ticketsObject = [ordered]@{schema_version=3;cycle_id='cycle-1';tickets=@($script:initialTicket)}
    $script:ticketsBody = $ticketsObject | ConvertTo-Json -Depth 32 -Compress
    $script:policyHash = Get-TextSha256 $script:policyBody
    $script:ticketsHash = Get-TextSha256 $script:ticketsBody
    [IO.File]::WriteAllText($contractPath, $promptText, [Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText($promptPath, $promptText, [Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText($goalPath, $goalText, [Text.UTF8Encoding]::new($false))
    $script:binding = Get-NormalizedSha256 $contractPath
    Set-V8Contract
    $script:promptRaw = Get-RawSha256 $promptPath
    $script:goalRaw = Get-RawSha256 $goalPath

    # Exact legacy terminal segment: caller Goal status must not mask the fuse.
    Set-LegacyFixture
    $payload = New-LegacyPayload
    Write-LegacyManifest $payload
    $before = Get-TreeSnapshot $script:projectPath
    $terminal = Invoke-Router -ProjectPath $script:projectPath -GoalStatus 'none'
    $after = Get-TreeSnapshot $script:projectPath
    Assert-Equal $terminal.schema 'math-research-startup-plan/v3' 'v3 schema'
    Assert-Equal $terminal.classifier_mode 'strict_read_only_no_launch_resume_or_goal_control' 'read-only mode'
    Assert-Equal $terminal.startup_class 'goal_continuity_terminal' 'terminal class'
    Assert-Equal $terminal.next_action 'stop_no_retry_preserve_run' 'terminal next action'
    Assert-True ([bool]$terminal.terminal_no_resume) 'terminal circuit is no-resume'
    Assert-True ([bool]$terminal.legacy_goal_bindings_obsolete) 'legacy Goal bindings are obsolete'
    Assert-True ([bool]$terminal.successor_v8_requires_explicit_new_active_goal) 'successor v8 requires explicit new Goal'
    Assert-True ([bool]$terminal.legacy_run_preservation_required) 'legacy run preservation required'
    Assert-Equal $terminal.goal_gate 'terminal_no_research_or_resume' 'terminal Goal gate'
    Assert-True (@($terminal.terminal_evidence) -ccontains 'last_segment_goal_continuity_failed') 'segment evidence recorded'
    Assert-Equal $terminal.manifest_advisory_last_segment_status 'goal_continuity_failed' 'last segment classified'
    Assert-Equal $terminal.manifest_advisory_used_backup $false 'primary selected'
    Assert-Equal $before $after 'legacy classification is project read-only'

    # Exact marker is independently sufficient only on a failed manifest.
    Set-LegacyFixture
    $payload = New-LegacyPayload -ExitReason 'failure: MATH_RESEARCH_GOAL_MISSING_OR_MISMATCHED' -LastStatus 'failed'
    Write-LegacyManifest $payload
    $markerPlan = Invoke-Router $script:projectPath
    Assert-Equal $markerPlan.startup_class 'goal_continuity_terminal' 'marker terminal class'
    Assert-True (@($markerPlan.terminal_evidence) -ccontains 'exact_goal_missing_or_mismatched_marker') 'marker evidence recorded'

    # Real legacy shape: the last segment hash-binds a file whose trimmed UTF-8
    # content is exactly the Goal-missing marker.
    Set-LegacyFixture
    $lastMessagePath = Join-Path $script:runPath 'last-message-001.md'
    [IO.File]::WriteAllText($lastMessagePath, "MATH_RESEARCH_GOAL_MISSING_OR_MISMATCHED`n", [Text.UTF8Encoding]::new($false))
    $payload = New-LegacyPayload -ExitReason 'child returned a terminal marker file' -LastStatus 'failed'
    $payload.segments[-1].last_message_file = 'last-message-001.md'
    $payload.segments[-1].last_message_sha256 = Get-RawSha256 $lastMessagePath
    Write-LegacyManifest $payload
    $boundMarkerPlan = Invoke-Router $script:projectPath
    Assert-Equal $boundMarkerPlan.startup_class 'goal_continuity_terminal' 'bound last-message marker terminal class'
    Assert-True (@($boundMarkerPlan.terminal_evidence) -ccontains 'exact_goal_missing_or_mismatched_marker') 'bound last-message marker evidence recorded'

    # Failed child Goal plus persistence=false and a mismatched status is a safe terminal combination.
    Set-LegacyFixture
    $payload = New-LegacyPayload -ExitReason 'child control state failed' -LastStatus 'failed'
    $payload.goal = [ordered]@{persistence_verified=$false;observed_status='mismatched'}
    Write-LegacyManifest $payload
    $persistencePlan = Invoke-Router $script:projectPath
    Assert-Equal $persistencePlan.startup_class 'goal_continuity_terminal' 'unverified child Goal terminal class'
    Assert-True (@($persistencePlan.terminal_evidence) -ccontains 'failed_child_goal_persistence_false_with_continuity_evidence') 'persistence evidence recorded'

    # Nonmatching legacy failure always fails closed; none/paused/cancelled do not mask its diagnosis.
    Set-LegacyFixture
    $payload = New-LegacyPayload -ExitReason 'different failure' -LastStatus 'failed'
    Write-LegacyManifest $payload
    foreach ($goalStatus in @('none','paused','cancelled')) {
        $diagnosis = Invoke-Router -ProjectPath $script:projectPath -GoalStatus $goalStatus
        Assert-Equal $diagnosis.startup_class 'legacy_execution_unsupported' "nonterminal class ($goalStatus)"
        Assert-Equal $diagnosis.next_action 'fail_closed_read_only_diagnosis' "diagnosis preserved ($goalStatus)"
        Assert-Equal $diagnosis.recovery_reason 'no_production_legacy_execution_route_for_nonterminal_manifest' "reason preserved ($goalStatus)"
    }
    $cancelled = Invoke-Router -ProjectPath $script:projectPath -GoalStatus 'cancelled'
    Assert-Equal $cancelled.goal_status_normalized 'none' 'cancelled normalizes to none'

    # Invalid primary may fall back to a self-consistent backup, but only for read-only classification.
    Set-LegacyFixture
    $payload = New-LegacyPayload
    Write-LegacyManifest -Payload $payload -Name 'run.json.bak'
    $tampered = New-AdvisoryEnvelope -Payload $payload
    $tampered.payload.revision = 8
    Write-JsonObject -Path $manifestPath -Value $tampered
    $backupPlan = Invoke-Router $script:projectPath
    Assert-Equal $backupPlan.startup_class 'goal_continuity_terminal' 'valid backup terminal class'
    Assert-Equal $backupPlan.manifest_advisory_used_backup $true 'backup use disclosed'
    Assert-True (@($backupPlan.minimal_model_read) -ccontains "runs\$($script:runId)\run.json.bak") 'backup path disclosed'
    Assert-True ([string]$backupPlan.manifest_advisory_trust -like '*hmac_metadata_advisory_not_verified') 'HMAC is not claimed verified'

    # Wrong project identity and a future timestamp grant no terminal or execution route.
    Set-LegacyFixture
    Write-LegacyManifest (New-LegacyPayload -ProjectId 'different-project-0001')
    $wrongManifestIdentity = Invoke-Router $script:projectPath
    Assert-Equal $wrongManifestIdentity.startup_class 'legacy_execution_unsupported' 'wrong manifest identity class'
    Assert-True ([string]$wrongManifestIdentity.recovery_reason -like 'no_production_legacy_execution_route__manifest_advisory_identity_mismatch') 'wrong manifest identity reason'
    Assert-True (-not [bool]$wrongManifestIdentity.terminal_no_resume) 'wrong identity is not reclassified terminal'

    Set-LegacyFixture
    $futurePayload = New-LegacyPayload
    $futurePayload.updated_at_utc = [DateTimeOffset]::UtcNow.AddDays(1).ToString('o')
    Write-LegacyManifest $futurePayload
    $futureManifest = Invoke-Router $script:projectPath
    Assert-True ([string]$futureManifest.recovery_reason -like '*manifest_advisory_timestamp_invalid_or_future') 'future legacy timestamp rejected'

    # All pointer-less legacy state is unsupported and the retired controller
    # canary is never invoked, even though it is present beside the router.
    Set-LegacyFixture
    Write-LegacyManifest (New-LegacyPayload -Status 'running' -ExitReason 'legacy nonterminal state' -LastStatus 'turn_completed')
    $legacyUnsupported = Invoke-Router -ProjectPath $script:projectPath -GoalStatus 'active'
    Assert-Equal $legacyUnsupported.startup_class 'legacy_execution_unsupported' 'pointer-less legacy state class'
    Assert-Equal $legacyUnsupported.next_action 'fail_closed_read_only_diagnosis' 'pointer-less legacy state action'
    Assert-Equal $legacyUnsupported.controller_call_count 0 'legacy controller call count remains zero'
    Assert-True (-not (Test-Path -LiteralPath (Join-Path $script:projectPath 'legacy-controller-was-called.txt'))) 'legacy controller canary has no side effect'

    # Direct current-task host advisory states: ready, exact resume, due audit, and closed review.
    Set-DirectHostFixture -Status not_started -WithTicket | Out-Null
    $before = Get-TreeSnapshot $script:projectPath
    $ready = Invoke-Router $script:projectPath
    $after = Get-TreeSnapshot $script:projectPath
    Assert-Equal $ready.startup_class 'goal_host_ready' "direct host ready class ($($ready|ConvertTo-Json -Depth 8 -Compress))"
    Assert-Equal $ready.controller_call_count 0 'direct host bypasses legacy controller'
    Assert-True ([bool]$ready.requires_current_goal_control_check) 'ready requires live Goal check'
    Assert-True ([string]$ready.goal_host_state_trust -like '*not_signature_or_goal_authorization') 'state trust boundary disclosed'
    Assert-Equal $before $after 'direct host classification is project read-only'

    Set-DirectHostFixture -Status not_started -WithTicket | Out-Null
    $extraHead=Get-Content -LiteralPath (Join-Path $script:projectPath 'project.json') -Raw|ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String;$extraHead.competing_authority='forbidden';Write-JsonObject (Join-Path $script:projectPath 'project.json') $extraHead
    Assert-Equal (Invoke-Router $script:projectPath).startup_class 'goal_host_state_invalid' 'startup rejects unknown project-head authority key'

    Set-DirectHostFixture -Status not_started -WithTicket | Out-Null
    $project=Get-Content -LiteralPath (Join-Path $script:projectPath 'project.json') -Raw|ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String;$realHostPath=Join-Path $script:projectPath ([string]$project.host_binding_head.path);$dummyRelative="runs\$($script:runId)\host-bindings\dummy-bind.json";$dummyPath=Join-Path $script:projectPath $dummyRelative;Copy-Item $realHostPath $dummyPath
    $runGenesisPath=Join-Path $script:runPath 'run.json';$runGenesis=Get-Content -LiteralPath $runGenesisPath -Raw|ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String;$runGenesis.host_binding=[ordered]@{path=$dummyRelative;sha256=Get-RawSha256 $dummyPath};Write-JsonObject $runGenesisPath $runGenesis
    Assert-Equal (Invoke-Router $script:projectPath).recovery_reason 'goal_host_state_run_genesis_invalid' 'startup rejects RUN_GENESIS dummy binding drift'

    $validV8Text = $script:v8Text
    $validV8Binding = $script:v8Binding
    Set-DirectHostFixture -Status not_started -WithTicket | Out-Null
    [IO.File]::WriteAllText($script:v8ContractPath, "# legacy contract pretending to be v8`n", [Text.UTF8Encoding]::new($false))
    Sync-ActiveContractBinding
    $legacyContractSpoof = Invoke-Router $script:projectPath
    Assert-Equal $legacyContractSpoof.startup_class 'goal_host_state_invalid' 'legacy contract spoof class'
    Assert-Equal $legacyContractSpoof.recovery_reason 'goal_host_state_contract_envelope_invalid' 'legacy contract spoof reason'
    [IO.File]::WriteAllText($script:v8ContractPath, $validV8Text, [Text.UTF8Encoding]::new($false))
    $script:v8Binding = $validV8Binding

    # Contract v8 is a closed envelope: legacy Goal metadata, rehashed invalid
    # policy values, and rehashed incomplete/over-broad tickets all fail closed.
    Set-DirectHostFixture -Status not_started -WithTicket | Out-Null
    $legacyMetadataText = $script:v8Text.Replace('goal_binding_policy: direct-current-task/v8', "goal_binding_policy: direct-current-task/v8`nhost_goal_objective_raw_sha256: $('a' * 64)")
    [IO.File]::WriteAllText($script:v8ContractPath, $legacyMetadataText, [Text.UTF8Encoding]::new($false))
    Sync-ActiveContractBinding
    Assert-Equal (Invoke-Router $script:projectPath).recovery_reason 'goal_host_state_contract_envelope_invalid' 'legacy Goal metadata in v8 Contract rejected'

    Set-DirectHostFixture -Status not_started -WithTicket | Out-Null
    $badPolicyBody = $script:policyBody.Replace('"max_repair_batches_per_attempt":1', '"max_repair_batches_per_attempt":-1')
    $badPolicyHash = Get-TextSha256 $badPolicyBody
    $badPolicyText = $script:v8Text.Replace($script:policyBody, $badPolicyBody).Replace("cycle_policy_sha256: $($script:policyHash)", "cycle_policy_sha256: $badPolicyHash")
    [IO.File]::WriteAllText($script:v8ContractPath, $badPolicyText, [Text.UTF8Encoding]::new($false))
    Sync-ActiveContractBinding
    Assert-Equal (Invoke-Router $script:projectPath).recovery_reason 'goal_host_state_contract_envelope_invalid' 'rehash-bound negative policy value rejected'

    Set-DirectHostFixture -Status not_started -WithTicket | Out-Null
    $badTicketsBody = $script:ticketsBody.Replace('"max_output_bytes":100000', '"max_output_bytes":-1')
    $badTicketsHash = Get-TextSha256 $badTicketsBody
    $badTicketsText = $script:v8Text.Replace($script:ticketsBody, $badTicketsBody).Replace("initial_tickets_sha256: $($script:ticketsHash)", "initial_tickets_sha256: $badTicketsHash")
    [IO.File]::WriteAllText($script:v8ContractPath, $badTicketsText, [Text.UTF8Encoding]::new($false))
    Sync-ActiveContractBinding
    Assert-Equal (Invoke-Router $script:projectPath).recovery_reason 'goal_host_state_contract_envelope_invalid' 'rehash-bound invalid ticket cap rejected'

    # A current-ticket hash alone is insufficient: the frozen bytes must parse,
    # bind this Contract/run/counter snapshot, and exactly match its Contract member.
    Set-DirectHostFixture -Status not_started -WithTicket | Out-Null
    $ticketState = Get-Content -LiteralPath $script:directStatePath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $ticketPath = Join-Path $script:projectPath ([string]$ticketState.current_ticket.path)
    Write-JsonObject -Path $ticketPath -Value ([ordered]@{})
    Sync-CurrentTicketHash
    Assert-Equal (Invoke-Router $script:projectPath).recovery_reason 'goal_host_state_ticket_content_invalid' 'empty but rehashed current ticket rejected'

    Set-DirectHostFixture -Status not_started -WithTicket | Out-Null
    $ticketState = Get-Content -LiteralPath $script:directStatePath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $ticketPath = Join-Path $script:projectPath ([string]$ticketState.current_ticket.path)
    $ticketRecord = Get-Content -LiteralPath $ticketPath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $ticketRecord.contract.binding_sha256 = ('f' * 64)
    Write-JsonObject -Path $ticketPath -Value $ticketRecord
    Sync-CurrentTicketHash
    Assert-Equal (Invoke-Router $script:projectPath).recovery_reason 'goal_host_state_ticket_content_invalid' 'mismatched ticket Contract binding rejected'

    Set-DirectHostFixture -Status not_started -WithTicket | Out-Null
    $ticketState = Get-Content -LiteralPath $script:directStatePath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $ticketPath = Join-Path $script:projectPath ([string]$ticketState.current_ticket.path)
    $ticketRecord = Get-Content -LiteralPath $ticketPath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $ticketRecord.ticket.allowed_tools = @('unapproved-tool')
    Write-JsonObject -Path $ticketPath -Value $ticketRecord
    Sync-CurrentTicketHash
    Assert-Equal (Invoke-Router $script:projectPath).recovery_reason 'goal_host_state_ticket_content_invalid' 'ticket permission broadening rejected'

    $invalidThreadState = Set-DirectHostFixture -Status not_started -WithTicket
    $invalidThreadState.host_goal.thread_id_available = $true
    $invalidThreadState.host_goal.thread_id = $null
    Write-JsonObject -Path $script:directStatePath -Value $invalidThreadState
    Update-DirectHeadHashes
    $invalidThread = Invoke-Router $script:projectPath
    Assert-Equal $invalidThread.startup_class 'goal_host_state_invalid' 'available-but-null thread ID class'
    Assert-Equal $invalidThread.recovery_reason 'goal_host_state_resource_binding_invalid' 'available-but-null thread ID reason'

    Set-DirectHostFixture -Status not_started | Out-Null
    $missingInitialTicket = Invoke-Router $script:projectPath
    Assert-Equal $missingInitialTicket.startup_class 'goal_host_state_invalid' 'not-started without initial ticket class'
    Assert-Equal $missingInitialTicket.recovery_reason 'goal_host_state_nonterminal_ticket_missing' 'not-started without initial ticket reason'

    Set-DirectHostFixture -Status attempt_running -AttemptCount 1 -TotalRoundCount 1 -AttemptsSinceLastAudit 1 -WithTicket | Out-Null
    $resume = Invoke-Router $script:projectPath
    Assert-Equal $resume.startup_class 'goal_host_resume' 'direct host resume advisory class'
    Assert-Equal $resume.next_action 'verify_current_goal_then_resume_exact_model_managed_ticket' 'resume still requires Goal check'
    Assert-True ([bool]$resume.requires_current_goal_control_check) 'resume requires live Goal check'

    Set-DirectHostFixture -Status audit_due -AttemptCount 4 -TotalRoundCount 4 -AttemptsSinceLastAudit 2 -AuditDue $true -WithTicket | Out-Null
    $audit = Invoke-Router $script:projectPath
    Assert-Equal $audit.startup_class 'goal_host_audit_due' 'direct host audit advisory class'
    Assert-True ([bool]$audit.requires_current_goal_control_check) 'audit requires live Goal check'

    Set-DirectHostFixture -Status preparing -WithTicket | Out-Null
    Assert-Equal (Invoke-Router $script:projectPath).startup_class 'goal_host_ready' 'preparing maps to ready'
    Set-DirectHostFixture -Status preparing -AttemptCount 5 -AuditCount 2 -TotalRoundCount 7 -AttemptsSinceLastAudit 1 -WithTicket | Out-Null
    Assert-Equal (Invoke-Router $script:projectPath).startup_class 'goal_host_ready' 'preparing preserves inherited cumulative counters'
    Add-LegacySuccessorFixture | Out-Null
    $successorReady = Invoke-Router $script:projectPath
    Assert-Equal $successorReady.startup_class 'goal_host_ready' 'valid legacy successor generation is ready'
    Assert-Equal $successorReady.legacy_successor_advisory_valid $true 'valid legacy successor advisory disclosed'
    Advance-SuccessorToGeneration2
    $successorGeneration2 = Invoke-Router $script:projectPath
    Assert-Equal $successorGeneration2.startup_class 'goal_host_resume' 'successor activation pointer remains valid in later lifecycle generation'
    Assert-Equal $successorGeneration2.legacy_successor_advisory_valid $true 'later generation preserves activated lineage binding'
    $generation2Project = Get-Content -LiteralPath (Join-Path $script:projectPath 'project.json') -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    Assert-Equal $generation2Project.legacy_successor.control_generation 1 'legacy-successor pointer retains activation generation'
    Assert-Equal $generation2Project.host_binding_head.control_generation 1 'unchanged host binding may predate lifecycle generation'

    Set-DirectHostFixture -Status preparing -AttemptCount 1 -TotalRoundCount 1 -AttemptsSinceLastAudit 1 -WithTicket | Out-Null
    Add-LegacySuccessorFixture -BaselineCounters ([ordered]@{attempt_count=0;audit_count=0;total_round_count=0;attempts_since_last_audit=0;audit_due=$false}) | Out-Null
    $activationCounterMismatch = Invoke-Router $script:projectPath
    Assert-Equal $activationCounterMismatch.startup_class 'goal_host_state_invalid' 'successor activation cannot start above inherited baseline'
    Assert-Equal $activationCounterMismatch.recovery_reason 'legacy_successor_lineage_invalid' 'successor activation baseline mismatch fails closed'

    Set-DirectHostFixture -Status preparing -WithTicket | Out-Null
    Add-LegacySuccessorFixture | Out-Null
    Assert-Equal (Invoke-Router $script:projectPath).startup_class 'goal_host_ready' 'zero-baseline successor activation is ready'
    Advance-SuccessorToGeneration2
    $paidSuccessorAttempt = Invoke-Router $script:projectPath
    Assert-Equal $paidSuccessorAttempt.startup_class 'goal_host_resume' "successor paid attempt is resumable ($($paidSuccessorAttempt|ConvertTo-Json -Depth 8 -Compress))"
    Advance-SuccessorToNoncandidatePreparingGeneration3
    $postAttemptSuccessor = Invoke-Router $script:projectPath
    Assert-Equal $postAttemptSuccessor.startup_class 'goal_host_ready' 'post-attempt successor preparing state preserves spent counters'
    Assert-Equal $postAttemptSuccessor.legacy_successor_advisory_valid $true 'post-attempt successor lineage remains valid'

    Set-DirectHostFixture -Status not_started -WithTicket | Out-Null
    $freshProject = Get-Content -LiteralPath (Join-Path $script:projectPath 'project.json') -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $freshProject.legacy_successor = $null
    Write-JsonObject -Path (Join-Path $script:projectPath 'project.json') -Value $freshProject
    Assert-Equal (Invoke-Router $script:projectPath).startup_class 'goal_host_ready' 'null legacy-successor pointer is fresh v8'

    Set-DirectHostFixture -Status preparing -AttemptCount 5 -AuditCount 2 -TotalRoundCount 7 -AttemptsSinceLastAudit 1 -WithTicket | Out-Null
    Add-LegacySuccessorFixture | Out-Null
    [IO.File]::AppendAllText($script:legacyBackupManifestPath, "tamper`n", [Text.UTF8Encoding]::new($false))
    $backupTamper = Invoke-Router $script:projectPath
    Assert-Equal $backupTamper.startup_class 'goal_host_state_invalid' 'predecessor backup tamper class'
    Assert-Equal $backupTamper.recovery_reason 'legacy_successor_lineage_invalid' 'predecessor backup tamper reason'

    Set-DirectHostFixture -Status preparing -AttemptCount 5 -AuditCount 2 -TotalRoundCount 7 -AttemptsSinceLastAudit 1 -WithTicket | Out-Null
    Add-LegacySuccessorFixture | Out-Null
    [IO.File]::AppendAllText($script:legacyArtifactIndexPath, "tamper`n", [Text.UTF8Encoding]::new($false))
    Assert-Equal (Invoke-Router $script:projectPath).recovery_reason 'legacy_successor_lineage_invalid' 'inherited artifact index tamper rejected'

    Set-DirectHostFixture -Status preparing -AttemptCount 4 -AuditCount 1 -TotalRoundCount 5 -AttemptsSinceLastAudit 1 -WithTicket | Out-Null
    Add-LegacySuccessorFixture -BaselineCounters ([ordered]@{attempt_count=5;audit_count=2;total_round_count=7;attempts_since_last_audit=1;audit_due=$false}) | Out-Null
    Assert-Equal (Invoke-Router $script:projectPath).recovery_reason 'legacy_successor_lineage_invalid' 'inherited counter reset rejected'

    Set-DirectHostFixture -Status preparing -AttemptCount 5 -AuditCount 2 -TotalRoundCount 7 -AttemptsSinceLastAudit 1 -WithTicket | Out-Null
    $lineageFixture = Add-LegacySuccessorFixture
    Remove-Item -LiteralPath $script:legacySnapshotPath -Force
    Assert-Equal (Invoke-Router $script:projectPath).recovery_reason 'legacy_successor_lineage_invalid' 'missing predecessor project-head snapshot rejected'

    Set-DirectHostFixture -Status preparing -AttemptCount 5 -AuditCount 2 -TotalRoundCount 7 -AttemptsSinceLastAudit 1 -WithTicket | Out-Null
    Add-LegacySuccessorFixture | Out-Null
    [IO.File]::AppendAllText($script:legacySnapshotPath, "tamper`n", [Text.UTF8Encoding]::new($false))
    Assert-Equal (Invoke-Router $script:projectPath).recovery_reason 'legacy_successor_lineage_invalid' 'tampered predecessor project-head snapshot rejected'

    Set-DirectHostFixture -Status preparing -AttemptCount 5 -AuditCount 2 -TotalRoundCount 7 -AttemptsSinceLastAudit 1 -WithTicket | Out-Null
    $lineageFixture = Add-LegacySuccessorFixture
    $lineageFixture.control_generation = 2
    Write-JsonObject -Path $script:lineagePath -Value $lineageFixture
    Update-LineagePointerHash
    Assert-Equal (Invoke-Router $script:projectPath).recovery_reason 'legacy_successor_lineage_invalid' 'lineage generation mismatch rejected'
    Set-DirectHostFixture -Status preparing -AttemptCount 5 -AuditCount 2 -TotalRoundCount 7 -AttemptsSinceLastAudit 2 -AuditDue $true -WithTicket | Out-Null
    $preparingDue = Invoke-Router $script:projectPath
    Assert-Equal $preparingDue.startup_class 'goal_host_state_invalid' 'preparing audit-due mismatch class'
    Assert-Equal $preparingDue.recovery_reason 'goal_host_state_preparing_must_transition_to_audit_due' 'preparing audit-due mismatch reason'
    Set-DirectHostFixture -Status attempt_running -AttemptCount 4 -TotalRoundCount 4 -AttemptsSinceLastAudit 2 -AuditDue $true -WithTicket | Out-Null
    Assert-Equal (Invoke-Router $script:projectPath).startup_class 'goal_host_resume' 'running attempt may finish when audit becomes due'
    Set-DirectHostFixture -Status auditing -AttemptCount 4 -TotalRoundCount 4 -AttemptsSinceLastAudit 2 -AuditDue $true -WithTicket | Out-Null
    Assert-Equal (Invoke-Router $script:projectPath).startup_class 'goal_host_audit_due' 'auditing maps to audit continuation'
    Set-DirectHostFixture -Status completion_candidate -AttemptCount 4 -AuditCount 3 -TotalRoundCount 7 -WithTicket | Out-Null
    Assert-Equal (Invoke-Router $script:projectPath).startup_class 'goal_host_audit_due' 'completion candidate maps to completion audits'
    Set-DirectHostFixture -Status awaiting_input -AttemptCount 1 -TotalRoundCount 1 -WithTicket | Out-Null
    Assert-Equal (Invoke-Router $script:projectPath).startup_class 'goal_host_resume' 'awaiting-input maps to controlled review'
    Set-DirectHostFixture -Status paused -AttemptCount 1 -TotalRoundCount 1 -WithTicket | Out-Null
    Assert-Equal (Invoke-Router $script:projectPath).startup_class 'goal_host_resume' 'paused maps to controlled resume advisory'
    foreach ($terminalStatus in @('goal_continuity_terminal','superseded')) {
        Set-DirectHostFixture -Status $terminalStatus -AttemptCount 1 -TotalRoundCount 1 | Out-Null
        Assert-Equal (Invoke-Router $script:projectPath).startup_class 'goal_host_closed_review' "$terminalStatus maps to closed review"
    }

    Set-DirectHostFixture -Status closed -AttemptCount 4 -AuditCount 1 -TotalRoundCount 5 | Out-Null
    $closed = Invoke-Router -ProjectPath $script:projectPath -GoalStatus complete
    Assert-Equal $closed.startup_class 'goal_host_state_invalid' 'Goal complete without durable completion evidence fails closed'
    Assert-Equal $closed.recovery_reason 'goal_complete_without_durable_completion_ready' 'missing durable completion reason'

    # Full completion path: an unaudited candidate consumes one terminal audit
    # round, freezes all three role tickets in one plan, publishes three PASS
    # reports on the same snapshot, and only then publishes COMPLETION_READY.
    Set-DirectHostFixture -Status completion_candidate -AttemptCount 4 -AuditCount 3 -TotalRoundCount 7 -WithTicket | Out-Null
    $project=Get-Content -LiteralPath (Join-Path $script:projectPath 'project.json') -Raw|ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $checkpoint=Get-Content -LiteralPath $script:directCheckpointPath -Raw|ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String;$state=Get-Content -LiteralPath $script:directStatePath -Raw|ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $snapshotPath=Join-Path $script:projectPath 'state/completion-snapshot.json';Write-JsonObject $snapshotPath ([ordered]@{schema='fixture-completion-snapshot/v1';state='frozen'})
    $candidatePointer=$script:directCompletionCandidatePointer;$snapshotPointer=[ordered]@{path='state/completion-snapshot.json';sha256=Get-RawSha256 $snapshotPath};$runIdentity=[ordered]@{id=$script:runId;path="runs/$($script:runId)"}
    $auditCounters=[ordered]@{attempt_count=4;audit_count=4;total_round_count=8;attempts_since_last_audit=0;audit_due=$false};$auditRun=[ordered]@{id=$script:runId;path=$runIdentity.path;status='auditing'};$roles=@('skeptic_quantifiers','skeptic_strategy','theory_tool_scout');$auditTickets=@();$activeTicket=$null;$activeLifecycle=$null
    foreach($role in $roles){
        $body=($script:initialTicket|ConvertTo-Json -Depth 64|ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String);$body.ticket_id="terminal-$role";$body.role=$role;$body.planned_lifecycle_slot='terminal_audit'
        $ticketRelative="runs/$($script:runId)/tickets/$($body.ticket_id)-g0003.json";$ticketPath=Join-Path $script:projectPath $ticketRelative
        Write-JsonObject $ticketPath ([ordered]@{schema='math-research-frozen-ticket/v8';project_id=$script:projectId;control_generation=3;contract=$project.active_contract;run=$auditRun;cycle_id='cycle-1';contract_initial_tickets_sha256=$script:ticketsHash;counter_snapshot=$auditCounters;ticket=$body})
        $ticketPointer=[ordered]@{path=$ticketRelative;sha256=Get-RawSha256 $ticketPath};$auditTickets+=,[ordered]@{role=$role;ticket=$ticketPointer}
        if($null-eq$activeTicket){
            $ticketEventRelative="runs/$($script:runId)/ticket-events/$($body.ticket_id)-g0003.json";$ticketEventPath=Join-Path $script:projectPath $ticketEventRelative
            Write-JsonObject $ticketEventPath ([ordered]@{schema='math-research-ticket-event/v8';project_id=$script:projectId;control_generation=3;event_id='TERMINAL-AUDIT-TICKET-G0003';ticket_id=$body.ticket_id;ticket=$ticketPointer;role=$role;contract=$project.active_contract;run=$runIdentity;counters=$auditCounters;input_artifacts=$body.input_artifacts;dependencies=$body.dependencies;updated_at_utc=[DateTime]::UtcNow.ToString('o')})
            $activeTicket=[ordered]@{id=$body.ticket_id;path=$ticketRelative;sha256=$ticketPointer.sha256;status='active';contract_initial_tickets_sha256=$script:ticketsHash;counter_snapshot=[ordered]@{attempt_count=4;audit_count=4;total_round_count=8};source_event=[ordered]@{path=$ticketEventRelative;sha256=Get-RawSha256 $ticketEventPath}}
            $activeLifecycle=[ordered]@{kind='frozen_ticket';id=$body.ticket_id;path=$ticketRelative;sha256=$ticketPointer.sha256}
        }
    }
    $planRelative='state/cycle-audits/terminal-plan-g0003.json';$planPath=Join-Path $script:projectPath $planRelative
    Write-JsonObject $planPath ([ordered]@{schema='math-research-cycle-audit-plan/v8';project_id=$script:projectId;contract=$project.active_contract;run=$runIdentity;audit_kind='terminal';candidate=$candidatePointer;snapshot=$snapshotPointer;active_ticket=[ordered]@{path=$activeTicket.path;sha256=$activeTicket.sha256};tickets=$auditTickets;started_at_utc=[DateTime]::UtcNow.ToString('o')});$planPointer=[ordered]@{path=$planRelative;sha256=Get-RawSha256 $planPath}
    $auditStartRelative='state/project-events/g0003.json';$auditStartPath=Join-Path $script:projectPath $auditStartRelative;$auditStart=[ordered]@{schema='math-research-project-event/v8';project_id=$script:projectId;control_generation=3;event_id='AUDIT_START-G0003';event_type='AUDIT_START';updated_at_utc=[DateTime]::UtcNow.ToString('o');previous_event_sha256=$project.project_event_head.sha256;contract=$project.active_contract;run=$auditRun;counters=$auditCounters;referenced_artifacts=@($planPointer)};Write-JsonObject $auditStartPath $auditStart;$auditStartPointer=[ordered]@{path=$auditStartRelative;sha256=Get-RawSha256 $auditStartPath}
    $checkpoint.control_generation=3;$checkpoint.run=$auditRun;$checkpoint.counters=$auditCounters;$checkpoint.current_lifecycle=$activeLifecycle;$checkpoint.last_run_event=[ordered]@{id=$auditStart.event_id;sha256=$auditStartPointer.sha256};$checkpoint.updated_at_utc=[DateTime]::UtcNow.ToString('o');$state.control_generation=3;$state.run=$auditRun;$state.counters=$auditCounters;$state.current_ticket=$activeTicket;$state.updated_at_utc=[DateTime]::UtcNow.ToString('o')
    $script:directCheckpointRelative='state/generations/g0003/checkpoint.json';$script:directStateRelative='state/generations/g0003/goal-host-v8.json';$script:directCheckpointPath=Join-Path $script:projectPath $script:directCheckpointRelative;$script:directStatePath=Join-Path $script:projectPath $script:directStateRelative;Write-JsonObject $script:directCheckpointPath $checkpoint;Write-JsonObject $script:directStatePath $state
    $project.control_generation=3;$project.active_run=$auditRun;$project.active_checkpoint=[ordered]@{path=$script:directCheckpointRelative;sha256=Get-RawSha256 $script:directCheckpointPath;control_generation=3};$project.goal_host_state=[ordered]@{path=$script:directStateRelative;sha256=Get-RawSha256 $script:directStatePath;control_generation=3};$project.project_event_head=[ordered]@{path=$auditStartRelative;sha256=$auditStartPointer.sha256;control_generation=3};Write-JsonObject (Join-Path $script:projectPath 'project.json') $project
    Assert-Equal (Invoke-Router $script:projectPath).startup_class 'goal_host_audit_due' 'early terminal audit with audit_due false remains resumable audit'

    $reportEntries=@();foreach($role in $roles){$relative="state/cycle-audits/terminal-$role-g0004.json";$path=Join-Path $script:projectPath $relative;Write-JsonObject $path ([ordered]@{schema='math-research-cycle-audit-report/v8';project_id=$script:projectId;contract=$project.active_contract;run=$runIdentity;role=$role;candidate=$candidatePointer;snapshot=$snapshotPointer;verdict='PASS';new_math_performed=$false;checked_at_utc=[DateTime]::UtcNow.ToString('o')});$reportEntries+=,[ordered]@{role=$role;report=[ordered]@{path=$relative;sha256=Get-RawSha256 $path}}}
    $summaryRelative='state/cycle-audits/terminal-summary-g0004.json';$summaryPath=Join-Path $script:projectPath $summaryRelative;Write-JsonObject $summaryPath ([ordered]@{schema='math-research-cycle-audit-summary/v8';project_id=$script:projectId;contract=$project.active_contract;run=$runIdentity;audit_kind='terminal';audit_start_event=$auditStartPointer;plan=$planPointer;candidate=$candidatePointer;snapshot=$snapshotPointer;reports=$reportEntries;completed_at_utc=[DateTime]::UtcNow.ToString('o')});$summaryPointer=[ordered]@{path=$summaryRelative;sha256=Get-RawSha256 $summaryPath}
    $candidateRun=[ordered]@{id=$script:runId;path=$runIdentity.path;status='completion_candidate'};$auditEndRelative='state/project-events/g0004.json';$auditEndPath=Join-Path $script:projectPath $auditEndRelative;$auditEnd=[ordered]@{schema='math-research-project-event/v8';project_id=$script:projectId;control_generation=4;event_id='AUDIT_END-G0004';event_type='AUDIT_END';updated_at_utc=[DateTime]::UtcNow.ToString('o');previous_event_sha256=$auditStartPointer.sha256;contract=$project.active_contract;run=$candidateRun;counters=$auditCounters;referenced_artifacts=@($summaryPointer)};Write-JsonObject $auditEndPath $auditEnd;$auditEndHash=Get-RawSha256 $auditEndPath
    $checkpoint.control_generation=4;$checkpoint.run=$candidateRun;$checkpoint.current_lifecycle=$null;$checkpoint.last_run_event=[ordered]@{id=$auditEnd.event_id;sha256=$auditEndHash};$checkpoint.updated_at_utc=[DateTime]::UtcNow.ToString('o');$state.control_generation=4;$state.run=$candidateRun;$state.current_ticket=$null;$state.updated_at_utc=[DateTime]::UtcNow.ToString('o')
    $script:directCheckpointRelative='state/generations/g0004/checkpoint.json';$script:directStateRelative='state/generations/g0004/goal-host-v8.json';$script:directCheckpointPath=Join-Path $script:projectPath $script:directCheckpointRelative;$script:directStatePath=Join-Path $script:projectPath $script:directStateRelative;Write-JsonObject $script:directCheckpointPath $checkpoint;Write-JsonObject $script:directStatePath $state
    $project.control_generation=4;$project.active_run=$candidateRun;$project.active_checkpoint=[ordered]@{path=$script:directCheckpointRelative;sha256=Get-RawSha256 $script:directCheckpointPath;control_generation=4};$project.goal_host_state=[ordered]@{path=$script:directStateRelative;sha256=Get-RawSha256 $script:directStatePath;control_generation=4};$project.project_event_head=[ordered]@{path=$auditEndRelative;sha256=$auditEndHash;control_generation=4};Write-JsonObject (Join-Path $script:projectPath 'project.json') $project
    Assert-Equal (Invoke-Router $script:projectPath).startup_class 'goal_host_completion_ready_to_publish' 'validated terminal audit exposes only completion publication'

    $closedRun=[ordered]@{id=$script:runId;path=$runIdentity.path;status='closed'};$eventRelative='state/project-events/g0005.json';$eventPath=Join-Path $script:projectPath $eventRelative;$event=[ordered]@{schema='math-research-project-event/v8';project_id=$script:projectId;control_generation=5;event_id='COMPLETION_READY-G0005';event_type='COMPLETION_READY';updated_at_utc=[DateTime]::UtcNow.ToString('o');previous_event_sha256=$auditEndHash;contract=$project.active_contract;run=$closedRun;counters=$auditCounters;referenced_artifacts=@($summaryPointer)};Write-JsonObject $eventPath $event;$eventHash=Get-RawSha256 $eventPath
    $checkpoint.control_generation=5;$checkpoint.run=$closedRun;$checkpoint.completion_ready=$true;$checkpoint.pending_goal_update=$true;$checkpoint.last_run_event=[ordered]@{id=$event.event_id;sha256=$eventHash};$checkpoint.updated_at_utc=[DateTime]::UtcNow.ToString('o');$state.control_generation=5;$state.run=$closedRun;$state.updated_at_utc=[DateTime]::UtcNow.ToString('o')
    $script:directCheckpointRelative='state/generations/g0005/checkpoint.json';$script:directStateRelative='state/generations/g0005/goal-host-v8.json';$script:directCheckpointPath=Join-Path $script:projectPath $script:directCheckpointRelative;$script:directStatePath=Join-Path $script:projectPath $script:directStateRelative;Write-JsonObject $script:directCheckpointPath $checkpoint;Write-JsonObject $script:directStatePath $state
    $project.control_generation=5;$project.active_run=$closedRun;$project.active_checkpoint=[ordered]@{path=$script:directCheckpointRelative;sha256=Get-RawSha256 $script:directCheckpointPath;control_generation=5};$project.goal_host_state=[ordered]@{path=$script:directStateRelative;sha256=Get-RawSha256 $script:directStatePath;control_generation=5};$project.project_event_head=[ordered]@{path=$eventRelative;sha256=$eventHash;control_generation=5};Write-JsonObject (Join-Path $script:projectPath 'project.json') $project
    $completionActive=Invoke-Router -ProjectPath $script:projectPath -GoalStatus active
    Assert-Equal $completionActive.startup_class 'goal_host_completion_pending' 'durable completion with active Goal is pending control-plane close'
    Assert-Equal $completionActive.next_action 'fresh_get_goal_then_update_goal_complete_no_project_write' 'completion pending never resumes research'
    $completionClosed=Invoke-Router -ProjectPath $script:projectPath -GoalStatus complete
    Assert-Equal $completionClosed.startup_class 'goal_host_closed_review' 'durable completion with complete Goal is closed review'
    Assert-True (-not[bool]$completionClosed.requires_current_goal_control_check) 'durable closed review requires no project mutation gate'
    $completionPaused=Invoke-Router -ProjectPath $script:projectPath -GoalStatus paused
    Assert-Equal $completionPaused.startup_class 'goal_host_completion_pending' 'durable completion with paused Goal remains read-only pending'
    Set-DirectHostFixture -Status closed | Out-Null;$checkpoint=Get-Content -LiteralPath $script:directCheckpointPath -Raw|ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String;$checkpoint.completion_ready=$true;$checkpoint.pending_goal_update=$false;Write-JsonObject $script:directCheckpointPath $checkpoint;Update-DirectHeadHashes
    Assert-Equal (Invoke-Router $script:projectPath).startup_class 'goal_host_state_invalid' 'mismatched completion flags fail closed'

    # Direct-host checkpoint drift, future time, duplicate keys, and project/checkpoint identity drift fail closed.
    Set-DirectHostFixture -Status attempt_running -AttemptCount 1 -TotalRoundCount 1 -AttemptsSinceLastAudit 1 -WithTicket | Out-Null
    $checkpoint = Get-Content -LiteralPath $script:directCheckpointPath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $checkpoint.counters.attempt_count = 2
    Write-JsonObject -Path $script:directCheckpointPath -Value $checkpoint
    Update-DirectHeadHashes
    $drift = Invoke-Router $script:projectPath
    Assert-Equal $drift.startup_class 'goal_host_state_invalid' 'checkpoint drift class'
    Assert-Equal $drift.recovery_reason 'goal_host_state_checkpoint_attempt_count_drift' 'checkpoint drift reason'

    Set-DirectHostFixture -Status not_started -WithTicket | Out-Null
    $projectAuthority = Get-Content -LiteralPath (Join-Path $script:projectPath 'project.json') -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $projectAuthority.active_run = $null
    Write-JsonObject -Path (Join-Path $script:projectPath 'project.json') -Value $projectAuthority
    $staleNullPointer = Invoke-Router $script:projectPath
    Assert-Equal $staleNullPointer.startup_class 'goal_host_state_invalid' 'null project pointer class'
    Assert-Equal $staleNullPointer.recovery_reason 'goal_host_state_project_authority_missing' 'null project pointer reason'

    Set-DirectHostFixture -Status not_started -WithTicket | Out-Null
    $checkpointAuthority = Get-Content -LiteralPath $script:directCheckpointPath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    [void]$checkpointAuthority.Remove('host_goal')
    Write-JsonObject -Path $script:directCheckpointPath -Value $checkpointAuthority
    Update-DirectHeadHashes
    $missingCheckpointAuthority = Invoke-Router $script:projectPath
    Assert-Equal $missingCheckpointAuthority.startup_class 'goal_host_state_invalid' 'missing checkpoint authority class'
    Assert-Equal $missingCheckpointAuthority.recovery_reason 'goal_host_state_checkpoint_authority_missing' 'missing checkpoint authority reason'

    $roundMismatchState = Set-DirectHostFixture -Status attempt_running -AttemptCount 1 -TotalRoundCount 1 -WithTicket
    $roundMismatchState.counters.total_round_count = 2
    Write-JsonObject -Path $script:directStatePath -Value $roundMismatchState
    $checkpointAuthority = Get-Content -LiteralPath $script:directCheckpointPath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $checkpointAuthority.counters.total_round_count = 2
    Write-JsonObject -Path $script:directCheckpointPath -Value $checkpointAuthority
    Update-DirectHeadHashes
    $roundMismatch = Invoke-Router $script:projectPath
    Assert-Equal $roundMismatch.startup_class 'goal_host_state_invalid' 'round-count mismatch class'
    Assert-Equal $roundMismatch.recovery_reason 'goal_host_state_counter_inconsistent' 'round-count mismatch reason'

    $dotSegmentState = Set-DirectHostFixture -Status not_started -WithTicket
    $dotPath = "runs\$($script:runId)\..\$($script:runId)"
    $dotSegmentState.run.path = $dotPath
    Write-JsonObject -Path $script:directStatePath -Value $dotSegmentState
    $projectAuthority = Get-Content -LiteralPath (Join-Path $script:projectPath 'project.json') -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $checkpointAuthority = Get-Content -LiteralPath $script:directCheckpointPath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $projectAuthority.active_run.path = $dotPath
    $checkpointAuthority.run.path = $dotPath
    Write-JsonObject -Path (Join-Path $script:projectPath 'project.json') -Value $projectAuthority
    Write-JsonObject -Path $script:directCheckpointPath -Value $checkpointAuthority
    Update-DirectHeadHashes
    $dotSegment = Invoke-Router $script:projectPath
    Assert-Equal $dotSegment.startup_class 'goal_host_state_invalid' 'dot-segment path class'
    Assert-Equal $dotSegment.recovery_reason 'goal_host_state_resource_binding_invalid' 'dot-segment path reason'

    Set-DirectHostFixture -Status not_started -WithTicket | Out-Null
    $pointerProject = Get-Content -LiteralPath (Join-Path $script:projectPath 'project.json') -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $pointerProject.goal_host_state.sha256 = ('f' * 64)
    Write-JsonObject -Path (Join-Path $script:projectPath 'project.json') -Value $pointerProject
    $pointerHashMismatch = Invoke-Router $script:projectPath
    Assert-Equal $pointerHashMismatch.startup_class 'goal_host_state_invalid' 'head pointer hash mismatch class'
    Assert-Equal $pointerHashMismatch.recovery_reason 'goal_host_state_pointer_invalid' 'head pointer hash mismatch reason'

    Set-DirectHostFixture -Status not_started -WithTicket | Out-Null
    $pointerProject = Get-Content -LiteralPath (Join-Path $script:projectPath 'project.json') -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $pointerProject.active_checkpoint.path = 'state\generations\g0001\checkpoint-alt.json'
    Write-JsonObject -Path (Join-Path $script:projectPath 'project.json') -Value $pointerProject
    $pointerPathMismatch = Invoke-Router $script:projectPath
    Assert-Equal $pointerPathMismatch.startup_class 'goal_host_state_invalid' 'head pointer path mismatch class'
    Assert-Equal $pointerPathMismatch.recovery_reason 'goal_host_state_pointer_invalid' 'head pointer path mismatch reason'

    Set-DirectHostFixture -Status not_started -WithTicket | Out-Null
    $pointerProject = Get-Content -LiteralPath (Join-Path $script:projectPath 'project.json') -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $pointerProject.goal_host_state.control_generation = 2
    Write-JsonObject -Path (Join-Path $script:projectPath 'project.json') -Value $pointerProject
    $pointerGenerationMismatch = Invoke-Router $script:projectPath
    Assert-Equal $pointerGenerationMismatch.startup_class 'goal_host_state_invalid' 'head pointer generation mismatch class'
    Assert-Equal $pointerGenerationMismatch.recovery_reason 'goal_host_state_pointer_invalid' 'head pointer generation mismatch reason'

    Set-DirectHostFixture -Status not_started -WithTicket | Out-Null
    $pointerProject = Get-Content -LiteralPath (Join-Path $script:projectPath 'project.json') -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    [void]$pointerProject.Remove('goal_host_state')
    Write-JsonObject -Path (Join-Path $script:projectPath 'project.json') -Value $pointerProject
    $incompleteHead = Invoke-Router $script:projectPath
    Assert-Equal $incompleteHead.startup_class 'goal_host_state_invalid' 'incomplete v8 head class'
    Assert-Equal $incompleteHead.recovery_reason 'goal_host_state_pointer_pair_incomplete' 'incomplete v8 head reason'

    Set-DirectHostFixture -Status not_started -WithTicket | Out-Null
    $legacySchemaWithV8Pointers = Get-Content -LiteralPath (Join-Path $script:projectPath 'project.json') -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $legacySchemaWithV8Pointers.schema = 1
    Write-JsonObject -Path (Join-Path $script:projectPath 'project.json') -Value $legacySchemaWithV8Pointers
    $schemaDowngrade = Invoke-Router $script:projectPath
    Assert-Equal $schemaDowngrade.startup_class 'legacy_execution_unsupported' 'legacy schema cannot masquerade as v8 head'
    Assert-Equal $schemaDowngrade.recovery_reason 'legacy_schema_cannot_activate_v8_generation_pointers' 'legacy schema v8-pointer reason'

    $futureState = Set-DirectHostFixture -Status not_started -WithTicket
    $futureState.updated_at_utc = [DateTimeOffset]::UtcNow.AddDays(1).ToString('o')
    Write-JsonObject -Path $script:directStatePath -Value $futureState
    Update-DirectHeadHashes
    $futureHost = Invoke-Router $script:projectPath
    Assert-Equal $futureHost.startup_class 'goal_host_state_invalid' 'future host state class'
    Assert-Equal $futureHost.recovery_reason 'goal_host_state_timestamp_invalid_or_future' 'future host state reason'

    $duplicateState = Set-DirectHostFixture -Status not_started -WithTicket
    $duplicateJson = $duplicateState | ConvertTo-Json -Depth 64
    $duplicateJson = $duplicateJson.Replace('"schema": "math-research-goal-host-state/v8",', '"schema": "math-research-goal-host-state/v8", "schema": "duplicate",')
    [IO.File]::WriteAllText($script:directStatePath, $duplicateJson, [Text.UTF8Encoding]::new($false))
    Update-DirectHeadHashes
    $duplicate = Invoke-Router $script:projectPath
    Assert-Equal $duplicate.startup_class 'goal_host_state_invalid' 'duplicate property class'
    Assert-Equal $duplicate.recovery_reason 'goal_host_state_not_strict_json' 'duplicate property reason'

    Set-DirectHostFixture -Status not_started -WithTicket | Out-Null
    $checkpoint = Get-Content -LiteralPath $script:directCheckpointPath -Raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    $checkpoint.project_id = 'different-project-0001'
    Write-JsonObject -Path $script:directCheckpointPath -Value $checkpoint
    Update-DirectHeadHashes
    $identityDrift = Invoke-Router $script:projectPath
    Assert-Equal $identityDrift.startup_class 'project_identity_invalid' 'project/checkpoint identity class'
    Assert-Equal $identityDrift.recovery_reason 'project_checkpoint_identity_mismatch' 'project/checkpoint identity reason'

    # Static constraints: the router contains no removed Goal-host/control-pointer path or Goal/launcher command.
    $source = Get-Content -LiteralPath $sourceRouter -Raw
    Assert-True ($source.Contains('ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String')) 'DateKind-string parser explicit'
    Assert-True (-not $source.Contains('invoke_math_research_goal_host_v3.ps1')) 'removed goal-host script not referenced'
    Assert-True (-not $source.Contains('invoke_math_research_project_v2.ps1')) 'retired legacy controller not referenced'
    Assert-True (-not $source.Contains('StructuralOnly') -and -not $source.Contains('ResumePlan')) 'retired controller actions not referenced'
    Assert-True (-not $source.Contains('math-research-control-pointer-v3.json')) 'removed control pointer not referenced'
    $routerAst=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$null,[ref]$null);$commandNames=@($routerAst.FindAll({param($node)$node-is[Management.Automation.Language.CommandAst]},$true)|ForEach-Object{$_.GetCommandName()}|Where-Object{$_})
    Assert-True (@($commandNames|Where-Object{$_-cin@('create_goal','update_goal','get_goal')}).Count-eq0) 'router cannot call Goal control tools'
    Assert-True (-not $source.Contains('codex exec')) 'router cannot launch codex exec'
    Assert-True (-not $source.Contains('Invoke-Expression')) 'router excludes Invoke-Expression'
    $parameterNames = @((Get-Command -Name $sourceRouter).Parameters.Keys)
    Assert-True (@($parameterNames | Where-Object { $_ -like 'Expected*' }).Count -eq 0) 'caller Expected* authority removed'

    [ordered]@{
        ok = $true
        assertions = $script:assertions
        router = $sourceRouter
        covered = @(
            'strict_json_duplicate_keys_and_datekind_string','legacy_terminal_segment_marker_and_persistence_false',
            'primary_invalid_backup_valid','future_timestamp_rejection','project_controller_checkpoint_identity',
            'pointerless_legacy_resume_and_audit_fail_closed','goal_none_paused_cancelled_preserve_diagnosis',
            'direct_host_ready_resume_audit_closed','legacy_successor_post_attempt_preparing','direct_host_state_drift','project_read_only'
        )
    } | ConvertTo-Json -Depth 8
}
finally {
    $tempFull = [IO.Path]::GetFullPath($temp)
    $systemTemp = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\') + '\'
    if ($tempFull.StartsWith($systemTemp, [StringComparison]::OrdinalIgnoreCase) -and (Split-Path -Leaf $tempFull) -match '^math-research-startup-v3-[0-9a-f]{32}$' -and (Test-Path -LiteralPath $tempFull)) {
        Remove-Item -LiteralPath $tempFull -Recurse -Force
    }
}
