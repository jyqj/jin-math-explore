[CmdletBinding(DefaultParameterSetName = 'Existing')]
param(
    [Parameter(Mandatory = $true, ParameterSetName = 'Existing')]
    [string]$ProjectDirectory,

    [Parameter(Mandatory = $true, ParameterSetName = 'Slot')]
    [string]$VaultRoot,

    [Parameter(Mandatory = $true, ParameterSetName = 'Slot')]
    [string]$ProjectDirectoryName,

    [Parameter(Mandatory = $true)]
    [ValidateSet('none','active','paused','complete','blocked','cancelled','unknown')]
    [string]$GoalStatus
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)

# This entry point is deliberately a read-only classifier.  It never invokes a
# legacy controller, launcher, external worker, or Goal-control operation.

function Assert-UniqueJsonProperties {
    param([Parameter(Mandatory = $true)][Text.Json.JsonElement]$Element, [Parameter(Mandatory = $true)][string]$Path)
    if ($Element.ValueKind -eq [Text.Json.JsonValueKind]::Object) {
        $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        foreach ($property in $Element.EnumerateObject()) {
            if (-not $seen.Add($property.Name)) { throw "Duplicate JSON property '$($property.Name)' at $Path." }
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

function Read-StrictJsonObject {
    param([Parameter(Mandatory = $true)][string]$LiteralPath, [Parameter(Mandatory = $true)][string]$Label)
    if (-not (Test-Path -LiteralPath $LiteralPath -PathType Leaf)) { throw "$Label is missing: $LiteralPath" }
    $bytes = [IO.File]::ReadAllBytes($LiteralPath)
    $text = [Text.UTF8Encoding]::new($false, $true).GetString($bytes)
    $options = [Text.Json.JsonDocumentOptions]::new()
    $options.AllowTrailingCommas = $false
    $options.CommentHandling = [Text.Json.JsonCommentHandling]::Disallow
    $options.MaxDepth = 64
    try { $document = [Text.Json.JsonDocument]::Parse($text, $options) }
    catch { throw "$Label is not strict JSON: $($_.Exception.Message)" }
    try {
        if ($document.RootElement.ValueKind -ne [Text.Json.JsonValueKind]::Object) { throw "$Label must be a JSON object." }
        Assert-UniqueJsonProperties -Element $document.RootElement -Path '$'
    }
    finally { $document.Dispose() }
    return ($text | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String)
}

function Assert-NoReparsePointChain {
    param([Parameter(Mandatory = $true)][string]$LiteralPath, [switch]$AllowMissingLeaf)
    $full = [IO.Path]::GetFullPath($LiteralPath).TrimEnd('\')
    if (-not (Test-Path -LiteralPath $full)) {
        if (-not $AllowMissingLeaf) { throw "Path is missing: $full" }
        $cursorPath = Split-Path -Parent $full
    }
    else { $cursorPath = $full }
    while (-not [string]::IsNullOrWhiteSpace($cursorPath) -and (Test-Path -LiteralPath $cursorPath)) {
        $item = Get-Item -LiteralPath $cursorPath -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Reparse point is forbidden in startup path: $($item.FullName)" }
        $parent = Split-Path -Parent $item.FullName
        if ($parent -eq $item.FullName) { break }
        $cursorPath = $parent
    }
    return $full
}

function Test-PathInside {
    param([Parameter(Mandatory = $true)][string]$Child, [Parameter(Mandatory = $true)][string]$Directory)
    $childFull = [IO.Path]::GetFullPath($Child)
    $directoryFull = [IO.Path]::GetFullPath($Directory).TrimEnd('\') + '\'
    return $childFull.StartsWith($directoryFull, [StringComparison]::OrdinalIgnoreCase)
}

function Assert-SafeLeafName {
    param([Parameter(Mandatory = $true)][string]$Value, [Parameter(Mandatory = $true)][string]$Label)
    if ([string]::IsNullOrWhiteSpace($Value) -or $Value -ne (Split-Path -Leaf $Value) -or $Value -match '[<>:"/\\|?*]' -or $Value.EndsWith('.') -or $Value.EndsWith(' ')) {
        throw "$Label must be one safe leaf filename."
    }
}

function Assert-LowerSha256 {
    param([Parameter(Mandatory = $true)][string]$Value, [Parameter(Mandatory = $true)][string]$Label)
    if ($Value -cnotmatch '^[0-9a-f]{64}$') { throw "$Label must be lowercase SHA-256." }
}

function Get-FileSha256 {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    return (Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-NormalizedTextSha256 {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    $text = [IO.File]::ReadAllText($LiteralPath, [Text.UTF8Encoding]::new($false, $true)) -replace "`r`n", "`n"
    if ($text.Contains("`r")) { throw "Text file contains an isolated CR: $LiteralPath" }
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.UTF8Encoding]::new($false).GetBytes($text))).ToLowerInvariant()
}

function Get-TextSha256 {
    param([Parameter(Mandatory = $true)][string]$Text)
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.UTF8Encoding]::new($false).GetBytes($Text))).ToLowerInvariant()
}

function Test-ExactKeys {
    param(
        [Parameter(Mandatory = $true)]$Object,
        [Parameter(Mandatory = $true)][string[]]$Required,
        [string[]]$Optional = @()
    )
    if ($Object -isnot [Collections.IDictionary]) { return $false }
    foreach ($key in $Required) { if (-not $Object.Contains($key)) { return $false } }
    $allowed = @($Required + $Optional)
    return @($Object.Keys | Where-Object { [string]$_ -cnotin $allowed }).Count -eq 0
}

function Test-NonnegativeJsonInteger {
    param($Value)
    if ($null -eq $Value) { return $false }
    if ($Value.GetType().Name -cnotin @('Byte','SByte','Int16','UInt16','Int32','UInt32','Int64','UInt64')) { return $false }
    try { return [decimal]$Value -ge 0 }
    catch { return $false }
}

function Test-JsonArray {
    param($Value)
    return $null -ne $Value -and $Value.GetType().IsArray
}

function Test-JsonDeepEqual {
    param($Left, $Right)
    if ($null -eq $Left -or $null -eq $Right) { return $null -eq $Left -and $null -eq $Right }
    if ($Left -is [Collections.IDictionary] -or $Right -is [Collections.IDictionary]) {
        if ($Left -isnot [Collections.IDictionary] -or $Right -isnot [Collections.IDictionary] -or $Left.Count -ne $Right.Count) { return $false }
        foreach ($key in $Left.Keys) {
            if (-not $Right.Contains($key) -or -not (Test-JsonDeepEqual -Left $Left[$key] -Right $Right[$key])) { return $false }
        }
        return $true
    }
    if ((Test-JsonArray $Left) -or (Test-JsonArray $Right)) {
        if (-not (Test-JsonArray $Left) -or -not (Test-JsonArray $Right) -or $Left.Count -ne $Right.Count) { return $false }
        for ($index = 0; $index -lt $Left.Count; $index++) {
            if (-not (Test-JsonDeepEqual -Left $Left[$index] -Right $Right[$index])) { return $false }
        }
        return $true
    }
    if ($Left.GetType().Name -cne $Right.GetType().Name) { return $false }
    return $Left -ceq $Right
}

function Test-FilePointer {
    param($Pointer, [string]$ExpectedPath, [string]$ExpectedSha256)
    return (Test-ExactKeys -Object $Pointer -Required @('path','sha256')) -and
        [string]$Pointer.path -ceq $ExpectedPath -and [string]$Pointer.sha256 -ceq $ExpectedSha256
}

function Read-StrictJsonText {
    param([Parameter(Mandatory = $true)][string]$Text, [Parameter(Mandatory = $true)][string]$Label)
    $options = [Text.Json.JsonDocumentOptions]::new()
    $options.AllowTrailingCommas = $false
    $options.CommentHandling = [Text.Json.JsonCommentHandling]::Disallow
    $options.MaxDepth = 64
    try { $document = [Text.Json.JsonDocument]::Parse($Text, $options) }
    catch { throw "$Label is not strict JSON: $($_.Exception.Message)" }
    try {
        if ($document.RootElement.ValueKind -ne [Text.Json.JsonValueKind]::Object) { throw "$Label must be a JSON object." }
        Assert-UniqueJsonProperties -Element $document.RootElement -Path '$'
    }
    finally { $document.Dispose() }
    return ($Text | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String)
}

function Test-CurrentUtcTimestamp {
    param([Parameter(Mandatory = $true)][string]$Value)
    if ($Value -cnotmatch '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,7})?Z$') { return $false }
    $parsed = [DateTimeOffset]::MinValue
    if (-not [DateTimeOffset]::TryParse($Value, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::AssumeUniversal -bor [Globalization.DateTimeStyles]::AdjustToUniversal, [ref]$parsed)) { return $false }
    return $parsed -le [DateTimeOffset]::UtcNow.AddMinutes(5)
}

function Resolve-ProjectRelativePath {
    param(
        [Parameter(Mandatory = $true)][string]$ProjectPath,
        [Parameter(Mandatory = $true)][string]$RelativePath,
        [Parameter(Mandatory = $true)][string]$RequiredRoot,
        [Parameter(Mandatory = $true)][ValidateSet('Leaf','Container')][string]$PathType
    )
    if ([string]::IsNullOrWhiteSpace($RelativePath) -or [IO.Path]::IsPathRooted($RelativePath) -or $RelativePath.Contains(':')) { throw 'Project-relative path is not relative.' }
    $segments = @($RelativePath -split '[\\/]')
    $minimumSegments = if ($RequiredRoot -ceq '.') { 1 } else { 2 }
    if ($segments.Count -lt $minimumSegments -or @($segments | Where-Object { [string]::IsNullOrEmpty([string]$_) -or [string]$_ -ceq '.' -or [string]$_ -ceq '..' }).Count -gt 0) {
        throw 'Project-relative path contains an empty, dot, or dot-dot segment.'
    }
    $full = [IO.Path]::GetFullPath((Join-Path $ProjectPath $RelativePath))
    $root = [IO.Path]::GetFullPath((Join-Path $ProjectPath $RequiredRoot))
    if (-not (Test-PathInside -Child $full -Directory $root)) { throw 'Project-relative path escapes its required root.' }
    if ($PathType -eq 'Leaf' -and -not (Test-Path -LiteralPath $full -PathType Leaf)) { throw 'Project-relative file is missing.' }
    if ($PathType -eq 'Container' -and -not (Test-Path -LiteralPath $full -PathType Container)) { throw 'Project-relative directory is missing.' }
    Assert-NoReparsePointChain -LiteralPath $full | Out-Null
    return $full
}

function Assert-ImmutableRawPointer {
    param(
        [Parameter(Mandatory = $true)]$Pointer,
        [Parameter(Mandatory = $true)][string]$ProjectPath,
        [Parameter(Mandatory = $true)][string]$Label,
        [string]$RequiredRoot = '.'
    )
    if (-not (Test-ExactKeys -Object $Pointer -Required @('path','sha256'))) { throw "$Label pointer is invalid." }
    Assert-LowerSha256 -Value ([string]$Pointer.sha256) -Label "$Label hash"
    $relative = [string]$Pointer.path
    if (-not (Test-ContractRelativePathSyntax -Value $relative -AllowLeaf) -or $relative.Contains('\')) { throw "$Label path is not one canonical project-relative path." }
    if ($relative.Equals('project.json',[StringComparison]::OrdinalIgnoreCase) -or
        $relative.StartsWith('state/staging/',[StringComparison]::OrdinalIgnoreCase) -or
        $relative.IndexOf('/staging/',[StringComparison]::OrdinalIgnoreCase) -ge 0 -or
        (Split-Path -Leaf $relative) -ieq 'final.build-v8.tmp') {
        throw "$Label must point to already-published immutable material, not mutable authority/staging."
    }
    $path = Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath $relative -RequiredRoot $RequiredRoot -PathType Leaf
    if ((Get-FileSha256 -LiteralPath $path) -cne [string]$Pointer.sha256) { throw "$Label hash mismatches." }
    return $path
}

function Assert-V8Counters {
    param([Parameter(Mandatory = $true)]$Object, [Parameter(Mandatory = $true)][string]$Label)
    $counters = if ($Object -is [Collections.IDictionary] -and $Object.Contains('counters')) { $Object.counters } else { $Object }
    if (-not (Test-ExactKeys -Object $counters -Required @('attempt_count','audit_count','total_round_count','attempts_since_last_audit','audit_due'))) { throw "$Label shape is invalid." }
    foreach ($key in @('attempt_count','audit_count','total_round_count','attempts_since_last_audit')) { if (-not (Test-NonnegativeJsonInteger $counters[$key])) { throw "$Label.$key is invalid." } }
    if ($counters.audit_due -isnot [bool] -or [decimal]$counters.total_round_count -ne ([decimal]$counters.attempt_count + [decimal]$counters.audit_count) -or [decimal]$counters.attempts_since_last_audit -gt [decimal]$counters.attempt_count) { throw "$Label is inconsistent." }
    return $counters
}

function Test-V8CountersEqual {
    param($Left,$Right)
    foreach ($key in @('attempt_count','audit_count','total_round_count','attempts_since_last_audit','audit_due')) { if ([string]$Left[$key] -cne [string]$Right[$key]) { return $false } }
    return $true
}

function Test-ContractPointer {
    param($Pointer, [Collections.IDictionary]$Expected)
    if ($Pointer -isnot [Collections.IDictionary]) { return $false }
    $pointerHash = if ($Pointer.Contains('binding_sha256')) { [string]$Pointer.binding_sha256 } elseif ($Pointer.Contains('sha256')) { [string]$Pointer.sha256 } else { '' }
    return (
        $Pointer.Contains('path') -and [string]$Pointer.path -ceq [string]$Expected.path -and
        $Pointer.Contains('version') -and [string]$Pointer.version -ceq [string]$Expected.version -and
        $pointerHash -ceq [string]$Expected.binding_sha256
    )
}

function Test-RunPointer {
    param($Pointer, [Collections.IDictionary]$Expected)
    if ($Pointer -isnot [Collections.IDictionary]) { return $false }
    return (
        $Pointer.Contains('id') -and [string]$Pointer.id -ceq [string]$Expected.id -and
        $Pointer.Contains('path') -and [string]$Pointer.path -ceq [string]$Expected.path -and
        $Pointer.Contains('status') -and [string]$Pointer.status -ceq [string]$Expected.status
    )
}

function Test-HostGoalPointer {
    param($Pointer, [Collections.IDictionary]$Expected)
    if (-not (Test-ExactKeys -Object $Pointer -Required @('thread_id_available','thread_id','objective_raw_sha256'))) { return $false }
    if ($Pointer.thread_id_available -isnot [bool] -or [bool]$Pointer.thread_id_available -ne [bool]$Expected.thread_id_available) { return $false }
    if ([string]$Pointer.objective_raw_sha256 -cne [string]$Expected.objective_raw_sha256) { return $false }
    if ([bool]$Expected.thread_id_available) { return [string]$Pointer.thread_id -ceq [string]$Expected.thread_id }
    return $null -eq $Pointer.thread_id -and $null -eq $Expected.thread_id
}

function Get-UniqueContractJsonBlock {
    param(
        [Parameter(Mandatory = $true)][string]$NormalizedContract,
        [Parameter(Mandatory = $true)][ValidateSet('math-research-cycle-policy','math-research-initial-tickets')][string]$Name
    )
    $tag = "<!-- $Name"
    $tagCount = [regex]::Matches($NormalizedContract, [regex]::Escape($tag)).Count
    $pattern = [regex]::Escape("<!-- $Name`n") + '(?<body>.*?)' + [regex]::Escape("`n-->")
    $matches = [regex]::Matches($NormalizedContract, $pattern, [Text.RegularExpressions.RegexOptions]::Singleline)
    if ($tagCount -ne 1 -or $matches.Count -ne 1) { throw "Contract must contain exactly one valid $Name block." }
    $body = $matches[0].Groups['body'].Value
    if ([string]::IsNullOrWhiteSpace($body)) { throw "$Name block is empty." }
    $options = [Text.Json.JsonDocumentOptions]::new()
    $options.AllowTrailingCommas = $false
    $options.CommentHandling = [Text.Json.JsonCommentHandling]::Disallow
    $options.MaxDepth = 64
    try { $document = [Text.Json.JsonDocument]::Parse($body, $options) }
    catch { throw "$Name block is not strict JSON." }
    try {
        if ($document.RootElement.ValueKind -ne [Text.Json.JsonValueKind]::Object) { throw "$Name block must be a JSON object." }
        Assert-UniqueJsonProperties -Element $document.RootElement -Path '$'
    }
    finally { $document.Dispose() }
    return [pscustomobject]@{ Body=$body; Object=($body | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String) }
}

function Test-ResolvedContractString {
    param($Value)
    if ($Value -isnot [string] -or [string]::IsNullOrWhiteSpace($Value) -or $Value.Length -gt 4096 -or $Value -match '[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]') { return $false }
    return $Value -notmatch '(?i)(replace[_ -]?with|placeholder|requires user decision|\[[^\]]*\]|^unknown$|64 lowercase hex)'
}

function Test-ContractRelativePathSyntax {
    param($Value, [switch]$AllowLeaf)
    if (-not (Test-ResolvedContractString $Value) -or [IO.Path]::IsPathRooted([string]$Value) -or ([string]$Value).Contains(':')) { return $false }
    $segments = @(([string]$Value) -split '[\\/]')
    if ((-not $AllowLeaf -and $segments.Count -lt 2) -or @($segments | Where-Object { [string]::IsNullOrEmpty([string]$_) -or [string]$_ -ceq '.' -or [string]$_ -ceq '..' }).Count -gt 0) { return $false }
    return $true
}

function Test-AllowedWorkerToolName {
    param($Value)
    return $Value-is[string]-and[string]$Value-cin@('apply_patch','collaboration.spawn_agent','collaboration.send_message','collaboration.wait_agent','shell_command','web__run')
}

function Assert-V8TicketBody {
    param(
        [Parameter(Mandatory=$true)]$Ticket,
        [Parameter(Mandatory=$true)]$Metadata,
        [Parameter(Mandatory=$true)]$MetadataIntegers,
        [Parameter(Mandatory=$true)][string]$ProjectPath,
        $ActiveRun=$null,
        $ActiveContract=$null
    )
    $ticketKeys=@('ticket_id','role','planned_lifecycle_slot','route_id','route_fingerprint_sha256','attempt_kind','route_family_id','mechanism_id','bottleneck_id','decision_question','input_artifacts','search_domain','success_signal','stop_signal','allowed_tools','source_network_policy','filesystem_scope','resource_caps','dependencies','evidence_grade_required','required_outputs','failure_return','reopen_condition')
    if([string]$Ticket.role-ceq'verifier'){$ticketKeys+=@('candidate_artifact')}
    if(-not(Test-ExactKeys -Object $Ticket -Required $ticketKeys)){throw 'Ticket body shape is incomplete or has unknown keys.'}
    Assert-SafeLeafName -Value ([string]$Ticket.ticket_id) -Label 'ticket ID'
    foreach($key in @('planned_lifecycle_slot','route_id','attempt_kind','route_family_id','mechanism_id','bottleneck_id','decision_question','search_domain','success_signal','stop_signal','evidence_grade_required','reopen_condition')){if(-not(Test-ResolvedContractString $Ticket[$key])){throw "Ticket $key is unresolved."}}
    if([string]$Ticket.role-cnotin@('solver','verifier','skeptic_quantifiers','skeptic_strategy','theory_tool_scout')){throw 'Ticket role is outside the closed set.'};Assert-LowerSha256 -Value ([string]$Ticket.route_fingerprint_sha256) -Label 'ticket route fingerprint'
    if(-not(Test-JsonArray $Ticket.input_artifacts)-or@($Ticket.input_artifacts).Count-lt1){throw 'Ticket must bind at least one input artifact.'}
    foreach($artifact in @($Ticket.input_artifacts)){if(-not(Test-ContractRelativePathSyntax $artifact.path)){throw 'Ticket input artifact pointer is invalid.'};$null=Assert-ImmutableRawPointer -Pointer $artifact -ProjectPath $ProjectPath -Label 'ticket input artifact'}
    if(-not(Test-JsonArray $Ticket.allowed_tools)-or@($Ticket.allowed_tools).Count-lt1){throw 'Ticket allowed_tools is empty.'}
    $ticketToolSet=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($tool in @($Ticket.allowed_tools)){if(-not(Test-AllowedWorkerToolName $tool)-or-not$ticketToolSet.Add([string]$tool)-or[string]$tool-cnotin@($Metadata.allowed_worker_tools)){throw 'Ticket allowed_tools is not a unique subset of the Contract worker-tool allowlist.'}}
    if([string]$Metadata.web_search-ceq'denied'-and'web__run'-cin@($Ticket.allowed_tools)){throw 'A network-denied ticket cannot authorize web__run.'}
    $network=$Ticket.source_network_policy;if(-not(Test-ExactKeys -Object $network -Required @('web','allowed_source_classes','network_destinations'))-or[string]$network.web-cne[string]$Metadata.web_search-or-not(Test-JsonArray $network.allowed_source_classes)-or@($network.allowed_source_classes).Count-lt1-or-not(Test-JsonArray $network.network_destinations)-or([string]$network.web-ceq'denied'-and@($network.network_destinations).Count-ne0)){throw 'Ticket source/network policy expands or contradicts Contract.'}
    $filesystem=$Ticket.filesystem_scope;if(-not(Test-ExactKeys -Object $filesystem -Required @('read_paths','writable_staging_path'))-or-not(Test-JsonArray $filesystem.read_paths)-or@($filesystem.read_paths).Count-lt1-or@($filesystem.read_paths|Where-Object{-not(Test-ContractRelativePathSyntax $_)}).Count-ne0-or-not(Test-ContractRelativePathSyntax $filesystem.writable_staging_path)){throw 'Ticket filesystem scope is invalid.'};if($null-ne$ActiveRun-and-not([string]$filesystem.writable_staging_path).Replace('\','/').StartsWith((([string]$ActiveRun.path).Replace('\','/')+'/staging/'),[StringComparison]::OrdinalIgnoreCase)){throw 'Ticket writable path is outside active-run staging.'}
    $caps=$Ticket.resource_caps;if(-not(Test-ExactKeys -Object $caps -Required @('child_agents','tool_calls','runtime_minutes','max_output_bytes'))){throw 'Ticket resource caps shape is invalid.'};foreach($key in @('child_agents','tool_calls','runtime_minutes','max_output_bytes')){if(-not(Test-NonnegativeJsonInteger $caps[$key])){throw 'Ticket resource cap is not a nonnegative integer.'}};if([int64]$caps.child_agents-gt[int64]$MetadataIntegers.max_child_agents-or([int64]$MetadataIntegers.max_runtime_minutes-gt0-and[int64]$caps.runtime_minutes-gt[int64]$MetadataIntegers.max_runtime_minutes)-or[int64]$caps.tool_calls-gt[int64]$MetadataIntegers.max_ticket_tool_calls-or[int64]$caps.max_output_bytes-lt1-or[int64]$caps.max_output_bytes-gt[int64]$MetadataIntegers.max_ticket_output_bytes){throw 'Ticket resource caps exceed Contract cycle-policy caps.'}
    if(-not(Test-JsonArray $Ticket.dependencies)){throw 'Ticket dependencies must be an array.'}
    $resolvedDependencies=[Collections.Generic.List[object]]::new();$dependencyIds=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($dependency in @($Ticket.dependencies)){
        if(-not(Test-ExactKeys -Object $dependency -Required @('ticket_id','path','sha256'))){throw 'Ticket dependency binding is invalid.'};Assert-SafeLeafName -Value ([string]$dependency.ticket_id) -Label 'ticket dependency ID';Assert-LowerSha256 -Value ([string]$dependency.sha256) -Label 'ticket dependency hash'
        if(-not$dependencyIds.Add([string]$dependency.ticket_id)){throw 'Ticket dependency IDs must be unique.'}
        $dependencyPath=Assert-ImmutableRawPointer -Pointer ([ordered]@{path=$dependency.path;sha256=$dependency.sha256}) -ProjectPath $ProjectPath -Label 'ticket dependency completion'
        $resolvedDependencies.Add([pscustomobject]@{Binding=$dependency;Path=$dependencyPath})
    }
    if([string]$Ticket.role-ceq'verifier'){
        if(@($Ticket.dependencies).Count-lt1){throw 'A verifier ticket must bind at least one completed dependency.'}
        if(-not(Test-ExactKeys -Object $Ticket.candidate_artifact -Required @('path','sha256'))-or-not(Test-ContractRelativePathSyntax $Ticket.candidate_artifact.path)){throw 'Verifier candidate_artifact pointer is invalid.'}
        $null=Assert-ImmutableRawPointer -Pointer $Ticket.candidate_artifact -ProjectPath $ProjectPath -Label 'verifier candidate artifact'
        if(@($Ticket.input_artifacts|Where-Object{Test-JsonDeepEqual -Left $_ -Right $Ticket.candidate_artifact}).Count-ne1){throw 'Verifier candidate_artifact must hash-match and exactly equal one input_artifacts member.'}
        $completionCount=0
        foreach($resolved in $resolvedDependencies){
            $dependency=$resolved.Binding
            if([string]$dependency.ticket_id-ceq[string]$Ticket.ticket_id-or[string]$dependency.sha256-ceq[string]$Ticket.candidate_artifact.sha256){throw 'Verifier dependency cannot self-reference the verifier ticket or masquerade as its candidate artifact.'}
            $completion=Read-StrictJsonObject -LiteralPath $resolved.Path -Label 'verifier ticket-completion dependency'
            if([string]$completion.schema-ceq'math-research-ticket-completion/v8'){
                if(-not(Test-ExactKeys -Object $completion -Required @('schema','project_id','contract','run','ticket_id','role','status','output','candidate_artifact','completed_at_utc'))-or-not(Test-ExactKeys -Object $completion.contract -Required @('path','version','binding_sha256'))-or-not(Test-ExactKeys -Object $completion.run -Required @('id','path'))){throw 'Verifier ticket-completion shape is invalid.'}
                foreach($raw in @($completion.output,$completion.candidate_artifact)){$null=Assert-ImmutableRawPointer -Pointer $raw -ProjectPath $ProjectPath -Label 'ticket-completion raw pointer'}
                $stagingPrefix=([string]$Ticket.filesystem_scope.writable_staging_path).Replace('\','/').TrimEnd('/')+'/'
                if($null-eq$ActiveContract-or[string]$completion.project_id-cne[string]$Metadata.project_id-or-not(Test-ContractPointer -Pointer $completion.contract -Expected $ActiveContract)-or[string]$completion.run.id-cne[string]$ActiveRun.id-or[string]$completion.run.path-cne[string]$ActiveRun.path-or[string]$completion.ticket_id-cne[string]$dependency.ticket_id-or[string]$completion.role-cne'solver'-or[string]$completion.status-cne'closed'-or-not(Test-JsonDeepEqual -Left $completion.candidate_artifact -Right $Ticket.candidate_artifact)-or([string]$completion.output.path).Replace('\','/').StartsWith($stagingPrefix,[StringComparison]::OrdinalIgnoreCase)-or-not(Test-CurrentUtcTimestamp -Value ([string]$completion.completed_at_utc))){throw 'Verifier ticket-completion is not a closed solver completion bound to the same candidate/Contract/run or publishes into verifier staging.'}
                $completionCount++
            }
        }
        if($completionCount-lt1){throw 'Verifier requires at least one exact solver ticket-completion dependency.'}
    }
    if(-not(Test-JsonArray $Ticket.required_outputs)-or@($Ticket.required_outputs).Count-lt1){throw 'Ticket required_outputs is empty.'};foreach($output in @($Ticket.required_outputs)){if(-not(Test-ExactKeys -Object $output -Required @('path','schema','sha256_on_return'))-or-not(Test-ContractRelativePathSyntax $output.path -AllowLeaf)-or-not(Test-ResolvedContractString $output.schema)-or[string]$output.sha256_on_return-cne'required'){throw 'Ticket required output is invalid.'}}
    $requiredFailure=@('status','failed_step','reason','partial_artifact_hashes','reopen_condition');if(-not(Test-ExactKeys -Object $Ticket.failure_return -Required @('schema','required_fields'))-or[string]$Ticket.failure_return.schema-cne'math-research-ticket-failure/v1'-or(@($Ticket.failure_return.required_fields)-join'|')-cne($requiredFailure-join'|')){throw 'Ticket failure-return schema is invalid.'}
}

function Test-RawPointerEqual {
    param($Left,$Right)
    return (Test-ExactKeys -Object $Left -Required @('path','sha256')) -and (Test-ExactKeys -Object $Right -Required @('path','sha256')) -and [string]$Left.path -ceq [string]$Right.path -and [string]$Left.sha256 -ceq [string]$Right.sha256
}

function Assert-VerifierPassResultV8 {
    param($Record,[string]$ProjectPath,[string]$ExpectedProjectId,$ExpectedContract,$ExpectedRun,$ExpectedCandidate,[string]$ExpectedAttemptId)
    if(-not(Test-ExactKeys -Object $Record -Required @('schema','project_id','contract','run','ticket_id','role','candidate_artifact','verdict','checked_at_utc'))-or
        -not(Test-ExactKeys -Object $Record.contract -Required @('path','version','binding_sha256'))-or-not(Test-ExactKeys -Object $Record.run -Required @('id','path'))){throw 'Verifier PASS result shape is invalid.'}
    Assert-SafeLeafName -Value ([string]$Record.ticket_id) -Label 'verifier PASS ticket_id'
    $null=Assert-ImmutableRawPointer -Pointer $Record.candidate_artifact -ProjectPath $ProjectPath -Label 'verifier PASS candidate'
    if([string]$Record.schema-cne'math-research-verifier-result/v8'-or[string]$Record.project_id-cne$ExpectedProjectId-or-not(Test-ContractPointer -Pointer $Record.contract -Expected $ExpectedContract)-or[string]$Record.run.id-cne[string]$ExpectedRun.id-or[string]$Record.run.path-cne[string]$ExpectedRun.path-or[string]$Record.ticket_id-ceq$ExpectedAttemptId-or[string]$Record.role-cne'verifier'-or-not(Test-RawPointerEqual -Left $Record.candidate_artifact -Right $ExpectedCandidate)-or[string]$Record.verdict-cne'PASS'-or-not(Test-CurrentUtcTimestamp -Value ([string]$Record.checked_at_utc))){throw 'Verifier PASS result is not an independent exact PASS on the claimed candidate/Contract/run.'}
    return $Record
}

function Assert-AttemptOutcomeV8 {
    param($Pointer,[string]$ProjectPath,[string]$ExpectedProjectId,$ExpectedContract,$ExpectedRun)
    $path=Assert-ImmutableRawPointer -Pointer $Pointer -ProjectPath $ProjectPath -Label 'ATTEMPT_END outcome'
    $outcome=Read-StrictJsonObject -LiteralPath $path -Label 'ATTEMPT_END outcome'
    if(-not(Test-ExactKeys -Object $outcome -Required @('schema','project_id','contract','run','attempt_id','outcome','candidate','verifier_completion','completed_at_utc'))-or-not(Test-ExactKeys -Object $outcome.contract -Required @('path','version','binding_sha256'))-or-not(Test-ExactKeys -Object $outcome.run -Required @('id','path'))){throw 'ATTEMPT_END outcome shape is invalid.'}
    Assert-SafeLeafName -Value ([string]$outcome.attempt_id) -Label 'ATTEMPT_END attempt_id'
    if([string]$outcome.schema-cne'math-research-attempt-outcome/v8'-or[string]$outcome.project_id-cne$ExpectedProjectId-or-not(Test-ContractPointer -Pointer $outcome.contract -Expected $ExpectedContract)-or[string]$outcome.run.id-cne[string]$ExpectedRun.id-or[string]$outcome.run.path-cne[string]$ExpectedRun.path-or[string]$outcome.outcome-cnotin@('candidate_found','no_candidate','inconclusive','failed','awaiting_input')-or-not(Test-CurrentUtcTimestamp -Value ([string]$outcome.completed_at_utc))){throw 'ATTEMPT_END outcome identity, Contract, run, closed outcome, or timestamp is invalid.'}
    if([string]$outcome.outcome-cne'candidate_found'){
        if($null-ne$outcome.candidate-or$null-ne$outcome.verifier_completion){throw 'A noncandidate ATTEMPT_END outcome must have null candidate/verifier_completion.'}
        return [pscustomobject]@{Record=$outcome;VerifierTicketId=$null}
    }
    if($null-eq$outcome.candidate-or$null-eq$outcome.verifier_completion){throw 'candidate_found requires immutable candidate and verifier_completion pointers.'}
    $null=Assert-ImmutableRawPointer -Pointer $outcome.candidate -ProjectPath $ProjectPath -Label 'ATTEMPT_END candidate'
    $verificationPath=Assert-ImmutableRawPointer -Pointer $outcome.verifier_completion -ProjectPath $ProjectPath -Label 'ATTEMPT_END verifier completion'
    $verification=Read-StrictJsonObject -LiteralPath $verificationPath -Label 'ATTEMPT_END verifier completion'
    if([string]$verification.schema-ceq'math-research-verifier-result/v8'){
        $null=Assert-VerifierPassResultV8 -Record $verification -ProjectPath $ProjectPath -ExpectedProjectId $ExpectedProjectId -ExpectedContract $ExpectedContract -ExpectedRun $ExpectedRun -ExpectedCandidate $outcome.candidate -ExpectedAttemptId ([string]$outcome.attempt_id)
        $verifiedTicketId=[string]$verification.ticket_id
    }
    elseif([string]$verification.schema-ceq'math-research-ticket-completion/v8'){
        if(-not(Test-ExactKeys -Object $verification -Required @('schema','project_id','contract','run','ticket_id','role','status','output','candidate_artifact','completed_at_utc'))-or-not(Test-ExactKeys -Object $verification.contract -Required @('path','version','binding_sha256'))-or-not(Test-ExactKeys -Object $verification.run -Required @('id','path'))){throw 'Verifier ticket completion shape is invalid.'}
        Assert-SafeLeafName -Value ([string]$verification.ticket_id) -Label 'verifier ticket completion ticket_id'
        foreach($raw in @($verification.output,$verification.candidate_artifact)){$null=Assert-ImmutableRawPointer -Pointer $raw -ProjectPath $ProjectPath -Label 'verifier ticket completion pointer'}
        if([string]$verification.project_id-cne$ExpectedProjectId-or-not(Test-ContractPointer -Pointer $verification.contract -Expected $ExpectedContract)-or[string]$verification.run.id-cne[string]$ExpectedRun.id-or[string]$verification.run.path-cne[string]$ExpectedRun.path-or[string]$verification.ticket_id-ceq[string]$outcome.attempt_id-or[string]$verification.role-cne'verifier'-or[string]$verification.status-cne'closed'-or-not(Test-RawPointerEqual -Left $verification.candidate_artifact -Right $outcome.candidate)-or-not(Test-CurrentUtcTimestamp -Value ([string]$verification.completed_at_utc))){throw 'Verifier ticket completion is not an independent closed verifier record on the claimed candidate.'}
        $resultPath=Assert-ImmutableRawPointer -Pointer $verification.output -ProjectPath $ProjectPath -Label 'verifier ticket completion PASS output';$result=Read-StrictJsonObject -LiteralPath $resultPath -Label 'verifier ticket completion PASS output'
        if([string]$result.ticket_id-cne[string]$verification.ticket_id){throw 'Verifier completion and PASS output bind different ticket IDs.'}
        $null=Assert-VerifierPassResultV8 -Record $result -ProjectPath $ProjectPath -ExpectedProjectId $ExpectedProjectId -ExpectedContract $ExpectedContract -ExpectedRun $ExpectedRun -ExpectedCandidate $outcome.candidate -ExpectedAttemptId ([string]$outcome.attempt_id)
        $verifiedTicketId=[string]$verification.ticket_id
    }
    else{throw 'candidate_found verifier_completion must be an exact verifier result or closed verifier ticket completion.'}
    return [pscustomobject]@{Record=$outcome;VerifierTicketId=$verifiedTicketId}
}

function Assert-CycleAuditSummary {
    param(
        [Parameter(Mandatory=$true)]$Pointer,
        [Parameter(Mandatory=$true)][string]$ProjectPath,
        [Parameter(Mandatory=$true)][string]$ExpectedProjectId,
        [Parameter(Mandatory=$true)]$ExpectedContract,
        [Parameter(Mandatory=$true)]$ExpectedRun,
        [Parameter(Mandatory=$true)][ValidateSet('scheduled','early','terminal')][string]$ExpectedAuditKind,
        [switch]$RequirePass
    )
    $path=Assert-ImmutableRawPointer -Pointer $Pointer -ProjectPath $ProjectPath -Label 'cycle-audit summary'
    $summary=Read-StrictJsonObject -LiteralPath $path -Label 'cycle-audit summary'
    if(-not(Test-ExactKeys -Object $summary -Required @('schema','project_id','contract','run','audit_kind','audit_start_event','plan','candidate','snapshot','reports','completed_at_utc'))-or
        [string]$summary.schema-cne'math-research-cycle-audit-summary/v8'-or[string]$summary.project_id-cne$ExpectedProjectId-or
        -not(Test-ExactKeys -Object $summary.contract -Required @('path','version','binding_sha256'))-or-not(Test-ContractPointer -Pointer $summary.contract -Expected $ExpectedContract)-or
        -not(Test-ExactKeys -Object $summary.run -Required @('id','path'))-or[string]$summary.run.id-cne[string]$ExpectedRun.id-or[string]$summary.run.path-cne[string]$ExpectedRun.path-or
        [string]$summary.audit_kind-cne$ExpectedAuditKind-or-not(Test-CurrentUtcTimestamp -Value ([string]$summary.completed_at_utc))){throw 'Cycle-audit summary identity, kind, Contract, run, or timestamp is invalid.'}
    foreach($name in @('audit_start_event','plan','snapshot')){$null=Assert-ImmutableRawPointer -Pointer $summary[$name] -ProjectPath $ProjectPath -Label "cycle-audit $name"}
    if($ExpectedAuditKind-ceq'terminal'){
        if($null-eq$summary.candidate){throw 'Terminal cycle-audit summary must bind one immutable candidate.'}
        $null=Assert-ImmutableRawPointer -Pointer $summary.candidate -ProjectPath $ProjectPath -Label 'terminal cycle-audit candidate'
    }
    elseif($null-ne$summary.candidate){throw 'Scheduled/early cycle-audit summary candidate must be null.'}
    $roles=@('skeptic_quantifiers','skeptic_strategy','theory_tool_scout')
    if(-not(Test-JsonArray $summary.reports)-or@($summary.reports).Count-ne3){throw 'Cycle-audit summary must contain exactly three ordered role reports.'}
    $reportPointers=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $allPass=$true
    for($index=0;$index-lt3;$index++){
        $entry=$summary.reports[$index]
        if(-not(Test-ExactKeys -Object $entry -Required @('role','report'))-or[string]$entry.role-cne$roles[$index]){throw 'Cycle-audit report entry/role is invalid.'}
        if(-not$reportPointers.Add("$([string]$entry.report.path)|$([string]$entry.report.sha256)")){throw 'Cycle-audit reports must be distinct immutable files.'}
        $reportPath=Assert-ImmutableRawPointer -Pointer $entry.report -ProjectPath $ProjectPath -Label "cycle-audit $($entry.role) report"
        $report=Read-StrictJsonObject -LiteralPath $reportPath -Label "cycle-audit $($entry.role) report"
        if(-not(Test-ExactKeys -Object $report -Required @('schema','project_id','contract','run','role','candidate','snapshot','verdict','new_math_performed','checked_at_utc'))-or
            [string]$report.schema-cne'math-research-cycle-audit-report/v8'-or[string]$report.project_id-cne$ExpectedProjectId-or
            -not(Test-ExactKeys -Object $report.contract -Required @('path','version','binding_sha256'))-or-not(Test-ContractPointer -Pointer $report.contract -Expected $ExpectedContract)-or
            -not(Test-ExactKeys -Object $report.run -Required @('id','path'))-or[string]$report.run.id-cne[string]$ExpectedRun.id-or[string]$report.run.path-cne[string]$ExpectedRun.path-or
            [string]$report.role-cne$roles[$index]-or-not(Test-JsonDeepEqual -Left $report.candidate -Right $summary.candidate)-or-not(Test-RawPointerEqual -Left $report.snapshot -Right $summary.snapshot)-or
            [string]$report.verdict-cnotin@('PASS','FAIL','INCONCLUSIVE')-or($RequirePass-and[string]$report.verdict-cne'PASS')-or$report.new_math_performed-isnot[bool]-or[bool]$report.new_math_performed-or
            -not(Test-CurrentUtcTimestamp -Value ([string]$report.checked_at_utc))){throw 'Cycle-audit report verdict/no-new-math/content binding is invalid.'}
        if([string]$report.verdict-cne'PASS'){$allPass=$false}
    }
    return [pscustomobject]@{Pointer=[ordered]@{path=[string]$Pointer.path;sha256=[string]$Pointer.sha256};Summary=$summary;AllPass=$allPass}
}

function Assert-CycleAuditPlan {
    param(
        [Parameter(Mandatory=$true)]$Pointer,
        [Parameter(Mandatory=$true)][string]$ProjectPath,
        [Parameter(Mandatory=$true)][string]$ExpectedProjectId,
        [Parameter(Mandatory=$true)]$ExpectedContract,
        [Parameter(Mandatory=$true)]$ExpectedRun,
        [Parameter(Mandatory=$true)][long]$Generation,
        [Parameter(Mandatory=$true)]$Counters,
        $CurrentTicket=$null,
        [Parameter(Mandatory=$true)]$ContractEnvelope,
        [Parameter(Mandatory=$true)][ValidateSet('scheduled','early','terminal')][string]$ExpectedAuditKind,
        $ExpectedCandidate=$null
    )
    $planPath=Assert-ImmutableRawPointer -Pointer $Pointer -ProjectPath $ProjectPath -Label 'cycle-audit plan'
    $plan=Read-StrictJsonObject -LiteralPath $planPath -Label 'cycle-audit plan'
    if(-not(Test-ExactKeys -Object $plan -Required @('schema','project_id','contract','run','audit_kind','candidate','snapshot','active_ticket','tickets','started_at_utc'))-or
        [string]$plan.schema-cne'math-research-cycle-audit-plan/v8'-or[string]$plan.project_id-cne$ExpectedProjectId-or
        -not(Test-ExactKeys -Object $plan.contract -Required @('path','version','binding_sha256'))-or-not(Test-ContractPointer -Pointer $plan.contract -Expected $ExpectedContract)-or
        -not(Test-ExactKeys -Object $plan.run -Required @('id','path'))-or[string]$plan.run.id-cne[string]$ExpectedRun.id-or[string]$plan.run.path-cne[string]$ExpectedRun.path-or
        [string]$plan.audit_kind-cne$ExpectedAuditKind-or-not(Test-CurrentUtcTimestamp -Value ([string]$plan.started_at_utc))){throw 'Cycle-audit plan identity, kind, Contract, run, or timestamp is invalid.'}
    $null=Assert-ImmutableRawPointer -Pointer $plan.snapshot -ProjectPath $ProjectPath -Label 'cycle-audit plan snapshot'
    if($ExpectedAuditKind-ceq'terminal'){
        if($null-eq$plan.candidate){throw 'Terminal cycle-audit plan must bind the verified ATTEMPT_END candidate.'}
        $null=Assert-ImmutableRawPointer -Pointer $plan.candidate -ProjectPath $ProjectPath -Label 'terminal cycle-audit plan candidate'
        if($null-ne$ExpectedCandidate-and-not(Test-RawPointerEqual -Left $plan.candidate -Right $ExpectedCandidate)){throw 'Terminal cycle-audit plan candidate differs from the verified attempt outcome.'}
    }
    elseif($null-ne$plan.candidate){throw 'Scheduled/early cycle-audit plan candidate must be null.'}
    $null=Assert-ImmutableRawPointer -Pointer $plan.active_ticket -ProjectPath $ProjectPath -Label 'cycle-audit plan active ticket' -RequiredRoot 'runs'
    if($null-ne$CurrentTicket-and-not(Test-FilePointer -Pointer $plan.active_ticket -ExpectedPath ([string]$CurrentTicket.path) -ExpectedSha256 ([string]$CurrentTicket.sha256))){throw 'AUDIT_START current ticket differs from plan.active_ticket.'}
    $roles=@('skeptic_quantifiers','skeptic_strategy','theory_tool_scout')
    if(-not(Test-JsonArray $plan.tickets)-or@($plan.tickets).Count-ne3){throw 'Cycle-audit plan must freeze exactly three role tickets.'}
    $ticketIds=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal);$ticketPointers=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase);$currentMatches=0
    for($index=0;$index-lt3;$index++){
        $entry=$plan.tickets[$index]
        if(-not(Test-ExactKeys -Object $entry -Required @('role','ticket'))-or[string]$entry.role-cne$roles[$index]){throw 'Cycle-audit ticket roles/order is invalid.'}
        if(-not$ticketPointers.Add("$([string]$entry.ticket.path)|$([string]$entry.ticket.sha256)")){throw 'Cycle-audit role tickets must be three distinct immutable files.'}
        $ticketPath=Assert-ImmutableRawPointer -Pointer $entry.ticket -ProjectPath $ProjectPath -Label "cycle-audit $($entry.role) ticket" -RequiredRoot 'runs'
        $record=Read-StrictJsonObject -LiteralPath $ticketPath -Label "cycle-audit $($entry.role) ticket"
        if(-not(Test-ExactKeys -Object $record -Required @('schema','project_id','control_generation','contract','run','cycle_id','contract_initial_tickets_sha256','counter_snapshot','ticket'))-or
            [string]$record.schema-cne'math-research-frozen-ticket/v8'-or[string]$record.project_id-cne$ExpectedProjectId-or-not(Test-NonnegativeJsonInteger $record.control_generation)-or[int64]$record.control_generation-ne$Generation-or
            -not(Test-ContractPointer -Pointer $record.contract -Expected $ExpectedContract)-or-not(Test-ExactKeys -Object $record.run -Required @('id','path','status'))-or[string]$record.run.id-cne[string]$ExpectedRun.id-or[string]$record.run.path-cne[string]$ExpectedRun.path-or[string]$record.run.status-cne'auditing'-or
            [string]$record.cycle_id-cne[string]$ContractEnvelope.Tickets.cycle_id-or[string]$record.contract_initial_tickets_sha256-cne[string]$ContractEnvelope.Metadata.initial_tickets_sha256-or
            -not(Test-V8CountersEqual -Left (Assert-V8Counters -Object $record.counter_snapshot -Label 'cycle-audit ticket counters') -Right $Counters)-or[string]$record.ticket.role-cne$roles[$index]){throw 'Cycle-audit frozen ticket binding is invalid.'}
        Assert-V8TicketBody -Ticket $record.ticket -Metadata $ContractEnvelope.Metadata -MetadataIntegers $ContractEnvelope.MetadataIntegers -ProjectPath $ProjectPath -ActiveRun $ExpectedRun -ActiveContract $ExpectedContract
        if(-not$ticketIds.Add([string]$record.ticket.ticket_id)){throw 'Cycle-audit ticket IDs must be distinct.'}
        if(Test-FilePointer -Pointer $plan.active_ticket -ExpectedPath ([string]$entry.ticket.path) -ExpectedSha256 ([string]$entry.ticket.sha256)){$currentMatches++}
    }
    if($currentMatches-ne1){throw 'AUDIT_START current ticket must be exactly one member of its three-role audit plan.'}
    return $plan
}

function Assert-CycleAuditHistory {
    param($SummaryResult,$EndEvent,[long]$EndGeneration,[string]$ProjectPath,[string]$ExpectedProjectId,$ExpectedContract,$ExpectedRun,$ContractEnvelope)
    $summary=$SummaryResult.Summary;$startPointer=$summary.audit_start_event
    if([string]$startPointer.path-cnotmatch'^state/project-events/g(?<generation>[0-9]{4,})\.json$'){throw 'Cycle-audit start event path is not generation-canonical.'}
    $startGeneration=[int64]$Matches.generation
    if($startGeneration-lt1-or$startGeneration-ge$EndGeneration){throw 'Cycle-audit start generation is outside the active audit interval.'}
    $startPath=Assert-ImmutableRawPointer -Pointer $startPointer -ProjectPath $ProjectPath -Label 'cycle-audit start event' -RequiredRoot 'state'
    $start=Read-StrictJsonObject -LiteralPath $startPath -Label 'cycle-audit start event';$eventKeys=@('schema','project_id','control_generation','event_id','event_type','updated_at_utc','previous_event_sha256','contract','run','counters','referenced_artifacts')
    if(-not(Test-ExactKeys -Object $start -Required $eventKeys)-or[string]$start.schema-cne'math-research-project-event/v8'-or[string]$start.project_id-cne$ExpectedProjectId-or-not(Test-NonnegativeJsonInteger $start.control_generation)-or[int64]$start.control_generation-ne$startGeneration-or
        [string]$start.event_type-cne'AUDIT_START'-or-not(Test-ContractPointer -Pointer $start.contract -Expected $ExpectedContract)-or-not(Test-ExactKeys -Object $start.run -Required @('id','path','status'))-or[string]$start.run.id-cne[string]$ExpectedRun.id-or[string]$start.run.path-cne[string]$ExpectedRun.path-or[string]$start.run.status-cne'auditing'-or
        -not(Test-CurrentUtcTimestamp -Value ([string]$start.updated_at_utc))-or-not(Test-JsonArray $start.referenced_artifacts)-or@($start.referenced_artifacts).Count-ne1-or-not(Test-RawPointerEqual -Left $start.referenced_artifacts[0] -Right $summary.plan)){throw 'Cycle-audit start event/plan binding is invalid.'}
    $startCounters=Assert-V8Counters -Object $start -Label 'cycle-audit start counters'
    $plan=Assert-CycleAuditPlan -Pointer $summary.plan -ProjectPath $ProjectPath -ExpectedProjectId $ExpectedProjectId -ExpectedContract $ExpectedContract -ExpectedRun $ExpectedRun -Generation $startGeneration -Counters $startCounters -ContractEnvelope $ContractEnvelope -ExpectedAuditKind ([string]$summary.audit_kind) -ExpectedCandidate $summary.candidate
    if(-not(Test-RawPointerEqual -Left $plan.snapshot -Right $summary.snapshot)-or-not(Test-JsonDeepEqual -Left $plan.candidate -Right $summary.candidate)){throw 'Cycle-audit summary candidate/snapshot differs from its frozen start plan.'}
    if([string]$summary.audit_kind-ceq'terminal'){
        $priorGeneration=$startGeneration-1;if($priorGeneration-lt1){throw 'Terminal audit start has no candidate_found predecessor.'}
        $priorPath=Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ('state/project-events/g{0:D4}.json'-f$priorGeneration) -RequiredRoot 'state' -PathType Leaf;$priorEvent=Read-StrictJsonObject -LiteralPath $priorPath -Label 'terminal audit predecessor'
        $priorRun=[ordered]@{id=[string]$ExpectedRun.id;path=[string]$ExpectedRun.path;status='completion_candidate'}
        $locked=Get-PreAuditCompletionOutcomeV8 -HeadEvent $priorEvent -HeadGeneration $priorGeneration -ProjectPath $ProjectPath -ExpectedProjectId $ExpectedProjectId -ExpectedContract $ExpectedContract -ExpectedRun $priorRun
        if($null-eq$locked-or-not(Test-RawPointerEqual -Left $locked.Outcome.candidate -Right $summary.candidate)){throw 'Terminal audit candidate is not the locked candidate_found ATTEMPT_END outcome.'}
    }
    $expectedPrevious=[string]$startPointer.sha256;$allowedIntermediate=@('CHECKPOINT_COMMIT','PAUSE','RESUME','HOST_REBIND')
    for($generation=$startGeneration+1;$generation-lt$EndGeneration;$generation++){
        $relative=('state/project-events/g{0:D4}.json'-f$generation);$path=Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath $relative -RequiredRoot 'state' -PathType Leaf;$hash=Get-FileSha256 -LiteralPath $path
        $middle=Read-StrictJsonObject -LiteralPath $path -Label 'cycle-audit intermediate event'
        if(-not(Test-ExactKeys -Object $middle -Required $eventKeys)-or[string]$middle.schema-cne'math-research-project-event/v8'-or[string]$middle.project_id-cne$ExpectedProjectId-or-not(Test-NonnegativeJsonInteger $middle.control_generation)-or[int64]$middle.control_generation-ne$generation-or
            [string]$middle.previous_event_sha256-cne$expectedPrevious-or[string]$middle.event_type-cnotin$allowedIntermediate-or-not(Test-ContractPointer -Pointer $middle.contract -Expected $ExpectedContract)-or-not(Test-ExactKeys -Object $middle.run -Required @('id','path','status'))-or[string]$middle.run.id-cne[string]$ExpectedRun.id-or[string]$middle.run.path-cne[string]$ExpectedRun.path-or[string]$middle.run.status-cnotin@('auditing','paused')-or
            -not(Test-V8CountersEqual -Left (Assert-V8Counters -Object $middle -Label 'cycle-audit intermediate counters') -Right $startCounters)){throw 'Cycle-audit intermediate history changes audit identity/counters or breaks the event chain.'}
        $expectedPrevious=$hash
    }
    if([string]$EndEvent.previous_event_sha256-cne$expectedPrevious){throw 'AUDIT_END is not chained from its bound authoritative AUDIT_START history.'}
    $endCounters=Assert-V8Counters -Object $EndEvent -Label 'cycle-audit end counters'
    foreach($name in @('attempt_count','audit_count','total_round_count')){if([int64]$endCounters[$name]-ne[int64]$startCounters[$name]){throw 'AUDIT_END global counters differ from AUDIT_START.'}}
    return $plan
}

function Get-AuditedCompletionSummary {
    param($HeadEvent,[long]$HeadGeneration,[string]$ProjectPath,[string]$ExpectedProjectId,$ExpectedContract,$ExpectedRun,$ContractEnvelope)
    if([string]$ExpectedRun.status-cne'completion_candidate'-or[string]$HeadEvent.event_type-cnotin@('AUDIT_END','HOST_REBIND')){return $null}
    if(-not(Test-JsonArray $HeadEvent.referenced_artifacts)-or@($HeadEvent.referenced_artifacts).Count-ne1){throw 'Audited completion event must carry exactly one terminal cycle-audit summary.'}
    $summaryPointer=$HeadEvent.referenced_artifacts[0];$cursor=$HeadEvent;$cursorGeneration=$HeadGeneration;$eventKeys=@('schema','project_id','control_generation','event_id','event_type','updated_at_utc','previous_event_sha256','contract','run','counters','referenced_artifacts')
    while([string]$cursor.event_type-ceq'HOST_REBIND'){
        if($cursorGeneration-le1){throw 'Audited completion HOST_REBIND chain has no terminal AUDIT_END predecessor.'}
        $priorGeneration=$cursorGeneration-1;$priorPath=Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ('state/project-events/g{0:D4}.json'-f$priorGeneration) -RequiredRoot 'state' -PathType Leaf;$priorHash=Get-FileSha256 -LiteralPath $priorPath
        if([string]$cursor.previous_event_sha256-cne$priorHash){throw 'Audited completion HOST_REBIND chain hash is broken.'}
        $prior=Read-StrictJsonObject -LiteralPath $priorPath -Label 'audited-completion predecessor event'
        if(-not(Test-ExactKeys -Object $prior -Required $eventKeys)-or[string]$prior.project_id-cne$ExpectedProjectId-or-not(Test-ContractPointer -Pointer $prior.contract -Expected $ExpectedContract)-or-not(Test-ExactKeys -Object $prior.run -Required @('id','path','status'))-or[string]$prior.run.id-cne[string]$ExpectedRun.id-or[string]$prior.run.path-cne[string]$ExpectedRun.path-or[string]$prior.run.status-cne'completion_candidate'-or[string]$prior.event_type-cnotin@('ATTEMPT_END','AUDIT_END','HOST_REBIND')-or-not(Test-JsonArray $prior.referenced_artifacts)-or@($prior.referenced_artifacts).Count-ne1-or-not(Test-RawPointerEqual -Left $prior.referenced_artifacts[0] -Right $summaryPointer)){throw 'Audited completion HOST_REBIND chain changes its terminal certificate/outcome or research identity.'}
        $cursor=$prior;$cursorGeneration=$priorGeneration
    }
    if([string]$cursor.event_type-cne'AUDIT_END'){return $null}
    $summaryResult=Assert-CycleAuditSummary -Pointer $summaryPointer -ProjectPath $ProjectPath -ExpectedProjectId $ExpectedProjectId -ExpectedContract $ExpectedContract -ExpectedRun $ExpectedRun -ExpectedAuditKind terminal -RequirePass
    $null=Assert-CycleAuditHistory -SummaryResult $summaryResult -EndEvent $cursor -EndGeneration $cursorGeneration -ProjectPath $ProjectPath -ExpectedProjectId $ExpectedProjectId -ExpectedContract $ExpectedContract -ExpectedRun $ExpectedRun -ContractEnvelope $ContractEnvelope
    return $summaryResult
}

function Get-PreAuditCompletionOutcomeV8 {
    param($HeadEvent,[long]$HeadGeneration,[string]$ProjectPath,[string]$ExpectedProjectId,$ExpectedContract,$ExpectedRun)
    if([string]$ExpectedRun.status-cne'completion_candidate'-or[string]$HeadEvent.event_type-cnotin@('ATTEMPT_END','HOST_REBIND')){return $null}
    if(-not(Test-JsonArray $HeadEvent.referenced_artifacts)-or@($HeadEvent.referenced_artifacts).Count-ne1){throw 'Pre-audit completion head must carry exactly one attempt outcome.'}
    $outcomePointer=$HeadEvent.referenced_artifacts[0];$cursor=$HeadEvent;$generation=$HeadGeneration;$keys=@('schema','project_id','control_generation','event_id','event_type','updated_at_utc','previous_event_sha256','contract','run','counters','referenced_artifacts')
    while([string]$cursor.event_type-ceq'HOST_REBIND'){
        if($generation-le1){throw 'Pre-audit HOST_REBIND chain has no ATTEMPT_END predecessor.'};$priorGeneration=$generation-1;$priorPath=Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ('state/project-events/g{0:D4}.json'-f$priorGeneration) -RequiredRoot 'state' -PathType Leaf;$priorHash=Get-FileSha256 -LiteralPath $priorPath
        if([string]$cursor.previous_event_sha256-cne$priorHash){throw 'Pre-audit HOST_REBIND chain hash is broken.'};$prior=Read-StrictJsonObject -LiteralPath $priorPath -Label 'pre-audit completion predecessor'
        if(-not(Test-ExactKeys -Object $prior -Required $keys)-or[string]$prior.project_id-cne$ExpectedProjectId-or-not(Test-ContractPointer -Pointer $prior.contract -Expected $ExpectedContract)-or-not(Test-ExactKeys -Object $prior.run -Required @('id','path','status'))-or[string]$prior.run.id-cne[string]$ExpectedRun.id-or[string]$prior.run.path-cne[string]$ExpectedRun.path-or[string]$prior.run.status-cne'completion_candidate'-or[string]$prior.event_type-cnotin@('ATTEMPT_END','AUDIT_END','HOST_REBIND')-or-not(Test-JsonArray $prior.referenced_artifacts)-or@($prior.referenced_artifacts).Count-ne1-or-not(Test-RawPointerEqual -Left $prior.referenced_artifacts[0] -Right $outcomePointer)){throw 'Pre-audit HOST_REBIND chain changes outcome/Contract/run identity.'}
        $cursor=$prior;$generation=$priorGeneration
    }
    if([string]$cursor.event_type-cne'ATTEMPT_END'){return $null}
    $result=Assert-AttemptOutcomeV8 -Pointer $outcomePointer -ProjectPath $ProjectPath -ExpectedProjectId $ExpectedProjectId -ExpectedContract $ExpectedContract -ExpectedRun $ExpectedRun
    if([string]$result.Record.outcome-cne'candidate_found'){throw 'Pre-audit completion outcome is not candidate_found.'}
    return [pscustomobject]@{Pointer=[ordered]@{path=[string]$outcomePointer.path;sha256=[string]$outcomePointer.sha256};Outcome=$result.Record;VerifierTicketId=$result.VerifierTicketId}
}

function Assert-ResumeCapsule {
    param($Pointer,[string]$ProjectPath,[string]$ExpectedProjectId,$ExpectedContract,$ExpectedRun,$ExpectedTicket,$ExpectedLifecycle,$ExpectedCounters,[string]$ExpectedPriorStatus)
    $path=Assert-ImmutableRawPointer -Pointer $Pointer -ProjectPath $ProjectPath -Label 'resume capsule';$capsule=Read-StrictJsonObject -LiteralPath $path -Label 'resume capsule'
    if(-not(Test-ExactKeys -Object $capsule -Required @('schema','project_id','contract','run','prior_status','ticket','lifecycle','counters','created_at_utc'))-or[string]$capsule.schema-cne'math-research-resume-capsule/v8'-or[string]$capsule.project_id-cne$ExpectedProjectId-or
        -not(Test-ExactKeys -Object $capsule.contract -Required @('path','version','binding_sha256'))-or-not(Test-ContractPointer -Pointer $capsule.contract -Expected $ExpectedContract)-or-not(Test-ExactKeys -Object $capsule.run -Required @('id','path'))-or[string]$capsule.run.id-cne[string]$ExpectedRun.id-or[string]$capsule.run.path-cne[string]$ExpectedRun.path-or
        [string]$capsule.prior_status-cne$ExpectedPriorStatus-or[string]$capsule.prior_status-cnotin@('attempt_running','auditing')-or-not(Test-JsonDeepEqual -Left $capsule.ticket -Right $ExpectedTicket)-or-not(Test-JsonDeepEqual -Left $capsule.lifecycle -Right $ExpectedLifecycle)-or
        -not(Test-V8CountersEqual -Left (Assert-V8Counters -Object $capsule -Label 'resume capsule counters') -Right $ExpectedCounters)-or-not(Test-CurrentUtcTimestamp -Value ([string]$capsule.created_at_utc))){throw 'Resume capsule identity/status/ticket/lifecycle/counters is invalid.'}
    return [pscustomobject]@{Pointer=[ordered]@{path=[string]$Pointer.path;sha256=[string]$Pointer.sha256};Capsule=$capsule}
}

function Get-PausedResumeCapsule {
    param($HeadEvent,[long]$HeadGeneration,[string]$ProjectPath,[string]$ExpectedProjectId,$ExpectedContract,$ExpectedRun,$ExpectedTicket,$ExpectedLifecycle,$ExpectedCounters)
    if([string]$ExpectedRun.status-cne'paused'-or[string]$HeadEvent.event_type-cnotin@('PAUSE','HOST_REBIND')){return $null}
    if(-not(Test-JsonArray $HeadEvent.referenced_artifacts)-or@($HeadEvent.referenced_artifacts).Count-ne1){throw 'Paused head must carry exactly one resume capsule.'}
    $capsulePointer=$HeadEvent.referenced_artifacts[0];$cursor=$HeadEvent;$generation=$HeadGeneration;$keys=@('schema','project_id','control_generation','event_id','event_type','updated_at_utc','previous_event_sha256','contract','run','counters','referenced_artifacts')
    while([string]$cursor.event_type-ceq'HOST_REBIND'){
        if($generation-le1){throw 'Paused HOST_REBIND chain has no PAUSE predecessor.'};$priorGeneration=$generation-1;$priorPath=Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ('state/project-events/g{0:D4}.json'-f$priorGeneration) -RequiredRoot 'state' -PathType Leaf;$priorHash=Get-FileSha256 -LiteralPath $priorPath
        if([string]$cursor.previous_event_sha256-cne$priorHash){throw 'Paused HOST_REBIND chain hash is broken.'};$prior=Read-StrictJsonObject -LiteralPath $priorPath -Label 'pause predecessor event'
        if(-not(Test-ExactKeys -Object $prior -Required $keys)-or[string]$prior.event_type-cnotin@('PAUSE','HOST_REBIND')-or[string]$prior.run.status-cne'paused'-or-not(Test-JsonArray $prior.referenced_artifacts)-or@($prior.referenced_artifacts).Count-ne1-or-not(Test-RawPointerEqual -Left $prior.referenced_artifacts[0] -Right $capsulePointer)){throw 'Paused HOST_REBIND chain changes or loses its resume capsule.'};$cursor=$prior;$generation=$priorGeneration
    }
    $capsulePath=Assert-ImmutableRawPointer -Pointer $capsulePointer -ProjectPath $ProjectPath -Label 'resume capsule';$capsulePreview=Read-StrictJsonObject -LiteralPath $capsulePath -Label 'resume capsule'
    return Assert-ResumeCapsule -Pointer $capsulePointer -ProjectPath $ProjectPath -ExpectedProjectId $ExpectedProjectId -ExpectedContract $ExpectedContract -ExpectedRun $ExpectedRun -ExpectedTicket $ExpectedTicket -ExpectedLifecycle $ExpectedLifecycle -ExpectedCounters $ExpectedCounters -ExpectedPriorStatus ([string]$capsulePreview.prior_status)
}

function Read-GoalHostV8ContractEnvelope {
    param(
        [Parameter(Mandatory = $true)][string]$ContractPath,
        [Parameter(Mandatory = $true)][string]$ExpectedVersion,
        [Parameter(Mandatory = $true)][string]$ExpectedProjectId,
        [Parameter(Mandatory = $true)][string]$ExpectedProjectDirectoryName,
        [Parameter(Mandatory = $true)][string]$ExpectedProjectIdentitySha256,
        [Parameter(Mandatory = $true)][string]$ExpectedProjectPath,
        [Parameter(Mandatory = $true)][string]$ExpectedProblemStatementSha256
    )
    try {
        $normalized = [IO.File]::ReadAllText($ContractPath, [Text.UTF8Encoding]::new($false, $true)) -replace "`r`n", "`n"
        if ($normalized.Contains("`r")) { throw 'Contract contains an isolated CR.' }
        if ([regex]::Matches($normalized, '(?m)^# Math Research Goal-Host Contract v8$').Count -ne 1) { throw 'Contract must contain exactly one v8 Goal-host H1.' }
        if ([regex]::Matches($normalized, [regex]::Escape('<!-- math-research-goal-host')).Count -ne 1) { throw 'Contract must contain exactly one Goal-host metadata tag.' }
        $metadataPattern = '\A# Math Research Goal-Host Contract v8\n<!-- math-research-goal-host\n(?<body>.*?)\n-->\n'
        $metadataMatch = [regex]::Match($normalized, $metadataPattern, [Text.RegularExpressions.RegexOptions]::Singleline)
        if (-not $metadataMatch.Success) { throw 'Goal-host metadata must immediately follow the v8 H1 in exact comment form.' }
        $allowed = @(
            'schema','goal_host_protocol','goal_binding_policy','goal_rebind_policy','contract_version','project_archive_schema','project_id',
            'project_directory_name','project_identity_sha256','model','reasoning_effort','approval_mode','web_search','audit_interval_attempts',
            'attempt_budget','total_round_budget','max_child_agents','max_total_agents','max_runtime_minutes','run_origin',
            'inherited_counter_budget_baseline_sha256','problem_statement_sha256','cycle_policy_sha256','initial_tickets_sha256'
        )
        $metadata = [ordered]@{}
        foreach ($line in ($metadataMatch.Groups['body'].Value -split "`n")) {
            if ($line -notmatch '^(?<key>[a-z][a-z0-9_]*):\s*(?<value>\S(?:.*\S)?)$') { throw "Invalid Goal-host metadata line: $line" }
            $key = $Matches['key']; $value = $Matches['value']
            if ($key -cnotin $allowed -or $metadata.Contains($key)) { throw "Unknown or duplicate Goal-host metadata key: $key" }
            $metadata[$key] = $value
        }
        if ($metadata.Count -ne $allowed.Count -or @($allowed | Where-Object { -not $metadata.Contains($_) }).Count -gt 0) { throw 'Goal-host metadata must contain the exact v8 key set.' }
        if ([string]$metadata.schema -cne '8' -or [string]$metadata.goal_host_protocol -cne 'direct-current-task/v8' -or
            [string]$metadata.goal_binding_policy -cne 'direct-current-task/v8' -or [string]$metadata.goal_rebind_policy -cne 'external-host-bind-chain/v8' -or
            [string]$metadata.project_archive_schema -cne 'math-research-project/v8') { throw 'Goal-host metadata protocol/policy/schema mismatch.' }
        if ([string]$metadata.contract_version -cne $ExpectedVersion -or [string]$metadata.project_id -cne $ExpectedProjectId -or
            [string]$metadata.project_directory_name -cne $ExpectedProjectDirectoryName -or [string]$metadata.project_identity_sha256 -cne $ExpectedProjectIdentitySha256 -or
            [string]$metadata.problem_statement_sha256 -cne $ExpectedProblemStatementSha256) { throw 'Goal-host metadata identity binding mismatch.' }
        foreach ($key in @('project_identity_sha256','problem_statement_sha256','cycle_policy_sha256','initial_tickets_sha256')) { Assert-LowerSha256 -Value ([string]$metadata[$key]) -Label "Contract $key" }
        if ([string]$metadata.model -cnotmatch '^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$' -or [string]$metadata.reasoning_effort -cnotin @('minimal','low','medium','high','xhigh','max','ultra') -or
            [string]$metadata.approval_mode -cnotin @('approve_for_me','never') -or [string]$metadata.web_search -cnotin @('allowed','denied')) { throw 'Contract model/reasoning/approval/web policy is invalid.' }
        $metadataIntegers = [ordered]@{}
        foreach ($key in @('audit_interval_attempts','attempt_budget','total_round_budget','max_child_agents','max_total_agents','max_runtime_minutes')) {
            if ([string]$metadata[$key] -cnotmatch '^(0|[1-9][0-9]*)$') { throw "Contract $key must be one nonnegative decimal integer." }
            $parsed = [int64]0
            if (-not [int64]::TryParse([string]$metadata[$key], [ref]$parsed)) { throw "Contract $key is out of range." }
            $metadataIntegers[$key] = $parsed
        }
        if ($metadataIntegers.audit_interval_attempts -lt 1 -or $metadataIntegers.attempt_budget -lt 1 -or $metadataIntegers.total_round_budget -lt 1 -or
            $metadataIntegers.max_child_agents -lt 1 -or $metadataIntegers.max_child_agents -gt 16 -or $metadataIntegers.max_total_agents -ne $metadataIntegers.max_child_agents + 1 -or
            $metadataIntegers.total_round_budget -lt $metadataIntegers.attempt_budget + [Math]::Ceiling($metadataIntegers.attempt_budget / [double]$metadataIntegers.audit_interval_attempts)) { throw 'Contract resource budgets cannot accommodate required audits/host capacity.' }
        if ([string]$metadata.run_origin -cnotin @('fresh','legacy_successor')) { throw 'Contract run_origin is invalid.' }
        if ([string]$metadata.run_origin -ceq 'fresh') {
            if ([string]$metadata.inherited_counter_budget_baseline_sha256 -cne 'null') { throw 'Fresh Contract must use a null inherited baseline.' }
        }
        else { Assert-LowerSha256 -Value ([string]$metadata.inherited_counter_budget_baseline_sha256) -Label 'successor inherited baseline hash' }

        $policyBlock = Get-UniqueContractJsonBlock -NormalizedContract $normalized -Name 'math-research-cycle-policy'
        $ticketsBlock = Get-UniqueContractJsonBlock -NormalizedContract $normalized -Name 'math-research-initial-tickets'
        if ((Get-TextSha256 -Text $policyBlock.Body) -cne [string]$metadata.cycle_policy_sha256 -or (Get-TextSha256 -Text $ticketsBlock.Body) -cne [string]$metadata.initial_tickets_sha256) { throw 'Machine-block exact-body hash mismatch.' }
        $policy = $policyBlock.Object
        if (-not (Test-ExactKeys -Object $policy -Required @('schema_version','protocol','total_round_budget','attempt_budget','audit_interval_attempts','max_route_family_attempts_per_cycle','max_repair_batches_per_attempt','allowed_worker_tools','max_ticket_tool_calls','max_ticket_output_bytes','audit_roles')) -or
            -not (Test-NonnegativeJsonInteger $policy.schema_version) -or [int]$policy.schema_version -ne 3 -or [string]$policy.protocol -cne 'math-research-cycle-policy/v3') { throw 'Cycle-policy block shape/schema/protocol mismatch.' }
        foreach ($key in @('total_round_budget','attempt_budget','audit_interval_attempts','max_route_family_attempts_per_cycle','max_repair_batches_per_attempt','max_ticket_tool_calls','max_ticket_output_bytes')) { if (-not (Test-NonnegativeJsonInteger $policy[$key])) { throw "Cycle policy $key must be a JSON integer." } }
        if ([int64]$policy.total_round_budget -ne $metadataIntegers.total_round_budget -or [int64]$policy.attempt_budget -ne $metadataIntegers.attempt_budget -or [int64]$policy.audit_interval_attempts -ne $metadataIntegers.audit_interval_attempts -or
            [int64]$policy.max_route_family_attempts_per_cycle -lt 1 -or [int64]$policy.max_repair_batches_per_attempt -lt 0 -or [int64]$policy.max_ticket_tool_calls-lt1-or[int64]$policy.max_ticket_output_bytes-lt1) { throw 'Cycle-policy budgets mismatch metadata or are invalid.' }
        if(-not(Test-JsonArray $policy.allowed_worker_tools)-or@($policy.allowed_worker_tools).Count-lt1){throw 'Cycle-policy allowed_worker_tools must be a nonempty closed array.'}
        $workerToolSet=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        foreach($tool in @($policy.allowed_worker_tools)){if(-not(Test-AllowedWorkerToolName $tool)-or-not$workerToolSet.Add([string]$tool)){throw 'Cycle-policy worker-tool allowlist contains a forbidden, unresolved, or duplicate name.'}}
        if([string]$metadata.web_search-ceq'denied'-and'web__run'-cin@($policy.allowed_worker_tools)){throw 'A network-denied Contract cannot authorize web__run.'}
        $metadata.allowed_worker_tools=@($policy.allowed_worker_tools);$metadataIntegers.max_ticket_tool_calls=[int64]$policy.max_ticket_tool_calls;$metadataIntegers.max_ticket_output_bytes=[int64]$policy.max_ticket_output_bytes
        $requiredAuditRoles = @('skeptic_quantifiers','skeptic_strategy','theory_tool_scout')
        if (-not (Test-JsonArray $policy.audit_roles) -or @($policy.audit_roles).Count -ne 3 -or (@($policy.audit_roles) -join '|') -cne ($requiredAuditRoles -join '|')) { throw 'Cycle-policy audit roles must be the exact three-role sequence.' }

        if (-not (Test-ExactKeys -Object $ticketsBlock.Object -Required @('schema_version','cycle_id','tickets')) -or -not (Test-NonnegativeJsonInteger $ticketsBlock.Object.schema_version) -or [int]$ticketsBlock.Object.schema_version -ne 3 -or
            -not (Test-ResolvedContractString $ticketsBlock.Object.cycle_id) -or -not (Test-JsonArray $ticketsBlock.Object.tickets) -or @($ticketsBlock.Object.tickets).Count -lt 1) { throw 'Initial-tickets block is empty or invalid.' }
        $ticketIds = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        foreach ($initialTicket in @($ticketsBlock.Object.tickets)) {
            $ticketKeys = @('ticket_id','role','planned_lifecycle_slot','route_id','route_fingerprint_sha256','attempt_kind','route_family_id','mechanism_id','bottleneck_id','decision_question','input_artifacts','search_domain','success_signal','stop_signal','allowed_tools','source_network_policy','filesystem_scope','resource_caps','dependencies','evidence_grade_required','required_outputs','failure_return','reopen_condition')
            if([string]$initialTicket.role-ceq'verifier'){$ticketKeys+=@('candidate_artifact')}
            if (-not (Test-ExactKeys -Object $initialTicket -Required $ticketKeys)) { throw 'Initial ticket shape is incomplete or has unknown keys.' }
            foreach ($key in @('ticket_id','planned_lifecycle_slot','route_id','attempt_kind','route_family_id','mechanism_id','bottleneck_id','decision_question','search_domain','success_signal','stop_signal','evidence_grade_required','reopen_condition')) {
                if (-not (Test-ResolvedContractString $initialTicket[$key])) { throw "Initial ticket $key is unresolved." }
            }
            if (-not $ticketIds.Add([string]$initialTicket.ticket_id) -or [string]$initialTicket.role -cnotin @('solver','verifier','skeptic_quantifiers','skeptic_strategy','theory_tool_scout')) { throw 'Initial ticket ID/role is invalid.' }
            Assert-LowerSha256 -Value ([string]$initialTicket.route_fingerprint_sha256) -Label 'ticket route fingerprint'
            if (-not (Test-JsonArray $initialTicket.input_artifacts) -or @($initialTicket.input_artifacts).Count -lt 1) { throw 'Initial ticket must bind at least one input artifact.' }
            foreach ($artifact in @($initialTicket.input_artifacts)) {
                if (-not (Test-ExactKeys -Object $artifact -Required @('path','sha256')) -or -not (Test-ContractRelativePathSyntax $artifact.path)) { throw 'Ticket input artifact pointer is invalid.' }
                Assert-LowerSha256 -Value ([string]$artifact.sha256) -Label 'ticket input artifact hash'
                $inputPath = [IO.Path]::GetFullPath((Join-Path $ExpectedProjectPath ([string]$artifact.path)))
                if (-not (Test-PathInside -Child $inputPath -Directory $ExpectedProjectPath) -or -not (Test-Path -LiteralPath $inputPath -PathType Leaf) -or (Get-FileSha256 -LiteralPath $inputPath) -cne [string]$artifact.sha256) { throw 'Ticket input artifact does not match project file bytes.' }
            }
            if (-not (Test-JsonArray $initialTicket.allowed_tools) -or @($initialTicket.allowed_tools).Count -lt 1) { throw 'Ticket allowed_tools is empty.' }
            $initialToolSet=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
            foreach($tool in @($initialTicket.allowed_tools)){if(-not(Test-AllowedWorkerToolName $tool)-or-not$initialToolSet.Add([string]$tool)-or[string]$tool-cnotin@($policy.allowed_worker_tools)){throw 'Initial ticket tools are not a unique subset of the cycle-policy allowlist.'}}
            $network = $initialTicket.source_network_policy
            if (-not (Test-ExactKeys -Object $network -Required @('web','allowed_source_classes','network_destinations')) -or [string]$network.web -cne [string]$metadata.web_search -or
                -not (Test-JsonArray $network.allowed_source_classes) -or -not (Test-JsonArray $network.network_destinations) -or @($network.allowed_source_classes).Count -lt 1 -or @($network.allowed_source_classes | Where-Object { -not (Test-ResolvedContractString $_) }).Count -gt 0 -or
                @($network.network_destinations | Where-Object { -not (Test-ResolvedContractString $_) }).Count -gt 0 -or ([string]$network.web -ceq 'denied' -and @($network.network_destinations).Count -ne 0)) { throw 'Ticket source/network policy is invalid.' }
            $filesystem = $initialTicket.filesystem_scope
            if (-not (Test-ExactKeys -Object $filesystem -Required @('read_paths','writable_staging_path')) -or -not (Test-JsonArray $filesystem.read_paths) -or @($filesystem.read_paths).Count -lt 1 -or
                @($filesystem.read_paths | Where-Object { -not (Test-ContractRelativePathSyntax $_) }).Count -gt 0 -or -not (Test-ContractRelativePathSyntax $filesystem.writable_staging_path)) { throw 'Ticket filesystem scope is invalid.' }
            $caps = $initialTicket.resource_caps
            if (-not (Test-ExactKeys -Object $caps -Required @('child_agents','tool_calls','runtime_minutes','max_output_bytes'))) { throw 'Ticket resource caps shape is invalid.' }
            foreach ($key in @('child_agents','tool_calls','runtime_minutes','max_output_bytes')) { if (-not (Test-NonnegativeJsonInteger $caps[$key])) { throw "Ticket resource cap $key must be a nonnegative JSON integer." } }
            if ([int64]$caps.child_agents -gt $metadataIntegers.max_child_agents -or ($metadataIntegers.max_runtime_minutes -gt 0 -and [int64]$caps.runtime_minutes -gt $metadataIntegers.max_runtime_minutes) -or [int64]$caps.tool_calls-gt[int64]$policy.max_ticket_tool_calls-or[int64]$caps.max_output_bytes-lt1-or[int64]$caps.max_output_bytes-gt[int64]$policy.max_ticket_output_bytes) { throw 'Ticket resource caps exceed Contract or cycle-policy caps.' }
            if (-not (Test-JsonArray $initialTicket.dependencies)) { throw 'Ticket dependency list is invalid.' }
            foreach ($dependency in @($initialTicket.dependencies)) {
                if (-not (Test-ExactKeys -Object $dependency -Required @('ticket_id','path','sha256'))) { throw 'Ticket dependency binding is invalid.' }
                Assert-SafeLeafName -Value ([string]$dependency.ticket_id) -Label 'ticket dependency ID'
                Assert-LowerSha256 -Value ([string]$dependency.sha256) -Label 'ticket dependency hash'
                $dependencyPath=Resolve-ProjectRelativePath -ProjectPath $ExpectedProjectPath -RelativePath ([string]$dependency.path) -RequiredRoot '.' -PathType Leaf
                if((Get-FileSha256 -LiteralPath $dependencyPath)-cne[string]$dependency.sha256){throw 'Ticket dependency hash mismatches.'}
            }
            if (-not (Test-JsonArray $initialTicket.required_outputs) -or @($initialTicket.required_outputs).Count -lt 1) { throw 'Ticket required_outputs is empty.' }
            foreach ($output in @($initialTicket.required_outputs)) {
                if (-not (Test-ExactKeys -Object $output -Required @('path','schema','sha256_on_return')) -or -not (Test-ContractRelativePathSyntax $output.path -AllowLeaf) -or
                    -not (Test-ResolvedContractString $output.schema) -or [string]$output.sha256_on_return -cne 'required') { throw 'Ticket required output is invalid.' }
            }
            $failure = $initialTicket.failure_return
            $requiredFailureFields = @('status','failed_step','reason','partial_artifact_hashes','reopen_condition')
            if (-not (Test-ExactKeys -Object $failure -Required @('schema','required_fields')) -or [string]$failure.schema -cne 'math-research-ticket-failure/v1' -or
                -not (Test-JsonArray $failure.required_fields) -or @($failure.required_fields).Count -ne $requiredFailureFields.Count -or (@($failure.required_fields) -join '|') -cne ($requiredFailureFields -join '|')) { throw 'Ticket failure-return schema is invalid.' }
        }
        return [pscustomobject]@{ Valid=$true; Metadata=$metadata; MetadataIntegers=$metadataIntegers; Policy=$policy; Tickets=$ticketsBlock.Object; TicketsBody=$ticketsBlock.Body }
    }
    catch { return [pscustomobject]@{ Valid=$false; Reason=$_.Exception.Message } }
}

function Read-LegacySuccessorAdvisory {
    param(
        [Parameter(Mandatory = $true)][string]$ProjectPath,
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Project,
        [Parameter(Mandatory = $true)][Collections.IDictionary]$State,
        [Parameter(Mandatory = $true)]$ContractEnvelope
    )
    try {
        $pointer = $Project.legacy_successor
        if (-not (Test-ExactKeys -Object $pointer -Required @('path','sha256','control_generation'))) { throw 'Legacy-successor pointer shape is invalid.' }
        Assert-LowerSha256 -Value ([string]$pointer.sha256) -Label 'legacy-successor pointer hash'
        if (-not (Test-NonnegativeJsonInteger $pointer.control_generation) -or [int64]$pointer.control_generation -lt 1 -or [int64]$pointer.control_generation -gt [int64]$Project.control_generation) { throw 'Legacy-successor activation generation is invalid for the current project head.' }
        $successorActivationGeneration = [int64]$pointer.control_generation
        if ([string]$pointer.path -cnotmatch '^state[\\/]successors[\\/]g(?<generation>[0-9]{4,})\.json$' -or [int64]$Matches['generation'] -ne $successorActivationGeneration) { throw 'Legacy-successor pointer path is not generation-bound.' }
        $successorPath = Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ([string]$pointer.path) -RequiredRoot 'state' -PathType Leaf
        if ((Get-FileSha256 -LiteralPath $successorPath) -cne [string]$pointer.sha256) { throw 'Legacy-successor pointer hash mismatches.' }
        $lineage = Read-StrictJsonObject -LiteralPath $successorPath -Label 'legacy-successor advisory'
        if (-not (Test-ExactKeys -Object $lineage -Required @('schema','project_id','control_generation','legacy_goal_bindings_obsolete','predecessor','inherited_artifact_index','inherited_counter_budget_baseline','successor'))) { throw 'Legacy-successor advisory shape is invalid.' }
        if ([string]$lineage.schema -cne 'math-research-legacy-successor-lineage/v8' -or [string]$lineage.project_id -cne [string]$Project.project_id -or
            -not (Test-NonnegativeJsonInteger $lineage.control_generation) -or [int64]$lineage.control_generation -ne $successorActivationGeneration -or
            $lineage.legacy_goal_bindings_obsolete -isnot [bool] -or -not [bool]$lineage.legacy_goal_bindings_obsolete) { throw 'Legacy-successor identity/retirement binding is invalid.' }

        $predecessor = $lineage.predecessor
        if (-not (Test-ExactKeys -Object $predecessor -Required @('project_head_snapshot','run_id','run_path','contract','primary_manifest','backup_manifest','checkpoint','handoff'))) { throw 'Predecessor binding is incomplete.' }
        Assert-SafeLeafName -Value ([string]$predecessor.run_id) -Label 'predecessor run ID'
        $predecessorRunPath = Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ([string]$predecessor.run_path) -RequiredRoot 'runs' -PathType Container
        if ((Split-Path -Leaf $predecessorRunPath) -cne [string]$predecessor.run_id) { throw 'Predecessor run path/ID mismatch.' }

        $snapshot = $predecessor.project_head_snapshot
        if (-not (Test-ExactKeys -Object $snapshot -Required @('path','sha256')) -or [string]$snapshot.path -cnotmatch '^state[\\/]successors[\\/]g(?<generation>[0-9]{4,})-predecessor-project\.json$' -or [int64]$Matches['generation'] -ne $successorActivationGeneration) { throw 'Predecessor project-head snapshot pointer is invalid.' }
        Assert-LowerSha256 -Value ([string]$snapshot.sha256) -Label 'predecessor project-head snapshot hash'
        $snapshotPath = Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ([string]$snapshot.path) -RequiredRoot 'state' -PathType Leaf
        if ((Get-FileSha256 -LiteralPath $snapshotPath) -cne [string]$snapshot.sha256) { throw 'Predecessor project-head snapshot hash mismatches.' }
        $snapshotHead = Read-StrictJsonObject -LiteralPath $snapshotPath -Label 'predecessor project-head snapshot'
        if (-not $snapshotHead.Contains('project_id') -or [string]$snapshotHead.project_id -cne [string]$Project.project_id -or [string]$snapshotHead.schema -ceq 'math-research-project/v8') { throw 'Predecessor project-head snapshot identity/schema is invalid.' }
        $expectedGeneration = [int64]1
        if ($snapshotHead.Contains('control_generation') -and $null -ne $snapshotHead.control_generation) {
            if (-not (Test-NonnegativeJsonInteger $snapshotHead.control_generation)) { throw 'Predecessor project-head generation is malformed.' }
            $expectedGeneration = [int64]$snapshotHead.control_generation + 1
        }
        if ($successorActivationGeneration -ne $expectedGeneration) { throw 'Successor activation generation is not predecessor generation plus one.' }

        $predecessorPaths = @{}
        foreach ($name in @('contract','primary_manifest','backup_manifest','checkpoint','handoff')) {
            $filePointer = $predecessor[$name]
            if ($null -eq $filePointer) {
                if ($name -cin @('backup_manifest','checkpoint','handoff')) { continue }
                throw "Required predecessor $name pointer is null."
            }
            if (-not (Test-ExactKeys -Object $filePointer -Required @('path','sha256'))) { throw "Predecessor $name pointer is invalid." }
            Assert-LowerSha256 -Value ([string]$filePointer.sha256) -Label "predecessor $name hash"
            $requiredRoot = if ($name -ceq 'contract') { 'contracts' } elseif ($name -cin @('primary_manifest','backup_manifest')) { 'runs' } elseif ($name -ceq 'checkpoint') { 'state' } else { '.' }
            $filePath = Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ([string]$filePointer.path) -RequiredRoot $requiredRoot -PathType Leaf
            if ($name -cin @('primary_manifest','backup_manifest') -and -not (Test-PathInside -Child $filePath -Directory $predecessorRunPath)) { throw 'Predecessor manifest is outside predecessor run.' }
            if ((Get-FileSha256 -LiteralPath $filePath) -cne [string]$filePointer.sha256) { throw "Predecessor $name hash mismatches." }
            $predecessorPaths[$name] = $filePath
        }

        $artifactPointer = $lineage.inherited_artifact_index
        if (-not (Test-ExactKeys -Object $artifactPointer -Required @('path','sha256'))) { throw 'Inherited artifact-index pointer is invalid.' }
        Assert-LowerSha256 -Value ([string]$artifactPointer.sha256) -Label 'inherited artifact-index hash'
        $artifactIndexPath = Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ([string]$artifactPointer.path) -RequiredRoot 'runs' -PathType Leaf
        if (-not (Test-PathInside -Child $artifactIndexPath -Directory (Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ([string]$State.run.path) -RequiredRoot 'runs' -PathType Container)) -or (Get-FileSha256 -LiteralPath $artifactIndexPath) -cne [string]$artifactPointer.sha256) { throw 'Inherited artifact-index path/hash mismatches.' }
        $artifactIndex = Read-StrictJsonObject -LiteralPath $artifactIndexPath -Label 'inherited artifact index'
        if (-not (Test-ExactKeys -Object $artifactIndex -Required @('schema','project_id','predecessor_run_id','source_snapshot','inventory_algorithm','covers','entries','category_counts','entry_count','complete_source_inventory')) -or
            [string]$artifactIndex.schema -cne 'math-research-inherited-artifact-index/v8' -or [string]$artifactIndex.project_id -cne [string]$Project.project_id -or [string]$artifactIndex.predecessor_run_id -cne [string]$predecessor.run_id -or
            -not (Test-ResolvedContractString $artifactIndex.inventory_algorithm) -or $artifactIndex.complete_source_inventory -isnot [bool] -or -not [bool]$artifactIndex.complete_source_inventory) { throw 'Inherited artifact index schema/identity/completeness is invalid.' }
        $requiredCoverage = @('problem','verified_partial_results','attempts','failures','evidence','routes','audits','handoff','source_artifacts','computation_artifacts','intermediate_artifacts')
        $coverage = @($artifactIndex.covers)
        if (-not (Test-JsonArray $artifactIndex.covers) -or ($coverage -join '|') -cne ($requiredCoverage -join '|') -or -not (Test-JsonArray $artifactIndex.entries) -or @($artifactIndex.entries).Count -lt 1 -or
            -not (Test-NonnegativeJsonInteger $artifactIndex.entry_count) -or [int64]$artifactIndex.entry_count -ne @($artifactIndex.entries).Count -or -not (Test-ExactKeys -Object $artifactIndex.category_counts -Required $requiredCoverage)) { throw 'Inherited artifact index coverage/count shape is incomplete.' }
        $sourceSnapshot = $artifactIndex.source_snapshot
        if (-not (Test-ExactKeys -Object $sourceSnapshot -Required @('primary_manifest_sha256','backup_manifest_sha256','checkpoint_sha256','handoff_sha256','authoritative_index_heads')) -or
            [string]$sourceSnapshot.primary_manifest_sha256 -cne [string]$predecessor.primary_manifest.sha256 -or -not (Test-JsonArray $sourceSnapshot.authoritative_index_heads) -or @($sourceSnapshot.authoritative_index_heads).Count -lt 1) { throw 'Inherited artifact-index source snapshot is incomplete.' }
        foreach ($pair in @(@('backup_manifest','backup_manifest_sha256'),@('checkpoint','checkpoint_sha256'),@('handoff','handoff_sha256'))) {
            $predecessorPointer = $predecessor[$pair[0]]; $snapshotHash = $sourceSnapshot[$pair[1]]
            if ($null -eq $predecessorPointer) { if ($null -ne $snapshotHash) { throw 'Nullable predecessor/source-snapshot binding mismatches.' } }
            elseif ([string]$snapshotHash -cne [string]$predecessorPointer.sha256) { throw 'Predecessor/source-snapshot hash mismatches.' }
        }
        foreach ($head in @($sourceSnapshot.authoritative_index_heads)) {
            if (-not (Test-ExactKeys -Object $head -Required @('path','sha256'))) { throw 'Authoritative predecessor index-head pointer is invalid.' }
            Assert-LowerSha256 -Value ([string]$head.sha256) -Label 'authoritative predecessor index-head hash'
            $headPath = Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ([string]$head.path) -RequiredRoot '.' -PathType Leaf
            if ((Get-FileSha256 -LiteralPath $headPath) -cne [string]$head.sha256) { throw 'Authoritative predecessor index-head hash mismatches.' }
        }
        $categoryObserved = @{}; foreach ($category in $requiredCoverage) { $categoryObserved[$category] = [int64]0 }
        $entryKeys = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
        foreach ($entry in @($artifactIndex.entries)) {
            if (-not (Test-ExactKeys -Object $entry -Required @('category','path','sha256','evidence_grade')) -or [string]$entry.category -cnotin $requiredCoverage -or -not (Test-ResolvedContractString $entry.evidence_grade)) { throw 'Inherited artifact entry is invalid.' }
            Assert-LowerSha256 -Value ([string]$entry.sha256) -Label 'inherited artifact entry hash'
            $entryCanonical = ([string]$entry.path).Replace('\','/')
            if ($entryCanonical -cmatch '^state/(?:staging|generations)/' -or $entryCanonical -ceq ([string]$artifactPointer.path).Replace('\','/') -or $entryCanonical.StartsWith((([string]$State.run.path).Replace('\','/') + '/'),[StringComparison]::Ordinal)) { throw 'Inherited artifact index references successor staging/current-run material.' }
            $entryPath = Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ([string]$entry.path) -RequiredRoot '.' -PathType Leaf
            if ((Get-FileSha256 -LiteralPath $entryPath) -cne [string]$entry.sha256 -or -not $entryKeys.Add(([string]$entry.category + '|' + [string]$entry.path))) { throw 'Inherited artifact entry hash/uniqueness is invalid.' }
            $categoryObserved[[string]$entry.category]++
        }
        if ($categoryObserved.problem -lt 1) { throw 'Inherited artifact index must contain the predecessor problem.' }
        foreach ($category in $requiredCoverage) {
            if (-not (Test-NonnegativeJsonInteger $artifactIndex.category_counts[$category]) -or [int64]$artifactIndex.category_counts[$category] -ne $categoryObserved[$category]) { throw 'Inherited artifact category count mismatches entries.' }
        }

        $baselinePointer = $lineage.inherited_counter_budget_baseline
        if (-not (Test-ExactKeys -Object $baselinePointer -Required @('path','sha256')) -or [string]$baselinePointer.path -cnotmatch '^state[\\/]successor-baselines[\\/]g(?<generation>[0-9]{4,})\.json$' -or [int64]$Matches['generation'] -ne $successorActivationGeneration) { throw 'Inherited counter/budget baseline pointer is invalid.' }
        Assert-LowerSha256 -Value ([string]$baselinePointer.sha256) -Label 'inherited counter/budget baseline hash'
        $baselinePath = Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ([string]$baselinePointer.path) -RequiredRoot 'state' -PathType Leaf
        if ((Get-FileSha256 -LiteralPath $baselinePath) -cne [string]$baselinePointer.sha256) { throw 'Inherited counter/budget baseline hash mismatches.' }
        $baseline = Read-StrictJsonObject -LiteralPath $baselinePath -Label 'inherited counter/budget baseline'
        if (-not (Test-ExactKeys -Object $baseline -Required @('schema','project_id','predecessor_run_id','attempt_count','audit_count','total_round_count','attempts_since_last_audit','audit_due','budget_consumption')) -or
            [string]$baseline.schema -cne 'math-research-counter-budget-baseline/v8' -or [string]$baseline.project_id -cne [string]$Project.project_id -or [string]$baseline.predecessor_run_id -cne [string]$predecessor.run_id) { throw 'Inherited counter/budget baseline identity/shape is invalid.' }
        foreach ($name in @('attempt_count','audit_count','total_round_count','attempts_since_last_audit')) { if (-not (Test-NonnegativeJsonInteger $baseline[$name])) { throw 'Inherited counter baseline contains a non-integer.' } }
        if ($baseline.audit_due -isnot [bool] -or [decimal]$baseline.total_round_count -ne ([decimal]$baseline.attempt_count + [decimal]$baseline.audit_count) -or [decimal]$baseline.attempts_since_last_audit -gt [decimal]$baseline.attempt_count) { throw 'Inherited counter baseline is inconsistent.' }
        $budget = $baseline.budget_consumption
        if (-not (Test-ExactKeys -Object $budget -Required @('attempt_budget_ceiling','attempts_spent','total_round_budget_ceiling','total_rounds_spent','runtime_or_other_cumulative')) -or $budget.runtime_or_other_cumulative -isnot [Collections.IDictionary]) { throw 'Inherited budget baseline shape is invalid.' }
        foreach ($name in @('attempt_budget_ceiling','attempts_spent','total_round_budget_ceiling','total_rounds_spent')) { if (-not (Test-NonnegativeJsonInteger $budget[$name])) { throw 'Inherited budget baseline contains a non-integer.' } }
        if ([int64]$budget.attempts_spent -ne [int64]$baseline.attempt_count -or [int64]$budget.total_rounds_spent -ne [int64]$baseline.total_round_count -or
            [int64]$budget.attempt_budget_ceiling -ne [int64]$ContractEnvelope.MetadataIntegers.attempt_budget -or [int64]$budget.total_round_budget_ceiling -ne [int64]$ContractEnvelope.MetadataIntegers.total_round_budget -or
            [int64]$budget.attempts_spent -gt [int64]$budget.attempt_budget_ceiling -or [int64]$budget.total_rounds_spent -gt [int64]$budget.total_round_budget_ceiling) { throw 'Inherited budget baseline counters/ceilings mismatch.' }

        $successor = $lineage.successor
        if (-not (Test-ExactKeys -Object $successor -Required @('contract','run_id','run_path','run_genesis','host_bind')) -or
            -not (Test-ExactKeys -Object $successor.contract -Required @('path','binding_sha256')) -or [string]$successor.contract.path -cne [string]$State.contract.path -or [string]$successor.contract.binding_sha256 -cne [string]$State.contract.binding_sha256 -or
            [string]$successor.run_id -cne [string]$State.run.id -or [string]$successor.run_path -cne [string]$State.run.path) { throw 'Successor active Contract/run binding mismatches.' }
        $successorRunPath = Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ([string]$successor.run_path) -RequiredRoot 'runs' -PathType Container
        foreach ($name in @('run_genesis','host_bind')) {
            $successorPointer = $successor[$name]
            if (-not (Test-ExactKeys -Object $successorPointer -Required @('path','sha256'))) { throw "Successor $name pointer is invalid." }
            Assert-LowerSha256 -Value ([string]$successorPointer.sha256) -Label "successor $name hash"
            $successorFilePath = Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ([string]$successorPointer.path) -RequiredRoot 'runs' -PathType Leaf
            if (-not (Test-PathInside -Child $successorFilePath -Directory $successorRunPath) -or (Get-FileSha256 -LiteralPath $successorFilePath) -cne [string]$successorPointer.sha256) { throw "Successor $name path/hash mismatches." }
        }
        if ([string]$ContractEnvelope.Metadata.run_origin -cne 'legacy_successor' -or [string]$ContractEnvelope.Metadata.inherited_counter_budget_baseline_sha256 -cne [string]$baselinePointer.sha256) { throw 'Successor Contract origin/baseline binding mismatches.' }
        $stateSuccessor = $State.successor
        if (-not (Test-ExactKeys -Object $stateSuccessor -Required @('lineage','inherited_artifact_index','counter_budget_baseline')) -or
            -not (Test-FilePointer -Pointer $stateSuccessor.lineage -ExpectedPath ([string]$pointer.path) -ExpectedSha256 ([string]$pointer.sha256)) -or
            -not (Test-FilePointer -Pointer $stateSuccessor.inherited_artifact_index -ExpectedPath ([string]$artifactPointer.path) -ExpectedSha256 ([string]$artifactPointer.sha256)) -or
            -not (Test-FilePointer -Pointer $stateSuccessor.counter_budget_baseline -ExpectedPath ([string]$baselinePointer.path) -ExpectedSha256 ([string]$baselinePointer.sha256))) { throw 'Goal-host successor summary mismatches activated lineage.' }
        foreach ($name in @('attempt_count','audit_count','total_round_count')) { if ([decimal]$State.counters[$name] -lt [decimal]$baseline[$name]) { throw 'Current cumulative counters reset below inherited baseline.' } }
        if ([int64]$State.control_generation -eq $successorActivationGeneration) {
            foreach ($name in @('attempt_count','audit_count','total_round_count','attempts_since_last_audit','audit_due')) { if ([string]$State.counters[$name] -cne [string]$baseline[$name]) { throw 'Successor activation counters must equal inherited baseline.' } }
        }
        return [pscustomobject]@{ Valid=$true; Path=[string]$pointer.path }
    }
    catch { return [pscustomobject]@{ Valid=$false; Reason=$_.Exception.Message } }
}

function Read-GoalHostV8Advisory {
    param(
        [Parameter(Mandatory = $true)][string]$StatePath,
        [Parameter(Mandatory = $true)][string]$ProjectPath,
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Project,
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Checkpoint
    )
    try { $state = Read-StrictJsonObject -LiteralPath $StatePath -Label 'goal-host-v8 advisory state' }
    catch { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_not_strict_json'; Detail=$_.Exception.Message } }

    $topRequired = @('schema','project_id','control_generation','contract','run','host_goal','problem_statement_sha256','successor','counters','current_ticket','updated_at_utc')
    if (-not (Test-ExactKeys -Object $state -Required $topRequired)) {
        return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_shape_invalid' }
    }
    if ([string]$state.schema -cne 'math-research-goal-host-state/v8') { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_schema_invalid' } }
    if ([string]::IsNullOrWhiteSpace([string]$state.project_id) -or [string]$state.project_id -cne [string]$Project.project_id -or [string]$state.project_id -cne [string]$Checkpoint.project_id) {
        return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_project_identity_mismatch' }
    }
    if (-not (Test-NonnegativeJsonInteger $state.control_generation) -or [decimal]$state.control_generation -lt 1) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_generation_invalid' } }
    if (-not (Test-CurrentUtcTimestamp -Value ([string]$state.updated_at_utc))) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_timestamp_invalid_or_future' } }

    $contract = $state.contract
    $run = $state.run
    $hostGoal = $state.host_goal
    $counters = $state.counters
    if (-not (Test-ExactKeys -Object $contract -Required @('path','version','binding_sha256')) -or
        -not (Test-ExactKeys -Object $run -Required @('id','path','status')) -or
        -not (Test-ExactKeys -Object $hostGoal -Required @('thread_id_available','thread_id','objective_raw_sha256')) -or
        -not (Test-ExactKeys -Object $counters -Required @('attempt_count','audit_count','total_round_count','attempts_since_last_audit','audit_due'))) {
        return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_nested_shape_invalid' }
    }

    try {
        Assert-LowerSha256 -Value ([string]$contract.binding_sha256) -Label 'goal-host contract binding'
        Assert-LowerSha256 -Value ([string]$hostGoal.objective_raw_sha256) -Label 'goal-host raw objective binding'
        Assert-LowerSha256 -Value ([string]$state.problem_statement_sha256) -Label 'goal-host problem statement binding'
        Assert-SafeLeafName -Value ([string]$run.id) -Label 'goal-host run ID'
        if ([string]$contract.version -cne 'v8') { throw 'Direct Goal-host Contract version must be v8.' }
        if ($hostGoal.thread_id_available -isnot [bool]) { throw 'Host Goal thread-ID availability flag is invalid.' }
        if ([bool]$hostGoal.thread_id_available) {
            if ([string]::IsNullOrWhiteSpace([string]$hostGoal.thread_id) -or ([string]$hostGoal.thread_id).Length -gt 256 -or [string]$hostGoal.thread_id -match '[\x00-\x1f\x7f]') { throw 'Available Host Goal thread ID is invalid.' }
        }
        elseif ($null -ne $hostGoal.thread_id) { throw 'Unavailable Host Goal thread ID must be null.' }
        $contractPath = Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ([string]$contract.path) -RequiredRoot 'contracts' -PathType Leaf
        $runPath = Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ([string]$run.path) -RequiredRoot 'runs' -PathType Container
        if ((Split-Path -Parent $runPath) -cne [IO.Path]::GetFullPath((Join-Path $ProjectPath 'runs')) -or (Split-Path -Leaf $runPath) -cne [string]$run.id) { throw 'Run is not one direct child of runs.' }
        if ((Get-NormalizedTextSha256 -LiteralPath $contractPath) -cne [string]$contract.binding_sha256) { throw 'Contract binding does not match file bytes.' }
    }
    catch { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_resource_binding_invalid'; Detail=$_.Exception.Message } }

    $contractEnvelope = Read-GoalHostV8ContractEnvelope -ContractPath $contractPath -ExpectedVersion ([string]$contract.version) -ExpectedProjectId ([string]$state.project_id) `
        -ExpectedProjectDirectoryName (Split-Path -Leaf $ProjectPath) -ExpectedProjectIdentitySha256 ([string]$Project.project_identity_sha256) -ExpectedProjectPath $ProjectPath `
        -ExpectedProblemStatementSha256 ([string]$state.problem_statement_sha256)
    if (-not [bool]$contractEnvelope.Valid) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_contract_envelope_invalid'; Detail=[string]$contractEnvelope.Reason } }
    if([int64]$counters.attempts_since_last_audit-gt[int64]$contractEnvelope.MetadataIntegers.audit_interval_attempts-or[bool]$counters.audit_due-ne([int64]$counters.attempts_since_last_audit-eq[int64]$contractEnvelope.MetadataIntegers.audit_interval_attempts)){return [pscustomobject]@{Valid=$false;Reason='goal_host_state_audit_interval_gate_invalid'}}

    try {
        $runGenesisPath=Join-Path $runPath 'run.json';$runGenesis=Read-StrictJsonObject -LiteralPath $runGenesisPath -Label 'active RUN_GENESIS'
        if(-not(Test-ExactKeys -Object $runGenesis -Required @('schema','project_id','control_generation','contract','run','host_binding','host_goal'))-or[string]$runGenesis.schema-cne'math-research-run-genesis/v8'-or[string]$runGenesis.project_id-cne[string]$state.project_id-or-not(Test-NonnegativeJsonInteger $runGenesis.control_generation)-or[int64]$runGenesis.control_generation-lt1-or[int64]$runGenesis.control_generation-gt[int64]$state.control_generation-or
            -not(Test-ContractPointer -Pointer $runGenesis.contract -Expected $contract)-or-not(Test-ExactKeys -Object $runGenesis.run -Required @('id','path','status'))-or[string]$runGenesis.run.id-cne[string]$run.id-or[string]$runGenesis.run.path-cne[string]$run.path-or[string]$runGenesis.run.status-cnotin@('not_started','preparing')-or-not(Test-HostGoalPointer -Pointer $runGenesis.host_goal -Expected $runGenesis.host_goal)){throw 'RUN_GENESIS exact shape/identity is invalid.'}
        if(-not(Test-ExactKeys -Object $runGenesis.host_binding -Required @('path','sha256'))){throw 'RUN_GENESIS host-binding pointer is invalid.'};Assert-LowerSha256 -Value ([string]$runGenesis.host_binding.sha256) -Label 'RUN_GENESIS host-binding hash'
        $initialHostPath=Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ([string]$runGenesis.host_binding.path) -RequiredRoot 'runs' -PathType Leaf;if(-not(Test-PathInside -Child $initialHostPath -Directory $runPath)-or(Get-FileSha256 -LiteralPath $initialHostPath)-cne[string]$runGenesis.host_binding.sha256){throw 'RUN_GENESIS host binding path/hash is invalid.'}
        $initialHost=Read-StrictJsonObject -LiteralPath $initialHostPath -Label 'RUN_GENESIS initial HOST_BIND';$hostKeys=@('schema','project_id','control_generation','event_type','prior_host_binding','retirement','contract','run','host_goal')
        if(-not(Test-ExactKeys -Object $initialHost -Required $hostKeys)-or[string]$initialHost.schema-cne'math-research-host-binding/v8'-or[string]$initialHost.event_type-cne'HOST_BIND'-or$null-ne$initialHost.prior_host_binding-or$null-ne$initialHost.retirement-or[string]$initialHost.project_id-cne[string]$state.project_id-or[string]$initialHost.control_generation-cne[string]$runGenesis.control_generation-or
            -not(Test-ContractPointer -Pointer $initialHost.contract -Expected $contract)-or-not(Test-ExactKeys -Object $initialHost.run -Required @('id','path'))-or[string]$initialHost.run.id-cne[string]$run.id-or[string]$initialHost.run.path-cne[string]$run.path-or-not(Test-HostGoalPointer -Pointer $initialHost.host_goal -Expected $runGenesis.host_goal)){throw 'RUN_GENESIS does not bind one canonical initial HOST_BIND.'}
        if([int64]$state.control_generation-eq[int64]$runGenesis.control_generation-and(-not(Test-FilePointer -Pointer $runGenesis.host_binding -ExpectedPath ([string]$Project.host_binding_head.path) -ExpectedSha256 ([string]$Project.host_binding_head.sha256))-or-not(Test-HostGoalPointer -Pointer $runGenesis.host_goal -Expected $hostGoal))){throw 'First activation RUN_GENESIS/HOST_BIND/host_goal does not equal the active binding.'}
    }
    catch{return [pscustomobject]@{Valid=$false;Reason='goal_host_state_run_genesis_invalid';Detail=$_.Exception.Message}}

    $stateHasSuccessor = $null -ne $state.successor
    $projectHasSuccessor = $Project.Contains('legacy_successor') -and $null -ne $Project.legacy_successor
    if ($stateHasSuccessor -ne $projectHasSuccessor) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_successor_presence_drift' } }
    if (-not $stateHasSuccessor) {
        if ([string]$contractEnvelope.Metadata.run_origin -cne 'fresh' -or [string]$contractEnvelope.Metadata.inherited_counter_budget_baseline_sha256 -cne 'null') { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_fresh_contract_origin_invalid' } }
    }
    elseif ([string]$contractEnvelope.Metadata.run_origin -cne 'legacy_successor') { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_successor_contract_origin_invalid' } }

    foreach ($counterName in @('attempt_count','audit_count','total_round_count','attempts_since_last_audit')) {
        if (-not (Test-NonnegativeJsonInteger $counters[$counterName])) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_counter_invalid' } }
    }
    if ($counters.audit_due -isnot [bool] -or [decimal]$counters.attempts_since_last_audit -gt [decimal]$counters.attempt_count -or
        [decimal]$counters.total_round_count -ne ([decimal]$counters.attempt_count + [decimal]$counters.audit_count)) {
        return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_counter_inconsistent' }
    }
    if ([int64]$counters.attempt_count -gt [int64]$contractEnvelope.MetadataIntegers.attempt_budget -or [int64]$counters.total_round_count -gt [int64]$contractEnvelope.MetadataIntegers.total_round_budget) {
        return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_contract_budget_exceeded' }
    }

    foreach ($key in @('active_contract','active_run','control_generation','problem_statement_sha256','project_identity_sha256','project_event_head','host_binding_head')) {
        if (-not $Project.Contains($key) -or $null -eq $Project[$key]) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_project_authority_missing' } }
    }
    if (-not $Project.Contains('legacy_successor')) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_project_authority_missing' } }
    $checkpointKeys = @('schema','project_id','control_generation','contract','run','problem_statement_sha256','host_goal','host_binding_head','counters','current_lifecycle','successor','completion_ready','pending_goal_update','last_run_event','updated_at_utc')
    if (-not (Test-ExactKeys -Object $Checkpoint -Required $checkpointKeys) -or [string]$Checkpoint.schema -cne 'math-research-checkpoint/v8' -or
        -not (Test-CurrentUtcTimestamp -Value ([string]$Checkpoint.updated_at_utc)) -or $Checkpoint.completion_ready -isnot [bool] -or $Checkpoint.pending_goal_update -isnot [bool] -or [bool]$Checkpoint.completion_ready -ne [bool]$Checkpoint.pending_goal_update) {
        return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_checkpoint_authority_missing' }
    }
    foreach ($key in @('contract','run','control_generation','problem_statement_sha256','host_goal','host_binding_head','counters','last_run_event')) {
        if (-not $Checkpoint.Contains($key) -or $null -eq $Checkpoint[$key]) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_checkpoint_authority_missing' } }
    }
    if (-not (Test-ExactKeys -Object $Project.active_contract -Required @('path','version','binding_sha256')) -or -not (Test-ExactKeys -Object $Checkpoint.contract -Required @('path','version','binding_sha256'))) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_contract_authority_shape_invalid' } }
    if (-not (Test-ExactKeys -Object $Project.active_run -Required @('id','path','status')) -or -not (Test-ExactKeys -Object $Checkpoint.run -Required @('id','path','status'))) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_run_authority_shape_invalid' } }
    if (-not (Test-ContractPointer -Pointer $Project.active_contract -Expected $contract)) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_project_contract_drift' } }
    if (-not (Test-ContractPointer -Pointer $Checkpoint.contract -Expected $contract)) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_checkpoint_contract_drift' } }
    if (-not (Test-RunPointer -Pointer $Project.active_run -Expected $run)) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_project_run_drift' } }
    if (-not (Test-RunPointer -Pointer $Checkpoint.run -Expected $run)) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_checkpoint_run_drift' } }
    if ([string]$Project.control_generation -cne [string]$state.control_generation -or [string]$Checkpoint.control_generation -cne [string]$state.control_generation) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_generation_drift' } }
    if ([string]$Project.problem_statement_sha256 -cne [string]$state.problem_statement_sha256 -or [string]$Checkpoint.problem_statement_sha256 -cne [string]$state.problem_statement_sha256) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_problem_binding_drift' } }
    if (-not (Test-HostGoalPointer -Pointer $Checkpoint.host_goal -Expected $hostGoal)) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_host_goal_binding_drift' } }
    if (-not (Test-ExactKeys -Object $Checkpoint.counters -Required @('attempt_count','audit_count','total_round_count','attempts_since_last_audit','audit_due'))) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_checkpoint_authority_missing' } }
    foreach ($counterName in @('attempt_count','audit_count','total_round_count','attempts_since_last_audit','audit_due')) {
        if ([string]$Checkpoint.counters[$counterName] -cne [string]$counters[$counterName]) { return [pscustomobject]@{ Valid=$false; Reason="goal_host_state_checkpoint_${counterName}_drift" } }
    }
    if (-not (Test-JsonDeepEqual -Left $Checkpoint.successor -Right $state.successor)) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_checkpoint_successor_drift' } }

    $cycleAuditSummaryResult=$null
    $auditedCompletionSummary=$null
    $pausedResumeCapsule=$null
    try {
        $projectHostHead = $Project.host_binding_head
        if (-not (Test-ExactKeys -Object $projectHostHead -Required @('path','sha256','control_generation')) -or -not (Test-NonnegativeJsonInteger $projectHostHead.control_generation) -or
            [int64]$projectHostHead.control_generation -lt 1 -or [int64]$projectHostHead.control_generation -gt [int64]$state.control_generation -or
            [string]$projectHostHead.path -cnotmatch '^runs[\\/][^\\/]+[\\/]host-bindings[\\/]host-bind-g(?<generation>[0-9]{4,})\.json$' -or [int64]$Matches['generation'] -ne [int64]$projectHostHead.control_generation) { throw 'Project host-binding head is invalid.' }
        Assert-LowerSha256 -Value ([string]$projectHostHead.sha256) -Label 'project host-binding head hash'
        $hostBindPath = Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ([string]$projectHostHead.path) -RequiredRoot 'runs' -PathType Leaf
        if (-not (Test-PathInside -Child $hostBindPath -Directory $runPath) -or (Get-FileSha256 -LiteralPath $hostBindPath) -cne [string]$projectHostHead.sha256 -or
            -not (Test-FilePointer -Pointer $Checkpoint.host_binding_head -ExpectedPath ([string]$projectHostHead.path) -ExpectedSha256 ([string]$projectHostHead.sha256))) { throw 'Host-binding head path/hash drifts.' }
        $hostBind = Read-StrictJsonObject -LiteralPath $hostBindPath -Label 'active host binding'
        $hostBindKeys = @('schema','project_id','control_generation','event_type','prior_host_binding','retirement','contract','run','host_goal')
        if (-not (Test-ExactKeys -Object $hostBind -Required $hostBindKeys) -or [string]$hostBind.schema -cne 'math-research-host-binding/v8' -or
            [string]$hostBind.project_id -cne [string]$state.project_id -or [string]$hostBind.control_generation -cne [string]$projectHostHead.control_generation -or
            -not (Test-ExactKeys -Object $hostBind.contract -Required @('path','version','binding_sha256')) -or -not (Test-ContractPointer -Pointer $hostBind.contract -Expected $contract) -or
            -not (Test-ExactKeys -Object $hostBind.run -Required @('id','path')) -or [string]$hostBind.run.id -cne [string]$run.id -or [string]$hostBind.run.path -cne [string]$run.path -or
            -not (Test-HostGoalPointer -Pointer $hostBind.host_goal -Expected $hostGoal)) { throw 'Active host-binding content drifts from advisory state.' }
        if ([string]$hostBind.event_type -ceq 'HOST_BIND') {
            if ($null -ne $hostBind.prior_host_binding -or $null -ne $hostBind.retirement) { throw 'Initial HOST_BIND must have null prior/retirement fields.' }
        }
        elseif ([string]$hostBind.event_type -ceq 'HOST_REBIND') {
            if (-not (Test-ExactKeys -Object $hostBind.prior_host_binding -Required @('path','sha256','control_generation')) -or
                -not (Test-NonnegativeJsonInteger $hostBind.prior_host_binding.control_generation) -or [int64]$hostBind.prior_host_binding.control_generation -lt 1 -or
                [int64]$hostBind.prior_host_binding.control_generation -ge [int64]$hostBind.control_generation -or
                -not (Test-ExactKeys -Object $hostBind.retirement -Required @('authority','reason')) -or [string]$hostBind.retirement.authority -cne 'user-explicit-revocation' -or
                [string]::IsNullOrWhiteSpace([string]$hostBind.retirement.reason)) { throw 'HOST_REBIND prior/retirement authorization is invalid.' }
            Assert-LowerSha256 -Value ([string]$hostBind.prior_host_binding.sha256) -Label 'prior host-binding hash'
            $priorHostPath = Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ([string]$hostBind.prior_host_binding.path) -RequiredRoot 'runs' -PathType Leaf
            if (-not (Test-PathInside -Child $priorHostPath -Directory $runPath) -or (Get-FileSha256 -LiteralPath $priorHostPath) -cne [string]$hostBind.prior_host_binding.sha256) { throw 'HOST_REBIND prior binding path/hash is invalid.' }
        }
        else { throw 'Host-binding event_type is outside HOST_BIND/HOST_REBIND.' }

        $projectEventHead = $Project.project_event_head
        if (-not (Test-ExactKeys -Object $projectEventHead -Required @('path','sha256','control_generation')) -or -not (Test-NonnegativeJsonInteger $projectEventHead.control_generation) -or [string]$projectEventHead.control_generation -cne [string]$state.control_generation) { throw 'Project event-head pointer is invalid.' }
        Assert-LowerSha256 -Value ([string]$projectEventHead.sha256) -Label 'project event-head hash'
        $projectEventPath = Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ([string]$projectEventHead.path) -RequiredRoot 'state' -PathType Leaf
        if ((Get-FileSha256 -LiteralPath $projectEventPath) -cne [string]$projectEventHead.sha256) { throw 'Project event-head hash mismatches.' }
        $projectEvent = Read-StrictJsonObject -LiteralPath $projectEventPath -Label 'project event head'
        $projectEventKeys = @('schema','project_id','control_generation','event_id','event_type','updated_at_utc','previous_event_sha256','contract','run','counters','referenced_artifacts')
        $projectEventTypes = @('RUN_GENESIS','LEGACY_SUCCESSOR','CHECKPOINT_COMMIT','ATTEMPT_START','ATTEMPT_END','AUDIT_START','AUDIT_END','HOST_REBIND','PAUSE','RESUME','COMPLETION_READY')
        if (-not (Test-ExactKeys -Object $projectEvent -Required $projectEventKeys) -or
            [string]$projectEvent.schema -cne 'math-research-project-event/v8' -or [string]$projectEvent.project_id -cne [string]$state.project_id -or [string]$projectEvent.control_generation -cne [string]$state.control_generation -or
            [string]$projectEvent.event_id -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$' -or [string]$projectEvent.event_type -cnotin $projectEventTypes -or -not (Test-CurrentUtcTimestamp -Value ([string]$projectEvent.updated_at_utc)) -or
            -not (Test-ContractPointer -Pointer $projectEvent.contract -Expected $contract) -or -not (Test-RunPointer -Pointer $projectEvent.run -Expected $run) -or
            -not (Test-JsonDeepEqual -Left $projectEvent.counters -Right $counters) -or -not (Test-JsonArray $projectEvent.referenced_artifacts) -or
            -not (Test-ExactKeys -Object $Checkpoint.last_run_event -Required @('id','sha256')) -or [string]$Checkpoint.last_run_event.id -cne [string]$projectEvent.event_id -or [string]$Checkpoint.last_run_event.sha256 -cne [string]$projectEventHead.sha256) { throw 'Project event/head/checkpoint binding drifts.' }
        if ([string]$projectEvent.event_type -cin @('RUN_GENESIS','LEGACY_SUCCESSOR')) {
            if ($null -ne $projectEvent.previous_event_sha256) { throw 'First v8 activation event must have null previous_event_sha256.' }
        }
        else {
            Assert-LowerSha256 -Value ([string]$projectEvent.previous_event_sha256) -Label 'project event previous hash'
            $canonicalPriorGeneration=[int64]$state.control_generation-1
            if($canonicalPriorGeneration-lt1){throw 'Non-activation project event has no predecessor generation.'}
            $canonicalPriorPath=Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ('state/project-events/g{0:D4}.json'-f$canonicalPriorGeneration) -RequiredRoot 'state' -PathType Leaf
            if((Get-FileSha256 -LiteralPath $canonicalPriorPath)-cne[string]$projectEvent.previous_event_sha256){throw 'Project event previous_event_sha256 does not bind the canonical predecessor generation.'}
        }
        foreach ($eventArtifact in @($projectEvent.referenced_artifacts)) { $null=Assert-ImmutableRawPointer -Pointer $eventArtifact -ProjectPath $ProjectPath -Label 'project event referenced artifact' }
        $attemptOutcome=$null
        if([string]$projectEvent.event_type-ceq'ATTEMPT_END'){
            if(@($projectEvent.referenced_artifacts).Count-ne1){throw 'Every ATTEMPT_END must publish exactly one immutable attempt outcome.'}
            $attemptOutcome=Assert-AttemptOutcomeV8 -Pointer $projectEvent.referenced_artifacts[0] -ProjectPath $ProjectPath -ExpectedProjectId ([string]$state.project_id) -ExpectedContract $contract -ExpectedRun $run
        }

        switch([string]$projectEvent.event_type){
            {$_-cin@('RUN_GENESIS','LEGACY_SUCCESSOR')} {if([string]$run.status-cnotin@('not_started','preparing')){throw 'Activation event run status is invalid.'};break}
            'ATTEMPT_START' {if([string]$run.status-cne'attempt_running'){throw 'ATTEMPT_START must enter attempt_running.'};break}
            'ATTEMPT_END' {
                $kind=[string]$attemptOutcome.Record.outcome
                $statusInvalid=if($kind-ceq'candidate_found'){[string]$run.status-cne'completion_candidate'}elseif([bool]$counters.audit_due){[string]$run.status-cne'audit_due'}elseif($kind-ceq'awaiting_input'){[string]$run.status-cne'awaiting_input'}else{[string]$run.status-cnotin@('not_started','preparing')}
                if($statusInvalid){throw 'ATTEMPT_END run status differs from its verified outcome/audit gate.'};break
            }
            'AUDIT_START' {if([string]$run.status-cne'auditing'){throw 'AUDIT_START must enter auditing.'};break}
            'AUDIT_END' {if([string]$run.status-ceq'auditing'){throw 'AUDIT_END cannot remain auditing.'};break}
            'PAUSE' {if([string]$run.status-cne'paused'){throw 'PAUSE must enter paused.'};break}
            'COMPLETION_READY' {if([string]$run.status-cne'closed'){throw 'COMPLETION_READY must enter closed.'};break}
        }

        if([string]$projectEvent.event_type-ceq'AUDIT_START'){
            if([string]$run.status-cne'auditing'-or@($projectEvent.referenced_artifacts).Count-ne1-or$null-eq$state.current_ticket){throw 'AUDIT_START must enter auditing and publish exactly one three-role audit plan.'}
            $planPath=Assert-ImmutableRawPointer -Pointer $projectEvent.referenced_artifacts[0] -ProjectPath $ProjectPath -Label 'cycle-audit plan';$planPreview=Read-StrictJsonObject -LiteralPath $planPath -Label 'cycle-audit plan preview';$auditKind=[string]$planPreview.audit_kind
            if($auditKind-cnotin@('scheduled','early','terminal')){throw 'AUDIT_START plan has an invalid audit_kind.'}
            $priorGeneration=[int64]$state.control_generation-1;if($priorGeneration-lt1){throw 'AUDIT_START has no predecessor generation.'}
            $priorPath=Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ('state/project-events/g{0:D4}.json'-f$priorGeneration) -RequiredRoot 'state' -PathType Leaf;$priorEvent=Read-StrictJsonObject -LiteralPath $priorPath -Label 'AUDIT_START predecessor event'
            $expectedAuditKind=if([string]$priorEvent.run.status-ceq'completion_candidate'){'terminal'}elseif([bool]$priorEvent.counters.audit_due){'scheduled'}else{'early'}
            if($auditKind-cne$expectedAuditKind){throw 'AUDIT_START kind does not match its predecessor completion/audit gate.'}
            $expectedAuditCandidate=$null
            if($auditKind-ceq'terminal'){
                $priorRun=[ordered]@{id=[string]$run.id;path=[string]$run.path;status='completion_candidate'}
                $priorOutcome=Get-PreAuditCompletionOutcomeV8 -HeadEvent $priorEvent -HeadGeneration $priorGeneration -ProjectPath $ProjectPath -ExpectedProjectId ([string]$state.project_id) -ExpectedContract $contract -ExpectedRun $priorRun
                if($null-eq$priorOutcome){throw 'Terminal AUDIT_START predecessor lacks one candidate_found outcome chain.'};$expectedAuditCandidate=$priorOutcome.Outcome.candidate
            }
            $null=Assert-CycleAuditPlan -Pointer $projectEvent.referenced_artifacts[0] -ProjectPath $ProjectPath -ExpectedProjectId ([string]$state.project_id) -ExpectedContract $contract -ExpectedRun $run -Generation ([int64]$state.control_generation) -Counters $counters -CurrentTicket $state.current_ticket -ContractEnvelope $contractEnvelope -ExpectedAuditKind $auditKind -ExpectedCandidate $expectedAuditCandidate
        }
        if([string]$projectEvent.event_type-ceq'AUDIT_END'){
            if(@($projectEvent.referenced_artifacts).Count-ne1){throw 'Every AUDIT_END must publish exactly one cycle-audit summary.'}
            $summaryPath=Assert-ImmutableRawPointer -Pointer $projectEvent.referenced_artifacts[0] -ProjectPath $ProjectPath -Label 'cycle-audit summary';$summaryPreview=Read-StrictJsonObject -LiteralPath $summaryPath -Label 'cycle-audit summary preview';$auditKind=[string]$summaryPreview.audit_kind
            if($auditKind-cnotin@('scheduled','early','terminal')-or([string]$run.status-ceq'completion_candidate'-and$auditKind-cne'terminal')-or($auditKind-cne'terminal'-and[string]$run.status-ceq'completion_candidate')){throw 'AUDIT_END status and audit_kind are incompatible.'}
            $cycleAuditSummaryResult=Assert-CycleAuditSummary -Pointer $projectEvent.referenced_artifacts[0] -ProjectPath $ProjectPath -ExpectedProjectId ([string]$state.project_id) -ExpectedContract $contract -ExpectedRun $run -ExpectedAuditKind $auditKind
            $null=Assert-CycleAuditHistory -SummaryResult $cycleAuditSummaryResult -EndEvent $projectEvent -EndGeneration ([int64]$state.control_generation) -ProjectPath $ProjectPath -ExpectedProjectId ([string]$state.project_id) -ExpectedContract $contract -ExpectedRun $run -ContractEnvelope $contractEnvelope
            if($auditKind-ceq'terminal'){
                if([bool]$cycleAuditSummaryResult.AllPass){if([string]$run.status-cne'completion_candidate'-or$null-ne$state.current_ticket-or$null-ne$Checkpoint.current_lifecycle){throw 'Three-PASS terminal AUDIT_END must return one null-ticket completion_candidate.'}}
                elseif([string]$run.status-cnotin@('preparing','awaiting_input')){throw 'Terminal FAIL/INCONCLUSIVE cannot preserve completion_candidate.'}
            }
        }

        if([string]$run.status-ceq'completion_candidate'){
            $auditedCompletionSummary=Get-AuditedCompletionSummary -HeadEvent $projectEvent -HeadGeneration ([int64]$state.control_generation) -ProjectPath $ProjectPath -ExpectedProjectId ([string]$state.project_id) -ExpectedContract $contract -ExpectedRun $run -ContractEnvelope $contractEnvelope
            if($null-eq$auditedCompletionSummary){$preAuditCompletionOutcome=Get-PreAuditCompletionOutcomeV8 -HeadEvent $projectEvent -HeadGeneration ([int64]$state.control_generation) -ProjectPath $ProjectPath -ExpectedProjectId ([string]$state.project_id) -ExpectedContract $contract -ExpectedRun $run;if($null-eq$preAuditCompletionOutcome){throw 'Unaudited completion_candidate has no authoritative candidate_found ATTEMPT_END outcome chain.'}}
            if($null-ne$auditedCompletionSummary-and($null-ne$state.current_ticket-or$null-ne$Checkpoint.current_lifecycle)){throw 'Audited completion candidate must have null ticket/lifecycle.'}
        }

        if([string]$run.status-ceq'paused'){
            $pausedResumeCapsule=Get-PausedResumeCapsule -HeadEvent $projectEvent -HeadGeneration ([int64]$state.control_generation) -ProjectPath $ProjectPath -ExpectedProjectId ([string]$state.project_id) -ExpectedContract $contract -ExpectedRun $run -ExpectedTicket $state.current_ticket -ExpectedLifecycle $Checkpoint.current_lifecycle -ExpectedCounters $counters
            if($null-eq$pausedResumeCapsule){throw 'Paused state lacks one exact PAUSE/resume-capsule authority chain.'}
        }

        if([string]$projectEvent.event_type-ceq'RESUME'){
            $priorGeneration=[int64]$state.control_generation-1
            if($priorGeneration-lt1){throw 'RESUME has no predecessor generation.'}
            $priorEventPath=Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ('state/project-events/g{0:D4}.json'-f$priorGeneration) -RequiredRoot 'state' -PathType Leaf;$priorHash=Get-FileSha256 -LiteralPath $priorEventPath
            if([string]$projectEvent.previous_event_sha256-cne$priorHash){throw 'RESUME predecessor hash is invalid.'};$priorEvent=Read-StrictJsonObject -LiteralPath $priorEventPath -Label 'RESUME predecessor event'
            if([string]$priorEvent.run.status-ceq'paused'){
                $priorRun=[ordered]@{id=[string]$run.id;path=[string]$run.path;status='paused'}
                $resumeCapsule=Get-PausedResumeCapsule -HeadEvent $priorEvent -HeadGeneration $priorGeneration -ProjectPath $ProjectPath -ExpectedProjectId ([string]$state.project_id) -ExpectedContract $contract -ExpectedRun $priorRun -ExpectedTicket $state.current_ticket -ExpectedLifecycle $Checkpoint.current_lifecycle -ExpectedCounters $counters
                if($null-eq$resumeCapsule-or[string]$run.status-cne[string]$resumeCapsule.Capsule.prior_status-or@($projectEvent.referenced_artifacts).Count-ne1-or-not(Test-RawPointerEqual -Left $projectEvent.referenced_artifacts[0] -Right $resumeCapsule.Pointer)){throw 'RESUME does not restore its exact paused capsule.'}
            }
            elseif([string]$priorEvent.run.status-ceq'awaiting_input'){
                $expectedStatuses=if([bool]$counters.audit_due){@('audit_due')}else{@('not_started','preparing')}
                if([string]$run.status-cnotin$expectedStatuses-or@($projectEvent.referenced_artifacts).Count-ne0){throw 'awaiting_input RESUME must route exactly according to its durable audit_due gate.'}
            }
            else{throw 'RESUME predecessor is neither paused nor awaiting_input.'}
        }

        if([string]$projectEvent.event_type-ceq'COMPLETION_READY'){
            $priorGeneration=[int64]$state.control_generation-1
            if($priorGeneration-lt1){throw 'COMPLETION_READY has no predecessor generation.'}
            $priorEventPath=Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ('state/project-events/g{0:D4}.json'-f$priorGeneration) -RequiredRoot 'state' -PathType Leaf;$priorHash=Get-FileSha256 -LiteralPath $priorEventPath
            if([string]$projectEvent.previous_event_sha256-cne$priorHash){throw 'COMPLETION_READY predecessor hash is invalid.'};$priorEvent=Read-StrictJsonObject -LiteralPath $priorEventPath -Label 'audited completion predecessor event'
            $candidateRun=[ordered]@{id=[string]$run.id;path=[string]$run.path;status='completion_candidate'}
            $priorSummary=Get-AuditedCompletionSummary -HeadEvent $priorEvent -HeadGeneration $priorGeneration -ProjectPath $ProjectPath -ExpectedProjectId ([string]$state.project_id) -ExpectedContract $contract -ExpectedRun $candidateRun -ContractEnvelope $contractEnvelope
            if($null-eq$priorSummary-or@($projectEvent.referenced_artifacts).Count-ne1-or-not(Test-RawPointerEqual -Left $projectEvent.referenced_artifacts[0] -Right $priorSummary.Pointer)){throw 'COMPLETION_READY must follow and republish one authoritative audited-completion certificate.'}
        }
        if ([bool]$Checkpoint.completion_ready) {
            if ([string]$projectEvent.event_type -cne 'COMPLETION_READY' -or [string]$run.status -cne 'closed' -or $null -ne $state.current_ticket -or @($projectEvent.referenced_artifacts).Count -lt 1) { throw 'Durable completion flags lack one closed COMPLETION_READY event with referenced evidence.' }
        }
        elseif ([string]$projectEvent.event_type -ceq 'COMPLETION_READY') { throw 'COMPLETION_READY event lacks durable checkpoint flags.' }
    }
    catch { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_host_or_event_binding_invalid'; Detail=$_.Exception.Message } }

    $ticket = $state.current_ticket
    if ($null -ne $ticket) {
        if (-not (Test-ExactKeys -Object $ticket -Required @('id','path','sha256','status','contract_initial_tickets_sha256','counter_snapshot','source_event')) -or
            -not (Test-ExactKeys -Object $ticket.counter_snapshot -Required @('attempt_count','audit_count','total_round_count'))) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_ticket_shape_invalid' } }
        try {
            Assert-SafeLeafName -Value ([string]$ticket.id) -Label 'goal-host ticket ID'
            Assert-LowerSha256 -Value ([string]$ticket.sha256) -Label 'goal-host ticket hash'
            Assert-LowerSha256 -Value ([string]$ticket.contract_initial_tickets_sha256) -Label 'goal-host Contract initial-ticket hash'
            if ([string]$ticket.contract_initial_tickets_sha256 -cne [string]$contractEnvelope.Metadata.initial_tickets_sha256) { throw 'Ticket pointer does not bind the Contract initial-ticket block.' }
            foreach ($counterName in @('attempt_count','audit_count','total_round_count')) {
                if (-not (Test-NonnegativeJsonInteger $ticket.counter_snapshot[$counterName]) -or [string]$ticket.counter_snapshot[$counterName] -cne [string]$counters[$counterName]) { throw 'Ticket pointer counter snapshot drifts.' }
            }
            if ([string]$ticket.status -cnotin @('frozen','ready','active','awaiting_verification','closed')) { throw 'Ticket status is outside the closed set.' }
            $ticketPath = Assert-ImmutableRawPointer -Pointer ([ordered]@{path=[string]$ticket.path;sha256=[string]$ticket.sha256}) -ProjectPath $ProjectPath -Label 'current frozen ticket' -RequiredRoot 'runs'
            if (-not (Test-PathInside -Child $ticketPath -Directory $runPath) -or (Get-FileSha256 -LiteralPath $ticketPath) -cne [string]$ticket.sha256) { throw 'Ticket path/hash is not bound to the active run.' }
            $ticketText = [Text.UTF8Encoding]::new($false, $true).GetString([IO.File]::ReadAllBytes($ticketPath))
            $ticketRecord = Read-StrictJsonText -Text $ticketText -Label 'frozen current ticket'
            if (-not (Test-ExactKeys -Object $ticketRecord -Required @('schema','project_id','control_generation','contract','run','cycle_id','contract_initial_tickets_sha256','counter_snapshot','ticket')) -or
                [string]$ticketRecord.schema -cne 'math-research-frozen-ticket/v8' -or [string]$ticketRecord.project_id -cne [string]$state.project_id -or -not(Test-NonnegativeJsonInteger $ticketRecord.control_generation) -or [int64]$ticketRecord.control_generation-lt1-or[int64]$ticketRecord.control_generation-gt[int64]$state.control_generation -or
                -not (Test-ContractPointer -Pointer $ticketRecord.contract -Expected $contract) -or -not(Test-ExactKeys -Object $ticketRecord.run -Required @('id','path','status'))-or[string]$ticketRecord.run.id-cne[string]$run.id-or[string]$ticketRecord.run.path-cne[string]$run.path -or
                [string]$ticketRecord.cycle_id -cne [string]$contractEnvelope.Tickets.cycle_id -or [string]$ticketRecord.contract_initial_tickets_sha256 -cne [string]$contractEnvelope.Metadata.initial_tickets_sha256 -or
                -not (Test-JsonDeepEqual -Left $ticketRecord.counter_snapshot -Right $counters) -or [string]$ticketRecord.ticket.ticket_id -cne [string]$ticket.id) { throw 'Frozen ticket envelope identity/ledger binding is invalid.' }
            $initialPhase = $null -eq $ticket.source_event
            if ($initialPhase) {
                if([string]$ticketRecord.ticket.role-cne'solver'){throw 'An initial source_event-null ticket must have role solver.'}
                if ([string]$run.status -cnotin @('not_started','preparing','paused','awaiting_input')) { throw 'Initial ticket source/lifecycle is incompatible with run status.' }
                $contractTicketMatches = @($contractEnvelope.Tickets.tickets | Where-Object { $_ -is [Collections.IDictionary] -and [string]$_.ticket_id -ceq [string]$ticket.id })
                if ($contractTicketMatches.Count -ne 1 -or -not (Test-JsonDeepEqual -Left $ticketRecord.ticket -Right $contractTicketMatches[0]) -or $null -ne $ticket.source_event) { throw 'Initial frozen ticket must exactly equal one Contract member and have null source_event.' }
            }
            else {
                if ([string]$run.status -ceq 'not_started') { throw 'A not_started run cannot activate a derived ticket.' }
                Assert-V8TicketBody -Ticket $ticketRecord.ticket -Metadata $contractEnvelope.Metadata -MetadataIntegers $contractEnvelope.MetadataIntegers -ProjectPath $ProjectPath -ActiveRun $run -ActiveContract $contract
                $sourceEventPointer = $ticket.source_event
                if (-not (Test-ExactKeys -Object $sourceEventPointer -Required @('path','sha256'))) { throw 'Derived ticket source-event pointer is invalid.' }
                Assert-LowerSha256 -Value ([string]$sourceEventPointer.sha256) -Label 'derived ticket source-event hash'
                $sourceEventPath = Assert-ImmutableRawPointer -Pointer $sourceEventPointer -ProjectPath $ProjectPath -Label 'derived ticket source event' -RequiredRoot 'runs'
                if (-not (Test-PathInside -Child $sourceEventPath -Directory $runPath) -or (Get-FileSha256 -LiteralPath $sourceEventPath) -cne [string]$sourceEventPointer.sha256) { throw 'Derived ticket source event is not hash-bound inside the run.' }
                $sourceEvent = Read-StrictJsonObject -LiteralPath $sourceEventPath -Label 'derived ticket source event'
                $ticketEventKeys = @('schema','project_id','control_generation','event_id','ticket_id','ticket','role','contract','run','counters','input_artifacts','dependencies','updated_at_utc')
                if (-not (Test-ExactKeys -Object $sourceEvent -Required $ticketEventKeys) -or [string]$sourceEvent.schema -cne 'math-research-ticket-event/v8' -or
                    [string]$sourceEvent.project_id -cne [string]$state.project_id -or [string]$sourceEvent.control_generation -cne [string]$ticketRecord.control_generation -or
                    [string]$sourceEvent.event_id -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$' -or [string]$sourceEvent.ticket_id -cne [string]$ticket.id -or
                    -not (Test-FilePointer -Pointer $sourceEvent.ticket -ExpectedPath ([string]$ticket.path) -ExpectedSha256 ([string]$ticket.sha256)) -or
                    [string]$sourceEvent.role -cne [string]$ticketRecord.ticket.role -or -not (Test-ContractPointer -Pointer $sourceEvent.contract -Expected $contract) -or
                    -not (Test-ExactKeys -Object $sourceEvent.run -Required @('id','path')) -or [string]$sourceEvent.run.id -cne [string]$run.id -or [string]$sourceEvent.run.path -cne [string]$run.path -or
                    -not (Test-JsonDeepEqual -Left $sourceEvent.counters -Right $counters) -or -not (Test-JsonDeepEqual -Left $sourceEvent.input_artifacts -Right $ticketRecord.ticket.input_artifacts) -or
                    -not (Test-JsonArray $sourceEvent.dependencies) -or -not (Test-JsonDeepEqual -Left $sourceEvent.dependencies -Right $ticketRecord.ticket.dependencies) -or -not (Test-CurrentUtcTimestamp -Value ([string]$sourceEvent.updated_at_utc))) { throw 'Derived ticket source event content is invalid.' }
                foreach ($dependency in @($sourceEvent.dependencies)) {
                    if (-not (Test-ExactKeys -Object $dependency -Required @('ticket_id','path','sha256'))) { throw 'Derived ticket dependency binding is invalid.' }
                    Assert-LowerSha256 -Value ([string]$dependency.sha256) -Label 'derived ticket dependency hash'
                }
            }
            if([string]$projectEvent.event_type-ceq'ATTEMPT_END'-and[string]$attemptOutcome.Record.outcome-ceq'candidate_found'){
                if($initialPhase-or[string]$ticketRecord.ticket.role-cne'verifier'-or[string]$ticket.id-cne[string]$attemptOutcome.VerifierTicketId-or-not(Test-RawPointerEqual -Left $ticketRecord.ticket.candidate_artifact -Right $attemptOutcome.Record.candidate)){throw 'candidate_found must close the current derived verifier ticket on exactly its bound candidate.'}
            }
            $expectedLifecycleKind = if ($initialPhase) { 'initial_ticket' } else { 'frozen_ticket' }
            if (-not (Test-ExactKeys -Object $Checkpoint.current_lifecycle -Required @('kind','id','path','sha256')) -or [string]$Checkpoint.current_lifecycle.kind -cne $expectedLifecycleKind -or
                [string]$Checkpoint.current_lifecycle.id -cne [string]$ticket.id -or [string]$Checkpoint.current_lifecycle.path -cne [string]$ticket.path -or [string]$Checkpoint.current_lifecycle.sha256 -cne [string]$ticket.sha256) { throw 'Checkpoint current lifecycle drifts from frozen ticket.' }
        }
        catch { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_ticket_content_invalid'; Detail=$_.Exception.Message } }
    }
    elseif ($null -ne $Checkpoint.current_lifecycle) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_checkpoint_lifecycle_drift' } }
    elseif ([string]$run.status -cnotin @('completion_candidate','goal_continuity_terminal','superseded','closed')) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_nonterminal_ticket_missing' } }
    elseif([string]$run.status-ceq'completion_candidate'-and$null-eq$auditedCompletionSummary){return [pscustomobject]@{Valid=$false;Reason='goal_host_state_unaudited_completion_ticket_missing'}}

    if($null-ne$ticket){
        $allowedTicketStatuses=switch([string]$run.status){
            {$_-cin@('not_started','preparing')} {@('frozen','ready');break}
            'attempt_running' {@('active');break}
            'audit_due' {@('frozen','ready');break}
            'auditing' {@('active');break}
            'completion_candidate' {@('frozen','ready','awaiting_verification');break}
            {$_-cin@('paused','awaiting_input')} {@('frozen','ready','active','awaiting_verification');break}
            default {@()}
        }
        if([string]$ticket.status-cnotin@($allowedTicketStatuses)){return [pscustomobject]@{Valid=$false;Reason='goal_host_state_ticket_status_incompatible'}}
        $ticketRole=[string]$ticketRecord.ticket.role
        if([string]$run.status-ceq'attempt_running'-and$ticketRole-cnotin@('solver','verifier')){return [pscustomobject]@{Valid=$false;Reason='goal_host_state_attempt_role_invalid'}}
        if([string]$run.status-ceq'auditing'-and$ticketRole-cnotin@('skeptic_quantifiers','skeptic_strategy','theory_tool_scout')){return [pscustomobject]@{Valid=$false;Reason='goal_host_state_audit_role_invalid'}}
        if([string]$projectEvent.event_type-ceq'ATTEMPT_START'-and$ticketRole-cne'solver'){return [pscustomobject]@{Valid=$false;Reason='goal_host_state_attempt_start_role_invalid'}}
        if([string]$projectEvent.event_type-ceq'AUDIT_START'-and$ticketRole-cnotin@('skeptic_quantifiers','skeptic_strategy','theory_tool_scout')){return [pscustomobject]@{Valid=$false;Reason='goal_host_state_audit_start_role_invalid'}}
    }

    $status = [string]$run.status
    $startupClass = $null
    $nextAction = $null
    if ([bool]$Checkpoint.completion_ready) {
        if ($status -cne 'closed' -or $null -ne $ticket -or $null -ne $Checkpoint.current_lifecycle -or [bool]$counters.audit_due) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_completion_ready_state_invalid' } }
        $startupClass='goal_host_completion_pending'
        $nextAction='read_only_completion_pending_wait_for_current_goal_control_decision'
    }
    else {
    switch ($status) {
        { $_ -cin @('not_started','preparing') } {
            if ([bool]$counters.audit_due) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_preparing_must_transition_to_audit_due' } }
            if ($null -eq $ticket -or [string]$ticket.status -cnotin @('frozen','ready')) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_initial_ticket_missing_or_not_frozen' } }
            $startupClass = 'goal_host_ready'
            $nextAction = 'verify_current_goal_then_begin_model_managed_attempt'
            break
        }
        'attempt_running' {
            if ($null -eq $ticket -or [string]$ticket.status -cne 'active') { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_attempt_running_inconsistent' } }
            $startupClass = 'goal_host_resume'
            $nextAction = 'verify_current_goal_then_resume_exact_model_managed_ticket'
            break
        }
        'audit_due' {
            if (-not [bool]$counters.audit_due -or $null -eq $ticket -or [string]$ticket.status -cnotin @('frozen','ready')) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_audit_due_inconsistent' } }
            $startupClass = 'goal_host_audit_due'
            $nextAction = 'verify_current_goal_then_run_due_audit'
            break
        }
        'auditing' {
            if ($null -eq $ticket -or [string]$ticket.status -cne 'active') { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_auditing_inconsistent' } }
            $startupClass = 'goal_host_audit_due'
            $nextAction = 'verify_current_goal_then_resume_exact_model_managed_audit'
            break
        }
        'completion_candidate' {
            if($null-ne$auditedCompletionSummary){
                if($null-ne$ticket-or$null-ne$Checkpoint.current_lifecycle-or[bool]$counters.audit_due){return [pscustomobject]@{Valid=$false;Reason='goal_host_state_audited_completion_inconsistent'}}
                $startupClass='goal_host_completion_ready_to_publish'
                $nextAction='verify_current_goal_then_publish_completion_ready_only'
            }
            else{
                if ($null -eq $ticket -or [string]$ticket.status -cnotin @('frozen','ready','awaiting_verification')) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_completion_candidate_inconsistent' } }
                $startupClass = 'goal_host_audit_due'
                $nextAction = 'verify_current_goal_then_run_completion_audits'
            }
            break
        }
        { $_ -cin @('awaiting_input','paused') } {
            if ($null -eq $ticket -or [string]$ticket.status -cnotin @('frozen','ready','active','awaiting_verification')) { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_paused_or_awaiting_ticket_missing' } }
            $startupClass = if($status-ceq'paused'-and$null-ne$pausedResumeCapsule-and[string]$pausedResumeCapsule.Capsule.prior_status-ceq'auditing'){'goal_host_audit_due'}else{'goal_host_resume'}
            $nextAction = if ($status -ceq 'awaiting_input') { 'verify_current_goal_then_review_awaiting_input' } elseif([string]$pausedResumeCapsule.Capsule.prior_status-ceq'auditing'){'verify_current_goal_then_resume_exact_model_managed_audit'}else{'verify_current_goal_then_resume_exact_model_managed_ticket'}
            break
        }
        { $_ -cin @('goal_continuity_terminal','superseded','closed') } {
            $startupClass = 'goal_host_closed_review'
            $nextAction = 'review_closed_goal_host_state_read_only'
            break
        }
        default { return [pscustomobject]@{ Valid=$false; Reason='goal_host_state_run_status_invalid' } }
    }
    }

    return [pscustomobject]@{
        Valid = $true
        Reason = $null
        StartupClass = $startupClass
        NextAction = $nextAction
        State = $state
        ContractEnvelope = $contractEnvelope
        ContractPath = [string]$contract.path
        RunPath = [string]$run.path
        TicketPath = if ($null -ne $ticket) { [string]$ticket.path } else { $null }
        CompletionReady = [bool]$Checkpoint.completion_ready
        Trust = 'strict_json_cross_checked_hash_bound_advisory_not_signature_or_goal_authorization'
    }
}

function Read-PreparingManifestAdvisory {
    param(
        [Parameter(Mandatory = $true)][string]$ManifestPath,
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Plan,
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Contract,
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Run,
        [Parameter(Mandatory = $true)][string]$RunPath
    )
    try { $envelope = Read-StrictJsonObject -LiteralPath $ManifestPath -Label 'legacy run manifest advisory' }
    catch { return [pscustomobject]@{ Valid=$false; Reason='manifest_advisory_not_strict_json' } }
    if ($envelope -isnot [Collections.IDictionary] -or
        -not $envelope.Contains('integrity_schema') -or [int]$envelope.integrity_schema -ne 1 -or
        -not $envelope.Contains('payload') -or $envelope.payload -isnot [Collections.IDictionary] -or
        -not $envelope.Contains('integrity') -or $envelope.integrity -isnot [Collections.IDictionary]) {
        return [pscustomobject]@{ Valid=$false; Reason='manifest_advisory_envelope_invalid' }
    }
    $payload = $envelope.payload
    $integrity = $envelope.integrity
    foreach ($key in @('algorithm','key_protection','payload_sha256','hmac_sha256')) {
        if (-not $integrity.Contains($key)) { return [pscustomobject]@{ Valid=$false; Reason='manifest_advisory_integrity_metadata_incomplete' } }
    }
    if ([string]$integrity.algorithm -cne 'HMAC-SHA256' -or [string]$integrity.key_protection -cne 'Windows-DPAPI-CurrentUser' -or
        [string]$integrity.payload_sha256 -cnotmatch '^[0-9a-f]{64}$' -or [string]$integrity.hmac_sha256 -cnotmatch '^[0-9a-f]{64}$') {
        return [pscustomobject]@{ Valid=$false; Reason='manifest_advisory_integrity_metadata_invalid' }
    }
    $payloadCanonical = $payload | ConvertTo-Json -Depth 64 -Compress
    if ((Get-TextSha256 -Text $payloadCanonical) -cne [string]$integrity.payload_sha256) { return [pscustomobject]@{ Valid=$false; Reason='manifest_advisory_payload_sha256_mismatch' } }

    foreach ($key in @('run_id','run_directory','contract_version','status','exit_reason','inputs','segments','updated_at_utc')) {
        if (-not $payload.Contains($key)) { return [pscustomobject]@{ Valid=$false; Reason='manifest_advisory_payload_incomplete' } }
    }
    if (-not (Test-CurrentUtcTimestamp -Value ([string]$payload.updated_at_utc))) { return [pscustomobject]@{ Valid=$false; Reason='manifest_advisory_timestamp_invalid_or_future' } }
    if (-not $payload.Contains('project') -or $payload.project -isnot [Collections.IDictionary] -or -not $payload.project.Contains('project_id')) { return [pscustomobject]@{ Valid=$false; Reason='manifest_advisory_project_pointer_missing' } }
    if ([string]$payload.project.project_id -cne [string]$Plan.ProjectId -or [string]$payload.run_id -cne [string]$Run.id -or [string]$payload.contract_version -cne [string]$Contract.version) {
        return [pscustomobject]@{ Valid=$false; Reason='manifest_advisory_identity_mismatch' }
    }
    try { $manifestRunPath = [IO.Path]::GetFullPath([string]$payload.run_directory) }
    catch { return [pscustomobject]@{ Valid=$false; Reason='manifest_advisory_run_pointer_invalid' } }
    if (-not $manifestRunPath.Equals([IO.Path]::GetFullPath($RunPath), [StringComparison]::OrdinalIgnoreCase)) { return [pscustomobject]@{ Valid=$false; Reason='manifest_advisory_run_pointer_mismatch' } }

    $inputs = $payload.inputs
    if ($inputs -isnot [Collections.IDictionary] -or -not $inputs.Contains('prompt') -or $inputs.prompt -isnot [Collections.IDictionary] -or -not $inputs.Contains('goal_objective') -or $inputs.goal_objective -isnot [Collections.IDictionary]) {
        return [pscustomobject]@{ Valid=$false; Reason='manifest_advisory_input_pointers_missing' }
    }
    $prompt = $inputs.prompt
    $goalInput = $inputs.goal_objective
    foreach ($key in @('file','sha256','contract_binding_sha256')) { if (-not $prompt.Contains($key)) { return [pscustomobject]@{ Valid=$false; Reason='manifest_advisory_prompt_pointer_incomplete' } } }
    foreach ($key in @('file','file_sha256')) { if (-not $goalInput.Contains($key)) { return [pscustomobject]@{ Valid=$false; Reason='manifest_advisory_goal_pointer_incomplete' } } }
    try {
        Assert-SafeLeafName -Value ([string]$prompt.file) -Label 'manifest prompt filename'
        Assert-SafeLeafName -Value ([string]$goalInput.file) -Label 'manifest Goal filename'
        Assert-LowerSha256 -Value ([string]$prompt.sha256) -Label 'manifest prompt hash'
        Assert-LowerSha256 -Value ([string]$prompt.contract_binding_sha256) -Label 'manifest contract binding'
        Assert-LowerSha256 -Value ([string]$goalInput.file_sha256) -Label 'manifest Goal hash'
    }
    catch { return [pscustomobject]@{ Valid=$false; Reason='manifest_advisory_input_pointer_invalid' } }
    if ([string]$prompt.file -ceq [string]$goalInput.file) { return [pscustomobject]@{ Valid=$false; Reason='manifest_advisory_input_pointer_collision' } }
    if ([string]$prompt.contract_binding_sha256 -cne [string]$Contract.sha256) { return [pscustomobject]@{ Valid=$false; Reason='manifest_advisory_contract_binding_mismatch' } }

    $segments = @($payload.segments)
    if ($segments.Count -lt 1) { return [pscustomobject]@{ Valid=$false; Reason='manifest_advisory_segments_invalid' } }
    for ($i = 0; $i -lt $segments.Count; $i++) {
        $segment = $segments[$i]
        if ($segment -isnot [Collections.IDictionary] -or -not $segment.Contains('index') -or -not $segment.Contains('kind') -or -not $segment.Contains('status') -or
            -not (Test-NonnegativeJsonInteger $segment.index) -or [decimal]$segment.index -ne $i -or [string]::IsNullOrWhiteSpace([string]$segment.kind) -or [string]::IsNullOrWhiteSpace([string]$segment.status)) {
            return [pscustomobject]@{ Valid=$false; Reason='manifest_advisory_segments_invalid' }
        }
    }
    $last = $segments[$segments.Count - 1]
    $lastSegmentStatus = [string]$last.status
    $exitReason = [string]$payload.exit_reason
    $marker = 'MATH_RESEARCH_GOAL_MISSING_OR_MISMATCHED'
    $segmentEvidence = $lastSegmentStatus -ceq 'goal_continuity_failed'
    $markerEvidence = $exitReason.Contains($marker)
    $hasLastMessageFile = $last.Contains('last_message_file') -and $null -ne $last.last_message_file
    $hasLastMessageHash = $last.Contains('last_message_sha256') -and $null -ne $last.last_message_sha256
    if ($hasLastMessageFile -xor $hasLastMessageHash) { return [pscustomobject]@{ Valid=$false; Reason='manifest_advisory_last_message_pointer_incomplete' } }
    if ($hasLastMessageFile) {
        try {
            Assert-SafeLeafName -Value ([string]$last.last_message_file) -Label 'last-message filename'
            Assert-LowerSha256 -Value ([string]$last.last_message_sha256) -Label 'last-message hash'
            $lastMessagePath = Join-Path $RunPath ([string]$last.last_message_file)
            if (-not (Test-Path -LiteralPath $lastMessagePath -PathType Leaf)) { throw 'Bound last-message file is missing.' }
            Assert-NoReparsePointChain -LiteralPath $lastMessagePath | Out-Null
            if ((Get-FileSha256 -LiteralPath $lastMessagePath) -cne [string]$last.last_message_sha256) { throw 'Bound last-message hash mismatches.' }
            $lastMessageText = [IO.File]::ReadAllText($lastMessagePath, [Text.UTF8Encoding]::new($false, $true)).Trim()
            if ($lastMessageText -ceq $marker) { $markerEvidence = $true }
        }
        catch { return [pscustomobject]@{ Valid=$false; Reason='manifest_advisory_last_message_binding_invalid' } }
    }
    foreach ($field in @('failure_code','failure_marker','terminal_marker')) {
        if ($payload.Contains($field) -and [string]$payload[$field] -ceq $marker) { $markerEvidence = $true }
        if ($last.Contains($field) -and [string]$last[$field] -ceq $marker) { $markerEvidence = $true }
    }
    $unverifiedGoalEvidence = $false
    if ($payload.Contains('goal') -and $payload.goal -is [Collections.IDictionary] -and $payload.goal.Contains('persistence_verified') -and $payload.goal.persistence_verified -is [bool] -and -not [bool]$payload.goal.persistence_verified) {
        $goalFailureStatus = $false
        foreach ($field in @('status','observed_status','continuity_status')) {
            if ($payload.goal.Contains($field) -and [string]$payload.goal[$field] -cin @('missing','mismatched','failed','none')) { $goalFailureStatus = $true }
        }
        $exactContinuityReason = $exitReason -ceq 'The in-thread Goal continuity gate reported a missing or mismatched Goal.'
        $unverifiedGoalEvidence = $goalFailureStatus -or $exactContinuityReason -or $segmentEvidence -or $markerEvidence
    }
    $terminalGoalContinuityFailure = [string]$payload.status -ceq 'failed' -and ($segmentEvidence -or $markerEvidence -or $unverifiedGoalEvidence)
    $terminalEvidence = @()
    if ($segmentEvidence) { $terminalEvidence += 'last_segment_goal_continuity_failed' }
    if ($markerEvidence) { $terminalEvidence += 'exact_goal_missing_or_mismatched_marker' }
    if ($unverifiedGoalEvidence) { $terminalEvidence += 'failed_child_goal_persistence_false_with_continuity_evidence' }

    return [pscustomobject]@{
        Valid = $true
        Reason = $null
        PromptFileName = [string]$prompt.file
        PromptRawSha256 = [string]$prompt.sha256
        GoalFileName = [string]$goalInput.file
        GoalRawSha256 = [string]$goalInput.file_sha256
        Status = [string]$payload.status
        ExitReason = $exitReason
        LastSegmentStatus = $lastSegmentStatus
        TerminalGoalContinuityFailure = $terminalGoalContinuityFailure
        TerminalEvidence = $terminalEvidence
        Trust = 'strict_datekind_string_payload_sha256_consistent_hmac_metadata_advisory_not_verified'
    }
}

function Read-PreparingManifestWithBackup {
    param(
        [Parameter(Mandatory = $true)][string]$RunPath,
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Plan,
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Contract,
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Run
    )
    $candidates = @('run.json','run.json.bak','run.json.backup')
    $firstFailure = $null
    $attempted = @()
    foreach ($name in $candidates) {
        $path = Join-Path $RunPath $name
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { continue }
        Assert-NoReparsePointChain -LiteralPath $path | Out-Null
        $attempted += $name
        $result = Read-PreparingManifestAdvisory -ManifestPath $path -Plan $Plan -Contract $Contract -Run $Run -RunPath $RunPath
        if ([bool]$result.Valid) {
            return [pscustomobject]@{ Valid=$true; Result=$result; FileName=$name; UsedBackup=($name -cne 'run.json'); Attempted=$attempted; FirstFailure=$firstFailure }
        }
        if ($null -eq $firstFailure) { $firstFailure = [string]$result.Reason }
    }
    return [pscustomobject]@{ Valid=$false; Result=$null; FileName=$null; UsedBackup=$false; Attempted=$attempted; FirstFailure=if($null -ne $firstFailure){$firstFailure}else{'manifest_advisory_missing'} }
}

function Test-ProjectPreparingState {
    param([Collections.IDictionary]$Plan, [string]$ProjectPath)
    $contract = $Plan.ActiveContract
    $run = $Plan.ActiveRun
    if ($contract -isnot [Collections.IDictionary] -or $run -isnot [Collections.IDictionary] -or -not [bool]$Plan.Dirty -or [string]$contract.status -cne 'confirmed' -or [string]$run.status -cne 'preparing') {
        return [pscustomobject]@{ Match=$false; Reason='checkpoint_not_registered_preparing' }
    }
    try {
        Assert-LowerSha256 -Value ([string]$contract.sha256) -Label 'active contract hash'
        $contractPath = Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ([string]$contract.path) -RequiredRoot 'contracts' -PathType Leaf
        if ((Get-NormalizedTextSha256 -LiteralPath $contractPath) -cne [string]$contract.sha256) { throw 'Contract bytes mismatch.' }
        Assert-SafeLeafName -Value ([string]$run.id) -Label 'active run ID'
        $runPath = Resolve-ProjectRelativePath -ProjectPath $ProjectPath -RelativePath ([string]$run.path) -RequiredRoot 'runs' -PathType Container
        if ((Split-Path -Parent $runPath) -cne [IO.Path]::GetFullPath((Join-Path $ProjectPath 'runs')) -or (Split-Path -Leaf $runPath) -cne [string]$run.id) { throw 'Run path is not the bound direct child.' }
    }
    catch { return [pscustomobject]@{ Match=$false; Reason='preparing_project_binding_invalid'; Detail=$_.Exception.Message } }

    $manifestChoice = Read-PreparingManifestWithBackup -RunPath $runPath -Plan $Plan -Contract $contract -Run $run
    if (-not [bool]$manifestChoice.Valid) { return [pscustomobject]@{ Match=$false; Reason=[string]$manifestChoice.FirstFailure } }
    $manifest = $manifestChoice.Result
    $promptPath = Join-Path $runPath ([string]$manifest.PromptFileName)
    $goalPath = Join-Path $runPath ([string]$manifest.GoalFileName)
    foreach ($path in @($promptPath,$goalPath)) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return [pscustomobject]@{ Match=$false; Reason='preparing_input_missing' } }
        Assert-NoReparsePointChain -LiteralPath $path | Out-Null
    }
    if ((Get-FileSha256 -LiteralPath $promptPath) -cne [string]$manifest.PromptRawSha256 -or
        (Get-NormalizedTextSha256 -LiteralPath $promptPath) -cne [string]$contract.sha256 -or
        (Get-FileSha256 -LiteralPath $goalPath) -cne [string]$manifest.GoalRawSha256) {
        return [pscustomobject]@{ Match=$false; Reason='preparing_input_hash_mismatch' }
    }
    return [pscustomobject]@{
        Match=$true
        Reason=$null
        Phase=if([bool]$manifest.TerminalGoalContinuityFailure){'legacy_manifest_terminal_goal_continuity_failure'}else{'legacy_manifest_present_no_execution_authority'}
        TerminalGoalContinuityFailure=[bool]$manifest.TerminalGoalContinuityFailure
        TerminalEvidence=@($manifest.TerminalEvidence)
        ManifestStatus=[string]$manifest.Status
        ManifestExitReason=[string]$manifest.ExitReason
        ManifestLastSegmentStatus=[string]$manifest.LastSegmentStatus
        ManifestTrust=[string]$manifest.Trust
        ManifestPath=('runs\' + [string]$run.id + '\' + [string]$manifestChoice.FileName)
        ManifestUsedBackup=[bool]$manifestChoice.UsedBackup
    }
}

$clock = [Diagnostics.Stopwatch]::StartNew()
$controllerCalls = 0
$controllerAction = $null
$plan = $null
$projectHint = $null
$checkpointHint = $null
$projectPath = $null
$startupClass = $null
$nextAction = $null
$recoveryReason = $null
$preparingPhase = $null
$terminalNoResume = $false
$terminalEvidence = @()
$manifestAdvisoryStatus = $null
$manifestAdvisoryExitReason = $null
$manifestAdvisoryLastSegmentStatus = $null
$manifestAdvisoryTrust = $null
$manifestAdvisoryUsedBackup = $false
$goalHostStateTrust = $null
$legacySuccessorAdvisoryValid = $false
$legacySuccessorAdvisoryPath = $null
$legacyArchiveDetected = $false
$unconvertedLegacyArchiveDetected = $false
$durableCompletionReady = $false
$validGoalHostV8 = $false
$requiresCurrentGoalControlCheck = $false
$minimalRead = @()
$normalizedGoalStatus = if ($GoalStatus -ceq 'cancelled') { 'none' } else { $GoalStatus }

if ($PSCmdlet.ParameterSetName -eq 'Slot') {
    if ([string]::IsNullOrWhiteSpace($ProjectDirectoryName) -or $ProjectDirectoryName -match '[<>:"/\\|?*]' -or $ProjectDirectoryName.EndsWith('.') -or $ProjectDirectoryName.EndsWith(' ')) { throw 'Unsafe ProjectDirectoryName.' }
    $vault = Assert-NoReparsePointChain -LiteralPath $VaultRoot
    if (-not (Test-Path -LiteralPath $vault -PathType Container)) { throw 'VaultRoot is not an existing directory.' }
    $projectsRoot = Assert-NoReparsePointChain -LiteralPath (Join-Path $vault '笔记草稿\公开问题的尝试')
    if (-not (Test-Path -LiteralPath $projectsRoot -PathType Container)) { throw 'The canonical math-research projects root is missing.' }
    $slot = [IO.Path]::GetFullPath((Join-Path $projectsRoot $ProjectDirectoryName))
    if (-not (Split-Path -Parent $slot).Equals([IO.Path]::GetFullPath($projectsRoot), [StringComparison]::OrdinalIgnoreCase)) { throw 'Project slot is not one direct child of the canonical projects root.' }
    if (-not (Test-Path -LiteralPath $slot)) {
        Assert-NoReparsePointChain -LiteralPath $slot -AllowMissingLeaf | Out-Null
        $startupClass = 'fresh_project_slot'
        $nextAction = 'model_may_initialize_only_after_active_goal_check'
        $projectPath = $slot
        $requiresCurrentGoalControlCheck = $true
    }
    elseif (-not (Test-Path -LiteralPath (Join-Path $slot 'project.json') -PathType Leaf)) {
        Assert-NoReparsePointChain -LiteralPath $slot | Out-Null
        $startupClass = 'partial_project_tree_recovery'
        $nextAction = 'inspect_partial_tree_read_only'
        $projectPath = $slot
        $recoveryReason = 'existing_slot_missing_project_json'
    }
    else { $projectPath = Assert-NoReparsePointChain -LiteralPath $slot }
}
else {
    $projectPath = Assert-NoReparsePointChain -LiteralPath $ProjectDirectory
    if (-not (Test-Path -LiteralPath $projectPath -PathType Container)) { throw 'Existing-mode ProjectDirectory is missing; use Slot mode only for a not-yet-created project.' }
}

if ($null -eq $startupClass) {
    $projectJsonHintPath = Join-Path $projectPath 'project.json'
    $stateHintPath = Join-Path $projectPath 'state'
    foreach ($hintPath in @($projectJsonHintPath,$stateHintPath)) { Assert-NoReparsePointChain -LiteralPath $hintPath | Out-Null }
    $projectHint = Read-StrictJsonObject -LiteralPath $projectJsonHintPath -Label 'project.json startup hint'
    $projectHintSha256 = Get-FileSha256 -LiteralPath $projectJsonHintPath
    $isV8Project = $projectHint.Contains('schema') -and [string]$projectHint.schema -ceq 'math-research-project/v8'
    $hasCheckpointHead = $projectHint.Contains('active_checkpoint')
    $hasGoalHostHead = $projectHint.Contains('goal_host_state')

    if (-not $isV8Project -and ($hasCheckpointHead -or $hasGoalHostHead)) {
        $legacyArchiveDetected = $true
        $unconvertedLegacyArchiveDetected = $true
        $startupClass = 'legacy_execution_unsupported'
        $nextAction = 'fail_closed_read_only_diagnosis'
        $recoveryReason = 'legacy_schema_cannot_activate_v8_generation_pointers'
        $minimalRead = @('project.json')
    }
    elseif ($isV8Project -and ($hasCheckpointHead -xor $hasGoalHostHead)) {
        $startupClass = 'goal_host_state_invalid'
        $nextAction = 'fail_closed_read_only_diagnosis'
        $recoveryReason = 'goal_host_state_pointer_pair_incomplete'
        $minimalRead = @('project.json')
    }
    elseif ($isV8Project -and $hasCheckpointHead -and $hasGoalHostHead) {
        try {
            $projectHeadKeys = @('schema','project_id','project_identity_sha256','problem_statement_sha256','control_generation','active_checkpoint','goal_host_state','project_event_head','host_binding_head','active_contract','active_run','legacy_successor')
            if (-not (Test-ExactKeys -Object $projectHint -Required $projectHeadKeys)) { throw 'Project v8 head has a missing or unknown authority field.' }
            if ([string]::IsNullOrWhiteSpace([string]$projectHint.project_id) -or -not (Test-NonnegativeJsonInteger $projectHint.control_generation) -or [decimal]$projectHint.control_generation -lt 1) { throw 'Project v8 head identity/generation is invalid.' }
            Assert-LowerSha256 -Value ([string]$projectHint.project_identity_sha256) -Label 'project identity hash'
            Assert-LowerSha256 -Value ([string]$projectHint.problem_statement_sha256) -Label 'project problem-statement hash'
            foreach ($pointerName in @('active_checkpoint','goal_host_state')) {
                $pointer = $projectHint[$pointerName]
                if (-not (Test-ExactKeys -Object $pointer -Required @('path','sha256','control_generation'))) { throw "$pointerName pointer shape is invalid." }
                Assert-LowerSha256 -Value ([string]$pointer.sha256) -Label "$pointerName pointer hash"
                if (-not (Test-NonnegativeJsonInteger $pointer.control_generation) -or [string]$pointer.control_generation -cne [string]$projectHint.control_generation) { throw "$pointerName generation mismatches project head." }
            }
            $checkpointPointerPattern = '^state[\\/]generations[\\/]g(?<generation>[0-9]{4,})[\\/]checkpoint\.json$'
            $statePointerPattern = '^state[\\/]generations[\\/]g(?<generation>[0-9]{4,})[\\/]goal-host-v8\.json$'
            if ([string]$projectHint.active_checkpoint.path -cnotmatch $checkpointPointerPattern) { throw 'Checkpoint pointer is not one immutable generation path.' }
            $checkpointPathGeneration = [int64]$Matches['generation']
            if ([string]$projectHint.goal_host_state.path -cnotmatch $statePointerPattern) { throw 'Goal-host pointer is not one immutable generation path.' }
            $statePathGeneration = [int64]$Matches['generation']
            if ($checkpointPathGeneration -lt 1 -or $statePathGeneration -lt 1 -or $checkpointPathGeneration -ne [int64]$projectHint.control_generation -or $statePathGeneration -ne [int64]$projectHint.control_generation) { throw 'Pointer directory generation mismatches project control_generation.' }
            $checkpointHintPath = Resolve-ProjectRelativePath -ProjectPath $projectPath -RelativePath ([string]$projectHint.active_checkpoint.path) -RequiredRoot 'state' -PathType Leaf
            $goalHostStatePath = Resolve-ProjectRelativePath -ProjectPath $projectPath -RelativePath ([string]$projectHint.goal_host_state.path) -RequiredRoot 'state' -PathType Leaf
            if ($checkpointHintPath.Equals($goalHostStatePath, [StringComparison]::OrdinalIgnoreCase)) { throw 'Checkpoint and Goal-host state pointers collide.' }
            if ((Get-FileSha256 -LiteralPath $checkpointHintPath) -cne [string]$projectHint.active_checkpoint.sha256 -or (Get-FileSha256 -LiteralPath $goalHostStatePath) -cne [string]$projectHint.goal_host_state.sha256) { throw 'A v8 project-head pointer hash mismatches.' }
            $checkpointHint = Read-StrictJsonObject -LiteralPath $checkpointHintPath -Label 'generation-bound checkpoint startup hint'
            $checkpointHintSha256 = Get-FileSha256 -LiteralPath $checkpointHintPath
        }
        catch {
            $startupClass = 'goal_host_state_invalid'
            $nextAction = 'fail_closed_read_only_diagnosis'
            $recoveryReason = 'goal_host_state_pointer_invalid'
            $minimalRead = @('project.json')
        }
        if ($null -eq $startupClass) {
            if (-not $checkpointHint.Contains('project_id') -or [string]$checkpointHint.project_id -cne [string]$projectHint.project_id) {
                $startupClass = 'project_identity_invalid'
                $nextAction = 'fail_closed_read_only_diagnosis'
                $recoveryReason = 'project_checkpoint_identity_mismatch'
            }
            else {
                $goalHostAdvisory = Read-GoalHostV8Advisory -StatePath $goalHostStatePath -ProjectPath $projectPath -Project $projectHint -Checkpoint $checkpointHint
                if ((Get-FileSha256 -LiteralPath $projectJsonHintPath) -cne $projectHintSha256 -or (Get-FileSha256 -LiteralPath $checkpointHintPath) -cne $checkpointHintSha256 -or
                    (Get-FileSha256 -LiteralPath $goalHostStatePath) -cne [string]$projectHint.goal_host_state.sha256) { throw 'Project v8 head files changed during read-only startup verification.' }
                if (-not [bool]$goalHostAdvisory.Valid) {
                    $startupClass = 'goal_host_state_invalid'
                    $nextAction = 'fail_closed_read_only_diagnosis'
                    $recoveryReason = [string]$goalHostAdvisory.Reason
                }
                else {
                    $state = $goalHostAdvisory.State
                    $hasLegacySuccessor = $projectHint.Contains('legacy_successor') -and $null -ne $projectHint.legacy_successor
                    $lineage = if ($hasLegacySuccessor) { Read-LegacySuccessorAdvisory -ProjectPath $projectPath -Project $projectHint -State $state -ContractEnvelope $goalHostAdvisory.ContractEnvelope } else { [pscustomobject]@{Valid=$true;Path=$null} }
                    if (-not [bool]$lineage.Valid) {
                        $startupClass = 'goal_host_state_invalid'
                        $nextAction = 'fail_closed_read_only_diagnosis'
                        $recoveryReason = 'legacy_successor_lineage_invalid'
                    }
                    else {
                        $legacySuccessorAdvisoryValid = $hasLegacySuccessor
                        if ($hasLegacySuccessor) { $legacyArchiveDetected = $true }
                        $legacySuccessorAdvisoryPath = [string]$lineage.Path
                        $startupClass = [string]$goalHostAdvisory.StartupClass
                        $nextAction = [string]$goalHostAdvisory.NextAction
                        $goalHostStateTrust = [string]$goalHostAdvisory.Trust
                        $durableCompletionReady = [bool]$goalHostAdvisory.CompletionReady
                        $validGoalHostV8 = $true
                        $requiresCurrentGoalControlCheck = $true
                        $plan = [ordered]@{ ProjectId=[string]$state.project_id; Action='goal_host_v8_advisory'; ActiveContract=$state.contract; ActiveRun=$state.run; ActiveTicket=if($state.Contains('current_ticket')){$state.current_ticket}else{$null} }
                    }
                }
                $advisoryContractRead = if ($goalHostAdvisory.PSObject.Properties.Name -contains 'ContractPath') { [string]$goalHostAdvisory.ContractPath } else { $null }
                $advisoryTicketRead = if ($goalHostAdvisory.PSObject.Properties.Name -contains 'TicketPath') { [string]$goalHostAdvisory.TicketPath } else { $null }
                $minimalRead = @('project.json',[string]$projectHint.active_checkpoint.path,[string]$projectHint.goal_host_state.path,$legacySuccessorAdvisoryPath,$advisoryContractRead,$advisoryTicketRead)
            }
        }
    }
    elseif ($isV8Project) {
        $startupClass = 'goal_host_state_invalid'
        $nextAction = 'fail_closed_read_only_diagnosis'
        $recoveryReason = 'goal_host_state_pointer_pair_missing'
        $minimalRead = @('project.json')
    }
    else {
        $checkpointHintPath = Join-Path $stateHintPath 'checkpoint.json'
        Assert-NoReparsePointChain -LiteralPath $checkpointHintPath | Out-Null
        $checkpointHint = Read-StrictJsonObject -LiteralPath $checkpointHintPath -Label 'legacy checkpoint startup hint'
        $checkpointHintSha256 = Get-FileSha256 -LiteralPath $checkpointHintPath
        if (Test-Path -LiteralPath (Join-Path $stateHintPath 'goal-host-v8.json') -PathType Leaf) {
            $startupClass = 'goal_host_state_invalid'
            $nextAction = 'fail_closed_read_only_diagnosis'
            $recoveryReason = 'goal_host_state_requires_project_head_pointers'
            $minimalRead = @('project.json','state/checkpoint.json','state/goal-host-v8.json')
        }
        elseif (-not $projectHint.Contains('project_id') -or [string]::IsNullOrWhiteSpace([string]$projectHint.project_id) -or -not $checkpointHint.Contains('project_id') -or [string]$checkpointHint.project_id -cne [string]$projectHint.project_id) {
            $startupClass = 'project_identity_invalid'
            $nextAction = 'fail_closed_read_only_diagnosis'
            $recoveryReason = 'project_checkpoint_identity_mismatch'
        }
        else {
        $legacyRunPointer = if ($checkpointHint.Contains('run')) { $checkpointHint.run } elseif ($projectHint.Contains('active_run')) { $projectHint.active_run } else { $null }
        if ($legacyRunPointer -is [Collections.IDictionary] -and $legacyRunPointer.Contains('id') -and -not [string]::IsNullOrWhiteSpace([string]$legacyRunPointer.id)) { $legacyArchiveDetected = $true; $unconvertedLegacyArchiveDetected = $true }
        $legacyContractPointer = if ($checkpointHint.Contains('contract')) { $checkpointHint.contract } elseif ($projectHint.Contains('active_contract')) { $projectHint.active_contract } else { $null }
        $legacyTicketPointer = if ($checkpointHint.Contains('active_ticket')) { $checkpointHint.active_ticket } else { $null }
        $plan = [ordered]@{
            ProjectId=[string]$projectHint.project_id;Action='legacy_read_only_classification'
            Dirty=($checkpointHint.Contains('dirty') -and [bool]$checkpointHint.dirty)
            ActiveContract=$legacyContractPointer;ActiveRun=$legacyRunPointer;ActiveTicket=$legacyTicketPointer
        }
        $minimalRead = @('project.json','state/checkpoint.json')
        $preparing = if ($legacyContractPointer -is [Collections.IDictionary] -and $legacyRunPointer -is [Collections.IDictionary] -and
            [string]$legacyContractPointer.status -ceq 'confirmed' -and [string]$legacyRunPointer.status -ceq 'preparing') {
            Test-ProjectPreparingState -Plan $plan -ProjectPath $projectPath
        } else { [pscustomobject]@{Match=$false;Reason='legacy_state_has_no_supported_execution_route'} }
        if ([bool]$preparing.Match) {
            $preparingPhase = [string]$preparing.Phase
            $manifestAdvisoryStatus = [string]$preparing.ManifestStatus
            $manifestAdvisoryExitReason = [string]$preparing.ManifestExitReason
            $manifestAdvisoryLastSegmentStatus = [string]$preparing.ManifestLastSegmentStatus
            $manifestAdvisoryTrust = [string]$preparing.ManifestTrust
            $manifestAdvisoryUsedBackup = [bool]$preparing.ManifestUsedBackup
            $terminalEvidence = @($preparing.TerminalEvidence)
            $minimalRead += [string]$preparing.ManifestPath
            if ([bool]$preparing.TerminalGoalContinuityFailure) {
                $startupClass = 'goal_continuity_terminal'
                $nextAction = 'stop_no_retry_preserve_run'
                $recoveryReason = 'goal_continuity_missing_or_mismatched_terminal'
                $terminalNoResume = $true
            }
            else {
                $startupClass = 'legacy_execution_unsupported'
                $nextAction = 'fail_closed_read_only_diagnosis'
                $recoveryReason = 'no_production_legacy_execution_route_for_nonterminal_manifest'
            }
        }
        else {
            $startupClass = 'legacy_execution_unsupported'
            $nextAction = 'fail_closed_read_only_diagnosis'
            $recoveryReason = 'no_production_legacy_execution_route__' + [string]$preparing.Reason
        }
        }
    }
}

# GoalStatus is advisory input only. Durable completion changes only the
# returned read-only/control-plane plan; it never authorizes project mutation.
if($durableCompletionReady){
    if($normalizedGoalStatus-ceq'complete'){$startupClass='goal_host_closed_review';$nextAction='review_durable_completed_goal_read_only';$requiresCurrentGoalControlCheck=$false}
    elseif($normalizedGoalStatus-ceq'active'){$startupClass='goal_host_completion_pending';$nextAction='fresh_get_goal_then_update_goal_complete_no_project_write';$requiresCurrentGoalControlCheck=$true}
    else{$startupClass='goal_host_completion_pending';$nextAction='read_only_completion_pending_goal_not_active';$requiresCurrentGoalControlCheck=$false}
}
elseif($validGoalHostV8-and$normalizedGoalStatus-ceq'complete'){
    $startupClass='goal_host_state_invalid';$nextAction='fail_closed_read_only_diagnosis';$recoveryReason='goal_complete_without_durable_completion_ready';$requiresCurrentGoalControlCheck=$false
}
$goalGate = 'current_goal_control_check_required_before_any_mutation'
if ($durableCompletionReady -and $normalizedGoalStatus -ceq 'complete') { $goalGate='durable_completion_closed_read_only' }
elseif ($durableCompletionReady -and $normalizedGoalStatus -cne 'active') { $goalGate='completion_pending_read_only_goal_not_active' }
elseif ($terminalNoResume) { $goalGate = 'terminal_no_research_or_resume' }
elseif ($normalizedGoalStatus -ceq 'none') { $goalGate = 'research_forbidden_no_current_goal' }
elseif ($normalizedGoalStatus -cne 'active') { $goalGate = "research_forbidden_goal_$normalizedGoalStatus" }

$clock.Stop()
[ordered]@{
    schema = 'math-research-startup-plan/v3'
    ok = $true
    classifier_mode = 'strict_read_only_no_launch_resume_or_goal_control'
    startup_class = $startupClass
    next_action = $nextAction
    recovery_reason = $recoveryReason
    preparing_phase = $preparingPhase
    terminal_no_resume = $terminalNoResume
    legacy_archive_detected = $legacyArchiveDetected
    legacy_lineage_preserved = $legacySuccessorAdvisoryValid
    legacy_goal_bindings_obsolete = ($terminalNoResume -or $legacyArchiveDetected)
    successor_v8_requires_explicit_new_active_goal = ($terminalNoResume -or $unconvertedLegacyArchiveDetected)
    legacy_run_preservation_required = ($terminalNoResume -or $legacyArchiveDetected)
    terminal_evidence = @($terminalEvidence)
    manifest_advisory_status = $manifestAdvisoryStatus
    manifest_advisory_exit_reason = $manifestAdvisoryExitReason
    manifest_advisory_last_segment_status = $manifestAdvisoryLastSegmentStatus
    manifest_advisory_trust = $manifestAdvisoryTrust
    manifest_advisory_used_backup = $manifestAdvisoryUsedBackup
    goal_host_state_trust = $goalHostStateTrust
    legacy_successor_advisory_valid = $legacySuccessorAdvisoryValid
    legacy_successor_advisory_path = $legacySuccessorAdvisoryPath
    project_id = if ($null -ne $plan -and $plan.Contains('ProjectId')) { [string]$plan.ProjectId } elseif ($null -ne $projectHint -and $projectHint.Contains('project_id')) { [string]$projectHint.project_id } else { $null }
    project_directory = $projectPath
    goal_status_supplied = $GoalStatus
    goal_status_normalized = $normalizedGoalStatus
    goal_status_evidence = 'caller_supplied_advisory_never_control_plane_proof'
    goal_gate = $goalGate
    requires_current_goal_control_check = $requiresCurrentGoalControlCheck
    controller_action = $controllerAction
    controller_call_count = $controllerCalls
    authoritative_resume_action = if ($null -ne $plan -and $plan.Contains('Action')) { [string]$plan.Action } else { $null }
    active_contract = if ($null -ne $plan -and $plan.Contains('ActiveContract')) { $plan.ActiveContract } else { $null }
    active_run = if ($null -ne $plan -and $plan.Contains('ActiveRun')) { $plan.ActiveRun } else { $null }
    minimal_model_read = @($minimalRead | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) } | Select-Object -Unique)
    contract_hash_role = 'ordinary_integrity_binding_not_signature_or_authorization'
    measured_router_elapsed_ms = [Math]::Round($clock.Elapsed.TotalMilliseconds, 3)
} | ConvertTo-Json -Depth 64
