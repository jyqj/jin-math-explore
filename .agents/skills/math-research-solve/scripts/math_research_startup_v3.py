#!/usr/bin/env python3
"""Native strict read-only Startup v3 classifier for legacy/v8 archives."""
from __future__ import annotations
import argparse, hashlib, json, time, sys
from pathlib import Path
from typing import Any
from math_research_control_primitives import assert_no_symlink_chain, strict_json_loads
from math_research_migrate_v8_to_v10 import _read_v8
from math_research_state_v10 import ResearchError, sha_file

GOALS={"none","active","paused","complete","blocked","cancelled","unknown"}
def read(path:Path)->dict[str,Any]:
    value=strict_json_loads(assert_no_symlink_chain(path).read_text(encoding="utf-8",errors="strict"));
    if not isinstance(value,dict): raise ValueError("strict JSON object required")
    return value
def pointer(root:Path,value:dict,label:str)->Path:
    if not isinstance(value,dict) or not {"path","sha256"}<=set(value): raise ValueError(f"{label} pointer invalid")
    path=(root/str(value["path"])).resolve(); path.relative_to(root.resolve())
    if not path.is_file() or sha_file(path)!=value["sha256"]: raise ValueError(f"{label} pointer hash differs")
    return assert_no_symlink_chain(path)

def valid_v8(project:Path,head:dict[str,Any])->dict[str,Any]:
    try: parsed=_read_v8(project); checkpoint=parsed["checkpoint"]
    except ResearchError:
        checkpoint=read(pointer(project,{"path":head["active_checkpoint"]["path"],"sha256":head["active_checkpoint"]["sha256"]},"checkpoint"))
        if checkpoint.get("current_lifecycle") is not None: raise
        contract=head.get("active_contract") or {}; contract_path=(project/str(contract.get("path",""))).resolve(); contract_path.relative_to(project.resolve())
        if not contract_path.is_file() or hashlib.sha256(contract_path.read_text(encoding="utf-8").replace("\r\n","\n").encode()).hexdigest()!=contract.get("binding_sha256"): raise ValueError("closed-state contract binding differs")
        pointer(project,{"path":head["project_event_head"]["path"],"sha256":head["project_event_head"]["sha256"]},"event head"); parsed={"checkpoint":checkpoint,"contract":contract,"run":head.get("active_run")}
    state_path=pointer(project,{"path":head["goal_host_state"]["path"],"sha256":head["goal_host_state"]["sha256"]},"goal host"); state=read(state_path); required={"schema","project_id","control_generation","contract","run","host_goal","problem_statement_sha256","successor","counters","current_ticket","updated_at_utc"}
    if set(state)!=required or state["schema"]!="math-research-goal-host-state/v8": raise ValueError("goal host state shape/schema invalid")
    for value in (head,checkpoint,state):
        if value["project_id"]!=head["project_id"] or value["control_generation"]!=head["control_generation"]: raise ValueError("project/generation drift")
    if state["contract"]!=head["active_contract"] or checkpoint["contract"]!=state["contract"] or state["run"]!=head["active_run"] or checkpoint["run"]!=state["run"]: raise ValueError("contract/run authority drift")
    if state["problem_statement_sha256"]!=head["problem_statement_sha256"] or checkpoint["problem_statement_sha256"]!=state["problem_statement_sha256"] or checkpoint["counters"]!=state["counters"] or checkpoint["successor"]!=state["successor"]: raise ValueError("checkpoint/state authority drift")
    counters=state["counters"]
    if set(counters)!={"attempt_count","audit_count","total_round_count","attempts_since_last_audit","audit_due"} or any(type(counters[k]) is not int or counters[k]<0 for k in ("attempt_count","audit_count","total_round_count","attempts_since_last_audit")) or type(counters["audit_due"]) is not bool or counters["total_round_count"]!=counters["attempt_count"]+counters["audit_count"]: raise ValueError("counter invariant invalid")
    if checkpoint["completion_ready"] is not checkpoint["pending_goal_update"]: raise ValueError("completion flags differ")
    ticket=state["current_ticket"]; lifecycle=checkpoint["current_lifecycle"]
    if (ticket is None)!=(lifecycle is None): raise ValueError("ticket/lifecycle presence differs")
    if ticket is not None:
        for key in ("id","path","sha256","status"):
            if key not in ticket: raise ValueError("ticket pointer incomplete")
        pointer(project,{"path":ticket["path"],"sha256":ticket["sha256"]},"current ticket")
        if lifecycle.get("id")!=ticket["id"] or lifecycle.get("path")!=ticket["path"] or lifecycle.get("sha256")!=ticket["sha256"]: raise ValueError("ticket/lifecycle drift")
    return {"parsed":parsed,"state":state,"checkpoint":checkpoint,"ticket":ticket}

