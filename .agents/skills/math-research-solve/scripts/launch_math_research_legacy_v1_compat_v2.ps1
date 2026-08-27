[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('New', 'Resume')]
    [string]$Mode,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$RunDirectory,

    [string]$PromptFile,

    [string]$GoalObjectiveFile,

    [ValidateRange(1, 16)]
    [int]$MaxChildAgents,

    [string]$Model,

    [ValidateSet('minimal', 'low', 'medium', 'high', 'xhigh', 'max', 'ultra')]
    [string]$ReasoningEffort,

    [string]$ContinuationPromptFile,

    [string]$MigrationReceiptFile,

    [string]$ControlPathReceiptFile,

    [ValidateRange(0, 525600)]
[int]$MaxRuntimeMinutes = 0
)

$invocationParameters = [ordered]@{}
foreach ($entry in $PSBoundParameters.GetEnumerator()) { $invocationParameters[$entry.Key] = $entry.Value }

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)

$compatLauncherModule = Import-Module (Join-Path $PSScriptRoot 'MathResearchLauncherLegacyV1Compat.psm1') -Force -DisableNameChecking -PassThru
Import-Module (Join-Path $PSScriptRoot 'MathResearchLegacyV1CompatMigration.psm1') -Force -DisableNameChecking
Import-Module (Join-Path $PSScriptRoot 'MathResearchLegacyV1ControlPathAmendmentV2.psm1') -Force -DisableNameChecking
Import-Module (Join-Path $PSScriptRoot 'MathResearchApproveForMeArgvCompatV2.psm1') -Force -DisableNameChecking
Enable-MathResearchApproveForMeArgvCompatV2 -TargetModule $compatLauncherModule -Flavor legacy-v1-compat
Assert-PowerShell7

$manifestFileName = 'run.json'
$goalBootstrapTimeoutMilliseconds = 10L * 60L * 1000L
$preflightTimeoutMilliseconds = 15L * 1000L
$jsonlMaximumBytes = 512L * 1024L * 1024L
$stderrMaximumBytes = 64L * 1024L * 1024L
$lastMessageMaximumBytes = 4L * 1024L * 1024L

function Assert-InvocationShape {
    param([Parameter(Mandatory = $true)][Collections.IDictionary]$BoundParameters)
    if ($Mode -cne 'Resume') { throw 'The legacy v1 compatibility launcher is Resume-only.' }
    if (-not $BoundParameters.Contains('MigrationReceiptFile') -or [string]::IsNullOrWhiteSpace([string]$MigrationReceiptFile)) {
        throw 'Compatibility Resume requires -MigrationReceiptFile.'
    }
    if (-not $BoundParameters.Contains('ControlPathReceiptFile') -or [string]::IsNullOrWhiteSpace([string]$ControlPathReceiptFile)) {
        throw 'Compatibility Resume v2 requires -ControlPathReceiptFile.'
    }
    $newOnly = @('PromptFile', 'GoalObjectiveFile', 'MaxChildAgents', 'Model', 'ReasoningEffort', 'MaxRuntimeMinutes')
    if ($Mode -eq 'New') {
        foreach ($name in @('PromptFile', 'GoalObjectiveFile', 'MaxChildAgents', 'Model', 'ReasoningEffort', 'MaxRuntimeMinutes')) {
            if (-not $BoundParameters.Contains($name)) { throw "New mode requires -$name." }
        }
        if ($BoundParameters.Contains('ContinuationPromptFile')) {
            throw 'New mode does not accept -ContinuationPromptFile.'
        }
        if ($Model -notmatch '^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$') {
            throw 'Model contains unsupported characters.'
        }
    }
    else {
        if (-not $BoundParameters.Contains('ContinuationPromptFile')) {
            throw 'Resume mode requires -ContinuationPromptFile.'
        }
        foreach ($name in $newOnly) {
            if ($BoundParameters.Contains($name)) {
                throw "Resume mode reads the original configuration from run.json and does not accept -$name."
            }
        }
    }
}

function Save-Manifest {
    param(
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Manifest,
        [Parameter(Mandatory = $true)][string]$ManifestPath,
        [switch]$CreateKeyIfMissing
    )
    $Manifest.revision = [int]$Manifest.revision + 1
    $Manifest.updated_at_utc = Get-UtcNowString
    Write-SignedJsonPayload -LiteralPath $ManifestPath -Payload $Manifest -CreateKeyIfMissing:$CreateKeyIfMissing
}

function Get-RelativeRunPath {
    param(
        [Parameter(Mandatory = $true)][string]$RunPath,
        [Parameter(Mandatory = $true)][string]$FilePath
    )
    return [IO.Path]::GetRelativePath($RunPath, $FilePath)
}

function New-SegmentPaths {
    param(
        [Parameter(Mandatory = $true)][string]$RunPath,
        [Parameter(Mandatory = $true)][int]$Index,
        [Parameter(Mandatory = $true)][ValidateSet('goal', 'research', 'resume')][string]$Kind
    )
    $prefix = '{0:D3}-{1}' -f $Index, $Kind
    $lastExtension = if ($Kind -eq 'goal') { 'json' } else { 'md' }
    return [pscustomobject]@{
        Events = Join-Path $RunPath "events-$prefix.jsonl"
        Stderr = Join-Path $RunPath "stderr-$prefix.log"
        LastMessage = Join-Path $RunPath "last-message-$prefix.$lastExtension"
    }
}

function Add-Usage {
    param(
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Manifest,
        [Parameter(Mandatory = $true)]$Usage
    )
    foreach ($key in @('input_tokens', 'cached_input_tokens', 'output_tokens', 'reasoning_output_tokens')) {
        $Manifest.token_usage[$key] = [long]$Manifest.token_usage[$key] + [long]$Usage.$key
    }
}

function Test-SignedStopRequest {
    param(
        [Parameter(Mandatory = $true)][string]$RunPath,
        [Parameter(Mandatory = $true)][int]$ProcessId,
        [Parameter(Mandatory = $true)][string]$ProcessStartTimeUtc,
        [Parameter(Mandatory = $true)][string]$RunId,
        [Parameter(Mandatory = $true)][string]$JobObjectName,
        [string]$ThreadId
    )
    $path = Join-Path $RunPath 'stop-request.json'
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return $false }
    try {
        $request = Read-SignedJsonPayload -LiteralPath $path
        return (
            $request.Payload.schema_version -eq 1 -and
            [int]$request.Payload.target_pid -eq $ProcessId -and
            [string]$request.Payload.target_process_start_time_utc -ceq $ProcessStartTimeUtc -and
            [string]$request.Payload.target_job_object_name -ceq $JobObjectName -and
            [string]$request.Payload.run_id -ceq $RunId -and
            [string]$request.Payload.thread_id -ceq [string]$ThreadId)
    }
    catch { return $false }
}

function Invoke-CapturedAttestedProcess {
    param(
        [Parameter(Mandatory = $true)]$Attestation,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$PromptText,
        [Parameter(Mandatory = $true)][string]$StdoutPath,
        [Parameter(Mandatory = $true)][string]$StderrPath,
        [Parameter(Mandatory = $true)][long]$TimeoutMilliseconds,
        [Parameter(Mandatory = $true)][long]$MaximumStdoutBytes,
        [Parameter(Mandatory = $true)][long]$MaximumStderrBytes,
        [Collections.IDictionary]$Manifest,
        [string]$ManifestPath,
        [Collections.IDictionary]$Segment
    )
    foreach ($path in @($StdoutPath, $StderrPath)) {
        if (Test-Path -LiteralPath $path) { throw "Refusing to overwrite an existing launcher output: $path" }
    }

    $handle = $null
    try {
        $jobName = if ($Manifest -and $Segment) { 'Local\OpenAI.Codex.MathResearch.Job.' + [Guid]::NewGuid().ToString('N') } else { $null }
        $handle = Start-AttestedProcess -Attestation $Attestation -Arguments $Arguments -WorkingDirectory $WorkingDirectory -StandardInput $PromptText -StdoutPath $StdoutPath -StderrPath $StderrPath -JobName $jobName
        if ($Manifest -and $Segment) {
            $Segment.pid = $handle.Child.ProcessId
            $Segment.process_start_time_utc = $handle.Child.ProcessStartTimeUtc
            $Segment.job_object_assigned = [bool]$handle.Child.JobAssigned
            $Segment.job_object_name = [string]$handle.Child.JobName
            $Manifest.process = [ordered]@{
                pid = $handle.Child.ProcessId
                start_time_utc = $handle.Child.ProcessStartTimeUtc
                executable_path = [string]$Attestation.path
                executable_sha256 = [string]$Attestation.sha256
                job_object_assigned = [bool]$handle.Child.JobAssigned
                job_object_name = [string]$handle.Child.JobName
                create_process_suspended = $false
            }
            Save-Manifest -Manifest $Manifest -ManifestPath $ManifestPath
        }
        $result = $handle.Child.Wait($TimeoutMilliseconds, $MaximumStdoutBytes, $MaximumStderrBytes)
        return $result
    }
    finally {
        Stop-AttestedProcessHandle -Handle $handle
    }
}

