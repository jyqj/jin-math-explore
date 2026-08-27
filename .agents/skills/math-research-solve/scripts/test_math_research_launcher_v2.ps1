[CmdletBinding()]
param(
    [string]$TestRoot = (Join-Path $env:TEMP ("math-research-launcher-v2-tests-" + [Guid]::NewGuid().ToString('N'))),
    [switch]$KeepTestFiles
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)

$scriptsRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\scripts'))
$candidateRoot = [IO.Path]::GetFullPath((Join-Path $scriptsRoot '..'))
$utf8 = [Text.UTF8Encoding]::new($false,$true)
$modulePath = Join-Path $scriptsRoot 'MathResearchLauncherV2.psm1'
$launcherPath = Join-Path $scriptsRoot 'launch_math_research_v2.ps1'
Import-Module $modulePath -Force -DisableNameChecking
$launcherModule = Get-Module MathResearchLauncherV2

$script:Passed = 0
$script:Results = [Collections.Generic.List[object]]::new()

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

function Assert-Equal {
    param($Actual, $Expected, [string]$Message)
    $actualJson = $Actual | ConvertTo-Json -Compress -Depth 32
    $expectedJson = $Expected | ConvertTo-Json -Compress -Depth 32
    if ($actualJson -cne $expectedJson) { throw "$Message`nExpected: $expectedJson`nActual: $actualJson" }
}

function Assert-ThrowsLike {
    param([scriptblock]$Action, [string]$Pattern, [string]$Message)
    $caught = $null
    try { & $Action }
    catch { $caught = $_ }
    if ($null -eq $caught) { throw $Message }
    if (-not [string]::IsNullOrWhiteSpace($Pattern) -and [string]$caught.Exception.Message -notlike "*$Pattern*") {
        throw "$Message Unexpected error: $($caught.Exception.Message)"
    }
}

function Invoke-Test {
    param([string]$Name, [scriptblock]$Action)
    try {
        & $Action
        $script:Passed++
        $script:Results.Add([pscustomobject]@{ Name=$Name; Status='passed'; Detail=$null })
    }
    catch {
        $script:Results.Add([pscustomobject]@{ Name=$Name; Status='failed'; Detail=$_.Exception.Message })
        throw "Test failed: $Name`n$($_.Exception.Message)"
    }
}

function Write-TestText {
    param([Parameter(Mandatory=$true)][string]$LiteralPath, [AllowEmptyString()][string]$Text)
    $parent = Split-Path -Parent $LiteralPath
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    [IO.File]::WriteAllText($LiteralPath, $Text, [Text.UTF8Encoding]::new($false))
}

function New-CanaryFixture {
    param([Parameter(Mandatory=$true)][string]$Root, [Parameter(Mandatory=$true)][string]$Name)
    $run = Join-Path $Root $Name
    New-Item -ItemType Directory -Force -Path (Join-Path $run 'cycle-ledger') | Out-Null
    Write-TestText -LiteralPath (Join-Path $run 'run.json') -Text '{"signed_fixture":true}'
    Write-TestText -LiteralPath (Join-Path $run 'cycle-ledger\state.json') -Text '{"AttemptCount":0,"TotalRoundCount":0}'
    $files = [ordered]@{}
    foreach ($leaf in @('launch_math_research_v2.ps1','MathResearchLauncherV2.psm1','invoke_math_research_canary_v2.ps1','invoke_math_research_cycle_v2.ps1','codex.exe')) {
        $path = Join-Path $run $leaf
        Write-TestText -LiteralPath $path -Text "fixture:$leaf"
        $files[$leaf] = $path
    }
    return [pscustomobject]@{ Run=$run; Files=$files }
}

$fullTestRoot = [IO.Path]::GetFullPath($TestRoot)
if (Test-Path -LiteralPath $fullTestRoot) { throw "TestRoot already exists: $fullTestRoot" }
New-Item -ItemType Directory -Force -Path $fullTestRoot | Out-Null
$testKeyPath = Join-Path $fullTestRoot 'dpapi\manifest-key.dpapi'
$allPassed = $false

