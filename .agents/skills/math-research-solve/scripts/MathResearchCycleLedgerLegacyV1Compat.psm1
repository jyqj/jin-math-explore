Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

$launcherModulePath = Join-Path $PSScriptRoot 'MathResearchLauncherLegacyV1Compat.psm1'
if ($null -eq (Get-Command Read-SignedJsonPayload -ErrorAction SilentlyContinue)) {
    Import-Module $launcherModulePath -DisableNameChecking
}
$projectModulePath = Join-Path $PSScriptRoot 'MathResearchProjectArchive.psm1'
if ($null -eq (Get-Command Test-MathResearchRouteStartObject -ErrorAction SilentlyContinue)) {
    Import-Module $projectModulePath -DisableNameChecking
}

$script:LedgerDirectoryName = 'cycle-ledger'
$script:PolicyFileName = 'cycle-policy.json'
$script:InitialTicketsFileName = 'cycle-tickets-000.json'
$script:AuditRoles = @('skeptic_quantifiers', 'skeptic_strategy', 'theory_tool_scout')
$script:NegativeOutcomes = @('route_refuted','bounded_negative','method_failed','substantive_inconclusive','aborted')
$script:ClaimOutcomes = @('candidate_found','proved_subclaim','route_refuted','bounded_negative')
$script:AttemptKinds = @('route_discovery','route_execution','candidate_revision','candidate_synthesis')
$script:HeldCycleMutexNames = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)

function Test-CycleKey {
    param([Parameter(Mandatory = $true)]$Object, [Parameter(Mandatory = $true)][string]$Key)
    return ($Object -is [Collections.IDictionary] -and $Object.Contains($Key))
}

function Assert-CycleExactKeys {
    param(
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Object,
        [Parameter(Mandatory = $true)][string[]]$Required,
        [string[]]$Optional = @(),
        [Parameter(Mandatory = $true)][string]$Label
    )
    $allowed = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($key in @($Required) + @($Optional)) { [void]$allowed.Add($key) }
    foreach ($key in $Required) {
        if (-not $Object.Contains($key)) { throw "$Label is missing required key '$key'." }
    }
    foreach ($key in $Object.Keys) {
        if (-not $allowed.Contains([string]$key)) { throw "$Label contains unknown key '$key'." }
    }
}

function Assert-CycleJsonUniqueProperties {
    param(
        [Parameter(Mandatory = $true)][Text.Json.JsonElement]$Element,
        [Parameter(Mandatory = $true)][string]$Path
    )
    if ($Element.ValueKind -eq [Text.Json.JsonValueKind]::Object) {
        $names = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        foreach ($property in $Element.EnumerateObject()) {
            if (-not $names.Add($property.Name)) { throw "JSON contains duplicate property '$($property.Name)' at $Path." }
            Assert-CycleJsonUniqueProperties -Element $property.Value -Path "$Path.$($property.Name)"
        }
    }
    elseif ($Element.ValueKind -eq [Text.Json.JsonValueKind]::Array) {
        $index = 0
        foreach ($item in $Element.EnumerateArray()) {
            Assert-CycleJsonUniqueProperties -Element $item -Path "$Path[$index]"
            $index++
        }
    }
}

function Read-CycleJsonFile {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)][string]$Label
    )
    $info = Read-StrictUtf8File -LiteralPath $LiteralPath -MaximumBytes 4194304 -Label $Label
    $options = [Text.Json.JsonDocumentOptions]::new()
    $options.AllowTrailingCommas = $false
    $options.CommentHandling = [Text.Json.JsonCommentHandling]::Disallow
    $options.MaxDepth = 64
    try { $document = [Text.Json.JsonDocument]::Parse($info.Text, $options) }
    catch { throw "$Label is not strict JSON: $($_.Exception.Message)" }
    try { Assert-CycleJsonUniqueProperties -Element $document.RootElement -Path '$' }
    finally { $document.Dispose() }
    try { $value = $info.Text | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String }
    catch { throw "$Label cannot be decoded: $($_.Exception.Message)" }
    if ($value -isnot [Collections.IDictionary]) { throw "$Label must be a JSON object." }
    return [pscustomobject]@{ Value = $value; Text = $info.Text; Sha256 = $info.Sha256; Bytes = $info.Bytes }
}

function Resolve-CycleRunPath {
    param([Parameter(Mandatory = $true)][string]$RunDirectory)
    $full = [IO.Path]::GetFullPath($RunDirectory)
    if (-not (Test-Path -LiteralPath $full -PathType Container)) { throw "Run directory does not exist: $full" }
    Assert-NoReparsePointChain -LiteralPath $full | Out-Null
    return $full.TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
}

function Get-CycleProjectDirectory {
    param([Parameter(Mandatory = $true)][string]$RunDirectory, [switch]$Required)
    $runsDirectory = Split-Path -Parent $RunDirectory
    $projectDirectory = Split-Path -Parent $runsDirectory
    if ((Split-Path -Leaf $runsDirectory) -cne 'runs' -or [string]::IsNullOrWhiteSpace($projectDirectory)) {
        if ($Required) { throw 'Project-aware cycle protocol requires <project>\runs\<run-id>.' }
        return $null
    }
    try {
        $project = Resolve-MathResearchProjectDirectory -ProjectDirectory $projectDirectory
        if (-not (Split-Path -Parent $RunDirectory).Equals((Join-Path $project.Path 'runs'), [StringComparison]::OrdinalIgnoreCase)) { throw 'Run is not a direct child of the project runs directory.' }
        return $project.Path
    }
    catch {
        if ($Required) { throw }
        return $null
    }
}

function Resolve-CycleRunFile {
    param(
        [Parameter(Mandatory = $true)][string]$RunDirectory,
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)][string]$Label
    )
    $full = [IO.Path]::GetFullPath($LiteralPath)
    if (-not (Test-PathInsideDirectory -Child $full -Directory $RunDirectory)) { throw "$Label is outside the run directory." }
    if (-not (Test-Path -LiteralPath $full -PathType Leaf)) { throw "$Label is missing: $full" }
    Assert-NoReparsePointChain -LiteralPath $full | Out-Null
    return $full
}

function Get-CycleRelativePath {
    param([string]$RunDirectory, [string]$LiteralPath)
    return [IO.Path]::GetRelativePath($RunDirectory, $LiteralPath)
}

function Enter-CycleLease {
    param([Parameter(Mandatory = $true)][string]$RunDirectory)
    $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $material = "$sid:cycle:$($RunDirectory.ToLowerInvariant())"
    $name = "Local\OpenAI.Codex.MathResearch.cycle.$(Get-Sha256HexFromText -Text $material)"
    if (-not $script:HeldCycleMutexNames.Add($name)) { throw 'This process already holds the cycle-ledger lease.' }
    $created = $false
    $mutex = [Threading.Mutex]::new($false, $name, [ref]$created)
    try {
        try { $acquired = $mutex.WaitOne(0) }
        catch [Threading.AbandonedMutexException] { $acquired = $true }
        if (-not $acquired) { throw 'Another process already holds the cycle-ledger lease.' }
        return [pscustomobject]@{ Mutex = $mutex; Name = $name }
    }
    catch {
        $mutex.Dispose()
        [void]$script:HeldCycleMutexNames.Remove($name)
        throw
    }
}

function Exit-CycleLease {
    param($Lease)
    if ($null -eq $Lease) { return }
    try { $Lease.Mutex.ReleaseMutex() } catch {}
    $Lease.Mutex.Dispose()
    [void]$script:HeldCycleMutexNames.Remove([string]$Lease.Name)
}

function Assert-CyclePolicy {
    param([Parameter(Mandatory = $true)][Collections.IDictionary]$Policy)
    $required = @(
        'schema_version', 'protocol', 'total_round_budget', 'attempt_budget',
        'audit_interval_attempts', 'max_route_family_attempts_per_cycle',
        'max_repair_batches_per_attempt', 'audit_roles'
    )
    Assert-CycleExactKeys -Object $Policy -Required $required -Label 'Cycle policy'
    $schema = [int]$Policy.schema_version
    if ($schema -notin @(1,2,3)) { throw 'Cycle policy schema_version must be 1, 2, or 3.' }
    $expectedProtocol = switch ($schema) {
        1 { 'math-research-cycle-policy/v1' }
        2 { 'math-research-cycle-policy/v2' }
        3 { 'math-research-cycle-policy/v3' }
    }
    if ([string]$Policy.protocol -cne $expectedProtocol) { throw 'Unsupported cycle policy protocol.' }
    $total = [int]$Policy.total_round_budget
    $attempts = [int]$Policy.attempt_budget
    $interval = [int]$Policy.audit_interval_attempts
    if ($total -lt 2 -or $attempts -lt 1 -or $attempts -gt $total -or $interval -lt 1) { throw 'Cycle policy budgets are invalid.' }
    $minimumAudits = [int][Math]::Ceiling($attempts / [double]$interval)
    if ($total -lt $attempts + $minimumAudits) { throw 'Cycle policy total_round_budget cannot accommodate the attempts and required audits.' }
    if ([int]$Policy.max_route_family_attempts_per_cycle -ne 2) { throw 'max_route_family_attempts_per_cycle must be 2.' }
    if ([int]$Policy.max_repair_batches_per_attempt -ne 1) { throw 'max_repair_batches_per_attempt must be 1.' }
    $roles = @($Policy.audit_roles | ForEach-Object { [string]$_ })
    if (($roles | ConvertTo-Json -Compress) -cne ($script:AuditRoles | ConvertTo-Json -Compress)) { throw 'Cycle policy audit_roles must be the fixed three-role list in canonical order.' }
}