function Invoke-JsonSegment {
    param(
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Manifest,
        [Parameter(Mandatory = $true)][string]$ManifestPath,
        [Parameter(Mandatory = $true)]$Attestation,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$PromptText,
        [Parameter(Mandatory = $true)][ValidateSet('goal', 'research', 'resume')][string]$Kind,
        [Parameter(Mandatory = $true)][long]$TimeoutMilliseconds,
        [string]$ExpectedThreadId
    )
    $index = [int]$Manifest.next_segment_index
    $paths = New-SegmentPaths -RunPath $Manifest.run_directory -Index $index -Kind $Kind
    foreach ($path in @($paths.Events, $paths.Stderr, $paths.LastMessage)) {
        if (Test-Path -LiteralPath $path) { throw "Segment output already exists: $path" }
    }
    $segment = [ordered]@{
        index = $index
        kind = $Kind
        status = 'running'
        started_at_utc = Get-UtcNowString
        ended_at_utc = $null
        events_file = Get-RelativeRunPath -RunPath $Manifest.run_directory -FilePath $paths.Events
        stderr_file = Get-RelativeRunPath -RunPath $Manifest.run_directory -FilePath $paths.Stderr
        last_message_file = Get-RelativeRunPath -RunPath $Manifest.run_directory -FilePath $paths.LastMessage
        pid = $null
        process_start_time_utc = $null
        job_object_assigned = $null
        job_object_name = $null
        exit_code = $null
        timed_out = $false
        output_limit_exceeded = $false
        standard_input_failed = $false
        standard_input_error = $null
        terminal_event = $null
        thread_id = $null
        token_usage = $null
        events_sha256 = $null
        stderr_sha256 = $null
        last_message_sha256 = $null
        item_errors = @()
        unknown_event_types = @()
    }
    $Manifest.segments = @($Manifest.segments) + @($segment)
    $Manifest.next_segment_index = $index + 1
    Save-Manifest -Manifest $Manifest -ManifestPath $ManifestPath

    $result = $null
    try {
        $result = Invoke-CapturedAttestedProcess -Attestation $Attestation -Arguments $Arguments -WorkingDirectory $Manifest.run_directory -PromptText $PromptText -StdoutPath $paths.Events -StderrPath $paths.Stderr -TimeoutMilliseconds $TimeoutMilliseconds -MaximumStdoutBytes $jsonlMaximumBytes -MaximumStderrBytes $stderrMaximumBytes -Manifest $Manifest -ManifestPath $ManifestPath -Segment $segment
        $segment.exit_code = $result.ExitCode
        $segment.timed_out = [bool]$result.TimedOut
        $segment.output_limit_exceeded = [bool]$result.OutputLimitExceeded
        $segment.standard_input_failed = [bool]$result.StandardInputFailed
        $segment.standard_input_error = $result.StandardInputError
        $segment.ended_at_utc = $result.ProcessEndTimeUtc
        $segment.status = if ($result.TimedOut) { 'timed_out' } elseif ($result.OutputLimitExceeded) { 'output_limit_exceeded' } elseif ($result.ExitCode -eq 0) { 'process_exited_0' } else { 'process_failed' }

        if (Test-Path -LiteralPath $paths.Events -PathType Leaf) { $segment.events_sha256 = Get-Sha256HexFromFile -LiteralPath $paths.Events }
        if (Test-Path -LiteralPath $paths.Stderr -PathType Leaf) { $segment.stderr_sha256 = Get-Sha256HexFromFile -LiteralPath $paths.Stderr }
        if (Test-Path -LiteralPath $paths.LastMessage -PathType Leaf) {
            Assert-NoReparsePointChain -LiteralPath $paths.LastMessage | Out-Null
            $lastMessageItem = Get-Item -LiteralPath $paths.LastMessage
            $segment.last_message_sha256 = Get-Sha256HexFromFile -LiteralPath $paths.LastMessage
            if ($lastMessageItem.Length -eq 0) { throw "$Kind final-message file is empty." }
            if ($lastMessageItem.Length -gt $lastMessageMaximumBytes) {
                $segment.output_limit_exceeded = $true
                $segment.status = 'output_limit_exceeded'
                throw "$Kind final-message file exceeded the $lastMessageMaximumBytes-byte limit."
            }
        }
        else { throw "$Kind segment did not write the required final-message file." }

        if (-not $result.TimedOut -and -not $result.OutputLimitExceeded -and (Get-Item -LiteralPath $paths.Events).Length -gt 0) {
            $events = Read-CodexJsonLog -LiteralPath $paths.Events -ExpectedThreadId $ExpectedThreadId
            $segment.terminal_event = $events.TerminalType
            $segment.thread_id = $events.ThreadId
            $segment.token_usage = [ordered]@{
                input_tokens = [long]$events.Usage.input_tokens
                cached_input_tokens = [long]$events.Usage.cached_input_tokens
                output_tokens = [long]$events.Usage.output_tokens
                reasoning_output_tokens = [long]$events.Usage.reasoning_output_tokens
            }
            $segment.item_errors = @($events.ItemErrors)
            $segment.unknown_event_types = @($events.UnknownTypes)
            Add-Usage -Manifest $Manifest -Usage $events.Usage
            if ($events.TopLevelErrors.Count -gt 0) { throw "Codex emitted a top-level error event: $($events.TopLevelErrors -join '; ')" }
            if ($events.TerminalType -ne 'turn.completed') { throw "Codex terminal event was $($events.TerminalType)." }
        }
        if ($result.TimedOut) { throw "$Kind segment exceeded its configured wall-clock timeout." }
        if ($result.OutputLimitExceeded) { throw "$Kind segment exceeded the launcher log-size limit." }
        if ($result.StandardInputFailed) { throw "$Kind segment could not deliver its complete prompt through stdin: $($result.StandardInputError)" }
        if ($result.ExitCode -ne 0) { throw "$Kind Codex process exited with code $($result.ExitCode)." }
        if ($null -eq $segment.terminal_event) { throw "$Kind segment did not produce a valid terminal JSONL event." }

        $segment.status = 'turn_completed'
        $Manifest.process = $null
        Save-Manifest -Manifest $Manifest -ManifestPath $ManifestPath
        return [pscustomobject]@{
            Segment = $segment
            Events = $events
            Paths = $paths
            ProcessResult = $result
        }
    }
    catch {
        $segmentFailure = $_
        if ($result -and (Test-SignedStopRequest -RunPath $Manifest.run_directory -ProcessId $result.ProcessId -ProcessStartTimeUtc $result.ProcessStartTimeUtc -RunId ([string]$Manifest.run_id) -JobObjectName ([string]$segment.job_object_name) -ThreadId ([string]$Manifest.thread_id))) {
            $segment.status = 'stopped'
        }
        elseif ($segment.status -notin @('timed_out', 'output_limit_exceeded', 'stopped')) {
            $segment.status = 'failed'
        }
        $Manifest.process = $null
        try { Save-Manifest -Manifest $Manifest -ManifestPath $ManifestPath }
        catch { [Console]::Error.WriteLine("Manifest update also failed while preserving a segment error: $($_.Exception.Message)") }
        throw $segmentFailure
    }
}

