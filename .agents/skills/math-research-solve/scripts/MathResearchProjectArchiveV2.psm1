Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

$script:ArchiveSchema = 1
$script:ProjectsRelativeRoot = '笔记草稿\公开问题的尝试'
$script:RequiredDirectories = @(
    'contracts', 'state', 'failures', 'cycles', 'attempts',
    'evidence\verified', 'evidence\partial', 'evidence\exploratory',
    'sources', 'handoffs', 'runs', 'manifests',
    'history\imported-workspace', 'history\legacy-runs', 'history\contract-packages'
)
$script:RequiredFiles = @(
    'README.md', 'project.json', 'state\CURRENT.md', 'state\RESULTS.md',
    'state\ROUTES.md', 'state\EVIDENCE.md', 'state\checkpoint.json',
    'state\project-events.jsonl', 'state\route-registry.json'
)
$script:NegativeOutcomes = @('route_refuted','bounded_negative','method_failed','substantive_inconclusive','aborted')
$script:PublicationFailAfterArtifactCommitForTests = $false

function Get-ProjectSha256 {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    return (Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-ProjectTextSha256 {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text)
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes($Text)
    $hash = [Security.Cryptography.SHA256]::HashData($bytes)
    return [Convert]::ToHexString($hash).ToLowerInvariant()
}

function Assert-ProjectLocalAbsolutePath {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    if (-not [IO.Path]::IsPathFullyQualified($LiteralPath)) { throw "Path must be absolute: $LiteralPath" }
    $full = [IO.Path]::GetFullPath($LiteralPath)
    $root = [IO.Path]::GetPathRoot($full)
    if ([string]::IsNullOrWhiteSpace($root) -or $root.StartsWith('\\')) { throw "Only local drive paths are allowed: $LiteralPath" }
    return $full.TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
}

function Assert-ProjectNoReparsePointChain {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    $full = Assert-ProjectLocalAbsolutePath -LiteralPath $LiteralPath
    $pathRoot = [IO.Path]::GetPathRoot($full)
    $current = $pathRoot
    $relative = $full.Substring($pathRoot.Length)
    foreach ($part in ($relative -split '[\\/]' | Where-Object { $_ -ne '' })) {
        $current = Join-Path $current $part
        if (-not (Test-Path -LiteralPath $current)) { break }
        $item = Get-Item -LiteralPath $current -Force -ErrorAction Stop
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Reparse points are not allowed in trusted project paths: $($item.FullName)"
        }
    }
    return $full
}

