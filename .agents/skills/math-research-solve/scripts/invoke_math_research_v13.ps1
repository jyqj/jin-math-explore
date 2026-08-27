param(
  [Parameter(Mandatory=$true)][ValidateSet('startup','state','commit','migrate','map-review')][string]$Tool,
  [Parameter(ValueFromRemainingArguments=$true)][string[]]$Rest
)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$script = switch ($Tool) {
  'startup' { 'math_research_state_v13.py' }
  'state' { 'math_research_state_v13.py' }
  'commit' { 'math_research_commit_v13.py' }
  'migrate' { 'math_research_migrate_v12_to_v13.py' }
  'map-review' { 'map_semantic_review_v1.py' }
}
& python -B (Join-Path $PSScriptRoot $script) @Rest
exit $LASTEXITCODE