function Invoke-FeaturePreflight {
    param(
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Manifest,
        [Parameter(Mandatory = $true)][string]$ManifestPath,
        [Parameter(Mandatory = $true)]$Attestation,
        [Parameter(Mandatory = $true)][int]$ChildCap
    )
    $preflightIndex = @($Manifest.preflights).Count
    while ($true) {
        if ($preflightIndex -gt (@($Manifest.preflights).Count + 1000)) { throw 'Too many occupied feature-preflight file indices.' }
        $preflightPrefix = '{0:D3}' -f $preflightIndex
        $stdoutPath = Join-Path $Manifest.run_directory "preflight-features-$preflightPrefix.stdout.txt"
        $stderrPath = Join-Path $Manifest.run_directory "preflight-features-$preflightPrefix.stderr.txt"
        if (-not (Test-Path -LiteralPath $stdoutPath) -and -not (Test-Path -LiteralPath $stderrPath)) { break }
        $preflightIndex++
    }
    $Manifest.status = 'preflight_running'
    $Manifest.capacity.cli_override_status = 'preflight_running'
    Save-Manifest -Manifest $Manifest -ManifestPath $ManifestPath
    $arguments = New-CodexFeaturesArguments -RunDirectory $Manifest.run_directory -MaxChildAgents $ChildCap
    $result = Invoke-CapturedAttestedProcess -Attestation $Attestation -Arguments $arguments -WorkingDirectory $Manifest.run_directory -PromptText '' -StdoutPath $stdoutPath -StderrPath $stderrPath -TimeoutMilliseconds $preflightTimeoutMilliseconds -MaximumStdoutBytes 2097152 -MaximumStderrBytes 2097152
    $stdout = [IO.File]::ReadAllText($stdoutPath, [Text.UTF8Encoding]::new($false, $true))
    $stderr = [IO.File]::ReadAllText($stderrPath, [Text.UTF8Encoding]::new($false, $true))
    $preflightRecord = [ordered]@{
        exit_code = $result.ExitCode
        timed_out = [bool]$result.TimedOut
        output_limit_exceeded = [bool]$result.OutputLimitExceeded
        stdout_file = Get-RelativeRunPath -RunPath $Manifest.run_directory -FilePath $stdoutPath
        stderr_file = Get-RelativeRunPath -RunPath $Manifest.run_directory -FilePath $stderrPath
        stdout_sha256 = Get-Sha256HexFromFile -LiteralPath $stdoutPath
        stderr_sha256 = Get-Sha256HexFromFile -LiteralPath $stderrPath
        working_directory = $Manifest.run_directory
    }
    $Manifest.preflight = $preflightRecord
    $Manifest.preflights = @($Manifest.preflights) + @($preflightRecord)
    if ($result.TimedOut) {
        $Manifest.capacity.cli_override_status = 'preflight_timed_out'
        throw 'Codex feature preflight timed out.'
    }
    if ($result.OutputLimitExceeded) {
        $Manifest.capacity.cli_override_status = 'preflight_output_limit_exceeded'
        throw 'Codex feature preflight exceeded its output limit.'
    }
    if ($result.ExitCode -ne 0) {
        $Manifest.capacity.cli_override_status = 'rejected_by_cli_preflight'
        throw "Codex feature preflight failed with code $($result.ExitCode): $stderr"
    }
    try { Test-CodexFeaturePreflightOutput -Text $stdout }
    catch {
        $Manifest.capacity.cli_override_status = 'rejected_by_cli_preflight'
        throw
    }
    $Manifest.capacity.cli_override_status = 'accepted_by_cli_preflight'
    $Manifest.status = 'preflight_passed'
    Save-Manifest -Manifest $Manifest -ManifestPath $ManifestPath
}

function Assert-TurnContinuityGatePassed {
    param(
        [Parameter(Mandatory = $true)]$Turn,
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Manifest,
        [Parameter(Mandatory = $true)][string]$ManifestPath
    )
    $message = [string]$Turn.Events.LastAgentMessage
    if ([string]::IsNullOrWhiteSpace($message)) {
        $Turn.Segment.status = 'missing_final_agent_message'
        Save-Manifest -Manifest $Manifest -ManifestPath $ManifestPath
        throw 'Research turn completed without a final agent message.'
    }
    if ($message.Trim() -ceq 'MATH_RESEARCH_GOAL_MISSING_OR_MISMATCHED') {
        $Turn.Segment.status = 'goal_continuity_failed'
        Save-Manifest -Manifest $Manifest -ManifestPath $ManifestPath
        throw 'The in-thread Goal continuity gate reported a missing or mismatched Goal.'
    }
}

function Import-CycleControllerBundle {
    $modulePath = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'MathResearchCycleLedgerLegacyV1Compat.psm1'))
    $cliPath = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'invoke_math_research_cycle_legacy_v1_compat.ps1'))
    $projectModulePath = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'MathResearchProjectArchive.psm1'))
    foreach ($path in @($modulePath, $cliPath, $projectModulePath)) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Required cycle-controller file is missing: $path" }
        Assert-NoReparsePointChain -LiteralPath $path | Out-Null
    }
    Import-Module $modulePath -Force -DisableNameChecking
    foreach ($commandName in @(
        'Initialize-MathResearchCycleLedger',
        'Verify-MathResearchCycleLedger',
        'Invoke-MathResearchCycleReturnCheck',
        'Save-MathResearchCycleCheckpoint')) {
        if ($null -eq (Get-Command $commandName -ErrorAction SilentlyContinue)) {
            throw "Cycle-controller module does not export required command: $commandName"
        }
    }
    return [pscustomobject]@{
        ModulePath = $modulePath
        ModuleSha256 = Get-Sha256HexFromFile -LiteralPath $modulePath
        CliPath = $cliPath
        CliSha256 = Get-Sha256HexFromFile -LiteralPath $cliPath
        ProjectModulePath = $projectModulePath
        ProjectModuleSha256 = Get-Sha256HexFromFile -LiteralPath $projectModulePath
    }
}

function Assert-CycleControllerBundleMatchesManifest {
    param(
        [Parameter(Mandatory = $true)]$Bundle,
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Manifest
    )
    if ($null -eq $Manifest.cycle_ledger) { throw 'Cycle Prompt manifest is missing cycle_ledger.' }
    $bundleItems = @(
        @($Bundle.ModulePath, [string]$Manifest.cycle_ledger.module.path, $Bundle.ModuleSha256, [string]$Manifest.cycle_ledger.module.sha256, 'module'),
        @($Bundle.CliPath, [string]$Manifest.cycle_ledger.cli.path, $Bundle.CliSha256, [string]$Manifest.cycle_ledger.cli.sha256, 'CLI'))
    if ([string]$Manifest.prompt_version -in @('v5','v6')) { $bundleItems += ,@($Bundle.ProjectModulePath, [string]$Manifest.cycle_ledger.project_module.path, $Bundle.ProjectModuleSha256, [string]$Manifest.cycle_ledger.project_module.sha256, 'project module') }
    foreach ($item in $bundleItems) {
        if (-not ([string]$item[0]).Equals([string]$item[1], [StringComparison]::OrdinalIgnoreCase)) {
            throw "Cycle-controller $($item[4]) path differs from the signed manifest."
        }
        if (-not (Test-FixedTimeHexEqual -Left ([string]$item[2]) -Right ([string]$item[3]))) {
            throw "Cycle-controller $($item[4]) SHA-256 differs from the signed manifest."
        }
    }
}

function Update-CycleCheckpoint {
    param(
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Manifest,
        [Parameter(Mandatory = $true)][string]$RunPath,
        [Parameter(Mandatory = $true)][string]$ManifestPath,
        [switch]$DoNotSaveManifest
    )
    $verified = Verify-MathResearchCycleLedger -RunDirectory $RunPath
    $checkpoint = Save-MathResearchCycleCheckpoint -RunDirectory $RunPath
    if ($null -eq $checkpoint) { throw 'Cycle controller returned an empty checkpoint.' }
    $Manifest.cycle_ledger.checkpoint = $checkpoint
    $Manifest.cycle_ledger.last_verified_at_utc = Get-UtcNowString
    if (-not $DoNotSaveManifest) { Save-Manifest -Manifest $Manifest -ManifestPath $ManifestPath }
    return $verified
}

function Complete-CycleReturnAndCheckpoint {
    param(
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Manifest,
        [Parameter(Mandatory = $true)][string]$RunPath,
        [Parameter(Mandatory = $true)][string]$ManifestPath
    )
    Invoke-MathResearchCycleReturnCheck -RunDirectory $RunPath | Out-Null
    $verified = Update-CycleCheckpoint -Manifest $Manifest -RunPath $RunPath -ManifestPath $ManifestPath -DoNotSaveManifest
    if ($null -eq $verified.CleanReturn -or -not [bool]$verified.CleanReturn) {
        throw 'Cycle ReturnCheck did not produce a clean return state.'
    }
    Save-Manifest -Manifest $Manifest -ManifestPath $ManifestPath
    return $verified
}

