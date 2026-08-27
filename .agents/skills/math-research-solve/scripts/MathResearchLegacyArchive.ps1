$script:LegacySemanticSchema = 1
$script:LegacyDispositions = @('attempt','failure','partial_evidence','exploratory_evidence','source','operational_blocker','duplicate','excluded_nonresearch')

function Throw-LegacySemanticIncomplete {
    param([string]$Detail)
    $code='legacy_semantic_archive_'+'incomplete'
    throw "${code}: $Detail"
}

function Get-LegacyFragmentId {
    param([string]$RelativePath,[string]$Locator,[string]$FragmentSha256)
    $hash=Get-ProjectTextSha256 -Text ($RelativePath.ToLowerInvariant()+"`n"+$Locator+"`n"+$FragmentSha256)
    return 'legacy-'+$hash.Substring(0,20)
}

function Get-LegacyDispositionSuggestion {
    param([string]$Kind,[string]$Text)
    $lower=$Text.ToLowerInvariant()
    switch($Kind){
        'attempt' { return [pscustomobject]@{Disposition='attempt';Rationale='Legacy attempt ledger entry.';Confidence='high'} }
        'source' { return [pscustomobject]@{Disposition='source';Rationale='Legacy source extraction or source audit.';Confidence='high'} }
        'sandbox_signal' { return [pscustomobject]@{Disposition='exploratory_evidence';Rationale='Bounded exploratory or sandbox signal; it is not promoted as a mathematical conclusion.';Confidence='high'} }
        'reproduction' { return [pscustomobject]@{Disposition='partial_evidence';Rationale='Reproduction or audit evidence with an explicit finite or unresolved boundary.';Confidence='high'} }
        'artifact_metadata' {
            if($lower -match 'sourceextract|source[-_ ]extract|sourcediscoveryfrontier|source[-_ ]discovery'){return [pscustomobject]@{Disposition='source';Rationale='Artifact metadata describes a source extraction, source discovery frontier, or source audit.';Confidence='high'}}
            if($lower -match 'sandbox(search|_search)|sandbox-only|exploratory'){return [pscustomobject]@{Disposition='exploratory_evidence';Rationale='Artifact metadata describes bounded exploratory work.';Confidence='medium'}}
            return [pscustomobject]@{Disposition='partial_evidence';Rationale='Artifact metadata preserves evidence and limitations without promoting a result.';Confidence='medium'}
        }
        'blocked' {
            if($lower -match 'tool.{0,40}(unavailable|missing|not available)|maple.{0,40}(unavailable|not available|absence)|bootstrap|initiali[sz]ation|ledger.{0,20}missing|no[- ]new[- ]object|environment|path.{0,20}missing'){return [pscustomobject]@{Disposition='operational_blocker';Rationale='The stop condition is operational or initialization-related, not a mathematical counterexample.';Confidence='medium'}}
            if($lower -match 'sourceextractaudit|sourcediscoveryfrontier|source extract|source discovery'){return [pscustomobject]@{Disposition='source';Rationale='The blocked-ledger entry is a source audit/frontier record, not a mathematical failure.';Confidence='medium'}}
            if($lower -match 'sandboxsearch|blockeddirection|method|insufficient|no-new-best|no new best|refut|fail|obstacle|boundary'){return [pscustomobject]@{Disposition='failure';Rationale='The entry documents a bounded method failure, negative result, or substantive inconclusive route.';Confidence='medium'}}
            return [pscustomobject]@{Disposition='failure';Rationale='The blocked-ledger entry is substantive and is conservatively retained as a legacy failure with no counter effect.';Confidence='low'}
        }
    }
    return [pscustomobject]@{Disposition='excluded_nonresearch';Rationale='No research-bearing structure was recognized.';Confidence='low'}
}