function Test-ProjectPathInside {
    param([Parameter(Mandatory = $true)][string]$Child, [Parameter(Mandatory = $true)][string]$Directory)
    $childFull = [IO.Path]::GetFullPath($Child)
    $rootFull = [IO.Path]::GetFullPath($Directory).TrimEnd('\') + '\'
    return $childFull.StartsWith($rootFull, [StringComparison]::OrdinalIgnoreCase)
}

function Write-ProjectUtf8New {
    param([Parameter(Mandatory = $true)][string]$LiteralPath, [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text)
    $parent = Split-Path -Parent $LiteralPath
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) { New-Item -ItemType Directory -Path $parent | Out-Null }
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes($Text)
    $stream = [IO.FileStream]::new($LiteralPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
    try { $stream.Write($bytes, 0, $bytes.Length); $stream.Flush($true) } finally { $stream.Dispose() }
}

function Write-ProjectUtf8Atomic {
    param([Parameter(Mandatory = $true)][string]$LiteralPath, [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text)
    $parent = Split-Path -Parent $LiteralPath
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) { New-Item -ItemType Directory -Path $parent | Out-Null }
    $temp = Join-Path $parent ('.tmp-' + [guid]::NewGuid().ToString('N'))
    try {
        Write-ProjectUtf8New -LiteralPath $temp -Text $Text
        Move-Item -LiteralPath $temp -Destination $LiteralPath -Force
    }
    finally { if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Force } }
}

function Assert-UniqueJsonProperties {
    param([Parameter(Mandatory = $true)][Text.Json.JsonElement]$Element, [Parameter(Mandatory = $true)][string]$Path)
    if ($Element.ValueKind -eq [Text.Json.JsonValueKind]::Object) {
        $names = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        foreach ($property in $Element.EnumerateObject()) {
            if (-not $names.Add($property.Name)) { throw "Duplicate JSON property '$($property.Name)' at $Path." }
            Assert-UniqueJsonProperties -Element $property.Value -Path "$Path.$($property.Name)"
        }
    }
    elseif ($Element.ValueKind -eq [Text.Json.JsonValueKind]::Array) {
        $index = 0
        foreach ($item in $Element.EnumerateArray()) { Assert-UniqueJsonProperties -Element $item -Path "$Path[$index]"; $index++ }
    }
}

function Read-ProjectJsonFile {
    param([Parameter(Mandatory = $true)][string]$LiteralPath, [Parameter(Mandatory = $true)][string]$Label)
    if (-not (Test-Path -LiteralPath $LiteralPath -PathType Leaf)) { throw "$Label is missing: $LiteralPath" }
    Assert-ProjectNoReparsePointChain -LiteralPath $LiteralPath | Out-Null
    $bytes = [IO.File]::ReadAllBytes($LiteralPath)
    $encoding = [Text.UTF8Encoding]::new($false, $true)
    try { $text = $encoding.GetString($bytes) } catch { throw "$Label is not strict UTF-8." }
    $options = [Text.Json.JsonDocumentOptions]::new()
    $options.AllowTrailingCommas = $false
    $options.CommentHandling = [Text.Json.JsonCommentHandling]::Disallow
    $options.MaxDepth = 64
    try { $document = [Text.Json.JsonDocument]::Parse($text, $options) } catch { throw "$Label is not strict JSON: $($_.Exception.Message)" }
    try { Assert-UniqueJsonProperties -Element $document.RootElement -Path '$' } finally { $document.Dispose() }
    try { $value = $text | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String } catch { throw "$Label cannot be decoded." }
    if ($value -isnot [Collections.IDictionary]) { throw "$Label must be a JSON object." }
    return [pscustomobject]@{ Value=$value; Text=$text; Sha256=(Get-ProjectSha256 -LiteralPath $LiteralPath); Bytes=$bytes.Length }
}

function Get-MathResearchProjectsRoot {
    param([Parameter(Mandatory = $true)][string]$VaultRoot)
    $vault = Assert-ProjectNoReparsePointChain -LiteralPath $VaultRoot
    if (-not (Test-Path -LiteralPath $vault -PathType Container)) { throw "Vault root is missing: $vault" }
    return [IO.Path]::GetFullPath((Join-Path $vault $script:ProjectsRelativeRoot)).TrimEnd('\')
}

function Resolve-MathResearchProjectDirectory {
    param([Parameter(Mandatory = $true)][string]$ProjectDirectory, [string]$ExpectedProjectId)
    $path = Assert-ProjectNoReparsePointChain -LiteralPath $ProjectDirectory
    if (-not (Test-Path -LiteralPath $path -PathType Container)) { throw "Project directory is missing: $path" }
    $name = Split-Path -Leaf $path
    if ([string]::IsNullOrWhiteSpace($name) -or $name -match '[<>:"/\\|?*]' -or $name.EndsWith('.') -or $name.EndsWith(' ')) { throw "Unsafe project directory name: $name" }
    $project = Read-ProjectJsonFile -LiteralPath (Join-Path $path 'project.json') -Label 'project.json'
    foreach ($key in @('schema','project_id','project_directory_name','status','active_contract','active_run')) {
        if (-not $project.Value.Contains($key)) { throw "project.json is missing '$key'." }
    }
    if ([int]$project.Value.schema -ne $script:ArchiveSchema) { throw 'Unsupported project archive schema.' }
    if ([string]$project.Value.project_directory_name -cne $name) { throw 'project.json directory name does not match the actual directory.' }
    if ([string]$project.Value.project_id -cnotmatch '^[a-z0-9][a-z0-9._-]{7,127}$') { throw 'Unsafe project_id.' }
    if (-not [string]::IsNullOrWhiteSpace($ExpectedProjectId) -and [string]$project.Value.project_id -cne $ExpectedProjectId) { throw 'project_id mismatch.' }
    return [pscustomobject]@{ Path=$path; Name=$name; Project=$project.Value; ProjectJsonSha256=$project.Sha256 }
}

function New-DefaultProjectSeed {
    param([string]$Root, [string]$ProjectId, [string]$ProjectDirectoryName, [string]$ProblemStatement)
    $now = [DateTime]::UtcNow.ToString('o')
    $project = [ordered]@{ schema=1; project_id=$ProjectId; project_directory_name=$ProjectDirectoryName; title=$ProjectDirectoryName; status='paused'; active_contract=$null; active_run=$null; created_at_utc=$now; updated_at_utc=$now }
    $checkpoint = [ordered]@{ schema=1; project_id=$ProjectId; project_status='paused'; goal=[ordered]@{ id=$null; status='none' }; contract=[ordered]@{ path=$null; sha256=$null; status='none' }; run=[ordered]@{ id=$null; path=$null; status='none' }; thread=[ordered]@{ id=$null; status='none' }; last_sealed_attempt=$null; last_completed_audit=$null; attempt_count=0; attempts_since_last_audit=0; audit_due=$false; active_ticket=$null; dirty=$false; recovery_required=$false; migration=[ordered]@{status='not_required';manifest_path=$null;manifest_sha256=$null;recognized_count=0;disposed_count=0;unresolved_substantive_count=0}; last_project_event_sha256=$null; updated_at_utc=$now }
    $registry = [ordered]@{ schema=1; project_id=$ProjectId; routes=@() }
    Write-ProjectUtf8New -LiteralPath (Join-Path $Root 'README.md') -Text ("# $ProjectDirectoryName`n`n## 精确问题`n`n$ProblemStatement`n`n## 最小读取顺序`n`n1. state/CURRENT.md`n2. state/checkpoint.json`n3. 活动合同与当前票据（若有）`n")
    Write-ProjectUtf8New -LiteralPath (Join-Path $Root 'project.json') -Text (($project | ConvertTo-Json -Depth 20) + "`n")
    Write-ProjectUtf8New -LiteralPath (Join-Path $Root 'state\CURRENT.md') -Text "# 当前状态`n`n项目已初始化，未建立活动合同或运行。`n"
    Write-ProjectUtf8New -LiteralPath (Join-Path $Root 'state\RESULTS.md') -Text "# 已验证结果`n`n尚未登记。`n"
    Write-ProjectUtf8New -LiteralPath (Join-Path $Root 'state\ROUTES.md') -Text "# 路线状态`n`n尚未登记。`n"
    Write-ProjectUtf8New -LiteralPath (Join-Path $Root 'state\EVIDENCE.md') -Text "# 证据索引`n`n尚未登记。`n"
    Write-ProjectUtf8New -LiteralPath (Join-Path $Root 'state\checkpoint.json') -Text (($checkpoint | ConvertTo-Json -Depth 20) + "`n")
    Write-ProjectUtf8New -LiteralPath (Join-Path $Root 'state\route-registry.json') -Text (($registry | ConvertTo-Json -Depth 20) + "`n")
    Write-ProjectUtf8New -LiteralPath (Join-Path $Root 'state\project-events.jsonl') -Text ''
}

function Add-ImportRecord {
    param([Collections.Generic.List[object]]$Records, [string]$Source, [string]$Destination, [string]$ArchiveRoot, [string]$Category, [string]$ImportedAt)
    $item = Get-Item -LiteralPath $Destination -Force
    $relativeDestination = [IO.Path]::GetRelativePath($ArchiveRoot, $Destination).Replace('/', '\')
    $Records.Add([ordered]@{ type='file'; source_path=$Source; destination_relative_path=$relativeDestination; bytes=[long]$item.Length; sha256=(Get-ProjectSha256 -LiteralPath $Destination); category=$Category; imported_at_utc=$ImportedAt })
}

function Copy-ProjectFileTracked {
    param([string]$Source, [string]$Destination, [string]$ArchiveRoot, [string]$Category, [Collections.Generic.List[object]]$Records, [string]$ImportedAt)
    $before = Get-ProjectSha256 -LiteralPath $Source
    $parent = Split-Path -Parent $Destination
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Destination
    $destinationHash = Get-ProjectSha256 -LiteralPath $Destination
    $after = Get-ProjectSha256 -LiteralPath $Source
    if ($before -cne $destinationHash -or $before -cne $after) { throw "Source changed during import or copy hash mismatch: $Source" }
    Add-ImportRecord -Records $Records -Source $Source -Destination $Destination -ArchiveRoot $ArchiveRoot -Category $Category -ImportedAt $ImportedAt
}

function Copy-ProjectTreeTracked {
    param(
        [string]$Source, [string]$Destination, [string]$Category,
        [Collections.Generic.List[object]]$Records, [Collections.Generic.List[object]]$Exclusions,
        [string]$ArchiveRoot,
        [string]$ImportedAt, [string[]]$ExcludedRelativePrefixes = @()
    )
    $sourceRoot = Assert-ProjectNoReparsePointChain -LiteralPath $Source
    if (-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) { return }
    foreach ($file in (Get-ChildItem -LiteralPath $sourceRoot -Recurse -File -Force | Sort-Object FullName)) {
        Assert-ProjectNoReparsePointChain -LiteralPath $file.FullName | Out-Null
        $relative = [IO.Path]::GetRelativePath($sourceRoot, $file.FullName).Replace('/', '\')
        $skip = $false
        $reason = $null
        foreach ($prefix in $ExcludedRelativePrefixes) {
            $normalized = $prefix.TrimEnd('\')
            if ($relative.Equals($normalized, [StringComparison]::OrdinalIgnoreCase) -or $relative.StartsWith($normalized + '\', [StringComparison]::OrdinalIgnoreCase)) { $skip=$true; $reason='excluded Skill-development subtree'; break }
        }
        if (-not $skip -and ($relative -match '(^|\\)(__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache)(\\|$)' -or $relative -match '\.(pyc|pyo)$')) { $skip=$true; $reason='regenerable cache' }
        if ($skip) { $Exclusions.Add([ordered]@{ type='excluded'; source_path=$file.FullName; rule='import-exclusion'; reason=$reason; imported_at_utc=$ImportedAt }); continue }
        $target = Join-Path $Destination $relative
        $parent = Split-Path -Parent $target
        if (-not (Test-Path -LiteralPath $parent -PathType Container)) { New-Item -ItemType Directory -Path $parent | Out-Null }
        Copy-ProjectFileTracked -Source $file.FullName -Destination $target -ArchiveRoot $ArchiveRoot -Category $Category -Records $Records -ImportedAt $ImportedAt
    }
}

function Initialize-MathResearchProjectArchive {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$VaultRoot,
        [Parameter(Mandatory = $true)][string]$ProjectDirectoryName,
        [Parameter(Mandatory = $true)][string]$ProjectId,
        [Parameter(Mandatory = $true)][string]$ProblemStatement,
        [string]$SeedDirectory,
        [string]$SourceWorkspace,
        [string[]]$LegacyRunDirectories = @(),
        [string[]]$AdditionalSourceFiles = @(),
        [string[]]$ContractPackageFiles = @()
    )
    if ($ProjectDirectoryName -match '[<>:"/\\|?*]' -or $ProjectDirectoryName.EndsWith('.') -or $ProjectDirectoryName.EndsWith(' ')) { throw 'Unsafe ProjectDirectoryName.' }
    if ($ProjectId -cnotmatch '^[a-z0-9][a-z0-9._-]{7,127}$') { throw 'Unsafe ProjectId.' }
    $projectsRoot = Get-MathResearchProjectsRoot -VaultRoot $VaultRoot
    $projectsParent = Split-Path -Parent $projectsRoot
    Assert-ProjectNoReparsePointChain -LiteralPath $projectsParent | Out-Null
    if (-not (Test-Path -LiteralPath $projectsRoot)) { New-Item -ItemType Directory -Path $projectsRoot | Out-Null }
    Assert-ProjectNoReparsePointChain -LiteralPath $projectsRoot | Out-Null
    $target = Join-Path $projectsRoot $ProjectDirectoryName
    if (Test-Path -LiteralPath $target) { throw "Project already exists: $target" }
    $stage = Join-Path $projectsRoot ('.' + $ProjectDirectoryName + '.stage-' + [guid]::NewGuid().ToString('N'))
    $records = [Collections.Generic.List[object]]::new()
    $exclusions = [Collections.Generic.List[object]]::new()
    $now = [DateTime]::UtcNow.ToString('o')
    try {
        New-Item -ItemType Directory -Path $stage | Out-Null
        foreach ($relative in $script:RequiredDirectories) { New-Item -ItemType Directory -Path (Join-Path $stage $relative) -Force | Out-Null }
        if (-not [string]::IsNullOrWhiteSpace($SeedDirectory)) {
            $seed = Assert-ProjectNoReparsePointChain -LiteralPath $SeedDirectory
            $seedRecords = [Collections.Generic.List[object]]::new()
            $seedExclusions = [Collections.Generic.List[object]]::new()
            Copy-ProjectTreeTracked -Source $seed -Destination $stage -ArchiveRoot $stage -Category 'project-seed' -Records $seedRecords -Exclusions $seedExclusions -ImportedAt $now
        }
        else { New-DefaultProjectSeed -Root $stage -ProjectId $ProjectId -ProjectDirectoryName $ProjectDirectoryName -ProblemStatement $ProblemStatement }
        foreach ($required in $script:RequiredFiles) { if (-not (Test-Path -LiteralPath (Join-Path $stage $required) -PathType Leaf)) { throw "Seed is missing required file: $required" } }
        $seedProject = Read-ProjectJsonFile -LiteralPath (Join-Path $stage 'project.json') -Label 'seed project.json'
        if ([string]$seedProject.Value.project_id -cne $ProjectId -or [string]$seedProject.Value.project_directory_name -cne $ProjectDirectoryName) { throw 'Seed project identity mismatch.' }

        if (-not [string]::IsNullOrWhiteSpace($SourceWorkspace)) {
            $workspace = Assert-ProjectNoReparsePointChain -LiteralPath $SourceWorkspace
            foreach ($rootFile in @('AI-START-HERE.md','research-ledger.md')) {
                $source = Join-Path $workspace $rootFile
                if (Test-Path -LiteralPath $source -PathType Leaf) {
                    $dest = Join-Path $stage ('history\imported-workspace\' + $rootFile)
                    Copy-ProjectFileTracked -Source $source -Destination $dest -ArchiveRoot $stage -Category 'workspace-root' -Records $records -ImportedAt $now
                }
            }
            foreach ($dir in @('work','archive','handoff','outputs')) {
                $source = Join-Path $workspace $dir
                $dest = Join-Path $stage ('history\imported-workspace\' + $dir)
                $exclude = if ($dir -eq 'work') { @('skill-dev') } else { @() }
                Copy-ProjectTreeTracked -Source $source -Destination $dest -ArchiveRoot $stage -Category "workspace-$dir" -Records $records -Exclusions $exclusions -ImportedAt $now -ExcludedRelativePrefixes $exclude
            }
            $excludedToolStage = Join-Path $workspace 'skill-update-candidate'
            if (Test-Path -LiteralPath $excludedToolStage) { $exclusions.Add([ordered]@{ type='excluded'; source_path=$excludedToolStage; rule='import-exclusion'; reason='current Skill-development staging tree, not mathematical research'; imported_at_utc=$now }) }
        }
        foreach ($legacy in $LegacyRunDirectories) {
            $legacyPath = Assert-ProjectNoReparsePointChain -LiteralPath $legacy
            $leaf = Split-Path -Leaf $legacyPath
            $dest = Join-Path $stage ('history\legacy-runs\' + $leaf)
            Copy-ProjectTreeTracked -Source $legacyPath -Destination $dest -ArchiveRoot $stage -Category 'legacy-run' -Records $records -Exclusions $exclusions -ImportedAt $now
        }
        $sourceLeafNames = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
        foreach ($additionalSource in $AdditionalSourceFiles) {
            $sourcePath = Assert-ProjectNoReparsePointChain -LiteralPath $additionalSource
            if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) { throw "Additional source file is missing: $sourcePath" }
            $leaf = Split-Path -Leaf $sourcePath
            if (-not $sourceLeafNames.Add($leaf)) { throw "Additional source filenames collide: $leaf" }
            $dest = Join-Path $stage ("sources\originals\$leaf")
            Copy-ProjectFileTracked -Source $sourcePath -Destination $dest -ArchiveRoot $stage -Category 'external-source-snapshot' -Records $records -ImportedAt $now
        }
        $contractLeafNames = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
        foreach ($contractPackage in $ContractPackageFiles) {
            $sourcePath = Assert-ProjectNoReparsePointChain -LiteralPath $contractPackage
            if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) { throw "Historical contract package is missing: $sourcePath" }
            $leaf = Split-Path -Leaf $sourcePath
            if (-not $contractLeafNames.Add($leaf)) { throw "Historical contract filenames collide: $leaf" }
            $dest = Join-Path $stage ("history\contract-packages\$leaf")
            Copy-ProjectFileTracked -Source $sourcePath -Destination $dest -ArchiveRoot $stage -Category 'historical-contract-package' -Records $records -ImportedAt $now
        }
        $manifestPath = Join-Path $stage 'manifests\import-manifest.jsonl'
        $lines = @(foreach ($entry in @($records) + @($exclusions)) { $entry | ConvertTo-Json -Compress -Depth 20 })
        Write-ProjectUtf8New -LiteralPath $manifestPath -Text (($lines -join "`n") + $(if ($lines.Count -gt 0) { "`n" } else { '' }))
        $manifestSummary = [ordered]@{ schema=1; project_id=$ProjectId; imported_at_utc=$now; file_count=$records.Count; exclusion_count=$exclusions.Count; manifest_sha256=(Get-ProjectSha256 -LiteralPath $manifestPath) }
        Write-ProjectUtf8New -LiteralPath (Join-Path $stage 'manifests\import-summary.json') -Text (($manifestSummary | ConvertTo-Json -Depth 20) + "`n")
        $legacyImportCount=@($records|Where-Object{[string]$_.category -eq 'legacy-run'}).Count
        if($legacyImportCount -gt 0){
            $projectPath=Join-Path $stage 'project.json';$projectState=(Read-ProjectJsonFile -LiteralPath $projectPath -Label 'project.json').Value;$projectState.status='migration_required';$projectState.updated_at_utc=$now;Write-ProjectUtf8Atomic -LiteralPath $projectPath -Text (($projectState|ConvertTo-Json -Depth 32)+"`n")
            $checkpointPath=Join-Path $stage 'state\checkpoint.json';$migrationCheckpoint=(Read-ProjectJsonFile -LiteralPath $checkpointPath -Label 'checkpoint.json').Value;$migrationCheckpoint.project_status='migration_required';$migrationCheckpoint.migration=[ordered]@{status='required';manifest_path='manifests\legacy-semantic-manifest.json';manifest_sha256=$null;recognized_count=$null;disposed_count=0;unresolved_substantive_count=$null};$migrationCheckpoint.updated_at_utc=$now;Write-ProjectUtf8Atomic -LiteralPath $checkpointPath -Text (($migrationCheckpoint|ConvertTo-Json -Depth 32)+"`n")
        }
        $eventData = [ordered]@{ schema=1; sequence=0; event_type='PROJECT_GENESIS'; project_id=$ProjectId; occurred_at_utc=$now; import_manifest_sha256=$manifestSummary.manifest_sha256; previous_event_sha256=$null }
        $eventText = $eventData | ConvertTo-Json -Compress -Depth 20
        $eventData['event_sha256'] = Get-ProjectTextSha256 -Text $eventText
        Write-ProjectUtf8Atomic -LiteralPath (Join-Path $stage 'state\project-events.jsonl') -Text (($eventData | ConvertTo-Json -Compress -Depth 20) + "`n")
        $checkpointPath = Join-Path $stage 'state\checkpoint.json'
        $checkpoint = (Read-ProjectJsonFile -LiteralPath $checkpointPath -Label 'checkpoint.json').Value
        $checkpoint.last_project_event_sha256 = $eventData.event_sha256
        $checkpoint.updated_at_utc = $now
        Write-ProjectUtf8Atomic -LiteralPath $checkpointPath -Text (($checkpoint | ConvertTo-Json -Depth 32) + "`n")
        Move-Item -LiteralPath $stage -Destination $target
    }
    catch {
        if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
        throw
    }
    return Verify-MathResearchProjectArchive -ProjectDirectory $target -StructuralOnly
}

function Read-ImportManifest {
    param([string]$ProjectDirectory)
    $path = Join-Path $ProjectDirectory 'manifests\import-manifest.jsonl'
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw 'Import manifest is missing.' }
    $records = @()
    $lineNumber = 0
    foreach ($line in [IO.File]::ReadLines($path, [Text.UTF8Encoding]::new($false, $true))) {
        $lineNumber++
        if ([string]::IsNullOrWhiteSpace($line)) { throw "Blank import manifest line $lineNumber." }
        try { $record = $line | ConvertFrom-Json -AsHashtable -Depth 20 -DateKind String } catch { throw "Invalid import manifest line $lineNumber." }
        $records += $record
    }
    return ,$records
}

. (Join-Path $PSScriptRoot 'MathResearchLegacyArchive.ps1')

function Verify-MathResearchProjectArchive {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$ProjectDirectory,[switch]$StructuralOnly)
    $resolved = Resolve-MathResearchProjectDirectory -ProjectDirectory $ProjectDirectory
    foreach ($relative in $script:RequiredDirectories) { if (-not (Test-Path -LiteralPath (Join-Path $resolved.Path $relative) -PathType Container)) { throw "Required project directory is missing: $relative" } }
    foreach ($relative in $script:RequiredFiles) { if (-not (Test-Path -LiteralPath (Join-Path $resolved.Path $relative) -PathType Leaf)) { throw "Required project file is missing: $relative" } }
    $checkpoint = Read-ProjectJsonFile -LiteralPath (Join-Path $resolved.Path 'state\checkpoint.json') -Label 'checkpoint.json'
    if ([string]$checkpoint.Value.project_id -cne [string]$resolved.Project.project_id) { throw 'Checkpoint project_id mismatch.' }
    $eventState = Get-ProjectEventState -ProjectDirectory $resolved.Path
    $summary = Read-ProjectJsonFile -LiteralPath (Join-Path $resolved.Path 'manifests\import-summary.json') -Label 'import-summary.json'
    $manifestPath = Join-Path $resolved.Path 'manifests\import-manifest.jsonl'
    if ([string]$summary.Value.manifest_sha256 -cne (Get-ProjectSha256 -LiteralPath $manifestPath)) { throw 'Import manifest hash mismatch.' }
    $verifiedFiles = 0
    foreach ($record in (Read-ImportManifest -ProjectDirectory $resolved.Path)) {
        if ([string]$record.type -ne 'file') { continue }
        $destination = [IO.Path]::GetFullPath((Join-Path $resolved.Path ([string]$record.destination_relative_path)))
        if (-not (Test-ProjectPathInside -Child $destination -Directory $resolved.Path)) { throw 'Import manifest destination escapes the project.' }
        if (-not (Test-Path -LiteralPath $destination -PathType Leaf)) { throw "Imported file is missing: $destination" }
        Assert-ProjectNoReparsePointChain -LiteralPath $destination | Out-Null
        if ([string]$record.sha256 -cne (Get-ProjectSha256 -LiteralPath $destination)) { throw "Imported file hash mismatch: $destination" }
        $verifiedFiles++
    }
    $semantic=$null
    if(-not $StructuralOnly){$semantic=Verify-MathResearchLegacySemanticArchive -ProjectDirectory $resolved.Path}
    return [pscustomobject]@{ Ok=$true; ProjectDirectory=$resolved.Path; ProjectId=[string]$resolved.Project.project_id; ProjectJsonSha256=$resolved.ProjectJsonSha256; Status=[string]$resolved.Project.status; ImportedFilesVerified=$verifiedFiles; ProjectEventHead=$eventState.HeadSha256; Checkpoint=$checkpoint.Value; SemanticArchive=$semantic }
}

function Get-MathResearchProjectResumePlan {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$ProjectDirectory)
    $verified = Verify-MathResearchProjectArchive -ProjectDirectory $ProjectDirectory
    $checkpoint = $verified.Checkpoint
    if ([bool]$checkpoint.dirty -or [bool]$checkpoint.recovery_required) { $action='recovery_or_audit_only' }
    elseif ([bool]$checkpoint.audit_due) { $action='audit_required' }
    elseif ([string]$checkpoint.contract.status -notin @('confirmed','active')) { $action='awaiting_contract' }
    elseif ([string]$checkpoint.run.status -eq 'attempt_running') { $action='resume_same_attempt' }
    elseif ([string]$checkpoint.run.status -in @('active','idle','paused')) { $action='resume_signed_run' }
    else { $action='awaiting_contract' }
    return [pscustomobject]@{ Ok=$true; ProjectId=$verified.ProjectId; Action=$action; AuditDue=[bool]$checkpoint.audit_due; Dirty=[bool]$checkpoint.dirty; ActiveContract=$checkpoint.contract; ActiveRun=$checkpoint.run; ActiveTicket=$checkpoint.active_ticket; MinimalRead=@('README.md','state/CURRENT.md','state/checkpoint.json') }
}

function Assert-StringField {
    param([Collections.IDictionary]$Object, [string]$Key, [string]$Label)
    if (-not $Object.Contains($Key) -or [string]::IsNullOrWhiteSpace([string]$Object[$Key])) { throw "$Label is missing nonempty '$Key'." }
}

function Test-MathResearchFailureRecord {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$FailureRecordFile, [string]$ExpectedAttemptId, [string]$ArtifactRoot)
    $read = Read-ProjectJsonFile -LiteralPath $FailureRecordFile -Label 'failure record'
    $value = $read.Value
    $required = @('schema','attempt_id','route_id','decision_problem','failed_step','failure_reason','excluded_scope','not_excluded_scope','retry_fingerprint_sha256','reopen_conditions','artifacts')
    foreach ($key in $required) { if (-not $value.Contains($key)) { throw "Failure record is missing '$key'." } }
    if ([int]$value.schema -ne 1) { throw 'Failure record schema must be 1.' }
    foreach ($key in @('attempt_id','route_id','decision_problem','failed_step','failure_reason','excluded_scope','not_excluded_scope')) { Assert-StringField -Object $value -Key $key -Label 'Failure record' }
    if (-not [string]::IsNullOrWhiteSpace($ExpectedAttemptId) -and [string]$value.attempt_id -cne $ExpectedAttemptId) { throw 'Failure record attempt_id mismatch.' }
    if ([string]$value.retry_fingerprint_sha256 -cnotmatch '^[0-9a-f]{64}$') { throw 'Failure retry fingerprint must be lowercase SHA-256.' }
    if ($value.reopen_conditions -isnot [Collections.IEnumerable] -or @($value.reopen_conditions).Count -lt 1) { throw 'Failure record requires at least one falsifiable reopen condition.' }
    foreach ($condition in @($value.reopen_conditions)) { if ([string]::IsNullOrWhiteSpace([string]$condition)) { throw 'Failure record has an empty reopen condition.' } }
    if (@($value.artifacts).Count -lt 1) { throw 'Failure record requires at least one artifact.' }
    foreach ($artifact in @($value.artifacts)) {
        if ($artifact -isnot [Collections.IDictionary] -or -not $artifact.Contains('file') -or -not $artifact.Contains('sha256')) { throw 'Failure artifact requires file and sha256.' }
        if ([string]$artifact.sha256 -cnotmatch '^[0-9a-f]{64}$') { throw 'Failure artifact hash must be lowercase SHA-256.' }
        if (-not [string]::IsNullOrWhiteSpace($ArtifactRoot)) {
            $artifactPath = [IO.Path]::GetFullPath((Join-Path $ArtifactRoot ([string]$artifact.file)))
            if (-not (Test-ProjectPathInside -Child $artifactPath -Directory $ArtifactRoot)) { throw 'Failure artifact escapes its root.' }
            if (-not (Test-Path -LiteralPath $artifactPath -PathType Leaf)) { throw "Failure artifact is missing: $artifactPath" }
            if ((Get-ProjectSha256 -LiteralPath $artifactPath) -cne [string]$artifact.sha256) { throw 'Failure artifact hash mismatch.' }
        }
    }
    return [pscustomobject]@{ Ok=$true; Sha256=$read.Sha256; Value=$value }
}

function Test-MathResearchRouteStart {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$ProjectDirectory, [Parameter(Mandatory = $true)][string]$TicketFile)
    $ticket = Read-ProjectJsonFile -LiteralPath $TicketFile -Label 'route ticket'
    return Test-MathResearchRouteStartObject -ProjectDirectory $ProjectDirectory -Ticket $ticket.Value
}

function Get-MathResearchRouteFingerprint {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][Collections.IDictionary]$Ticket)
    foreach ($key in @('route_id','route_family_id','mechanism_id','decision_problem','frozen_domain','resource_caps')) {
        if (-not $Ticket.Contains($key)) { throw "Route fingerprint input is missing '$key'." }
    }
    $material = [ordered]@{
        route_id = [string]$Ticket.route_id
        route_family_id = [string]$Ticket.route_family_id
        mechanism_id = [string]$Ticket.mechanism_id
        decision_problem = [string]$Ticket.decision_problem
        frozen_domain = [string]$Ticket.frozen_domain
        resource_caps = $Ticket.resource_caps
    }
    return Get-ProjectTextSha256 -Text ($material | ConvertTo-Json -Compress -Depth 32)
}

