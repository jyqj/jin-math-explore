Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

function Enable-MathResearchApproveForMeArgvCompatV2 {
    param(
        [Parameter(Mandatory = $true)][Management.Automation.PSModuleInfo]$TargetModule,
        [Parameter(Mandatory = $true)][ValidateSet('launcher-v2','legacy-v1-compat')][string]$Flavor
    )

    & $TargetModule {
        param([string]$SelectedFlavor)
        if ($SelectedFlavor -eq 'launcher-v2') {
            function script:New-CodexGlobalArguments {
                param(
                    [Parameter(Mandatory = $true)][string]$RunDirectory,
                    [Parameter(Mandatory = $true)][string]$Model,
                    [Parameter(Mandatory = $true)][string]$ReasoningEffort,
                    [Parameter(Mandatory = $true)][ValidateSet('read-only', 'workspace-write')][string]$Sandbox,
                    [Parameter(Mandatory = $true)][ValidateSet('approve_for_me','never')][string]$ApprovalMode,
                    [Parameter(Mandatory = $true)][bool]$AllowWebSearch,
                    [Parameter(Mandatory = $true)][bool]$EnableMultiAgent,
                    [int]$MaxChildAgents = 1
                )
                $arguments = [Collections.Generic.List[string]]::new()
                $arguments.Add('--strict-config')
                $arguments.Add('-C'); $arguments.Add($RunDirectory)
                $arguments.Add('-m'); $arguments.Add($Model)
                if ($ApprovalMode -eq 'approve_for_me') {
                    if ($Sandbox -ne 'workspace-write') { throw 'approve_for_me is valid only with its intrinsic workspace-write sandbox.' }
                    $arguments.Add('--approve-for-me')
                }
                else {
                    $arguments.Add('-s'); $arguments.Add($Sandbox)
                    $arguments.Add('-a'); $arguments.Add('never')
                }
                $arguments.Add('-c'); $arguments.Add("model_reasoning_effort=$(ConvertTo-TomlBasicString $ReasoningEffort)")
                $arguments.Add('-c'); $arguments.Add('sandbox_workspace_write.network_access=false')
                $arguments.Add('--enable'); $arguments.Add('goals')
                $arguments.Add('--disable'); $arguments.Add('plugins')
                $arguments.Add('--disable'); $arguments.Add('apps')
                $arguments.Add('--disable'); $arguments.Add('enable_mcp_apps')
                $arguments.Add('--disable'); $arguments.Add('multi_agent_v2')
                if ($EnableMultiAgent) {
                    $arguments.Add('--enable'); $arguments.Add('multi_agent')
                    $arguments.Add('-c'); $arguments.Add("agents.max_threads=$MaxChildAgents")
                }
                else { $arguments.Add('--disable'); $arguments.Add('multi_agent') }
                if ($AllowWebSearch) { $arguments.Add('--search') }
                return ,$arguments
            }

            function script:New-CodexFeaturesArguments {
                param(
                    [Parameter(Mandatory = $true)][string]$RunDirectory,
                    [Parameter(Mandatory = $true)][ValidateRange(1, 16)][int]$MaxChildAgents,
                    [Parameter(Mandatory = $true)][ValidateSet('approve_for_me','never')][string]$ApprovalMode
                )
                $arguments = [Collections.Generic.List[string]]::new()
                foreach ($value in @('--strict-config','-C',$RunDirectory)) { $arguments.Add($value) }
                if ($ApprovalMode -eq 'approve_for_me') { $arguments.Add('--approve-for-me') }
                else { foreach ($value in @('-s','workspace-write','-a','never')) { $arguments.Add($value) } }
                foreach ($value in @(
                    '--enable','goals','--enable','multi_agent','--disable','multi_agent_v2',
                    '--disable','plugins','--disable','apps','--disable','enable_mcp_apps',
                    '-c',"agents.max_threads=$MaxChildAgents",'features','list')) { $arguments.Add($value) }
                return [string[]]$arguments
            }
        }
        else {
            function script:New-CodexGlobalArguments {
                param(
                    [Parameter(Mandatory = $true)][string]$RunDirectory,
                    [Parameter(Mandatory = $true)][string]$Model,
                    [Parameter(Mandatory = $true)][string]$ReasoningEffort,
                    [Parameter(Mandatory = $true)][ValidateSet('read-only', 'workspace-write')][string]$Sandbox,
                    [Parameter(Mandatory = $true)][bool]$AllowWebSearch,
                    [Parameter(Mandatory = $true)][bool]$EnableMultiAgent,
                    [int]$MaxChildAgents = 1
                )
                if ($Sandbox -ne 'workspace-write') { throw 'Legacy compatibility approve_for_me requires its intrinsic workspace-write sandbox.' }
                $arguments = [Collections.Generic.List[string]]::new()
                $arguments.Add('--strict-config')
                $arguments.Add('-C'); $arguments.Add($RunDirectory)
                $arguments.Add('-m'); $arguments.Add($Model)
                $arguments.Add('--approve-for-me')
                $arguments.Add('-c'); $arguments.Add("model_reasoning_effort=$(ConvertTo-TomlBasicString $ReasoningEffort)")
                $arguments.Add('-c'); $arguments.Add('sandbox_workspace_write.network_access=false')
                $arguments.Add('--enable'); $arguments.Add('goals')
                $arguments.Add('--disable'); $arguments.Add('plugins')
                $arguments.Add('--disable'); $arguments.Add('apps')
                $arguments.Add('--disable'); $arguments.Add('enable_mcp_apps')
                $arguments.Add('--disable'); $arguments.Add('multi_agent_v2')
                if ($EnableMultiAgent) {
                    $arguments.Add('--enable'); $arguments.Add('multi_agent')
                    $arguments.Add('-c'); $arguments.Add("agents.max_threads=$MaxChildAgents")
                }
                else { $arguments.Add('--disable'); $arguments.Add('multi_agent') }
                if ($AllowWebSearch) { $arguments.Add('--search') }
                return ,$arguments
            }
        }
    } $Flavor
}

function Assert-MathResearchApproveForMeArgvCompatV2 {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    if (@($Arguments | Where-Object { $_ -ceq '--approve-for-me' }).Count -ne 1) { throw 'approve_for_me argv must contain exactly one literal --approve-for-me.' }
    if (@($Arguments | Where-Object { $_ -in @('-s','--sandbox') }).Count -ne 0) { throw 'approve_for_me argv must omit the mutually exclusive explicit sandbox option.' }
    if (@($Arguments | Where-Object { $_ -ceq 'sandbox_workspace_write.network_access=false' }).Count -ne 1) { throw 'approve_for_me argv must keep shell network disabled in the intrinsic workspace-write sandbox.' }
    return $true
}

Export-ModuleMember -Function @('Enable-MathResearchApproveForMeArgvCompatV2','Assert-MathResearchApproveForMeArgvCompatV2')
