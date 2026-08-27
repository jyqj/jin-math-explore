#!/usr/bin/env python3
"""Read-only, project-neutral Startup validator for frozen v11 projects.

The former one-project v10-to-v11 merge implementation was deliberately
retired.  Existing v11 projects remain readable and hash-auditable; migration
or mutation requires a separately frozen project-local adapter and the current
v13 migration transaction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any


PROJECT_SCHEMA = "math-research-project/v11"
OBJECTIVE_SCHEMA = "math-research-project-objective/v1"
MEMORY_SCHEMA = "math-research-project-memory/v1"
STATE_SCHEMA = "math-research-state/v11"
ROUTE_REVIEW_SCHEMA = "math-research-route-review/v1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
MEMORY_CLASSES = {
    "verified_fact",
    "verified_failure_boundary",
    "conditional_result",
    "attempted_with_difficulty",
    "known_pitfall",
    "route_local",
}
TRUST_STATES = {
    "promoted",
    "independently_verified",
    "registered_unverified",
    "reproduction_blocked",
    "bounded_negative",
}
ORIGIN_KINDS = {"legacy_project_import", "external_intake", "internal_attempt", "migration"}


class ResearchError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def fail(condition: bool, code: str, message: str) -> None:
    if condition:
        raise ResearchError(code, message)


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ResearchError("json_duplicate_key", f"Duplicate JSON key: {key}")
        out[key] = value
    return out


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicates)
    except ResearchError:
        raise
    except Exception as exc:
        raise ResearchError("json_invalid", f"Cannot parse {path}: {exc}") from exc


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_rel(value: Any, label: str) -> str:
    fail(not isinstance(value, str) or not value, "path_invalid", f"{label} must be nonempty.")
    path = PurePosixPath(value)
    fail(path.is_absolute() or ".." in path.parts or "\\" in value, "path_invalid", f"{label} must be project-relative.")
    return path.as_posix()


def require_id(value: Any, label: str) -> str:
    fail(not isinstance(value, str) or not SAFE_ID.fullmatch(value), "id_invalid", f"{label} is invalid.")
    return value


def pointer(root: Path, value: Any, label: str) -> Path:
    fail(not isinstance(value, dict) or set(value) != {"path", "sha256"}, "pointer_invalid", f"{label} must be path/hash.")
    fail(not isinstance(value["sha256"], str) or not HEX64.fullmatch(value["sha256"]), "pointer_invalid", f"{label} hash is invalid.")
    path = root.joinpath(*PurePosixPath(safe_rel(value["path"], label)).parts)
    fail(not path.is_file() or path.is_symlink(), "pointer_missing", f"{label} target is missing.")
    fail(sha_file(path) != value["sha256"], "pointer_hash_mismatch", f"{label} hash mismatch.")
    return path


def validate_objective(value: Any, project_id: str) -> dict[str, Any]:
    required = {
        "schema", "project_id", "statement", "domain", "quantifier_order",
        "assumptions", "evidence_standard", "completion_standard", "created_at_utc",
    }
    fail(not isinstance(value, dict) or set(value) != required, "objective_invalid", "Project objective keys are invalid.")
    fail(value["schema"] != OBJECTIVE_SCHEMA or value["project_id"] != project_id, "objective_invalid", "Project objective identity is invalid.")
    for key in ("statement", "domain", "quantifier_order", "evidence_standard", "completion_standard", "created_at_utc"):
        fail(not isinstance(value[key], str) or not value[key].strip(), "objective_invalid", f"Objective field {key} is empty.")
    fail(not isinstance(value["assumptions"], list) or not all(isinstance(item, str) and item.strip() for item in value["assumptions"]), "objective_invalid", "Objective assumptions are invalid.")
    return value


def validate_memory(value: Any, project_id: str, objective_sha: str) -> dict[str, Any]:
    required = {"schema", "project_id", "project_objective_sha256", "entries", "current_frontier", "updated_at_utc"}
    fail(not isinstance(value, dict) or set(value) != required, "memory_invalid", "Project memory keys are invalid.")
    fail(value["schema"] != MEMORY_SCHEMA or value["project_id"] != project_id or value["project_objective_sha256"] != objective_sha, "memory_invalid", "Project memory identity mismatch.")
    fail(not isinstance(value["entries"], list), "memory_invalid", "Memory entries must be an array.")
    seen: set[str] = set()
    for item in value["entries"]:
        keys = {"memory_id", "classification", "statement", "origin", "trust_state", "permits", "does_not_imply", "reopen_condition", "evidence"}
        fail(not isinstance(item, dict) or set(item) != keys, "memory_invalid", "Memory entry keys are invalid.")
        memory_id = require_id(item["memory_id"], "memory_id")
        fail(memory_id in seen, "memory_invalid", "Duplicate memory ID.")
        seen.add(memory_id)
        fail(item["classification"] not in MEMORY_CLASSES or item["trust_state"] not in TRUST_STATES, "memory_invalid", "Memory classification/trust invalid.")
        fail(not isinstance(item["origin"], dict) or item["origin"].get("kind") not in ORIGIN_KINDS, "memory_invalid", "Memory origin invalid.")
        if item["classification"] in {"verified_fact", "verified_failure_boundary"} and item["trust_state"] == "promoted" and item["origin"]["kind"] == "external_intake":
            fail(not item["origin"].get("reproduction_sha256") or not item["origin"].get("verifier_id"), "verification_required", "Promoted external memory requires reproduction and verifier bindings.")
    return value


def startup(project: Path, *, full: bool = False) -> dict[str, Any]:
    project = project.resolve()
    head_path = project / "project.json"
    fail(not head_path.is_file(), "project_missing", "project.json is absent.")
    head = load_json(head_path)
    if not isinstance(head, dict) or head.get("schema") != PROJECT_SCHEMA:
        return {"classification": "delegate_startup_v5", "schema": head.get("schema") if isinstance(head, dict) else None, "project_sha256": sha_file(head_path)}
    required = {"schema", "project_id", "control_generation", "project_objective", "state", "event_tail", "archive_manifest", "updated_at_utc"}
    fail(set(head) != required, "project_invalid", "v11 project head keys are invalid.")
    project_id = require_id(head["project_id"], "project_id")
    objective_path = pointer(project, head["project_objective"], "project objective")
    objective = validate_objective(load_json(objective_path), project_id)
    state_path = pointer(project, head["state"], "v11 state")
    event_path = pointer(project, head["event_tail"], "v11 event")
    manifest_path = pointer(project, head["archive_manifest"], "v11 manifest")
    state = load_json(state_path)
    fail(state.get("schema") != STATE_SCHEMA or state.get("project_id") != project_id, "state_invalid", "v11 state identity invalid.")
    fail(state.get("project_objective") != head["project_objective"], "objective_changed", "State objective pointer differs from immutable head objective.")
    memory_path = pointer(project, state["project_memory"], "project memory")
    memory = validate_memory(load_json(memory_path), project_id, head["project_objective"]["sha256"])
    review = load_json(pointer(project, state["latest_route_review"], "route review"))
    fail(review.get("schema") != ROUTE_REVIEW_SCHEMA or review.get("new_math_performed") is not False, "route_review_invalid", "Route review is invalid or performed new mathematics.")
    counters = state.get("counters")
    counter_keys = {"internal_attempts_started", "internal_attempts_completed", "terminal_audits", "route_reviews", "attempts_since_route_review", "route_review_due"}
    fail(not isinstance(counters, dict) or set(counters) != counter_keys, "counter_invalid", "v11 counters are invalid.")
    fail(counters["internal_attempts_completed"] > counters["internal_attempts_started"], "counter_invalid", "Completed attempts exceed starts.")
    fail(counters["attempts_since_route_review"] >= 3 and not counters["route_review_due"], "route_review_gate_invalid", "Three completed attempts require a route review gate.")
    event = load_json(event_path)
    fail(event.get("schema") != "math-research-event/v11" or event.get("project_id") != project_id, "event_invalid", "v11 event invalid.")
    manifest = load_json(manifest_path)
    fail(manifest.get("schema") != "math-research-archive-manifest/v11" or manifest.get("project_id") != project_id, "manifest_invalid", "v11 manifest invalid.")
    for entry in manifest.get("entries", []):
        rel = safe_rel(entry.get("path"), "manifest path")
        path = project.joinpath(*PurePosixPath(rel).parts)
        fail(not path.is_file(), "manifest_missing_file", f"Manifest file missing: {rel}")
        if full:
            fail(path.stat().st_size != entry.get("size") or sha_file(path) != entry.get("sha256"), "archive_hash_mismatch", f"Manifest mismatch: {rel}")
    for intake_ptr in state.get("intakes", []):
        pointer(project, intake_ptr, "intake")
    return {
        "classification": "v11_ready",
        "schema_version": 11,
        "project_id": project_id,
        "project_sha256": sha_file(head_path),
        "control_generation": head["control_generation"],
        "project_complete": state["project_complete"],
        "objective": objective["completion_standard"],
        "counters": counters,
        "memory_entry_count": len(memory["entries"]),
        "route_review_due": counters["route_review_due"],
        "current_task": state["current_task"],
        "active_run": state["active_run"],
        "audit_mode_used": "Full" if full else "Auto",
        "mutation_supported": False,
    }


def parser() -> argparse.ArgumentParser:
    out = argparse.ArgumentParser(description=__doc__)
    sub = out.add_subparsers(dest="command", required=True)
    start = sub.add_parser("startup")
    start.add_argument("--project", type=Path, required=True)
    start.add_argument("--full", action="store_true")
    return out


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result = startup(args.project, full=args.full)
        print(json.dumps({"ok": True, **result}, ensure_ascii=False, separators=(",", ":")))
        return 0
    except ResearchError as exc:
        print(json.dumps({"ok": False, "error": {"code": exc.code, "message": str(exc)}}, ensure_ascii=False, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
