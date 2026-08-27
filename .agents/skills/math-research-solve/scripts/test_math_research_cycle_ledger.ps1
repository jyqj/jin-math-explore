[CmdletBinding()]
param(
    [string]$TestRoot = (Join-Path ([IO.Path]::GetTempPath()) ("math-research-cycle-tests-" + [Guid]::NewGuid().ToString('N')))
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)

$modulePath = Join-Path $PSScriptRoot 'MathResearchCycleLedger.psm1'
Import-Module $modulePath -Force -DisableNameChecking
Import-Module (Join-Path $PSScriptRoot 'MathResearchProjectArchive.psm1') -Force -DisableNameChecking

$passed = 0
$failed = 0

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

function Assert-Throws {
    param([scriptblock]$Action, [string]$Message)
    $threw = $false
    try { & $Action | Out-Null } catch { $threw = $true }
    if (-not $threw) { throw $Message }
}

function Invoke-Test {
    param([string]$Name, [scriptblock]$Action)
    try {
        & $Action
        $script:passed++
        Write-Host "PASS $Name"
    }
    catch {
        $script:failed++
        Write-Host "FAIL $Name :: $($_.Exception.Message)"
    }
}

function Write-Utf8Fixture {
    param([string]$Path, [string]$Text)
    [IO.File]::WriteAllText($Path, $Text, [Text.UTF8Encoding]::new($false))
}

function New-PolicyObject {
    param([int]$Total = 8, [int]$Attempts = 5, [int]$Interval = 2)
    return [ordered]@{
        schema_version = 1
        protocol = 'math-research-cycle-policy/v1'
        total_round_budget = $Total
        attempt_budget = $Attempts
        audit_interval_attempts = $Interval
        max_route_family_attempts_per_cycle = 2
        max_repair_batches_per_attempt = 1
        audit_roles = @('skeptic_quantifiers', 'skeptic_strategy', 'theory_tool_scout')
    }
}

function New-Ticket {
    param([string]$Id, [string]$Route = 'route-a', [string]$Mechanism = 'mechanism-a')
    return [ordered]@{
        ticket_id = $Id
        route_family_id = $Route
        mechanism_id = $Mechanism
        bottleneck_id = 'bottleneck-a'
        decision_question = "Decide $Id."
        search_domain = 'one frozen bounded domain'
        success_signal = 'one inspectable artifact'
        stop_signal = 'stop at the declared cap'
        resource_caps = [ordered]@{ child_agents = 1; tool_calls = 4; wall_minutes = 5 }
        reopen_condition = 'a pre-registered changed obligation'
    }
}

function New-TestRun {
    param(
        [string]$Name,
        [Collections.IDictionary]$Policy = (New-PolicyObject),
        [object[]]$Tickets = @((New-Ticket -Id 'C1-A1'), (New-Ticket -Id 'C1-A2' -Mechanism 'mechanism-b'), (New-Ticket -Id 'C1-A3' -Mechanism 'mechanism-c'))
    )
    $run = Join-Path $TestRoot $Name
    New-Item -ItemType Directory -Path $run | Out-Null
    $policyPath = Join-Path $run 'cycle-policy.json'
    $ticketsPath = Join-Path $run 'cycle-tickets-000.json'
    Write-Utf8Fixture -Path $policyPath -Text ($Policy | ConvertTo-Json -Depth 32)
    $manifest = [ordered]@{ schema_version = 1; cycle_id = 'cycle-1'; tickets = @($Tickets) }
    Write-Utf8Fixture -Path $ticketsPath -Text ($manifest | ConvertTo-Json -Depth 32)
    $contract = ('a' * 64)
    Initialize-MathResearchCycleLedger -RunDirectory $run -RunId $Name -ContractSha256 $contract -PolicyFile $policyPath -TicketsFile $ticketsPath | Out-Null
    return $run
}

function Write-AttemptArtifact {
    param([string]$Run, [string]$Name)
    $path = Join-Path $Run $Name
    Write-Utf8Fixture -Path $path -Text "artifact $Name"
    return $path
}

function Write-AuditTicket {
    param([string]$Run, [string]$AuditId, [string]$Trigger = 'scheduled')
    $state = Verify-MathResearchCycleLedger -RunDirectory $Run
    $path = Join-Path $Run "$AuditId-ticket.json"
    $ticket = [ordered]@{
        schema_version = 1
        audit_id = $AuditId
        trigger = $Trigger
        snapshot_head_sha256 = $state.HeadPayloadSha256
        contract_binding_sha256 = $state.ContractBindingSha256
        read_only = $true
        roles = @('skeptic_quantifiers', 'skeptic_strategy', 'theory_tool_scout')
        resource_caps = [ordered]@{ agent_turns_per_role = 1; tool_calls_per_role = 3; wall_minutes = 5; sources = 5 }
    }
    Write-Utf8Fixture -Path $path -Text ($ticket | ConvertTo-Json -Depth 32)
    return $path
}

