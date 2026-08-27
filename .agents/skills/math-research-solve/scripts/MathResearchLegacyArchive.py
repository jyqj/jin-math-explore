#!/usr/bin/env python3
"""Native reviewed semantic archive for imported legacy research records."""

from __future__ import annotations

import json
import re
import shutil
import uuid
from pathlib import Path
from typing import Any

from MathResearchProjectArchiveV2 import (
    ProjectArchiveError, atomic_text, compact, generated_block, read_json,
    resolve_project, safe_inside, sha_bytes, sha_file, utc_now,
)
from math_research_control_primitives import strict_json_loads

DISPOSITIONS=("attempt","failure","partial_evidence","exploratory_evidence","source","operational_blocker","duplicate","excluded_nonresearch")


def incomplete(detail: str) -> None: raise ProjectArchiveError(f"legacy_semantic_archive_incomplete: {detail}")


def import_records(project: Path) -> list[dict[str,Any]]:
    path=project/"manifests/import-manifest.jsonl"; records=[]
    for number,line in enumerate(path.read_text(encoding="utf-8",errors="strict").splitlines(),1):
        if not line.strip(): raise ProjectArchiveError(f"blank import manifest line {number}")
        value=strict_json_loads(line)
        if isinstance(value,dict): records.append(value)
    return records


def import_state(project: Path) -> dict[str,Any]:
    legacy=[x for x in import_records(project) if x.get("type")=="file" and x.get("category")=="legacy-run"]
    return {"has_legacy":bool(legacy),"legacy_file_count":len(legacy),"import_manifest_sha256":sha_file(project/"manifests/import-manifest.jsonl")}


def suggestion(kind: str, text: str) -> tuple[str,str,str]:
    lower=text.casefold()
    if kind=="attempt": return "attempt","Legacy attempt ledger entry.","high"
    if kind=="source": return "source","Legacy source extraction or source audit.","high"
    if kind=="sandbox_signal": return "exploratory_evidence","Bounded exploratory or sandbox signal; it is not promoted as a mathematical conclusion.","high"
    if kind=="reproduction": return "partial_evidence","Reproduction or audit evidence with an explicit finite or unresolved boundary.","high"
    if kind=="artifact_metadata":
        if re.search(r"sourceextract|source[-_ ]extract|sourcediscoveryfrontier|source[-_ ]discovery",lower): return "source","Artifact metadata describes a source extraction, source discovery frontier, or source audit.","high"
        if re.search(r"sandbox(search|_search)|sandbox-only|exploratory",lower): return "exploratory_evidence","Artifact metadata describes bounded exploratory work.","medium"
        return "partial_evidence","Artifact metadata preserves evidence and limitations without promoting a result.","medium"
    if kind=="blocked":
        if re.search(r"tool.{0,40}(unavailable|missing|not available)|maple.{0,40}(unavailable|not available|absence)|bootstrap|initiali[sz]ation|ledger.{0,20}missing|no[- ]new[- ]object|environment|path.{0,20}missing",lower): return "operational_blocker","The stop condition is operational or initialization-related, not a mathematical counterexample.","medium"
        if re.search(r"sourceextractaudit|sourcediscoveryfrontier|source extract|source discovery",lower): return "source","The blocked-ledger entry is a source audit/frontier record, not a mathematical failure.","medium"
        confidence="medium" if re.search(r"sandboxsearch|blockeddirection|method|insufficient|no-new-best|no new best|refut|fail|obstacle|boundary",lower) else "low"
        return "failure","The entry documents a bounded method failure, negative result, or substantive inconclusive route." if confidence=="medium" else "The blocked-ledger entry is substantive and is conservatively retained as a legacy failure with no counter effect.",confidence
    return "excluded_nonresearch","No research-bearing structure was recognized.","low"