function Assert-ResumeManifest {
    param(
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Manifest,
        [Parameter(Mandatory = $true)][string]$RunPath,
        $RunContext
    )
    if ($Manifest.schema_version -ne 1) { throw 'Unsupported run manifest schema.' }
    if ([string]$Manifest.prompt_version -notin @('v3', 'v4', 'v5', 'v6')) { throw 'Resume requires a v3, v4, v5, or v6 research run manifest.' }
    if ($null -ne $RunContext -and [string]$Manifest.prompt_version -in @('v3','v4') -and [string]$RunContext.Layout -cne 'legacy') { throw 'Legacy v3/v4 runs may Resume only from the original legacy runs root.' }
    if ([string]$Manifest.prompt_version -in @('v5','v6') -and ($null -eq $RunContext -or [string]$RunContext.Layout -cne 'project')) { throw 'Prompt v5/v6 may Resume only from its verified project archive runs directory.' }
    if (-not ([string]$Manifest.run_directory).Equals($RunPath, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Manifest run_directory does not match -RunDirectory.'
    }
    $thread = [Guid]::Empty
    if (-not [Guid]::TryParseExact([string]$Manifest.thread_id, 'D', [ref]$thread)) {
        throw 'Manifest does not contain a canonical UUID thread id.'
    }
    if ($Manifest.config.max_child_agents -lt 1 -or $Manifest.config.max_child_agents -gt 16) {
        throw 'Manifest contains an invalid child-agent cap.'
    }
    if ($Manifest.config.max_total_agents -ne $Manifest.config.max_child_agents + 1) {
        throw 'Manifest total-agent cap is inconsistent.'
    }
    $expectedStages = @(Get-AgentStages -MaxChildAgents ([int]$Manifest.config.max_child_agents))
    $recordedStages = @($Manifest.config.agent_stages | ForEach-Object { [int]$_ })
    if (($expectedStages | ConvertTo-Json -Compress) -cne ($recordedStages | ConvertTo-Json -Compress)) {
        throw 'Manifest adaptive child-agent stages are inconsistent.'
    }
    if ([int]$Manifest.config.max_runtime_minutes -lt 0 -or [int]$Manifest.config.max_runtime_minutes -gt 525600) {
        throw 'Manifest contains an invalid per-segment runtime limit.'
    }
    if ([string]$Manifest.config.web_search -notin @('allowed', 'denied')) { throw 'Manifest contains an invalid web-search policy.' }
    if ([string]$Manifest.config.reasoning_effort -notin @('minimal', 'low', 'medium', 'high', 'xhigh', 'max', 'ultra')) { throw 'Manifest contains an invalid reasoning effort.' }
    $hashes = @(
        [string]$Manifest.inputs.prompt.sha256,
        [string]$Manifest.inputs.goal_objective.file_sha256,
        [string]$Manifest.goal.objective_sha256)
    if ($Manifest.prompt_version -eq 'v3') {
        if ([int]$Manifest.config.round_budget -lt 1) { throw 'Legacy v3 manifest contains an invalid round budget.' }
        if ($null -eq $Manifest.prompt_v3 -or $Manifest.prompt_v3.status -ne 'turn_completed') {
            throw 'Resume is refused because the full Prompt v3 turn was not completed successfully in this thread.'
        }
        $hashes += [string]$Manifest.prompt_v3.submitted_sha256
    }
    else {
        $promptState = if ([string]$Manifest.prompt_version -eq 'v6') { $Manifest.prompt_v6 } elseif ([string]$Manifest.prompt_version -eq 'v5') { $Manifest.prompt_v5 } else { $Manifest.prompt_v4 }
        if ([int]$Manifest.config.total_round_budget -lt 1) { throw 'Cycle Prompt manifest contains an invalid total round budget.' }
        if ([int]$Manifest.config.attempt_budget -lt 1 -or [int]$Manifest.config.attempt_budget -gt [int]$Manifest.config.total_round_budget) { throw 'Cycle Prompt manifest contains an invalid attempt budget.' }
        if ([int]$Manifest.config.audit_interval_attempts -lt 1) { throw 'Cycle Prompt manifest contains an invalid audit interval.' }
        if ([string]$Manifest.config.round_budget_enforcement -cne 'cycle_controller') { throw 'Cycle Prompt manifest does not bind budget enforcement to the cycle controller.' }
        if ($null -eq $promptState -or [string]$promptState.status -notin @('prepared', 'turn_completed')) {
            throw 'Resume is refused because the full cycle Prompt turn was not prepared or completed in this thread.'
        }
        if ($promptState.status -eq 'prepared') {
            $promptSegment = @($Manifest.segments | Where-Object { [int]$_.index -eq [int]$promptState.segment_index -and $_.kind -eq 'research' })
            if ($promptSegment.Count -ne 1) { throw 'Cycle Prompt recovery Resume has no unique original research segment.' }
        }
        if ($null -eq $Manifest.cycle_ledger) { throw 'Cycle Prompt manifest is missing cycle_ledger.' }
        $hashes += @(
            [string]$promptState.submitted_sha256,
            [string]$Manifest.cycle_ledger.contract_binding_sha256,
            [string]$Manifest.cycle_ledger.module.sha256,
            [string]$Manifest.cycle_ledger.cli.sha256,
            [string]$Manifest.cycle_ledger.policy.sha256,
            [string]$Manifest.cycle_ledger.initial_tickets.sha256)
        $storedBinding = if ([string]$Manifest.prompt_version -in @('v5','v6')) { [string]$Manifest.inputs.prompt.contract_binding_sha256 } else { [string]$Manifest.inputs.prompt.sha256 }
        if ([string]$Manifest.cycle_ledger.contract_binding_sha256 -cne $storedBinding) {
            throw 'Cycle Prompt contract binding does not match the approved PromptFile binding hash.'
        }
        if ([string]$Manifest.prompt_version -in @('v5','v6')) {
            $hashes += [string]$Manifest.inputs.prompt.contract_binding_sha256
            $hashes += [string]$Manifest.cycle_ledger.project_module.sha256
            if ($null -eq $Manifest.project -or [string]$Manifest.project.project_id -cne [string]$RunContext.ProjectId -or [string]$Manifest.project.directory_name -cne [string]$RunContext.ProjectDirectoryName -or [int]$Manifest.project.archive_schema -ne [int]$RunContext.ProjectArchiveSchema) { throw 'Project Prompt manifest identity does not match the live project archive.' }
            $identity = Get-ProjectIdentitySha256 -ProjectArchiveSchema ([int]$RunContext.ProjectArchiveSchema) -ProjectId ([string]$RunContext.ProjectId) -ProjectDirectoryName ([string]$RunContext.ProjectDirectoryName)
            if ([string]$Manifest.project.identity_sha256 -cne $identity) { throw 'Project Prompt manifest identity hash mismatch.' }
        }
    }
    foreach ($hash in $hashes) {
        if ($hash -cnotmatch '^[0-9a-f]{64}$') { throw 'Manifest contains an invalid SHA-256 field.' }
    }
    if ($Manifest.goal.confirmation -ne 'model_reported_via_nonce_marker') {
        throw 'Resume requires a successful Goal bootstrap marker.'
    }
    if ($Manifest.goal.persistence_verified -ne $false) {
        throw 'Unexpected Goal persistence verification value.'
    }
}

Assert-InvocationShape -BoundParameters $invocationParameters

$runPath = $null
$runLease = $null
$runLeaseFile = $null
$threadLease = $null
$manifest = $null
$manifestPath = $null
$cycleController = $null
$cycleState = $null
$fatal = $null

try {
    $runContext = Resolve-ResearchRunContext -RunDirectory $RunDirectory -Operation $Mode
    $runPath = $runContext.RunPath
    $runLease = Enter-NamedLease -Kind run -Value $runPath

    if ($Mode -eq 'New') {
        $promptPath = Resolve-RunInputFile -LiteralPath $PromptFile -RunDirectory $runPath -Label 'PromptFile'
        $goalPath = Resolve-RunInputFile -LiteralPath $GoalObjectiveFile -RunDirectory $runPath -Label 'GoalObjectiveFile'
        if ($promptPath.Equals($goalPath, [StringComparison]::OrdinalIgnoreCase)) {
            throw 'PromptFile and GoalObjectiveFile must be different files.'
        }
        Assert-FreshRunDirectory -RunDirectory $runPath -AllowedInputFiles @($promptPath, $goalPath)
        $runLeaseFile = Open-RunLeaseFile -RunDirectory $runPath

        $promptInfo = Read-StrictUtf8File -LiteralPath $promptPath -MaximumBytes 4194304 -Label 'PromptFile'
        $contractBindingSha256 = Get-Sha256HexFromText -Text ($promptInfo.Text -replace "`r`n", "`n")
        $goalFileInfo = Read-StrictUtf8File -LiteralPath $goalPath -MaximumBytes 16384 -Label 'GoalObjectiveFile'
        $objective = $goalFileInfo.Text.Trim()
        if ($objective.Length -gt 4000) { throw 'Goal objective exceeds the 4,000-character persisted Goal limit.' }
        $objectiveSha256 = Get-Sha256HexFromText -Text $objective
        $metadata = Parse-PromptV6Metadata -PromptText $promptInfo.Text
        Test-PromptMetadataAgainstParameters -Metadata $metadata -MaxChildAgents $MaxChildAgents -Model $Model -ReasoningEffort $ReasoningEffort -MaxRuntimeMinutes $MaxRuntimeMinutes -GoalObjectiveSha256 $objectiveSha256 -RunContext $runContext
        $agentStages = Get-AgentStages -MaxChildAgents $MaxChildAgents

        $cyclePolicyPath = Join-Path $runPath 'cycle-policy.json'
        $initialTicketsPath = Join-Path $runPath 'cycle-tickets-000.json'
        Write-Utf8FileNew -LiteralPath $cyclePolicyPath -Text ([string]$metadata.cycle_policy_json)
        Write-Utf8FileNew -LiteralPath $initialTicketsPath -Text ([string]$metadata.initial_tickets_json)
        if (-not (Test-FixedTimeHexEqual -Left (Get-Sha256HexFromFile -LiteralPath $cyclePolicyPath) -Right ([string]$metadata.cycle_policy_sha256))) {
            throw 'Written cycle-policy.json does not match cycle_policy_sha256.'
        }
        if (-not (Test-FixedTimeHexEqual -Left (Get-Sha256HexFromFile -LiteralPath $initialTicketsPath) -Right ([string]$metadata.initial_tickets_sha256))) {
            throw 'Written cycle-tickets-000.json does not match initial_tickets_sha256.'
        }
        $cycleController = Import-CycleControllerBundle
        Initialize-MathResearchCycleLedger -RunDirectory $runPath -RunId (Split-Path -Leaf $runPath) -ContractSha256 $contractBindingSha256 -PolicyFile $cyclePolicyPath -TicketsFile $initialTicketsPath | Out-Null
        $cycleState = Verify-MathResearchCycleLedger -RunDirectory $runPath
        if ([int]$cycleState.TotalRoundBudget -ne [int]$metadata.total_round_budget -or
            [int]$cycleState.AttemptBudget -ne [int]$metadata.attempt_budget -or
            [int]$cycleState.AuditIntervalAttempts -ne [int]$metadata.audit_interval_attempts) {
            throw 'Cycle policy budgets do not match the Prompt v6 launcher metadata.'
        }
        if ($null -eq $cycleState.CleanReturn -or -not [bool]$cycleState.CleanReturn) {
            throw 'Fresh cycle-ledger genesis is not in a clean return state.'
        }
        $cycleCheckpoint = Save-MathResearchCycleCheckpoint -RunDirectory $runPath

        $manifestPath = Join-Path $runPath $manifestFileName
        $manifest = [ordered]@{
            schema_version = 1
            run_id = Split-Path -Leaf $runPath
            revision = 0
            created_at_utc = Get-UtcNowString
            updated_at_utc = Get-UtcNowString
            prompt_version = 'v6'
            prompt_header = 'Math Research Orchestration Prompt v6'
            contract_version = [string]$metadata.contract_version
            run_directory = $runPath
            project = [ordered]@{
                archive_schema = [int]$runContext.ProjectArchiveSchema
                project_id = [string]$runContext.ProjectId
                directory_name = [string]$runContext.ProjectDirectoryName
                directory = [string]$runContext.ProjectDirectory
                identity_sha256 = [string]$metadata.project_identity_sha256
            }
            invocation_mode = 'new'
            status = 'prepared'
            exit_reason = $null
            thread_id = $null
            launcher = [ordered]@{
                pid = $PID
                powershell_version = $PSVersionTable.PSVersion.ToString()
                coordination_scope = 'launcher_instances_only'
                run_mutex_name = $runLease.Name
                run_mutex_abandoned = [bool]$runLease.Abandoned
                process_creation_suspended = $false
                process_creation_race_note = 'Process is assigned to a kill-on-close Job Object immediately after Process.Start; a small pre-assignment window remains.'
            }
            inputs = [ordered]@{
                prompt = [ordered]@{ file = Get-RelativeRunPath -RunPath $runPath -FilePath $promptPath; sha256 = $promptInfo.Sha256; contract_binding_sha256 = $contractBindingSha256; bytes = $promptInfo.Bytes }
                goal_objective = [ordered]@{ file = Get-RelativeRunPath -RunPath $runPath -FilePath $goalPath; file_sha256 = $goalFileInfo.Sha256; normalized_sha256 = $objectiveSha256; bytes = $goalFileInfo.Bytes }
                continuations = @()
            }
            config = [ordered]@{
                model = $Model
                reasoning_effort = $ReasoningEffort
                web_search = [string]$metadata.web_search
                total_round_budget = [int]$metadata.total_round_budget
                attempt_budget = [int]$metadata.attempt_budget
                audit_interval_attempts = [int]$metadata.audit_interval_attempts
                round_budget_enforcement = 'cycle_controller'
                observed_research_rounds = $null
                max_runtime_minutes = $MaxRuntimeMinutes
                max_runtime_scope = 'per_research_or_resume_exec_segment'
                max_child_agents = $MaxChildAgents
                max_total_agents = $MaxChildAgents + 1
                agent_stages = [int[]]$agentStages
                agents_max_threads = $MaxChildAgents
                sandbox = 'workspace-write'
                approval_policy = 'never'
                ignore_user_config = $true
                ignore_rules = $false
                shell_network_access = $false
                configured_to_disable_user_plugins_and_mcp = $true
                observed_user_plugins_and_mcp_loaded = 'unknown'
            }
            capacity = [ordered]@{
                requested_child_cap = $MaxChildAgents
                configured_child_cap = $MaxChildAgents
                configured_total_cap = $MaxChildAgents + 1
                cli_override_status = 'not_checked'
                runtime_capacity_status = 'unknown'
                verified_runtime_child_cap = $null
                observed_peak_child_agents = $null
                observed_peak_total_agents = $null
                observation_evidence = $null
            }
            isolation = [ordered]@{
                writable_workspace = $runPath
                standard_sandbox_read_isolation_guaranteed = $false
                audit_integrity = 'HMAC-SHA256 with a Windows DPAPI CurrentUser key; this detects ordinary tampering but is not a boundary against hostile same-user code that can access the key.'
                inherited_environment_variable_names = @((Get-SanitizedEnvironment).Keys | Sort-Object)
                custom_base_url_inherited = $false
                proxy_environment_inherited = $false
                api_key_environment_inherited = $false
                canonical_codex_home = Join-Path ([Environment]::GetFolderPath([Environment+SpecialFolder]::UserProfile)) '.codex'
                credential_isolation_guaranteed = $false
                path_is_inherited = $true
            }
            executable = $null
            preflight = $null
            preflights = @()
            goal = [ordered]@{
                objective_sha256 = $objectiveSha256
                confirmation = 'not_started'
                persistence_verified = $false
                confirmation_trust = 'none'
                observed_status = $null
                nonce = $null
            }
            prompt_v6 = [ordered]@{
                status = 'not_started'
                segment_index = $null
                submitted_sha256 = $null
                turn_completed_at_utc = $null
            }
            cycle_ledger = [ordered]@{
                contract_binding_sha256 = $contractBindingSha256
                module = [ordered]@{ path = $cycleController.ModulePath; sha256 = $cycleController.ModuleSha256 }
                cli = [ordered]@{ path = $cycleController.CliPath; sha256 = $cycleController.CliSha256 }
                project_module = [ordered]@{ path = $cycleController.ProjectModulePath; sha256 = $cycleController.ProjectModuleSha256 }
                policy = [ordered]@{ path = $cyclePolicyPath; sha256 = [string]$metadata.cycle_policy_sha256 }
                initial_tickets = [ordered]@{ path = $initialTicketsPath; sha256 = [string]$metadata.initial_tickets_sha256 }
                checkpoint = $cycleCheckpoint
                last_verified_at_utc = Get-UtcNowString
            }
            process = $null
            next_segment_index = 0
            segments = @()
            token_usage = [ordered]@{ input_tokens = 0L; cached_input_tokens = 0L; output_tokens = 0L; reasoning_output_tokens = 0L }
            global_config_modified = $false
            actual_observed_peak_child_agents = $null
        }
        Save-Manifest -Manifest $manifest -ManifestPath $manifestPath -CreateKeyIfMissing

        $attestation = Select-TrustedCodexExecutable -WorkingDirectory $runPath
        $manifest.executable = [ordered]@{
            path = $attestation.path
            version = $attestation.version
            sha256 = $attestation.sha256
            signature_status = $attestation.signature_status
            signer_name = $attestation.signer_name
            signer_subject = $attestation.signer_subject
            signer_thumbprint = $attestation.signer_thumbprint
            selection = 'highest_semantic_version'
            downgrade_fallback = $false
        }
        Save-Manifest -Manifest $manifest -ManifestPath $manifestPath
        Invoke-FeaturePreflight -Manifest $manifest -ManifestPath $manifestPath -Attestation $attestation -ChildCap $MaxChildAgents

        $nonceBytes = [byte[]]::new(32)
        [Security.Cryptography.RandomNumberGenerator]::Fill($nonceBytes)
        $nonce = [Convert]::ToHexString($nonceBytes).ToLowerInvariant()
        [Array]::Clear($nonceBytes, 0, $nonceBytes.Length)
        $goalBootstrapPath = Join-Path $runPath 'goal-bootstrap.md'
        $goalSchemaPath = Join-Path $runPath 'goal-output-schema.json'
        $goalBootstrap = New-GoalBootstrapPrompt -Objective $objective -ObjectiveSha256 $objectiveSha256 -Nonce $nonce
        $goalSchema = New-GoalOutputSchema -ObjectiveSha256 $objectiveSha256 -Nonce $nonce
        Write-Utf8FileNew -LiteralPath $goalBootstrapPath -Text $goalBootstrap
        Write-Utf8FileNew -LiteralPath $goalSchemaPath -Text ($goalSchema | ConvertTo-Json -Depth 16)
        $manifest.goal.nonce = $nonce
        $manifest.status = 'goal_bootstrap_running'
        Save-Manifest -Manifest $manifest -ManifestPath $manifestPath

        $goalPaths = New-SegmentPaths -RunPath $runPath -Index ([int]$manifest.next_segment_index) -Kind goal
        $goalArguments = New-CodexExecArguments -RunDirectory $runPath -Model $Model -ReasoningEffort $ReasoningEffort -Sandbox 'read-only' -AllowWebSearch:$false -EnableMultiAgent:$false -MaxChildAgents 1 -LastMessagePath $goalPaths.LastMessage -OutputSchemaPath $goalSchemaPath
        $goalTurn = Invoke-JsonSegment -Manifest $manifest -ManifestPath $manifestPath -Attestation $attestation -Arguments $goalArguments -PromptText $goalBootstrap -Kind goal -TimeoutMilliseconds $goalBootstrapTimeoutMilliseconds
        if (-not (Test-Path -LiteralPath $goalTurn.Paths.LastMessage -PathType Leaf)) {
            throw 'Goal bootstrap did not write the required final-message file.'
        }
        $goalLastMessageInfo = Read-StrictUtf8File -LiteralPath $goalTurn.Paths.LastMessage -MaximumBytes 65536 -Label 'Goal final message'
        $goalLastMessage = $goalLastMessageInfo.Text
        if ($goalTurn.Events.LastAgentMessage.Trim() -cne $goalLastMessage.Trim()) {
            throw 'Goal bootstrap JSONL final agent message differs from the -o final-message file.'
        }
        $goalMarker = Test-GoalReadyMarker -Message $goalLastMessage.Trim() -ObjectiveSha256 $objectiveSha256 -Nonce $nonce
        $manifest.thread_id = $goalTurn.Events.ThreadId
        $threadLease = Enter-NamedLease -Kind thread -Value $manifest.thread_id
        $manifest.launcher.thread_mutex_name = $threadLease.Name
        $manifest.launcher.thread_mutex_abandoned = [bool]$threadLease.Abandoned
        $manifest.goal.confirmation = 'model_reported_via_nonce_marker'
        $manifest.goal.persistence_verified = $false
        $manifest.goal.confirmation_trust = 'model_report_only_exec_jsonl_does_not_expose_goal_function_calls'
        $manifest.goal.observed_status = $goalMarker.observed_status
        $manifest.status = 'goal_model_reported'
        Save-Manifest -Manifest $manifest -ManifestPath $manifestPath

        $cycleState = Update-CycleCheckpoint -Manifest $manifest -RunPath $runPath -ManifestPath $manifestPath
        $researchTurnPath = Join-Path $runPath 'research-turn.md'
        $researchTurnPrompt = New-CycleResearchTurnPrompt -Objective $objective -ObjectiveSha256 $objectiveSha256 -PromptText $promptInfo.Text -MaxChildAgents $MaxChildAgents -AgentStages $agentStages -TotalRoundBudget ([int]$metadata.total_round_budget) -AttemptBudget ([int]$metadata.attempt_budget) -AuditIntervalAttempts ([int]$metadata.audit_interval_attempts) -MaxRuntimeMinutes $MaxRuntimeMinutes -WebSearch ([string]$metadata.web_search) -RunDirectory $runPath -CycleCliPath $cycleController.CliPath -CycleCliSha256 $cycleController.CliSha256 -CyclePolicyFile $cyclePolicyPath -CyclePolicySha256 ([string]$metadata.cycle_policy_sha256) -InitialTicketsFile $initialTicketsPath -InitialTicketsSha256 ([string]$metadata.initial_tickets_sha256) -ContractBindingSha256 $contractBindingSha256 -CycleState $cycleState
        Write-Utf8FileNew -LiteralPath $researchTurnPath -Text $researchTurnPrompt
        $manifest.inputs.research_turn = [ordered]@{
            file = 'research-turn.md'
            sha256 = Get-Sha256HexFromFile -LiteralPath $researchTurnPath
            bytes = (Get-Item -LiteralPath $researchTurnPath).Length
        }
        $manifest.prompt_v6.status = 'prepared'
        $manifest.prompt_v6.segment_index = [int]$manifest.next_segment_index
        $manifest.prompt_v6.submitted_sha256 = $manifest.inputs.research_turn.sha256
        $manifest.status = 'research_running'
        Save-Manifest -Manifest $manifest -ManifestPath $manifestPath

        $researchPaths = New-SegmentPaths -RunPath $runPath -Index ([int]$manifest.next_segment_index) -Kind research
        $allowSearch = $metadata.web_search -eq 'allowed'
        $researchArguments = New-CodexExecArguments -RunDirectory $runPath -Model $Model -ReasoningEffort $ReasoningEffort -Sandbox 'workspace-write' -AllowWebSearch:$allowSearch -EnableMultiAgent:$true -MaxChildAgents $MaxChildAgents -LastMessagePath $researchPaths.LastMessage -ResumeThreadId $manifest.thread_id
        $researchTimeout = if ($MaxRuntimeMinutes -eq 0) { 0L } else { [long]$MaxRuntimeMinutes * 60L * 1000L }
        $researchTurn = Invoke-JsonSegment -Manifest $manifest -ManifestPath $manifestPath -Attestation $attestation -Arguments $researchArguments -PromptText $researchTurnPrompt -Kind research -TimeoutMilliseconds $researchTimeout -ExpectedThreadId $manifest.thread_id
        Assert-TurnContinuityGatePassed -Turn $researchTurn -Manifest $manifest -ManifestPath $manifestPath
        $cycleState = Complete-CycleReturnAndCheckpoint -Manifest $manifest -RunPath $runPath -ManifestPath $manifestPath
        $manifest.prompt_v6.status = 'turn_completed'
        $manifest.prompt_v6.turn_completed_at_utc = Get-UtcNowString
        $manifest.status = 'turn_completed'
        $manifest.exit_reason = 'research_exec_turn_completed'
        Save-Manifest -Manifest $manifest -ManifestPath $manifestPath
    }
    else {
        $runLeaseFile = Open-RunLeaseFile -RunDirectory $runPath
        $manifestPath = Join-Path $runPath $manifestFileName
        $read = Read-SignedJsonPayload -LiteralPath $manifestPath
        $manifest = $read.Payload
        $receiptRead = Read-MathResearchLegacyV1CompatReceipt -LiteralPath $MigrationReceiptFile
        $controlPathReceiptRead = Read-MathResearchLegacyV1ControlPathReceiptV2 -LiteralPath $ControlPathReceiptFile
        $priorCompatLauncherEntryPath = Join-Path $PSScriptRoot 'launch_math_research_legacy_v1_compat.ps1'
        $compatLauncherModulePath = Join-Path $PSScriptRoot 'MathResearchLauncherLegacyV1Compat.psm1'
        $compatCycleModulePath = Join-Path $PSScriptRoot 'MathResearchCycleLedgerLegacyV1Compat.psm1'
        $compatCycleCliPath = Join-Path $PSScriptRoot 'invoke_math_research_cycle_legacy_v1_compat.ps1'
        $compatProjectModulePath = Join-Path $PSScriptRoot 'MathResearchProjectArchive.psm1'
        $priorCompatCanaryHostPath = Join-Path $PSScriptRoot 'invoke_math_research_legacy_v1_compat_canary_host.ps1'
        $compatCanaryHostPath = Join-Path $PSScriptRoot 'invoke_math_research_legacy_v1_compat_canary_host_v2.ps1'
        $installedCanaryEntryPath = Join-Path $PSScriptRoot 'invoke_math_research_canary_v2.ps1'
        Assert-MathResearchLegacyV1CompatState -Manifest $manifest -RunPath $runPath -ReceiptRead $receiptRead -LauncherEntryPath $priorCompatLauncherEntryPath -LauncherModulePath $compatLauncherModulePath -CycleModulePath $compatCycleModulePath -CycleCliPath $compatCycleCliPath -ProjectModulePath $compatProjectModulePath -CanaryHostPath $priorCompatCanaryHostPath -CanaryEntryPath $installedCanaryEntryPath -RequireApplied | Out-Null
        $controlPathPaths = @{
            PriorLauncherEntry=$priorCompatLauncherEntryPath; LauncherEntry=$PSCommandPath; LauncherModule=$compatLauncherModulePath
            ArgvCompatModule=(Join-Path $PSScriptRoot 'MathResearchApproveForMeArgvCompatV2.psm1')
            PriorCanaryHost=$priorCompatCanaryHostPath; CanaryHost=$compatCanaryHostPath
            CanaryModule=(Join-Path $PSScriptRoot 'MathResearchLauncherV2.psm1'); CanaryEntry=$installedCanaryEntryPath
            CycleModule=$compatCycleModulePath; CycleCli=$compatCycleCliPath; ProjectModule=$compatProjectModulePath
            AmendmentModule=(Join-Path $PSScriptRoot 'MathResearchLegacyV1ControlPathAmendmentV2.psm1')
            AmendmentCli=(Join-Path $PSScriptRoot 'invoke_math_research_legacy_v1_control_path_amendment_v2.ps1')
        }
        Assert-MathResearchLegacyV1ControlPathAmendmentV2State -Manifest $manifest -RunPath $runPath -ReceiptRead $controlPathReceiptRead -PriorReceiptRead $receiptRead -Paths $controlPathPaths -RequireApplied | Out-Null
        Assert-ResumeManifest -Manifest $manifest -RunPath $runPath -RunContext $runContext
        $resumeCycleMode = 'legacy_v3'
        if ($manifest.prompt_version -in @('v4','v5','v6')) {
            $cycleController = Import-CycleControllerBundle
            Assert-CycleControllerBundleMatchesManifest -Bundle $cycleController -Manifest $manifest
            foreach ($cycleInput in @(
                @([string]$manifest.cycle_ledger.policy.path, [string]$manifest.cycle_ledger.policy.sha256, 'cycle-policy.json'),
                @([string]$manifest.cycle_ledger.initial_tickets.path, [string]$manifest.cycle_ledger.initial_tickets.sha256, 'cycle-tickets-000.json'))) {
                $cycleInputPath = Assert-NoReparsePointChain -LiteralPath ([string]$cycleInput[0])
                if (-not (Split-Path -Parent $cycleInputPath).Equals($runPath, [StringComparison]::OrdinalIgnoreCase) -or
                    -not (Split-Path -Leaf $cycleInputPath).Equals([string]$cycleInput[2], [StringComparison]::OrdinalIgnoreCase)) {
                    throw "Cycle input path is outside the expected run-local location: $cycleInputPath"
                }
                if (-not (Test-FixedTimeHexEqual -Left (Get-Sha256HexFromFile -LiteralPath $cycleInputPath) -Right ([string]$cycleInput[1]))) {
                    throw "Cycle input SHA-256 differs from the signed manifest: $cycleInputPath"
                }
            }
            $cycleState = Update-CycleCheckpoint -Manifest $manifest -RunPath $runPath -ManifestPath $manifestPath
            $resumeCycleMode = if ($null -ne $cycleState.CleanReturn -and [bool]$cycleState.CleanReturn) { 'normal' } else { 'recovery_or_audit_only' }
        }
        if ($read.RecoveredFromBackup) {
            $manifest.recovered_from_manifest_backup = $true
            Save-Manifest -Manifest $manifest -ManifestPath $manifestPath
        }
        if (Test-ProcessIdentityFromManifest -ProcessRecord $manifest.process) {
            throw 'The manifest still identifies a live Codex process; concurrent Resume is refused.'
        }
        $threadLease = Enter-NamedLease -Kind thread -Value ([string]$manifest.thread_id)
        $manifest.launcher.run_mutex_name = $runLease.Name
        $manifest.launcher.run_mutex_abandoned = [bool]$runLease.Abandoned
        $manifest.launcher.thread_mutex_name = $threadLease.Name
        $manifest.launcher.thread_mutex_abandoned = [bool]$threadLease.Abandoned
        $manifest.launcher.pid = $PID

        $continuationPath = Resolve-RunInputFile -LiteralPath $ContinuationPromptFile -RunDirectory $runPath -Label 'ContinuationPromptFile'
        $continuationInfo = Read-StrictUtf8File -LiteralPath $continuationPath -MaximumBytes 1048576 -Label 'ContinuationPromptFile'
        Assert-ContinuationInstruction -Text $continuationInfo.Text -Sha256 $continuationInfo.Sha256 -OriginalPromptSha256 ([string]$manifest.inputs.prompt.sha256)
        $storedGoalPath = Join-Path $runPath ([string]$manifest.inputs.goal_objective.file)
        $storedGoalPath = Resolve-RunInputFile -LiteralPath $storedGoalPath -RunDirectory $runPath -Label 'Stored GoalObjectiveFile'
        $storedGoalInfo = Read-StrictUtf8File -LiteralPath $storedGoalPath -MaximumBytes 16384 -Label 'Stored GoalObjectiveFile'
        if (-not (Test-FixedTimeHexEqual -Left $storedGoalInfo.Sha256 -Right ([string]$manifest.inputs.goal_objective.file_sha256))) {
            throw 'Stored GoalObjectiveFile no longer matches its signed file hash.'
        }
        $storedObjective = $storedGoalInfo.Text.Trim()
        if ((Get-Sha256HexFromText -Text $storedObjective) -cne [string]$manifest.goal.objective_sha256) {
            throw 'Stored GoalObjectiveFile no longer matches the Goal objective hash.'
        }
        if ($manifest.prompt_version -in @('v4','v5','v6')) {
            $continuationTurnPrompt = New-CycleContinuationTurnPrompt -Objective $storedObjective -ObjectiveSha256 ([string]$manifest.goal.objective_sha256) -ContinuationText $continuationInfo.Text -MaxChildAgents ([int]$manifest.config.max_child_agents) -AgentStages ([int[]]$manifest.config.agent_stages) -TotalRoundBudget ([int]$manifest.config.total_round_budget) -AttemptBudget ([int]$manifest.config.attempt_budget) -AuditIntervalAttempts ([int]$manifest.config.audit_interval_attempts) -MaxRuntimeMinutes ([int]$manifest.config.max_runtime_minutes) -WebSearch ([string]$manifest.config.web_search) -RunDirectory $runPath -CycleCliPath $cycleController.CliPath -CycleCliSha256 $cycleController.CliSha256 -CyclePolicyFile ([string]$manifest.cycle_ledger.policy.path) -CyclePolicySha256 ([string]$manifest.cycle_ledger.policy.sha256) -InitialTicketsFile ([string]$manifest.cycle_ledger.initial_tickets.path) -InitialTicketsSha256 ([string]$manifest.cycle_ledger.initial_tickets.sha256) -ContractBindingSha256 ([string]$manifest.cycle_ledger.contract_binding_sha256) -CycleState $cycleState -ResumeMode $resumeCycleMode
        }
        else {
            $continuationTurnPrompt = New-ContinuationTurnPrompt -Objective $storedObjective -ObjectiveSha256 ([string]$manifest.goal.objective_sha256) -ContinuationText $continuationInfo.Text -MaxChildAgents ([int]$manifest.config.max_child_agents) -AgentStages ([int[]]$manifest.config.agent_stages) -RoundBudget ([int]$manifest.config.round_budget) -MaxRuntimeMinutes ([int]$manifest.config.max_runtime_minutes) -WebSearch ([string]$manifest.config.web_search)
        }
        $manifest.invocation_mode = 'resume'
        $manifest.status = 'resume_preflight'
        $manifest.exit_reason = $null
        Save-Manifest -Manifest $manifest -ManifestPath $manifestPath

        $attestation = Select-TrustedCodexExecutable -WorkingDirectory $runPath
        if ([string]$attestation.version -cne [string]$manifest.executable.version -or
            -not (Test-FixedTimeHexEqual -Left ([string]$attestation.sha256) -Right ([string]$manifest.executable.sha256))) {
            throw "Resume is pinned to Codex $($manifest.executable.version) with SHA-256 $($manifest.executable.sha256). The currently selected highest signed executable is $($attestation.version) with SHA-256 $($attestation.sha256). Automatic upgrade or downgrade is refused; start a new reviewed run after a CLI change."
        }
        $manifest.executable.last_resume_attestation_at_utc = Get-UtcNowString
        Save-Manifest -Manifest $manifest -ManifestPath $manifestPath
        Invoke-FeaturePreflight -Manifest $manifest -ManifestPath $manifestPath -Attestation $attestation -ChildCap ([int]$manifest.config.max_child_agents)
        $manifest.status = 'canary_running'
        Save-Manifest -Manifest $manifest -ManifestPath $manifestPath
        $pwsh = (Get-Process -Id $PID).Path
        $canaryOutput = & $pwsh -NoLogo -NoProfile -File $compatCanaryHostPath -RunDirectory $runPath -ManifestPath $manifestPath -MigrationReceiptFile $MigrationReceiptFile -ControlPathReceiptFile $ControlPathReceiptFile
        if ($LASTEXITCODE -ne 0) { throw "Compatibility launcher canary failed with exit code $LASTEXITCODE." }
        $canaryText = @($canaryOutput) -join "`n"
        try { $canary = $canaryText | ConvertFrom-Json -AsHashtable -Depth 16 -DateKind String }
        catch { throw 'Compatibility launcher canary returned malformed JSON.' }
        if (-not [bool]$canary.Passed) { throw 'Compatibility launcher canary did not pass.' }
        $manifest.control_path_amendment_v2['canary'] = [ordered]@{ protocol='math-research-launcher-canary/v2'; receipt_path=[string]$canary.ReceiptPath; binding_sha256=[string]$canary.BindingSha256; reused=[bool]$canary.Reused; passed=[bool]$canary.Passed }
        $manifest.status = 'canary_passed'
        Save-Manifest -Manifest $manifest -ManifestPath $manifestPath

        $submittedBytes = [Text.UTF8Encoding]::new($false).GetByteCount($continuationTurnPrompt)
        $manifest.inputs.continuations = @($manifest.inputs.continuations) + @([ordered]@{
            source_file = Get-RelativeRunPath -RunPath $runPath -FilePath $continuationPath
            source_sha256 = $continuationInfo.Sha256
            source_bytes = $continuationInfo.Bytes
            submitted_file = $null
            submitted_sha256 = Get-Sha256HexFromText -Text $continuationTurnPrompt
            submitted_bytes = $submittedBytes
            submitted_at_utc = Get-UtcNowString
            wrapper = if ($manifest.prompt_version -in @('v4','v5','v6')) { "launcher_enforced_cycle_continuation_gate_v1:$resumeCycleMode" } else { 'launcher_enforced_continuation_gate_v1' }
        })
        $manifest.status = 'research_resume_running'
        Save-Manifest -Manifest $manifest -ManifestPath $manifestPath
        $resumePaths = New-SegmentPaths -RunPath $runPath -Index ([int]$manifest.next_segment_index) -Kind resume
        $allowSearch = $manifest.config.web_search -eq 'allowed'
        $resumeArguments = New-CodexExecArguments -RunDirectory $runPath -Model ([string]$manifest.config.model) -ReasoningEffort ([string]$manifest.config.reasoning_effort) -Sandbox 'workspace-write' -AllowWebSearch:$allowSearch -EnableMultiAgent:$true -MaxChildAgents ([int]$manifest.config.max_child_agents) -LastMessagePath $resumePaths.LastMessage -ResumeThreadId ([string]$manifest.thread_id)
        Assert-MathResearchApproveForMeArgvCompatV2 -Arguments $resumeArguments | Out-Null
        $resumeTimeout = if ([int]$manifest.config.max_runtime_minutes -eq 0) { 0L } else { [long]$manifest.config.max_runtime_minutes * 60L * 1000L }
        $resumeTurn = Invoke-JsonSegment -Manifest $manifest -ManifestPath $manifestPath -Attestation $attestation -Arguments $resumeArguments -PromptText $continuationTurnPrompt -Kind resume -TimeoutMilliseconds $resumeTimeout -ExpectedThreadId ([string]$manifest.thread_id)
        Assert-TurnContinuityGatePassed -Turn $resumeTurn -Manifest $manifest -ManifestPath $manifestPath
        if ($manifest.prompt_version -in @('v4','v5','v6')) {
            $cycleState = Complete-CycleReturnAndCheckpoint -Manifest $manifest -RunPath $runPath -ManifestPath $manifestPath
        }
        $manifest.status = 'turn_completed'
        $manifest.exit_reason = 'resume_exec_turn_completed'
        Save-Manifest -Manifest $manifest -ManifestPath $manifestPath
    }

    [pscustomobject]@{
        RunDirectory = $runPath
        Manifest = $manifestPath
        ThreadId = $manifest.thread_id
        Status = $manifest.status
        MaxChildAgents = $manifest.config.max_child_agents
        MaxTotalAgents = $manifest.config.max_total_agents
        ActualObservedPeakChildAgents = $null
        GoalConfirmation = $manifest.goal.confirmation
        GoalPersistenceVerified = $false
        TokenUsage = $manifest.token_usage
    } | ConvertTo-Json -Depth 8
}
catch {
    $fatal = $_
    if ($manifest -and $manifestPath) {
        try {
            if ($cycleController -and $manifest.prompt_version -in @('v4','v5','v6') -and $null -ne $manifest.cycle_ledger) {
                try {
                    Verify-MathResearchCycleLedger -RunDirectory $runPath | Out-Null
                    $manifest.cycle_ledger.checkpoint = Save-MathResearchCycleCheckpoint -RunDirectory $runPath
                    $manifest.cycle_ledger.last_verified_at_utc = Get-UtcNowString
                }
                catch {
                    [Console]::Error.WriteLine("Best-effort cycle-ledger verification after failure also failed: $($_.Exception.Message)")
                }
            }
            $manifest.status = if ($manifest.segments.Count -gt 0 -and $manifest.segments[-1].status -eq 'timed_out') { 'timed_out' } elseif ($manifest.segments.Count -gt 0 -and $manifest.segments[-1].status -eq 'stopped') { 'stopped' } else { 'failed' }
            $manifest.exit_reason = $fatal.Exception.Message
            $manifest.process = $null
            Save-Manifest -Manifest $manifest -ManifestPath $manifestPath
        }
        catch { [Console]::Error.WriteLine("Manifest failure-state update failed: $($_.Exception.Message)") }
    }
    throw
}
finally {
    if ($threadLease) { Exit-NamedLease -Lease $threadLease }
    if ($runLeaseFile) { $runLeaseFile.Dispose() }
    if ($runLease) { Exit-NamedLease -Lease $runLease }
}
