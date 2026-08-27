[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Initialize','Verify','StructuralOnly','Status','ResumePlan','AnalyzeLegacy','ApplyLegacyMigration','VerifySemanticArchive','ValidateFailure','ValidateLegacyFailure','ValidateSources','CheckRoute','RegisterContract','PublishCheckpoint','Handoff','RepairEventTail')]
    [string]$Action,

    [string]$ProjectDirectory,
    [string]$VaultRoot,
    [string]$ProjectDirectoryName,
    [string]$ProjectId,
    [string]$ProblemStatement,
    [string]$SeedDirectory,
    [string]$SourceWorkspace,
    [string[]]$LegacyRunDirectories = @(),
    [string[]]$AdditionalSourceFiles = @(),
    [string[]]$ContractPackageFiles = @(),
    [string]$FailureRecordFile,
    [string]$ManifestFile,
    [string]$CurrentConclusion,
    [string[]]$ClaimSha256 = @(),
    [string]$ExpectedAttemptId,
    [string]$ArtifactRoot,
    [string]$TicketFile,
    [string]$ContractFile,
    [string]$ContractBindingSha256,
    [string]$ContractVersion,
    [string]$RunDirectory,
    [string]$HandoffLabel = 'handoff'
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)

Import-Module (Join-Path $PSScriptRoot 'MathResearchProjectArchive.psm1') -Force -DisableNameChecking

