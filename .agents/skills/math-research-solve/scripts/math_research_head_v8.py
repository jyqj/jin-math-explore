#!/usr/bin/env python3
"""Native, fail-closed v8 successor staging and project-head CAS.

This module is intentionally dependency-free.  It is the non-Windows authority
for the two PowerShell v8 entrypoints and never invokes a platform shell.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import stat
import tempfile
from pathlib import Path
from typing import Any


class HeadV8Error(RuntimeError):
    def __init__(self, code: str, detail: str):
        super().__init__(detail); self.code = code


def fail(ok: bool, code: str, detail: str) -> None:
    if ok: raise HeadV8Error(code, detail)


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def sha_bytes(raw: bytes) -> str: return hashlib.sha256(raw).hexdigest()
def sha_file(path: Path) -> str: return sha_bytes(path.read_bytes())
def sha_text(text: str) -> str: return sha_bytes(text.replace("\r\n", "\n").encode("utf-8"))


def read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
            out: dict[str, Any] = {}
            for key, value in items:
                fail(key in out, "json_duplicate_key", f"{label} contains duplicate key {key!r}.")
                out[key] = value
            return out
        value = json.loads(path.read_text("utf-8"), object_pairs_hook=pairs)
    except HeadV8Error: raise
    except Exception as exc: raise HeadV8Error("json_invalid", f"Cannot read {label}: {exc}") from exc
    fail(not isinstance(value, dict), "json_invalid", f"{label} must be one JSON object.")
    return value


def plain_tree(root: Path) -> None:
    fail(not root.is_dir(), "project_missing", "ProjectDirectory is missing.")
    for path in (root, *root.rglob("*")):
        info = path.lstat(); attrs = getattr(info, "st_file_attributes", 0)
        fail(path.is_symlink() or bool(attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)),
             "reparse_forbidden", f"Links/reparse points are forbidden: {path}")


def safe_path(root: Path, relative: str) -> Path:
    fail(not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative,
         "unsafe_pointer_path", "Pointer path syntax is unsafe.")
    fail(any(part in ("", ".", "..") for part in relative.split("/")), "unsafe_pointer_path", "Pointer has a dot/empty segment.")
    result = (root / relative).resolve()
    fail(result != root and root not in result.parents, "unsafe_pointer_path", "Pointer escapes the project.")
    return result


def pointer(root: Path, relative: str) -> dict[str, str]:
    path = safe_path(root, relative)
    fail(not path.is_file(), "pointer_missing", f"Referenced file is absent: {relative}")
    return {"path": relative, "sha256": sha_file(path)}


def write_or_verify(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".build-v8.tmp")
    if path.exists():
        fail(path.read_bytes() != raw, "staging_collision", f"Existing deterministic output differs: {path}")
        if tmp.exists(): tmp.unlink()
        return
    if tmp.exists() and tmp.read_bytes() != raw: tmp.unlink()
    if not tmp.exists():
        with open(tmp, "xb") as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    os.replace(tmp, path)


def write_json(path: Path, value: Any) -> None: write_or_verify(path, canonical(value))


def normalized_hash(path: Path) -> str:
    text = path.read_text("utf-8").replace("\r\n", "\n")
    fail("\r" in text, "contract_invalid", "Contract contains an isolated CR.")
    return sha_text(text)


def tree_hash(root: Path, excluded: set[str] | None = None) -> str:
    excluded = excluded or set(); digest = hashlib.sha256()
    for path in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
        if rel in excluded or rel.endswith(".build-v8.tmp"): continue
        digest.update(rel.encode()); digest.update(b"\0"); digest.update(bytes.fromhex(sha_file(path)))
    return digest.hexdigest()


def _legacy_facts(root: Path) -> dict[str, Any]:
    old = read_json(root / "project.json", "legacy project head")
    fail(old.get("schema") == "math-research-project/v8", "already_v8", "LEGACY_SUCCESSOR is not applicable to v8.")
    project_id = old.get("project_id")
    fail(not isinstance(project_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", project_id), "legacy_head_invalid", "project_id is invalid.")
    generation = old.get("control_generation", 0)
    fail(type(generation) is not int or generation < 0, "old_generation_invalid", "Legacy generation is invalid.")
    contract_rel = (old.get("active_contract") or {}).get("path")
    fail(not isinstance(contract_rel, str), "legacy_head_invalid", "Legacy active_contract.path is missing.")
    contract_path = safe_path(root, contract_rel)
    fail(not contract_path.is_file(), "legacy_contract_missing", "Legacy Contract is missing.")
    run = old.get("active_run") or {}; run_id = run.get("id", "legacy-run")
    fail(not isinstance(run_id, str), "legacy_head_invalid", "Legacy run ID is invalid.")
    contract_text = contract_path.read_text("utf-8").replace("\r\n", "\n")
    return {"old": old, "old_hash": sha_file(root / "project.json"), "project_id": project_id,
            "generation": generation, "contract_rel": contract_rel, "contract_text": contract_text,
            "run_id": run_id}


def build_legacy_successor(project: Path, goal_raw: str, goal_sha256: str,
                           goal_thread_id: str | None = None, dry_run: bool = False) -> dict[str, Any]:
    root = project.resolve(); plain_tree(root); facts = _legacy_facts(root)
    fail(not re.fullmatch(r"[0-9a-f]{64}", goal_sha256) or sha_text(goal_raw) != goal_sha256,
         "goal_objective_hash_mismatch", "GoalObjectiveSha256 does not bind the supplied UTF-8 text.")
    old_tree = tree_hash(root); generation = facts["generation"] + 1; g = f"g{generation:04d}"
    run_id = f"successor-{g}"; run_rel = f"runs/{run_id}"
    candidate_rel = f"state/staging/legacy-successor-{g}.json"
    generated = {
        "intent": f"state/build-intents/{g}.json", "contract": f"contracts/contract-v8-{g}.md",
        "ticket": f"{run_rel}/tickets/legacy-initial-{g}.json", "run": f"{run_rel}/run.json",
        "host": f"{run_rel}/host-bindings/host-bind-{g}.json", "lineage": f"state/successors/{g}.json",
        "event": f"state/project-events/{g}.json", "checkpoint": f"state/generations/{g}/checkpoint.json",
        "state": f"state/generations/{g}/goal-host-v8.json", "candidate": candidate_rel,
    }
    prior_intent = root / generated["intent"]
    timestamp = None
    if prior_intent.exists(): timestamp = read_json(prior_intent, "build intent").get("created_at_utc")
    timestamp = timestamp or dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    intent = {"schema":"math-research-legacy-successor-build-intent/v8","builder_protocol":"staging-only-legacy-successor/v8",
              "project_id":facts["project_id"],"predecessor_project_head_sha256":facts["old_hash"],
              "predecessor_control_generation":facts["generation"],"control_generation":generation,
              "goal_host":{"thread_id_available":goal_thread_id is not None,"thread_id":goal_thread_id,"objective_raw_sha256":goal_sha256},
              "generated_paths":list(generated.values()),"created_at_utc":timestamp}
    if dry_run:
        return {"schema":"math-research-legacy-successor-build-result/v8","built":False,"reason":"dry_run_verified",
                "expected_old_sha256":facts["old_hash"],"expected_old_control_generation":str(facts["generation"]),
                "expected_new_control_generation":generation,"candidate_head_file":str(root / candidate_rel),
                "source_project_tree_sha256_before":old_tree,"source_project_tree_sha256_after":tree_hash(root)}
    write_json(prior_intent, intent)
    counters={"attempt_count":0,"audit_count":0,"total_round_count":0,"attempts_since_last_audit":0,"audit_due":False}
    policy={"schema_version":3,"protocol":"math-research-cycle-policy/v3","total_round_budget":100,"attempt_budget":100,
            "audit_interval_attempts":10,"max_route_family_attempts_per_cycle":3,"max_repair_batches_per_attempt":3,
            "allowed_worker_tools":["apply_patch","collaboration.spawn_agent","collaboration.send_message","collaboration.wait_agent","shell_command"],
            "max_ticket_tool_calls":32,"max_ticket_output_bytes":8388608,"audit_roles":["skeptic_quantifiers","skeptic_strategy","theory_tool_scout"]}
    problem_hash=sha_text(facts["contract_text"]); identity=sha_text(facts["project_id"])
    contract=("# Math Research Goal-Host Contract v8\n<!-- math-research-goal-host\n"
              f"schema: 8\nproject_id: {facts['project_id']}\ncontract_version: v8\n-->\n\n<!-- math-research-cycle-policy\n"
              + json.dumps(policy,ensure_ascii=False,separators=(",",":")) + "\n-->\n\n## Preserved predecessor Contract\n\n" + facts["contract_text"])
    write_or_verify(root/generated["contract"],contract.encode("utf-8"))
    contract_ptr={"path":generated["contract"],"version":"v8","binding_sha256":normalized_hash(root/generated["contract"])}
    run_ptr={"id":run_id,"path":run_rel,"status":"not_started"}; host_goal=intent["goal_host"]
    host={"schema":"math-research-host-binding/v8","project_id":facts["project_id"],"control_generation":generation,"event_type":"HOST_BIND",
          "prior_host_binding":None,"retirement":None,"contract":contract_ptr,"run":{"id":run_id,"path":run_rel},"host_goal":host_goal}
    write_json(root/generated["host"],host); host_ptr=pointer(root,generated["host"])
    write_json(root/generated["run"],{"schema":"math-research-run-genesis/v8","project_id":facts["project_id"],"control_generation":generation,
                                     "contract":contract_ptr,"run":run_ptr,"host_binding":host_ptr,"host_goal":host_goal})
    ticket={"schema":"math-research-frozen-ticket/v8","project_id":facts["project_id"],"control_generation":generation,"ticket":{"ticket_id":"legacy-initial"}}
    write_json(root/generated["ticket"],ticket); ticket_ptr=pointer(root,generated["ticket"])
    lineage={"schema":"math-research-legacy-successor-lineage/v8","project_id":facts["project_id"],"control_generation":generation,
             "legacy_goal_bindings_obsolete":True,"predecessor":{"project_head_sha256":facts["old_hash"],"run_id":facts["run_id"],"contract_path":facts["contract_rel"]},
             "successor":{"run_id":run_id,"run_path":run_rel}}
    write_json(root/generated["lineage"],lineage); lineage_ptr=pointer(root,generated["lineage"])
    event={"schema":"math-research-project-event/v8","project_id":facts["project_id"],"control_generation":generation,"event_id":f"LEGACY_SUCCESSOR-{g}",
           "event_type":"LEGACY_SUCCESSOR","updated_at_utc":timestamp,"previous_event_sha256":None,"contract":contract_ptr,"run":run_ptr,
           "counters":counters,"referenced_artifacts":[pointer(root,generated["intent"]),lineage_ptr]}
    write_json(root/generated["event"],event); event_ptr=pointer(root,generated["event"])
    lifecycle={"kind":"initial_ticket","id":"legacy-initial","path":generated["ticket"],"sha256":ticket_ptr["sha256"]}
    successor={"lineage":lineage_ptr}
    checkpoint={"schema":"math-research-checkpoint/v8","project_id":facts["project_id"],"control_generation":generation,"contract":contract_ptr,"run":run_ptr,
                "problem_statement_sha256":problem_hash,"host_goal":host_goal,"host_binding_head":host_ptr,"counters":counters,"current_lifecycle":lifecycle,
                "successor":successor,"completion_ready":False,"pending_goal_update":False,"last_run_event":{"id":event["event_id"],"sha256":event_ptr["sha256"]},"updated_at_utc":timestamp}
    state={"schema":"math-research-goal-host-state/v8","project_id":facts["project_id"],"control_generation":generation,"contract":contract_ptr,"run":run_ptr,
           "host_goal":host_goal,"problem_statement_sha256":problem_hash,"successor":successor,"counters":counters,
           "current_ticket":{"id":"legacy-initial","path":generated["ticket"],"sha256":ticket_ptr["sha256"],"status":"ready"},"updated_at_utc":timestamp}
    write_json(root/generated["checkpoint"],checkpoint); write_json(root/generated["state"],state)
    head={"schema":"math-research-project/v8","project_id":facts["project_id"],"project_identity_sha256":identity,"problem_statement_sha256":problem_hash,
          "control_generation":generation,"active_checkpoint":pointer(root,generated["checkpoint"]),"goal_host_state":pointer(root,generated["state"]),
          "project_event_head":event_ptr,"host_binding_head":host_ptr,"active_contract":contract_ptr,"active_run":run_ptr,"legacy_successor":lineage_ptr}
    write_json(root/candidate_rel,head)
    fail(sha_file(root/"project.json") != facts["old_hash"], "head_mutated", "Staging changed project.json.")
    return {"schema":"math-research-legacy-successor-build-result/v8","built":True,"reason":"staged_successor_ready_for_goal_gated_commit",
            "expected_old_sha256":facts["old_hash"],"expected_old_control_generation":str(facts["generation"]),"expected_new_control_generation":generation,
            "candidate_head_file":str(root/candidate_rel),"candidate_head_sha256":sha_file(root/candidate_rel),"source_project_tree_sha256_before":old_tree,
            "source_project_tree_sha256_after":tree_hash(root)}


def _candidate_basics(root: Path, candidate: Path, generation: int, project_id: str) -> dict[str, Any]:
    rel=candidate.relative_to(root).as_posix()
    fail(not re.fullmatch(r"state/(?:staging(?:/[A-Za-z0-9._-]+)+|generations/g[0-9]{4,}(?:/[A-Za-z0-9._-]+)+)\.json",rel),"unsafe_candidate_path","Candidate must be safe JSON under state/staging or state/generations.")
    value=read_json(candidate,"candidate project head")
    required={"schema","project_id","project_identity_sha256","problem_statement_sha256","control_generation","active_checkpoint","goal_host_state","project_event_head","host_binding_head","active_contract","active_run","legacy_successor"}
    fail(set(value)!=required or value.get("schema")!="math-research-project/v8","candidate_schema_invalid","Candidate has the wrong exact schema.")
    fail(value.get("project_id")!=project_id or value.get("control_generation")!=generation,"candidate_generation_invalid","Candidate identity/generation differs.")
    for key in ("active_checkpoint","goal_host_state","project_event_head","host_binding_head","legacy_successor"):
        item=value[key]; fail(not isinstance(item,dict) or set(item)!={"path","sha256"},"candidate_pointer_invalid",f"{key} is invalid.")
        path=safe_path(root,item["path"]); fail(not path.is_file() or sha_file(path)!=item["sha256"],"candidate_pointer_invalid",f"{key} hash differs.")
    contract=value["active_contract"]; path=safe_path(root,contract["path"])
    fail(normalized_hash(path)!=contract.get("binding_sha256"),"contract_hash_mismatch","Candidate Contract hash differs.")
    return value


def commit_head(project: Path, candidate_file: Path, expected_old_sha256: str,
                expected_old_generation: str, expected_new_generation: int) -> dict[str, Any]:
    root=project.resolve(); plain_tree(root); live=root/"project.json"; candidate=candidate_file.resolve()
    fail(root not in candidate.parents,"unsafe_candidate_path","Candidate is outside ProjectDirectory.")
    fail(not re.fullmatch(r"[0-9a-f]{64}",expected_old_sha256),"stale_hash","ExpectedOldSha256 must be lowercase SHA-256.")
    fail(not live.is_file() or sha_file(live)!=expected_old_sha256,"stale_hash","Current project head differs from expected hash.")
    old=read_json(live,"current project head"); old_gen=old.get("control_generation",0)
    fail(str(old_gen)!=expected_old_generation,"stale_generation","Current generation differs from expected generation.")
    fail(expected_new_generation!=old_gen+1,"generation_not_successor","New generation must be exactly old+1.")
    value=_candidate_basics(root,candidate,expected_new_generation,old.get("project_id")); candidate_hash=sha_file(candidate)
    lock=root/".project-head-v8.lock"
    try: fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError: raise HeadV8Error("commit_locked","Another head commit holds the lock.")
    temp: Path|None=None
    try:
        os.write(fd,canonical({"schema":"math-research-head-lock/v8","expected_old_sha256":expected_old_sha256})); os.fsync(fd); os.close(fd)
        fail(sha_file(live)!=expected_old_sha256,"stale_hash","Head changed before CAS.")
        fail(sha_file(candidate)!=candidate_hash,"candidate_changed","Candidate changed before CAS.")
        backup=root/f".project.json.g{old_gen:04d}.bak"; write_or_verify(backup,live.read_bytes())
        temp_fd,temp_name=tempfile.mkstemp(prefix=".project.json.",suffix=".tmp",dir=root)
        os.close(temp_fd); temp=Path(temp_name)
        with open(temp,"wb") as stream: stream.write(candidate.read_bytes()); stream.flush(); os.fsync(stream.fileno())
        os.replace(temp,live); temp=None
        try:
            from math_research_migrate_v8_to_v10 import _read_v8
            verified=_read_v8(root)
            fail(verified["head_hash"]!=candidate_hash,"post_commit_verification_failed","Committed hash differs.")
        except Exception as exc:
            os.replace(backup,live)
            if isinstance(exc,HeadV8Error): raise
            raise HeadV8Error("post_commit_verification_failed",str(exc)) from exc
        return {"schema":"math-research-head-commit-result/v8","committed":True,"reason":"committed","project_json":str(live),
                "old_sha256":expected_old_sha256,"candidate_sha256":candidate_hash,"new_sha256":sha_file(live),
                "old_control_generation":old_gen,"new_control_generation":expected_new_generation,"trust":"local_atomic_project_head_cas_not_goal_authorization"}
    finally:
        if temp and temp.exists(): temp.unlink()
        if lock.exists(): lock.unlink()