function Test-MathResearchRouteStartObject {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$ProjectDirectory, [Parameter(Mandatory = $true)][Collections.IDictionary]$Ticket)
    $verified = Verify-MathResearchProjectArchive -ProjectDirectory $ProjectDirectory
    foreach ($key in @('route_id','route_fingerprint_sha256','mechanism_id','decision_problem','frozen_domain')) { Assert-StringField -Object $Ticket -Key $key -Label 'Route ticket' }
    if ([string]$Ticket.route_fingerprint_sha256 -cnotmatch '^[0-9a-f]{64}$') { throw 'Route ticket fingerprint must be lowercase SHA-256.' }
    $computedFingerprint = Get-MathResearchRouteFingerprint -Ticket $Ticket
    if ([string]$Ticket.route_fingerprint_sha256 -cne $computedFingerprint) { throw 'Route ticket fingerprint does not match the controller-computed frozen route material.' }
    $registryRead = Read-ProjectJsonFile -LiteralPath (Join-Path $verified.ProjectDirectory 'state\route-registry.json') -Label 'route registry'
    $routeMatches = @($registryRead.Value.routes | Where-Object {
        ([string]$_.route_id -ceq [string]$Ticket.route_id -and [string]$_.retry_fingerprint_sha256 -ceq [string]$Ticket.route_fingerprint_sha256) -or
        ([string]$_.route_family_id -ceq [string]$Ticket.route_family_id -and [string]$_.status -in @('frozen','closed'))
    })
    if ($routeMatches.Count -gt 1) {
        $exact = @($routeMatches | Where-Object { [string]$_.route_id -ceq [string]$Ticket.route_id -and [string]$_.retry_fingerprint_sha256 -ceq [string]$Ticket.route_fingerprint_sha256 })
        if ($exact.Count -eq 1) { $routeMatches = $exact } else { throw 'Route family is frozen by multiple inherited records; a reviewed registry amendment is required.' }
    }
    if ($routeMatches.Count -eq 1 -and [string]$routeMatches[0].status -in @('frozen','closed')) {
        if (-not $Ticket.Contains('reopen_evidence') -or $Ticket.reopen_evidence -isnot [Collections.IDictionary]) { throw 'Duplicate frozen route is blocked without bound reopen evidence.' }
        $evidence = $Ticket.reopen_evidence
        foreach ($key in @('condition_id','evidence_sha256')) { Assert-StringField -Object $evidence -Key $key -Label 'reopen_evidence' }
        if ([string]$evidence.evidence_sha256 -cnotmatch '^[0-9a-f]{64}$') { throw 'Reopen evidence hash must be lowercase SHA-256.' }
        $conditionId = [string]$evidence['condition_id']
        $evidenceSha256 = [string]$evidence['evidence_sha256']
        $allowedConditionIds = if ($routeMatches[0].Contains('reopen_condition_ids')) { [string[]]@($routeMatches[0]['reopen_condition_ids']) } else { @() }
        $seenEvidence = if ($routeMatches[0].Contains('seen_evidence_sha256')) { [string[]]@($routeMatches[0]['seen_evidence_sha256']) } else { @() }
        if ($allowedConditionIds -cnotcontains $conditionId) { throw 'Reopen evidence does not satisfy a pre-registered condition id.' }
        if ($seenEvidence -ccontains $evidenceSha256) { throw 'Reopen evidence was already considered.' }
    }
    return [pscustomobject]@{ Ok=$true; ProjectId=$verified.ProjectId; RouteId=[string]$Ticket.route_id; Fingerprint=[string]$Ticket.route_fingerprint_sha256 }
}