def recognized_record(project: Path, relative: str, kind: str, locator: str, title: str, fragment: str) -> dict[str,Any]:
    fragment_hash=sha_bytes(fragment.encode("utf-8")); record_id="legacy-"+sha_bytes((relative.casefold()+"\n"+locator+"\n"+fragment_hash).encode("utf-8"))[:20]; disposition,rationale,confidence=suggestion(kind,fragment)
    return {"record_id":record_id,"record_kind":kind,"title":title,"substantive":disposition!="excluded_nonresearch","source":{"path":relative,"locator":locator,"file_sha256":sha_file(project/relative),"fragment_sha256":fragment_hash},"fragment_text":fragment,"disposition":disposition,"disposition_rationale":rationale,"mapping_confidence":confidence,"duplicate_of":None,"targets":[]}


def recognize(project_directory: Path) -> list[dict[str,Any]]:
    project=resolve_project(project_directory)["path"]; result=[]
    for imported in sorted((x for x in import_records(project) if x.get("type")=="file" and x.get("category")=="legacy-run"),key=lambda x:x["destination_relative_path"]):
        relative=imported["destination_relative_path"]; path=project/relative
        if not safe_inside(path,project) or not path.is_file() or sha_file(path)!=imported["sha256"]: raise ProjectArchiveError("legacy imported file is absent, escaped, or changed")
        if path.name.casefold()=="metadata.json":
            text=path.read_text(encoding="utf-8",errors="strict"); result.append(recognized_record(project,relative,"artifact_metadata","json-root",path.parent.name,text)); continue
        if path.suffix.casefold()!=".md": continue
        stem=path.stem.casefold(); kind="attempt" if "attempt" in stem else "blocked" if re.search(r"blocked|failure|obstacle",stem) else "source" if "source" in stem else "sandbox_signal" if re.search(r"signal|sandbox",stem) else "reproduction" if re.search(r"reproduction|audit",stem) else None
        if kind is None: continue
        text=path.read_text(encoding="utf-8",errors="strict"); matches=list(re.finditer(r"(?ms)^###\s+([^\r\n]+)\r?\n(.*?)(?=^###\s+|\Z)",text))
        if matches:
            fragments=[(f"heading[{index}]:{match.group(1).strip()}",match.group(1).strip(),match.group(0).rstrip()) for index,match in enumerate(matches,1)]
        else:
            fragments=[]; row_index=0; data_index=0
            for line in text.splitlines():
                if not line.lstrip().startswith("|"): continue
                row_index+=1; cells=[x.strip() for x in line.strip().strip("|").split("|")]
                if not cells or all(re.fullmatch(r":?-{3,}:?",x) for x in cells): continue
                if data_index==0: data_index+=1; continue
                fragments.append((f"table-row[{row_index}]"," - ".join(cells[:2]),line.strip()))
        for locator,title,fragment in fragments: result.append(recognized_record(project,relative,kind,locator,title,fragment))
    return result


def analyze(project_directory: Path) -> dict[str,Any]:
    project=resolve_project(project_directory); state=import_state(project["path"]); records=recognize(project["path"]) if state["has_legacy"] else []; counts={name:sum(x["disposition"]==name for x in records) for name in DISPOSITIONS}
    return {"schema":1,"project_id":project["project"]["project_id"],"import_manifest_sha256":state["import_manifest_sha256"],"generated_at_utc":utc_now(),"review_status":"suggested","recognized_count":len(records),"records":records,"disposition_counts":counts}


def legacy_failure(path: Path) -> dict[str,Any]:
    value=read_json(path,"legacy failure record"); required={"schema","record_type","origin","legacy_record_id","route_id","decision_problem","failed_step","failure_reason","excluded_scope","not_excluded_scope","source_locator","mapping_confidence","counter_effect","reopen_conditions"};
    if not required<=set(value) or value["schema"]!=1 or value["record_type"]!="legacy_failure" or value["origin"]!="legacy_import" or value["counter_effect"]!="none" or value["mapping_confidence"] not in {"low","medium","high"}: raise ProjectArchiveError("legacy failure identity is invalid")
    if not {"path","locator","file_sha256","fragment_sha256"}<=set(value["source_locator"]) or not value["reopen_conditions"]: raise ProjectArchiveError("legacy failure source/reopen contract is invalid")
    return {"Ok":True,"Sha256":sha_file(path),"Value":value}