function New-LegacyRecognizedRecord {
    param([string]$ProjectDirectory,[string]$RelativePath,[string]$Kind,[string]$Locator,[string]$Title,[string]$FragmentText)
    $path=Join-Path $ProjectDirectory $RelativePath
    $fragmentSha=Get-ProjectTextSha256 -Text $FragmentText
    $suggestion=Get-LegacyDispositionSuggestion -Kind $Kind -Text $FragmentText
    return [ordered]@{
        record_id=Get-LegacyFragmentId -RelativePath $RelativePath -Locator $Locator -FragmentSha256 $fragmentSha
        record_kind=$Kind
        title=$Title
        substantive=($suggestion.Disposition -ne 'excluded_nonresearch')
        source=[ordered]@{ path=$RelativePath; locator=$Locator; file_sha256=(Get-ProjectSha256 -LiteralPath $path); fragment_sha256=$fragmentSha }
        fragment_text=$FragmentText
        disposition=$suggestion.Disposition
        disposition_rationale=$suggestion.Rationale
        mapping_confidence=$suggestion.Confidence
        duplicate_of=$null
        targets=@()
    }
}

function Get-LegacyMarkdownSections {
    param([string]$Text)
    $items=[Collections.Generic.List[object]]::new()
    $matches=[regex]::Matches($Text,'(?ms)^###\s+([^\r\n]+)\r?\n(.*?)(?=^###\s+|\z)')
    $index=0
    foreach($match in $matches){
        $index++
        $fragment=$match.Value.TrimEnd()
        $items.Add([pscustomobject]@{Locator="heading[$index]:"+$match.Groups[1].Value.Trim();Title=$match.Groups[1].Value.Trim();Text=$fragment})
    }
    return @($items)
}

function Get-LegacyMarkdownTableRows {
    param([string]$Text)
    $items=[Collections.Generic.List[object]]::new();$rowIndex=0;$dataIndex=0
    foreach($line in ($Text -split "`r?`n")){
        if(-not $line.TrimStart().StartsWith('|')){continue}
        $rowIndex++
        $cells=@($line.Trim().Trim('|').Split('|')|ForEach-Object{$_.Trim()})
        if($cells.Count -eq 0 -or (@($cells|Where-Object{$_ -notmatch '^:?-{3,}:?$'}).Count -eq 0)){continue}
        if($dataIndex -eq 0){$dataIndex++;continue}
        $items.Add([pscustomobject]@{Locator="table-row[$rowIndex]";Title=($cells[0..([Math]::Min(1,$cells.Count-1))] -join ' - ');Text=$line.Trim()})
    }
    return @($items)
}

function Get-LegacyRecognizedRecords {
    param([Parameter(Mandatory=$true)][string]$ProjectDirectory)
    $project=Resolve-MathResearchProjectDirectory -ProjectDirectory $ProjectDirectory
    $records=[Collections.Generic.List[object]]::new()
    $legacyFiles=@((Read-ImportManifest -ProjectDirectory $project.Path)|Where-Object{[string]$_.type -eq 'file' -and [string]$_.category -eq 'legacy-run'}|Sort-Object destination_relative_path)
    foreach($import in $legacyFiles){
        $relative=[string]$import.destination_relative_path
        $path=[IO.Path]::GetFullPath((Join-Path $project.Path $relative))
        if(-not (Test-ProjectPathInside -Child $path -Directory $project.Path)){throw 'Legacy import path escapes the project.'}
        if(-not (Test-Path -LiteralPath $path -PathType Leaf)){throw "Legacy imported file is missing: $relative"}
        if((Get-ProjectSha256 -LiteralPath $path) -cne [string]$import.sha256){throw "Legacy imported file hash mismatch: $relative"}
        $leaf=[IO.Path]::GetFileName($path);$stem=[IO.Path]::GetFileNameWithoutExtension($path)
        if($leaf -ieq 'metadata.json'){
            $text=[IO.File]::ReadAllText($path,[Text.UTF8Encoding]::new($false,$true))
            $title=Split-Path -Leaf (Split-Path -Parent $path)
            $records.Add((New-LegacyRecognizedRecord -ProjectDirectory $project.Path -RelativePath $relative -Kind 'artifact_metadata' -Locator 'json-root' -Title $title -FragmentText $text))
            continue
        }
        if([IO.Path]::GetExtension($path) -ine '.md'){continue}
        $kind=$null
        if($stem -match '(?i)attempt'){$kind='attempt'}
        elseif($stem -match '(?i)blocked|failure|obstacle'){$kind='blocked'}
        elseif($stem -match '(?i)source'){$kind='source'}
        elseif($stem -match '(?i)signal|sandbox'){$kind='sandbox_signal'}
        elseif($stem -match '(?i)reproduction|audit'){$kind='reproduction'}
        if($null -eq $kind){continue}
        $text=[IO.File]::ReadAllText($path,[Text.UTF8Encoding]::new($false,$true))
        $fragments=@(Get-LegacyMarkdownSections -Text $text)
        if($fragments.Count -eq 0){$fragments=@(Get-LegacyMarkdownTableRows -Text $text)}
        foreach($fragment in $fragments){$records.Add((New-LegacyRecognizedRecord -ProjectDirectory $project.Path -RelativePath $relative -Kind $kind -Locator $fragment.Locator -Title $fragment.Title -FragmentText $fragment.Text))}
    }
    return @($records)
}

