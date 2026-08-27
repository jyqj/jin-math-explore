[CmdletBinding()]
param([switch]$IncludeBenchmark)
$ErrorActionPreference='Stop'
$env:PYTHONUTF8='1'
& python -B (Join-Path $PSScriptRoot 'test_math_research_state_v9.py')
if($LASTEXITCODE-ne0){exit $LASTEXITCODE}
if($IncludeBenchmark){
    & python -B (Join-Path $PSScriptRoot 'benchmark_math_research_startup_v9.py')
    if($LASTEXITCODE-ne0){exit $LASTEXITCODE}
}
exit 0