function Get-MathResearchProjectStatus {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$ProjectDirectory)
    $verified = Verify-MathResearchProjectArchive -ProjectDirectory $ProjectDirectory -StructuralOnly
    $migrationStatus=if($verified.Checkpoint.Contains('migration')){[string]$verified.Checkpoint.migration.status}elseif((Get-LegacyImportState -ProjectDirectory $verified.ProjectDirectory).HasLegacy){'required'}else{'not_required'}
    return [pscustomobject]@{ Ok=$true; ProjectId=$verified.ProjectId; ProjectDirectory=$verified.ProjectDirectory; Status=$verified.Status; ProjectJsonSha256=$verified.ProjectJsonSha256; AttemptCount=[int]$verified.Checkpoint.attempt_count; AttemptsSinceLastAudit=[int]$verified.Checkpoint.attempts_since_last_audit; AuditDue=[bool]$verified.Checkpoint.audit_due; Dirty=[bool]$verified.Checkpoint.dirty; MigrationStatus=$migrationStatus }
}

function Test-MathResearchSourceClaims {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$ProjectDirectory, [Parameter(Mandatory = $true)][string[]]$ClaimSha256)
    $verified=Verify-MathResearchProjectArchive -ProjectDirectory $ProjectDirectory
    if($ClaimSha256.Count -lt 1){throw 'At least one source claim/evidence hash is required.'}
    $wanted=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($hash in $ClaimSha256){if($hash -cnotmatch '^[0-9a-f]{64}$'){throw 'Source claim/evidence hashes must be lowercase SHA-256.'};[void]$wanted.Add($hash)}
    $found=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($relativeRoot in @('evidence','attempts')){
        $root=Join-Path $verified.ProjectDirectory $relativeRoot
        foreach($file in @(Get-ChildItem -LiteralPath $root -File -Recurse -Force)){
            Assert-ProjectNoReparsePointChain -LiteralPath $file.FullName|Out-Null
            $hash=Get-ProjectSha256 -LiteralPath $file.FullName
            if($wanted.Contains($hash)){[void]$found.Add($hash)}
        }
    }
    $missing=@($wanted|Where-Object{-not $found.Contains($_)})
    if($missing.Count -gt 0){throw "Source claim/evidence hashes are not present in the verified project archive: $($missing -join ', ')"}
    return [pscustomobject]@{Ok=$true;ProjectId=$verified.ProjectId;VerifiedHashes=@($found)}
}

function Get-ProjectEventState {
    param([Parameter(Mandatory = $true)][string]$ProjectDirectory)
    $path = Join-Path $ProjectDirectory 'state\project-events.jsonl'
    $events = @()
    $sequence = -1
    $head = $null
    # Read the bounded project event stream eagerly so exceptions cannot leave a
    # lazy ReadLines enumerator holding the ledger open on Windows. Preserve JSON
    # date lexemes because PowerShell's default ISO-date coercion can trim a
    # trailing fractional zero and thereby change the hash preimage.
    foreach ($line in [IO.File]::ReadAllLines($path, [Text.UTF8Encoding]::new($false, $true))) {
        if ([string]::IsNullOrWhiteSpace($line)) { throw 'Project event stream contains a blank line.' }
        $event = $line | ConvertFrom-Json -AsHashtable -Depth 32 -DateKind String
        $sequence++
        if ([int]$event.sequence -ne $sequence) { throw 'Project event sequence has a gap or duplicate.' }
        if ($sequence -eq 0 -and $null -ne $event.previous_event_sha256) { throw 'Project genesis has a previous hash.' }
        if ($sequence -gt 0 -and [string]$event.previous_event_sha256 -cne [string]$head) { throw 'Project event hash chain is broken.' }
        $claimed = [string]$event.event_sha256
        $payload = [ordered]@{}
        foreach ($key in $event.Keys) { if ([string]$key -cne 'event_sha256') { $payload[$key] = $event[$key] } }
        $actual = Get-ProjectTextSha256 -Text ($payload | ConvertTo-Json -Compress -Depth 32)
        if ($claimed -cne $actual) { throw 'Project event payload hash mismatch.' }
        $head = $claimed
        $events += ,$event
    }
    if ($events.Count -lt 1) { throw 'Project event stream has no genesis.' }
    return [pscustomobject]@{ Path=$path; Events=$events; HeadSequence=$sequence; HeadSha256=$head }
}