function Write-AuditResult {
    param([string]$Run, [string]$AuditId, [string]$Snapshot, [string]$Action = 'continue', [string[]]$Verdicts = @('PASS','PASS','PASS'))
    $roles = @('skeptic_quantifiers', 'skeptic_strategy', 'theory_tool_scout')
    $reports = @()
    for ($i = 0; $i -lt 3; $i++) {
        $artifactPath = Join-Path $Run "$AuditId-$($roles[$i]).md"
        Write-Utf8Fixture -Path $artifactPath -Text "report $($roles[$i])"
        $reports += [ordered]@{ role=$roles[$i]; verdict=$Verdicts[$i]; artifact_file=[IO.Path]::GetRelativePath($Run,$artifactPath); artifact_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $artifactPath).Hash.ToLowerInvariant() }
    }
    $path = Join-Path $Run "$AuditId-result.json"
    $result = [ordered]@{
        schema_version = 1
        audit_id = $AuditId
        snapshot_head_sha256 = $Snapshot
        contract_binding_sha256 = ('a' * 64)
        new_math_performed = $false
        reports = $reports
        synthesis = [ordered]@{ action=$Action; blocking_findings=@(); quarantined_leads=@() }
    }
    Write-Utf8Fixture -Path $path -Text ($result | ConvertTo-Json -Depth 32)
    return $path
}

function Write-NextTickets {
    param([string]$Run, [string]$AuditId, [int]$Cycle = 2)
    $path = Join-Path $Run ("cycle-tickets-{0:D3}.json" -f ($Cycle - 1))
    $manifest = [ordered]@{ schema_version=1; cycle_id="cycle-$Cycle"; source_audit_id=$AuditId; tickets=@((New-Ticket -Id "C$Cycle-A1" -Route 'route-b' -Mechanism 'mechanism-next')) }
    Write-Utf8Fixture -Path $path -Text ($manifest | ConvertTo-Json -Depth 32)
    return $path
}

function New-ProjectTestRun {
    param([string]$Name, [switch]$FreezeRoute)
    $vault = Join-Path $TestRoot ("vault-$Name")
    New-Item -ItemType Directory -Path $vault -Force | Out-Null
    $projectName = "project-$Name"
    $projectId = "project-$Name-0001"
    Initialize-MathResearchProjectArchive -VaultRoot $vault -ProjectDirectoryName $projectName -ProjectId $projectId -ProblemStatement 'Prove T.' | Out-Null
    $project = Join-Path $vault ("笔记草稿\公开问题的尝试\$projectName")
    $run = Join-Path $project ("runs\$Name")
    New-Item -ItemType Directory -Path $run | Out-Null
    $resourceCaps = [ordered]@{ child_agents=1; tool_calls=4; wall_minutes=5 }
    $routeMaterial = [ordered]@{ route_id='route-a'; route_family_id='family-a'; mechanism_id='mechanism-a'; decision_problem='Decide C1-A1.'; frozen_domain='one frozen bounded domain'; resource_caps=$resourceCaps }
    $fingerprint = Get-MathResearchRouteFingerprint -Ticket $routeMaterial
    $ticket = [ordered]@{
        route_id='route-a'; route_fingerprint_sha256=$fingerprint; ticket_id='C1-A1'; route_family_id='family-a'; mechanism_id='mechanism-a'; bottleneck_id='bottleneck-a'
        decision_question='Decide C1-A1.'; search_domain='one frozen bounded domain'; success_signal='one inspectable artifact'; stop_signal='stop at the declared cap'; resource_caps=$resourceCaps; reopen_condition='new-global-lemma'
    }
    if ($FreezeRoute) {
        $registry = [ordered]@{ schema=1; project_id=$projectId; routes=@([ordered]@{ route_id='route-a'; route_family_id='family-a'; retry_fingerprint_sha256=$fingerprint; status='frozen'; reopen_condition_ids=@('new-global-lemma'); seen_evidence_sha256=@() }) }
        Write-Utf8Fixture -Path (Join-Path $project 'state\route-registry.json') -Text ($registry | ConvertTo-Json -Depth 20)
    }
    $policy = [ordered]@{ schema_version=2; protocol='math-research-cycle-policy/v2'; total_round_budget=3; attempt_budget=1; audit_interval_attempts=1; max_route_family_attempts_per_cycle=2; max_repair_batches_per_attempt=1; audit_roles=@('skeptic_quantifiers','skeptic_strategy','theory_tool_scout') }
    $manifest = [ordered]@{ schema_version=2; cycle_id='cycle-1'; tickets=@($ticket) }
    $policyPath = Join-Path $run 'cycle-policy.json'; $ticketsPath = Join-Path $run 'cycle-tickets-000.json'
    Write-Utf8Fixture -Path $policyPath -Text ($policy | ConvertTo-Json -Depth 20)
    Write-Utf8Fixture -Path $ticketsPath -Text ($manifest | ConvertTo-Json -Depth 20)
    Initialize-MathResearchCycleLedger -RunDirectory $run -RunId $Name -ContractSha256 ('a' * 64) -PolicyFile $policyPath -TicketsFile $ticketsPath | Out-Null
    return [pscustomobject]@{ Run=$run; Project=$project; Ticket=$ticket; Fingerprint=$fingerprint }
}

