Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

$compatLauncherModule = Join-Path $PSScriptRoot 'MathResearchLauncherLegacyV1Compat.psm1'
if ($null -eq (Get-Command Read-SignedJsonPayload -ErrorAction SilentlyContinue)) {
    Import-Module $compatLauncherModule -DisableNameChecking
}

function Assert-CompatUniqueJsonProperties {
    param([Parameter(Mandatory = $true)][Text.Json.JsonElement]$Element, [Parameter(Mandatory = $true)][string]$Path)
    if ($Element.ValueKind -eq [Text.Json.JsonValueKind]::Object) {
        $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        foreach ($property in $Element.EnumerateObject()) {
            if (-not $seen.Add($property.Name)) { throw "Duplicate JSON property '$($property.Name)' at $Path." }
            Assert-CompatUniqueJsonProperties -Element $property.Value -Path "$Path.$($property.Name)"
        }
    }
    elseif ($Element.ValueKind -eq [Text.Json.JsonValueKind]::Array) {
        $index = 0
        foreach ($item in $Element.EnumerateArray()) {
            Assert-CompatUniqueJsonProperties -Element $item -Path "$Path[$index]"
            $index++
        }
    }
}

function Read-MathResearchLegacyV1CompatReceipt {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    $path = Assert-NoReparsePointChain -LiteralPath ([IO.Path]::GetFullPath($LiteralPath))
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Compatibility migration receipt is missing: $path" }
    $bytes = [IO.File]::ReadAllBytes($path)
    $text = [Text.UTF8Encoding]::new($false, $true).GetString($bytes)
    $options = [Text.Json.JsonDocumentOptions]::new()
    $options.AllowTrailingCommas = $false
    $options.CommentHandling = [Text.Json.JsonCommentHandling]::Disallow
    $options.MaxDepth = 64
    try { $document = [Text.Json.JsonDocument]::Parse($text, $options) }
    catch { throw "Compatibility migration receipt is not strict JSON: $($_.Exception.Message)" }
    try {
        if ($document.RootElement.ValueKind -ne [Text.Json.JsonValueKind]::Object) { throw 'Compatibility migration receipt must be a JSON object.' }
        Assert-CompatUniqueJsonProperties -Element $document.RootElement -Path '$'
    }
    finally { $document.Dispose() }
    $value = $text | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    return [pscustomobject]@{
        Path = $path
        Text = $text
        Value = $value
        RawSha256 = Get-Sha256HexFromBytes -Bytes $bytes
    }
}

function Assert-CompatHash {
    param([Parameter(Mandatory = $true)][string]$Value, [Parameter(Mandatory = $true)][string]$Label)
    if ($Value -cnotmatch '^[0-9a-f]{64}$') { throw "$Label must be a lowercase SHA-256." }
}

function Assert-CompatFileBinding {
    param(
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Binding,
        [Parameter(Mandatory = $true)][string]$ExpectedPath,
        [Parameter(Mandatory = $true)][string]$Label
    )
    if (-not $Binding.Contains('path') -or -not $Binding.Contains('sha256')) { throw "$Label binding is incomplete." }
    $boundPath = [IO.Path]::GetFullPath([string]$Binding.path)
    $actualPath = [IO.Path]::GetFullPath($ExpectedPath)
    if (-not $boundPath.Equals($actualPath, [StringComparison]::OrdinalIgnoreCase)) { throw "$Label path differs from the receipt." }
    Assert-NoReparsePointChain -LiteralPath $actualPath | Out-Null
    Assert-CompatHash -Value ([string]$Binding.sha256) -Label "$Label sha256"
    if ((Get-Sha256HexFromFile -LiteralPath $actualPath) -cne [string]$Binding.sha256) { throw "$Label bytes differ from the receipt." }
}

function Assert-CompatCounterSnapshot {
    param(
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Snapshot,
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Checkpoint,
        [switch]$AllowMonotoneAdvance
    )
    foreach ($key in @('head_sequence','head_payload_sha256','attempt_count','audit_count','total_round_count','attempts_since_last_audit','audit_due')) {
        if (-not $Snapshot.Contains($key)) { throw "Compatibility receipt counter snapshot is missing $key." }
    }
    Assert-CompatHash -Value ([string]$Snapshot.head_payload_sha256) -Label 'source counters head_payload_sha256'
    if ($AllowMonotoneAdvance) {
        foreach ($key in @('head_sequence','attempt_count','audit_count','total_round_count')) {
            if ([int64]$Checkpoint[$key] -lt [int64]$Snapshot[$key]) { throw "Compatibility migration detected a counter rollback at $key." }
        }
        return
    }
    foreach ($key in @('head_sequence','head_payload_sha256','attempt_count','audit_count','total_round_count','attempts_since_last_audit','audit_due')) {
        if ([string]$Checkpoint[$key] -cne [string]$Snapshot[$key]) { throw "Compatibility migration source counter mismatch at $key." }
    }
}