switch ($Action) {
    'Initialize' {
        foreach ($name in @('VaultRoot','ProjectDirectoryName','ProjectId','ProblemStatement')) {
            if (-not $PSBoundParameters.ContainsKey($name) -or [string]::IsNullOrWhiteSpace([string](Get-Variable -Name $name -ValueOnly))) { throw "Initialize requires -$name." }
        }
        $args = @{ VaultRoot=$VaultRoot; ProjectDirectoryName=$ProjectDirectoryName; ProjectId=$ProjectId; ProblemStatement=$ProblemStatement }
        foreach ($name in @('SeedDirectory','SourceWorkspace')) { if ($PSBoundParameters.ContainsKey($name)) { $args[$name] = Get-Variable -Name $name -ValueOnly } }
        if ($LegacyRunDirectories.Count -gt 0) { $args.LegacyRunDirectories = $LegacyRunDirectories }
        if ($AdditionalSourceFiles.Count -gt 0) { $args.AdditionalSourceFiles = $AdditionalSourceFiles }
        if ($ContractPackageFiles.Count -gt 0) { $args.ContractPackageFiles = $ContractPackageFiles }
        $result = Initialize-MathResearchProjectArchive @args
    }
    'Verify' { if ([string]::IsNullOrWhiteSpace($ProjectDirectory)) { throw 'Verify requires -ProjectDirectory.' }; $result = Verify-MathResearchProjectArchive -ProjectDirectory $ProjectDirectory }
    'StructuralOnly' { if ([string]::IsNullOrWhiteSpace($ProjectDirectory)) { throw 'StructuralOnly requires -ProjectDirectory.' }; $result = Verify-MathResearchProjectArchive -ProjectDirectory $ProjectDirectory -StructuralOnly }
    'Status' { if ([string]::IsNullOrWhiteSpace($ProjectDirectory)) { throw 'Status requires -ProjectDirectory.' }; $result = Get-MathResearchProjectStatus -ProjectDirectory $ProjectDirectory }
    'ResumePlan' { if ([string]::IsNullOrWhiteSpace($ProjectDirectory)) { throw 'ResumePlan requires -ProjectDirectory.' }; $result = Get-MathResearchProjectResumePlan -ProjectDirectory $ProjectDirectory }
    'AnalyzeLegacy' { if ([string]::IsNullOrWhiteSpace($ProjectDirectory)) { throw 'AnalyzeLegacy requires -ProjectDirectory.' }; $result = Analyze-MathResearchLegacyArchive -ProjectDirectory $ProjectDirectory }
    'ApplyLegacyMigration' {
        if ([string]::IsNullOrWhiteSpace($ProjectDirectory) -or [string]::IsNullOrWhiteSpace($ManifestFile)) { throw 'ApplyLegacyMigration requires -ProjectDirectory and -ManifestFile.' }
        $args=@{ProjectDirectory=$ProjectDirectory;ManifestFile=$ManifestFile};if($PSBoundParameters.ContainsKey('CurrentConclusion')){$args.CurrentConclusion=$CurrentConclusion}
        $result=Apply-MathResearchLegacyMigration @args
    }
    'VerifySemanticArchive' { if ([string]::IsNullOrWhiteSpace($ProjectDirectory)) { throw 'VerifySemanticArchive requires -ProjectDirectory.' }; $result = Verify-MathResearchLegacySemanticArchive -ProjectDirectory $ProjectDirectory }
    'ValidateFailure' {
        if ([string]::IsNullOrWhiteSpace($FailureRecordFile)) { throw 'ValidateFailure requires -FailureRecordFile.' }
        $args = @{ FailureRecordFile=$FailureRecordFile }
        foreach ($name in @('ExpectedAttemptId','ArtifactRoot')) { if ($PSBoundParameters.ContainsKey($name)) { $args[$name] = Get-Variable -Name $name -ValueOnly } }
        $result = Test-MathResearchFailureRecord @args
    }
    'ValidateLegacyFailure' {
        if ([string]::IsNullOrWhiteSpace($FailureRecordFile)) { throw 'ValidateLegacyFailure requires -FailureRecordFile.' }
        $result=Test-MathResearchLegacyFailureRecord -FailureRecordFile $FailureRecordFile
    }
    'ValidateSources' {
        if ([string]::IsNullOrWhiteSpace($ProjectDirectory) -or $ClaimSha256.Count -lt 1) { throw 'ValidateSources requires -ProjectDirectory and at least one -ClaimSha256.' }
        $result = Test-MathResearchSourceClaims -ProjectDirectory $ProjectDirectory -ClaimSha256 $ClaimSha256
    }
    'CheckRoute' {
        if ([string]::IsNullOrWhiteSpace($ProjectDirectory) -or [string]::IsNullOrWhiteSpace($TicketFile)) { throw 'CheckRoute requires -ProjectDirectory and -TicketFile.' }
        $result = Test-MathResearchRouteStart -ProjectDirectory $ProjectDirectory -TicketFile $TicketFile
    }
    'RegisterContract' {
        foreach ($name in @('ProjectDirectory','ContractFile','ContractBindingSha256','ContractVersion','RunDirectory')) { if (-not $PSBoundParameters.ContainsKey($name) -or [string]::IsNullOrWhiteSpace([string](Get-Variable -Name $name -ValueOnly))) { throw "RegisterContract requires -$name." } }
        $result = Register-MathResearchProjectContract -ProjectDirectory $ProjectDirectory -ContractFile $ContractFile -ContractBindingSha256 $ContractBindingSha256 -ContractVersion $ContractVersion -RunDirectory $RunDirectory
    }
    'PublishCheckpoint' {
        if ([string]::IsNullOrWhiteSpace($ProjectDirectory) -or [string]::IsNullOrWhiteSpace($RunDirectory)) { throw 'PublishCheckpoint requires -ProjectDirectory and -RunDirectory.' }
        $result = Publish-MathResearchProjectCheckpoint -ProjectDirectory $ProjectDirectory -RunDirectory $RunDirectory
    }
    'Handoff' {
        if ([string]::IsNullOrWhiteSpace($ProjectDirectory)) { throw 'Handoff requires -ProjectDirectory.' }
        $result = New-MathResearchProjectHandoff -ProjectDirectory $ProjectDirectory -Label $HandoffLabel
    }
    'RepairEventTail' {
        if ([string]::IsNullOrWhiteSpace($ProjectDirectory)) { throw 'RepairEventTail requires -ProjectDirectory.' }
        $result = Repair-MathResearchProjectEventTail -ProjectDirectory $ProjectDirectory
    }
}

$result | ConvertTo-Json -Depth 64
