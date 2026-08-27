[CmdletBinding()]
param(
    [string]$TestRoot = (Join-Path $env:TEMP ("math-research-v2-bundle-tests-" + [Guid]::NewGuid().ToString('N'))),
    [switch]$KeepTestFiles
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)

$candidateRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
if (Test-Path -LiteralPath (Join-Path $candidateRoot 'scripts\MathResearchLauncherV2.psm1') -PathType Leaf) {
    $candidateScripts = Join-Path $candidateRoot 'scripts'
    $sourceTestRoot = $PSScriptRoot
}
elseif (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'MathResearchLauncherV2.psm1') -PathType Leaf) {
    # Installed layout promotes deterministic tests into the Skill's scripts directory.
    $candidateScripts = $PSScriptRoot
    $sourceTestRoot = $PSScriptRoot
}
else { throw 'Cannot resolve the v2 bundle from candidate tests/ or installed scripts/ layout.' }
$installedScripts = $candidateScripts
$pwsh = Join-Path $PSHOME 'pwsh.exe'
$fullTestRoot = [IO.Path]::GetFullPath($TestRoot)
$utf8 = [Text.UTF8Encoding]::new($false)

function Assert-True([bool]$Condition,[string]$Message) { if (-not $Condition) { throw $Message } }

function Copy-FixtureFile([string]$Source,[string]$Destination) {
    $parent = Split-Path -Parent $Destination
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Destination
}

function New-V2Fixture([string]$Name) {
    $root = Join-Path $fullTestRoot $Name
    $scripts = Join-Path $root 'scripts'
    $tests = Join-Path $root 'tests'
    New-Item -ItemType Directory -Force -Path $scripts,$tests,(Join-Path $root 'references') | Out-Null
    foreach ($leaf in @(
        'MathResearchLauncherV2.psm1','MathResearchProjectArchiveV2.psm1','MathResearchCycleLedgerV2.psm1',
        'invoke_math_research_project_v2.ps1','invoke_math_research_cycle_v2.ps1','invoke_math_research_startup_v2.ps1')) {
        Copy-FixtureFile -Source (Join-Path $candidateScripts $leaf) -Destination (Join-Path $scripts $leaf)
    }
    foreach ($leaf in @('observer_run.ps1','MathResearchLegacyArchive.ps1')) {
        Copy-FixtureFile -Source (Join-Path $installedScripts $leaf) -Destination (Join-Path $scripts $leaf)
    }
    Copy-FixtureFile -Source (Join-Path $candidateRoot 'SKILL.md') -Destination (Join-Path $root 'SKILL.md')
    Copy-FixtureFile -Source (Join-Path $candidateRoot 'references\observer-phases.json') -Destination (Join-Path $root 'references\observer-phases.json')
    return [pscustomobject]@{ Root=$root; Scripts=$scripts; Tests=$tests }
}

