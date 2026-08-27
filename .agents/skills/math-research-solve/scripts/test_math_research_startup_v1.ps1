[CmdletBinding()]
param()

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
$script:assertions = 0

function Assert-Equal {
    param($Actual, $Expected, [string]$Label)
    $script:assertions++
    if ($Actual -cne $Expected) { throw "$Label expected '$Expected' but got '$Actual'." }
}

function Assert-True {
    param([bool]$Condition, [string]$Label)
    $script:assertions++
    if (-not $Condition) { throw "$Label expected true." }
}

function Get-RawSha256 {
    param([string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-NormalizedSha256 {
    param([string]$Path)
    $text = [IO.File]::ReadAllText($Path, [Text.UTF8Encoding]::new($false, $true)) -replace "`r`n", "`n"
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.UTF8Encoding]::new($false).GetBytes($text))).ToLowerInvariant()
}

function Write-JsonObject {
    param([string]$Path, [Collections.IDictionary]$Value)
    [IO.File]::WriteAllText($Path, (($Value | ConvertTo-Json -Depth 64) + "`n"), [Text.UTF8Encoding]::new($false))
}

function Invoke-Router {
    param([hashtable]$Parameters)
    $output = & $script:router @Parameters
    return ($output | ConvertFrom-Json -AsHashtable -Depth 64)
}

$candidateRoot = Split-Path -Parent $PSScriptRoot
$sourceRouter = Join-Path $candidateRoot 'scripts\invoke_math_research_startup_v1.ps1'
$installedScripts = Join-Path $candidateRoot 'scripts'
$temp = Join-Path ([IO.Path]::GetTempPath()) ('math-research-startup-v1-' + [guid]::NewGuid().ToString('N'))
$scriptRoot = Join-Path $temp 'skill\scripts'
$vault = Join-Path $temp 'vault'
$projectsRoot = Join-Path $vault '笔记草稿\公开问题的尝试'
New-Item -ItemType Directory -Path $scriptRoot -Force | Out-Null
New-Item -ItemType Directory -Path $projectsRoot -Force | Out-Null
$launcherModule = $null

