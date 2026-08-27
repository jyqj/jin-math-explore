[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ProjectDirectory,
    [Parameter(Mandatory = $true)][string]$CandidateHeadFile,
    [Parameter(Mandatory = $true)][string]$ExpectedOldSha256,
    [Parameter(Mandatory = $true)][string]$ExpectedOldControlGeneration,
    [Parameter(Mandatory = $true)][long]$ExpectedNewControlGeneration
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)

$result = [ordered]@{
    schema = 'math-research-head-commit-result/v8'
    committed = $false
    reason = 'unclassified_failure'
    detail = $null
    project_json = $null
    old_sha256 = $null
    candidate_sha256 = $null
    new_sha256 = $null
    old_control_generation = $null
    new_control_generation = $null
    trust = 'local_atomic_project_head_cas_not_goal_authorization'
}

function Stop-Commit {
    param([Parameter(Mandatory = $true)][string]$Code, [Parameter(Mandatory = $true)][string]$Message)
    throw "[$Code] $Message"
}

function Get-BytesSha256 {
    param([Parameter(Mandatory = $true)][byte[]]$Bytes)
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes)).ToLowerInvariant()
}

function Get-FileSha256 {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    return (Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-NormalizedTextSha256 {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    $text = [IO.File]::ReadAllText($LiteralPath, [Text.UTF8Encoding]::new($false, $true)) -replace "`r`n", "`n"
    if ($text.Contains("`r")) { Stop-Commit 'contract_invalid' "Contract contains an isolated CR: $LiteralPath" }
    return Get-BytesSha256 ([Text.UTF8Encoding]::new($false).GetBytes($text))
}

function Test-ResolvedContractString {
    param($Value)
    return $Value -is [string] -and -not [string]::IsNullOrWhiteSpace([string]$Value) -and ([string]$Value).Length -le 4096 -and [string]$Value -notmatch '[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]' -and [string]$Value -notmatch '(?i)(replace[_ -]?with|placeholder|requires user decision|\[[^\]]*\]|^unknown$|64 lowercase hex)'
}

function Test-ContractRelativePathSyntax {
    param($Value,[switch]$AllowLeaf)
    if (-not (Test-ResolvedContractString $Value) -or [IO.Path]::IsPathRooted([string]$Value) -or ([string]$Value).Contains(':') -or ([string]$Value).Contains('\')) { return $false }
    $segments=@(([string]$Value)-split '/')
    return ($AllowLeaf -or $segments.Count -ge 2) -and @($segments|Where-Object{[string]::IsNullOrEmpty([string]$_)-or[string]$_-cin @('.','..')}).Count -eq 0
}

function Test-AllowedWorkerToolName {
    param($Value)
    return $Value-is[string]-and[string]$Value-cin@('apply_patch','collaboration.spawn_agent','collaboration.send_message','collaboration.wait_agent','shell_command','web__run')
}

function Get-ContractBudgetMetadata {
    param(
        [Parameter(Mandatory = $true)][string]$ContractPath,
        [Parameter(Mandatory = $true)][string]$ProjectPath,
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Candidate
    )
    $text = [IO.File]::ReadAllText($ContractPath,[Text.UTF8Encoding]::new($false,$true)) -replace "`r`n","`n"
    if($text.Contains("`r") -or [regex]::Matches($text,'(?m)^# Math Research Goal-Host Contract v8$').Count-ne1){Stop-Commit 'contract_invalid' 'Contract is not one canonical normalized v8 Goal-host envelope.'}
    $metadataMatch=[regex]::Match($text,'\A# Math Research Goal-Host Contract v8\n<!-- math-research-goal-host\n(?<body>.*?)\n-->\n',[Text.RegularExpressions.RegexOptions]::Singleline)
    if(-not$metadataMatch.Success){Stop-Commit 'contract_invalid' 'Contract metadata must immediately follow the v8 H1.'}
    $allowed=@('schema','goal_host_protocol','goal_binding_policy','goal_rebind_policy','contract_version','project_archive_schema','project_id','project_directory_name','project_identity_sha256','model','reasoning_effort','approval_mode','web_search','audit_interval_attempts','attempt_budget','total_round_budget','max_child_agents','max_total_agents','max_runtime_minutes','run_origin','inherited_counter_budget_baseline_sha256','problem_statement_sha256','cycle_policy_sha256','initial_tickets_sha256')
    $metadata=[ordered]@{}
    foreach($line in ($metadataMatch.Groups['body'].Value-split "`n")){
        if($line-cnotmatch'^(?<key>[a-z][a-z0-9_]*):\s*(?<value>\S(?:.*\S)?)$'){Stop-Commit 'contract_invalid' 'Contract contains a malformed metadata line.'}
        $key=$Matches.key;if($key-cnotin$allowed-or$metadata.Contains($key)){Stop-Commit 'contract_invalid' 'Contract metadata has an unknown or duplicate key.'};$metadata[$key]=$Matches.value
    }
    if($metadata.Count-ne$allowed.Count-or@($allowed|Where-Object{-not$metadata.Contains($_)}).Count-ne0){Stop-Commit 'contract_invalid' 'Contract metadata does not have the exact v8 key set.'}
    if([string]$metadata.schema-cne'8'-or[string]$metadata.goal_host_protocol-cne'direct-current-task/v8'-or[string]$metadata.goal_binding_policy-cne'direct-current-task/v8'-or[string]$metadata.goal_rebind_policy-cne'external-host-bind-chain/v8'-or[string]$metadata.project_archive_schema-cne'math-research-project/v8'-or
        [string]$metadata.contract_version-cne[string]$Candidate.active_contract.version-or[string]$metadata.project_id-cne[string]$Candidate.project_id-or[string]$metadata.project_directory_name-cne(Split-Path -Leaf $ProjectPath)-or[string]$metadata.project_identity_sha256-cne[string]$Candidate.project_identity_sha256-or[string]$metadata.problem_statement_sha256-cne[string]$Candidate.problem_statement_sha256){Stop-Commit 'contract_invalid' 'Contract protocol or project identity binding mismatches the candidate head.'}
    foreach($shaName in @('project_identity_sha256','problem_statement_sha256','cycle_policy_sha256','initial_tickets_sha256')){Assert-LowerSha256 $metadata[$shaName] "Contract $shaName"}
    if([string]$metadata.model-cnotmatch'^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$'-or[string]$metadata.reasoning_effort-cnotin@('minimal','low','medium','high','xhigh','max','ultra')-or[string]$metadata.approval_mode-cnotin@('approve_for_me','never')-or[string]$metadata.web_search-cnotin@('allowed','denied')){Stop-Commit 'contract_invalid' 'Contract model/reasoning/approval/web policy is invalid.'}
    $values=[ordered]@{}
    foreach($name in @('attempt_budget','total_round_budget','audit_interval_attempts','max_child_agents','max_total_agents','max_runtime_minutes')){$parsed=0L;if([string]$metadata[$name]-cnotmatch'^(0|[1-9][0-9]*)$'-or-not[long]::TryParse([string]$metadata[$name],[ref]$parsed)){Stop-Commit 'contract_invalid' "Contract $name is not a safely parseable integer."};$values[$name]=$parsed}
    if($values.attempt_budget-lt1-or$values.total_round_budget-lt1-or$values.audit_interval_attempts-lt1-or$values.max_child_agents-lt1-or$values.max_child_agents-gt16-or$values.max_total_agents-ne($values.max_child_agents+1)-or$values.total_round_budget-lt($values.attempt_budget+[Math]::Ceiling($values.attempt_budget/[double]$values.audit_interval_attempts))){Stop-Commit 'contract_invalid' 'Contract resource ceilings cannot accommodate the mandatory audit schedule.'}
    if([string]$metadata.run_origin-cnotin@('fresh','legacy_successor')-or([string]$metadata.run_origin-ceq'fresh'-and[string]$metadata.inherited_counter_budget_baseline_sha256-cne'null')){Stop-Commit 'contract_invalid' 'Contract run origin/baseline binding is invalid.'}
    if([string]$metadata.run_origin-ceq'legacy_successor'){Assert-LowerSha256 $metadata.inherited_counter_budget_baseline_sha256 'Contract inherited baseline hash'}
    $values.run_origin=[string]$metadata.run_origin;$values.inherited_counter_budget_baseline_sha256=[string]$metadata.inherited_counter_budget_baseline_sha256;$values.web_search=[string]$metadata.web_search
    $blocks=[ordered]@{}
    foreach($name in @('math-research-cycle-policy','math-research-initial-tickets')){
        $matches=[regex]::Matches($text,"<!-- $([regex]::Escape($name))\n(?<body>.*?)\n-->",[Text.RegularExpressions.RegexOptions]::Singleline)
        if($matches.Count-ne1){Stop-Commit 'contract_invalid' "Contract must contain exactly one $name block."};$body=$matches[0].Groups['body'].Value
        $bodyHash=Get-BytesSha256 ([Text.UTF8Encoding]::new($false).GetBytes($body));$expected=if($name-ceq'math-research-cycle-policy'){$metadata.cycle_policy_sha256}else{$metadata.initial_tickets_sha256};if($bodyHash-cne[string]$expected){Stop-Commit 'contract_invalid' "$name exact-body hash mismatches metadata."}
        $blocks[$name]=ConvertFrom-StrictJsonBytes -Bytes ([Text.UTF8Encoding]::new($false).GetBytes($body)) -Label "Contract $name"
    }
    $policy=$blocks['math-research-cycle-policy'];Assert-RequiredKeys $policy @('schema_version','protocol','total_round_budget','attempt_budget','audit_interval_attempts','max_route_family_attempts_per_cycle','max_repair_batches_per_attempt','allowed_worker_tools','max_ticket_tool_calls','max_ticket_output_bytes','audit_roles') 'Contract cycle policy' -Exact
    if([string]$policy.schema_version-cne'3'-or[string]$policy.protocol-cne'math-research-cycle-policy/v3'-or[string]$policy.total_round_budget-cne[string]$values.total_round_budget-or[string]$policy.attempt_budget-cne[string]$values.attempt_budget-or[string]$policy.audit_interval_attempts-cne[string]$values.audit_interval_attempts-or-not(Test-JsonInteger $policy.max_ticket_tool_calls 1)-or-not(Test-JsonInteger $policy.max_ticket_output_bytes 1)-or(@($policy.audit_roles)-join'|')-cne'skeptic_quantifiers|skeptic_strategy|theory_tool_scout'){Stop-Commit 'contract_invalid' 'Contract cycle policy mismatches metadata, resource caps, or the mandatory audit roles.'}
    if($policy.allowed_worker_tools-isnot[Collections.IList]-or@($policy.allowed_worker_tools).Count-lt1){Stop-Commit 'contract_invalid' 'Contract allowed_worker_tools must be a nonempty closed array.'}
    $toolSet=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($tool in @($policy.allowed_worker_tools)){if(-not(Test-AllowedWorkerToolName $tool)-or-not$toolSet.Add([string]$tool)){Stop-Commit 'contract_invalid' 'Contract allowed_worker_tools contains a forbidden, unresolved, or duplicate name.'}}
    if([string]$metadata.web_search-ceq'denied'-and'web__run'-cin@($policy.allowed_worker_tools)){Stop-Commit 'contract_invalid' 'A network-denied Contract cannot authorize web__run.'}
    $values.allowed_worker_tools=@($policy.allowed_worker_tools);$values.max_ticket_tool_calls=[long]$policy.max_ticket_tool_calls;$values.max_ticket_output_bytes=[long]$policy.max_ticket_output_bytes
    $values.project_id=[string]$Candidate.project_id;$values.contract_pointer=$Candidate.active_contract;$values.run_pointer=$Candidate.active_run
    $tickets=$blocks['math-research-initial-tickets'];Assert-RequiredKeys $tickets @('schema_version','cycle_id','tickets') 'Contract initial tickets' -Exact
    if([string]$tickets.schema_version-cne'3'-or-not(Test-ResolvedContractString $tickets.cycle_id)-or$tickets.tickets-isnot[Collections.IList]-or@($tickets.tickets).Count-lt1){Stop-Commit 'contract_invalid' 'Contract initial-ticket block is invalid.'}
    $values.metadata=$metadata;$values.cycle_id=[string]$tickets.cycle_id;$values.initial_tickets=@($tickets.tickets)
    $seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($ticket in @($values.initial_tickets)){Assert-TicketBody -Ticket $ticket -ContractFacts $values -ProjectPath $ProjectPath -ActiveRun $Candidate.active_run;if(-not$seen.Add([string]$ticket.ticket_id)){Stop-Commit 'contract_invalid' 'Contract initial ticket IDs are duplicated.'}}
    return $values
}

function Assert-TicketBody {
    param($Ticket,[Parameter(Mandatory=$true)]$ContractFacts,[Parameter(Mandatory=$true)][string]$ProjectPath,[Parameter(Mandatory=$true)]$ActiveRun)
    $keys=@('ticket_id','role','planned_lifecycle_slot','route_id','route_fingerprint_sha256','attempt_kind','route_family_id','mechanism_id','bottleneck_id','decision_question','input_artifacts','search_domain','success_signal','stop_signal','allowed_tools','source_network_policy','filesystem_scope','resource_caps','dependencies','evidence_grade_required','required_outputs','failure_return','reopen_condition')
    if([string]$Ticket.role-ceq'verifier'){$keys+=@('candidate_artifact')}
    Assert-RequiredKeys $Ticket $keys 'frozen ticket body' -Exact;Assert-SafeId $Ticket.ticket_id 'ticket ID'
    foreach($name in @('planned_lifecycle_slot','route_id','attempt_kind','route_family_id','mechanism_id','bottleneck_id','decision_question','search_domain','success_signal','stop_signal','evidence_grade_required','reopen_condition')){if(-not(Test-ResolvedContractString $Ticket[$name])){Stop-Commit 'ticket_invalid' "Ticket $name is unresolved."}}
    if([string]$Ticket.role-cnotin@('solver','verifier','skeptic_quantifiers','skeptic_strategy','theory_tool_scout')){Stop-Commit 'ticket_invalid' 'Ticket role is outside the closed set.'};Assert-LowerSha256 $Ticket.route_fingerprint_sha256 'ticket route fingerprint'
    if($Ticket.input_artifacts-isnot[Collections.IList]-or@($Ticket.input_artifacts).Count-lt1){Stop-Commit 'ticket_invalid' 'Ticket has no bound input artifact.'}
    foreach($artifact in @($Ticket.input_artifacts)){if(-not(Test-ContractRelativePathSyntax $artifact.path)){Stop-Commit 'ticket_invalid' 'Ticket input artifact path is unsafe.'};$null=Assert-RawPointer $artifact $ProjectPath 'ticket input artifact' '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf}
    if($Ticket.allowed_tools-isnot[Collections.IList]-or@($Ticket.allowed_tools).Count-lt1){Stop-Commit 'ticket_invalid' 'Ticket allowed_tools is empty.'}
    $ticketToolSet=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($tool in @($Ticket.allowed_tools)){if(-not(Test-AllowedWorkerToolName $tool)-or-not$ticketToolSet.Add([string]$tool)-or[string]$tool-cnotin@($ContractFacts.allowed_worker_tools)){Stop-Commit 'ticket_invalid' 'Ticket allowed_tools is not a unique subset of the Contract worker-tool allowlist.'}}
    if([string]$ContractFacts.web_search-ceq'denied'-and'web__run'-cin@($Ticket.allowed_tools)){Stop-Commit 'ticket_invalid' 'A network-denied ticket cannot authorize web__run.'}
    Assert-RequiredKeys $Ticket.source_network_policy @('web','allowed_source_classes','network_destinations') 'ticket source/network policy' -Exact
    if([string]$Ticket.source_network_policy.web-cne[string]$ContractFacts.web_search-or$Ticket.source_network_policy.allowed_source_classes-isnot[Collections.IList]-or@($Ticket.source_network_policy.allowed_source_classes).Count-lt1-or$Ticket.source_network_policy.network_destinations-isnot[Collections.IList]-or([string]$Ticket.source_network_policy.web-ceq'denied'-and@($Ticket.source_network_policy.network_destinations).Count-ne0)){Stop-Commit 'ticket_invalid' 'Ticket source/network policy expands or contradicts the Contract.'}
    Assert-RequiredKeys $Ticket.filesystem_scope @('read_paths','writable_staging_path') 'ticket filesystem scope' -Exact
    if($Ticket.filesystem_scope.read_paths-isnot[Collections.IList]-or@($Ticket.filesystem_scope.read_paths).Count-lt1-or@($Ticket.filesystem_scope.read_paths|Where-Object{-not(Test-ContractRelativePathSyntax $_)}).Count-ne0-or-not(Test-ContractRelativePathSyntax $Ticket.filesystem_scope.writable_staging_path)-or-not([string]$Ticket.filesystem_scope.writable_staging_path).StartsWith(([string]$ActiveRun.path+'/staging/'),[StringComparison]::OrdinalIgnoreCase)){Stop-Commit 'ticket_invalid' 'Ticket filesystem scope is not confined to the active run staging subtree.'}
    Assert-RequiredKeys $Ticket.resource_caps @('child_agents','tool_calls','runtime_minutes','max_output_bytes') 'ticket resource caps' -Exact
    foreach($name in @('child_agents','tool_calls','runtime_minutes','max_output_bytes')){if(-not(Test-JsonInteger $Ticket.resource_caps[$name] 0)){Stop-Commit 'ticket_invalid' 'Ticket resource caps must be nonnegative integers.'}}
    if([long]$Ticket.resource_caps.child_agents-gt[long]$ContractFacts.max_child_agents-or([long]$ContractFacts.max_runtime_minutes-gt0-and[long]$Ticket.resource_caps.runtime_minutes-gt[long]$ContractFacts.max_runtime_minutes)-or[long]$Ticket.resource_caps.tool_calls-gt[long]$ContractFacts.max_ticket_tool_calls-or[long]$Ticket.resource_caps.max_output_bytes-lt1-or[long]$Ticket.resource_caps.max_output_bytes-gt[long]$ContractFacts.max_ticket_output_bytes){Stop-Commit 'ticket_invalid' 'Ticket resource caps exceed the Contract cycle-policy caps.'}
    if($Ticket.dependencies-isnot[Collections.IList]){Stop-Commit 'ticket_invalid' 'Ticket dependencies must be an array.'}
    $resolvedDependencies=[Collections.Generic.List[object]]::new();$dependencyIds=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($dependency in @($Ticket.dependencies)){
        Assert-RequiredKeys $dependency @('ticket_id','path','sha256') 'ticket dependency' -Exact;Assert-SafeId $dependency.ticket_id 'ticket dependency ID'
        if(-not$dependencyIds.Add([string]$dependency.ticket_id)){Stop-Commit 'ticket_invalid' 'Ticket dependency IDs must be unique.'}
        $dependencyPath=Assert-RawPointer ([ordered]@{path=$dependency.path;sha256=$dependency.sha256}) $ProjectPath 'ticket dependency completion' '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf
        $resolvedDependencies.Add([pscustomobject]@{Binding=$dependency;Path=$dependencyPath})
    }
    if([string]$Ticket.role-ceq'verifier'){
        if(@($Ticket.dependencies).Count-lt1){Stop-Commit 'ticket_invalid' 'A verifier ticket must bind at least one completed dependency.'}
        $null=Assert-RawPointer $Ticket.candidate_artifact $ProjectPath 'verifier candidate artifact' '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf
        if(@($Ticket.input_artifacts|Where-Object{Test-JsonDeepEqual $_ $Ticket.candidate_artifact}).Count-ne1){Stop-Commit 'ticket_invalid' 'Verifier candidate_artifact must exactly equal one input_artifacts member.'}
        $completionCount=0
        foreach($resolved in $resolvedDependencies){
            $dependency=$resolved.Binding
            if([string]$dependency.ticket_id-ceq[string]$Ticket.ticket_id-or[string]$dependency.sha256-ceq[string]$Ticket.candidate_artifact.sha256){Stop-Commit 'ticket_invalid' 'Verifier dependency cannot self-reference the verifier ticket or masquerade as its candidate artifact.'}
            $completion=Read-StrictJsonObject $resolved.Path 'verifier ticket-completion dependency'
            if([string]$completion.schema-ceq'math-research-ticket-completion/v8'){
                Assert-RequiredKeys $completion @('schema','project_id','contract','run','ticket_id','role','status','output','candidate_artifact','completed_at_utc') 'verifier ticket-completion dependency' -Exact
                Assert-RequiredKeys $completion.contract @('path','version','binding_sha256') 'ticket-completion Contract' -Exact;Assert-RequiredKeys $completion.run @('id','path') 'ticket-completion run' -Exact
                $outputPath=Assert-RawPointer $completion.output $ProjectPath 'ticket-completion output' '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf
                $null=Assert-RawPointer $completion.candidate_artifact $ProjectPath 'ticket-completion candidate artifact' '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf
                $stagingPrefix=([string]$Ticket.filesystem_scope.writable_staging_path).TrimEnd('/')+'/'
                if([string]$completion.project_id-cne[string]$ContractFacts.project_id-or-not(Test-PointerEqual $completion.contract $ContractFacts.contract_pointer contract)-or[string]$completion.run.id-cne[string]$ActiveRun.id-or[string]$completion.run.path-cne[string]$ActiveRun.path-or[string]$completion.ticket_id-cne[string]$dependency.ticket_id-or[string]$completion.role-cne'solver'-or[string]$completion.status-cne'closed'-or-not(Test-PointerEqual $completion.candidate_artifact $Ticket.candidate_artifact raw)-or([string]$completion.output.path).StartsWith($stagingPrefix,[StringComparison]::OrdinalIgnoreCase)-or-not(Test-CurrentUtcTimestamp $completion.completed_at_utc)){Stop-Commit 'ticket_invalid' 'Verifier ticket-completion dependency is not a closed solver completion bound to the same candidate/Contract/run or publishes into verifier staging.'}
                $completionCount++
            }
        }
        if($completionCount-lt1){Stop-Commit 'ticket_invalid' 'Verifier requires at least one exact solver ticket-completion dependency.'}
    }
    if($Ticket.required_outputs-isnot[Collections.IList]-or@($Ticket.required_outputs).Count-lt1){Stop-Commit 'ticket_invalid' 'Ticket required_outputs is empty.'};foreach($output in @($Ticket.required_outputs)){Assert-RequiredKeys $output @('path','schema','sha256_on_return') 'ticket required output' -Exact;if(-not(Test-ContractRelativePathSyntax $output.path -AllowLeaf)-or-not(Test-ResolvedContractString $output.schema)-or[string]$output.sha256_on_return-cne'required'){Stop-Commit 'ticket_invalid' 'Ticket required output is invalid.'}}
    Assert-RequiredKeys $Ticket.failure_return @('schema','required_fields') 'ticket failure return' -Exact;$requiredFailure=@('status','failed_step','reason','partial_artifact_hashes','reopen_condition');if([string]$Ticket.failure_return.schema-cne'math-research-ticket-failure/v1'-or(@($Ticket.failure_return.required_fields)-join'|')-cne($requiredFailure-join'|')){Stop-Commit 'ticket_invalid' 'Ticket failure-return schema is invalid.'}
}

function Assert-VerifierPassResult {
    param($Record,[string]$ProjectPath,$Candidate,$ExpectedCandidate,[string]$ExpectedAttemptId)
    Assert-RequiredKeys $Record @('schema','project_id','contract','run','ticket_id','role','candidate_artifact','verdict','checked_at_utc') 'verifier PASS result' -Exact
    Assert-RequiredKeys $Record.contract @('path','version','binding_sha256') 'verifier PASS Contract' -Exact
    Assert-RequiredKeys $Record.run @('id','path') 'verifier PASS run' -Exact
    Assert-SafeId $Record.ticket_id 'verifier PASS ticket_id'
    $null=Assert-RawPointer $Record.candidate_artifact $ProjectPath 'verifier PASS candidate' '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf
    if([string]$Record.schema-cne'math-research-verifier-result/v8'-or[string]$Record.project_id-cne[string]$Candidate.project_id-or-not(Test-PointerEqual $Record.contract $Candidate.active_contract contract)-or[string]$Record.run.id-cne[string]$Candidate.active_run.id-or[string]$Record.run.path-cne[string]$Candidate.active_run.path-or[string]$Record.ticket_id-ceq$ExpectedAttemptId-or[string]$Record.role-cne'verifier'-or-not(Test-PointerEqual $Record.candidate_artifact $ExpectedCandidate raw)-or[string]$Record.verdict-cne'PASS'-or-not(Test-CurrentUtcTimestamp $Record.checked_at_utc)){Stop-Commit 'attempt_outcome_invalid' 'Verifier PASS result is not an independent exact PASS on the claimed candidate/Contract/run.'}
    return $Record
}

function Assert-AttemptOutcome {
    param($Pointer,[string]$ProjectPath,$Candidate)
    $path=Assert-RawPointer $Pointer $ProjectPath 'ATTEMPT_END outcome' '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf
    $outcome=Read-StrictJsonObject $path 'ATTEMPT_END outcome'
    Assert-RequiredKeys $outcome @('schema','project_id','contract','run','attempt_id','outcome','candidate','verifier_completion','completed_at_utc') 'ATTEMPT_END outcome' -Exact
    Assert-RequiredKeys $outcome.contract @('path','version','binding_sha256') 'ATTEMPT_END outcome Contract' -Exact
    Assert-RequiredKeys $outcome.run @('id','path') 'ATTEMPT_END outcome run' -Exact
    Assert-SafeId $outcome.attempt_id 'ATTEMPT_END attempt_id'
    $allowedOutcomes=@('candidate_found','no_candidate','inconclusive','failed','awaiting_input')
    if([string]$outcome.schema-cne'math-research-attempt-outcome/v8'-or[string]$outcome.project_id-cne[string]$Candidate.project_id-or-not(Test-PointerEqual $outcome.contract $Candidate.active_contract contract)-or[string]$outcome.run.id-cne[string]$Candidate.active_run.id-or[string]$outcome.run.path-cne[string]$Candidate.active_run.path-or[string]$outcome.outcome-cnotin$allowedOutcomes-or-not(Test-CurrentUtcTimestamp $outcome.completed_at_utc)){Stop-Commit 'attempt_outcome_invalid' 'ATTEMPT_END outcome identity, Contract, run, closed outcome, or timestamp is invalid.'}
    if([string]$outcome.outcome-cne'candidate_found'){
        if($null-ne$outcome.candidate-or$null-ne$outcome.verifier_completion){Stop-Commit 'attempt_outcome_invalid' 'A noncandidate ATTEMPT_END outcome must have null candidate/verifier_completion.'}
        return [pscustomobject]@{Record=$outcome;VerifierTicketId=$null}
    }
    if($null-eq$outcome.candidate-or$null-eq$outcome.verifier_completion){Stop-Commit 'attempt_outcome_invalid' 'candidate_found requires immutable candidate and verifier_completion pointers.'}
    $null=Assert-RawPointer $outcome.candidate $ProjectPath 'ATTEMPT_END candidate' '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf
    $verificationPath=Assert-RawPointer $outcome.verifier_completion $ProjectPath 'ATTEMPT_END verifier completion' '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf
    $verification=Read-StrictJsonObject $verificationPath 'ATTEMPT_END verifier completion'
    if([string]$verification.schema-ceq'math-research-verifier-result/v8'){
        $null=Assert-VerifierPassResult $verification $ProjectPath $Candidate $outcome.candidate ([string]$outcome.attempt_id)
        $verifiedTicketId=[string]$verification.ticket_id
    }
    elseif([string]$verification.schema-ceq'math-research-ticket-completion/v8'){
        Assert-RequiredKeys $verification @('schema','project_id','contract','run','ticket_id','role','status','output','candidate_artifact','completed_at_utc') 'verifier ticket completion' -Exact
        Assert-RequiredKeys $verification.contract @('path','version','binding_sha256') 'verifier ticket completion Contract' -Exact
        Assert-RequiredKeys $verification.run @('id','path') 'verifier ticket completion run' -Exact
        Assert-SafeId $verification.ticket_id 'verifier ticket completion ticket_id'
        $null=Assert-RawPointer $verification.candidate_artifact $ProjectPath 'verifier ticket completion candidate' '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf
        $resultPath=Assert-RawPointer $verification.output $ProjectPath 'verifier ticket completion output' '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf
        if([string]$verification.project_id-cne[string]$Candidate.project_id-or-not(Test-PointerEqual $verification.contract $Candidate.active_contract contract)-or[string]$verification.run.id-cne[string]$Candidate.active_run.id-or[string]$verification.run.path-cne[string]$Candidate.active_run.path-or[string]$verification.ticket_id-ceq[string]$outcome.attempt_id-or[string]$verification.role-cne'verifier'-or[string]$verification.status-cne'closed'-or-not(Test-PointerEqual $verification.candidate_artifact $outcome.candidate raw)-or-not(Test-CurrentUtcTimestamp $verification.completed_at_utc)){Stop-Commit 'attempt_outcome_invalid' 'Verifier ticket completion is not an independent closed verifier record on the claimed candidate.'}
        $result=Read-StrictJsonObject $resultPath 'verifier ticket completion PASS output'
        if([string]$result.ticket_id-cne[string]$verification.ticket_id){Stop-Commit 'attempt_outcome_invalid' 'Verifier completion and PASS output bind different ticket IDs.'}
        $null=Assert-VerifierPassResult $result $ProjectPath $Candidate $outcome.candidate ([string]$outcome.attempt_id)
        $verifiedTicketId=[string]$verification.ticket_id
    }
    else{Stop-Commit 'attempt_outcome_invalid' 'candidate_found verifier_completion must be an exact verifier result or closed verifier ticket completion.'}
    return [pscustomobject]@{Record=$outcome;VerifierTicketId=$verifiedTicketId}
}

function Get-PreAuditCompletionOutcome {
    param($Head,[long]$HeadGeneration,[string]$ProjectPath,$Candidate)
    if([string]$Head.active_run.status-cne'completion_candidate'){return $null}
    $eventKeys=@('schema','project_id','control_generation','event_id','event_type','updated_at_utc','previous_event_sha256','contract','run','counters','referenced_artifacts')
    $eventPath=Assert-GenerationPointer $Head.project_event_head $ProjectPath $HeadGeneration 'pre-audit completion event head' '^state/project-events/g(?<generation>[0-9]{4,})\.json$'
    $cursor=Read-StrictJsonObject $eventPath 'pre-audit completion event head';Assert-RequiredKeys $cursor $eventKeys 'pre-audit completion event head' -Exact
    if([string]$cursor.event_type-cnotin@('ATTEMPT_END','HOST_REBIND')){return $null}
    if($cursor.referenced_artifacts-isnot[Collections.IList]-or@($cursor.referenced_artifacts).Count-ne1){Stop-Commit 'attempt_outcome_invalid' 'Pre-audit completion head must carry exactly one attempt outcome.'}
    $outcomePointer=$cursor.referenced_artifacts[0];$cursorGeneration=$HeadGeneration
    while([string]$cursor.event_type-ceq'HOST_REBIND'){
        if([string]$cursor.run.status-cne'completion_candidate'-or-not(Test-PointerEqual $cursor.referenced_artifacts[0] $outcomePointer raw)){Stop-Commit 'attempt_outcome_invalid' 'Pre-audit HOST_REBIND changed the completion candidate/outcome authority.'}
        if($cursorGeneration-le1){Stop-Commit 'attempt_outcome_invalid' 'Pre-audit HOST_REBIND has no ATTEMPT_END predecessor.'}
        $priorGeneration=$cursorGeneration-1;$priorRelative=('state/project-events/g{0:D4}.json'-f$priorGeneration);$priorPath=Resolve-ProjectRelativeFile $ProjectPath $priorRelative 'pre-audit completion predecessor' '^state/project-events/'
        $priorHash=Get-FileSha256 $priorPath
        if([string]$cursor.previous_event_sha256-cne$priorHash){Stop-Commit 'attempt_outcome_invalid' 'Pre-audit completion HOST_REBIND event chain is broken.'}
        $prior=Read-StrictJsonObject $priorPath 'pre-audit completion predecessor';Assert-RequiredKeys $prior $eventKeys 'pre-audit completion predecessor' -Exact
        if([string]$prior.project_id-cne[string]$Candidate.project_id-or-not(Test-PointerEqual $prior.contract $Candidate.active_contract contract)-or[string]$prior.run.id-cne[string]$Candidate.active_run.id-or[string]$prior.run.path-cne[string]$Candidate.active_run.path-or[string]$prior.run.status-cne'completion_candidate'-or[string]$prior.event_type-cnotin@('ATTEMPT_END','AUDIT_END','HOST_REBIND')-or$prior.referenced_artifacts-isnot[Collections.IList]-or@($prior.referenced_artifacts).Count-ne1-or-not(Test-PointerEqual $prior.referenced_artifacts[0] $outcomePointer raw)){Stop-Commit 'attempt_outcome_invalid' 'Pre-audit completion HOST_REBIND chain changes outcome/Contract/run identity.'}
        $cursor=$prior;$cursorGeneration=$priorGeneration
    }
    if([string]$cursor.event_type-cne'ATTEMPT_END'){return $null}
    $result=Assert-AttemptOutcome $outcomePointer $ProjectPath $Candidate
    if([string]$result.Record.outcome-cne'candidate_found'){Stop-Commit 'attempt_outcome_invalid' 'Pre-audit completion outcome is not candidate_found.'}
    return [pscustomobject]@{Pointer=[ordered]@{path=[string]$outcomePointer.path;sha256=[string]$outcomePointer.sha256};Outcome=$result.Record;VerifierTicketId=$result.VerifierTicketId}
}

function Assert-CycleAuditSummary {
    param(
        [Parameter(Mandatory=$true)]$Pointer,
        [Parameter(Mandatory=$true)][string]$ProjectPath,
        [Parameter(Mandatory=$true)]$Candidate,
        [Parameter(Mandatory=$true)][ValidateSet('scheduled','early','terminal')][string]$ExpectedAuditKind,
        [switch]$RequirePass
    )
    $summaryRelative=[string]$Pointer.path
    if($summaryRelative.StartsWith('state/staging/',[StringComparison]::OrdinalIgnoreCase)-or$summaryRelative.IndexOf('/staging/',[StringComparison]::OrdinalIgnoreCase)-ge0){Stop-Commit 'cycle_audit_invalid' 'Cycle-audit summary cannot be published from staging.'}
    $summaryPath=Assert-RawPointer $Pointer $ProjectPath 'cycle-audit summary' '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf
    $summary=Read-StrictJsonObject $summaryPath 'cycle-audit summary'
    Assert-RequiredKeys $summary @('schema','project_id','contract','run','audit_kind','audit_start_event','plan','candidate','snapshot','reports','completed_at_utc') 'cycle-audit summary' -Exact
    Assert-RequiredKeys $summary.contract @('path','version','binding_sha256') 'cycle-audit summary Contract' -Exact
    Assert-RequiredKeys $summary.run @('id','path') 'cycle-audit summary run' -Exact
    if([string]$summary.schema-cne'math-research-cycle-audit-summary/v8'-or[string]$summary.project_id-cne[string]$Candidate.project_id-or-not(Test-PointerEqual $summary.contract $Candidate.active_contract contract)-or[string]$summary.run.id-cne[string]$Candidate.active_run.id-or[string]$summary.run.path-cne[string]$Candidate.active_run.path-or[string]$summary.audit_kind-cne$ExpectedAuditKind-or-not(Test-CurrentUtcTimestamp $summary.completed_at_utc)){Stop-Commit 'cycle_audit_invalid' 'Cycle-audit summary identity, kind, Contract, run, or timestamp is invalid.'}
    $null=Assert-RawPointer $summary.snapshot $ProjectPath 'cycle-audit snapshot' '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf
    if($ExpectedAuditKind-ceq'terminal'){
        if($null-eq$summary.candidate){Stop-Commit 'cycle_audit_invalid' 'Terminal cycle-audit summary must bind one immutable candidate.'}
        $null=Assert-RawPointer $summary.candidate $ProjectPath 'terminal cycle-audit candidate' '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf
    }
    elseif($null-ne$summary.candidate){Stop-Commit 'cycle_audit_invalid' 'Scheduled/early cycle-audit summary candidate must be null.'}
    $null=Assert-RawPointer $summary.audit_start_event $ProjectPath 'cycle-audit start event' '^state/project-events/'
    $null=Assert-RawPointer $summary.plan $ProjectPath 'cycle-audit plan pointer' '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf
    $roles=@('skeptic_quantifiers','skeptic_strategy','theory_tool_scout')
    if($summary.reports-isnot[Collections.IList]-or@($summary.reports).Count-ne3){Stop-Commit 'cycle_audit_invalid' 'Cycle-audit summary must contain exactly three reports.'}
    $reportPointers=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $allPass=$true
    for($index=0;$index-lt3;$index++){
        $entry=$summary.reports[$index]
        Assert-RequiredKeys $entry @('role','report') "cycle-audit report entry $index" -Exact
        if([string]$entry.role-cne$roles[$index]){Stop-Commit 'cycle_audit_invalid' 'Cycle-audit report roles/order is invalid.'}
        $reportRelative=[string]$entry.report.path
        if(-not$reportPointers.Add("$reportRelative|$([string]$entry.report.sha256)")-or$reportRelative.StartsWith('state/staging/',[StringComparison]::OrdinalIgnoreCase)-or$reportRelative.IndexOf('/staging/',[StringComparison]::OrdinalIgnoreCase)-ge0){Stop-Commit 'cycle_audit_invalid' 'Cycle-audit reports must be three distinct immutable non-staging files.'}
        $reportPath=Assert-RawPointer $entry.report $ProjectPath "cycle-audit $($entry.role) report" '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf
        $report=Read-StrictJsonObject $reportPath "cycle-audit $($entry.role) report"
        Assert-RequiredKeys $report @('schema','project_id','contract','run','role','candidate','snapshot','verdict','new_math_performed','checked_at_utc') "cycle-audit $($entry.role) report" -Exact
        Assert-RequiredKeys $report.contract @('path','version','binding_sha256') 'cycle-audit report Contract' -Exact
        Assert-RequiredKeys $report.run @('id','path') 'cycle-audit report run' -Exact
        if([string]$report.schema-cne'math-research-cycle-audit-report/v8'-or[string]$report.project_id-cne[string]$Candidate.project_id-or-not(Test-PointerEqual $report.contract $Candidate.active_contract contract)-or[string]$report.run.id-cne[string]$Candidate.active_run.id-or[string]$report.run.path-cne[string]$Candidate.active_run.path-or[string]$report.role-cne$roles[$index]-or-not(Test-JsonDeepEqual $report.candidate $summary.candidate)-or-not(Test-PointerEqual $report.snapshot $summary.snapshot raw)-or[string]$report.verdict-cnotin@('PASS','FAIL','INCONCLUSIVE')-or($RequirePass-and[string]$report.verdict-cne'PASS')-or$report.new_math_performed-isnot[bool]-or[bool]$report.new_math_performed-or-not(Test-CurrentUtcTimestamp $report.checked_at_utc)){Stop-Commit 'cycle_audit_invalid' 'Cycle-audit report verdict/no-new-math/content binding is invalid.'}
        if([string]$report.verdict-cne'PASS'){$allPass=$false}
    }
    return [pscustomobject]@{Pointer=[ordered]@{path=[string]$Pointer.path;sha256=[string]$Pointer.sha256};Summary=$summary;AllPass=$allPass}
}

function Assert-CycleAuditPlan {
    param(
        [Parameter(Mandatory=$true)]$Pointer,
        [Parameter(Mandatory=$true)][string]$ProjectPath,
        [Parameter(Mandatory=$true)][string]$ProjectId,
        [Parameter(Mandatory=$true)]$Contract,
        [Parameter(Mandatory=$true)]$Run,
        [Parameter(Mandatory=$true)][long]$Generation,
        [Parameter(Mandatory=$true)]$Counters,
        [AllowNull()]$CurrentTicket,
        [Parameter(Mandatory=$true)]$ContractFacts,
        [Parameter(Mandatory=$true)][ValidateSet('scheduled','early','terminal')][string]$ExpectedAuditKind,
        [AllowNull()]$ExpectedCandidate=$null
    )
    $relative=[string]$Pointer.path
    if($relative.StartsWith('state/staging/',[StringComparison]::OrdinalIgnoreCase)-or$relative.IndexOf('/staging/',[StringComparison]::OrdinalIgnoreCase)-ge0){Stop-Commit 'cycle_audit_invalid' 'Cycle-audit plan cannot be published from staging.'}
    $planPath=Assert-RawPointer $Pointer $ProjectPath 'cycle-audit plan' '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf
    $plan=Read-StrictJsonObject $planPath 'cycle-audit plan'
    Assert-RequiredKeys $plan @('schema','project_id','contract','run','audit_kind','candidate','snapshot','active_ticket','tickets','started_at_utc') 'cycle-audit plan' -Exact
    Assert-RequiredKeys $plan.contract @('path','version','binding_sha256') 'cycle-audit plan Contract' -Exact
    Assert-RequiredKeys $plan.run @('id','path') 'cycle-audit plan run' -Exact
    if([string]$plan.schema-cne'math-research-cycle-audit-plan/v8'-or[string]$plan.project_id-cne$ProjectId-or-not(Test-PointerEqual $plan.contract $Contract contract)-or[string]$plan.run.id-cne[string]$Run.id-or[string]$plan.run.path-cne[string]$Run.path-or[string]$plan.audit_kind-cne$ExpectedAuditKind-or-not(Test-CurrentUtcTimestamp $plan.started_at_utc)){Stop-Commit 'cycle_audit_invalid' 'Cycle-audit plan identity, kind, Contract, run, or timestamp is invalid.'}
    $null=Assert-RawPointer $plan.snapshot $ProjectPath 'cycle-audit plan snapshot' '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf
    if($ExpectedAuditKind-ceq'terminal'){
        if($null-eq$plan.candidate){Stop-Commit 'cycle_audit_invalid' 'Terminal cycle-audit plan must bind the verified ATTEMPT_END candidate.'}
        $null=Assert-RawPointer $plan.candidate $ProjectPath 'terminal cycle-audit plan candidate' '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf
        if($null-ne$ExpectedCandidate-and-not(Test-PointerEqual $plan.candidate $ExpectedCandidate raw)){Stop-Commit 'cycle_audit_invalid' 'Terminal cycle-audit plan candidate differs from the verified attempt outcome.'}
    }
    elseif($null-ne$plan.candidate){Stop-Commit 'cycle_audit_invalid' 'Scheduled/early cycle-audit plan candidate must be null.'}
    $null=Assert-RawPointer $plan.active_ticket $ProjectPath 'cycle-audit plan active_ticket' '^runs/'
    if($null-ne$CurrentTicket-and([string]$CurrentTicket.path-cne[string]$plan.active_ticket.path-or[string]$CurrentTicket.sha256-cne[string]$plan.active_ticket.sha256)){Stop-Commit 'cycle_audit_invalid' 'AUDIT_START state current ticket differs from plan.active_ticket.'}
    $roles=@('skeptic_quantifiers','skeptic_strategy','theory_tool_scout')
    if($plan.tickets-isnot[Collections.IList]-or@($plan.tickets).Count-ne3){Stop-Commit 'cycle_audit_invalid' 'Cycle-audit plan must freeze exactly three role tickets.'}
    $ticketIds=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $ticketPointers=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $currentMatches=0
    for($index=0;$index-lt3;$index++){
        $entry=$plan.tickets[$index]
        Assert-RequiredKeys $entry @('role','ticket') "cycle-audit ticket entry $index" -Exact
        if([string]$entry.role-cne$roles[$index]){Stop-Commit 'cycle_audit_invalid' 'Cycle-audit ticket roles/order is invalid.'}
        $ticketPath=Assert-RawPointer $entry.ticket $ProjectPath "cycle-audit $($entry.role) ticket" '^runs/'
        if(-not$ticketPointers.Add("$([string]$entry.ticket.path)|$([string]$entry.ticket.sha256)")){Stop-Commit 'cycle_audit_invalid' 'Cycle-audit role tickets must be three distinct immutable files.'}
        $record=Read-StrictJsonObject $ticketPath "cycle-audit $($entry.role) ticket"
        Assert-RequiredKeys $record @('schema','project_id','control_generation','contract','run','cycle_id','contract_initial_tickets_sha256','counter_snapshot','ticket') 'cycle-audit frozen ticket' -Exact
        if([string]$record.schema-cne'math-research-frozen-ticket/v8'-or[string]$record.project_id-cne$ProjectId-or-not(Test-JsonInteger $record.control_generation 1)-or[long]$record.control_generation-ne$Generation-or-not(Test-PointerEqual $record.contract $Contract contract)-or[string]$record.run.id-cne[string]$Run.id-or[string]$record.run.path-cne[string]$Run.path-or[string]$record.run.status-cne'auditing'-or[string]$record.cycle_id-cne[string]$ContractFacts.cycle_id-or[string]$record.contract_initial_tickets_sha256-cne[string]$ContractFacts.metadata.initial_tickets_sha256-or-not(Test-CountersEqual (Get-Counters $record.counter_snapshot 'cycle-audit ticket counters') $Counters)-or[string]$record.ticket.role-cne$roles[$index]){Stop-Commit 'cycle_audit_invalid' 'Cycle-audit frozen ticket binding is invalid.'}
        Assert-TicketBody $record.ticket $ContractFacts $ProjectPath $Run
        if(-not$ticketIds.Add([string]$record.ticket.ticket_id)){Stop-Commit 'cycle_audit_invalid' 'Cycle-audit ticket IDs must be distinct.'}
        if([string]$plan.active_ticket.path-ceq[string]$entry.ticket.path-and[string]$plan.active_ticket.sha256-ceq[string]$entry.ticket.sha256){$currentMatches++}
    }
    if($currentMatches-ne1){Stop-Commit 'cycle_audit_invalid' 'AUDIT_START current ticket must be exactly one member of its three-role audit plan.'}
    return $plan
}

function Assert-CycleAuditHistory {
    param(
        [Parameter(Mandatory=$true)]$SummaryResult,
        [Parameter(Mandatory=$true)]$EndEvent,
        [Parameter(Mandatory=$true)][long]$EndGeneration,
        [Parameter(Mandatory=$true)][string]$ProjectPath,
        [Parameter(Mandatory=$true)]$Candidate,
        [Parameter(Mandatory=$true)]$ContractFacts
    )
    $summary=$SummaryResult.Summary;$startPointer=$summary.audit_start_event
    if([string]$startPointer.path-cnotmatch'^state/project-events/g(?<generation>[0-9]{4,})\.json$'){Stop-Commit 'cycle_audit_invalid' 'Cycle-audit start event path is not generation-canonical.'}
    $startGeneration=[long]$Matches.generation
    if($startGeneration-lt1-or$startGeneration-ge$EndGeneration){Stop-Commit 'cycle_audit_invalid' 'Cycle-audit start generation is outside the active audit interval.'}
    $startPath=Assert-RawPointer $startPointer $ProjectPath 'cycle-audit start event' '^state/project-events/'
    $start=Read-StrictJsonObject $startPath 'cycle-audit start event'
    $eventKeys=@('schema','project_id','control_generation','event_id','event_type','updated_at_utc','previous_event_sha256','contract','run','counters','referenced_artifacts')
    Assert-RequiredKeys $start $eventKeys 'cycle-audit start event' -Exact
    if([string]$start.schema-cne'math-research-project-event/v8'-or[string]$start.project_id-cne[string]$Candidate.project_id-or-not(Test-JsonInteger $start.control_generation 1)-or[long]$start.control_generation-ne$startGeneration-or[string]$start.event_type-cne'AUDIT_START'-or-not(Test-PointerEqual $start.contract $Candidate.active_contract contract)-or[string]$start.run.id-cne[string]$Candidate.active_run.id-or[string]$start.run.path-cne[string]$Candidate.active_run.path-or[string]$start.run.status-cne'auditing'-or-not(Test-CurrentUtcTimestamp $start.updated_at_utc)-or$start.referenced_artifacts-isnot[Collections.IList]-or@($start.referenced_artifacts).Count-ne1-or-not(Test-PointerEqual $start.referenced_artifacts[0] $summary.plan raw)){Stop-Commit 'cycle_audit_invalid' 'Cycle-audit start event/plan binding is invalid.'}
    $startCounters=Get-Counters $start 'cycle-audit start counters'
    $plan=Assert-CycleAuditPlan -Pointer $summary.plan -ProjectPath $ProjectPath -ProjectId ([string]$Candidate.project_id) -Contract $Candidate.active_contract -Run $Candidate.active_run -Generation $startGeneration -Counters $startCounters -CurrentTicket $null -ContractFacts $ContractFacts -ExpectedAuditKind ([string]$summary.audit_kind) -ExpectedCandidate $summary.candidate
    if(-not(Test-PointerEqual $plan.snapshot $summary.snapshot raw)-or-not(Test-JsonDeepEqual $plan.candidate $summary.candidate)){Stop-Commit 'cycle_audit_invalid' 'Cycle-audit summary candidate/snapshot differs from its frozen start plan.'}
    if([string]$summary.audit_kind-ceq'terminal'){
        $priorGeneration=$startGeneration-1
        if($priorGeneration-lt1){Stop-Commit 'cycle_audit_invalid' 'Terminal audit start has no candidate_found predecessor.'}
        $priorPath=Resolve-ProjectRelativeFile $ProjectPath ('state/project-events/g{0:D4}.json'-f$priorGeneration) 'terminal audit predecessor' '^state/project-events/'
        $priorEvent=Read-StrictJsonObject $priorPath 'terminal audit predecessor';$priorRun=[ordered]@{id=[string]$Candidate.active_run.id;path=[string]$Candidate.active_run.path;status='completion_candidate'}
        $priorHead=[ordered]@{active_run=$priorRun;project_event_head=[ordered]@{path=('state/project-events/g{0:D4}.json'-f$priorGeneration);sha256=Get-FileSha256 $priorPath;control_generation=$priorGeneration}}
        $locked=Get-PreAuditCompletionOutcome -Head $priorHead -HeadGeneration $priorGeneration -ProjectPath $ProjectPath -Candidate $Candidate
        if($null-eq$locked-or-not(Test-PointerEqual $locked.Outcome.candidate $summary.candidate raw)){Stop-Commit 'cycle_audit_invalid' 'Terminal audit candidate is not the locked candidate_found ATTEMPT_END outcome.'}
    }
    $expectedPrevious=[string]$startPointer.sha256
    $allowedIntermediate=@('CHECKPOINT_COMMIT','PAUSE','RESUME','HOST_REBIND')
    for($generation=$startGeneration+1;$generation-lt$EndGeneration;$generation++){
        $relative=('state/project-events/g{0:D4}.json'-f$generation)
        $path=Resolve-ProjectRelativeFile $ProjectPath $relative 'cycle-audit intermediate event' '^state/project-events/'
        $hash=Get-FileSha256 $path;$middle=Read-StrictJsonObject $path 'cycle-audit intermediate event';Assert-RequiredKeys $middle $eventKeys 'cycle-audit intermediate event' -Exact
        if([string]$middle.schema-cne'math-research-project-event/v8'-or[string]$middle.project_id-cne[string]$Candidate.project_id-or-not(Test-JsonInteger $middle.control_generation 1)-or[long]$middle.control_generation-ne$generation-or[string]$middle.previous_event_sha256-cne$expectedPrevious-or[string]$middle.event_type-cnotin$allowedIntermediate-or-not(Test-PointerEqual $middle.contract $Candidate.active_contract contract)-or[string]$middle.run.id-cne[string]$Candidate.active_run.id-or[string]$middle.run.path-cne[string]$Candidate.active_run.path-or[string]$middle.run.status-cnotin@('auditing','paused')-or-not(Test-CountersEqual (Get-Counters $middle 'cycle-audit intermediate counters') $startCounters)){Stop-Commit 'cycle_audit_invalid' 'Cycle-audit intermediate history changes audit identity/counters or breaks the event chain.'}
        $expectedPrevious=$hash
    }
    if([string]$EndEvent.previous_event_sha256-cne$expectedPrevious){Stop-Commit 'cycle_audit_invalid' 'AUDIT_END is not chained from its bound authoritative AUDIT_START history.'}
    $endCounters=Get-Counters $EndEvent 'cycle-audit end counters'
    foreach($name in @('attempt_count','audit_count','total_round_count')){if([long]$endCounters[$name]-ne[long]$startCounters[$name]){Stop-Commit 'cycle_audit_invalid' 'AUDIT_END global counters differ from AUDIT_START.'}}
    return $plan
}

function Get-AuditedCompletionSummary {
    param(
        [Parameter(Mandatory=$true)]$Head,
        [Parameter(Mandatory=$true)][long]$HeadGeneration,
        [Parameter(Mandatory=$true)][string]$ProjectPath,
        [Parameter(Mandatory=$true)]$Candidate,
        [Parameter(Mandatory=$true)]$ContractFacts
    )
    if([string]$Head.active_run.status-cne'completion_candidate'){return $null}
    $eventKeys=@('schema','project_id','control_generation','event_id','event_type','updated_at_utc','previous_event_sha256','contract','run','counters','referenced_artifacts')
    $eventPath=Assert-GenerationPointer $Head.project_event_head $ProjectPath $HeadGeneration 'audited-completion event head' '^state/project-events/g(?<generation>[0-9]{4,})\.json$'
    $headEvent=Read-StrictJsonObject $eventPath 'audited-completion event head';Assert-RequiredKeys $headEvent $eventKeys 'audited-completion event head' -Exact
    if([string]$headEvent.event_type-cnotin@('AUDIT_END','HOST_REBIND')){return $null}
    if($headEvent.referenced_artifacts-isnot[Collections.IList]-or@($headEvent.referenced_artifacts).Count-ne1){Stop-Commit 'completion_transition_invalid' 'Audited completion event must carry exactly one terminal cycle-audit summary.'}
    $summaryPointer=$headEvent.referenced_artifacts[0];$cursor=$headEvent;$cursorGeneration=$HeadGeneration
    while([string]$cursor.event_type-ceq'HOST_REBIND'){
        if($cursorGeneration-le1){Stop-Commit 'completion_transition_invalid' 'Audited completion HOST_REBIND chain has no terminal AUDIT_END predecessor.'}
        $priorGeneration=$cursorGeneration-1;$priorRelative=('state/project-events/g{0:D4}.json'-f$priorGeneration);$priorPath=Resolve-ProjectRelativeFile $ProjectPath $priorRelative 'audited-completion predecessor event' '^state/project-events/'
        $priorHash=Get-FileSha256 $priorPath
        if([string]$cursor.previous_event_sha256-cne$priorHash){Stop-Commit 'completion_transition_invalid' 'Audited completion HOST_REBIND chain hash is broken.'}
        $prior=Read-StrictJsonObject $priorPath 'audited-completion predecessor event';Assert-RequiredKeys $prior $eventKeys 'audited-completion predecessor event' -Exact
        if([string]$prior.project_id-cne[string]$Candidate.project_id-or-not(Test-PointerEqual $prior.contract $Candidate.active_contract contract)-or[string]$prior.run.id-cne[string]$Candidate.active_run.id-or[string]$prior.run.path-cne[string]$Candidate.active_run.path-or[string]$prior.run.status-cne'completion_candidate'-or[string]$prior.event_type-cnotin@('ATTEMPT_END','AUDIT_END','HOST_REBIND')-or$prior.referenced_artifacts-isnot[Collections.IList]-or@($prior.referenced_artifacts).Count-ne1-or-not(Test-PointerEqual $prior.referenced_artifacts[0] $summaryPointer raw)){Stop-Commit 'completion_transition_invalid' 'Audited completion HOST_REBIND chain changes its terminal certificate/outcome or research identity.'}
        $cursor=$prior;$cursorGeneration=$priorGeneration
    }
    if([string]$cursor.event_type-cne'AUDIT_END'){return $null}
    $summaryResult=Assert-CycleAuditSummary $summaryPointer $ProjectPath $Candidate terminal -RequirePass
    $null=Assert-CycleAuditHistory $summaryResult $cursor $cursorGeneration $ProjectPath $Candidate $ContractFacts
    return $summaryResult
}

function Assert-ResumeCapsule {
    param($Pointer,[string]$ProjectPath,$Candidate,$ExpectedTicket,$ExpectedLifecycle,$ExpectedCounters,[string]$ExpectedPriorStatus)
    $path=Assert-RawPointer $Pointer $ProjectPath 'resume capsule' '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf;$capsule=Read-StrictJsonObject $path 'resume capsule'
    Assert-RequiredKeys $capsule @('schema','project_id','contract','run','prior_status','ticket','lifecycle','counters','created_at_utc') 'resume capsule' -Exact
    Assert-RequiredKeys $capsule.contract @('path','version','binding_sha256') 'resume capsule Contract' -Exact;Assert-RequiredKeys $capsule.run @('id','path') 'resume capsule run' -Exact
    if([string]$capsule.schema-cne'math-research-resume-capsule/v8'-or[string]$capsule.project_id-cne[string]$Candidate.project_id-or-not(Test-PointerEqual $capsule.contract $Candidate.active_contract contract)-or[string]$capsule.run.id-cne[string]$Candidate.active_run.id-or[string]$capsule.run.path-cne[string]$Candidate.active_run.path-or[string]$capsule.prior_status-cne$ExpectedPriorStatus-or[string]$capsule.prior_status-cnotin@('attempt_running','auditing')-or-not(Test-JsonDeepEqual $capsule.ticket $ExpectedTicket)-or-not(Test-JsonDeepEqual $capsule.lifecycle $ExpectedLifecycle)-or-not(Test-CountersEqual (Get-Counters $capsule 'resume capsule counters') $ExpectedCounters)-or-not(Test-CurrentUtcTimestamp $capsule.created_at_utc)){Stop-Commit 'resume_capsule_invalid' 'Resume capsule identity/status/ticket/lifecycle/counters is invalid.'}
    return [pscustomobject]@{Pointer=[ordered]@{path=[string]$Pointer.path;sha256=[string]$Pointer.sha256};Capsule=$capsule}
}

function Get-PausedResumeCapsule {
    param($Head,[long]$HeadGeneration,[string]$ProjectPath,$Candidate,$ExpectedTicket,$ExpectedLifecycle,$ExpectedCounters)
    if([string]$Head.active_run.status-cne'paused'){return $null}
    $keys=@('schema','project_id','control_generation','event_id','event_type','updated_at_utc','previous_event_sha256','contract','run','counters','referenced_artifacts')
    $path=Assert-GenerationPointer $Head.project_event_head $ProjectPath $HeadGeneration 'paused event head' '^state/project-events/g(?<generation>[0-9]{4,})\.json$';$cursor=Read-StrictJsonObject $path 'paused event head';Assert-RequiredKeys $cursor $keys 'paused event head' -Exact
    if([string]$cursor.event_type-cnotin@('PAUSE','HOST_REBIND')-or$cursor.referenced_artifacts-isnot[Collections.IList]-or@($cursor.referenced_artifacts).Count-ne1){return $null}
    $capsulePointer=$cursor.referenced_artifacts[0];$generation=$HeadGeneration
    while([string]$cursor.event_type-ceq'HOST_REBIND'){
        if($generation-le1){Stop-Commit 'resume_capsule_invalid' 'Paused HOST_REBIND chain has no PAUSE predecessor.'};$priorGeneration=$generation-1;$priorPath=Resolve-ProjectRelativeFile $ProjectPath ('state/project-events/g{0:D4}.json'-f$priorGeneration) 'pause predecessor event' '^state/project-events/';$priorHash=Get-FileSha256 $priorPath
        if([string]$cursor.previous_event_sha256-cne$priorHash){Stop-Commit 'resume_capsule_invalid' 'Paused HOST_REBIND chain hash is broken.'};$prior=Read-StrictJsonObject $priorPath 'pause predecessor event';Assert-RequiredKeys $prior $keys 'pause predecessor event' -Exact
        if([string]$prior.event_type-cnotin@('PAUSE','HOST_REBIND')-or[string]$prior.run.status-cne'paused'-or$prior.referenced_artifacts-isnot[Collections.IList]-or@($prior.referenced_artifacts).Count-ne1-or-not(Test-PointerEqual $prior.referenced_artifacts[0] $capsulePointer raw)){Stop-Commit 'resume_capsule_invalid' 'Paused HOST_REBIND chain changes or loses its resume capsule.'};$cursor=$prior;$generation=$priorGeneration
    }
    return Assert-ResumeCapsule $capsulePointer $ProjectPath $Candidate $ExpectedTicket $ExpectedLifecycle $ExpectedCounters ([string](Read-StrictJsonObject (Assert-RawPointer $capsulePointer $ProjectPath 'resume capsule' '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf) 'resume capsule').prior_status)
}

function Assert-UniqueJsonProperties {
    param([Parameter(Mandatory = $true)][Text.Json.JsonElement]$Element, [Parameter(Mandatory = $true)][string]$Path)
    if ($Element.ValueKind -eq [Text.Json.JsonValueKind]::Object) {
        $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        foreach ($property in $Element.EnumerateObject()) {
            if (-not $seen.Add($property.Name)) { Stop-Commit 'strict_json_invalid' "Duplicate JSON property '$($property.Name)' at $Path." }
            Assert-UniqueJsonProperties -Element $property.Value -Path "$Path.$($property.Name)"
        }
    }
    elseif ($Element.ValueKind -eq [Text.Json.JsonValueKind]::Array) {
        $index = 0
        foreach ($item in $Element.EnumerateArray()) {
            Assert-UniqueJsonProperties -Element $item -Path "$Path[$index]"
            $index++
        }
    }
}

function ConvertFrom-StrictJsonBytes {
    param([Parameter(Mandatory = $true)][byte[]]$Bytes, [Parameter(Mandatory = $true)][string]$Label)
    try { $text = [Text.UTF8Encoding]::new($false, $true).GetString($Bytes) }
    catch { Stop-Commit 'strict_json_invalid' "$Label is not valid UTF-8." }
    $options = [Text.Json.JsonDocumentOptions]::new()
    $options.AllowTrailingCommas = $false
    $options.CommentHandling = [Text.Json.JsonCommentHandling]::Disallow
    $options.MaxDepth = 64
    try { $document = [Text.Json.JsonDocument]::Parse($text, $options) }
    catch { Stop-Commit 'strict_json_invalid' "$Label is not strict JSON: $($_.Exception.Message)" }
    try {
        if ($document.RootElement.ValueKind -ne [Text.Json.JsonValueKind]::Object) { Stop-Commit 'strict_json_invalid' "$Label must be a JSON object." }
        Assert-UniqueJsonProperties -Element $document.RootElement -Path '$'
    }
    finally { $document.Dispose() }
    try { return ($text | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String) }
    catch { Stop-Commit 'strict_json_invalid' "$Label cannot be converted without date coercion." }
}

function Read-StrictJsonObject {
    param([Parameter(Mandatory = $true)][string]$LiteralPath, [Parameter(Mandatory = $true)][string]$Label)
    if (-not (Test-Path -LiteralPath $LiteralPath -PathType Leaf)) { Stop-Commit 'referenced_file_missing' "$Label is missing: $LiteralPath" }
    return ConvertFrom-StrictJsonBytes -Bytes ([IO.File]::ReadAllBytes($LiteralPath)) -Label $Label
}

function Test-JsonInteger {
    param($Value, [long]$Minimum = 0)
    if ($null -eq $Value -or $Value.GetType().Name -cnotin @('Byte','SByte','Int16','UInt16','Int32','UInt32','Int64','UInt64')) { return $false }
    try { return [decimal]$Value -ge $Minimum }
    catch { return $false }
}

function Test-CurrentUtcTimestamp {
    param($Value)
    if ($Value -isnot [string] -or [string]$Value -cnotmatch '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,7})?Z$') { return $false }
    $parsed = [DateTimeOffset]::MinValue
    if (-not [DateTimeOffset]::TryParse([string]$Value,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::AssumeUniversal -bor [Globalization.DateTimeStyles]::AdjustToUniversal,[ref]$parsed)) { return $false }
    return $parsed -le [DateTimeOffset]::UtcNow.AddMinutes(5)
}

function Assert-LowerSha256 {
    param($Value, [Parameter(Mandatory = $true)][string]$Label)
    if ($Value -isnot [string] -or [string]$Value -cnotmatch '^[0-9a-f]{64}$') { Stop-Commit 'hash_invalid' "$Label must be one lowercase SHA-256 value." }
}

function Assert-RequiredKeys {
    param($Object, [Parameter(Mandatory = $true)][string[]]$Required, [Parameter(Mandatory = $true)][string]$Label, [switch]$Exact)
    if ($Object -isnot [Collections.IDictionary]) { Stop-Commit 'shape_invalid' "$Label must be an object." }
    foreach ($key in $Required) {
        if (-not $Object.Contains($key)) { Stop-Commit 'shape_invalid' "$Label is missing '$key'." }
    }
    if ($Exact -and @($Object.Keys).Count -ne $Required.Count) { Stop-Commit 'shape_invalid' "$Label has unknown properties." }
}

function Assert-SafeId {
    param($Value, [Parameter(Mandatory = $true)][string]$Label)
    if ($Value -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$Value) -or ([string]$Value).Length -gt 128 -or [string]$Value -cnotmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$') {
        Stop-Commit 'identity_invalid' "$Label is not a safe identifier."
    }
}

function Test-PathInside {
    param([Parameter(Mandatory = $true)][string]$Child, [Parameter(Mandatory = $true)][string]$Directory)
    $childFull = [IO.Path]::GetFullPath($Child)
    $directoryFull = [IO.Path]::GetFullPath($Directory).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    return $childFull.StartsWith($directoryFull, [StringComparison]::OrdinalIgnoreCase)
}

function Convert-LegacyRelativePath {
    param($Value,[Parameter(Mandatory = $true)][string]$Label)
    if ($Value -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$Value) -or [IO.Path]::IsPathRooted([string]$Value) -or ([string]$Value).Contains(':')) { Stop-Commit 'lineage_invalid' "$Label is not one safe legacy relative path." }
    $canonical = ([string]$Value).Replace('\','/')
    $segments = @($canonical -split '/')
    if ($segments.Count -lt 2 -or @($segments | Where-Object { [string]::IsNullOrEmpty([string]$_) -or [string]$_ -in @('.','..') }).Count -gt 0) { Stop-Commit 'lineage_invalid' "$Label contains an empty/dot/escape segment." }
    return $canonical
}

function Assert-NoReparsePointChain {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    $cursor = [IO.Path]::GetFullPath($LiteralPath)
    while (-not [string]::IsNullOrWhiteSpace($cursor) -and (Test-Path -LiteralPath $cursor)) {
        $item = Get-Item -LiteralPath $cursor -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { Stop-Commit 'reparse_point_forbidden' "Reparse point is forbidden: $($item.FullName)" }
        $parent = Split-Path -Parent $item.FullName
        if ([string]::IsNullOrWhiteSpace($parent) -or $parent -ceq $item.FullName) { break }
        $cursor = $parent
    }
}

function Resolve-ProjectRelativeFile {
    param(
        [Parameter(Mandatory = $true)][string]$ProjectPath,
        [Parameter(Mandatory = $true)]$RelativePath,
        [Parameter(Mandatory = $true)][string]$Label,
        [string]$RequiredPattern = '^(?:state|runs|contracts|indexes)/',
        [switch]$AllowProjectRootLeaf
    )
    if ($RelativePath -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$RelativePath) -or [IO.Path]::IsPathRooted([string]$RelativePath) -or ([string]$RelativePath).Contains(':') -or ([string]$RelativePath).Contains('\')) {
        Stop-Commit 'unsafe_pointer_path' "$Label must use a canonical forward-slash project-relative path."
    }
    $segments = @(([string]$RelativePath) -split '/')
    $minimumSegments = if ($AllowProjectRootLeaf) { 1 } else { 2 }
    if ($segments.Count -lt $minimumSegments -or @($segments | Where-Object { [string]::IsNullOrEmpty([string]$_) -or [string]$_ -in @('.','..') }).Count -gt 0 -or [string]$RelativePath -cnotmatch $RequiredPattern) {
        Stop-Commit 'unsafe_pointer_path' "$Label is outside its allowed project subtree."
    }
    $full = [IO.Path]::GetFullPath((Join-Path $ProjectPath (([string]$RelativePath).Replace('/', [IO.Path]::DirectorySeparatorChar))))
    if (-not (Test-PathInside -Child $full -Directory $ProjectPath) -or -not (Test-Path -LiteralPath $full -PathType Leaf)) { Stop-Commit 'referenced_file_missing' "$Label does not resolve to one project file." }
    Assert-NoReparsePointChain -LiteralPath $full
    return $full
}

function Assert-RawPointer {
    param(
        $Pointer,
        [Parameter(Mandatory = $true)][string]$ProjectPath,
        [Parameter(Mandatory = $true)][string]$Label,
        [string]$RequiredPattern = '^(?:state|runs|contracts|indexes)/',
        [switch]$AllowProjectRootLeaf
    )
    Assert-RequiredKeys -Object $Pointer -Required @('path','sha256') -Label $Label -Exact
    Assert-LowerSha256 -Value $Pointer.sha256 -Label "$Label.sha256"
    $canonical=[string]$Pointer.path
    if($canonical.Equals('project.json',[StringComparison]::OrdinalIgnoreCase)-or$canonical.StartsWith('state/staging/',[StringComparison]::OrdinalIgnoreCase)-or$canonical.IndexOf('/staging/',[StringComparison]::OrdinalIgnoreCase)-ge0-or(Split-Path -Leaf $canonical)-ieq'final.build-v8.tmp'){Stop-Commit 'unsafe_pointer_path' "$Label must point to already-published immutable material, not mutable authority/staging."}
    $full = Resolve-ProjectRelativeFile -ProjectPath $ProjectPath -RelativePath $Pointer.path -Label "$Label.path" -RequiredPattern $RequiredPattern -AllowProjectRootLeaf:$AllowProjectRootLeaf
    try{$candidateFull=[IO.Path]::GetFullPath($CandidateHeadFile)}catch{$candidateFull=$null};if($null-ne$candidateFull-and[IO.Path]::GetFullPath($full)-ceq$candidateFull){Stop-Commit 'unsafe_pointer_path' "$Label cannot point at the candidate head being committed."}
    if ((Get-FileSha256 -LiteralPath $full) -cne [string]$Pointer.sha256) { Stop-Commit 'pointer_hash_mismatch' "$Label hash does not match its immutable file." }
    return $full
}

function Assert-GenerationPointer {
    param(
        $Pointer,
        [Parameter(Mandatory = $true)][string]$ProjectPath,
        [Parameter(Mandatory = $true)][long]$Generation,
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$PathPattern
    )
    Assert-RequiredKeys -Object $Pointer -Required @('path','sha256','control_generation') -Label $Label -Exact
    Assert-LowerSha256 -Value $Pointer.sha256 -Label "$Label.sha256"
    if (-not (Test-JsonInteger $Pointer.control_generation 1) -or [long]$Pointer.control_generation -ne $Generation) { Stop-Commit 'generation_mismatch' "$Label generation is not the candidate generation." }
    if ([string]$Pointer.path -cnotmatch $PathPattern -or [long]$Matches['generation'] -ne $Generation) { Stop-Commit 'unsafe_pointer_path' "$Label path is not generation-bound." }
    $full = Resolve-ProjectRelativeFile -ProjectPath $ProjectPath -RelativePath $Pointer.path -Label "$Label.path"
    if ((Get-FileSha256 -LiteralPath $full) -cne [string]$Pointer.sha256) { Stop-Commit 'pointer_hash_mismatch' "$Label hash does not match its immutable file." }
    return $full
}

function Assert-ContractPointer {
    param($Pointer, [Parameter(Mandatory = $true)][string]$ProjectPath, [Parameter(Mandatory = $true)][string]$Label)
    Assert-RequiredKeys -Object $Pointer -Required @('path','version','binding_sha256') -Label $Label -Exact
    if ([string]$Pointer.version -cne 'v8') { Stop-Commit 'contract_invalid' "$Label version must be exactly v8." }
    Assert-LowerSha256 -Value $Pointer.binding_sha256 -Label "$Label.binding_sha256"
    $full = Resolve-ProjectRelativeFile -ProjectPath $ProjectPath -RelativePath $Pointer.path -Label "$Label.path" -RequiredPattern '^contracts/[^/]+$'
    if ((Get-NormalizedTextSha256 -LiteralPath $full) -cne [string]$Pointer.binding_sha256) { Stop-Commit 'pointer_hash_mismatch' "$Label binding hash does not match the normalized Contract bytes." }
    return $full
}

function Assert-RunPointer {
    param($Pointer, [Parameter(Mandatory = $true)][string]$ProjectPath, [Parameter(Mandatory = $true)][string]$Label)
    Assert-RequiredKeys -Object $Pointer -Required @('id','path','status') -Label $Label -Exact
    Assert-SafeId -Value $Pointer.id -Label "$Label.id"
    $statuses = @('not_started','preparing','attempt_running','audit_due','auditing','completion_candidate','awaiting_input','paused','goal_continuity_terminal','superseded','closed')
    if ([string]$Pointer.status -cnotin $statuses -or [string]$Pointer.path -cne "runs/$([string]$Pointer.id)") { Stop-Commit 'run_invalid' "$Label is not one canonical active run pointer." }
    $full = [IO.Path]::GetFullPath((Join-Path $ProjectPath (([string]$Pointer.path).Replace('/', [IO.Path]::DirectorySeparatorChar))))
    if (-not (Test-PathInside -Child $full -Directory (Join-Path $ProjectPath 'runs')) -or -not (Test-Path -LiteralPath $full -PathType Container)) { Stop-Commit 'run_invalid' "$Label run directory is missing." }
    Assert-NoReparsePointChain -LiteralPath $full
    return $full
}

function Test-PointerEqual {
    param($Left, $Right, [Parameter(Mandatory = $true)][ValidateSet('contract','run','raw','generation')][string]$Kind)
    if ($Left -isnot [Collections.IDictionary] -or $Right -isnot [Collections.IDictionary]) { return $false }
    $keys = switch ($Kind) {
        'contract' { @('path','version','binding_sha256') }
        'run' { @('id','path','status') }
        'raw' { @('path','sha256') }
        'generation' { @('path','sha256','control_generation') }
    }
    foreach ($key in $keys) { if (-not $Left.Contains($key) -or -not $Right.Contains($key) -or [string]$Left[$key] -cne [string]$Right[$key]) { return $false } }
    return $true
}

function Test-HostGoalEqual {
    param($Left, $Right)
    foreach ($value in @($Left,$Right)) { Assert-RequiredKeys -Object $value -Required @('thread_id_available','thread_id','objective_raw_sha256') -Label 'host_goal' -Exact }
    if ($Left.thread_id_available -isnot [bool] -or $Right.thread_id_available -isnot [bool]) { return $false }
    Assert-LowerSha256 -Value $Left.objective_raw_sha256 -Label 'host_goal.objective_raw_sha256'
    Assert-LowerSha256 -Value $Right.objective_raw_sha256 -Label 'host_goal.objective_raw_sha256'
    foreach ($value in @($Left,$Right)) {
        if ([bool]$value.thread_id_available) {
            if ($value.thread_id -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$value.thread_id) -or ([string]$value.thread_id).Length -gt 256 -or [string]$value.thread_id -match '[\x00-\x1f\x7f]') { return $false }
        }
        elseif ($null -ne $value.thread_id) { return $false }
    }
    return ([bool]$Left.thread_id_available -eq [bool]$Right.thread_id_available -and [string]$Left.thread_id -ceq [string]$Right.thread_id -and [string]$Left.objective_raw_sha256 -ceq [string]$Right.objective_raw_sha256)
}

function Get-Counters {
    param($Object, [Parameter(Mandatory = $true)][string]$Label)
    $counters = if ($Object -is [Collections.IDictionary] -and $Object.Contains('counters')) { $Object.counters } else { $Object }
    Assert-RequiredKeys -Object $counters -Required @('attempt_count','audit_count','total_round_count','attempts_since_last_audit','audit_due') -Label $Label -Exact
    foreach ($key in @('attempt_count','audit_count','total_round_count','attempts_since_last_audit')) { if (-not (Test-JsonInteger $counters[$key] 0)) { Stop-Commit 'counter_invalid' "$Label.$key is not a nonnegative JSON integer." } }
    if ($counters.audit_due -isnot [bool] -or [decimal]$counters.total_round_count -ne ([decimal]$counters.attempt_count + [decimal]$counters.audit_count) -or [decimal]$counters.attempts_since_last_audit -gt [decimal]$counters.attempt_count) {
        Stop-Commit 'counter_invalid' "$Label counters are inconsistent."
    }
    return $counters
}

function Test-CountersEqual {
    param($Left, $Right)
    foreach ($key in @('attempt_count','audit_count','total_round_count','attempts_since_last_audit','audit_due')) { if ([string]$Left[$key] -cne [string]$Right[$key]) { return $false } }
    return $true
}

function Test-JsonDeepEqual {
    param($Left,$Right)
    if ($null -eq $Left -or $null -eq $Right) { return $null -eq $Left -and $null -eq $Right }
    if ($Left -is [Collections.IDictionary] -or $Right -is [Collections.IDictionary]) {
        if ($Left -isnot [Collections.IDictionary] -or $Right -isnot [Collections.IDictionary] -or @($Left.Keys).Count -ne @($Right.Keys).Count) { return $false }
        foreach ($key in $Left.Keys) { if (-not $Right.Contains($key) -or -not (Test-JsonDeepEqual $Left[$key] $Right[$key])) { return $false } }
        return $true
    }
    $leftArray = $Left -is [Collections.IList] -and $Left -isnot [string]
    $rightArray = $Right -is [Collections.IList] -and $Right -isnot [string]
    if ($leftArray -or $rightArray) {
        if (-not $leftArray -or -not $rightArray -or $Left.Count -ne $Right.Count) { return $false }
        for ($i=0;$i -lt $Left.Count;$i++) { if (-not (Test-JsonDeepEqual $Left[$i] $Right[$i])) { return $false } }
        return $true
    }
    return $Left.GetType().Name -ceq $Right.GetType().Name -and $Left -ceq $Right
}

function Assert-CrossBoundRecord {
    param(
        $Record,
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$ProjectId,
        [Parameter(Mandatory = $true)][long]$Generation,
        $Contract,
        $Run,
        [switch]$RunIdentityOnly
    )
    Assert-RequiredKeys -Object $Record -Required @('project_id','control_generation','contract','run') -Label $Label
    if ([string]$Record.project_id -cne $ProjectId -or -not (Test-JsonInteger $Record.control_generation 1) -or [long]$Record.control_generation -ne $Generation) { Stop-Commit 'cross_binding_mismatch' "$Label project/generation binding mismatches." }
    $runMatches = if ($RunIdentityOnly) {
        $Record.run -is [Collections.IDictionary] -and $Record.run.Contains('id') -and $Record.run.Contains('path') -and [string]$Record.run.id -ceq [string]$Run.id -and [string]$Record.run.path -ceq [string]$Run.path
    }
    else { Test-PointerEqual $Record.run $Run run }
    if (-not (Test-PointerEqual $Record.contract $Contract contract) -or -not $runMatches) { Stop-Commit 'cross_binding_mismatch' "$Label Contract/run binding mismatches." }
}

function Assert-LegacySuccessor {
    param(
        $Pointer,
        [Parameter(Mandatory = $true)][string]$ProjectPath,
        [Parameter(Mandatory = $true)][string]$ProjectId,
        [Parameter(Mandatory = $true)][long]$ActivationGeneration,
        [AllowNull()][string]$ExpectedActivationOldHash,
        [Parameter(Mandatory = $true)][bool]$FirstActivation,
        $ActiveContract,
        $ActiveRun,
        $HostBindingHead,
        $StateSuccessor,
        $CheckpointSuccessor
    )
    $lineagePath = Assert-GenerationPointer -Pointer $Pointer -ProjectPath $ProjectPath -Generation $ActivationGeneration -Label 'legacy_successor' -PathPattern '^state/successors/g(?<generation>[0-9]{4,})\.json$'
    $lineage = Read-StrictJsonObject -LiteralPath $lineagePath -Label 'legacy successor lineage'
    $lineageKeys = @('schema','project_id','control_generation','legacy_goal_bindings_obsolete','predecessor','inherited_artifact_index','inherited_counter_budget_baseline','successor')
    Assert-RequiredKeys -Object $lineage -Required $lineageKeys -Label 'legacy successor lineage' -Exact
    if ([string]$lineage.schema -cne 'math-research-legacy-successor-lineage/v8' -or [string]$lineage.project_id -cne $ProjectId -or -not (Test-JsonInteger $lineage.control_generation 1) -or [long]$lineage.control_generation -ne $ActivationGeneration -or $lineage.legacy_goal_bindings_obsolete -isnot [bool] -or -not [bool]$lineage.legacy_goal_bindings_obsolete) {
        Stop-Commit 'lineage_invalid' 'Legacy successor lineage identity, generation, or retirement flag is invalid.'
    }

    $predecessor = $lineage.predecessor
    Assert-RequiredKeys -Object $predecessor -Required @('project_head_snapshot','run_id','run_path','contract','primary_manifest','backup_manifest','checkpoint','handoff') -Label 'lineage.predecessor' -Exact
    Assert-SafeId -Value $predecessor.run_id -Label 'lineage.predecessor.run_id'
    if ([string]$predecessor.run_path -cne "runs/$([string]$predecessor.run_id)") { Stop-Commit 'lineage_invalid' 'Predecessor run path/ID mismatches.' }
    $snapshotPath = Assert-RawPointer -Pointer $predecessor.project_head_snapshot -ProjectPath $ProjectPath -Label 'lineage.predecessor.project_head_snapshot' -RequiredPattern '^state/successors/g[0-9]{4,}-predecessor-project\.json$'
    if ($FirstActivation -and [string]$predecessor.project_head_snapshot.sha256 -cne [string]$ExpectedActivationOldHash) { Stop-Commit 'lineage_invalid' 'Predecessor project snapshot is not the activation CAS expected-old bytes.' }
    $predecessorSnapshot = Read-StrictJsonObject -LiteralPath $snapshotPath -Label 'predecessor project-head snapshot'
    if ($predecessorSnapshot.active_run -isnot [Collections.IDictionary] -or $predecessorSnapshot.active_contract -isnot [Collections.IDictionary]) { Stop-Commit 'lineage_invalid' 'Old project snapshot lacks active run/Contract pointers.' }
    $snapshotRunPath = Convert-LegacyRelativePath $predecessorSnapshot.active_run.path 'snapshot active_run.path'
    $snapshotContractPath = Convert-LegacyRelativePath $predecessorSnapshot.active_contract.path 'snapshot active_contract.path'
    if ([string]$predecessorSnapshot.project_id -cne $ProjectId -or [string]$predecessorSnapshot.active_run.id -cne [string]$predecessor.run_id -or
        $snapshotRunPath -cne [string]$predecessor.run_path -or $snapshotContractPath -cne [string]$predecessor.contract.path) { Stop-Commit 'lineage_invalid' 'Lineage predecessor does not identify the active run/Contract in the exact old project snapshot.' }
    $snapshotContractHash = if ($predecessorSnapshot.active_contract.Contains('sha256')) { [string]$predecessorSnapshot.active_contract.sha256 } elseif ($predecessorSnapshot.active_contract.Contains('binding_sha256')) { [string]$predecessorSnapshot.active_contract.binding_sha256 } else { $null }
    if ($null -ne $snapshotContractHash -and $snapshotContractHash -cne [string]$predecessor.contract.sha256) { Stop-Commit 'lineage_invalid' 'Predecessor Contract hash differs from the old project snapshot.' }
    foreach ($name in @('contract','primary_manifest','backup_manifest','checkpoint','handoff')) {
        $entry = $predecessor[$name]
        if ($null -eq $entry) {
            if ($name -notin @('backup_manifest','checkpoint','handoff')) { Stop-Commit 'lineage_invalid' "Required predecessor $name pointer is null." }
            continue
        }
        $pattern = if ($name -eq 'contract') { '^contracts/' } elseif ($name -in @('primary_manifest','backup_manifest')) { '^runs/' } elseif ($name -eq 'checkpoint') { '^state/' } else { '^(?:[^/]+/|[^/]+$)' }
        $full = Assert-RawPointer -Pointer $entry -ProjectPath $ProjectPath -Label "lineage.predecessor.$name" -RequiredPattern $pattern -AllowProjectRootLeaf:($name -eq 'handoff')
        if ($name -in @('primary_manifest','backup_manifest') -and -not (Test-PathInside -Child $full -Directory (Join-Path $ProjectPath (([string]$predecessor.run_path).Replace('/', [IO.Path]::DirectorySeparatorChar))))) { Stop-Commit 'lineage_invalid' "Predecessor $name is outside its run." }
    }

    $indexPath = Assert-RawPointer -Pointer $lineage.inherited_artifact_index -ProjectPath $ProjectPath -Label 'lineage.inherited_artifact_index' -RequiredPattern '^runs/'
    $index = Read-StrictJsonObject -LiteralPath $indexPath -Label 'inherited artifact index'
    $coverage = @('problem','verified_partial_results','attempts','failures','evidence','routes','audits','handoff','source_artifacts','computation_artifacts','intermediate_artifacts')
    Assert-RequiredKeys -Object $index -Required @('schema','project_id','predecessor_run_id','source_snapshot','inventory_algorithm','covers','entries','category_counts','entry_count','complete_source_inventory') -Label 'inherited artifact index' -Exact
    if ([string]$index.schema -cne 'math-research-inherited-artifact-index/v8' -or [string]$index.project_id -cne $ProjectId -or [string]$index.predecessor_run_id -cne [string]$predecessor.run_id -or
        [string]::IsNullOrWhiteSpace([string]$index.inventory_algorithm) -or (@($index.covers) -join '|') -cne ($coverage -join '|') -or $index.complete_source_inventory -isnot [bool] -or -not [bool]$index.complete_source_inventory -or -not (Test-JsonInteger $index.entry_count 1)) { Stop-Commit 'lineage_invalid' 'Inherited artifact index identity/algorithm/coverage/completeness is invalid.' }
    $sourceSnapshot = $index.source_snapshot
    Assert-RequiredKeys -Object $sourceSnapshot -Required @('primary_manifest_sha256','backup_manifest_sha256','checkpoint_sha256','handoff_sha256','authoritative_index_heads') -Label 'inherited artifact source_snapshot' -Exact
    if ([string]$sourceSnapshot.primary_manifest_sha256 -cne [string]$predecessor.primary_manifest.sha256) { Stop-Commit 'lineage_invalid' 'Source snapshot primary manifest hash mismatches.' }
    foreach ($pair in @(@('backup_manifest','backup_manifest_sha256'),@('checkpoint','checkpoint_sha256'),@('handoff','handoff_sha256'))) {
        $predecessorPointer = $predecessor[$pair[0]]; $snapshotHash = $sourceSnapshot[$pair[1]]
        if (($null -eq $predecessorPointer -and $null -ne $snapshotHash) -or ($null -ne $predecessorPointer -and [string]$snapshotHash -cne [string]$predecessorPointer.sha256)) { Stop-Commit 'lineage_invalid' 'Nullable predecessor/source-snapshot binding mismatches.' }
    }
    if (@($sourceSnapshot.authoritative_index_heads).Count -lt 1) { Stop-Commit 'lineage_invalid' 'Source snapshot has no authoritative predecessor index head.' }
    foreach ($sourceHead in @($sourceSnapshot.authoritative_index_heads)) {
        if ([string]$sourceHead.path -cmatch '^state/(?:staging|generations)/' -or ([string]$sourceHead.path).StartsWith(([string]$ActiveRun.path + '/'),[StringComparison]::Ordinal)) { Stop-Commit 'lineage_invalid' 'Authoritative predecessor index head points into successor material.' }
        $null = Assert-RawPointer -Pointer $sourceHead -ProjectPath $ProjectPath -Label 'authoritative predecessor index head' -RequiredPattern '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf
    }
    Assert-RequiredKeys -Object $index.category_counts -Required $coverage -Label 'inherited artifact category counts' -Exact
    $sum = [decimal]0
    foreach ($category in $coverage) { if (-not (Test-JsonInteger $index.category_counts[$category] 0)) { Stop-Commit 'lineage_invalid' 'Inherited artifact category count is invalid.' }; $sum += [decimal]$index.category_counts[$category] }
    if ($sum -ne [decimal]$index.entry_count -or @($index.entries).Count -ne [int]$index.entry_count) { Stop-Commit 'lineage_invalid' 'Inherited artifact entry/count totals mismatch.' }
    $seenEntries = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $observed = @{}; foreach ($category in $coverage) { $observed[$category] = 0L }
    foreach ($entry in @($index.entries)) {
        Assert-RequiredKeys -Object $entry -Required @('category','path','sha256','evidence_grade') -Label 'inherited artifact entry' -Exact
        if ([string]$entry.category -cnotin $coverage -or [string]::IsNullOrWhiteSpace([string]$entry.evidence_grade) -or -not $seenEntries.Add("$([string]$entry.category)|$([string]$entry.path)")) { Stop-Commit 'lineage_invalid' 'Inherited artifact category/path/evidence grade is invalid or duplicated.' }
        if ([string]$entry.path -cmatch '^state/(?:staging|generations)/' -or [string]$entry.path -ceq [string]$lineage.inherited_artifact_index.path -or ([string]$entry.path).StartsWith(([string]$ActiveRun.path + '/'),[StringComparison]::OrdinalIgnoreCase)) { Stop-Commit 'lineage_invalid' 'Inherited artifact index references successor staging/current-run material.' }
        $null = Assert-RawPointer -Pointer ([ordered]@{path=$entry.path;sha256=$entry.sha256}) -ProjectPath $ProjectPath -Label 'inherited artifact entry' -RequiredPattern '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf
        $observed[[string]$entry.category]++
    }
    if ($observed.problem -lt 1) { Stop-Commit 'lineage_invalid' 'Inherited artifact index contains no predecessor problem.' }
    foreach ($category in $coverage) { if ([long]$index.category_counts[$category] -ne [long]$observed[$category]) { Stop-Commit 'lineage_invalid' 'Inherited artifact category counts do not match entries.' } }

    $baselinePath = Assert-RawPointer -Pointer $lineage.inherited_counter_budget_baseline -ProjectPath $ProjectPath -Label 'lineage.inherited_counter_budget_baseline' -RequiredPattern '^state/successor-baselines/g[0-9]{4,}\.json$'
    $baseline = Read-StrictJsonObject -LiteralPath $baselinePath -Label 'successor counter/budget baseline'
    Assert-RequiredKeys -Object $baseline -Required @('schema','project_id','predecessor_run_id','attempt_count','audit_count','total_round_count','attempts_since_last_audit','audit_due','budget_consumption') -Label 'counter/budget baseline' -Exact
    if ([string]$baseline.schema -cne 'math-research-counter-budget-baseline/v8' -or [string]$baseline.project_id -cne $ProjectId -or [string]$baseline.predecessor_run_id -cne [string]$predecessor.run_id) { Stop-Commit 'lineage_invalid' 'Counter/budget baseline identity mismatches.' }
    $baselineCounters = Get-Counters -Object ([ordered]@{attempt_count=$baseline.attempt_count;audit_count=$baseline.audit_count;total_round_count=$baseline.total_round_count;attempts_since_last_audit=$baseline.attempts_since_last_audit;audit_due=$baseline.audit_due}) -Label 'counter/budget baseline'
    $currentCounters = Get-Counters -Object ([ordered]@{counters=$StateSuccessor.__counters}) -Label 'successor state counters'
    if ($FirstActivation) {
        if (-not (Test-CountersEqual $baselineCounters $currentCounters)) { Stop-Commit 'lineage_invalid' 'Initial successor counters do not equal the inherited baseline.' }
    }
    else {
        foreach ($counterName in @('attempt_count','audit_count','total_round_count')) { if ([decimal]$currentCounters[$counterName] -lt [decimal]$baselineCounters[$counterName]) { Stop-Commit 'lineage_invalid' 'Current counters reset below the inherited baseline.' } }
    }
    Assert-RequiredKeys -Object $baseline.budget_consumption -Required @('attempt_budget_ceiling','attempts_spent','total_round_budget_ceiling','total_rounds_spent','runtime_or_other_cumulative') -Label 'baseline.budget_consumption' -Exact
    $budget = $baseline.budget_consumption
    foreach ($budgetName in @('attempt_budget_ceiling','attempts_spent','total_round_budget_ceiling','total_rounds_spent')) { if (-not (Test-JsonInteger $budget[$budgetName] 0)) { Stop-Commit 'lineage_invalid' 'Inherited budget baseline contains a nonnegative-integer violation.' } }
    if ($budget.runtime_or_other_cumulative -isnot [Collections.IDictionary] -or [long]$budget.attempts_spent -ne [long]$baseline.attempt_count -or [long]$budget.total_rounds_spent -ne [long]$baseline.total_round_count -or
        [long]$budget.attempts_spent -gt [long]$budget.attempt_budget_ceiling -or [long]$budget.total_rounds_spent -gt [long]$budget.total_round_budget_ceiling) { Stop-Commit 'lineage_invalid' 'Inherited budget consumption/counter/ceiling binding is invalid.' }

    $successor = $lineage.successor
    Assert-RequiredKeys -Object $successor -Required @('contract','run_id','run_path','run_genesis','host_bind') -Label 'lineage.successor' -Exact
    Assert-RequiredKeys -Object $successor.contract -Required @('path','binding_sha256') -Label 'lineage.successor.contract' -Exact
    if ([string]$successor.contract.path -ceq [string]$predecessor.contract.path -or [string]$successor.contract.binding_sha256 -ceq [string]$predecessor.contract.sha256) { Stop-Commit 'lineage_invalid' 'Successor v8 Contract must be distinct from the preserved predecessor Contract.' }
    if ([string]$successor.run_id -ceq [string]$predecessor.run_id -or ([string]$successor.run_path).Equals([string]$predecessor.run_path,[StringComparison]::OrdinalIgnoreCase)) { Stop-Commit 'lineage_invalid' 'Successor run must be additive and distinct from the preserved predecessor run.' }
    if ([string]$successor.run_id -cne [string]$ActiveRun.id -or [string]$successor.run_path -cne [string]$ActiveRun.path -or
        [string]$successor.contract.path -cne [string]$ActiveContract.path -or [string]$successor.contract.binding_sha256 -cne [string]$ActiveContract.binding_sha256) { Stop-Commit 'lineage_invalid' 'Lineage successor Contract/run identity mismatches the candidate head.' }
    $genesisPath = Assert-RawPointer -Pointer $successor.run_genesis -ProjectPath $ProjectPath -Label 'lineage.successor.run_genesis' -RequiredPattern '^runs/'
    $successorHostPath = Assert-RawPointer -Pointer $successor.host_bind -ProjectPath $ProjectPath -Label 'lineage.successor.host_bind' -RequiredPattern '^runs/'
    $successorRunDirectory = Join-Path $ProjectPath (([string]$successor.run_path).Replace('/',[IO.Path]::DirectorySeparatorChar))
    if ([string]$successor.run_genesis.path -cne ([string]$successor.run_path + '/run.json') -or -not (Test-PathInside -Child $successorHostPath -Directory $successorRunDirectory)) { Stop-Commit 'lineage_invalid' 'Lineage successor genesis/host binding is outside the successor run.' }
    if ($FirstActivation -and ([string]$successor.host_bind.path -cne [string]$HostBindingHead.path -or [string]$successor.host_bind.sha256 -cne [string]$HostBindingHead.sha256)) { Stop-Commit 'lineage_invalid' 'Initial lineage successor host binding is not the activation binding head.' }
    $null = $genesisPath; $null = $successorHostPath

    $summary = [ordered]@{
        lineage = [ordered]@{path=$Pointer.path;sha256=$Pointer.sha256}
        inherited_artifact_index = [ordered]@{path=$lineage.inherited_artifact_index.path;sha256=$lineage.inherited_artifact_index.sha256}
        counter_budget_baseline = [ordered]@{path=$lineage.inherited_counter_budget_baseline.path;sha256=$lineage.inherited_counter_budget_baseline.sha256}
    }
    foreach ($actual in @($StateSuccessor.__summary,$CheckpointSuccessor.__summary)) {
        Assert-RequiredKeys -Object $actual -Required @('lineage','inherited_artifact_index','counter_budget_baseline') -Label 'successor summary' -Exact
        foreach ($name in @('lineage','inherited_artifact_index','counter_budget_baseline')) { if (-not (Test-PointerEqual $actual[$name] $summary[$name] raw)) { Stop-Commit 'lineage_invalid' 'Successor summaries do not match the activated lineage.' } }
    }
}

function Assert-CandidateHead {
    param(
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Candidate,
        [Parameter(Mandatory = $true)][string]$ProjectPath,
        [Parameter(Mandatory = $true)][long]$Generation,
        [Parameter(Mandatory = $true)][string]$OldProjectId,
        [Parameter(Mandatory = $true)][string]$ExpectedOldHash,
        [Parameter(Mandatory = $true)][bool]$OldWasLegacy,
        [AllowNull()][Collections.IDictionary]$OldHead,
        [Parameter(Mandatory = $true)][string]$CandidatePath
    )
    $required = @('schema','project_id','project_identity_sha256','problem_statement_sha256','control_generation','active_checkpoint','goal_host_state','project_event_head','host_binding_head','active_contract','active_run','legacy_successor')
    Assert-RequiredKeys -Object $Candidate -Required $required -Label 'candidate project head' -Exact
    if ([string]$Candidate.schema -cne 'math-research-project/v8') { Stop-Commit 'candidate_schema_invalid' 'Candidate head schema is not exactly math-research-project/v8.' }
    Assert-SafeId -Value $Candidate.project_id -Label 'candidate project_id'
    if ([string]$Candidate.project_id -cne $OldProjectId) { Stop-Commit 'project_id_mismatch' 'Candidate project_id differs from the current head.' }
    Assert-LowerSha256 -Value $Candidate.project_identity_sha256 -Label 'candidate.project_identity_sha256'
    Assert-LowerSha256 -Value $Candidate.problem_statement_sha256 -Label 'candidate.problem_statement_sha256'
    if (-not (Test-JsonInteger $Candidate.control_generation 1) -or [long]$Candidate.control_generation -ne $Generation) { Stop-Commit 'generation_mismatch' 'Candidate control_generation differs from ExpectedNewControlGeneration.' }
    $oldWasV8 = $null -ne $OldHead -and [string]$OldHead.schema -ceq 'math-research-project/v8'
    $oldCheckpoint = $null; $oldState = $null; $oldCounters = $null
    if ($oldWasV8) {
        foreach ($identityField in @('project_identity_sha256','problem_statement_sha256','active_contract','active_run','active_checkpoint','goal_host_state','host_binding_head','legacy_successor')) {
            if (-not $OldHead.Contains($identityField)) { Stop-Commit 'old_head_invalid' "Current v8 head is missing $identityField." }
        }
        if ([string]$Candidate.project_identity_sha256 -cne [string]$OldHead.project_identity_sha256 -or [string]$Candidate.problem_statement_sha256 -cne [string]$OldHead.problem_statement_sha256) { Stop-Commit 'project_identity_mismatch' 'Project/path problem identity changed in an ordinary v8 head commit.' }
        if (-not (Test-PointerEqual $Candidate.active_contract $OldHead.active_contract contract)) { Stop-Commit 'contract_changed' 'An ordinary v8 head commit cannot replace the immutable active Contract.' }
        if ($Candidate.active_run -isnot [Collections.IDictionary] -or $OldHead.active_run -isnot [Collections.IDictionary] -or [string]$Candidate.active_run.id -cne [string]$OldHead.active_run.id -or [string]$Candidate.active_run.path -cne [string]$OldHead.active_run.path) { Stop-Commit 'run_identity_changed' 'An ordinary v8 head commit cannot replace the active run identity.' }
        if ([string]$OldHead.active_run.status -cin @('goal_continuity_terminal','superseded','closed')) { Stop-Commit 'terminal_head_immutable' 'A terminal v8 run cannot receive another project-head mutation.' }
        $oldGeneration = [long]$OldHead.control_generation
        $oldCheckpointPath = Assert-GenerationPointer -Pointer $OldHead.active_checkpoint -ProjectPath $ProjectPath -Generation $oldGeneration -Label 'old active_checkpoint' -PathPattern '^state/generations/g(?<generation>[0-9]{4,})/checkpoint\.json$'
        $oldStatePath = Assert-GenerationPointer -Pointer $OldHead.goal_host_state -ProjectPath $ProjectPath -Generation $oldGeneration -Label 'old goal_host_state' -PathPattern '^state/generations/g(?<generation>[0-9]{4,})/goal-host-v8\.json$'
        $oldCheckpoint = Read-StrictJsonObject -LiteralPath $oldCheckpointPath -Label 'old checkpoint'
        $oldState = Read-StrictJsonObject -LiteralPath $oldStatePath -Label 'old Goal-host state'
        if ($oldCheckpoint.Contains('completion_ready') -and $oldCheckpoint.Contains('pending_goal_update') -and ([bool]$oldCheckpoint.completion_ready -or [bool]$oldCheckpoint.pending_goal_update)) { Stop-Commit 'completion_head_immutable' 'A durable completion-ready head is permanently read-only.' }
        foreach ($oldRecord in @($oldCheckpoint,$oldState)) {
            if ([string]$oldRecord.project_id -cne [string]$OldHead.project_id -or [string]$oldRecord.control_generation -cne [string]$OldHead.control_generation -or -not (Test-PointerEqual $oldRecord.run $OldHead.active_run run) -or -not (Test-PointerEqual $oldRecord.contract $OldHead.active_contract contract)) { Stop-Commit 'old_head_invalid' 'Old v8 checkpoint/state cross-binding is invalid.' }
        }
        $oldCheckpointCounters = Get-Counters -Object $oldCheckpoint -Label 'old checkpoint counters'
        $oldStateCounters = Get-Counters -Object $oldState -Label 'old Goal-host counters'
        if (-not (Test-CountersEqual $oldCheckpointCounters $oldStateCounters)) { Stop-Commit 'old_head_invalid' 'Old checkpoint/state counters disagree.' }
        $oldCounters = $oldCheckpointCounters
    }

    $checkpointPath = Assert-GenerationPointer -Pointer $Candidate.active_checkpoint -ProjectPath $ProjectPath -Generation $Generation -Label 'active_checkpoint' -PathPattern '^state/generations/g(?<generation>[0-9]{4,})/checkpoint\.json$'
    $statePath = Assert-GenerationPointer -Pointer $Candidate.goal_host_state -ProjectPath $ProjectPath -Generation $Generation -Label 'goal_host_state' -PathPattern '^state/generations/g(?<generation>[0-9]{4,})/goal-host-v8\.json$'
    if ($checkpointPath.Equals($statePath, [StringComparison]::OrdinalIgnoreCase) -or $CandidatePath.Equals($checkpointPath, [StringComparison]::OrdinalIgnoreCase) -or $CandidatePath.Equals($statePath, [StringComparison]::OrdinalIgnoreCase)) { Stop-Commit 'pointer_collision' 'Candidate head collides with an immutable generation file.' }
    $eventPath = Assert-GenerationPointer -Pointer $Candidate.project_event_head -ProjectPath $ProjectPath -Generation $Generation -Label 'project_event_head' -PathPattern '^state/project-events/g(?<generation>[0-9]{4,})\.json$'
    Assert-RequiredKeys -Object $Candidate.host_binding_head -Required @('path','sha256','control_generation') -Label 'host_binding_head' -Exact
    if (-not (Test-JsonInteger $Candidate.host_binding_head.control_generation 1) -or [long]$Candidate.host_binding_head.control_generation -gt $Generation -or [string]$Candidate.host_binding_head.path -cnotmatch '^runs/[A-Za-z0-9][A-Za-z0-9._-]*/host-bindings/host-bind-g(?<generation>[0-9]{4,})\.json$' -or [long]$Matches['generation'] -ne [long]$Candidate.host_binding_head.control_generation) { Stop-Commit 'generation_mismatch' 'Host-binding head has an invalid activation generation.' }
    $hostPath = Resolve-ProjectRelativeFile -ProjectPath $ProjectPath -RelativePath $Candidate.host_binding_head.path -Label 'host_binding_head.path' -RequiredPattern '^runs/'
    Assert-LowerSha256 -Value $Candidate.host_binding_head.sha256 -Label 'host_binding_head.sha256'
    if ((Get-FileSha256 -LiteralPath $hostPath) -cne [string]$Candidate.host_binding_head.sha256) { Stop-Commit 'pointer_hash_mismatch' 'Host-binding head hash mismatches.' }
    $hostBindingChanged = $false
    if ($oldWasV8) {
        if (-not (Test-PointerEqual $Candidate.host_binding_head $OldHead.host_binding_head generation)) {
            $hostBindingChanged = $true
            if ([long]$Candidate.host_binding_head.control_generation -ne $Generation) { Stop-Commit 'host_binding_drift' 'A changed host binding must be activated in the new generation.' }
        }
    }
    elseif ([long]$Candidate.host_binding_head.control_generation -ne $Generation) { Stop-Commit 'host_binding_drift' 'Initial v8 activation requires a binding in its activation generation.' }
    $contractPath = Assert-ContractPointer -Pointer $Candidate.active_contract -ProjectPath $ProjectPath -Label 'active_contract'
    $contractBudgets = Get-ContractBudgetMetadata -ContractPath $contractPath -ProjectPath $ProjectPath -Candidate $Candidate
    $runPath = Assert-RunPointer -Pointer $Candidate.active_run -ProjectPath $ProjectPath -Label 'active_run'
    if (-not (Test-PathInside -Child $hostPath -Directory $runPath)) { Stop-Commit 'cross_binding_mismatch' 'Host-binding head is outside the active run.' }

    $checkpoint = Read-StrictJsonObject -LiteralPath $checkpointPath -Label 'candidate checkpoint'
    $state = Read-StrictJsonObject -LiteralPath $statePath -Label 'candidate Goal-host state'
    $checkpointKeys = @('schema','project_id','control_generation','contract','run','problem_statement_sha256','host_goal','host_binding_head','counters','current_lifecycle','successor','completion_ready','pending_goal_update','last_run_event','updated_at_utc')
    $stateKeys = @('schema','project_id','control_generation','contract','run','host_goal','problem_statement_sha256','successor','counters','current_ticket','updated_at_utc')
    Assert-RequiredKeys -Object $checkpoint -Required $checkpointKeys -Label 'candidate checkpoint' -Exact
    Assert-RequiredKeys -Object $state -Required $stateKeys -Label 'candidate Goal-host state' -Exact
    if ([string]$checkpoint.schema -cne 'math-research-checkpoint/v8' -or [string]$state.schema -cne 'math-research-goal-host-state/v8') { Stop-Commit 'referenced_schema_invalid' 'Checkpoint or Goal-host state schema is invalid.' }
    if (-not (Test-CurrentUtcTimestamp $checkpoint.updated_at_utc) -or -not (Test-CurrentUtcTimestamp $state.updated_at_utc) -or $checkpoint.completion_ready -isnot [bool] -or $checkpoint.pending_goal_update -isnot [bool] -or [bool]$checkpoint.completion_ready -ne [bool]$checkpoint.pending_goal_update) { Stop-Commit 'referenced_state_invalid' 'Checkpoint timestamp/completion flags are invalid; completion flags must be false/false or true/true.' }
    foreach ($record in @($checkpoint,$state)) {
        if ([string]$record.project_id -cne [string]$Candidate.project_id -or -not (Test-JsonInteger $record.control_generation 1) -or [long]$record.control_generation -ne $Generation -or [string]$record.problem_statement_sha256 -cne [string]$Candidate.problem_statement_sha256) { Stop-Commit 'cross_binding_mismatch' 'Generation state identity/problem/generation mismatches.' }
        if (-not (Test-PointerEqual $record.contract $Candidate.active_contract contract) -or -not (Test-PointerEqual $record.run $Candidate.active_run run)) { Stop-Commit 'cross_binding_mismatch' 'Generation state Contract/run mismatches the project head.' }
    }
    if (-not (Test-PointerEqual $checkpoint.host_binding_head $Candidate.host_binding_head raw) -or @($checkpoint.host_binding_head.Keys).Count -ne 2) { Stop-Commit 'cross_binding_mismatch' 'Checkpoint raw host-binding path/hash mismatches project head.' }
    if (-not (Test-HostGoalEqual $checkpoint.host_goal $state.host_goal)) { Stop-Commit 'cross_binding_mismatch' 'Checkpoint and Goal-host state bind different Goals.' }
    $checkpointCounters = Get-Counters -Object $checkpoint -Label 'checkpoint counters'
    $stateCounters = Get-Counters -Object $state -Label 'Goal-host state counters'
    if (-not (Test-CountersEqual $checkpointCounters $stateCounters)) { Stop-Commit 'cross_binding_mismatch' 'Checkpoint and Goal-host state counters differ.' }
    if ([long]$checkpointCounters.attempt_count -gt [long]$contractBudgets.attempt_budget -or [long]$checkpointCounters.total_round_count -gt [long]$contractBudgets.total_round_budget) { Stop-Commit 'budget_exhausted' 'Candidate cumulative counters exceed immutable Contract ceilings.' }
    if ([long]$checkpointCounters.attempts_since_last_audit -gt [long]$contractBudgets.audit_interval_attempts -or [bool]$checkpointCounters.audit_due -ne ([long]$checkpointCounters.attempts_since_last_audit -eq [long]$contractBudgets.audit_interval_attempts)) { Stop-Commit 'audit_gate_invalid' 'Candidate audit gate must equal the exact Contract interval threshold.' }

    $stateTicket = $state.current_ticket
    $ticketRecord = $null
    $lifecycle = $checkpoint.current_lifecycle
    if (($null -eq $stateTicket) -xor ($null -eq $lifecycle)) { Stop-Commit 'cross_binding_mismatch' 'Checkpoint lifecycle and Goal-host ticket nullability differ.' }
    if ($null -eq $stateTicket -and [string]$Candidate.active_run.status -cnotin @('completion_candidate','goal_continuity_terminal','superseded','closed')) { Stop-Commit 'ticket_invalid' 'Every open non-completion run state requires one current ticket/lifecycle pair.' }
    if ($null -ne $stateTicket) {
        Assert-RequiredKeys -Object $stateTicket -Required @('id','path','sha256','status','contract_initial_tickets_sha256','counter_snapshot','source_event') -Label 'Goal-host current_ticket' -Exact
        Assert-RequiredKeys -Object $stateTicket.counter_snapshot -Required @('attempt_count','audit_count','total_round_count') -Label 'current ticket counter snapshot' -Exact
        Assert-RequiredKeys -Object $lifecycle -Required @('kind','id','path','sha256') -Label 'checkpoint current_lifecycle' -Exact
        if ([string]$stateTicket.id -cne [string]$lifecycle.id -or [string]$stateTicket.path -cne [string]$lifecycle.path -or [string]$stateTicket.sha256 -cne [string]$lifecycle.sha256) { Stop-Commit 'cross_binding_mismatch' 'Checkpoint lifecycle and Goal-host ticket differ.' }
        if ([string]$stateTicket.status -cnotin @('frozen','ready','active','awaiting_verification','closed')) { Stop-Commit 'ticket_invalid' 'Current-ticket status is outside the closed set.' }
        $ticketPath = Assert-RawPointer -Pointer ([ordered]@{path=$stateTicket.path;sha256=$stateTicket.sha256}) -ProjectPath $ProjectPath -Label 'current ticket' -RequiredPattern '^runs/'
        if (-not (Test-PathInside -Child $ticketPath -Directory $runPath)) { Stop-Commit 'ticket_invalid' 'Current ticket is outside the active run.' }
        foreach ($counterName in @('attempt_count','audit_count','total_round_count')) { if ([string]$stateTicket.counter_snapshot[$counterName] -cne [string]$checkpointCounters[$counterName]) { Stop-Commit 'cross_binding_mismatch' 'Current-ticket counter snapshot differs from generation counters.' } }
        $ticketRecord=Read-StrictJsonObject -LiteralPath $ticketPath -Label 'frozen current ticket'
        Assert-RequiredKeys $ticketRecord @('schema','project_id','control_generation','contract','run','cycle_id','contract_initial_tickets_sha256','counter_snapshot','ticket') 'frozen current ticket' -Exact
        if([string]$ticketRecord.schema-cne'math-research-frozen-ticket/v8'-or[string]$ticketRecord.project_id-cne[string]$Candidate.project_id-or-not(Test-JsonInteger $ticketRecord.control_generation 1)-or[long]$ticketRecord.control_generation-gt$Generation-or
            -not(Test-PointerEqual $ticketRecord.contract $Candidate.active_contract contract)-or[string]$ticketRecord.run.id-cne[string]$Candidate.active_run.id-or[string]$ticketRecord.run.path-cne[string]$Candidate.active_run.path-or[string]$ticketRecord.cycle_id-cne[string]$contractBudgets.cycle_id-or
            [string]$ticketRecord.contract_initial_tickets_sha256-cne[string]$contractBudgets.metadata.initial_tickets_sha256-or-not(Test-CountersEqual (Get-Counters $ticketRecord.counter_snapshot 'frozen ticket counter snapshot') $checkpointCounters)-or[string]$ticketRecord.ticket.ticket_id-cne[string]$stateTicket.id){Stop-Commit 'ticket_invalid' 'Frozen ticket envelope identity/Contract/run/counter binding is invalid.'}
        Assert-TicketBody -Ticket $ticketRecord.ticket -ContractFacts $contractBudgets -ProjectPath $ProjectPath -ActiveRun $Candidate.active_run
        if([string]$ticketRecord.ticket.role-ceq'verifier'-and$null-eq$stateTicket.source_event){Stop-Commit 'ticket_invalid' 'A verifier ticket is valid only as a derived ticket with a source_event.'}
        if ($null -eq $stateTicket.source_event) {
            if([string]$ticketRecord.ticket.role-cne'solver'){Stop-Commit 'ticket_invalid' 'An initial source_event-null ticket must have role solver.'}
            if ([string]$lifecycle.kind -cne 'initial_ticket') { Stop-Commit 'ticket_invalid' 'A null source_event requires initial_ticket lifecycle kind.' }
            $contractTicketMatches=@($contractBudgets.initial_tickets|Where-Object{[string]$_.ticket_id-ceq[string]$stateTicket.id})
            if($contractTicketMatches.Count-ne1-or-not(Test-JsonDeepEqual $ticketRecord.ticket $contractTicketMatches[0])){Stop-Commit 'ticket_invalid' 'Initial frozen ticket must equal exactly one Contract initial-ticket member.'}
        }
        else {
            if ([string]$lifecycle.kind -cne 'frozen_ticket') { Stop-Commit 'ticket_invalid' 'A derived ticket requires frozen_ticket lifecycle kind.' }
            $ticketEventPath=Assert-RawPointer -Pointer $stateTicket.source_event -ProjectPath $ProjectPath -Label 'derived ticket source_event' -RequiredPattern '^runs/'
            if(-not(Test-PathInside -Child $ticketEventPath -Directory $runPath)){Stop-Commit 'ticket_invalid' 'Derived ticket source event is outside the active run.'}
            $ticketEvent=Read-StrictJsonObject -LiteralPath $ticketEventPath -Label 'derived ticket source event'
            Assert-RequiredKeys $ticketEvent @('schema','project_id','control_generation','event_id','ticket_id','ticket','role','contract','run','counters','input_artifacts','dependencies','updated_at_utc') 'derived ticket source event' -Exact
            Assert-SafeId $ticketEvent.event_id 'derived ticket event ID';Assert-RequiredKeys $ticketEvent.ticket @('path','sha256') 'derived ticket event ticket pointer' -Exact;Assert-RequiredKeys $ticketEvent.contract @('path','version','binding_sha256') 'derived ticket event Contract' -Exact;Assert-RequiredKeys $ticketEvent.run @('id','path') 'derived ticket event run' -Exact
            if([string]$ticketEvent.schema-cne'math-research-ticket-event/v8'-or[string]$ticketEvent.project_id-cne[string]$Candidate.project_id-or[string]$ticketEvent.control_generation-cne[string]$ticketRecord.control_generation-or[string]$ticketEvent.ticket_id-cne[string]$stateTicket.id-or
                [string]$ticketEvent.ticket.path-cne[string]$stateTicket.path-or[string]$ticketEvent.ticket.sha256-cne[string]$stateTicket.sha256-or[string]$ticketEvent.role-cne[string]$ticketRecord.ticket.role-or-not(Test-PointerEqual $ticketEvent.contract $Candidate.active_contract contract)-or
                [string]$ticketEvent.run.id-cne[string]$Candidate.active_run.id-or[string]$ticketEvent.run.path-cne[string]$Candidate.active_run.path-or-not(Test-CountersEqual (Get-Counters $ticketEvent.counters 'derived ticket event counters') $checkpointCounters)-or
                -not(Test-JsonDeepEqual $ticketEvent.input_artifacts $ticketRecord.ticket.input_artifacts)-or-not(Test-JsonDeepEqual $ticketEvent.dependencies $ticketRecord.ticket.dependencies)-or-not(Test-CurrentUtcTimestamp $ticketEvent.updated_at_utc)){Stop-Commit 'ticket_invalid' 'Derived ticket source-event bindings do not match the frozen ticket and candidate generation.'}
        }
    }
    $runTicketStatus=[string]$Candidate.active_run.status
    if($runTicketStatus-cin@('goal_continuity_terminal','superseded','closed')){if($null-ne$stateTicket){Stop-Commit 'ticket_invalid' 'Terminal, superseded, and closed runs must have null ticket/lifecycle.'}}
    elseif($null-ne$stateTicket){
        $allowedTicketStatuses=switch($runTicketStatus){
            {$_-cin@('not_started','preparing')} {@('frozen','ready');break}
            'attempt_running' {@('active');break}
            'audit_due' {@('frozen','ready');break}
            'auditing' {@('active');break}
            'completion_candidate' {@('frozen','ready','awaiting_verification');break}
            {$_-cin@('paused','awaiting_input')} {@('frozen','ready','active','awaiting_verification');break}
            default {@()}
        }
        if([string]$stateTicket.status-cnotin@($allowedTicketStatuses)){Stop-Commit 'ticket_invalid' 'Current ticket status is incompatible with the active run status.'}
        if($runTicketStatus-ceq'attempt_running'-and[string]$ticketRecord.ticket.role-cnotin@('solver','verifier')){Stop-Commit 'ticket_invalid' 'attempt_running ticket role must be solver or verifier.'}
        if($runTicketStatus-ceq'auditing'-and[string]$ticketRecord.ticket.role-cnotin@('skeptic_quantifiers','skeptic_strategy','theory_tool_scout')){Stop-Commit 'ticket_invalid' 'auditing ticket role must be one of the three audit roles.'}
    }

    $event = Read-StrictJsonObject -LiteralPath $eventPath -Label 'candidate project event'
    $hostBinding = Read-StrictJsonObject -LiteralPath $hostPath -Label 'candidate host binding'
    $eventKeys = @('schema','project_id','control_generation','event_id','event_type','updated_at_utc','previous_event_sha256','contract','run','counters','referenced_artifacts')
    Assert-RequiredKeys -Object $event -Required $eventKeys -Label 'project event' -Exact
    $eventTypes = @('RUN_GENESIS','LEGACY_SUCCESSOR','CHECKPOINT_COMMIT','ATTEMPT_START','ATTEMPT_END','AUDIT_START','AUDIT_END','HOST_REBIND','PAUSE','RESUME','COMPLETION_READY')
    Assert-SafeId -Value $event.event_id -Label 'project event_id'
    if ([string]$event.schema -cne 'math-research-project-event/v8' -or [string]$event.event_type -cnotin $eventTypes -or -not (Test-CurrentUtcTimestamp $event.updated_at_utc)) { Stop-Commit 'referenced_schema_invalid' 'Project event schema/type/timestamp is invalid.' }
    Assert-CrossBoundRecord -Record $event -Label 'project event' -ProjectId ([string]$Candidate.project_id) -Generation $Generation -Contract $Candidate.active_contract -Run $Candidate.active_run
    if (-not (Test-CountersEqual (Get-Counters -Object $event -Label 'project event counters') $checkpointCounters)) { Stop-Commit 'cross_binding_mismatch' 'Project event counter snapshot differs from the generation state.' }
    if ($oldWasV8) {
        Assert-LowerSha256 -Value $event.previous_event_sha256 -Label 'project event previous_event_sha256'
        if (-not $OldHead.Contains('project_event_head') -or [string]$event.previous_event_sha256 -cne [string]$OldHead.project_event_head.sha256) { Stop-Commit 'event_chain_invalid' 'Project event does not chain from the old authoritative event head.' }
    }
    elseif ($null -ne $event.previous_event_sha256) { Stop-Commit 'event_chain_invalid' 'First v8 activation must have null previous_event_sha256.' }
    if ($event.referenced_artifacts -isnot [Collections.IList]) { Stop-Commit 'shape_invalid' 'Project event referenced_artifacts must be a JSON array.' }
    foreach ($eventArtifact in @($event.referenced_artifacts)) {
        $artifactRelative=[string]$eventArtifact.path
        if($artifactRelative.StartsWith('state/staging/',[StringComparison]::OrdinalIgnoreCase)-or$artifactRelative.IndexOf('/staging/',[StringComparison]::OrdinalIgnoreCase)-ge0-or$artifactRelative.Equals([IO.Path]::GetRelativePath($ProjectPath,$CandidatePath).Replace('\','/'),[StringComparison]::OrdinalIgnoreCase)){Stop-Commit 'unsafe_pointer_path' 'Project event cannot publish staging or candidate-head material as authoritative evidence.'}
        $null = Assert-RawPointer -Pointer $eventArtifact -ProjectPath $ProjectPath -Label 'project event referenced artifact' -RequiredPattern '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf
    }
    $attemptOutcome=$null
    if([string]$event.event_type-ceq'ATTEMPT_END'){
        if(@($event.referenced_artifacts).Count-ne1){Stop-Commit 'attempt_outcome_invalid' 'Every ATTEMPT_END must publish exactly one immutable attempt outcome.'}
        $attemptOutcome=Assert-AttemptOutcome -Pointer $event.referenced_artifacts[0] -ProjectPath $ProjectPath -Candidate $Candidate
    }
    $oldAuditedCompletion=$null;$oldPreAuditCompletion=$null
    if($oldWasV8-and[string]$OldHead.active_run.status-ceq'completion_candidate'){
        $oldAuditedCompletion=Get-AuditedCompletionSummary -Head $OldHead -HeadGeneration ($Generation-1) -ProjectPath $ProjectPath -Candidate $Candidate -ContractFacts $contractBudgets
        if($null-eq$oldAuditedCompletion){$oldPreAuditCompletion=Get-PreAuditCompletionOutcome -Head $OldHead -HeadGeneration ($Generation-1) -ProjectPath $ProjectPath -Candidate $Candidate}
        if($null-eq$oldAuditedCompletion-and$null-eq$oldPreAuditCompletion){Stop-Commit 'attempt_outcome_invalid' 'Unaudited completion_candidate has no authoritative candidate_found ATTEMPT_END outcome chain.'}
    }
    if([string]$event.event_type-ceq'AUDIT_START'){
        if($null-eq$stateTicket-or$null-eq$ticketRecord-or[string]$ticketRecord.ticket.role-cnotin@('skeptic_quantifiers','skeptic_strategy','theory_tool_scout')){Stop-Commit 'cycle_audit_invalid' 'AUDIT_START current ticket must have one closed audit role.'}
        if(@($event.referenced_artifacts).Count-ne1){Stop-Commit 'cycle_audit_invalid' 'AUDIT_START must publish exactly one three-role cycle-audit plan.'}
        $auditKind=if([string]$OldHead.active_run.status-ceq'completion_candidate'){'terminal'}elseif([bool]$oldCounters.audit_due){'scheduled'}else{'early'}
        if($auditKind-ceq'terminal'-and$null-eq$oldPreAuditCompletion){Stop-Commit 'completion_transition_invalid' 'An already-audited completion candidate cannot start another terminal audit.'}
        $expectedAuditCandidate=if($auditKind-ceq'terminal'){$oldPreAuditCompletion.Outcome.candidate}else{$null}
        $null=Assert-CycleAuditPlan -Pointer $event.referenced_artifacts[0] -ProjectPath $ProjectPath -ProjectId ([string]$Candidate.project_id) -Contract $Candidate.active_contract -Run $Candidate.active_run -Generation $Generation -Counters $checkpointCounters -CurrentTicket $stateTicket -ContractFacts $contractBudgets -ExpectedAuditKind $auditKind -ExpectedCandidate $expectedAuditCandidate
    }
    if([string]$event.event_type-ceq'AUDIT_END'){
        if(@($event.referenced_artifacts).Count-ne1){Stop-Commit 'cycle_audit_invalid' 'Every AUDIT_END must publish exactly one cycle-audit summary.'}
        $summaryPath=Assert-RawPointer $event.referenced_artifacts[0] $ProjectPath 'cycle-audit summary' '^(?:[^/]+/|[^/]+$)' -AllowProjectRootLeaf;$summaryPreview=Read-StrictJsonObject $summaryPath 'cycle-audit summary preview';$auditKind=[string]$summaryPreview.audit_kind
        if($auditKind-cnotin@('scheduled','early','terminal')-or([string]$Candidate.active_run.status-ceq'completion_candidate'-and$auditKind-cne'terminal')-or($auditKind-cne'terminal'-and[string]$Candidate.active_run.status-ceq'completion_candidate')){Stop-Commit 'cycle_audit_invalid' 'AUDIT_END status and cycle-audit kind are incompatible.'}
        $summaryResult=Assert-CycleAuditSummary -Pointer $event.referenced_artifacts[0] -ProjectPath $ProjectPath -Candidate $Candidate -ExpectedAuditKind $auditKind
        $null=Assert-CycleAuditHistory -SummaryResult $summaryResult -EndEvent $event -EndGeneration $Generation -ProjectPath $ProjectPath -Candidate $Candidate -ContractFacts $contractBudgets
        if($auditKind-ceq'terminal'){
            if([bool]$summaryResult.AllPass){
                if([string]$Candidate.active_run.status-cne'completion_candidate'-or$null-ne$stateTicket){Stop-Commit 'cycle_audit_invalid' 'Three-PASS terminal AUDIT_END must return one null-ticket completion_candidate.'}
            }
            elseif([string]$Candidate.active_run.status-cnotin@('preparing','awaiting_input')){Stop-Commit 'cycle_audit_invalid' 'A terminal audit with FAIL/INCONCLUSIVE cannot preserve completion_candidate.'}
        }
    }
    if($null-ne$oldAuditedCompletion){
        if([string]$event.event_type-cnotin@('COMPLETION_READY','HOST_REBIND')-or@($event.referenced_artifacts).Count-ne1-or-not(Test-PointerEqual $event.referenced_artifacts[0] $oldAuditedCompletion.Pointer raw)-or$null-ne$stateTicket){Stop-Commit 'completion_transition_invalid' 'An audited-completion head permits only COMPLETION_READY or certificate-preserving HOST_REBIND with null ticket.'}
    }
    elseif($null-ne$oldPreAuditCompletion){
        if([string]$event.event_type-ceq'HOST_REBIND'){
            if([string]$Candidate.active_run.status-cne'completion_candidate'-or@($event.referenced_artifacts).Count-ne1-or-not(Test-PointerEqual $event.referenced_artifacts[0] $oldPreAuditCompletion.Pointer raw)){Stop-Commit 'attempt_outcome_invalid' 'Pre-audit completion HOST_REBIND must preserve and republish the exact attempt outcome.'}
        }
        elseif([string]$event.event_type-cne'AUDIT_START'){Stop-Commit 'attempt_outcome_invalid' 'Pre-audit completion permits only its locked terminal AUDIT_START or outcome-preserving HOST_REBIND.'}
    }
    elseif([string]$event.event_type-ceq'COMPLETION_READY'){Stop-Commit 'completion_transition_invalid' 'COMPLETION_READY requires one authoritative terminal AUDIT_END certificate.'}
    $oldPauseCapsule=$null
    if($oldWasV8-and[string]$OldHead.active_run.status-ceq'paused'){$oldPauseCapsule=Get-PausedResumeCapsule $OldHead ($Generation-1) $ProjectPath $Candidate $oldState.current_ticket $oldCheckpoint.current_lifecycle $oldCounters}
    if($oldWasV8-and[string]$OldHead.active_run.status-ceq'paused'-and[string]$event.event_type-cnotin@('RESUME','HOST_REBIND')){Stop-Commit 'resume_capsule_invalid' 'A paused head permits only exact capsule-bound RESUME or capsule-preserving HOST_REBIND.'}
    if([string]$event.event_type-ceq'PAUSE'){
        if([string]$Candidate.active_run.status-cne'paused'-or[string]$OldHead.active_run.status-cnotin@('attempt_running','auditing')-or$null-eq$stateTicket-or[string]$stateTicket.status-cne'active'-or-not(Test-JsonDeepEqual $stateTicket $oldState.current_ticket)-or-not(Test-JsonDeepEqual $lifecycle $oldCheckpoint.current_lifecycle)-or-not(Test-CountersEqual $checkpointCounters $oldCounters)-or@($event.referenced_artifacts).Count-ne1){Stop-Commit 'resume_capsule_invalid' 'PAUSE must preserve one active ticket/lifecycle/counters and publish exactly one resume capsule.'}
        $null=Assert-ResumeCapsule $event.referenced_artifacts[0] $ProjectPath $Candidate $stateTicket $lifecycle $checkpointCounters ([string]$OldHead.active_run.status)
    }
    if([string]$event.event_type-ceq'HOST_REBIND'-and[string]$OldHead.active_run.status-ceq'paused'){
        if($null-eq$oldPauseCapsule-or@($event.referenced_artifacts).Count-ne1-or-not(Test-PointerEqual $event.referenced_artifacts[0] $oldPauseCapsule.Pointer raw)){Stop-Commit 'resume_capsule_invalid' 'HOST_REBIND while paused must republish the unchanged resume capsule.'}
    }
    if([string]$event.event_type-ceq'RESUME'){
        if([string]$OldHead.active_run.status-ceq'paused'){
            if($null-eq$oldPauseCapsule-or[string]$Candidate.active_run.status-cne[string]$oldPauseCapsule.Capsule.prior_status-or@($event.referenced_artifacts).Count-ne1-or-not(Test-PointerEqual $event.referenced_artifacts[0] $oldPauseCapsule.Pointer raw)-or-not(Test-JsonDeepEqual $stateTicket $oldPauseCapsule.Capsule.ticket)-or-not(Test-JsonDeepEqual $lifecycle $oldPauseCapsule.Capsule.lifecycle)-or-not(Test-CountersEqual $checkpointCounters $oldCounters)){Stop-Commit 'resume_capsule_invalid' 'RESUME must restore the exact paused ticket/lifecycle/counters/prior status from its capsule.'}
        }
        elseif([string]$OldHead.active_run.status-ceq'awaiting_input'){
            $expectedAwaitingStatuses=if([bool]$checkpointCounters.audit_due){@('audit_due')}else{@('not_started','preparing')}
            if([string]$Candidate.active_run.status-cnotin$expectedAwaitingStatuses-or@($event.referenced_artifacts).Count-ne0){Stop-Commit 'resume_capsule_invalid' 'awaiting_input RESUME has no pause capsule and must route exactly according to its durable audit_due gate.'}
        }
    }
    if (-not (Test-PointerEqual $checkpoint.last_run_event ([ordered]@{id=$event.event_id;sha256=$Candidate.project_event_head.sha256}) raw)) {
        if ($checkpoint.last_run_event -isnot [Collections.IDictionary] -or -not $checkpoint.last_run_event.Contains('id') -or -not $checkpoint.last_run_event.Contains('sha256') -or [string]$checkpoint.last_run_event.id -cne [string]$event.event_id -or [string]$checkpoint.last_run_event.sha256 -cne [string]$Candidate.project_event_head.sha256) { Stop-Commit 'cross_binding_mismatch' 'Checkpoint last_run_event does not bind the active project event.' }
    }
    $hostKeys = @('schema','project_id','control_generation','event_type','prior_host_binding','retirement','contract','run','host_goal')
    Assert-RequiredKeys -Object $hostBinding -Required $hostKeys -Label 'host binding' -Exact
    Assert-RequiredKeys -Object $hostBinding.contract -Required @('path','version','binding_sha256') -Label 'host binding contract' -Exact
    Assert-RequiredKeys -Object $hostBinding.run -Required @('id','path') -Label 'host binding run' -Exact
    if ([string]$hostBinding.schema -cne 'math-research-host-binding/v8' -or [string]$hostBinding.project_id -cne [string]$Candidate.project_id -or
        -not (Test-JsonInteger $hostBinding.control_generation 1) -or [long]$hostBinding.control_generation -ne [long]$Candidate.host_binding_head.control_generation -or
        -not (Test-PointerEqual $hostBinding.contract $Candidate.active_contract contract) -or [string]$hostBinding.run.id -cne [string]$Candidate.active_run.id -or [string]$hostBinding.run.path -cne [string]$Candidate.active_run.path) { Stop-Commit 'cross_binding_mismatch' 'Host-binding project/generation/Contract/run identity mismatches.' }
    if (-not (Test-HostGoalEqual $hostBinding.host_goal $state.host_goal)) { Stop-Commit 'cross_binding_mismatch' 'Host binding and generation state bind different Goals.' }
    if ([string]$hostBinding.event_type -ceq 'HOST_BIND') {
        if ($null -ne $hostBinding.prior_host_binding -or $null -ne $hostBinding.retirement -or $hostBindingChanged) { Stop-Commit 'host_binding_drift' 'HOST_BIND must be the unchained initial binding.' }
    }
    elseif ([string]$hostBinding.event_type -ceq 'HOST_REBIND') {
        Assert-RequiredKeys -Object $hostBinding.prior_host_binding -Required @('path','sha256','control_generation') -Label 'HOST_REBIND prior_host_binding' -Exact
        Assert-RequiredKeys -Object $hostBinding.retirement -Required @('authority','reason') -Label 'HOST_REBIND retirement' -Exact
        Assert-LowerSha256 -Value $hostBinding.prior_host_binding.sha256 -Label 'HOST_REBIND prior_host_binding.sha256'
        if (-not (Test-JsonInteger $hostBinding.prior_host_binding.control_generation 1) -or [long]$hostBinding.prior_host_binding.control_generation -ge [long]$hostBinding.control_generation -or
            [string]$hostBinding.retirement.authority -cne 'user-explicit-revocation' -or [string]::IsNullOrWhiteSpace([string]$hostBinding.retirement.reason)) { Stop-Commit 'host_binding_drift' 'HOST_REBIND has an invalid prior generation or retirement authority.' }
        $priorHostPath = Resolve-ProjectRelativeFile -ProjectPath $ProjectPath -RelativePath $hostBinding.prior_host_binding.path -Label 'HOST_REBIND prior_host_binding.path' -RequiredPattern '^runs/'
        if ((Get-FileSha256 -LiteralPath $priorHostPath) -cne [string]$hostBinding.prior_host_binding.sha256 -or -not (Test-PathInside -Child $priorHostPath -Directory $runPath)) { Stop-Commit 'host_binding_drift' 'HOST_REBIND prior binding path/hash is invalid.' }
        if ($hostBindingChanged -and -not (Test-PointerEqual $hostBinding.prior_host_binding $OldHead.host_binding_head generation)) { Stop-Commit 'host_binding_drift' 'New HOST_REBIND does not chain from the old active binding.' }
    }
    else {
        Stop-Commit 'host_binding_drift' 'Host-binding event_type is outside HOST_BIND/HOST_REBIND.'
    }

    if ($oldWasV8) {
        if ($hostBindingChanged -ne ([string]$event.event_type -ceq 'HOST_REBIND')) { Stop-Commit 'host_binding_drift' 'A changed host-binding head and the HOST_REBIND project event must occur together.' }
        foreach ($counterName in @('attempt_count','audit_count','total_round_count')) { if ([long]$checkpointCounters[$counterName] -lt [long]$oldCounters[$counterName]) { Stop-Commit 'counter_rollback' 'Cumulative attempt/audit/round counters cannot decrease.' } }
        $isAuditEnd = [string]$event.event_type -ceq 'AUDIT_END'
        $isAuditStart = [string]$event.event_type -ceq 'AUDIT_START'
        $isAttemptStart = [string]$event.event_type -ceq 'ATTEMPT_START'
        $attemptDelta = [long]$checkpointCounters.attempt_count - [long]$oldCounters.attempt_count
        $auditDelta = [long]$checkpointCounters.audit_count - [long]$oldCounters.audit_count
        $totalDelta = [long]$checkpointCounters.total_round_count - [long]$oldCounters.total_round_count
        $oldStatus=[string]$OldHead.active_run.status;$newStatus=[string]$Candidate.active_run.status;$eventType=[string]$event.event_type
        if ($isAttemptStart) {
            if ([bool]$oldCounters.audit_due -or [long]$oldCounters.attempt_count -ge [long]$contractBudgets.attempt_budget -or [long]$oldCounters.total_round_count -ge [long]$contractBudgets.total_round_budget) { Stop-Commit 'attempt_start_forbidden' 'ATTEMPT_START is forbidden by an audit gate or exhausted Contract budget.' }
            $newSince=[long]$oldCounters.attempts_since_last_audit+1
            if ($attemptDelta -ne 1 -or $auditDelta -ne 0 -or $totalDelta -ne 1 -or [long]$checkpointCounters.attempts_since_last_audit -ne $newSince -or [bool]$checkpointCounters.audit_due -ne ($newSince -eq [long]$contractBudgets.audit_interval_attempts)) { Stop-Commit 'counter_transition_invalid' 'ATTEMPT_START must consume exactly one attempt/round and set the exact interval gate.' }
            if(([long]$oldCounters.total_round_count+2)-gt[long]$contractBudgets.total_round_budget){Stop-Commit 'attempt_start_forbidden' 'ATTEMPT_START must preserve one remaining round for a possible terminal or scheduled audit.'}
            if($oldStatus-cnotin@('not_started','preparing')-or$newStatus-cne'attempt_running'-or$null-eq$stateTicket-or$null-eq$stateTicket.source_event-or[string]$stateTicket.status-cne'active'-or[string]$lifecycle.kind-cne'frozen_ticket'-or[string]$ticketRecord.ticket.role-cne'solver'){Stop-Commit 'lifecycle_transition_invalid' 'ATTEMPT_START must enter attempt_running with one active derived solver ticket.'}
        }
        elseif ($isAuditStart) {
            if ([long]$oldCounters.total_round_count -ge [long]$contractBudgets.total_round_budget) { Stop-Commit 'audit_start_forbidden' 'AUDIT_START is forbidden by exhausted total-round budget.' }
            if ($attemptDelta -ne 0 -or $auditDelta -ne 1 -or $totalDelta -ne 1 -or [long]$checkpointCounters.attempts_since_last_audit -ne [long]$oldCounters.attempts_since_last_audit -or [bool]$checkpointCounters.audit_due-ne[bool]$oldCounters.audit_due) { Stop-Commit 'counter_transition_invalid' 'AUDIT_START must consume exactly one audit/round without changing attempt counters or the gate.' }
            if($oldStatus-cnotin@('not_started','preparing','audit_due','completion_candidate')-or$newStatus-cne'auditing'-or$null-eq$stateTicket-or$null-eq$stateTicket.source_event-or[string]$stateTicket.status-cne'active'-or[string]$lifecycle.kind-cne'frozen_ticket'){Stop-Commit 'lifecycle_transition_invalid' 'AUDIT_START must enter auditing with one active derived ticket.'}
        }
        elseif ($attemptDelta -ne 0 -or $auditDelta -ne 0 -or $totalDelta -ne 0) { Stop-Commit 'counter_transition_invalid' 'Only ATTEMPT_START/AUDIT_START may change global counters or total rounds.' }
        if($isAuditEnd){if([long]$checkpointCounters.attempts_since_last_audit-ne0-or[bool]$checkpointCounters.audit_due){Stop-Commit 'audit_gate_rollback' 'AUDIT_END must reset attempts_since_last_audit to zero and clear audit_due.'}}
        elseif(-not$isAttemptStart-and([long]$checkpointCounters.attempts_since_last_audit-ne[long]$oldCounters.attempts_since_last_audit-or[bool]$checkpointCounters.audit_due-ne[bool]$oldCounters.audit_due)){Stop-Commit 'audit_gate_transition_invalid' 'Only ATTEMPT_START may advance the gate and only AUDIT_END may reset it.'}
        switch($eventType){
            'ATTEMPT_END' {
                $attemptOutcomeKind=[string]$attemptOutcome.Record.outcome
                $outcomeStatusInvalid=if($attemptOutcomeKind-ceq'candidate_found'){
                    $newStatus-cne'completion_candidate'
                }elseif([bool]$checkpointCounters.audit_due){
                    $newStatus-cne'audit_due'
                }elseif($attemptOutcomeKind-ceq'awaiting_input'){
                    $newStatus-cne'awaiting_input'
                }else{
                    $newStatus-cnotin@('not_started','preparing')
                }
                if($attemptOutcomeKind-ceq'candidate_found'-and($null-eq$stateTicket-or$null-eq$stateTicket.source_event-or$null-eq$ticketRecord-or[string]$ticketRecord.ticket.role-cne'verifier'-or[string]$stateTicket.id-cne[string]$attemptOutcome.VerifierTicketId-or-not(Test-PointerEqual $ticketRecord.ticket.candidate_artifact $attemptOutcome.Record.candidate raw))){Stop-Commit 'attempt_outcome_invalid' 'candidate_found must close the current derived verifier ticket on exactly its bound candidate.'}
                if($oldStatus-cne'attempt_running'-or$outcomeStatusInvalid-or($null-ne$stateTicket-and[string]$stateTicket.status-ceq'active')){Stop-Commit 'lifecycle_transition_invalid' 'ATTEMPT_END must enter the exact state dictated by its verified outcome and durable audit gate; PAUSE is a separate capsule-bound event.'}
            }
            'AUDIT_END' { if($oldStatus-cne'auditing'-or$newStatus-cnotin@('not_started','preparing','awaiting_input','completion_candidate')-or($null-ne$stateTicket-and[string]$stateTicket.status-ceq'active')){Stop-Commit 'lifecycle_transition_invalid' 'AUDIT_END must leave auditing with a reset gate; PAUSE is a separate capsule-bound event.'} }
            'PAUSE' { if($newStatus-cne'paused'){Stop-Commit 'lifecycle_transition_invalid' 'PAUSE must enter paused.'} }
            'RESUME' {
                $samePausedAttempt=$false
                if([bool]$checkpointCounters.audit_due-and$newStatus-ceq'attempt_running'-and$null-ne$oldState.current_ticket-and$null-ne$stateTicket-and[string]$oldState.current_ticket.status-ceq'active'-and[string]$stateTicket.status-ceq'active'-and[string]$oldState.current_ticket.id-ceq[string]$stateTicket.id){
                    $oldResumeTicketPath=Assert-RawPointer ([ordered]@{path=$oldState.current_ticket.path;sha256=$oldState.current_ticket.sha256}) $ProjectPath 'paused active ticket' '^runs/';$oldResumeTicket=Read-StrictJsonObject $oldResumeTicketPath 'paused active frozen ticket';$samePausedAttempt=Test-JsonDeepEqual $oldResumeTicket.ticket $ticketRecord.ticket
                }
                if($oldStatus-cnotin@('paused','awaiting_input')-or$newStatus-cnotin@('not_started','preparing','attempt_running','audit_due','auditing')-or([bool]$checkpointCounters.audit_due-and$newStatus-ceq'attempt_running'-and-not$samePausedAttempt)-or([bool]$checkpointCounters.audit_due-and$newStatus-cnotin@('attempt_running','audit_due','auditing'))){Stop-Commit 'lifecycle_transition_invalid' 'RESUME has an invalid run-status/audit-gate transition.'}
            }
            'CHECKPOINT_COMMIT' { if($newStatus-cne$oldStatus){Stop-Commit 'lifecycle_transition_invalid' 'CHECKPOINT_COMMIT cannot change run status.'} }
            'HOST_REBIND' { if($newStatus-cne$oldStatus){Stop-Commit 'lifecycle_transition_invalid' 'HOST_REBIND cannot change run status.'} }
            'COMPLETION_READY' { if($oldStatus-cne'completion_candidate'-or$newStatus-cne'closed'-or-not[bool]$checkpoint.completion_ready-or$null-ne$stateTicket-or@($event.referenced_artifacts).Count-lt1-or[bool]$checkpointCounters.audit_due){Stop-Commit 'completion_transition_invalid' 'COMPLETION_READY requires an audited completion candidate, closed run, null lifecycle, durable flags, and referenced evidence.'} }
            'RUN_GENESIS' { Stop-Commit 'lifecycle_transition_invalid' 'RUN_GENESIS is only valid for absent-head activation.' }
            'LEGACY_SUCCESSOR' { Stop-Commit 'lifecycle_transition_invalid' 'LEGACY_SUCCESSOR is only valid for legacy first activation.' }
        }
        if([bool]$checkpoint.completion_ready-and$eventType-cne'COMPLETION_READY'){Stop-Commit 'completion_transition_invalid' 'Durable completion flags can be set only by COMPLETION_READY.'}
        if(-not[bool]$checkpoint.completion_ready-and$eventType-ceq'COMPLETION_READY'){Stop-Commit 'completion_transition_invalid' 'COMPLETION_READY must set both durable completion flags.'}
        $hostLifecycleChanged=($null-eq$oldCheckpoint.current_lifecycle)-ne($null-eq$checkpoint.current_lifecycle)
        $hostTicketChanged=($null-eq$oldState.current_ticket)-ne($null-eq$state.current_ticket)
        if(-not$hostLifecycleChanged-and$null-ne$oldCheckpoint.current_lifecycle){$hostLifecycleChanged=[string]$oldCheckpoint.current_lifecycle.kind-cne[string]$checkpoint.current_lifecycle.kind-or[string]$oldCheckpoint.current_lifecycle.id-cne[string]$checkpoint.current_lifecycle.id}
        if(-not$hostTicketChanged-and$null-ne$oldState.current_ticket){$hostTicketChanged=[string]$oldState.current_ticket.id-cne[string]$state.current_ticket.id-or[string]$oldState.current_ticket.status-cne[string]$state.current_ticket.status-or[string]$oldState.current_ticket.contract_initial_tickets_sha256-cne[string]$state.current_ticket.contract_initial_tickets_sha256-or-not(Test-JsonDeepEqual $oldState.current_ticket.counter_snapshot $state.current_ticket.counter_snapshot)}
        if ($hostBindingChanged -and (
            -not (Test-CountersEqual $oldCounters $checkpointCounters) -or [string]$Candidate.active_run.status -cne [string]$OldHead.active_run.status -or
            $hostLifecycleChanged -or $hostTicketChanged -or
            -not (Test-JsonDeepEqual $oldCheckpoint.successor $checkpoint.successor) -or [bool]$oldCheckpoint.completion_ready -ne [bool]$checkpoint.completion_ready -or
            [bool]$oldCheckpoint.pending_goal_update -ne [bool]$checkpoint.pending_goal_update)) { Stop-Commit 'host_rebind_state_changed' 'HOST_REBIND must preserve counters, ticket/lifecycle, successor, completion flags, and run status exactly.' }
        if($hostBindingChanged){
            if(($null-eq$oldState.current_ticket)-ne($null-eq$state.current_ticket)-or($null-ne$oldState.current_ticket-and(($null-eq$oldState.current_ticket.source_event)-ne($null-eq$state.current_ticket.source_event)))){Stop-Commit 'host_rebind_state_changed' 'HOST_REBIND cannot change ticket kind/nullability.'}
            if($null-ne$oldState.current_ticket){
                $oldTicketPath=Assert-RawPointer -Pointer ([ordered]@{path=$oldState.current_ticket.path;sha256=$oldState.current_ticket.sha256}) -ProjectPath $ProjectPath -Label 'old current ticket' -RequiredPattern '^runs/'
                $oldTicketRecord=Read-StrictJsonObject -LiteralPath $oldTicketPath -Label 'old frozen current ticket'
                if(-not(Test-JsonDeepEqual $oldTicketRecord.ticket $ticketRecord.ticket)-or[string]$oldTicketRecord.cycle_id-cne[string]$ticketRecord.cycle_id-or[string]$oldTicketRecord.contract_initial_tickets_sha256-cne[string]$ticketRecord.contract_initial_tickets_sha256){Stop-Commit 'host_rebind_state_changed' 'HOST_REBIND cannot change frozen research ticket semantics.'}
            }
        }
        if ([string]$OldHead.active_run.status -ceq 'completion_candidate' -and [string]$Candidate.active_run.status -cnotin @('completion_candidate','closed') -and -not ([string]$event.event_type -ceq 'AUDIT_START' -and [string]$Candidate.active_run.status -ceq 'auditing')) { Stop-Commit 'run_status_rollback' 'completion_candidate can only remain pending, enter its terminal audit, or close durably.' }
    }

    $runGenesisPath = Join-Path $runPath 'run.json'
    Assert-NoReparsePointChain -LiteralPath $runGenesisPath
    $runGenesis = Read-StrictJsonObject -LiteralPath $runGenesisPath -Label 'active RUN_GENESIS'
    Assert-RequiredKeys -Object $runGenesis -Required @('schema','project_id','control_generation','contract','run','host_binding','host_goal') -Label 'RUN_GENESIS' -Exact
    Assert-RequiredKeys -Object $runGenesis.contract -Required @('path','version','binding_sha256') -Label 'RUN_GENESIS.contract' -Exact
    Assert-RequiredKeys -Object $runGenesis.run -Required @('id','path','status') -Label 'RUN_GENESIS.run' -Exact
    if ([string]$runGenesis.schema -cne 'math-research-run-genesis/v8' -or [string]$runGenesis.project_id -cne [string]$Candidate.project_id -or
        -not (Test-JsonInteger $runGenesis.control_generation 1) -or [long]$runGenesis.control_generation -gt $Generation -or
        -not (Test-PointerEqual $runGenesis.contract $Candidate.active_contract contract) -or [string]$runGenesis.run.status -cnotin @('not_started','preparing') -or
        [string]$runGenesis.run.id -cne [string]$Candidate.active_run.id -or [string]$runGenesis.run.path -cne [string]$Candidate.active_run.path) {
        Stop-Commit 'cross_binding_mismatch' 'RUN_GENESIS project/generation/Contract/run identity mismatches the active run.'
    }
    $genesisHostPath = Assert-RawPointer -Pointer $runGenesis.host_binding -ProjectPath $ProjectPath -Label 'RUN_GENESIS.host_binding' -RequiredPattern '^runs/'
    if (-not (Test-PathInside -Child $genesisHostPath -Directory $runPath)) { Stop-Commit 'cross_binding_mismatch' 'RUN_GENESIS host binding is outside the active run.' }
    $genesisHost = Read-StrictJsonObject -LiteralPath $genesisHostPath -Label 'RUN_GENESIS initial host binding'
    Assert-RequiredKeys -Object $genesisHost -Required @('schema','project_id','control_generation','event_type','prior_host_binding','retirement','contract','run','host_goal') -Label 'RUN_GENESIS initial host binding' -Exact
    Assert-RequiredKeys -Object $genesisHost.contract -Required @('path','version','binding_sha256') -Label 'RUN_GENESIS host-binding contract' -Exact
    Assert-RequiredKeys -Object $genesisHost.run -Required @('id','path') -Label 'RUN_GENESIS host-binding run' -Exact
    if ([string]$genesisHost.schema -cne 'math-research-host-binding/v8' -or [string]$genesisHost.event_type -cne 'HOST_BIND' -or
        $null -ne $genesisHost.prior_host_binding -or $null -ne $genesisHost.retirement -or [string]$genesisHost.project_id -cne [string]$Candidate.project_id -or
        [string]$genesisHost.control_generation -cne [string]$runGenesis.control_generation -or -not (Test-PointerEqual $genesisHost.contract $Candidate.active_contract contract) -or
        [string]$genesisHost.run.id -cne [string]$Candidate.active_run.id -or [string]$genesisHost.run.path -cne [string]$Candidate.active_run.path -or
        -not (Test-HostGoalEqual $genesisHost.host_goal $runGenesis.host_goal)) { Stop-Commit 'cross_binding_mismatch' 'RUN_GENESIS does not bind one canonical immutable initial HOST_BIND.' }
    if (-not $oldWasV8 -and (-not (Test-PointerEqual $runGenesis.host_binding $Candidate.host_binding_head raw) -or -not (Test-HostGoalEqual $runGenesis.host_goal $state.host_goal))) {
        Stop-Commit 'cross_binding_mismatch' 'First v8 activation RUN_GENESIS/HOST_BIND/host_goal does not equal the activated binding head.'
    }
    $null = $contractPath

    $stateSummary = [ordered]@{__summary=$state.successor;__counters=$stateCounters}
    $checkpointSummary = [ordered]@{__summary=$checkpoint.successor;__counters=$checkpointCounters}
    if ($OldWasLegacy) {
        if ($null -eq $Candidate.legacy_successor -or $null -eq $state.successor -or $null -eq $checkpoint.successor) { Stop-Commit 'lineage_required' 'A legacy-to-v8 activation requires an immutable successor lineage and both summaries.' }
        Assert-LegacySuccessor -Pointer $Candidate.legacy_successor -ProjectPath $ProjectPath -ProjectId ([string]$Candidate.project_id) -ActivationGeneration $Generation -ExpectedActivationOldHash $ExpectedOldHash -FirstActivation $true -ActiveContract $Candidate.active_contract -ActiveRun $Candidate.active_run -HostBindingHead $Candidate.host_binding_head -StateSuccessor $stateSummary -CheckpointSuccessor $checkpointSummary
        if ([string]$contractBudgets.run_origin -cne 'legacy_successor' -or [string]$contractBudgets.inherited_counter_budget_baseline_sha256 -cne [string]$checkpoint.successor.counter_budget_baseline.sha256 -or
            [string]$event.event_type -cne 'LEGACY_SUCCESSOR' -or [string]$Candidate.active_run.status -cnotin @('not_started','preparing') -or [string]$lifecycle.kind -cne 'initial_ticket' -or [bool]$checkpoint.completion_ready) {
            Stop-Commit 'first_activation_invalid' 'Legacy first activation must bind the inherited baseline and begin with LEGACY_SUCCESSOR in an initial run state.'
        }
    }
    elseif ($oldWasV8) {
        if ($null -eq $OldHead.legacy_successor) {
            if ($null -ne $Candidate.legacy_successor -or $null -ne $state.successor -or $null -ne $checkpoint.successor) { Stop-Commit 'lineage_drift' 'An ordinary fresh-v8 commit cannot invent a legacy successor lineage.' }
        }
        else {
            if ($null -eq $Candidate.legacy_successor -or -not (Test-PointerEqual $Candidate.legacy_successor $OldHead.legacy_successor generation)) { Stop-Commit 'lineage_drift' 'The immutable legacy-successor activation pointer changed after activation.' }
            if ($null -eq $state.successor -or $null -eq $checkpoint.successor) { Stop-Commit 'lineage_invalid' 'Activated successor lineage is missing its generation summaries.' }
            Assert-LegacySuccessor -Pointer $Candidate.legacy_successor -ProjectPath $ProjectPath -ProjectId ([string]$Candidate.project_id) -ActivationGeneration ([long]$Candidate.legacy_successor.control_generation) -ExpectedActivationOldHash $null -FirstActivation $false -ActiveContract $Candidate.active_contract -ActiveRun $Candidate.active_run -HostBindingHead $Candidate.host_binding_head -StateSuccessor $stateSummary -CheckpointSuccessor $checkpointSummary
        }
    }
    else {
        if ($null -ne $Candidate.legacy_successor -or $null -ne $state.successor -or $null -ne $checkpoint.successor) { Stop-Commit 'lineage_drift' 'An absent-head genesis cannot claim a legacy successor lineage.' }
        if ([string]$contractBudgets.run_origin -cne 'fresh' -or [string]$contractBudgets.inherited_counter_budget_baseline_sha256 -cne 'null' -or
            [string]$event.event_type -cne 'RUN_GENESIS' -or [string]$Candidate.active_run.status -cnotin @('not_started','preparing') -or [string]$lifecycle.kind -cne 'initial_ticket' -or
            [long]$checkpointCounters.attempt_count -ne 0 -or [long]$checkpointCounters.audit_count -ne 0 -or [long]$checkpointCounters.total_round_count -ne 0 -or
            [long]$checkpointCounters.attempts_since_last_audit -ne 0 -or [bool]$checkpointCounters.audit_due -or [bool]$checkpoint.completion_ready) {
            Stop-Commit 'first_activation_invalid' 'Absent-head genesis must be a zero-counter fresh RUN_GENESIS with no inherited baseline or lineage.'
        }
    }
}

function Get-OldHeadFacts {
    param([Parameter(Mandatory = $true)][Collections.IDictionary]$Old, [Parameter(Mandatory = $true)][string]$ExpectedGeneration)
    Assert-RequiredKeys -Object $Old -Required @('schema','project_id') -Label 'current project head'
    Assert-SafeId -Value $Old.project_id -Label 'current project_id'
    if ([string]$Old.schema -ceq 'math-research-project/v8') {
        if (-not (Test-JsonInteger $Old.control_generation 1)) { Stop-Commit 'old_generation_invalid' 'Current v8 head has no valid control_generation.' }
        if ([decimal]$Old.control_generation -ge [decimal][long]::MaxValue) { Stop-Commit 'old_generation_invalid' 'Current v8 control_generation cannot be incremented safely.' }
        $parsedExpected = 0L
        if ($ExpectedGeneration -cnotmatch '^[1-9][0-9]*$' -or -not [long]::TryParse($ExpectedGeneration,[ref]$parsedExpected) -or $parsedExpected -ne [long]$Old.control_generation) { Stop-Commit 'stale_generation' 'Expected old generation does not match the current v8 head.' }
        return [pscustomobject]@{ Legacy=$false; RequiresLineage=$false; Generation=[long]$Old.control_generation; NextGeneration=([long]$Old.control_generation + 1); ProjectId=[string]$Old.project_id }
    }
    $hasLegacyContract = $Old.Contains('active_contract') -and $null -ne $Old.active_contract
    $hasLegacyRun = $Old.Contains('active_run') -and $null -ne $Old.active_run
    if ($hasLegacyContract -xor $hasLegacyRun) { Stop-Commit 'old_head_invalid' 'A non-v8 head has only one of active_contract/active_run.' }
    if (-not $hasLegacyContract) { Stop-Commit 'old_head_unsupported' 'An existing pointerless pre-v8 head cannot be activated; fresh genesis requires absent project.json.' }
    $requiresLineage = $true
    if ($Old.Contains('control_generation')) {
        if (-not (Test-JsonInteger $Old.control_generation 0) -or [decimal]$Old.control_generation -ge [decimal][long]::MaxValue) { Stop-Commit 'old_generation_invalid' 'Legacy control_generation must be a safely incrementable nonnegative JSON integer.' }
        $legacyGeneration = [long]$Old.control_generation
        $parsedExpected = 0L
        if ($ExpectedGeneration -cnotmatch '^(?:0|[1-9][0-9]*)$' -or -not [long]::TryParse($ExpectedGeneration,[ref]$parsedExpected) -or $parsedExpected -ne $legacyGeneration) { Stop-Commit 'stale_generation' 'Expected old generation does not match the legacy head.' }
        return [pscustomobject]@{ Legacy=$true; RequiresLineage=$requiresLineage; Generation=$legacyGeneration; NextGeneration=($legacyGeneration + 1); ProjectId=[string]$Old.project_id }
    }
    if ($ExpectedGeneration -cnotin @('0','none')) { Stop-Commit 'stale_generation' 'A generationless legacy head requires ExpectedOldControlGeneration 0 or none.' }
    return [pscustomobject]@{ Legacy=$true; RequiresLineage=$requiresLineage; Generation=$null; NextGeneration=1L; ProjectId=[string]$Old.project_id }
}

try {
    $absentGenesis = [string]$ExpectedOldSha256 -ceq 'absent'
    if (-not $absentGenesis) { Assert-LowerSha256 -Value $ExpectedOldSha256 -Label 'ExpectedOldSha256' }
    if ($ExpectedOldControlGeneration -cnotmatch '^(?:none|0|[1-9][0-9]*)$') { Stop-Commit 'expected_generation_invalid' 'ExpectedOldControlGeneration must be none, 0, or a positive decimal integer.' }
    if ($ExpectedNewControlGeneration -lt 1) { Stop-Commit 'expected_generation_invalid' 'ExpectedNewControlGeneration must be positive.' }
    if ($ProjectDirectory -match '[\\/]\.{1,2}(?:[\\/]|$)') { Stop-Commit 'unsafe_project_path' 'ProjectDirectory contains a dot segment.' }
    $projectPath = [IO.Path]::GetFullPath($ProjectDirectory).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
    if (-not (Test-Path -LiteralPath $projectPath -PathType Container)) { Stop-Commit 'project_missing' 'ProjectDirectory is missing.' }
    Assert-NoReparsePointChain -LiteralPath $projectPath
    $migrationFreezePath = Join-Path $projectPath 'state\migration-freeze-v10.json'
    if (Test-Path -LiteralPath $migrationFreezePath) {
        Stop-Commit 'v8_migrated_frozen' 'This v8 archive is frozen by an additive v10 migration. Continue only in the successor named by state/migration-freeze-v10.json.'
    }
    $projectJsonPath = [IO.Path]::GetFullPath((Join-Path $projectPath 'project.json'))
    if ((Split-Path -Parent $projectJsonPath) -cne $projectPath) { Stop-Commit 'unsafe_project_path' 'project.json is not a direct child of ProjectDirectory.' }
    if ($absentGenesis) {
        if ($ExpectedOldControlGeneration -cne '0') { Stop-Commit 'expected_generation_invalid' 'An absent-head genesis requires ExpectedOldControlGeneration 0.' }
        if (Test-Path -LiteralPath $projectJsonPath) { Stop-Commit 'stale_hash' 'Expected an absent project head, but project.json already exists.' }
        if ($ExpectedNewControlGeneration -ne 1) { Stop-Commit 'generation_transition_invalid' 'An absent-head genesis must activate generation 1.' }
    }
    else {
        if (-not (Test-Path -LiteralPath $projectJsonPath -PathType Leaf)) { Stop-Commit 'project_head_missing' 'project.json must be a direct child of ProjectDirectory.' }
        Assert-NoReparsePointChain -LiteralPath $projectJsonPath
    }
    $result.project_json = $projectJsonPath

    if ($CandidateHeadFile -match '[\\/]\.{1,2}(?:[\\/]|$)') { Stop-Commit 'unsafe_candidate_path' 'CandidateHeadFile contains a dot segment.' }
    $candidatePath = [IO.Path]::GetFullPath($CandidateHeadFile)
    if (-not (Test-Path -LiteralPath $candidatePath -PathType Leaf)) { Stop-Commit 'candidate_missing' 'CandidateHeadFile is missing.' }
    Assert-NoReparsePointChain -LiteralPath $candidatePath
    if (-not (Test-PathInside -Child $candidatePath -Directory $projectPath)) { Stop-Commit 'unsafe_candidate_path' 'CandidateHeadFile is outside the project.' }
    $candidateRelative = [IO.Path]::GetRelativePath($projectPath, $candidatePath).Replace('\','/')
    if ($candidateRelative -cnotmatch '^state/(?:staging(?:/[A-Za-z0-9._-]+)+|generations/g[0-9]{4,}(?:/[A-Za-z0-9._-]+)+)$' -or $candidateRelative -notmatch '\.json$') { Stop-Commit 'unsafe_candidate_path' 'CandidateHeadFile must be one safe JSON file under state/staging or state/generations/gNNNN.' }

    $candidateBytes = [IO.File]::ReadAllBytes($candidatePath)
    $candidateHash = Get-BytesSha256 $candidateBytes
    $result.candidate_sha256 = $candidateHash
    $candidate = ConvertFrom-StrictJsonBytes -Bytes $candidateBytes -Label 'candidate project head'
    $old = $null
    if ($absentGenesis) {
        Assert-RequiredKeys -Object $candidate -Required @('project_id') -Label 'candidate project head'
        Assert-SafeId -Value $candidate.project_id -Label 'candidate project_id'
        $oldFacts = [pscustomobject]@{ Legacy=$false; RequiresLineage=$false; Generation=$null; NextGeneration=1L; ProjectId=[string]$candidate.project_id }
        $result.old_sha256 = $null
        $result.old_control_generation = $null
    }
    else {
        $oldBytes = [IO.File]::ReadAllBytes($projectJsonPath)
        $oldHash = Get-BytesSha256 $oldBytes
        $result.old_sha256 = $oldHash
        if ($oldHash -cne $ExpectedOldSha256) { Stop-Commit 'stale_hash' 'ExpectedOldSha256 does not match the current project head.' }
        $old = ConvertFrom-StrictJsonBytes -Bytes $oldBytes -Label 'current project head'
        $oldFacts = Get-OldHeadFacts -Old $old -ExpectedGeneration $ExpectedOldControlGeneration
        $result.old_control_generation = $oldFacts.Generation
        if ($ExpectedNewControlGeneration -ne [long]$oldFacts.NextGeneration) {
            Stop-Commit 'generation_transition_invalid' 'A generationless legacy head starts at 1; otherwise the head advances by exactly one.'
        }
    }
    Assert-CandidateHead -Candidate $candidate -ProjectPath $projectPath -Generation $ExpectedNewControlGeneration -OldProjectId $oldFacts.ProjectId -ExpectedOldHash $ExpectedOldSha256 -OldWasLegacy $oldFacts.RequiresLineage -OldHead $old -CandidatePath $candidatePath

    $mutexSeed = [Text.UTF8Encoding]::new($false).GetBytes($projectPath.ToUpperInvariant())
    $mutexName = 'Local\MathResearchHeadV8_' + (Get-BytesSha256 $mutexSeed)
    $createdNew = $false
    $mutex = [Threading.Mutex]::new($false, $mutexName, [ref]$createdNew)
    $lockHeld = $false
    $tempPath = $null
    try {
        try { $lockHeld = $mutex.WaitOne([TimeSpan]::FromSeconds(30)) }
        catch [Threading.AbandonedMutexException] { $lockHeld = $true }
        if (-not $lockHeld) { Stop-Commit 'mutex_timeout' 'Timed out waiting for the project-head commit mutex.' }

        $lockedOld = $null
        if ($absentGenesis) {
            if (Test-Path -LiteralPath $projectJsonPath) { Stop-Commit 'stale_hash' 'project.json appeared before the absent-head CAS acquired its lock.' }
            $lockedFacts = $oldFacts
        }
        else {
            $lockedOldBytes = [IO.File]::ReadAllBytes($projectJsonPath)
            $lockedOldHash = Get-BytesSha256 $lockedOldBytes
            if ($lockedOldHash -cne $ExpectedOldSha256) { Stop-Commit 'stale_hash' 'Project head changed before the CAS lock was acquired.' }
            $lockedOld = ConvertFrom-StrictJsonBytes -Bytes $lockedOldBytes -Label 'locked current project head'
            $lockedFacts = Get-OldHeadFacts -Old $lockedOld -ExpectedGeneration $ExpectedOldControlGeneration
            if ([bool]$lockedFacts.Legacy -ne [bool]$oldFacts.Legacy -or [bool]$lockedFacts.RequiresLineage -ne [bool]$oldFacts.RequiresLineage -or [string]$lockedFacts.ProjectId -cne [string]$oldFacts.ProjectId) { Stop-Commit 'stale_generation' 'Current project-head identity changed before commit.' }
        }
        if ((Get-FileSha256 -LiteralPath $candidatePath) -cne $candidateHash) { Stop-Commit 'candidate_changed' 'CandidateHeadFile changed before commit.' }
        $lockedCandidateBytes = [IO.File]::ReadAllBytes($candidatePath)
        if ((Get-BytesSha256 $lockedCandidateBytes) -cne $candidateHash) { Stop-Commit 'candidate_changed' 'CandidateHeadFile changed during its locked read.' }
        $lockedCandidate = ConvertFrom-StrictJsonBytes -Bytes $lockedCandidateBytes -Label 'locked candidate project head'
        Assert-CandidateHead -Candidate $lockedCandidate -ProjectPath $projectPath -Generation $ExpectedNewControlGeneration -OldProjectId $lockedFacts.ProjectId -ExpectedOldHash $ExpectedOldSha256 -OldWasLegacy $lockedFacts.RequiresLineage -OldHead $lockedOld -CandidatePath $candidatePath
        if ($absentGenesis) {
            if (Test-Path -LiteralPath $projectJsonPath) { Stop-Commit 'stale_hash' 'project.json appeared immediately before absent-head activation.' }
        }
        elseif ((Get-FileSha256 -LiteralPath $projectJsonPath) -cne $ExpectedOldSha256) { Stop-Commit 'stale_hash' 'Project head changed immediately before atomic replacement.' }

        $tempPath = Join-Path $projectPath ('.project.json.' + [guid]::NewGuid().ToString('N') + '.tmp')
        $stream = [IO.FileStream]::new($tempPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None, 4096, [IO.FileOptions]::WriteThrough)
        try {
            $stream.Write($lockedCandidateBytes, 0, $lockedCandidateBytes.Length)
            $stream.Flush($true)
        }
        finally { $stream.Dispose() }
        if ((Get-FileSha256 -LiteralPath $tempPath) -cne $candidateHash) { Stop-Commit 'temp_verification_failed' 'Durably flushed temporary head bytes do not match the candidate.' }
        if ($absentGenesis) { [IO.File]::Move($tempPath, $projectJsonPath) }
        else { [IO.File]::Move($tempPath, $projectJsonPath, $true) }
        $tempPath = $null

        $postVerifyFailure = $null
        try {
            # Post-move verification begins here; production behavior has no test hook.
            $committedBytes = [IO.File]::ReadAllBytes($projectJsonPath)
            $committedHash = Get-BytesSha256 $committedBytes
            $committedObject = ConvertFrom-StrictJsonBytes -Bytes $committedBytes -Label 'committed project head'
            if ($committedHash -cne $candidateHash -or [string]$committedObject.schema -cne 'math-research-project/v8' -or [long]$committedObject.control_generation -ne $ExpectedNewControlGeneration) { throw 'Committed head failed exact hash/JSON/generation verification.' }
        }
        catch { $postVerifyFailure = $_.Exception.Message }
        if ($null -ne $postVerifyFailure) {
            $liveHash = try { if (Test-Path -LiteralPath $projectJsonPath -PathType Leaf) { Get-FileSha256 -LiteralPath $projectJsonPath } else { $null } } catch { $null }
            $recoveryRelative = 'head-commit-recovery-' + [guid]::NewGuid().ToString('N') + '.json'
            $recoveryPath = Join-Path $projectPath $recoveryRelative
            Assert-NoReparsePointChain -LiteralPath $projectPath
            $recoveryObject = [ordered]@{schema='math-research-head-commit-recovery/v8';project_id=[string]$candidate.project_id;expected_old_sha256=if($absentGenesis){$null}else{$ExpectedOldSha256};candidate_sha256=$candidateHash;observed_live_sha256=$liveHash;reason=$postVerifyFailure;created_at_utc=[DateTime]::UtcNow.ToString('o')}
            $recoveryBytes = [Text.UTF8Encoding]::new($false).GetBytes(($recoveryObject | ConvertTo-Json -Compress) + "`n")
            $recoveryStream = [IO.FileStream]::new($recoveryPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read,4096,[IO.FileOptions]::WriteThrough)
            try { $recoveryStream.Write($recoveryBytes,0,$recoveryBytes.Length); $recoveryStream.Flush($true) }
            finally { $recoveryStream.Dispose() }
            Stop-Commit 'post_commit_state_indeterminate' "Post-move verification failed. No automatic rollback was attempted because project-head CAS is cooperative and a non-cooperating writer could race rollback. Recovery artifact: $recoveryRelative"
        }
        $result.committed = $true
        $result.reason = 'committed'
        $result.new_sha256 = $committedHash
        $result.new_control_generation = $ExpectedNewControlGeneration
    }
    finally {
        if ($null -ne $tempPath -and (Test-Path -LiteralPath $tempPath -PathType Leaf)) { Remove-Item -LiteralPath $tempPath -Force -ErrorAction SilentlyContinue }
        if ($lockHeld) { try { $mutex.ReleaseMutex() } catch {} }
        $mutex.Dispose()
    }
}
catch {
    $message = $_.Exception.Message
    if ($message -match '^\[(?<code>[a-z0-9_]+)\]\s*(?<detail>.*)$') {
        $result.reason = $Matches['code']
        $result.detail = $Matches['detail']
    }
    else {
        $result.reason = 'io_or_runtime_failure'
        $result.detail = $message
    }
}

$result | ConvertTo-Json -Depth 8 -Compress
if (-not [bool]$result.committed) { exit 1 }
