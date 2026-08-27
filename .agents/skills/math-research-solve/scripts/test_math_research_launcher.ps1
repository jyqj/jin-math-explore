[CmdletBinding()]
param(
    [string]$TestRoot = (Join-Path $env:TEMP ("math-research-launcher-tests-" + [Guid]::NewGuid().ToString('N'))),
    [switch]$KeepTestFiles
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)

$modulePath = Join-Path $PSScriptRoot 'MathResearchLauncher.psm1'
$projectModulePath = Join-Path $PSScriptRoot 'MathResearchProjectArchive.psm1'
$launcherPath = Join-Path $PSScriptRoot 'launch_math_research.ps1'
$stopPath = Join-Path $PSScriptRoot 'stop_math_research.ps1'
Import-Module $modulePath -Force -DisableNameChecking
Import-Module $projectModulePath -Force -DisableNameChecking
$launcherModule = Get-Module MathResearchLauncher

$script:Passed = 0
$script:Skipped = 0
$script:Results = [Collections.Generic.List[object]]::new()

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

function Assert-Equal {
    param($Actual, $Expected, [string]$Message)
    if (($Actual | ConvertTo-Json -Compress -Depth 16) -cne ($Expected | ConvertTo-Json -Compress -Depth 16)) {
        throw "$Message`nExpected: $($Expected | ConvertTo-Json -Compress -Depth 16)`nActual: $($Actual | ConvertTo-Json -Compress -Depth 16)"
    }
}

function Assert-Throws {
    param([scriptblock]$Action, [string]$Message)
    $threw = $false
    try { & $Action }
    catch { $threw = $true }
    if (-not $threw) { throw $Message }
}

function Invoke-Test {
    param([string]$Name, [scriptblock]$Action)
    try {
        & $Action
        $script:Passed++
        $script:Results.Add([pscustomobject]@{ Name = $Name; Status = 'passed'; Detail = $null })
    }
    catch {
        $script:Results.Add([pscustomobject]@{ Name = $Name; Status = 'failed'; Detail = $_.Exception.Message })
        throw "Test failed: $Name`n$($_.Exception.Message)"
    }
}

function Add-SkippedTest {
    param([string]$Name, [string]$Detail)
    $script:Skipped++
    $script:Results.Add([pscustomobject]@{ Name = $Name; Status = 'skipped'; Detail = $Detail })
}

function Invoke-PwshProbe {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    $psi = [Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = Join-Path $PSHOME 'pwsh.exe'
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    foreach ($argument in $Arguments) { $psi.ArgumentList.Add($argument) }
    $process = [Diagnostics.Process]::Start($psi)
    try {
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit(15000)) {
            $process.Kill($true)
            throw 'PowerShell probe timed out.'
        }
        return [pscustomobject]@{
            ExitCode = $process.ExitCode
            Stdout = $stdout.GetAwaiter().GetResult()
            Stderr = $stderr.GetAwaiter().GetResult()
        }
    }
    finally { $process.Dispose() }
}

$fullTestRoot = [IO.Path]::GetFullPath($TestRoot)
if (Test-Path -LiteralPath $fullTestRoot) { throw "TestRoot already exists: $fullTestRoot" }
New-Item -ItemType Directory -Force -Path $fullTestRoot | Out-Null
$originalLocalAppData = $env:LOCALAPPDATA
$originalVaultRoot = $env:OBSIDIAN_VAULT_ROOT
$allPassed = $false

