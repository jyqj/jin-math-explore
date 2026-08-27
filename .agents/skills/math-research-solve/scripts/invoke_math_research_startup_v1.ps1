[CmdletBinding(DefaultParameterSetName = 'Existing')]
param(
    [Parameter(Mandatory = $true, ParameterSetName = 'Existing')]
    [string]$ProjectDirectory,

    [Parameter(Mandatory = $true, ParameterSetName = 'Slot')]
    [string]$VaultRoot,

    [Parameter(Mandatory = $true, ParameterSetName = 'Slot')]
    [string]$ProjectDirectoryName,

    [Parameter(Mandatory = $true)]
    [ValidateSet('none','active','paused','complete','blocked','unknown')]
    [string]$GoalStatus,

    [string]$ExpectedProjectId,
    [string]$ExpectedContractVersion,
    [string]$ExpectedContractBindingSha256,
    [string]$ExpectedRunId,
    [string]$ExpectedPromptFileName,
    [string]$ExpectedPromptRawSha256,
    [string]$ExpectedGoalFileName,
    [string]$ExpectedGoalRawSha256
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)

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
        foreach ($item in $Element.EnumerateArray()) { Assert-UniqueJsonProperties -Element $item -Path "$Path[$index]"; $index++ }
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
    try { $document = [Text.Json.JsonDocument]::Parse($text, $options) } catch { throw "$Label is not strict JSON: $($_.Exception.Message)" }
    try {
        if ($document.RootElement.ValueKind -ne [Text.Json.JsonValueKind]::Object) { throw "$Label must be a JSON object." }
        Assert-UniqueJsonProperties -Element $document.RootElement -Path '$'
    }
    finally { $document.Dispose() }
    return ($text | ConvertFrom-Json -AsHashtable -Depth 64)
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

function Assert-SafeLeafName {
    param([Parameter(Mandatory = $true)][string]$Value, [Parameter(Mandatory = $true)][string]$Label)
    if ([string]::IsNullOrWhiteSpace($Value) -or $Value -ne (Split-Path -Leaf $Value) -or $Value -match '[<>:"/\\|?*]' -or $Value.EndsWith('.') -or $Value.EndsWith(' ')) {
        throw "$Label must be one safe leaf filename."
    }
}

function Invoke-ControllerAction {
    param([Parameter(Mandatory = $true)][string]$Action, [Parameter(Mandatory = $true)][string]$ProjectPath)
    $observer = Join-Path $PSScriptRoot 'observer_run.ps1'
    $controller = Join-Path $PSScriptRoot 'invoke_math_research_project.ps1'
    foreach ($path in @($observer, $controller)) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Pinned controller companion is missing: $path" }
    }
    $quote = { param([string]$Value) return "'" + $Value.Replace("'", "''") + "'" }
    $arguments = @('-Action', $Action, '-ProjectDirectory', $ProjectPath)
    $encodedArguments = ($arguments | ForEach-Object { & $quote ([string]$_) }) -join ', '
    $command = "& $(& $quote $observer) -Skill 'math-research-solve' -Catalog 'math-research-solve/v1' -Phase 'math-research-solve.script.invoke_math_research_project' -FilePath $(& $quote $controller) -ArgumentList @($encodedArguments)"
    $encodedCommand = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($command))
    $pwsh = (Get-Process -Id $PID).Path
    $output = & $pwsh -NoLogo -NoProfile -EncodedCommand $encodedCommand
    if ($LASTEXITCODE -ne 0) { throw "Authoritative project controller action '$Action' failed with exit code $LASTEXITCODE." }
    $text = @($output) -join "`n"
    if ([string]::IsNullOrWhiteSpace($text)) { throw "Authoritative project controller action '$Action' returned no JSON." }
    try { return ($text | ConvertFrom-Json -AsHashtable -Depth 64) }
    catch { throw "Authoritative project controller action '$Action' returned malformed JSON." }
}

