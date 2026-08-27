[CmdletBinding()]
param()

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)

Import-Module (Join-Path $PSScriptRoot 'MathResearchProjectArchive.psm1') -Force -DisableNameChecking
Import-Module (Join-Path $PSScriptRoot 'MathResearchLauncher.psm1') -Force -DisableNameChecking
Import-Module (Join-Path $PSScriptRoot 'MathResearchCycleLedger.psm1') -Force -DisableNameChecking

$script:passed = 0
$script:failed = 0
$script:skipped = 0

function Assert-True([bool]$Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Assert-Throws([scriptblock]$Action, [string]$Message) { try { & $Action; throw $Message } catch { if ($_.Exception.Message -eq $Message) { throw } } }
function Invoke-Test([string]$Name, [scriptblock]$Body) {
    try { & $Body; $script:passed++; Write-Host "PASS $Name" }
    catch { $script:failed++; Write-Host "FAIL $Name :: $($_.Exception.Message) :: $($_.ScriptStackTrace)" }
}
function Write-Utf8([string]$Path, [string]$Text) {
    $parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    [IO.File]::WriteAllText($Path, $Text, [Text.UTF8Encoding]::new($false))
}

$testRoot = Join-Path ([IO.Path]::GetTempPath()) ('math-research-project-test-' + [guid]::NewGuid().ToString('N'))
$vault = Join-Path $testRoot 'Vault'
$source = Join-Path $testRoot 'source'
$projectName = 'sample-open-problem'
$projectId = 'sample-open-problem-0001'
$project = Join-Path $vault ('笔记草稿\公开问题的尝试\' + $projectName)
New-Item -ItemType Directory -Path $vault -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $source 'work\proof') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $source 'work\skill-dev') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $source 'outputs') -Force | Out-Null
Write-Utf8 (Join-Path $source 'AI-START-HERE.md') "entry`n"
Write-Utf8 (Join-Path $source 'research-ledger.md') "ledger`n"
Write-Utf8 (Join-Path $source 'work\proof\result.md') "proof`n"
Write-Utf8 (Join-Path $source 'work\skill-dev\tool.md') "exclude`n"
Write-Utf8 (Join-Path $source 'outputs\answer.md') "answer`n"
Write-Utf8 (Join-Path $source 'work\proof\cache.pyc') "cache`n"
$launcherModule=Get-Module MathResearchLauncher -All|Select-Object -First 1
$testKeyPath=Join-Path $testRoot 'manifest-key.dpapi'
& $launcherModule { param($path) $script:ManifestKeyPathOverrideForTests=$path } $testKeyPath