function Assert-CycleResourceCaps {
    param([Parameter(Mandatory = $true)]$Caps, [Parameter(Mandatory = $true)][string]$Label)
    if ($Caps -isnot [Collections.IDictionary] -or $Caps.Count -lt 1) { throw "$Label resource_caps must be a nonempty JSON object." }
    foreach ($entry in $Caps.GetEnumerator()) {
        if ([string]$entry.Key -cnotmatch '^[a-z][a-z0-9_]{0,63}$') { throw "$Label has an invalid resource cap name." }
        $number = 0
        if (-not [int]::TryParse([string]$entry.Value, [ref]$number) -or $number -lt 1) { throw "$Label resource caps must be positive integers." }
    }
}

function Get-CycleTicketRecords {
    param(
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Manifest,
        [Parameter(Mandatory = $true)][string]$Label
    )
    Assert-CycleExactKeys -Object $Manifest -Required @('schema_version', 'cycle_id', 'tickets') -Optional @('source_audit_id') -Label $Label
    $ticketSchema = [int]$Manifest.schema_version
    if ($ticketSchema -notin @(1,2,3)) { throw "$Label schema_version must be 1, 2, or 3." }
    if ([string]$Manifest.cycle_id -cnotmatch '^cycle-[1-9]\d*$') { throw "$Label cycle_id must be cycle-N." }
    $tickets = @($Manifest.tickets)
    if ($tickets.Count -lt 1) { throw "$Label must contain at least one ticket." }
    $ids = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $records = @()
    $required = @('ticket_id', 'route_family_id', 'mechanism_id', 'bottleneck_id', 'decision_question', 'search_domain', 'success_signal', 'stop_signal', 'resource_caps', 'reopen_condition')
    if ($ticketSchema -ge 2) { $required = @('route_id','route_fingerprint_sha256') + $required }
    if ($ticketSchema -eq 3) { $required = @('attempt_kind') + $required }
    foreach ($ticket in $tickets) {
        if ($ticket -isnot [Collections.IDictionary]) { throw "$Label contains a non-object ticket." }
        [string[]]$optional = if ($ticketSchema -ge 2) { @('reopen_evidence') } else { @() }
        if ($ticketSchema -eq 3) { $optional = @($optional) + @('source_route_card','source_claims') }
        Assert-CycleExactKeys -Object $ticket -Required $required -Optional $optional -Label "$Label ticket"
        foreach ($key in $required | Where-Object { $_ -ne 'resource_caps' }) {
            if ([string]::IsNullOrWhiteSpace([string]$ticket[$key])) { throw "$Label ticket '$($ticket.ticket_id)' has an empty $key." }
        }
        if ([string]$ticket.ticket_id -cnotmatch '^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$') { throw "$Label contains an unsafe ticket_id." }
        if ($ticketSchema -ge 2 -and [string]$ticket.route_fingerprint_sha256 -cnotmatch '^[0-9a-f]{64}$') { throw "$Label route_fingerprint_sha256 must be lowercase SHA-256." }
        if ($ticketSchema -eq 3) {
            if ($script:AttemptKinds -notcontains [string]$ticket.attempt_kind) { throw "$Label ticket '$($ticket.ticket_id)' has an invalid attempt_kind." }
            if ($ticket.Contains('source_route_card')) {
                if (-not $Manifest.Contains('source_audit_id')) { throw "$Label ticket '$($ticket.ticket_id)' cannot bind source_route_card before an audit." }
                if ($ticket.source_route_card -isnot [Collections.IDictionary]) { throw "$Label ticket '$($ticket.ticket_id)' source_route_card must be an object." }
                Assert-CycleExactKeys -Object $ticket.source_route_card -Required @('source_attempt_id','card_sha256') -Label "$Label ticket '$($ticket.ticket_id)' source_route_card"
                if ([string]$ticket.source_route_card.source_attempt_id -cnotmatch '^attempt-\d{4}$' -or [string]$ticket.source_route_card.card_sha256 -cnotmatch '^[0-9a-f]{64}$') { throw "$Label ticket '$($ticket.ticket_id)' source_route_card is invalid." }
            }
            [object[]]$sourceClaims = if ($ticket.Contains('source_claims')) { @($ticket.source_claims) } else { @() }
            foreach ($claim in $sourceClaims) { if ([string]$claim -cnotmatch '^[0-9a-f]{64}$') { throw "$Label ticket '$($ticket.ticket_id)' source_claims must contain lowercase SHA-256 values." } }
            if ([string]$ticket.attempt_kind -in @('candidate_revision','candidate_synthesis') -and $sourceClaims.Count -lt 1) { throw "$Label ticket '$($ticket.ticket_id)' requires source_claims for its attempt_kind." }
        }
        if (-not $ids.Add([string]$ticket.ticket_id)) { throw "$Label contains duplicate ticket_id '$($ticket.ticket_id)'." }
        Assert-CycleResourceCaps -Caps $ticket.resource_caps -Label "$Label ticket '$($ticket.ticket_id)'"
        $records += [pscustomobject]@{
            TicketId = [string]$ticket.ticket_id
            TicketSha256 = Get-Sha256HexFromText -Text (ConvertTo-CanonicalJson -InputObject $ticket)
            Ticket = $ticket
        }
    }
    return [pscustomobject]@{ CycleId = [string]$Manifest.cycle_id; Records = @($records) }
}

function Read-CycleTicketManifest {
    param([string]$RunDirectory, [string]$LiteralPath, [string]$ExpectedSha256, [string]$Label)
    $path = Resolve-CycleRunFile -RunDirectory $RunDirectory -LiteralPath $LiteralPath -Label $Label
    $read = Read-CycleJsonFile -LiteralPath $path -Label $Label
    if (-not (Test-FixedTimeHexEqual -Left $read.Sha256 -Right $ExpectedSha256)) { throw "$Label SHA-256 differs from the signed ledger." }
    $tickets = Get-CycleTicketRecords -Manifest $read.Value -Label $Label
    return [pscustomobject]@{ Path = $path; RelativePath = Get-CycleRelativePath -RunDirectory $RunDirectory -LiteralPath $path; Sha256 = $read.Sha256; Value = $read.Value; CycleId = $tickets.CycleId; Records = $tickets.Records }
}

function Get-CycleEventPayloadSha256 {
    param([Parameter(Mandatory = $true)]$Payload)
    return Get-Sha256HexFromText -Text (ConvertTo-CanonicalJson -InputObject $Payload)
}

function Add-CycleEvent {
    param(
        [Parameter(Mandatory = $true)][string]$LedgerDirectory,
        [Parameter(Mandatory = $true)][int]$Sequence,
        [Parameter(Mandatory = $true)][string]$RunId,
        [Parameter(Mandatory = $true)][string]$EventType,
        [AllowNull()][string]$PreviousPayloadSha256,
        [Parameter(Mandatory = $true)]$Data
    )
    $path = Join-Path $LedgerDirectory ('{0:D8}.json' -f $Sequence)
    if (Test-Path -LiteralPath $path) { throw "Cycle event already exists: $path" }
    $payload = [ordered]@{
        ledger_schema_version = 1
        sequence = $Sequence
        run_id = $RunId
        event_type = $EventType
        previous_payload_sha256 = if ($Sequence -eq 0) { $null } else { $PreviousPayloadSha256 }
        recorded_at_utc = Get-UtcNowString
        data = $Data
    }
    # Normalize live PowerShell scalar/container types before signing. Without this
    # round-trip, ConvertTo-Json can serialize a live object differently from the
    # hashtable reconstructed by Read-SignedJsonPayload (for example, a one-item
    # pipeline result), making an otherwise unchanged immutable event unverifiable.
    $stablePayload = (ConvertTo-CanonicalJson -InputObject $payload) | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    Write-SignedJsonPayload -LiteralPath $path -Payload $stablePayload -CreateKeyIfMissing
    return [pscustomobject]@{ Path = $path; Payload = $stablePayload; PayloadSha256 = Get-CycleEventPayloadSha256 -Payload $stablePayload }
}

function New-CycleState {
    return [ordered]@{
        RunId = $null; ContractBindingSha256 = $null; Policy = $null
        HeadSequence = -1; HeadPayloadSha256 = $null; LastEventType = $null
        AttemptCount = 0; AuditCount = 0; TotalRoundCount = 0; AttemptsSinceLastAudit = 0
        AuditDue = $false; ActiveAttempt = $null; ActiveAudit = $null
        CompletionCandidate = $false; CompletionAuthorized = $false
        CurrentTicketsFile = $null; CurrentTicketsSha256 = $null; CurrentCycleId = $null
        ConsumedTicketIds = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        RouteCounts = [ordered]@{}; PendingRouteCards = [ordered]@{}
        CleanReturn = $false; LastReturnCheckSequence = $null
    }
}