function Convert-TestToV2([string]$Source,[string]$Destination,[string]$FixtureScripts,[switch]$Startup) {
    $text = [IO.File]::ReadAllText($Source,[Text.UTF8Encoding]::new($false,$true))
    $text = $text.Replace('MathResearchProjectArchive.psm1','MathResearchProjectArchiveV2.psm1')
    $text = $text.Replace('MathResearchCycleLedger.psm1','MathResearchCycleLedgerV2.psm1')
    $text = $text.Replace('MathResearchLauncher.psm1','MathResearchLauncherV2.psm1')
    $text = $text.Replace('Get-Module MathResearchProjectArchive','Get-Module MathResearchProjectArchiveV2')
    $text = $text.Replace('Get-Module MathResearchCycleLedger','Get-Module MathResearchCycleLedgerV2')
    $text = $text.Replace('Get-Module MathResearchLauncher','Get-Module MathResearchLauncherV2')
    $text = $text.Replace('Remove-Module MathResearchProjectArchive','Remove-Module MathResearchProjectArchiveV2')
    $text = $text.Replace('Remove-Module MathResearchCycleLedger','Remove-Module MathResearchCycleLedgerV2')
    $text = $text.Replace('Remove-Module MathResearchLauncher','Remove-Module MathResearchLauncherV2')
    $text = $text.Replace('invoke_math_research_project.ps1','invoke_math_research_project_v2.ps1')
    $text = $text.Replace('invoke_math_research_cycle.ps1','invoke_math_research_cycle_v2.ps1')
    $text = $text.Replace('math-research-solve.script.invoke_math_research_project','math-research-solve.script.invoke_math_research_project_v2')
    $text = $text.Replace('math-research-solve.script.invoke_math_research_cycle','math-research-solve.script.invoke_math_research_cycle_v2')
    if ($Startup) {
        $text = $text.Replace('invoke_math_research_startup_v1.ps1','invoke_math_research_startup_v2.ps1')
        $text = $text.Replace('math-research-solve.script.invoke_math_research_startup_v1','math-research-solve.script.invoke_math_research_startup_v2')
        $installedLiteral = $FixtureScripts.Replace("'","''")
        $text = [regex]::Replace($text,'(?m)^\$installedScripts\s*=\s*''[^'']+''\s*$',("`$installedScripts = '" + $installedLiteral + "'"),1)
    }
    [IO.File]::WriteAllText($Destination,$text,$utf8)
}

function Invoke-IsolatedTest([string]$Name,[string]$Path,[int]$TimeoutMilliseconds=180000) {
    $stdout = "$Path.stdout.log"; $stderr = "$Path.stderr.log"
    $psi = [Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $pwsh; $psi.UseShellExecute=$false; $psi.CreateNoWindow=$true
    $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true
    foreach ($arg in @('-NoLogo','-NoProfile','-File',$Path)) { $psi.ArgumentList.Add($arg) }
    $process = [Diagnostics.Process]::Start($psi)
    try {
        $outTask=$process.StandardOutput.ReadToEndAsync(); $errTask=$process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($TimeoutMilliseconds)) { $process.Kill($true); throw "$Name timed out after $TimeoutMilliseconds ms." }
        $out=$outTask.GetAwaiter().GetResult(); $err=$errTask.GetAwaiter().GetResult()
        [IO.File]::WriteAllText($stdout,$out,$utf8); [IO.File]::WriteAllText($stderr,$err,$utf8)
        if ($process.ExitCode -ne 0) { throw "$Name failed with exit $($process.ExitCode).`nSTDOUT:`n$out`nSTDERR:`n$err" }
        return [pscustomobject]@{Name=$Name;ExitCode=$process.ExitCode;Stdout=$out;Stderr=$err}
    }
    finally { $process.Dispose() }
}

if (Test-Path -LiteralPath $fullTestRoot) { throw "TestRoot already exists: $fullTestRoot" }
New-Item -ItemType Directory -Force -Path $fullTestRoot | Out-Null
$sourceTests = [ordered]@{
    startup=(Join-Path $sourceTestRoot 'test_math_research_startup_v1.ps1')
    project=(Join-Path $installedScripts 'test_math_research_project_archive.ps1')
    cycle=(Join-Path $installedScripts 'test_math_research_cycle_ledger.ps1')
}
$before = [ordered]@{}
foreach ($key in $sourceTests.Keys) { $before[$key]=(Get-FileHash -LiteralPath $sourceTests[$key] -Algorithm SHA256).Hash.ToLowerInvariant() }
$allPassed=$false