function Get-LegacyImportState {
    param([string]$ProjectDirectory)
    $manifestPath=Join-Path $ProjectDirectory 'manifests\import-manifest.jsonl'
    $legacy=@((Read-ImportManifest -ProjectDirectory $ProjectDirectory)|Where-Object{[string]$_.type -eq 'file' -and [string]$_.category -eq 'legacy-run'})
    return [pscustomobject]@{HasLegacy=($legacy.Count -gt 0);LegacyFileCount=$legacy.Count;ImportManifestSha256=(Get-ProjectSha256 -LiteralPath $manifestPath)}
}

function Analyze-MathResearchLegacyArchive {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$ProjectDirectory)
    $project=Resolve-MathResearchProjectDirectory -ProjectDirectory $ProjectDirectory
    $state=Get-LegacyImportState -ProjectDirectory $project.Path
    $records=@()
    if($state.HasLegacy){$records=@(Get-LegacyRecognizedRecords -ProjectDirectory $project.Path)}
    $counts=[ordered]@{}
    foreach($name in $script:LegacyDispositions){$counts[$name]=@($records|Where-Object{[string]$_.disposition -eq $name}).Count}
    return [ordered]@{schema=$script:LegacySemanticSchema;project_id=[string]$project.Project.project_id;import_manifest_sha256=$state.ImportManifestSha256;generated_at_utc=[DateTime]::UtcNow.ToString('o');review_status='suggested';recognized_count=$records.Count;records=$records;disposition_counts=$counts}
}

function Test-MathResearchLegacyFailureRecord {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$FailureRecordFile)
    $read=Read-ProjectJsonFile -LiteralPath $FailureRecordFile -Label 'legacy failure record';$v=$read.Value
    foreach($key in @('schema','record_type','origin','legacy_record_id','route_id','decision_problem','failed_step','failure_reason','excluded_scope','not_excluded_scope','source_locator','mapping_confidence','counter_effect','reopen_conditions')){if(-not $v.Contains($key)){throw "Legacy failure record is missing '$key'."}}
    if([int]$v.schema -ne 1 -or [string]$v.record_type -cne 'legacy_failure' -or [string]$v.origin -cne 'legacy_import'){throw 'Legacy failure identity is invalid.'}
    if([string]$v.counter_effect -cne 'none'){throw 'Legacy failure counter_effect must be none.'}
    if([string]$v.mapping_confidence -notin @('low','medium','high')){throw 'Legacy failure mapping_confidence is invalid.'}
    foreach($key in @('path','locator','file_sha256','fragment_sha256')){if(-not $v.source_locator.Contains($key)){throw "Legacy failure source locator is missing '$key'."}}
    if(@($v.reopen_conditions).Count -lt 1){throw 'Legacy failure requires a falsifiable reopen condition.'}
    return [pscustomobject]@{Ok=$true;Sha256=$read.Sha256;Value=$v}
}