try {
    Invoke-Test 'PowerShell files parse' {
        foreach ($path in @($modulePath, $launcherPath, $stopPath, $PSCommandPath)) {
            $tokens = $null
            $errors = $null
            [Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$errors) | Out-Null
            $parseDetails = @($errors | ForEach-Object { $_.Message }) -join '; '
            Assert-True ($errors.Count -eq 0) "$path has parser errors: $parseDetails"
        }
    }

    Invoke-Test 'Public launcher parameters are narrow' {
        $tokens = $null
        $errors = $null
        $ast = [Management.Automation.Language.Parser]::ParseFile($launcherPath, [ref]$tokens, [ref]$errors)
        $actual = @($ast.ParamBlock.Parameters.Name.VariablePath.UserPath | Sort-Object)
        $expected = @('ContinuationPromptFile', 'GoalObjectiveFile', 'MaxChildAgents', 'MaxRuntimeMinutes', 'Mode', 'Model', 'PromptFile', 'ReasoningEffort', 'RunDirectory' | Sort-Object)
        Assert-Equal $actual $expected 'Launcher parameter surface changed unexpectedly.'
        foreach ($removed in @('ResumeSessionId', 'ConfirmSessionIdle', 'IgnoreRules', 'CodexCommand', 'OutputLastMessageFile', 'WorkingDirectory')) {
            Assert-True ($actual -notcontains $removed) "Removed parameter is still public: $removed"
        }
    }

    Invoke-Test 'Prompt v6 genesis precedes the first Codex selection' {
        $launcherSource = [IO.File]::ReadAllText($launcherPath, [Text.UTF8Encoding]::new($false))
        $newBranch = $launcherSource.IndexOf("if (`$Mode -eq 'New')", [StringComparison]::Ordinal)
        $policyWrite = $launcherSource.IndexOf('Write-Utf8FileNew -LiteralPath $cyclePolicyPath', $newBranch, [StringComparison]::Ordinal)
        $initialize = $launcherSource.IndexOf('Initialize-MathResearchCycleLedger -RunDirectory', $newBranch, [StringComparison]::Ordinal)
        $codexSelection = $launcherSource.IndexOf('$attestation = Select-TrustedCodexExecutable', $newBranch, [StringComparison]::Ordinal)
        Assert-True ($newBranch -ge 0 -and $policyWrite -gt $newBranch -and $initialize -gt $policyWrite -and $codexSelection -gt $initialize) 'Prompt v6 policy/ticket genesis is not completed before the first possible Codex process path.'
        Assert-True ($launcherSource -match '\$metadata = Parse-PromptV6Metadata' -and $launcherSource -match "prompt_version = 'v6'") 'New mode is not pinned to Prompt v6.'
    }

    Invoke-Test 'Legacy v3 manifest remains Resume-compatible without migration' {
        $tokens = $null
        $errors = $null
        $launcherAst = [Management.Automation.Language.Parser]::ParseFile($launcherPath, [ref]$tokens, [ref]$errors)
        $resumeValidator = $launcherAst.Find({ param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Assert-ResumeManifest' }, $true)
        Assert-True ($null -ne $resumeValidator) 'Could not locate Assert-ResumeManifest for compatibility test.'
        Invoke-Expression $resumeValidator.Extent.Text
        $legacyRunPath = 'C:\approved\legacy-v3-run'
        $legacy = [ordered]@{
            schema_version = 1
            prompt_version = 'v3'
            run_directory = $legacyRunPath
            thread_id = '12345678-1234-4234-8234-1234567890ab'
            config = [ordered]@{ max_child_agents = 4; max_total_agents = 5; agent_stages = @(4); round_budget = 60; max_runtime_minutes = 0; web_search = 'denied'; reasoning_effort = 'xhigh' }
            inputs = [ordered]@{ prompt = [ordered]@{ sha256 = ('a' * 64) }; goal_objective = [ordered]@{ file_sha256 = ('b' * 64) } }
            goal = [ordered]@{ objective_sha256 = ('c' * 64); confirmation = 'model_reported_via_nonce_marker'; persistence_verified = $false }
            prompt_v3 = [ordered]@{ status = 'turn_completed'; submitted_sha256 = ('d' * 64) }
        }
        Assert-ResumeManifest -Manifest $legacy -RunPath $legacyRunPath
        Assert-True (-not $legacy.Contains('cycle_ledger')) 'Legacy v3 manifest was silently migrated to a cycle ledger.'
    }

    Invoke-Test 'Prompt v4 v5 and v6 manifests Resume only in their original layouts' {
        $tokens = $null; $errors = $null
        $launcherAst = [Management.Automation.Language.Parser]::ParseFile($launcherPath, [ref]$tokens, [ref]$errors)
        $resumeValidator = $launcherAst.Find({ param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Assert-ResumeManifest' }, $true)
        Invoke-Expression $resumeValidator.Extent.Text
        $identity = Get-ProjectIdentitySha256 -ProjectArchiveSchema 1 -ProjectId 'sample-open-problem-0001' -ProjectDirectoryName 'sample-open-problem'
        function New-CycleResumeManifest([string]$Version,[string]$RunPath) {
            $promptState=[ordered]@{status='turn_completed';submitted_sha256=('d'*64)}
            $manifest=[ordered]@{
                schema_version=1;prompt_version=$Version;run_directory=$RunPath;thread_id='12345678-1234-4234-8234-1234567890ab'
                config=[ordered]@{max_child_agents=4;max_total_agents=5;agent_stages=@(4);max_runtime_minutes=0;web_search='denied';reasoning_effort='ultra';total_round_budget=4;attempt_budget=2;audit_interval_attempts=1;round_budget_enforcement='cycle_controller'}
                inputs=[ordered]@{prompt=[ordered]@{sha256=('a'*64)};goal_objective=[ordered]@{file_sha256=('b'*64)}}
                goal=[ordered]@{objective_sha256=('c'*64);confirmation='model_reported_via_nonce_marker';persistence_verified=$false}
                cycle_ledger=[ordered]@{contract_binding_sha256=('a'*64);module=[ordered]@{sha256=('e'*64)};cli=[ordered]@{sha256=('f'*64)};policy=[ordered]@{sha256=('1'*64)};initial_tickets=[ordered]@{sha256=('2'*64)}}
            }
            if($Version -eq 'v4'){$manifest.prompt_v4=$promptState}
            else{
                $manifest.inputs.prompt.contract_binding_sha256=('9'*64);$manifest.cycle_ledger.contract_binding_sha256=('9'*64)
                $manifest.cycle_ledger.project_module=[ordered]@{sha256=('3'*64)}
                $manifest.project=[ordered]@{archive_schema=1;project_id='sample-open-problem-0001';directory_name='sample-open-problem';identity_sha256=$identity}
                if($Version -eq 'v5'){$manifest.prompt_v5=$promptState}else{$manifest.prompt_v6=$promptState}
            }
            return $manifest
        }
        $legacyContext=[pscustomobject]@{Layout='legacy'}
        $projectContext=[pscustomobject]@{Layout='project';ProjectArchiveSchema=1;ProjectId='sample-open-problem-0001';ProjectDirectoryName='sample-open-problem'}
        $v4=New-CycleResumeManifest -Version v4 -RunPath 'C:\approved\legacy-v4-run'
        Assert-ResumeManifest -Manifest $v4 -RunPath $v4.run_directory -RunContext $legacyContext
        $v5=New-CycleResumeManifest -Version v5 -RunPath 'C:\approved\project\runs\v5-run'
        Assert-ResumeManifest -Manifest $v5 -RunPath $v5.run_directory -RunContext $projectContext
        $v6=New-CycleResumeManifest -Version v6 -RunPath 'C:\approved\project\runs\v6-run'
        Assert-ResumeManifest -Manifest $v6 -RunPath $v6.run_directory -RunContext $projectContext
        Assert-Throws { Assert-ResumeManifest -Manifest $v5 -RunPath $v5.run_directory -RunContext $legacyContext } 'Prompt v5 resumed from legacy layout.'
        Assert-Throws { Assert-ResumeManifest -Manifest $v6 -RunPath $v6.run_directory -RunContext $legacyContext } 'Prompt v6 resumed from legacy layout.'
        Assert-Throws { Assert-ResumeManifest -Manifest $v4 -RunPath $v4.run_directory -RunContext $projectContext } 'Prompt v4 resumed from project layout.'
    }

    Invoke-Test 'Script entry validates the caller parameter set, not function-local bindings' {
        $missingRun = Join-Path $fullTestRoot 'missing-run'
        $newProbe = Invoke-PwshProbe -Arguments @('-NoLogo', '-NoProfile', '-File', $launcherPath, '-Mode', 'New', '-RunDirectory', $missingRun, '-PromptFile', (Join-Path $missingRun 'prompt.md'), '-GoalObjectiveFile', (Join-Path $missingRun 'goal.md'), '-MaxChildAgents', '1', '-Model', 'gpt-5.4', '-ReasoningEffort', 'high', '-MaxRuntimeMinutes', '0')
        Assert-True ($newProbe.ExitCode -ne 0) 'Shape test unexpectedly reached a real New launch.'
        Assert-True ($newProbe.Stderr -notmatch 'New mode requires') "Valid New parameters were lost inside Assert-InvocationShape: $($newProbe.Stderr)"

        $resumeProbe = Invoke-PwshProbe -Arguments @('-NoLogo', '-NoProfile', '-File', $launcherPath, '-Mode', 'Resume', '-RunDirectory', $missingRun, '-ContinuationPromptFile', (Join-Path $missingRun 'continue.md'))
        Assert-True ($resumeProbe.ExitCode -ne 0) 'Shape test unexpectedly reached a real Resume launch.'
        Assert-True ($resumeProbe.Stderr -notmatch 'Resume mode requires') "Valid Resume parameters were lost inside Assert-InvocationShape: $($resumeProbe.Stderr)"
    }

    Invoke-Test 'Agent stages map arbitrary child caps' {
        Assert-Equal @(Get-AgentStages -MaxChildAgents 1) @(1) 'C=1 stages are wrong.'
        Assert-Equal @(Get-AgentStages -MaxChildAgents 6) @(4, 6) 'C=6 stages are wrong.'
        Assert-Equal @(Get-AgentStages -MaxChildAgents 10) @(4, 8, 10) 'C=10 stages are wrong.'
        Assert-Equal @(Get-AgentStages -MaxChildAgents 16) @(4, 8, 12, 16) 'C=16 stages are wrong.'
        Assert-Throws { Get-AgentStages -MaxChildAgents 0 } 'C=0 was accepted.'
        Assert-Throws { Get-AgentStages -MaxChildAgents 17 } 'C=17 was accepted.'
    }

    Invoke-Test 'Prompt v4 metadata and exact LF JSON-body hashes are strict' {
        $policyJson = '{"schema":1,"audit_interval_attempts":5}'
        $ticketsJson = '{"schema":1,"tickets":[{"ticket_id":"T-001"}]}'
        $policySha256 = Get-Sha256HexFromText -Text $policyJson
        $ticketsSha256 = Get-Sha256HexFromText -Text $ticketsJson
        $prompt = @"
# Math Research Orchestration Prompt v4
<!-- math-research-launcher
schema: 4
contract_version: v2
model: gpt-5.4
reasoning_effort: xhigh
web_search: allowed
total_round_budget: 18
attempt_budget: 15
audit_interval_attempts: 5
max_child_agents: 16
max_total_agents: 17
max_runtime_minutes: 0
goal_objective_sha256: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
cycle_policy_sha256: $policySha256
initial_tickets_sha256: $ticketsSha256
-->

<!-- math-research-cycle-policy
$policyJson
-->

<!-- math-research-initial-tickets
$ticketsJson
-->

## Launch intent

The bound confirmation approves this exact PromptFile and authorizes immediate Cycle 1 launch.

## Goal continuity and bootstrap gate

Before mathematical research, inspect the Goal control plane.

## Immutable Research Contract v2

Frozen contract.

## State, events, and budget gate

Before every substantive mathematical attempt, register ATTEMPT_START and account for it. When ``attempts_since_last_audit == audit_interval_attempts``, set the audit gate. A valid audit clears attempts-since-audit, but global ``attempt_count`` never resets.

## Research execution

Use bounded tickets and inspectable artifacts.

## Three-role audit

Spawn exactly ``skeptic_quantifiers``, ``skeptic_strategy``, and ``theory_tool_scout`` for separate reports. They inspect only existing evidence and do no proof repair. Completion requires all three PASS on the same frozen completion candidate.

## Sources, computation, and isolation

Preserve evidence grades and launcher isolation.

## Pause, Resume, and return

Resume only the signed run with the pinned thread/executable and same contract. A pending audit remains first after Resume. Never silently amend the theorem or contract.
"@
        $metadata = Parse-PromptV4Metadata -PromptText $prompt
        Test-PromptMetadataAgainstParameters -Metadata $metadata -MaxChildAgents 16 -Model 'gpt-5.4' -ReasoningEffort 'xhigh' -MaxRuntimeMinutes 0 -GoalObjectiveSha256 ('a' * 64)
        Assert-True ($metadata.web_search -eq 'allowed') 'web_search metadata was not parsed.'
        Assert-True ($metadata.total_round_budget -eq 18 -and $metadata.attempt_budget -eq 15 -and $metadata.audit_interval_attempts -eq 5) 'Cycle budgets were not parsed.'
        Assert-True ($metadata.cycle_policy_json -ceq $policyJson -and $metadata.initial_tickets_json -ceq $ticketsJson) 'Exact JSON bodies were not preserved.'
        $crlfPrompt = $prompt.Replace("`n", "`r`n")
        $crlfMetadata = Parse-PromptV4Metadata -PromptText $crlfPrompt
        Assert-True ($crlfMetadata.cycle_policy_json -ceq $policyJson) 'CRLF-to-LF normalization changed the captured JSON body.'
        Assert-Throws { Test-PromptMetadataAgainstParameters -Metadata $metadata -MaxChildAgents 15 -Model 'gpt-5.4' -ReasoningEffort 'xhigh' -MaxRuntimeMinutes 0 -GoalObjectiveSha256 ('a' * 64) } 'A mismatched child cap was accepted.'
        Assert-Throws { Test-PromptMetadataAgainstParameters -Metadata $metadata -MaxChildAgents 16 -Model 'gpt-5.4' -ReasoningEffort 'xhigh' -MaxRuntimeMinutes 0 -GoalObjectiveSha256 ('b' * 64) } 'A mismatched Goal objective hash was accepted.'
        Assert-Throws { Parse-PromptV4Metadata -PromptText ($prompt.Replace('## Immutable Research Contract v2', '## Immutable Research Contract v1')) } 'A mismatched Research Contract heading was accepted.'
        Assert-Throws { Parse-PromptV4Metadata -PromptText ($prompt.Replace('They inspect only existing evidence', 'Auditors inspect evidence')) } 'A missing collaboration rule was accepted.'
        Assert-Throws { Parse-PromptV4Metadata -PromptText ($prompt.Replace("cycle_policy_sha256: $policySha256", ('cycle_policy_sha256: ' + ('b' * 64)))) } 'A mismatched exact policy-body hash was accepted.'
        Assert-Throws { Parse-PromptV4Metadata -PromptText ($prompt.Replace($policyJson, '{"schema":1,"schema":2,"audit_interval_attempts":5}').Replace("cycle_policy_sha256: $policySha256", ('cycle_policy_sha256: ' + (Get-Sha256HexFromText -Text '{"schema":1,"schema":2,"audit_interval_attempts":5}')))) } 'Duplicate JSON properties were accepted.'
        Assert-Throws { Parse-PromptV4Metadata -PromptText ($prompt + "`n<!-- math-research-cycle-policy`n{}`n-->") } 'A duplicate policy block was accepted.'
        Assert-Throws { Parse-PromptV4Metadata -PromptText ($prompt.Replace('Frozen contract.', "Frozen`rcontract.")) } 'An isolated CR was accepted.'
        Assert-Throws { Parse-PromptV4Metadata -PromptText ($prompt.Replace('# Math Research Orchestration Prompt v4', '# Math Research Orchestration Prompt v3').Replace('schema: 4', 'schema: 3')) } 'New mode accepted a legacy full Prompt v3.'

        $identity = Get-ProjectIdentitySha256 -ProjectArchiveSchema 1 -ProjectId 'sample-open-problem-0001' -ProjectDirectoryName 'sample-open-problem'
        $v5 = $prompt.Replace('# Math Research Orchestration Prompt v4', '# Math Research Orchestration Prompt v5').Replace("schema: 4`n", "schema: 5`nproject_archive_schema: 1`nproject_id: sample-open-problem-0001`nproject_directory_name: sample-open-problem`nproject_identity_sha256: $identity`n").Replace('reasoning_effort: xhigh','reasoning_effort: ultra')
        $v5Metadata = Parse-PromptV5Metadata -PromptText $v5
        Assert-True ($v5Metadata.project_id -eq 'sample-open-problem-0001' -and $v5Metadata.reasoning_effort -eq 'ultra') 'Prompt v5 project identity or ultra reasoning was not parsed.'
        $runContext = [pscustomobject]@{ Layout='project'; ProjectArchiveSchema=1; ProjectId='sample-open-problem-0001'; ProjectDirectoryName='sample-open-problem' }
        Test-PromptMetadataAgainstParameters -Metadata $v5Metadata -MaxChildAgents 16 -Model 'gpt-5.4' -ReasoningEffort 'ultra' -MaxRuntimeMinutes 0 -GoalObjectiveSha256 ('a' * 64) -RunContext $runContext
        Assert-Throws { Parse-PromptV5Metadata -PromptText ($v5.Replace("project_identity_sha256: $identity", ('project_identity_sha256: ' + ('0' * 64)))) } 'Prompt v5 accepted a mismatched project identity hash.'

        $policyV6 = '{"schema_version":3,"protocol":"math-research-cycle-policy/v3"}'
        $ticketsV6 = '{"schema_version":3,"tickets":[{"attempt_kind":"route_execution"}]}'
        $rulesV6 = @'
有可靠的开放路线时，从档案中选择一条与近期失败路线原理不同的路线继续。

没有可用路线时，登记一次范围明确、停止条件明确的路线发现尝试。

每次尝试只回答一个已经冻结的数学问题。

只要结局声称产生数学结论，就必须由另一份核验报告逐步检查最终候选。

每次尝试最多使用一次预先登记的定向修订；修订后的版本必须重新核验。

如果需要新的引理、桥梁或跨路线综合，必须另行登记 ATTEMPT_START。

审计只能整理既有路线卡，不能现场发明路线或补证明。
'@
        $v6 = $v5.Replace('# Math Research Orchestration Prompt v5', '# Math Research Orchestration Prompt v6').Replace("schema: 5`n", "schema: 6`n").Replace($policyJson,$policyV6).Replace($ticketsJson,$ticketsV6).Replace("cycle_policy_sha256: $policySha256", ('cycle_policy_sha256: ' + (Get-Sha256HexFromText -Text $policyV6))).Replace("initial_tickets_sha256: $ticketsSha256", ('initial_tickets_sha256: ' + (Get-Sha256HexFromText -Text $ticketsV6))).Replace('Use bounded tickets and inspectable artifacts.',("Use bounded tickets and inspectable artifacts.`n`n" + $rulesV6.TrimEnd()))
        $v6Metadata = Parse-PromptV6Metadata -PromptText $v6
        Assert-True ($v6Metadata.schema -eq 6 -and $v6Metadata.project_id -eq 'sample-open-problem-0001') 'Prompt v6 metadata was not parsed.'
        Test-PromptMetadataAgainstParameters -Metadata $v6Metadata -MaxChildAgents 16 -Model 'gpt-5.4' -ReasoningEffort 'ultra' -MaxRuntimeMinutes 0 -GoalObjectiveSha256 ('a' * 64) -RunContext $runContext
        Assert-Throws { Parse-PromptV6Metadata -PromptText $v5 } 'Prompt v5 was accepted as a new v6 run.'
        Assert-Throws { Parse-PromptV6Metadata -PromptText ($v6.Replace('每次尝试只回答一个已经冻结的数学问题。','每次可处理若干问题。')) } 'Prompt v6 accepted a missing research-loop rule.'
    }

    Invoke-Test 'CLI arguments enforce isolation and direct child cap' {
        $run = 'C:\approved\run'
        $last = 'C:\approved\run\last-message-001-research.md'
        $thread = '12345678-1234-4234-8234-1234567890ab'
        $args = New-CodexExecArguments -RunDirectory $run -Model 'gpt-5.4' -ReasoningEffort 'xhigh' -Sandbox 'workspace-write' -AllowWebSearch:$true -EnableMultiAgent:$true -MaxChildAgents 16 -LastMessagePath $last -ResumeThreadId $thread
        Assert-True ($args -contains 'agents.max_threads=16') 'agents.max_threads is not set directly to the child cap.'
        Assert-True ($args -notcontains 'agents.max_threads=17') 'The old off-by-one mapping remains.'
        Assert-True ($args -contains '--ignore-user-config') '--ignore-user-config is missing.'
        Assert-True ($args -contains '--search') '--search is missing for an allowed contract.'
        Assert-True ($args -notcontains '--ignore-rules') 'Rules bypass was added.'
        $separator = [Array]::IndexOf($args, '--')
        $threadIndex = [Array]::IndexOf($args, $thread)
        Assert-True ($separator -ge 0 -and $threadIndex -eq $separator + 1) 'The UUID is not protected by --.'
        Assert-True ($args[$threadIndex + 1] -eq '-') 'Resume stdin marker is misplaced.'

        $goalArgs = New-CodexExecArguments -RunDirectory $run -Model 'gpt-5.4' -ReasoningEffort 'xhigh' -Sandbox 'read-only' -AllowWebSearch:$false -EnableMultiAgent:$false -LastMessagePath 'C:\approved\run\last-message-000-goal.json'
        $multiAgentIndex = [Array]::IndexOf([string[]]$goalArgs, 'multi_agent')
        Assert-True ($multiAgentIndex -gt 0 -and $goalArgs[$multiAgentIndex - 1] -eq '--disable') 'Goal bootstrap did not disable the multi_agent feature.'
        Assert-Equal @($goalArgs | Where-Object { $_ -like 'agents.max_threads=*' }).Count 0 'Goal bootstrap unexpectedly configured child-agent threads.'
        Assert-True ($goalArgs -notcontains '--search') 'Goal bootstrap unexpectedly enables search.'
        Assert-Throws { New-CodexExecArguments -RunDirectory $run -Model 'gpt-5.4' -ReasoningEffort 'xhigh' -Sandbox 'workspace-write' -AllowWebSearch:$false -EnableMultiAgent:$true -MaxChildAgents 1 -LastMessagePath $last -ResumeThreadId '--last' } 'Resume option injection was accepted.'

        $continuationText = "# Math Research Continuation v1`n`nContinue from obligation L3."
        $continuation = New-ContinuationTurnPrompt -Objective 'Prove T.' -ObjectiveSha256 ('a' * 64) -ContinuationText $continuationText -MaxChildAgents 10 -AgentStages @(4, 8, 10) -RoundBudget 60 -MaxRuntimeMinutes 0 -WebSearch denied
        Assert-True ($continuation -match 'call `get_goal`' -and $continuation -match 'Continue from obligation L3\.') 'Resume continuation gate is incomplete.'
        Assert-True ($continuation -notmatch '# Math Research Orchestration Prompt v3') 'Resume wrapper repeats the initial Prompt v3 header.'
        Assert-Throws { Assert-ContinuationInstruction -Text '# Math Research Orchestration Prompt v3' -Sha256 ('b' * 64) -OriginalPromptSha256 ('a' * 64) } 'A full Prompt v3 header was accepted as a continuation.'
        Assert-Throws { Assert-ContinuationInstruction -Text '# Math Research Orchestration Prompt v4' -Sha256 ('b' * 64) -OriginalPromptSha256 ('a' * 64) } 'A full Prompt v4 header was accepted as a continuation.'
        Assert-Throws { Assert-ContinuationInstruction -Text $continuationText -Sha256 ('a' * 64) -OriginalPromptSha256 ('a' * 64) } 'The original Prompt v3 hash was accepted as a continuation.'
        Assert-Throws { Assert-ContinuationInstruction -Text "# Math Research Continuation v1`n`n# Immutable Research Contract v1`n..." -Sha256 ('b' * 64) -OriginalPromptSha256 ('a' * 64) } 'A copied frozen contract was accepted as a continuation.'
        Assert-ContinuationInstruction -Text $continuationText -Sha256 ('b' * 64) -OriginalPromptSha256 ('a' * 64)
        Assert-True ($continuation -match 'round_budget_must_not_reset_on_resume: true' -and $continuation -match 'web_search: denied') 'Resume wrapper omitted frozen budget or search facts.'

        $researchTurn = New-ResearchTurnPrompt -Objective 'Prove T.' -ObjectiveSha256 ('a' * 64) -PromptText 'approved body' -MaxChildAgents 10 -AgentStages @(4, 8, 10) -RoundBudget 60 -MaxRuntimeMinutes 0 -WebSearch denied
        Assert-True ($researchTurn -match 'configured_child_agent_cap: 10' -and $researchTurn -match 'possible_configured_total_including_root: 11') 'Research wrapper omitted the direct child and total caps.'
        Assert-True ($researchTurn -match 'adaptive_child_agent_stages: 4,8,10' -and $researchTurn -match 'round_budget: 60' -and $researchTurn -match 'web_search: denied') 'Research wrapper omitted stages, budget, or search policy.'

        $cycleState = [pscustomobject]@{ State = 'ready'; HeadSequence = 0; HeadPayloadSha256 = ('c' * 64); CleanReturn = $true; CompletionEligible = $false; AuditDue = $false; ActiveAttempt = $null; ActiveAudit = $null }
        $cycleCliPath = 'C:\approved\scripts\invoke_math_research_cycle.ps1'
        $cycleResearch = New-CycleResearchTurnPrompt -Objective 'Prove T.' -ObjectiveSha256 ('a' * 64) -PromptText 'approved v4 body' -MaxChildAgents 10 -AgentStages @(4, 8, 10) -TotalRoundBudget 18 -AttemptBudget 15 -AuditIntervalAttempts 5 -MaxRuntimeMinutes 0 -WebSearch denied -RunDirectory $run -CycleCliPath $cycleCliPath -CycleCliSha256 ('d' * 64) -CyclePolicyFile 'C:\approved\run\cycle-policy.json' -CyclePolicySha256 ('e' * 64) -InitialTicketsFile 'C:\approved\run\cycle-tickets-000.json' -InitialTicketsSha256 ('f' * 64) -ContractBindingSha256 ('a' * 64) -CycleState $cycleState
        Assert-True ($cycleResearch -match '"cycle_cli_path":"C:\\\\approved\\\\scripts\\\\invoke_math_research_cycle\.ps1"' -and $cycleResearch -match ('d' * 64)) 'Prompt v4 wrapper omitted the JSON-encoded absolute cycle CLI path or pinned hash.'
        Assert-True ($cycleResearch -match 'round_budget_enforcement: cycle_controller' -and $cycleResearch -match 'attempts_since_last_audit') 'Prompt v4 wrapper omitted controller budget semantics.'
        $dirtyState = [pscustomobject]@{ State = 'attempt_active'; HeadSequence = 7; HeadPayloadSha256 = ('c' * 64); CleanReturn = $false; CompletionEligible = $false; AuditDue = $true; ActiveAttempt = @{ ticket_id = 'T-001' }; ActiveAudit = $null }
        $cycleContinuation = New-CycleContinuationTurnPrompt -Objective 'Prove T.' -ObjectiveSha256 ('a' * 64) -ContinuationText $continuationText -MaxChildAgents 10 -AgentStages @(4, 8, 10) -TotalRoundBudget 18 -AttemptBudget 15 -AuditIntervalAttempts 5 -MaxRuntimeMinutes 0 -WebSearch denied -RunDirectory $run -CycleCliPath $cycleCliPath -CycleCliSha256 ('d' * 64) -CyclePolicyFile 'C:\approved\run\cycle-policy.json' -CyclePolicySha256 ('e' * 64) -InitialTicketsFile 'C:\approved\run\cycle-tickets-000.json' -InitialTicketsSha256 ('f' * 64) -ContractBindingSha256 ('a' * 64) -CycleState $dirtyState -ResumeMode recovery_or_audit_only
        Assert-True ($cycleContinuation -match 'resume_cycle_mode: recovery_or_audit_only' -and $cycleContinuation -match 'only_allowed_initial_substantive_cycle_action: AttemptEnd for the same active attempt' -and $cycleContinuation -match 'Do not perform the requested continuation') 'Dirty Prompt v4 Resume is not restricted to its unique recovery/audit action.'

        $environment = Get-SanitizedEnvironment
        foreach ($removedName in @('OPENAI_API_KEY', 'CODEX_API_KEY', 'OPENAI_BASE_URL', 'CHATGPT_BASE_URL', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY')) {
            Assert-True (-not $environment.ContainsKey($removedName)) "Sensitive or endpoint environment variable was inherited: $removedName"
        }
        Assert-True ($environment['LOCALAPPDATA'] -eq (Get-TrustedLocalAppData)) 'LOCALAPPDATA was not replaced with the Windows known folder.'
    }

    Invoke-Test 'Run-directory boundary rejects outside inputs and extra files' {
        $vault = Join-Path $fullTestRoot 'vault'
        $runs = Join-Path $vault '笔记草稿\数学研究运行'
        $run = Join-Path $runs 'run-001'
        New-Item -ItemType Directory -Force -Path $run | Out-Null
        $env:OBSIDIAN_VAULT_ROOT = $vault
        $prompt = Join-Path $run 'prompt-v3.md'
        $objective = Join-Path $run 'goal-objective.md'
        [IO.File]::WriteAllText($prompt, 'prompt', [Text.UTF8Encoding]::new($false))
        [IO.File]::WriteAllText($objective, 'objective', [Text.UTF8Encoding]::new($false))
        $resolved = Resolve-ResearchRunDirectory -RunDirectory $run
        Assert-True ($resolved -eq $run) 'RunDirectory did not resolve inside the approved root.'
        Resolve-RunInputFile -LiteralPath $prompt -RunDirectory $run -Label 'PromptFile' | Out-Null
        Assert-FreshRunDirectory -RunDirectory $run -AllowedInputFiles @($prompt, $objective)
        $outside = Join-Path $vault 'outside.md'
        [IO.File]::WriteAllText($outside, 'outside', [Text.UTF8Encoding]::new($false))
        Assert-Throws { Resolve-RunInputFile -LiteralPath $outside -RunDirectory $run -Label 'PromptFile' } 'An outside prompt was accepted.'
        $extra = Join-Path $run 'extra.txt'
        [IO.File]::WriteAllText($extra, 'extra', [Text.UTF8Encoding]::new($false))
        Assert-Throws { Assert-FreshRunDirectory -RunDirectory $run -AllowedInputFiles @($prompt, $objective) } 'An extra file was accepted in a fresh run directory.'
        Remove-Item -LiteralPath $extra -Force
        $staleLease = Join-Path $run '.launcher.lease'
        [IO.File]::WriteAllText($staleLease, '', [Text.UTF8Encoding]::new($false))
        Assert-Throws { Assert-FreshRunDirectory -RunDirectory $run -AllowedInputFiles @($prompt, $objective) } 'A stale launcher lease was accepted as a fresh run directory.'
    }

    Invoke-Test 'Project run layout is required for New while legacy remains Resume-only' {
        $vault = Join-Path $fullTestRoot 'project-layout-vault'
        $legacy = Join-Path $vault '笔记草稿\数学研究运行\legacy-001'
        $project = Join-Path $vault '笔记草稿\公开问题的尝试\sample-open-problem'
        $run = Join-Path $project 'runs\run-001'
        New-Item -ItemType Directory -Path $legacy -Force | Out-Null
        Initialize-MathResearchProjectArchive -VaultRoot $vault -ProjectDirectoryName 'sample-open-problem' -ProjectId 'sample-open-problem-0001' -ProblemStatement 'Decide the synthetic statement.' | Out-Null
        New-Item -ItemType Directory -Path $run -Force | Out-Null
        $env:OBSIDIAN_VAULT_ROOT = $vault
        $context = Resolve-ResearchRunContext -RunDirectory $run -Operation New
        Assert-True ($context.Layout -eq 'project' -and $context.ProjectId -eq 'sample-open-problem-0001') 'Project run context was not resolved.'
        Assert-Throws { Resolve-ResearchRunContext -RunDirectory $legacy -Operation New } 'Legacy root accepted a New run.'
        Assert-True ((Resolve-ResearchRunContext -RunDirectory $legacy -Operation Resume).Layout -eq 'legacy') 'Legacy Resume compatibility was lost.'
        $historyRun = Join-Path $project 'history\legacy-runs\copied-run'
        New-Item -ItemType Directory -Path $historyRun -Force | Out-Null
        Assert-Throws { Resolve-ResearchRunContext -RunDirectory $historyRun -Operation Resume } 'Copied historical run was accepted as active.'
    }

    Invoke-Test 'Signed manifest detects tampering and recovers a valid backup' {
        $testKeyPath = Join-Path $fullTestRoot 'localappdata\manifest-key.dpapi'
        & $launcherModule { param($path) $script:ManifestKeyPathOverrideForTests = $path } $testKeyPath
        $manifestPath = Join-Path $fullTestRoot 'signed.json'
        try {
            $payload1 = [ordered]@{ schema_version = 1; revision = 1; value = 'alpha' }
            Write-SignedJsonPayload -LiteralPath $manifestPath -Payload $payload1 -CreateKeyIfMissing
            $read1 = Read-SignedJsonPayload -LiteralPath $manifestPath
            Assert-True ($read1.Payload.value -eq 'alpha' -and -not $read1.RecoveredFromBackup) 'Initial signed payload failed validation.'
            $payload2 = [ordered]@{ schema_version = 1; revision = 2; value = 'beta' }
            Write-SignedJsonPayload -LiteralPath $manifestPath -Payload $payload2
            $raw = [IO.File]::ReadAllText($manifestPath, [Text.UTF8Encoding]::new($false))
            [IO.File]::WriteAllText($manifestPath, $raw.Replace('beta', 'tampered'), [Text.UTF8Encoding]::new($false))
            $recovered = Read-SignedJsonPayload -LiteralPath $manifestPath
            Assert-True ($recovered.RecoveredFromBackup -and $recovered.Payload.value -eq 'alpha') 'A valid manifest backup was not recovered.'
            [IO.File]::WriteAllText((Join-Path $fullTestRoot 'unsigned.json'), '{"payload":{"x":1}}', [Text.UTF8Encoding]::new($false))
            Assert-Throws { Read-SignedJsonPayload -LiteralPath (Join-Path $fullTestRoot 'unsigned.json') } 'Unsigned JSON was accepted.'
        }
        finally { & $launcherModule { $script:ManifestKeyPathOverrideForTests = $null } }
    }

    Invoke-Test 'Named leases reject concurrent use' {
        $lease1 = Enter-NamedLease -Kind thread -Value '12345678-1234-4234-8234-1234567890ab'
        try {
            Assert-Throws { Enter-NamedLease -Kind thread -Value '12345678-1234-4234-8234-1234567890ab' } 'A second thread lease was acquired concurrently.'
        }
        finally { Exit-NamedLease -Lease $lease1 }
    }

    Invoke-Test 'Thread lease excludes a second launcher process' {
        $helperPath = Join-Path $fullTestRoot 'hold-thread-lease.ps1'
        $signalPath = Join-Path $fullTestRoot 'thread-lease-ready.txt'
        $thread = '22345678-1234-4234-8234-1234567890ab'
        $helperText = @'
param([string]$ModulePath, [string]$SignalPath, [string]$ThreadId)
$ErrorActionPreference = 'Stop'
Import-Module $ModulePath -Force -DisableNameChecking
$lease = Enter-NamedLease -Kind thread -Value $ThreadId
try {
    [IO.File]::WriteAllText($SignalPath, 'ready', [Text.UTF8Encoding]::new($false))
    Start-Sleep -Seconds 15
}
finally { Exit-NamedLease -Lease $lease }
'@
        [IO.File]::WriteAllText($helperPath, $helperText, [Text.UTF8Encoding]::new($false))
        $psi = [Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = Join-Path $PSHOME 'pwsh.exe'
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        foreach ($argument in @('-NoLogo', '-NoProfile', '-File', $helperPath, '-ModulePath', $modulePath, '-SignalPath', $signalPath, '-ThreadId', $thread)) {
            $psi.ArgumentList.Add($argument)
        }
        $holder = [Diagnostics.Process]::Start($psi)
        try {
            for ($attempt = 0; $attempt -lt 100 -and -not (Test-Path -LiteralPath $signalPath); $attempt++) {
                Start-Sleep -Milliseconds 100
            }
            Assert-True (Test-Path -LiteralPath $signalPath) 'The helper process did not acquire the thread lease in time.'
            Assert-Throws { Enter-NamedLease -Kind thread -Value $thread } 'A second process acquired the same thread lease.'
        }
        finally {
            if (-not $holder.HasExited) { $holder.Kill($true) }
            $holder.WaitForExit(5000) | Out-Null
            $holder.Dispose()
        }
    }

    Invoke-Test 'JSONL parser records UUID, terminal event, and token usage' {
        $thread = '12345678-1234-4234-8234-1234567890ab'
        $message = '{"marker":"MATH_RESEARCH_GOAL_READY","nonce":"n","objective_sha256":"h","observed_status":"active"}'
        $lines = @(
            (@{ type = 'thread.started'; thread_id = $thread } | ConvertTo-Json -Compress),
            (@{ type = 'turn.started' } | ConvertTo-Json -Compress),
            (@{ type = 'item.completed'; item = @{ type = 'agent_message'; text = $message } } | ConvertTo-Json -Compress -Depth 5),
            (@{ type = 'turn.completed'; usage = @{ input_tokens = 10; cached_input_tokens = 4; output_tokens = 3 } } | ConvertTo-Json -Compress -Depth 5)
        ) -join "`n"
        $path = Join-Path $fullTestRoot 'events.jsonl'
        [IO.File]::WriteAllText($path, $lines + "`n", [Text.UTF8Encoding]::new($false))
        $parsed = Read-CodexJsonLog -LiteralPath $path -ExpectedThreadId $thread
        Assert-True ($parsed.ThreadId -eq $thread -and $parsed.TerminalType -eq 'turn.completed') 'JSONL state was parsed incorrectly.'
        Assert-True ($parsed.Usage.input_tokens -eq 10 -and $parsed.Usage.output_tokens -eq 3) 'Token usage was parsed incorrectly.'
        Test-GoalReadyMarker -Message $message -ObjectiveSha256 'h' -Nonce 'n' | Out-Null
        $failedMarker = $message.Replace('MATH_RESEARCH_GOAL_READY', 'MATH_RESEARCH_GOAL_FAILED')
        Assert-Throws { Test-GoalReadyMarker -Message $failedMarker -ObjectiveSha256 'h' -Nonce 'n' } 'A failed Goal marker was accepted.'
        Assert-Throws { Test-GoalReadyMarker -Message $message -ObjectiveSha256 'h' -Nonce 'wrong' } 'A Goal marker with the wrong nonce was accepted.'
        $duplicate = $lines + "`n" + (@{ type = 'thread.started'; thread_id = $thread } | ConvertTo-Json -Compress)
        [IO.File]::WriteAllText($path, $duplicate, [Text.UTF8Encoding]::new($false))
        Assert-Throws { Read-CodexJsonLog -LiteralPath $path } 'Duplicate thread.started was accepted.'
        $duplicateTerminal = $lines + "`n" + (@{ type = 'turn.completed'; usage = @{ input_tokens = 1; output_tokens = 1 } } | ConvertTo-Json -Compress -Depth 5)
        [IO.File]::WriteAllText($path, $duplicateTerminal, [Text.UTF8Encoding]::new($false))
        Assert-Throws { Read-CodexJsonLog -LiteralPath $path } 'Duplicate terminal turn events were accepted.'
    }

    Invoke-Test 'Highest signed Codex is selected without mtime fallback' {
        $env:LOCALAPPDATA = $originalLocalAppData
        $attestation = Select-TrustedCodexExecutable -WorkingDirectory $fullTestRoot
        Assert-True ($attestation.signature_status -eq 'Valid') 'Selected Codex signature is invalid.'
        Assert-True ($attestation.signer_name -eq 'OpenAI OpCo, LLC') 'Selected Codex signer is unexpected.'
        Assert-True ($attestation.version -match '^\d+\.\d+\.\d+') 'Selected Codex semantic version is missing.'
        Assert-Throws { Get-OpenAIExecutableAttestation -LiteralPath (Join-Path $PSHOME 'pwsh.exe') } 'An executable outside the official Codex directory was accepted.'
        $trustedRoot = Get-CodexBinRoot
        $env:LOCALAPPDATA = Join-Path $fullTestRoot 'forged-localappdata'
        try {
            Assert-True ((Get-CodexBinRoot) -eq $trustedRoot) 'An environment-variable override changed the official Codex bin root.'
        }
        finally { $env:LOCALAPPDATA = $originalLocalAppData }
    }

    Invoke-Test 'Installed CLI accepts the V1 child-cap preflight' {
        $env:LOCALAPPDATA = $originalLocalAppData
        $attestation = Select-TrustedCodexExecutable -WorkingDirectory $fullTestRoot
        $arguments = New-CodexFeaturesArguments -RunDirectory $fullTestRoot -MaxChildAgents 16
        $preflight = Invoke-ShortAttestedProcess -Attestation $attestation -Arguments $arguments -WorkingDirectory $fullTestRoot -TimeoutSeconds 15 -MaximumOutputBytes 2097152
        Assert-True ($preflight.Result.ExitCode -eq 0) "Feature preflight failed: $($preflight.Stderr)"
        Test-CodexFeaturePreflightOutput -Text $preflight.Stdout
        Assert-True ($arguments -contains 'agents.max_threads=16') 'Feature preflight did not use the direct child cap.'
    }

    Invoke-Test 'Installed CLI parses the exact Resume option layout offline' {
        $env:LOCALAPPDATA = $originalLocalAppData
        $attestation = Select-TrustedCodexExecutable -WorkingDirectory $fullTestRoot
        $thread = '12345678-1234-4234-8234-1234567890ab'
        $resumeArguments = [Collections.Generic.List[string]]::new()
        $generated = New-CodexExecArguments -RunDirectory $fullTestRoot -Model 'gpt-5.4' -ReasoningEffort 'xhigh' -Sandbox 'workspace-write' -AllowWebSearch:$false -EnableMultiAgent:$true -MaxChildAgents 16 -LastMessagePath (Join-Path $fullTestRoot 'offline-last.md') -ResumeThreadId $thread
        foreach ($argument in $generated) { $resumeArguments.Add($argument) }
        $separator = $resumeArguments.IndexOf('--')
        $resumeArguments.Insert($separator, '--help')
        $parse = Invoke-ShortAttestedProcess -Attestation $attestation -Arguments ([string[]]$resumeArguments) -WorkingDirectory $fullTestRoot -TimeoutSeconds 15 -MaximumOutputBytes 2097152
        Assert-True ($parse.Result.ExitCode -eq 0) "Installed CLI rejected the Resume option layout: $($parse.Stderr)"
        Assert-True ($parse.Stdout -match 'Usage: codex exec resume') 'Offline Resume parse did not reach the expected help command.'

        $goalArguments = [Collections.Generic.List[string]]::new()
        $generatedGoal = New-CodexExecArguments -RunDirectory $fullTestRoot -Model 'gpt-5.4' -ReasoningEffort 'xhigh' -Sandbox 'read-only' -AllowWebSearch:$false -EnableMultiAgent:$false -LastMessagePath (Join-Path $fullTestRoot 'offline-goal-last.json') -OutputSchemaPath (Join-Path $fullTestRoot 'offline-goal-schema.json')
        foreach ($argument in $generatedGoal) { $goalArguments.Add($argument) }
        $stdinIndex = $goalArguments.Count - 1
        $goalArguments.Insert($stdinIndex, '--help')
        $goalParse = Invoke-ShortAttestedProcess -Attestation $attestation -Arguments ([string[]]$goalArguments) -WorkingDirectory $fullTestRoot -TimeoutSeconds 15 -MaximumOutputBytes 2097152
        Assert-True ($goalParse.Result.ExitCode -eq 0) "Installed CLI rejected the Goal option layout: $($goalParse.Stderr)"
        Assert-True ($goalParse.Stdout -match 'Usage: codex exec') 'Offline Goal parse did not reach the expected help command.'
    }

    Invoke-Test 'Async stdin cannot bypass the Job Object timeout' {
        $stdout = Join-Path $fullTestRoot 'job.stdout'
        $stderr = Join-Path $fullTestRoot 'job.stderr'
        $environment = Get-SanitizedEnvironment
        $startTimer = [Diagnostics.Stopwatch]::StartNew()
        $child = [MathResearchLauncher.ManagedProcess]::Start(
            (Join-Path $PSHOME 'pwsh.exe'),
            [string[]]@('-NoLogo', '-NoProfile', '-Command', 'Start-Sleep -Seconds 30'),
            $fullTestRoot,
            ('x' * 4194304),
            $stdout,
            $stderr,
            $environment,
            $null)
        $startTimer.Stop()
        try {
            Assert-True ($startTimer.Elapsed.TotalSeconds -lt 5) 'ManagedProcess.Start blocked while the child ignored stdin.'
            $result = $child.Wait(700, 1048576, 1048576)
            Assert-True $result.TimedOut 'Managed process was not terminated at the timeout.'
        }
        finally { $child.Dispose() }
        Assert-True ($null -eq (Get-Process -Id $result.ProcessId -ErrorAction SilentlyContinue)) 'Timed-out child process is still alive.'
    }

    Invoke-Test 'Manual stop terminates the exact named Job Object' {
        $stdout = Join-Path $fullTestRoot 'named-job.stdout'
        $stderr = Join-Path $fullTestRoot 'named-job.stderr'
        $jobName = 'Local\OpenAI.Codex.MathResearch.Job.' + [Guid]::NewGuid().ToString('N')
        $child = [MathResearchLauncher.ManagedProcess]::Start(
            (Join-Path $PSHOME 'pwsh.exe'),
            [string[]]@('-NoLogo', '-NoProfile', '-Command', 'Start-Sleep -Seconds 30'),
            $fullTestRoot,
            '',
            $stdout,
            $stderr,
            (Get-SanitizedEnvironment),
            $jobName)
        try {
            Assert-True ($child.JobName -ceq $jobName) 'Managed process did not expose the exact Job Object name.'
            [MathResearchLauncher.ManagedProcess]::TerminateNamedJob($jobName, 130)
            $result = $child.Wait(5000, 1048576, 1048576)
        }
        finally { $child.Dispose() }
        Assert-True ($null -eq (Get-Process -Id $result.ProcessId -ErrorAction SilentlyContinue)) 'Named Job Object termination left the child alive.'
    }

    Invoke-Test 'Killing the launcher process closes the Job and kills its child' {
        $helperPath = Join-Path $fullTestRoot 'job-parent.ps1'
        $pidPath = Join-Path $fullTestRoot 'job-child.pid'
        $helperText = @'
param([string]$ModulePath, [string]$TestRoot, [string]$PidPath)
$ErrorActionPreference = 'Stop'
Import-Module $ModulePath -Force -DisableNameChecking
$child = [MathResearchLauncher.ManagedProcess]::Start(
    (Join-Path $PSHOME 'pwsh.exe'),
    [string[]]@('-NoLogo', '-NoProfile', '-Command', 'Start-Sleep -Seconds 60'),
    $TestRoot,
    '',
    (Join-Path $TestRoot 'parent-death.stdout'),
    (Join-Path $TestRoot 'parent-death.stderr'),
    (Get-SanitizedEnvironment),
    ('Local\OpenAI.Codex.MathResearch.Job.' + [Guid]::NewGuid().ToString('N')))
[IO.File]::WriteAllText($PidPath, [string]$child.ProcessId, [Text.UTF8Encoding]::new($false))
Start-Sleep -Seconds 60
'@
        [IO.File]::WriteAllText($helperPath, $helperText, [Text.UTF8Encoding]::new($false))
        $psi = [Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = Join-Path $PSHOME 'pwsh.exe'
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        foreach ($argument in @('-NoLogo', '-NoProfile', '-File', $helperPath, '-ModulePath', $modulePath, '-TestRoot', $fullTestRoot, '-PidPath', $pidPath)) {
            $psi.ArgumentList.Add($argument)
        }
        $parent = [Diagnostics.Process]::Start($psi)
        $childPid = $null
        try {
            for ($attempt = 0; $attempt -lt 100 -and -not (Test-Path -LiteralPath $pidPath); $attempt++) {
                Start-Sleep -Milliseconds 100
            }
            Assert-True (Test-Path -LiteralPath $pidPath) 'The launcher helper did not publish its child PID in time.'
            $childPid = [int][IO.File]::ReadAllText($pidPath)
            Assert-True ($null -ne (Get-Process -Id $childPid -ErrorAction SilentlyContinue)) 'The managed child was not running before the launcher was killed.'
            $parent.Kill()
            $parent.WaitForExit(5000) | Out-Null
            for ($attempt = 0; $attempt -lt 100 -and $null -ne (Get-Process -Id $childPid -ErrorAction SilentlyContinue); $attempt++) {
                Start-Sleep -Milliseconds 100
            }
            Assert-True ($null -eq (Get-Process -Id $childPid -ErrorAction SilentlyContinue)) 'The child survived after the launcher process closed its Job handle.'
        }
        finally {
            if (-not $parent.HasExited) { $parent.Kill($true) }
            $parent.Dispose()
            if ($childPid -and $null -ne (Get-Process -Id $childPid -ErrorAction SilentlyContinue)) {
                Stop-Process -Id $childPid -Force
            }
        }
    }

    Invoke-Test 'Directory junction chains are rejected' {
        $junctionTarget = Join-Path $fullTestRoot 'junction-target'
        $junctionPath = Join-Path $fullTestRoot 'junction-path'
        New-Item -ItemType Directory -Force -Path $junctionTarget | Out-Null
        New-Item -ItemType Junction -Path $junctionPath -Target $junctionTarget -ErrorAction Stop | Out-Null
        Assert-Throws { Assert-NoReparsePointChain -LiteralPath $junctionPath } 'A directory-junction path was accepted.'
    }

    try {
        $linkTarget = Join-Path $fullTestRoot 'link-target'
        $linkPath = Join-Path $fullTestRoot 'link-path'
        New-Item -ItemType Directory -Force -Path $linkTarget | Out-Null
        New-Item -ItemType SymbolicLink -Path $linkPath -Target $linkTarget -ErrorAction Stop | Out-Null
        Invoke-Test 'Reparse point chains are rejected' {
            Assert-Throws { Assert-NoReparsePointChain -LiteralPath $linkPath } 'A symbolic-link path was accepted.'
        }
    }
    catch {
        Add-SkippedTest -Name 'Reparse point chains are rejected' -Detail 'The current Windows account could not create a test symbolic link.'
    }

    $allPassed = $true
}
finally {
    $env:LOCALAPPDATA = $originalLocalAppData
    $env:OBSIDIAN_VAULT_ROOT = $originalVaultRoot
    if ($allPassed -and -not $KeepTestFiles) {
        $resolved = [IO.Path]::GetFullPath($fullTestRoot)
        if ($resolved -eq [IO.Path]::GetPathRoot($resolved) -or $resolved.Length -lt 20) {
            throw "Unsafe TestRoot cleanup path: $resolved"
        }
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}

[pscustomobject]@{
    Passed = $script:Passed
    Skipped = $script:Skipped
    Failed = @($script:Results | Where-Object Status -eq 'failed').Count
    TestRoot = $fullTestRoot
    KeptTestFiles = [bool]$KeepTestFiles
    Results = @($script:Results)
} | ConvertTo-Json -Depth 6