function Read-CycleLedgerStateInternal {
    param([Parameter(Mandatory = $true)][string]$RunDirectory)
    $ledgerDirectory = Join-Path $RunDirectory $script:LedgerDirectoryName
    if (-not (Test-Path -LiteralPath $ledgerDirectory -PathType Container)) { throw 'Cycle ledger has not been initialized.' }
    Assert-NoReparsePointChain -LiteralPath $ledgerDirectory | Out-Null
    $files = @(Get-ChildItem -LiteralPath $ledgerDirectory -File -Filter '*.json' | Sort-Object Name)
    if ($files.Count -lt 1) { throw 'Cycle ledger contains no genesis event.' }
    $state = New-CycleState
    $previous = $null
    for ($i = 0; $i -lt $files.Count; $i++) {
        $expectedName = '{0:D8}.json' -f $i
        if ($files[$i].Name -cne $expectedName) { throw "Cycle ledger sequence has a gap, duplicate, or unexpected file at $($files[$i].Name)." }
        $read = Read-SignedJsonPayload -LiteralPath $files[$i].FullName
        if ($read.RecoveredFromBackup) { throw 'Immutable cycle events may not recover from mutable .bak files.' }
        $event = $read.Payload
        if ([int]$event.ledger_schema_version -ne 1 -or [int]$event.sequence -ne $i) { throw "Cycle event $expectedName has an invalid schema or sequence." }
        if ($i -eq 0) {
            if ([string]$event.event_type -cne 'GENESIS' -or $null -ne $event.previous_payload_sha256) { throw 'Cycle event zero must be GENESIS with no previous hash.' }
            $state.RunId = [string]$event.run_id
            $state.ContractBindingSha256 = [string]$event.data.contract_binding_sha256
            $state.Policy = $event.data.policy
            Assert-CyclePolicy -Policy $state.Policy
            $state.CurrentTicketsFile = [string]$event.data.initial_tickets_file
            $state.CurrentTicketsSha256 = [string]$event.data.initial_tickets_sha256
            $state.CurrentCycleId = [string]$event.data.initial_cycle_id
        }
        else {
            if ([string]$event.run_id -cne [string]$state.RunId) { throw "Cycle event $expectedName changed run_id." }
            if ([string]$event.previous_payload_sha256 -cne [string]$previous) { throw "Cycle event $expectedName breaks the payload hash chain." }
            switch ([string]$event.event_type) {
                'ATTEMPT_START' {
                    if ($null -ne $state.ActiveAttempt -or $null -ne $state.ActiveAudit -or $state.AuditDue -or $state.CompletionAuthorized) { throw "Cycle event $expectedName starts an attempt from an illegal state." }
                    if ($state.AttemptCount -ge [int]$state.Policy.attempt_budget -or $state.TotalRoundCount + 2 -gt [int]$state.Policy.total_round_budget) { throw "Cycle event $expectedName violates the attempt or reserved-audit budget." }
                    if ($state.ConsumedTicketIds.Contains([string]$event.data.ticket_id)) { throw "Cycle event $expectedName reuses a consumed ticket id." }
                    $ticketManifest = Read-CycleTicketManifest -RunDirectory $RunDirectory -LiteralPath (Join-Path $RunDirectory ([string]$event.data.ticket_manifest_file)) -ExpectedSha256 ([string]$event.data.ticket_manifest_sha256) -Label "ticket manifest for $expectedName"
                    $ticketMatches = @($ticketManifest.Records | Where-Object { $_.TicketId -ceq [string]$event.data.ticket_id })
                    if ($ticketMatches.Count -ne 1 -or [string]$ticketMatches[0].TicketSha256 -cne [string]$event.data.ticket_sha256) { throw "Cycle event $expectedName is not bound to one exact ticket." }
                    if ([string]$ticketManifest.CycleId -cne [string]$event.data.cycle_id -or [string]$ticketMatches[0].Ticket.route_family_id -cne [string]$event.data.route_family_id -or [string]$ticketMatches[0].Ticket.mechanism_id -cne [string]$event.data.mechanism_id) { throw "Cycle event $expectedName changed ticket routing fields." }
                    if ([int]$state.Policy.schema_version -ge 2 -and
                        ([string]$ticketMatches[0].Ticket.route_id -cne [string]$event.data.route_id -or
                         [string]$ticketMatches[0].Ticket.route_fingerprint_sha256 -cne [string]$event.data.route_fingerprint_sha256)) {
                        throw "Cycle event $expectedName changed the project route identity or fingerprint."
                    }
                    if ([int]$state.Policy.schema_version -eq 3 -and
                        ([string]$ticketMatches[0].Ticket.attempt_kind -cne [string]$event.data.attempt_kind -or
                         [string]$ticketMatches[0].Ticket.decision_question -cne [string]$event.data.decision_question)) {
                        throw "Cycle event $expectedName changed the attempt kind or decision question."
                    }
                    $priorRoute = if ($state.RouteCounts.Contains([string]$event.data.route_family_id)) { [int]$state.RouteCounts[[string]$event.data.route_family_id] } else { 0 }
                    if ($priorRoute -ge [int]$state.Policy.max_route_family_attempts_per_cycle) { throw "Cycle event $expectedName exceeds the route-family cap." }
                    $state.AttemptCount++
                    $state.TotalRoundCount++
                    $state.AttemptsSinceLastAudit++
                    $state.ActiveAttempt = $event.data
                    [void]$state.ConsumedTicketIds.Add([string]$event.data.ticket_id)
                    $route = [string]$event.data.route_family_id
                    $state.RouteCounts[$route] = if ($state.RouteCounts.Contains($route)) { [int]$state.RouteCounts[$route] + 1 } else { 1 }
                    if ($state.AttemptsSinceLastAudit -ge [int]$state.Policy.audit_interval_attempts) { $state.AuditDue = $true }
                }
                'ATTEMPT_END' {
                    if ($null -eq $state.ActiveAttempt -or [string]$state.ActiveAttempt.attempt_id -cne [string]$event.data.attempt_id) { throw "Cycle event $expectedName ends no matching active attempt." }
                    $attemptArtifact = Get-CycleArtifactRecord -RunDirectory $RunDirectory -LiteralPath (Join-Path $RunDirectory ([string]$event.data.artifact_file)) -Label "attempt artifact for $expectedName"
                    if ([string]$attemptArtifact.file -cne [string]$event.data.artifact_file -or [string]$attemptArtifact.sha256 -cne [string]$event.data.artifact_sha256) { throw "Cycle event $expectedName has a changed attempt artifact." }
                    if ([int]$state.Policy.schema_version -ge 2 -and [string]$event.data.outcome -in $script:NegativeOutcomes) {
                        $failurePath = Resolve-CycleRunFile -RunDirectory $RunDirectory -LiteralPath (Join-Path $RunDirectory ([string]$event.data.failure_record_file)) -Label "failure record for $expectedName"
                        $failure = Test-MathResearchFailureRecord -FailureRecordFile $failurePath -ExpectedAttemptId ([string]$state.ActiveAttempt.attempt_id) -ArtifactRoot $RunDirectory
                        if ([string]$failure.Sha256 -cne [string]$event.data.failure_record_sha256 -or [string]$failure.Value.retry_fingerprint_sha256 -cne [string]$state.ActiveAttempt.route_fingerprint_sha256) { throw "Cycle event $expectedName has a changed or mismatched failure record." }
                    }
                    if ([int]$state.Policy.schema_version -eq 3) {
                        $attemptRecordPath = Resolve-CycleRunFile -RunDirectory $RunDirectory -LiteralPath (Join-Path $RunDirectory ([string]$event.data.attempt_record_file)) -Label "attempt record for $expectedName"
                        $attemptRecord = Test-CycleAttemptRecord -RunDirectory $RunDirectory -LiteralPath $attemptRecordPath -ActiveAttempt $state.ActiveAttempt -Outcome ([string]$event.data.outcome) -ArtifactRecord $attemptArtifact -RepairBatches ([int]$event.data.repair_batches)
                        if ([string]$attemptRecord.Sha256 -cne [string]$event.data.attempt_record_sha256) { throw "Cycle event $expectedName has a changed attempt record." }
                        if ([string]$event.data.outcome -eq 'portfolio_proposed') {
                            $cardHashes = @($attemptRecord.RouteCards | ForEach-Object { [string]$_.CardSha256 })
                            if ([string]$event.data.route_portfolio_file -cne [string]$attemptRecord.Value.route_portfolio.file -or
                                [string]$event.data.route_portfolio_sha256 -cne [string]$attemptRecord.Value.route_portfolio.sha256 -or
                                ($cardHashes | ConvertTo-Json -Compress) -cne (@($event.data.route_card_hashes) | ConvertTo-Json -Compress)) { throw "Cycle event $expectedName changed its route portfolio binding." }
                        }
                        foreach ($routeCard in @($attemptRecord.RouteCards)) {
                            if ($state.PendingRouteCards.Contains([string]$routeCard.CardSha256)) { throw "Cycle event $expectedName repeats a pending route-card hash." }
                            $state.PendingRouteCards[[string]$routeCard.CardSha256] = [ordered]@{ source_attempt_id=[string]$state.ActiveAttempt.attempt_id; card=$routeCard.Card }
                        }
                    }
                    if ([int]$event.data.repair_batches -gt [int]$state.Policy.max_repair_batches_per_attempt) { throw "Cycle event $expectedName exceeds the repair-batch cap." }
                    $state.ActiveAttempt = $null
                    if ([string]$event.data.outcome -eq 'candidate_found') { $state.CompletionCandidate = $true; $state.AuditDue = $true }
                    if ([string]$event.data.outcome -eq 'portfolio_proposed') { $state.AuditDue = $true }
                }
                'AUDIT_START' {
                    if ($null -ne $state.ActiveAttempt -or $null -ne $state.ActiveAudit -or $state.AttemptsSinceLastAudit -lt 1) { throw "Cycle event $expectedName starts an audit from an illegal state." }
                    if ($state.TotalRoundCount + 1 -gt [int]$state.Policy.total_round_budget) { throw "Cycle event $expectedName exceeds the total-round budget." }
                    $auditTicket = Read-CycleAuditTicket -RunDirectory $RunDirectory -LiteralPath (Join-Path $RunDirectory ([string]$event.data.audit_ticket_file)) -State $state
                    if ([string]$auditTicket.Sha256 -cne [string]$event.data.audit_ticket_sha256 -or [string]$auditTicket.Value.audit_id -cne [string]$event.data.audit_id) { throw "Cycle event $expectedName has a changed audit ticket." }
                    $state.AuditCount++
                    $state.TotalRoundCount++
                    $state.ActiveAudit = $event.data
                }
                'AUDIT_END' {
                    if ($null -eq $state.ActiveAudit -or [string]$state.ActiveAudit.audit_id -cne [string]$event.data.audit_id) { throw "Cycle event $expectedName ends no matching active audit." }
                    $auditResult = Read-CycleAuditResult -RunDirectory $RunDirectory -LiteralPath (Join-Path $RunDirectory ([string]$event.data.audit_result_file)) -State $state
                    if ([string]$auditResult.Sha256 -cne [string]$event.data.audit_result_sha256 -or [string]$auditResult.Action -cne [string]$event.data.action -or [bool]$auditResult.AllPass -ne [bool]$event.data.all_reports_pass) { throw "Cycle event $expectedName has a changed audit result." }
                    if (-not [string]::IsNullOrWhiteSpace([string]$event.data.next_tickets_file)) {
                        $verifiedNext = Read-CycleTicketManifest -RunDirectory $RunDirectory -LiteralPath (Join-Path $RunDirectory ([string]$event.data.next_tickets_file)) -ExpectedSha256 ([string]$event.data.next_tickets_sha256) -Label "next ticket manifest for $expectedName"
                        if ([string]$verifiedNext.CycleId -cne [string]$event.data.next_cycle_id) { throw "Cycle event $expectedName changed its next cycle id." }
                        if ([int]$state.Policy.schema_version -eq 3) {
                            if ((@($auditResult.AcceptedRouteCards) | ConvertTo-Json -Compress -Depth 10) -cne (@($event.data.accepted_route_cards) | ConvertTo-Json -Compress -Depth 10)) { throw "Cycle event $expectedName changed accepted route-card bindings." }
                            $accepted = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
                            foreach ($entry in @($auditResult.AcceptedRouteCards)) { [void]$accepted.Add([string]$entry.card_sha256) }
                            foreach ($record in @($verifiedNext.Records)) {
                                if ($record.Ticket.Contains('source_route_card')) {
                                    $source = $record.Ticket.source_route_card
                                    $cardHash = [string]$source.card_sha256
                                    if (-not $accepted.Contains($cardHash) -or -not $state.PendingRouteCards.Contains($cardHash)) { throw "Cycle event $expectedName binds an unaccepted route card." }
                                    $stored = $state.PendingRouteCards[$cardHash]
                                    $card = $stored.card
                                    if ([string]$source.source_attempt_id -cne [string]$stored.source_attempt_id -or
                                        [string]$record.Ticket.route_id -cne [string]$card.route_id -or
                                        [string]$record.Ticket.route_family_id -cne [string]$card.route_family_id -or
                                        [string]$record.Ticket.mechanism_id -cne [string]$card.mechanism_id -or
                                        [string]$record.Ticket.bottleneck_id -cne [string]$card.bottleneck_id -or
                                        [string]$record.Ticket.decision_question -cne [string]$card.decision_question -or
                                        [string]$record.Ticket.search_domain -cne [string]$card.search_domain -or
                                        [string]$record.Ticket.success_signal -cne [string]$card.success_signal -or
                                        [string]$record.Ticket.stop_signal -cne [string]$card.stop_signal -or
                                        [string]$record.Ticket.reopen_condition -cne [string]$card.reopen_condition) { throw "Cycle event $expectedName changed an accepted route card." }
                                }
                            }
                        }
                    }
                    $state.ActiveAudit = $null
                    $state.AttemptsSinceLastAudit = 0
                    $state.AuditDue = $false
                    $state.RouteCounts = [ordered]@{}
                    $state.PendingRouteCards = [ordered]@{}
                    if ([bool]$event.data.completion_authorized) { $state.CompletionAuthorized = $true }
                    elseif ($state.CompletionCandidate) { $state.CompletionCandidate = $false }
                    if (-not [string]::IsNullOrWhiteSpace([string]$event.data.next_tickets_file)) {
                        $state.CurrentTicketsFile = [string]$event.data.next_tickets_file
                        $state.CurrentTicketsSha256 = [string]$event.data.next_tickets_sha256
                        $state.CurrentCycleId = [string]$event.data.next_cycle_id
                    }
                    else {
                        $state.CurrentTicketsFile = $null; $state.CurrentTicketsSha256 = $null; $state.CurrentCycleId = $null
                    }
                }
                'RETURN_CHECKED' { $state.LastReturnCheckSequence = $i }
                default { throw "Cycle event $expectedName has unknown event_type '$($event.event_type)'." }
            }
        }
        if ($state.AttemptCount -gt [int]$state.Policy.attempt_budget -or $state.TotalRoundCount -gt [int]$state.Policy.total_round_budget -or $state.AttemptsSinceLastAudit -gt [int]$state.Policy.audit_interval_attempts) { throw "Cycle event $expectedName violates a frozen budget." }
        $previous = Get-CycleEventPayloadSha256 -Payload $event
        $state.HeadSequence = $i
        $state.HeadPayloadSha256 = $previous
        $state.LastEventType = [string]$event.event_type
    }
    $initialPolicyPath = Join-Path $RunDirectory $script:PolicyFileName
    $policyRead = Read-CycleJsonFile -LiteralPath (Resolve-CycleRunFile -RunDirectory $RunDirectory -LiteralPath $initialPolicyPath -Label 'cycle policy') -Label 'cycle policy'
    if ((Get-Sha256HexFromText -Text (ConvertTo-CanonicalJson -InputObject $policyRead.Value)) -cne (Get-Sha256HexFromText -Text (ConvertTo-CanonicalJson -InputObject $state.Policy))) { throw 'Cycle policy content differs from signed genesis.' }
    if ($null -ne $state.CurrentTicketsFile) {
        [void](Read-CycleTicketManifest -RunDirectory $RunDirectory -LiteralPath (Join-Path $RunDirectory $state.CurrentTicketsFile) -ExpectedSha256 $state.CurrentTicketsSha256 -Label 'current ticket manifest')
    }
    $state.CleanReturn = ($null -eq $state.ActiveAttempt -and $null -eq $state.ActiveAudit -and -not $state.AuditDue -and $state.AttemptsSinceLastAudit -eq 0)
    return $state
}