try {
    Copy-Item -LiteralPath (Join-Path $installedScripts 'invoke_math_research_project.ps1') -Destination $scriptRoot
    Copy-Item -LiteralPath (Join-Path $installedScripts 'observer_run.ps1') -Destination $scriptRoot
    Copy-Item -LiteralPath (Join-Path $installedScripts 'MathResearchProjectArchive.psm1') -Destination $scriptRoot
    Copy-Item -LiteralPath (Join-Path $installedScripts 'MathResearchLegacyArchive.ps1') -Destination $scriptRoot
    Copy-Item -LiteralPath (Join-Path $installedScripts 'MathResearchLauncher.psm1') -Destination $scriptRoot
    Copy-Item -LiteralPath $sourceRouter -Destination $scriptRoot
    $script:router = Join-Path $scriptRoot 'invoke_math_research_startup_v1.ps1'
    Import-Module (Join-Path $scriptRoot 'MathResearchProjectArchive.psm1') -Force -DisableNameChecking
    Import-Module (Join-Path $scriptRoot 'MathResearchLauncher.psm1') -Force -DisableNameChecking
    $launcherModule = Get-Module MathResearchLauncher -All | Select-Object -First 1
    $testManifestKey = Join-Path $temp 'manifest-key\manifest-key.dpapi'
    & $launcherModule { param($Path) $script:ManifestKeyPathOverrideForTests=$Path } $testManifestKey

    $fresh = Invoke-Router -Parameters @{ VaultRoot=$vault; ProjectDirectoryName='fresh-slot'; GoalStatus='none'; ExpectedProjectId='fixture-project-0001' }
    Assert-Equal $fresh.startup_class 'fresh_project_slot' 'fresh slot class'
    Assert-Equal $fresh.controller_call_count 0 'fresh slot controller calls'
    Assert-Equal $fresh.goal_gate 'pre_goal_preparation_only_research_forbidden' 'fresh pre-goal gate'

    $partialPath = Join-Path $projectsRoot 'partial-slot'
    New-Item -ItemType Directory -Path $partialPath | Out-Null
    [IO.File]::WriteAllText((Join-Path $partialPath 'orphan.txt'),'orphan',[Text.UTF8Encoding]::new($false))
    $partial = Invoke-Router -Parameters @{ VaultRoot=$vault; ProjectDirectoryName='partial-slot'; GoalStatus='none' }
    Assert-Equal $partial.startup_class 'partial_project_tree_recovery' 'partial slot class'
    Assert-Equal $partial.next_action 'inspect_partial_tree_without_initializing_over_it' 'partial slot action'

    $projectId = 'fixture-project-0001'
    $project = Initialize-MathResearchProjectArchive -VaultRoot $vault -ProjectDirectoryName 'fixture-project' -ProjectId $projectId -ProblemStatement 'Decide one exact fixture statement.'
    $projectPath = [string]$project.ProjectDirectory
    $first = Invoke-Router -Parameters @{ ProjectDirectory=$projectPath; GoalStatus='none'; ExpectedProjectId=$projectId }
    Assert-Equal $first.startup_class 'existing_project_first_contract' 'first contract class'
    Assert-Equal $first.controller_action 'ResumePlan' 'first contract controller action'
    Assert-Equal $first.controller_call_count 1 'single authoritative call'
    Assert-Equal $first.contract_hash_role 'integrity_receipt_not_authorization_phrase' 'hash receipt role'
    Assert-Equal $first.goal_gate 'pre_goal_preparation_only_research_forbidden' 'first-contract pre-goal gate'

    foreach ($terminalStatus in @('closed','exhausted')) {
        $terminalId = "fixture-$terminalStatus-0001"
        $terminal = Initialize-MathResearchProjectArchive -VaultRoot $vault -ProjectDirectoryName "$terminalStatus-project" -ProjectId $terminalId -ProblemStatement 'Terminal fixture.'
        $terminalPath = [string]$terminal.ProjectDirectory
        $terminalProjectPath = Join-Path $terminalPath 'project.json'
        $terminalCheckpointPath = Join-Path $terminalPath 'state\checkpoint.json'
        $terminalProject = Get-Content -Raw $terminalProjectPath | ConvertFrom-Json -AsHashtable -Depth 64
        $terminalCheckpoint = Get-Content -Raw $terminalCheckpointPath | ConvertFrom-Json -AsHashtable -Depth 64
        $terminalProject.status = $terminalStatus
        $terminalCheckpoint.project_status = $terminalStatus
        $terminalCheckpoint.attempt_count = 24
        $terminalCheckpoint.attempts_since_last_audit = 0
        Write-JsonObject -Path $terminalProjectPath -Value $terminalProject
        Write-JsonObject -Path $terminalCheckpointPath -Value $terminalCheckpoint
        $terminalBefore = @{
            project=(Get-RawSha256 -Path $terminalProjectPath)
            checkpoint=(Get-RawSha256 -Path $terminalCheckpointPath)
            events=(Get-RawSha256 -Path (Join-Path $terminalPath 'state\project-events.jsonl'))
        }
        $terminalPlan = Invoke-Router -Parameters @{ ProjectDirectory=$terminalPath; GoalStatus='none'; ExpectedProjectId=$terminalId }
        Assert-Equal $terminalPlan.startup_class 'new_contract_or_closed_review' "$terminalStatus class"
        Assert-Equal $terminalPlan.next_action 'review_terminal_or_prior_history_before_new_contract' "$terminalStatus review action"
        Assert-Equal (Get-RawSha256 -Path $terminalProjectPath) $terminalBefore.project "$terminalStatus project zero mutation"
        Assert-Equal (Get-RawSha256 -Path $terminalCheckpointPath) $terminalBefore.checkpoint "$terminalStatus checkpoint zero mutation"
        Assert-Equal (Get-RawSha256 -Path (Join-Path $terminalPath 'state\project-events.jsonl')) $terminalBefore.events "$terminalStatus events zero mutation"
    }

    $reparse = Initialize-MathResearchProjectArchive -VaultRoot $vault -ProjectDirectoryName 'reparse-project' -ProjectId 'fixture-reparse-0001' -ProblemStatement 'Reparse fixture.'
    $reparsePath = [string]$reparse.ProjectDirectory
    $statePath = Join-Path $reparsePath 'state'
    $stateTarget = Join-Path $reparsePath 'state-real'
    Move-Item -LiteralPath $statePath -Destination $stateTarget
    $junction = New-Item -ItemType Junction -Path $statePath -Target $stateTarget
    Assert-True (($junction.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) 'state junction fixture created'
    $reparseProjectBefore = Get-RawSha256 -Path (Join-Path $reparsePath 'project.json')
    $reparseCheckpointBefore = Get-RawSha256 -Path (Join-Path $stateTarget 'checkpoint.json')
    $reparseEventsBefore = Get-RawSha256 -Path (Join-Path $stateTarget 'project-events.jsonl')
    $reparseFailed = $false
    try {
        $reparseParameters = @{ ProjectDirectory=$reparsePath; GoalStatus='none'; ExpectedProjectId='fixture-reparse-0001' }
        & $script:router @reparseParameters 2>$null | Out-Null
    }
    catch { $reparseFailed = $true }
    Assert-True $reparseFailed 'internal state junction rejected'
    Assert-Equal (Get-RawSha256 -Path (Join-Path $reparsePath 'project.json')) $reparseProjectBefore 'reparse project zero mutation'
    Assert-Equal (Get-RawSha256 -Path (Join-Path $stateTarget 'checkpoint.json')) $reparseCheckpointBefore 'reparse checkpoint zero mutation'
    Assert-Equal (Get-RawSha256 -Path (Join-Path $stateTarget 'project-events.jsonl')) $reparseEventsBefore 'reparse events zero mutation'
    Remove-Item -LiteralPath $statePath -Force

    $runId = 'fixture-run-0001'
    $runPath = Join-Path $projectPath "runs\$runId"
    New-Item -ItemType Directory -Path $runPath | Out-Null
    $promptName = 'Prompt-v1.md'
    $goalName = 'GoalObjective.txt'
    $promptPath = Join-Path $runPath $promptName
    $goalPath = Join-Path $runPath $goalName
    [IO.File]::WriteAllText($promptPath,"# exact fixture contract`n",[Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText($goalPath,"exact fixture objective`n",[Text.UTF8Encoding]::new($false))
    $binding = Get-NormalizedSha256 -Path $promptPath
    $promptRaw = Get-RawSha256 -Path $promptPath
    $goalRaw = Get-RawSha256 -Path $goalPath
    $registration = Register-MathResearchProjectContract -ProjectDirectory $projectPath -ContractFile $promptPath -ContractBindingSha256 $binding -ContractVersion 'v1' -RunDirectory $runPath
    Assert-Equal $registration.Run.status 'preparing' 'registered run status'

    $receiptParameters = @{
        ProjectDirectory=$projectPath; GoalStatus='active'; ExpectedProjectId=$projectId
        ExpectedContractVersion='v1'; ExpectedContractBindingSha256=$binding; ExpectedRunId=$runId
        ExpectedPromptFileName=$promptName; ExpectedPromptRawSha256=$promptRaw
        ExpectedGoalFileName=$goalName; ExpectedGoalRawSha256=$goalRaw
    }
    $preparing = Invoke-Router -Parameters $receiptParameters
    Assert-Equal $preparing.startup_class 'registered_preparing_recovery' 'preparing recovery class'
    Assert-Equal $preparing.preparing_phase 'registered_before_launcher' 'preparing phase'
    Assert-Equal $preparing.next_action 'invoke_new_launcher_without_reregistering' 'preparing recovery action'
    Assert-Equal $preparing.authoritative_resume_action 'recovery_or_audit_only' 'underlying fail-closed action'
    Assert-Equal $preparing.controller_call_count 1 'preparing single controller call'

    $pausedParameters = $receiptParameters.Clone()
    $pausedParameters.GoalStatus = 'paused'
    $paused = Invoke-Router -Parameters $pausedParameters
    Assert-Equal $paused.next_action 'wait_for_goal_control' 'paused preparing action'
    Assert-Equal $paused.recovery_reason 'goal_control_paused' 'paused preparing reason'

    $projectBefore = Get-RawSha256 -Path (Join-Path $projectPath 'project.json')
    $checkpointBefore = Get-RawSha256 -Path (Join-Path $projectPath 'state\checkpoint.json')
    $eventsBefore = Get-RawSha256 -Path (Join-Path $projectPath 'state\project-events.jsonl')
    $secondRegistrationFailed = $false
    try { Register-MathResearchProjectContract -ProjectDirectory $projectPath -ContractFile $promptPath -ContractBindingSha256 $binding -ContractVersion 'v1' -RunDirectory $runPath | Out-Null }
    catch { $secondRegistrationFailed = $true }
    Assert-True $secondRegistrationFailed 'repeat registration rejected'
    Assert-Equal (Get-RawSha256 -Path (Join-Path $projectPath 'project.json')) $projectBefore 'repeat registration project unchanged'
    Assert-Equal (Get-RawSha256 -Path (Join-Path $projectPath 'state\checkpoint.json')) $checkpointBefore 'repeat registration checkpoint unchanged'
    Assert-Equal (Get-RawSha256 -Path (Join-Path $projectPath 'state\project-events.jsonl')) $eventsBefore 'repeat registration events unchanged'

    $campaignCopy = Join-Path $runPath 'campaign-spec.json'
    [IO.File]::WriteAllText($campaignCopy,'{}',[Text.UTF8Encoding]::new($false))
    $extra = Invoke-Router -Parameters $receiptParameters
    Assert-Equal $extra.startup_class 'recovery_only' 'prelauncher extra file class'
    Assert-Equal $extra.recovery_reason 'prelauncher_directory_must_contain_only_prompt_and_goal' 'prelauncher extra file reason'
    Remove-Item -LiteralPath $campaignCopy -Force

    [IO.File]::WriteAllText((Join-Path $runPath 'run.json'),'{}',[Text.UTF8Encoding]::new($false))
    $manifestPresent = Invoke-Router -Parameters $receiptParameters
    Assert-Equal $manifestPresent.startup_class 'registered_preparing_recovery' 'manifest-present class'
    Assert-Equal $manifestPresent.preparing_phase 'launcher_manifest_present_requires_signed_resume_verification' 'manifest-present phase'
    Assert-Equal $manifestPresent.next_action 'invoke_signed_resume_verification_without_reregistering' 'manifest-present action'

    $wrongReceiptParameters = $receiptParameters.Clone()
    $wrongReceiptParameters.ExpectedContractBindingSha256 = ('0' * 64)
    $wrong = Invoke-Router -Parameters $wrongReceiptParameters
    Assert-Equal $wrong.startup_class 'recovery_only' 'wrong receipt class'
    Assert-Equal $wrong.recovery_reason 'preparing_identity_or_binding_mismatch' 'wrong receipt reason'

    $resumeId = 'fixture-resume-0001'
    $resumeProject = Initialize-MathResearchProjectArchive -VaultRoot $vault -ProjectDirectoryName 'resume-project' -ProjectId $resumeId -ProblemStatement 'Signed Resume fixture.'
    $resumePath = [string]$resumeProject.ProjectDirectory
    $resumeRunId = 'resume-run-0001'
    $resumeRun = Join-Path $resumePath "runs\$resumeRunId"
    New-Item -ItemType Directory -Path $resumeRun | Out-Null
    $resumePrompt = Join-Path $resumeRun 'Prompt-v1.md'
    [IO.File]::WriteAllText($resumePrompt,"# signed resume fixture`n",[Text.UTF8Encoding]::new($false))
    $resumeBinding = Get-NormalizedSha256 -Path $resumePrompt
    Register-MathResearchProjectContract -ProjectDirectory $resumePath -ContractFile $resumePrompt -ContractBindingSha256 $resumeBinding -ContractVersion 'v1' -RunDirectory $resumeRun | Out-Null
    $signedPayload = [ordered]@{ run_directory=$resumeRun; project=[ordered]@{project_id=$resumeId}; goal=[ordered]@{observed_status='active'}; thread_id='12345678-1234-4234-8234-1234567890ab' }
    Write-SignedJsonPayload -LiteralPath (Join-Path $resumeRun 'run.json') -Payload $signedPayload -CreateKeyIfMissing
    $resumeProjectPath = Join-Path $resumePath 'project.json'
    $resumeCheckpointPath = Join-Path $resumePath 'state\checkpoint.json'
    $resumeProjectState = Get-Content -Raw $resumeProjectPath | ConvertFrom-Json -AsHashtable -Depth 64
    $resumeCheckpoint = Get-Content -Raw $resumeCheckpointPath | ConvertFrom-Json -AsHashtable -Depth 64
    $resumeProjectState.status='active';$resumeProjectState.active_contract.status='active';$resumeProjectState.active_run.status='active'
    $resumeCheckpoint.project_status='active';$resumeCheckpoint.contract.status='active';$resumeCheckpoint.run.status='active';$resumeCheckpoint.dirty=$false;$resumeCheckpoint.recovery_required=$false;$resumeCheckpoint.audit_due=$false
    Write-JsonObject -Path $resumeProjectPath -Value $resumeProjectState
    Write-JsonObject -Path $resumeCheckpointPath -Value $resumeCheckpoint
    $signedResume = Invoke-Router -Parameters @{ ProjectDirectory=$resumePath; GoalStatus='active'; ExpectedProjectId=$resumeId }
    Assert-Equal $signedResume.startup_class 'same_run_resume' 'signed Resume class'
    Assert-Equal $signedResume.next_action 'resume_signed_run' 'signed Resume action'
    Assert-Equal $signedResume.controller_call_count 1 'signed Resume controller calls'

    $resumeCheckpoint.run.status='attempt_running'
    Write-JsonObject -Path $resumeCheckpointPath -Value $resumeCheckpoint
    $sameAttempt = Invoke-Router -Parameters @{ ProjectDirectory=$resumePath; GoalStatus='active'; ExpectedProjectId=$resumeId }
    Assert-Equal $sameAttempt.next_action 'resume_same_attempt' 'same attempt action'

    $resumeCheckpoint.run.status='active';$resumeCheckpoint.audit_due=$true
    Write-JsonObject -Path $resumeCheckpointPath -Value $resumeCheckpoint
    $auditDue = Invoke-Router -Parameters @{ ProjectDirectory=$resumePath; GoalStatus='active'; ExpectedProjectId=$resumeId }
    Assert-Equal $auditDue.startup_class 'same_run_resume' 'audit due class'
    Assert-Equal $auditDue.next_action 'run_due_audit' 'audit due action'

    $legacySource = Join-Path $temp 'legacy-source'
    New-Item -ItemType Directory -Path $legacySource | Out-Null
    [IO.File]::WriteAllText((Join-Path $legacySource 'record.md'),'legacy attempt',[Text.UTF8Encoding]::new($false))
    $legacy = Initialize-MathResearchProjectArchive -VaultRoot $vault -ProjectDirectoryName 'legacy-project' -ProjectId 'fixture-legacy-0001' -ProblemStatement 'Legacy fixture.' -LegacyRunDirectories @($legacySource)
    $legacyPlan = Invoke-Router -Parameters @{ ProjectDirectory=[string]$legacy.ProjectDirectory; GoalStatus='none'; ExpectedProjectId='fixture-legacy-0001' }
    Assert-Equal $legacyPlan.startup_class 'first_legacy_migration' 'legacy class'
    Assert-Equal $legacyPlan.controller_action 'StructuralOnly' 'legacy authoritative action'
    Assert-Equal $legacyPlan.controller_call_count 1 'legacy controller calls'
    Assert-Equal $legacyPlan.goal_gate 'pre_goal_preparation_only_research_forbidden' 'legacy pre-goal gate'

    if ((Split-Path -Leaf $script:router) -ceq 'invoke_math_research_startup_v2.ps1') {
        $analysis = Analyze-MathResearchLegacyArchive -ProjectDirectory ([string]$legacy.ProjectDirectory)
        $analysis.review_status = 'approved'
        $reviewedManifest = Join-Path $temp 'reviewed-legacy-manifest.json'
        [IO.File]::WriteAllText($reviewedManifest,(($analysis | ConvertTo-Json -Depth 64) + "`n"),[Text.UTF8Encoding]::new($false))
        $applied = Apply-MathResearchLegacyMigration -ProjectDirectory ([string]$legacy.ProjectDirectory) -ManifestFile $reviewedManifest -CurrentConclusion 'No candidate; migration changes no mathematical conclusion.'
        Assert-True ($applied.Ok -and [string]$applied.Status -ceq 'complete') 'completed legacy migration verification'
        $completedCheckpointPath = Join-Path ([string]$legacy.ProjectDirectory) 'state\checkpoint.json'
        $completedCheckpoint = Get-Content -Raw -LiteralPath $completedCheckpointPath | ConvertFrom-Json -AsHashtable -Depth 64
        Assert-Equal ([string]$completedCheckpoint.migration.status) 'complete' 'completed migration checkpoint status'
        $completedProjectPath = Join-Path ([string]$legacy.ProjectDirectory) 'project.json'
        $completedEventsPath = Join-Path ([string]$legacy.ProjectDirectory) 'state\project-events.jsonl'
        $completedBefore = @{
            project = Get-RawSha256 -Path $completedProjectPath
            checkpoint = Get-RawSha256 -Path $completedCheckpointPath
            events = Get-RawSha256 -Path $completedEventsPath
        }
        $completedPlan = Invoke-Router -Parameters @{ ProjectDirectory=[string]$legacy.ProjectDirectory; GoalStatus='none'; ExpectedProjectId='fixture-legacy-0001' }
        Assert-Equal $completedPlan.startup_class 'existing_project_first_contract' 'completed migration normal startup class'
        Assert-Equal $completedPlan.controller_action 'ResumePlan' 'completed migration authoritative action'
        Assert-Equal $completedPlan.controller_call_count 1 'completed migration controller calls'
        Assert-Equal (Get-RawSha256 -Path $completedProjectPath) $completedBefore.project 'completed migration project zero mutation'
        Assert-Equal (Get-RawSha256 -Path $completedCheckpointPath) $completedBefore.checkpoint 'completed migration checkpoint zero mutation'
        Assert-Equal (Get-RawSha256 -Path $completedEventsPath) $completedBefore.events 'completed migration events zero mutation'
    }

    $importedLegacy = Get-ChildItem -Recurse -File (Join-Path ([string]$legacy.ProjectDirectory) 'history\legacy-runs') | Select-Object -First 1
    [IO.File]::AppendAllText($importedLegacy.FullName,'tamper',[Text.UTF8Encoding]::new($false))
    $tamperFailed = $false
    try {
        $tamperParameters = @{ ProjectDirectory=[string]$legacy.ProjectDirectory; GoalStatus='active' }
        & $script:router @tamperParameters 2>$null | Out-Null
    }
    catch { $tamperFailed = $true }
    Assert-True $tamperFailed 'tampered legacy import rejected by real controller'

    $source = Get-Content -Raw $sourceRouter
    Assert-Equal ([regex]::Matches($source,'Invoke-ControllerAction -Action \$controllerAction').Count) 2 'closed controller call sites'
    Assert-True (-not $source.Contains("Invoke-ControllerAction -Action 'Verify'")) 'no explicit duplicate Verify call'
    Assert-True (-not $source.Contains('Invoke-Expression')) 'router excludes Invoke-Expression'
    $phaseCatalog = Get-Content -Raw (Join-Path $candidateRoot 'references\observer-phases.json') | ConvertFrom-Json -AsHashtable -Depth 16
    Assert-True (@($phaseCatalog.script_phases) -ccontains 'math-research-solve.script.invoke_math_research_startup_v1') 'startup observer phase registered'
    $candidateSkill = Get-Content -Raw (Join-Path $candidateRoot 'SKILL.md')
    Assert-True ($candidateSkill.Contains('scripts/invoke_math_research_startup_v1.ps1')) 'full SKILL routes startup'

    [pscustomobject]@{
        ok = $true
        assertions = $script:assertions
        real_controller_fixtures = $true
        router = $sourceRouter
        covered = @('fresh_slot','partial_tree','first_contract','closed','exhausted','internal_reparse','registered_preparing','paused','repeat_registration','prelaunch_directory','manifest_present','wrong_receipt','signed_resume','same_attempt','audit_due','legacy','tamper','observer_phase')
    } | ConvertTo-Json -Depth 8
}
finally {
    if ($null -ne $launcherModule) { & $launcherModule { $script:ManifestKeyPathOverrideForTests=$null } }
    Remove-Module MathResearchProjectArchive -Force -ErrorAction SilentlyContinue
    Remove-Module MathResearchLauncher -Force -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
}