function Assert-MathResearchLegacyV1CompatState {
    param(
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Manifest,
        [Parameter(Mandatory = $true)][string]$RunPath,
        [Parameter(Mandatory = $true)]$ReceiptRead,
        [Parameter(Mandatory = $true)][string]$LauncherEntryPath,
        [Parameter(Mandatory = $true)][string]$LauncherModulePath,
        [Parameter(Mandatory = $true)][string]$CycleModulePath,
        [Parameter(Mandatory = $true)][string]$CycleCliPath,
        [Parameter(Mandatory = $true)][string]$ProjectModulePath,
        [Parameter(Mandatory = $true)][string]$CanaryHostPath,
        [Parameter(Mandatory = $true)][string]$CanaryEntryPath,
        [switch]$RequireApplied
    )
    $receipt = $ReceiptRead.Value
    if ([int]$receipt.schema_version -ne 1 -or [string]$receipt.protocol -cne 'math-research-legacy-v1-compat-migration/v1') {
        throw 'Unsupported compatibility migration receipt protocol.'
    }
    foreach ($section in @('project','run','contract','goal','source','target','authorization')) {
        if (-not $receipt.Contains($section) -or $receipt[$section] -isnot [Collections.IDictionary]) { throw "Compatibility migration receipt is missing $section." }
    }
    if ([string]$receipt.action -cne 'resume_prompt_v6_with_compat_bundle' -or [string]$receipt.migration_id -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$') {
        throw 'Compatibility migration receipt action or migration_id is invalid.'
    }
    $runFull = [IO.Path]::GetFullPath($RunPath)
    if (-not ([IO.Path]::GetFullPath([string]$receipt.run.directory)).Equals($runFull, [StringComparison]::OrdinalIgnoreCase)) { throw 'Compatibility receipt run directory mismatch.' }
    if ([string]$Manifest.run_id -cne [string]$receipt.run.id -or [string]$Manifest.thread_id -cne [string]$receipt.run.thread_id) { throw 'Compatibility receipt run or thread identity mismatch.' }
    if ([string]$Manifest.project.project_id -cne [string]$receipt.project.project_id -or -not ([IO.Path]::GetFullPath([string]$Manifest.project.directory)).Equals([IO.Path]::GetFullPath([string]$receipt.project.directory), [StringComparison]::OrdinalIgnoreCase)) { throw 'Compatibility receipt project identity mismatch.' }
    if ([string]$Manifest.contract_version -cne [string]$receipt.contract.version -or [string]$Manifest.cycle_ledger.contract_binding_sha256 -cne [string]$receipt.contract.binding_sha256) { throw 'Compatibility receipt contract binding mismatch.' }
    Assert-CompatHash -Value ([string]$receipt.contract.binding_sha256) -Label 'contract binding'
    if ([string]$Manifest.goal.objective_sha256 -cne [string]$receipt.goal.objective_sha256) { throw 'Compatibility receipt Goal objective mismatch.' }
    if ([string]$Manifest.prompt_version -cne 'v6' -or [int]$Manifest.schema_version -ne 1) { throw 'Compatibility migration accepts only a signed schema-1 Prompt v6 manifest.' }
    if ([string]$receipt.authorization.approval_mode_from -cne 'never' -or [string]$receipt.authorization.approval_mode_to -cne 'approve_for_me' -or
        [bool]$receipt.authorization.objective_changed -or [bool]$receipt.authorization.quantifiers_changed -or [bool]$receipt.authorization.counters_reset) {
        throw 'Compatibility migration authorization envelope is invalid.'
    }
    Assert-CompatFileBinding -Binding $receipt.target.launcher_entry -ExpectedPath $LauncherEntryPath -Label 'compat launcher entry'
    Assert-CompatFileBinding -Binding $receipt.target.launcher_module -ExpectedPath $LauncherModulePath -Label 'compat launcher module'
    Assert-CompatFileBinding -Binding $receipt.target.cycle_module -ExpectedPath $CycleModulePath -Label 'compat cycle module'
    Assert-CompatFileBinding -Binding $receipt.target.cycle_cli -ExpectedPath $CycleCliPath -Label 'compat cycle CLI'
    Assert-CompatFileBinding -Binding $receipt.target.project_module -ExpectedPath $ProjectModulePath -Label 'project module'
    Assert-CompatFileBinding -Binding $receipt.target.canary_host -ExpectedPath $CanaryHostPath -Label 'compat canary host'
    Assert-CompatFileBinding -Binding $receipt.target.canary_entry -ExpectedPath $CanaryEntryPath -Label 'installed canary entry'
    foreach ($bindingName in @('launcher_entry','launcher_module','cycle_module','cycle_cli','project_module')) {
        $binding = $receipt.source[$bindingName]
        if ($binding -isnot [Collections.IDictionary]) { throw "Compatibility source binding $bindingName is missing." }
        Assert-CompatFileBinding -Binding $binding -ExpectedPath ([string]$binding.path) -Label "source $bindingName"
    }
    if ($receipt.source.counters -isnot [Collections.IDictionary]) { throw 'Compatibility source counter snapshot is missing.' }
    Assert-CompatCounterSnapshot -Snapshot $receipt.source.counters -Checkpoint $Manifest.cycle_ledger.checkpoint -AllowMonotoneAdvance:$RequireApplied
    if (-not $RequireApplied) { return $true }

    if ($Manifest.compatibility_migration -isnot [Collections.IDictionary] -or
        [string]$Manifest.compatibility_migration.protocol -cne [string]$receipt.protocol -or
        [string]$Manifest.compatibility_migration.migration_id -cne [string]$receipt.migration_id -or
        [string]$Manifest.compatibility_migration.receipt_sha256 -cne [string]$ReceiptRead.RawSha256) {
        throw 'Signed manifest is not bound to this compatibility migration receipt.'
    }
    if ([string]$Manifest.config.approval_policy -cne 'approve_for_me' -or [string]$Manifest.config.approval_mode -cne 'approve_for_me') {
        throw 'Signed manifest did not apply the approved approval-mode amendment.'
    }
    foreach ($item in @(
        @($Manifest.cycle_ledger.module, $receipt.target.cycle_module, 'cycle module'),
        @($Manifest.cycle_ledger.cli, $receipt.target.cycle_cli, 'cycle CLI'),
        @($Manifest.cycle_ledger.project_module, $receipt.target.project_module, 'project module'))) {
        if (-not ([IO.Path]::GetFullPath([string]$item[0].path)).Equals([IO.Path]::GetFullPath([string]$item[1].path), [StringComparison]::OrdinalIgnoreCase) -or [string]$item[0].sha256 -cne [string]$item[1].sha256) {
            throw "Signed manifest compatibility $($item[2]) binding mismatch."
        }
    }
    $archivePath = Join-Path $runFull ([string]$receipt.archive_directory_name)
    if (-not (Test-Path -LiteralPath $archivePath -PathType Container)) { throw 'Compatibility source archive is missing.' }
    foreach ($item in @(
        @('original-run.json',[string]$receipt.source.manifest_primary_sha256),
        @('original-run.json.bak',[string]$receipt.source.manifest_backup_sha256),
        @('migration-receipt.json',[string]$ReceiptRead.RawSha256))) {
        Assert-CompatHash -Value $item[1] -Label "archive $($item[0])"
        $path = Join-Path $archivePath $item[0]
        if (-not (Test-Path -LiteralPath $path -PathType Leaf) -or (Get-Sha256HexFromFile -LiteralPath $path) -cne $item[1]) { throw "Compatibility source archive mismatch: $($item[0])" }
    }
    return $true
}

