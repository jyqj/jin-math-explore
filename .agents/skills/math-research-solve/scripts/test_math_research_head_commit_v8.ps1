[CmdletBinding()]
param()

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)

$script:assertions = 0
function Assert-True([bool]$Condition,[string]$Message) { $script:assertions++; if (-not $Condition) { throw "ASSERT: $Message" } }
function Assert-Equal($Actual,$Expected,[string]$Message) { $script:assertions++; if ([string]$Actual -cne [string]$Expected) { throw "ASSERT: $Message (actual='$Actual', expected='$Expected')" } }

function Get-BytesHash([byte[]]$Bytes) { [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes)).ToLowerInvariant() }
function Get-FileHashLower([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Get-TextHash([string]$Text) { Get-BytesHash ([Text.UTF8Encoding]::new($false).GetBytes($Text)) }
function Get-NormalizedHash([string]$Path) {
    $text = [IO.File]::ReadAllText($Path,[Text.UTF8Encoding]::new($false,$true)) -replace "`r`n","`n"
    Get-TextHash $text
}
function Write-Utf8([string]$Path,[string]$Text) {
    $parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    [IO.File]::WriteAllText($Path,$Text,[Text.UTF8Encoding]::new($false))
}
function Write-Json([string]$Path,$Value) { Write-Utf8 $Path (($Value | ConvertTo-Json -Depth 64 -Compress) + "`n") }
function Read-Json([string]$Path) { Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String }
function Raw-Pointer([string]$Project,[string]$Relative) { [ordered]@{path=$Relative;sha256=Get-FileHashLower (Join-Path $Project $Relative.Replace('/','\'))} }
function Gen-Pointer([string]$Project,[string]$Relative,[long]$Generation) { [ordered]@{path=$Relative;sha256=Get-FileHashLower (Join-Path $Project $Relative.Replace('/','\'));control_generation=$Generation} }

function Set-CycleAuditStartFixture {
    param(
        [string]$Project,
        [string]$CandidatePath,
        [ValidateSet('scheduled','early','terminal')][string]$AuditKind,
        [AllowNull()][Collections.IDictionary]$CandidatePointer=$null
    )
    $head=Read-Json $CandidatePath
    $generation=[long]$head.control_generation
    $statePath=Join-Path $Project ([string]$head.goal_host_state.path).Replace('/','\')
    $checkpointPath=Join-Path $Project ([string]$head.active_checkpoint.path).Replace('/','\')
    $eventPath=Join-Path $Project ([string]$head.project_event_head.path).Replace('/','\')
    $state=Read-Json $statePath;$checkpoint=Read-Json $checkpointPath;$event=Read-Json $eventPath
    if($null-eq$state.current_ticket-or$null-eq$state.current_ticket.source_event){throw 'AUDIT_START fixture requires a derived current ticket.'}
    $sourceTicketPath=Join-Path $Project ([string]$state.current_ticket.path).Replace('/','\')
    $sourceRecord=Read-Json $sourceTicketPath
    $roles=@('skeptic_quantifiers','skeptic_strategy','theory_tool_scout')
    $ticketEntries=@();$activeTicket=$null;$activeLifecycle=$null
    foreach($role in $roles){
        $body=$sourceRecord.ticket|ConvertTo-Json -Depth 64 -Compress|ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
        $body.ticket_id=('audit-g{0:D4}-{1}'-f$generation,$role)
        $body.role=$role
        $body.planned_lifecycle_slot=($AuditKind+'_audit')
        $ticketRelative=('runs/run-0001/tickets/{0}.json'-f$body.ticket_id)
        $ticketPath=Join-Path $Project $ticketRelative.Replace('/','\')
        $record=[ordered]@{
            schema='math-research-frozen-ticket/v8';project_id=[string]$head.project_id;control_generation=$generation
            contract=$head.active_contract;run=$head.active_run;cycle_id=[string]$sourceRecord.cycle_id
            contract_initial_tickets_sha256=[string]$sourceRecord.contract_initial_tickets_sha256;counter_snapshot=$checkpoint.counters;ticket=$body
        }
        Write-Json $ticketPath $record
        $ticketPointer=Raw-Pointer $Project $ticketRelative
        $ticketEntries+=,[ordered]@{role=$role;ticket=$ticketPointer}
        if($null-eq$activeTicket){
            $ticketEventRelative=('runs/run-0001/ticket-events/{0}.json'-f$body.ticket_id)
            $ticketEventPath=Join-Path $Project $ticketEventRelative.Replace('/','\')
            Write-Json $ticketEventPath ([ordered]@{
                schema='math-research-ticket-event/v8';project_id=[string]$head.project_id;control_generation=$generation
                event_id=('AUDIT-TICKET-G{0:D4}'-f$generation);ticket_id=[string]$body.ticket_id;ticket=$ticketPointer;role=$role
                contract=$head.active_contract;run=[ordered]@{id=$head.active_run.id;path=$head.active_run.path};counters=$checkpoint.counters
                input_artifacts=$body.input_artifacts;dependencies=$body.dependencies;updated_at_utc=[DateTime]::UtcNow.ToString('o')
            })
            $activeTicket=[ordered]@{
                id=[string]$body.ticket_id;path=$ticketRelative;sha256=[string]$ticketPointer.sha256;status='active'
                contract_initial_tickets_sha256=[string]$sourceRecord.contract_initial_tickets_sha256
                counter_snapshot=[ordered]@{attempt_count=$checkpoint.counters.attempt_count;audit_count=$checkpoint.counters.audit_count;total_round_count=$checkpoint.counters.total_round_count}
                source_event=Raw-Pointer $Project $ticketEventRelative
            }
            $activeLifecycle=[ordered]@{kind='frozen_ticket';id=[string]$body.ticket_id;path=$ticketRelative;sha256=[string]$ticketPointer.sha256}
        }
    }
    $snapshotRelative=('evidence/cycle-audits/g{0:D4}-snapshot.json'-f$generation)
    Write-Json (Join-Path $Project $snapshotRelative.Replace('/','\')) ([ordered]@{schema='fixture-cycle-audit-snapshot/v1';control_generation=$generation;audit_kind=$AuditKind})
    $snapshotPointer=Raw-Pointer $Project $snapshotRelative
    if($AuditKind-ceq'terminal'-and$null-eq$CandidatePointer){throw 'Terminal audit fixture requires the locked attempt candidate.'}
    if($AuditKind-cne'terminal'){$CandidatePointer=$null}
    $planRelative=('evidence/cycle-audits/g{0:D4}-plan.json'-f$generation)
    Write-Json (Join-Path $Project $planRelative.Replace('/','\')) ([ordered]@{
        schema='math-research-cycle-audit-plan/v8';project_id=[string]$head.project_id;contract=$head.active_contract
        run=[ordered]@{id=$head.active_run.id;path=$head.active_run.path};audit_kind=$AuditKind;candidate=$CandidatePointer;snapshot=$snapshotPointer
        active_ticket=[ordered]@{path=$activeTicket.path;sha256=$activeTicket.sha256};tickets=$ticketEntries;started_at_utc=[DateTime]::UtcNow.ToString('o')
    })
    $planPointer=Raw-Pointer $Project $planRelative
    $state.current_ticket=$activeTicket;$checkpoint.current_lifecycle=$activeLifecycle
    $event.referenced_artifacts=@($planPointer)
    Write-Json $statePath $state;Write-Json $checkpointPath $checkpoint;Write-Json $eventPath $event
    Refresh-CandidateHead $Project $CandidatePath -RefreshEventBinding
    $refreshed=Read-Json $CandidatePath
    return [pscustomobject]@{
        Plan=$planPointer;Snapshot=$snapshotPointer
        StartEvent=[ordered]@{path=[string]$refreshed.project_event_head.path;sha256=[string]$refreshed.project_event_head.sha256}
    }
}

function New-CycleAuditEvidence {
    param(
        [string]$Project,
        [ValidateSet('scheduled','early','terminal')][string]$AuditKind,
        [long]$EndGeneration,
        [string[]]$Verdicts=@('PASS','PASS','PASS')
    )
    if($Verdicts.Count-ne3){throw 'Cycle-audit fixture requires three verdicts.'}
    $head=Read-Json (Join-Path $Project 'project.json')
    $startPointer=[ordered]@{path=[string]$head.project_event_head.path;sha256=[string]$head.project_event_head.sha256}
    $startEvent=Read-Json (Join-Path $Project ([string]$startPointer.path).Replace('/','\'))
    $planPointer=$startEvent.referenced_artifacts[0]
    $plan=Read-Json (Join-Path $Project ([string]$planPointer.path).Replace('/','\'))
    $candidatePointer=$plan.candidate
    if($AuditKind-ceq'terminal'-and$null-eq$candidatePointer){throw 'Terminal audit evidence fixture has no plan candidate.'}
    if($AuditKind-cne'terminal'-and$null-ne$candidatePointer){throw 'Nonterminal audit evidence fixture unexpectedly has a candidate.'}
    $runIdentity=[ordered]@{id=$head.active_run.id;path=$head.active_run.path}
    $roles=@('skeptic_quantifiers','skeptic_strategy','theory_tool_scout');$entries=@()
    for($index=0;$index-lt3;$index++){
        $role=$roles[$index]
        $reportRelative=('evidence/cycle-audits/g{0:D4}-{1}.json'-f$EndGeneration,$role)
        Write-Json (Join-Path $Project $reportRelative.Replace('/','\')) ([ordered]@{
            schema='math-research-cycle-audit-report/v8';project_id=[string]$head.project_id;contract=$head.active_contract;run=$runIdentity
            role=$role;candidate=$candidatePointer;snapshot=$plan.snapshot;verdict=$Verdicts[$index];new_math_performed=$false;checked_at_utc=[DateTime]::UtcNow.ToString('o')
        })
        $entries+=,[ordered]@{role=$role;report=Raw-Pointer $Project $reportRelative}
    }
    $summaryRelative=('evidence/cycle-audits/g{0:D4}-summary.json'-f$EndGeneration)
    Write-Json (Join-Path $Project $summaryRelative.Replace('/','\')) ([ordered]@{
        schema='math-research-cycle-audit-summary/v8';project_id=[string]$head.project_id;contract=$head.active_contract;run=$runIdentity
        audit_kind=$AuditKind;audit_start_event=$startPointer;plan=$planPointer;candidate=$candidatePointer;snapshot=$plan.snapshot
        reports=$entries;completed_at_utc=[DateTime]::UtcNow.ToString('o')
    })
    return Raw-Pointer $Project $summaryRelative
}

function New-Project {
    param([string]$Base,[string]$Name = ('project-' + [guid]::NewGuid().ToString('N')))
    $path = Join-Path $Base $Name
    New-Item -ItemType Directory -Path $path -Force | Out-Null
    return $path
}

function Set-FixtureV8Contract {
    param([string]$Project,[string]$RunId,[ValidateSet('fresh','legacy_successor')][string]$RunOrigin='fresh',[AllowNull()][string]$BaselineSha256=$null,[ValidateSet('allowed','denied')][string]$WebSearch='allowed',[string[]]$PolicyAllowedWorkerTools=@('apply_patch','collaboration.spawn_agent','shell_command'),[string[]]$TicketAllowedTools=@('apply_patch','collaboration.spawn_agent'),[long]$TicketToolCalls=20,[long]$TicketMaxOutputBytes=100000,[long]$AttemptBudget=6,[long]$TotalRoundBudget=9)
    $problemPath=Join-Path $Project 'state\problem.md'; if(-not(Test-Path -LiteralPath $problemPath)){Write-Utf8 $problemPath "fixture problem`n"}
    $problemHash=Get-FileHashLower $problemPath
    $ticket=[ordered]@{
        ticket_id='ticket-0001';role='solver';planned_lifecycle_slot='first_attempt';route_id='route-fixture-001';route_fingerprint_sha256=Get-TextHash 'route-fixture-001'
        attempt_kind='route_execution';route_family_id='fixture-family';mechanism_id='fixture-mechanism';bottleneck_id='fixture-bottleneck';decision_question='Does the exact fixture route satisfy its bounded decision question?'
        input_artifacts=@([ordered]@{path='state/problem.md';sha256=$problemHash});search_domain='A bounded exact fixture domain';success_signal='A verifier-ready exact fixture result';stop_signal='The bounded fixture domain is exhausted'
        allowed_tools=@($TicketAllowedTools);source_network_policy=[ordered]@{web=$WebSearch;allowed_source_classes=@('primary_source');network_destinations=@()}
        filesystem_scope=[ordered]@{read_paths=@('state/problem.md');writable_staging_path="runs/$RunId/staging/ticket-0001/solver-1"}
        resource_caps=[ordered]@{child_agents=1;tool_calls=$TicketToolCalls;runtime_minutes=10;max_output_bytes=$TicketMaxOutputBytes};dependencies=@();evidence_grade_required='proved_or_exact_computation'
        required_outputs=@([ordered]@{path='solver-report.md';schema='math-research-solver-report/v1';sha256_on_return='required'})
        failure_return=[ordered]@{schema='math-research-ticket-failure/v1';required_fields=@('status','failed_step','reason','partial_artifact_hashes','reopen_condition')}
        reopen_condition='A new exact fixture route is registered'
    }
    $policy=[ordered]@{schema_version=3;protocol='math-research-cycle-policy/v3';total_round_budget=$TotalRoundBudget;attempt_budget=$AttemptBudget;audit_interval_attempts=2;max_route_family_attempts_per_cycle=2;max_repair_batches_per_attempt=1;allowed_worker_tools=@($PolicyAllowedWorkerTools);max_ticket_tool_calls=32;max_ticket_output_bytes=8388608;audit_roles=@('skeptic_quantifiers','skeptic_strategy','theory_tool_scout')}
    $tickets=[ordered]@{schema_version=3;cycle_id='cycle-1';tickets=@($ticket)}
    $policyBody=$policy|ConvertTo-Json -Depth 32 -Compress; $ticketsBody=$tickets|ConvertTo-Json -Depth 64 -Compress
    $baselineValue=if($RunOrigin -eq 'fresh'){'null'}else{$BaselineSha256}
    if($RunOrigin -eq 'legacy_successor' -and [string]$BaselineSha256 -cnotmatch '^[0-9a-f]{64}$'){throw 'Successor fixture requires baseline hash.'}
    $identity=Get-TextHash ('project|'+[IO.Path]::GetFullPath($Project))
    $lines=@(
        '# Math Research Goal-Host Contract v8','<!-- math-research-goal-host','schema: 8','goal_host_protocol: direct-current-task/v8','goal_binding_policy: direct-current-task/v8','goal_rebind_policy: external-host-bind-chain/v8','contract_version: v8','project_archive_schema: math-research-project/v8','project_id: fixture-project',
        ('project_directory_name: '+(Split-Path -Leaf $Project)),('project_identity_sha256: '+$identity),'model: gpt-5.6-sol','reasoning_effort: xhigh','approval_mode: approve_for_me',('web_search: '+$WebSearch),'audit_interval_attempts: 2',('attempt_budget: '+$AttemptBudget),('total_round_budget: '+$TotalRoundBudget),'max_child_agents: 3','max_total_agents: 4','max_runtime_minutes: 60',
        ('run_origin: '+$RunOrigin),('inherited_counter_budget_baseline_sha256: '+$baselineValue),('problem_statement_sha256: '+$problemHash),('cycle_policy_sha256: '+(Get-TextHash $policyBody)),('initial_tickets_sha256: '+(Get-TextHash $ticketsBody)),'-->','',
        '<!-- math-research-cycle-policy',$policyBody,'-->','','<!-- math-research-initial-tickets',$ticketsBody,'-->','','## Launch intent','','Exact helper/startup fixture.'
    )
    $contractPath=Join-Path $Project 'contracts\contract-v8.md'; Write-Utf8 $contractPath (($lines-join "`n")+"`n")
    return [pscustomobject]@{Path=$contractPath;ProblemHash=$problemHash;Ticket=$ticket;TicketsHash=Get-TextHash $ticketsBody;CycleId='cycle-1';ProjectIdentity=$identity}
}

function New-Candidate {
    param(
        [string]$Project,
        [long]$Generation,
        [Collections.IDictionary]$PreservedHostBinding = $null,
        [Collections.IDictionary]$LegacyPointer = $null,
        [Collections.IDictionary]$SuccessorSummary = $null,
        [ValidateSet('fresh','legacy_successor')][string]$RunOrigin='fresh',
        [AllowNull()][string]$BaselineSha256=$null,
        [switch]$ForceGenesis,
        [AllowNull()][Collections.IDictionary]$CountersOverride=$null,
        [AllowNull()][string]$EventTypeOverride=$null,
        [ValidateSet('not_started','preparing','attempt_running','audit_due','auditing','completion_candidate','awaiting_input','paused','goal_continuity_terminal','superseded','closed')][string]$RunStatus='not_started',
        [switch]$DerivedTicket,
        [ValidateSet('frozen','ready','active','awaiting_verification','closed')][string]$TicketStatus='ready',
        [AllowNull()][Collections.IDictionary]$HostGoalOverride=$null,
        [AllowNull()][Collections.IDictionary]$RebindFrom=$null,
        [switch]$CompletionReady,
        [switch]$NoTicket,
        [AllowNull()][Collections.IList]$ReferencedArtifacts=$null,
        [ValidateSet('allowed','denied')][string]$WebSearch='allowed',
        [string[]]$PolicyAllowedWorkerTools=@('apply_patch','collaboration.spawn_agent','shell_command'),
        [string[]]$TicketAllowedTools=@('apply_patch','collaboration.spawn_agent'),
        [long]$TicketToolCalls=20,
        [long]$TicketMaxOutputBytes=100000,
        [long]$AttemptBudget=6,
        [long]$TotalRoundBudget=9
    )
    $projectId = 'fixture-project'
    $runId = 'run-0001'
    $runRelative = "runs/$runId"
    $runPath = Join-Path $Project 'runs\run-0001'
    $contractRelative = 'contracts/contract-v8.md'
    $material=Set-FixtureV8Contract -Project $Project -RunId $runId -RunOrigin $RunOrigin -BaselineSha256 $BaselineSha256 -WebSearch $WebSearch -PolicyAllowedWorkerTools $PolicyAllowedWorkerTools -TicketAllowedTools $TicketAllowedTools -TicketToolCalls $TicketToolCalls -TicketMaxOutputBytes $TicketMaxOutputBytes -AttemptBudget $AttemptBudget -TotalRoundBudget $TotalRoundBudget
    $contractPath = $material.Path
    $contract = [ordered]@{path=$contractRelative;version='v8';binding_sha256=Get-NormalizedHash $contractPath}
    $run = [ordered]@{id=$runId;path=$runRelative;status=$RunStatus}
    $hostGoal = if($null-ne$HostGoalOverride){$HostGoalOverride}else{[ordered]@{thread_id_available=$false;thread_id=$null;objective_raw_sha256=Get-TextHash 'fixture goal'}}
    $problemHash = $material.ProblemHash

    if ($null -ne $RebindFrom) {
        $hostRelative = ('runs/run-0001/host-bindings/host-bind-g{0:D4}.json' -f $Generation)
        $hostPath = Join-Path $Project $hostRelative.Replace('/','\')
        Write-Json $hostPath ([ordered]@{
            schema='math-research-host-binding/v8';project_id=$projectId;control_generation=$Generation;event_type='HOST_REBIND';prior_host_binding=$RebindFrom;retirement=[ordered]@{authority='user-explicit-revocation';reason='Synthetic explicit host replacement'}
            contract=$contract;run=[ordered]@{id=$run.id;path=$run.path};host_goal=$hostGoal
        })
        $hostHead = Gen-Pointer $Project $hostRelative $Generation
    }
    elseif ($null -eq $PreservedHostBinding) {
        $hostRelative = ('runs/run-0001/host-bindings/host-bind-g{0:D4}.json' -f $Generation)
        $hostPath = Join-Path $Project $hostRelative.Replace('/','\')
        Write-Json $hostPath ([ordered]@{
            schema='math-research-host-binding/v8';project_id=$projectId;control_generation=$Generation;event_type='HOST_BIND';prior_host_binding=$null;retirement=$null
            contract=$contract;run=[ordered]@{id=$run.id;path=$run.path};host_goal=$hostGoal
        })
        $hostHead = Gen-Pointer $Project $hostRelative $Generation
    }
    else { $hostHead = $PreservedHostBinding }

    $runGenesisPath = Join-Path $runPath 'run.json'
    if (-not (Test-Path -LiteralPath $runGenesisPath) -or $ForceGenesis) {
        Write-Json $runGenesisPath ([ordered]@{
            schema='math-research-run-genesis/v8';project_id=$projectId;control_generation=$Generation;contract=$contract;run=$run
            host_binding=[ordered]@{path=$hostHead.path;sha256=$hostHead.sha256};host_goal=$hostGoal
        })
    }

    $counters = if($null -ne $CountersOverride){$CountersOverride}else{[ordered]@{attempt_count=0;audit_count=0;total_round_count=0;attempts_since_last_audit=0;audit_due=$false}}
    $oldProjectPath=Join-Path $Project 'project.json'; $oldProjectForEvent=if(Test-Path -LiteralPath $oldProjectPath){Read-Json $oldProjectPath}else{$null}
    $oldIsV8=$null-ne$oldProjectForEvent -and [string]$oldProjectForEvent.schema -eq 'math-research-project/v8'
    $eventType=if(-not [string]::IsNullOrWhiteSpace($EventTypeOverride)){$EventTypeOverride}elseif($oldIsV8){'CHECKPOINT_COMMIT'}elseif($RunOrigin-eq'legacy_successor'){'LEGACY_SUCCESSOR'}else{'RUN_GENESIS'}
    $previousEventHash=if($oldIsV8){[string]$oldProjectForEvent.project_event_head.sha256}else{$null}
    $eventRelative = ('state/project-events/g{0:D4}.json' -f $Generation)
    $eventArtifacts=@();if($null-ne$ReferencedArtifacts){$eventArtifacts=@($ReferencedArtifacts)}
    Write-Json (Join-Path $Project $eventRelative.Replace('/','\')) ([ordered]@{
        schema='math-research-project-event/v8';project_id=$projectId;control_generation=$Generation;event_id=($eventType+'-G'+('{0:D4}'-f$Generation));event_type=$eventType
        updated_at_utc=[DateTime]::UtcNow.ToString('o');previous_event_sha256=$previousEventHash;contract=$contract;run=$run;counters=$counters;referenced_artifacts=$eventArtifacts
    })
    $ticketPointer=$null;$currentLifecycle=$null
    if(-not$CompletionReady-and-not$NoTicket){
        $ticketRelative = ('runs/run-0001/tickets/ticket-g{0:D4}.json' -f $Generation)
        $ticketPath=Join-Path $Project $ticketRelative.Replace('/','\')
        Write-Json $ticketPath ([ordered]@{schema='math-research-frozen-ticket/v8';project_id=$projectId;control_generation=$Generation;contract=$contract;run=$run;cycle_id=$material.CycleId;contract_initial_tickets_sha256=$material.TicketsHash;counter_snapshot=$counters;ticket=$material.Ticket})
        $ticketHash=Get-FileHashLower $ticketPath;$sourceEvent=$null
        if($DerivedTicket){
            $ticketEventRelative=('runs/run-0001/ticket-events/ticket-event-g{0:D4}.json'-f$Generation);$ticketEventPath=Join-Path $Project $ticketEventRelative.Replace('/','\')
            Write-Json $ticketEventPath ([ordered]@{schema='math-research-ticket-event/v8';project_id=$projectId;control_generation=$Generation;event_id=('ticket-event-g{0:D4}'-f$Generation);ticket_id='ticket-0001';ticket=[ordered]@{path=$ticketRelative;sha256=$ticketHash};role=$material.Ticket.role;contract=$contract;run=[ordered]@{id=$run.id;path=$run.path};counters=$counters;input_artifacts=$material.Ticket.input_artifacts;dependencies=$material.Ticket.dependencies;updated_at_utc=[DateTime]::UtcNow.ToString('o')})
            $sourceEvent=Raw-Pointer $Project $ticketEventRelative
        }
        $ticketPointer = [ordered]@{id='ticket-0001';path=$ticketRelative;sha256=$ticketHash;status=$TicketStatus;contract_initial_tickets_sha256=$material.TicketsHash;counter_snapshot=[ordered]@{attempt_count=$counters.attempt_count;audit_count=$counters.audit_count;total_round_count=$counters.total_round_count};source_event=$sourceEvent}
        $currentLifecycle=[ordered]@{kind=if($DerivedTicket){'frozen_ticket'}else{'initial_ticket'};id=$ticketPointer.id;path=$ticketPointer.path;sha256=$ticketPointer.sha256}
    }
    $checkpointRelative = ('state/generations/g{0:D4}/checkpoint.json' -f $Generation)
    $stateRelative = ('state/generations/g{0:D4}/goal-host-v8.json' -f $Generation)
    Write-Json (Join-Path $Project $checkpointRelative.Replace('/','\')) ([ordered]@{
        schema='math-research-checkpoint/v8';project_id=$projectId;control_generation=$Generation;contract=$contract;run=$run
        problem_statement_sha256=$problemHash;host_binding_head=[ordered]@{path=$hostHead.path;sha256=$hostHead.sha256};host_goal=$hostGoal;counters=$counters
        current_lifecycle=$currentLifecycle;successor=$SuccessorSummary;completion_ready=[bool]$CompletionReady;pending_goal_update=[bool]$CompletionReady
        last_run_event=[ordered]@{id=($eventType+'-G'+('{0:D4}'-f$Generation));sha256=Get-FileHashLower (Join-Path $Project $eventRelative.Replace('/','\'))};updated_at_utc=[DateTime]::UtcNow.ToString('o')
    })
    Write-Json (Join-Path $Project $stateRelative.Replace('/','\')) ([ordered]@{
        schema='math-research-goal-host-state/v8';project_id=$projectId;control_generation=$Generation;contract=$contract;run=$run;host_goal=$hostGoal
        problem_statement_sha256=$problemHash;counters=$counters;current_ticket=$ticketPointer;successor=$SuccessorSummary;updated_at_utc=[DateTime]::UtcNow.ToString('o')
    })
    $head = [ordered]@{
        schema='math-research-project/v8';project_id=$projectId;project_identity_sha256=Get-TextHash ("project|" + [IO.Path]::GetFullPath($Project))
        problem_statement_sha256=$problemHash;control_generation=$Generation
        active_checkpoint=Gen-Pointer $Project $checkpointRelative $Generation
        goal_host_state=Gen-Pointer $Project $stateRelative $Generation
        project_event_head=Gen-Pointer $Project $eventRelative $Generation
        host_binding_head=$hostHead;active_contract=$contract;active_run=$run;legacy_successor=$LegacyPointer
    }
    $candidatePath = Join-Path $Project ('state\staging\candidate-g{0:D4}.json' -f $Generation)
    Write-Json $candidatePath $head
    return [pscustomobject]@{Path=$candidatePath;Head=$head;HostBinding=$hostHead;Contract=$contract;Run=$run;Counters=$counters;ProjectId=$projectId}
}

function New-V8TransitionFixture {
    param([string]$Base)
    $project = New-Project $Base
    $g1 = New-Candidate -Project $project -Generation 1
    Copy-Item -LiteralPath $g1.Path -Destination (Join-Path $project 'project.json')
    $oldHash = Get-FileHashLower (Join-Path $project 'project.json')
    $g2 = New-Candidate -Project $project -Generation 2 -PreservedHostBinding $g1.HostBinding
    return [pscustomobject]@{Project=$project;OldHash=$oldHash;Candidate=$g2;G1=$g1}
}

function New-LegacyTransitionFixture {
    param([string]$Base,[Nullable[long]]$LegacyControlGeneration = $null)
    $project = New-Project $Base
    $oldHead = [ordered]@{
        schema=1;project_id='fixture-project';status='legacy'
        active_contract=[ordered]@{path='contracts\contract-v7.md';version='v7'}
        active_run=[ordered]@{id='legacy-run';path='runs\legacy-run';status='closed'}
    }
    if ($null -ne $LegacyControlGeneration) { $oldHead.control_generation = [long]$LegacyControlGeneration }
    $activationGeneration = if ($null -eq $LegacyControlGeneration) { 1L } else { [long]$LegacyControlGeneration + 1 }
    $generationName = 'g{0:D4}' -f $activationGeneration
    Write-Json (Join-Path $project 'project.json') $oldHead
    $oldHash = Get-FileHashLower (Join-Path $project 'project.json')
    $candidate = New-Candidate -Project $project -Generation $activationGeneration

    $snapshotRelative = "state/successors/$generationName-predecessor-project.json"
    New-Item -ItemType Directory -Path (Join-Path $project 'state\successors') -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $project 'project.json') -Destination (Join-Path $project $snapshotRelative.Replace('/','\'))
    $legacyRunId = 'legacy-run'
    $legacyRunRelative = "runs/$legacyRunId"
    Write-Utf8 (Join-Path $project 'contracts\contract-v7.md') "# Legacy`n"
    Write-Json (Join-Path $project 'runs\legacy-run\run.json') ([ordered]@{schema='legacy-run/v7';run_id=$legacyRunId})
    Write-Json (Join-Path $project 'indexes\legacy-authority.json') ([ordered]@{schema='legacy-index';run_id=$legacyRunId})
    $indexRelative = 'runs/run-0001/evidence/inherited-artifacts.json'
    $categories = @('problem','verified_partial_results','attempts','failures','evidence','routes','audits','handoff','source_artifacts','computation_artifacts','intermediate_artifacts')
    $counts = [ordered]@{}; foreach ($name in $categories) { $counts[$name] = if ($name -eq 'problem') { 1 } else { 0 } }
    Write-Json (Join-Path $project $indexRelative.Replace('/','\')) ([ordered]@{
        schema='math-research-inherited-artifact-index/v8';project_id='fixture-project';predecessor_run_id=$legacyRunId
        source_snapshot=[ordered]@{
            primary_manifest_sha256=Get-FileHashLower (Join-Path $project 'runs\legacy-run\run.json');backup_manifest_sha256=$null;checkpoint_sha256=$null;handoff_sha256=$null
            authoritative_index_heads=@(Raw-Pointer $project 'indexes/legacy-authority.json')
        }
        inventory_algorithm='fixture complete inventory';covers=$categories
        entries=@([ordered]@{category='problem';path='state/problem.md';sha256=Get-FileHashLower (Join-Path $project 'state\problem.md');evidence_grade='not_applicable'})
        category_counts=$counts;entry_count=1;complete_source_inventory=$true
    })
    $baselineRelative = "state/successor-baselines/$generationName.json"
    Write-Json (Join-Path $project $baselineRelative.Replace('/','\')) ([ordered]@{
        schema='math-research-counter-budget-baseline/v8';project_id='fixture-project';predecessor_run_id=$legacyRunId
        attempt_count=0;audit_count=0;total_round_count=0;attempts_since_last_audit=0;audit_due=$false
        budget_consumption=[ordered]@{attempt_budget_ceiling=6;attempts_spent=0;total_round_budget_ceiling=9;total_rounds_spent=0;runtime_or_other_cumulative=[ordered]@{runtime_minutes=0}}
    })
    $baselineHash=Get-FileHashLower (Join-Path $project $baselineRelative.Replace('/','\'))
    $candidate=New-Candidate -Project $project -Generation $activationGeneration -RunOrigin legacy_successor -BaselineSha256 $baselineHash -ForceGenesis
    $lineageRelative = "state/successors/$generationName.json"
    $lineage = [ordered]@{
        schema='math-research-legacy-successor-lineage/v8';project_id='fixture-project';control_generation=$activationGeneration;legacy_goal_bindings_obsolete=$true
        predecessor=[ordered]@{
            project_head_snapshot=Raw-Pointer $project $snapshotRelative;run_id=$legacyRunId;run_path=$legacyRunRelative
            contract=Raw-Pointer $project 'contracts/contract-v7.md';primary_manifest=Raw-Pointer $project 'runs/legacy-run/run.json'
            backup_manifest=$null;checkpoint=$null;handoff=$null
        }
        inherited_artifact_index=Raw-Pointer $project $indexRelative
        inherited_counter_budget_baseline=Raw-Pointer $project $baselineRelative
        successor=[ordered]@{
            contract=[ordered]@{path=$candidate.Contract.path;binding_sha256=$candidate.Contract.binding_sha256}
            run_id=$candidate.Run.id;run_path=$candidate.Run.path;run_genesis=Raw-Pointer $project 'runs/run-0001/run.json'
            host_bind=[ordered]@{path=$candidate.HostBinding.path;sha256=$candidate.HostBinding.sha256}
        }
    }
    Write-Json (Join-Path $project $lineageRelative.Replace('/','\')) $lineage
    $lineagePointer = Gen-Pointer $project $lineageRelative $activationGeneration
    $summary = [ordered]@{
        lineage=[ordered]@{path=$lineagePointer.path;sha256=$lineagePointer.sha256}
        inherited_artifact_index=Raw-Pointer $project $indexRelative
        counter_budget_baseline=Raw-Pointer $project $baselineRelative
    }
    $checkpointPath = Join-Path $project "state\generations\$generationName\checkpoint.json"
    $statePath = Join-Path $project "state\generations\$generationName\goal-host-v8.json"
    $checkpoint = Read-Json $checkpointPath; $checkpoint.successor=$summary
    Write-Json $checkpointPath $checkpoint
    $state = Read-Json $statePath; $state.successor=$summary
    Write-Json $statePath $state
    $head = Read-Json $candidate.Path; $head.legacy_successor=$lineagePointer
    $head.active_checkpoint.sha256=Get-FileHashLower $checkpointPath
    $head.goal_host_state.sha256=Get-FileHashLower $statePath
    Write-Json $candidate.Path $head
    return [pscustomobject]@{Project=$project;OldHash=$oldHash;OldGeneration=$LegacyControlGeneration;ActivationGeneration=$activationGeneration;BaselineHash=$baselineHash;Candidate=[pscustomobject]@{Path=$candidate.Path;Head=$head;HostBinding=$candidate.HostBinding;Contract=$candidate.Contract;Run=$candidate.Run};LineagePointer=$lineagePointer;Summary=$summary}
}

function Refresh-CandidateHead {
    param([string]$Project,[string]$CandidatePath,[switch]$RefreshEventBinding)
    $head=Read-Json $CandidatePath
    $checkpointPath=Join-Path $Project ([string]$head.active_checkpoint.path).Replace('/','\')
    if($RefreshEventBinding){
        $eventPath=Join-Path $Project ([string]$head.project_event_head.path).Replace('/','\');$event=Read-Json $eventPath;$checkpoint=Read-Json $checkpointPath
        $checkpoint.last_run_event=[ordered]@{id=[string]$event.event_id;sha256=Get-FileHashLower $eventPath};Write-Json $checkpointPath $checkpoint
    }
    $head.active_checkpoint.sha256=Get-FileHashLower $checkpointPath
    $head.goal_host_state.sha256=Get-FileHashLower (Join-Path $Project ([string]$head.goal_host_state.path).Replace('/','\'))
    $head.project_event_head.sha256=Get-FileHashLower (Join-Path $Project ([string]$head.project_event_head.path).Replace('/','\'))
    Write-Json $CandidatePath $head
}

function Set-PauseCandidateFixture {
    param([string]$Project,[string]$CandidatePath)
    $oldHead=Read-Json (Join-Path $Project 'project.json')
    $oldState=Read-Json (Join-Path $Project ([string]$oldHead.goal_host_state.path).Replace('/','\'))
    $oldCheckpoint=Read-Json (Join-Path $Project ([string]$oldHead.active_checkpoint.path).Replace('/','\'))
    $head=Read-Json $CandidatePath;$generation=[long]$head.control_generation
    $statePath=Join-Path $Project ([string]$head.goal_host_state.path).Replace('/','\');$state=Read-Json $statePath
    $checkpointPath=Join-Path $Project ([string]$head.active_checkpoint.path).Replace('/','\');$checkpoint=Read-Json $checkpointPath
    $eventPath=Join-Path $Project ([string]$head.project_event_head.path).Replace('/','\');$event=Read-Json $eventPath
    $state.current_ticket=$oldState.current_ticket;$checkpoint.current_lifecycle=$oldCheckpoint.current_lifecycle
    $capsuleRelative=('evidence/resume-capsules/g{0:D4}.json'-f$generation)
    Write-Json (Join-Path $Project $capsuleRelative.Replace('/','\')) ([ordered]@{
        schema='math-research-resume-capsule/v8';project_id=[string]$head.project_id;contract=$head.active_contract
        run=[ordered]@{id=$head.active_run.id;path=$head.active_run.path};prior_status=[string]$oldHead.active_run.status
        ticket=$oldState.current_ticket;lifecycle=$oldCheckpoint.current_lifecycle;counters=$checkpoint.counters;created_at_utc=[DateTime]::UtcNow.ToString('o')
    })
    $capsule=Raw-Pointer $Project $capsuleRelative;$event.referenced_artifacts=@($capsule)
    Write-Json $statePath $state;Write-Json $checkpointPath $checkpoint;Write-Json $eventPath $event
    Refresh-CandidateHead $Project $CandidatePath -RefreshEventBinding
    return $capsule
}

function Set-ResumeCandidateFixture {
    param([string]$Project,[string]$CandidatePath)
    $oldHead=Read-Json (Join-Path $Project 'project.json')
    $oldState=Read-Json (Join-Path $Project ([string]$oldHead.goal_host_state.path).Replace('/','\'))
    $oldCheckpoint=Read-Json (Join-Path $Project ([string]$oldHead.active_checkpoint.path).Replace('/','\'))
    $oldEvent=Read-Json (Join-Path $Project ([string]$oldHead.project_event_head.path).Replace('/','\'))
    $head=Read-Json $CandidatePath
    $statePath=Join-Path $Project ([string]$head.goal_host_state.path).Replace('/','\');$state=Read-Json $statePath
    $checkpointPath=Join-Path $Project ([string]$head.active_checkpoint.path).Replace('/','\');$checkpoint=Read-Json $checkpointPath
    $eventPath=Join-Path $Project ([string]$head.project_event_head.path).Replace('/','\');$event=Read-Json $eventPath
    $state.current_ticket=$oldState.current_ticket;$checkpoint.current_lifecycle=$oldCheckpoint.current_lifecycle
    $event.referenced_artifacts=@($oldEvent.referenced_artifacts[0])
    Write-Json $statePath $state;Write-Json $checkpointPath $checkpoint;Write-Json $eventPath $event
    Refresh-CandidateHead $Project $CandidatePath -RefreshEventBinding
}

function Set-DerivedVerifierTicket {
    param([string]$Project,[string]$CandidatePath,[ValidateSet('valid','missing_candidate','empty_dependencies','candidate_not_input','random_dependency_hash','missing_completion','wrong_completion_role','completion_in_verifier_staging')][string]$Mode='valid')
    $head=Read-Json $CandidatePath
    $generation=[long]$head.control_generation
    $statePath=Join-Path $Project ([string]$head.goal_host_state.path).Replace('/','\');$state=Read-Json $statePath
    if($null-eq$state.current_ticket.source_event){throw 'Verifier fixture requires one derived ticket.'}
    $checkpointPath=Join-Path $Project ([string]$head.active_checkpoint.path).Replace('/','\');$checkpoint=Read-Json $checkpointPath
    $ticketPath=Join-Path $Project ([string]$state.current_ticket.path).Replace('/','\');$ticketRecord=Read-Json $ticketPath
    $candidateRelative=('evidence/verifier-candidate-g{0:D4}.json'-f$generation);$solverOutputRelative=('evidence/solver-output-g{0:D4}.json'-f$generation);$dependencyRelative=('evidence/solver-completion-g{0:D4}.json'-f$generation)
    Write-Json (Join-Path $Project $candidateRelative.Replace('/','\')) ([ordered]@{schema='fixture-candidate/v1';claim='candidate to verify'})
    Write-Json (Join-Path $Project $solverOutputRelative.Replace('/','\')) ([ordered]@{schema='fixture-solver-report/v1';status='complete'})
    $candidatePointer=Raw-Pointer $Project $candidateRelative;$solverOutput=Raw-Pointer $Project $solverOutputRelative
    if($Mode-ceq'completion_in_verifier_staging'){$stagingRelative='runs/run-0001/staging/ticket-0001/solver-1/forged-output.json';Write-Json (Join-Path $Project $stagingRelative.Replace('/','\')) ([ordered]@{schema='fixture-output/v1'});$solverOutput=Raw-Pointer $Project $stagingRelative}
    $completion=[ordered]@{schema='math-research-ticket-completion/v8';project_id='fixture-project';contract=$head.active_contract;run=[ordered]@{id=$head.active_run.id;path=$head.active_run.path};ticket_id='solver-ticket-0001';role=if($Mode-ceq'wrong_completion_role'){'verifier'}else{'solver'};status='closed';output=$solverOutput;candidate_artifact=$candidatePointer;completed_at_utc=[DateTime]::UtcNow.ToString('o')}
    if($Mode-cne'missing_completion'){Write-Json (Join-Path $Project $dependencyRelative.Replace('/','\')) $completion}
    $dependency=[ordered]@{ticket_id='solver-ticket-0001';path=$dependencyRelative;sha256=if($Mode-ceq'missing_completion'){'0'*64}else{Get-FileHashLower (Join-Path $Project $dependencyRelative.Replace('/','\'))}}
    if($Mode-ceq'random_dependency_hash'){$dependency.sha256='f'*64}
    $ticketRecord.ticket.role='verifier'
    if($Mode-ceq'empty_dependencies'){$ticketRecord.ticket.dependencies=@()}else{$ticketRecord.ticket.dependencies=[object[]]@($dependency)}
    if($Mode-cne'missing_candidate'){$ticketRecord.ticket.candidate_artifact=$candidatePointer}else{$null=$ticketRecord.ticket.Remove('candidate_artifact')}
    if($Mode-cne'candidate_not_input'){$ticketRecord.ticket.input_artifacts=@($candidatePointer)+@($ticketRecord.ticket.input_artifacts)}
    Write-Json $ticketPath $ticketRecord;$ticketHash=Get-FileHashLower $ticketPath
    $ticketEventPath=Join-Path $Project ([string]$state.current_ticket.source_event.path).Replace('/','\');$ticketEvent=Read-Json $ticketEventPath
    $ticketEvent.ticket.sha256=$ticketHash;$ticketEvent.role='verifier';$ticketEvent.input_artifacts=$ticketRecord.ticket.input_artifacts;$ticketEvent.dependencies=$ticketRecord.ticket.dependencies;Write-Json $ticketEventPath $ticketEvent
    $state.current_ticket.sha256=$ticketHash;$state.current_ticket.source_event.sha256=Get-FileHashLower $ticketEventPath;Write-Json $statePath $state
    $checkpoint.current_lifecycle.sha256=$ticketHash;Write-Json $checkpointPath $checkpoint
    Refresh-CandidateHead $Project $CandidatePath
}

function Set-AttemptOutcomeFixture {
    param(
        [string]$Project,
        [string]$CandidatePath,
        [ValidateSet('candidate_found','no_candidate','inconclusive','failed','awaiting_input')][string]$Outcome='no_candidate',
        [ValidateSet('valid','false_candidate','verifier_fail','extra_artifact','missing')][string]$Mode='valid'
    )
    $head=Read-Json $CandidatePath;$generation=[long]$head.control_generation
    $eventPath=Join-Path $Project ([string]$head.project_event_head.path).Replace('/','\');$event=Read-Json $eventPath
    if($Mode-ceq'missing'){$event.referenced_artifacts=@();Write-Json $eventPath $event;Refresh-CandidateHead $Project $CandidatePath -RefreshEventBinding;return $null}
    $candidatePointer=$null;$verifierPointer=$null
    if($Outcome-ceq'candidate_found'){
        $state=Read-Json (Join-Path $Project ([string]$head.goal_host_state.path).Replace('/','\'))
        $ticketRecord=if($null-ne$state.current_ticket){Read-Json (Join-Path $Project ([string]$state.current_ticket.path).Replace('/','\'))}else{$null}
        if($null-ne$ticketRecord-and$ticketRecord.ticket.Contains('candidate_artifact')){$candidatePointer=$ticketRecord.ticket.candidate_artifact}
        else{$candidateRelative=('evidence/attempts/g{0:D4}-candidate.json'-f$generation);Write-Json (Join-Path $Project $candidateRelative.Replace('/','\')) ([ordered]@{schema='fixture-attempt-candidate/v1';generation=$generation});$candidatePointer=Raw-Pointer $Project $candidateRelative}
        $verifiedCandidate=$candidatePointer
        if($Mode-ceq'false_candidate'){$falseRelative=('evidence/attempts/g{0:D4}-false-candidate.json'-f$generation);Write-Json (Join-Path $Project $falseRelative.Replace('/','\')) ([ordered]@{schema='fixture-false-candidate/v1'});$candidatePointer=Raw-Pointer $Project $falseRelative}
        $ticketId=if($null-ne$ticketRecord){[string]$ticketRecord.ticket.ticket_id}else{'verifier-ticket-g'+('{0:D4}'-f$generation)}
        $verifierRelative=('evidence/attempts/g{0:D4}-verifier-result.json'-f$generation)
        Write-Json (Join-Path $Project $verifierRelative.Replace('/','\')) ([ordered]@{
            schema='math-research-verifier-result/v8';project_id=[string]$head.project_id;contract=$head.active_contract
            run=[ordered]@{id=$head.active_run.id;path=$head.active_run.path};ticket_id=$ticketId;role='verifier';candidate_artifact=$verifiedCandidate
            verdict=if($Mode-ceq'verifier_fail'){'FAIL'}else{'PASS'};checked_at_utc=[DateTime]::UtcNow.ToString('o')
        })
        $verifierPointer=Raw-Pointer $Project $verifierRelative
    }
    $outcomeRelative=('evidence/attempts/g{0:D4}-outcome.json'-f$generation)
    Write-Json (Join-Path $Project $outcomeRelative.Replace('/','\')) ([ordered]@{
        schema='math-research-attempt-outcome/v8';project_id=[string]$head.project_id;contract=$head.active_contract
        run=[ordered]@{id=$head.active_run.id;path=$head.active_run.path};attempt_id=('attempt-g{0:D4}'-f$generation);outcome=$Outcome
        candidate=$candidatePointer;verifier_completion=$verifierPointer;completed_at_utc=[DateTime]::UtcNow.ToString('o')
    })
    $outcomePointer=Raw-Pointer $Project $outcomeRelative
    if($Mode-ceq'extra_artifact'){$extraRelative=('evidence/attempts/g{0:D4}-extra.json'-f$generation);Write-Json (Join-Path $Project $extraRelative.Replace('/','\')) ([ordered]@{schema='fixture-extra/v1'});$event.referenced_artifacts=@($outcomePointer,(Raw-Pointer $Project $extraRelative))}else{$event.referenced_artifacts=@($outcomePointer)}
    Write-Json $eventPath $event;Refresh-CandidateHead $Project $CandidatePath -RefreshEventBinding
    return [pscustomobject]@{Pointer=$outcomePointer;Candidate=$candidatePointer;Verifier=$verifierPointer}
}

$script:pwsh = (Get-Process -Id $PID).Path
$script:helper = Join-Path $PSScriptRoot 'commit_math_research_head_v8.ps1'
$script:startup = Join-Path $PSScriptRoot 'invoke_math_research_startup_v3.ps1'
function Start-CommitProcess {
    param([string]$Project,[string]$Candidate,[string]$OldHash,[string]$OldGeneration,[long]$NewGeneration,[string]$HelperPath=$script:helper)
    $psi = [Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $script:pwsh; $psi.UseShellExecute=$false; $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true; $psi.CreateNoWindow=$true
    foreach ($arg in @('-NoProfile','-NonInteractive','-File',$HelperPath,'-ProjectDirectory',$Project,'-CandidateHeadFile',$Candidate,'-ExpectedOldSha256',$OldHash,'-ExpectedOldControlGeneration',$OldGeneration,'-ExpectedNewControlGeneration',[string]$NewGeneration)) { $null=$psi.ArgumentList.Add($arg) }
    return [Diagnostics.Process]::Start($psi)
}
function Wait-CommitProcess([Diagnostics.Process]$Process) {
    $stdout=$Process.StandardOutput.ReadToEnd(); $stderr=$Process.StandardError.ReadToEnd(); $Process.WaitForExit()
    if ([string]::IsNullOrWhiteSpace($stdout)) { throw "Helper emitted no JSON (exit=$($Process.ExitCode), stderr=$stderr)" }
    $json=$stdout.Trim() | ConvertFrom-Json -AsHashtable -Depth 16 -DateKind String
    return [pscustomobject]@{ExitCode=$Process.ExitCode;Json=$json;Stderr=$stderr}
}
function Invoke-Commit { param([string]$Project,[string]$Candidate,[string]$OldHash,[string]$OldGeneration,[long]$NewGeneration,[string]$HelperPath=$script:helper) Wait-CommitProcess (Start-CommitProcess @PSBoundParameters) }
function Invoke-Startup {
    param([string]$Project,[string]$GoalStatus='active')
    $psi=[Diagnostics.ProcessStartInfo]::new();$psi.FileName=$script:pwsh;$psi.UseShellExecute=$false;$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true;$psi.CreateNoWindow=$true
    foreach($arg in @('-NoProfile','-NonInteractive','-File',$script:startup,'-ProjectDirectory',$Project,'-GoalStatus',$GoalStatus)){[void]$psi.ArgumentList.Add($arg)}
    $process=[Diagnostics.Process]::Start($psi);$stdout=$process.StandardOutput.ReadToEnd();$stderr=$process.StandardError.ReadToEnd();$process.WaitForExit()
    if($process.ExitCode-ne 0-or[string]::IsNullOrWhiteSpace($stdout)){throw "Startup e2e failed (exit=$($process.ExitCode), stderr=$stderr, stdout=$stdout)"}
    return ($stdout.Trim()|ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String)
}

$temp = Join-Path ([IO.Path]::GetTempPath()) ('math-research-head-v8-test-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $temp | Out-Null
try {
    # Absent-head genesis.
    $project=New-Project $temp; $c=New-Candidate $project 1
    $r=Invoke-Commit $project $c.Path 'absent' '0' 1
    $eventDebug=Read-Json (Join-Path $project 'state\project-events\g0001.json')
    Assert-Equal $r.ExitCode 0 "absent genesis exit ($($r.Json.reason): $($r.Json.detail); event_id='$($eventDebug.event_id)' type='$($eventDebug.event_id.GetType().FullName)')"; Assert-True ([bool]$r.Json.committed) 'absent genesis committed'
    Assert-Equal (Get-FileHashLower (Join-Path $project 'project.json')) $r.Json.new_sha256 'absent genesis readback hash'
    Assert-Equal @($r.Json.Keys).Count 11 'closed result key set'
    $startupResult=Invoke-Startup $project
    Assert-Equal $startupResult.startup_class 'goal_host_ready' "helper-committed absent genesis is accepted by startup ($($startupResult.recovery_reason))"

    # Existing legacy -> first v8 successor activation.
    $legacy=New-LegacyTransitionFixture $temp
    $r=Invoke-Commit $legacy.Project $legacy.Candidate.Path $legacy.OldHash '0' 1
    Assert-True ([bool]$r.Json.committed) 'generationless legacy successor committed'; Assert-Equal $r.Json.new_control_generation 1 'generationless legacy activates generation 1'
    Assert-True ($null -eq $r.Json.old_control_generation) 'generationless legacy reports null old generation'
    $startupResult=Invoke-Startup $legacy.Project
    Assert-Equal $startupResult.startup_class 'goal_host_ready' "helper-committed legacy successor is accepted by startup ($($startupResult|ConvertTo-Json -Depth 12 -Compress))"
    Assert-True ([bool]$startupResult.legacy_archive_detected) 'startup reports preserved legacy history'
    Assert-True (-not [bool]$startupResult.successor_v8_requires_explicit_new_active_goal) 'activated successor does not require another new Goal'
    $legacy7=New-LegacyTransitionFixture -Base $temp -LegacyControlGeneration 7
    $r=Invoke-Commit $legacy7.Project $legacy7.Candidate.Path $legacy7.OldHash '7' 8
    Assert-True ([bool]$r.Json.committed) 'legacy generation 7 successor committed'; Assert-Equal $r.Json.new_control_generation 8 'legacy generation 7 advances to 8'
    $invalidProject=New-Project $temp; Write-Json (Join-Path $invalidProject 'project.json') ([ordered]@{schema=1;project_id='fixture-project';control_generation='invalid';active_contract=[ordered]@{path='contracts\legacy.md'};active_run=[ordered]@{id='legacy';path='runs\legacy'}})
    $invalidOldHash=Get-FileHashLower (Join-Path $invalidProject 'project.json'); $invalidCandidate=New-Candidate $invalidProject 1
    $r=Invoke-Commit $invalidProject $invalidCandidate.Path $invalidOldHash '0' 1
    Assert-Equal $r.Json.reason 'old_generation_invalid' 'invalid legacy generation fails closed'

    # An existing empty pointerless pre-v8 archive is unsupported; fresh requires absent head.
    $emptyProject=New-Project $temp; Write-Json (Join-Path $emptyProject 'project.json') ([ordered]@{schema=1;project_id='fixture-project';status='empty'})
    $emptyHash=Get-FileHashLower (Join-Path $emptyProject 'project.json'); $emptyCandidate=New-Candidate $emptyProject 1
    $r=Invoke-Commit $emptyProject $emptyCandidate.Path $emptyHash '0' 1
    Assert-Equal $r.Json.reason 'old_head_unsupported' 'existing empty archive cannot masquerade as fresh genesis'

    # Existing v8 -> exactly +1, preserving host binding.
    $fx=New-V8TransitionFixture $temp
    $r=Invoke-Commit $fx.Project $fx.Candidate.Path $fx.OldHash '1' 2
    Assert-True ([bool]$r.Json.committed) 'v8 plus-one committed'; Assert-Equal $r.Json.new_control_generation 2 'v8 advances one generation'
    $startupResult=Invoke-Startup $fx.Project
    Assert-Equal $startupResult.startup_class 'goal_host_ready' "helper-committed ordinary generation is accepted by startup ($($startupResult.recovery_reason))"
    $g2Hash=Get-FileHashLower (Join-Path $fx.Project 'project.json')
    $g3=New-Candidate -Project $fx.Project -Generation 3 -PreservedHostBinding $fx.G1.HostBinding
    $r=Invoke-Commit $fx.Project $g3.Path $g2Hash '2' 3
    Assert-True ([bool]$r.Json.committed) 'ordinary lifecycle g2 to g3 preserves host binding'

    # Stale hash and stale generation never alter the old head.
    $fx=New-V8TransitionFixture $temp; $before=Get-FileHashLower (Join-Path $fx.Project 'project.json')
    $r=Invoke-Commit $fx.Project $fx.Candidate.Path ('0'*64) '1' 2
    Assert-Equal $r.Json.reason 'stale_hash' 'stale hash rejected'; Assert-Equal (Get-FileHashLower (Join-Path $fx.Project 'project.json')) $before 'stale hash preserves head'
    $r=Invoke-Commit $fx.Project $fx.Candidate.Path $fx.OldHash '2' 2
    Assert-Equal $r.Json.reason 'stale_generation' 'stale generation rejected'; Assert-Equal (Get-FileHashLower (Join-Path $fx.Project 'project.json')) $before 'stale generation preserves head'

    # Candidate strict-JSON tamper, schema mismatch, and project mismatch.
    $fx=New-V8TransitionFixture $temp; $before=$fx.OldHash
    $raw=Get-Content -LiteralPath $fx.Candidate.Path -Raw; Write-Utf8 $fx.Candidate.Path ($raw.Replace('{"schema":','{"schema":"duplicate","schema":'))
    $r=Invoke-Commit $fx.Project $fx.Candidate.Path $fx.OldHash '1' 2
    Assert-Equal $r.Json.reason 'strict_json_invalid' 'duplicate candidate property rejected'; Assert-Equal (Get-FileHashLower (Join-Path $fx.Project 'project.json')) $before 'candidate tamper preserves head'
    $fx=New-V8TransitionFixture $temp; $h=Read-Json $fx.Candidate.Path; $h.schema='wrong'; Write-Json $fx.Candidate.Path $h
    $r=Invoke-Commit $fx.Project $fx.Candidate.Path $fx.OldHash '1' 2; Assert-Equal $r.Json.reason 'candidate_schema_invalid' 'candidate schema rejected'
    $fx=New-V8TransitionFixture $temp; $h=Read-Json $fx.Candidate.Path; $h.project_id='different-project'; Write-Json $fx.Candidate.Path $h
    $r=Invoke-Commit $fx.Project $fx.Candidate.Path $fx.OldHash '1' 2; Assert-Equal $r.Json.reason 'project_id_mismatch' 'candidate project mismatch rejected'

    # Pointer tamper and missing target.
    $fx=New-V8TransitionFixture $temp; Add-Content -LiteralPath (Join-Path $fx.Project 'state\generations\g0002\checkpoint.json') -Value ' ' -Encoding UTF8
    $r=Invoke-Commit $fx.Project $fx.Candidate.Path $fx.OldHash '1' 2; Assert-Equal $r.Json.reason 'pointer_hash_mismatch' 'pointer target tamper rejected'
    $fx=New-V8TransitionFixture $temp; Remove-Item -LiteralPath (Join-Path $fx.Project 'state\generations\g0002\checkpoint.json')
    $r=Invoke-Commit $fx.Project $fx.Candidate.Path $fx.OldHash '1' 2; Assert-Equal $r.Json.reason 'referenced_file_missing' 'missing pointer target rejected'

    # Dot path escape and reparse-point candidate route.
    $fx=New-V8TransitionFixture $temp
    $dotCandidate=Join-Path $fx.Project 'state\staging\..\staging\candidate-g0002.json'
    $r=Invoke-Commit $fx.Project $dotCandidate $fx.OldHash '1' 2; Assert-Equal $r.Json.reason 'unsafe_candidate_path' 'dot segment rejected'
    $fx=New-V8TransitionFixture $temp
    $outside=Join-Path $temp ('outside-' + [guid]::NewGuid().ToString('N')); New-Item -ItemType Directory -Path $outside | Out-Null
    Copy-Item -LiteralPath $fx.Candidate.Path -Destination (Join-Path $outside 'candidate-g0002.json')
    Remove-Item -LiteralPath (Join-Path $fx.Project 'state\staging') -Recurse -Force
    New-Item -ItemType Junction -Path (Join-Path $fx.Project 'state\staging') -Target $outside | Out-Null
    $r=Invoke-Commit $fx.Project (Join-Path $fx.Project 'state\staging\candidate-g0002.json') $fx.OldHash '1' 2
    Assert-Equal $r.Json.reason 'reparse_point_forbidden' 'reparse candidate route rejected'

    # First activation is a zero-counter fresh RUN_GENESIS with an exact head/genesis/binding chain.
    $project=New-Project $temp;$nonzero=[ordered]@{attempt_count=1;audit_count=0;total_round_count=1;attempts_since_last_audit=1;audit_due=$false};$c=New-Candidate -Project $project -Generation 1 -CountersOverride $nonzero
    $r=Invoke-Commit $project $c.Path 'absent' '0' 1;Assert-Equal $r.Json.reason 'first_activation_invalid' 'fresh activation cannot import nonzero counters'
    $project=New-Project $temp;$c=New-Candidate -Project $project -Generation 1 -EventTypeOverride CHECKPOINT_COMMIT
    $r=Invoke-Commit $project $c.Path 'absent' '0' 1;Assert-Equal $r.Json.reason 'first_activation_invalid' 'fresh activation requires RUN_GENESIS event'
    $project=New-Project $temp;$c=New-Candidate $project 1;$head=Read-Json $c.Path;$head.competing_authority='forbidden';Write-Json $c.Path $head
    $r=Invoke-Commit $project $c.Path 'absent' '0' 1;Assert-Equal $r.Json.reason 'shape_invalid' 'project head rejects unknown authority key'
    $project=New-Project $temp;$c=New-Candidate $project 1;$fakeRelative='runs/run-0001/host-bindings/dummy-bind.json';$realHost=Read-Json (Join-Path $project $c.HostBinding.path.Replace('/','\'));Write-Json (Join-Path $project $fakeRelative.Replace('/','\')) $realHost
    $genesisPath=Join-Path $project 'runs\run-0001\run.json';$genesis=Read-Json $genesisPath;$genesis.host_binding=Raw-Pointer $project $fakeRelative;Write-Json $genesisPath $genesis
    $r=Invoke-Commit $project $c.Path 'absent' '0' 1;Assert-Equal $r.Json.reason 'cross_binding_mismatch' 'RUN_GENESIS cannot point at a dummy binding instead of activated HOST_BIND'

    # Cycle policy is the closed worker-tool and per-ticket resource authority.
    $project=New-Project $temp;$c=New-Candidate -Project $project -Generation 1 -PolicyAllowedWorkerTools @('apply_patch','collaboration.spawn_agent','shell_command') -TicketAllowedTools @('apply_patch');$r=Invoke-Commit $project $c.Path 'absent' '0' 1;Assert-True ([bool]$r.Json.committed) 'apply_patch is accepted by the exact global worker-tool set';Assert-Equal (Invoke-Startup $project).startup_class 'goal_host_ready' 'apply_patch-authorized helper output is startup-readable'
    $project=New-Project $temp;$c=New-Candidate -Project $project -Generation 1 -PolicyAllowedWorkerTools @('create_goal') -TicketAllowedTools @('create_goal');$r=Invoke-Commit $project $c.Path 'absent' '0' 1;Assert-Equal $r.Json.reason 'contract_invalid' 'Goal control tools are forbidden even when named in policy'
    $project=New-Project $temp;$c=New-Candidate -Project $project -Generation 1 -PolicyAllowedWorkerTools @('exec') -TicketAllowedTools @('exec');$r=Invoke-Commit $project $c.Path 'absent' '0' 1;Assert-Equal $r.Json.reason 'contract_invalid' 'generic exec authority is outside the exact worker-tool set'
    $project=New-Project $temp;$c=New-Candidate -Project $project -Generation 1 -PolicyAllowedWorkerTools @('read_file') -TicketAllowedTools @('read_file');$r=Invoke-Commit $project $c.Path 'absent' '0' 1;Assert-Equal $r.Json.reason 'contract_invalid' 'benign-looking unknown tool is rejected by the exact worker-tool set'
    $project=New-Project $temp;$c=New-Candidate -Project $project -Generation 1 -TicketAllowedTools @('web.run');$r=Invoke-Commit $project $c.Path 'absent' '0' 1;Assert-Equal $r.Json.reason 'ticket_invalid' 'ticket tool outside the policy allowlist is rejected'
    $project=New-Project $temp;$c=New-Candidate -Project $project -Generation 1 -WebSearch denied -PolicyAllowedWorkerTools @('apply_patch','web__run') -TicketAllowedTools @('apply_patch');$r=Invoke-Commit $project $c.Path 'absent' '0' 1;Assert-Equal $r.Json.reason 'contract_invalid' 'network-denied Contract cannot authorize web__run in policy'
    $project=New-Project $temp;$c=New-Candidate -Project $project -Generation 1 -WebSearch denied -PolicyAllowedWorkerTools @('apply_patch','shell_command') -TicketAllowedTools @('apply_patch');$r=Invoke-Commit $project $c.Path 'absent' '0' 1;Assert-True ([bool]$r.Json.committed) 'network-denied Contract remains executable without web__run';Assert-Equal (Invoke-Startup $project).startup_class 'goal_host_ready' 'network-denied no-web helper output is startup-readable'
    $project=New-Project $temp;$c=New-Candidate -Project $project -Generation 1 -PolicyAllowedWorkerTools @('apply_patch','web__run') -TicketAllowedTools @('apply_patch','web__run');$r=Invoke-Commit $project $c.Path 'absent' '0' 1;Assert-True ([bool]$r.Json.committed) 'network-allowed Contract may authorize web__run'
    $project=New-Project $temp;$c=New-Candidate -Project $project -Generation 1 -TicketToolCalls 33;$r=Invoke-Commit $project $c.Path 'absent' '0' 1;Assert-Equal $r.Json.reason 'ticket_invalid' 'ticket tool-call cap cannot exceed cycle policy'
    $project=New-Project $temp;$c=New-Candidate -Project $project -Generation 1 -TicketMaxOutputBytes 8388609;$r=Invoke-Commit $project $c.Path 'absent' '0' 1;Assert-Equal $r.Json.reason 'ticket_invalid' 'ticket output cap cannot exceed cycle policy'
    $project=New-Project $temp;$oneRoundGenesis=New-Candidate -Project $project -Generation 1 -AttemptBudget 1 -TotalRoundBudget 2;$r=Invoke-Commit $project $oneRoundGenesis.Path 'absent' '0' 1;Assert-True ([bool]$r.Json.committed) "two-round Contract genesis committed ($($r.Json.reason): $($r.Json.detail))"
    $oneRoundHash=Get-FileHashLower (Join-Path $project 'project.json');$earlyAuditCounters=[ordered]@{attempt_count=0;audit_count=1;total_round_count=1;attempts_since_last_audit=0;audit_due=$false};$earlyAudit=New-Candidate -Project $project -Generation 2 -PreservedHostBinding $oneRoundGenesis.HostBinding -CountersOverride $earlyAuditCounters -EventTypeOverride AUDIT_START -RunStatus auditing -DerivedTicket -TicketStatus active -AttemptBudget 1 -TotalRoundBudget 2;$null=Set-CycleAuditStartFixture -Project $project -CandidatePath $earlyAudit.Path -AuditKind early
    $r=Invoke-Commit $project $earlyAudit.Path $oneRoundHash '1' 2;Assert-True ([bool]$r.Json.committed) 'early audit legitimately leaves exactly one total round'
    $oneRoundHash=Get-FileHashLower (Join-Path $project 'project.json');$earlySummary=New-CycleAuditEvidence -Project $project -AuditKind early -EndGeneration 3;$earlyAuditEnd=New-Candidate -Project $project -Generation 3 -PreservedHostBinding $oneRoundGenesis.HostBinding -CountersOverride $earlyAuditCounters -EventTypeOverride AUDIT_END -RunStatus preparing -DerivedTicket -TicketStatus ready -ReferencedArtifacts @($earlySummary) -AttemptBudget 1 -TotalRoundBudget 2
    $r=Invoke-Commit $project $earlyAuditEnd.Path $oneRoundHash '2' 3;Assert-True ([bool]$r.Json.committed) 'early audit closes into a valid nonterminal one-round-remaining head'
    $oneRoundHash=Get-FileHashLower (Join-Path $project 'project.json');$oneRoundStartCounters=[ordered]@{attempt_count=1;audit_count=1;total_round_count=2;attempts_since_last_audit=1;audit_due=$false};$oneRoundStart=New-Candidate -Project $project -Generation 4 -PreservedHostBinding $oneRoundGenesis.HostBinding -CountersOverride $oneRoundStartCounters -EventTypeOverride ATTEMPT_START -RunStatus attempt_running -DerivedTicket -TicketStatus active -AttemptBudget 1 -TotalRoundBudget 2
    $r=Invoke-Commit $project $oneRoundStart.Path $oneRoundHash '3' 4;Assert-Equal $r.Json.reason 'attempt_start_forbidden' 'non-interval ATTEMPT_START cannot consume the final round needed by a possible terminal audit'

    # A complete ATTEMPT/AUDIT sequence enforces exact start accounting, interval gates, and ticket/event bindings.
    $fx=New-V8TransitionFixture $temp
    $extraCounterCandidate=New-Candidate -Project $fx.Project -Generation 2 -PreservedHostBinding $fx.G1.HostBinding;$extraCounterCheckpoint=Join-Path $fx.Project 'state\generations\g0002\checkpoint.json';$extraCounterRecord=Read-Json $extraCounterCheckpoint;$extraCounterRecord.counters.shadow_counter=0;Write-Json $extraCounterCheckpoint $extraCounterRecord;Refresh-CandidateHead $fx.Project $extraCounterCandidate.Path
    $r=Invoke-Commit $fx.Project $extraCounterCandidate.Path $fx.OldHash '1' 2;Assert-Equal $r.Json.reason 'shape_invalid' 'counter objects reject unknown competing fields'
    $missingRound=[ordered]@{attempt_count=1;audit_count=0;total_round_count=0;attempts_since_last_audit=1;audit_due=$false};$badRoundStart=New-Candidate -Project $fx.Project -Generation 2 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $missingRound -EventTypeOverride ATTEMPT_START -RunStatus attempt_running -DerivedTicket -TicketStatus active
    $r=Invoke-Commit $fx.Project $badRoundStart.Path $fx.OldHash '1' 2;Assert-Equal $r.Json.reason 'counter_invalid' 'ATTEMPT_START cannot omit its total-round increment'
    $extraRound=[ordered]@{attempt_count=0;audit_count=0;total_round_count=1;attempts_since_last_audit=0;audit_due=$false};$badRoundCommit=New-Candidate -Project $fx.Project -Generation 2 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $extraRound -EventTypeOverride CHECKPOINT_COMMIT -RunStatus not_started
    $r=Invoke-Commit $fx.Project $badRoundCommit.Path $fx.OldHash '1' 2;Assert-Equal $r.Json.reason 'counter_invalid' 'non-start event cannot invent a total round'
    $startCounters=[ordered]@{attempt_count=1;audit_count=0;total_round_count=1;attempts_since_last_audit=1;audit_due=$false}
    $badStart=New-Candidate -Project $fx.Project -Generation 2 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $startCounters -EventTypeOverride ATTEMPT_START -RunStatus not_started -DerivedTicket -TicketStatus active
    $r=Invoke-Commit $fx.Project $badStart.Path $fx.OldHash '1' 2;Assert-Equal $r.Json.reason 'ticket_invalid' 'ATTEMPT_START cannot consume counters while remaining ready'
    $start=New-Candidate -Project $fx.Project -Generation 2 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $startCounters -EventTypeOverride ATTEMPT_START -RunStatus attempt_running -DerivedTicket -TicketStatus active
    $statePath=Join-Path $fx.Project 'state\generations\g0002\goal-host-v8.json';$state=Read-Json $statePath;$ticketEventPath=Join-Path $fx.Project ([string]$state.current_ticket.source_event.path).Replace('/','\');$ticketEvent=Read-Json $ticketEventPath;$ticketEvent.dependencies=@([ordered]@{ticket_id='forged';path='state/problem.md';sha256=Get-FileHashLower (Join-Path $fx.Project 'state\problem.md')});Write-Json $ticketEventPath $ticketEvent;$state.current_ticket.source_event.sha256=Get-FileHashLower $ticketEventPath;Write-Json $statePath $state;Refresh-CandidateHead $fx.Project $start.Path
    $r=Invoke-Commit $fx.Project $start.Path $fx.OldHash '1' 2;Assert-Equal $r.Json.reason 'ticket_invalid' 'derived ticket event dependencies must equal frozen ticket dependencies'
    $start=New-Candidate -Project $fx.Project -Generation 2 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $startCounters -EventTypeOverride ATTEMPT_START -RunStatus attempt_running -DerivedTicket -TicketStatus active
    $r=Invoke-Commit $fx.Project $start.Path $fx.OldHash '1' 2;Assert-True ([bool]$r.Json.committed) 'ATTEMPT_START exact +1 transition committed';Assert-Equal (Invoke-Startup $fx.Project).startup_class 'goal_host_resume' 'ATTEMPT_START helper output is startup-resumable'

    # Verifier tickets are derived and bind one exact candidate plus completed dependencies.
    $vf=New-V8TransitionFixture $temp;$forbiddenVerifierStart=New-Candidate -Project $vf.Project -Generation 2 -PreservedHostBinding $vf.G1.HostBinding -CountersOverride $startCounters -EventTypeOverride ATTEMPT_START -RunStatus attempt_running -DerivedTicket -TicketStatus active;Set-DerivedVerifierTicket -Project $vf.Project -CandidatePath $forbiddenVerifierStart.Path
    $r=Invoke-Commit $vf.Project $forbiddenVerifierStart.Path $vf.OldHash '1' 2;Assert-Equal $r.Json.reason 'lifecycle_transition_invalid' 'ATTEMPT_START cannot use a verifier ticket'
    foreach($mode in @('missing_candidate','empty_dependencies','candidate_not_input','random_dependency_hash','missing_completion','wrong_completion_role','completion_in_verifier_staging')){
        $vf=New-V8TransitionFixture $temp;$solverStart=New-Candidate -Project $vf.Project -Generation 2 -PreservedHostBinding $vf.G1.HostBinding -CountersOverride $startCounters -EventTypeOverride ATTEMPT_START -RunStatus attempt_running -DerivedTicket -TicketStatus active
        $r=Invoke-Commit $vf.Project $solverStart.Path $vf.OldHash '1' 2;Assert-True ([bool]$r.Json.committed) "verifier fixture solver start committed for $mode"
        $solverHeadHash=Get-FileHashLower (Join-Path $vf.Project 'project.json');$vc=New-Candidate -Project $vf.Project -Generation 3 -PreservedHostBinding $vf.G1.HostBinding -CountersOverride $startCounters -EventTypeOverride CHECKPOINT_COMMIT -RunStatus attempt_running -DerivedTicket -TicketStatus active
        Set-DerivedVerifierTicket -Project $vf.Project -CandidatePath $vc.Path -Mode $mode
        $r=Invoke-Commit $vf.Project $vc.Path $solverHeadHash '2' 3;Assert-True (-not[bool]$r.Json.committed) "verifier mode $mode is rejected"
    }
    $vf=New-V8TransitionFixture $temp;$solverStart=New-Candidate -Project $vf.Project -Generation 2 -PreservedHostBinding $vf.G1.HostBinding -CountersOverride $startCounters -EventTypeOverride ATTEMPT_START -RunStatus attempt_running -DerivedTicket -TicketStatus active;$r=Invoke-Commit $vf.Project $solverStart.Path $vf.OldHash '1' 2;Assert-True ([bool]$r.Json.committed) 'valid verifier fixture solver start committed'
    $solverHeadHash=Get-FileHashLower (Join-Path $vf.Project 'project.json');$vc=New-Candidate -Project $vf.Project -Generation 3 -PreservedHostBinding $vf.G1.HostBinding -CountersOverride $startCounters -EventTypeOverride CHECKPOINT_COMMIT -RunStatus attempt_running -DerivedTicket -TicketStatus active;Set-DerivedVerifierTicket -Project $vf.Project -CandidatePath $vc.Path
    $r=Invoke-Commit $vf.Project $vc.Path $solverHeadHash '2' 3;Assert-True ([bool]$r.Json.committed) "derived verifier binds one candidate artifact and completed solver dependency ($($r.Json.reason): $($r.Json.detail))";Assert-Equal (Invoke-Startup $vf.Project).startup_class 'goal_host_resume' 'valid derived verifier is startup-readable'
    $headHash=Get-FileHashLower (Join-Path $fx.Project 'project.json')
    $delayed=[ordered]@{attempt_count=2;audit_count=0;total_round_count=2;attempts_since_last_audit=1;audit_due=$false};$badEnd=New-Candidate -Project $fx.Project -Generation 3 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $delayed -EventTypeOverride ATTEMPT_END -RunStatus preparing
    $null=Set-AttemptOutcomeFixture -Project $fx.Project -CandidatePath $badEnd.Path -Outcome no_candidate
    $r=Invoke-Commit $fx.Project $badEnd.Path $headHash '2' 3;Assert-Equal $r.Json.reason 'counter_transition_invalid' 'ATTEMPT_END cannot delay attempt counter consumption'
    $pausedEnd=New-Candidate -Project $fx.Project -Generation 3 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $startCounters -EventTypeOverride ATTEMPT_END -RunStatus paused -DerivedTicket -TicketStatus ready
    $null=Set-AttemptOutcomeFixture -Project $fx.Project -CandidatePath $pausedEnd.Path -Outcome no_candidate
    $r=Invoke-Commit $fx.Project $pausedEnd.Path $headHash '2' 3;Assert-Equal $r.Json.reason 'lifecycle_transition_invalid' 'ATTEMPT_END cannot masquerade as capsule-bound PAUSE'
    $end=New-Candidate -Project $fx.Project -Generation 3 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $startCounters -EventTypeOverride ATTEMPT_END -RunStatus preparing
    $null=Set-AttemptOutcomeFixture -Project $fx.Project -CandidatePath $end.Path -Outcome no_candidate
    $r=Invoke-Commit $fx.Project $end.Path $headHash '2' 3;Assert-True ([bool]$r.Json.committed) 'ATTEMPT_END preserves consumed counters'
    $headHash=Get-FileHashLower (Join-Path $fx.Project 'project.json')
    $thresholdBad=[ordered]@{attempt_count=2;audit_count=0;total_round_count=2;attempts_since_last_audit=2;audit_due=$false};$badThreshold=New-Candidate -Project $fx.Project -Generation 4 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $thresholdBad -EventTypeOverride ATTEMPT_START -RunStatus attempt_running -DerivedTicket -TicketStatus active
    $r=Invoke-Commit $fx.Project $badThreshold.Path $headHash '3' 4;Assert-Equal $r.Json.reason 'audit_gate_invalid' 'interval hit cannot leave audit_due false'
    $threshold=[ordered]@{attempt_count=2;audit_count=0;total_round_count=2;attempts_since_last_audit=2;audit_due=$true};$start2=New-Candidate -Project $fx.Project -Generation 4 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $threshold -EventTypeOverride ATTEMPT_START -RunStatus attempt_running -DerivedTicket -TicketStatus active
    $r=Invoke-Commit $fx.Project $start2.Path $headHash '3' 4;Assert-True ([bool]$r.Json.committed) 'interval-hitting ATTEMPT_START sets audit gate'
    $headHash=Get-FileHashLower (Join-Path $fx.Project 'project.json');$due=New-Candidate -Project $fx.Project -Generation 5 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $threshold -EventTypeOverride ATTEMPT_END -RunStatus audit_due -DerivedTicket -TicketStatus ready
    $null=Set-AttemptOutcomeFixture -Project $fx.Project -CandidatePath $due.Path -Outcome no_candidate
    $r=Invoke-Commit $fx.Project $due.Path $headHash '4' 5;Assert-True ([bool]$r.Json.committed) 'ATTEMPT_END enters audit_due at threshold'
    $headHash=Get-FileHashLower (Join-Path $fx.Project 'project.json');$bypass=New-Candidate -Project $fx.Project -Generation 6 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $threshold -EventTypeOverride ATTEMPT_START -RunStatus attempt_running -DerivedTicket -TicketStatus active
    $r=Invoke-Commit $fx.Project $bypass.Path $headHash '5' 6;Assert-Equal $r.Json.reason 'attempt_start_forbidden' 'audit_due gate blocks another ATTEMPT_START'
    $auditCounters=[ordered]@{attempt_count=2;audit_count=1;total_round_count=3;attempts_since_last_audit=2;audit_due=$true};$auditStart=New-Candidate -Project $fx.Project -Generation 6 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $auditCounters -EventTypeOverride AUDIT_START -RunStatus auditing -DerivedTicket -TicketStatus active
    $null=Set-CycleAuditStartFixture -Project $fx.Project -CandidatePath $auditStart.Path -AuditKind scheduled
    $r=Invoke-Commit $fx.Project $auditStart.Path $headHash '5' 6;Assert-True ([bool]$r.Json.committed) 'AUDIT_START consumes exactly one audit round'
    $headHash=Get-FileHashLower (Join-Path $fx.Project 'project.json');$auditSummary=New-CycleAuditEvidence -Project $fx.Project -AuditKind scheduled -EndGeneration 9
    $auditEndCounters=[ordered]@{attempt_count=2;audit_count=1;total_round_count=3;attempts_since_last_audit=0;audit_due=$false};$pausedAuditEnd=New-Candidate -Project $fx.Project -Generation 7 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $auditEndCounters -EventTypeOverride AUDIT_END -RunStatus paused -DerivedTicket -TicketStatus ready -ReferencedArtifacts @($auditSummary)
    $r=Invoke-Commit $fx.Project $pausedAuditEnd.Path $headHash '6' 7;Assert-Equal $r.Json.reason 'lifecycle_transition_invalid' 'AUDIT_END cannot masquerade as capsule-bound PAUSE'
    $auditPause=New-Candidate -Project $fx.Project -Generation 7 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $auditCounters -EventTypeOverride PAUSE -RunStatus paused -DerivedTicket -TicketStatus active
    $null=Set-PauseCandidateFixture -Project $fx.Project -CandidatePath $auditPause.Path
    $r=Invoke-Commit $fx.Project $auditPause.Path $headHash '6' 7;Assert-True ([bool]$r.Json.committed) 'active audit PAUSE freezes one exact resume capsule';Assert-Equal (Invoke-Startup $fx.Project).startup_class 'goal_host_audit_due' 'paused scheduled audit remains on the audit route'
    $headHash=Get-FileHashLower (Join-Path $fx.Project 'project.json');$auditResume=New-Candidate -Project $fx.Project -Generation 8 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $auditCounters -EventTypeOverride RESUME -RunStatus auditing -DerivedTicket -TicketStatus active
    Set-ResumeCandidateFixture -Project $fx.Project -CandidatePath $auditResume.Path
    $r=Invoke-Commit $fx.Project $auditResume.Path $headHash '7' 8;Assert-True ([bool]$r.Json.committed) 'RESUME restores exact paused audit ticket/lifecycle/counters';Assert-Equal (Invoke-Startup $fx.Project).startup_class 'goal_host_audit_due' 'resumed audit remains startup-readable'
    $headHash=Get-FileHashLower (Join-Path $fx.Project 'project.json');$auditEnd=New-Candidate -Project $fx.Project -Generation 9 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $auditEndCounters -EventTypeOverride AUDIT_END -RunStatus preparing -DerivedTicket -TicketStatus ready -ReferencedArtifacts @($auditSummary)
    $r=Invoke-Commit $fx.Project $auditEnd.Path $headHash '8' 9;Assert-True ([bool]$r.Json.committed) 'AUDIT_END exactly resets interval gate with three-role summary';Assert-Equal (Invoke-Startup $fx.Project).startup_class 'goal_host_ready' 'AUDIT_END prepared result is startup-readable'
    $completionFx=$fx;$completionHost=$fx.G1.HostBinding

    # PAUSE is legal only for an active attempt/audit with an immutable resume capsule.
    $fx=New-V8TransitionFixture $temp;$pause=New-Candidate -Project $fx.Project -Generation 2 -PreservedHostBinding $fx.G1.HostBinding -EventTypeOverride PAUSE -RunStatus paused
    $r=Invoke-Commit $fx.Project $pause.Path $fx.OldHash '1' 2;Assert-Equal $r.Json.reason 'resume_capsule_invalid' 'pre-first-attempt PAUSE cannot fabricate an unpaid resumable capsule'
    $fx=New-V8TransitionFixture $temp;$attemptCounters=[ordered]@{attempt_count=1;audit_count=0;total_round_count=1;attempts_since_last_audit=1;audit_due=$false}
    $attemptStart=New-Candidate -Project $fx.Project -Generation 2 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $attemptCounters -EventTypeOverride ATTEMPT_START -RunStatus attempt_running -DerivedTicket -TicketStatus active
    $r=Invoke-Commit $fx.Project $attemptStart.Path $fx.OldHash '1' 2;Assert-True ([bool]$r.Json.committed) 'attempt pause fixture starts one paid solver attempt'
    $headHash=Get-FileHashLower (Join-Path $fx.Project 'project.json');$attemptPause=New-Candidate -Project $fx.Project -Generation 3 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $attemptCounters -EventTypeOverride PAUSE -RunStatus paused -DerivedTicket -TicketStatus active
    $null=Set-PauseCandidateFixture -Project $fx.Project -CandidatePath $attemptPause.Path
    $r=Invoke-Commit $fx.Project $attemptPause.Path $headHash '2' 3;Assert-True ([bool]$r.Json.committed) 'active attempt PAUSE freezes exact ticket/lifecycle/counters'
    $headHash=Get-FileHashLower (Join-Path $fx.Project 'project.json');$pausedCheckpoint=New-Candidate -Project $fx.Project -Generation 4 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $attemptCounters -EventTypeOverride CHECKPOINT_COMMIT -RunStatus paused -DerivedTicket -TicketStatus active
    Set-ResumeCandidateFixture -Project $fx.Project -CandidatePath $pausedCheckpoint.Path
    $r=Invoke-Commit $fx.Project $pausedCheckpoint.Path $headHash '3' 4;Assert-Equal $r.Json.reason 'resume_capsule_invalid' 'paused head rejects CHECKPOINT_COMMIT even when it republishes the capsule'
    $pausedAgain=New-Candidate -Project $fx.Project -Generation 4 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $attemptCounters -EventTypeOverride PAUSE -RunStatus paused -DerivedTicket -TicketStatus active
    Set-ResumeCandidateFixture -Project $fx.Project -CandidatePath $pausedAgain.Path
    $r=Invoke-Commit $fx.Project $pausedAgain.Path $headHash '3' 4;Assert-Equal $r.Json.reason 'resume_capsule_invalid' 'paused head rejects every non-RESUME/non-HOST_REBIND event'
    $headHash=Get-FileHashLower (Join-Path $fx.Project 'project.json');$attemptResume=New-Candidate -Project $fx.Project -Generation 4 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $attemptCounters -EventTypeOverride RESUME -RunStatus attempt_running -DerivedTicket -TicketStatus active
    Set-ResumeCandidateFixture -Project $fx.Project -CandidatePath $attemptResume.Path
    $r=Invoke-Commit $fx.Project $attemptResume.Path $headHash '3' 4;Assert-True ([bool]$r.Json.committed) 'RESUME restores exact paid attempt';Assert-Equal (Invoke-Startup $fx.Project).startup_class 'goal_host_resume' 'resumed paid attempt is startup-readable'
    $fx=New-V8TransitionFixture $temp;$awaitCounters=[ordered]@{attempt_count=1;audit_count=0;total_round_count=1;attempts_since_last_audit=1;audit_due=$false}
    $awaitStart=New-Candidate -Project $fx.Project -Generation 2 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $awaitCounters -EventTypeOverride ATTEMPT_START -RunStatus attempt_running -DerivedTicket -TicketStatus active;$r=Invoke-Commit $fx.Project $awaitStart.Path $fx.OldHash '1' 2;Assert-True ([bool]$r.Json.committed) 'awaiting-input fixture starts one paid attempt'
    $headHash=Get-FileHashLower (Join-Path $fx.Project 'project.json');$awaitEnd=New-Candidate -Project $fx.Project -Generation 3 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $awaitCounters -EventTypeOverride ATTEMPT_END -RunStatus awaiting_input -DerivedTicket -TicketStatus ready;$null=Set-AttemptOutcomeFixture -Project $fx.Project -CandidatePath $awaitEnd.Path -Outcome awaiting_input;$r=Invoke-Commit $fx.Project $awaitEnd.Path $headHash '2' 3;Assert-True ([bool]$r.Json.committed) 'ATTEMPT_END may enter awaiting_input without changing its gate'
    $headHash=Get-FileHashLower (Join-Path $fx.Project 'project.json');$forgedDueResume=New-Candidate -Project $fx.Project -Generation 4 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $awaitCounters -EventTypeOverride RESUME -RunStatus audit_due -DerivedTicket -TicketStatus ready;$r=Invoke-Commit $fx.Project $forgedDueResume.Path $headHash '3' 4;Assert-Equal $r.Json.reason 'resume_capsule_invalid' 'awaiting_input RESUME cannot invent audit_due when the durable gate is false'
    $readyResume=New-Candidate -Project $fx.Project -Generation 4 -PreservedHostBinding $fx.G1.HostBinding -CountersOverride $awaitCounters -EventTypeOverride RESUME -RunStatus preparing -DerivedTicket -TicketStatus ready;$r=Invoke-Commit $fx.Project $readyResume.Path $headHash '3' 4;Assert-True ([bool]$r.Json.committed) 'awaiting_input RESUME with false gate returns only to preparing'
    $fx=New-V8TransitionFixture $temp;$nullTicket=New-Candidate -Project $fx.Project -Generation 2 -PreservedHostBinding $fx.G1.HostBinding
    $statePath=Join-Path $fx.Project 'state\generations\g0002\goal-host-v8.json';$checkpointPath=Join-Path $fx.Project 'state\generations\g0002\checkpoint.json';$state=Read-Json $statePath;$state.current_ticket=$null;Write-Json $statePath $state;$checkpoint=Read-Json $checkpointPath;$checkpoint.current_lifecycle=$null;Write-Json $checkpointPath $checkpoint;Refresh-CandidateHead $fx.Project $nullTicket.Path
    $r=Invoke-Commit $fx.Project $nullTicket.Path $fx.OldHash '1' 2;Assert-Equal $r.Json.reason 'ticket_invalid' 'null ticket/lifecycle is forbidden in nonterminal state'
    $fx=New-V8TransitionFixture $temp;$closedTicket=New-Candidate -Project $fx.Project -Generation 2 -PreservedHostBinding $fx.G1.HostBinding -TicketStatus closed;$r=Invoke-Commit $fx.Project $closedTicket.Path $fx.OldHash '1' 2;Assert-Equal $r.Json.reason 'ticket_invalid' 'closed ticket is forbidden on a nonterminal run'

    # HOST_REBIND changes only the Goal-binding chain and survives ordinary later commits.
    $fx=New-V8TransitionFixture $temp;$newGoal=[ordered]@{thread_id_available=$true;thread_id='thread-rebound';objective_raw_sha256=Get-TextHash 'rebound fixture goal'}
    $rebind=New-Candidate -Project $fx.Project -Generation 2 -RebindFrom $fx.G1.HostBinding -HostGoalOverride $newGoal -EventTypeOverride HOST_REBIND -RunStatus not_started
    $r=Invoke-Commit $fx.Project $rebind.Path $fx.OldHash '1' 2;Assert-True ([bool]$r.Json.committed) "HOST_REBIND exact chain committed ($($r.Json.reason): $($r.Json.detail))";Assert-Equal (Invoke-Startup $fx.Project).startup_class 'goal_host_ready' 'HOST_REBIND helper output is startup-readable'
    $headHash=Get-FileHashLower (Join-Path $fx.Project 'project.json');$afterRebind=New-Candidate -Project $fx.Project -Generation 3 -PreservedHostBinding $rebind.HostBinding -HostGoalOverride $newGoal -RunStatus not_started
    $r=Invoke-Commit $fx.Project $afterRebind.Path $headHash '2' 3;Assert-True ([bool]$r.Json.committed) 'ordinary generation preserves prior HOST_REBIND pointer';Assert-Equal (Invoke-Startup $fx.Project).startup_class 'goal_host_ready' 'ordinary post-rebind generation is startup-readable'
    $fx=New-V8TransitionFixture $temp;$badRebind=New-Candidate -Project $fx.Project -Generation 2 -RebindFrom $fx.G1.HostBinding -HostGoalOverride $newGoal -EventTypeOverride CHECKPOINT_COMMIT
    $r=Invoke-Commit $fx.Project $badRebind.Path $fx.OldHash '1' 2;Assert-Equal $r.Json.reason 'host_binding_drift' 'changed host binding requires HOST_REBIND project event'

    # A non-interval attempt can also find a candidate, so its reserved audit round must remain usable.
    $nonIntervalProject=New-Project $temp;$nonIntervalGenesis=New-Candidate -Project $nonIntervalProject -Generation 1;$r=Invoke-Commit $nonIntervalProject $nonIntervalGenesis.Path 'absent' '0' 1;Assert-True ([bool]$r.Json.committed) 'non-interval completion chain genesis committed'
    $nonIntervalCounters=[ordered]@{attempt_count=1;audit_count=0;total_round_count=1;attempts_since_last_audit=1;audit_due=$false};$nonIntervalHash=Get-FileHashLower (Join-Path $nonIntervalProject 'project.json');$nonIntervalStart=New-Candidate -Project $nonIntervalProject -Generation 2 -PreservedHostBinding $nonIntervalGenesis.HostBinding -CountersOverride $nonIntervalCounters -EventTypeOverride ATTEMPT_START -RunStatus attempt_running -DerivedTicket -TicketStatus active
    $r=Invoke-Commit $nonIntervalProject $nonIntervalStart.Path $nonIntervalHash '1' 2;Assert-True ([bool]$r.Json.committed) 'non-interval attempt starts with a reserved terminal-audit round'
    $nonIntervalHash=Get-FileHashLower (Join-Path $nonIntervalProject 'project.json');$nonIntervalEnd=New-Candidate -Project $nonIntervalProject -Generation 3 -PreservedHostBinding $nonIntervalGenesis.HostBinding -CountersOverride $nonIntervalCounters -EventTypeOverride ATTEMPT_END -RunStatus completion_candidate -DerivedTicket -TicketStatus awaiting_verification;Set-DerivedVerifierTicket -Project $nonIntervalProject -CandidatePath $nonIntervalEnd.Path;$nonIntervalOutcome=Set-AttemptOutcomeFixture -Project $nonIntervalProject -CandidatePath $nonIntervalEnd.Path -Outcome candidate_found
    $r=Invoke-Commit $nonIntervalProject $nonIntervalEnd.Path $nonIntervalHash '2' 3;Assert-True ([bool]$r.Json.committed) 'non-interval ATTEMPT_END preserves its verifier-locked candidate';Assert-Equal (Invoke-Startup $nonIntervalProject).startup_class 'goal_host_audit_due' 'non-interval candidate routes to terminal audit even with audit_due false'
    $nonIntervalHash=Get-FileHashLower (Join-Path $nonIntervalProject 'project.json');$nonIntervalAuditCounters=[ordered]@{attempt_count=1;audit_count=1;total_round_count=2;attempts_since_last_audit=1;audit_due=$false};$nonIntervalAudit=New-Candidate -Project $nonIntervalProject -Generation 4 -PreservedHostBinding $nonIntervalGenesis.HostBinding -CountersOverride $nonIntervalAuditCounters -EventTypeOverride AUDIT_START -RunStatus auditing -DerivedTicket -TicketStatus active;$null=Set-CycleAuditStartFixture -Project $nonIntervalProject -CandidatePath $nonIntervalAudit.Path -AuditKind terminal -CandidatePointer $nonIntervalOutcome.Candidate
    $r=Invoke-Commit $nonIntervalProject $nonIntervalAudit.Path $nonIntervalHash '3' 4;Assert-True ([bool]$r.Json.committed) 'reserved terminal audit starts after a non-interval candidate'
    $nonIntervalHash=Get-FileHashLower (Join-Path $nonIntervalProject 'project.json');$nonIntervalSummary=New-CycleAuditEvidence -Project $nonIntervalProject -AuditKind terminal -EndGeneration 5;$nonIntervalAfterAudit=[ordered]@{attempt_count=1;audit_count=1;total_round_count=2;attempts_since_last_audit=0;audit_due=$false};$nonIntervalAuditEnd=New-Candidate -Project $nonIntervalProject -Generation 5 -PreservedHostBinding $nonIntervalGenesis.HostBinding -CountersOverride $nonIntervalAfterAudit -EventTypeOverride AUDIT_END -RunStatus completion_candidate -NoTicket -ReferencedArtifacts @($nonIntervalSummary)
    $r=Invoke-Commit $nonIntervalProject $nonIntervalAuditEnd.Path $nonIntervalHash '4' 5;Assert-True ([bool]$r.Json.committed) 'non-interval candidate terminal audit closes with three PASS reports';Assert-Equal (Invoke-Startup $nonIntervalProject).startup_class 'goal_host_completion_ready_to_publish' 'audited non-interval candidate exposes completion publication'
    $nonIntervalHash=Get-FileHashLower (Join-Path $nonIntervalProject 'project.json');$nonIntervalComplete=New-Candidate -Project $nonIntervalProject -Generation 6 -PreservedHostBinding $nonIntervalGenesis.HostBinding -CountersOverride $nonIntervalAfterAudit -EventTypeOverride COMPLETION_READY -RunStatus closed -CompletionReady -ReferencedArtifacts @($nonIntervalSummary)
    $r=Invoke-Commit $nonIntervalProject $nonIntervalComplete.Path $nonIntervalHash '5' 6;Assert-True ([bool]$r.Json.committed) 'non-interval candidate completes after its reserved terminal audit';Assert-Equal (Invoke-Startup $nonIntervalProject).startup_class 'goal_host_completion_pending' 'non-interval completion head is permanently read-only'

    # A candidate found on the final interval-hitting attempt remains live through its mandatory terminal audit.
    $project=$completionFx.Project;$completionBinding=$completionHost;$headHash=Get-FileHashLower (Join-Path $project 'project.json')
    $attempt3=[ordered]@{attempt_count=3;audit_count=1;total_round_count=4;attempts_since_last_audit=1;audit_due=$false}
    $start3=New-Candidate -Project $project -Generation 10 -PreservedHostBinding $completionBinding -CountersOverride $attempt3 -EventTypeOverride ATTEMPT_START -RunStatus attempt_running -DerivedTicket -TicketStatus active
    $r=Invoke-Commit $project $start3.Path $headHash '9' 10;Assert-True ([bool]$r.Json.committed) 'completion liveness chain starts attempt three'
    $headHash=Get-FileHashLower (Join-Path $project 'project.json');$end3=New-Candidate -Project $project -Generation 11 -PreservedHostBinding $completionBinding -CountersOverride $attempt3 -EventTypeOverride ATTEMPT_END -RunStatus preparing;$null=Set-AttemptOutcomeFixture -Project $project -CandidatePath $end3.Path -Outcome no_candidate
    $r=Invoke-Commit $project $end3.Path $headHash '10' 11;Assert-True ([bool]$r.Json.committed) 'attempt three closes without a candidate'
    $headHash=Get-FileHashLower (Join-Path $project 'project.json');$attempt4=[ordered]@{attempt_count=4;audit_count=1;total_round_count=5;attempts_since_last_audit=2;audit_due=$true};$start4=New-Candidate -Project $project -Generation 12 -PreservedHostBinding $completionBinding -CountersOverride $attempt4 -EventTypeOverride ATTEMPT_START -RunStatus attempt_running -DerivedTicket -TicketStatus active
    $r=Invoke-Commit $project $start4.Path $headHash '11' 12;Assert-True ([bool]$r.Json.committed) 'attempt four hits the next audit interval'
    $headHash=Get-FileHashLower (Join-Path $project 'project.json');$end4=New-Candidate -Project $project -Generation 13 -PreservedHostBinding $completionBinding -CountersOverride $attempt4 -EventTypeOverride ATTEMPT_END -RunStatus audit_due -DerivedTicket -TicketStatus ready;$null=Set-AttemptOutcomeFixture -Project $project -CandidatePath $end4.Path -Outcome no_candidate
    $r=Invoke-Commit $project $end4.Path $headHash '12' 13;Assert-True ([bool]$r.Json.committed) 'attempt four enters its scheduled audit gate'
    $headHash=Get-FileHashLower (Join-Path $project 'project.json');$audit2=[ordered]@{attempt_count=4;audit_count=2;total_round_count=6;attempts_since_last_audit=2;audit_due=$true};$audit2Start=New-Candidate -Project $project -Generation 14 -PreservedHostBinding $completionBinding -CountersOverride $audit2 -EventTypeOverride AUDIT_START -RunStatus auditing -DerivedTicket -TicketStatus active;$null=Set-CycleAuditStartFixture -Project $project -CandidatePath $audit2Start.Path -AuditKind scheduled
    $r=Invoke-Commit $project $audit2Start.Path $headHash '13' 14;Assert-True ([bool]$r.Json.committed) 'second scheduled audit starts'
    $headHash=Get-FileHashLower (Join-Path $project 'project.json');$audit2Summary=New-CycleAuditEvidence -Project $project -AuditKind scheduled -EndGeneration 15;$afterAudit2=[ordered]@{attempt_count=4;audit_count=2;total_round_count=6;attempts_since_last_audit=0;audit_due=$false};$audit2End=New-Candidate -Project $project -Generation 15 -PreservedHostBinding $completionBinding -CountersOverride $afterAudit2 -EventTypeOverride AUDIT_END -RunStatus preparing -DerivedTicket -TicketStatus ready -ReferencedArtifacts @($audit2Summary)
    $r=Invoke-Commit $project $audit2End.Path $headHash '14' 15;Assert-True ([bool]$r.Json.committed) 'second scheduled audit closes and resets the gate'
    $headHash=Get-FileHashLower (Join-Path $project 'project.json');$attempt5=[ordered]@{attempt_count=5;audit_count=2;total_round_count=7;attempts_since_last_audit=1;audit_due=$false};$start5=New-Candidate -Project $project -Generation 16 -PreservedHostBinding $completionBinding -CountersOverride $attempt5 -EventTypeOverride ATTEMPT_START -RunStatus attempt_running -DerivedTicket -TicketStatus active
    $r=Invoke-Commit $project $start5.Path $headHash '15' 16;Assert-True ([bool]$r.Json.committed) 'penultimate attempt starts'
    $headHash=Get-FileHashLower (Join-Path $project 'project.json');$end5=New-Candidate -Project $project -Generation 17 -PreservedHostBinding $completionBinding -CountersOverride $attempt5 -EventTypeOverride ATTEMPT_END -RunStatus preparing;$null=Set-AttemptOutcomeFixture -Project $project -CandidatePath $end5.Path -Outcome no_candidate
    $r=Invoke-Commit $project $end5.Path $headHash '16' 17;Assert-True ([bool]$r.Json.committed) 'penultimate attempt closes without a candidate'
    $headHash=Get-FileHashLower (Join-Path $project 'project.json');$finalAttempt=[ordered]@{attempt_count=6;audit_count=2;total_round_count=8;attempts_since_last_audit=2;audit_due=$true};$finalStart=New-Candidate -Project $project -Generation 18 -PreservedHostBinding $completionBinding -CountersOverride $finalAttempt -EventTypeOverride ATTEMPT_START -RunStatus attempt_running -DerivedTicket -TicketStatus active
    $r=Invoke-Commit $project $finalStart.Path $headHash '17' 18;Assert-True ([bool]$r.Json.committed) 'final permitted attempt starts and reserves its mandatory audit round'
    $headHash=Get-FileHashLower (Join-Path $project 'project.json')
    $missingOutcome=New-Candidate -Project $project -Generation 19 -PreservedHostBinding $completionBinding -CountersOverride $finalAttempt -EventTypeOverride ATTEMPT_END -RunStatus completion_candidate -DerivedTicket -TicketStatus awaiting_verification;Set-DerivedVerifierTicket -Project $project -CandidatePath $missingOutcome.Path;$null=Set-AttemptOutcomeFixture -Project $project -CandidatePath $missingOutcome.Path -Outcome candidate_found -Mode missing
    $r=Invoke-Commit $project $missingOutcome.Path $headHash '18' 19;Assert-Equal $r.Json.reason 'attempt_outcome_invalid' 'candidate_found ATTEMPT_END cannot omit its exact outcome'
    $falseCandidate=New-Candidate -Project $project -Generation 19 -PreservedHostBinding $completionBinding -CountersOverride $finalAttempt -EventTypeOverride ATTEMPT_END -RunStatus completion_candidate -DerivedTicket -TicketStatus awaiting_verification;Set-DerivedVerifierTicket -Project $project -CandidatePath $falseCandidate.Path;$null=Set-AttemptOutcomeFixture -Project $project -CandidatePath $falseCandidate.Path -Outcome candidate_found -Mode false_candidate
    $r=Invoke-Commit $project $falseCandidate.Path $headHash '18' 19;Assert-Equal $r.Json.reason 'attempt_outcome_invalid' 'attempt outcome candidate must equal the verifier ticket and PASS result candidate'
    $failedVerification=New-Candidate -Project $project -Generation 19 -PreservedHostBinding $completionBinding -CountersOverride $finalAttempt -EventTypeOverride ATTEMPT_END -RunStatus completion_candidate -DerivedTicket -TicketStatus awaiting_verification;Set-DerivedVerifierTicket -Project $project -CandidatePath $failedVerification.Path;$null=Set-AttemptOutcomeFixture -Project $project -CandidatePath $failedVerification.Path -Outcome candidate_found -Mode verifier_fail
    $r=Invoke-Commit $project $failedVerification.Path $headHash '18' 19;Assert-Equal $r.Json.reason 'attempt_outcome_invalid' 'candidate_found requires an exact verifier PASS'
    $solverCandidate=New-Candidate -Project $project -Generation 19 -PreservedHostBinding $completionBinding -CountersOverride $finalAttempt -EventTypeOverride ATTEMPT_END -RunStatus completion_candidate -DerivedTicket -TicketStatus awaiting_verification;$null=Set-AttemptOutcomeFixture -Project $project -CandidatePath $solverCandidate.Path -Outcome candidate_found
    $r=Invoke-Commit $project $solverCandidate.Path $headHash '18' 19;Assert-Equal $r.Json.reason 'attempt_outcome_invalid' 'solver ticket cannot directly publish a completion candidate'
    $candidateEnd=New-Candidate -Project $project -Generation 19 -PreservedHostBinding $completionBinding -CountersOverride $finalAttempt -EventTypeOverride ATTEMPT_END -RunStatus completion_candidate -DerivedTicket -TicketStatus awaiting_verification;Set-DerivedVerifierTicket -Project $project -CandidatePath $candidateEnd.Path;$lockedOutcome=Set-AttemptOutcomeFixture -Project $project -CandidatePath $candidateEnd.Path -Outcome candidate_found
    $r=Invoke-Commit $project $candidateEnd.Path $headHash '18' 19;Assert-True ([bool]$r.Json.committed) 'final interval-hitting ATTEMPT_END publishes a verifier-locked candidate despite audit_due';Assert-Equal (Invoke-Startup $project).startup_class 'goal_host_audit_due' 'unaudited final candidate routes only to terminal audit'
    $headHash=Get-FileHashLower (Join-Path $project 'project.json');$completionAuditCounters=[ordered]@{attempt_count=6;audit_count=3;total_round_count=9;attempts_since_last_audit=2;audit_due=$true};$completionAudit=New-Candidate -Project $project -Generation 20 -PreservedHostBinding $completionBinding -CountersOverride $completionAuditCounters -EventTypeOverride AUDIT_START -RunStatus auditing -DerivedTicket -TicketStatus active
    $null=Set-CycleAuditStartFixture -Project $project -CandidatePath $completionAudit.Path -AuditKind terminal -CandidatePointer $lockedOutcome.Candidate
    $r=Invoke-Commit $project $completionAudit.Path $headHash '19' 20;Assert-True ([bool]$r.Json.committed) 'final candidate enters its reserved terminal audit';Assert-Equal (Invoke-Startup $project).startup_class 'goal_host_audit_due' 'terminal audit remains startup-readable even when the prior attempt set audit_due'
    $headHash=Get-FileHashLower (Join-Path $project 'project.json');$terminalSummary=New-CycleAuditEvidence -Project $project -AuditKind terminal -EndGeneration 21;$terminalEvidence=@($terminalSummary);$afterTerminal=[ordered]@{attempt_count=6;audit_count=3;total_round_count=9;attempts_since_last_audit=0;audit_due=$false}
    $missingTerminal=New-Candidate -Project $project -Generation 21 -PreservedHostBinding $completionBinding -CountersOverride $afterTerminal -EventTypeOverride AUDIT_END -RunStatus completion_candidate -NoTicket
    $r=Invoke-Commit $project $missingTerminal.Path $headHash '20' 21;Assert-Equal $r.Json.reason 'cycle_audit_invalid' 'terminal AUDIT_END cannot omit its exact summary'
    $failedTerminalSummary=New-CycleAuditEvidence -Project $project -AuditKind terminal -EndGeneration 21 -Verdicts @('FAIL','PASS','PASS');$failedTerminal=New-Candidate -Project $project -Generation 21 -PreservedHostBinding $completionBinding -CountersOverride $afterTerminal -EventTypeOverride AUDIT_END -RunStatus completion_candidate -NoTicket -ReferencedArtifacts @($failedTerminalSummary)
    $r=Invoke-Commit $project $failedTerminal.Path $headHash '20' 21;Assert-Equal $r.Json.reason 'cycle_audit_invalid' 'terminal FAIL cannot preserve completion_candidate'
    $terminalSummary=New-CycleAuditEvidence -Project $project -AuditKind terminal -EndGeneration 21;$terminalEvidence=@($terminalSummary);$completionAuditEnd=New-Candidate -Project $project -Generation 21 -PreservedHostBinding $completionBinding -CountersOverride $afterTerminal -EventTypeOverride AUDIT_END -RunStatus completion_candidate -NoTicket -ReferencedArtifacts $terminalEvidence
    $r=Invoke-Commit $project $completionAuditEnd.Path $headHash '20' 21;Assert-True ([bool]$r.Json.committed) 'terminal AUDIT_END returns to completion_candidate with the same locked candidate and three PASS reports';Assert-Equal (Invoke-Startup $project).startup_class 'goal_host_completion_ready_to_publish' 'terminal AUDIT_END certificate exposes only completion publication'
    $headHash=Get-FileHashLower (Join-Path $project 'project.json');$complete=New-Candidate -Project $project -Generation 22 -PreservedHostBinding $completionBinding -CountersOverride $afterTerminal -EventTypeOverride COMPLETION_READY -RunStatus closed -CompletionReady -ReferencedArtifacts $terminalEvidence
    $r=Invoke-Commit $project $complete.Path $headHash '21' 22;Assert-True ([bool]$r.Json.committed) "COMPLETION_READY durable close committed ($($r.Json.reason): $($r.Json.detail))";$completionPlan=Invoke-Startup $project;Assert-Equal $completionPlan.startup_class 'goal_host_completion_pending' 'completed helper head never resumes research'
    $completedHash=Get-FileHashLower (Join-Path $project 'project.json');$afterComplete=New-Candidate -Project $project -Generation 23 -PreservedHostBinding $completionBinding -CountersOverride $afterTerminal -EventTypeOverride CHECKPOINT_COMMIT -RunStatus closed -CompletionReady -ReferencedArtifacts $terminalEvidence
    $r=Invoke-Commit $project $afterComplete.Path $completedHash '22' 23;Assert-True (-not[bool]$r.Json.committed) 'completion-ready head is immutable'

    # Immutable lineage pointer survives later generations; any drift fails.
    $legacy=New-LegacyTransitionFixture $temp
    $r=Invoke-Commit $legacy.Project $legacy.Candidate.Path $legacy.OldHash '0' 1; Assert-True ([bool]$r.Json.committed) 'lineage fixture activated'
    $oldHash=Get-FileHashLower (Join-Path $legacy.Project 'project.json')
    $g2=New-Candidate -Project $legacy.Project -Generation 2 -PreservedHostBinding $legacy.Candidate.HostBinding -LegacyPointer $legacy.LineagePointer -SuccessorSummary $legacy.Summary -RunOrigin legacy_successor -BaselineSha256 $legacy.BaselineHash
    $r=Invoke-Commit $legacy.Project $g2.Path $oldHash '1' 2; Assert-True ([bool]$r.Json.committed) "g1 lineage pointer preserved into g2 ($($r.Json.reason): $($r.Json.detail))"
    $oldHash=Get-FileHashLower (Join-Path $legacy.Project 'project.json')
    $g3=New-Candidate -Project $legacy.Project -Generation 3 -PreservedHostBinding $legacy.Candidate.HostBinding -LegacyPointer $legacy.LineagePointer -SuccessorSummary $legacy.Summary -RunOrigin legacy_successor -BaselineSha256 $legacy.BaselineHash
    $r=Invoke-Commit $legacy.Project $g3.Path $oldHash '2' 3; Assert-True ([bool]$r.Json.committed) 'g2 lineage pointer preserved into g3'
    $oldHash=Get-FileHashLower (Join-Path $legacy.Project 'project.json')
    $g4=New-Candidate -Project $legacy.Project -Generation 4 -PreservedHostBinding $legacy.Candidate.HostBinding -LegacyPointer $legacy.LineagePointer -SuccessorSummary $legacy.Summary -RunOrigin legacy_successor -BaselineSha256 $legacy.BaselineHash
    $h=Read-Json $g4.Path; $h.legacy_successor.sha256='0'*64; Write-Json $g4.Path $h
    $r=Invoke-Commit $legacy.Project $g4.Path $oldHash '3' 4; Assert-Equal $r.Json.reason 'lineage_drift' 'lineage pointer drift rejected'

    # Two identical expected-old commits serialize; exactly one wins.
    $project=New-Project $temp; $c=New-Candidate $project 1
    $p1=Start-CommitProcess $project $c.Path 'absent' '0' 1; $p2=Start-CommitProcess $project $c.Path 'absent' '0' 1
    $rr=@((Wait-CommitProcess $p1),(Wait-CommitProcess $p2))
    Assert-Equal @($rr | Where-Object {$_.Json.committed}).Count 1 'concurrent CAS has one winner'
    Assert-Equal @($rr | Where-Object {-not $_.Json.committed}).Count 1 'concurrent CAS has one stale loser'
    Assert-Equal @($rr | Where-Object {-not $_.Json.committed})[0].Json.reason 'stale_hash' 'concurrent loser reports stale head'

    # An OS-level replacement failure leaves the old head byte-identical.
    $fx=New-V8TransitionFixture $temp; $headPath=Join-Path $fx.Project 'project.json'; $before=Get-FileHashLower $headPath
    $hold=[IO.File]::Open($headPath,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    try { $r=Invoke-Commit $fx.Project $fx.Candidate.Path $fx.OldHash '1' 2 } finally { $hold.Dispose() }
    Assert-True (-not [bool]$r.Json.committed) 'replacement failure is closed'; Assert-Equal (Get-FileHashLower $headPath) $before 'replacement failure preserves exact old head'

    # Post-move verification failure is indeterminate and never races a non-cooperating writer with rollback.
    $instrumentedHelper=Join-Path $temp 'instrumented-postverify-helper.ps1';$helperText=[IO.File]::ReadAllText($script:helper,[Text.UTF8Encoding]::new($false,$true));$needle='# Post-move verification begins here; production behavior has no test hook.'
    Assert-Equal ([regex]::Matches($helperText,[regex]::Escape($needle))).Count 1 'instrumentation anchor is unique';Write-Utf8 $instrumentedHelper ($helperText.Replace($needle,"throw 'instrumented post-move verification failure'"))
    $fx=New-V8TransitionFixture $temp;$r=Invoke-Commit $fx.Project $fx.Candidate.Path $fx.OldHash '1' 2 -HelperPath $instrumentedHelper
    Assert-Equal $r.Json.reason 'post_commit_state_indeterminate' 'postverify failure reports indeterminate without rollback'
    Assert-Equal (Get-FileHashLower (Join-Path $fx.Project 'project.json')) (Get-FileHashLower $fx.Candidate.Path) 'postverify failure does not overwrite moved or concurrent bytes'
    Assert-Equal @(Get-ChildItem -LiteralPath $fx.Project -Filter 'head-commit-recovery-*.json' -File).Count 1 'postverify failure emits one project-root recovery artifact'
    Assert-True (-not $helperText.Contains('MATH_RESEARCH_HEAD_V8_TEST_')) 'production helper has no ambient fault-injection hook'
    Assert-Equal @(Get-ChildItem -LiteralPath $temp -Recurse -Force -File | Where-Object {$_.Name -like '.project.json.*.tmp' -or $_.Name -like '.project.json.rollback.*'}).Count 0 'no head temp/rollback residue remains'

    # Both production and test files parse as PowerShell ASTs.
    foreach ($path in @($script:helper,$script:startup,$PSCommandPath)) {
        $tokens=$null;$errors=$null;[Management.Automation.Language.Parser]::ParseFile($path,[ref]$tokens,[ref]$errors)|Out-Null
        Assert-Equal @($errors).Count 0 "AST parses: $path"
    }

    [ordered]@{schema='math-research-head-commit-tests/v8';status='passed';assertions=$script:assertions;helper_sha256=Get-FileHashLower $script:helper;test_sha256=Get-FileHashLower $PSCommandPath} | ConvertTo-Json -Compress
}
finally {
    if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
}