try {
    $startupFixture=New-V2Fixture 'startup'
    $startupTest=Join-Path $startupFixture.Tests 'test_math_research_startup_v2.fixture.ps1'
    Convert-TestToV2 -Source $sourceTests.startup -Destination $startupTest -FixtureScripts $startupFixture.Scripts -Startup
    $startup=Invoke-IsolatedTest -Name 'startup v2 real-controller differential' -Path $startupTest
    Assert-True ($startup.Stdout -match '"ok"\s*:\s*true' -and $startup.Stdout -match '"assertions"\s*:\s*68') 'Startup v2 did not pass all 68 real-controller assertions.'

    $projectFixture=New-V2Fixture 'project'
    $projectTest=Join-Path $projectFixture.Scripts 'test_math_research_project_archive_v2.fixture.ps1'
    Convert-TestToV2 -Source $sourceTests.project -Destination $projectTest -FixtureScripts $projectFixture.Scripts
    $project=Invoke-IsolatedTest -Name 'project module v2 differential' -Path $projectTest
    Assert-True ($project.Stdout -match 'RESULT passed=14 failed=0 skipped=0') 'V2 project module did not pass the unchanged 14-case behavior suite.'

    $cycleFixture=New-V2Fixture 'cycle'
    $cycleTest=Join-Path $cycleFixture.Scripts 'test_math_research_cycle_ledger_v2.fixture.ps1'
    Convert-TestToV2 -Source $sourceTests.cycle -Destination $cycleTest -FixtureScripts $cycleFixture.Scripts
    $cycle=Invoke-IsolatedTest -Name 'cycle module v2 differential' -Path $cycleTest
    Assert-True ($cycle.Stdout -match 'RESULT passed=17 failed=0') 'V2 cycle module did not pass the unchanged 17-case behavior suite.'

    $provenancePath=Join-Path $cycleFixture.Scripts 'test_v2_command_provenance.fixture.ps1'
    $provenanceSource=@'
$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSScriptRoot 'MathResearchLauncherV2.psm1') -Force -DisableNameChecking
$project=Import-Module (Join-Path $PSScriptRoot 'MathResearchProjectArchiveV2.psm1') -Force -DisableNameChecking -PassThru
$cycle=Import-Module (Join-Path $PSScriptRoot 'MathResearchCycleLedgerV2.psm1') -Force -DisableNameChecking -PassThru
$expected=[ordered]@{
    'Test-MathResearchRouteStartObject'=[string]$project.Name
    'Initialize-MathResearchCycleLedger'=[string]$cycle.Name
    'Verify-MathResearchCycleLedger'=[string]$cycle.Name
    'Invoke-MathResearchCycleReturnCheck'=[string]$cycle.Name
    'Save-MathResearchCycleCheckpoint'=[string]$cycle.Name
    'Read-SignedJsonPayload'='MathResearchLauncherV2'
}
foreach($name in $expected.Keys){$command=Get-Command $name -CommandType Function -ErrorAction Stop;if([string]$command.Source -cne [string]$expected[$name]){throw "Command provenance mismatch: $name source=$($command.Source) expected=$($expected[$name])"}}
'PROVENANCE PASS'
'@
    [IO.File]::WriteAllText($provenancePath,$provenanceSource,$utf8)
    $provenance=Invoke-IsolatedTest -Name 'v2 command provenance' -Path $provenancePath
    Assert-True ($provenance.Stdout -match 'PROVENANCE PASS') 'V2 command source provenance was not verified.'

    foreach ($key in $sourceTests.Keys) {
        $after=(Get-FileHash -LiteralPath $sourceTests[$key] -Algorithm SHA256).Hash.ToLowerInvariant()
        Assert-True ($after -ceq [string]$before[$key]) "Source regression test bytes changed while testing: $key"
    }
    $allPassed=$true
    [pscustomobject]@{
        SchemaVersion=1;Protocol='math-research-v2-bundle-differential/v1';AllPassed=$true
        StartupAssertions=68;ProjectCases=14;CycleCases=17;CommandProvenance=$true
        SourceTestSha256=$before
    } | ConvertTo-Json -Depth 6
}
finally {
    if (-not $KeepTestFiles -and (Test-Path -LiteralPath $fullTestRoot)) { Remove-Item -LiteralPath $fullTestRoot -Recurse -Force }
}
if (-not $allPassed) { exit 1 }