function Convert-CycleStateForOutput {
    param([Parameter(Mandatory = $true)][Collections.IDictionary]$State)
    return [pscustomobject][ordered]@{
        RunId = $State.RunId; ContractBindingSha256 = $State.ContractBindingSha256
        HeadSequence = $State.HeadSequence; HeadPayloadSha256 = $State.HeadPayloadSha256; LastEventType = $State.LastEventType
        AttemptCount = $State.AttemptCount; AuditCount = $State.AuditCount; TotalRoundCount = $State.TotalRoundCount
        AttemptsSinceLastAudit = $State.AttemptsSinceLastAudit; AuditDue = [bool]$State.AuditDue
        ActiveAttempt = $State.ActiveAttempt; ActiveAudit = $State.ActiveAudit
        CompletionCandidate = [bool]$State.CompletionCandidate; CompletionAuthorized = [bool]$State.CompletionAuthorized
        CurrentTicketsFile = $State.CurrentTicketsFile; CurrentTicketsSha256 = $State.CurrentTicketsSha256; CurrentCycleId = $State.CurrentCycleId
        CleanReturn = [bool]$State.CleanReturn
        TotalRoundBudget = [int]$State.Policy.total_round_budget; AttemptBudget = [int]$State.Policy.attempt_budget
        AuditIntervalAttempts = [int]$State.Policy.audit_interval_attempts
    }
}

