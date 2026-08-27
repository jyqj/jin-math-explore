[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Status', 'Verify', 'AttemptStart', 'AttemptEnd', 'AuditStart', 'AuditEnd', 'ReturnCheck')]
    [string]$Action,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$RunDirectory,

    [string]$TicketId,

    [ValidateSet('candidate_found', 'proved_subclaim', 'route_refuted', 'bounded_negative', 'portfolio_proposed', 'method_failed', 'substantive_inconclusive', 'aborted')]
    [string]$Outcome,

    [string]$ArtifactFile,

    [string]$AttemptRecordFile,

    [string]$FailureRecordFile,

    [ValidateSet('present', 'absent', 'unknown')]
    [string]$StructureSignal = 'unknown',

    [ValidateRange(0, 2147483647)]
    [int]$RepairBatches = 0,

    [string]$AuditTicketFile,

    [string]$AuditResultFile,

    [string]$NextTicketsFile,

    [switch]$Completion
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)

Import-Module (Join-Path $PSScriptRoot 'MathResearchCycleLedgerV2.psm1') -Force -DisableNameChecking

if ($Action -in @('Status', 'Verify')) {
    $result = Verify-MathResearchCycleLedger -RunDirectory $RunDirectory
}
else {
    $arguments = @{
        Action = $Action
        RunDirectory = $RunDirectory
        StructureSignal = $StructureSignal
        RepairBatches = $RepairBatches
        Completion = $Completion
    }
    foreach ($pair in @(
        @('TicketId', $TicketId),
        @('Outcome', $Outcome),
        @('ArtifactFile', $ArtifactFile),
        @('AttemptRecordFile', $AttemptRecordFile),
        @('FailureRecordFile', $FailureRecordFile),
        @('AuditTicketFile', $AuditTicketFile),
        @('AuditResultFile', $AuditResultFile),
        @('NextTicketsFile', $NextTicketsFile))) {
        if (-not [string]::IsNullOrWhiteSpace([string]$pair[1])) { $arguments[[string]$pair[0]] = [string]$pair[1] }
    }
    $result = Invoke-MathResearchCycleAction @arguments
}

$result | ConvertTo-Json -Depth 64