function Get-LegacyTargetSpecs {
    param([Collections.IDictionary]$Record)
    $id=[string]$Record.record_id
    switch([string]$Record.disposition){
        'attempt' { return @([ordered]@{path="attempts\legacy\$id.md";kind='markdown'}) }
        'failure' { return @([ordered]@{path="failures\$id.md";kind='markdown'},[ordered]@{path="failures\$id.legacy-failure.json";kind='legacy_failure'}) }
        'partial_evidence' { return @([ordered]@{path="evidence\partial\$id.md";kind='markdown'}) }
        'exploratory_evidence' { return @([ordered]@{path="evidence\exploratory\$id.md";kind='markdown'}) }
        'source' { return @([ordered]@{path="sources\$id.md";kind='markdown'},[ordered]@{path="evidence\partial\$id-source-index.md";kind='markdown'}) }
        'operational_blocker' { return @([ordered]@{path="cycles\legacy\blockers\$id.md";kind='markdown'}) }
        default { return @() }
    }
}

function Get-LegacyMarkdownRecordText {
    param([Collections.IDictionary]$Record)
    $source=$Record.source
    $title=[string]$Record.title;$fragment=([string]$Record.fragment_text).TrimEnd();$maxTildes=0
    foreach($match in [regex]::Matches(($title+"`n"+$fragment),'~+')){if($match.Length -gt $maxTildes){$maxTildes=$match.Length}}
    $fence='~' * [Math]::Max(3,$maxTildes+1)
    return "# Legacy record: $($Record.record_id)`n`n- origin: legacy_import`n- legacy_record_id: $($Record.record_id)`n- disposition: $($Record.disposition)`n- mapping_confidence: $($Record.mapping_confidence)`n- source: ``$($source.path)```n- locator: ``$($source.locator)```n- source_sha256: ``$($source.file_sha256)```n- fragment_sha256: ``$($source.fragment_sha256)```n- counter_effect: none`n`n## Legacy title`n`n$fence`n$title`n$fence`n`n## 归档理由`n`n$($Record.disposition_rationale)`n`n## 原始记录`n`n$fence`n$fragment`n$fence`n"
}

function New-LegacyFailureObject {
    param([Collections.IDictionary]$Record)
    $suffix=([string]$Record.record_id).Substring(7)
    return [ordered]@{schema=1;record_type='legacy_failure';origin='legacy_import';legacy_record_id=[string]$Record.record_id;route_id="legacy-route-$suffix";decision_problem=[string]$Record.title;failed_step='The documented legacy route stopped at its recorded boundary.';failure_reason=[string]$Record.disposition_rationale;excluded_scope='Only the documented legacy method, finite bounds, and stated assumptions are ruled out.';not_excluded_scope='The full research problem, other route families, and stronger resources are not ruled out.';source_locator=$Record.source;mapping_confidence=[string]$Record.mapping_confidence;counter_effect='none';reopen_conditions=@([ordered]@{id="legacy-reopen-$suffix";description='Provide new evidence that directly falsifies the recorded stop reason or crosses its stated bound.'})}
}

