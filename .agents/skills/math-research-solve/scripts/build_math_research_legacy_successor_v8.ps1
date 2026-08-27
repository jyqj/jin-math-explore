[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ProjectDirectory,
    [Parameter(Mandatory = $true)][AllowEmptyString()][string]$GoalObjectiveRaw,
    [Parameter(Mandatory = $true)][string]$GoalObjectiveSha256,
    [AllowNull()][string]$GoalThreadId = $null,
    [AllowNull()][string]$OutputDirectory = $null,
    [switch]$DryRun
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)

$result = [ordered]@{
    schema = 'math-research-legacy-successor-build-result/v8'
    built = $false
    dry_run = [bool]$DryRun
    reason = 'unclassified_failure'
    detail = $null
    source_project = $null
    target_project = $null
    source_project_tree_sha256_before = $null
    source_project_tree_sha256_after = $null
    expected_old_sha256 = $null
    expected_old_control_generation = $null
    expected_new_control_generation = $null
    candidate_head_file = $null
    candidate_head_sha256 = $null
    effective_envelope = $null
    migration_map = $null
    inherited_artifact_count = $null
    trust = 'staging_only_strict_self_consistency_no_hmac_authenticity_not_goal_authorization'
}
$script:createdFiles = 0
$script:reusedFiles = 0

function Stop-Build {
    param([Parameter(Mandatory = $true)][string]$Code,[Parameter(Mandatory = $true)][string]$Message)
    throw "[$Code] $Message"
}

