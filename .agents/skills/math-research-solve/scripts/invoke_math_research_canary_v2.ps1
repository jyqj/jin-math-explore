[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][ValidateNotNullOrEmpty()][string]$RunDirectory,
    [Parameter(Mandatory = $true)][ValidateNotNullOrEmpty()][string]$ChallengeFile,
    [Parameter(Mandatory = $true)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedChallengeSha256
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)

if (-not (Get-Command ConvertFrom-Json -ErrorAction Stop).Parameters.ContainsKey('DateKind')) {
    throw 'Canary v2 requires ConvertFrom-Json -DateKind String.'
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant()
}

function Get-TextSha256([string]$Text) {
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.UTF8Encoding]::new($false).GetBytes($Text))).ToLowerInvariant()
}

function Get-TreeDigest([string]$Root) {
    if (-not (Test-Path -LiteralPath $Root -PathType Container)) { throw "Canary ledger root is missing: $Root" }
    $records = [Collections.Generic.List[string]]::new()
    foreach ($file in @(Get-ChildItem -LiteralPath $Root -Recurse -File -Force | Sort-Object FullName)) {
        if (($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Canary ledger contains a reparse point: $($file.FullName)" }
        $relative = [IO.Path]::GetRelativePath($Root, $file.FullName).Replace('\','/')
        $records.Add("$relative`0$($file.Length)`0$(Get-Sha256 $file.FullName)")
    }
    return Get-TextSha256 ($records -join "`n")
}

$runPath = [IO.Path]::GetFullPath($RunDirectory).TrimEnd('\')
$challengePath = [IO.Path]::GetFullPath($ChallengeFile)
if (-not (Split-Path -Parent $challengePath).Equals($runPath, [StringComparison]::OrdinalIgnoreCase) -or
    (Split-Path -Leaf $challengePath) -cne 'launcher-canary-challenge-v2.json') {
    throw 'Canary challenge must be the fixed direct child of RunDirectory.'
}
foreach ($path in @($runPath,$challengePath)) {
    $cursor = $path
    while (-not [string]::IsNullOrWhiteSpace($cursor)) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Canary path contains a reparse point: $cursor" }
        }
        $parent = Split-Path -Parent $cursor
        if ([string]::IsNullOrWhiteSpace($parent) -or $parent.Equals($cursor,[StringComparison]::OrdinalIgnoreCase)) { break }
        $cursor = $parent
    }
}
if ((Get-Sha256 $challengePath) -cne $ExpectedChallengeSha256) { throw 'Canary challenge hash differs from the pinned invocation.' }
$challengeText = [IO.File]::ReadAllText($challengePath, [Text.UTF8Encoding]::new($false, $true))
$challenge = $challengeText | ConvertFrom-Json -AsHashtable -Depth 32 -DateKind String
if ([int]$challenge.schema_version -ne 2 -or [string]$challenge.protocol -cne 'math-research-launcher-canary/v2') { throw 'Canary challenge protocol mismatch.' }
if (-not $runPath.Equals([IO.Path]::GetFullPath([string]$challenge.run_directory).TrimEnd('\'), [StringComparison]::OrdinalIgnoreCase)) { throw 'Canary challenge run directory mismatch.' }
$selfPath = [IO.Path]::GetFullPath($PSCommandPath)
if (-not $selfPath.Equals([IO.Path]::GetFullPath([string]$challenge.canary_entry_path), [StringComparison]::OrdinalIgnoreCase) -or
    (Get-Sha256 $selfPath) -cne [string]$challenge.canary_entry_sha256) { throw 'Canary installed entry attestation mismatch.' }

$manifestPath = [IO.Path]::GetFullPath([string]$challenge.manifest_path)
if (-not (Split-Path -Parent $manifestPath).Equals($runPath, [StringComparison]::OrdinalIgnoreCase) -or (Split-Path -Leaf $manifestPath) -cne 'run.json') { throw 'Canary manifest path mismatch.' }
if ((Get-Sha256 $manifestPath) -cne [string]$challenge.manifest_sha256) { throw 'Canary manifest hash mismatch.' }
$cycleCli = [IO.Path]::GetFullPath([string]$challenge.cycle_cli_path)
if ((Get-Sha256 $cycleCli) -cne [string]$challenge.cycle_cli_sha256) { throw 'Canary cycle CLI hash mismatch.' }

$ledgerRoot = Join-Path $runPath 'cycle-ledger'
$ledgerBefore = Get-TreeDigest $ledgerRoot
$statusLines = @(& $cycleCli -Action Status -RunDirectory $runPath)
if (-not $?) { throw 'Exact cycle Status command failed.' }
$statusText = ($statusLines | ForEach-Object { [string]$_ }) -join "`n"
if ([string]::IsNullOrWhiteSpace($statusText)) { throw 'Exact cycle Status returned no JSON.' }
$status = $statusText | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
$ledgerAfter = Get-TreeDigest $ledgerRoot
if ($ledgerBefore -cne $ledgerAfter) { throw 'Read-only cycle Status changed the signed ledger.' }

$scratchPath = Join-Path $runPath 'launcher-canary-scratch-v2.tmp'
$scratchCreated = $false
$scratchRemoved = $false
try {
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes([string]$challenge.nonce)
    $stream = [IO.FileStream]::new($scratchPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    try { $stream.Write($bytes,0,$bytes.Length); $stream.Flush($true) } finally { $stream.Dispose() }
    $scratchCreated = ((Get-Sha256 $scratchPath) -ceq (Get-TextSha256 ([string]$challenge.nonce)))
    if (-not $scratchCreated) { throw 'Canary scratch artifact read-back failed.' }
}
finally {
    if (Test-Path -LiteralPath $scratchPath) { Remove-Item -LiteralPath $scratchPath -Force }
    $scratchRemoved = -not (Test-Path -LiteralPath $scratchPath)
}
if (-not $scratchRemoved) { throw 'Canary scratch artifact was not removed.' }

$evidence = [ordered]@{
    schema_version = 2
    protocol = 'math-research-launcher-canary/v2'
    challenge_nonce = [string]$challenge.nonce
    run_manifest_sha256 = [string]$challenge.manifest_sha256
    challenge_sha256 = $ExpectedChallengeSha256
    ledger_before_sha256 = $ledgerBefore
    ledger_after_sha256 = $ledgerAfter
    cycle_status_sha256 = Get-TextSha256 $statusText
    cycle_status_exit_code = 0
    attempt_count = [int]$status.AttemptCount
    total_round_count = [int]$status.TotalRoundCount
    scratch_created = $scratchCreated
    scratch_removed = $scratchRemoved
}
$evidenceText = $evidence | ConvertTo-Json -Depth 16
$evidencePath = Join-Path $runPath 'launcher-canary-evidence-v2.json'
$stream = [IO.FileStream]::new($evidencePath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
try {
    $evidenceBytes = [Text.UTF8Encoding]::new($false).GetBytes($evidenceText)
    $stream.Write($evidenceBytes,0,$evidenceBytes.Length)
    $stream.Flush($true)
}
finally { $stream.Dispose() }
$readBack = [IO.File]::ReadAllText($evidencePath, [Text.UTF8Encoding]::new($false, $true)) | ConvertFrom-Json -AsHashtable -Depth 16 -DateKind String
if ([string]$readBack.challenge_nonce -cne [string]$challenge.nonce) { throw 'Canary evidence read-back failed.' }
$evidence | ConvertTo-Json -Compress -Depth 16