def classify(*,project_directory:Path|None=None,vault_root:Path|None=None,project_directory_name:str|None=None,goal_status:str="none")->dict[str,Any]:
    start=time.perf_counter();
    if goal_status not in GOALS: raise ValueError("GoalStatus invalid")
    startup=None; action=None; reason=None; project_id=None; plan=None; minimal=[]; valid=False; completion=False; legacy=False
    if vault_root is not None or project_directory_name is not None:
        if vault_root is None or not project_directory_name or Path(project_directory_name).name!=project_directory_name: raise ValueError("unsafe slot")
        root=assert_no_symlink_chain(vault_root/"笔记草稿"/"公开问题的尝试"); project=(root/project_directory_name).resolve(); project.relative_to(root.resolve())
        if not project.exists(): startup="fresh_project_slot"; action="initialize_then_render_goal_host_contract"; minimal=[]
        elif not (project/"project.json").is_file(): startup="partial_project_tree_recovery"; action="inspect_partial_tree_read_only"; reason="existing_slot_missing_project_json"
    else:
        if project_directory is None: raise ValueError("ProjectDirectory required")
        project=assert_no_symlink_chain(project_directory)
        if not project.is_dir(): raise ValueError("project missing")
    if startup is None:
        head=read(project/"project.json"); project_id=head.get("project_id"); is_v8=head.get("schema")=="math-research-project/v8"; has_checkpoint="active_checkpoint" in head; has_goal="goal_host_state" in head
        if not is_v8 and (has_checkpoint or has_goal): startup="legacy_execution_unsupported"; action="fail_closed_read_only_diagnosis"; reason="legacy_schema_cannot_activate_v8_generation_pointers"; legacy=True; minimal=["project.json"]
        elif is_v8 and (not has_checkpoint or not has_goal): startup="goal_host_state_invalid"; action="fail_closed_read_only_diagnosis"; reason="goal_host_state_pointer_pair_incomplete"; minimal=["project.json"]
        elif is_v8:
            try:
                checked=valid_v8(project,head); state=checked["state"]; checkpoint=checked["checkpoint"]; ticket=checked["ticket"]; status=state["run"]["status"]; completion=bool(checkpoint["completion_ready"]); valid=True; legacy=head.get("legacy_successor") is not None; plan={"ProjectId":state["project_id"],"Action":"goal_host_v8_advisory","ActiveContract":state["contract"],"ActiveRun":state["run"],"ActiveTicket":ticket}
                if completion:
                    if status!="closed" or ticket is not None or checkpoint["current_lifecycle"] is not None or state["counters"]["audit_due"]: raise ValueError("completion-ready state invalid")
                    startup="goal_host_completion_pending"; action="read_only_completion_pending_wait_for_current_goal_control_decision"
                elif status in {"not_started","preparing"}: startup="goal_host_ready"; action="verify_current_goal_then_begin_model_managed_attempt"
                elif status=="attempt_running": startup="goal_host_resume"; action="verify_current_goal_then_resume_exact_model_managed_ticket"
                elif status in {"audit_due","auditing","completion_candidate"}: startup="goal_host_audit_due"; action="verify_current_goal_then_run_due_audit"
                elif status=="awaiting_input": startup="goal_host_resume"; action="verify_current_goal_then_review_awaiting_input"
                elif status=="paused": startup="goal_host_resume"; action="verify_current_goal_then_resume_exact_model_managed_ticket"
                elif status in {"goal_continuity_terminal","superseded","closed"}: startup="goal_host_closed_review"; action="review_closed_goal_host_state_read_only"
                else: raise ValueError("run status invalid")
                minimal=["project.json",head["active_checkpoint"]["path"],head["goal_host_state"]["path"],state["contract"]["path"],state["current_ticket"]["path"] if state["current_ticket"] else None]
            except (ValueError,KeyError,TypeError,ResearchError,OSError) as exc: startup="goal_host_state_invalid"; action="fail_closed_read_only_diagnosis"; reason="goal_host_state_authority_invalid"; minimal=["project.json"]
        else:
            checkpoint=read(project/"state/checkpoint.json");
            if checkpoint.get("project_id")!=project_id: startup="project_identity_invalid"; action="fail_closed_read_only_diagnosis"; reason="project_checkpoint_identity_mismatch"
            else: startup="legacy_execution_unsupported"; action="fail_closed_read_only_diagnosis"; reason="no_production_legacy_execution_route"; legacy=bool((checkpoint.get("run") or head.get("active_run") or {}).get("id")); plan={"ProjectId":project_id,"Action":"legacy_read_only_classification","ActiveContract":checkpoint.get("contract") or head.get("active_contract"),"ActiveRun":checkpoint.get("run") or head.get("active_run"),"ActiveTicket":checkpoint.get("active_ticket")}; minimal=["project.json","state/checkpoint.json"]
    requires=valid
    if completion:
        if goal_status=="complete": startup="goal_host_closed_review"; action="review_durable_completed_goal_read_only"; requires=False
        elif goal_status=="active": startup="goal_host_completion_pending"; action="fresh_get_goal_then_update_goal_complete_no_project_write"; requires=True
        else: startup="goal_host_completion_pending"; action="read_only_completion_pending_goal_not_active"; requires=False
    elif valid and goal_status=="complete": startup="goal_host_state_invalid";action="fail_closed_read_only_diagnosis";reason="goal_complete_without_durable_completion_ready";requires=False
    gate="current_goal_control_check_required_before_any_mutation"
    if completion and goal_status=="complete":gate="durable_completion_closed_read_only"
    elif completion and goal_status!="active":gate="completion_pending_read_only_goal_not_active"
    elif goal_status=="none":gate="research_forbidden_no_current_goal"
    elif goal_status!="active":gate=f"research_forbidden_goal_{goal_status}"
    return {"schema":"math-research-startup-plan/v3","ok":True,"classifier_mode":"strict_read_only_no_launch_resume_or_goal_control","startup_class":startup,"next_action":action,"recovery_reason":reason,"preparing_phase":None,"terminal_no_resume":False,"legacy_archive_detected":legacy,"legacy_lineage_preserved":legacy and valid,"legacy_goal_bindings_obsolete":legacy,"successor_v8_requires_explicit_new_active_goal":legacy,"legacy_run_preservation_required":legacy,"terminal_evidence":[],"manifest_advisory_status":None,"manifest_advisory_exit_reason":None,"manifest_advisory_last_segment_status":None,"manifest_advisory_trust":"none","manifest_advisory_used_backup":False,"goal_host_state_trust":"strict_json_cross_checked_hash_bound_advisory_not_signature_or_goal_authorization" if valid else "none","legacy_successor_advisory_valid":legacy and valid,"legacy_successor_advisory_path":None,"project_id":plan.get("ProjectId") if plan else project_id,"project_directory":str(project),"goal_status_supplied":goal_status,"goal_status_normalized":goal_status,"goal_status_evidence":"caller_supplied_advisory_never_control_plane_proof","goal_gate":gate,"requires_current_goal_control_check":requires,"controller_action":None,"controller_call_count":0,"authoritative_resume_action":plan.get("Action") if plan else None,"active_contract":plan.get("ActiveContract") if plan else None,"active_run":plan.get("ActiveRun") if plan else None,"minimal_model_read":list(dict.fromkeys(x for x in minimal if x)),"contract_hash_role":"ordinary_integrity_binding_not_signature_or_authorization","measured_router_elapsed_ms":round((time.perf_counter()-start)*1000,3)}

def main(argv=None)->int:
    p=argparse.ArgumentParser();p.add_argument("--project-directory","-ProjectDirectory",type=Path);p.add_argument("--vault-root","-VaultRoot",type=Path);p.add_argument("--project-directory-name","-ProjectDirectoryName");p.add_argument("--goal-status","-GoalStatus",required=True,choices=sorted(GOALS));a=p.parse_args(argv)
    try:print(json.dumps(classify(project_directory=a.project_directory,vault_root=a.vault_root,project_directory_name=a.project_directory_name,goal_status=a.goal_status),ensure_ascii=False,separators=(",",":")));return 0
    except Exception as exc:print(json.dumps({"ok":False,"error":str(exc)},ensure_ascii=False,separators=(",",":")),file=sys.stderr);return 2
if __name__=="__main__":raise SystemExit(main())
