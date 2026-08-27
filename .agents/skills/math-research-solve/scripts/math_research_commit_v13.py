#!/usr/bin/env python3
"""Journaled, conditional-rollback CAS commit Harness for v13 project writes."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import time
import uuid
from pathlib import Path, PurePosixPath
from typing import Any

from attempt_package_preflight_v13 import RECEIPT_NAME, validate_package_mapping
from v13_common import V13Error, canonical_json, configure_stdio, emit, error_result, inventory, is_sha256, load_json, load_json_bytes, resolved_child, sha256_bytes, sha256_file

PLAN_FIELDS = {
    "schema", "expected_project_head_sha256", "expected_execution_head_sha256",
    "expected_research_authority_head_sha256", "staging_inventory_sha256",
    "plan_sha256", "writes",
}
WRITE_FIELDS = {"path", "source", "sha256", "immutable", "expected_old_sha256"}
PLAN_HASH_FIELDS = (
    "schema", "expected_project_head_sha256", "expected_execution_head_sha256",
    "expected_research_authority_head_sha256", "staging_inventory_sha256", "writes",
)


def require(condition: bool, code: str, message: str, path: str | None = None) -> None:
    if not condition:
        raise V13Error(code, message, path)


def _inventory_sha(root: Path) -> str:
    return sha256_bytes(canonical_json(inventory(root)))


def _current_heads(project: Path) -> tuple[str, dict[str, Any]]:
    head_path = project / "project.json"
    require(head_path.is_file(), "project_head_missing", "project.json is missing")
    head = load_json(head_path, canonical_required=True)
    require(head.get("schema") == "math-research-project/v13", "project_schema_invalid", "Not a v13 project")
    return sha256_file(head_path), head


def _walk_forbidden_final_binding(value: Any, final_sha: str, source: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"final_project_head_sha256", "candidate_project_head_sha256", "same_generation_project_head_sha256"} and item == final_sha:
                raise V13Error("cyclic_head_binding", "Candidate object reverse-binds the same-generation final head", source)
            _walk_forbidden_final_binding(item, final_sha, source)
    elif isinstance(value, list):
        for item in value:
            _walk_forbidden_final_binding(item, final_sha, source)


def _target_bytes(project: Path, staging: Path, target_rows: dict[str, dict[str, Any]], rel: str) -> bytes:
    if rel in target_rows:
        source = resolved_child(staging, target_rows[rel]["source"], require_existing=True)
        return source.read_bytes()
    target = resolved_child(project, rel, require_existing=True)
    require(target.is_file(), "attempt_package_pointer_missing", "Attempt-package pointer target is not a file", rel)
    return target.read_bytes()


def _validate_candidate_map_review(
    project: Path,
    staging: Path,
    target_rows: dict[str, dict[str, Any]],
    current: dict[str, Any],
    candidate_project: dict[str, Any],
) -> None:
    """Validate map-review closure against the exact post-commit byte view."""
    authority_changed = candidate_project["research_authority_head"] != current["research_authority_head"]
    map_bytes_changed = any(path == "研究地图" or path.startswith("研究地图/") for path in target_rows)
    if not authority_changed and not map_bytes_changed:
        # Execution-only commits may finish an already-active window frozen on
        # legacy authority.  The next authority/map publication is still gated.
        return

    authority = load_json_bytes(
        _target_bytes(project, staging, target_rows, candidate_project["research_authority_head"]["path"]),
        canonical_required=True,
    )
    require(authority.get("schema") == "math-research-authority-head/v13", "authority_head_invalid", "Candidate authority schema invalid")
    closure_pointer = authority.get("independent_semantic_review")
    require(isinstance(closure_pointer, dict) and set(closure_pointer) == {"path", "sha256"} and is_sha256(closure_pointer.get("sha256")), "map_review_closure_missing", "Candidate authority must bind a map-review closure")
    closure_bytes = _target_bytes(project, staging, target_rows, closure_pointer["path"])
    require(sha256_bytes(closure_bytes) == closure_pointer["sha256"], "map_review_closure_mismatch", "Candidate authority closure pointer differs from candidate bytes")
    closure = load_json_bytes(closure_bytes, canonical_required=True)
    require(closure.get("schema") == "math-research-map-review-closure/v1", "map_review_closure_invalid", "Thin semantic-review receipts cannot publish a research map")
    try:
        from map_semantic_review_v1 import validate_closure_document
    except ImportError as exc:
        raise V13Error("map_review_harness_unavailable", "Map semantic-review Harness is unavailable") from exc

    def read_bytes(rel: str) -> bytes:
        return _target_bytes(project, staging, target_rows, PurePosixPath(rel).as_posix())

    result = validate_closure_document(project, closure, read_bytes=read_bytes, expected_closure_path=closure_pointer["path"])
    require(isinstance(result, dict) and result.get("ok") is True, "map_review_closure_invalid", "Candidate map-review closure failed exact staged-overlay validation")


def _package_files(project: Path, staging: Path, target_rows: dict[str, dict[str, Any]], prefix: str) -> dict[str, bytes]:
    marker = prefix + "/"
    files: dict[str, bytes] = {}
    existing = resolved_child(project, prefix)
    if existing.exists():
        require(existing.is_dir(), "attempt_package_root_invalid", "Attempt package root must be a directory", prefix)
        for row in inventory(existing):
            files[row["path"]] = (existing / PurePosixPath(row["path"])).read_bytes()
    for target, row in target_rows.items():
        if target.startswith(marker):
            require(row["immutable"] is True, "attempt_package_write_mutable", "Attempt package files must be immutable commit writes", target)
            files[target[len(marker):]] = resolved_child(staging, row["source"], require_existing=True).read_bytes()
    return files


def _validate_attempt_preflights(project: Path, staging: Path, target_rows: dict[str, dict[str, Any]], execution: dict[str, Any]) -> None:
    attempts = execution.get("active_attempts")
    if not isinstance(attempts, list):
        return
    for attempt in attempts:
        closing = attempt.get("closing") if isinstance(attempt, dict) else None
        if not isinstance(closing, dict):
            continue
        refs = closing.get("artifact_refs")
        require(isinstance(refs, list), "attempt_package_preflight_missing", "Closing attempt artifact_refs are missing")
        receipt_refs = [ref for ref in refs if isinstance(ref, dict) and isinstance(ref.get("path"), str) and ref["path"].endswith("/" + RECEIPT_NAME)]
        require(len(receipt_refs) == 1, "attempt_package_preflight_missing", "Exactly one attempt-package preflight receipt is required")
        receipt_path = receipt_refs[0]["path"]
        prefix = PurePosixPath(receipt_path).parent.as_posix()
        package_files = _package_files(project, staging, target_rows, prefix)
        require(RECEIPT_NAME in package_files, "attempt_package_preflight_missing", "Preflight receipt bytes are absent from the commit dependency closure", receipt_path)
        validate_package_mapping(
            package_files,
            expected_closing=closing,
            external_reader=lambda rel: _target_bytes(project, staging, target_rows, rel),
        )
        package = attempt.get("package")
        if isinstance(package, dict):
            require(package.get("artifact_refs") == closing["artifact_refs"], "attempt_package_lineage_mismatch", "Ready package changed the preflight-bound artifact refs")


def validate_plan(project: Path, staging: Path, plan_path: Path) -> dict[str, Any]:
    require(project.is_dir() and staging.is_dir(), "root_missing", "Project and staging directories are required")
    plan = load_json(plan_path, canonical_required=True)
    require(isinstance(plan, dict) and set(plan) == PLAN_FIELDS and plan.get("schema") == "math-research-commit-plan/v13", "plan_schema_invalid", "Commit plan schema/fields invalid")
    payload = {key: plan[key] for key in PLAN_HASH_FIELDS}
    require(plan["plan_sha256"] == sha256_bytes(canonical_json(payload)), "plan_hash_mismatch", "Plan SHA mismatch")
    for key in ("expected_project_head_sha256", "expected_execution_head_sha256", "expected_research_authority_head_sha256", "staging_inventory_sha256", "plan_sha256"):
        require(is_sha256(plan[key]), "plan_hash_invalid", f"{key} invalid")
    project_sha, current = _current_heads(project)
    require(project_sha == plan["expected_project_head_sha256"], "cas_failed", "Expected project head is no longer current")
    require(current.get("project_complete") is not True, "project_closed", "Completed project authority is immutable")
    require(current["execution_state_head"]["sha256"] == plan["expected_execution_head_sha256"] and current["research_authority_head"]["sha256"] == plan["expected_research_authority_head_sha256"], "component_cas_failed", "Expected execution/research head is no longer current")
    require(project.stat().st_dev == staging.stat().st_dev, "cross_volume_staging", "Staging must be on the same volume")
    actual_inventory = inventory(staging)
    require(plan["staging_inventory_sha256"] == sha256_bytes(canonical_json(actual_inventory)), "staging_inventory_mismatch", "Full staging inventory changed")
    require(isinstance(plan["writes"], list) and plan["writes"], "writes_missing", "Commit writes are empty")
    paths: set[str] = set(); sources: set[str] = set(); folded_paths: set[str] = set()
    final_sha: str | None = None
    for index, row in enumerate(plan["writes"]):
        require(isinstance(row, dict) and set(row) == WRITE_FIELDS, "write_invalid", "Write entry fields invalid")
        require(isinstance(row["path"], str) and isinstance(row["source"], str) and is_sha256(row["sha256"]) and isinstance(row["immutable"], bool), "write_invalid", "Write entry types invalid")
        require(row["expected_old_sha256"] is None or is_sha256(row["expected_old_sha256"]), "write_invalid", "expected_old_sha256 invalid")
        require(row["path"] not in paths and row["source"] not in sources and row["path"].casefold() not in folded_paths, "duplicate_write", "Duplicate/case-colliding write", row["path"])
        paths.add(row["path"]); sources.add(row["source"]); folded_paths.add(row["path"].casefold())
        target = resolved_child(project, row["path"]); source = resolved_child(staging, row["source"], require_existing=True)
        require(source.is_file() and sha256_file(source) == row["sha256"], "staging_hash_mismatch", "Staged source hash mismatch", row["source"])
        if target.exists():
            old_sha = sha256_file(target)
            if row["immutable"]:
                require(old_sha == row["sha256"], "immutable_overwrite", "Immutable target already exists with different bytes", row["path"])
            else:
                require(row["expected_old_sha256"] == old_sha, "target_cas_failed", "Mutable target expected-old hash differs", row["path"])
        else:
            require(row["expected_old_sha256"] is None, "target_cas_failed", "Absent target must have null expected-old", row["path"])
        if row["path"] == "project.json":
            require(index == len(plan["writes"]) - 1 and row["immutable"] is False and row["expected_old_sha256"] == plan["expected_project_head_sha256"], "head_not_last", "Mutable project.json with expected-old must be last")
            final_sha = row["sha256"]
    require(plan["writes"][-1]["path"] == "project.json", "head_not_last", "project.json must be last")
    require(sources == {row["path"] for row in actual_inventory}, "unknown_staging_file", "Every staged file must be named exactly once by the plan")
    candidate_project = load_json(resolved_child(staging, plan["writes"][-1]["source"], require_existing=True), canonical_required=True)
    require(candidate_project.get("schema") == "math-research-project/v13" and candidate_project.get("generation") == current["generation"] + 1, "candidate_project_invalid", "Candidate project schema/generation invalid")
    require(candidate_project.get("objective_commitment_sha256") == current["objective_commitment_sha256"] and candidate_project.get("project_id") == current["project_id"] and candidate_project.get("created_at_utc") == current["created_at_utc"], "candidate_identity_changed", "Candidate changed permanent project identity")
    require(isinstance(candidate_project.get("project_complete"), bool) and isinstance(candidate_project.get("pending_goal_update"), bool) and (not candidate_project["project_complete"] or candidate_project["pending_goal_update"]), "candidate_completion_flags_invalid", "A complete candidate must retain pending_goal_update=true")
    target_rows = {row["path"]: row for row in plan["writes"]}
    for key in ("objective", "research_authority_head", "execution_state_head"):
        pointer = candidate_project.get(key)
        require(isinstance(pointer, dict) and set(pointer) == {"path", "sha256"} and is_sha256(pointer["sha256"]), "candidate_pointer_invalid", f"Candidate {key} pointer invalid")
        if pointer["path"] in target_rows:
            require(target_rows[pointer["path"]]["sha256"] == pointer["sha256"], "candidate_pointer_mismatch", f"Candidate {key} does not bind staged bytes")
        else:
            existing = resolved_child(project, pointer["path"], require_existing=True)
            require(existing.is_file() and sha256_file(existing) == pointer["sha256"], "candidate_pointer_mismatch", f"Candidate {key} does not bind existing bytes")
    candidate_execution = load_json_bytes(_target_bytes(project, staging, target_rows, candidate_project["execution_state_head"]["path"]), canonical_required=True)
    _validate_attempt_preflights(project, staging, target_rows, candidate_execution)
    _validate_candidate_map_review(project, staging, target_rows, current, candidate_project)
    require(final_sha is not None, "head_not_last", "Final head missing")
    for row in plan["writes"][:-1]:
        source = resolved_child(staging, row["source"], require_existing=True)
        try:
            value = load_json(source, canonical_required=True)
        except V13Error as exc:
            if exc.code == "invalid_json":
                continue
            raise
        _walk_forbidden_final_binding(value, final_sha, row["source"])
    return {"ok": True, "plan_sha256": plan["plan_sha256"], "writes": len(plan["writes"]), "inventory_files": len(actual_inventory), "candidate_project_head_sha256": final_sha}


def _write_journal(path: Path, value: dict[str, Any]) -> None:
    temp = path.with_name(path.name + ".tmp")
    temp.write_bytes(canonical_json(value)); os.replace(temp, path)


def commit(project: Path, staging: Path, plan_path: Path, journal_dir: Path, goal_state: str) -> dict[str, Any]:
    require(goal_state == "active", "goal_gate_closed", "Local Goal gate is not active; it never replaces Host fresh get_goal")
    checked = validate_plan(project, staging, plan_path); plan = load_json(plan_path, canonical_required=True)
    journal_dir.mkdir(parents=True, exist_ok=True)
    lock_dir = project / ".research" / "locks"; lock_dir.mkdir(parents=True, exist_ok=True)
    lock = lock_dir / "commit-v13.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise V13Error("named_lock_busy", "Stable project commit lock is busy") from exc
    transaction_id = uuid.uuid4().hex
    backups = journal_dir / ("rollback-" + transaction_id); backups.mkdir()
    journal_path = journal_dir / ("journal-" + transaction_id + ".json")
    applied: list[dict[str, Any]] = []
    journal: dict[str, Any] = {"schema": "math-research-commit-journal/v13", "transaction_id": transaction_id, "status": "applying", "plan_sha256": checked["plan_sha256"], "expected_project_head_sha256": plan["expected_project_head_sha256"], "applied": applied, "rollback_conflicts": []}
    recovery_required = False
    try:
        os.close(fd); _write_journal(journal_path, journal)
        # Recheck after lock acquisition.  A non-cooperating writer is still detected by CAS.
        validate_plan(project, staging, plan_path)
        for row in plan["writes"]:
            target = resolved_child(project, row["path"]); source = resolved_child(staging, row["source"], require_existing=True)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and row["immutable"] and sha256_file(target) == row["sha256"]:
                applied.append({"path": row["path"], "sha256": row["sha256"], "action": "verified_existing"}); _write_journal(journal_path, journal); continue
            if target.exists():
                backup = backups / row["path"]; backup.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(target, backup)
            temp = target.with_name(target.name + ".v13tmp-" + transaction_id); shutil.copy2(source, temp)
            require(sha256_file(temp) == row["sha256"], "readback_failed", "Temporary readback failed", row["path"])
            os.replace(temp, target)
            require(sha256_file(target) == row["sha256"], "readback_failed", "Committed readback failed", row["path"])
            applied.append({"path": row["path"], "sha256": row["sha256"], "action": "written"}); _write_journal(journal_path, journal)
        require(sha256_file(project / "project.json") == checked["candidate_project_head_sha256"], "final_readback_failed", "Final project head readback failed")
        journal.update({"status": "committed", "committed_at_unix": int(time.time())}); _write_journal(journal_path, journal)
        return {"ok": True, "status": "committed", "plan_sha256": checked["plan_sha256"], "writes": len(applied), "new_project_head_sha256": checked["candidate_project_head_sha256"], "journal_id": journal_path.stem}
    except Exception:
        for entry in reversed(applied):
            if entry["action"] != "written":
                continue
            rel = entry["path"]; target = resolved_child(project, rel); backup = backups / rel
            if not target.exists() or sha256_file(target) != entry["sha256"]:
                journal["rollback_conflicts"].append(rel); recovery_required = True; continue
            if backup.exists(): shutil.copy2(backup, target)
            else: target.unlink()
        journal["status"] = "recovery_required" if recovery_required else "rolled_back"; _write_journal(journal_path, journal)
        raise
    finally:
        try: lock.unlink(missing_ok=True)
        except OSError: pass


def main() -> int:
    configure_stdio(); parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "commit"):
        command = sub.add_parser(name); command.add_argument("--project", type=Path, required=True); command.add_argument("--staging", type=Path, required=True); command.add_argument("--plan", type=Path, required=True)
        if name == "commit": command.add_argument("--journal-dir", type=Path, required=True); command.add_argument("--goal-state", required=True)
    args = parser.parse_args()
    try:
        result = validate_plan(args.project, args.staging, args.plan) if args.command == "validate" else commit(args.project, args.staging, args.plan, args.journal_dir, args.goal_state)
        return emit(result)
    except Exception as exc:
        value, code = error_result(exc); return emit(value, code)


if __name__ == "__main__":
    raise SystemExit(main())