function Initialize-MathResearchCycleLedger {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$RunDirectory,
        [Parameter(Mandatory = $true)][string]$RunId,
        [Parameter(Mandatory = $true)][string]$ContractSha256,
        [Parameter(Mandatory = $true)][string]$PolicyFile,
        [Parameter(Mandatory = $true)][string]$TicketsFile
    )
    $runPath = Resolve-CycleRunPath -RunDirectory $RunDirectory
    $lease = Enter-CycleLease -RunDirectory $runPath
    try {
        if ($RunId -cnotmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$') { throw 'RunId contains unsupported characters.' }
        if ($ContractSha256 -cnotmatch '^[0-9a-f]{64}$') { throw 'ContractSha256 must be lowercase SHA-256.' }
        $policyPath = Resolve-CycleRunFile -RunDirectory $runPath -LiteralPath $PolicyFile -Label 'cycle policy'
        $ticketsPath = Resolve-CycleRunFile -RunDirectory $runPath -LiteralPath $TicketsFile -Label 'initial ticket manifest'
        if ((Split-Path -Leaf $policyPath) -cne $script:PolicyFileName -or (Split-Path -Leaf $ticketsPath) -cne $script:InitialTicketsFileName) { throw 'Cycle input filenames are not canonical.' }
        $policy = Read-CycleJsonFile -LiteralPath $policyPath -Label 'cycle policy'
        Assert-CyclePolicy -Policy $policy.Value
        $tickets = Read-CycleJsonFile -LiteralPath $ticketsPath -Label 'initial ticket manifest'
        $ticketRecords = Get-CycleTicketRecords -Manifest $tickets.Value -Label 'initial ticket manifest'
        if ([int]$policy.Value.schema_version -ne [int]$tickets.Value.schema_version) { throw 'Cycle policy and ticket manifest schema versions must match.' }
        if ([int]$policy.Value.schema_version -ge 2) { Get-CycleProjectDirectory -RunDirectory $runPath -Required | Out-Null }
        if ($ticketRecords.CycleId -cne 'cycle-1') { throw 'Initial ticket manifest cycle_id must be cycle-1.' }
        $ledger = Join-Path $runPath $script:LedgerDirectoryName
        if (Test-Path -LiteralPath $ledger) { throw 'Cycle ledger already exists; initialization is not repeatable.' }
        New-Item -ItemType Directory -Path $ledger | Out-Null
        Assert-NoReparsePointChain -LiteralPath $ledger | Out-Null
        $ticketHashes = @($ticketRecords.Records | ForEach-Object { [ordered]@{ ticket_id = $_.TicketId; ticket_sha256 = $_.TicketSha256 } })
        $data = [ordered]@{
            contract_binding_sha256 = $ContractSha256
            policy_file = $script:PolicyFileName
            policy_sha256 = $policy.Sha256
            policy = $policy.Value
            baseline_audit_id = 'audit-0'
            baseline_completed = $true
            baseline_counts_toward_budget = $false
            baseline_user_ratified = $true
            baseline_snapshot_manifest_sha256 = $tickets.Sha256
            initial_tickets_file = $script:InitialTicketsFileName
            initial_tickets_sha256 = $tickets.Sha256
            initial_cycle_id = $ticketRecords.CycleId
            initial_ticket_hashes = $ticketHashes
        }
        [void](Add-CycleEvent -LedgerDirectory $ledger -Sequence 0 -RunId $RunId -EventType 'GENESIS' -PreviousPayloadSha256 $null -Data $data)
        return Convert-CycleStateForOutput -State (Read-CycleLedgerStateInternal -RunDirectory $runPath)
    }
    finally { Exit-CycleLease -Lease $lease }
}

function Verify-MathResearchCycleLedger {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$RunDirectory)
    $runPath = Resolve-CycleRunPath -RunDirectory $RunDirectory
    $lease = Enter-CycleLease -RunDirectory $runPath
    try { return Convert-CycleStateForOutput -State (Read-CycleLedgerStateInternal -RunDirectory $runPath) }
    finally { Exit-CycleLease -Lease $lease }
}

function Save-MathResearchCycleCheckpoint {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$RunDirectory)
    $state = Verify-MathResearchCycleLedger -RunDirectory $RunDirectory
    return [ordered]@{
        ledger_schema_version = 1
        head_sequence = [int]$state.HeadSequence
        head_payload_sha256 = [string]$state.HeadPayloadSha256
        attempt_count = [int]$state.AttemptCount
        audit_count = [int]$state.AuditCount
        total_round_count = [int]$state.TotalRoundCount
        attempts_since_last_audit = [int]$state.AttemptsSinceLastAudit
        audit_due = [bool]$state.AuditDue
        clean_return = [bool]$state.CleanReturn
        completion_authorized = [bool]$state.CompletionAuthorized
    }
}

function Get-CycleArtifactRecord {
    param([string]$RunDirectory, [string]$LiteralPath, [string]$Label)
    $path = Resolve-CycleRunFile -RunDirectory $RunDirectory -LiteralPath $LiteralPath -Label $Label
    return [ordered]@{ file = Get-CycleRelativePath -RunDirectory $RunDirectory -LiteralPath $path; sha256 = Get-Sha256HexFromFile -LiteralPath $path }
}

function Read-CycleRoutePortfolio {
    param(
        [Parameter(Mandatory = $true)][string]$RunDirectory,
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)][string]$ExpectedAttemptId
    )
    $path = Resolve-CycleRunFile -RunDirectory $RunDirectory -LiteralPath $LiteralPath -Label 'route portfolio'
    $read = Read-CycleJsonFile -LiteralPath $path -Label 'route portfolio'
    Assert-CycleExactKeys -Object $read.Value -Required @('schema_version','source_attempt_id','routes') -Label 'Route portfolio'
    if ([int]$read.Value.schema_version -ne 1 -or [string]$read.Value.source_attempt_id -cne $ExpectedAttemptId) { throw 'Route portfolio schema or source_attempt_id is invalid.' }
    $routes = @($read.Value.routes)
    if ($routes.Count -lt 1) { throw 'Route portfolio must contain at least one route card.' }
    $ids = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $records = @()
    foreach ($card in $routes) {
        if ($card -isnot [Collections.IDictionary]) { throw 'Route portfolio contains a non-object card.' }
        Assert-CycleExactKeys -Object $card -Required @('card_id','route_id','route_family_id','mechanism_id','bottleneck_id','decision_question','search_domain','success_signal','stop_signal','reopen_condition') -Label 'Route card'
        foreach ($key in @('card_id','route_id','route_family_id','mechanism_id','bottleneck_id','decision_question','search_domain','success_signal','stop_signal','reopen_condition')) {
            if ([string]::IsNullOrWhiteSpace([string]$card[$key])) { throw "Route card has an empty $key." }
        }
        if ([string]$card.card_id -cnotmatch '^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$' -or -not $ids.Add([string]$card.card_id)) { throw 'Route portfolio contains an unsafe or duplicate card_id.' }
        $records += [pscustomobject]@{ CardSha256=Get-Sha256HexFromText -Text (ConvertTo-CanonicalJson -InputObject $card); Card=$card }
    }
    return [pscustomobject]@{ Path=$path; RelativePath=Get-CycleRelativePath -RunDirectory $RunDirectory -LiteralPath $path; Sha256=$read.Sha256; Records=@($records) }
}