def reviewed(manifest: dict[str,Any], project_directory: Path) -> tuple[dict[str,Any],dict[str,Any],list[dict[str,Any]]]:
    project=resolve_project(project_directory); state=import_state(project["path"])
    if manifest.get("schema")!=1 or manifest.get("project_id")!=project["project"]["project_id"] or manifest.get("import_manifest_sha256")!=state["import_manifest_sha256"]: raise ProjectArchiveError("legacy semantic manifest identity/binding mismatches")
    if manifest.get("review_status")!="approved": incomplete("semantic manifest has not been approved")
    current=recognize(project["path"]); by_id={x["record_id"]:x for x in current}; records=manifest.get("records",[])
    if len(records)!=len(current): incomplete("recognized record coverage is not 100%")
    seen=set()
    for record in records:
        identity=record.get("record_id"); live=by_id.get(identity)
        if identity in seen or live is None: incomplete(f"record set mismatch at {identity}")
        seen.add(identity)
        if record.get("source",{}).get("file_sha256")!=live["source"]["file_sha256"] or record.get("source",{}).get("fragment_sha256")!=live["source"]["fragment_sha256"]: incomplete(f"source hash mismatch at {identity}")
        if record.get("disposition") not in DISPOSITIONS: incomplete(f"invalid disposition at {identity}")
        if record.get("substantive") and record["disposition"]=="excluded_nonresearch": incomplete(f"substantive record cannot be excluded at {identity}")
        if record["disposition"]=="duplicate" and record.get("duplicate_of") not in by_id: incomplete(f"duplicate target is invalid at {identity}")
        record["fragment_text"]=live["fragment_text"]
    return project,state,records


def target_specs(record: dict[str,Any]) -> list[tuple[str,str]]:
    identity=record["record_id"]; disposition=record["disposition"]
    return {"attempt":[(f"attempts/legacy/{identity}.md","markdown")],"failure":[(f"failures/{identity}.md","markdown"),(f"failures/{identity}.legacy-failure.json","legacy_failure")],"partial_evidence":[(f"evidence/partial/{identity}.md","markdown")],"exploratory_evidence":[(f"evidence/exploratory/{identity}.md","markdown")],"source":[(f"sources/{identity}.md","markdown"),(f"evidence/partial/{identity}-source-index.md","markdown")],"operational_blocker":[(f"cycles/legacy/blockers/{identity}.md","markdown")]}.get(disposition,[])


def record_markdown(record: dict[str,Any]) -> str:
    source=record["source"]; title=record["title"]; fragment=record["fragment_text"].rstrip(); max_tildes=max([len(x) for x in re.findall(r"~+",title+"\n"+fragment)]+[2]); fence="~"*max(3,max_tildes+1)
    return f"# Legacy record: {record['record_id']}\n\n- origin: legacy_import\n- legacy_record_id: {record['record_id']}\n- disposition: {record['disposition']}\n- mapping_confidence: {record['mapping_confidence']}\n- source: `{source['path']}`\n- locator: `{source['locator']}`\n- source_sha256: `{source['file_sha256']}`\n- fragment_sha256: `{source['fragment_sha256']}`\n- counter_effect: none\n\n## Legacy title\n\n{fence}\n{title}\n{fence}\n\n## 归档理由\n\n{record['disposition_rationale']}\n\n## 原始记录\n\n{fence}\n{fragment}\n{fence}\n"


def failure_object(record: dict[str,Any]) -> dict[str,Any]:
    suffix=record["record_id"][7:]
    return {"schema":1,"record_type":"legacy_failure","origin":"legacy_import","legacy_record_id":record["record_id"],"route_id":f"legacy-route-{suffix}","decision_problem":record["title"],"failed_step":"The documented legacy route stopped at its recorded boundary.","failure_reason":record["disposition_rationale"],"excluded_scope":"Only the documented legacy method, finite bounds, and stated assumptions are ruled out.","not_excluded_scope":"The full research problem, other route families, and stronger resources are not ruled out.","source_locator":record["source"],"mapping_confidence":record["mapping_confidence"],"counter_effect":"none","reopen_conditions":[{"id":f"legacy-reopen-{suffix}","description":"Provide new evidence that directly falsifies the recorded stop reason or crosses its stated bound."}]}


