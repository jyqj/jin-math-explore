Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

if ($null -eq (Get-Command Read-SignedJsonPayload -ErrorAction SilentlyContinue)) {
    Import-Module (Join-Path $PSScriptRoot 'MathResearchLauncherLegacyV1Compat.psm1') -DisableNameChecking
}
if ($null -eq (Get-Command Assert-MathResearchLegacyV1CompatState -ErrorAction SilentlyContinue)) {
    Import-Module (Join-Path $PSScriptRoot 'MathResearchLegacyV1CompatMigration.psm1') -DisableNameChecking
}

function Assert-ControlPathUniqueJsonPropertiesV2 {
    param([Parameter(Mandatory = $true)][Text.Json.JsonElement]$Element, [Parameter(Mandatory = $true)][string]$Path)
    if ($Element.ValueKind -eq [Text.Json.JsonValueKind]::Object) {
        $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        foreach ($property in $Element.EnumerateObject()) {
            if (-not $seen.Add($property.Name)) { throw "Duplicate JSON property '$($property.Name)' at $Path." }
            Assert-ControlPathUniqueJsonPropertiesV2 -Element $property.Value -Path "$Path.$($property.Name)"
        }
    }
    elseif ($Element.ValueKind -eq [Text.Json.JsonValueKind]::Array) {
        $index = 0
        foreach ($item in $Element.EnumerateArray()) { Assert-ControlPathUniqueJsonPropertiesV2 -Element $item -Path "$Path[$index]"; $index++ }
    }
}

function Read-MathResearchLegacyV1ControlPathReceiptV2 {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    $path = Assert-NoReparsePointChain -LiteralPath ([IO.Path]::GetFullPath($LiteralPath))
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Control-path amendment receipt is missing: $path" }
    $bytes = [IO.File]::ReadAllBytes($path)
    $text = [Text.UTF8Encoding]::new($false, $true).GetString($bytes)
    $options = [Text.Json.JsonDocumentOptions]::new()
    $options.AllowTrailingCommas = $false; $options.CommentHandling = [Text.Json.JsonCommentHandling]::Disallow; $options.MaxDepth = 64
    try { $document = [Text.Json.JsonDocument]::Parse($text, $options) }
    catch { throw "Control-path amendment receipt is not strict JSON: $($_.Exception.Message)" }
    try {
        if ($document.RootElement.ValueKind -ne [Text.Json.JsonValueKind]::Object) { throw 'Control-path amendment receipt must be a JSON object.' }
        Assert-ControlPathUniqueJsonPropertiesV2 -Element $document.RootElement -Path '$'
    }
    finally { $document.Dispose() }
    return [pscustomobject]@{ Path=$path; Text=$text; Value=($text | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String); RawSha256=Get-Sha256HexFromBytes -Bytes $bytes }
}

function Assert-ControlPathHashV2 {
    param([Parameter(Mandatory = $true)][string]$Value,[Parameter(Mandatory = $true)][string]$Label)
    if ($Value -cnotmatch '^[0-9a-f]{64}$') { throw "$Label must be a lowercase SHA-256." }
}

function Assert-ControlPathFileBindingV2 {
    param([Parameter(Mandatory = $true)][Collections.IDictionary]$Binding,[Parameter(Mandatory = $true)][string]$ExpectedPath,[Parameter(Mandatory = $true)][string]$Label)
    if (-not $Binding.Contains('path') -or -not $Binding.Contains('sha256')) { throw "$Label binding is incomplete." }
    $actual = [IO.Path]::GetFullPath($ExpectedPath); $bound = [IO.Path]::GetFullPath([string]$Binding.path)
    if (-not $actual.Equals($bound,[StringComparison]::OrdinalIgnoreCase)) { throw "$Label path differs from the receipt." }
    Assert-NoReparsePointChain -LiteralPath $actual | Out-Null
    Assert-ControlPathHashV2 -Value ([string]$Binding.sha256) -Label "$Label sha256"
    if ((Get-Sha256HexFromFile -LiteralPath $actual) -cne [string]$Binding.sha256) { throw "$Label bytes differ from the receipt." }
}