function Test-ExactFirstContractState {
    param(
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Plan,
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Project,
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Checkpoint
    )
    $contract = $Plan.ActiveContract
    $run = $Plan.ActiveRun
    $contractVersion = if ($contract -is [Collections.IDictionary] -and $contract.Contains('version')) { [string]$contract.version } else { '' }
    foreach ($key in @('attempt_count','attempts_since_last_audit','last_sealed_attempt','last_completed_audit','audit_due','dirty','recovery_required','project_status')) {
        if (-not $Checkpoint.Contains($key)) { return $false }
    }
    return (
        $contract -is [Collections.IDictionary] -and
        $run -is [Collections.IDictionary] -and
        [string]$contract.status -ceq 'none' -and
        [string]::IsNullOrWhiteSpace([string]$contract.path) -and
        [string]::IsNullOrWhiteSpace([string]$contract.sha256) -and
        [string]::IsNullOrWhiteSpace($contractVersion) -and
        [string]$run.status -ceq 'none' -and
        [string]::IsNullOrWhiteSpace([string]$run.id) -and
        [string]::IsNullOrWhiteSpace([string]$run.path) -and
        $null -eq $Plan.ActiveTicket -and
        [string]$Project.status -ceq 'paused' -and
        $null -eq $Project.active_contract -and
        $null -eq $Project.active_run -and
        [string]$Checkpoint.project_status -ceq 'paused' -and
        [int]$Checkpoint.attempt_count -eq 0 -and
        [int]$Checkpoint.attempts_since_last_audit -eq 0 -and
        $null -eq $Checkpoint.last_sealed_attempt -and
        $null -eq $Checkpoint.last_completed_audit -and
        -not [bool]$Checkpoint.audit_due -and
        -not [bool]$Checkpoint.dirty -and
        -not [bool]$Checkpoint.recovery_required
    )
}

function Test-ExpectedPreparingReceipt {
    param([Parameter(Mandatory = $true)][Collections.IDictionary]$Plan, [Parameter(Mandatory = $true)][string]$ProjectPath)
    $requiredText = @($ExpectedProjectId,$ExpectedContractVersion,$ExpectedContractBindingSha256,$ExpectedRunId,$ExpectedPromptFileName,$ExpectedPromptRawSha256,$ExpectedGoalFileName,$ExpectedGoalRawSha256)
    if (@($requiredText | Where-Object { [string]::IsNullOrWhiteSpace([string]$_) }).Count -gt 0) {
        return [pscustomobject]@{ Match=$false; Reason='expected_preparing_receipt_incomplete'; Phase=$null }
    }
    Assert-LowerSha256 -Value $ExpectedContractBindingSha256 -Label 'ExpectedContractBindingSha256'
    Assert-LowerSha256 -Value $ExpectedPromptRawSha256 -Label 'ExpectedPromptRawSha256'
    Assert-LowerSha256 -Value $ExpectedGoalRawSha256 -Label 'ExpectedGoalRawSha256'
    Assert-SafeLeafName -Value $ExpectedPromptFileName -Label 'ExpectedPromptFileName'
    Assert-SafeLeafName -Value $ExpectedGoalFileName -Label 'ExpectedGoalFileName'
    if ($ExpectedPromptFileName.Equals($ExpectedGoalFileName, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Expected Prompt and Goal filenames must be distinct.'
    }

    $contract = $Plan.ActiveContract
    $run = $Plan.ActiveRun
    if (-not [bool]$Plan.Dirty -or [string]$contract.status -cne 'confirmed' -or [string]$run.status -cne 'preparing') {
        return [pscustomobject]@{ Match=$false; Reason='checkpoint_not_registered_preparing'; Phase=$null }
    }
    if ([string]$Plan.ProjectId -cne $ExpectedProjectId -or [string]$contract.version -cne $ExpectedContractVersion -or [string]$contract.sha256 -cne $ExpectedContractBindingSha256 -or [string]$run.id -cne $ExpectedRunId) {
        return [pscustomobject]@{ Match=$false; Reason='preparing_identity_or_binding_mismatch'; Phase=$null }
    }

    $contractPath = [IO.Path]::GetFullPath((Join-Path $ProjectPath ([string]$contract.path)))
    $contractsRoot = Join-Path $ProjectPath 'contracts'
    if (-not (Test-PathInside -Child $contractPath -Directory $contractsRoot) -or -not (Test-Path -LiteralPath $contractPath -PathType Leaf)) {
        return [pscustomobject]@{ Match=$false; Reason='preparing_contract_path_invalid'; Phase=$null }
    }
    Assert-NoReparsePointChain -LiteralPath $contractPath | Out-Null
    if ((Get-NormalizedTextSha256 -LiteralPath $contractPath) -cne $ExpectedContractBindingSha256) {
        return [pscustomobject]@{ Match=$false; Reason='preparing_contract_bytes_mismatch'; Phase=$null }
    }

    $runPath = [IO.Path]::GetFullPath((Join-Path $ProjectPath ([string]$run.path)))
    $runsRoot = Join-Path $ProjectPath 'runs'
    if (-not (Test-PathInside -Child $runPath -Directory $runsRoot) -or -not (Split-Path -Parent $runPath).Equals([IO.Path]::GetFullPath($runsRoot), [StringComparison]::OrdinalIgnoreCase) -or (Split-Path -Leaf $runPath) -cne $ExpectedRunId -or -not (Test-Path -LiteralPath $runPath -PathType Container)) {
        return [pscustomobject]@{ Match=$false; Reason='preparing_run_path_invalid'; Phase=$null }
    }
    Assert-NoReparsePointChain -LiteralPath $runPath | Out-Null
    $promptPath = Join-Path $runPath $ExpectedPromptFileName
    $goalPath = Join-Path $runPath $ExpectedGoalFileName
    foreach ($path in @($promptPath,$goalPath)) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return [pscustomobject]@{ Match=$false; Reason='preparing_input_missing'; Phase=$null } }
        Assert-NoReparsePointChain -LiteralPath $path | Out-Null
    }
    if ((Get-FileSha256 -LiteralPath $promptPath) -cne $ExpectedPromptRawSha256 -or (Get-NormalizedTextSha256 -LiteralPath $promptPath) -cne $ExpectedContractBindingSha256 -or (Get-FileSha256 -LiteralPath $goalPath) -cne $ExpectedGoalRawSha256) {
        return [pscustomobject]@{ Match=$false; Reason='preparing_input_hash_mismatch'; Phase=$null }
    }

    $runManifest = Join-Path $runPath 'run.json'
    if (Test-Path -LiteralPath $runManifest -PathType Leaf) {
        Assert-NoReparsePointChain -LiteralPath $runManifest | Out-Null
        return [pscustomobject]@{ Match=$true; Reason=$null; Phase='launcher_manifest_present_requires_signed_resume_verification' }
    }
    $actualNames = @(Get-ChildItem -LiteralPath $runPath -Force | ForEach-Object { $_.Name })
    $expectedNames = @($ExpectedPromptFileName,$ExpectedGoalFileName)
    if (@($actualNames | Where-Object { $_ -cnotin $expectedNames }).Count -gt 0 -or @($expectedNames | Where-Object { $_ -cnotin $actualNames }).Count -gt 0) {
        return [pscustomobject]@{ Match=$false; Reason='prelauncher_directory_must_contain_only_prompt_and_goal'; Phase=$null }
    }
    return [pscustomobject]@{ Match=$true; Reason=$null; Phase='registered_before_launcher' }
}

