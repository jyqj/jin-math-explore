#!/usr/bin/env python3
"""Native project-archive foundation shared by all supported host systems."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from math_research_control_primitives import ControlIntegrityError, assert_no_symlink_chain, strict_json_loads
from math_research_control_primitives import read_signed_json

PROJECTS_RELATIVE_ROOT = Path("笔记草稿") / "公开问题的尝试"
REQUIRED_DIRECTORIES = ["contracts","state","failures","cycles","attempts","evidence/verified","evidence/partial","evidence/exploratory","sources","handoffs","runs","manifests","history/imported-workspace","history/legacy-runs","history/contract-packages"]
REQUIRED_FILES = ["README.md","project.json","state/CURRENT.md","state/RESULTS.md","state/ROUTES.md","state/EVIDENCE.md","state/checkpoint.json","state/project-events.jsonl","state/route-registry.json"]


class ProjectArchiveError(RuntimeError): pass


def require(condition: bool, message: str) -> None:
    if not condition: raise ProjectArchiveError(message)


def utc_now() -> str: return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
def sha_bytes(value: bytes) -> str: return hashlib.sha256(value).hexdigest()
def sha_file(path: Path) -> str: return sha_bytes(path.read_bytes())
def compact(value: Any) -> str: return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
def sha_event(value: Any) -> str: return sha_bytes(compact(value).encode("utf-8"))


def read_json(path: Path, label: str) -> dict[str, Any]:
    path = assert_no_symlink_chain(path)
    require(path.is_file(), f"{label} is missing")
    try: value = strict_json_loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeError, ControlIntegrityError) as exc: raise ProjectArchiveError(f"{label} is not strict JSON") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def atomic_text(path: Path, text: str, *, new: bool = False) -> None:
    path = assert_no_symlink_chain(path); parent = assert_no_symlink_chain(path.parent)
    require(parent.is_dir(), "output parent is missing")
    if new: require(not path.exists(), f"file already exists: {path}")
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
        if os.name != "nt":
            directory = os.open(parent, os.O_RDONLY); os.fsync(directory); os.close(directory)
    finally: temporary.unlink(missing_ok=True)


def safe_inside(child: Path, root: Path) -> bool:
    try: child.resolve(strict=False).relative_to(root.resolve(strict=True)); return True
    except ValueError: return False


def projects_root(vault_root: Path) -> Path:
    vault = assert_no_symlink_chain(vault_root); require(vault.is_dir(), "vault root is missing")
    return vault / PROJECTS_RELATIVE_ROOT


def resolve_project(project_directory: Path, expected_project_id: str | None = None) -> dict[str, Any]:
    path = assert_no_symlink_chain(project_directory); require(path.is_dir(), "project directory is missing")
    name = path.name; require(bool(name) and re.fullmatch(r'[^<>:"/\\|?*]+', name) is not None and not name.endswith((".", " ")), "unsafe project directory name")
    project = read_json(path / "project.json", "project.json")
    require({"schema","project_id","project_directory_name","status","active_contract","active_run"} <= set(project), "project.json is incomplete")
    require(project["schema"] == 1 and project["project_directory_name"] == name, "project schema or directory identity is invalid")
    require(isinstance(project["project_id"], str) and re.fullmatch(r"[a-z0-9][a-z0-9._-]{7,127}", project["project_id"]) is not None, "unsafe project_id")
    require(expected_project_id is None or project["project_id"] == expected_project_id, "project_id mismatch")
    return {"path": path, "name": name, "project": project, "project_json_sha256": sha_file(path / "project.json")}


def _seed(root: Path, project_id: str, name: str, problem: str) -> None:
    timestamp = utc_now()
    project = {"schema":1,"project_id":project_id,"project_directory_name":name,"title":name,"status":"paused","active_contract":None,"active_run":None,"created_at_utc":timestamp,"updated_at_utc":timestamp}
    checkpoint = {"schema":1,"project_id":project_id,"project_status":"paused","goal":{"id":None,"status":"none"},"contract":{"path":None,"sha256":None,"status":"none"},"run":{"id":None,"path":None,"status":"none"},"thread":{"id":None,"status":"none"},"last_sealed_attempt":None,"last_completed_audit":None,"attempt_count":0,"attempts_since_last_audit":0,"audit_due":False,"active_ticket":None,"dirty":False,"recovery_required":False,"migration":{"status":"not_required","manifest_path":None,"manifest_sha256":None,"recognized_count":0,"disposed_count":0,"unresolved_substantive_count":0},"last_project_event_sha256":None,"updated_at_utc":timestamp}
    files = {
        "README.md":f"# {name}\n\n## 精确问题\n\n{problem}\n\n## 最小读取顺序\n\n1. state/CURRENT.md\n2. state/checkpoint.json\n3. 活动合同与当前票据（若有）\n",
        "project.json":json.dumps(project, ensure_ascii=False, indent=2)+"\n",
        "state/CURRENT.md":"# 当前状态\n\n项目已初始化，未建立活动合同或运行。\n",
        "state/RESULTS.md":"# 已验证结果\n\n尚未登记。\n", "state/ROUTES.md":"# 路线状态\n\n尚未登记。\n", "state/EVIDENCE.md":"# 证据索引\n\n尚未登记。\n",
        "state/checkpoint.json":json.dumps(checkpoint, ensure_ascii=False, indent=2)+"\n",
        "state/route-registry.json":json.dumps({"schema":1,"project_id":project_id,"routes":[]}, ensure_ascii=False, indent=2)+"\n",
        "state/project-events.jsonl":"",
    }
    for relative, text in files.items(): atomic_text(root / relative, text, new=True)


def _copy_tree(source: Path, destination: Path, archive: Path, category: str, timestamp: str, exclusions: list[dict[str, Any]], excluded_prefixes: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    records = []
    if not source.is_dir(): return records
    assert_no_symlink_chain(source)
    for item in sorted(source.rglob("*")):
        if not item.is_file(): continue
        assert_no_symlink_chain(item); relative = item.relative_to(source); posix = relative.as_posix()
        skip = any(posix.casefold() == x.casefold() or posix.casefold().startswith(x.casefold().rstrip("/")+"/") for x in excluded_prefixes)
        cache = any(part in {"__pycache__",".pytest_cache",".mypy_cache",".ruff_cache"} for part in relative.parts) or item.suffix.casefold() in {".pyc",".pyo"}
        if skip or cache:
            exclusions.append({"type":"excluded","source_path":str(item),"rule":"import-exclusion","reason":"excluded Skill-development subtree" if skip else "regenerable cache","imported_at_utc":timestamp}); continue
        target = destination / relative; target.parent.mkdir(parents=True, exist_ok=True)
        before = sha_file(item); shutil.copyfile(item, target); require(before == sha_file(item) == sha_file(target), "source changed during import")
        records.append({"type":"file","source_path":str(item),"destination_relative_path":target.relative_to(archive).as_posix(),"bytes":target.stat().st_size,"sha256":before,"category":category,"imported_at_utc":timestamp})
    return records


def initialize_project(vault_root: Path, project_directory_name: str, project_id: str, problem_statement: str, *, seed_directory: Path | None = None, source_workspace: Path | None = None, legacy_run_directories: list[Path] | None = None, additional_source_files: list[Path] | None = None, contract_package_files: list[Path] | None = None) -> dict[str, Any]:
    require(re.fullmatch(r'[^<>:"/\\|?*]+', project_directory_name) is not None and not project_directory_name.endswith((".", " ")), "unsafe project directory name")
    require(re.fullmatch(r"[a-z0-9][a-z0-9._-]{7,127}", project_id) is not None, "unsafe project id")
    root = projects_root(vault_root); root.mkdir(parents=True, exist_ok=True); assert_no_symlink_chain(root)
    target = root / project_directory_name; require(not target.exists(), "project already exists")
    stage = root / f".{project_directory_name}.stage-{uuid.uuid4().hex}"; records: list[dict[str, Any]] = []; exclusions: list[dict[str, Any]] = []; timestamp = utc_now()
    try:
        stage.mkdir()
        for relative in REQUIRED_DIRECTORIES: (stage / relative).mkdir(parents=True, exist_ok=True)
        if seed_directory is None: _seed(stage, project_id, project_directory_name, problem_statement)
        else:
            seed_exclusions=[]; _copy_tree(assert_no_symlink_chain(seed_directory),stage,stage,"project-seed",timestamp,seed_exclusions)
            require(all((stage/relative).is_file() for relative in REQUIRED_FILES),"seed is missing required project files")
            seeded=read_json(stage/"project.json","seed project.json"); require(seeded.get("project_id")==project_id and seeded.get("project_directory_name")==project_directory_name,"seed project identity mismatches")
        if source_workspace is not None:
            workspace = assert_no_symlink_chain(source_workspace)
            for filename in ("AI-START-HERE.md", "research-ledger.md"):
                item = workspace / filename
                if item.is_file():
                    assert_no_symlink_chain(item); target_file=stage/"history/imported-workspace"/filename; before=sha_file(item); shutil.copyfile(item,target_file); require(before==sha_file(item)==sha_file(target_file),"source changed during import")
                    records.append({"type":"file","source_path":str(item),"destination_relative_path":target_file.relative_to(stage).as_posix(),"bytes":target_file.stat().st_size,"sha256":before,"category":"workspace-root","imported_at_utc":timestamp})
            for directory in ("work","archive","handoff","outputs"):
                records += _copy_tree(workspace / directory, stage / "history/imported-workspace" / directory, stage, f"workspace-{directory}", timestamp, exclusions, ("skill-dev",) if directory == "work" else ())
        for legacy in legacy_run_directories or []:
            records += _copy_tree(assert_no_symlink_chain(legacy), stage / "history/legacy-runs" / legacy.name, stage, "legacy-run", timestamp, exclusions)
        seen=set()
        for item in additional_source_files or []:
            source=assert_no_symlink_chain(item); require(source.is_file(),"additional source file is missing"); require(source.name.casefold() not in seen,"additional source filenames collide"); seen.add(source.name.casefold()); destination=stage/"sources/originals"/source.name; destination.parent.mkdir(parents=True,exist_ok=True); before=sha_file(source); shutil.copyfile(source,destination); require(before==sha_file(source)==sha_file(destination),"additional source changed during import"); records.append({"type":"file","source_path":str(source),"destination_relative_path":destination.relative_to(stage).as_posix(),"bytes":destination.stat().st_size,"sha256":before,"category":"external-source-snapshot","imported_at_utc":timestamp})
        seen=set()
        for item in contract_package_files or []:
            source=assert_no_symlink_chain(item); require(source.is_file(),"historical contract package is missing"); require(source.name.casefold() not in seen,"historical contract filenames collide"); seen.add(source.name.casefold()); destination=stage/"history/contract-packages"/source.name; before=sha_file(source); shutil.copyfile(source,destination); require(before==sha_file(source)==sha_file(destination),"contract package changed during import"); records.append({"type":"file","source_path":str(source),"destination_relative_path":destination.relative_to(stage).as_posix(),"bytes":destination.stat().st_size,"sha256":before,"category":"historical-contract-package","imported_at_utc":timestamp})
        manifest = "".join(compact(x)+"\n" for x in records + exclusions); atomic_text(stage / "manifests/import-manifest.jsonl", manifest, new=True)
        summary = {"schema":1,"project_id":project_id,"imported_at_utc":timestamp,"file_count":len(records),"exclusion_count":len(exclusions),"manifest_sha256":sha_file(stage / "manifests/import-manifest.jsonl")}
        atomic_text(stage / "manifests/import-summary.json", json.dumps(summary, ensure_ascii=False, indent=2)+"\n", new=True)
        if any(x["category"] == "legacy-run" for x in records):
            project = read_json(stage / "project.json", "project.json"); project.update({"status":"migration_required","updated_at_utc":timestamp}); atomic_text(stage / "project.json", json.dumps(project, ensure_ascii=False, indent=2)+"\n")
            checkpoint = read_json(stage / "state/checkpoint.json", "checkpoint.json"); checkpoint.update({"project_status":"migration_required","migration":{"status":"required","manifest_path":"manifests/legacy-semantic-manifest.json","manifest_sha256":None,"recognized_count":None,"disposed_count":0,"unresolved_substantive_count":None},"updated_at_utc":timestamp}); atomic_text(stage / "state/checkpoint.json", json.dumps(checkpoint, ensure_ascii=False, indent=2)+"\n")
        genesis = {"schema":1,"sequence":0,"event_type":"PROJECT_GENESIS","project_id":project_id,"occurred_at_utc":timestamp,"import_manifest_sha256":summary["manifest_sha256"],"previous_event_sha256":None}
        genesis["event_sha256"] = sha_event(genesis); atomic_text(stage / "state/project-events.jsonl", compact(genesis)+"\n")
        checkpoint = read_json(stage / "state/checkpoint.json", "checkpoint.json"); checkpoint.update({"last_project_event_sha256":genesis["event_sha256"],"updated_at_utc":timestamp}); atomic_text(stage / "state/checkpoint.json", json.dumps(checkpoint, ensure_ascii=False, indent=2)+"\n")
        os.replace(stage, target)
    finally:
        if stage.exists(): shutil.rmtree(stage)
    return verify_project(target, structural_only=True)


def event_state(project_directory: Path) -> dict[str, Any]:
    path = project_directory / "state/project-events.jsonl"; lines = path.read_text(encoding="utf-8", errors="strict").splitlines(); require(bool(lines), "project event stream has no genesis")
    events = []; head = None
    for sequence, line in enumerate(lines):
        require(bool(line.strip()), "project event stream contains blank line"); event = strict_json_loads(line); require(isinstance(event, dict) and event.get("sequence") == sequence, "project event sequence has a gap or duplicate")
        require((sequence == 0 and event.get("previous_event_sha256") is None) or (sequence > 0 and event.get("previous_event_sha256") == head), "project event hash chain is broken")
        payload = {key:value for key,value in event.items() if key != "event_sha256"}; require(event.get("event_sha256") == sha_event(payload), "project event payload hash mismatch")
        head = event["event_sha256"]; events.append(event)
    return {"path":path,"events":events,"head_sequence":len(events)-1,"head_sha256":head}


def add_event(project_directory: Path, event_type: str, data: dict[str, Any]) -> dict[str, Any]:
    state = event_state(project_directory); event = {"schema":1,"sequence":state["head_sequence"]+1,"event_type":event_type,"project_id":data["project_id"],"occurred_at_utc":utc_now(),"data":data,"previous_event_sha256":state["head_sha256"]}; event["event_sha256"] = sha_event(event)
    atomic_text(state["path"], state["path"].read_text(encoding="utf-8")+compact(event)+"\n"); return event


def verify_project(project_directory: Path, *, structural_only: bool = False) -> dict[str, Any]:
    resolved = resolve_project(project_directory)
    for relative in REQUIRED_DIRECTORIES: require((resolved["path"] / relative).is_dir(), f"required project directory is missing: {relative}")
    for relative in REQUIRED_FILES: require((resolved["path"] / relative).is_file(), f"required project file is missing: {relative}")
    checkpoint = read_json(resolved["path"] / "state/checkpoint.json", "checkpoint.json"); require(checkpoint.get("project_id") == resolved["project"]["project_id"], "checkpoint project_id mismatch")
    events = event_state(resolved["path"]); summary = read_json(resolved["path"] / "manifests/import-summary.json", "import summary"); manifest = resolved["path"] / "manifests/import-manifest.jsonl"; require(summary.get("manifest_sha256") == sha_file(manifest), "import manifest hash mismatch")
    verified = 0
    for number, line in enumerate(manifest.read_text(encoding="utf-8", errors="strict").splitlines(), 1):
        require(bool(line.strip()), f"blank import manifest line {number}"); record = strict_json_loads(line)
        if record.get("type") != "file": continue
        destination = resolved["path"] / record["destination_relative_path"]; require(safe_inside(destination, resolved["path"]) and destination.is_file(), "imported file is missing or escapes project"); assert_no_symlink_chain(destination); require(sha_file(destination) == record["sha256"], "imported file hash mismatch"); verified += 1
    semantic=None
    if not structural_only:
        from MathResearchLegacyArchive import verify as verify_legacy
        semantic=verify_legacy(resolved["path"])
    return {"Ok":True,"ProjectDirectory":str(resolved["path"]),"ProjectId":resolved["project"]["project_id"],"ProjectJsonSha256":resolved["project_json_sha256"],"Status":resolved["project"]["status"],"ImportedFilesVerified":verified,"ProjectEventHead":events["head_sha256"],"Checkpoint":checkpoint,"SemanticArchive":semantic}


def resume_plan(project_directory: Path) -> dict[str, Any]:
    verified = verify_project(project_directory); checkpoint = verified["Checkpoint"]
    if checkpoint["dirty"] or checkpoint["recovery_required"]: action = "recovery_or_audit_only"
    elif checkpoint["audit_due"]: action = "audit_required"
    elif checkpoint["contract"]["status"] not in {"confirmed","active"}: action = "awaiting_contract"
    elif checkpoint["run"]["status"] == "attempt_running": action = "resume_same_attempt"
    elif checkpoint["run"]["status"] in {"active","idle","paused"}: action = "resume_signed_run"
    else: action = "awaiting_contract"
    return {"Ok":True,"ProjectId":verified["ProjectId"],"Action":action,"AuditDue":checkpoint["audit_due"],"Dirty":checkpoint["dirty"],"ActiveContract":checkpoint["contract"],"ActiveRun":checkpoint["run"],"ActiveTicket":checkpoint["active_ticket"],"MinimalRead":["README.md","state/CURRENT.md","state/checkpoint.json"]}


def failure_record(path: Path, expected_attempt_id: str | None = None, artifact_root: Path | None = None) -> dict[str, Any]:
    value = read_json(path, "failure record"); required = {"schema","attempt_id","route_id","decision_problem","failed_step","failure_reason","excluded_scope","not_excluded_scope","retry_fingerprint_sha256","reopen_conditions","artifacts"}; require(required <= set(value) and value["schema"] == 1, "failure record schema or fields are invalid")
    require(all(isinstance(value[key], str) and bool(value[key].strip()) for key in required-{"schema","reopen_conditions","artifacts"}), "failure record text is incomplete"); require(expected_attempt_id is None or value["attempt_id"] == expected_attempt_id, "failure record attempt_id mismatch"); require(re.fullmatch(r"[0-9a-f]{64}", value["retry_fingerprint_sha256"]) is not None, "failure retry fingerprint is invalid")
    require(isinstance(value["reopen_conditions"], list) and bool(value["reopen_conditions"]) and all(isinstance(x,str) and bool(x.strip()) for x in value["reopen_conditions"]), "failure reopen conditions are invalid"); require(isinstance(value["artifacts"], list) and bool(value["artifacts"]), "failure artifacts are empty")
    for item in value["artifacts"]:
        require(isinstance(item,dict) and set(item)>={"file","sha256"} and re.fullmatch(r"[0-9a-f]{64}",str(item["sha256"])), "failure artifact binding is invalid")
        if artifact_root is not None:
            bound = artifact_root / item["file"]; require(safe_inside(bound,artifact_root) and bound.is_file() and sha_file(bound)==item["sha256"], "failure artifact is missing, escaped, or changed")
    return {"Ok":True,"Sha256":sha_file(path),"Value":value}


def route_fingerprint(ticket: dict[str, Any]) -> str:
    keys=("route_id","route_family_id","mechanism_id","decision_problem","frozen_domain","resource_caps"); require(all(key in ticket for key in keys), "route fingerprint input is incomplete")
    return sha_event({key:ticket[key] for key in keys})


def route_start(project_directory: Path, ticket: dict[str, Any]) -> dict[str, Any]:
    verified=verify_project(project_directory); require(all(isinstance(ticket.get(key),str) and ticket[key] for key in ("route_id","route_fingerprint_sha256","mechanism_id","decision_problem","frozen_domain")), "route ticket is incomplete"); require(ticket["route_fingerprint_sha256"]==route_fingerprint(ticket), "route ticket fingerprint mismatches")
    registry=read_json(Path(verified["ProjectDirectory"])/"state/route-registry.json","route registry"); matches=[x for x in registry.get("routes",[]) if (x.get("route_id")==ticket["route_id"] and x.get("retry_fingerprint_sha256")==ticket["route_fingerprint_sha256"]) or (x.get("route_family_id")==ticket["route_family_id"] and x.get("status") in {"frozen","closed"})]
    if len(matches)>1:
        exact=[x for x in matches if x.get("route_id")==ticket["route_id"] and x.get("retry_fingerprint_sha256")==ticket["route_fingerprint_sha256"]]; require(len(exact)==1,"route family is frozen by multiple records"); matches=exact
    if len(matches)==1 and matches[0].get("status") in {"frozen","closed"}:
        evidence=ticket.get("reopen_evidence"); require(isinstance(evidence,dict) and set(evidence)>={"condition_id","evidence_sha256"},"duplicate frozen route lacks reopen evidence"); require(evidence["condition_id"] in matches[0].get("reopen_condition_ids",[]) and evidence["evidence_sha256"] not in matches[0].get("seen_evidence_sha256",[]),"reopen evidence is not new and registered")
    return {"Ok":True,"ProjectId":verified["ProjectId"],"RouteId":ticket["route_id"],"Fingerprint":ticket["route_fingerprint_sha256"]}


def source_claims(project_directory: Path, hashes: list[str]) -> dict[str, Any]:
    verified=verify_project(project_directory); require(bool(hashes) and all(re.fullmatch(r"[0-9a-f]{64}",x) for x in hashes),"source claim hashes are invalid"); found=set()
    for root in ("evidence","attempts"):
        for item in (Path(verified["ProjectDirectory"])/root).rglob("*"):
            if item.is_file() and not item.is_symlink() and sha_file(item) in hashes: found.add(sha_file(item))
    require(set(hashes)<=found,"source claim hashes are absent from project archive"); return {"Ok":True,"ProjectId":verified["ProjectId"],"VerifiedHashes":sorted(found)}


def project_status(project_directory: Path) -> dict[str, Any]:
    verified=verify_project(project_directory,structural_only=True); checkpoint=verified["Checkpoint"]
    return {"Ok":True,"ProjectId":verified["ProjectId"],"ProjectDirectory":verified["ProjectDirectory"],"Status":verified["Status"],"ProjectJsonSha256":verified["ProjectJsonSha256"],"AttemptCount":checkpoint["attempt_count"],"AttemptsSinceLastAudit":checkpoint["attempts_since_last_audit"],"AuditDue":checkpoint["audit_due"],"Dirty":checkpoint["dirty"],"MigrationStatus":checkpoint.get("migration",{}).get("status","not_required")}


def new_handoff(project_directory: Path, label: str="handoff") -> dict[str, Any]:
    require(re.fullmatch(r"[A-Za-z0-9._-]{1,64}",label) is not None,"unsafe handoff label"); verified=verify_project(project_directory); plan=resume_plan(project_directory); timestamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"); path=Path(verified["ProjectDirectory"])/"handoffs"/f"{timestamp}-{label}.md"
    body=f"# Math research handoff\n\n- project_id: {verified['ProjectId']}\n- status: {verified['Status']}\n- next_action: {plan['Action']}\n- audit_due: {str(plan['AuditDue']).lower()}\n- dirty: {str(plan['Dirty']).lower()}\n- project_json_sha256: {verified['ProjectJsonSha256']}\n\n## 最小恢复读取\n\n1. ../README.md\n2. ../state/CURRENT.md\n3. ../state/checkpoint.json\n4. 活动合同与当前票据（若有）\n"; atomic_text(path,body,new=True)
    event=add_event(Path(verified["ProjectDirectory"]),"HANDOFF_CREATED",{"project_id":verified["ProjectId"],"handoff_path":path.relative_to(verified["ProjectDirectory"]).as_posix(),"handoff_sha256":sha_file(path),"next_action":plan["Action"]}); checkpoint_path=Path(verified["ProjectDirectory"])/"state/checkpoint.json"; checkpoint=read_json(checkpoint_path,"checkpoint"); checkpoint.update({"last_project_event_sha256":event["event_sha256"],"updated_at_utc":utc_now()}); atomic_text(checkpoint_path,json.dumps(checkpoint,ensure_ascii=False,indent=2)+"\n")
    return {"Ok":True,"Path":str(path),"Sha256":sha_file(path),"NextAction":plan["Action"],"EventSha256":event["event_sha256"]}


def repair_event_tail(project_directory: Path) -> dict[str, Any]:
    project=resolve_project(project_directory); path=project["path"]/"state/project-events.jsonl"; lines=path.read_text(encoding="utf-8",errors="strict").splitlines(); require(len(lines)>=2,"event-tail repair requires a post-genesis event"); head=None
    for index,line in enumerate(lines):
        event=strict_json_loads(line); require(isinstance(event,dict) and event.get("sequence")==index,"event-tail repair refuses sequence gap"); require((index==0 and event.get("previous_event_sha256") is None) or (index>0 and event.get("previous_event_sha256")==head),"event-tail repair refuses predecessor corruption"); payload={key:value for key,value in event.items() if key!="event_sha256"}; actual=sha_event(payload)
        if index<len(lines)-1: require(event.get("event_sha256")==actual,"event-tail repair refuses corruption before tail")
        else:
            old=event.get("event_sha256")
            if old==actual: return {"Ok":True,"Changed":False,"EventSha256":actual}
            checkpoint_path=project["path"]/"state/checkpoint.json"; checkpoint=read_json(checkpoint_path,"checkpoint.json"); require(checkpoint.get("last_project_event_sha256")==old,"checkpoint does not point to damaged tail")
            event["event_sha256"]=actual; lines[index]=compact(event); atomic_text(path,"\n".join(lines)+"\n"); checkpoint.update({"last_project_event_sha256":actual,"updated_at_utc":utc_now()}); atomic_text(checkpoint_path,json.dumps(checkpoint,ensure_ascii=False,indent=2)+"\n"); return {"Ok":True,"Changed":True,"PreviousEventSha256":old,"EventSha256":actual}
        head=event["event_sha256"]
    raise ProjectArchiveError("event-tail repair failed")


def resolve_run(project_directory: Path, run_directory: Path) -> dict[str, Any]:
    project=resolve_project(project_directory); run=assert_no_symlink_chain(run_directory); require(run.is_dir() and run.parent.resolve()==(project["path"]/"runs").resolve(),"run must be one direct child of project runs")
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}",run.name) is not None,"unsafe run id"); return {"project":project,"run":run,"run_id":run.name}


def register_contract(project_directory: Path, contract_file: Path, contract_binding_sha256: str, contract_version: str, run_directory: Path) -> dict[str, Any]:
    verify_project(project_directory); context=resolve_run(project_directory,run_directory); contract=assert_no_symlink_chain(contract_file); text=contract.read_text(encoding="utf-8",errors="strict").replace("\r\n","\n"); require("\r" not in text and re.fullmatch(r"[0-9a-f]{64}",contract_binding_sha256) and sha_bytes(text.encode("utf-8"))==contract_binding_sha256,"contract normalized binding mismatches"); require(re.fullmatch(r"v[1-9]\d*",contract_version) is not None,"contract version is invalid")
    destination=context["project"]["path"]/"contracts"/f"{contract_version}-prompt.md"; require(not destination.exists(),"contract version is already registered"); shutil.copyfile(contract,destination); require(sha_bytes(destination.read_text(encoding="utf-8",errors="strict").replace("\r\n","\n").encode("utf-8"))==contract_binding_sha256,"contract copy changed")
    relative_contract=destination.relative_to(context["project"]["path"]).as_posix(); relative_run=context["run"].relative_to(context["project"]["path"]).as_posix(); timestamp=utc_now(); project_path=context["project"]["path"]/"project.json"; project=read_json(project_path,"project.json"); project.update({"status":"contract_registered","active_contract":{"version":contract_version,"path":relative_contract,"sha256":contract_binding_sha256,"status":"confirmed"},"active_run":{"id":context["run_id"],"path":relative_run,"status":"preparing"},"updated_at_utc":timestamp}); atomic_text(project_path,json.dumps(project,ensure_ascii=False,indent=2)+"\n")
    checkpoint_path=context["project"]["path"]/"state/checkpoint.json"; checkpoint=read_json(checkpoint_path,"checkpoint.json"); checkpoint.update({"project_status":"contract_registered","contract":{"path":relative_contract,"sha256":contract_binding_sha256,"status":"confirmed","version":contract_version},"run":{"id":context["run_id"],"path":relative_run,"status":"preparing","ledger_head_sequence":None,"ledger_head_sha256":None},"dirty":True,"recovery_required":False,"updated_at_utc":timestamp}); atomic_text(checkpoint_path,json.dumps(checkpoint,ensure_ascii=False,indent=2)+"\n")
    event=add_event(context["project"]["path"],"CONTRACT_REGISTERED",{"project_id":context["project"]["project"]["project_id"],"contract_version":contract_version,"contract_sha256":contract_binding_sha256,"run_id":context["run_id"]}); checkpoint["last_project_event_sha256"]=event["event_sha256"]; atomic_text(checkpoint_path,json.dumps(checkpoint,ensure_ascii=False,indent=2)+"\n"); return {"Ok":True,"ProjectId":context["project"]["project"]["project_id"],"Contract":project["active_contract"],"Run":project["active_run"],"SagaState":"CONTRACT_REGISTERED","EventSha256":event["event_sha256"]}


def generated_block(path: Path, name: str, body: str) -> None:
    start=f"<!-- math-research-generated-{name}:start -->"; end=f"<!-- math-research-generated-{name}:end -->"; block=f"{start}\n{body}\n{end}"; text=path.read_text(encoding="utf-8",errors="strict") if path.exists() else ""; pattern=re.compile(re.escape(start)+r".*?"+re.escape(end),re.S); updated=pattern.sub(lambda _:block,text) if pattern.search(text) else text.rstrip()+f"\n\n{block}\n"; atomic_text(path,updated)


def _verified_copy(run: Path, project: Path, source_relative: str, expected_hash: str, destination_relative: str, *, preflight: bool=False) -> str:
    require(not Path(source_relative).is_absolute() and not Path(destination_relative).is_absolute(),"publication paths must be relative"); source=run/source_relative; destination=project/destination_relative; require(safe_inside(source,run) and safe_inside(destination,project) and source.is_file(),"publication path escapes or source is absent"); assert_no_symlink_chain(source); require(re.fullmatch(r"[0-9a-f]{64}",expected_hash) and sha_file(source)==expected_hash,"publication source hash mismatches"); destination.parent.mkdir(parents=True,exist_ok=True); assert_no_symlink_chain(destination.parent)
    if destination.exists(): require(destination.is_file() and sha_file(destination)==expected_hash,"publication destination conflicts")
    elif not preflight: shutil.copyfile(source,destination); require(sha_file(destination)==expected_hash,"publication copy verification failed")
    return destination.relative_to(project).as_posix()


def _cycle_events(run: Path) -> list[dict[str,Any]]:
    events=[]
    for path in sorted((run/"cycle-ledger").glob("*.json")):
        read=read_signed_json(path); require(not read["recovered_from_backup"],"immutable cycle event recovered from backup"); events.append(read["payload"])
    return events


def _publication_plan(run: Path, project: Path, run_id: str, *, preflight: bool=False) -> list[str]:
    published=[]
    for event in _cycle_events(run):
        data=event.get("data",{}); kind=event.get("event_type")
        if kind=="ATTEMPT_END":
            attempt=data["attempt_id"]; require(re.fullmatch(r"attempt-\d{4}",attempt) is not None,"unsafe attempt id"); extension=Path(data["artifact_file"]).suffix; classification="verified" if data["outcome"] in {"candidate_found","proved_subclaim","route_refuted","bounded_negative"} else "exploratory" if data["outcome"]=="portfolio_proposed" else "partial"
            published.append(_verified_copy(run,project,data["artifact_file"],data["artifact_sha256"],f"attempts/{run_id}/{attempt}/result{extension}",preflight=preflight)); published.append(_verified_copy(run,project,data["artifact_file"],data["artifact_sha256"],f"evidence/{classification}/{run_id}-{attempt}{extension}",preflight=preflight))
            if data.get("attempt_record_file"):
                published.append(_verified_copy(run,project,data["attempt_record_file"],data["attempt_record_sha256"],f"attempts/{run_id}/{attempt}/attempt-record.json",preflight=preflight)); record=read_json(run/data["attempt_record_file"],"attempt record")
                for index,report in enumerate(record.get("solver_reports",[]),1): published.append(_verified_copy(run,project,report["file"],report["sha256"],f"attempts/{run_id}/{attempt}/solver-{index:02d}{Path(report['file']).suffix}",preflight=preflight))
                for index,report in enumerate(record.get("verification_reports",[]),1): published.append(_verified_copy(run,project,report["artifact_file"],report["artifact_sha256"],f"attempts/{run_id}/{attempt}/verification-{index:02d}{Path(report['artifact_file']).suffix}",preflight=preflight))
                if record.get("route_portfolio"): published.append(_verified_copy(run,project,record["route_portfolio"]["file"],record["route_portfolio"]["sha256"],f"cycles/{run_id}/route-portfolios/{attempt}.json",preflight=preflight))
            if data.get("failure_record_file"):
                validated=failure_record(run/data["failure_record_file"],attempt,run); require(validated["Sha256"]==data["failure_record_sha256"],"failure publication binding mismatches"); route=validated["Value"]["route_id"]; require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}",route) is not None,"unsafe route id"); published.append(_verified_copy(run,project,data["failure_record_file"],data["failure_record_sha256"],f"failures/{route}.failure.json",preflight=preflight))
        elif kind=="AUDIT_END":
            audit=data["audit_id"]; require(re.fullmatch(r"audit-\d+",audit) is not None,"unsafe audit id"); published.append(_verified_copy(run,project,data["audit_result_file"],data["audit_result_sha256"],f"cycles/{run_id}/{audit}/audit-result.json",preflight=preflight)); result=read_json(run/data["audit_result_file"],"audit result")
            for report in result["reports"]: require(report["role"] in {"skeptic_quantifiers","skeptic_strategy","theory_tool_scout"},"unsafe audit role"); published.append(_verified_copy(run,project,report["artifact_file"],report["artifact_sha256"],f"cycles/{run_id}/{audit}/{report['role']}{Path(report['artifact_file']).suffix}",preflight=preflight))
    return published


def _publication_summary(run: Path) -> dict[str,Any]:
    kinds={}; attempts=[]; audits=[]
    for event in _cycle_events(run):
        data=event.get("data",{}); kind=event.get("event_type")
        if kind=="ATTEMPT_START": kinds[data["attempt_id"]]=data.get("attempt_kind","legacy")
        elif kind=="ATTEMPT_END": attempts.append({"attempt_id":data["attempt_id"],"attempt_kind":kinds.get(data["attempt_id"],"legacy"),"outcome":data["outcome"],"artifact_file":data["artifact_file"],"artifact_sha256":data["artifact_sha256"],"route_portfolio_file":data.get("route_portfolio_file")})
        elif kind=="AUDIT_END": audits.append({"audit_id":data["audit_id"],"action":data["action"],"accepted_route_cards":data.get("accepted_route_cards",[])})
    return {"attempts":attempts,"audits":audits}


def _update_failure_registry(run: Path, project: Path, run_id: str) -> None:
    path=project/"state/route-registry.json"; registry=read_json(path,"route registry"); routes=list(registry.get("routes",[]))
    for event in _cycle_events(run):
        data=event.get("data",{})
        if event.get("event_type")!="ATTEMPT_END" or not data.get("failure_record_file"): continue
        failure=failure_record(run/data["failure_record_file"],data["attempt_id"],run)["Value"]; route=failure["route_id"]; matches=[x for x in routes if x.get("route_id")==route]; require(len(matches)<=1,"route registry has duplicate route_id")
        entry={"route_id":route,"route_family_id":route,"retry_fingerprint_sha256":failure["retry_fingerprint_sha256"],"status":"frozen","origin":"active_run","run_id":run_id,"attempt_id":data["attempt_id"],"counter_effect":"active_attempt","reopen_condition_ids":[str(x).split(":",1)[0] for x in failure["reopen_conditions"]],"seen_evidence_sha256":[]}
        if matches: require(matches[0].get("retry_fingerprint_sha256")==entry["retry_fingerprint_sha256"],"route registry conflicts with published failure")
        else: routes.append(entry)
        markdown=project/"failures"/f"{route}.md"; body=f"# Failure dossier: {route}\n\n- run_id: {run_id}\n- attempt_id: {data['attempt_id']}\n- decision_problem: {failure['decision_problem']}\n- failed_step: {failure['failed_step']}\n- failure_reason: {failure['failure_reason']}\n- excluded_scope: {failure['excluded_scope']}\n- not_excluded_scope: {failure['not_excluded_scope']}\n- retry_fingerprint_sha256: `{failure['retry_fingerprint_sha256']}`\n\n## Reopen conditions\n\n"+"\n".join(f"- {x}" for x in failure["reopen_conditions"])+"\n"
        if markdown.exists(): require(markdown.read_text(encoding="utf-8")==body,"failure dossier destination conflicts")
        else: atomic_text(markdown,body,new=True)
    registry["routes"]=routes; atomic_text(path,json.dumps(registry,ensure_ascii=False,indent=2)+"\n")


def publish_checkpoint(project_directory: Path, run_directory: Path, *, fail_after_first_commit: bool=False) -> dict[str,Any]:
    verify_project(project_directory); context=resolve_run(project_directory,run_directory); project_path=context["project"]["path"]; run=context["run"]; run_id=context["run_id"]
    manifest_read=read_signed_json(run/"run.json"); require(not manifest_read["recovered_from_backup"],"run manifest recovered from backup"); manifest=manifest_read["payload"]; require(Path(manifest["run_directory"]).resolve()==run.resolve() and manifest["project"]["project_id"]==context["project"]["project"]["project_id"],"run manifest does not match project")
    from MathResearchCycleLedgerV2 import verify as verify_cycle
    cycle=verify_cycle(run); checkpoint_path=project_path/"state/checkpoint.json"; checkpoint=read_json(checkpoint_path,"checkpoint.json"); index_path=project_path/"manifests/publication-index.json"; index=read_json(index_path,"publication index") if index_path.exists() else {"schema":1,"project_id":context["project"]["project"]["project_id"],"entries":[]}; require(index.get("schema")==1 and index.get("project_id")==context["project"]["project"]["project_id"],"publication index identity mismatches")
    same=[x for x in index["entries"] if x["run_id"]==run_id and x["ledger_head_sequence"]==cycle["HeadSequence"]]
    if same:
        require(len(same)==1 and same[0]["ledger_head_sha256"]==cycle["HeadPayloadSha256"] and not checkpoint["recovery_required"],"indexed publication diverged or needs recovery")
        for artifact in same[0]["artifacts"]: require((project_path/artifact["path"]).is_file() and sha_file(project_path/artifact["path"])==artifact["sha256"],"indexed publication artifact changed")
        return {"Ok":True,"AlreadyPublished":True,"ProjectId":index["project_id"],"RunId":run_id,"LedgerHeadSequence":cycle["HeadSequence"],"LedgerHeadSha256":cycle["HeadPayloadSha256"],"PublishedArtifacts":[x["path"] for x in same[0]["artifacts"]],"EventSha256":same[0]["project_event_sha256"]}
    require(not any(x["run_id"]==run_id and x["ledger_head_sequence"]>cycle["HeadSequence"] for x in index["entries"]),"publication index is ahead of ledger")
    stage=project_path/f".publication-stage-{uuid.uuid4().hex}"; stage.mkdir(); records=[]
    try:
        artifacts=_publication_plan(run,stage,run_id)
        records=[{"path":relative,"sha256":sha_file(stage/relative)} for relative in artifacts]
        for record in records:
            destination=project_path/record["path"]
            if destination.exists(): require(destination.is_file() and sha_file(destination)==record["sha256"],"publication destination conflicts")
        checkpoint.update({"dirty":True,"recovery_required":True,"updated_at_utc":utc_now()}); atomic_text(checkpoint_path,json.dumps(checkpoint,ensure_ascii=False,indent=2)+"\n")
        for number,record in enumerate(records,1):
            source=stage/record["path"]; destination=project_path/record["path"]; destination.parent.mkdir(parents=True,exist_ok=True)
            if not destination.exists(): shutil.copyfile(source,destination)
            require(sha_file(destination)==record["sha256"],"publication commit verification failed")
            if fail_after_first_commit and number==1: raise ProjectArchiveError("synthetic publication commit interruption")
    finally: shutil.rmtree(stage,ignore_errors=True)
    summary=_publication_summary(run); _update_failure_registry(run,project_path,run_id)
    run_status="attempt_running" if cycle["ActiveAttempt"] else "auditing" if cycle["ActiveAudit"] else "completion_authorized" if cycle["CompletionAuthorized"] else "completion_candidate" if cycle["CompletionCandidate"] else "audit_due" if cycle["AuditDue"] else "idle" if cycle["CleanReturn"] else "active_dirty"
    checkpoint.update({"project_status":"completion_candidate" if cycle["CompletionAuthorized"] else "audit_due" if cycle["AuditDue"] else "active" if cycle["CleanReturn"] else "active_dirty","goal":{"id":manifest["goal"].get("goal_id"),"status":manifest["goal"]["observed_status"]},"run":{"id":run_id,"path":run.relative_to(project_path).as_posix(),"status":run_status,"ledger_head_sequence":cycle["HeadSequence"],"ledger_head_sha256":cycle["HeadPayloadSha256"],"manifest_sha256":sha_file(run/"run.json")},"thread":{"id":manifest["thread_id"],"status":"bound"},"attempt_count":cycle["AttemptCount"],"attempts_since_last_audit":cycle["AttemptsSinceLastAudit"],"audit_due":cycle["AuditDue"],"dirty":not cycle["CleanReturn"],"recovery_required":bool(cycle["ActiveAttempt"] or cycle["ActiveAudit"]),"active_ticket":{"ticket_id":cycle["ActiveAttempt"]["ticket_id"],"attempt_id":cycle["ActiveAttempt"]["attempt_id"]} if cycle["ActiveAttempt"] else None,"updated_at_utc":utc_now()}); atomic_text(checkpoint_path,json.dumps(checkpoint,ensure_ascii=False,indent=2)+"\n")
    generated_block(project_path/"state/CURRENT.md","status",f"## 控制器状态\n\n- project_status: {checkpoint['project_status']}\n- run: {run_id}\n- attempt_count: {checkpoint['attempt_count']}\n- attempts_since_last_audit: {checkpoint['attempts_since_last_audit']}\n- audit_due: {checkpoint['audit_due']}\n- dirty: {checkpoint['dirty']}\n- ledger_head: {cycle['HeadSequence']} / {cycle['HeadPayloadSha256']}")
    generated_block(project_path/"state/EVIDENCE.md",f"evidence-{run_id}","\n".join([f"## Run {run_id} 已发布证据",*[f"- `{x}` — SHA-256 `{sha_file(project_path/x)}`" for x in artifacts]])); generated_block(project_path/"state/RESULTS.md",f"results-{run_id}","\n".join([f"## Run {run_id} 尝试结果",*[f"- {x['attempt_id']} / {x['attempt_kind']}: `{x['outcome']}`；原始产物 `{x['artifact_file']}`；SHA-256 `{x['artifact_sha256']}`" for x in summary["attempts"]]])); generated_block(project_path/"state/ROUTES.md",f"routes-{run_id}","\n".join([f"## Run {run_id} 路线记录",*[f"- {x['audit_id']}: `{x['action']}`；接受路线卡 {len(x['accepted_route_cards'])} 张。" for x in summary["audits"]]]))
    event=add_event(project_path,"RUN_CHECKPOINT_PUBLISHED",{"project_id":context["project"]["project"]["project_id"],"run_id":run_id,"ledger_head_sequence":cycle["HeadSequence"],"ledger_head_sha256":cycle["HeadPayloadSha256"],"attempt_count":cycle["AttemptCount"],"audit_due":cycle["AuditDue"],"published_artifacts":artifacts}); index["entries"].append({"run_id":run_id,"ledger_head_sequence":cycle["HeadSequence"],"ledger_head_sha256":cycle["HeadPayloadSha256"],"run_manifest_sha256":sha_file(run/"run.json"),"artifacts":records,"project_event_sha256":event["event_sha256"],"published_at_utc":utc_now()}); atomic_text(index_path,json.dumps(index,ensure_ascii=False,indent=2)+"\n"); checkpoint["last_project_event_sha256"]=event["event_sha256"]; atomic_text(checkpoint_path,json.dumps(checkpoint,ensure_ascii=False,indent=2)+"\n")
    return {"Ok":True,"AlreadyPublished":False,"ProjectId":index["project_id"],"RunId":run_id,"LedgerHeadSequence":cycle["HeadSequence"],"LedgerHeadSha256":cycle["HeadPayloadSha256"],"CleanReturn":cycle["CleanReturn"],"AuditDue":cycle["AuditDue"],"RecoveryRequired":checkpoint["recovery_required"],"PublishedArtifacts":artifacts,"EventSha256":event["event_sha256"]}


# Facade routes for the four legacy-semantic functions exported by the platform module.
def analyze_legacy(project_directory: Path) -> dict[str,Any]:
    from MathResearchLegacyArchive import analyze
    return analyze(project_directory)


def apply_legacy(project_directory: Path, manifest_file: Path, current_conclusion: str="Legacy material migrated; migration alone promotes no candidate and changes no baseline.") -> dict[str,Any]:
    from MathResearchLegacyArchive import apply
    return apply(project_directory,manifest_file,current_conclusion)


def verify_legacy(project_directory: Path) -> dict[str,Any]:
    from MathResearchLegacyArchive import verify
    return verify(project_directory)


def test_legacy_failure(path: Path) -> dict[str,Any]:
    from MathResearchLegacyArchive import legacy_failure
    return legacy_failure(path)