function Assert-ControlPathCountersV2 {
    param([Parameter(Mandatory = $true)][Collections.IDictionary]$Snapshot,[Parameter(Mandatory = $true)][Collections.IDictionary]$Checkpoint,[switch]$AllowMonotoneAdvance)
    foreach($key in @('head_sequence','head_payload_sha256','attempt_count','audit_count','total_round_count','attempts_since_last_audit','audit_due')) { if(-not $Snapshot.Contains($key)){throw "Control-path receipt counter snapshot is missing $key."} }
    Assert-ControlPathHashV2 -Value ([string]$Snapshot.head_payload_sha256) -Label 'control-path source head hash'
    if($AllowMonotoneAdvance){
        foreach($key in @('head_sequence','attempt_count','audit_count','total_round_count')){if([int64]$Checkpoint[$key]-lt[int64]$Snapshot[$key]){throw "Control-path amendment detected counter rollback at $key."}}
    }
    else { foreach($key in @('head_sequence','head_payload_sha256','attempt_count','audit_count','total_round_count','attempts_since_last_audit','audit_due')){if([string]$Checkpoint[$key]-cne[string]$Snapshot[$key]){throw "Control-path amendment source counter mismatch at $key."}} }
}

function Assert-MathResearchLegacyV1ControlPathAmendmentV2State {
    param(
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Manifest,
        [Parameter(Mandatory = $true)][string]$RunPath,
        [Parameter(Mandatory = $true)]$ReceiptRead,
        [Parameter(Mandatory = $true)]$PriorReceiptRead,
        [Parameter(Mandatory = $true)][hashtable]$Paths,
        [switch]$RequireApplied
    )
    $receipt=$ReceiptRead.Value
    if([int]$receipt.schema_version-ne 1-or[string]$receipt.protocol-cne'math-research-legacy-v1-control-path-amendment/v2'){throw 'Unsupported control-path amendment receipt protocol.'}
    foreach($section in @('project','run','contract','goal','prior_migration','source','target','authorization')){if(-not$receipt.Contains($section)-or$receipt[$section]-isnot[Collections.IDictionary]){throw "Control-path amendment receipt is missing $section."}}
    if([string]$receipt.action-cne'omit_explicit_sandbox_with_approve_for_me'-or[string]$receipt.amendment_id-notmatch'^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$'){throw 'Control-path amendment action or id is invalid.'}
    $runFull=[IO.Path]::GetFullPath($RunPath)
    if(-not([IO.Path]::GetFullPath([string]$receipt.run.directory)).Equals($runFull,[StringComparison]::OrdinalIgnoreCase)){throw 'Control-path run directory mismatch.'}
    if([string]$Manifest.run_id-cne[string]$receipt.run.id-or[string]$Manifest.thread_id-cne[string]$receipt.run.thread_id){throw 'Control-path run or thread identity mismatch.'}
    if([string]$Manifest.project.project_id-cne[string]$receipt.project.project_id-or-not([IO.Path]::GetFullPath([string]$Manifest.project.directory)).Equals([IO.Path]::GetFullPath([string]$receipt.project.directory),[StringComparison]::OrdinalIgnoreCase)){throw 'Control-path project identity mismatch.'}
    if([string]$Manifest.contract_version-cne[string]$receipt.contract.version-or[string]$Manifest.cycle_ledger.contract_binding_sha256-cne[string]$receipt.contract.binding_sha256){throw 'Control-path contract binding mismatch.'}
    if([string]$Manifest.goal.objective_sha256-cne[string]$receipt.goal.objective_sha256){throw 'Control-path Goal objective mismatch.'}
    if([string]$PriorReceiptRead.RawSha256-cne[string]$receipt.prior_migration.receipt_sha256-or[string]$Manifest.compatibility_migration.receipt_sha256-cne[string]$receipt.prior_migration.receipt_sha256){throw 'Control-path prior migration binding mismatch.'}
    if([string]$receipt.authorization.approval_mode-cne'approve_for_me'-or[string]$receipt.authorization.effective_sandbox-cne'workspace-write'-or-not[bool]$receipt.authorization.explicit_sandbox_argument_omitted-or[bool]$receipt.authorization.objective_changed-or[bool]$receipt.authorization.quantifiers_changed-or[bool]$receipt.authorization.counters_reset-or[bool]$receipt.authorization.permission_scope_expanded){throw 'Control-path amendment authorization envelope is invalid.'}

    Assert-MathResearchLegacyV1CompatState -Manifest $Manifest -RunPath $runFull -ReceiptRead $PriorReceiptRead -LauncherEntryPath $Paths.PriorLauncherEntry -LauncherModulePath $Paths.LauncherModule -CycleModulePath $Paths.CycleModule -CycleCliPath $Paths.CycleCli -ProjectModulePath $Paths.ProjectModule -CanaryHostPath $Paths.PriorCanaryHost -CanaryEntryPath $Paths.CanaryEntry -RequireApplied | Out-Null
    foreach($item in @(
        @('launcher_entry',$Paths.LauncherEntry,'control-path launcher entry'),
        @('launcher_module',$Paths.LauncherModule,'legacy launcher module'),
        @('argv_compat_module',$Paths.ArgvCompatModule,'argv compatibility module'),
        @('canary_host',$Paths.CanaryHost,'control-path canary host'),
        @('canary_module',$Paths.CanaryModule,'v2 canary module'),
        @('canary_entry',$Paths.CanaryEntry,'installed canary entry'),
        @('cycle_cli',$Paths.CycleCli,'compatibility cycle CLI'),
        @('amendment_module',$Paths.AmendmentModule,'control-path amendment module'),
        @('amendment_cli',$Paths.AmendmentCli,'control-path amendment CLI'))){Assert-ControlPathFileBindingV2 -Binding $receipt.target[$item[0]] -ExpectedPath $item[1] -Label $item[2]}
    Assert-ControlPathCountersV2 -Snapshot $receipt.source.counters -Checkpoint $Manifest.cycle_ledger.checkpoint -AllowMonotoneAdvance:$RequireApplied
    if(-not$RequireApplied){return $true}
    $record=$Manifest.control_path_amendment_v2
    if($record-isnot[Collections.IDictionary]-or[string]$record.protocol-cne[string]$receipt.protocol-or[string]$record.amendment_id-cne[string]$receipt.amendment_id-or[string]$record.receipt_sha256-cne[string]$ReceiptRead.RawSha256){throw 'Signed manifest is not bound to this control-path amendment receipt.'}
    $archive=Join-Path $runFull ([string]$receipt.archive_directory_name)
    if(-not(Test-Path -LiteralPath $archive -PathType Container)){throw 'Control-path source archive is missing.'}
    foreach($item in @(@('pre-amendment-run.json',[string]$receipt.source.manifest_primary_sha256),@('pre-amendment-run.json.bak',[string]$receipt.source.manifest_backup_sha256),@('control-path-receipt.json',[string]$ReceiptRead.RawSha256))){Assert-ControlPathHashV2 -Value $item[1] -Label "archive $($item[0])";$path=Join-Path $archive $item[0];if(-not(Test-Path -LiteralPath $path -PathType Leaf)-or(Get-Sha256HexFromFile -LiteralPath $path)-cne$item[1]){throw "Control-path source archive mismatch: $($item[0])"}}
    return $true
}