function Add-ProjectEvent {
    param([string]$ProjectDirectory, [string]$EventType, [Collections.IDictionary]$Data)
    $state = Get-ProjectEventState -ProjectDirectory $ProjectDirectory
    $event = [ordered]@{ schema=1; sequence=$state.HeadSequence+1; event_type=$EventType; project_id=$Data.project_id; occurred_at_utc=[DateTime]::UtcNow.ToString('o'); data=$Data; previous_event_sha256=$state.HeadSha256 }
    $eventHash = Get-ProjectTextSha256 -Text ($event | ConvertTo-Json -Compress -Depth 32)
    $event.event_sha256 = $eventHash
    $existing = [IO.File]::ReadAllText($state.Path, [Text.UTF8Encoding]::new($false, $true))
    Write-ProjectUtf8Atomic -LiteralPath $state.Path -Text ($existing + ($event | ConvertTo-Json -Compress -Depth 32) + "`n")
    return $event
}

function Repair-MathResearchProjectEventTail {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$ProjectDirectory)
    $project = Resolve-MathResearchProjectDirectory -ProjectDirectory $ProjectDirectory
    $path = Join-Path $project.Path 'state\project-events.jsonl'
    $lines = @([IO.File]::ReadAllLines($path, [Text.UTF8Encoding]::new($false,$true)))
    if ($lines.Count -lt 2) { throw 'Event-tail repair requires at least one post-genesis event.' }
    $head = $null
    for ($i=0; $i -lt $lines.Count; $i++) {
        $event = $lines[$i] | ConvertFrom-Json -AsHashtable -Depth 32 -DateKind String
        if ([int]$event.sequence -ne $i) { throw 'Event-tail repair refuses a sequence gap.' }
        if ($i -eq 0 -and $null -ne $event.previous_event_sha256) { throw 'Event-tail repair refuses an invalid genesis.' }
        if ($i -gt 0 -and [string]$event.previous_event_sha256 -cne [string]$head) { throw 'Event-tail repair refuses a broken predecessor chain.' }
        $payload=[ordered]@{}
        foreach($key in $event.Keys){if([string]$key -cne 'event_sha256'){$payload[$key]=$event[$key]}}
        $actual=Get-ProjectTextSha256 -Text ($payload | ConvertTo-Json -Compress -Depth 32)
        if ($i -lt $lines.Count-1 -and [string]$event.event_sha256 -cne $actual) { throw 'Event-tail repair refuses corruption before the tail.' }
        if ($i -eq $lines.Count-1) {
            $old=[string]$event.event_sha256
            if ($old -ceq $actual) { return [pscustomobject]@{ Ok=$true; Changed=$false; EventSha256=$actual } }
            $event['event_sha256']=$actual
            $lines[$i]=$event | ConvertTo-Json -Compress -Depth 32
            $checkpointPath=Join-Path $project.Path 'state\checkpoint.json'
            $checkpoint=(Read-ProjectJsonFile -LiteralPath $checkpointPath -Label 'checkpoint.json').Value
            if ([string]$checkpoint.last_project_event_sha256 -cne $old) { throw 'Checkpoint does not point to the damaged tail; repair is refused.' }
            Write-ProjectUtf8Atomic -LiteralPath $path -Text (($lines -join "`n")+"`n")
            $checkpoint.last_project_event_sha256=$actual; $checkpoint.updated_at_utc=[DateTime]::UtcNow.ToString('o')
            Write-ProjectUtf8Atomic -LiteralPath $checkpointPath -Text (($checkpoint|ConvertTo-Json -Depth 32)+"`n")
            return [pscustomobject]@{ Ok=$true; Changed=$true; PreviousEventSha256=$old; EventSha256=$actual }
        }
        $head=[string]$event.event_sha256
    }
}

function Resolve-ProjectRunDirectory {
    param([string]$ProjectDirectory, [string]$RunDirectory)
    $project = Resolve-MathResearchProjectDirectory -ProjectDirectory $ProjectDirectory
    $run = Assert-ProjectNoReparsePointChain -LiteralPath $RunDirectory
    if (-not (Test-Path -LiteralPath $run -PathType Container)) { throw 'Run directory is missing.' }
    if (-not (Split-Path -Parent $run).Equals((Join-Path $project.Path 'runs'), [StringComparison]::OrdinalIgnoreCase)) { throw 'Run must be one direct child of the project runs directory.' }
    return [pscustomobject]@{ Project=$project; Run=$run; RunId=(Split-Path -Leaf $run) }
}

function Register-MathResearchProjectContract {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$ProjectDirectory,
        [Parameter(Mandatory = $true)][string]$ContractFile,
        [Parameter(Mandatory = $true)][string]$ContractBindingSha256,
        [Parameter(Mandatory = $true)][string]$ContractVersion,
        [Parameter(Mandatory = $true)][string]$RunDirectory
    )
    Verify-MathResearchProjectArchive -ProjectDirectory $ProjectDirectory|Out-Null
    $context = Resolve-ProjectRunDirectory -ProjectDirectory $ProjectDirectory -RunDirectory $RunDirectory
    $contractBytes = [IO.File]::ReadAllBytes($ContractFile)
    try { $contractText = [Text.UTF8Encoding]::new($false,$true).GetString($contractBytes) } catch { throw 'Contract file is not strict UTF-8.' }
    if (($contractText -replace "`r`n", "`n").Contains("`r")) { throw 'Contract file contains an isolated CR.' }
    $normalizedContractSha256 = Get-ProjectTextSha256 -Text ($contractText -replace "`r`n", "`n")
    if ($ContractBindingSha256 -cnotmatch '^[0-9a-f]{64}$' -or $normalizedContractSha256 -cne $ContractBindingSha256) { throw 'Contract file does not match the confirmed normalized binding hash.' }
    if ($ContractVersion -cnotmatch '^v[1-9]\d*$') { throw 'ContractVersion must be vN.' }
    $contractDestination = Join-Path $context.Project.Path ("contracts\$ContractVersion-prompt.md")
    if (Test-Path -LiteralPath $contractDestination) { throw 'Contract version is already registered.' }
    Copy-Item -LiteralPath $ContractFile -Destination $contractDestination
    $projectRead = Read-ProjectJsonFile -LiteralPath (Join-Path $context.Project.Path 'project.json') -Label 'project.json'
    $project = $projectRead.Value
    $project.status = 'contract_registered'
    $project.active_contract = [ordered]@{ version=$ContractVersion; path=[IO.Path]::GetRelativePath($context.Project.Path,$contractDestination); sha256=$ContractBindingSha256; status='confirmed' }
    $project.active_run = [ordered]@{ id=$context.RunId; path=[IO.Path]::GetRelativePath($context.Project.Path,$context.Run); status='preparing' }
    $project.updated_at_utc = [DateTime]::UtcNow.ToString('o')
    Write-ProjectUtf8Atomic -LiteralPath (Join-Path $context.Project.Path 'project.json') -Text (($project | ConvertTo-Json -Depth 32) + "`n")
    $checkpointRead = Read-ProjectJsonFile -LiteralPath (Join-Path $context.Project.Path 'state\checkpoint.json') -Label 'checkpoint.json'
    $checkpoint = $checkpointRead.Value
    $checkpoint.project_status='contract_registered'
    $checkpoint.contract=[ordered]@{ path=$project.active_contract.path; sha256=$ContractBindingSha256; status='confirmed'; version=$ContractVersion }
    $checkpoint.run=[ordered]@{ id=$context.RunId; path=$project.active_run.path; status='preparing'; ledger_head_sequence=$null; ledger_head_sha256=$null }
    $checkpoint.dirty=$true; $checkpoint.recovery_required=$false; $checkpoint.updated_at_utc=[DateTime]::UtcNow.ToString('o')
    Write-ProjectUtf8Atomic -LiteralPath (Join-Path $context.Project.Path 'state\checkpoint.json') -Text (($checkpoint | ConvertTo-Json -Depth 32) + "`n")
    $event = Add-ProjectEvent -ProjectDirectory $context.Project.Path -EventType 'CONTRACT_REGISTERED' -Data ([ordered]@{ project_id=[string]$context.Project.Project.project_id; contract_version=$ContractVersion; contract_sha256=$ContractBindingSha256; run_id=$context.RunId })
    $checkpoint.last_project_event_sha256=$event.event_sha256
    Write-ProjectUtf8Atomic -LiteralPath (Join-Path $context.Project.Path 'state\checkpoint.json') -Text (($checkpoint | ConvertTo-Json -Depth 32) + "`n")
    return [pscustomobject]@{ Ok=$true; ProjectId=[string]$context.Project.Project.project_id; Contract=$project.active_contract; Run=$project.active_run; SagaState='CONTRACT_REGISTERED'; EventSha256=$event.event_sha256 }
}

function Set-GeneratedMarkdownBlock {
    param([string]$LiteralPath, [string]$Name, [string]$Body)
    $start = "<!-- math-research-generated-${Name}:start -->"
    $end = "<!-- math-research-generated-${Name}:end -->"
    $block = "$start`n$Body`n$end"
    $text = if (Test-Path -LiteralPath $LiteralPath) { [IO.File]::ReadAllText($LiteralPath, [Text.UTF8Encoding]::new($false, $true)) } else { '' }
    $pattern = [regex]::Escape($start) + '.*?' + [regex]::Escape($end)
    if ([regex]::IsMatch($text,$pattern,[Text.RegularExpressions.RegexOptions]::Singleline)) { $text=[regex]::Replace($text,$pattern,[Text.RegularExpressions.MatchEvaluator]{param($m)$block},[Text.RegularExpressions.RegexOptions]::Singleline) }
    else { $text=$text.TrimEnd()+"`n`n$block`n" }
    Write-ProjectUtf8Atomic -LiteralPath $LiteralPath -Text $text
}