$clock = [Diagnostics.Stopwatch]::StartNew()
$controllerCalls = 0
$controllerAction = $null
$plan = $null
$projectPath = $null
$startupClass = $null
$nextAction = $null
$recoveryReason = $null
$preparingPhase = $null
$minimalRead = @()

if ($PSCmdlet.ParameterSetName -eq 'Slot') {
    if ([string]::IsNullOrWhiteSpace($ProjectDirectoryName) -or $ProjectDirectoryName -match '[<>:"/\\|?*]' -or $ProjectDirectoryName.EndsWith('.') -or $ProjectDirectoryName.EndsWith(' ')) { throw 'Unsafe ProjectDirectoryName.' }
    $vault = Assert-NoReparsePointChain -LiteralPath $VaultRoot
    if (-not (Test-Path -LiteralPath $vault -PathType Container)) { throw 'VaultRoot is not an existing directory.' }
    $projectsRoot = Join-Path $vault '笔记草稿\公开问题的尝试'
    $projectsRoot = Assert-NoReparsePointChain -LiteralPath $projectsRoot
    if (-not (Test-Path -LiteralPath $projectsRoot -PathType Container)) { throw 'The canonical math-research projects root is missing.' }
    $slot = [IO.Path]::GetFullPath((Join-Path $projectsRoot $ProjectDirectoryName))
    if (-not (Split-Path -Parent $slot).Equals([IO.Path]::GetFullPath($projectsRoot), [StringComparison]::OrdinalIgnoreCase)) { throw 'Project slot is not one direct child of the canonical projects root.' }
    if (-not (Test-Path -LiteralPath $slot)) {
        Assert-NoReparsePointChain -LiteralPath $slot -AllowMissingLeaf | Out-Null
        $startupClass = 'fresh_project_slot'
        $nextAction = 'initialize_then_render_contract'
        $projectPath = $slot
    }
    elseif (-not (Test-Path -LiteralPath (Join-Path $slot 'project.json') -PathType Leaf)) {
        Assert-NoReparsePointChain -LiteralPath $slot | Out-Null
        $startupClass = 'partial_project_tree_recovery'
        $nextAction = 'inspect_partial_tree_without_initializing_over_it'
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
    $checkpointHintPath = Join-Path $stateHintPath 'checkpoint.json'
    foreach ($hintPath in @($projectJsonHintPath,$stateHintPath,$checkpointHintPath)) { Assert-NoReparsePointChain -LiteralPath $hintPath | Out-Null }
    $projectHint = Read-StrictJsonObject -LiteralPath $projectJsonHintPath -Label 'project.json startup hint'
    $checkpointHint = Read-StrictJsonObject -LiteralPath $checkpointHintPath -Label 'checkpoint startup hint'
    $projectHintSha256 = Get-FileSha256 -LiteralPath $projectJsonHintPath
    $checkpointHintSha256 = Get-FileSha256 -LiteralPath $checkpointHintPath
    $migrationHint = if ($checkpointHint.Contains('migration') -and $checkpointHint.migration -is [Collections.IDictionary]) { [string]$checkpointHint.migration.status } else { 'unknown' }
    if ([string]$projectHint.status -eq 'migration_required' -or $migrationHint -notin @('not_required','verified')) {
        $controllerAction = 'StructuralOnly'
        $plan = Invoke-ControllerAction -Action $controllerAction -ProjectPath $projectPath
        $controllerCalls = 1
        if ((Get-FileSha256 -LiteralPath $projectJsonHintPath) -cne $projectHintSha256 -or (Get-FileSha256 -LiteralPath $checkpointHintPath) -cne $checkpointHintSha256) { throw 'Project authority files changed during startup verification.' }
        if ([string]$plan.ProjectId -cne [string]$projectHint.project_id -or [string]$plan.Checkpoint.project_id -cne [string]$plan.ProjectId) { throw 'Structural controller receipt does not match project identity.' }
        $migration = $plan.Checkpoint.migration
        if ($migration -isnot [Collections.IDictionary] -or [string]$plan.Status -cne 'migration_required') { throw 'Structural controller receipt does not authorize legacy migration routing.' }
        $startupClass = 'first_legacy_migration'
        $nextAction = switch ([string]$migration.status) {
            'required' { 'analyze_legacy_once' }
            'analyzed' { 'complete_semantic_review' }
            'review_required' { 'complete_semantic_review' }
            'approved' { 'apply_then_verify_semantic_migration' }
            default { 'inspect_legacy_migration_recovery' }
        }
        $minimalRead = @('project.json','state/checkpoint.json','manifests/import-summary.json')
    }
    else {
        $controllerAction = 'ResumePlan'
        $plan = Invoke-ControllerAction -Action $controllerAction -ProjectPath $projectPath
        $controllerCalls = 1
        if ((Get-FileSha256 -LiteralPath $projectJsonHintPath) -cne $projectHintSha256 -or (Get-FileSha256 -LiteralPath $checkpointHintPath) -cne $checkpointHintSha256) { throw 'Project authority files changed during startup verification.' }
        if ([string]::IsNullOrWhiteSpace([string]$plan.ProjectId)) { throw 'ResumePlan omitted project identity.' }
        if (-not [string]::IsNullOrWhiteSpace($ExpectedProjectId) -and [string]$plan.ProjectId -cne $ExpectedProjectId) { throw 'Expected project_id mismatch.' }
        $minimalRead = @('README.md','state/CURRENT.md','state/checkpoint.json')
        $activeContractPath = if ($plan.ActiveContract -is [Collections.IDictionary] -and $plan.ActiveContract.Contains('path')) { [string]$plan.ActiveContract.path } else { $null }
        $activeTicketPath = if ($plan.ActiveTicket -is [Collections.IDictionary] -and $plan.ActiveTicket.Contains('path')) { [string]$plan.ActiveTicket.path } else { $null }
        switch ([string]$plan.Action) {
            'resume_same_attempt' { $startupClass='same_run_resume';$nextAction='resume_same_attempt';$minimalRead+=@($activeContractPath,$activeTicketPath) }
            'resume_signed_run' { $startupClass='same_run_resume';$nextAction='resume_signed_run';$minimalRead+=@($activeContractPath,$activeTicketPath) }
            'audit_required' { $startupClass='same_run_resume';$nextAction='run_due_audit';$minimalRead+=@($activeContractPath,$activeTicketPath) }
            'awaiting_contract' {
                if (Test-ExactFirstContractState -Plan $plan -Project $projectHint -Checkpoint $checkpointHint) { $startupClass='existing_project_first_contract';$nextAction='render_contract' }
                else { $startupClass='new_contract_or_closed_review';$nextAction='review_terminal_or_prior_history_before_new_contract' }
            }
            'recovery_or_audit_only' {
                $preparing = Test-ExpectedPreparingReceipt -Plan $plan -ProjectPath $projectPath
                if ([bool]$preparing.Match) {
                    $startupClass='registered_preparing_recovery'
                    $preparingPhase=[string]$preparing.Phase
                    $nextAction = if ($preparingPhase -eq 'registered_before_launcher') { 'invoke_new_launcher_without_reregistering' } else { 'invoke_signed_resume_verification_without_reregistering' }
                }
                else { $startupClass='recovery_only';$nextAction='perform_unique_recovery_action';$recoveryReason=[string]$preparing.Reason }
            }
            default { throw "Unsupported authoritative ResumePlan action: $($plan.Action)" }
        }
    }
}

$preGoalPreparationActions = @(
    'initialize_then_render_contract','analyze_legacy_once','complete_semantic_review',
    'apply_then_verify_semantic_migration','inspect_legacy_migration_recovery','render_contract',
    'review_terminal_or_prior_history_before_new_contract','inspect_partial_tree_without_initializing_over_it'
)
$wouldMutate = $nextAction -notin @('inspect_partial_tree_without_initializing_over_it','check_goal_control','stop_campaign')
$goalGate = 'active_advisory_launcher_recheck_required'
if ($GoalStatus -eq 'none') {
    if ($nextAction -in $preGoalPreparationActions) { $goalGate='pre_goal_preparation_only_research_forbidden' }
    else { $nextAction='create_or_bind_matching_goal_before_research';$recoveryReason='goal_control_none';$goalGate='research_forbidden_until_matching_goal_active' }
}
elseif ($wouldMutate -and $GoalStatus -ne 'active') {
    if ($GoalStatus -eq 'paused') { $nextAction='wait_for_goal_control';$recoveryReason='goal_control_paused' }
    elseif ($GoalStatus -eq 'unknown') { $nextAction='check_goal_control';$recoveryReason='goal_control_unknown' }
    else { $nextAction='stop_campaign';$recoveryReason="goal_control_$GoalStatus" }
    $goalGate='research_and_mutation_forbidden'
}

$clock.Stop()
[ordered]@{
    schema = 'math-research-startup-plan/v1'
    ok = $true
    startup_class = $startupClass
    next_action = $nextAction
    recovery_reason = $recoveryReason
    preparing_phase = $preparingPhase
    project_id = if ($null -ne $plan -and $plan.Contains('ProjectId')) { [string]$plan.ProjectId } else { $ExpectedProjectId }
    project_directory = $projectPath
    goal_status_supplied = $GoalStatus
    goal_status_evidence = 'caller_supplied_advisory_launcher_must_recheck_control_plane'
    goal_gate = $goalGate
    controller_action = $controllerAction
    controller_call_count = $controllerCalls
    authoritative_resume_action = if ($null -ne $plan -and $plan.Contains('Action')) { [string]$plan.Action } else { $null }
    active_contract = if ($null -ne $plan -and $plan.Contains('ActiveContract')) { $plan.ActiveContract } else { $null }
    active_run = if ($null -ne $plan -and $plan.Contains('ActiveRun')) { $plan.ActiveRun } else { $null }
    minimal_model_read = @($minimalRead | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) } | Select-Object -Unique)
    contract_hash_role = 'integrity_receipt_not_authorization_phrase'
    measured_router_elapsed_ms = [Math]::Round($clock.Elapsed.TotalMilliseconds, 3)
} | ConvertTo-Json -Depth 64