function Assert-ReviewedLegacyManifest {
    param([Collections.IDictionary]$Manifest,[string]$ProjectDirectory)
    $project=Resolve-MathResearchProjectDirectory -ProjectDirectory $ProjectDirectory
    $state=Get-LegacyImportState -ProjectDirectory $project.Path
    if([int]$Manifest.schema -ne $script:LegacySemanticSchema -or [string]$Manifest.project_id -cne [string]$project.Project.project_id){throw 'Legacy semantic manifest identity mismatch.'}
    if([string]$Manifest.import_manifest_sha256 -cne $state.ImportManifestSha256){throw 'Legacy semantic manifest is bound to a different import manifest.'}
    if([string]$Manifest.review_status -cne 'approved'){Throw-LegacySemanticIncomplete 'semantic manifest has not been approved'}
    $current=@(Get-LegacyRecognizedRecords -ProjectDirectory $project.Path);$byId=@{}
    foreach($record in $current){$byId[[string]$record.record_id]=$record}
    if(@($Manifest.records).Count -ne $current.Count){Throw-LegacySemanticIncomplete 'recognized record coverage is not 100%'}
    $seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($record in @($Manifest.records)){
        $id=[string]$record.record_id
        if(-not $seen.Add($id) -or -not $byId.ContainsKey($id)){Throw-LegacySemanticIncomplete "record set mismatch at $id"}
        $live=$byId[$id]
        if([string]$record.source.file_sha256 -cne [string]$live.source.file_sha256 -or [string]$record.source.fragment_sha256 -cne [string]$live.source.fragment_sha256){Throw-LegacySemanticIncomplete "source hash mismatch at $id"}
        if([string]$record.disposition -notin $script:LegacyDispositions){Throw-LegacySemanticIncomplete "missing or invalid disposition at $id"}
        if([bool]$record.substantive -and [string]$record.disposition -eq 'excluded_nonresearch'){Throw-LegacySemanticIncomplete "substantive record cannot be excluded at $id"}
        if([string]$record.disposition -eq 'excluded_nonresearch' -and [string]::IsNullOrWhiteSpace([string]$record.disposition_rationale)){Throw-LegacySemanticIncomplete "non-research exclusion lacks a reason at $id"}
        if([string]$record.disposition -eq 'duplicate' -and ([string]::IsNullOrWhiteSpace([string]$record.duplicate_of) -or -not $byId.ContainsKey([string]$record.duplicate_of))){Throw-LegacySemanticIncomplete "duplicate target is invalid at $id"}
        $record.fragment_text=$live.fragment_text
    }
    return [pscustomobject]@{Project=$project;State=$state;Records=@($Manifest.records)}
}

