[CmdletBinding()]
param(
    [ValidateSet('ReadOrCreate', 'Refresh', 'Invalidate', 'RecordMcp')]
    [string]$Mode = 'ReadOrCreate',
    [string]$StateFile = '',
    [ValidateSet('all', 'mathematica', 'primecount', 'sagemath', 'python')]
    [string[]]$Backend = @('all'),
    [string]$ReasonCode = '',
    [int]$MaxAgeHours = 168,
    [string]$ProbeScript = (Join-Path $PSScriptRoot 'probe_backends.ps1'),
    [string]$ProbeJsonFile = '',
    [string]$PythonCommand = 'python',
    [string]$SageCommand = '',
    [string]$WslDistro = '',
    [string]$WslSageCommand = 'sage',
    [string]$PrimecountCommand = '',
    [string]$McpServerName = '',
    [string]$McpProtocolVersion = '',
    [string]$McpServerVersion = '',
    [string]$McpWolframLanguageVersion = '',
    [string]$McpObservedAtUtc = ''
)

$ErrorActionPreference = 'Stop'
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
if ($Mode -eq 'Invalidate' -and $ReasonCode -notmatch '^[a-z][a-z0-9_]{0,31}$') {
    throw "Invalidate mode requires a bounded lowercase reason code."
}

function Get-DefaultStateFile {
    if ($env:MATH_SCIENCE_BACKEND_INVENTORY) {
        return $env:MATH_SCIENCE_BACKEND_INVENTORY
    }
    return (Join-Path (Join-Path (Join-Path ([IO.Path]::GetTempPath()) 'Codex') 'math-science-computation') 'backend-inventory.json')
}