function New-V6ProjectTestRun {
    param([string]$Name, [string]$AttemptKind = 'route_execution', [object[]]$SourceClaims = @())
    $vault = Join-Path $TestRoot ("vault-v6-$Name")
    New-Item -ItemType Directory -Path $vault -Force | Out-Null
    $projectName = "project-v6-$Name"
    $projectId = "project-v6-$Name-0001"
    Initialize-MathResearchProjectArchive -VaultRoot $vault -ProjectDirectoryName $projectName -ProjectId $projectId -ProblemStatement 'Prove T.' | Out-Null
    $project = Join-Path $vault ("笔记草稿\公开问题的尝试\$projectName")
    $run = Join-Path $project ("runs\$Name")
    New-Item -ItemType Directory -Path $run | Out-Null
    $resourceCaps = [ordered]@{ child_agents=1; tool_calls=6; wall_minutes=5 }
    $routeMaterial = [ordered]@{ route_id='route-v6'; route_family_id='family-v6'; mechanism_id='mechanism-v6'; decision_problem='Decide the v6 claim.'; frozen_domain='one frozen v6 domain'; resource_caps=$resourceCaps }
    $fingerprint = Get-MathResearchRouteFingerprint -Ticket $routeMaterial
    $ticket = [ordered]@{
        attempt_kind=$AttemptKind; route_id='route-v6'; route_fingerprint_sha256=$fingerprint; ticket_id='C1-A1'; route_family_id='family-v6'; mechanism_id='mechanism-v6'; bottleneck_id='bottleneck-v6'
        decision_question='Decide the v6 claim.'; search_domain='one frozen v6 domain'; success_signal='one inspectable v6 artifact'; stop_signal='stop at the v6 cap'; resource_caps=$resourceCaps; reopen_condition='new-v6-evidence'
    }
    if ($SourceClaims.Count -gt 0) { $ticket.source_claims = @($SourceClaims) }
    $policy = [ordered]@{ schema_version=3; protocol='math-research-cycle-policy/v3'; total_round_budget=4; attempt_budget=2; audit_interval_attempts=1; max_route_family_attempts_per_cycle=2; max_repair_batches_per_attempt=1; audit_roles=@('skeptic_quantifiers','skeptic_strategy','theory_tool_scout') }
    $manifest = [ordered]@{ schema_version=3; cycle_id='cycle-1'; tickets=@($ticket) }
    $policyPath = Join-Path $run 'cycle-policy.json'; $ticketsPath = Join-Path $run 'cycle-tickets-000.json'
    Write-Utf8Fixture -Path $policyPath -Text ($policy | ConvertTo-Json -Depth 30)
    Write-Utf8Fixture -Path $ticketsPath -Text ($manifest | ConvertTo-Json -Depth 30)
    Initialize-MathResearchCycleLedger -RunDirectory $run -RunId $Name -ContractSha256 ('a' * 64) -PolicyFile $policyPath -TicketsFile $ticketsPath | Out-Null
    return [pscustomobject]@{ Run=$run; Project=$project; Ticket=$ticket; Fingerprint=$fingerprint }
}

function Write-V6AttemptRecord {
    param(
        [string]$Run,
        [string]$Artifact,
        [string]$AttemptKind = 'route_execution',
        [int]$RepairBatches = 0,
        [string[]]$Verdicts = @('PASS'),
        [switch]$NoVerification,
        [switch]$ReuseSolverAsVerifier,
        [string]$RoutePortfolio,
        [object[]]$SourceClaims = @()
    )
    $artifactHash = (Get-FileHash -LiteralPath $Artifact -Algorithm SHA256).Hash.ToLowerInvariant()
    $solver = Join-Path $Run 'solver.md'
    Write-Utf8Fixture -Path $solver -Text 'solver report'
    $solverHash = (Get-FileHash -LiteralPath $solver -Algorithm SHA256).Hash.ToLowerInvariant()
    $verification = @()
    if (-not $NoVerification) {
        for ($i=0; $i -lt $Verdicts.Count; $i++) {
            $candidateHash = if ($i -eq $Verdicts.Count - 1) { $artifactHash } else { ('b' * 64) }
            $verifier = if ($ReuseSolverAsVerifier) { $solver } else { Join-Path $Run ("verification-$i.md") }
            if (-not $ReuseSolverAsVerifier) { Write-Utf8Fixture -Path $verifier -Text "verification $i" }
            $verification += [ordered]@{ candidate_sha256=$candidateHash; verdict=$Verdicts[$i]; artifact_file=[IO.Path]::GetRelativePath($Run,$verifier); artifact_sha256=(Get-FileHash -LiteralPath $verifier -Algorithm SHA256).Hash.ToLowerInvariant(); new_math_performed=$false }
        }
    }
    $portfolioValue = $null
    if (-not [string]::IsNullOrWhiteSpace($RoutePortfolio)) { $portfolioValue = [ordered]@{ file=[IO.Path]::GetRelativePath($Run,$RoutePortfolio); sha256=(Get-FileHash -LiteralPath $RoutePortfolio -Algorithm SHA256).Hash.ToLowerInvariant() } }
    $record = [ordered]@{
        schema_version=1; attempt_id='attempt-0001'; ticket_id='C1-A1'; attempt_kind=$AttemptKind; decision_question='Decide the v6 claim.'
        solver_reports=@([ordered]@{ file=[IO.Path]::GetRelativePath($Run,$solver); sha256=$solverHash })
        verification_reports=@($verification); repair_batches=$RepairBatches
        result_artifact=[ordered]@{ file=[IO.Path]::GetRelativePath($Run,$Artifact); sha256=$artifactHash }
        route_portfolio=$portfolioValue; source_claims=@($SourceClaims)
    }
    $path = Join-Path $Run 'attempt-record.json'
    Write-Utf8Fixture -Path $path -Text ($record | ConvertTo-Json -Depth 30)
    return $path
}