function Apply-MathResearchLegacyMigration {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$ProjectDirectory,[Parameter(Mandatory=$true)][string]$ManifestFile,[string]$CurrentConclusion='Legacy material migrated; migration alone promotes no candidate and changes no baseline.')
    $manifestRead=Read-ProjectJsonFile -LiteralPath $ManifestFile -Label 'reviewed legacy semantic manifest';$checked=Assert-ReviewedLegacyManifest -Manifest $manifestRead.Value -ProjectDirectory $ProjectDirectory
    $project=$checked.Project;$stage=Join-Path $project.Path ('.legacy-migration-stage-'+[guid]::NewGuid().ToString('N'))
    $checkpointPath=Join-Path $project.Path 'state\checkpoint.json'
    $replaceable=@{};$existingManifestPath=Join-Path $project.Path 'manifests\legacy-semantic-manifest.json'
    if(Test-Path -LiteralPath $existingManifestPath -PathType Leaf){
        $existingManifest=Read-ProjectJsonFile -LiteralPath $existingManifestPath -Label 'existing legacy semantic manifest'
        foreach($oldRecord in @($existingManifest.Value.records)){foreach($oldTarget in @($oldRecord.targets)){$replaceable[[string]$oldTarget.path]=[string]$oldTarget.sha256}}
        $replaceable['manifests\legacy-semantic-manifest.json']=$existingManifest.Sha256
    }
    try{
        New-Item -ItemType Directory -Path $stage|Out-Null
        $finalRecords=[Collections.Generic.List[object]]::new();$routeEntries=[Collections.Generic.List[object]]::new()
        foreach($record in $checked.Records){
            $targets=[Collections.Generic.List[object]]::new()
            foreach($spec in @(Get-LegacyTargetSpecs -Record $record)){
                $target=Join-Path $stage ([string]$spec.path)
                if([string]$spec.kind -eq 'legacy_failure'){$text=(New-LegacyFailureObject -Record $record|ConvertTo-Json -Depth 32)+"`n"}else{$text=Get-LegacyMarkdownRecordText -Record $record}
                Write-ProjectUtf8New -LiteralPath $target -Text $text
                if([string]$spec.kind -eq 'legacy_failure'){Test-MathResearchLegacyFailureRecord -FailureRecordFile $target|Out-Null}
                $targets.Add([ordered]@{path=[string]$spec.path;sha256=(Get-ProjectSha256 -LiteralPath $target)})
            }
            $record.targets=@($targets);$finalRecords.Add($record)
            if([string]$record.disposition -in @('failure','operational_blocker')){
                $suffix=([string]$record.record_id).Substring(7);$status=if([string]$record.disposition -eq 'failure'){'frozen'}else{'blocked'}
                $routeEntries.Add([ordered]@{route_id="legacy-route-$suffix";route_family_id="legacy-family-$suffix";retry_fingerprint_sha256=[string]$record.source.fragment_sha256;status=$status;origin='legacy_import';migration_record_id=[string]$record.record_id;counter_effect='none';reopen_condition_ids=@("legacy-reopen-$suffix");seen_evidence_sha256=@()})
            }
        }
        $counts=[ordered]@{};foreach($name in $script:LegacyDispositions){$counts[$name]=@($finalRecords|Where-Object{[string]$_.disposition -eq $name}).Count}
        $finalManifest=[ordered]@{schema=$script:LegacySemanticSchema;project_id=[string]$project.Project.project_id;import_manifest_sha256=$checked.State.ImportManifestSha256;generated_at_utc=[string]$manifestRead.Value.generated_at_utc;applied_at_utc=[DateTime]::UtcNow.ToString('o');review_status='approved';recognized_count=$finalRecords.Count;disposed_count=$finalRecords.Count;unresolved_substantive_count=0;records=@($finalRecords);disposition_counts=$counts}
        $manifestStage=Join-Path $stage 'manifests\legacy-semantic-manifest.json';Write-ProjectUtf8New -LiteralPath $manifestStage -Text (($finalManifest|ConvertTo-Json -Depth 64)+"`n")
        $registry=(Read-ProjectJsonFile -LiteralPath (Join-Path $project.Path 'state\route-registry.json') -Label 'route registry').Value
        $kept=@($registry.routes|Where-Object{-not ($_.Contains('origin') -and [string]$_.origin -eq 'legacy_import')});$registry.routes=@($kept)+@($routeEntries)
        Write-ProjectUtf8New -LiteralPath (Join-Path $stage 'state\route-registry.json') -Text (($registry|ConvertTo-Json -Depth 64)+"`n")
        $summary="- migration_status: complete`n- recognized: $($finalRecords.Count)`n- unresolved_substantive: 0`n- current_conclusion: $CurrentConclusion"
        foreach($name in @('CURRENT','RESULTS','ROUTES','EVIDENCE')){
            $sourcePath=Join-Path $project.Path "state\$name.md";$copyPath=Join-Path $stage "state\$name.md";New-Item -ItemType Directory -Path (Split-Path -Parent $copyPath) -Force|Out-Null;Copy-Item -LiteralPath $sourcePath -Destination $copyPath
            $body=switch($name){'CURRENT'{"## Legacy semantic archive`n`n$summary"};'RESULTS'{"## Legacy imported results`n`nMigration promotes no mathematical conclusion and changes no baseline. Attempts: $($counts.attempt); failures: $($counts.failure)."};'ROUTES'{"## Legacy route boundaries`n`nFrozen failures: $($counts.failure). Operational blockers: $($counts.operational_blocker). Every route retains counter_effect=none and a falsifiable reopen condition."};'EVIDENCE'{"## Legacy evidence coverage`n`nSources: $($counts.source). Partial: $($counts.partial_evidence). Exploratory: $($counts.exploratory_evidence). Coverage: $($finalRecords.Count)/$($finalRecords.Count)."}}
            Set-GeneratedMarkdownBlock -LiteralPath $copyPath -Name 'legacy-semantic-archive' -Body $body
        }
        foreach($file in @(Get-ChildItem -LiteralPath $stage -Recurse -File|Where-Object{$_.FullName -notmatch '\\state\\(CURRENT|RESULTS|ROUTES|EVIDENCE)\.md$' -and $_.FullName -notmatch '\\state\\route-registry\.json$'})){
            $relative=[IO.Path]::GetRelativePath($stage,$file.FullName).Replace('/','\');$destination=Join-Path $project.Path $relative
            if(Test-Path -LiteralPath $destination){$currentHash=Get-ProjectSha256 -LiteralPath $destination;$stagedHash=Get-ProjectSha256 -LiteralPath $file.FullName;if($currentHash -cne $stagedHash -and (-not $replaceable.ContainsKey($relative) -or [string]$replaceable[$relative] -cne $currentHash)){throw "Legacy migration destination conflict: $relative"}}
        }
        $checkpoint=(Read-ProjectJsonFile -LiteralPath $checkpointPath -Label 'checkpoint.json').Value;$checkpoint.migration=[ordered]@{status='applying';manifest_path='manifests\legacy-semantic-manifest.json';manifest_sha256=$null;recognized_count=$finalRecords.Count;disposed_count=0;unresolved_substantive_count=0};$checkpoint.dirty=$true;$checkpoint.recovery_required=$true;$checkpoint.updated_at_utc=[DateTime]::UtcNow.ToString('o');Write-ProjectUtf8Atomic -LiteralPath $checkpointPath -Text (($checkpoint|ConvertTo-Json -Depth 64)+"`n")
        foreach($file in @(Get-ChildItem -LiteralPath $stage -Recurse -File)){
            $relative=[IO.Path]::GetRelativePath($stage,$file.FullName).Replace('/','\');$destination=Join-Path $project.Path $relative
            if($relative -in @('state\CURRENT.md','state\RESULTS.md','state\ROUTES.md','state\EVIDENCE.md','state\route-registry.json')){Write-ProjectUtf8Atomic -LiteralPath $destination -Text ([IO.File]::ReadAllText($file.FullName,[Text.UTF8Encoding]::new($false,$true)))}
            elseif(-not (Test-Path -LiteralPath $destination)){New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force|Out-Null;[IO.File]::Copy($file.FullName,$destination,$false)}
            elseif((Get-ProjectSha256 -LiteralPath $destination) -cne (Get-ProjectSha256 -LiteralPath $file.FullName)){Write-ProjectUtf8Atomic -LiteralPath $destination -Text ([IO.File]::ReadAllText($file.FullName,[Text.UTF8Encoding]::new($false,$true)))}
        }
        foreach($relative in @('state\CURRENT.md','state\RESULTS.md','state\ROUTES.md','state\EVIDENCE.md','state\route-registry.json')){
            $stagedMutable=Join-Path $stage $relative
            if(-not (Test-Path -LiteralPath $stagedMutable -PathType Leaf)){throw "Legacy migration staging omitted $relative"}
            Write-ProjectUtf8Atomic -LiteralPath (Join-Path $project.Path $relative) -Text ([IO.File]::ReadAllText($stagedMutable,[Text.UTF8Encoding]::new($false,$true)))
        }
        $manifestPath=Join-Path $project.Path 'manifests\legacy-semantic-manifest.json';$checkpoint.migration.status='complete';$checkpoint.migration.manifest_sha256=Get-ProjectSha256 -LiteralPath $manifestPath;$checkpoint.migration.disposed_count=$finalRecords.Count;if([string]$checkpoint.project_status -eq 'migration_required'){$checkpoint.project_status='paused'};$checkpoint.dirty=$false;$checkpoint.recovery_required=$false;$checkpoint.updated_at_utc=[DateTime]::UtcNow.ToString('o');Write-ProjectUtf8Atomic -LiteralPath $checkpointPath -Text (($checkpoint|ConvertTo-Json -Depth 64)+"`n")
        $projectJsonPath=Join-Path $project.Path 'project.json';$projectJson=(Read-ProjectJsonFile -LiteralPath $projectJsonPath -Label 'project.json').Value;if([string]$projectJson.status -eq 'migration_required'){$projectJson.status='paused'};$projectJson.updated_at_utc=[DateTime]::UtcNow.ToString('o');Write-ProjectUtf8Atomic -LiteralPath $projectJsonPath -Text (($projectJson|ConvertTo-Json -Depth 64)+"`n")
        return Verify-MathResearchLegacySemanticArchive -ProjectDirectory $project.Path
    } finally {if(Test-Path -LiteralPath $stage){Remove-Item -LiteralPath $stage -Recurse -Force}}
}

function Verify-MathResearchLegacySemanticArchive {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$ProjectDirectory)
    $project=Resolve-MathResearchProjectDirectory -ProjectDirectory $ProjectDirectory;$state=Get-LegacyImportState -ProjectDirectory $project.Path
    if(-not $state.HasLegacy){return [pscustomobject]@{Ok=$true;Required=$false;Status='not_required';Recognized=0;Disposed=0;UnresolvedSubstantive=0;HashMismatches=0}}
    $manifestPath=Join-Path $project.Path 'manifests\legacy-semantic-manifest.json'
    if(-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)){Throw-LegacySemanticIncomplete 'legacy-semantic-manifest.json is missing'}
    $read=Read-ProjectJsonFile -LiteralPath $manifestPath -Label 'legacy semantic manifest';$checked=Assert-ReviewedLegacyManifest -Manifest $read.Value -ProjectDirectory $project.Path
    $routeRegistry=(Read-ProjectJsonFile -LiteralPath (Join-Path $project.Path 'state\route-registry.json') -Label 'route registry').Value
    foreach($record in $checked.Records){
        foreach($target in @($record.targets)){
            $path=[IO.Path]::GetFullPath((Join-Path $project.Path ([string]$target.path)))
            if(-not (Test-ProjectPathInside -Child $path -Directory $project.Path) -or -not (Test-Path -LiteralPath $path -PathType Leaf)){Throw-LegacySemanticIncomplete "canonical target missing for $($record.record_id)"}
            if((Get-ProjectSha256 -LiteralPath $path) -cne [string]$target.sha256){Throw-LegacySemanticIncomplete "canonical target hash mismatch for $($record.record_id)"}
        }
        if([string]$record.disposition -in @('failure','operational_blocker')){if(@($routeRegistry.routes|Where-Object{$_.Contains('migration_record_id') -and [string]$_.migration_record_id -eq [string]$record.record_id}).Count -ne 1){Throw-LegacySemanticIncomplete "route index mismatch for $($record.record_id)"}}
    }
    foreach($name in @('CURRENT','RESULTS','ROUTES','EVIDENCE')){if(-not ([IO.File]::ReadAllText((Join-Path $project.Path "state\$name.md"),[Text.UTF8Encoding]::new($false,$true)).Contains('<!-- math-research-generated-legacy-semantic-archive:start -->'))){Throw-LegacySemanticIncomplete "state/$name.md lacks the legacy semantic index"}}
    $checkpoint=(Read-ProjectJsonFile -LiteralPath (Join-Path $project.Path 'state\checkpoint.json') -Label 'checkpoint.json').Value
    if(-not $checkpoint.Contains('migration') -or [string]$checkpoint.migration.status -cne 'complete' -or [string]$checkpoint.migration.manifest_sha256 -cne $read.Sha256){Throw-LegacySemanticIncomplete 'checkpoint migration state or manifest hash is inconsistent'}
    return [pscustomobject]@{Ok=$true;Required=$true;Status='complete';Recognized=@($checked.Records).Count;Disposed=@($checked.Records).Count;UnresolvedSubstantive=0;HashMismatches=0;ManifestSha256=$read.Sha256;DispositionCounts=$read.Value.disposition_counts}
}