function Get-HostIdentity {
    $system = if ([Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([Runtime.InteropServices.OSPlatform]::Windows)) {
        'Windows'
    }
    elseif ([Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([Runtime.InteropServices.OSPlatform]::OSX)) {
        'Darwin'
    }
    else {
        'Linux'
    }
    $rawArchitecture = [Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLowerInvariant()
    $architecture = switch ($rawArchitecture) {
        'x64' { 'x86_64' }
        'amd64' { 'x86_64' }
        'arm64' { 'arm64' }
        'x86' { 'x86' }
        default { $rawArchitecture }
    }
    return [ordered]@{ system = $system; architecture = $architecture; powershell_edition = $PSVersionTable.PSEdition }
}

function Read-Inventory {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $null
    }
    try {
        $inventory = Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json -AsHashtable
        if ($inventory.inventory_schema_version -ne '1.0' -or $inventory.local.schema_version -ne '1.0') {
            return $null
        }
        return $inventory
    }
    catch {
        return $null
    }
}

function Invoke-LocalProbe {
    if ($ProbeJsonFile) {
        return (Get-Content -Raw -LiteralPath $ProbeJsonFile | ConvertFrom-Json -AsHashtable)
    }
    if (-not (Test-Path -LiteralPath $ProbeScript -PathType Leaf)) {
        throw "Backend probe script is unavailable."
    }

    $probeArguments = @{
        PythonCommand = $PythonCommand
        SageCommand = $SageCommand
        WslDistro = $WslDistro
        WslSageCommand = $WslSageCommand
        PrimecountCommand = $PrimecountCommand
    }
    $raw = & $ProbeScript @probeArguments
    if ($LASTEXITCODE -notin @($null, 0)) {
        throw "Backend probe failed with a nonzero exit code."
    }
    return (($raw -join "`n") | ConvertFrom-Json -AsHashtable)
}

function New-Inventory {
    param([Parameter(Mandatory = $true)][hashtable]$Local)

    $now = [DateTime]::UtcNow.ToString('o')
    return [ordered]@{
        inventory_schema_version = '1.0'
        created_at_utc = $now
        updated_at_utc = $now
        local = $Local
        mcp = [ordered]@{
            authority = 'current_session_tool_discovery_and_call'
            persisted_status = 'historical_only'
            required_action = 'Build a current-session overlay and live-check only the selected MCP backend.'
        }
        invalidations = @()
    }
}

function New-McpObservation {
    $required = [ordered]@{
        server_name = $McpServerName
        protocol_version = $McpProtocolVersion
        server_version = $McpServerVersion
        wolfram_language_version = $McpWolframLanguageVersion
    }
    $missing = @($required.GetEnumerator() | Where-Object { -not $_.Value.Trim() } | ForEach-Object Key)
    if ($missing.Count -gt 0) {
        throw ('RecordMcp requires: ' + ($missing -join ', '))
    }
    if ($McpProtocolVersion -notmatch '^\d{4}-\d{2}-\d{2}$') {
        throw 'MCP protocol version must use the negotiated YYYY-MM-DD form.'
    }
    $observedAt = if ($McpObservedAtUtc) { $McpObservedAtUtc } else { [DateTime]::UtcNow.ToString('o') }
    try { [void][DateTimeOffset]::Parse($observedAt) }
    catch { throw 'MCP observation time must be an ISO-8601 timestamp.' }
    return [ordered]@{
        server_name = $McpServerName
        protocol_version = $McpProtocolVersion
        server_version = $McpServerVersion
        wolfram_language_version = $McpWolframLanguageVersion
        observed_at_utc = $observedAt
        evidence = 'initialize_handshake_and_evaluator'
    }
}

function Write-InventoryAtomic {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Inventory,
        [Parameter(Mandatory = $true)][string]$Path
    )

    $parent = Split-Path -Parent $Path
    if (-not $parent) {
        $parent = (Get-Location).Path
        $Path = Join-Path $parent $Path
    }
    [IO.Directory]::CreateDirectory($parent) | Out-Null
    $temporary = Join-Path $parent ('.backend-inventory-' + [Guid]::NewGuid().ToString('N') + '.tmp')
    try {
        $json = $Inventory | ConvertTo-Json -Depth 12
        [IO.File]::WriteAllText($temporary, $json, [Text.UTF8Encoding]::new($false))
        [IO.File]::Move($temporary, $Path, $true)
    }
    finally {
        if (Test-Path -LiteralPath $temporary -PathType Leaf) {
            Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
        }
    }
}

function Get-MissingBackendPaths {
    param([Parameter(Mandatory = $true)][hashtable]$Inventory)

    $missing = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($installation in @($Inventory.local.mathematica.installations)) {
        if ($installation.executable -and -not (Test-Path -LiteralPath $installation.executable -PathType Leaf)) {
            [void]$missing.Add('mathematica')
        }
    }
    $checks = @(
        @('mathematica', $Inventory.local.mathematica.wolframscript.path),
        @('primecount', $Inventory.local.primecount.path),
        @('sagemath', $Inventory.local.sagemath.native.path),
        @('python', $Inventory.local.python.path)
    )
    foreach ($check in $checks) {
        if ($check[1] -and -not (Test-Path -LiteralPath $check[1] -PathType Leaf)) {
            [void]$missing.Add([string]$check[0])
        }
    }
    return @($missing)
}

function Test-InventoryExpired {
    param([Parameter(Mandatory = $true)][hashtable]$Inventory)

    if ($MaxAgeHours -le 0) {
        return $false
    }
    try {
        $updated = [DateTimeOffset]::Parse([string]$Inventory.updated_at_utc)
        return ([DateTimeOffset]::UtcNow - $updated).TotalHours -ge $MaxAgeHours
    }
    catch {
        return $true
    }
}

function Test-InventoryHostMismatch {
    param([Parameter(Mandatory = $true)][hashtable]$Inventory)

    $current = Get-HostIdentity
    $stored = $Inventory.local.host
    if (-not $stored) {
        return $true
    }
    return ($stored.system -ne $current.system -or $stored.architecture -ne $current.architecture)
}

function Merge-Backends {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Inventory,
        [Parameter(Mandatory = $true)][hashtable]$FreshLocal,
        [Parameter(Mandatory = $true)][string[]]$Names
    )

    $selected = if ($Names -contains 'all') {
        @('mathematica', 'primecount', 'sagemath', 'python')
    }
    else {
        @($Names | Select-Object -Unique)
    }
    foreach ($name in $selected) {
        $Inventory.local[$name] = $FreshLocal[$name]
    }
    $Inventory.local.probed_at_utc = $FreshLocal.probed_at_utc
    $Inventory.local.host = $FreshLocal.host
    $Inventory.updated_at_utc = [DateTime]::UtcNow.ToString('o')
    return $Inventory
}