function Write-CompatArchiveFile {
    param([Parameter(Mandatory = $true)][string]$Source, [Parameter(Mandatory = $true)][string]$Destination, [Parameter(Mandatory = $true)][string]$ExpectedSha256)
    Assert-CompatHash -Value $ExpectedSha256 -Label 'archive expected sha256'
    if (Test-Path -LiteralPath $Destination -PathType Leaf) {
        if ((Get-Sha256HexFromFile -LiteralPath $Destination) -cne $ExpectedSha256) { throw "Compatibility archive conflict: $Destination" }
        return
    }
    $bytes = [IO.File]::ReadAllBytes($Source)
    try {
        $stream = [IO.FileStream]::new($Destination, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
        try { $stream.Write($bytes, 0, $bytes.Length); $stream.Flush($true) } finally { $stream.Dispose() }
    }
    finally { [Array]::Clear($bytes, 0, $bytes.Length) }
    if ((Get-Sha256HexFromFile -LiteralPath $Destination) -cne $ExpectedSha256) { throw "Compatibility archive write verification failed: $Destination" }
}

function Invoke-MathResearchLegacyV1CompatMigration {
    param(
        [Parameter(Mandatory = $true)][ValidateSet('Analyze','Apply','Verify')][string]$Action,
        [Parameter(Mandatory = $true)][string]$RunDirectory,
        [Parameter(Mandatory = $true)][string]$ReceiptFile,
        [Parameter(Mandatory = $true)][string]$LauncherEntryPath,
        [Parameter(Mandatory = $true)][string]$LauncherModulePath,
        [Parameter(Mandatory = $true)][string]$CycleModulePath,
        [Parameter(Mandatory = $true)][string]$CycleCliPath,
        [Parameter(Mandatory = $true)][string]$ProjectModulePath,
        [Parameter(Mandatory = $true)][string]$CanaryHostPath,
        [Parameter(Mandatory = $true)][string]$CanaryEntryPath
    )
    $runPath = Assert-NoReparsePointChain -LiteralPath ([IO.Path]::GetFullPath($RunDirectory))
    $manifestPath = Join-Path $runPath 'run.json'
    $receiptRead = Read-MathResearchLegacyV1CompatReceipt -LiteralPath $ReceiptFile
    $lease = $null
    $leaseFile = $null
    try {
        $lease = Enter-NamedLease -Kind run -Value $runPath
        $leaseFile = Open-RunLeaseFile -RunDirectory $runPath
        $read = Read-SignedJsonPayload -LiteralPath $manifestPath
        $manifest = $read.Payload
        if ($manifest.Contains('compatibility_migration')) {
            Assert-MathResearchLegacyV1CompatState -Manifest $manifest -RunPath $runPath -ReceiptRead $receiptRead -LauncherEntryPath $LauncherEntryPath -LauncherModulePath $LauncherModulePath -CycleModulePath $CycleModulePath -CycleCliPath $CycleCliPath -ProjectModulePath $ProjectModulePath -CanaryHostPath $CanaryHostPath -CanaryEntryPath $CanaryEntryPath -RequireApplied | Out-Null
            return [pscustomobject]@{ Ok=$true; Action=$Action; Status='already_applied'; RunId=$manifest.run_id; ThreadId=$manifest.thread_id; ReceiptSha256=$receiptRead.RawSha256; AttemptCount=[int]$manifest.cycle_ledger.checkpoint.attempt_count; TotalRoundCount=[int]$manifest.cycle_ledger.checkpoint.total_round_count }
        }
        Assert-MathResearchLegacyV1CompatState -Manifest $manifest -RunPath $runPath -ReceiptRead $receiptRead -LauncherEntryPath $LauncherEntryPath -LauncherModulePath $LauncherModulePath -CycleModulePath $CycleModulePath -CycleCliPath $CycleCliPath -ProjectModulePath $ProjectModulePath -CanaryHostPath $CanaryHostPath -CanaryEntryPath $CanaryEntryPath | Out-Null
        if ($Action -eq 'Verify') { throw 'Compatibility migration has not been applied.' }
        if ([string]$manifest.config.approval_policy -cne 'never' -or [string]$manifest.status -cne [string]$receiptRead.Value.source.status) { throw 'Compatibility migration source approval policy or status mismatch.' }
        if (Test-ProcessIdentityFromManifest -ProcessRecord $manifest.process) { throw 'Compatibility migration refuses a live Codex process.' }
        Assert-CompatHash -Value ([string]$receiptRead.Value.source.manifest_primary_sha256) -Label 'source manifest primary sha256'
        Assert-CompatHash -Value ([string]$receiptRead.Value.source.manifest_backup_sha256) -Label 'source manifest backup sha256'
        if ((Get-Sha256HexFromFile -LiteralPath $manifestPath) -cne [string]$receiptRead.Value.source.manifest_primary_sha256 -or
            (Get-Sha256HexFromFile -LiteralPath "$manifestPath.bak") -cne [string]$receiptRead.Value.source.manifest_backup_sha256) {
            throw 'Compatibility migration source manifest bytes differ from the receipt.'
        }
        if ($Action -eq 'Analyze') {
            return [pscustomobject]@{ Ok=$true; Action=$Action; Status='ready_to_apply'; RunId=$manifest.run_id; ThreadId=$manifest.thread_id; ReceiptSha256=$receiptRead.RawSha256; AttemptCount=[int]$manifest.cycle_ledger.checkpoint.attempt_count; TotalRoundCount=[int]$manifest.cycle_ledger.checkpoint.total_round_count }
        }

        $archivePath = Join-Path $runPath ([string]$receiptRead.Value.archive_directory_name)
        if (-not (Test-Path -LiteralPath $archivePath)) { [IO.Directory]::CreateDirectory($archivePath) | Out-Null }
        Assert-NoReparsePointChain -LiteralPath $archivePath | Out-Null
        Write-CompatArchiveFile -Source $manifestPath -Destination (Join-Path $archivePath 'original-run.json') -ExpectedSha256 ([string]$receiptRead.Value.source.manifest_primary_sha256)
        Write-CompatArchiveFile -Source "$manifestPath.bak" -Destination (Join-Path $archivePath 'original-run.json.bak') -ExpectedSha256 ([string]$receiptRead.Value.source.manifest_backup_sha256)
        Write-CompatArchiveFile -Source $receiptRead.Path -Destination (Join-Path $archivePath 'migration-receipt.json') -ExpectedSha256 $receiptRead.RawSha256

        $manifest.config.approval_policy = 'approve_for_me'
        $manifest.config['approval_mode'] = 'approve_for_me'
        $manifest.cycle_ledger.module = $receiptRead.Value.target.cycle_module
        $manifest.cycle_ledger.cli = $receiptRead.Value.target.cycle_cli
        $manifest.cycle_ledger.project_module = $receiptRead.Value.target.project_module
        $manifest['compatibility_migration'] = [ordered]@{
            schema_version = 1
            protocol = [string]$receiptRead.Value.protocol
            migration_id = [string]$receiptRead.Value.migration_id
            receipt_sha256 = [string]$receiptRead.RawSha256
            source_manifest_primary_sha256 = [string]$receiptRead.Value.source.manifest_primary_sha256
            source_manifest_backup_sha256 = [string]$receiptRead.Value.source.manifest_backup_sha256
            source_thread_id = [string]$receiptRead.Value.run.thread_id
            source_contract_binding_sha256 = [string]$receiptRead.Value.contract.binding_sha256
            source_counters = $receiptRead.Value.source.counters
            objective_changed = $false
            quantifiers_changed = $false
            counters_reset = $false
            approval_mode_from = 'never'
            approval_mode_to = 'approve_for_me'
            applied_at_utc = Get-UtcNowString
        }
        $manifest.revision = [int]$manifest.revision + 1
        $manifest.updated_at_utc = Get-UtcNowString
        $manifest.exit_reason = 'compatibility_migration_applied_ready_to_resume'
        Write-SignedJsonPayload -LiteralPath $manifestPath -Payload $manifest
        $readBack = Read-SignedJsonPayload -LiteralPath $manifestPath
        Assert-MathResearchLegacyV1CompatState -Manifest $readBack.Payload -RunPath $runPath -ReceiptRead $receiptRead -LauncherEntryPath $LauncherEntryPath -LauncherModulePath $LauncherModulePath -CycleModulePath $CycleModulePath -CycleCliPath $CycleCliPath -ProjectModulePath $ProjectModulePath -CanaryHostPath $CanaryHostPath -CanaryEntryPath $CanaryEntryPath -RequireApplied | Out-Null
        return [pscustomobject]@{ Ok=$true; Action=$Action; Status='applied'; RunId=$readBack.Payload.run_id; ThreadId=$readBack.Payload.thread_id; ReceiptSha256=$receiptRead.RawSha256; AttemptCount=[int]$readBack.Payload.cycle_ledger.checkpoint.attempt_count; TotalRoundCount=[int]$readBack.Payload.cycle_ledger.checkpoint.total_round_count }
    }
    finally {
        if ($leaseFile) { $leaseFile.Dispose() }
        Exit-NamedLease -Lease $lease
    }
}

Export-ModuleMember -Function @(
    'Read-MathResearchLegacyV1CompatReceipt',
    'Assert-MathResearchLegacyV1CompatState',
    'Invoke-MathResearchLegacyV1CompatMigration'
)
