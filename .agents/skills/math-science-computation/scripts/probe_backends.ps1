[CmdletBinding()]
param(
    [string]$PythonCommand = 'python',
    [string]$SageCommand = '',
    [string]$WslDistro = '',
    [string]$WslSageCommand = 'sage',
    [string]$PrimecountCommand = ''
)

$ErrorActionPreference = 'Stop'

function Resolve-CommandPath {
    param([Parameter(Mandatory = $true)][string]$Name)

    if (Test-Path -LiteralPath $Name -PathType Leaf) {
        return (Get-Item -LiteralPath $Name).FullName
    }

    $command = Get-Command -Name $Name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $command) {
        return $null
    }
    return $command.Source
}

function Invoke-VersionProbe {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    try {
        $output = & $Executable @Arguments 2>&1
        $exitCode = $LASTEXITCODE
        return [ordered]@{
            status = if ($exitCode -eq 0) { 'available' } else { 'probe_failed' }
            version_output = (($output | ForEach-Object { $_.ToString() }) -join "`n").Trim()
            exit_code = $exitCode
            error = ''
        }
    }
    catch {
        return [ordered]@{
            status = 'probe_failed'
            version_output = ''
            exit_code = $null
            error = $_.Exception.Message
        }
    }
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

$wolframInstallations = @()
$programRoots = @()
if ($env:ProgramFiles) {
    $programRoots += (Join-Path $env:ProgramFiles 'Wolfram Research\Wolfram')
}
if (${env:ProgramFiles(x86)}) {
    $programRoots += (Join-Path ${env:ProgramFiles(x86)} 'Wolfram Research\Wolfram')
}

foreach ($programRoot in ($programRoots | Select-Object -Unique)) {
    if (-not (Test-Path -LiteralPath $programRoot -PathType Container)) {
        continue
    }
    foreach ($versionDirectory in (Get-ChildItem -LiteralPath $programRoot -Directory -ErrorAction SilentlyContinue)) {
        $wolframExecutable = Join-Path $versionDirectory.FullName 'wolfram.exe'
        if (Test-Path -LiteralPath $wolframExecutable -PathType Leaf) {
            $item = Get-Item -LiteralPath $wolframExecutable
            $wolframInstallations += [ordered]@{
                version_directory = $versionDirectory.Name
                executable = $item.FullName
                file_version = $item.VersionInfo.FileVersion
            }
        }
    }
}

$wolframScriptPath = Resolve-CommandPath -Name 'wolframscript'
if (-not $wolframScriptPath -and $env:ProgramFiles) {
    $knownWolframScript = Join-Path $env:ProgramFiles 'Wolfram Research\WolframScript\wolframscript.exe'
    if (Test-Path -LiteralPath $knownWolframScript -PathType Leaf) {
        $wolframScriptPath = (Get-Item -LiteralPath $knownWolframScript).FullName
    }
}

$wolframScript = if ($wolframScriptPath) {
    $probe = Invoke-VersionProbe -Executable $wolframScriptPath -Arguments @('-version')
    [ordered]@{
        status = $probe.status
        path = $wolframScriptPath
        version_output = $probe.version_output
        exit_code = $probe.exit_code
        error = $probe.error
    }
}
else {
    [ordered]@{
        status = 'unavailable'
        path = $null
        version_output = ''
        exit_code = $null
        error = ''
    }
}

$primecountRequestedCommand = ''
$primecountDiscoverySource = ''
$primecountPath = $null
if ($PrimecountCommand) {
    $primecountRequestedCommand = $PrimecountCommand
    $primecountDiscoverySource = 'explicit'
    $primecountPath = Resolve-CommandPath -Name $PrimecountCommand
}
elseif ($env:PRIMECOUNT_EXE) {
    $primecountRequestedCommand = $env:PRIMECOUNT_EXE
    $primecountDiscoverySource = 'environment'
    $primecountPath = Resolve-CommandPath -Name $env:PRIMECOUNT_EXE
}
else {
    $primecountRequestedCommand = 'primecount'
    $primecountDiscoverySource = 'path'
    $primecountPath = Resolve-CommandPath -Name 'primecount'
    if (-not $primecountPath -and $env:LOCALAPPDATA) {
        $knownPrimecount = Join-Path $env:LOCALAPPDATA 'Programs\primecount\primecount.exe'
        if (Test-Path -LiteralPath $knownPrimecount -PathType Leaf) {
            $primecountPath = (Get-Item -LiteralPath $knownPrimecount).FullName
            $primecountDiscoverySource = 'known_user_location'
        }
    }
}

$primecount = if ($primecountPath) {
    $probe = Invoke-VersionProbe -Executable $primecountPath -Arguments @('--version')
    [ordered]@{
        status = $probe.status
        requested_command = $primecountRequestedCommand
        discovery_source = $primecountDiscoverySource
        path = $primecountPath
        version_output = $probe.version_output
        exit_code = $probe.exit_code
        error = $probe.error
    }
}
else {
    [ordered]@{
        status = 'unavailable'
        requested_command = $primecountRequestedCommand
        discovery_source = $primecountDiscoverySource
        path = $null
        version_output = ''
        exit_code = $null
        error = ''
    }
}

$nativeSageName = if ($SageCommand) { $SageCommand } else { 'sage' }
$nativeSagePath = Resolve-CommandPath -Name $nativeSageName
$nativeSage = if ($nativeSagePath) {
    $probe = Invoke-VersionProbe -Executable $nativeSagePath -Arguments @('--version')
    [ordered]@{
        status = $probe.status
        requested_command = $nativeSageName
        path = $nativeSagePath
        version_output = $probe.version_output
        exit_code = $probe.exit_code
        error = $probe.error
    }
}
else {
    [ordered]@{
        status = 'unavailable'
        requested_command = $nativeSageName
        path = $null
        version_output = ''
        exit_code = $null
        error = ''
    }
}

$wslSage = [ordered]@{
    status = 'not_requested'
    distro = $WslDistro
    requested_command = $WslSageCommand
    version_output = ''
    exit_code = $null
    error = ''
}
if ($WslDistro) {
    $wslPath = Resolve-CommandPath -Name 'wsl.exe'
    if (-not $wslPath) {
        $wslSage.status = 'wsl_unavailable'
    }
    else {
        try {
            $output = & $wslPath -d $WslDistro -- $WslSageCommand --version 2>&1
            $exitCode = $LASTEXITCODE
            $wslSage.status = if ($exitCode -eq 0) { 'available' } else { 'probe_failed' }
            $wslSage.version_output = (($output | ForEach-Object { $_.ToString() }) -join "`n").Trim()
            $wslSage.exit_code = $exitCode
        }
        catch {
            $wslSage.status = 'probe_failed'
            $wslSage.error = $_.Exception.Message
        }
    }
}

$pythonPath = Resolve-CommandPath -Name $PythonCommand
$pythonProbe = if ($pythonPath) {
    $probeCode = @'
import importlib.metadata
import importlib.util
import json
import sys

modules = {
    "numpy": "numpy",
    "sympy": "sympy",
    "scipy": "scipy",
    "mpmath": "mpmath",
    "sage": "sagemath-standard",
    "sageall": "sagemath-standard",
}
libraries = {}
for module_name, distribution_name in modules.items():
    available = importlib.util.find_spec(module_name) is not None
    version = None
    if available:
        try:
            version = importlib.metadata.version(distribution_name)
        except importlib.metadata.PackageNotFoundError:
            version = None
    libraries[module_name] = {"available": available, "version": version}
print(json.dumps({
    "python_version": sys.version.split()[0],
    "executable": sys.executable,
    "libraries": libraries,
}, ensure_ascii=False))
'@
    try {
        $output = & $pythonPath -c $probeCode 2>&1
        $exitCode = $LASTEXITCODE
        if ($exitCode -ne 0) {
            [ordered]@{
                status = 'probe_failed'
                requested_command = $PythonCommand
                path = $pythonPath
                version = ''
                libraries = [ordered]@{}
                exit_code = $exitCode
                error = (($output | ForEach-Object { $_.ToString() }) -join "`n").Trim()
            }
        }
        else {
            $data = ($output -join "`n") | ConvertFrom-Json -AsHashtable
            [ordered]@{
                status = 'available'
                requested_command = $PythonCommand
                path = $data.executable
                version = $data.python_version
                libraries = $data.libraries
                exit_code = 0
                error = ''
            }
        }
    }
    catch {
        [ordered]@{
            status = 'probe_failed'
            requested_command = $PythonCommand
            path = $pythonPath
            version = ''
            libraries = [ordered]@{}
            exit_code = $null
            error = $_.Exception.Message
        }
    }
}
else {
    [ordered]@{
        status = 'unavailable'
        requested_command = $PythonCommand
        path = $null
        version = ''
        libraries = [ordered]@{}
        exit_code = $null
        error = ''
    }
}

$result = [ordered]@{
    schema_version = '1.0'
    probed_at_utc = [DateTime]::UtcNow.ToString('o')
    host = Get-HostIdentity
    mathematica = [ordered]@{
        installations = $wolframInstallations
        wolframscript = $wolframScript
        mcp = [ordered]@{
            status = 'requires_agent_probe'
            evidence = 'Call the configured Mathematica MCP from the agent and record the returned Wolfram Language version.'
        }
    }
    primecount = $primecount
    sagemath = [ordered]@{
        native = $nativeSage
        wsl = $wslSage
    }
    python = $pythonProbe
}

$result | ConvertTo-Json -Depth 10 -Compress
