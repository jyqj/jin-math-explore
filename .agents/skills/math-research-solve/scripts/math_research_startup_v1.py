#!/usr/bin/env python3
"""Native shared Startup v1/v2 classifier; read-only except its authoritative controller reads."""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys, time
from pathlib import Path
from typing import Any
from MathResearchProjectArchiveV2 import resume_plan, verify_project
from math_research_control_primitives import assert_no_symlink_chain, strict_json_loads

GOALS={"none","active","paused","complete","blocked","unknown"}
def sha_file(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def sha_text(text:str)->str:return hashlib.sha256(text.replace("\r\n","\n").encode()).hexdigest()
def read(path:Path)->dict[str,Any]:
    value=strict_json_loads(assert_no_symlink_chain(path).read_text(encoding="utf-8",errors="strict"));
    if not isinstance(value,dict): raise ValueError(f"JSON object required: {path}")
    return value
def inside(path:Path,root:Path)->bool:
    try:path.resolve().relative_to(root.resolve());return True
    except ValueError:return False
def safe_leaf(value:str)->bool:return bool(value) and Path(value).name==value and not re.search(r'[<>:"/\\|?*]',value) and not value.endswith(("."," "))

def first_contract(plan:dict,project:dict,checkpoint:dict)->bool:
    contract=plan.get("ActiveContract") or {}; run=plan.get("ActiveRun") or {}; required={"attempt_count","attempts_since_last_audit","last_sealed_attempt","last_completed_audit","audit_due","dirty","recovery_required","project_status"}
    return required<=set(checkpoint) and contract.get("status")=="none" and not contract.get("path") and not contract.get("sha256") and not contract.get("version") and run.get("status")=="none" and not run.get("id") and not run.get("path") and plan.get("ActiveTicket") is None and project.get("status")=="paused" and project.get("active_contract") is None and project.get("active_run") is None and checkpoint.get("project_status")=="paused" and checkpoint.get("attempt_count")==0 and checkpoint.get("attempts_since_last_audit")==0 and checkpoint.get("last_sealed_attempt") is None and checkpoint.get("last_completed_audit") is None and checkpoint.get("audit_due") is False and checkpoint.get("dirty") is False and checkpoint.get("recovery_required") is False

def preparing(plan:dict,project:Path,expected:dict[str,str|None])->dict[str,Any]:
    names=("project_id","contract_version","contract_sha","run_id","prompt_name","prompt_sha","goal_name","goal_sha")
    if any(not expected.get(x) for x in names): return {"match":False,"reason":"expected_preparing_receipt_incomplete","phase":None}
    if not safe_leaf(str(expected["prompt_name"])) or not safe_leaf(str(expected["goal_name"])) or expected["prompt_name"]==expected["goal_name"]: raise ValueError("expected input filenames are unsafe")
    contract=plan.get("ActiveContract") or {}; run=plan.get("ActiveRun") or {}
    if not plan.get("Dirty") or contract.get("status")!="confirmed" or run.get("status")!="preparing": return {"match":False,"reason":"checkpoint_not_registered_preparing","phase":None}
    if plan.get("ProjectId")!=expected["project_id"] or contract.get("version")!=expected["contract_version"] or contract.get("sha256")!=expected["contract_sha"] or run.get("id")!=expected["run_id"]: return {"match":False,"reason":"preparing_identity_or_binding_mismatch","phase":None}
    contract_path=(project/str(contract.get("path",""))).resolve(); run_path=(project/str(run.get("path",""))).resolve()
    if not inside(contract_path,project/"contracts") or not contract_path.is_file() or sha_text(contract_path.read_text(encoding="utf-8",errors="strict"))!=expected["contract_sha"]: return {"match":False,"reason":"preparing_contract_bytes_mismatch","phase":None}
    if not inside(run_path,project/"runs") or run_path.parent.resolve()!=(project/"runs").resolve() or run_path.name!=expected["run_id"] or not run_path.is_dir(): return {"match":False,"reason":"preparing_run_path_invalid","phase":None}
    prompt=run_path/str(expected["prompt_name"]); goal=run_path/str(expected["goal_name"])
    if not prompt.is_file() or not goal.is_file(): return {"match":False,"reason":"preparing_input_missing","phase":None}
    if sha_file(prompt)!=expected["prompt_sha"] or sha_text(prompt.read_text(encoding="utf-8",errors="strict"))!=expected["contract_sha"] or sha_file(goal)!=expected["goal_sha"]: return {"match":False,"reason":"preparing_input_hash_mismatch","phase":None}
    if (run_path/"run.json").is_file(): return {"match":True,"reason":None,"phase":"launcher_manifest_present_requires_signed_resume_verification"}
    if {x.name for x in run_path.iterdir()}!={expected["prompt_name"],expected["goal_name"]}: return {"match":False,"reason":"prelauncher_directory_must_contain_only_prompt_and_goal","phase":None}
    return {"match":True,"reason":None,"phase":"registered_before_launcher"}

def classify(*,version:int,goal_status:str,project_directory:Path|None=None,vault_root:Path|None=None,project_directory_name:str|None=None,expected:dict[str,str|None]|None=None)->dict[str,Any]:
    started=time.perf_counter();
    if version not in {1,2} or goal_status not in GOALS: raise ValueError("version or GoalStatus invalid")
    startup=None; action=None; reason=None; phase=None; plan=None; controller=None; calls=0; minimal=[]; expected=expected or {}
    if vault_root is not None or project_directory_name is not None:
        if vault_root is None or not safe_leaf(project_directory_name or ""): raise ValueError("slot mode requires safe VaultRoot/name")
        vault=assert_no_symlink_chain(vault_root); root=assert_no_symlink_chain(vault/"笔记草稿"/"公开问题的尝试"); project=(root/project_directory_name).resolve()
        if project.parent!=root.resolve(): raise ValueError("project slot escaped canonical root")
        if not project.exists(): startup="fresh_project_slot"; action="initialize_then_render_contract"
        elif not (project/"project.json").is_file(): startup="partial_project_tree_recovery"; action="inspect_partial_tree_without_initializing_over_it"; reason="existing_slot_missing_project_json"
    else:
        if project_directory is None: raise ValueError("ProjectDirectory is required")
        project=assert_no_symlink_chain(project_directory)
        if not project.is_dir(): raise ValueError("Existing-mode ProjectDirectory is missing")
    if startup is None:
        head=read(project/"project.json"); checkpoint=read(project/"state"/"checkpoint.json"); before=(sha_file(project/"project.json"),sha_file(project/"state"/"checkpoint.json")); migration=(checkpoint.get("migration") or {}).get("status","unknown"); allowed={"not_required","verified"}|({"complete"} if version==2 else set())
        if head.get("status")=="migration_required" or migration not in allowed:
            controller="StructuralOnly"; verified=verify_project(project,structural_only=True); calls=1; cp=verified["Checkpoint"]; plan={"ProjectId":verified["ProjectId"],"Checkpoint":cp,"Status":verified["Status"]};
            if (sha_file(project/"project.json"),sha_file(project/"state"/"checkpoint.json"))!=before: raise ValueError("authority changed during verification")
            migration=cp.get("migration") or {}; startup="first_legacy_migration"; action={"required":"analyze_legacy_once","analyzed":"complete_semantic_review","review_required":"complete_semantic_review","approved":"apply_then_verify_semantic_migration"}.get(migration.get("status"),"inspect_legacy_migration_recovery"); minimal=["project.json","state/checkpoint.json","manifests/import-summary.json"]
        else:
            controller="ResumePlan"; plan=resume_plan(project); calls=1
            if (sha_file(project/"project.json"),sha_file(project/"state"/"checkpoint.json"))!=before: raise ValueError("authority changed during ResumePlan")
            if expected.get("project_id") and plan["ProjectId"]!=expected["project_id"]: raise ValueError("expected project_id mismatch")
            minimal=["README.md","state/CURRENT.md","state/checkpoint.json"]; route=plan["Action"]
            if route in {"resume_same_attempt","resume_signed_run"}: startup="same_run_resume"; action=route
            elif route=="audit_required": startup="same_run_resume"; action="run_due_audit"
            elif route=="awaiting_contract":
                if first_contract(plan,head,checkpoint): startup="existing_project_first_contract"; action="render_contract"
                else: startup="new_contract_or_closed_review"; action="review_terminal_or_prior_history_before_new_contract"
            elif route=="recovery_or_audit_only":
                check=preparing(plan,project,expected)
                if check["match"]: startup="registered_preparing_recovery"; phase=check["phase"]; action="invoke_new_launcher_without_reregistering" if phase=="registered_before_launcher" else "invoke_signed_resume_verification_without_reregistering"
                else: startup="recovery_only"; action="perform_unique_recovery_action"; reason=check["reason"]
            else: raise ValueError(f"unsupported ResumePlan action: {route}")
            for item in ((plan.get("ActiveContract") or {}).get("path"),(plan.get("ActiveTicket") or {}).get("path")):
                if item:minimal.append(item)
    pre={"initialize_then_render_contract","analyze_legacy_once","complete_semantic_review","apply_then_verify_semantic_migration","inspect_legacy_migration_recovery","render_contract","review_terminal_or_prior_history_before_new_contract","inspect_partial_tree_without_initializing_over_it"}; mutates=action not in {"inspect_partial_tree_without_initializing_over_it","check_goal_control","stop_campaign"}; gate="active_advisory_launcher_recheck_required"
    if goal_status=="none":
        if action in pre: gate="pre_goal_preparation_only_research_forbidden"
        else: action="create_or_bind_matching_goal_before_research"; reason="goal_control_none"; gate="research_forbidden_until_matching_goal_active"
    elif mutates and goal_status!="active":
        if goal_status=="paused":action="wait_for_goal_control";reason="goal_control_paused"
        elif goal_status=="unknown":action="check_goal_control";reason="goal_control_unknown"
        else:action="stop_campaign";reason=f"goal_control_{goal_status}"
        gate="research_and_mutation_forbidden"
    return {"schema":f"math-research-startup-plan/v{version}","ok":True,"startup_class":startup,"next_action":action,"recovery_reason":reason,"preparing_phase":phase,"project_id":plan.get("ProjectId") if plan else expected.get("project_id"),"project_directory":str(project),"goal_status_supplied":goal_status,"goal_status_evidence":"caller_supplied_advisory_launcher_must_recheck_control_plane","goal_gate":gate,"controller_action":controller,"controller_call_count":calls,"authoritative_resume_action":plan.get("Action") if plan else None,"active_contract":plan.get("ActiveContract") if plan else None,"active_run":plan.get("ActiveRun") if plan else None,"minimal_model_read":list(dict.fromkeys(x for x in minimal if x)),"contract_hash_role":"integrity_receipt_not_authorization_phrase","measured_router_elapsed_ms":round((time.perf_counter()-started)*1000,3)}

def main(version:int,argv=None)->int:
    p=argparse.ArgumentParser(); p.add_argument("--project-directory","-ProjectDirectory",type=Path); p.add_argument("--vault-root","-VaultRoot",type=Path); p.add_argument("--project-directory-name","-ProjectDirectoryName"); p.add_argument("--goal-status","-GoalStatus",required=True,choices=sorted(GOALS));
    for name in ("project-id","contract-version","contract-binding-sha256","run-id","prompt-file-name","prompt-raw-sha256","goal-file-name","goal-raw-sha256"):p.add_argument("--expected-"+name,"-Expected"+"".join(x.title() for x in name.split("-")))
    a=p.parse_args(argv); expected={"project_id":a.expected_project_id,"contract_version":a.expected_contract_version,"contract_sha":a.expected_contract_binding_sha256,"run_id":a.expected_run_id,"prompt_name":a.expected_prompt_file_name,"prompt_sha":a.expected_prompt_raw_sha256,"goal_name":a.expected_goal_file_name,"goal_sha":a.expected_goal_raw_sha256}
    try: print(json.dumps(classify(version=version,goal_status=a.goal_status,project_directory=a.project_directory,vault_root=a.vault_root,project_directory_name=a.project_directory_name,expected=expected),ensure_ascii=False,separators=(",",":")));return 0
    except Exception as exc:print(json.dumps({"ok":False,"error":str(exc)},ensure_ascii=False,separators=(",",":")),file=sys.stderr);return 2