function Publish-VerifiedRunArtifact {
    param(
        [Parameter(Mandatory = $true)][string]$RunDirectory,
        [Parameter(Mandatory = $true)][string]$ProjectDirectory,
        [Parameter(Mandatory = $true)][string]$SourceRelativePath,
        [Parameter(Mandatory = $true)][string]$ExpectedSha256,
        [Parameter(Mandatory = $true)][string]$DestinationRelativePath,
        [switch]$PreflightOnly
    )
    if ([IO.Path]::IsPathFullyQualified($SourceRelativePath) -or [IO.Path]::IsPathFullyQualified($DestinationRelativePath)) { throw 'Published artifact paths must be relative.' }
    $source = [IO.Path]::GetFullPath((Join-Path $RunDirectory $SourceRelativePath))
    $destination = [IO.Path]::GetFullPath((Join-Path $ProjectDirectory $DestinationRelativePath))
    if (-not (Test-ProjectPathInside -Child $source -Directory $RunDirectory) -or -not (Test-ProjectPathInside -Child $destination -Directory $ProjectDirectory)) { throw 'Published artifact path escapes its trusted root.' }
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Published source artifact is missing: $SourceRelativePath" }
    Assert-ProjectNoReparsePointChain -LiteralPath $source | Out-Null
    if ($ExpectedSha256 -cnotmatch '^[0-9a-f]{64}$' -or (Get-ProjectSha256 -LiteralPath $source) -cne $ExpectedSha256) { throw "Published source artifact hash mismatch: $SourceRelativePath" }
    $parent = Split-Path -Parent $destination
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) { New-Item -ItemType Directory -Path $parent | Out-Null }
    Assert-ProjectNoReparsePointChain -LiteralPath $parent | Out-Null
    if (Test-Path -LiteralPath $destination) {
        if (-not (Test-Path -LiteralPath $destination -PathType Leaf) -or (Get-ProjectSha256 -LiteralPath $destination) -cne $ExpectedSha256) { throw "Published artifact destination conflict: $DestinationRelativePath" }
    }
    elseif (-not $PreflightOnly) {
        [IO.File]::Copy($source, $destination, $false)
        if ((Get-ProjectSha256 -LiteralPath $destination) -cne $ExpectedSha256) { throw "Published artifact copy verification failed: $DestinationRelativePath" }
    }
    return [IO.Path]::GetRelativePath($ProjectDirectory, $destination)
}