try {
    & $launcherModule { param($path) $script:ManifestKeyPathOverrideForTests = $path } $testKeyPath

    Invoke-Test 'All additive v2 PowerShell files parse and preserve JSON strings' {
        $productionV2Names = @(
            'invoke_math_research_startup_v2.ps1',
            'launch_math_research_v2.ps1',
            'MathResearchLauncherV2.psm1',
            'invoke_math_research_canary_v2.ps1',
            'MathResearchCycleLedgerV2.psm1',
            'invoke_math_research_cycle_v2.ps1',
            'MathResearchProjectArchiveV2.psm1',
            'invoke_math_research_project_v2.ps1',
            'stop_math_research_v2.ps1'
        )
        $v2Files = @($productionV2Names | ForEach-Object { Get-Item -LiteralPath (Join-Path $scriptsRoot $_) })
        Assert-True ($v2Files.Count -eq 9) "Expected nine named additive v2 production files; found $($v2Files.Count)."
        foreach ($file in $v2Files) {
            $tokens = $null; $errors = $null
            [Management.Automation.Language.Parser]::ParseFile($file.FullName, [ref]$tokens, [ref]$errors) | Out-Null
            $parseDetails = @($errors | ForEach-Object { $_.Message }) -join '; '
            Assert-True (@($errors).Count -eq 0) "$($file.Name) has parser errors: $parseDetails"
            foreach ($line in [IO.File]::ReadLines($file.FullName)) {
                if ($line -match '\|\s*ConvertFrom-Json\b') {
                    Assert-True ($line -match '-DateKind\s+String\b') "$($file.Name) has a JSON decode path without -DateKind String: $line"
                }
            }
        }
        Assert-PowerShell7
    }

    Invoke-Test 'Production-shaped trailing-zero manifest round-trips under a temp DPAPI key' {
        $raw = '{"schema_version":1,"launcher_protocol":"math-research-launcher/v2","created_at_utc":"2026-08-08T12:34:56.1200000Z","config":{"model":"gpt-5.6-sol","approval_mode":"approve_for_me"},"launcher_bundle":{"launcher_entry":{"path":"C:\\\\trusted\\\\launch_math_research_v2.ps1","sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}}}'
        $defaultObject = $raw | ConvertFrom-Json -AsHashtable -Depth 64
        $stringObject = $raw | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
        $defaultCanonical = ConvertTo-CanonicalJson -InputObject $defaultObject
        $stringCanonical = ConvertTo-CanonicalJson -InputObject $stringObject
        Assert-True ($defaultCanonical -cne $stringCanonical) 'Fixture did not expose PowerShell 7.6 ISO DateTime auto-conversion.'
        Assert-True ([string]$stringObject.created_at_utc -ceq '2026-08-08T12:34:56.1200000Z') 'DateKind String did not retain the trailing fractional zero.'

        $signedPath = Join-Path $fullTestRoot 'production-run.json'
        Write-SignedJsonPayload -LiteralPath $signedPath -Payload $stringObject -CreateKeyIfMissing
        Assert-True (Test-Path -LiteralPath $testKeyPath -PathType Leaf) 'The test-only DPAPI key was not created under TestRoot.'
        $read = Read-SignedJsonPayload -LiteralPath $signedPath
        Assert-True (-not $read.RecoveredFromBackup) 'A freshly written signed manifest did not verify from its primary path.'
        Assert-True ([string]$read.Payload.created_at_utc -ceq '2026-08-08T12:34:56.1200000Z') 'Signed read-back changed the timestamp string.'
        Assert-Equal (ConvertTo-CanonicalJson -InputObject $read.Payload) $stringCanonical 'Signed root/envelope round-trip changed the production-shaped payload.'

        $tampered = [IO.File]::ReadAllText($signedPath, [Text.UTF8Encoding]::new($false,$true)).Replace('gpt-5.6-sol','gpt-5.6-terra')
        Write-TestText -LiteralPath $signedPath -Text $tampered
        Assert-ThrowsLike { Read-SignedJsonPayload -LiteralPath $signedPath } 'No valid signed JSON' 'A tampered signed payload was accepted.'
    }

    Invoke-Test 'ApprovalMode generates the exact fail-closed Codex argv' {
        $run = 'C:\trusted\research-run'
        $last = 'C:\trusted\research-run\last-message.json'
        $approve = [string[]](New-CodexExecArguments -RunDirectory $run -Model 'gpt-5.6-sol' -ReasoningEffort 'xhigh' -Sandbox workspace-write -ApprovalMode approve_for_me -AllowWebSearch:$true -EnableMultiAgent:$true -MaxChildAgents 3 -LastMessagePath $last)
        Assert-True (@($approve | Where-Object { $_ -ceq '--approve-for-me' }).Count -eq 1) 'approve_for_me did not emit exactly one literal --approve-for-me.'
        Assert-True ($approve -notcontains '-a') 'approve_for_me was weakened or combined with an ask-for-approval policy.'
        Assert-True ($approve -contains 'workspace-write' -and $approve -contains '--ignore-user-config' -and $approve -notcontains '--ignore-rules') 'approve_for_me isolation argv is incomplete.'
        Assert-True ($approve -contains '--search' -and $approve -contains 'agents.max_threads=3') 'Research resource envelope was not preserved in argv.'
        Assert-ThrowsLike { New-CodexExecArguments -RunDirectory $run -Model 'gpt-5.6-sol' -ReasoningEffort low -Sandbox read-only -ApprovalMode approve_for_me -AllowWebSearch:$false -EnableMultiAgent:$false -LastMessagePath $last } 'workspace-write' 'approve_for_me was accepted under read-only.'

        $never = [string[]](New-CodexExecArguments -RunDirectory $run -Model 'gpt-5.6-sol' -ReasoningEffort xhigh -Sandbox read-only -ApprovalMode never -AllowWebSearch:$false -EnableMultiAgent:$false -LastMessagePath $last)
        $askIndex = [Array]::IndexOf($never, '-a')
        Assert-True ($askIndex -ge 0 -and $never[$askIndex + 1] -ceq 'never') 'Intentional never is not represented explicitly as -a never.'
        Assert-True ($never -notcontains '--approve-for-me') 'Intentional never emitted approve-for-me.'

        $features = [string[]](New-CodexFeaturesArguments -RunDirectory $run -MaxChildAgents 3 -ApprovalMode approve_for_me)
        Assert-True ($features -contains '--approve-for-me' -and $features -notcontains '-a') 'Feature preflight omitted the contract-bound approval flag.'
    }

    Invoke-Test 'Prompt v7 binds approval mode and rejects legacy or mismatched authority' {
        $policyJson = '{"schema_version":3,"protocol":"math-research-cycle-policy/v3"}'
        $ticketsJson = '{"schema_version":3,"tickets":[{"attempt_kind":"route_execution"}]}'
        $policySha = Get-Sha256HexFromText -Text $policyJson
        $ticketsSha = Get-Sha256HexFromText -Text $ticketsJson
        $identity = Get-ProjectIdentitySha256 -ProjectArchiveSchema 1 -ProjectId 'five-sixth-powers-0001' -ProjectDirectoryName 'five-sixth-powers'
        $prompt = @"
# Math Research Orchestration Prompt v7
<!-- math-research-launcher
schema: 7
approval_mode: approve_for_me
contract_version: v3
model: gpt-5.6-sol
reasoning_effort: xhigh
web_search: allowed
total_round_budget: 5
attempt_budget: 3
audit_interval_attempts: 2
max_child_agents: 3
max_total_agents: 4
max_runtime_minutes: 0
goal_objective_sha256: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
cycle_policy_sha256: $policySha
initial_tickets_sha256: $ticketsSha
project_archive_schema: 1
project_id: five-sixth-powers-0001
project_directory_name: five-sixth-powers
project_identity_sha256: $identity
-->

<!-- math-research-cycle-policy
$policyJson
-->

<!-- math-research-initial-tickets
$ticketsJson
-->

## Launch intent

The semantic authorization receipt approves this exact v7 contract and immediate launch.

## Goal continuity and bootstrap gate

Establish and verify the Goal before research.

## Immutable Research Contract v3

Frozen contract.

## State, events, and budget gate

Before every substantive mathematical attempt, register ATTEMPT_START. When ``attempts_since_last_audit == audit_interval_attempts``, audit. The global ``attempt_count`` never resets.

## Research execution

有可靠的开放路线时，从档案中选择一条与近期失败路线原理不同的路线继续。

没有可用路线时，登记一次范围明确、停止条件明确的路线发现尝试。

每次尝试只回答一个已经冻结的数学问题。

只要结局声称产生数学结论，就必须由另一份核验报告逐步检查最终候选。

每次尝试最多使用一次预先登记的定向修订；修订后的版本必须重新核验。

如果需要新的引理、桥梁或跨路线综合，必须另行登记 ATTEMPT_START。

审计只能整理既有路线卡，不能现场发明路线或补证明。

## Three-role audit

Spawn exactly ``skeptic_quantifiers``, ``skeptic_strategy``, and ``theory_tool_scout``. They inspect only existing evidence. Completion requires all three PASS on the same frozen completion candidate.

## Sources, computation, and isolation

Preserve source grades and isolation.

## Pause, Resume, and return

Resume only the signed run with the pinned thread/executable and same contract. A pending audit remains first after Resume. Never silently amend the theorem or contract.
"@
        $metadata = Parse-PromptV7Metadata -PromptText $prompt
        Assert-True ([int]$metadata.schema -eq 7 -and [string]$metadata.approval_mode -ceq 'approve_for_me') 'Prompt v7 did not retain approval_mode.'
        $context = [pscustomobject]@{ Layout='project'; ProjectArchiveSchema=1; ProjectId='five-sixth-powers-0001'; ProjectDirectoryName='five-sixth-powers' }
        Test-PromptMetadataAgainstParameters -Metadata $metadata -MaxChildAgents 3 -Model 'gpt-5.6-sol' -ReasoningEffort xhigh -ApprovalMode approve_for_me -MaxRuntimeMinutes 0 -GoalObjectiveSha256 ('a' * 64) -RunContext $context
        Assert-ThrowsLike { Test-PromptMetadataAgainstParameters -Metadata $metadata -MaxChildAgents 3 -Model 'gpt-5.6-sol' -ReasoningEffort xhigh -ApprovalMode never -MaxRuntimeMinutes 0 -GoalObjectiveSha256 ('a' * 64) -RunContext $context } 'approval_mode' 'Caller argv was allowed to amend Prompt v7 authority.'
        $v6 = $prompt.Replace('# Math Research Orchestration Prompt v7','# Math Research Orchestration Prompt v6').Replace("schema: 7`napproval_mode: approve_for_me`n", "schema: 6`n")
        Assert-ThrowsLike { Parse-PromptV7Metadata -PromptText $v6 } 'v2 mode accepts only' 'Prompt v6 was accepted for a v2 New run.'
        Assert-ThrowsLike { Parse-PromptV7Metadata -PromptText ($prompt.Replace('approval_mode: approve_for_me','approval_mode: on-request')) } 'exactly one approval_mode' 'An unsupported approval mode was accepted.'
        Assert-ThrowsLike { Parse-PromptV7Metadata -PromptText ($prompt.Replace("approval_mode: approve_for_me`n",'')) } 'exactly one approval_mode' 'A missing approval authority binding was accepted.'
    }

    Invoke-Test 'V2 bundle receipt accepts one coherent tuple and blocks legacy, mixed, and tampered tuples' {
        function Get-FixtureHash([string]$text) { Get-Sha256HexFromText -Text $text }
        $bundle = [pscustomobject]@{
            ModulePath='C:\trusted\v2\MathResearchCycleLedgerV2.psm1'; ModuleSha256=Get-FixtureHash 'cycle-module'
            CliPath='C:\trusted\v2\invoke_math_research_cycle_v2.ps1'; CliSha256=Get-FixtureHash 'cycle-cli'
            ProjectModulePath='C:\trusted\v2\MathResearchProjectArchiveV2.psm1'; ProjectModuleSha256=Get-FixtureHash 'project-module'
            ProjectCliPath='C:\trusted\v2\invoke_math_research_project_v2.ps1'; ProjectCliSha256=Get-FixtureHash 'project-cli'
            LauncherModulePath='C:\trusted\v2\MathResearchLauncherV2.psm1'; LauncherModuleSha256=Get-FixtureHash 'launcher-module'
            LauncherEntryPath='C:\trusted\v2\launch_math_research_v2.ps1'; LauncherEntrySha256=Get-FixtureHash 'launcher-entry'
            CanaryEntryPath='C:\trusted\v2\invoke_math_research_canary_v2.ps1'; CanaryEntrySha256=Get-FixtureHash 'canary-entry'
            StopCliPath='C:\trusted\v2\stop_math_research_v2.ps1'; StopCliSha256=Get-FixtureHash 'stop-cli'
        }
        $manifest = [ordered]@{
            launcher_protocol='math-research-launcher/v2'; prompt_version='v7'
            cycle_ledger=[ordered]@{
                module=[ordered]@{path=$bundle.ModulePath;sha256=$bundle.ModuleSha256}
                cli=[ordered]@{path=$bundle.CliPath;sha256=$bundle.CliSha256}
                project_module=[ordered]@{path=$bundle.ProjectModulePath;sha256=$bundle.ProjectModuleSha256}
            }
            launcher_bundle=[ordered]@{
                cycle_module=[ordered]@{path=$bundle.ModulePath;sha256=$bundle.ModuleSha256}
                cycle_cli=[ordered]@{path=$bundle.CliPath;sha256=$bundle.CliSha256}
                project_module=[ordered]@{path=$bundle.ProjectModulePath;sha256=$bundle.ProjectModuleSha256}
                project_cli=[ordered]@{path=$bundle.ProjectCliPath;sha256=$bundle.ProjectCliSha256}
                launcher_module=[ordered]@{path=$bundle.LauncherModulePath;sha256=$bundle.LauncherModuleSha256}
                launcher_entry=[ordered]@{path=$bundle.LauncherEntryPath;sha256=$bundle.LauncherEntrySha256}
                canary_entry=[ordered]@{path=$bundle.CanaryEntryPath;sha256=$bundle.CanaryEntrySha256}
                stop_cli=[ordered]@{path=$bundle.StopCliPath;sha256=$bundle.StopCliSha256}
            }
        }
        Assert-True (Assert-MathResearchV2BundleReceipt -Bundle $bundle -Manifest $manifest) 'A coherent v2 bundle was rejected.'
        $tampered = ($manifest | ConvertTo-Json -Depth 32) | ConvertFrom-Json -AsHashtable -Depth 32 -DateKind String
        $tampered.launcher_bundle.project_cli.sha256 = ('0' * 64)
        Assert-ThrowsLike { Assert-MathResearchV2BundleReceipt -Bundle $bundle -Manifest $tampered } 'SHA-256 differs' 'A single-pin tamper was accepted.'
        $mixed = ($manifest | ConvertTo-Json -Depth 32) | ConvertFrom-Json -AsHashtable -Depth 32 -DateKind String
        $mixed.launcher_bundle.cycle_cli.path = 'C:\trusted\v1\invoke_math_research_cycle.ps1'
        Assert-ThrowsLike { Assert-MathResearchV2BundleReceipt -Bundle $bundle -Manifest $mixed } 'path differs' 'A mixed v1/v2 tuple was accepted.'
        $legacy = ($manifest | ConvertTo-Json -Depth 32) | ConvertFrom-Json -AsHashtable -Depth 32 -DateKind String
        $legacy.launcher_protocol = 'math-research-launcher/v1'; $legacy.prompt_version = 'v6'
        Assert-ThrowsLike { Assert-MathResearchV2BundleReceipt -Bundle $bundle -Manifest $legacy } 'versioned_migration_required' 'A legacy run was silently accepted by v2.'
    }

    Invoke-Test 'Mandatory canary succeeds, reuses only an identical binding, and uses immutable low-cost argv' {
        $fixture = New-CanaryFixture -Root $fullTestRoot -Name 'canary-success'
        $attestation = [pscustomobject]@{
            path=$fixture.Files['codex.exe']; sha256=Get-Sha256HexFromFile -LiteralPath $fixture.Files['codex.exe']
            version='0.147.0-alpha.6.5'; signer_thumbprint='fixture-thumbprint'
        }
        $global:MathResearchV2CanaryFixture = [ordered]@{ Count=0; Mode='success'; Contexts=[Collections.Generic.List[object]]::new() }
        $callback = {
            param($context)
            $state = $global:MathResearchV2CanaryFixture
            $state.Count = [int]$state.Count + 1
            $state.Contexts.Add($context)
            if ([string]$state.Mode -ceq 'failure') {
                return [pscustomobject]@{ ExitCode=73; TimedOut=$false; OutputLimitExceeded=$false }
            }
            $threadId = '11111111-1111-4111-8111-111111111111'
            $marker = '{"marker":"MATH_RESEARCH_LAUNCHER_CANARY_V2_OK"}'
            $events = @(
                ([ordered]@{type='thread.started';thread_id=$threadId} | ConvertTo-Json -Compress),
                ([ordered]@{type='item.completed';item=[ordered]@{type='agent_message';text=$marker}} | ConvertTo-Json -Compress -Depth 8),
                ([ordered]@{type='turn.completed';usage=[ordered]@{input_tokens=1;cached_input_tokens=0;output_tokens=1;reasoning_output_tokens=0}} | ConvertTo-Json -Compress -Depth 8)
            ) -join "`n"
            Write-TestText -LiteralPath $context.StdoutPath -Text ($events + "`n")
            Write-TestText -LiteralPath $context.StderrPath -Text ''
            Write-TestText -LiteralPath $context.LastMessagePath -Text $marker
            $evidence = [ordered]@{
                schema_version=2; protocol='math-research-launcher-canary/v2'; challenge_nonce=[string]$context.Challenge.nonce
                run_manifest_sha256=[string]$context.Challenge.manifest_sha256; challenge_sha256=('a' * 64)
                ledger_before_sha256=('b' * 64); ledger_after_sha256=('b' * 64); cycle_status_sha256=('c' * 64)
                cycle_status_exit_code=0; attempt_count=0; total_round_count=0; scratch_created=$true; scratch_removed=$true
            }
            Write-TestText -LiteralPath $context.EvidencePath -Text ($evidence | ConvertTo-Json -Depth 16)
            return [pscustomobject]@{ ExitCode=0; TimedOut=$false; OutputLimitExceeded=$false }
        }
        & $launcherModule { param($override) $script:CanaryInvokerOverrideForTests = $override } $callback

        $invoke = @{
            Attestation=$attestation; RunDirectory=$fixture.Run; ManifestPath=(Join-Path $fixture.Run 'run.json')
            LauncherEntryPath=$fixture.Files['launch_math_research_v2.ps1']; LauncherModulePath=$fixture.Files['MathResearchLauncherV2.psm1']
            CanaryEntryPath=$fixture.Files['invoke_math_research_canary_v2.ps1']; CycleCliPath=$fixture.Files['invoke_math_research_cycle_v2.ps1']
            ApprovalMode='approve_for_me'; Model='gpt-5.6-sol'; ReasoningEffort='xhigh'; WebSearch='allowed'; MaxChildAgents=3
        }
        $first = Invoke-MathResearchLauncherCanaryV2 @invoke
        Assert-True ($first.Passed -and -not $first.Reused -and [int]$global:MathResearchV2CanaryFixture.Count -eq 1) 'Fresh canary did not run exactly once.'
        $context = $global:MathResearchV2CanaryFixture.Contexts[0]
        $args = [string[]]$context.Arguments
        Assert-True ($args -contains '--approve-for-me' -and $args -notcontains '-a' -and $args -contains 'workspace-write') 'Canary did not use the bound approval/sandbox control path.'
        Assert-True ($args -contains '--ephemeral' -and $args -contains 'model_reasoning_effort="low"' -and $args -notcontains '--search') 'Canary did not use the fixed low-cost ephemeral envelope.'
        $multiIndex = [Array]::IndexOf($args,'multi_agent')
        Assert-True ($multiIndex -gt 0 -and $args[$multiIndex-1] -ceq '--disable') 'Canary did not disable child agents.'
        Assert-True ($context.PromptText.Contains($fixture.Files['invoke_math_research_canary_v2.ps1'])) 'Canary prompt did not invoke the pinned installed entry.'
        Assert-True (-not $context.PromptText.Contains((Join-Path $fixture.Run 'launcher-canary-probe-v2.ps1'))) 'Canary prompt executes an agent-writable wrapper.'
        $receipt = Read-SignedJsonPayload -LiteralPath $first.ReceiptPath
        Assert-True ([string]$receipt.Payload.binding.canary_execution.reasoning_effort -ceq 'low' -and [string]$receipt.Payload.binding.research_envelope.reasoning_effort -ceq 'xhigh') 'Receipt conflated operational and research reasoning envelopes.'
        Assert-True ([int]$receipt.Payload.result.attempt_count -eq 0 -and [int]$receipt.Payload.result.total_round_count -eq 0) 'Canary consumed a research attempt or round.'

        $second = Invoke-MathResearchLauncherCanaryV2 @invoke
        Assert-True ($second.Reused -and [int]$global:MathResearchV2CanaryFixture.Count -eq 1) 'Identical signed canary binding was not reused.'
        New-Item -ItemType Directory -Force -Path (Join-Path $fixture.Run '.codex\rules') | Out-Null
        Write-TestText -LiteralPath (Join-Path $fixture.Run '.codex\rules\fixture.rules') -Text 'prefix_rule(pattern=["fixture"], decision="allow")'
        $third = Invoke-MathResearchLauncherCanaryV2 @invoke
        Assert-True (-not $third.Reused -and [int]$global:MathResearchV2CanaryFixture.Count -eq 2) 'Rules fingerprint change did not invalidate the canary receipt.'
    }

    Invoke-Test 'Mandatory canary blocks launch on policy-path failure and writes no passing receipt' {
        $fixture = New-CanaryFixture -Root $fullTestRoot -Name 'canary-failure'
        $attestation = [pscustomobject]@{
            path=$fixture.Files['codex.exe']; sha256=Get-Sha256HexFromFile -LiteralPath $fixture.Files['codex.exe']
            version='0.147.0-alpha.6.5'; signer_thumbprint='fixture-thumbprint'
        }
        $global:MathResearchV2CanaryFixture.Mode = 'failure'
        $callback = { param($context) $global:MathResearchV2CanaryFixture.Count = [int]$global:MathResearchV2CanaryFixture.Count + 1; return [pscustomobject]@{ExitCode=73;TimedOut=$false;OutputLimitExceeded=$false} }
        & $launcherModule { param($override) $script:CanaryInvokerOverrideForTests = $override } $callback
        Assert-ThrowsLike {
            Invoke-MathResearchLauncherCanaryV2 -Attestation $attestation -RunDirectory $fixture.Run -ManifestPath (Join-Path $fixture.Run 'run.json') -LauncherEntryPath $fixture.Files['launch_math_research_v2.ps1'] -LauncherModulePath $fixture.Files['MathResearchLauncherV2.psm1'] -CanaryEntryPath $fixture.Files['invoke_math_research_canary_v2.ps1'] -CycleCliPath $fixture.Files['invoke_math_research_cycle_v2.ps1'] -ApprovalMode approve_for_me -Model 'gpt-5.6-sol' -ReasoningEffort xhigh -WebSearch allowed -MaxChildAgents 3
        } 'Mandatory launcher canary was rejected' 'A rejected mandatory canary did not block launch.'
        Assert-True (-not (Test-Path -LiteralPath (Join-Path $fixture.Run 'launcher-canary-v2.json'))) 'A failed canary wrote a passing receipt.'
    }

    Invoke-Test 'Default entry and frozen launcher references preserve current authority without hash relay or host-policy leakage' {
        $surfacePaths = @(
            (Join-Path $candidateRoot 'SKILL.md'),
            (Join-Path $candidateRoot 'agents\openai.yaml'),
            (Join-Path $candidateRoot 'references\startup-fast-path.md'),
            (Join-Path $candidateRoot 'references\campaign-authorization.md'),
            (Join-Path $candidateRoot 'references\contract-and-prompt-template-v7.md'),
            (Join-Path $candidateRoot 'references\cycle-audit-protocol.md'),
            (Join-Path $candidateRoot 'references\research-project-archive.md'),
            (Join-Path $candidateRoot 'references\legacy-semantic-archive.md'),
            (Join-Path $candidateRoot 'assets\heartbeat-prompt.md.template'))
        foreach ($path in $surfacePaths) {
            Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Required authority surface is missing: $path"
            $text = [IO.File]::ReadAllText($path,[Text.UTF8Encoding]::new($false,$true))
            Assert-True ($text -notmatch 'reply_exactly|确认并启动') "Obsolete hash/phrase relay remains in an automatic or normative surface: $path"
            Assert-True ($text -notmatch '(?i)new\s+(?:runs?|contracts?).{0,40}Prompt v6|新(?:运行|合同).{0,40}Prompt v6') "A normative surface still routes New to Prompt v6: $path"
        }
        $skillText=[IO.File]::ReadAllText((Join-Path $candidateRoot 'SKILL.md'),$utf8)
        $campaignText=[IO.File]::ReadAllText((Join-Path $candidateRoot 'references\campaign-authorization.md'),$utf8)
        $heartbeatText=[IO.File]::ReadAllText((Join-Path $candidateRoot 'assets\heartbeat-prompt.md.template'),$utf8)
        foreach ($text in @($campaignText,$heartbeatText)) {
            Assert-True ($text -match 'require_escalated' -and $text -match 'managed auto-review') 'Auto-review surface omits direct narrow escalation semantics.'
            Assert-True ($text -match 'scheduler host' -and $text -match 'child' -and $text -match 'manifest') 'Host scheduler policy is not explicitly separated from child contract authority.'
        }
        Assert-True ($skillText -match 'Freshly call `get_goal`' -and $skillText -match 'local fail-closed gate') 'Current v13 Skill omits its direct Goal-authority gate.'
        $agentText=[IO.File]::ReadAllText((Join-Path $candidateRoot 'agents\openai.yaml'),$utf8)
        Assert-True ($agentText -match 'v13 Full Startup' -and $agentText -match 'fresh independent subagent' -and $agentText -match 'six-field objective commitment') 'Default agent prompt does not bind the current v13 startup and review authority.'
        foreach ($legacyPath in @('references\contract-and-prompt-template.md','references\legacy-math-research-prompt.md')) {
            $legacy=[IO.File]::ReadAllText((Join-Path $candidateRoot $legacyPath),$utf8)
            Assert-True ($legacy -match 'inspection-only' -and $legacy -notmatch 'reply_exactly|确认并启动') "Legacy compatibility path is still runnable or hash-gated: $legacyPath"
        }
        $launcherSource=[IO.File]::ReadAllText($launcherPath,$utf8)
        Assert-True ($launcherSource -match '\$approvalModeForRun\s*=\s*\[string\]\$manifest\.config\.approval_mode') 'Resume does not derive child ApprovalMode from the signed manifest.'
        Assert-True ($launcherSource -match '-ApprovalMode \$approvalModeForRun' -and $launcherSource -notmatch '(?s)else\s*\{.{0,400}BoundParameters\.Contains\(''ApprovalMode''\).{0,400}\$approvalModeForRun\s*=\s*\$ApprovalMode') 'A host/caller approval mode can override Resume child argv.'
    }

    Invoke-Test 'Selected attested Codex binary advertises both approval control paths' {
        $attestation = Select-TrustedCodexExecutable -WorkingDirectory $fullTestRoot
        $selectedPath = [IO.Path]::GetFullPath([string]$attestation.path)
        Assert-True (Test-PathInsideDirectory -Child $selectedPath -Directory (Get-CodexBinRoot)) "Selected Codex binary escaped the official signed bin root: $selectedPath"
        Assert-True ([string]$attestation.signature_status -ceq 'Valid' -and [string]$attestation.signer_name -ceq 'OpenAI OpCo, LLC') 'Selected Codex Authenticode identity is invalid.'
        Assert-True ([string]$attestation.version -match '^\d+\.\d+\.\d+(?:[-+].+)?$') 'Selected Codex version is not semantic.'
        Assert-True ([string]$attestation.sha256 -ceq (Get-Sha256HexFromFile -LiteralPath $selectedPath)) 'Selected Codex attestation SHA does not match its actual bytes.'
        $approve = Assert-CodexApprovalModeCapability -Attestation $attestation -WorkingDirectory $fullTestRoot -ApprovalMode approve_for_me
        $never = Assert-CodexApprovalModeCapability -Attestation $attestation -WorkingDirectory $fullTestRoot -ApprovalMode never
        Assert-True ($approve.Verified -and $never.Verified -and [string]$approve.ExecHelpSha256 -ceq [string]$never.ExecHelpSha256) 'Global capability probe did not verify both modes against one binary.'
    }

    Invoke-Test 'Launcher source orders v7 genesis, full-bundle validation, canary, and Goal bootstrap' {
        $source = [IO.File]::ReadAllText($launcherPath, [Text.UTF8Encoding]::new($false,$true))
        $newBranch = $source.IndexOf("if (`$Mode -eq 'New')",[StringComparison]::Ordinal)
        $v7Parse = $source.IndexOf('Parse-PromptV7Metadata',$newBranch,[StringComparison]::Ordinal)
        $manifestWrite = $source.IndexOf('Save-Manifest -Manifest $manifest',$v7Parse,[StringComparison]::Ordinal)
        $canary = $source.IndexOf('Invoke-MathResearchLauncherCanaryV2',$manifestWrite,[StringComparison]::Ordinal)
        $goal = $source.IndexOf('New-GoalBootstrapPrompt',$canary,[StringComparison]::Ordinal)
        Assert-True ($newBranch -ge 0 -and $v7Parse -gt $newBranch -and $manifestWrite -gt $v7Parse -and $canary -gt $manifestWrite -and $goal -gt $canary) 'New v2 does not complete signed genesis and mandatory canary before Goal bootstrap.'
        foreach ($field in @('cycle_module','cycle_cli','project_module','project_cli','launcher_module','launcher_entry','canary_entry','stop_cli')) {
            Assert-True ($source -match ("(?m)^\s*" + [regex]::Escape($field) + "\s*=")) "V2 manifest does not pin bundle field $field."
        }
        $resumeBranch=$source.IndexOf('$approvalModeForRun = [string]$manifest.config.approval_mode',[StringComparison]::Ordinal)
        $resumeResolve=$source.IndexOf('$cycleController = Resolve-CycleControllerBundle',$resumeBranch,[StringComparison]::Ordinal)
        $resumeValidate=$source.IndexOf('Assert-CycleControllerBundleMatchesManifest',$resumeResolve,[StringComparison]::Ordinal)
        $resumeImport=$source.IndexOf('$cycleController = Import-CycleControllerBundle -Bundle $cycleController',$resumeValidate,[StringComparison]::Ordinal)
        Assert-True ($resumeBranch -ge 0 -and $resumeResolve -gt $resumeBranch -and $resumeValidate -gt $resumeResolve -and $resumeImport -gt $resumeValidate) 'Resume executes v2 cycle/project module bytes before signed full-tuple validation.'
        Assert-True ($source -match 'versioned_migration_required' -and $source -notmatch "prompt_version\s*=\s*'v6'") 'Legacy runs can silently enter or be created by v2.'
    }

    $allPassed = $true
}
finally {
    & $launcherModule { $script:ManifestKeyPathOverrideForTests = $null; $script:CanaryInvokerOverrideForTests = $null }
    Remove-Variable -Name MathResearchV2CanaryFixture -Scope Global -ErrorAction SilentlyContinue
    if (-not $KeepTestFiles -and (Test-Path -LiteralPath $fullTestRoot)) { Remove-Item -LiteralPath $fullTestRoot -Recurse -Force }
}

$summary = [pscustomobject]@{
    SchemaVersion=2
    Protocol='math-research-launcher-v2-tests/v1'
    Passed=$script:Passed
    Failed=@($script:Results | Where-Object Status -eq 'failed').Count
    AllPassed=$allPassed
    Results=@($script:Results)
}
$summary | ConvertTo-Json -Depth 12
if (-not $allPassed) { exit 1 }