function Write-V6RoutePortfolio {
    param([string]$Run)
    $card = [ordered]@{ card_id='card-1'; route_id='route-card'; route_family_id='family-card'; mechanism_id='mechanism-card'; bottleneck_id='bottleneck-card'; decision_question='Decide the accepted card.'; search_domain='bounded card domain'; success_signal='card result'; stop_signal='card cap'; reopen_condition='new-card-evidence' }
    $portfolio = [ordered]@{ schema_version=1; source_attempt_id='attempt-0001'; routes=@($card) }
    $path = Join-Path $Run 'route-portfolio.json'
    Write-Utf8Fixture -Path $path -Text ($portfolio | ConvertTo-Json -Depth 20)
    $launcher = Get-Module MathResearchLauncher -All | Select-Object -First 1
    $cardHash = & $launcher { param($value) Get-Sha256HexFromText -Text (ConvertTo-CanonicalJson -InputObject $value) } $card
    return [pscustomobject]@{ Path=$path; Card=$card; CardSha256=$cardHash }
}

function Write-V6AuditResult {
    param([string]$Run, [string]$Snapshot, [object[]]$AcceptedRouteCards=@(), [string]$Action='continue')
    $roles=@('skeptic_quantifiers','skeptic_strategy','theory_tool_scout'); $reports=@()
    foreach($role in $roles){ $path=Join-Path $Run "audit-1-$role.md"; Write-Utf8Fixture -Path $path -Text "report $role"; $reports += [ordered]@{ role=$role; verdict='PASS'; artifact_file=[IO.Path]::GetRelativePath($Run,$path); artifact_sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() } }
    $result=[ordered]@{ schema_version=2; audit_id='audit-1'; snapshot_head_sha256=$Snapshot; contract_binding_sha256=('a'*64); new_math_performed=$false; reports=$reports; synthesis=[ordered]@{ action=$Action; blocking_findings=@(); quarantined_leads=@(); accepted_route_cards=@($AcceptedRouteCards) } }
    $path=Join-Path $Run 'audit-1-result.json'; Write-Utf8Fixture -Path $path -Text ($result|ConvertTo-Json -Depth 30); return $path
}

function Write-V6NextTicketsFromCard {
    param([string]$Run, $Card, [string]$CardSha256, [switch]$Tamper)
    $caps=[ordered]@{child_agents=1;tool_calls=6;wall_minutes=5}
    $decision=if($Tamper){'Changed after audit.'}else{[string]$Card.decision_question}
    $material=[ordered]@{route_id=[string]$Card.route_id;route_family_id=[string]$Card.route_family_id;mechanism_id=[string]$Card.mechanism_id;decision_problem=$decision;frozen_domain=[string]$Card.search_domain;resource_caps=$caps}
    $ticket=[ordered]@{attempt_kind='route_execution';route_id=[string]$Card.route_id;route_fingerprint_sha256=(Get-MathResearchRouteFingerprint -Ticket $material);ticket_id='C2-A1';route_family_id=[string]$Card.route_family_id;mechanism_id=[string]$Card.mechanism_id;bottleneck_id=[string]$Card.bottleneck_id;decision_question=$decision;search_domain=[string]$Card.search_domain;success_signal=[string]$Card.success_signal;stop_signal=[string]$Card.stop_signal;resource_caps=$caps;reopen_condition=[string]$Card.reopen_condition;source_route_card=[ordered]@{source_attempt_id='attempt-0001';card_sha256=$CardSha256}}
    $manifest=[ordered]@{schema_version=3;cycle_id='cycle-2';source_audit_id='audit-1';tickets=@($ticket)}
    $path=Join-Path $Run 'cycle-tickets-001.json';Write-Utf8Fixture -Path $path -Text ($manifest|ConvertTo-Json -Depth 30);return $path
}

$fullRoot = [IO.Path]::GetFullPath($TestRoot)
New-Item -ItemType Directory -Path $fullRoot -Force | Out-Null
$launcherModule = Get-Module MathResearchLauncher -All | Select-Object -First 1
if ($null -eq $launcherModule) { throw 'MathResearchLauncher dependency module was not loaded.' }
$testKeyPath = Join-Path $fullRoot 'manifest-key.dpapi'
& $launcherModule { param($path) $script:ManifestKeyPathOverrideForTests = $path } $testKeyPath