function Write-ControlPathArchiveFileV2 {
    param([string]$Source,[string]$Destination,[string]$ExpectedSha256)
    Assert-ControlPathHashV2 -Value $ExpectedSha256 -Label 'archive expected sha256'
    if(Test-Path -LiteralPath $Destination -PathType Leaf){if((Get-Sha256HexFromFile -LiteralPath $Destination)-cne$ExpectedSha256){throw "Control-path archive conflict: $Destination"};return}
    $bytes=[IO.File]::ReadAllBytes($Source);try{$stream=[IO.FileStream]::new($Destination,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None);try{$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}}finally{[Array]::Clear($bytes,0,$bytes.Length)}
    if((Get-Sha256HexFromFile -LiteralPath $Destination)-cne$ExpectedSha256){throw "Control-path archive write verification failed: $Destination"}
}

function Invoke-MathResearchLegacyV1ControlPathAmendmentV2 {
    param([ValidateSet('Analyze','Apply','Verify')][string]$Action,[string]$RunDirectory,[string]$ReceiptFile,[string]$PriorReceiptFile,[hashtable]$Paths)
    $runPath=Assert-NoReparsePointChain -LiteralPath ([IO.Path]::GetFullPath($RunDirectory));$manifestPath=Join-Path $runPath 'run.json';$receiptRead=Read-MathResearchLegacyV1ControlPathReceiptV2 -LiteralPath $ReceiptFile;$priorRead=Read-MathResearchLegacyV1CompatReceipt -LiteralPath $PriorReceiptFile;$lease=$null;$leaseFile=$null
    try{
        $lease=Enter-NamedLease -Kind run -Value $runPath;$leaseFile=Open-RunLeaseFile -RunDirectory $runPath;$manifest=(Read-SignedJsonPayload -LiteralPath $manifestPath).Payload
        if($manifest.Contains('control_path_amendment_v2')){Assert-MathResearchLegacyV1ControlPathAmendmentV2State -Manifest $manifest -RunPath $runPath -ReceiptRead $receiptRead -PriorReceiptRead $priorRead -Paths $Paths -RequireApplied|Out-Null;return [pscustomobject]@{Ok=$true;Action=$Action;Status='already_applied';RunId=$manifest.run_id;ThreadId=$manifest.thread_id;ReceiptSha256=$receiptRead.RawSha256;AttemptCount=[int]$manifest.cycle_ledger.checkpoint.attempt_count;TotalRoundCount=[int]$manifest.cycle_ledger.checkpoint.total_round_count}}
        Assert-MathResearchLegacyV1ControlPathAmendmentV2State -Manifest $manifest -RunPath $runPath -ReceiptRead $receiptRead -PriorReceiptRead $priorRead -Paths $Paths|Out-Null
        if($Action-eq'Verify'){throw 'Control-path amendment has not been applied.'}
        if([string]$manifest.status-cne[string]$receiptRead.Value.source.status){throw 'Control-path amendment source status mismatch.'}
        if(Test-ProcessIdentityFromManifest -ProcessRecord $manifest.process){throw 'Control-path amendment refuses a live Codex process.'}
        foreach($key in @('manifest_primary_sha256','manifest_backup_sha256')){Assert-ControlPathHashV2 -Value ([string]$receiptRead.Value.source[$key]) -Label "source $key"}
        if((Get-Sha256HexFromFile -LiteralPath $manifestPath)-cne[string]$receiptRead.Value.source.manifest_primary_sha256-or(Get-Sha256HexFromFile -LiteralPath "$manifestPath.bak")-cne[string]$receiptRead.Value.source.manifest_backup_sha256){throw 'Control-path amendment source manifest bytes differ from the receipt.'}
        if($Action-eq'Analyze'){return [pscustomobject]@{Ok=$true;Action=$Action;Status='ready_to_apply';RunId=$manifest.run_id;ThreadId=$manifest.thread_id;ReceiptSha256=$receiptRead.RawSha256;AttemptCount=[int]$manifest.cycle_ledger.checkpoint.attempt_count;TotalRoundCount=[int]$manifest.cycle_ledger.checkpoint.total_round_count}}
        $archive=Join-Path $runPath ([string]$receiptRead.Value.archive_directory_name);if(-not(Test-Path -LiteralPath $archive)){[IO.Directory]::CreateDirectory($archive)|Out-Null};Assert-NoReparsePointChain -LiteralPath $archive|Out-Null
        Write-ControlPathArchiveFileV2 -Source $manifestPath -Destination (Join-Path $archive 'pre-amendment-run.json') -ExpectedSha256 ([string]$receiptRead.Value.source.manifest_primary_sha256)
        Write-ControlPathArchiveFileV2 -Source "$manifestPath.bak" -Destination (Join-Path $archive 'pre-amendment-run.json.bak') -ExpectedSha256 ([string]$receiptRead.Value.source.manifest_backup_sha256)
        Write-ControlPathArchiveFileV2 -Source $receiptRead.Path -Destination (Join-Path $archive 'control-path-receipt.json') -ExpectedSha256 $receiptRead.RawSha256
        $manifest['control_path_amendment_v2']=[ordered]@{schema_version=1;protocol=[string]$receiptRead.Value.protocol;amendment_id=[string]$receiptRead.Value.amendment_id;receipt_sha256=$receiptRead.RawSha256;source_manifest_primary_sha256=[string]$receiptRead.Value.source.manifest_primary_sha256;source_manifest_backup_sha256=[string]$receiptRead.Value.source.manifest_backup_sha256;source_counters=$receiptRead.Value.source.counters;approval_mode='approve_for_me';effective_sandbox='workspace-write';explicit_sandbox_argument_omitted=$true;objective_changed=$false;quantifiers_changed=$false;counters_reset=$false;permission_scope_expanded=$false;applied_at_utc=Get-UtcNowString}
        $manifest.revision=[int]$manifest.revision+1;$manifest.updated_at_utc=Get-UtcNowString;$manifest.exit_reason='control_path_amendment_v2_applied_ready_to_resume';Write-SignedJsonPayload -LiteralPath $manifestPath -Payload $manifest
        $readBack=(Read-SignedJsonPayload -LiteralPath $manifestPath).Payload;Assert-MathResearchLegacyV1ControlPathAmendmentV2State -Manifest $readBack -RunPath $runPath -ReceiptRead $receiptRead -PriorReceiptRead $priorRead -Paths $Paths -RequireApplied|Out-Null
        return [pscustomobject]@{Ok=$true;Action=$Action;Status='applied';RunId=$readBack.run_id;ThreadId=$readBack.thread_id;ReceiptSha256=$receiptRead.RawSha256;AttemptCount=[int]$readBack.cycle_ledger.checkpoint.attempt_count;TotalRoundCount=[int]$readBack.cycle_ledger.checkpoint.total_round_count}
    }finally{if($leaseFile){$leaseFile.Dispose()};Exit-NamedLease -Lease $lease}
}

Export-ModuleMember -Function @('Read-MathResearchLegacyV1ControlPathReceiptV2','Assert-MathResearchLegacyV1ControlPathAmendmentV2State','Invoke-MathResearchLegacyV1ControlPathAmendmentV2')