function Publish-VerifiedRunEvidence {
    param([string]$RunDirectory, [string]$ProjectDirectory, [string]$RunId, [switch]$PreflightOnly)
    if ($RunId -cnotmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$') { throw 'Artifact publication encountered an unsafe run id.' }
    $ledger = Join-Path $RunDirectory 'cycle-ledger'
    $published = [Collections.Generic.List[string]]::new()
    foreach ($eventFile in @(Get-ChildItem -LiteralPath $ledger -File -Filter '*.json' | Sort-Object Name)) {
        $read = Read-SignedJsonPayload -LiteralPath $eventFile.FullName
        if ($read.RecoveredFromBackup) { throw 'Project publication refuses an immutable cycle event recovered from backup.' }
        $event = $read.Payload
        if ([string]$event.event_type -eq 'ATTEMPT_END') {
            $attemptId = [string]$event.data.attempt_id
            if ($attemptId -cnotmatch '^attempt-\d{4}$') { throw 'Attempt publication encountered an unsafe attempt id.' }
            $extension = [IO.Path]::GetExtension([string]$event.data.artifact_file)
            $published.Add((Publish-VerifiedRunArtifact -RunDirectory $RunDirectory -ProjectDirectory $ProjectDirectory -SourceRelativePath ([string]$event.data.artifact_file) -ExpectedSha256 ([string]$event.data.artifact_sha256) -DestinationRelativePath "attempts\$RunId\$attemptId\result$extension" -PreflightOnly:$PreflightOnly))
            $evidenceClass = if ([string]$event.data.outcome -in @('candidate_found','proved_subclaim','route_refuted','bounded_negative')) { 'verified' } elseif ([string]$event.data.outcome -eq 'portfolio_proposed') { 'exploratory' } else { 'partial' }
            $published.Add((Publish-VerifiedRunArtifact -RunDirectory $RunDirectory -ProjectDirectory $ProjectDirectory -SourceRelativePath ([string]$event.data.artifact_file) -ExpectedSha256 ([string]$event.data.artifact_sha256) -DestinationRelativePath "evidence\$evidenceClass\$RunId-$attemptId$extension" -PreflightOnly:$PreflightOnly))
            if ($event.data.Contains('attempt_record_file')) {
                $recordRelative = [string]$event.data.attempt_record_file
                $recordHash = [string]$event.data.attempt_record_sha256
                $published.Add((Publish-VerifiedRunArtifact -RunDirectory $RunDirectory -ProjectDirectory $ProjectDirectory -SourceRelativePath $recordRelative -ExpectedSha256 $recordHash -DestinationRelativePath "attempts\$RunId\$attemptId\attempt-record.json" -PreflightOnly:$PreflightOnly))
                $record = (Read-ProjectJsonFile -LiteralPath (Join-Path $RunDirectory $recordRelative) -Label "attempt record $attemptId").Value
                $index = 0
                foreach ($report in @($record.solver_reports)) {
                    $index++; $ext=[IO.Path]::GetExtension([string]$report.file)
                    $published.Add((Publish-VerifiedRunArtifact -RunDirectory $RunDirectory -ProjectDirectory $ProjectDirectory -SourceRelativePath ([string]$report.file) -ExpectedSha256 ([string]$report.sha256) -DestinationRelativePath ("attempts\$RunId\$attemptId\solver-{0:D2}$ext" -f $index) -PreflightOnly:$PreflightOnly))
                }
                $index = 0
                foreach ($report in @($record.verification_reports)) {
                    $index++; $ext=[IO.Path]::GetExtension([string]$report.artifact_file)
                    $published.Add((Publish-VerifiedRunArtifact -RunDirectory $RunDirectory -ProjectDirectory $ProjectDirectory -SourceRelativePath ([string]$report.artifact_file) -ExpectedSha256 ([string]$report.artifact_sha256) -DestinationRelativePath ("attempts\$RunId\$attemptId\verification-{0:D2}$ext" -f $index) -PreflightOnly:$PreflightOnly))
                }
                if ($null -ne $record.route_portfolio) {
                    $published.Add((Publish-VerifiedRunArtifact -RunDirectory $RunDirectory -ProjectDirectory $ProjectDirectory -SourceRelativePath ([string]$record.route_portfolio.file) -ExpectedSha256 ([string]$record.route_portfolio.sha256) -DestinationRelativePath "cycles\$RunId\route-portfolios\$attemptId.json" -PreflightOnly:$PreflightOnly))
                }
            }
            if ($event.data.Contains('failure_record_file')) {
                $failureRelative=[string]$event.data.failure_record_file
                $failureValidated=Test-MathResearchFailureRecord -FailureRecordFile (Join-Path $RunDirectory $failureRelative) -ExpectedAttemptId $attemptId -ArtifactRoot $RunDirectory
                if($failureValidated.Sha256 -cne [string]$event.data.failure_record_sha256){throw 'Failure publication hash does not match the AttemptEnd binding.'}
                $routeId=[string]$failureValidated.Value.route_id
                if($routeId -cnotmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$'){throw 'Failure publication encountered an unsafe route id.'}
                $published.Add((Publish-VerifiedRunArtifact -RunDirectory $RunDirectory -ProjectDirectory $ProjectDirectory -SourceRelativePath $failureRelative -ExpectedSha256 ([string]$event.data.failure_record_sha256) -DestinationRelativePath "failures\$routeId.failure.json" -PreflightOnly:$PreflightOnly))
                $markdownRelative="failures\$routeId.md";$markdownPath=Join-Path $ProjectDirectory $markdownRelative
                $failure=$failureValidated.Value
                $reopenLines=(@($failure.reopen_conditions)|ForEach-Object{"- $_"}) -join "`n"
                $markdown="# Failure dossier: $routeId`n`n- run_id: $RunId`n- attempt_id: $attemptId`n- decision_problem: $($failure.decision_problem)`n- failed_step: $($failure.failed_step)`n- failure_reason: $($failure.failure_reason)`n- excluded_scope: $($failure.excluded_scope)`n- not_excluded_scope: $($failure.not_excluded_scope)`n- retry_fingerprint_sha256: ``$($failure.retry_fingerprint_sha256)```n`n## Reopen conditions`n`n$reopenLines`n"
                if(Test-Path -LiteralPath $markdownPath){if([IO.File]::ReadAllText($markdownPath,[Text.UTF8Encoding]::new($false,$true)) -cne $markdown){throw "Published artifact destination conflict: $markdownRelative"}}
                elseif(-not $PreflightOnly){Write-ProjectUtf8New -LiteralPath $markdownPath -Text $markdown}
                if(-not $PreflightOnly){$published.Add($markdownRelative)}
            }
        }
        elseif ([string]$event.event_type -eq 'AUDIT_END') {
            $auditId = [string]$event.data.audit_id
            if ($auditId -cnotmatch '^audit-\d+$') { throw 'Audit publication encountered an unsafe audit id.' }
            $resultRelative = [string]$event.data.audit_result_file
            $published.Add((Publish-VerifiedRunArtifact -RunDirectory $RunDirectory -ProjectDirectory $ProjectDirectory -SourceRelativePath $resultRelative -ExpectedSha256 ([string]$event.data.audit_result_sha256) -DestinationRelativePath "cycles\$RunId\$auditId\audit-result.json" -PreflightOnly:$PreflightOnly))
            $audit = (Read-ProjectJsonFile -LiteralPath (Join-Path $RunDirectory $resultRelative) -Label "audit result $auditId").Value
            foreach ($report in @($audit.reports)) {
                $role = [string]$report.role
                if ($role -notin @('skeptic_quantifiers','skeptic_strategy','theory_tool_scout')) { throw 'Audit publication encountered an unsafe role.' }
                $ext=[IO.Path]::GetExtension([string]$report.artifact_file)
                $published.Add((Publish-VerifiedRunArtifact -RunDirectory $RunDirectory -ProjectDirectory $ProjectDirectory -SourceRelativePath ([string]$report.artifact_file) -ExpectedSha256 ([string]$report.artifact_sha256) -DestinationRelativePath "cycles\$RunId\$auditId\$role$ext" -PreflightOnly:$PreflightOnly))
            }
        }
    }
    return @($published)
}

function Get-VerifiedRunPublicationSummary {
    param([string]$RunDirectory)
    $attemptKinds=[ordered]@{};$attempts=[Collections.Generic.List[object]]::new();$audits=[Collections.Generic.List[object]]::new()
    foreach($eventFile in @(Get-ChildItem -LiteralPath (Join-Path $RunDirectory 'cycle-ledger') -File -Filter '*.json'|Sort-Object Name)){
        $event=(Read-SignedJsonPayload -LiteralPath $eventFile.FullName).Payload
        if([string]$event.event_type -eq 'ATTEMPT_START'){$attemptKinds[[string]$event.data.attempt_id]=if($event.data.Contains('attempt_kind')){[string]$event.data.attempt_kind}else{'legacy'}}
        elseif([string]$event.event_type -eq 'ATTEMPT_END'){$attempts.Add([ordered]@{attempt_id=[string]$event.data.attempt_id;attempt_kind=[string]$attemptKinds[[string]$event.data.attempt_id];outcome=[string]$event.data.outcome;artifact_file=[string]$event.data.artifact_file;artifact_sha256=[string]$event.data.artifact_sha256;route_portfolio_file=if($event.data.Contains('route_portfolio_file')){[string]$event.data.route_portfolio_file}else{$null}})}
        elseif([string]$event.event_type -eq 'AUDIT_END'){$audits.Add([ordered]@{audit_id=[string]$event.data.audit_id;action=[string]$event.data.action;accepted_route_cards=if($event.data.Contains('accepted_route_cards')){@($event.data.accepted_route_cards)}else{@()}})}
    }
    return [pscustomobject]@{Attempts=@($attempts);Audits=@($audits)}
}

function Update-ProjectRouteRegistryFromRunFailures {
    param([string]$RunDirectory,[string]$ProjectDirectory,[string]$RunId)
    $registryPath=Join-Path $ProjectDirectory 'state\route-registry.json';$registry=(Read-ProjectJsonFile -LiteralPath $registryPath -Label 'route registry').Value
    $routes=[Collections.Generic.List[object]]::new();foreach($existing in @($registry.routes)){$routes.Add($existing)}
    foreach($eventFile in @(Get-ChildItem -LiteralPath (Join-Path $RunDirectory 'cycle-ledger') -File -Filter '*.json'|Sort-Object Name)){
        $event=(Read-SignedJsonPayload -LiteralPath $eventFile.FullName).Payload
        if([string]$event.event_type -ne 'ATTEMPT_END' -or -not $event.data.Contains('failure_record_file')){continue}
        $attemptId=[string]$event.data.attempt_id;$failure=(Test-MathResearchFailureRecord -FailureRecordFile (Join-Path $RunDirectory ([string]$event.data.failure_record_file)) -ExpectedAttemptId $attemptId -ArtifactRoot $RunDirectory).Value
        $routeId=[string]$failure.route_id;$matches=@($routes|Where-Object{[string]$_.route_id -eq $routeId})
        if($matches.Count -gt 1){throw "Route registry has duplicate route_id $routeId."}
        $entry=[ordered]@{route_id=$routeId;route_family_id=$routeId;retry_fingerprint_sha256=[string]$failure.retry_fingerprint_sha256;status='frozen';origin='active_run';run_id=$RunId;attempt_id=$attemptId;counter_effect='active_attempt';reopen_condition_ids=@($failure.reopen_conditions|ForEach-Object{([string]$_ -split ':',2)[0]});seen_evidence_sha256=@()}
        if($matches.Count -eq 1){if([string]$matches[0].retry_fingerprint_sha256 -cne [string]$entry.retry_fingerprint_sha256){throw "Route registry conflicts with published failure $routeId."}}
        else{$routes.Add($entry)}
    }
    $registry.routes=@($routes);Write-ProjectUtf8Atomic -LiteralPath $registryPath -Text (($registry|ConvertTo-Json -Depth 64)+"`n")
}

function Publish-MathResearchProjectCheckpoint {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$ProjectDirectory, [Parameter(Mandatory = $true)][string]$RunDirectory)
    Verify-MathResearchProjectArchive -ProjectDirectory $ProjectDirectory|Out-Null
    $context = Resolve-ProjectRunDirectory -ProjectDirectory $ProjectDirectory -RunDirectory $RunDirectory
    $launcherModule = Join-Path $PSScriptRoot 'MathResearchLauncherV2.psm1'
    $cycleModule = Join-Path $PSScriptRoot 'MathResearchCycleLedgerV2.psm1'
    if ($null -eq (Get-Command Read-SignedJsonPayload -ErrorAction SilentlyContinue)) { Import-Module $launcherModule -DisableNameChecking }
    if ($null -eq (Get-Command Verify-MathResearchCycleLedger -ErrorAction SilentlyContinue)) { Import-Module $cycleModule -DisableNameChecking }
    $manifestPath = Join-Path $context.Run 'run.json'
    $manifestRead = Read-SignedJsonPayload -LiteralPath $manifestPath
    if ($manifestRead.RecoveredFromBackup) { throw 'Project publication refuses a run manifest recovered from backup.' }
    $manifest = $manifestRead.Payload
    if ([string]$manifest.run_directory -cne $context.Run -or [string]$manifest.project.project_id -cne [string]$context.Project.Project.project_id) { throw 'Run manifest does not match the project archive.' }
    $cycle = Verify-MathResearchCycleLedger -RunDirectory $context.Run
    $checkpointPath = Join-Path $context.Project.Path 'state\checkpoint.json'
    $checkpointRead = Read-ProjectJsonFile -LiteralPath $checkpointPath -Label 'checkpoint.json'
    $checkpoint = $checkpointRead.Value
    $publicationIndexPath=Join-Path $context.Project.Path 'manifests\publication-index.json'
    $publicationIndex=if(Test-Path -LiteralPath $publicationIndexPath){(Read-ProjectJsonFile -LiteralPath $publicationIndexPath -Label 'publication index').Value}else{[ordered]@{schema=1;project_id=[string]$context.Project.Project.project_id;entries=@()}}
    if([int]$publicationIndex.schema -ne 1 -or [string]$publicationIndex.project_id -cne [string]$context.Project.Project.project_id){throw 'Publication index identity mismatch.'}
    $sameSequence=@($publicationIndex.entries|Where-Object{[string]$_.run_id -eq $context.RunId -and [int]$_.ledger_head_sequence -eq [int]$cycle.HeadSequence})
    if($sameSequence.Count -gt 0){
        if($sameSequence.Count -ne 1 -or [string]$sameSequence[0].ledger_head_sha256 -cne [string]$cycle.HeadPayloadSha256){throw 'Publication index and verified ledger have diverged.'}
        if([bool]$checkpoint.recovery_required){throw 'Publication recovery is required before an indexed checkpoint can be accepted.'}
        foreach($artifact in @($sameSequence[0].artifacts)){$path=Join-Path $context.Project.Path ([string]$artifact.path);if(-not (Test-Path -LiteralPath $path -PathType Leaf) -or (Get-ProjectSha256 -LiteralPath $path) -cne [string]$artifact.sha256){throw 'Indexed publication artifact is missing or changed.'}}
        return [pscustomobject]@{Ok=$true;AlreadyPublished=$true;ProjectId=[string]$context.Project.Project.project_id;RunId=$context.RunId;LedgerHeadSequence=[int]$cycle.HeadSequence;LedgerHeadSha256=[string]$cycle.HeadPayloadSha256;PublishedArtifacts=@($sameSequence[0].artifacts|ForEach-Object{[string]$_.path});EventSha256=[string]$sameSequence[0].project_event_sha256}
    }
    $higher=@($publicationIndex.entries|Where-Object{[string]$_.run_id -eq $context.RunId -and [int]$_.ledger_head_sequence -gt [int]$cycle.HeadSequence})
    if($higher.Count -gt 0){throw 'Publication index is ahead of the verified run ledger.'}
    $publicationStage=Join-Path $context.Project.Path ('.publication-stage-'+[guid]::NewGuid().ToString('N'))
    try{
        New-Item -ItemType Directory -Path $publicationStage|Out-Null
        $publishedArtifacts=@(Publish-VerifiedRunEvidence -RunDirectory $context.Run -ProjectDirectory $publicationStage -RunId $context.RunId)
        $publicationRecords=[Collections.Generic.List[object]]::new()
        foreach($relative in $publishedArtifacts){$staged=Join-Path $publicationStage $relative;$publicationRecords.Add([ordered]@{path=$relative;sha256=(Get-ProjectSha256 -LiteralPath $staged)})}
        foreach($record in $publicationRecords){$destination=Join-Path $context.Project.Path ([string]$record.path);if(Test-Path -LiteralPath $destination){if((Get-ProjectSha256 -LiteralPath $destination) -cne [string]$record.sha256){throw "Published artifact destination conflict: $($record.path)"}}}
        $checkpoint.dirty=$true;$checkpoint.recovery_required=$true;$checkpoint.updated_at_utc=[DateTime]::UtcNow.ToString('o');Write-ProjectUtf8Atomic -LiteralPath $checkpointPath -Text (($checkpoint|ConvertTo-Json -Depth 64)+"`n")
        $committedCount=0
        foreach($record in $publicationRecords){$source=Join-Path $publicationStage ([string]$record.path);$destination=Join-Path $context.Project.Path ([string]$record.path);if(-not (Test-Path -LiteralPath $destination)){New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force|Out-Null;[IO.File]::Copy($source,$destination,$false)};if((Get-ProjectSha256 -LiteralPath $destination) -cne [string]$record.sha256){throw 'Publication commit hash verification failed.'};$committedCount++;if($script:PublicationFailAfterArtifactCommitForTests -and $committedCount -eq 1){throw 'Synthetic publication commit interruption.'}}
    } finally {if(Test-Path -LiteralPath $publicationStage){Remove-Item -LiteralPath $publicationStage -Recurse -Force}}
    $publicationSummary = Get-VerifiedRunPublicationSummary -RunDirectory $context.Run
    Update-ProjectRouteRegistryFromRunFailures -RunDirectory $context.Run -ProjectDirectory $context.Project.Path -RunId $context.RunId
    if ($checkpoint.run.Contains('ledger_head_sequence') -and $null -ne $checkpoint.run.ledger_head_sequence -and [int]$checkpoint.run.ledger_head_sequence -gt [int]$cycle.HeadSequence) { throw 'Project checkpoint is ahead of the verified run ledger.' }
    if ($checkpoint.run.Contains('ledger_head_sequence') -and $null -ne $checkpoint.run.ledger_head_sequence -and [int]$checkpoint.run.ledger_head_sequence -eq [int]$cycle.HeadSequence -and $checkpoint.run.Contains('ledger_head_sha256') -and [string]$checkpoint.run.ledger_head_sha256 -cne [string]$cycle.HeadPayloadSha256) { throw 'Project checkpoint and run ledger have diverged.' }
    $checkpoint.project_status = if ($cycle.CompletionAuthorized) { 'completion_candidate' } elseif ($cycle.AuditDue) { 'audit_due' } elseif ($cycle.CleanReturn) { 'active' } else { 'active_dirty' }
    $goalId = if ($manifest.goal.Contains('goal_id')) { $manifest.goal.goal_id } else { $null }
    $checkpoint.goal=[ordered]@{ id=$goalId; status=$manifest.goal.observed_status }
    $runState = if ($null -ne $cycle.ActiveAttempt) { 'attempt_running' } elseif ($null -ne $cycle.ActiveAudit) { 'auditing' } elseif ($cycle.CompletionAuthorized) { 'completion_authorized' } elseif ($cycle.CompletionCandidate) { 'completion_candidate' } elseif ($cycle.AuditDue) { 'audit_due' } elseif ($cycle.CleanReturn) { 'idle' } else { 'active_dirty' }
    $checkpoint.run=[ordered]@{ id=$context.RunId; path=[IO.Path]::GetRelativePath($context.Project.Path,$context.Run); status=$runState; ledger_head_sequence=[int]$cycle.HeadSequence; ledger_head_sha256=[string]$cycle.HeadPayloadSha256; manifest_sha256=(Get-ProjectSha256 -LiteralPath $manifestPath) }
    $checkpoint.thread=[ordered]@{ id=[string]$manifest.thread_id; status='bound' }
    $checkpoint.attempt_count=[int]$cycle.AttemptCount; $checkpoint.attempts_since_last_audit=[int]$cycle.AttemptsSinceLastAudit; $checkpoint.audit_due=[bool]$cycle.AuditDue; $checkpoint.dirty=(-not [bool]$cycle.CleanReturn); $checkpoint.recovery_required=($null -ne $cycle.ActiveAttempt -or $null -ne $cycle.ActiveAudit)
    $checkpoint.active_ticket=if ($null -ne $cycle.ActiveAttempt) { [ordered]@{ ticket_id=[string]$cycle.ActiveAttempt.ticket_id; attempt_id=[string]$cycle.ActiveAttempt.attempt_id } } else { $null }
    $checkpoint.updated_at_utc=[DateTime]::UtcNow.ToString('o')
    Write-ProjectUtf8Atomic -LiteralPath $checkpointPath -Text (($checkpoint | ConvertTo-Json -Depth 32) + "`n")
    $statusBody = "## 控制器状态`n`n- project_status: $($checkpoint.project_status)`n- run: $($context.RunId)`n- attempt_count: $($checkpoint.attempt_count)`n- attempts_since_last_audit: $($checkpoint.attempts_since_last_audit)`n- audit_due: $($checkpoint.audit_due)`n- dirty: $($checkpoint.dirty)`n- ledger_head: $($cycle.HeadSequence) / $($cycle.HeadPayloadSha256)"
    Set-GeneratedMarkdownBlock -LiteralPath (Join-Path $context.Project.Path 'state\CURRENT.md') -Name 'status' -Body $statusBody
    $evidenceLines=[Collections.Generic.List[string]]::new();$evidenceLines.Add("## Run $($context.RunId) 已发布证据")
    foreach($relative in $publishedArtifacts){$hash=Get-ProjectSha256 -LiteralPath (Join-Path $context.Project.Path $relative);$evidenceLines.Add("- ``$relative`` — SHA-256 ``$hash``")}
    Set-GeneratedMarkdownBlock -LiteralPath (Join-Path $context.Project.Path 'state\EVIDENCE.md') -Name "evidence-$($context.RunId)" -Body ($evidenceLines -join "`n")
    $resultLines=[Collections.Generic.List[string]]::new();$resultLines.Add("## Run $($context.RunId) 尝试结果")
    foreach($attempt in @($publicationSummary.Attempts)){$resultLines.Add("- $($attempt.attempt_id) / $($attempt.attempt_kind): ``$($attempt.outcome)``；原始产物 ``$($attempt.artifact_file)``；SHA-256 ``$($attempt.artifact_sha256)``")}
    Set-GeneratedMarkdownBlock -LiteralPath (Join-Path $context.Project.Path 'state\RESULTS.md') -Name "results-$($context.RunId)" -Body ($resultLines -join "`n")
    $routeLines=[Collections.Generic.List[string]]::new();$routeLines.Add("## Run $($context.RunId) 路线记录")
    foreach($attempt in @($publicationSummary.Attempts|Where-Object{-not [string]::IsNullOrWhiteSpace([string]$_.route_portfolio_file)})){$routeLines.Add("- $($attempt.attempt_id) 提交路线组合 ``$($attempt.route_portfolio_file)``，须以随后审计记录为准。")}
    foreach($audit in @($publicationSummary.Audits)){$routeLines.Add("- $($audit.audit_id): ``$($audit.action)``；接受路线卡 $(@($audit.accepted_route_cards).Count) 张。")}
    Set-GeneratedMarkdownBlock -LiteralPath (Join-Path $context.Project.Path 'state\ROUTES.md') -Name "routes-$($context.RunId)" -Body ($routeLines -join "`n")
    $event = Add-ProjectEvent -ProjectDirectory $context.Project.Path -EventType 'RUN_CHECKPOINT_PUBLISHED' -Data ([ordered]@{ project_id=[string]$context.Project.Project.project_id; run_id=$context.RunId; ledger_head_sequence=[int]$cycle.HeadSequence; ledger_head_sha256=[string]$cycle.HeadPayloadSha256; attempt_count=[int]$cycle.AttemptCount; audit_due=[bool]$cycle.AuditDue; published_artifacts=@($publishedArtifacts) })
    $publicationIndex.entries=@($publicationIndex.entries)+@([ordered]@{run_id=$context.RunId;ledger_head_sequence=[int]$cycle.HeadSequence;ledger_head_sha256=[string]$cycle.HeadPayloadSha256;run_manifest_sha256=(Get-ProjectSha256 -LiteralPath $manifestPath);artifacts=@($publicationRecords);project_event_sha256=[string]$event.event_sha256;published_at_utc=[DateTime]::UtcNow.ToString('o')})
    Write-ProjectUtf8Atomic -LiteralPath $publicationIndexPath -Text (($publicationIndex|ConvertTo-Json -Depth 64)+"`n")
    $checkpoint.last_project_event_sha256=$event.event_sha256
    Write-ProjectUtf8Atomic -LiteralPath $checkpointPath -Text (($checkpoint | ConvertTo-Json -Depth 32) + "`n")
    return [pscustomobject]@{ Ok=$true; AlreadyPublished=$false; ProjectId=[string]$context.Project.Project.project_id; RunId=$context.RunId; LedgerHeadSequence=[int]$cycle.HeadSequence; LedgerHeadSha256=[string]$cycle.HeadPayloadSha256; CleanReturn=[bool]$cycle.CleanReturn; AuditDue=[bool]$cycle.AuditDue; RecoveryRequired=[bool]$checkpoint.recovery_required; PublishedArtifacts=@($publishedArtifacts); EventSha256=$event.event_sha256 }
}

function New-MathResearchProjectHandoff {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$ProjectDirectory, [string]$Label = 'handoff')
    $verified = Verify-MathResearchProjectArchive -ProjectDirectory $ProjectDirectory
    $plan = Get-MathResearchProjectResumePlan -ProjectDirectory $ProjectDirectory
    $timestamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
    $path = Join-Path $verified.ProjectDirectory ("handoffs\$timestamp-$Label.md")
    $body = "# Math research handoff`n`n- project_id: $($verified.ProjectId)`n- status: $($verified.Status)`n- next_action: $($plan.Action)`n- audit_due: $($plan.AuditDue)`n- dirty: $($plan.Dirty)`n- project_json_sha256: $($verified.ProjectJsonSha256)`n`n## 最小恢复读取`n`n1. ../README.md`n2. ../state/CURRENT.md`n3. ../state/checkpoint.json`n4. 活动合同与当前票据（若有）`n"
    Write-ProjectUtf8New -LiteralPath $path -Text $body
    $event = Add-ProjectEvent -ProjectDirectory $verified.ProjectDirectory -EventType 'HANDOFF_CREATED' -Data ([ordered]@{ project_id=$verified.ProjectId; handoff_path=[IO.Path]::GetRelativePath($verified.ProjectDirectory,$path); handoff_sha256=(Get-ProjectSha256 -LiteralPath $path); next_action=$plan.Action })
    $checkpointPath = Join-Path $verified.ProjectDirectory 'state\checkpoint.json'
    $checkpoint = (Read-ProjectJsonFile -LiteralPath $checkpointPath -Label 'checkpoint.json').Value
    $checkpoint.last_project_event_sha256=$event.event_sha256; $checkpoint.updated_at_utc=[DateTime]::UtcNow.ToString('o')
    Write-ProjectUtf8Atomic -LiteralPath $checkpointPath -Text (($checkpoint | ConvertTo-Json -Depth 32) + "`n")
    return [pscustomobject]@{ Ok=$true; Path=$path; Sha256=(Get-ProjectSha256 -LiteralPath $path); NextAction=$plan.Action; EventSha256=$event.event_sha256 }
}

Export-ModuleMember -Function @(
    'Get-MathResearchProjectsRoot','Resolve-MathResearchProjectDirectory',
    'Initialize-MathResearchProjectArchive','Verify-MathResearchProjectArchive',
    'Analyze-MathResearchLegacyArchive','Apply-MathResearchLegacyMigration','Verify-MathResearchLegacySemanticArchive','Test-MathResearchLegacyFailureRecord',
    'Get-MathResearchProjectResumePlan','Get-MathResearchProjectStatus','Test-MathResearchSourceClaims',
    'Test-MathResearchFailureRecord','Get-MathResearchRouteFingerprint',
    'Test-MathResearchRouteStart','Test-MathResearchRouteStartObject',
    'Register-MathResearchProjectContract','Publish-MathResearchProjectCheckpoint',
    'New-MathResearchProjectHandoff','Repair-MathResearchProjectEventTail'
)