function Get-BytesSha256([byte[]]$Bytes) {
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes)).ToLowerInvariant()
}
function Get-TextSha256([string]$Text) { return Get-BytesSha256 ([Text.UTF8Encoding]::new($false).GetBytes($Text)) }
function Get-FileSha256([string]$LiteralPath) { return (Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256).Hash.ToLowerInvariant() }
function Get-NormalizedTextSha256([string]$LiteralPath) {
    $text = [IO.File]::ReadAllText($LiteralPath,[Text.UTF8Encoding]::new($false,$true)) -replace "`r`n","`n"
    if ($text.Contains("`r")) { Stop-Build 'text_invalid' "Text contains an isolated CR: $LiteralPath" }
    return Get-TextSha256 $text
}
function Assert-LowerSha256($Value,[string]$Label) {
    if ($Value -isnot [string] -or [string]$Value -cnotmatch '^[0-9a-f]{64}$') { Stop-Build 'hash_invalid' "$Label must be one lowercase SHA-256 value." }
}
function Assert-SafeId($Value,[string]$Label) {
    if ($Value -isnot [string] -or [string]$Value -cnotmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$') { Stop-Build 'identity_invalid' "$Label is not a safe identifier." }
}
function Test-JsonInteger($Value,[long]$Minimum=0) {
    if ($null -eq $Value -or $Value.GetType().Name -cnotin @('Byte','SByte','Int16','UInt16','Int32','UInt32','Int64','UInt64')) { return $false }
    try { return [decimal]$Value -ge $Minimum } catch { return $false }
}
function Assert-ExactKeys($Object,[string[]]$Keys,[string]$Label) {
    if ($Object -isnot [Collections.IDictionary]) { Stop-Build 'shape_invalid' "$Label must be an object." }
    if (@($Object.Keys).Count -ne $Keys.Count) { Stop-Build 'shape_invalid' "$Label has an unexpected property count." }
    foreach ($key in $Keys) { if (-not $Object.Contains($key)) { Stop-Build 'shape_invalid' "$Label is missing '$key'." } }
}
function Assert-UniqueJsonProperties([Text.Json.JsonElement]$Element,[string]$Path) {
    if ($Element.ValueKind -eq [Text.Json.JsonValueKind]::Object) {
        $seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        foreach($property in $Element.EnumerateObject()) {
            if(-not $seen.Add($property.Name)){Stop-Build 'strict_json_invalid' "Duplicate JSON property '$($property.Name)' at $Path."}
            Assert-UniqueJsonProperties $property.Value "$Path.$($property.Name)"
        }
    } elseif($Element.ValueKind -eq [Text.Json.JsonValueKind]::Array) {
        $i=0; foreach($item in $Element.EnumerateArray()){Assert-UniqueJsonProperties $item "$Path[$i]";$i++}
    }
}
function Read-StrictJson([string]$LiteralPath,[string]$Label) {
    if(-not(Test-Path -LiteralPath $LiteralPath -PathType Leaf)){Stop-Build 'source_missing' "$Label is missing: $LiteralPath"}
    $bytes=[IO.File]::ReadAllBytes($LiteralPath)
    try{$text=[Text.UTF8Encoding]::new($false,$true).GetString($bytes)}catch{Stop-Build 'strict_json_invalid' "$Label is not valid UTF-8."}
    $options=[Text.Json.JsonDocumentOptions]::new();$options.AllowTrailingCommas=$false;$options.CommentHandling=[Text.Json.JsonCommentHandling]::Disallow;$options.MaxDepth=100
    try{$document=[Text.Json.JsonDocument]::Parse($text,$options)}catch{Stop-Build 'strict_json_invalid' "$Label is not strict JSON: $($_.Exception.Message)"}
    try{if($document.RootElement.ValueKind-ne[Text.Json.JsonValueKind]::Object){Stop-Build 'strict_json_invalid' "$Label must be a JSON object."};Assert-UniqueJsonProperties $document.RootElement '$'}finally{$document.Dispose()}
    try{return ($text|ConvertFrom-Json -AsHashtable -Depth 100 -DateKind String)}catch{Stop-Build 'strict_json_invalid' "$Label cannot be converted without coercion."}
}
function ConvertTo-CanonicalJson($Value) { return (($Value|ConvertTo-Json -Depth 100 -Compress)+"`n") }
function Write-OrVerifyBytes([string]$LiteralPath,[byte[]]$ExpectedBytes) {
    $tempPath=$LiteralPath+'.build-v8.tmp'
    if(Test-Path -LiteralPath $LiteralPath){
        if(-not(Test-Path -LiteralPath $LiteralPath -PathType Leaf)){Stop-Build 'staging_artifact_mismatch' "Expected staging file is not a regular file: $LiteralPath"}
        Assert-NoReparsePointChain $LiteralPath
        $actual=[IO.File]::ReadAllBytes($LiteralPath)
        if($actual.Length-ne$ExpectedBytes.Length-or(Get-BytesSha256 $actual)-cne(Get-BytesSha256 $ExpectedBytes)){Stop-Build 'staging_artifact_mismatch' "Existing staged artifact bytes differ from deterministic build output: $LiteralPath"}
        if(Test-Path -LiteralPath $tempPath){if(-not(Test-Path -LiteralPath $tempPath -PathType Leaf)){Stop-Build 'staging_temp_invalid' "Deterministic staging temp is not a regular file: $tempPath"};Assert-NoReparsePointChain $tempPath;Remove-Item -LiteralPath $tempPath -Force}
        $script:reusedFiles++
        return
    }
    $parent=Split-Path -Parent $LiteralPath
    if(-not(Test-Path -LiteralPath $parent)){New-Item -ItemType Directory -Path $parent -Force|Out-Null}
    Assert-NoReparsePointChain $parent
    if(Test-Path -LiteralPath $tempPath){
        if(-not(Test-Path -LiteralPath $tempPath -PathType Leaf)){Stop-Build 'staging_temp_invalid' "Deterministic staging temp is not a regular file: $tempPath"}
        Assert-NoReparsePointChain $tempPath
        Remove-Item -LiteralPath $tempPath -Force
    }
    try{
        $stream=[IO.FileStream]::new($tempPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
        try{$stream.Write($ExpectedBytes,0,$ExpectedBytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
        if((Get-FileSha256 $tempPath)-cne(Get-BytesSha256 $ExpectedBytes)){Stop-Build 'staging_temp_invalid' "Flushed staging temp bytes differ from expected output: $tempPath"}
        [IO.File]::Move($tempPath,$LiteralPath,$false)
    }
    catch{
        if(Test-Path -LiteralPath $LiteralPath -PathType Leaf){
            $actual=[IO.File]::ReadAllBytes($LiteralPath)
            if($actual.Length-ne$ExpectedBytes.Length-or(Get-BytesSha256 $actual)-cne(Get-BytesSha256 $ExpectedBytes)){Stop-Build 'staging_artifact_mismatch' "Concurrent final staged artifact differs from deterministic build output: $LiteralPath"}
            if(Test-Path -LiteralPath $tempPath -PathType Leaf){Remove-Item -LiteralPath $tempPath -Force}
            $script:reusedFiles++
            return
        }
        throw
    }
    if(-not(Test-Path -LiteralPath $LiteralPath -PathType Leaf)-or(Get-FileSha256 $LiteralPath)-cne(Get-BytesSha256 $ExpectedBytes)){Stop-Build 'staging_publish_failed' "Atomic no-overwrite publish did not produce the exact final bytes: $LiteralPath"}
    $script:createdFiles++
}
function Write-Utf8([string]$LiteralPath,[string]$Text) {
    Write-OrVerifyBytes $LiteralPath ([Text.UTF8Encoding]::new($false).GetBytes($Text))
}
function Write-CanonicalJson([string]$LiteralPath,$Value) { Write-Utf8 $LiteralPath (ConvertTo-CanonicalJson $Value) }
function Test-PathInside([string]$Child,[string]$Directory) {
    $childFull=[IO.Path]::GetFullPath($Child)
    $directoryFull=[IO.Path]::GetFullPath($Directory).TrimEnd([IO.Path]::DirectorySeparatorChar,[IO.Path]::AltDirectorySeparatorChar)+[IO.Path]::DirectorySeparatorChar
    return $childFull.StartsWith($directoryFull,[StringComparison]::OrdinalIgnoreCase)
}
function Assert-NoReparsePointChain([string]$LiteralPath) {
    $cursor=[IO.Path]::GetFullPath($LiteralPath)
    while(-not[string]::IsNullOrWhiteSpace($cursor)-and(Test-Path -LiteralPath $cursor)){
        $item=Get-Item -LiteralPath $cursor -Force
        if(($item.Attributes-band[IO.FileAttributes]::ReparsePoint)-ne0){Stop-Build 'reparse_point_forbidden' "Reparse point is forbidden: $($item.FullName)"}
        $parent=Split-Path -Parent $item.FullName;if([string]::IsNullOrWhiteSpace($parent)-or$parent-ceq$item.FullName){break};$cursor=$parent
    }
}
function Convert-LegacyRelativePath($Value,[string]$Label) {
    if($Value-isnot[string]-or[string]::IsNullOrWhiteSpace([string]$Value)-or[IO.Path]::IsPathRooted([string]$Value)-or([string]$Value).Contains(':')){Stop-Build 'unsafe_source_path' "$Label is not a safe relative path."}
    $canonical=([string]$Value).Replace('\','/');$segments=@($canonical-split'/')
    if($segments.Count-lt2-or@($segments|Where-Object{[string]::IsNullOrEmpty([string]$_)-or[string]$_-in@('.','..')}).Count-gt0){Stop-Build 'unsafe_source_path' "$Label contains an empty/dot/escape segment."}
    return $canonical
}
function Resolve-RelativeFile([string]$ProjectPath,$Relative,[string]$Label) {
    $canonical=Convert-LegacyRelativePath $Relative $Label
    $full=[IO.Path]::GetFullPath((Join-Path $ProjectPath $canonical.Replace('/',[IO.Path]::DirectorySeparatorChar)))
    if(-not(Test-PathInside $full $ProjectPath)-or-not(Test-Path -LiteralPath $full -PathType Leaf)){Stop-Build 'source_missing' "$Label does not resolve to a project file."}
    Assert-NoReparsePointChain $full
    return [pscustomobject]@{Canonical=$canonical;Full=$full}
}
function Resolve-RelativeDirectory([string]$ProjectPath,$Relative,[string]$Label) {
    $canonical=Convert-LegacyRelativePath $Relative $Label
    $full=[IO.Path]::GetFullPath((Join-Path $ProjectPath $canonical.Replace('/',[IO.Path]::DirectorySeparatorChar)))
    if(-not(Test-PathInside $full $ProjectPath)-or-not(Test-Path -LiteralPath $full -PathType Container)){Stop-Build 'source_missing' "$Label does not resolve to a project directory."}
    Assert-NoReparsePointChain $full
    return [pscustomobject]@{Canonical=$canonical;Full=$full}
}
function Raw-Pointer([string]$ProjectPath,[string]$Relative) {
    $resolved=Resolve-RelativeFile $ProjectPath $Relative 'raw pointer target'
    return [ordered]@{path=$resolved.Canonical;sha256=Get-FileSha256 $resolved.Full}
}
function Generation-Pointer([string]$ProjectPath,[string]$Relative,[long]$Generation) {
    $raw=Raw-Pointer $ProjectPath $Relative
    return [ordered]@{path=$raw.path;sha256=$raw.sha256;control_generation=$Generation}
}
function Get-TreeHash([string]$Root) {
    $rootFull=[IO.Path]::GetFullPath($Root).TrimEnd('\','/')
    $lines=[Collections.Generic.List[string]]::new()
    foreach($file in @(Get-ChildItem -LiteralPath $rootFull -Recurse -File -Force|Sort-Object FullName)){
        Assert-NoReparsePointChain $file.FullName
        $relative=$file.FullName.Substring($rootFull.Length+1).Replace('\','/')
        $lines.Add("$relative`t$(Get-FileSha256 $file.FullName)")
    }
    return Get-TextSha256 (($lines-join"`n")+"`n")
}
function Get-PathHashBinding($Hashes) {
    $keys=[string[]]@($Hashes.Keys);[Array]::Sort($keys,[StringComparer]::OrdinalIgnoreCase)
    $lines=[Collections.Generic.List[string]]::new();foreach($key in $keys){$lines.Add("$key`t$([string]$Hashes[$key])")}
    return Get-TextSha256 (($lines-join"`n")+"`n")
}
function Get-ContractMetadata([string]$Text,[string]$Name) {
    $matches=[regex]::Matches($Text,"(?m)^$([regex]::Escape($Name)):\s*(?<value>\S(?:.*\S)?)$")
    if($matches.Count-ne1){Stop-Build 'contract_invalid' "Legacy Contract must contain exactly one $Name metadata line."}
    return $matches[0].Groups['value'].Value
}
function Get-ContractSection([string]$Text,[string]$Heading,[string]$Label) {
    $pattern="(?ms)^###\s+$([regex]::Escape($Heading))\s*\n(?<body>.*?)(?=^###\s+|^##\s+|\z)"
    $matches=[regex]::Matches($Text,$pattern)
    if($matches.Count-ne1-or[string]::IsNullOrWhiteSpace($matches[0].Groups['body'].Value)){Stop-Build 'contract_invalid' "Legacy Contract lacks one unambiguous $Label section."}
    return ("### $Heading`n"+$matches[0].Groups['body'].Value.Trim()+"`n")
}
function Assert-LegacyManifestIntegrity($Manifest,[string]$Label) {
    Assert-ExactKeys $Manifest @('integrity_schema','payload','integrity') $Label
    if(-not(Test-JsonInteger $Manifest.integrity_schema 1)-or[int]$Manifest.integrity_schema-ne1){Stop-Build 'manifest_invalid' "$Label integrity schema is unsupported."}
    if($Manifest.payload-isnot[Collections.IDictionary]-or$Manifest.integrity-isnot[Collections.IDictionary]){Stop-Build 'manifest_invalid' "$Label payload/integrity is invalid."}
    foreach($key in @('algorithm','key_protection','payload_sha256','hmac_sha256')){if(-not$Manifest.integrity.Contains($key)){Stop-Build 'manifest_invalid' "$Label integrity metadata is incomplete."}}
    Assert-LowerSha256 $Manifest.integrity.payload_sha256 "$Label payload hash";Assert-LowerSha256 $Manifest.integrity.hmac_sha256 "$Label HMAC metadata"
    $calculated=Get-TextSha256 ($Manifest.payload|ConvertTo-Json -Depth 100 -Compress)
    if($calculated-cne[string]$Manifest.integrity.payload_sha256){Stop-Build 'manifest_payload_hash_mismatch' "$Label payload hash is invalid."}
}
function Assert-CounterEqual($Left,$Right,[string]$Label) {
    foreach($key in @('attempt_count','audit_count','total_round_count','attempts_since_last_audit','audit_due')){
        if(-not$Left.Contains($key)-or-not$Right.Contains($key)-or[string]$Left[$key]-cne[string]$Right[$key]){Stop-Build 'counter_conflict' "$Label differs at $key."}
    }
}
function Get-CounterSnapshot($Object,[string]$Label) {
    $counter=[ordered]@{}
    foreach($key in @('attempt_count','audit_count','total_round_count','attempts_since_last_audit')){
        if(-not$Object.Contains($key)-or-not(Test-JsonInteger $Object[$key] 0)){Stop-Build 'counter_invalid' "$Label.$key is not a nonnegative integer."};$counter[$key]=[long]$Object[$key]
    }
    if(-not$Object.Contains('audit_due')-or$Object.audit_due-isnot[bool]){Stop-Build 'counter_invalid' "$Label.audit_due is not Boolean."};$counter.audit_due=[bool]$Object.audit_due
    if($counter.total_round_count-ne$counter.attempt_count+$counter.audit_count-or$counter.attempts_since_last_audit-gt$counter.attempt_count){Stop-Build 'counter_invalid' "$Label counters are inconsistent."}
    return $counter
}
function Get-LegacyLedgerReplay([string]$RunDirectory,[string]$RunId,[string]$ContractBindingSha256,$Checkpoint,$Policy) {
    if($Checkpoint-isnot[Collections.IDictionary]){Stop-Build 'ledger_checkpoint_invalid' 'Legacy cycle-ledger checkpoint must be an object.'}
    foreach($key in @('head_sequence','head_payload_sha256')){if(-not$Checkpoint.Contains($key)){Stop-Build 'ledger_checkpoint_invalid' "Legacy cycle-ledger checkpoint lacks $key."}}
    if(-not(Test-JsonInteger $Checkpoint.head_sequence 0)-or[decimal]$Checkpoint.head_sequence-gt1000000){Stop-Build 'ledger_checkpoint_invalid' 'Legacy cycle-ledger head_sequence is invalid.'}
    Assert-LowerSha256 $Checkpoint.head_payload_sha256 'legacy cycle-ledger checkpoint head hash'
    foreach($key in @('attempt_budget','total_round_budget','audit_interval_attempts')){if(-not(Test-JsonInteger $Policy[$key] 1)){Stop-Build 'ledger_policy_invalid' "Legacy cycle policy $key must be a positive integer."}}
    $head=[long]$Checkpoint.head_sequence
    $ledgerDirectory=Join-Path $RunDirectory 'cycle-ledger'
    if(-not(Test-Path -LiteralPath $ledgerDirectory -PathType Container)){Stop-Build 'ledger_missing' 'Legacy cycle-ledger directory is missing.'}
    Assert-NoReparsePointChain $ledgerDirectory
    $jsonFiles=@(Get-ChildItem -LiteralPath $ledgerDirectory -File -Filter '*.json'|Sort-Object Name)
    if($jsonFiles.Count-ne($head+1)){Stop-Build 'ledger_sequence_invalid' "Legacy cycle-ledger JSON file count does not equal head_sequence+1."}
    $snapshots=[ordered]@{}
    $previous=$null;$attemptCount=0L;$auditCount=0L;$totalRoundCount=0L;$attemptsSinceLastAudit=0L;$auditDue=$false
    $activeAttempt=$null;$activeAudit=$null;$completionCandidate=$false;$completionAuthorized=$false
    for($i=0L;$i-le$head;$i++){
        $expectedName='{0:D8}.json'-f$i
        if($jsonFiles[[int]$i].Name-cne$expectedName){Stop-Build 'ledger_sequence_invalid' "Legacy cycle-ledger has a gap, duplicate, or unexpected JSON file at '$($jsonFiles[[int]$i].Name)'."}
        $envelope=Read-StrictJson $jsonFiles[[int]$i].FullName "legacy cycle event $expectedName"
        Assert-ExactKeys $envelope @('integrity_schema','payload','integrity') "legacy cycle event $expectedName envelope"
        if(-not(Test-JsonInteger $envelope.integrity_schema 1)-or[long]$envelope.integrity_schema-ne1){Stop-Build 'ledger_envelope_invalid' "Legacy cycle event $expectedName integrity_schema is unsupported."}
        Assert-ExactKeys $envelope.integrity @('algorithm','key_protection','payload_sha256','hmac_sha256') "legacy cycle event $expectedName integrity"
        if([string]$envelope.integrity.algorithm-cne'HMAC-SHA256'-or[string]::IsNullOrWhiteSpace([string]$envelope.integrity.key_protection)){Stop-Build 'ledger_envelope_invalid' "Legacy cycle event $expectedName integrity metadata is invalid."}
        Assert-LowerSha256 $envelope.integrity.payload_sha256 "legacy cycle event $expectedName payload hash"
        Assert-LowerSha256 $envelope.integrity.hmac_sha256 "legacy cycle event $expectedName HMAC metadata"
        if($envelope.payload-isnot[Collections.IDictionary]){Stop-Build 'ledger_payload_invalid' "Legacy cycle event $expectedName payload is not an object."}
        Assert-ExactKeys $envelope.payload @('ledger_schema_version','sequence','run_id','event_type','previous_payload_sha256','recorded_at_utc','data') "legacy cycle event $expectedName payload"
        $calculated=Get-TextSha256 ($envelope.payload|ConvertTo-Json -Depth 100 -Compress)
        if($calculated-cne[string]$envelope.integrity.payload_sha256){Stop-Build 'ledger_payload_hash_mismatch' "Legacy cycle event $expectedName payload hash is invalid."}
        $event=$envelope.payload
        if(-not(Test-JsonInteger $event.ledger_schema_version 1)-or[long]$event.ledger_schema_version-ne1-or-not(Test-JsonInteger $event.sequence 0)-or[long]$event.sequence-ne$i){Stop-Build 'ledger_sequence_invalid' "Legacy cycle event $expectedName has an invalid schema or sequence."}
        if([string]$event.run_id-cne$RunId){Stop-Build 'ledger_run_mismatch' "Legacy cycle event $expectedName changed run_id."}
        if($event.data-isnot[Collections.IDictionary]){Stop-Build 'ledger_payload_invalid' "Legacy cycle event $expectedName data is not an object."}
        if($i-eq0){
            if([string]$event.event_type-cne'GENESIS'-or$null-ne$event.previous_payload_sha256){Stop-Build 'ledger_genesis_invalid' 'Legacy cycle event zero must be GENESIS with no previous hash.'}
            foreach($key in @('contract_binding_sha256','policy_sha256','policy')){if(-not$event.data.Contains($key)){Stop-Build 'ledger_genesis_invalid' "Legacy cycle genesis lacks $key."}}
            if([string]$event.data.contract_binding_sha256-cne$ContractBindingSha256){Stop-Build 'ledger_genesis_invalid' 'Legacy cycle genesis Contract binding differs from the active Contract.'}
            if([string]$event.data.policy_sha256-cne(Get-FileSha256 (Join-Path $RunDirectory 'cycle-policy.json'))-or(Get-TextSha256 ($event.data.policy|ConvertTo-Json -Depth 100 -Compress))-cne(Get-TextSha256 ($Policy|ConvertTo-Json -Depth 100 -Compress))){Stop-Build 'ledger_genesis_invalid' 'Legacy cycle genesis policy binding differs from cycle-policy.json.'}
        } else {
            Assert-LowerSha256 $event.previous_payload_sha256 "legacy cycle event $expectedName previous hash"
            if([string]$event.previous_payload_sha256-cne$previous){Stop-Build 'ledger_chain_invalid' "Legacy cycle event $expectedName breaks the payload hash chain."}
            switch([string]$event.event_type){
                'ATTEMPT_START' {
                    if($null-ne$activeAttempt-or$null-ne$activeAudit-or$auditDue-or$completionAuthorized){Stop-Build 'ledger_transition_invalid' "Legacy cycle event $expectedName starts an attempt from an illegal state."}
                    if(-not$event.data.Contains('attempt_id')-or[string]::IsNullOrWhiteSpace([string]$event.data.attempt_id)){Stop-Build 'ledger_payload_invalid' "Legacy cycle event $expectedName lacks attempt_id."}
                    if($attemptCount-ge[long]$Policy.attempt_budget-or$totalRoundCount+2-gt[long]$Policy.total_round_budget){Stop-Build 'ledger_budget_invalid' "Legacy cycle event $expectedName violates the attempt or reserved-audit budget."}
                    $attemptCount++;$totalRoundCount++;$attemptsSinceLastAudit++;$activeAttempt=[string]$event.data.attempt_id
                    if($attemptsSinceLastAudit-ge[long]$Policy.audit_interval_attempts){$auditDue=$true}
                }
                'ATTEMPT_END' {
                    if($null-eq$activeAttempt-or-not$event.data.Contains('attempt_id')-or[string]$event.data.attempt_id-cne$activeAttempt){Stop-Build 'ledger_transition_invalid' "Legacy cycle event $expectedName ends no matching active attempt."}
                    $activeAttempt=$null
                    if($event.data.Contains('outcome')-and[string]$event.data.outcome-ceq'candidate_found'){$completionCandidate=$true;$auditDue=$true}
                    if($event.data.Contains('outcome')-and[string]$event.data.outcome-ceq'portfolio_proposed'){$auditDue=$true}
                }
                'AUDIT_START' {
                    if($null-ne$activeAttempt-or$null-ne$activeAudit-or$attemptsSinceLastAudit-lt1){Stop-Build 'ledger_transition_invalid' "Legacy cycle event $expectedName starts an audit from an illegal state."}
                    if(-not$event.data.Contains('audit_id')-or[string]::IsNullOrWhiteSpace([string]$event.data.audit_id)){Stop-Build 'ledger_payload_invalid' "Legacy cycle event $expectedName lacks audit_id."}
                    if($totalRoundCount+1-gt[long]$Policy.total_round_budget){Stop-Build 'ledger_budget_invalid' "Legacy cycle event $expectedName exceeds the total-round budget."}
                    $auditCount++;$totalRoundCount++;$activeAudit=[string]$event.data.audit_id
                }
                'AUDIT_END' {
                    if($null-eq$activeAudit-or-not$event.data.Contains('audit_id')-or[string]$event.data.audit_id-cne$activeAudit){Stop-Build 'ledger_transition_invalid' "Legacy cycle event $expectedName ends no matching active audit."}
                    $activeAudit=$null;$attemptsSinceLastAudit=0L;$auditDue=$false
                    if($event.data.Contains('completion_authorized')-and[bool]$event.data.completion_authorized){$completionAuthorized=$true}elseif($completionCandidate){$completionCandidate=$false}
                }
                'RETURN_CHECKED' {}
                default {Stop-Build 'ledger_event_type_invalid' "Legacy cycle event $expectedName has unknown event_type '$($event.event_type)'."}
            }
        }
        if($attemptCount-gt[long]$Policy.attempt_budget-or$totalRoundCount-gt[long]$Policy.total_round_budget-or$attemptsSinceLastAudit-gt[long]$Policy.audit_interval_attempts){Stop-Build 'ledger_budget_invalid' "Legacy cycle event $expectedName violates a frozen budget."}
        $previous=$calculated
        $snapshots[[string]$i]=[ordered]@{head_sequence=$i;head_payload_sha256=$previous;attempt_count=$attemptCount;audit_count=$auditCount;total_round_count=$totalRoundCount;attempts_since_last_audit=$attemptsSinceLastAudit;audit_due=$auditDue}
    }
    if($null-ne$activeAttempt-or$null-ne$activeAudit){Stop-Build 'ledger_open_event' 'Legacy cycle-ledger head leaves an attempt or audit open; migration requires a closed event boundary.'}
    if($previous-cne[string]$Checkpoint.head_payload_sha256){Stop-Build 'ledger_checkpoint_invalid' 'Legacy manifest checkpoint does not bind the replayed ledger head.'}
    $derived=$snapshots[[string]$head]
    Assert-CounterEqual $derived (Get-CounterSnapshot $Checkpoint 'legacy cycle-ledger checkpoint') 'replayed ledger and manifest checkpoint counters'
    return [pscustomobject]@{Counters=(Get-CounterSnapshot $derived 'replayed ledger counters');Snapshots=$snapshots;HeadRelative=('cycle-ledger/{0:D8}.json'-f$head)}
}
function Assert-ReceiptPrefixCounters($ReceiptCounters,$Replay,[string]$Label) {
    Assert-ExactKeys $ReceiptCounters @('head_sequence','head_payload_sha256','attempt_count','audit_count','total_round_count','attempts_since_last_audit','audit_due') $Label
    if(-not(Test-JsonInteger $ReceiptCounters.head_sequence 0)){Stop-Build 'amendment_chain_invalid' "$Label head_sequence is invalid."}
    Assert-LowerSha256 $ReceiptCounters.head_payload_sha256 "$Label head hash"
    $sequence=[string][long]$ReceiptCounters.head_sequence
    if(-not$Replay.Snapshots.Contains($sequence)){Stop-Build 'amendment_chain_invalid' "$Label does not identify a replayed ledger prefix."}
    $expected=$Replay.Snapshots[$sequence]
    if([string]$ReceiptCounters.head_payload_sha256-cne[string]$expected.head_payload_sha256){Stop-Build 'amendment_chain_invalid' "$Label head hash does not bind its ledger prefix."}
    Assert-CounterEqual $expected (Get-CounterSnapshot $ReceiptCounters $Label) "$Label and replayed ledger prefix counters"
}
function Get-ArtifactCategory([string]$Relative) {
    if($Relative-ceq'contracts/v1-prompt.md'){return 'problem'}
    if($Relative-cmatch'^attempts/'){return 'attempts'}
    if($Relative-cmatch'^failures/'){return 'failures'}
    if($Relative-cmatch'^evidence/'){return 'evidence'}
    if($Relative-cmatch'^cycles/'){return 'routes'}
    if($Relative-cmatch'^handoffs/'){return 'handoff'}
    if($Relative-cmatch'^sources/'){return 'source_artifacts'}
    if($Relative-cmatch'\.(?:py|sage|m|nb|ipynb|wl|ps1|psm1)$'){return 'computation_artifacts'}
    if($Relative-cmatch'(?:result|proof|verified|audit)'){return 'verified_partial_results'}
    return 'intermediate_artifacts'
}
function Get-EvidenceGrade([string]$Category) {
    switch($Category){'problem'{'not_applicable'};'verified_partial_results'{'preserved_predecessor_claim_not_promoted'};'evidence'{'preserved_original_grade'};default{'preserved_unverified_or_operational'}}
}

try {
    Assert-LowerSha256 $GoalObjectiveSha256 'GoalObjectiveSha256'
    $goalHash=Get-TextSha256 $GoalObjectiveRaw
    if($goalHash-cne$GoalObjectiveSha256){Stop-Build 'goal_objective_hash_mismatch' 'GoalObjectiveSha256 does not hash the exact supplied GoalObjectiveRaw UTF-8 bytes.'}
    $goalThreadAvailable=-not[string]::IsNullOrWhiteSpace($GoalThreadId)
    $goalThreadValue=$null
    if($goalThreadAvailable){if($GoalThreadId.Length-gt256-or$GoalThreadId-match'[\x00-\x1f\x7f]'){Stop-Build 'goal_thread_invalid' 'GoalThreadId is invalid.'};$goalThreadValue=[string]$GoalThreadId}

    $source=[IO.Path]::GetFullPath($ProjectDirectory).TrimEnd('\','/')
    if(-not(Test-Path -LiteralPath $source -PathType Container)){Stop-Build 'project_missing' 'ProjectDirectory is missing.'}
    Assert-NoReparsePointChain $source
    $result.source_project=$source
    $result.source_project_tree_sha256_before=Get-TreeHash $source

    $sourceHeadPath=Join-Path $source 'project.json'
    $oldHead=Read-StrictJson $sourceHeadPath 'legacy project head'
    foreach($key in @('schema','project_id','active_contract','active_run')){if(-not$oldHead.Contains($key)){Stop-Build 'legacy_head_invalid' "Legacy project head is missing $key."}}
    if([string]$oldHead.schema-ceq'math-research-project/v8'){Stop-Build 'already_v8' 'The project already has a v8 authoritative head; LEGACY_SUCCESSOR is not applicable.'}
    Assert-SafeId $oldHead.project_id 'project_id'
    $projectId=[string]$oldHead.project_id
    $oldHash=Get-FileSha256 $sourceHeadPath;$result.expected_old_sha256=$oldHash
    $oldGeneration=$null
    if($oldHead.Contains('control_generation')){if(-not(Test-JsonInteger $oldHead.control_generation 0)-or[decimal]$oldHead.control_generation-ge[decimal][long]::MaxValue){Stop-Build 'old_generation_invalid' 'Legacy control_generation is invalid.'};$oldGeneration=[long]$oldHead.control_generation}
    $newGeneration=if($null-eq$oldGeneration){1L}else{$oldGeneration+1}
    $result.expected_old_control_generation=if($null-eq$oldGeneration){'0'}else{[string]$oldGeneration};$result.expected_new_control_generation=$newGeneration

    if($oldHead.active_contract-isnot[Collections.IDictionary]-or$oldHead.active_run-isnot[Collections.IDictionary]){Stop-Build 'legacy_head_invalid' 'Legacy active Contract/run pointers are invalid.'}
    foreach($key in @('path','version')){if(-not$oldHead.active_contract.Contains($key)){Stop-Build 'legacy_head_invalid' "Legacy active_contract lacks $key."}}
    foreach($key in @('id','path')){if(-not$oldHead.active_run.Contains($key)){Stop-Build 'legacy_head_invalid' "Legacy active_run lacks $key."}}
    Assert-SafeId $oldHead.active_run.id 'predecessor run id'
    $contractResolved=Resolve-RelativeFile $source $oldHead.active_contract.path 'legacy Contract'
    $contractRawHash=Get-FileSha256 $contractResolved.Full
    $headContractHash=if($oldHead.active_contract.Contains('sha256')){[string]$oldHead.active_contract.sha256}elseif($oldHead.active_contract.Contains('binding_sha256')){[string]$oldHead.active_contract.binding_sha256}else{$null}
    if($null-eq$headContractHash){Stop-Build 'legacy_head_invalid' 'Legacy active_contract has no byte hash.'};Assert-LowerSha256 $headContractHash 'legacy Contract hash'
    if($headContractHash-cne$contractRawHash){Stop-Build 'legacy_contract_hash_mismatch' 'Legacy Contract bytes differ from project.json.'}
    $runResolved=Resolve-RelativeDirectory $source $oldHead.active_run.path 'legacy active run'
    if($runResolved.Canonical-cne"runs/$([string]$oldHead.active_run.id)"){Stop-Build 'legacy_head_invalid' 'Legacy active run path/ID mismatch.'}
    $primaryPath=Join-Path $runResolved.Full 'run.json';$backupPath=Join-Path $runResolved.Full 'run.json.bak'
    $primary=Read-StrictJson $primaryPath 'legacy primary run manifest';$backup=Read-StrictJson $backupPath 'legacy backup run manifest'
    Assert-LegacyManifestIntegrity $primary 'legacy primary run manifest';Assert-LegacyManifestIntegrity $backup 'legacy backup run manifest'
    foreach($manifest in @($primary,$backup)){if(-not$manifest.payload.Contains('revision')-or-not(Test-JsonInteger $manifest.payload.revision 0)){Stop-Build 'manifest_invalid' 'Legacy manifest revision is invalid.'}}
    if([long]$primary.payload.revision-le[long]$backup.payload.revision){Stop-Build 'manifest_precedence_invalid' 'Primary run manifest must be the strictly newer self-consistent revision.'}
    $payload=$primary.payload
    if([string]$payload.run_id-cne[string]$oldHead.active_run.id-or[string]$payload.project.project_id-cne$projectId-or[string]$payload.contract_version-cne[string]$oldHead.active_contract.version){Stop-Build 'manifest_binding_mismatch' 'Current manifest does not bind the active project/run/Contract.'}
    if([string]$payload.inputs.prompt.contract_binding_sha256-cne$contractRawHash){Stop-Build 'manifest_binding_mismatch' 'Current manifest prompt binding differs from the active Contract.'}

    $legacyContractText=[IO.File]::ReadAllText($contractResolved.Full,[Text.UTF8Encoding]::new($false,$true))-replace"`r`n","`n"
    if($legacyContractText.Contains("`r")){Stop-Build 'contract_invalid' 'Legacy Contract contains isolated CR.'}
    $targetSection=Get-ContractSection $legacyContractText '精确目标与量词' 'target/quantifier'
    $assumptionSection=Get-ContractSection $legacyContractText '工具、计算与复现' 'assumption/tool'
    $completionSection=Get-ContractSection $legacyContractText '终止性完成标准' 'completion'
    $permissionSection=Get-ContractSection $legacyContractText '权限、外部影响与隐私' 'permission/privacy'
    $oldObjectiveHash=[string]$payload.inputs.goal_objective.normalized_sha256;Assert-LowerSha256 $oldObjectiveHash 'predecessor objective hash'
    $goalObjectivePath=Join-Path $runResolved.Full ([string]$payload.inputs.goal_objective.file)
    if(-not(Test-Path -LiteralPath $goalObjectivePath -PathType Leaf)-or(Get-FileSha256 $goalObjectivePath)-cne[string]$payload.inputs.goal_objective.file_sha256-or(Get-TextSha256 (([IO.File]::ReadAllText($goalObjectivePath,[Text.UTF8Encoding]::new($false,$true))-replace"`r`n","`n").Trim()))-cne$oldObjectiveHash){Stop-Build 'objective_source_invalid' 'Predecessor GoalObjective source does not match current manifest.'}

    $config=$payload.config;$policyPath=Join-Path $runResolved.Full 'cycle-policy.json';$ticketsPath=Join-Path $runResolved.Full 'cycle-tickets-000.json'
    $policy=Read-StrictJson $policyPath 'legacy cycle policy';$legacyTickets=Read-StrictJson $ticketsPath 'legacy initial tickets'
    if((Get-FileSha256 $policyPath)-cne[string]$payload.cycle_ledger.policy.sha256-or(Get-FileSha256 $ticketsPath)-cne[string]$payload.cycle_ledger.initial_tickets.sha256){Stop-Build 'manifest_binding_mismatch' 'Current manifest cycle policy/ticket hash differs from files.'}
    foreach($key in @('attempt_budget','total_round_budget','audit_interval_attempts','max_child_agents','max_total_agents','max_runtime_minutes')){if(-not(Test-JsonInteger $config[$key] 0)){Stop-Build 'config_invalid' "Effective config $key is invalid."}}
    foreach($key in @('attempt_budget','total_round_budget','audit_interval_attempts')){if([long]$config[$key]-ne[long]$policy[$key]-or[string](Get-ContractMetadata $legacyContractText $key)-cne[string]$config[$key]){Stop-Build 'envelope_conflict' "Contract/manifest/policy disagree at $key."}}
    foreach($key in @('model','reasoning_effort','web_search')){if([string](Get-ContractMetadata $legacyContractText $key)-cne[string]$config[$key]){Stop-Build 'envelope_conflict' "Contract and effective manifest config disagree at $key."}}
    if([long]$config.max_total_agents-ne[long]$config.max_child_agents+1){Stop-Build 'config_invalid' 'max_total_agents must equal max_child_agents+1.'}
    $replay=Get-LegacyLedgerReplay $runResolved.Full ([string]$oldHead.active_run.id) $contractRawHash $payload.cycle_ledger.checkpoint $policy
    $counters=$replay.Counters
    $ledgerRelative=$replay.HeadRelative
    $ledgerPath=Join-Path $runResolved.Full $ledgerRelative.Replace('/',[IO.Path]::DirectorySeparatorChar)

    $amendments=[Collections.Generic.List[object]]::new()
    $compatHash=$null
    if($payload.Contains('compatibility_migration')){
        $embedded=$payload.compatibility_migration
        if([string]$embedded.protocol-cne'math-research-legacy-v1-compat-migration/v1'){Stop-Build 'amendment_invalid' 'Unknown compatibility migration protocol.'}
        $receiptRelative="$($runResolved.Canonical)/compat-migration-v1/migration-receipt.json";$receiptPath=Join-Path $source $receiptRelative.Replace('/',[IO.Path]::DirectorySeparatorChar)
        $receipt=Read-StrictJson $receiptPath 'compatibility migration receipt';$compatHash=Get-FileSha256 $receiptPath
        if($compatHash-cne[string]$embedded.receipt_sha256-or[string]$receipt.protocol-cne[string]$embedded.protocol-or[string]$receipt.project.project_id-cne$projectId-or[string]$receipt.run.id-cne[string]$oldHead.active_run.id-or[string]$receipt.contract.binding_sha256-cne$contractRawHash){Stop-Build 'amendment_chain_invalid' 'Compatibility migration receipt is not cross-bound.'}
        Assert-ReceiptPrefixCounters $receipt.source.counters $replay 'compatibility receipt source counters'
        $amendments.Add([ordered]@{protocol=[string]$receipt.protocol;receipt_id=[string]$receipt.migration_id;path=$receiptRelative;sha256=$compatHash;applied_at_utc=[string]$embedded.applied_at_utc;precedence_rank=1;objective_changed=[bool]$embedded.objective_changed;quantifiers_changed=[bool]$embedded.quantifiers_changed;counters_reset=[bool]$embedded.counters_reset;permission_effect='authorized_approval_mode_change'})
    }
    if($payload.Contains('control_path_amendment_v2')){
        if($null-eq$compatHash){Stop-Build 'amendment_chain_invalid' 'Control-path v2 requires the verified compatibility receipt.'}
        $embedded=$payload.control_path_amendment_v2
        if([string]$embedded.protocol-cne'math-research-legacy-v1-control-path-amendment/v2'){Stop-Build 'amendment_invalid' 'Unknown control-path amendment protocol.'}
        $receiptRelative="$($runResolved.Canonical)/control-path-amendment-v2/control-path-receipt.json";$receiptPath=Join-Path $source $receiptRelative.Replace('/',[IO.Path]::DirectorySeparatorChar)
        $receipt=Read-StrictJson $receiptPath 'control-path amendment receipt';$receiptHash=Get-FileSha256 $receiptPath
        if($receiptHash-cne[string]$embedded.receipt_sha256-or[string]$receipt.protocol-cne[string]$embedded.protocol-or[string]$receipt.prior_migration.receipt_sha256-cne$compatHash-or[string]$receipt.project.project_id-cne$projectId-or[string]$receipt.run.id-cne[string]$oldHead.active_run.id-or[string]$receipt.contract.binding_sha256-cne$contractRawHash){Stop-Build 'amendment_chain_invalid' 'Control-path amendment receipt is not cross-bound to compatibility migration.'}
        Assert-ReceiptPrefixCounters $receipt.source.counters $replay 'control-path receipt source counters'
        if([bool]$embedded.objective_changed-or[bool]$embedded.quantifiers_changed-or[bool]$embedded.counters_reset-or[bool]$embedded.permission_scope_expanded){Stop-Build 'envelope_expansion' 'Control-path receipt records a prohibited objective/quantifier/counter/permission expansion.'}
        $amendments.Add([ordered]@{protocol=[string]$receipt.protocol;receipt_id=[string]$receipt.amendment_id;path=$receiptRelative;sha256=$receiptHash;applied_at_utc=[string]$embedded.applied_at_utc;precedence_rank=2;objective_changed=[bool]$embedded.objective_changed;quantifiers_changed=[bool]$embedded.quantifiers_changed;counters_reset=[bool]$embedded.counters_reset;permission_effect='control_argv_only_no_scope_expansion'})
    }
    if([string]$config.approval_mode-cne[string]$config.approval_policy){Stop-Build 'config_invalid' 'Effective approval_mode/approval_policy disagree.'}
    if(@($amendments).Count-gt0-and[string]$config.approval_mode-cne'approve_for_me'){Stop-Build 'amendment_chain_invalid' 'Applied compatibility receipts do not yield approve_for_me in the current manifest.'}
    if([string]$config.web_search-cnotin@('allowed','denied')){Stop-Build 'config_invalid' 'Effective web_search must be allowed or denied.'}
    $allowedWorkerTools=@('apply_patch','collaboration.spawn_agent','collaboration.send_message','collaboration.wait_agent','shell_command')
    if([string]$config.web_search-ceq'allowed'){$allowedWorkerTools+=@('web__run')}
    $allowedWorkerToolSet=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($toolName in $allowedWorkerTools){if(-not$allowedWorkerToolSet.Add($toolName)){Stop-Build 'config_invalid' 'Internal allowed_worker_tools contains a duplicate.'}}

    $target=$source
    if(-not[string]::IsNullOrWhiteSpace($OutputDirectory)){
        $target=[IO.Path]::GetFullPath($OutputDirectory).TrimEnd('\','/')
        if($target-ceq$source-or(Test-PathInside $target $source)-or(Test-PathInside $source $target)){Stop-Build 'unsafe_output_path' 'OutputDirectory must be a distinct non-nested directory.'}
    }
    $result.target_project=$target
    $generationName='g{0:D4}'-f$newGeneration;$newRunId="successor-$generationName";Assert-SafeId $newRunId 'successor run id'
    $newRunRelative="runs/$newRunId";$contractRelative="contracts/contract-v8-$generationName.md"
    $snapshotRelative="state/successors/$generationName-predecessor-project.json"
    $baselineRelative="state/successor-baselines/$generationName.json"
    $problemRelative="$newRunRelative/evidence/problem-statement.md"
    $envelopeRelative="$newRunRelative/evidence/effective-predecessor-envelope.json"
    $mappingRelative="$newRunRelative/evidence/control-migration-map.json"
    $indexRelative="$newRunRelative/evidence/inherited-artifacts.json"
    $lineageRelative="state/successors/$generationName.json"
    $hostRelative="$newRunRelative/host-bindings/host-bind-$generationName.json"
    $eventRelative="state/project-events/$generationName.json"
    $checkpointRelative="state/generations/$generationName/checkpoint.json"
    $stateRelative="state/generations/$generationName/goal-host-v8.json"
    $candidateRelative="state/staging/legacy-successor-$generationName.json"
    $intentRelative="state/build-intents/$generationName.json"
    if($legacyTickets.tickets-isnot[Collections.IList]-or@($legacyTickets.tickets).Count-lt1-or@($legacyTickets.tickets)[0]-isnot[Collections.IDictionary]-or-not@($legacyTickets.tickets)[0].Contains('ticket_id')){Stop-Build 'ticket_source_invalid' 'Legacy initial tickets are empty or lack ticket_id.'}
    $plannedTicketId=[string]@($legacyTickets.tickets)[0].ticket_id;Assert-SafeId $plannedTicketId 'initial ticket id'
    $generatedFiles=@($intentRelative,$snapshotRelative,$baselineRelative,$problemRelative,$envelopeRelative,$mappingRelative,$indexRelative,$contractRelative,$hostRelative,"$newRunRelative/run.json",$lineageRelative,"$newRunRelative/tickets/$plannedTicketId-$generationName.json",$eventRelative,$checkpointRelative,$stateRelative,$candidateRelative)
    $generatedSet=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase);foreach($relative in $generatedFiles){if(-not$generatedSet.Add($relative)){Stop-Build 'config_invalid' 'Generated successor path set contains a duplicate.'}}
    $transientSet=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase);foreach($relative in $generatedFiles){[void]$transientSet.Add($relative+'.build-v8.tmp')}
    $intentPath=Join-Path $target $intentRelative.Replace('/',[IO.Path]::DirectorySeparatorChar)
    $intentExisted=Test-Path -LiteralPath $intentPath -PathType Leaf
    $intentTempExisted=Test-Path -LiteralPath ($intentPath+'.build-v8.tmp') -PathType Leaf
    if((Test-Path -LiteralPath $target)-and$target-cne$source-and-not$intentExisted-and-not$intentTempExisted){Stop-Build 'output_exists' 'An existing OutputDirectory is reusable only when it contains this deterministic build intent or its interrupted deterministic temp.'}
    if($target-ceq$source-and-not$intentExisted){foreach($relative in $generatedFiles){if(Test-Path -LiteralPath (Join-Path $target $relative.Replace('/',[IO.Path]::DirectorySeparatorChar))){Stop-Build 'successor_collision' "A generated successor path exists without its build intent: $relative"}}}

    $sourceFiles=@(Get-ChildItem -LiteralPath $source -Recurse -File -Force|Sort-Object FullName)
    foreach($file in $sourceFiles){Assert-NoReparsePointChain $file.FullName}
    $predecessorHashes=[ordered]@{}
    $sourceInventory=[Collections.Generic.List[object]]::new()
    foreach($file in $sourceFiles){
        $relative=$file.FullName.Substring($source.Length+1).Replace('\','/')
        if($target-ceq$source-and($generatedSet.Contains($relative)-or$transientSet.Contains($relative))){continue}
        $predecessorHashes[$relative]=Get-FileSha256 $file.FullName
        if($relative-ceq'project.json'){continue}
        $category=Get-ArtifactCategory $relative
        $sourceInventory.Add([ordered]@{category=$category;path=$relative;sha256=$predecessorHashes[$relative];evidence_grade=Get-EvidenceGrade $category})
    }
    if(-not$predecessorHashes.Contains('project.json')-or[string]$predecessorHashes['project.json']-cne$oldHash){Stop-Build 'predecessor_mutated' 'Predecessor project.json is absent or changed.'}
    $predecessorInventorySha256=Get-PathHashBinding $predecessorHashes

    $existingIntent=$null
    if($intentExisted){
        $existingIntent=Read-StrictJson $intentPath 'legacy successor build intent'
        Assert-ExactKeys $existingIntent @('schema','builder_protocol','project_id','predecessor_project_head_sha256','predecessor_control_generation','control_generation','goal_host','target_project_directory_name','predecessor_inventory_sha256','generated_paths','created_at_utc') 'legacy successor build intent'
        if([string]$existingIntent.created_at_utc-cnotmatch'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,7})?Z$'){Stop-Build 'build_intent_invalid' 'Build-intent frozen timestamp is invalid.'}
        $frozenUtc=[string]$existingIntent.created_at_utc
    }
    else{$frozenUtc=[DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ',[Globalization.CultureInfo]::InvariantCulture)}
    $intent=[ordered]@{schema='math-research-legacy-successor-build-intent/v8';builder_protocol='staging-only-legacy-successor/v8';project_id=$projectId;predecessor_project_head_sha256=$oldHash;predecessor_control_generation=$oldGeneration;control_generation=$newGeneration;goal_host=[ordered]@{thread_id_available=$goalThreadAvailable;thread_id=$goalThreadValue;objective_raw_sha256=$goalHash};target_project_directory_name=Split-Path -Leaf $target;predecessor_inventory_sha256=$predecessorInventorySha256;generated_paths=@($generatedFiles);created_at_utc=$frozenUtc}
    if($intentExisted){$expectedIntentBytes=[Text.UTF8Encoding]::new($false).GetBytes((ConvertTo-CanonicalJson $intent));$actualIntentBytes=[IO.File]::ReadAllBytes($intentPath);if($actualIntentBytes.Length-ne$expectedIntentBytes.Length-or(Get-BytesSha256 $actualIntentBytes)-cne(Get-BytesSha256 $expectedIntentBytes)){Stop-Build 'build_intent_mismatch' 'Existing build intent differs from the current project/Goal/input envelope.'}}

    if($DryRun){
        $result.reason='dry_run_verified';$result.inherited_artifact_count=$sourceInventory.Count+1;$result.candidate_head_file=Join-Path $target $candidateRelative.Replace('/',[IO.Path]::DirectorySeparatorChar)
        $result.source_project_tree_sha256_after=Get-TreeHash $source
        $result|ConvertTo-Json -Depth 16 -Compress
        exit 0
    }

    if($target-cne$source-and-not(Test-Path -LiteralPath $target)){
        New-Item -ItemType Directory -Path $target -Force|Out-Null
        foreach($item in @(Get-ChildItem -LiteralPath $source -Force)){Copy-Item -LiteralPath $item.FullName -Destination $target -Recurse -Force}
    }
    foreach($relative in $predecessorHashes.Keys){$targetPredecessorPath=Join-Path $target $relative.Replace('/',[IO.Path]::DirectorySeparatorChar);if(-not(Test-Path -LiteralPath $targetPredecessorPath -PathType Leaf)-or(Get-FileSha256 $targetPredecessorPath)-cne[string]$predecessorHashes[$relative]){Stop-Build 'copy_verification_failed' "Target predecessor bytes are absent or changed: $relative"}}
    $targetUnexpected=@(Get-ChildItem -LiteralPath $target -Recurse -File -Force|ForEach-Object{$_.FullName.Substring($target.Length+1).Replace('\','/')}|Where-Object{-not$predecessorHashes.Contains($_)-and-not$generatedSet.Contains($_)-and-not$transientSet.Contains($_)})
    if($targetUnexpected.Count-gt0){Stop-Build 'unexpected_staging_write' "Target contains files outside predecessor plus deterministic staging set: $($targetUnexpected-join',')"}
    if((Get-FileSha256 (Join-Path $target 'project.json'))-cne$oldHash){Stop-Build 'stale_source' 'Target legacy head changed before staging.'}
    Write-CanonicalJson $intentPath $intent
    $intentPointer=Raw-Pointer $target $intentRelative

    $snapshotPath=Join-Path $target $snapshotRelative.Replace('/',[IO.Path]::DirectorySeparatorChar);Write-OrVerifyBytes $snapshotPath ([IO.File]::ReadAllBytes((Join-Path $target 'project.json')))
    $problemText="# Migrated problem statement`n`n- predecessor Contract: ``$($contractResolved.Canonical)```n- predecessor Contract SHA-256: ``$contractRawHash```n`n$targetSection`n$completionSection`n"
    Write-Utf8 (Join-Path $target $problemRelative.Replace('/',[IO.Path]::DirectorySeparatorChar)) $problemText

    $baseline=[ordered]@{schema='math-research-counter-budget-baseline/v8';project_id=$projectId;predecessor_run_id=[string]$oldHead.active_run.id;attempt_count=$counters.attempt_count;audit_count=$counters.audit_count;total_round_count=$counters.total_round_count;attempts_since_last_audit=$counters.attempts_since_last_audit;audit_due=$counters.audit_due;budget_consumption=[ordered]@{attempt_budget_ceiling=[long]$config.attempt_budget;attempts_spent=$counters.attempt_count;total_round_budget_ceiling=[long]$config.total_round_budget;total_rounds_spent=$counters.total_round_count;runtime_or_other_cumulative=[ordered]@{runtime_minutes=0;token_usage_input=if($payload.token_usage){[long]$payload.token_usage.input_tokens}else{0};token_usage_output=if($payload.token_usage){[long]$payload.token_usage.output_tokens}else{0}}}}
    Write-CanonicalJson (Join-Path $target $baselineRelative.Replace('/',[IO.Path]::DirectorySeparatorChar)) $baseline
    $baselinePointer=Raw-Pointer $target $baselineRelative

    $sourceBindings=[ordered]@{project_head_snapshot=Raw-Pointer $target $snapshotRelative;contract=[ordered]@{path=$contractResolved.Canonical;sha256=$contractRawHash};primary_manifest=Raw-Pointer $target "$($runResolved.Canonical)/run.json";backup_manifest=Raw-Pointer $target "$($runResolved.Canonical)/run.json.bak";cycle_policy=Raw-Pointer $target "$($runResolved.Canonical)/cycle-policy.json";initial_tickets=Raw-Pointer $target "$($runResolved.Canonical)/cycle-tickets-000.json";ledger_head=Raw-Pointer $target "$($runResolved.Canonical)/$ledgerRelative"}
    $effectiveEnvelope=[ordered]@{
        schema='math-research-effective-predecessor-envelope/v8';project_id=$projectId;predecessor_run=[ordered]@{id=[string]$oldHead.active_run.id;path=$runResolved.Canonical;manifest_revision=[long]$payload.revision;manifest_status=[string]$payload.status}
        source_precedence=@('strict_self_consistent_current_primary_manifest_payload_after_applied_receipts_hmac_not_authenticated','strict_hash_cross_bound_receipt_chain_compat_then_control_v2','immutable_legacy_contract_semantic_sections_and_machine_blocks','exact_cycle_ledger_checkpoint_counters_no_conflict_allowed')
        source_bindings=$sourceBindings
        semantic=[ordered]@{problem_statement=Raw-Pointer $target $problemRelative;predecessor_goal_objective_sha256=$oldObjectiveHash;target_quantifiers_sha256=Get-TextSha256 $targetSection;assumptions_sha256=Get-TextSha256 $assumptionSection;completion_criteria_sha256=Get-TextSha256 $completionSection;objective_changed=$false;quantifiers_changed=$false}
        permissions=[ordered]@{approval_mode=[string]$config.approval_mode;web_search=[string]$config.web_search;sandbox=[string]$config.sandbox;filesystem_read_scope='project-index-bounded-plus-required-local-tools';filesystem_write_scope='active-successor-run-staging_then-goal-host-verified-project-publication';private_data_policy='no_unrelated_private_files_credentials_or_personal_data_to_external_services';external_messages='denied';deployments='denied';purchases='denied';software_installation='denied';network_services='denied';shell_network_access=[bool]$config.shell_network_access;user_plugins_and_mcp_enabled=(-not[bool]$config.configured_to_disable_user_plugins_and_mcp)}
        resources=[ordered]@{model=[string]$config.model;reasoning_effort=[string]$config.reasoning_effort;max_child_agents=[long]$config.max_child_agents;max_total_agents=[long]$config.max_total_agents;max_runtime_minutes=[long]$config.max_runtime_minutes;allowed_tools=@($allowedWorkerTools)}
        budgets=[ordered]@{audit_interval_attempts=[long]$config.audit_interval_attempts;attempt_budget=[long]$config.attempt_budget;total_round_budget=[long]$config.total_round_budget;max_route_family_attempts_per_cycle=[long]$policy.max_route_family_attempts_per_cycle;max_repair_batches_per_attempt=[long]$policy.max_repair_batches_per_attempt}
        counters=$counters;amendments=@($amendments)
    }
    Write-CanonicalJson (Join-Path $target $envelopeRelative.Replace('/',[IO.Path]::DirectorySeparatorChar)) $effectiveEnvelope
    $envelopePointer=Raw-Pointer $target $envelopeRelative

    $mapping=[ordered]@{
        schema='math-research-control-migration-map/v8';project_id=$projectId;predecessor_run_id=[string]$oldHead.active_run.id;successor_run_id=$newRunId;control_generation=$newGeneration;source_envelope=$envelopePointer;mapping_policy='exact_semantic_and_ceiling_preservation_with_control_plane_retirement/v8'
        preserved_bindings=@(
            [ordered]@{name='mathematical_target_quantifiers';mapping='preserve_exact_hash';source_sha256=$effectiveEnvelope.semantic.target_quantifiers_sha256;successor='contract_problem_statement'},
            [ordered]@{name='completion_criteria';mapping='preserve_exact_hash';source_sha256=$effectiveEnvelope.semantic.completion_criteria_sha256;successor='contract_completion_gate'},
            [ordered]@{name='permissions_privacy_external_effect_ceilings';mapping='preserve_effective_value';source_sha256=Get-TextSha256 (ConvertTo-CanonicalJson $effectiveEnvelope.permissions);successor='contract_permission_envelope'},
            [ordered]@{name='budgets_and_consumption';mapping='preserve_effective_value';source_sha256=Get-TextSha256 (ConvertTo-CanonicalJson ([ordered]@{budgets=$effectiveEnvelope.budgets;counters=$effectiveEnvelope.counters}));successor='contract_and_counter_baseline'}
        )
        retired_bindings=@(
            [ordered]@{name='child_goal_created_inside_codex_exec';mapping='retire_without_successor_authority';successor=$null;reason='Goal authority belongs only to the current product task'},
            [ordered]@{name='legacy_launcher_resume_thread';mapping='retire_without_successor_authority';successor=$null;reason='No legacy Resume or isolated child-thread continuity'},
            [ordered]@{name='dispatcher_daemon_heartbeat_lease';mapping='retire_without_successor_authority';successor=$null;reason='No external scheduler or daemon authority'},
            [ordered]@{name='legacy_goal_controller_state';mapping='retire_without_successor_authority';successor=$null;reason='Historical control files remain evidence only'}
        )
        control_mapping=@(
            [ordered]@{from='legacy_outer_or_child_goal';mapping='replace_with_goal_host_v8';to='current_product_goal_host'},
            [ordered]@{from='legacy_worker_prompt';mapping='replace_with_goal_host_v8';to='hash_bound_collaboration_ticket'},
            [ordered]@{from='legacy_project_mutation';mapping='replace_with_goal_host_v8';to='cooperative_guarded_project_head_commit'},
            [ordered]@{from='post_v8_contract_or_run_change';mapping='fail_closed_unimplemented';to='RUN_SUCCESSOR_required'}
        )
        unresolved_gaps=@([ordered]@{name='future_v8_resource_or_semantic_expansion';mapping='fail_closed_unimplemented';effect='read_only_until_RUN_SUCCESSOR_is_implemented_and_authorized'})
    }
    Write-CanonicalJson (Join-Path $target $mappingRelative.Replace('/',[IO.Path]::DirectorySeparatorChar)) $mapping
    $mappingPointer=Raw-Pointer $target $mappingRelative

    $coverage=@('problem','verified_partial_results','attempts','failures','evidence','routes','audits','handoff','source_artifacts','computation_artifacts','intermediate_artifacts')
    $entries=[Collections.Generic.List[object]]::new()
    foreach($entry in $sourceInventory){$entries.Add($entry)}
    $entries.Add([ordered]@{category='intermediate_artifacts';path=$snapshotRelative;sha256=(Get-FileSha256 (Join-Path $target $snapshotRelative.Replace('/',[IO.Path]::DirectorySeparatorChar)));evidence_grade='exact_predecessor_head_snapshot'})
    $entriesSorted=@($entries|Sort-Object category,path)
    $counts=[ordered]@{};foreach($category in $coverage){$counts[$category]=[long]@($entriesSorted|Where-Object{$_.category-ceq$category}).Count}
    if([long]$counts.problem-lt1){Stop-Build 'inventory_invalid' 'Artifact inventory has no problem entry.'}
    $authoritativeHeads=[Collections.Generic.List[object]]::new();$authoritativeHeads.Add((Raw-Pointer $target 'state/checkpoint.json'))
    if(Test-Path -LiteralPath (Join-Path $target 'manifests/legacy-semantic-manifest.json')){$authoritativeHeads.Add((Raw-Pointer $target 'manifests/legacy-semantic-manifest.json'))}
    $checkpointPointer=Raw-Pointer $target 'state/checkpoint.json'
    $handoffCandidates=@('handoffs/INITIAL-ARCHIVE-HANDOFF.md')+@(Get-ChildItem -LiteralPath (Join-Path $target 'handoffs') -File|Sort-Object Name -Descending|ForEach-Object{"handoffs/$($_.Name)"})
    $handoffRelative=@($handoffCandidates|Where-Object{Test-Path -LiteralPath (Join-Path $target $_.Replace('/',[IO.Path]::DirectorySeparatorChar))}|Select-Object -First 1)[0]
    $handoffPointer=if($null-eq$handoffRelative){$null}else{Raw-Pointer $target $handoffRelative}
    $index=[ordered]@{schema='math-research-inherited-artifact-index/v8';project_id=$projectId;predecessor_run_id=[string]$oldHead.active_run.id;source_snapshot=[ordered]@{primary_manifest_sha256=Get-FileSha256 (Join-Path $target "$($runResolved.Canonical.Replace('/',[IO.Path]::DirectorySeparatorChar))\run.json");backup_manifest_sha256=Get-FileSha256 (Join-Path $target "$($runResolved.Canonical.Replace('/',[IO.Path]::DirectorySeparatorChar))\run.json.bak");checkpoint_sha256=$checkpointPointer.sha256;handoff_sha256=if($handoffPointer){$handoffPointer.sha256}else{$null};authoritative_index_heads=@($authoritativeHeads)};inventory_algorithm='recursive byte inventory v1: strict non-reparse regular files sorted ordinal-ignore-case; original project.json represented by exact successor snapshot; generated successor artifacts excluded';covers=$coverage;entries=$entriesSorted;category_counts=$counts;entry_count=[long]$entriesSorted.Count;complete_source_inventory=$true}
    Write-CanonicalJson (Join-Path $target $indexRelative.Replace('/',[IO.Path]::DirectorySeparatorChar)) $index
    $indexPointer=Raw-Pointer $target $indexRelative

    $newContractPolicy=[ordered]@{schema_version=3;protocol='math-research-cycle-policy/v3';total_round_budget=[long]$config.total_round_budget;attempt_budget=[long]$config.attempt_budget;audit_interval_attempts=[long]$config.audit_interval_attempts;max_route_family_attempts_per_cycle=[long]$policy.max_route_family_attempts_per_cycle;max_repair_batches_per_attempt=[long]$policy.max_repair_batches_per_attempt;audit_roles=@('skeptic_quantifiers','skeptic_strategy','theory_tool_scout');allowed_worker_tools=@($allowedWorkerTools);max_ticket_tool_calls=32L;max_ticket_output_bytes=8388608L}
    if($legacyTickets.tickets-isnot[Collections.IList]-or@($legacyTickets.tickets).Count-lt1){Stop-Build 'ticket_source_invalid' 'Legacy initial tickets are empty.'}
    $legacyTicket=@($legacyTickets.tickets)[0]
    foreach($key in @('ticket_id','route_id','route_fingerprint_sha256','attempt_kind','route_family_id','mechanism_id','bottleneck_id','decision_question','search_domain','success_signal','stop_signal','resource_caps','reopen_condition')){if(-not$legacyTicket.Contains($key)){Stop-Build 'ticket_source_invalid' "Legacy initial ticket lacks $key."}}
    Assert-SafeId $legacyTicket.ticket_id 'initial ticket id';Assert-LowerSha256 $legacyTicket.route_fingerprint_sha256 'initial ticket route hash'
    $ticketId=[string]$legacyTicket.ticket_id;$ticketRelative="$newRunRelative/tickets/$ticketId-$generationName.json"
    $ticket=[ordered]@{ticket_id=$ticketId;role='solver';planned_lifecycle_slot='legacy_successor_initial';route_id=[string]$legacyTicket.route_id;route_fingerprint_sha256=[string]$legacyTicket.route_fingerprint_sha256;attempt_kind=[string]$legacyTicket.attempt_kind;route_family_id=[string]$legacyTicket.route_family_id;mechanism_id=[string]$legacyTicket.mechanism_id;bottleneck_id=[string]$legacyTicket.bottleneck_id;decision_question=[string]$legacyTicket.decision_question;input_artifacts=@((Raw-Pointer $target $problemRelative),$envelopePointer,$mappingPointer,$indexPointer);search_domain=[string]$legacyTicket.search_domain;success_signal=[string]$legacyTicket.success_signal;stop_signal=[string]$legacyTicket.stop_signal;allowed_tools=@($allowedWorkerTools);source_network_policy=[ordered]@{web=[string]$config.web_search;allowed_source_classes=@('primary_source','official_documentation');network_destinations=@()};filesystem_scope=[ordered]@{read_paths=@($problemRelative,$envelopeRelative,$mappingRelative,$indexRelative,$contractResolved.Canonical);writable_staging_path="$newRunRelative/staging/$ticketId/solver-1"};resource_caps=[ordered]@{child_agents=[long][Math]::Min([long]$config.max_child_agents,[long]$legacyTicket.resource_caps.child_agents);tool_calls=[long][Math]::Min([long]$legacyTicket.resource_caps.tool_calls,[long]$newContractPolicy.max_ticket_tool_calls);runtime_minutes=60L;max_output_bytes=[long]$newContractPolicy.max_ticket_output_bytes};dependencies=@();evidence_grade_required='proved_or_exact_computation';required_outputs=@([ordered]@{path='solver-report.md';schema='math-research-solver-report/v1';sha256_on_return='required'});failure_return=[ordered]@{schema='math-research-ticket-failure/v1';required_fields=@('status','failed_step','reason','partial_artifact_hashes','reopen_condition')};reopen_condition=[string]$legacyTicket.reopen_condition}
    $newTickets=[ordered]@{schema_version=3;cycle_id=[string]$legacyTickets.cycle_id;tickets=@($ticket)}
    $policyBody=$newContractPolicy|ConvertTo-Json -Depth 100 -Compress;$ticketsBody=$newTickets|ConvertTo-Json -Depth 100 -Compress
    $projectIdentity=if($payload.project.Contains('identity_sha256')){[string]$payload.project.identity_sha256}else{[string](Get-ContractMetadata $legacyContractText 'project_identity_sha256')};Assert-LowerSha256 $projectIdentity 'project identity'
    $problemHash=Get-FileSha256 (Join-Path $target $problemRelative.Replace('/',[IO.Path]::DirectorySeparatorChar))
    $metadataLines=@('schema: 8','goal_host_protocol: direct-current-task/v8','goal_binding_policy: direct-current-task/v8','goal_rebind_policy: external-host-bind-chain/v8','contract_version: v8','project_archive_schema: math-research-project/v8',"project_id: $projectId","project_directory_name: $(Split-Path -Leaf $target)","project_identity_sha256: $projectIdentity","model: $([string]$config.model)","reasoning_effort: $([string]$config.reasoning_effort)","approval_mode: $([string]$config.approval_mode)","web_search: $([string]$config.web_search)","audit_interval_attempts: $([long]$config.audit_interval_attempts)","attempt_budget: $([long]$config.attempt_budget)","total_round_budget: $([long]$config.total_round_budget)","max_child_agents: $([long]$config.max_child_agents)","max_total_agents: $([long]$config.max_total_agents)","max_runtime_minutes: $([long]$config.max_runtime_minutes)",'run_origin: legacy_successor',"inherited_counter_budget_baseline_sha256: $($baselinePointer.sha256)","problem_statement_sha256: $problemHash","cycle_policy_sha256: $(Get-TextSha256 $policyBody)","initial_tickets_sha256: $(Get-TextSha256 $ticketsBody)")
    $contractText=( @('# Math Research Goal-Host Contract v8','<!-- math-research-goal-host')+$metadataLines+@('-->','','<!-- math-research-cycle-policy',$policyBody,'-->','','<!-- math-research-initial-tickets',$ticketsBody,'-->','','## Legacy-successor binding','',"- Deterministic build intent: ``$intentRelative`` (``$($intentPointer.sha256)``)","- Effective predecessor envelope: ``$envelopeRelative`` (``$($envelopePointer.sha256)``)","- Control migration map: ``$mappingRelative`` (``$($mappingPointer.sha256)``)","- Inherited artifact index: ``$indexRelative`` (``$($indexPointer.sha256)``)","- Predecessor Contract: ``$($contractResolved.Canonical)`` (``$contractRawHash``)",'','## Preserved target, quantifiers, and completion','',$targetSection,$completionSection,'## Preserved assumptions and permissions','',$assumptionSection,$permissionSection,'## Control-plane retirement','','Legacy child Goal, launcher, Resume thread, dispatcher, daemon, heartbeat, lease, and controller files are evidence only. The current product Goal is the sole Goal Host; collaboration workers receive hash-bound tickets only.','') )-join"`n"
    Write-Utf8 (Join-Path $target $contractRelative.Replace('/',[IO.Path]::DirectorySeparatorChar)) $contractText
    $contractPointer=[ordered]@{path=$contractRelative;version='v8';binding_sha256=Get-NormalizedTextSha256 (Join-Path $target $contractRelative.Replace('/',[IO.Path]::DirectorySeparatorChar))}
    $runPointer=[ordered]@{id=$newRunId;path=$newRunRelative;status='not_started'}
    $hostGoal=[ordered]@{thread_id_available=$goalThreadAvailable;thread_id=$goalThreadValue;objective_raw_sha256=$goalHash}
    $hostBinding=[ordered]@{schema='math-research-host-binding/v8';project_id=$projectId;control_generation=$newGeneration;event_type='HOST_BIND';prior_host_binding=$null;retirement=$null;contract=$contractPointer;run=[ordered]@{id=$newRunId;path=$newRunRelative};host_goal=$hostGoal}
    Write-CanonicalJson (Join-Path $target $hostRelative.Replace('/',[IO.Path]::DirectorySeparatorChar)) $hostBinding
    $hostPointer=Generation-Pointer $target $hostRelative $newGeneration
    $runGenesis=[ordered]@{schema='math-research-run-genesis/v8';project_id=$projectId;control_generation=$newGeneration;contract=$contractPointer;run=$runPointer;host_binding=[ordered]@{path=$hostPointer.path;sha256=$hostPointer.sha256};host_goal=$hostGoal}
    Write-CanonicalJson (Join-Path $target "$newRunRelative/run.json".Replace('/',[IO.Path]::DirectorySeparatorChar)) $runGenesis

    $lineage=[ordered]@{schema='math-research-legacy-successor-lineage/v8';project_id=$projectId;control_generation=$newGeneration;legacy_goal_bindings_obsolete=$true;predecessor=[ordered]@{project_head_snapshot=Raw-Pointer $target $snapshotRelative;run_id=[string]$oldHead.active_run.id;run_path=$runResolved.Canonical;contract=[ordered]@{path=$contractResolved.Canonical;sha256=$contractRawHash};primary_manifest=Raw-Pointer $target "$($runResolved.Canonical)/run.json";backup_manifest=Raw-Pointer $target "$($runResolved.Canonical)/run.json.bak";checkpoint=$checkpointPointer;handoff=$handoffPointer};inherited_artifact_index=$indexPointer;inherited_counter_budget_baseline=$baselinePointer;successor=[ordered]@{contract=[ordered]@{path=$contractPointer.path;binding_sha256=$contractPointer.binding_sha256};run_id=$newRunId;run_path=$newRunRelative;run_genesis=Raw-Pointer $target "$newRunRelative/run.json";host_bind=[ordered]@{path=$hostPointer.path;sha256=$hostPointer.sha256}}}
    Write-CanonicalJson (Join-Path $target $lineageRelative.Replace('/',[IO.Path]::DirectorySeparatorChar)) $lineage
    $lineagePointer=Generation-Pointer $target $lineageRelative $newGeneration
    $successorSummary=[ordered]@{lineage=[ordered]@{path=$lineagePointer.path;sha256=$lineagePointer.sha256};inherited_artifact_index=$indexPointer;counter_budget_baseline=$baselinePointer}

    $frozenTicket=[ordered]@{schema='math-research-frozen-ticket/v8';project_id=$projectId;control_generation=$newGeneration;contract=$contractPointer;run=$runPointer;cycle_id=[string]$newTickets.cycle_id;contract_initial_tickets_sha256=Get-TextSha256 $ticketsBody;counter_snapshot=$counters;ticket=$ticket}
    Write-CanonicalJson (Join-Path $target $ticketRelative.Replace('/',[IO.Path]::DirectorySeparatorChar)) $frozenTicket
    $ticketHash=Get-FileSha256 (Join-Path $target $ticketRelative.Replace('/',[IO.Path]::DirectorySeparatorChar))
    $ticketPointer=[ordered]@{id=$ticketId;path=$ticketRelative;sha256=$ticketHash;status='ready';contract_initial_tickets_sha256=Get-TextSha256 $ticketsBody;counter_snapshot=[ordered]@{attempt_count=$counters.attempt_count;audit_count=$counters.audit_count;total_round_count=$counters.total_round_count};source_event=$null}
    $timestamp=$frozenUtc
    $eventId="LEGACY_SUCCESSOR-$generationName";Assert-SafeId $eventId 'event id'
    $event=[ordered]@{schema='math-research-project-event/v8';project_id=$projectId;control_generation=$newGeneration;event_id=$eventId;event_type='LEGACY_SUCCESSOR';updated_at_utc=$timestamp;previous_event_sha256=$null;contract=$contractPointer;run=$runPointer;counters=$counters;referenced_artifacts=@($intentPointer,$envelopePointer,$mappingPointer,$indexPointer,$baselinePointer,[ordered]@{path=$lineagePointer.path;sha256=$lineagePointer.sha256})}
    Write-CanonicalJson (Join-Path $target $eventRelative.Replace('/',[IO.Path]::DirectorySeparatorChar)) $event
    $eventPointer=Generation-Pointer $target $eventRelative $newGeneration
    $checkpoint=[ordered]@{schema='math-research-checkpoint/v8';project_id=$projectId;control_generation=$newGeneration;contract=$contractPointer;run=$runPointer;problem_statement_sha256=$problemHash;host_goal=$hostGoal;host_binding_head=[ordered]@{path=$hostPointer.path;sha256=$hostPointer.sha256};counters=$counters;current_lifecycle=[ordered]@{kind='initial_ticket';id=$ticketId;path=$ticketRelative;sha256=$ticketHash};successor=$successorSummary;completion_ready=$false;pending_goal_update=$false;last_run_event=[ordered]@{id=$eventId;sha256=$eventPointer.sha256};updated_at_utc=$timestamp}
    $state=[ordered]@{schema='math-research-goal-host-state/v8';project_id=$projectId;control_generation=$newGeneration;contract=$contractPointer;run=$runPointer;host_goal=$hostGoal;problem_statement_sha256=$problemHash;successor=$successorSummary;counters=$counters;current_ticket=$ticketPointer;updated_at_utc=$timestamp}
    Write-CanonicalJson (Join-Path $target $checkpointRelative.Replace('/',[IO.Path]::DirectorySeparatorChar)) $checkpoint
    Write-CanonicalJson (Join-Path $target $stateRelative.Replace('/',[IO.Path]::DirectorySeparatorChar)) $state
    $head=[ordered]@{schema='math-research-project/v8';project_id=$projectId;project_identity_sha256=$projectIdentity;problem_statement_sha256=$problemHash;control_generation=$newGeneration;active_checkpoint=Generation-Pointer $target $checkpointRelative $newGeneration;goal_host_state=Generation-Pointer $target $stateRelative $newGeneration;project_event_head=$eventPointer;host_binding_head=$hostPointer;active_contract=$contractPointer;active_run=$runPointer;legacy_successor=$lineagePointer}
    Write-CanonicalJson (Join-Path $target $candidateRelative.Replace('/',[IO.Path]::DirectorySeparatorChar)) $head
    if((Get-FileSha256 (Join-Path $target 'project.json'))-cne$oldHash){Stop-Build 'head_mutated' 'Staging unexpectedly changed project.json.'}
    $result.built=$true;$result.reason=if($intentExisted){'reused_staging_ready_for_goal_gated_commit'}else{'staged_successor_ready_for_goal_gated_commit'};$result.candidate_head_file=Join-Path $target $candidateRelative.Replace('/',[IO.Path]::DirectorySeparatorChar);$result.candidate_head_sha256=Get-FileSha256 $result.candidate_head_file;$result.effective_envelope=$envelopePointer;$result.migration_map=$mappingPointer;$result.inherited_artifact_count=[long]$entriesSorted.Count
    $result.source_project_tree_sha256_after=Get-TreeHash $source
    if($target-cne$source){
        if($result.source_project_tree_sha256_after-cne$result.source_project_tree_sha256_before){Stop-Build 'source_mutated' 'The external source project tree changed during copied staging.'}
    }
    else {
        foreach($relative in $predecessorHashes.Keys){$path=Join-Path $source $relative.Replace('/',[IO.Path]::DirectorySeparatorChar);if(-not(Test-Path -LiteralPath $path -PathType Leaf)-or(Get-FileSha256 $path)-cne[string]$predecessorHashes[$relative]){Stop-Build 'predecessor_mutated' "A predecessor file changed during additive staging: $relative"}}
        $newFiles=@(Get-ChildItem -LiteralPath $source -Recurse -File -Force|ForEach-Object{$_.FullName.Substring($source.Length+1).Replace('\','/')}|Where-Object{-not$predecessorHashes.Contains($_)}|Sort-Object)
        $expectedNew=@($generatedFiles|Sort-Object)
        if(($newFiles-join'|')-cne($expectedNew-join'|')){Stop-Build 'unexpected_staging_write' "Additive staging wrote an unexpected file set. observed=$($newFiles-join',')"}
    }
    $result|ConvertTo-Json -Depth 16 -Compress
    exit 0
}
catch {
    $message=$_.Exception.Message;$code='build_failed'
    if($message-match'^\[(?<code>[a-z0-9_]+)\]\s*(?<detail>.*)$'){$code=$Matches['code'];$message=$Matches['detail']}
    $result.reason=$code;$result.detail=$message
    try{if($null-ne$result.source_project-and(Test-Path -LiteralPath $result.source_project -PathType Container)){$result.source_project_tree_sha256_after=Get-TreeHash $result.source_project}}catch{}
    $result|ConvertTo-Json -Depth 16 -Compress
    exit 1
}