def apply(project_directory: Path, manifest_file: Path, current_conclusion: str="Legacy material migrated; migration alone promotes no candidate and changes no baseline.") -> dict[str,Any]:
    manifest=read_json(manifest_file,"reviewed legacy semantic manifest"); project,state,records=reviewed(manifest,project_directory); root=project["path"]; stage=root/f".legacy-migration-stage-{uuid.uuid4().hex}"; checkpoint_path=root/"state/checkpoint.json"; stage.mkdir(); final=[]; route_entries=[]
    try:
        for source_record in records:
            record=dict(source_record); targets=[]
            for relative,kind in target_specs(record):
                target=stage/relative; target.parent.mkdir(parents=True,exist_ok=True); text=json.dumps(failure_object(record),ensure_ascii=False,indent=2)+"\n" if kind=="legacy_failure" else record_markdown(record); atomic_text(target,text,new=True)
                if kind=="legacy_failure": legacy_failure(target)
                targets.append({"path":relative,"sha256":sha_file(target)})
            record["targets"]=targets; final.append(record)
            if record["disposition"] in {"failure","operational_blocker"}:
                suffix=record["record_id"][7:]; route_entries.append({"route_id":f"legacy-route-{suffix}","route_family_id":f"legacy-family-{suffix}","retry_fingerprint_sha256":record["source"]["fragment_sha256"],"status":"frozen" if record["disposition"]=="failure" else "blocked","origin":"legacy_import","migration_record_id":record["record_id"],"counter_effect":"none","reopen_condition_ids":[f"legacy-reopen-{suffix}"],"seen_evidence_sha256":[]})
        counts={name:sum(x["disposition"]==name for x in final) for name in DISPOSITIONS}; final_manifest={"schema":1,"project_id":project["project"]["project_id"],"import_manifest_sha256":state["import_manifest_sha256"],"generated_at_utc":manifest["generated_at_utc"],"applied_at_utc":utc_now(),"review_status":"approved","recognized_count":len(final),"disposed_count":len(final),"unresolved_substantive_count":0,"records":final,"disposition_counts":counts}; (stage/"manifests").mkdir(); atomic_text(stage/"manifests/legacy-semantic-manifest.json",json.dumps(final_manifest,ensure_ascii=False,indent=2)+"\n",new=True)
        registry=read_json(root/"state/route-registry.json","route registry"); registry["routes"]=[x for x in registry.get("routes",[]) if x.get("origin")!="legacy_import"]+route_entries; (stage/"state").mkdir(); atomic_text(stage/"state/route-registry.json",json.dumps(registry,ensure_ascii=False,indent=2)+"\n",new=True)
        summary=f"- migration_status: complete\n- recognized: {len(final)}\n- unresolved_substantive: 0\n- current_conclusion: {current_conclusion}"
        bodies={"CURRENT":f"## Legacy semantic archive\n\n{summary}","RESULTS":f"## Legacy imported results\n\nMigration promotes no mathematical conclusion and changes no baseline. Attempts: {counts['attempt']}; failures: {counts['failure']}.","ROUTES":f"## Legacy route boundaries\n\nFrozen failures: {counts['failure']}. Operational blockers: {counts['operational_blocker']}. Every route retains counter_effect=none and a falsifiable reopen condition.","EVIDENCE":f"## Legacy evidence coverage\n\nSources: {counts['source']}. Partial: {counts['partial_evidence']}. Exploratory: {counts['exploratory_evidence']}. Coverage: {len(final)}/{len(final)}."}
        for name,body in bodies.items(): target=stage/"state"/f"{name}.md"; shutil.copyfile(root/"state"/f"{name}.md",target); generated_block(target,"legacy-semantic-archive",body)
        # Preflight every immutable destination before switching checkpoint to applying.
        for item in stage.rglob("*"):
            if not item.is_file() or item.parent==stage/"state": continue
            destination=root/item.relative_to(stage)
            if destination.exists() and destination.read_bytes()!=item.read_bytes(): raise ProjectArchiveError(f"legacy migration destination conflict: {item.relative_to(stage).as_posix()}")
        checkpoint=read_json(checkpoint_path,"checkpoint.json"); checkpoint.update({"migration":{"status":"applying","manifest_path":"manifests/legacy-semantic-manifest.json","manifest_sha256":None,"recognized_count":len(final),"disposed_count":0,"unresolved_substantive_count":0},"dirty":True,"recovery_required":True,"updated_at_utc":utc_now()}); atomic_text(checkpoint_path,json.dumps(checkpoint,ensure_ascii=False,indent=2)+"\n")
        for item in stage.rglob("*"):
            if not item.is_file(): continue
            destination=root/item.relative_to(stage); destination.parent.mkdir(parents=True,exist_ok=True)
            if not destination.exists(): shutil.copyfile(item,destination)
            elif destination.read_bytes()!=item.read_bytes(): atomic_text(destination,item.read_text(encoding="utf-8",errors="strict"))
        manifest_path=root/"manifests/legacy-semantic-manifest.json"; checkpoint["migration"].update({"status":"complete","manifest_sha256":sha_file(manifest_path),"disposed_count":len(final)}); checkpoint.update({"project_status":"paused" if checkpoint.get("project_status")=="migration_required" else checkpoint.get("project_status"),"dirty":False,"recovery_required":False,"updated_at_utc":utc_now()}); atomic_text(checkpoint_path,json.dumps(checkpoint,ensure_ascii=False,indent=2)+"\n"); project_json=root/"project.json"; project_value=read_json(project_json,"project.json"); project_value.update({"status":"paused" if project_value.get("status")=="migration_required" else project_value.get("status"),"updated_at_utc":utc_now()}); atomic_text(project_json,json.dumps(project_value,ensure_ascii=False,indent=2)+"\n")
        return verify(root)
    finally: shutil.rmtree(stage,ignore_errors=True)