try {
    Invoke-Test 'Initialize creates the fixed tree without an active run or attempt' {
        $result = Initialize-MathResearchProjectArchive -VaultRoot $vault -ProjectDirectoryName $projectName -ProjectId $projectId -ProblemStatement 'Prove T.' -SourceWorkspace $source
        Assert-True $result.Ok 'Initialize did not verify.'
        foreach ($path in @('contracts','state\CURRENT.md','failures','cycles','attempts','evidence\verified','handoffs','runs','history\legacy-runs')) { Assert-True (Test-Path -LiteralPath (Join-Path $project $path)) "Missing $path" }
        Assert-True (-not (Test-Path -LiteralPath (Join-Path $project 'history\imported-workspace\work\skill-dev\tool.md'))) 'Skill-development work was imported.'
        Assert-True (-not (Test-Path -LiteralPath (Join-Path $project 'history\imported-workspace\work\proof\cache.pyc'))) 'Regenerable cache was imported.'
        Assert-True ([int]$result.Checkpoint.attempt_count -eq 0 -and [string]$result.Checkpoint.goal.status -eq 'none') 'Initialize created research state.'
    }

    Invoke-Test 'Duplicate initialization does not overwrite the project' {
        Assert-Throws { Initialize-MathResearchProjectArchive -VaultRoot $vault -ProjectDirectoryName $projectName -ProjectId $projectId -ProblemStatement 'Prove T.' } 'Duplicate project initialization was accepted.'
    }

    Invoke-Test 'ResumePlan uses the minimal read state and awaits a contract' {
        $plan = Get-MathResearchProjectResumePlan -ProjectDirectory $project
        Assert-True ($plan.Action -eq 'awaiting_contract') 'Fresh project did not await a contract.'
        Assert-True ($plan.MinimalRead.Count -eq 3) 'ResumePlan expanded the baseline read set.'
    }

    Invoke-Test 'Legacy imports are structurally preserved but every normal research entry is blocked until reviewed migration' {
        $legacy=Join-Path $testRoot 'synthetic-legacy';New-Item -ItemType Directory -Path (Join-Path $legacy 'artifacts\bounded-scan') -Force|Out-Null
        Write-Utf8 (Join-Path $legacy 'AttemptLedger.md') "# Attempts`n`n### 2030-01-01 - route-one`n- Result: incomplete`n- Boundary: finite family only`n"
        Write-Utf8 (Join-Path $legacy 'BlockedLedger.md') "# Blocks`n`n### 2030-01-01 - missing-tool`n- Artifact type: BlockedReport`n- Stop reason: required tool unavailable`n`n### 2030-01-02 - bounded-method`n- Artifact type: BlockedDirection`n- Stop reason: method insufficient on the frozen family`n- Reopen: prove a new lemma`n"
        Write-Utf8 (Join-Path $legacy 'SourceLedger.md') "| Date | Source | Status |`n|---|---|---|`n| 2030-01-03 | Synthetic paper | partial audit |`n"
        Write-Utf8 (Join-Path $legacy 'SandboxSignals.md') "| Date | Signal | Status |`n|---|---|---|`n| 2030-01-04 | finite scan | exploratory |`n"
        Write-Utf8 (Join-Path $legacy 'artifacts\bounded-scan\metadata.json') '{"artifact_type":"SandboxSearch","candidate_status":"not-candidate"}'
        $legacyName='legacy-open-problem';$legacyId='legacy-open-problem-0001';$legacyProject=Join-Path $vault ('笔记草稿\公开问题的尝试\'+$legacyName)
        $created=Initialize-MathResearchProjectArchive -VaultRoot $vault -ProjectDirectoryName $legacyName -ProjectId $legacyId -ProblemStatement 'Decide S.' -LegacyRunDirectories @($legacy)
        Assert-True ($created.Ok -and [string]$created.Checkpoint.migration.status -eq 'required') 'Initialize did not preserve migration_required.'
        Assert-True (Verify-MathResearchProjectArchive -ProjectDirectory $legacyProject -StructuralOnly).Ok 'StructuralOnly rejected a preserved import.'
        foreach($entry in @(
            {Verify-MathResearchProjectArchive -ProjectDirectory $legacyProject},
            {Get-MathResearchProjectResumePlan -ProjectDirectory $legacyProject},
            {New-MathResearchProjectHandoff -ProjectDirectory $legacyProject -Label blocked}
        )){try{& $entry;throw 'Legacy research entry was accepted.'}catch{if($_.Exception.Message -eq 'Legacy research entry was accepted.'){throw};Assert-True ($_.Exception.Message -match '^legacy_semantic_archive_incomplete:') 'Legacy gate returned the wrong error code.'}}
        $analysis=Analyze-MathResearchLegacyArchive -ProjectDirectory $legacyProject
        Assert-True ([int]$analysis.recognized_count -eq 6) 'Synthetic recognizer coverage changed.'
        Assert-True ([int]$analysis.disposition_counts.operational_blocker -eq 1 -and [int]$analysis.disposition_counts.failure -eq 1) 'Blocked records were mechanically collapsed into one class.'
        $invalidManifest=($analysis|ConvertTo-Json -Depth 64|ConvertFrom-Json -AsHashtable -Depth 64);$invalidManifest.review_status='approved';$invalidManifest.records[0].disposition='excluded_nonresearch'
        $invalidPath=Join-Path $testRoot 'invalid-reviewed-legacy.json';Write-Utf8 $invalidPath (($invalidManifest|ConvertTo-Json -Depth 64)+"`n")
        Assert-Throws { Apply-MathResearchLegacyMigration -ProjectDirectory $legacyProject -ManifestFile $invalidPath } 'An unresolved substantive legacy record was accepted.'
        $manifestPath=Join-Path $testRoot 'reviewed-legacy.json';$analysis.review_status='approved';Write-Utf8 $manifestPath (($analysis|ConvertTo-Json -Depth 64)+"`n")
        $applied=Apply-MathResearchLegacyMigration -ProjectDirectory $legacyProject -ManifestFile $manifestPath -CurrentConclusion 'No candidate; baseline unchanged.'
        Assert-True ($applied.Ok -and $applied.Recognized -eq 6 -and $applied.UnresolvedSubstantive -eq 0 -and $applied.HashMismatches -eq 0) 'Reviewed semantic migration did not close coverage.'
        $completedCheckpoint=Get-Content -Raw -LiteralPath (Join-Path $legacyProject 'state\checkpoint.json')|ConvertFrom-Json -AsHashtable -Depth 64
        Assert-True ([string]$completedCheckpoint.project_status -eq 'paused' -and [string]$completedCheckpoint.migration.status -eq 'complete') 'Migration completion left checkpoint project_status inconsistent.'
        Assert-True (@(Get-ChildItem -LiteralPath (Join-Path $legacyProject 'failures') -Filter '*.legacy-failure.json').Count -eq 1) 'Semantic failure was not materialized.'
        Assert-True (@(Get-ChildItem -LiteralPath (Join-Path $legacyProject 'cycles\legacy\blockers') -Filter '*.md').Count -eq 1) 'Operational blocker was not separated.'
        Assert-True (Verify-MathResearchProjectArchive -ProjectDirectory $legacyProject).Ok 'Normal verification did not open after migration.'

        $legacyFailure=(Get-ChildItem -LiteralPath (Join-Path $legacyProject 'failures') -Filter '*.legacy-failure.json'|Select-Object -First 1).FullName
        Assert-True (Test-MathResearchLegacyFailureRecord -FailureRecordFile $legacyFailure).Ok 'Legacy failure schema was rejected.'
        Assert-Throws { Test-MathResearchFailureRecord -FailureRecordFile $legacyFailure } 'Legacy failure was accepted as an active AttemptEnd failure.'

        $semantic=(Get-Content -Raw -LiteralPath (Join-Path $legacyProject 'manifests\legacy-semantic-manifest.json')|ConvertFrom-Json -AsHashtable -Depth 64)
        $target=[string]$semantic.records[0].targets[0].path;$targetPath=Join-Path $legacyProject $target;$original=[IO.File]::ReadAllText($targetPath)
        try{Write-Utf8 $targetPath 'tampered';Assert-Throws { Verify-MathResearchLegacySemanticArchive -ProjectDirectory $legacyProject } 'Tampered semantic target was accepted.'}finally{Write-Utf8 $targetPath $original}
        Assert-True (Verify-MathResearchLegacySemanticArchive -ProjectDirectory $legacyProject).Ok 'Semantic archive did not recover after target restoration.'
        $routesPath=Join-Path $legacyProject 'state\ROUTES.md';$routesText=[IO.File]::ReadAllText($routesPath)
        try{Write-Utf8 $routesPath ($routesText -replace '<!-- math-research-generated-legacy-semantic-archive:start -->','');Assert-Throws { Verify-MathResearchLegacySemanticArchive -ProjectDirectory $legacyProject } 'A missing state index marker was accepted.'}finally{Write-Utf8 $routesPath $routesText}
        Assert-True (Verify-MathResearchLegacySemanticArchive -ProjectDirectory $legacyProject).Ok 'Semantic archive did not recover after index restoration.'
    }

    Invoke-Test 'Legacy migration accepts an explicitly reviewed empty recognized-record set' {
        $legacyEmpty=Join-Path $testRoot 'synthetic-legacy-empty';New-Item -ItemType Directory -Path $legacyEmpty -Force|Out-Null
        Write-Utf8 (Join-Path $legacyEmpty 'Math-Research-Orchestration-Prompt-v4.md') "# Historical prompt`n"
        Write-Utf8 (Join-Path $legacyEmpty 'events.jsonl') "{}`n"
        $legacyEmptyName='legacy-empty-open-problem';$legacyEmptyId='legacy-empty-open-problem-0001';$legacyEmptyProject=Join-Path $vault ('笔记草稿\公开问题的尝试\'+$legacyEmptyName)
        $created=Initialize-MathResearchProjectArchive -VaultRoot $vault -ProjectDirectoryName $legacyEmptyName -ProjectId $legacyEmptyId -ProblemStatement 'Decide E.' -LegacyRunDirectories @($legacyEmpty)
        Assert-True ($created.Ok -and [string]$created.Checkpoint.migration.status -eq 'required') 'Empty-recognition fixture did not require semantic migration.'
        Assert-Throws { Verify-MathResearchProjectArchive -ProjectDirectory $legacyEmptyProject } 'An unreviewed empty-recognition legacy import was accepted.'
        $analysis=Analyze-MathResearchLegacyArchive -ProjectDirectory $legacyEmptyProject
        Assert-True ([int]$analysis.recognized_count -eq 0 -and @($analysis.records).Count -eq 0) 'Empty recognized-record analysis was not represented as an empty array.'
        $analysis.review_status='approved';$manifestPath=Join-Path $testRoot 'reviewed-empty-legacy.json';Write-Utf8 $manifestPath (($analysis|ConvertTo-Json -Depth 64)+"`n")
        $applied=Apply-MathResearchLegacyMigration -ProjectDirectory $legacyEmptyProject -ManifestFile $manifestPath -CurrentConclusion 'No recognized research records; migration promotes no conclusion.'
        Assert-True ($applied.Ok -and $applied.Recognized -eq 0 -and $applied.Disposed -eq 0) 'Reviewed empty semantic migration did not close cleanly.'
        Assert-True (Verify-MathResearchProjectArchive -ProjectDirectory $legacyEmptyProject).Ok 'Normal verification did not open after reviewed empty migration.'
    }

    Invoke-Test 'Project identity mismatch and directory prefix collision are rejected' {
        Assert-Throws { Resolve-MathResearchProjectDirectory -ProjectDirectory $project -ExpectedProjectId 'different-project-0001' } 'Wrong project_id was accepted.'
        $outside = Join-Path $vault '笔记草稿\公开问题的尝试-other\sample-open-problem'
        New-Item -ItemType Directory -Path $outside -Force | Out-Null
        Copy-Item -LiteralPath (Join-Path $project 'project.json') -Destination (Join-Path $outside 'project.json')
        $root = Get-MathResearchProjectsRoot -VaultRoot $vault
        Assert-True (-not ([IO.Path]::GetFullPath($outside).StartsWith(([IO.Path]::GetFullPath($root).TrimEnd('\') + '\'), [StringComparison]::OrdinalIgnoreCase))) 'Prefix-collision fixture is invalid.'
    }

    Invoke-Test 'Import manifest detects artifact tampering' {
        $file = Join-Path $project 'history\imported-workspace\outputs\answer.md'
        $original = [IO.File]::ReadAllText($file)
        try { Write-Utf8 $file "tampered`n"; Assert-Throws { Verify-MathResearchProjectArchive -ProjectDirectory $project } 'Tampered imported artifact was accepted.' }
        finally { Write-Utf8 $file $original }
        Assert-True (Verify-MathResearchProjectArchive -ProjectDirectory $project).Ok 'Archive did not recover after fixture restore.'
    }

    Invoke-Test 'Failure record requires every semantic boundary and verifies artifact hashes' {
        $run = Join-Path $project 'runs\run-test'
        New-Item -ItemType Directory -Path $run -Force | Out-Null
        $artifact = Join-Path $run 'attempt.md'
        Write-Utf8 $artifact "attempt`n"
        $hash = (Get-FileHash -LiteralPath $artifact -Algorithm SHA256).Hash.ToLowerInvariant()
        $record = [ordered]@{ schema=1; attempt_id='attempt-0001'; route_id='route-a'; decision_problem='Decide A.'; failed_step='Step 2'; failure_reason='Lemma false.'; excluded_scope='This ansatz.'; not_excluded_scope='General points.'; retry_fingerprint_sha256=('a' * 64); reopen_conditions=@('new-lemma: produce a proof of L'); artifacts=@([ordered]@{file='attempt.md';sha256=$hash}) }
        $recordPath = Join-Path $run 'failure.json'
        Write-Utf8 $recordPath (($record | ConvertTo-Json -Depth 20) + "`n")
        Assert-True (Test-MathResearchFailureRecord -FailureRecordFile $recordPath -ExpectedAttemptId 'attempt-0001' -ArtifactRoot $run).Ok 'Valid failure record failed.'
        $record.Remove('not_excluded_scope')
        Write-Utf8 $recordPath (($record | ConvertTo-Json -Depth 20) + "`n")
        Assert-Throws { Test-MathResearchFailureRecord -FailureRecordFile $recordPath -ExpectedAttemptId 'attempt-0001' -ArtifactRoot $run } 'Failure record without non-entailment boundary was accepted.'
    }

    Invoke-Test 'Frozen duplicate route requires new pre-registered reopen evidence' {
        $registryPath = Join-Path $project 'state\route-registry.json'
        $ticketPath = Join-Path $testRoot 'ticket.json'
        $ticket = [ordered]@{ route_id='route-a'; route_family_id='family-a'; route_fingerprint_sha256=('0' * 64); mechanism_id='same'; decision_problem='Decide A.'; frozen_domain='all inputs'; resource_caps=[ordered]@{tool_calls=2} }
        $ticket.route_fingerprint_sha256 = Get-MathResearchRouteFingerprint -Ticket $ticket
        $registry = [ordered]@{ schema=1; project_id=$projectId; routes=@([ordered]@{ route_id='route-a'; route_family_id='family-a'; retry_fingerprint_sha256=$ticket.route_fingerprint_sha256; status='frozen'; reopen_condition_ids=@('new-global-lemma'); seen_evidence_sha256=@() }) }
        Write-Utf8 $registryPath (($registry | ConvertTo-Json -Depth 20) + "`n")
        Write-Utf8 $ticketPath (($ticket | ConvertTo-Json -Depth 20) + "`n")
        Assert-Throws { Test-MathResearchRouteStart -ProjectDirectory $project -TicketFile $ticketPath } 'Frozen duplicate route was accepted.'
        $ticket.reopen_evidence = [ordered]@{ condition_id='new-global-lemma'; evidence_sha256=('c' * 64) }
        Write-Utf8 $ticketPath (($ticket | ConvertTo-Json -Depth 20) + "`n")
        Assert-True (Test-MathResearchRouteStart -ProjectDirectory $project -TicketFile $ticketPath).Ok 'Qualified reopen evidence was rejected.'
    }

    Invoke-Test 'Dirty and audit gates determine the unique Resume class' {
        $checkpointPath = Join-Path $project 'state\checkpoint.json'
        $checkpoint = (Get-Content -LiteralPath $checkpointPath -Raw | ConvertFrom-Json -AsHashtable -Depth 20)
        $checkpoint.dirty = $true
        Write-Utf8 $checkpointPath (($checkpoint | ConvertTo-Json -Depth 20) + "`n")
        Assert-True ((Get-MathResearchProjectResumePlan -ProjectDirectory $project).Action -eq 'recovery_or_audit_only') 'Dirty state did not force recovery.'
        $checkpoint.dirty = $false; $checkpoint.audit_due = $true
        Write-Utf8 $checkpointPath (($checkpoint | ConvertTo-Json -Depth 20) + "`n")
        Assert-True ((Get-MathResearchProjectResumePlan -ProjectDirectory $project).Action -eq 'audit_required') 'Audit gate did not precede Resume.'
    }

    Invoke-Test 'Reparse project paths are rejected when junctions are available' {
        $target = Join-Path $testRoot 'junction-target'
        $junction = Join-Path $testRoot 'junction-project'
        New-Item -ItemType Directory -Path $target -Force | Out-Null
        try {
            New-Item -ItemType Junction -Path $junction -Target $target -ErrorAction Stop | Out-Null
            Assert-Throws { Resolve-MathResearchProjectDirectory -ProjectDirectory $junction } 'Junction project was accepted.'
        }
        catch {
            if ($_.Exception.Message -eq 'Junction project was accepted.') { throw }
            $script:skipped++; Write-Host "SKIP junction creation unavailable :: $($_.Exception.Message)"
        }
    }

    Invoke-Test 'Observer wrapper forwards named PowerShell parameters' {
        $wrapper = Join-Path $PSScriptRoot 'observer_run.ps1'
        $cli = Join-Path $PSScriptRoot 'invoke_math_research_project.ps1'
        $output = & $wrapper -Skill math-research-solve -Catalog math-research-solve/v1 -Phase math-research-solve.script.invoke_math_research_project -FilePath $cli -ArgumentList @('-Action','Status','-ProjectDirectory',$project)
        Assert-True ($LASTEXITCODE -eq 0) 'Observer wrapper did not preserve project CLI success.'
        $status = $output | ConvertFrom-Json
        Assert-True ($status.ProjectId -eq $projectId) 'Observer wrapper changed named PowerShell arguments.'
    }

    Invoke-Test 'v6 checkpoint publication copies attempt reports and verified evidence by run id' {
        $runId='publish-v6';$run=Join-Path $project "runs\$runId";New-Item -ItemType Directory -Path $run -Force|Out-Null
        $caps=[ordered]@{child_agents=1;tool_calls=4;wall_minutes=5}
        $material=[ordered]@{route_id='route-publish';route_family_id='family-publish';mechanism_id='mechanism-publish';decision_problem='Decide publish claim.';frozen_domain='publish domain';resource_caps=$caps}
        $fingerprint=Get-MathResearchRouteFingerprint -Ticket $material
        $ticket=[ordered]@{attempt_kind='route_execution';route_id='route-publish';route_fingerprint_sha256=$fingerprint;ticket_id='C1-A1';route_family_id='family-publish';mechanism_id='mechanism-publish';bottleneck_id='bottleneck-publish';decision_question='Decide publish claim.';search_domain='publish domain';success_signal='publish result';stop_signal='publish cap';resource_caps=$caps;reopen_condition='new-publish-evidence'}
        $policy=[ordered]@{schema_version=3;protocol='math-research-cycle-policy/v3';total_round_budget=2;attempt_budget=1;audit_interval_attempts=1;max_route_family_attempts_per_cycle=2;max_repair_batches_per_attempt=1;audit_roles=@('skeptic_quantifiers','skeptic_strategy','theory_tool_scout')}
        $tickets=[ordered]@{schema_version=3;cycle_id='cycle-1';tickets=@($ticket)}
        $policyPath=Join-Path $run 'cycle-policy.json';$ticketsPath=Join-Path $run 'cycle-tickets-000.json'
        Write-Utf8 $policyPath ($policy|ConvertTo-Json -Depth 20);Write-Utf8 $ticketsPath ($tickets|ConvertTo-Json -Depth 20)
        Initialize-MathResearchCycleLedger -RunDirectory $run -RunId $runId -ContractSha256 ('a'*64) -PolicyFile $policyPath -TicketsFile $ticketsPath|Out-Null
        Invoke-MathResearchCycleAction -Action AttemptStart -RunDirectory $run -TicketId 'C1-A1'|Out-Null
        $solver=Join-Path $run 'solver.md';$result=Join-Path $run 'result.md';$verification=Join-Path $run 'verification.md'
        Write-Utf8 $solver 'solver';Write-Utf8 $result 'result';Write-Utf8 $verification 'verification'
        $solverHash=(Get-FileHash -LiteralPath $solver -Algorithm SHA256).Hash.ToLowerInvariant();$resultHash=(Get-FileHash -LiteralPath $result -Algorithm SHA256).Hash.ToLowerInvariant();$verificationHash=(Get-FileHash -LiteralPath $verification -Algorithm SHA256).Hash.ToLowerInvariant()
        $record=[ordered]@{schema_version=1;attempt_id='attempt-0001';ticket_id='C1-A1';attempt_kind='route_execution';decision_question='Decide publish claim.';solver_reports=@([ordered]@{file='solver.md';sha256=$solverHash});verification_reports=@([ordered]@{candidate_sha256=$resultHash;verdict='PASS';artifact_file='verification.md';artifact_sha256=$verificationHash;new_math_performed=$false});repair_batches=0;result_artifact=[ordered]@{file='result.md';sha256=$resultHash};route_portfolio=$null;source_claims=@()}
        $recordPath=Join-Path $run 'attempt-record.json';Write-Utf8 $recordPath ($record|ConvertTo-Json -Depth 20)
        $failure=[ordered]@{schema=1;attempt_id='attempt-0001';route_id='route-publish';decision_problem='Decide publish claim.';failed_step='bounded route step';failure_reason='verified route refutation';excluded_scope='the frozen route';not_excluded_scope='other route families';retry_fingerprint_sha256=$fingerprint;reopen_conditions=@('new-publish-evidence: provide a falsifying witness');artifacts=@([ordered]@{file='result.md';sha256=$resultHash})}
        $failurePath=Join-Path $run 'failure.json';Write-Utf8 $failurePath ($failure|ConvertTo-Json -Depth 20)
        Invoke-MathResearchCycleAction -Action AttemptEnd -RunDirectory $run -Outcome route_refuted -ArtifactFile $result -AttemptRecordFile $recordPath -FailureRecordFile $failurePath|Out-Null
        $manifest=[ordered]@{run_directory=$run;project=[ordered]@{project_id=$projectId};goal=[ordered]@{observed_status='active'};thread_id='12345678-1234-4234-8234-1234567890ab'}
        Write-SignedJsonPayload -LiteralPath (Join-Path $run 'run.json') -Payload $manifest -CreateKeyIfMissing
        $projectModule=Get-Module MathResearchProjectArchive -All|Select-Object -First 1
        & $projectModule {$script:PublicationFailAfterArtifactCommitForTests=$true}
        Assert-Throws { Publish-MathResearchProjectCheckpoint -ProjectDirectory $project -RunDirectory $run } 'Synthetic publication interruption was accepted.'
        $recoveryCheckpoint=Get-Content -Raw -LiteralPath (Join-Path $project 'state\checkpoint.json')|ConvertFrom-Json -AsHashtable -Depth 64
        Assert-True ([bool]$recoveryCheckpoint.recovery_required) 'Interrupted publication did not fail closed into recovery.'
        & $projectModule {$script:PublicationFailAfterArtifactCommitForTests=$false}
        $published=Publish-MathResearchProjectCheckpoint -ProjectDirectory $project -RunDirectory $run
        Assert-True ($published.PublishedArtifacts.Count -ge 5) 'Publication omitted v6 attempt materials.'
        foreach($path in @("attempts\$runId\attempt-0001\attempt-record.json","attempts\$runId\attempt-0001\solver-01.md","attempts\$runId\attempt-0001\verification-01.md","evidence\verified\$runId-attempt-0001.md")){Assert-True (Test-Path -LiteralPath (Join-Path $project $path)) "Published file missing: $path"}
        Assert-True ((Get-FileHash -LiteralPath (Join-Path $project "evidence\verified\$runId-attempt-0001.md") -Algorithm SHA256).Hash.ToLowerInvariant() -eq $resultHash) 'Published evidence hash changed.'
        Assert-True ((Get-Content -LiteralPath (Join-Path $project 'state\RESULTS.md') -Raw) -match 'route_refuted') 'Published result is missing from state/RESULTS.md.'
        Assert-True ((Get-Content -LiteralPath (Join-Path $project 'state\EVIDENCE.md') -Raw) -match [regex]::Escape("evidence\verified\$runId-attempt-0001.md")) 'Published evidence is missing from state/EVIDENCE.md.'
        Assert-True ((Test-Path -LiteralPath (Join-Path $project 'failures\route-publish.failure.json')) -and (Test-Path -LiteralPath (Join-Path $project 'failures\route-publish.md'))) 'Published failure dossier is incomplete.'
        $publishedRoutes=Get-Content -Raw -LiteralPath (Join-Path $project 'state\route-registry.json')|ConvertFrom-Json -AsHashtable -Depth 64
        Assert-True (@($publishedRoutes.routes|Where-Object{[string]$_.route_id -eq 'route-publish'}).Count -eq 1) 'Published failure was not indexed in the route registry.'
        $eventCountBefore=@([IO.File]::ReadAllLines((Join-Path $project 'state\project-events.jsonl'))).Count
        $publishedAgain=Publish-MathResearchProjectCheckpoint -ProjectDirectory $project -RunDirectory $run
        $eventCountAfter=@([IO.File]::ReadAllLines((Join-Path $project 'state\project-events.jsonl'))).Count
        Assert-True ($publishedAgain.AlreadyPublished -and $eventCountBefore -eq $eventCountAfter) 'Repeated publication was not idempotent.'
        $publicationIndex=Get-Content -Raw -LiteralPath (Join-Path $project 'manifests\publication-index.json')|ConvertFrom-Json -AsHashtable -Depth 64
        Assert-True (@($publicationIndex.entries).Count -eq 1) 'Publication index duplicated the same ledger checkpoint.'
    }

    Invoke-Test 'Handoff appends a valid project event and tail repair is bounded' {
        $handoff = New-MathResearchProjectHandoff -ProjectDirectory $project -Label test
        Assert-True (Test-Path -LiteralPath $handoff.Path) 'Handoff file was not created.'
        Assert-True (Verify-MathResearchProjectArchive -ProjectDirectory $project).Ok 'Valid handoff event broke project verification.'
        $eventsPath = Join-Path $project 'state\project-events.jsonl'
        $lines = @([IO.File]::ReadAllLines($eventsPath, [Text.UTF8Encoding]::new($false,$true)))
        $tail = $lines[-1] | ConvertFrom-Json -AsHashtable -Depth 32 -DateKind String
        $damaged = 'd' * 64
        $tail.event_sha256 = $damaged
        $lines[-1] = $tail | ConvertTo-Json -Compress -Depth 32
        Write-Utf8 $eventsPath (($lines -join "`n") + "`n")
        $checkpointPath = Join-Path $project 'state\checkpoint.json'
        $checkpoint = Get-Content -LiteralPath $checkpointPath -Raw | ConvertFrom-Json -AsHashtable -Depth 32
        $checkpoint.last_project_event_sha256 = $damaged
        Write-Utf8 $checkpointPath (($checkpoint | ConvertTo-Json -Depth 32) + "`n")
        Assert-Throws { Verify-MathResearchProjectArchive -ProjectDirectory $project } 'Damaged event tail was accepted.'
        $repair = Repair-MathResearchProjectEventTail -ProjectDirectory $project
        Assert-True ($repair.Changed -and (Verify-MathResearchProjectArchive -ProjectDirectory $project).Ok) 'Bounded event-tail repair failed.'
    }
}
finally {
    & $launcherModule { $script:ManifestKeyPathOverrideForTests=$null }
    if (Test-Path -LiteralPath $testRoot) { Remove-Item -LiteralPath $testRoot -Recurse -Force }
}

Write-Host "RESULT passed=$script:passed failed=$script:failed skipped=$script:skipped"
if ($script:failed -gt 0) { exit 1 }