function Test-CycleAttemptRecord {
    param(
        [Parameter(Mandatory = $true)][string]$RunDirectory,
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)][Collections.IDictionary]$ActiveAttempt,
        [Parameter(Mandatory = $true)][string]$Outcome,
        [Parameter(Mandatory = $true)][Collections.IDictionary]$ArtifactRecord,
        [Parameter(Mandatory = $true)][int]$RepairBatches
    )
    $path = Resolve-CycleRunFile -RunDirectory $RunDirectory -LiteralPath $LiteralPath -Label 'attempt record'
    $read = Read-CycleJsonFile -LiteralPath $path -Label 'attempt record'
    $required = @('schema_version','attempt_id','ticket_id','attempt_kind','decision_question','solver_reports','verification_reports','repair_batches','result_artifact','route_portfolio','source_claims')
    Assert-CycleExactKeys -Object $read.Value -Required $required -Label 'Attempt record'
    if ([int]$read.Value.schema_version -ne 1 -or [string]$read.Value.attempt_id -cne [string]$ActiveAttempt.attempt_id -or [string]$read.Value.ticket_id -cne [string]$ActiveAttempt.ticket_id) { throw 'Attempt record does not match the active attempt.' }
    if ([string]$read.Value.attempt_kind -cne [string]$ActiveAttempt.attempt_kind -or [string]$read.Value.decision_question -cne [string]$ActiveAttempt.decision_question) { throw 'Attempt record changed the frozen attempt kind or decision question.' }
    if ([int]$read.Value.repair_batches -ne $RepairBatches) { throw 'Attempt record repair_batches does not match AttemptEnd.' }
    if ($RepairBatches -gt 1) { throw 'Attempt record exceeds the one-batch repair limit.' }

    if ($read.Value.result_artifact -isnot [Collections.IDictionary]) { throw 'Attempt record result_artifact must be an object.' }
    Assert-CycleExactKeys -Object $read.Value.result_artifact -Required @('file','sha256') -Label 'Attempt result artifact'
    if ([string]$read.Value.result_artifact.file -cne [string]$ArtifactRecord.file -or [string]$read.Value.result_artifact.sha256 -cne [string]$ArtifactRecord.sha256) { throw 'Attempt record result_artifact does not match AttemptEnd.' }

    $solverReports = @($read.Value.solver_reports)
    if ($Outcome -ne 'aborted' -and $solverReports.Count -lt 1) { throw 'A non-aborted v6 attempt requires at least one solver report.' }
    $solverHashes = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($report in $solverReports) {
        if ($report -isnot [Collections.IDictionary]) { throw 'Solver report entry must be an object.' }
        Assert-CycleExactKeys -Object $report -Required @('file','sha256') -Label 'Solver report entry'
        $artifact = Get-CycleArtifactRecord -RunDirectory $RunDirectory -LiteralPath (Join-Path $RunDirectory ([string]$report.file)) -Label 'solver report'
        if ([string]$artifact.file -cne [string]$report.file -or [string]$artifact.sha256 -cne [string]$report.sha256) { throw 'Solver report artifact hash mismatch.' }
        if (-not $solverHashes.Add([string]$report.sha256)) { throw 'Solver reports must not repeat the same artifact hash.' }
    }

    $verificationReports = @($read.Value.verification_reports)
    foreach ($report in $verificationReports) {
        if ($report -isnot [Collections.IDictionary]) { throw 'Verification report entry must be an object.' }
        Assert-CycleExactKeys -Object $report -Required @('candidate_sha256','verdict','artifact_file','artifact_sha256','new_math_performed') -Label 'Verification report entry'
        if ([string]$report.candidate_sha256 -cnotmatch '^[0-9a-f]{64}$' -or [string]$report.verdict -notin @('PASS','FAIL','INCONCLUSIVE')) { throw 'Verification report candidate hash or verdict is invalid.' }
        if ($report.new_math_performed -ne $false) { throw 'Candidate verification must declare new_math_performed=false.' }
        $artifact = Get-CycleArtifactRecord -RunDirectory $RunDirectory -LiteralPath (Join-Path $RunDirectory ([string]$report.artifact_file)) -Label 'candidate verification report'
        if ([string]$artifact.file -cne [string]$report.artifact_file -or [string]$artifact.sha256 -cne [string]$report.artifact_sha256) { throw 'Candidate verification report artifact hash mismatch.' }
        if ($solverHashes.Contains([string]$report.artifact_sha256)) { throw 'A solver report cannot also serve as the candidate verification report.' }
    }

    $claimOutcome = ($script:ClaimOutcomes -contains $Outcome)
    if ($claimOutcome) {
        if ([string]$ActiveAttempt.attempt_kind -eq 'route_discovery') { throw 'route_discovery cannot end with a mathematical claim outcome.' }
        if ($verificationReports.Count -lt 1) { throw 'A mathematical claim outcome requires a candidate verification report.' }
        $finalVerification = $verificationReports[-1]
        if ([string]$finalVerification.verdict -cne 'PASS' -or [string]$finalVerification.candidate_sha256 -cne [string]$ArtifactRecord.sha256) { throw 'The final candidate verification must PASS the exact final result artifact.' }
        if ($RepairBatches -eq 1 -and ($verificationReports.Count -lt 2 -or -not (@($verificationReports[0..($verificationReports.Count-2)] | Where-Object { [string]$_.verdict -ne 'PASS' }).Count))) { throw 'A repaired mathematical claim requires a pre-repair non-PASS verification and a final PASS re-verification.' }
    }

    [object[]]$sourceClaims = @($read.Value.source_claims)
    foreach ($claim in $sourceClaims) { if ([string]$claim -cnotmatch '^[0-9a-f]{64}$') { throw 'Attempt record source_claims must contain lowercase SHA-256 values.' } }
    $expectedSourceClaims = if ($ActiveAttempt.Contains('source_claims')) { @($ActiveAttempt.source_claims) } else { @() }
    if ((ConvertTo-Json -InputObject ([object[]]$sourceClaims) -Compress) -cne (ConvertTo-Json -InputObject ([object[]]@($expectedSourceClaims)) -Compress)) { throw 'Attempt record source_claims do not match the frozen ticket.' }
    if ([string]$ActiveAttempt.attempt_kind -in @('candidate_revision','candidate_synthesis') -and $sourceClaims.Count -lt 1) { throw 'Revision and synthesis attempts require source_claims.' }

    $routeCards = @()
    if ($Outcome -eq 'portfolio_proposed') {
        if ([string]$ActiveAttempt.attempt_kind -cne 'route_discovery') { throw 'Only route_discovery may end with portfolio_proposed.' }
        if ($null -eq $read.Value.route_portfolio -or $read.Value.route_portfolio -isnot [Collections.IDictionary]) { throw 'portfolio_proposed requires a route_portfolio artifact.' }
        Assert-CycleExactKeys -Object $read.Value.route_portfolio -Required @('file','sha256') -Label 'Attempt route_portfolio'
        $portfolio = Read-CycleRoutePortfolio -RunDirectory $RunDirectory -LiteralPath (Join-Path $RunDirectory ([string]$read.Value.route_portfolio.file)) -ExpectedAttemptId ([string]$ActiveAttempt.attempt_id)
        if ([string]$portfolio.RelativePath -cne [string]$read.Value.route_portfolio.file -or [string]$portfolio.Sha256 -cne [string]$read.Value.route_portfolio.sha256) { throw 'Attempt record route_portfolio hash mismatch.' }
        $routeCards = @($portfolio.Records)
    }
    elseif ($null -ne $read.Value.route_portfolio) { throw 'Only portfolio_proposed may bind a route_portfolio.' }
    elseif ([string]$ActiveAttempt.attempt_kind -eq 'route_discovery' -and $claimOutcome) { throw 'route_discovery cannot promote a mathematical claim.' }

    return [pscustomobject]@{ Path=$path; RelativePath=Get-CycleRelativePath -RunDirectory $RunDirectory -LiteralPath $path; Sha256=$read.Sha256; Value=$read.Value; RouteCards=@($routeCards) }
}

function Read-CycleAuditTicket {
    param([string]$RunDirectory, [string]$LiteralPath, [Collections.IDictionary]$State)
    $path = Resolve-CycleRunFile -RunDirectory $RunDirectory -LiteralPath $LiteralPath -Label 'audit ticket'
    $read = Read-CycleJsonFile -LiteralPath $path -Label 'audit ticket'
    $required = @('schema_version','audit_id','trigger','snapshot_head_sha256','contract_binding_sha256','read_only','roles','resource_caps')
    Assert-CycleExactKeys -Object $read.Value -Required $required -Label 'Audit ticket'
    if ([int]$read.Value.schema_version -ne 1 -or [string]$read.Value.audit_id -cnotmatch '^audit-[1-9]\d*$') { throw 'Audit ticket schema or audit_id is invalid.' }
    if ([string]$read.Value.trigger -notin @('scheduled','early','completion','closing')) { throw 'Audit ticket trigger is invalid.' }
    if ([string]$read.Value.snapshot_head_sha256 -cne [string]$State.HeadPayloadSha256 -or [string]$read.Value.contract_binding_sha256 -cne [string]$State.ContractBindingSha256) { throw 'Audit ticket is not bound to the current ledger head and contract.' }
    if ($read.Value.read_only -ne $true) { throw 'Audit ticket must declare read_only=true.' }
    $roles = @($read.Value.roles | ForEach-Object { [string]$_ })
    if (($roles | ConvertTo-Json -Compress) -cne ($script:AuditRoles | ConvertTo-Json -Compress)) { throw 'Audit ticket roles are not the fixed three-role list.' }
    Assert-CycleResourceCaps -Caps $read.Value.resource_caps -Label 'Audit ticket'
    return [pscustomobject]@{ Path=$path; RelativePath=Get-CycleRelativePath -RunDirectory $RunDirectory -LiteralPath $path; Sha256=$read.Sha256; Value=$read.Value }
}

function Read-CycleAuditResult {
    param([string]$RunDirectory, [string]$LiteralPath, [Collections.IDictionary]$State)
    $path = Resolve-CycleRunFile -RunDirectory $RunDirectory -LiteralPath $LiteralPath -Label 'audit result'
    $read = Read-CycleJsonFile -LiteralPath $path -Label 'audit result'
    $required = @('schema_version','audit_id','snapshot_head_sha256','contract_binding_sha256','new_math_performed','reports','synthesis')
    Assert-CycleExactKeys -Object $read.Value -Required $required -Label 'Audit result'
    $expectedSchema = if ([int]$State.Policy.schema_version -eq 3) { 2 } else { 1 }
    if ([int]$read.Value.schema_version -ne $expectedSchema -or [string]$read.Value.audit_id -cne [string]$State.ActiveAudit.audit_id) { throw 'Audit result does not match the active audit or policy schema.' }
    if ([string]$read.Value.snapshot_head_sha256 -cne [string]$State.ActiveAudit.snapshot_head_sha256 -or [string]$read.Value.contract_binding_sha256 -cne [string]$State.ContractBindingSha256) { throw 'Audit result snapshot or contract binding is wrong.' }
    if ($read.Value.new_math_performed -ne $false) { throw 'Audit result must declare new_math_performed=false.' }
    $reports = @($read.Value.reports)
    if ($reports.Count -ne 3) { throw 'Audit result must contain exactly three reports.' }
    $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $allPass = $true
    foreach ($report in $reports) {
        if ($report -isnot [Collections.IDictionary]) { throw 'Audit report entry must be an object.' }
        Assert-CycleExactKeys -Object $report -Required @('role','verdict','artifact_file','artifact_sha256') -Label 'Audit report entry'
        $role = [string]$report.role
        if ($script:AuditRoles -notcontains $role -or -not $seen.Add($role)) { throw 'Audit result has a duplicate or unknown role.' }
        if ([string]$report.verdict -notin @('PASS','FAIL','INCONCLUSIVE')) { throw 'Audit report verdict is invalid.' }
        if ([string]$report.verdict -ne 'PASS') { $allPass = $false }
        $artifact = Get-CycleArtifactRecord -RunDirectory $RunDirectory -LiteralPath (Join-Path $RunDirectory ([string]$report.artifact_file)) -Label "audit report for $role"
        if ([string]$artifact.file -cne [string]$report.artifact_file -or [string]$artifact.sha256 -cne [string]$report.artifact_sha256) { throw "Audit report artifact hash mismatch for $role." }
    }
    if ($read.Value.synthesis -isnot [Collections.IDictionary]) { throw 'Audit result synthesis must be an object.' }
    $synthesisRequired = @('action','blocking_findings','quarantined_leads')
    if ($expectedSchema -eq 2) { $synthesisRequired += 'accepted_route_cards' }
    Assert-CycleExactKeys -Object $read.Value.synthesis -Required $synthesisRequired -Label 'Audit synthesis'
    $action = [string]$read.Value.synthesis.action
    if ($action -notin @('continue','pivot-within-contract','pause','amendment-required','reject-completion','approve-completion')) { throw 'Audit synthesis action is invalid.' }
    if ($action -eq 'approve-completion' -and (-not $allPass -or -not $State.CompletionCandidate)) { throw 'Completion requires a frozen completion candidate and three PASS verdicts.' }
    $acceptedRouteCards = @()
    if ($expectedSchema -eq 2) {
        $seenCards = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        foreach ($accepted in @($read.Value.synthesis.accepted_route_cards)) {
            if ($accepted -isnot [Collections.IDictionary]) { throw 'accepted_route_cards entries must be objects.' }
            Assert-CycleExactKeys -Object $accepted -Required @('source_attempt_id','card_sha256') -Label 'Accepted route card'
            $cardHash = [string]$accepted.card_sha256
            if ([string]$accepted.source_attempt_id -cnotmatch '^attempt-\d{4}$' -or $cardHash -cnotmatch '^[0-9a-f]{64}$' -or -not $seenCards.Add($cardHash)) { throw 'Accepted route card identity is invalid or duplicated.' }
            if (-not $State.PendingRouteCards.Contains($cardHash) -or [string]$State.PendingRouteCards[$cardHash].source_attempt_id -cne [string]$accepted.source_attempt_id) { throw 'Audit accepted a route card that was not present in the frozen attempt evidence.' }
            $acceptedRouteCards += $accepted
        }
    }
    return [pscustomobject]@{ Path=$path; RelativePath=Get-CycleRelativePath -RunDirectory $RunDirectory -LiteralPath $path; Sha256=$read.Sha256; Value=$read.Value; AllPass=$allPass; Action=$action; AcceptedRouteCards=@($acceptedRouteCards) }
}