def verify(project_directory: Path) -> dict[str,Any]:
    project=resolve_project(project_directory); state=import_state(project["path"])
    if not state["has_legacy"]: return {"Ok":True,"Required":False,"Status":"not_required","Recognized":0,"Disposed":0,"UnresolvedSubstantive":0,"HashMismatches":0}
    manifest_path=project["path"]/"manifests/legacy-semantic-manifest.json"
    if not manifest_path.is_file(): incomplete("legacy-semantic-manifest.json is missing")
    manifest=read_json(manifest_path,"legacy semantic manifest"); _,_,records=reviewed(manifest,project["path"]); registry=read_json(project["path"]/"state/route-registry.json","route registry")
    for record in records:
        for target in record.get("targets",[]):
            path=project["path"]/target["path"]
            if not safe_inside(path,project["path"]) or not path.is_file(): incomplete(f"canonical target missing for {record['record_id']}")
            if sha_file(path)!=target["sha256"]: incomplete(f"canonical target hash mismatch for {record['record_id']}")
        if record["disposition"] in {"failure","operational_blocker"} and sum(x.get("migration_record_id")==record["record_id"] for x in registry.get("routes",[]))!=1: incomplete(f"route index mismatch for {record['record_id']}")
    marker="<!-- math-research-generated-legacy-semantic-archive:start -->"
    for name in ("CURRENT","RESULTS","ROUTES","EVIDENCE"):
        if marker not in (project["path"]/"state"/f"{name}.md").read_text(encoding="utf-8",errors="strict"): incomplete(f"state/{name}.md lacks the legacy semantic index")
    checkpoint=read_json(project["path"]/"state/checkpoint.json","checkpoint.json")
    if checkpoint.get("migration",{}).get("status")!="complete" or checkpoint["migration"].get("manifest_sha256")!=sha_file(manifest_path): incomplete("checkpoint migration state or manifest hash is inconsistent")
    return {"Ok":True,"Required":True,"Status":"complete","Recognized":len(records),"Disposed":len(records),"UnresolvedSubstantive":0,"HashMismatches":0,"ManifestSha256":sha_file(manifest_path),"DispositionCounts":manifest["disposition_counts"]}
