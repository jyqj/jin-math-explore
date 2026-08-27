#!/usr/bin/env python3
"""Receipt-bound, additive migration of a live v8 archive into a v10 successor.

The predecessor head is never rewritten.  A migration plan first freezes an exact
v8 snapshot, then the same freeze record is installed create-new in the predecessor
before the v10 plan may be committed.  Official v8 writers reject that marker and
v10 ATTEMPT_START independently reopens it.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import stat
import sys
import time
from pathlib import Path
from typing import Any

import math_research_state_v10 as mr


FREEZE_REL = "state/migration-freeze-v10.json"
FREEZE_COPY_REL = "lineage/predecessor-v8/freeze-record.json"
MIGRATION_MANIFEST_REL = "lineage/predecessor-v8/migration-manifest.json"
ENVELOPE_REL = "lineage/predecessor-v8/envelope-snapshot.json"
LINEAGE_REL = "lineage/predecessor-v8/lineage.json"


def _exact(value: Any, keys: tuple[str, ...], label: str) -> dict[str, Any]:
    return mr.require_exact(value, keys, label)


def _pointer(root: Path, value: Any, label: str) -> tuple[str, Path]:
    return mr.pointer(value, root, label)


def _normalized_text_hash(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise mr.ResearchError("v8_contract_unreadable", f"Cannot read the v8 contract: {exc}") from exc
    text = text.replace("\r\n", "\n")
    mr.fail("\r" in text, "v8_contract_invalid", "The v8 contract contains an isolated CR.")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _cycle_policy(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    matches = re.findall(r"<!-- math-research-cycle-policy\n(.*?)\n-->", text, flags=re.S)
    mr.fail(len(matches) != 1, "v8_contract_invalid", "The v8 contract must contain one cycle-policy block.")
    try:
        value = json.loads(matches[0], object_pairs_hook=mr._pairs_no_duplicates)
    except Exception as exc:
        raise mr.ResearchError("v8_contract_invalid", f"The v8 cycle-policy block is invalid: {exc}") from exc
    required = (
        "schema_version", "protocol", "total_round_budget", "attempt_budget",
        "audit_interval_attempts", "max_route_family_attempts_per_cycle",
        "max_repair_batches_per_attempt", "allowed_worker_tools",
        "max_ticket_tool_calls", "max_ticket_output_bytes", "audit_roles",
    )
    policy = _exact(value, required, "v8 cycle policy")
    for key in ("total_round_budget", "attempt_budget", "audit_interval_attempts"):
        mr.fail(type(policy[key]) is not int or policy[key] < 0, "v8_contract_invalid", f"{key} is invalid.")
    return policy


def _assert_plain_tree(root: Path) -> None:
    mr.fail(not root.is_dir(), "predecessor_missing", "The v8 predecessor directory is absent.")
    for path in [root, *root.rglob("*")]:
        try:
            attrs = path.lstat().st_file_attributes if hasattr(path.lstat(), "st_file_attributes") else 0
        except OSError as exc:
            raise mr.ResearchError("predecessor_unreadable", f"Cannot inspect predecessor path: {path.name}: {exc}") from exc
        is_reparse = bool(attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
        mr.fail(path.is_symlink() or is_reparse, "migration_reparse_forbidden", f"Reparse points are forbidden: {path}")


def _read_v8(root: Path) -> dict[str, Any]:
    _assert_plain_tree(root)
    head_path = root / "project.json"
    mr.fail(not head_path.is_file(), "predecessor_missing", "The v8 predecessor project.json is absent.")
    head = mr.load_json(head_path)
    required = (
        "schema", "project_id", "project_identity_sha256", "problem_statement_sha256",
        "control_generation", "active_checkpoint", "goal_host_state", "project_event_head",
        "host_binding_head", "active_contract", "active_run", "legacy_successor",
    )
    _exact(head, required, "v8 project head")
    mr.fail(head["schema"] != "math-research-project/v8", "predecessor_not_v8", "Predecessor is not v8.")
    mr.require_id(head["project_id"], "v8 project id")
    mr.require_hash(head["problem_statement_sha256"], "v8 problem statement hash")
    mr.fail(type(head["control_generation"]) is not int or head["control_generation"] < 1, "v8_head_invalid", "v8 generation is invalid.")
    head_hash = mr.sha_file(head_path)
    _, checkpoint_path = _pointer(root, {"path": head["active_checkpoint"]["path"], "sha256": head["active_checkpoint"]["sha256"]}, "v8 checkpoint")
    checkpoint = mr.load_json(checkpoint_path)
    _exact(checkpoint, ("schema", "project_id", "control_generation", "contract", "run", "problem_statement_sha256", "host_goal", "host_binding_head", "counters", "current_lifecycle", "successor", "completion_ready", "pending_goal_update", "last_run_event", "updated_at_utc"), "v8 checkpoint")
    mr.fail(checkpoint["schema"] != "math-research-checkpoint/v8" or checkpoint["project_id"] != head["project_id"] or checkpoint["control_generation"] != head["control_generation"], "v8_head_invalid", "v8 checkpoint identity differs from the head.")
    counters = _exact(checkpoint["counters"], ("attempt_count", "audit_count", "total_round_count", "attempts_since_last_audit", "audit_due"), "v8 counters")
    for key in ("attempt_count", "audit_count", "total_round_count", "attempts_since_last_audit"):
        mr.fail(type(counters[key]) is not int or counters[key] < 0, "counter_invalid", f"v8 {key} is invalid.")
    mr.fail(counters["total_round_count"] != counters["attempt_count"] + counters["audit_count"], "counter_invalid", "v8 round counters are inconsistent.")
    run = _exact(head["active_run"], ("id", "path", "status"), "v8 active run")
    mr.require_id(run["id"], "v8 run id")
    mr.fail(run != checkpoint["run"], "v8_head_invalid", "v8 run differs between head and checkpoint.")
    contract = _exact(head["active_contract"], ("path", "version", "binding_sha256"), "v8 contract pointer")
    mr.require_hash(contract["binding_sha256"], "v8 contract binding")
    contract_path = mr.resolve_under(root, contract["path"], "v8 contract")
    mr.fail(_normalized_text_hash(contract_path) != contract["binding_sha256"], "v8_contract_hash_mismatch", "v8 contract binding differs from live bytes.")
    policy = _cycle_policy(contract_path)
    remaining_attempts = policy["attempt_budget"] - counters["attempt_count"]
    remaining_rounds = policy["total_round_budget"] - counters["total_round_count"]
    mr.fail(remaining_attempts < 0 or remaining_rounds < 0, "budget_invalid", "v8 counters exceed the frozen budget.")
    lifecycle = _exact(checkpoint["current_lifecycle"], ("kind", "id", "path", "sha256"), "v8 current lifecycle")
    _, lifecycle_path = _pointer(root, {"path": lifecycle["path"], "sha256": lifecycle["sha256"]}, "v8 current lifecycle")
    event_rel, event_path = _pointer(root, {"path": head["project_event_head"]["path"], "sha256": head["project_event_head"]["sha256"]}, "v8 event head")
    event = mr.load_json(event_path)
    asset_pointer = None
    for item in event.get("referenced_artifacts", []):
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            continue
        try:
            candidate = mr.load_json(mr.resolve_under(root, item["path"], "v8 referenced artifact"))
        except mr.ResearchError:
            continue
        if isinstance(candidate, dict) and candidate.get("schema") == "math-research-asset-index/v1":
            asset_pointer = {"path": item["path"], "sha256": item["sha256"]}
            break
    return {
        "root": root,
        "head": head,
        "head_hash": head_hash,
        "checkpoint": checkpoint,
        "counters": counters,
        "run": run,
        "contract": contract,
        "contract_path": contract_path,
        "policy": policy,
        "remaining_attempts": remaining_attempts,
        "remaining_rounds": remaining_rounds,
        "lifecycle": lifecycle,
        "lifecycle_path": lifecycle_path,
        "event_path": event_rel,
        "asset_index": asset_pointer,
    }


def _inventory(root: Path, head_generation: int, asset_paths: set[str]) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    entries: list[dict[str, Any]] = []
    groups = {key: [] for key in ("attempts", "audits", "routes", "evidence", "assets", "unreferenced_recovery_candidates", "staging")}
    generation_re = re.compile(r"(?:^|/)(?:g|generation-?)(\d{4,})(?:/|\.|$)", re.I)
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
        lowered = rel.lower()
        tags: list[str] = []
        if "/staging/" in f"/{lowered}/":
            tags.append("staging")
        match = generation_re.search(lowered)
        if match and int(match.group(1)) > head_generation:
            tags.append("unreferenced_recovery_candidate")
        if "attempt" in lowered or "/tickets/" in f"/{lowered}/":
            tags.append("attempt")
        if "audit" in lowered:
            tags.append("audit")
        if "route" in lowered or "portfolio" in lowered:
            tags.append("route")
        if any(token in lowered for token in ("evidence", "candidate", "verifier", "solver-result", "source")):
            tags.append("evidence")
        if rel in asset_paths:
            tags.append("asset")
        tags = sorted(set(tags)) or ["archive"]
        entry = {"path": rel, "sha256": mr.sha_file(path), "size": path.stat().st_size, "tags": tags}
        entries.append(entry)
        for tag, key in (("attempt", "attempts"), ("audit", "audits"), ("route", "routes"), ("evidence", "evidence"), ("asset", "assets"), ("unreferenced_recovery_candidate", "unreferenced_recovery_candidates"), ("staging", "staging")):
            if tag in tags:
                groups[key].append(rel)
    return entries, groups


def _copy_to_stage(source: Path, stage_root: Path, target_rel: str, expected_hash: str, stamp: int) -> dict[str, Any]:
    rel = mr.safe_relative(target_rel, "migration target")
    mr.require_hash(expected_hash, "migration source hash")
    mr.fail(not source.is_file(), "migration_input_missing", f"Migration input is absent: {source}")
    mr.fail(mr.sha_file(source) != expected_hash, "migration_input_hash_mismatch", f"Migration input hash differs: {source.name}")
    data = source.read_bytes()
    target = stage_root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    os.utime(target, ns=(stamp, stamp))
    return {"target": rel, "source": str(target.resolve()), "sha256": expected_hash, "size": len(data), "mtime_ns": stamp}


def _write_value(stage_root: Path, rel: str, value: Any, stamp: int) -> dict[str, Any]:
    info = mr._write_stage(stage_root / rel, value, stamp)
    return {"target": rel, **info}


def _asset_closure(v8: dict[str, Any]) -> list[dict[str, str]]:
    pointer = v8["asset_index"]
    if pointer is None:
        return []
    try:
        return mr.asset_index_closure(pointer, v8["root"], v8["head"]["project_id"])
    except mr.ResearchError:
        raise
    except Exception as exc:
        raise mr.ResearchError("asset_index_invalid", f"Cannot validate the inherited v8 asset index: {exc}") from exc


def inspect_v8(predecessor: Path) -> dict[str, Any]:
    root = predecessor.resolve()
    v8 = _read_v8(root)
    envelope = {"contract_binding_sha256": v8["contract"]["binding_sha256"], "problem_statement_sha256": v8["head"]["problem_statement_sha256"]}
    permission = {"contract_binding_sha256": v8["contract"]["binding_sha256"], "allowed_worker_tools": v8["policy"]["allowed_worker_tools"]}
    resource = {"contract_binding_sha256": v8["contract"]["binding_sha256"], "cycle_policy": v8["policy"]}
    return {
        "classification": "v8_incremental_migration_ready",
        "project_id": v8["head"]["project_id"],
        "head_sha256": v8["head_hash"],
        "control_generation": v8["head"]["control_generation"],
        "run_id": v8["run"]["id"],
        "run_status": v8["run"]["status"],
        "counters": {key: v8["counters"][key] for key in ("attempt_count", "audit_count", "total_round_count", "attempts_since_last_audit")},
        "remaining_budgets": {"attempt_budget": v8["remaining_attempts"], "total_round_budget": v8["remaining_rounds"]},
        "envelope_sha256": mr.sha_bytes(mr.canonical_bytes(envelope)),
        "permission_envelope_sha256": mr.sha_bytes(mr.canonical_bytes(permission)),
        "resource_envelope_sha256": mr.sha_bytes(mr.canonical_bytes(resource)),
        "asset_index": v8["asset_index"],
        "current_lifecycle": {key: v8["lifecycle"][key] for key in ("kind", "id", "path", "sha256")},
    }


def prepare(predecessor: Path, successor: Path, bootstrap_path: Path, output: Path) -> dict[str, Any]:
    pred = predecessor.resolve()
    succ = successor.resolve()
    mr.fail(pred == succ or pred in succ.parents or succ in pred.parents, "migration_path_invalid", "Predecessor and successor must be distinct sibling directories.")
    mr.fail(pred.parent != succ.parent, "migration_path_invalid", "Incremental migration requires sibling v8 and v10 directories under one migration boundary.")
    mr.fail((succ / "project.json").exists(), "successor_exists", "The v10 successor already has project.json.")
    v8 = _read_v8(pred)
    bootstrap = mr.load_json(bootstrap_path)
    _exact(bootstrap, ("schema", "successor_run_id", "initial_ticket", "initial_capsule", "initial_route_card", "copy_artifacts", "occurred_at_utc"), "v8 migration bootstrap")
    mr.fail(bootstrap["schema"] != "math-research-v8-incremental-migration-bootstrap/v10", "migration_bootstrap_invalid", "Migration bootstrap schema is invalid.")
    mr.require_timestamp(bootstrap["occurred_at_utc"], "migration occurred_at_utc")
    run_id = mr.require_id(bootstrap["successor_run_id"], "successor run id")
    mr.fail(run_id == v8["run"]["id"], "migration_bootstrap_invalid", "Successor run ID must differ from the v8 run ID.")
    stage_root = output.resolve()
    mr.fail(stage_root == pred or pred in stage_root.parents or stage_root == succ or succ in stage_root.parents, "stage_invalid", "Migration staging must be outside both project roots.")
    stage_root.mkdir(parents=True, exist_ok=True)
    mr.fail(any(stage_root.iterdir()), "stage_not_empty", "Migration staging must be empty.")
    stamp = time.time_ns()
    immutable: list[dict[str, Any]] = []
    copied: dict[str, str] = {}

    def copy_source(source_rel: str, target_rel: str, expected_hash: str) -> None:
        nonlocal stamp
        source_path = mr.resolve_under(pred, source_rel, "migration source")
        target = mr.safe_relative(target_rel, "migration target")
        prior = copied.get(target)
        mr.fail(prior is not None and prior != expected_hash, "migration_target_collision", f"Migration target collision: {target}")
        if prior is None:
            immutable.append(_copy_to_stage(source_path, stage_root, target, expected_hash, stamp))
            copied[target] = expected_hash
            stamp += 1

    items = bootstrap["copy_artifacts"]
    mr.fail(not isinstance(items, list), "migration_bootstrap_invalid", "copy_artifacts must be an array.")
    for item in items:
        record = _exact(item, ("source_path", "target_path", "sha256"), "migration copy artifact")
        copy_source(record["source_path"], record["target_path"], record["sha256"])
    copy_source(v8["contract"]["path"], v8["contract"]["path"], mr.sha_file(v8["contract_path"]))

    asset_closure = _asset_closure(v8)
    asset_paths = {item["path"] for item in asset_closure}
    for item in asset_closure:
        copy_source(item["path"], item["path"], item["sha256"])

    inventory, groups = _inventory(pred, v8["head"]["control_generation"], asset_paths)
    migration_id = "migrate-" + mr.sha_bytes(mr.canonical_bytes({"project_id": v8["head"]["project_id"], "head_sha256": v8["head_hash"], "successor_run_id": run_id}))[:24]
    migration_manifest = {
        "schema": "math-research-v8-migration-manifest/v10",
        "migration_id": migration_id,
        "predecessor": {
            "schema": "math-research-project/v8",
            "project_id": v8["head"]["project_id"],
            "head_sha256": v8["head_hash"],
            "control_generation": v8["head"]["control_generation"],
            "run_id": v8["run"]["id"],
            "run_status": v8["run"]["status"],
            "contract": v8["contract"],
            "problem_statement_sha256": v8["head"]["problem_statement_sha256"],
            "current_lifecycle": v8["lifecycle"],
            "counters": v8["counters"],
        },
        "successor": {"schema": "math-research-project/v10", "project_id": v8["head"]["project_id"], "run_id": run_id},
        "inventory": inventory,
        "semantic_indexes": groups,
        "asset_index": v8["asset_index"],
        "created_at_utc": bootstrap["occurred_at_utc"],
    }
    immutable.append(_write_value(stage_root, MIGRATION_MANIFEST_REL, migration_manifest, stamp)); stamp += 1
    migration_manifest_ptr = {"path": MIGRATION_MANIFEST_REL, "sha256": immutable[-1]["sha256"]}

    envelope_payload = {"contract_binding_sha256": v8["contract"]["binding_sha256"], "problem_statement_sha256": v8["head"]["problem_statement_sha256"]}
    permission_payload = {"contract_binding_sha256": v8["contract"]["binding_sha256"], "allowed_worker_tools": v8["policy"]["allowed_worker_tools"]}
    resource_payload = {"contract_binding_sha256": v8["contract"]["binding_sha256"], "cycle_policy": v8["policy"]}
    envelope_snapshot = {
        "schema": "math-research-v8-envelope-snapshot/v10",
        "contract": v8["contract"],
        "cycle_policy": v8["policy"],
        "envelope_sha256": mr.sha_bytes(mr.canonical_bytes(envelope_payload)),
        "permission_envelope_sha256": mr.sha_bytes(mr.canonical_bytes(permission_payload)),
        "resource_envelope_sha256": mr.sha_bytes(mr.canonical_bytes(resource_payload)),
        "remaining_budgets": {"attempt_budget": v8["remaining_attempts"], "total_round_budget": v8["remaining_rounds"]},
    }
    immutable.append(_write_value(stage_root, ENVELOPE_REL, envelope_snapshot, stamp)); stamp += 1
    envelope_ptr = {"path": ENVELOPE_REL, "sha256": immutable[-1]["sha256"]}

    freeze_record = {
        "schema": "math-research-v8-freeze/v10",
        "migration_id": migration_id,
        "predecessor": {"project_id": v8["head"]["project_id"], "head_sha256": v8["head_hash"], "control_generation": v8["head"]["control_generation"], "run_id": v8["run"]["id"], "run_status": v8["run"]["status"]},
        "successor": {"project_id": v8["head"]["project_id"], "run_id": run_id, "directory_name": succ.name},
        "migration_manifest": migration_manifest_ptr,
        "occurred_at_utc": bootstrap["occurred_at_utc"],
    }
    immutable.append(_write_value(stage_root, FREEZE_COPY_REL, freeze_record, stamp)); stamp += 1
    freeze_ptr = {"path": FREEZE_COPY_REL, "sha256": immutable[-1]["sha256"]}

    route = bootstrap["initial_route_card"]
    mr.validate_route_card(route)
    route_rel = f"runs/{run_id}/routes/{route['route_id']}.json"
    immutable.append(_write_value(stage_root, route_rel, route, stamp)); stamp += 1
    route_ptr = {"path": route_rel, "sha256": immutable[-1]["sha256"]}

    capsule = json.loads(json.dumps(bootstrap["initial_capsule"]))
    capsule["project_id"] = v8["head"]["project_id"]
    capsule["run_id"] = run_id
    capsule["generation"] = 1
    capsule["target_sha256"] = v8["head"]["problem_statement_sha256"]
    required = capsule.get("required_full_artifacts")
    mr.fail(not isinstance(required, list), "migration_bootstrap_invalid", "Capsule required_full_artifacts must be an array.")
    for item in (migration_manifest_ptr, freeze_ptr, envelope_ptr):
        if item not in required:
            required.append(item)
    capsule_rel = f"runs/{run_id}/continuity/capsule-g0001.json"
    immutable.append(_write_value(stage_root, capsule_rel, capsule, stamp)); stamp += 1
    capsule_ptr = {"path": capsule_rel, "sha256": immutable[-1]["sha256"]}
    mr.validate_continuity_capsule(capsule, stage_root)

    ticket = json.loads(json.dumps(bootstrap["initial_ticket"]))
    ticket["continuity_capsule"] = capsule_ptr
    ticket["route_card"] = route_ptr
    ticket["writable_staging_path"] = f"runs/{run_id}/staging/{ticket['ticket_id']}/solver"
    ticket["attempt_scope"]["target_sha256"] = v8["head"]["problem_statement_sha256"]
    mr.fail(ticket["attempt_scope"]["resource_envelope_sha256"] != envelope_snapshot["resource_envelope_sha256"], "migration_bootstrap_invalid", "Ticket resource envelope differs from the inherited v8 envelope.")
    generated = [
        ("capsule", "continuity_capsule", capsule_ptr),
        ("route", "route_card", route_ptr),
        ("migration_manifest", "other", migration_manifest_ptr),
        ("freeze_record", "other", freeze_ptr),
        ("envelope_snapshot", "task_contract", envelope_ptr),
    ]
    generated_ids = {item[0] for item in generated}
    ticket["source_requirements"] = [item for item in ticket["source_requirements"] if item.get("id") not in generated_ids]
    ticket["input_artifacts"] = [item for item in ticket["input_artifacts"] if item.get("id") not in generated_ids]
    for ident, role, pointer in generated:
        ticket["source_requirements"].append({"id": ident, "role": role, "required": True})
        ticket["input_artifacts"].append({"id": ident, "role": role, **pointer})
    ticket["allowed_reads"] = sorted(set(ticket["allowed_reads"] + [item[2]["path"] for item in generated]))
    for artifact in ticket["input_artifacts"]:
        path = mr.resolve_under(stage_root, artifact["path"], "migration ticket input")
        mr.fail(not path.is_file() or mr.sha_file(path) != artifact["sha256"], "migration_input_missing", f"Ticket input was not staged: {artifact['path']}")
    mr.validate_v10_ticket(ticket, stage_root)
    ticket_rel = f"runs/{run_id}/tickets/{ticket['ticket_id']}.json"
    immutable.append(_write_value(stage_root, ticket_rel, ticket, stamp)); stamp += 1
    ticket_ptr = {"path": ticket_rel, "sha256": immutable[-1]["sha256"]}

    lineage = {
        "schema": "math-research-predecessor/v10",
        "project_id": v8["head"]["project_id"],
        "run_id": v8["run"]["id"],
        "head_sha256": v8["head_hash"],
        "final_status": "superseded_by_v10_migration",
        "predecessor_schema": "v8",
        "control_generation": v8["head"]["control_generation"],
        "migration_manifest": migration_manifest_ptr,
        "freeze_record": freeze_ptr,
    }
    immutable.append(_write_value(stage_root, LINEAGE_REL, lineage, stamp)); stamp += 1
    lineage_ptr = {"path": LINEAGE_REL, "sha256": immutable[-1]["sha256"]}

    state_rel = "state/generations/g0001/state-v10.json"
    state = {
        "schema": "math-research-state/v10",
        "project_id": v8["head"]["project_id"],
        "control_generation": 1,
        "active_run": {
            "id": run_id,
            "status": "preparing",
            "envelope_sha256": envelope_snapshot["envelope_sha256"],
            "permission_envelope_sha256": envelope_snapshot["permission_envelope_sha256"],
            "resource_envelope_sha256": envelope_snapshot["resource_envelope_sha256"],
            "predecessor": {"project_id": v8["head"]["project_id"], "run_id": v8["run"]["id"], "head_sha256": v8["head_hash"], "final_status": "superseded_by_v10_migration"},
            "budgets": {"attempt_budget": v8["remaining_attempts"], "total_round_budget": v8["remaining_rounds"]},
        },
        "current_attempt": None,
        "current_ticket": {"id": ticket["ticket_id"], "path": ticket_rel, "sha256": ticket_ptr["sha256"], "lifecycle": "planned"},
        "continuity_capsule": capsule_ptr,
        "active_route_card": route_ptr,
        "strategy_action": None,
        "route_reset": None,
        "asset_index": v8["asset_index"],
        "migration": {
            "schema": "math-research-incremental-migration/v10",
            "status": "frozen",
            "migration_id": migration_id,
            "predecessor_schema": "v8",
            "predecessor_directory_name": pred.name,
            "successor_directory_name": succ.name,
            "predecessor_control_generation": v8["head"]["control_generation"],
            "predecessor_run_status": v8["run"]["status"],
            "manifest": migration_manifest_ptr,
            "freeze_record": freeze_ptr,
            "envelope_snapshot": envelope_ptr,
            "lineage": lineage_ptr,
        },
        "counters": {
            "run_local": {"attempt_count": 0, "audit_count": 0, "total_round_count": 0, "attempts_since_last_audit": 0},
            "cumulative": {key: v8["counters"][key] for key in ("attempt_count", "audit_count", "total_round_count", "attempts_since_last_audit")},
        },
        "evidence_items": [],
        "typed_references": [
            {"kind": "migration_record", "path": migration_manifest_ptr["path"], "sha256": migration_manifest_ptr["sha256"], "attempt_id": None, "ticket_id": None},
            {"kind": "migration_record", "path": freeze_ptr["path"], "sha256": freeze_ptr["sha256"], "attempt_id": None, "ticket_id": None},
        ],
        "updated_at_utc": bootstrap["occurred_at_utc"],
    }
    immutable.append(_write_value(stage_root, state_rel, state, stamp)); stamp += 1

    event_rel = "events/g0001-v8-incremental-migration.json"
    event = {"schema": "math-research-event/v10", "project_id": v8["head"]["project_id"], "control_generation": 1, "event_type": "V8_INCREMENTAL_MIGRATION", "previous_event": None, "payload_sha256": mr.sha_file(bootstrap_path), "occurred_at_utc": bootstrap["occurred_at_utc"]}
    immutable.append(_write_value(stage_root, event_rel, event, stamp)); stamp += 1

    by_target = {item["target"]: item for item in immutable}
    manifest_rel = "state/manifests/g0001.json"
    entries = [{"path": rel, "sha256": item["sha256"], "size": item["size"], "mtime_ns": item["mtime_ns"], "generation_added": 1} for rel, item in sorted(by_target.items())]
    manifest = {"schema": "math-research-archive-manifest/v10", "project_id": v8["head"]["project_id"], "control_generation": 1, "entries": entries, "created_at_utc": bootstrap["occurred_at_utc"]}
    immutable.append(_write_value(stage_root, manifest_rel, manifest, stamp)); stamp += 1
    manifest_ptr = {"path": manifest_rel, "sha256": immutable[-1]["sha256"]}
    head = {"schema": "math-research-project/v10", "project_id": v8["head"]["project_id"], "control_generation": 1, "state": {"path": state_rel, "sha256": by_target[state_rel]["sha256"]}, "event_tail": {"path": event_rel, "sha256": by_target[event_rel]["sha256"]}, "archive_manifest": manifest_ptr, "last_full_audit_generation": 1, "last_full_audit_at_utc": bootstrap["occurred_at_utc"]}
    project_info = mr._write_stage(stage_root / "project.json", head, stamp); stamp += 1
    plan = {
        "schema": "math-research-transition-plan/v10",
        "project_root": str(succ),
        "expected_head_sha256": None,
        "expected_generation": 0,
        "new_generation": 1,
        "event_type": "V8_INCREMENTAL_MIGRATION",
        "immutable_files": immutable,
        "candidate_project": {"source": project_info["source"], "sha256": project_info["sha256"], "mtime_ns": project_info["mtime_ns"]},
        "created_at_utc": mr.now_utc(),
    }
    plan_info = mr._write_stage(stage_root / "transition-plan.json", plan, stamp)
    mr.validate_state(stage_root, state)
    return {
        "prepared": True,
        "migration_id": migration_id,
        "plan_path": str((stage_root / "transition-plan.json").resolve()),
        "plan_sha256": plan_info["sha256"],
        "predecessor_head_sha256": v8["head_hash"],
        "candidate_head_sha256": project_info["sha256"],
        "freeze_record": {"source": str((stage_root / FREEZE_COPY_REL).resolve()), "sha256": freeze_ptr["sha256"], "target": FREEZE_REL},
        "inherited_counters": state["counters"]["cumulative"],
        "remaining_budgets": state["active_run"]["budgets"],
        "asset_index": state["asset_index"],
        "inventory_count": len(inventory),
        "unreferenced_recovery_count": len(groups["unreferenced_recovery_candidates"]),
    }


def freeze(predecessor: Path, plan_path: Path) -> dict[str, Any]:
    pred = predecessor.resolve()
    v8 = _read_v8(pred)
    plan = mr.load_json(plan_path)
    mr.fail(plan.get("schema") != "math-research-transition-plan/v10" or plan.get("event_type") != "V8_INCREMENTAL_MIGRATION", "migration_plan_invalid", "Plan is not a v8 incremental migration plan.")
    records = [item for item in plan.get("immutable_files", []) if item.get("target") == FREEZE_COPY_REL]
    mr.fail(len(records) != 1, "migration_plan_invalid", "Plan must contain one freeze record.")
    record = records[0]
    mr.require_hash(record["sha256"], "freeze record hash")
    source = Path(record["source"])
    mr.fail(not source.is_file() or mr.sha_file(source) != record["sha256"], "migration_plan_invalid", "Staged freeze record differs from the plan.")
    value = mr.load_json(source)
    mr.fail(value.get("schema") != "math-research-v8-freeze/v10", "migration_plan_invalid", "Freeze record schema is invalid.")
    mr.fail(value["predecessor"]["head_sha256"] != v8["head_hash"] or value["predecessor"]["control_generation"] != v8["head"]["control_generation"], "cas_conflict", "The v8 head changed after migration preparation.")
    successor = pred.parent / value["successor"]["directory_name"]
    mr.fail(str(successor.resolve()) != str(Path(plan["project_root"]).resolve()), "migration_plan_invalid", "Plan target differs from the freeze-record successor.")
    target = pred / FREEZE_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        mr.fail(not target.is_file() or mr.sha_file(target) != record["sha256"], "freeze_conflict", "A different v8 freeze marker already exists.")
        return {"frozen": True, "reused": True, "freeze_path": str(target), "freeze_sha256": record["sha256"], "predecessor_head_sha256": v8["head_hash"]}
    data = source.read_bytes()
    fd = None
    try:
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
        with os.fdopen(fd, "wb", closefd=True) as handle:
            fd = None
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        if fd is not None:
            os.close(fd)
        try:
            if target.exists() and mr.sha_file(target) != record["sha256"]:
                target.unlink()
        except OSError:
            pass
        raise
    mr.fail(mr.sha_file(target) != record["sha256"], "freeze_readback_failed", "v8 freeze marker readback failed.")
    return {"frozen": True, "reused": False, "freeze_path": str(target), "freeze_sha256": record["sha256"], "predecessor_head_sha256": v8["head_hash"]}


def verify(predecessor: Path, successor: Path, plan_path: Path) -> dict[str, Any]:
    pred = predecessor.resolve()
    succ = successor.resolve()
    plan = mr.load_json(plan_path)
    mr.fail(Path(plan["project_root"]).resolve() != succ, "migration_plan_invalid", "Plan target differs from successor.")
    freeze_records = [item for item in plan["immutable_files"] if item["target"] == FREEZE_COPY_REL]
    mr.fail(len(freeze_records) != 1, "migration_plan_invalid", "Plan freeze record is missing.")
    marker = pred / FREEZE_REL
    mr.fail(not marker.is_file() or mr.sha_file(marker) != freeze_records[0]["sha256"], "predecessor_not_frozen", "v8 freeze marker is absent or mismatched.")
    mr.fail(not (succ / "project.json").is_file() or mr.sha_file(succ / "project.json") != plan["candidate_project"]["sha256"], "successor_not_committed", "v10 successor head is absent or differs from the migration plan.")
    head, state, manifest, head_hash, notes = mr.load_v10_project(succ, "Full")
    mr.validate_migration_predecessor_freeze(succ, state)
    return {
        "verified": True,
        "predecessor_head_sha256": mr.sha_file(pred / "project.json"),
        "predecessor_freeze_sha256": mr.sha_file(marker),
        "successor_head_sha256": head_hash,
        "successor_generation": head["control_generation"],
        "cumulative_counters": state["counters"]["cumulative"],
        "remaining_budgets": state["active_run"]["budgets"],
        "asset_index": state.get("asset_index"),
        "manifest_entry_count": len(manifest["entries"]),
        "audit_notes": notes,
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command", required=True)
    inspect = sub.add_parser("inspect")
    inspect.add_argument("--predecessor", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--predecessor", required=True)
    prep.add_argument("--successor", required=True)
    prep.add_argument("--bootstrap", required=True)
    prep.add_argument("--output", required=True)
    frz = sub.add_parser("freeze")
    frz.add_argument("--predecessor", required=True)
    frz.add_argument("--plan", required=True)
    check = sub.add_parser("verify")
    check.add_argument("--predecessor", required=True)
    check.add_argument("--successor", required=True)
    check.add_argument("--plan", required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "inspect":
            data = inspect_v8(Path(args.predecessor))
        elif args.command == "prepare":
            data = prepare(Path(args.predecessor), Path(args.successor), Path(args.bootstrap), Path(args.output))
        elif args.command == "freeze":
            data = freeze(Path(args.predecessor), Path(args.plan))
        else:
            data = verify(Path(args.predecessor), Path(args.successor), Path(args.plan))
        return mr.emit_success(data)
    except mr.ResearchError as exc:
        return mr.emit_error(exc)
    except Exception as exc:
        return mr.emit_error(mr.ResearchError("migration_internal_error", f"{type(exc).__name__}: {exc}"))


if __name__ == "__main__":
    sys.exit(main())