function Invoke-MathResearchCycleAction {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][ValidateSet('AttemptStart','AttemptEnd','AuditStart','AuditEnd','ReturnCheck')][string]$Action,
        [Parameter(Mandatory = $true)][string]$RunDirectory,
        [string]$TicketId,
        [ValidateSet('candidate_found','proved_subclaim','route_refuted','bounded_negative','portfolio_proposed','method_failed','substantive_inconclusive','aborted')][string]$Outcome,
        [string]$ArtifactFile,
        [string]$AttemptRecordFile,
        [string]$FailureRecordFile,
        [ValidateSet('present','absent','unknown')][string]$StructureSignal = 'unknown',
        [ValidateRange(0, 2147483647)][int]$RepairBatches = 0,
        [string]$AuditTicketFile,
        [string]$AuditResultFile,
        [string]$NextTicketsFile,
        [switch]$Completion
    )
    $runPath = Resolve-CycleRunPath -RunDirectory $RunDirectory
    $lease = Enter-CycleLease -RunDirectory $runPath
    try {
        $state = Read-CycleLedgerStateInternal -RunDirectory $runPath
        $ledger = Join-Path $runPath $script:LedgerDirectoryName
        $sequence = [int]$state.HeadSequence + 1
        $data = $null
        switch ($Action) {
            'AttemptStart' {
                if ([string]::IsNullOrWhiteSpace($TicketId)) { throw 'AttemptStart requires -TicketId.' }
                if ($null -ne $state.ActiveAttempt -or $null -ne $state.ActiveAudit -or $state.AuditDue -or $state.CompletionAuthorized) { throw 'AttemptStart is blocked by the current cycle state.' }
                if ($state.AttemptCount -ge [int]$state.Policy.attempt_budget) { throw 'Attempt budget is exhausted.' }
                if ($state.TotalRoundCount + 2 -gt [int]$state.Policy.total_round_budget) { throw 'AttemptStart would consume the round reserved for a required audit.' }
                if ([string]::IsNullOrWhiteSpace([string]$state.CurrentTicketsFile)) { throw 'No audit-approved ticket manifest is active.' }
                $manifest = Read-CycleTicketManifest -RunDirectory $runPath -LiteralPath (Join-Path $runPath $state.CurrentTicketsFile) -ExpectedSha256 $state.CurrentTicketsSha256 -Label 'current ticket manifest'
                $matches = @($manifest.Records | Where-Object { $_.TicketId -ceq $TicketId })
                if ($matches.Count -ne 1) { throw 'TicketId is not uniquely present in the current approved manifest.' }
                if ($state.ConsumedTicketIds.Contains($TicketId)) { throw 'TicketId has already been consumed.' }
                $ticket = $matches[0]
                $route = [string]$ticket.Ticket.route_family_id
                $routeCount = if ($state.RouteCounts.Contains($route)) { [int]$state.RouteCounts[$route] } else { 0 }
                if ($routeCount -ge [int]$state.Policy.max_route_family_attempts_per_cycle) { throw 'The route-family hard maximum for this cycle has been reached.' }
                $attemptId = 'attempt-{0:D4}' -f ([int]$state.AttemptCount + 1)
                $data = [ordered]@{ attempt_id=$attemptId; ticket_id=$TicketId; ticket_sha256=$ticket.TicketSha256; ticket_manifest_file=$manifest.RelativePath; ticket_manifest_sha256=$manifest.Sha256; cycle_id=$manifest.CycleId; route_family_id=$route; mechanism_id=[string]$ticket.Ticket.mechanism_id; bottleneck_id=[string]$ticket.Ticket.bottleneck_id }
                if ([int]$state.Policy.schema_version -ge 2) {
                    $projectDirectory = Get-CycleProjectDirectory -RunDirectory $runPath -Required
                    $projectTicket = [ordered]@{
                        route_id=[string]$ticket.Ticket.route_id
                        route_family_id=[string]$ticket.Ticket.route_family_id
                        route_fingerprint_sha256=[string]$ticket.Ticket.route_fingerprint_sha256
                        mechanism_id=[string]$ticket.Ticket.mechanism_id
                        decision_problem=[string]$ticket.Ticket.decision_question
                        frozen_domain=[string]$ticket.Ticket.search_domain
                        resource_caps=$ticket.Ticket.resource_caps
                    }
                    if ($ticket.Ticket.Contains('reopen_evidence')) { $projectTicket.reopen_evidence = $ticket.Ticket.reopen_evidence }
                    Test-MathResearchRouteStartObject -ProjectDirectory $projectDirectory -Ticket $projectTicket | Out-Null
                    $data.route_id = [string]$ticket.Ticket.route_id
                    $data.route_fingerprint_sha256 = [string]$ticket.Ticket.route_fingerprint_sha256
                }
                if ([int]$state.Policy.schema_version -eq 3) {
                    $data.attempt_kind = [string]$ticket.Ticket.attempt_kind
                    $data.decision_question = [string]$ticket.Ticket.decision_question
                    [object[]]$boundSourceClaims = @()
                    if ($ticket.Ticket.Contains('source_claims')) { $boundSourceClaims = @($ticket.Ticket.source_claims) }
                    $data.source_claims = $boundSourceClaims
                    if ([string]$ticket.Ticket.attempt_kind -in @('candidate_revision','candidate_synthesis')) {
                        Test-MathResearchSourceClaims -ProjectDirectory $projectDirectory -ClaimSha256 ([string[]]@($data.source_claims)) | Out-Null
                    }
                }
                [void](Add-CycleEvent -LedgerDirectory $ledger -Sequence $sequence -RunId $state.RunId -EventType 'ATTEMPT_START' -PreviousPayloadSha256 $state.HeadPayloadSha256 -Data $data)
            }
            'AttemptEnd' {
                if ($null -eq $state.ActiveAttempt) { throw 'AttemptEnd requires an active attempt.' }
                if ([string]::IsNullOrWhiteSpace($Outcome) -or [string]::IsNullOrWhiteSpace($ArtifactFile)) { throw 'AttemptEnd requires -Outcome and -ArtifactFile.' }
                if ($RepairBatches -gt [int]$state.Policy.max_repair_batches_per_attempt) { throw 'AttemptEnd exceeds the frozen repair-batch cap.' }
                $artifact = Get-CycleArtifactRecord -RunDirectory $runPath -LiteralPath $ArtifactFile -Label 'attempt artifact'
                $data = [ordered]@{ attempt_id=[string]$state.ActiveAttempt.attempt_id; ticket_id=[string]$state.ActiveAttempt.ticket_id; outcome=$Outcome; artifact_file=$artifact.file; artifact_sha256=$artifact.sha256; structure_signal=$StructureSignal; repair_batches=$RepairBatches }
                if ([int]$state.Policy.schema_version -eq 3) {
                    if ([string]::IsNullOrWhiteSpace($AttemptRecordFile)) { throw 'Prompt v6 AttemptEnd requires -AttemptRecordFile.' }
                    $attemptRecord = Test-CycleAttemptRecord -RunDirectory $runPath -LiteralPath $AttemptRecordFile -ActiveAttempt $state.ActiveAttempt -Outcome $Outcome -ArtifactRecord $artifact -RepairBatches $RepairBatches
                    $data.attempt_record_file = $attemptRecord.RelativePath
                    $data.attempt_record_sha256 = $attemptRecord.Sha256
                    if ($Outcome -eq 'portfolio_proposed') {
                        $data.route_portfolio_file = [string]$attemptRecord.Value.route_portfolio.file
                        $data.route_portfolio_sha256 = [string]$attemptRecord.Value.route_portfolio.sha256
                        $data.route_card_hashes = @($attemptRecord.RouteCards | ForEach-Object { [string]$_.CardSha256 })
                    }
                }
                if ([int]$state.Policy.schema_version -ge 2 -and $Outcome -in $script:NegativeOutcomes) {
                    if ([string]::IsNullOrWhiteSpace($FailureRecordFile)) { throw 'Negative AttemptEnd requires -FailureRecordFile.' }
                    $failurePath = Resolve-CycleRunFile -RunDirectory $runPath -LiteralPath $FailureRecordFile -Label 'failure record'
                    $failure = Test-MathResearchFailureRecord -FailureRecordFile $failurePath -ExpectedAttemptId ([string]$state.ActiveAttempt.attempt_id) -ArtifactRoot $runPath
                    if ([string]$failure.Value.retry_fingerprint_sha256 -cne [string]$state.ActiveAttempt.route_fingerprint_sha256) { throw 'Failure record retry fingerprint does not match the frozen route.' }
                    $data.failure_record_file = Get-CycleRelativePath -RunDirectory $runPath -LiteralPath $failurePath
                    $data.failure_record_sha256 = [string]$failure.Sha256
                }
                [void](Add-CycleEvent -LedgerDirectory $ledger -Sequence $sequence -RunId $state.RunId -EventType 'ATTEMPT_END' -PreviousPayloadSha256 $state.HeadPayloadSha256 -Data $data)
            }
            'AuditStart' {
                if ($null -ne $state.ActiveAttempt -or $null -ne $state.ActiveAudit -or $state.AttemptsSinceLastAudit -lt 1) { throw 'AuditStart requires completed attempts since the previous audit and no active work.' }
                if ($state.TotalRoundCount + 1 -gt [int]$state.Policy.total_round_budget) { throw 'No total-round budget remains for AuditStart.' }
                if ([string]::IsNullOrWhiteSpace($AuditTicketFile)) { throw 'AuditStart requires -AuditTicketFile.' }
                $ticket = Read-CycleAuditTicket -RunDirectory $runPath -LiteralPath $AuditTicketFile -State $state
                $expectedAuditId = 'audit-{0}' -f ([int]$state.AuditCount + 1)
                if ([string]$ticket.Value.audit_id -cne $expectedAuditId) { throw "Audit id must be the next monotone id '$expectedAuditId'." }
                $data = [ordered]@{ audit_id=[string]$ticket.Value.audit_id; trigger=[string]$ticket.Value.trigger; snapshot_head_sha256=[string]$ticket.Value.snapshot_head_sha256; audit_ticket_file=$ticket.RelativePath; audit_ticket_sha256=$ticket.Sha256; contract_binding_sha256=$state.ContractBindingSha256 }
                [void](Add-CycleEvent -LedgerDirectory $ledger -Sequence $sequence -RunId $state.RunId -EventType 'AUDIT_START' -PreviousPayloadSha256 $state.HeadPayloadSha256 -Data $data)
            }
            'AuditEnd' {
                if ($null -eq $state.ActiveAudit -or [string]::IsNullOrWhiteSpace($AuditResultFile)) { throw 'AuditEnd requires an active audit and -AuditResultFile.' }
                $result = Read-CycleAuditResult -RunDirectory $runPath -LiteralPath $AuditResultFile -State $state
                $nextFile = $null; $nextSha = $null; $nextCycle = $null; $nextTicketHashes = @()
                if (-not [string]::IsNullOrWhiteSpace($NextTicketsFile)) {
                    if ($result.Action -in @('approve-completion','pause','amendment-required')) { throw 'This audit action may not bind next research tickets.' }
                    $nextPath = Resolve-CycleRunFile -RunDirectory $runPath -LiteralPath $NextTicketsFile -Label 'next ticket manifest'
                    $nextRead = Read-CycleJsonFile -LiteralPath $nextPath -Label 'next ticket manifest'
                    $next = Get-CycleTicketRecords -Manifest $nextRead.Value -Label 'next ticket manifest'
                    if ([int]$state.Policy.schema_version -eq 3 -and [int]$nextRead.Value.schema_version -ne 3) { throw 'Prompt v6 audits must bind ticket manifest schema 3.' }
                    if (-not (Test-CycleKey -Object $nextRead.Value -Key 'source_audit_id') -or [string]$nextRead.Value.source_audit_id -cne [string]$state.ActiveAudit.audit_id) { throw 'Next ticket manifest must bind the active audit id.' }
                    $expectedCycleNumber = [int](([string]$state.CurrentCycleId).Substring(6)) + 1
                    if ($next.CycleId -cne "cycle-$expectedCycleNumber") { throw 'Next ticket manifest has the wrong cycle_id.' }
                    if ([int]$state.Policy.schema_version -eq 3) {
                        $accepted = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
                        foreach ($entry in @($result.AcceptedRouteCards)) { [void]$accepted.Add([string]$entry.card_sha256) }
                        foreach ($record in @($next.Records)) {
                            if (-not $record.Ticket.Contains('source_route_card')) {
                                $matchesPendingCard = @($state.PendingRouteCards.Values | Where-Object { [string]$_.card.route_id -ceq [string]$record.Ticket.route_id })
                                if ($matchesPendingCard.Count -gt 0) { throw 'A ticket using a discovered route must bind its audit-accepted route card.' }
                            }
                            if ($record.Ticket.Contains('source_route_card')) {
                                $source = $record.Ticket.source_route_card
                                $cardHash = [string]$source.card_sha256
                                if (-not $accepted.Contains($cardHash) -or -not $state.PendingRouteCards.Contains($cardHash)) { throw 'Next ticket references a route card not accepted by this audit.' }
                                $stored = $state.PendingRouteCards[$cardHash]
                                $card = $stored.card
                                if ([string]$source.source_attempt_id -cne [string]$stored.source_attempt_id -or
                                    [string]$record.Ticket.route_id -cne [string]$card.route_id -or
                                    [string]$record.Ticket.route_family_id -cne [string]$card.route_family_id -or
                                    [string]$record.Ticket.mechanism_id -cne [string]$card.mechanism_id -or
                                    [string]$record.Ticket.bottleneck_id -cne [string]$card.bottleneck_id -or
                                    [string]$record.Ticket.decision_question -cne [string]$card.decision_question -or
                                    [string]$record.Ticket.search_domain -cne [string]$card.search_domain -or
                                    [string]$record.Ticket.success_signal -cne [string]$card.success_signal -or
                                    [string]$record.Ticket.stop_signal -cne [string]$card.stop_signal -or
                                    [string]$record.Ticket.reopen_condition -cne [string]$card.reopen_condition) { throw 'Next ticket changed an accepted route card.' }
                            }
                        }
                    }
                    $nextFile = Get-CycleRelativePath -RunDirectory $runPath -LiteralPath $nextPath
                    $nextSha = $nextRead.Sha256
                    $nextCycle = $next.CycleId
                    $nextTicketHashes = @($next.Records | ForEach-Object { [ordered]@{ ticket_id=$_.TicketId; ticket_sha256=$_.TicketSha256 } })
                }
                elseif ($result.Action -in @('continue','pivot-within-contract','reject-completion')) { throw 'A continuing audit action requires -NextTicketsFile.' }
                $completionAuthorized = ($result.Action -eq 'approve-completion' -and $result.AllPass)
                $data = [ordered]@{ audit_id=[string]$state.ActiveAudit.audit_id; audit_result_file=$result.RelativePath; audit_result_sha256=$result.Sha256; action=$result.Action; all_reports_pass=[bool]$result.AllPass; completion_authorized=[bool]$completionAuthorized; next_tickets_file=$nextFile; next_tickets_sha256=$nextSha; next_cycle_id=$nextCycle; next_ticket_hashes=$nextTicketHashes }
                if ([int]$state.Policy.schema_version -eq 3) { $data.accepted_route_cards = @($result.AcceptedRouteCards) }
                [void](Add-CycleEvent -LedgerDirectory $ledger -Sequence $sequence -RunId $state.RunId -EventType 'AUDIT_END' -PreviousPayloadSha256 $state.HeadPayloadSha256 -Data $data)
            }
            'ReturnCheck' {
                if ($null -ne $state.ActiveAttempt -or $null -ne $state.ActiveAudit -or $state.AuditDue -or $state.AttemptsSinceLastAudit -ne 0) { throw 'ReturnCheck requires a completed closing/cycle audit and no active work.' }
                if ($Completion -and -not $state.CompletionAuthorized) { throw 'Completion ReturnCheck requires a unanimous completion audit.' }
                $data = [ordered]@{ completion=[bool]$Completion; completion_authorized=[bool]$state.CompletionAuthorized }
                [void](Add-CycleEvent -LedgerDirectory $ledger -Sequence $sequence -RunId $state.RunId -EventType 'RETURN_CHECKED' -PreviousPayloadSha256 $state.HeadPayloadSha256 -Data $data)
            }
        }
        return Convert-CycleStateForOutput -State (Read-CycleLedgerStateInternal -RunDirectory $runPath)
    }
    finally { Exit-CycleLease -Lease $lease }
}

function Invoke-MathResearchCycleReturnCheck {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$RunDirectory, [switch]$Completion)
    return Invoke-MathResearchCycleAction -Action ReturnCheck -RunDirectory $RunDirectory -Completion:$Completion
}

Export-ModuleMember -Function @(
    'Initialize-MathResearchCycleLedger', 'Verify-MathResearchCycleLedger',
    'Save-MathResearchCycleCheckpoint', 'Invoke-MathResearchCycleReturnCheck',
    'Invoke-MathResearchCycleAction'
)