function Write-Result {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Inventory,
        [Parameter(Mandatory = $true)][string]$CacheStatus,
        [string[]]$RefreshedBackends = @(),
        [string[]]$InvalidPaths = @(),
        [bool]$BackendStarted = $false,
        [string]$WriteError = ''
    )

    $stopwatch.Stop()
    $output = [ordered]@{
        inventory_schema_version = $Inventory.inventory_schema_version
        snapshot_updated_at_utc = $Inventory.updated_at_utc
        cache = [ordered]@{
            status = $CacheStatus
            state_file = $StateFile
            elapsed_ms = $stopwatch.ElapsedMilliseconds
            backend_started = $BackendStarted
            refreshed_backends = @($RefreshedBackends)
            invalid_path_backends = @($InvalidPaths)
            write_error = $WriteError
        }
        local = $Inventory.local
        mcp = [ordered]@{
            status = 'session_probe_required'
            authority = 'current_session_tool_discovery_and_call'
            note = 'The persisted snapshot is not evidence that an MCP tool is callable in this session.'
            recorded_mathematica_observation = $Inventory.mcp.mathematica
        }
    }
    $output | ConvertTo-Json -Depth 12 -Compress
}

if (-not $StateFile) {
    $StateFile = Get-DefaultStateFile
}
$StateFile = [IO.Path]::GetFullPath($StateFile)
$inventory = Read-Inventory -Path $StateFile
$missingBackends = @()

if ($Mode -eq 'RecordMcp') {
    $observation = New-McpObservation
    $backendStarted = $false
    if (-not $inventory) {
        $freshLocal = Invoke-LocalProbe
        if ($freshLocal.schema_version -ne '1.0') { throw 'Unsupported backend probe schema.' }
        if ($freshLocal.mathematica -is [Collections.IDictionary] -and $freshLocal.mathematica.Contains('mcp')) {
            [void]$freshLocal.mathematica.Remove('mcp')
        }
        $inventory = New-Inventory -Local $freshLocal
        $backendStarted = $true
    }
    $inventory.mcp.mathematica = $observation
    $inventory.updated_at_utc = [DateTime]::UtcNow.ToString('o')
    Write-InventoryAtomic -Inventory $inventory -Path $StateFile
    Write-Result -Inventory $inventory -CacheStatus 'mcp_recorded' -BackendStarted $backendStarted
    exit 0
}

if ($Mode -eq 'ReadOrCreate' -and $inventory) {
    $missingBackends = @(Get-MissingBackendPaths -Inventory $inventory)
    if ($missingBackends.Count -eq 0 -and -not (Test-InventoryExpired -Inventory $inventory) -and -not (Test-InventoryHostMismatch -Inventory $inventory)) {
        Write-Result -Inventory $inventory -CacheStatus 'hit' -BackendStarted $false
        exit 0
    }
}

$freshLocal = Invoke-LocalProbe
if ($freshLocal.schema_version -ne '1.0') {
    throw "Unsupported backend probe schema."
}
if ($freshLocal.mathematica -is [Collections.IDictionary] -and $freshLocal.mathematica.Contains('mcp')) {
    [void]$freshLocal.mathematica.Remove('mcp')
}

$refreshed = @('mathematica', 'primecount', 'sagemath', 'python')
$cacheStatus = 'created'
if (-not $inventory) {
    $inventory = New-Inventory -Local $freshLocal
}
else {
    $cacheStatus = 'refreshed'
    if ($Mode -eq 'Invalidate') {
        $targets = if ($Backend -contains 'all') { @('mathematica', 'primecount', 'sagemath', 'python') } else { @($Backend) }
        $inventory.invalidations = @($inventory.invalidations) + @($targets | ForEach-Object {
            [ordered]@{ backend = $_; reason = $ReasonCode; recorded_at_utc = [DateTime]::UtcNow.ToString('o') }
        })
        if ($inventory.invalidations.Count -gt 20) {
            $inventory.invalidations = @($inventory.invalidations | Select-Object -Last 20)
        }
        $refreshed = $targets
    }
    elseif ($Mode -eq 'Refresh') {
        $refreshed = if ($Backend -contains 'all') { @('mathematica', 'primecount', 'sagemath', 'python') } else { @($Backend) }
    }
    elseif ($missingBackends.Count -gt 0) {
        $refreshed = $missingBackends
    }
    $inventory = Merge-Backends -Inventory $inventory -FreshLocal $freshLocal -Names $refreshed
}

$writeError = ''
try {
    Write-InventoryAtomic -Inventory $inventory -Path $StateFile
}
catch {
    $writeError = $_.Exception.GetType().Name
    $cacheStatus = 'write_failed'
}
Write-Result -Inventory $inventory -CacheStatus $cacheStatus -RefreshedBackends $refreshed -InvalidPaths $missingBackends -BackendStarted $true -WriteError $writeError
