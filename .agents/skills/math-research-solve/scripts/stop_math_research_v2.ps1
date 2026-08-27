[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$RunDirectory
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)

Import-Module (Join-Path $PSScriptRoot 'MathResearchLauncherV2.psm1') -Force -DisableNameChecking
Assert-PowerShell7

$runPath = Resolve-ResearchRunDirectory -RunDirectory $RunDirectory
$manifestPath = Join-Path $runPath 'run.json'
$read = Read-SignedJsonPayload -LiteralPath $manifestPath
$manifest = $read.Payload

if ($manifest.schema_version -ne 1) { throw 'Unsupported run manifest schema.' }
if ($null -eq $manifest.process -or $null -eq $manifest.process.pid) {
    throw 'The manifest does not identify an active Codex process.'
}
if (-not (Test-ProcessIdentityFromManifest -ProcessRecord $manifest.process)) {
    throw 'The recorded PID, executable path, and process start time do not identify the same live process. Refusing to terminate it.'
}

$pidToStop = [int]$manifest.process.pid
$process = Get-Process -Id $pidToStop -ErrorAction Stop
$path = $process.Path
$attestation = Get-OpenAIExecutableAttestation -LiteralPath $path
if (-not (Test-FixedTimeHexEqual -Left ([string]$attestation.sha256) -Right ([string]$manifest.process.executable_sha256))) {
    throw 'The live process executable hash differs from the signed manifest.'
}
$jobName = [string]$manifest.process.job_object_name
if ($jobName -cnotmatch '^Local\\OpenAI\.Codex\.MathResearch\.Job\.[0-9a-f]{32}$') {
    throw 'The signed manifest does not contain a valid per-segment Job Object name.'
}

$requestPath = Join-Path $runPath 'stop-request.json'
$request = [ordered]@{
    schema_version = 1
    run_id = $manifest.run_id
    thread_id = $manifest.thread_id
    target_pid = $pidToStop
    target_process_start_time_utc = $manifest.process.start_time_utc
    target_job_object_name = $jobName
    requested_at_utc = Get-UtcNowString
    requested_by_sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
}
Write-SignedJsonPayload -LiteralPath $requestPath -Payload $request

[MathResearchLauncher.ManagedProcess]::TerminateNamedJob($jobName, 130)
if (-not $process.WaitForExit(15000)) {
    throw 'The named Job Object was terminated, but the recorded Codex process did not exit within 15 seconds.'
}

[pscustomobject]@{
    RunDirectory = $runPath
    ThreadId = $manifest.thread_id
    StoppedPid = $pidToStop
    JobObjectName = $jobName
    StopRequest = $requestPath
} | ConvertTo-Json -Depth 4
