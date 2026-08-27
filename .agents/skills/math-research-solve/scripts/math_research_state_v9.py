#!/usr/bin/env python3
"""Shared validator, transition builder, and guarded publisher for Math Research v9.

The module deliberately leaves product Goal verification to the Goal Host.  A literal
``--goal-status active`` is only a final fail-closed caller assertion, never an
attestation.  Immutable files are create-new; ``project.json`` is replaced last under
a cooperative lock and expected-head comparison.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable


HEX64 = re.compile(r"^[0-9a-f]{64}$")
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
RFC3339_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z$")
DISPOSITIONS = {
    "candidate",
    "no_candidate_with_evidence",
    "no_candidate",
    "inconclusive",
    "blocked",
}
EVIDENCE_KINDS = {
    "candidate",
    "verified_partial",
    "failure_boundary",
    "source_claim",
    "exact_computation",
}
REFERENCE_KINDS = {
    "attempt_record",
    "solver_result",
    "verifier_completion",
    "verified_partial",
    "candidate",
    "failure_record",
    "audit_record",
    "route_record",
    "handoff",
}
SOURCE_ROLES = {
    "primary_source",
    "formula_extract",
    "prior_proof",
    "computation_output",
    "task_contract",
    "candidate",
    "dependency",
    "other",
}
TRANSITIONS = {
    "ATTEMPT_START",
    "SOLVER_COMPLETE",
    "VERIFIER_COMPLETE",
    "ATTEMPT_END",
    "CHECKPOINT_COMMIT",
}
AUTHORITATIVE_PREFIXES = ("contracts/", "events/", "evidence/", "inputs/", "lineage/", "runs/", "state/")


class ResearchError(Exception):
    def __init__(self, code: str, message: str, recovery: str = "Preserve the project and repair the stated invariant before retrying."):
        super().__init__(message)
        self.code = code
        self.message = message
        self.recovery = recovery


def fail(condition: bool, code: str, message: str) -> None:
    if condition:
        raise ResearchError(code, message)


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ResearchError("duplicate_json_key", f"Duplicate JSON key: {key}")
        out[key] = value
    return out


def load_json(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ResearchError("json_read_failed", f"Cannot read JSON file: {path.name}: {exc}") from exc
    try:
        return json.loads(text, object_pairs_hook=_pairs_no_duplicates, parse_float=str)
    except ResearchError:
        raise
    except Exception as exc:
        raise ResearchError("json_invalid", f"Invalid JSON in {path.name}: {exc}") from exc


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def parse_utc(value: str) -> dt.datetime:
    require_timestamp(value, "timestamp")
    return dt.datetime.fromisoformat(value[:-1] + "+00:00")


def require_timestamp(value: Any, label: str) -> None:
    fail(not isinstance(value, str) or not RFC3339_Z.fullmatch(value), "timestamp_invalid", f"{label} must be an RFC3339 UTC Z string.")
    try:
        dt.datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ResearchError("timestamp_invalid", f"{label} is not a valid timestamp.") from exc


def require_exact(obj: Any, keys: Iterable[str], label: str) -> dict[str, Any]:
    fail(not isinstance(obj, dict), "schema_invalid", f"{label} must be an object.")
    expected = set(keys)
    actual = set(obj)
    fail(actual != expected, "schema_invalid", f"{label} keys differ: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}")
    return obj


def require_id(value: Any, label: str) -> str:
    fail(not isinstance(value, str) or not SAFE_ID.fullmatch(value), "identifier_invalid", f"{label} is not a safe identifier.")
    return value


def require_hash(value: Any, label: str) -> str:
    fail(not isinstance(value, str) or not HEX64.fullmatch(value), "hash_invalid", f"{label} must be lowercase SHA-256.")
    return value


def safe_relative(value: Any, label: str) -> str:
    fail(not isinstance(value, str) or not value or "\\" in value, "path_invalid", f"{label} must use a nonempty project-relative slash path.")
    posix = Path(value)
    fail(posix.is_absolute() or any(part in ("", ".", "..") for part in posix.parts), "path_invalid", f"{label} is unsafe.")
    fail(value.startswith("/") or re.match(r"^[A-Za-z]:", value) is not None, "path_invalid", f"{label} is absolute.")
    return value


def resolve_under(root: Path, relative: str, label: str, must_exist: bool = True) -> Path:
    safe_relative(relative, label)
    root_real = Path(os.path.realpath(root))
    candidate = root / Path(relative)
    real = Path(os.path.realpath(candidate))
    try:
        real.relative_to(root_real)
    except ValueError as exc:
        raise ResearchError("path_escape", f"{label} escapes the project root.") from exc
    if must_exist:
        fail(not real.is_file(), "artifact_missing", f"{label} does not resolve to a file: {relative}")
    return real


def pointer(obj: Any, root: Path, label: str, *, hash_now: bool = True) -> tuple[str, Path]:
    require_exact(obj, ("path", "sha256"), label)
    rel = safe_relative(obj["path"], f"{label}.path")
    expected = require_hash(obj["sha256"], f"{label}.sha256")
    path = resolve_under(root, rel, label)
    if hash_now:
        fail(sha_file(path) != expected, "artifact_hash_mismatch", f"{label} hash mismatch: {rel}")
    return rel, path


def counters(value: Any, label: str) -> dict[str, int]:
    require_exact(value, ("attempt_count", "audit_count", "total_round_count", "attempts_since_last_audit"), label)
    out: dict[str, int] = {}
    for key, item in value.items():
        fail(type(item) is not int or item < 0, "counter_invalid", f"{label}.{key} must be a nonnegative integer.")
        out[key] = item
    fail(out["total_round_count"] != out["attempt_count"] + out["audit_count"], "counter_invalid", f"{label}.total_round_count must equal attempts plus audits.")
    fail(out["attempts_since_last_audit"] > out["attempt_count"], "counter_invalid", f"{label}.attempts_since_last_audit exceeds attempts.")
    return out


def validate_v9_ticket(ticket: Any, root: Path, *, expected_lifecycle: str | None = None) -> dict[str, Any]:
    keys = (
        "schema", "ticket_id", "role", "initial_lifecycle", "source_requirements",
        "input_artifacts", "allowed_reads", "writable_staging_path", "decision_question",
        "allowed_tools", "resource_caps", "required_outputs", "failure_return",
    )
    require_exact(ticket, keys, "v9 ticket")
    fail(ticket["schema"] != "math-research-ticket/v9", "ticket_invalid", "Ticket schema is not v9.")
    require_id(ticket["ticket_id"], "ticket_id")
    fail(ticket["role"] not in ("attempt", "audit"), "ticket_invalid", "Ticket role must be attempt or audit.")
    fail(ticket["initial_lifecycle"] != "planned", "ticket_invalid", "A frozen v9 ticket must start at planned.")
    if expected_lifecycle is not None:
        fail(expected_lifecycle not in ("planned", "active", "solver_completed", "verifier_completed", "closed"), "ticket_invalid", "State ticket lifecycle is invalid.")
    fail(not isinstance(ticket["decision_question"], str) or not ticket["decision_question"].strip(), "ticket_invalid", "Ticket decision question is empty.")
    requirements = ticket["source_requirements"]
    artifacts = ticket["input_artifacts"]
    reads = ticket["allowed_reads"]
    fail(not isinstance(requirements, list) or not requirements, "ticket_invalid", "source_requirements must be nonempty.")
    fail(not isinstance(artifacts, list) or not artifacts, "ticket_invalid", "input_artifacts must be nonempty.")
    fail(not isinstance(reads, list) or not reads, "ticket_invalid", "allowed_reads must be nonempty.")
    req_map: dict[str, dict[str, Any]] = {}
    for req in requirements:
        require_exact(req, ("id", "role", "required"), "source requirement")
        rid = require_id(req["id"], "source requirement id")
        fail(rid in req_map, "ticket_invalid", f"Duplicate source requirement id: {rid}")
        fail(req["role"] not in SOURCE_ROLES, "ticket_invalid", f"Unsupported source role: {req['role']}")
        fail(type(req["required"]) is not bool, "ticket_invalid", "source requirement required must be boolean.")
        req_map[rid] = req
    artifact_map: dict[str, dict[str, Any]] = {}
    artifact_paths: list[str] = []
    for item in artifacts:
        require_exact(item, ("id", "role", "path", "sha256"), "input artifact")
        iid = require_id(item["id"], "input artifact id")
        fail(iid in artifact_map, "ticket_invalid", f"Duplicate input artifact id: {iid}")
        fail(item["role"] not in SOURCE_ROLES, "ticket_invalid", f"Unsupported input role: {item['role']}")
        rel, _ = pointer({"path": item["path"], "sha256": item["sha256"]}, root, f"input artifact {iid}")
        artifact_map[iid] = item
        artifact_paths.append(rel)
    for rid, req in req_map.items():
        if req["required"]:
            fail(rid not in artifact_map, "ticket_input_incomplete", f"Required source is missing: {rid}")
        if rid in artifact_map:
            fail(artifact_map[rid]["role"] != req["role"], "ticket_input_incomplete", f"Source role mismatch for {rid}")
    read_paths = [safe_relative(item, "allowed_reads item") for item in reads]
    fail(len(read_paths) != len(set(read_paths)), "ticket_invalid", "allowed_reads contains duplicates.")
    fail(set(read_paths) != set(artifact_paths), "ticket_read_closure_failed", "allowed_reads and input artifact paths must be exactly equal.")
    writable = safe_relative(ticket["writable_staging_path"], "writable_staging_path")
    fail("/staging/" not in f"/{writable}/", "ticket_invalid", "writable_staging_path must be inside a staging directory.")
    fail(not isinstance(ticket["allowed_tools"], list) or len(ticket["allowed_tools"]) != len(set(ticket["allowed_tools"])), "ticket_invalid", "allowed_tools must be a unique array.")
    require_exact(ticket["resource_caps"], ("child_agents", "tool_calls", "runtime_minutes", "max_output_bytes"), "resource_caps")
    for key, value in ticket["resource_caps"].items():
        fail(type(value) is not int or value < 0, "ticket_invalid", f"resource_caps.{key} must be nonnegative integer.")
    fail(not isinstance(ticket["required_outputs"], list) or not ticket["required_outputs"], "ticket_invalid", "required_outputs must be nonempty.")
    require_exact(ticket["failure_return"], ("schema", "required_fields"), "failure_return")
    fail(ticket["failure_return"]["schema"] != "math-research-ticket-failure/v1", "ticket_invalid", "Failure schema is invalid.")
    return ticket


def preflight_v8(project: Path, ticket_path: Path, requirements_path: Path, access_log: Path | None) -> dict[str, Any]:
    wrapper = load_json(ticket_path)
    if isinstance(wrapper, dict) and "ticket" in wrapper:
        ticket = wrapper["ticket"]
        control_reads = set()
        contract = wrapper.get("contract")
        if isinstance(contract, dict) and isinstance(contract.get("path"), str):
            control_reads.add(safe_relative(contract["path"], "contract path"))
    else:
        ticket = wrapper
        control_reads = set()
    fail(not isinstance(ticket, dict), "ticket_invalid", "Ticket is not an object.")
    fail(not isinstance(ticket.get("input_artifacts"), list) or not ticket["input_artifacts"], "ticket_invalid", "v8 ticket has no input artifacts.")
    scope = ticket.get("filesystem_scope")
    fail(not isinstance(scope, dict) or not isinstance(scope.get("read_paths"), list), "ticket_invalid", "v8 ticket has no read_paths.")
    inputs: dict[str, str] = {}
    for index, item in enumerate(ticket["input_artifacts"]):
        rel, _ = pointer(item, project, f"v8 input artifact {index}")
        fail(rel in inputs, "ticket_invalid", f"Duplicate v8 input path: {rel}")
        inputs[rel] = item["sha256"]
    reads = [safe_relative(item, "v8 read_path") for item in scope["read_paths"]]
    fail(len(reads) != len(set(reads)), "ticket_invalid", "v8 read_paths contains duplicates.")
    fail(not set(inputs).issubset(set(reads)), "ticket_read_closure_failed", "Every v8 input artifact must be readable.")
    fail(set(reads) - set(inputs) - control_reads, "ticket_read_closure_failed", "v8 read_paths contains unbound non-control paths.")

    req_rel = requirements_path.resolve().relative_to(project.resolve()).as_posix()
    fail(req_rel not in inputs, "ticket_input_incomplete", "The source-requirements manifest is not hash-bound as a ticket input.")
    requirements = load_json(requirements_path)
    require_exact(requirements, ("schema", "requirements"), "v8 source requirements")
    fail(requirements["schema"] != "math-research-source-requirements/v1", "ticket_input_incomplete", "Source-requirements schema is invalid.")
    fail(not isinstance(requirements["requirements"], list) or not requirements["requirements"], "ticket_input_incomplete", "Source requirements are empty.")
    represented: set[str] = set()
    seen_ids: set[str] = set()
    for req in requirements["requirements"]:
        require_exact(req, ("id", "role", "path", "sha256", "required"), "v8 source requirement")
        rid = require_id(req["id"], "v8 source requirement id")
        fail(rid in seen_ids, "ticket_input_incomplete", f"Duplicate source id: {rid}")
        seen_ids.add(rid)
        fail(req["role"] not in SOURCE_ROLES, "ticket_input_incomplete", f"Unsupported source role: {req['role']}")
        fail(type(req["required"]) is not bool, "ticket_input_incomplete", "Source required flag must be boolean.")
        rel = safe_relative(req["path"], "v8 source path")
        expected = require_hash(req["sha256"], "v8 source sha256")
        if req["required"]:
            fail(rel not in inputs, "ticket_input_incomplete", f"Required v8 source is not a ticket input: {rid}")
        if rel in inputs:
            fail(inputs[rel] != expected, "ticket_input_incomplete", f"Source hash differs from ticket input: {rid}")
            represented.add(rel)
    fail(set(inputs) - {req_rel} - represented, "ticket_input_incomplete", "At least one v8 input lacks a typed source requirement.")

    reads_seen: list[str] = []
    if access_log is not None:
        log = load_json(access_log)
        require_exact(log, ("schema", "reads"), "worker access log")
        fail(log["schema"] != "math-research-worker-access-log/v1" or not isinstance(log["reads"], list), "worker_access_invalid", "Worker access log schema is invalid.")
        reads_seen = [safe_relative(item, "worker read") for item in log["reads"]]
        fail(set(reads_seen) - set(inputs) - control_reads, "worker_access_out_of_scope", "Worker reported an unbound read; discard the return.")
    return {
        "classification": "ticket_ready",
        "ticket_id": ticket.get("ticket_id"),
        "input_count": len(inputs),
        "source_requirement_count": len(requirements["requirements"]),
        "access_log_checked": access_log is not None,
        "access_read_count": len(reads_seen),
        "worker_capsule": {
            "required_fork_turns": "none",
            "context_inputs": [ticket_path.resolve().as_posix()] + [resolve_under(project, rel, "capsule input").as_posix() for rel in sorted(inputs)],
            "isolation_level": "protocol_only_shared_filesystem",
        },
    }


def validate_manifest(root: Path, manifest: Any) -> dict[str, Any]:
    require_exact(manifest, ("schema", "project_id", "control_generation", "entries", "created_at_utc"), "archive manifest")
    fail(manifest["schema"] != "math-research-archive-manifest/v9", "manifest_invalid", "Manifest schema is invalid.")
    require_id(manifest["project_id"], "manifest project_id")
    fail(type(manifest["control_generation"]) is not int or manifest["control_generation"] < 1, "manifest_invalid", "Manifest generation is invalid.")
    require_timestamp(manifest["created_at_utc"], "manifest created_at_utc")
    fail(not isinstance(manifest["entries"], list), "manifest_invalid", "Manifest entries must be an array.")
    seen: set[str] = set()
    for entry in manifest["entries"]:
        require_exact(entry, ("path", "sha256", "size", "mtime_ns", "generation_added"), "manifest entry")
        rel = safe_relative(entry["path"], "manifest entry path")
        fail(rel in seen, "manifest_invalid", f"Duplicate manifest path: {rel}")
        seen.add(rel)
        require_hash(entry["sha256"], "manifest entry hash")
        for key in ("size", "mtime_ns", "generation_added"):
            fail(type(entry[key]) is not int or entry[key] < 0, "manifest_invalid", f"Manifest {key} is invalid.")
    return manifest


def _authoritative_files(root: Path) -> set[str]:
    result: set[str] = set()
    if not root.exists():
        return result
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel == "project.json" or "/staging/" in f"/{rel}/" or rel.endswith(".lock"):
            continue
        if rel.startswith(AUTHORITATIVE_PREFIXES):
            result.add(rel)
    return result


def validate_state(root: Path, state: Any) -> dict[str, Any]:
    require_exact(state, ("schema", "project_id", "control_generation", "active_run", "current_attempt", "current_ticket", "counters", "evidence_items", "typed_references", "updated_at_utc"), "v9 state")
    fail(state["schema"] != "math-research-state/v9", "state_invalid", "State schema is invalid.")
    require_id(state["project_id"], "state project_id")
    fail(type(state["control_generation"]) is not int or state["control_generation"] < 1, "state_invalid", "State generation is invalid.")
    require_timestamp(state["updated_at_utc"], "state updated_at_utc")
    run = require_exact(state["active_run"], ("id", "status", "envelope_sha256", "permission_envelope_sha256", "resource_envelope_sha256", "predecessor", "budgets"), "active_run")
    require_id(run["id"], "run id")
    fail(run["status"] not in ("preparing", "attempt_running", "audit_due", "auditing", "awaiting_input", "paused", "superseded", "closed"), "state_invalid", "Run status is invalid.")
    for key in ("envelope_sha256", "permission_envelope_sha256", "resource_envelope_sha256"):
        require_hash(run[key], f"active_run.{key}")
    require_exact(run["budgets"], ("attempt_budget", "total_round_budget"), "run budgets")
    for key, value in run["budgets"].items():
        fail(type(value) is not int or value < 0, "state_invalid", f"Budget {key} is invalid.")
    if run["predecessor"] is not None:
        pred = require_exact(run["predecessor"], ("project_id", "run_id", "head_sha256", "final_status"), "predecessor")
        require_id(pred["project_id"], "predecessor project id")
        require_id(pred["run_id"], "predecessor run id")
        require_hash(pred["head_sha256"], "predecessor head hash")
        fail(pred["final_status"] not in ("closed", "superseded", "budget_exhausted", "route_exhausted"), "state_invalid", "Predecessor final status is invalid.")
    require_exact(state["counters"], ("run_local", "cumulative"), "counters")
    local = counters(state["counters"]["run_local"], "run_local counters")
    cumulative = counters(state["counters"]["cumulative"], "cumulative counters")
    for key in local:
        fail(local[key] > cumulative[key], "counter_invalid", f"Run-local {key} exceeds cumulative value.")
    attempt = state["current_attempt"]
    ticket_state = state["current_ticket"]
    if attempt is None:
        fail(run["status"] == "attempt_running", "state_invalid", "attempt_running requires current_attempt.")
    else:
        require_exact(attempt, ("id", "ticket_id", "started_generation", "kind", "solver_result", "verifier_completion", "disposition"), "current_attempt")
        require_id(attempt["id"], "attempt id")
        require_id(attempt["ticket_id"], "attempt ticket id")
        fail(type(attempt["started_generation"]) is not int or attempt["started_generation"] < 1, "state_invalid", "Attempt generation is invalid.")
        fail(attempt["kind"] not in ("route_discovery", "route_execution", "candidate_revision", "candidate_synthesis"), "state_invalid", "Attempt kind is invalid.")
        for key in ("solver_result", "verifier_completion"):
            if attempt[key] is not None:
                pointer(attempt[key], root, f"attempt {key}")
        if attempt["disposition"] is not None:
            fail(attempt["disposition"] not in DISPOSITIONS, "state_invalid", "Attempt disposition is invalid.")
    if ticket_state is None:
        fail(attempt is not None, "state_invalid", "An active attempt requires current_ticket.")
    else:
        require_exact(ticket_state, ("id", "path", "sha256", "lifecycle"), "current_ticket")
        require_id(ticket_state["id"], "current_ticket id")
        fail(ticket_state["lifecycle"] not in ("planned", "active", "solver_completed", "verifier_completed", "closed"), "state_invalid", "Ticket lifecycle is invalid.")
        rel, path = pointer({"path": ticket_state["path"], "sha256": ticket_state["sha256"]}, root, "current_ticket")
        ticket = load_json(path)
        validate_v9_ticket(ticket, root, expected_lifecycle=ticket_state["lifecycle"])
        fail(ticket["ticket_id"] != ticket_state["id"], "state_invalid", "Current ticket ID differs from frozen ticket.")
        if attempt is not None:
            fail(attempt["ticket_id"] != ticket_state["id"], "state_invalid", "Attempt and ticket IDs differ.")
    validate_evidence(state["evidence_items"], root, "state evidence")
    validate_references(state["typed_references"], root, "state references")
    return state


def validate_evidence(items: Any, root: Path, label: str) -> list[dict[str, Any]]:
    fail(not isinstance(items, list), "evidence_invalid", f"{label} must be an array.")
    seen: set[tuple[str, str]] = set()
    for item in items:
        require_exact(item, ("kind", "path", "sha256", "ticket_id", "attempt_id"), "evidence item")
        fail(item["kind"] not in EVIDENCE_KINDS, "evidence_invalid", f"Unsupported evidence kind: {item['kind']}")
        require_id(item["ticket_id"], "evidence ticket id")
        require_id(item["attempt_id"], "evidence attempt id")
        rel, _ = pointer({"path": item["path"], "sha256": item["sha256"]}, root, "evidence item")
        key = (item["kind"], rel)
        fail(key in seen, "evidence_invalid", "Duplicate evidence item.")
        seen.add(key)
    return items


def validate_references(items: Any, root: Path, label: str) -> list[dict[str, Any]]:
    fail(not isinstance(items, list), "reference_invalid", f"{label} must be an array.")
    for item in items:
        require_exact(item, ("kind", "path", "sha256", "attempt_id", "ticket_id"), "typed reference")
        fail(item["kind"] not in REFERENCE_KINDS, "reference_invalid", f"Unsupported reference kind: {item['kind']}")
        if item["attempt_id"] is not None:
            require_id(item["attempt_id"], "reference attempt id")
        if item["ticket_id"] is not None:
            require_id(item["ticket_id"], "reference ticket id")
        pointer({"path": item["path"], "sha256": item["sha256"]}, root, "typed reference")
    return items


def load_v9_project(root: Path, audit_mode: str = "Auto", allowed_unmanifested: set[str] | None = None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str, list[str]]:
    project_path = root / "project.json"
    fail(not project_path.is_file(), "project_missing", "project.json is absent.")
    head_hash = sha_file(project_path)
    head = load_json(project_path)
    require_exact(head, ("schema", "project_id", "control_generation", "state", "event_tail", "archive_manifest", "last_full_audit_generation", "last_full_audit_at_utc"), "project head")
    fail(head["schema"] != "math-research-project/v9", "not_v9", "Project is not v9.")
    require_id(head["project_id"], "project_id")
    fail(type(head["control_generation"]) is not int or head["control_generation"] < 1, "project_invalid", "Head generation is invalid.")
    fail(type(head["last_full_audit_generation"]) is not int or head["last_full_audit_generation"] < 0, "project_invalid", "Full-audit generation is invalid.")
    require_timestamp(head["last_full_audit_at_utc"], "last_full_audit_at_utc")
    _, state_path = pointer(head["state"], root, "head state")
    _, event_path = pointer(head["event_tail"], root, "head event")
    manifest_rel, manifest_path = pointer(head["archive_manifest"], root, "head manifest")
    state = validate_state(root, load_json(state_path))
    manifest = validate_manifest(root, load_json(manifest_path))
    fail(state["project_id"] != head["project_id"] or manifest["project_id"] != head["project_id"], "project_invalid", "Project identity differs across head/state/manifest.")
    fail(state["control_generation"] != head["control_generation"] or manifest["control_generation"] != head["control_generation"], "project_invalid", "Generation differs across head/state/manifest.")
    event = load_json(event_path)
    require_exact(event, ("schema", "project_id", "control_generation", "event_type", "previous_event", "payload_sha256", "occurred_at_utc"), "event tail")
    fail(event["schema"] != "math-research-event/v9" or event["project_id"] != head["project_id"] or event["control_generation"] != head["control_generation"], "event_invalid", "Event tail binding is invalid.")
    require_hash(event["payload_sha256"], "event payload hash")
    require_timestamp(event["occurred_at_utc"], "event occurred_at_utc")
    if event["previous_event"] is not None:
        pointer(event["previous_event"], root, "previous event")

    entries = {item["path"]: item for item in manifest["entries"]}
    known = set(entries) | {manifest_rel}
    unexpected = _authoritative_files(root) - known - (allowed_unmanifested or set())
    fail(bool(unexpected), "manifest_unexpected_file", f"Unmanifested authoritative files exist: {sorted(unexpected)[:5]}")
    warnings: list[str] = []
    use_full = audit_mode == "Full"
    fail(audit_mode not in ("Auto", "Full"), "audit_mode_invalid", "AuditMode must be Auto or Full.")
    if audit_mode == "Auto":
        age = dt.datetime.now(dt.timezone.utc) - parse_utc(head["last_full_audit_at_utc"])
        if head["control_generation"] - head["last_full_audit_generation"] >= 10 or age > dt.timedelta(days=7):
            use_full = True
            warnings.append("periodic_full_audit_due")
    current_paths = {head["state"]["path"], head["event_tail"]["path"], head["archive_manifest"]["path"]}
    if state["current_ticket"] is not None:
        current_paths.add(state["current_ticket"]["path"])
    metadata_drift = False
    for rel, entry in entries.items():
        path = resolve_under(root, rel, "manifested file")
        stat = path.stat()
        if stat.st_size != entry["size"] or stat.st_mtime_ns != entry["mtime_ns"]:
            metadata_drift = True
        if use_full or rel in current_paths or entry["generation_added"] == head["control_generation"]:
            fail(sha_file(path) != entry["sha256"], "archive_hash_mismatch", f"Manifested file hash mismatch: {rel}")
    if metadata_drift and audit_mode == "Auto":
        warnings.append("metadata_drift_escalated_to_full")
    if metadata_drift and not use_full:
        for rel, entry in entries.items():
            path = resolve_under(root, rel, "manifested file")
            fail(sha_file(path) != entry["sha256"], "archive_hash_mismatch", f"Manifested file hash mismatch: {rel}")
        use_full = True
    return head, state, manifest, head_hash, warnings + (["full_audit_used"] if use_full else ["fast_audit_used"])


def _entry_for(root: Path, rel: str, generation: int) -> dict[str, Any]:
    path = resolve_under(root, rel, "manifest addition")
    stat = path.stat()
    return {"path": rel, "sha256": sha_file(path), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "generation_added": generation}


def _collect_state_pointers(state: dict[str, Any]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    if state["current_ticket"] is not None:
        result.append({"path": state["current_ticket"]["path"], "sha256": state["current_ticket"]["sha256"]})
    if state["current_attempt"] is not None:
        for key in ("solver_result", "verifier_completion"):
            if state["current_attempt"][key] is not None:
                result.append(state["current_attempt"][key])
    for item in state["evidence_items"] + state["typed_references"]:
        result.append({"path": item["path"], "sha256": item["sha256"]})
    return result


def apply_transition(root: Path, state: dict[str, Any], kind: str, payload: dict[str, Any], generation: int) -> dict[str, Any]:
    fail(kind not in TRANSITIONS, "transition_invalid", f"Unsupported transition: {kind}")
    new = copy.deepcopy(state)
    attempt = new["current_attempt"]
    ticket_state = new["current_ticket"]
    if kind == "ATTEMPT_START":
        require_exact(payload, ("schema", "attempt_id", "attempt_kind", "ticket", "occurred_at_utc"), "ATTEMPT_START payload")
        fail(payload["schema"] != "math-research-transition-payload/v9", "transition_invalid", "Payload schema is invalid.")
        require_timestamp(payload["occurred_at_utc"], "ATTEMPT_START occurred_at_utc")
        fail(attempt is not None or ticket_state is None or ticket_state["lifecycle"] != "planned" or new["active_run"]["status"] != "preparing", "transition_invalid", "ATTEMPT_START requires a preparing run and planned ticket with no attempt.")
        rel, ticket_path = pointer(payload["ticket"], root, "ATTEMPT_START ticket")
        ticket = validate_v9_ticket(load_json(ticket_path), root)
        fail(ticket["ticket_id"] != ticket_state["id"] or rel != ticket_state["path"] or payload["ticket"]["sha256"] != ticket_state["sha256"], "transition_invalid", "ATTEMPT_START ticket differs from the planned current ticket.")
        aid = require_id(payload["attempt_id"], "attempt_id")
        fail(payload["attempt_kind"] not in ("route_discovery", "route_execution", "candidate_revision", "candidate_synthesis"), "transition_invalid", "Attempt kind is invalid.")
        local = new["counters"]["run_local"]
        cumulative = new["counters"]["cumulative"]
        budgets = new["active_run"]["budgets"]
        fail(local["attempt_count"] + 1 > budgets["attempt_budget"] or local["total_round_count"] + 2 > budgets["total_round_budget"], "budget_exhausted", "ATTEMPT_START would consume the reserved terminal-audit round.")
        for target in (local, cumulative):
            target["attempt_count"] += 1
            target["total_round_count"] += 1
            target["attempts_since_last_audit"] += 1
        new["current_attempt"] = {"id": aid, "ticket_id": ticket_state["id"], "started_generation": generation, "kind": payload["attempt_kind"], "solver_result": None, "verifier_completion": None, "disposition": None}
        new["current_ticket"]["lifecycle"] = "active"
        new["active_run"]["status"] = "attempt_running"
    elif kind == "SOLVER_COMPLETE":
        require_exact(payload, ("schema", "solver_result", "occurred_at_utc"), "SOLVER_COMPLETE payload")
        require_timestamp(payload["occurred_at_utc"], "SOLVER_COMPLETE occurred_at_utc")
        fail(attempt is None or ticket_state is None or ticket_state["lifecycle"] != "active", "transition_invalid", "SOLVER_COMPLETE requires an active attempt ticket.")
        pointer(payload["solver_result"], root, "solver result")
        new["current_attempt"]["solver_result"] = payload["solver_result"]
        new["current_ticket"]["lifecycle"] = "solver_completed"
    elif kind == "VERIFIER_COMPLETE":
        require_exact(payload, ("schema", "verifier_completion", "evidence_items", "occurred_at_utc"), "VERIFIER_COMPLETE payload")
        require_timestamp(payload["occurred_at_utc"], "VERIFIER_COMPLETE occurred_at_utc")
        fail(attempt is None or ticket_state is None or ticket_state["lifecycle"] != "solver_completed", "transition_invalid", "VERIFIER_COMPLETE requires solver_completed.")
        _, completion_path = pointer(payload["verifier_completion"], root, "verifier completion")
        completion = load_json(completion_path)
        require_exact(completion, ("schema", "project_id", "run_id", "attempt_id", "ticket_id", "verdict", "candidate", "completed_at_utc"), "verifier completion")
        fail(completion["schema"] != "math-research-verifier-completion/v9" or completion["project_id"] != new["project_id"] or completion["run_id"] != new["active_run"]["id"] or completion["attempt_id"] != attempt["id"] or completion["ticket_id"] != ticket_state["id"], "transition_invalid", "Verifier completion identity binding failed.")
        fail(completion["verdict"] not in ("PASS", "FAIL", "INCONCLUSIVE"), "transition_invalid", "Verifier verdict is invalid.")
        require_timestamp(completion["completed_at_utc"], "verifier completion time")
        if completion["candidate"] is not None:
            pointer(completion["candidate"], root, "verified candidate")
        evidence = validate_evidence(payload["evidence_items"], root, "verifier evidence")
        for item in evidence:
            fail(item["attempt_id"] != attempt["id"] or item["ticket_id"] != ticket_state["id"], "evidence_invalid", "Evidence is not bound to the current attempt and ticket.")
        new["current_attempt"]["verifier_completion"] = payload["verifier_completion"]
        new["current_ticket"]["lifecycle"] = "verifier_completed"
        new["evidence_items"].extend(copy.deepcopy(evidence))
    elif kind == "ATTEMPT_END":
        require_exact(payload, ("schema", "disposition", "attempt_record", "evidence_items", "next_ticket", "occurred_at_utc"), "ATTEMPT_END payload")
        require_timestamp(payload["occurred_at_utc"], "ATTEMPT_END occurred_at_utc")
        disposition = payload["disposition"]
        fail(disposition not in DISPOSITIONS, "transition_invalid", "Attempt disposition is invalid.")
        fail(attempt is None or ticket_state is None or ticket_state["lifecycle"] != "verifier_completed", "transition_invalid", "ATTEMPT_END requires verifier_completed.")
        _, record_path = pointer(payload["attempt_record"], root, "attempt record")
        record = load_json(record_path)
        require_exact(record, ("schema", "project_id", "run_id", "attempt_id", "ticket_id", "disposition", "evidence", "completed_at_utc"), "attempt record")
        fail(record["schema"] != "math-research-attempt-record/v9" or record["project_id"] != new["project_id"] or record["run_id"] != new["active_run"]["id"] or record["attempt_id"] != attempt["id"] or record["ticket_id"] != ticket_state["id"] or record["disposition"] != disposition, "transition_invalid", "Attempt record identity/outcome binding failed.")
        validate_evidence(record["evidence"], root, "attempt record evidence")
        evidence = validate_evidence(payload["evidence_items"], root, "ATTEMPT_END evidence")
        fail(record["evidence"] != evidence, "transition_invalid", "Attempt record evidence differs from ATTEMPT_END evidence.")
        completion = load_json(resolve_under(root, attempt["verifier_completion"]["path"], "verifier completion"))
        kinds = {item["kind"] for item in evidence}
        if disposition == "candidate":
            fail(completion["verdict"] != "PASS" or "candidate" not in kinds, "transition_invalid", "candidate disposition requires PASS and candidate evidence.")
        if disposition == "no_candidate_with_evidence":
            fail(completion["verdict"] != "PASS" or "verified_partial" not in kinds, "transition_invalid", "no_candidate_with_evidence requires PASS verified_partial evidence.")
        new["evidence_items"] = _dedupe_records(new["evidence_items"] + copy.deepcopy(evidence))
        new["typed_references"].append({"kind": "attempt_record", "path": payload["attempt_record"]["path"], "sha256": payload["attempt_record"]["sha256"], "attempt_id": attempt["id"], "ticket_id": ticket_state["id"]})
        new["current_attempt"]["disposition"] = disposition
        new["current_ticket"]["lifecycle"] = "closed"
        new["current_attempt"] = None
        if payload["next_ticket"] is not None:
            rel, next_path = pointer(payload["next_ticket"], root, "next planned ticket")
            next_ticket = validate_v9_ticket(load_json(next_path), root)
            fail(next_ticket["ticket_id"] == ticket_state["id"], "transition_invalid", "The next ticket must have a fresh ID.")
            new["current_ticket"] = {"id": next_ticket["ticket_id"], "path": rel, "sha256": payload["next_ticket"]["sha256"], "lifecycle": "planned"}
            new["active_run"]["status"] = "preparing"
        else:
            new["current_ticket"] = None
            new["active_run"]["status"] = "audit_due" if disposition == "candidate" else "awaiting_input"
    else:
        require_exact(payload, ("schema", "references", "occurred_at_utc"), "CHECKPOINT_COMMIT payload")
        require_timestamp(payload["occurred_at_utc"], "CHECKPOINT_COMMIT occurred_at_utc")
        refs = validate_references(payload["references"], root, "checkpoint references")
        if attempt is not None:
            for item in refs:
                if item["attempt_id"] is not None:
                    fail(item["attempt_id"] != attempt["id"], "reference_invalid", "Checkpoint reference attempt binding differs from current attempt.")
                if item["ticket_id"] is not None:
                    fail(item["ticket_id"] != ticket_state["id"], "reference_invalid", "Checkpoint reference ticket binding differs from current ticket.")
        new["typed_references"] = _dedupe_records(new["typed_references"] + copy.deepcopy(refs))
    new["control_generation"] = generation
    new["updated_at_utc"] = payload["occurred_at_utc"]
    return new


def _dedupe_records(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[bytes] = set()
    for item in items:
        key = canonical_bytes(item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _write_stage(path: Path, value: Any, mtime_ns: int) -> dict[str, Any]:
    data = canonical_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    os.utime(path, ns=(mtime_ns, mtime_ns))
    return {"source": str(path.resolve()), "sha256": sha_bytes(data), "size": len(data), "mtime_ns": mtime_ns}


def _payload_pointer_paths(value: Any) -> set[str]:
    result: set[str] = set()
    if isinstance(value, dict):
        if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
            result.add(safe_relative(value["path"], "payload pointer path"))
        for child in value.values():
            result.update(_payload_pointer_paths(child))
    elif isinstance(value, list):
        for child in value:
            result.update(_payload_pointer_paths(child))
    return result


def prepare_transition(project: Path, kind: str, payload_path: Path, output: Path, audit_mode: str) -> dict[str, Any]:
    payload = load_json(payload_path)
    head, state, manifest, old_hash, audit_notes = load_v9_project(project, audit_mode, _payload_pointer_paths(payload))
    generation = head["control_generation"] + 1
    new_state = apply_transition(project, state, kind, payload, generation)
    validate_state(project, new_state)
    stamp = time.time_ns()
    generation_name = f"g{generation:04d}"
    state_rel = f"state/generations/{generation_name}/state-v9.json"
    event_rel = f"events/{generation_name}-{kind.lower().replace('_', '-')}.json"
    manifest_rel = f"state/manifests/{generation_name}.json"
    stage_root = output.resolve()
    fail(stage_root == project.resolve() or project.resolve() in stage_root.parents, "stage_invalid", "Transition staging must be outside the project root.")
    stage_root.mkdir(parents=True, exist_ok=True)
    state_info = _write_stage(stage_root / state_rel, new_state, stamp)
    event = {
        "schema": "math-research-event/v9",
        "project_id": head["project_id"],
        "control_generation": generation,
        "event_type": kind,
        "previous_event": head["event_tail"],
        "payload_sha256": sha_file(payload_path),
        "occurred_at_utc": payload["occurred_at_utc"],
    }
    event_info = _write_stage(stage_root / event_rel, event, stamp + 1)

    entries = copy.deepcopy(manifest["entries"])
    by_path = {item["path"]: item for item in entries}
    old_manifest_rel = head["archive_manifest"]["path"]
    if old_manifest_rel not in by_path:
        by_path[old_manifest_rel] = _entry_for(project, old_manifest_rel, head["control_generation"])
    for ptr in _collect_state_pointers(new_state):
        rel, _ = pointer(ptr, project, "transition referenced artifact")
        if rel not in by_path:
            by_path[rel] = _entry_for(project, rel, generation)
    by_path[state_rel] = {"path": state_rel, "sha256": state_info["sha256"], "size": state_info["size"], "mtime_ns": state_info["mtime_ns"], "generation_added": generation}
    by_path[event_rel] = {"path": event_rel, "sha256": event_info["sha256"], "size": event_info["size"], "mtime_ns": event_info["mtime_ns"], "generation_added": generation}
    new_manifest = {"schema": "math-research-archive-manifest/v9", "project_id": head["project_id"], "control_generation": generation, "entries": [by_path[key] for key in sorted(by_path)], "created_at_utc": payload["occurred_at_utc"]}
    manifest_info = _write_stage(stage_root / manifest_rel, new_manifest, stamp + 2)
    full_used = "full_audit_used" in audit_notes
    new_head = {
        "schema": "math-research-project/v9",
        "project_id": head["project_id"],
        "control_generation": generation,
        "state": {"path": state_rel, "sha256": state_info["sha256"]},
        "event_tail": {"path": event_rel, "sha256": event_info["sha256"]},
        "archive_manifest": {"path": manifest_rel, "sha256": manifest_info["sha256"]},
        "last_full_audit_generation": generation if full_used else head["last_full_audit_generation"],
        "last_full_audit_at_utc": payload["occurred_at_utc"] if full_used else head["last_full_audit_at_utc"],
    }
    project_info = _write_stage(stage_root / "project.json", new_head, stamp + 3)
    files = [
        {"target": state_rel, **state_info},
        {"target": event_rel, **event_info},
        {"target": manifest_rel, **manifest_info},
    ]
    plan = {
        "schema": "math-research-transition-plan/v9",
        "project_root": str(project.resolve()),
        "expected_head_sha256": old_hash,
        "expected_generation": head["control_generation"],
        "new_generation": generation,
        "event_type": kind,
        "immutable_files": files,
        "candidate_project": {"source": project_info["source"], "sha256": project_info["sha256"], "mtime_ns": project_info["mtime_ns"]},
        "created_at_utc": now_utc(),
    }
    plan_info = _write_stage(stage_root / "transition-plan.json", plan, stamp + 4)
    return {"prepared": True, "plan_path": str((stage_root / "transition-plan.json").resolve()), "plan_sha256": plan_info["sha256"], "old_head_sha256": old_hash, "candidate_head_sha256": project_info["sha256"], "new_generation": generation, "audit_notes": audit_notes}


def prepare_successor(predecessor: Path, successor: Path, spec_path: Path, output: Path) -> dict[str, Any]:
    pred_head_path = predecessor / "project.json"
    fail(not pred_head_path.is_file(), "predecessor_missing", "Predecessor project.json is absent.")
    pred_hash = sha_file(pred_head_path)
    spec = load_json(spec_path)
    require_exact(spec, ("schema", "predecessor", "successor", "reason", "cumulative_counters", "initial_ticket", "occurred_at_utc"), "successor spec")
    fail(spec["schema"] != "math-research-successor-spec/v9", "successor_invalid", "Successor spec schema is invalid.")
    require_timestamp(spec["occurred_at_utc"], "successor occurred_at_utc")
    pred = require_exact(spec["predecessor"], ("project_id", "run_id", "head_sha256", "final_status", "envelope_sha256", "permission_envelope_sha256", "resource_envelope_sha256", "remaining_attempt_budget", "remaining_total_round_budget"), "predecessor spec")
    succ = require_exact(spec["successor"], ("project_id", "run_id", "envelope_sha256", "permission_envelope_sha256", "resource_envelope_sha256", "budgets"), "successor identity")
    require_id(pred["project_id"], "predecessor project id")
    require_id(pred["run_id"], "predecessor run id")
    require_hash(pred["head_sha256"], "predecessor head hash")
    fail(pred["head_sha256"] != pred_hash, "successor_invalid", "Predecessor head hash differs from live project.json.")
    fail(pred["final_status"] not in ("closed", "superseded", "budget_exhausted", "route_exhausted"), "successor_invalid", "Predecessor is not terminal for successor creation.")
    require_id(succ["project_id"], "successor project id")
    require_id(succ["run_id"], "successor run id")
    fail(succ["project_id"] != pred["project_id"], "successor_invalid", "Successor must preserve the project lineage ID.")
    for key in ("envelope_sha256", "permission_envelope_sha256", "resource_envelope_sha256"):
        require_hash(pred[key], f"predecessor {key}")
        require_hash(succ[key], f"successor {key}")
        fail(pred[key] != succ[key], "successor_envelope_expanded", f"Successor {key} differs from predecessor.")
    fail(spec["reason"] not in ("budget_exhausted", "route_exhausted", "schema_upgrade", "operator_request"), "successor_invalid", "Successor reason is invalid.")
    for key in ("remaining_attempt_budget", "remaining_total_round_budget"):
        fail(type(pred[key]) is not int or pred[key] < 0, "successor_invalid", f"{key} is invalid.")
    require_exact(succ["budgets"], ("attempt_budget", "total_round_budget"), "successor budgets")
    fail(type(succ["budgets"]["attempt_budget"]) is not int or succ["budgets"]["attempt_budget"] < 0 or succ["budgets"]["attempt_budget"] > pred["remaining_attempt_budget"], "successor_envelope_expanded", "Successor attempt budget exceeds predecessor remainder.")
    fail(type(succ["budgets"]["total_round_budget"]) is not int or succ["budgets"]["total_round_budget"] < 0 or succ["budgets"]["total_round_budget"] > pred["remaining_total_round_budget"], "successor_envelope_expanded", "Successor round budget exceeds predecessor remainder.")
    cumulative = counters(spec["cumulative_counters"], "successor cumulative counters")
    fail((successor / "project.json").exists(), "successor_exists", "Successor project already has project.json; use ordinary transitions or idempotent commit.")
    ticket = validate_v9_ticket(spec["initial_ticket"], successor)
    ticket_rel = f"runs/{succ['run_id']}/tickets/{ticket['ticket_id']}.json"
    stage_root = output.resolve()
    fail(stage_root == successor.resolve() or successor.resolve() in stage_root.parents, "stage_invalid", "Successor staging must be outside the successor root.")
    stage_root.mkdir(parents=True, exist_ok=True)
    stamp = time.time_ns()
    ticket_info = _write_stage(stage_root / ticket_rel, ticket, stamp)
    lineage_rel = "lineage/predecessor-v9.json"
    lineage = {"schema": "math-research-predecessor/v9", "project_id": pred["project_id"], "run_id": pred["run_id"], "head_sha256": pred_hash, "final_status": pred["final_status"]}
    lineage_info = _write_stage(stage_root / lineage_rel, lineage, stamp + 1)
    state_rel = "state/generations/g0001/state-v9.json"
    state = {
        "schema": "math-research-state/v9",
        "project_id": succ["project_id"],
        "control_generation": 1,
        "active_run": {"id": succ["run_id"], "status": "preparing", "envelope_sha256": succ["envelope_sha256"], "permission_envelope_sha256": succ["permission_envelope_sha256"], "resource_envelope_sha256": succ["resource_envelope_sha256"], "predecessor": {"project_id": pred["project_id"], "run_id": pred["run_id"], "head_sha256": pred_hash, "final_status": pred["final_status"]}, "budgets": succ["budgets"]},
        "current_attempt": None,
        "current_ticket": {"id": ticket["ticket_id"], "path": ticket_rel, "sha256": ticket_info["sha256"], "lifecycle": "planned"},
        "counters": {"run_local": {"attempt_count": 0, "audit_count": 0, "total_round_count": 0, "attempts_since_last_audit": 0}, "cumulative": cumulative},
        "evidence_items": [],
        "typed_references": [],
        "updated_at_utc": spec["occurred_at_utc"],
    }
    state_info = _write_stage(stage_root / state_rel, state, stamp + 2)
    event_rel = "events/g0001-run-successor.json"
    event = {"schema": "math-research-event/v9", "project_id": succ["project_id"], "control_generation": 1, "event_type": "RUN_SUCCESSOR", "previous_event": None, "payload_sha256": sha_file(spec_path), "occurred_at_utc": spec["occurred_at_utc"]}
    event_info = _write_stage(stage_root / event_rel, event, stamp + 3)
    entries: list[dict[str, Any]] = []
    for item in ticket["input_artifacts"]:
        entries.append(_entry_for(successor, item["path"], 1))
    for rel, info in ((ticket_rel, ticket_info), (lineage_rel, lineage_info), (state_rel, state_info), (event_rel, event_info)):
        entries.append({"path": rel, "sha256": info["sha256"], "size": info["size"], "mtime_ns": info["mtime_ns"], "generation_added": 1})
    entries = [dict(item) for item in {item["path"]: item for item in entries}.values()]
    manifest_rel = "state/manifests/g0001.json"
    manifest = {"schema": "math-research-archive-manifest/v9", "project_id": succ["project_id"], "control_generation": 1, "entries": sorted(entries, key=lambda item: item["path"]), "created_at_utc": spec["occurred_at_utc"]}
    manifest_info = _write_stage(stage_root / manifest_rel, manifest, stamp + 4)
    head = {"schema": "math-research-project/v9", "project_id": succ["project_id"], "control_generation": 1, "state": {"path": state_rel, "sha256": state_info["sha256"]}, "event_tail": {"path": event_rel, "sha256": event_info["sha256"]}, "archive_manifest": {"path": manifest_rel, "sha256": manifest_info["sha256"]}, "last_full_audit_generation": 1, "last_full_audit_at_utc": spec["occurred_at_utc"]}
    project_info = _write_stage(stage_root / "project.json", head, stamp + 5)
    immutable = []
    for rel, info in ((ticket_rel, ticket_info), (lineage_rel, lineage_info), (state_rel, state_info), (event_rel, event_info), (manifest_rel, manifest_info)):
        immutable.append({"target": rel, **info})
    plan = {"schema": "math-research-transition-plan/v9", "project_root": str(successor.resolve()), "expected_head_sha256": None, "expected_generation": 0, "new_generation": 1, "event_type": "RUN_SUCCESSOR", "immutable_files": immutable, "candidate_project": {"source": project_info["source"], "sha256": project_info["sha256"], "mtime_ns": project_info["mtime_ns"]}, "created_at_utc": now_utc()}
    plan_info = _write_stage(stage_root / "transition-plan.json", plan, stamp + 6)
    return {"prepared": True, "plan_path": str((stage_root / "transition-plan.json").resolve()), "plan_sha256": plan_info["sha256"], "predecessor_head_sha256": pred_hash, "candidate_head_sha256": project_info["sha256"], "new_generation": 1}


def _copy_create_new(source: Path, target: Path, expected_hash: str, mtime_ns: int) -> None:
    fail(sha_file(source) != expected_hash, "plan_invalid", f"Staged source hash mismatch: {source.name}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        fail(not target.is_file() or sha_file(target) != expected_hash, "immutable_conflict", f"Immutable target exists with different bytes: {target}")
        return
    data = source.read_bytes()
    try:
        with target.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        fail(sha_file(target) != expected_hash, "immutable_conflict", f"Immutable target raced with different bytes: {target}")
    os.utime(target, ns=(mtime_ns, mtime_ns))


def commit_plan(plan_path: Path, goal_status: str) -> dict[str, Any]:
    fail(goal_status != "active", "goal_not_active", "A fresh active Goal assertion is required immediately before commit.")
    plan = load_json(plan_path)
    require_exact(plan, ("schema", "project_root", "expected_head_sha256", "expected_generation", "new_generation", "event_type", "immutable_files", "candidate_project", "created_at_utc"), "transition plan")
    fail(plan["schema"] != "math-research-transition-plan/v9", "plan_invalid", "Transition plan schema is invalid.")
    project = Path(plan["project_root"])
    project.mkdir(parents=True, exist_ok=True)
    lock = project / ".math-research-v9.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise ResearchError("writer_busy", "The cooperative v9 writer lock already exists.") from exc
    try:
        os.write(fd, f"pid={os.getpid()}\n".encode("ascii"))
        os.close(fd)
        head_path = project / "project.json"
        candidate = plan["candidate_project"]
        require_exact(candidate, ("source", "sha256", "mtime_ns"), "candidate project")
        candidate_source = Path(candidate["source"])
        candidate_hash = require_hash(candidate["sha256"], "candidate project hash")
        fail(sha_file(candidate_source) != candidate_hash, "plan_invalid", "Candidate project bytes changed.")
        if head_path.exists() and sha_file(head_path) == candidate_hash:
            return {"committed": True, "reused": True, "project_sha256": candidate_hash, "generation": plan["new_generation"]}
        if plan["expected_head_sha256"] is None:
            fail(head_path.exists(), "cas_conflict", "Successor project head appeared after preparation.")
        else:
            expected = require_hash(plan["expected_head_sha256"], "expected head hash")
            fail(not head_path.is_file() or sha_file(head_path) != expected, "cas_conflict", "project.json differs from the prepared expected head.")
        fail(not isinstance(plan["immutable_files"], list) or not plan["immutable_files"], "plan_invalid", "Plan has no immutable files.")
        for item in plan["immutable_files"]:
            require_exact(item, ("target", "source", "sha256", "size", "mtime_ns"), "plan immutable file")
            rel = safe_relative(item["target"], "immutable target")
            source = Path(item["source"])
            expected = require_hash(item["sha256"], "immutable hash")
            fail(type(item["mtime_ns"]) is not int or item["mtime_ns"] < 0, "plan_invalid", "Immutable mtime is invalid.")
            _copy_create_new(source, project / rel, expected, item["mtime_ns"])
        if plan["expected_head_sha256"] is not None:
            fail(sha_file(head_path) != plan["expected_head_sha256"], "cas_conflict", "project.json changed during immutable publication.")
        elif head_path.exists():
            fail(True, "cas_conflict", "Successor project head appeared during immutable publication.")
        data = candidate_source.read_bytes()
        temp = project / f".project.{os.getpid()}.{time.time_ns()}.tmp"
        with temp.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.utime(temp, ns=(candidate["mtime_ns"], candidate["mtime_ns"]))
        os.replace(temp, head_path)
        fail(sha_file(head_path) != candidate_hash, "commit_readback_failed", "Committed project.json did not read back with the candidate hash.")
        return {"committed": True, "reused": False, "project_sha256": candidate_hash, "generation": plan["new_generation"], "cooperative_cas_only": True}
    finally:
        try:
            if lock.exists():
                lock.unlink()
        except OSError:
            pass


def startup(project: Path, audit_mode: str, legacy_goal_status: str | None) -> dict[str, Any]:
    project_path = project / "project.json"
    if not project_path.exists():
        return {"classification": "fresh_project_slot", "schema_version": None, "audit_mode_used": "none"}
    raw = load_json(project_path)
    if isinstance(raw, dict) and raw.get("schema") == "math-research-project/v9":
        head, state, _, head_hash, notes = load_v9_project(project, audit_mode)
        used = "Full" if "full_audit_used" in notes else "Fast"
        return {"classification": "v9_ready", "schema_version": 9, "project_id": head["project_id"], "control_generation": head["control_generation"], "project_sha256": head_hash, "run_status": state["active_run"]["status"], "ticket_lifecycle": None if state["current_ticket"] is None else state["current_ticket"]["lifecycle"], "audit_mode_used": used, "audit_notes": notes}
    return {"classification": "delegate_startup_v3", "schema_version": "v3-v8", "goal_status_advisory": legacy_goal_status}


def emit_success(data: dict[str, Any]) -> int:
    print(json.dumps({"ok": True, "data": data, "warnings": []}, ensure_ascii=False, sort_keys=True))
    return 0


def emit_error(exc: ResearchError) -> int:
    print(json.dumps({"ok": False, "error": {"code": exc.code, "message": exc.message, "recovery": exc.recovery}}, ensure_ascii=False, sort_keys=True))
    return 2


def parser() -> argparse.ArgumentParser:
    main = argparse.ArgumentParser()
    sub = main.add_subparsers(dest="command", required=True)
    pre = sub.add_parser("ticket-preflight-v8")
    pre.add_argument("--project", required=True)
    pre.add_argument("--ticket", required=True)
    pre.add_argument("--source-requirements", required=True)
    pre.add_argument("--access-log")
    start = sub.add_parser("startup")
    start.add_argument("--project", required=True)
    start.add_argument("--audit-mode", choices=("Auto", "Full"), default="Auto")
    start.add_argument("--legacy-goal-status")
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--project", required=True)
    prepare.add_argument("--transition", choices=sorted(TRANSITIONS), required=True)
    prepare.add_argument("--payload", required=True)
    prepare.add_argument("--output", required=True)
    prepare.add_argument("--audit-mode", choices=("Auto", "Full"), default="Auto")
    successor = sub.add_parser("prepare-successor")
    successor.add_argument("--predecessor-project", required=True)
    successor.add_argument("--successor-project", required=True)
    successor.add_argument("--spec", required=True)
    successor.add_argument("--output", required=True)
    commit = sub.add_parser("commit")
    commit.add_argument("--plan", required=True)
    commit.add_argument("--goal-status", required=True)
    return main


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "ticket-preflight-v8":
            data = preflight_v8(Path(args.project), Path(args.ticket), Path(args.source_requirements), Path(args.access_log) if args.access_log else None)
        elif args.command == "startup":
            data = startup(Path(args.project), args.audit_mode, args.legacy_goal_status)
        elif args.command == "prepare":
            data = prepare_transition(Path(args.project), args.transition, Path(args.payload), Path(args.output), args.audit_mode)
        elif args.command == "prepare-successor":
            data = prepare_successor(Path(args.predecessor_project), Path(args.successor_project), Path(args.spec), Path(args.output))
        else:
            data = commit_plan(Path(args.plan), args.goal_status)
        return emit_success(data)
    except ResearchError as exc:
        return emit_error(exc)
    except Exception as exc:  # fail closed without a traceback in the machine contract
        return emit_error(ResearchError("internal_error", f"{type(exc).__name__}: {exc}"))


if __name__ == "__main__":
    sys.exit(main())