try {
    Invoke-Test 'genesis is signed and clean' {
        $run = New-TestRun -Name 'genesis'
        $state = Verify-MathResearchCycleLedger -RunDirectory $run
        Assert-True ($state.HeadSequence -eq 0 -and $state.CleanReturn) 'Genesis state is not clean.'
        Assert-True ($state.AttemptCount -eq 0 -and $state.AuditCount -eq 0) 'Genesis counters are nonzero.'
    }

    Invoke-Test 'Nth attempt start blocks N plus one until audit' {
        $run = New-TestRun -Name 'nth-gate'
        Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $run -TicketId 'C1-A1' | Out-Null
        $a1 = Write-AttemptArtifact -Run $run -Name 'attempt-1.md'
        Invoke-MathResearchCycleAction -Action AttemptEnd -RunDirectory $run -Outcome proved_subclaim -ArtifactFile $a1 -StructureSignal present | Out-Null
        Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $run -TicketId 'C1-A2' | Out-Null
        $a2 = Write-AttemptArtifact -Run $run -Name 'attempt-2.md'
        $state = Invoke-MathResearchCycleAction -Action AttemptEnd -RunDirectory $run -Outcome substantive_inconclusive -ArtifactFile $a2 -StructureSignal absent -RepairBatches 1
        Assert-True ($state.AuditDue -and $state.AttemptsSinceLastAudit -eq 2) 'Nth attempt did not set audit_due.'
        Assert-Throws { Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $run -TicketId 'C1-A3' } 'N+1 attempt was accepted before audit.'
    }

    Invoke-Test 'complete periodic audit resets cycle and permits next ticket' {
        $run = New-TestRun -Name 'audit-reset'
        foreach ($id in @('C1-A1','C1-A2')) {
            Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $run -TicketId $id | Out-Null
            $artifact = Write-AttemptArtifact -Run $run -Name "$id.md"
            Invoke-MathResearchCycleAction -Action AttemptEnd -RunDirectory $run -Outcome method_failed -ArtifactFile $artifact | Out-Null
        }
        $auditTicket = Write-AuditTicket -Run $run -AuditId 'audit-1'
        $before = Verify-MathResearchCycleLedger -RunDirectory $run
        Invoke-MathResearchCycleAction -Action AuditStart -RunDirectory $run -AuditTicketFile $auditTicket | Out-Null
        $result = Write-AuditResult -Run $run -AuditId 'audit-1' -Snapshot $before.HeadPayloadSha256
        $next = Write-NextTickets -Run $run -AuditId 'audit-1'
        $state = Invoke-MathResearchCycleAction -Action AuditEnd -RunDirectory $run -AuditResultFile $result -NextTicketsFile $next
        Assert-True (-not $state.AuditDue -and $state.AttemptsSinceLastAudit -eq 0 -and $state.CurrentCycleId -eq 'cycle-2') 'Audit did not reset and bind the next cycle.'
        Invoke-MathResearchCycleAction -Action ReturnCheck -RunDirectory $run | Out-Null
        Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $run -TicketId 'C2-A1' | Out-Null
    }

    Invoke-Test 'ticket manifest tamper is rejected' {
        $run = New-TestRun -Name 'ticket-tamper'
        Add-Content -LiteralPath (Join-Path $run 'cycle-tickets-000.json') -Value ' ' -Encoding utf8NoBOM
        Assert-Throws { Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $run -TicketId 'C1-A1' } 'A changed ticket manifest was accepted.'
    }

    Invoke-Test 'route family hard max is two per cycle' {
        $policy = New-PolicyObject -Total 6 -Attempts 4 -Interval 4
        $run = New-TestRun -Name 'route-max' -Policy $policy
        foreach ($id in @('C1-A1','C1-A2')) {
            Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $run -TicketId $id | Out-Null
            $artifact = Write-AttemptArtifact -Run $run -Name "$id.md"
            Invoke-MathResearchCycleAction -Action AttemptEnd -RunDirectory $run -Outcome method_failed -ArtifactFile $artifact | Out-Null
        }
        Assert-Throws { Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $run -TicketId 'C1-A3' } 'A third same-family attempt was accepted.'
    }

    Invoke-Test 'dirty return and concurrent attempt are rejected' {
        $run = New-TestRun -Name 'dirty-return'
        Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $run -TicketId 'C1-A1' | Out-Null
        Assert-Throws { Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $run -TicketId 'C1-A2' } 'A second active attempt was accepted.'
        $state = Verify-MathResearchCycleLedger -RunDirectory $run
        Assert-True ($null -ne $state.ActiveAttempt -and -not $state.CleanReturn) 'Crash recovery did not preserve the active attempt.'
        $artifact = Write-AttemptArtifact -Run $run -Name 'aborted.md'
        Invoke-MathResearchCycleAction -Action AttemptEnd -RunDirectory $run -Outcome aborted -ArtifactFile $artifact | Out-Null
        Assert-Throws { Invoke-MathResearchCycleAction -Action ReturnCheck -RunDirectory $run } 'Dirty return without closing audit was accepted.'
    }

    Invoke-Test 'completion requires and accepts three PASS reports' {
        $run = New-TestRun -Name 'completion'
        Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $run -TicketId 'C1-A1' | Out-Null
        $artifact = Write-AttemptArtifact -Run $run -Name 'candidate.md'
        Invoke-MathResearchCycleAction -Action AttemptEnd -RunDirectory $run -Outcome candidate_found -ArtifactFile $artifact -StructureSignal present | Out-Null
        $auditTicket = Write-AuditTicket -Run $run -AuditId 'audit-1' -Trigger completion
        $before = Verify-MathResearchCycleLedger -RunDirectory $run
        Invoke-MathResearchCycleAction -Action AuditStart -RunDirectory $run -AuditTicketFile $auditTicket | Out-Null
        $result = Write-AuditResult -Run $run -AuditId 'audit-1' -Snapshot $before.HeadPayloadSha256 -Action approve-completion
        $state = Invoke-MathResearchCycleAction -Action AuditEnd -RunDirectory $run -AuditResultFile $result
        Assert-True $state.CompletionAuthorized 'Three PASS completion audit did not authorize completion.'
        $state = Invoke-MathResearchCycleAction -Action ReturnCheck -RunDirectory $run -Completion
        Assert-True $state.CleanReturn 'Completion return was not clean.'
    }

    Invoke-Test 'non-PASS completion is blocked' {
        $run = New-TestRun -Name 'completion-fail'
        Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $run -TicketId 'C1-A1' | Out-Null
        $artifact = Write-AttemptArtifact -Run $run -Name 'candidate.md'
        Invoke-MathResearchCycleAction -Action AttemptEnd -RunDirectory $run -Outcome candidate_found -ArtifactFile $artifact | Out-Null
        $ticket = Write-AuditTicket -Run $run -AuditId 'audit-1' -Trigger completion
        $before = Verify-MathResearchCycleLedger -RunDirectory $run
        Invoke-MathResearchCycleAction -Action AuditStart -RunDirectory $run -AuditTicketFile $ticket | Out-Null
        $result = Write-AuditResult -Run $run -AuditId 'audit-1' -Snapshot $before.HeadPayloadSha256 -Action approve-completion -Verdicts @('PASS','FAIL','PASS')
        Assert-Throws { Invoke-MathResearchCycleAction -Action AuditEnd -RunDirectory $run -AuditResultFile $result } 'A non-unanimous completion audit was accepted.'
    }

    Invoke-Test 'event tamper is detected' {
        $run = New-TestRun -Name 'event-tamper'
        $event = Join-Path $run 'cycle-ledger\00000000.json'
        $text = [IO.File]::ReadAllText($event)
        [IO.File]::WriteAllText($event, $text.Replace('GENESIS','GENESIX'), [Text.UTF8Encoding]::new($false))
        Assert-Throws { Verify-MathResearchCycleLedger -RunDirectory $run } 'A modified signed event was accepted.'
    }

    Invoke-Test 'bound attempt artifact tamper is detected' {
        $run = New-TestRun -Name 'artifact-tamper'
        Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $run -TicketId 'C1-A1' | Out-Null
        $artifact = Write-AttemptArtifact -Run $run -Name 'bound.md'
        Invoke-MathResearchCycleAction -Action AttemptEnd -RunDirectory $run -Outcome proved_subclaim -ArtifactFile $artifact | Out-Null
        Write-Utf8Fixture -Path $artifact -Text 'changed after binding'
        Assert-Throws { Verify-MathResearchCycleLedger -RunDirectory $run } 'A changed bound attempt artifact was accepted.'
    }

    Invoke-Test 'project-aware AttemptEnd requires and binds a complete failure record' {
        $fixture = New-ProjectTestRun -Name 'project-failure'
        Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $fixture.Run -TicketId 'C1-A1' | Out-Null
        $artifact = Write-AttemptArtifact -Run $fixture.Run -Name 'attempt.md'
        Assert-Throws { Invoke-MathResearchCycleAction -Action AttemptEnd -RunDirectory $fixture.Run -Outcome substantive_inconclusive -ArtifactFile $artifact } 'Negative AttemptEnd without a failure record was accepted.'
        $artifactHash = (Get-FileHash -LiteralPath $artifact -Algorithm SHA256).Hash.ToLowerInvariant()
        $failure = [ordered]@{ schema=1; attempt_id='attempt-0001'; route_id='route-a'; decision_problem='Decide C1-A1.'; failed_step='bounded search exhausted'; failure_reason='no decisive signal'; excluded_scope='the frozen search domain'; not_excluded_scope='the general theorem'; retry_fingerprint_sha256=$fixture.Fingerprint; reopen_conditions=@('new-global-lemma'); artifacts=@([ordered]@{file='attempt.md';sha256=$artifactHash}) }
        $failurePath = Join-Path $fixture.Run 'failure.json'
        Write-Utf8Fixture -Path $failurePath -Text ($failure | ConvertTo-Json -Depth 20)
        Invoke-MathResearchCycleAction -Action AttemptEnd -RunDirectory $fixture.Run -Outcome substantive_inconclusive -ArtifactFile $artifact -FailureRecordFile $failurePath | Out-Null
        Assert-True (Verify-MathResearchCycleLedger -RunDirectory $fixture.Run).AuditDue 'Project-aware failure did not close the active attempt.'
        Write-Utf8Fixture -Path $failurePath -Text (($failure | ConvertTo-Json -Depth 20) + ' ')
        Assert-Throws { Verify-MathResearchCycleLedger -RunDirectory $fixture.Run } 'Changed failure record was accepted after binding.'
    }

    Invoke-Test 'project-aware AttemptStart blocks a frozen duplicate route' {
        $fixture = New-ProjectTestRun -Name 'project-frozen' -FreezeRoute
        Assert-Throws { Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $fixture.Run -TicketId 'C1-A1' } 'Frozen project route was started without reopen evidence.'
        $state = Verify-MathResearchCycleLedger -RunDirectory $fixture.Run
        Assert-True ($state.AttemptCount -eq 0 -and $state.HeadSequence -eq 0) 'Blocked route consumed an attempt or appended an event.'
    }

    Invoke-Test 'v6 claim AttemptEnd requires a bound attempt record and separate PASS verification' {
        $fixture = New-V6ProjectTestRun -Name 'claim-gates'
        Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $fixture.Run -TicketId 'C1-A1' | Out-Null
        $artifact = Write-AttemptArtifact -Run $fixture.Run -Name 'claim.md'
        Assert-Throws { Invoke-MathResearchCycleAction -Action AttemptEnd -RunDirectory $fixture.Run -Outcome proved_subclaim -ArtifactFile $artifact } 'v6 claim ended without an attempt record.'
        $record = Write-V6AttemptRecord -Run $fixture.Run -Artifact $artifact -NoVerification
        Assert-Throws { Invoke-MathResearchCycleAction -Action AttemptEnd -RunDirectory $fixture.Run -Outcome proved_subclaim -ArtifactFile $artifact -AttemptRecordFile $record } 'v6 claim ended without candidate verification.'
        $record = Write-V6AttemptRecord -Run $fixture.Run -Artifact $artifact -ReuseSolverAsVerifier
        Assert-Throws { Invoke-MathResearchCycleAction -Action AttemptEnd -RunDirectory $fixture.Run -Outcome proved_subclaim -ArtifactFile $artifact -AttemptRecordFile $record } 'One report served as both solver and verifier.'
        $record = Write-V6AttemptRecord -Run $fixture.Run -Artifact $artifact
        $wrong = Get-Content -LiteralPath $record -Raw | ConvertFrom-Json -AsHashtable -Depth 30
        $wrong.verification_reports[-1].candidate_sha256=('0'*64)
        Write-Utf8Fixture -Path $record -Text ($wrong|ConvertTo-Json -Depth 30)
        Assert-Throws { Invoke-MathResearchCycleAction -Action AttemptEnd -RunDirectory $fixture.Run -Outcome proved_subclaim -ArtifactFile $artifact -AttemptRecordFile $record } 'A verifier PASS for a different candidate hash was accepted.'
        $record = Write-V6AttemptRecord -Run $fixture.Run -Artifact $artifact
        Invoke-MathResearchCycleAction -Action AttemptEnd -RunDirectory $fixture.Run -Outcome proved_subclaim -ArtifactFile $artifact -AttemptRecordFile $record | Out-Null
        Assert-True (Verify-MathResearchCycleLedger -RunDirectory $fixture.Run).AuditDue 'Valid v6 claim did not close at the audit gate.'
    }

    Invoke-Test 'v6 targeted revision requires a prior non-PASS and final re-verification' {
        $fixture = New-V6ProjectTestRun -Name 'revision-gates'
        Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $fixture.Run -TicketId 'C1-A1' | Out-Null
        $artifact = Write-AttemptArtifact -Run $fixture.Run -Name 'revised.md'
        $record = Write-V6AttemptRecord -Run $fixture.Run -Artifact $artifact -RepairBatches 1 -Verdicts @('PASS')
        Assert-Throws { Invoke-MathResearchCycleAction -Action AttemptEnd -RunDirectory $fixture.Run -Outcome proved_subclaim -ArtifactFile $artifact -AttemptRecordFile $record -RepairBatches 1 } 'A revision without a pre-repair non-PASS was accepted.'
        $record = Write-V6AttemptRecord -Run $fixture.Run -Artifact $artifact -RepairBatches 1 -Verdicts @('FAIL','PASS')
        Invoke-MathResearchCycleAction -Action AttemptEnd -RunDirectory $fixture.Run -Outcome proved_subclaim -ArtifactFile $artifact -AttemptRecordFile $record -RepairBatches 1 | Out-Null
        $other = New-V6ProjectTestRun -Name 'revision-overflow'
        Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $other.Run -TicketId 'C1-A1' | Out-Null
        $otherArtifact = Write-AttemptArtifact -Run $other.Run -Name 'overflow.md'
        $otherRecord = Write-V6AttemptRecord -Run $other.Run -Artifact $otherArtifact -RepairBatches 2 -Verdicts @('FAIL','PASS')
        Assert-Throws { Invoke-MathResearchCycleAction -Action AttemptEnd -RunDirectory $other.Run -Outcome proved_subclaim -ArtifactFile $otherArtifact -AttemptRecordFile $otherRecord -RepairBatches 2 } 'More than one revision was accepted.'
    }

    Invoke-Test 'v6 route discovery requires audit acceptance before a route card can be executed' {
        $fixture = New-V6ProjectTestRun -Name 'route-discovery' -AttemptKind route_discovery
        Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $fixture.Run -TicketId 'C1-A1' | Out-Null
        $artifact = Write-AttemptArtifact -Run $fixture.Run -Name 'route-summary.md'
        $missingPortfolioRecord = Write-V6AttemptRecord -Run $fixture.Run -Artifact $artifact -AttemptKind route_discovery -NoVerification
        Assert-Throws { Invoke-MathResearchCycleAction -Action AttemptEnd -RunDirectory $fixture.Run -Outcome portfolio_proposed -ArtifactFile $artifact -AttemptRecordFile $missingPortfolioRecord } 'Route discovery ended without a route portfolio.'
        $portfolio = Write-V6RoutePortfolio -Run $fixture.Run
        $record = Write-V6AttemptRecord -Run $fixture.Run -Artifact $artifact -AttemptKind route_discovery -NoVerification -RoutePortfolio $portfolio.Path
        Invoke-MathResearchCycleAction -Action AttemptEnd -RunDirectory $fixture.Run -Outcome portfolio_proposed -ArtifactFile $artifact -AttemptRecordFile $record | Out-Null
        Assert-Throws { Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $fixture.Run -TicketId 'C1-A1' } 'Route discovery bypassed the required audit.'
        $before=Verify-MathResearchCycleLedger -RunDirectory $fixture.Run
        $auditTicket=Write-AuditTicket -Run $fixture.Run -AuditId 'audit-1' -Trigger early
        Invoke-MathResearchCycleAction -Action AuditStart -RunDirectory $fixture.Run -AuditTicketFile $auditTicket | Out-Null
        $accepted=@([ordered]@{source_attempt_id='attempt-0001';card_sha256=$portfolio.CardSha256})
        $result=Write-V6AuditResult -Run $fixture.Run -Snapshot $before.HeadPayloadSha256 -AcceptedRouteCards $accepted
        $tampered=Write-V6NextTicketsFromCard -Run $fixture.Run -Card $portfolio.Card -CardSha256 $portfolio.CardSha256 -Tamper
        Assert-Throws { Invoke-MathResearchCycleAction -Action AuditEnd -RunDirectory $fixture.Run -AuditResultFile $result -NextTicketsFile $tampered } 'Audit accepted a ticket that changed the route card.'
        $next=Write-V6NextTicketsFromCard -Run $fixture.Run -Card $portfolio.Card -CardSha256 $portfolio.CardSha256
        Invoke-MathResearchCycleAction -Action AuditEnd -RunDirectory $fixture.Run -AuditResultFile $result -NextTicketsFile $next | Out-Null
        Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $fixture.Run -TicketId 'C2-A1' | Out-Null
    }

    Invoke-Test 'v6 synthesis ticket requires source claim hashes' {
        Assert-Throws { New-V6ProjectTestRun -Name 'synthesis-missing' -AttemptKind candidate_synthesis } 'candidate_synthesis without source claims was accepted.'
        $fake = New-V6ProjectTestRun -Name 'synthesis-fake' -AttemptKind candidate_synthesis -SourceClaims @(('c' * 64))
        Assert-Throws { Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $fake.Run -TicketId 'C1-A1' } 'A synthesis ticket bound a hash absent from project evidence.'
        $claimText='source evidence';$claimHash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.UTF8Encoding]::new($false).GetBytes($claimText))).ToLowerInvariant()
        $fixture = New-V6ProjectTestRun -Name 'synthesis-bound' -AttemptKind candidate_synthesis -SourceClaims @($claimHash)
        Write-Utf8Fixture -Path (Join-Path $fixture.Project 'evidence\verified\source.md') -Text $claimText
        Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $fixture.Run -TicketId 'C1-A1' | Out-Null
        $artifact=Write-AttemptArtifact -Run $fixture.Run -Name 'synthesis.md'
        $wrongRecord=Write-V6AttemptRecord -Run $fixture.Run -Artifact $artifact -AttemptKind candidate_synthesis -SourceClaims @(('d'*64))
        Assert-Throws { Invoke-MathResearchCycleAction -Action AttemptEnd -RunDirectory $fixture.Run -Outcome proved_subclaim -ArtifactFile $artifact -AttemptRecordFile $wrongRecord } 'Synthesis AttemptEnd changed its frozen source claim hash.'
        $record=Write-V6AttemptRecord -Run $fixture.Run -Artifact $artifact -AttemptKind candidate_synthesis -SourceClaims @($claimHash)
        Invoke-MathResearchCycleAction -Action AttemptEnd -RunDirectory $fixture.Run -Outcome proved_subclaim -ArtifactFile $artifact -AttemptRecordFile $record|Out-Null
    }

    Invoke-Test 'event sequence gap is detected' {
        $run = New-TestRun -Name 'event-gap'
        Invoke-MathResearchCycleAction -Action ReturnCheck -RunDirectory $run | Out-Null
        Move-Item -LiteralPath (Join-Path $run 'cycle-ledger\00000001.json') -Destination (Join-Path $run 'cycle-ledger\00000002.json')
        Assert-Throws { Verify-MathResearchCycleLedger -RunDirectory $run } 'A ledger gap was accepted.'
    }
}
finally {
    $tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\') + '\'
    if ($fullRoot.StartsWith($tempRoot, [StringComparison]::OrdinalIgnoreCase) -and (Split-Path -Leaf $fullRoot) -like 'math-research-cycle-tests-*') {
        Remove-Item -LiteralPath $fullRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "RESULT passed=$passed failed=$failed"
if ($failed -ne 0) { exit 1 }
