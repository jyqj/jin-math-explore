#!/usr/bin/env python3
"""Shared validator, transition builder, and guarded publisher for Math Research v10.

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
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable

import math_research_state_v9 as legacy_v9


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
CLAIM_STATUSES = {"verified", "working", "conditional", "refuted"}
RESET_TRIGGERS = {
    "none",
    "explicit_user_ban",
    "same_family_negative_ceiling",
    "special_family_without_coverage_bridge",
    "strategy_semantic_overlap",
    "same_family_ceiling",
}
STRATEGY_ACTIONS = {"continue", "synthesize", "semantic_reset", "quarantine", "await_input"}
PROOF_DIRECTIONS = {
    "primal_extremizer",
    "dual_separation",
    "explicit_construction",
    "induction",
    "counterexample",
    "computation",
    "other",
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
    "execution_topology_receipt",
    "migration_record",
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
    "continuity_capsule",
    "route_card",
    "proof_artifact",
    "strategy_audit",
}
TRANSITIONS = {
    "ATTEMPT_START",
    "ROUTE_RESET_TRIGGER",
    "ROUTE_PORTFOLIO_ACCEPT",
    "SOLVER_COMPLETE",
    "VERIFIER_COMPLETE",
    "ATTEMPT_END",
    "CHECKPOINT_COMMIT",
    "RESEARCH_CHECKPOINT",
    "ASSET_REGISTRY_UPDATE",
}
AUTHORITATIVE_PREFIXES = ("contracts/", "events/", "evidence/", "inputs/", "lineage/", "runs/", "state/")
V8_FREEZE_REL = "state/migration-freeze-v10.json"


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


def _asset_tools():
    path = Path(__file__).with_name("math_research_assets.py")
    spec = importlib.util.spec_from_file_location("math_research_assets", path)
    fail(spec is None or spec.loader is None, "asset_tool_unavailable", "The research asset validator is unavailable.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_asset_index_pointer(value: Any, root: Path, project_id: str) -> dict[str, str]:
    rel, path = pointer(value, root, "asset index")
    try:
        loaded = _asset_tools().load_index(root, path)
    except Exception as exc:
        code = getattr(exc, "code", "asset_index_invalid")
        message = getattr(exc, "message", str(exc))
        raise ResearchError(code, f"Asset index validation failed: {message}") from exc
    fail(loaded["index"]["project_id"] != project_id, "asset_index_invalid", "Asset index project identity differs from state.")
    return {"path": rel, "sha256": value["sha256"]}


def asset_index_closure(value: Any, root: Path, project_id: str) -> list[dict[str, str]]:
    index_pointer = validate_asset_index_pointer(value, root, project_id)
    index_path = resolve_under(root, index_pointer["path"], "asset index")
    loaded = _asset_tools().load_index(root, index_path)
    result = [index_pointer]
    result.extend(copy.deepcopy(loaded["index"][key]) for key in ("asset_registry", "contribution_ledger", "export_policy"))
    for asset in loaded["registry"]["assets"]:
        for artifact in asset["local_artifacts"]:
            result.append({"path": artifact["path"], "sha256": artifact["sha256"]})
    return _dedupe_pointer_records(result)


def _dedupe_pointer_records(items: list[dict[str, str]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in items:
        if item["path"] not in seen:
            seen.add(item["path"])
            result.append(item)
    return result


def validate_incremental_migration(value: Any, root: Path, state: dict[str, Any]) -> dict[str, Any]:
    migration = require_exact(
        value,
        (
            "schema", "status", "migration_id", "predecessor_schema",
            "predecessor_directory_name", "predecessor_control_generation",
            "predecessor_run_status", "successor_directory_name", "manifest", "freeze_record",
            "envelope_snapshot", "lineage",
        ),
        "incremental migration",
    )
    fail(migration["schema"] != "math-research-incremental-migration/v10" or migration["status"] != "frozen", "migration_invalid", "Incremental migration schema or status is invalid.")
    require_id(migration["migration_id"], "migration id")
    fail(migration["predecessor_schema"] != "v8", "migration_invalid", "Only a v8 predecessor is supported by this migration record.")
    fail(type(migration["predecessor_control_generation"]) is not int or migration["predecessor_control_generation"] < 1, "migration_invalid", "Predecessor generation is invalid.")
    fail(not isinstance(migration["predecessor_directory_name"], str) or migration["predecessor_directory_name"] in ("", ".", "..") or Path(migration["predecessor_directory_name"]).name != migration["predecessor_directory_name"], "migration_invalid", "Predecessor directory name is invalid.")
    fail(not isinstance(migration["successor_directory_name"], str) or migration["successor_directory_name"] in ("", ".", "..") or Path(migration["successor_directory_name"]).name != migration["successor_directory_name"], "migration_invalid", "Successor directory name is invalid.")
    fail(not isinstance(migration["predecessor_run_status"], str) or not migration["predecessor_run_status"], "migration_invalid", "Predecessor run status is invalid.")
    for key in ("manifest", "freeze_record", "envelope_snapshot", "lineage"):
        pointer(migration[key], root, f"migration {key}")
    freeze = load_json(resolve_under(root, migration["freeze_record"]["path"], "migration freeze record"))
    require_exact(freeze, ("schema", "migration_id", "predecessor", "successor", "migration_manifest", "occurred_at_utc"), "migration freeze record")
    fail(freeze["schema"] != "math-research-v8-freeze/v10" or freeze["migration_id"] != migration["migration_id"], "migration_invalid", "Freeze record identity differs from state.")
    require_timestamp(freeze["occurred_at_utc"], "migration freeze time")
    predecessor = require_exact(freeze["predecessor"], ("project_id", "head_sha256", "control_generation", "run_id", "run_status"), "migration predecessor")
    successor = require_exact(freeze["successor"], ("project_id", "run_id", "directory_name"), "migration successor")
    active_predecessor = state["active_run"]["predecessor"]
    fail(
        predecessor["project_id"] != state["project_id"]
        or predecessor["head_sha256"] != active_predecessor["head_sha256"]
        or predecessor["control_generation"] != migration["predecessor_control_generation"]
        or predecessor["run_id"] != active_predecessor["run_id"]
        or predecessor["run_status"] != migration["predecessor_run_status"],
        "migration_invalid",
        "Freeze record predecessor differs from the migrated state.",
    )
    fail(successor != {"project_id": state["project_id"], "run_id": state["active_run"]["id"], "directory_name": migration["successor_directory_name"]}, "migration_invalid", "Freeze record successor differs from the migrated state.")
    fail(freeze["migration_manifest"] != migration["manifest"], "migration_invalid", "Freeze record manifest differs from state.")
    return migration


def validate_migration_predecessor_freeze(root: Path, state: dict[str, Any]) -> dict[str, Any] | None:
    migration = state.get("migration")
    if migration is None:
        return None
    validate_incremental_migration(migration, root, state)
    predecessor_root = root.parent / migration["predecessor_directory_name"]
    fail(predecessor_root.resolve().parent != root.resolve().parent, "migration_path_invalid", "Migrated predecessor is not a sibling of the v10 project.")
    marker = predecessor_root / V8_FREEZE_REL
    fail(not marker.is_file(), "predecessor_not_frozen", "The migrated v8 predecessor freeze marker is absent.")
    expected = migration["freeze_record"]["sha256"]
    fail(sha_file(marker) != expected, "predecessor_not_frozen", "The migrated v8 predecessor freeze marker differs from the v10 record.")
    predecessor_head = predecessor_root / "project.json"
    fail(not predecessor_head.is_file() or sha_file(predecessor_head) != state["active_run"]["predecessor"]["head_sha256"], "predecessor_changed_after_migration", "The frozen v8 project head changed after migration.")
    return {"predecessor_root": str(predecessor_root.resolve()), "freeze_sha256": expected}


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


def _string(value: Any, label: str) -> str:
    fail(not isinstance(value, str) or not value.strip(), "schema_invalid", f"{label} must be a nonempty string.")
    return value


def _string_array(value: Any, label: str, *, allow_empty: bool = True) -> list[str]:
    fail(not isinstance(value, list) or (not allow_empty and not value), "schema_invalid", f"{label} must be an array.")
    out: list[str] = []
    for index, item in enumerate(value):
        fail(not isinstance(item, str) or not item.strip(), "schema_invalid", f"{label}[{index}] must be a nonempty string.")
        out.append(item)
    fail(len(out) != len(set(out)), "schema_invalid", f"{label} contains duplicates.")
    return out


def validate_route_reset_directive(value: Any) -> dict[str, Any]:
    require_exact(
        value,
        ("required", "trigger", "forbidden_mechanism_family_ids", "minimum_distinct_cards", "same_family_ceiling"),
        "route reset directive",
    )
    fail(type(value["required"]) is not bool, "route_reset_invalid", "route reset required must be Boolean.")
    fail(value["trigger"] not in RESET_TRIGGERS, "route_reset_invalid", "route reset trigger is invalid.")
    _string_array(value["forbidden_mechanism_family_ids"], "forbidden mechanism families")
    for key in ("minimum_distinct_cards", "same_family_ceiling"):
        fail(type(value[key]) is not int or value[key] < 1, "route_reset_invalid", f"{key} must be a positive integer.")
    if value["required"]:
        fail(value["trigger"] == "none", "route_reset_invalid", "A required semantic reset needs a concrete trigger.")
        fail(value["minimum_distinct_cards"] < 2, "route_reset_invalid", "A semantic reset requires at least two distinct route cards.")
    else:
        fail(value["trigger"] != "none", "route_reset_invalid", "A non-required reset must use trigger=none.")
    return value


def validate_route_card(value: Any) -> dict[str, Any]:
    require_exact(
        value,
        (
            "schema", "route_id", "status", "core_proof_object", "proof_direction",
            "quantifier_strategy", "mechanism_family_id", "ancestor_route_ids",
            "coverage_bridge", "forbidden_family_relationship", "non_renaming_reason",
            "special_family", "created_at_utc",
        ),
        "v10 route card",
    )
    fail(value["schema"] != "math-research-route-card/v10", "route_card_invalid", "Route card schema is not v10.")
    require_id(value["route_id"], "route id")
    fail(value["status"] not in ("proposed", "active", "accepted", "rejected", "quarantined"), "route_card_invalid", "Route status is invalid.")
    _string(value["core_proof_object"], "core proof object")
    fail(value["proof_direction"] not in PROOF_DIRECTIONS, "route_card_invalid", "Proof direction is invalid.")
    _string(value["quantifier_strategy"], "quantifier strategy")
    require_id(value["mechanism_family_id"], "mechanism family id")
    ancestors = _string_array(value["ancestor_route_ids"], "ancestor route ids")
    for item in ancestors:
        require_id(item, "ancestor route id")
    require_exact(value["coverage_bridge"], ("status", "statement", "test"), "coverage bridge")
    fail(value["coverage_bridge"]["status"] not in ("none", "working", "verified"), "route_card_invalid", "Coverage bridge status is invalid.")
    if value["coverage_bridge"]["status"] == "none":
        fail(value["coverage_bridge"]["statement"] not in (None, "") or value["coverage_bridge"]["test"] not in (None, ""), "route_card_invalid", "A missing bridge cannot carry a statement or test.")
    else:
        _string(value["coverage_bridge"]["statement"], "coverage bridge statement")
        _string(value["coverage_bridge"]["test"], "coverage bridge test")
    _string(value["forbidden_family_relationship"], "forbidden family relationship")
    _string(value["non_renaming_reason"], "non-renaming reason")
    fail(type(value["special_family"]) is not bool, "route_card_invalid", "special_family must be Boolean.")
    if value["special_family"] and value["status"] in ("active", "accepted"):
        fail(value["coverage_bridge"]["status"] == "none", "coverage_bridge_missing", "An active special-family route needs a stated, testable coverage bridge.")
    require_timestamp(value["created_at_utc"], "route card created_at_utc")
    return value


def validate_route_portfolio(value: Any, *, reset_directive: dict[str, Any] | None = None) -> dict[str, Any]:
    require_exact(value, ("schema", "routes", "created_at_utc"), "route portfolio")
    fail(value["schema"] != "math-research-route-portfolio/v10", "route_portfolio_invalid", "Route portfolio schema is not v10.")
    fail(not isinstance(value["routes"], list) or not value["routes"], "route_portfolio_invalid", "Route portfolio must be nonempty.")
    cards = [validate_route_card(item) for item in value["routes"]]
    ids = [item["route_id"] for item in cards]
    fail(len(ids) != len(set(ids)), "route_portfolio_invalid", "Route portfolio contains duplicate route IDs.")
    require_timestamp(value["created_at_utc"], "route portfolio created_at_utc")
    if reset_directive is not None and reset_directive["required"]:
        fail(len(cards) < reset_directive["minimum_distinct_cards"], "route_portfolio_too_small", "Semantic reset route portfolio is too small.")
        forbidden = set(reset_directive["forbidden_mechanism_family_ids"])
        fail(any(card["mechanism_family_id"] in forbidden for card in cards), "surface_route_reset", "A reset route reuses a forbidden mechanism family.")
        fingerprints = {(card["core_proof_object"], card["quantifier_strategy"]) for card in cards}
        fail(len(fingerprints) < 2, "surface_route_reset", "Reset portfolio does not change proof object or quantifier strategy across cards.")
    return value


def validate_continuity_capsule(value: Any, root: Path) -> dict[str, Any]:
    require_exact(
        value,
        (
            "schema", "project_id", "run_id", "generation", "target_sha256", "proof_spine",
            "open_bottlenecks", "live_routes", "rejected_routes", "quarantined_routes",
            "forbidden_families", "synthesis_candidates", "required_full_artifacts",
            "route_reset_directive", "updated_at_utc",
        ),
        "continuity capsule",
    )
    fail(value["schema"] != "math-research-continuity-capsule/v1", "capsule_invalid", "Continuity capsule schema is invalid.")
    require_id(value["project_id"], "capsule project id")
    require_id(value["run_id"], "capsule run id")
    fail(type(value["generation"]) is not int or value["generation"] < 1, "capsule_invalid", "Capsule generation is invalid.")
    require_hash(value["target_sha256"], "capsule target hash")
    fail(not isinstance(value["proof_spine"], list), "capsule_invalid", "proof_spine must be an array.")
    claim_ids: set[str] = set()
    for claim in value["proof_spine"]:
        require_exact(claim, ("claim_id", "status", "statement", "dependencies", "artifact"), "proof-spine claim")
        cid = require_id(claim["claim_id"], "claim id")
        fail(cid in claim_ids, "capsule_invalid", "Duplicate claim id in proof spine.")
        claim_ids.add(cid)
        fail(claim["status"] not in CLAIM_STATUSES, "capsule_invalid", "Claim status is invalid.")
        _string(claim["statement"], "claim statement")
        deps = _string_array(claim["dependencies"], "claim dependencies")
        for dep in deps:
            require_id(dep, "claim dependency")
        if claim["artifact"] is not None:
            pointer(claim["artifact"], root, f"claim artifact {cid}")
        fail(claim["status"] in ("verified", "refuted") and claim["artifact"] is None, "capsule_invalid", "Verified or refuted claims need a full artifact pointer.")
    for claim in value["proof_spine"]:
        fail(any(dep not in claim_ids for dep in claim["dependencies"]), "capsule_invalid", "Claim dependency is absent from the proof spine.")
    _string_array(value["open_bottlenecks"], "open bottlenecks")
    for key in ("live_routes", "rejected_routes", "quarantined_routes", "forbidden_families"):
        ids = _string_array(value[key], key)
        for item in ids:
            require_id(item, key)
    route_registries = [set(value[key]) for key in ("live_routes", "rejected_routes", "quarantined_routes")]
    fail(any(route_registries[i] & route_registries[j] for i in range(3) for j in range(i + 1, 3)), "capsule_invalid", "Live, rejected, and quarantined route registries must be pairwise disjoint.")
    fail(not isinstance(value["synthesis_candidates"], list), "capsule_invalid", "synthesis_candidates must be an array.")
    for item in value["synthesis_candidates"]:
        require_exact(item, ("claim_ids", "bridge_question"), "synthesis candidate")
        ids = _string_array(item["claim_ids"], "synthesis claim ids", allow_empty=False)
        fail(any(cid not in claim_ids for cid in ids), "capsule_invalid", "Synthesis candidate names an absent claim.")
        _string(item["bridge_question"], "synthesis bridge question")
    fail(not isinstance(value["required_full_artifacts"], list), "capsule_invalid", "required_full_artifacts must be an array.")
    required_paths: set[str] = set()
    for item in value["required_full_artifacts"]:
        rel, _ = pointer(item, root, "required full artifact")
        fail(rel in required_paths, "capsule_invalid", "Duplicate required full artifact.")
        required_paths.add(rel)
    validate_route_reset_directive(value["route_reset_directive"])
    require_timestamp(value["updated_at_utc"], "capsule updated_at_utc")
    return value


def validate_reset_successor_capsule(
    old_capsule: dict[str, Any],
    successor_capsule: dict[str, Any],
    selected_route: dict[str, Any],
    reset_directive: dict[str, Any],
    generation: int,
    verified_paths: set[str] | None = None,
) -> None:
    fail(successor_capsule["generation"] != generation, "route_reset_sequence_invalid", "Successor capsule generation must equal the portfolio-acceptance generation.")
    fail(successor_capsule["target_sha256"] != old_capsule["target_sha256"], "ticket_scope_changed", "A semantic reset cannot change the frozen target.")
    fail(selected_route["status"] not in ("active", "accepted"), "route_reset_sequence_invalid", "The selected successor route must be active or accepted.")
    old_route_ids = set(old_capsule["live_routes"]) | set(old_capsule["rejected_routes"]) | set(old_capsule["quarantined_routes"])
    fail(selected_route["route_id"] in old_route_ids, "route_reset_sequence_invalid", "A semantic-reset successor must use a new route ID.")
    fail(selected_route["route_id"] not in successor_capsule["live_routes"], "route_reset_sequence_invalid", "Successor capsule does not list the selected route as live.")
    old_terminal = {
        claim["claim_id"]: claim
        for claim in old_capsule["proof_spine"]
        if claim["status"] in ("verified", "refuted")
    }
    successor_claims = {claim["claim_id"]: claim for claim in successor_capsule["proof_spine"]}
    fail(any(successor_claims.get(claim_id) != claim for claim_id, claim in old_terminal.items()), "terminal_claim_regression", "A reset successor cannot delete, downgrade, or rewrite a terminal claim.")
    verified_paths = verified_paths or set()
    for claim_id, claim in successor_claims.items():
        if claim["status"] not in ("verified", "refuted") or claim_id in old_terminal:
            continue
        fail(claim["artifact"] is None or claim["artifact"]["path"] not in verified_paths, "unverified_claim_promotion", "A reset successor cannot add a terminal claim without PASS-verifier-bound evidence.")
    old_required = {canonical_bytes(item) for item in old_capsule["required_full_artifacts"]}
    successor_required = {canonical_bytes(item) for item in successor_capsule["required_full_artifacts"]}
    fail(not old_required.issubset(successor_required), "ticket_full_context_missing", "A reset successor dropped a required full artifact.")
    successor_live = set(successor_capsule["live_routes"])
    retired = set(successor_capsule["rejected_routes"]) | set(successor_capsule["quarantined_routes"])
    stale_live = set(old_capsule["live_routes"])
    fail(bool(stale_live & successor_live) or not stale_live.issubset(retired), "route_reset_sequence_invalid", "Superseded live routes must leave live_routes and be rejected or quarantined.")
    fail(not set(reset_directive["forbidden_mechanism_family_ids"]).issubset(set(successor_capsule["forbidden_families"])), "surface_route_reset", "Successor capsule dropped a forbidden mechanism family.")
    successor_directive = successor_capsule["route_reset_directive"]
    fail(successor_directive != {"required": False, "trigger": "none", "forbidden_mechanism_family_ids": [], "minimum_distinct_cards": reset_directive["minimum_distinct_cards"], "same_family_ceiling": reset_directive["same_family_ceiling"]}, "route_reset_sequence_invalid", "Successor capsule must carry the canonical inactive reset directive.")


def validate_strategy_action(value: Any, root: Path) -> dict[str, Any]:
    require_exact(
        value,
        (
            "schema", "action", "bottleneck_progress", "surface_reset_risk", "missing_full_artifacts",
            "synthesis_map", "ranked_route_portfolio", "required_next_inputs", "new_math_performed",
            "created_at_utc",
        ),
        "strategy action",
    )
    fail(value["schema"] != "math-research-strategy-action/v1", "strategy_action_invalid", "Strategy action schema is invalid.")
    fail(value["action"] not in STRATEGY_ACTIONS, "strategy_action_invalid", "Strategy action is invalid.")
    _string(value["bottleneck_progress"], "bottleneck progress")
    fail(value["surface_reset_risk"] not in ("none", "possible", "confirmed"), "strategy_action_invalid", "surface_reset_risk is invalid.")
    fail(type(value["new_math_performed"]) is not bool, "strategy_action_invalid", "new_math_performed must be Boolean.")
    fail(value["new_math_performed"], "strategy_audit_new_math", "Strategy audit performed new mathematics; quarantine the lead and open a later solver attempt.")
    for key in ("missing_full_artifacts", "required_next_inputs"):
        fail(not isinstance(value[key], list), "strategy_action_invalid", f"{key} must be an array.")
        for item in value[key]:
            pointer(item, root, key)
    fail(not isinstance(value["synthesis_map"], list), "strategy_action_invalid", "synthesis_map must be an array.")
    for item in value["synthesis_map"]:
        require_exact(item, ("claim_ids", "reason"), "strategy synthesis item")
        _string_array(item["claim_ids"], "strategy synthesis claim ids", allow_empty=False)
        _string(item["reason"], "strategy synthesis reason")
    fail(not isinstance(value["ranked_route_portfolio"], list), "strategy_action_invalid", "ranked_route_portfolio must be an array.")
    for item in value["ranked_route_portfolio"]:
        require_exact(item, ("route_id", "rank", "reason"), "ranked route")
        require_id(item["route_id"], "ranked route id")
        fail(type(item["rank"]) is not int or item["rank"] < 1, "strategy_action_invalid", "Route rank must be positive.")
        _string(item["reason"], "ranked route reason")
    require_timestamp(value["created_at_utc"], "strategy action created_at_utc")
    return value


def assess_route_reset(value: Any) -> dict[str, Any]:
    require_exact(
        value,
        (
            "schema", "explicit_user_ban", "consecutive_same_family_negative_attempts",
            "consecutive_special_family_successes_without_bridge", "strategy_overlap_detected",
            "same_family_attempt_count", "same_family_ceiling",
        ),
        "route reset assessment input",
    )
    fail(value["schema"] != "math-research-route-reset-assessment-input/v1", "route_reset_invalid", "Assessment schema is invalid.")
    for key in ("explicit_user_ban", "strategy_overlap_detected"):
        fail(type(value[key]) is not bool, "route_reset_invalid", f"{key} must be Boolean.")
    for key in (
        "consecutive_same_family_negative_attempts",
        "consecutive_special_family_successes_without_bridge",
        "same_family_attempt_count",
        "same_family_ceiling",
    ):
        fail(type(value[key]) is not int or value[key] < 0, "route_reset_invalid", f"{key} must be a nonnegative integer.")
    fail(value["same_family_ceiling"] < 1, "route_reset_invalid", "same_family_ceiling must be positive.")
    triggers: list[str] = []
    if value["explicit_user_ban"]:
        triggers.append("explicit_user_ban")
    if value["consecutive_same_family_negative_attempts"] >= 2:
        triggers.append("same_family_negative_ceiling")
    if value["consecutive_special_family_successes_without_bridge"] >= 2:
        triggers.append("special_family_without_coverage_bridge")
    if value["strategy_overlap_detected"]:
        triggers.append("strategy_semantic_overlap")
    if value["same_family_attempt_count"] >= value["same_family_ceiling"]:
        triggers.append("same_family_ceiling")
    return {"reset_required": bool(triggers), "triggers": triggers, "minimum_distinct_cards": 2 if triggers else 0}


def validate_route_reset_state(value: Any, root: Path, control_generation: int) -> dict[str, Any] | None:
    if value is None:
        return None
    require_exact(
        value,
        (
            "status", "trigger_generation", "triggers", "portfolio_generation",
            "portfolio", "predecessor_attempt_id", "predecessor_lead_id", "selected_route",
            "successor_capsule", "successor_attempt_id",
        ),
        "route reset state",
    )
    fail(value["status"] not in ("triggered", "portfolio_accepted", "successor_started", "completed"), "route_reset_sequence_invalid", "Route reset lifecycle status is invalid.")
    fail(type(value["trigger_generation"]) is not int or value["trigger_generation"] < 1 or value["trigger_generation"] > control_generation, "route_reset_sequence_invalid", "Route reset trigger generation is invalid.")
    triggers = _string_array(value["triggers"], "route reset triggers")
    fail(not triggers or len(triggers) != len(set(triggers)) or any(item not in RESET_TRIGGERS or item == "none" for item in triggers), "route_reset_sequence_invalid", "Route reset triggers are empty, duplicated, or invalid.")
    require_id(value["predecessor_attempt_id"], "route reset predecessor attempt id")
    require_id(value["predecessor_lead_id"], "route reset predecessor lead id")
    if value["status"] == "triggered":
        fail(any(value[key] is not None for key in ("portfolio_generation", "portfolio", "selected_route", "successor_capsule", "successor_attempt_id")), "route_reset_sequence_invalid", "A trigger-only reset cannot already bind a portfolio or successor.")
        return value
    fail(type(value["portfolio_generation"]) is not int or value["portfolio_generation"] <= value["trigger_generation"] or value["portfolio_generation"] > control_generation, "route_reset_sequence_invalid", "Route portfolio acceptance must occur after the trigger.")
    _, portfolio_path = pointer(value["portfolio"], root, "route reset portfolio")
    portfolio = validate_route_portfolio(load_json(portfolio_path))
    _, route_path = pointer(value["selected_route"], root, "route reset selected route")
    selected = validate_route_card(load_json(route_path))
    matches = [card for card in portfolio["routes"] if card["route_id"] == selected["route_id"]]
    fail(len(matches) != 1 or matches[0] != selected, "route_reset_sequence_invalid", "Selected route is not the exact accepted portfolio card.")
    _, capsule_path = pointer(value["successor_capsule"], root, "route reset successor capsule")
    capsule = validate_continuity_capsule(load_json(capsule_path), root)
    fail(capsule["generation"] > control_generation, "route_reset_sequence_invalid", "Successor capsule generation is from the future.")
    fail(selected["route_id"] not in capsule["live_routes"], "route_reset_sequence_invalid", "Successor capsule does not bind the selected live route.")
    if value["status"] == "portfolio_accepted":
        fail(value["successor_attempt_id"] is not None, "route_reset_sequence_invalid", "An accepted portfolio cannot predeclare a successor attempt ID.")
    else:
        require_id(value["successor_attempt_id"], "route reset successor attempt id")
        fail(value["successor_attempt_id"] == value["predecessor_attempt_id"], "route_reset_sequence_invalid", "Route reset successor must have a distinct attempt ID.")
    return value


def validate_v10_ticket(ticket: Any, root: Path, *, expected_lifecycle: str | None = None) -> dict[str, Any]:
    keys = (
        "schema", "ticket_id", "role", "initial_lifecycle", "source_requirements",
        "input_artifacts", "allowed_reads", "writable_staging_path", "decision_question",
        "allowed_tools", "resource_caps", "required_outputs", "failure_return",
        "continuity_capsule", "route_card", "persistent_lead", "attempt_scope",
    )
    require_exact(ticket, keys, "v10 ticket")
    fail(ticket["schema"] != "math-research-ticket/v10", "ticket_invalid", "Ticket schema is not v10.")
    require_id(ticket["ticket_id"], "ticket_id")
    fail(ticket["role"] not in ("attempt", "audit"), "ticket_invalid", "Ticket role must be attempt or audit.")
    fail(ticket["initial_lifecycle"] != "planned", "ticket_invalid", "A frozen v10 ticket must start at planned.")
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
    capsule_rel, capsule_path = pointer(ticket["continuity_capsule"], root, "ticket continuity capsule")
    capsule = validate_continuity_capsule(load_json(capsule_path), root)
    route_rel, route_path = pointer(ticket["route_card"], root, "ticket route card")
    route = validate_route_card(load_json(route_path))
    fail(capsule_rel not in artifact_paths or route_rel not in artifact_paths, "ticket_input_incomplete", "Ticket must bind its capsule and route card as input artifacts.")
    artifact_roles = {item["path"]: item["role"] for item in artifacts}
    fail(artifact_roles[capsule_rel] != "continuity_capsule" or artifact_roles[route_rel] != "route_card", "ticket_input_incomplete", "Capsule and route-card input roles are invalid.")
    required_full = {item["path"] for item in capsule["required_full_artifacts"]}
    missing_full = required_full - set(artifact_paths)
    fail(bool(missing_full), "ticket_full_context_missing", f"Ticket omitted capsule-required full artifacts: {sorted(missing_full)}")
    require_exact(ticket["persistent_lead"], ("lead_id", "mode", "previous_ticket_id"), "persistent lead")
    require_id(ticket["persistent_lead"]["lead_id"], "lead id")
    fail(ticket["persistent_lead"]["mode"] not in ("new", "resume"), "ticket_invalid", "Persistent lead mode is invalid.")
    if ticket["persistent_lead"]["mode"] == "new":
        fail(ticket["persistent_lead"]["previous_ticket_id"] is not None, "ticket_invalid", "A new lead cannot name a previous ticket.")
    else:
        require_id(ticket["persistent_lead"]["previous_ticket_id"], "previous ticket id")
    require_exact(
        ticket["attempt_scope"],
        (
            "attempt_kind", "target_sha256", "route_family_id", "proof_object",
            "quantifier_strategy", "evidence_standard", "resource_envelope_sha256",
        ),
        "attempt scope",
    )
    fail(ticket["attempt_scope"]["attempt_kind"] not in ("route_discovery", "route_execution", "candidate_revision", "candidate_synthesis"), "ticket_invalid", "Attempt kind is invalid.")
    for key in ("target_sha256", "resource_envelope_sha256"):
        require_hash(ticket["attempt_scope"][key], f"attempt scope {key}")
    require_id(ticket["attempt_scope"]["route_family_id"], "route family id")
    _string(ticket["attempt_scope"]["proof_object"], "attempt proof object")
    _string(ticket["attempt_scope"]["quantifier_strategy"], "attempt quantifier strategy")
    _string(ticket["attempt_scope"]["evidence_standard"], "attempt evidence standard")
    fail(ticket["attempt_scope"]["target_sha256"] != capsule["target_sha256"], "ticket_scope_changed", "Ticket target differs from the continuity capsule.")
    fail(ticket["attempt_scope"]["route_family_id"] != route["mechanism_family_id"], "ticket_scope_changed", "Ticket route family differs from the route card.")
    fail(ticket["attempt_scope"]["proof_object"] != route["core_proof_object"] or ticket["attempt_scope"]["quantifier_strategy"] != route["quantifier_strategy"], "ticket_scope_changed", "Ticket proof object or quantifier strategy differs from the route card.")
    reset = capsule["route_reset_directive"]
    if reset["required"]:
        fail(ticket["attempt_scope"]["attempt_kind"] != "route_discovery", "semantic_reset_required", "A required semantic reset permits only route discovery.")
        fail(route["mechanism_family_id"] in reset["forbidden_mechanism_family_ids"] and route["status"] not in ("rejected", "quarantined"), "surface_route_reset", "Active ticket reuses a forbidden mechanism family.")
        fail("route_portfolio" not in ticket["required_outputs"], "semantic_reset_required", "Reset discovery must require a route_portfolio output.")
    return ticket


def _validate_topology_descriptor_binding(value: Any, root: Path, roles: set[str], label: str) -> None:
    require_exact(value, ("descriptor", "sha256"), label)
    descriptor = value["descriptor"]
    require_exact(descriptor, ("schema", "role", "transport", "execution_workspace_root", "runner", "sandbox_mode", "runner_arguments"), f"{label} descriptor")
    fail(descriptor["schema"] != "math-research-execution-topology-descriptor/v1" or descriptor["role"] not in roles, "topology_receipt_invalid", f"{label} schema or role is invalid.")
    fail(not isinstance(descriptor["runner_arguments"], list) or any(not isinstance(item, str) for item in descriptor["runner_arguments"]), "topology_receipt_invalid", f"{label} runner_arguments must be an array of strings.")
    fail(Path(os.path.realpath(descriptor["execution_workspace_root"])) != Path(os.path.realpath(root)), "execution_workspace_mismatch", f"{label} execution workspace is not the project root.")
    expected = require_hash(value["sha256"], f"{label} hash")
    fail(sha_bytes(canonical_bytes(descriptor)) != expected, "topology_receipt_invalid", f"{label} descriptor hash mismatch.")


def validate_execution_topology_receipt(receipt: Any, root: Path, state: dict[str, Any], ticket: dict[str, Any], ticket_pointer: dict[str, str], receipt_rel: str) -> dict[str, Any]:
    require_exact(
        receipt,
        (
            "schema", "status", "receipt_id", "project_id", "run_id", "control_generation",
            "project_head", "ticket", "inputs", "staging_root", "worker_observation",
            "readback_observation", "consumer_principal", "consumer_observation", "issued_at_utc", "expires_at_utc",
        ),
        "execution topology receipt",
    )
    fail(receipt["schema"] != "math-research-execution-topology-receipt/v1" or receipt["status"] != "ready_for_attempt_start", "topology_receipt_invalid", "ATTEMPT_START requires a ready execution-topology receipt.")
    require_id(receipt["receipt_id"], "topology receipt id")
    fail(receipt["project_id"] != state["project_id"] or receipt["run_id"] != state["active_run"]["id"], "topology_receipt_mismatch", "Topology receipt project or run differs from active state.")
    fail(type(receipt["control_generation"]) is not int or receipt["control_generation"] != state["control_generation"], "topology_receipt_stale", "Topology receipt does not bind the current control generation.")
    require_exact(receipt["project_head"], ("path", "sha256"), "topology receipt project head")
    fail(receipt["project_head"]["path"] != "project.json" or receipt["project_head"]["sha256"] != sha_file(root / "project.json"), "topology_receipt_stale", "Topology receipt project-head binding is stale.")
    require_exact(receipt["ticket"], ("path", "sha256", "ticket_id"), "topology receipt ticket")
    fail(receipt["ticket"] != {**ticket_pointer, "ticket_id": ticket["ticket_id"]}, "topology_receipt_mismatch", "Topology receipt ticket binding differs from ATTEMPT_START.")
    expected_inputs = [{"path": item["path"], "sha256": item["sha256"]} for item in ticket["input_artifacts"]]
    fail(receipt["inputs"] != expected_inputs, "topology_receipt_mismatch", "Topology receipt input closure differs from the ticket.")
    staging = safe_relative(receipt["staging_root"], "topology receipt staging root")
    fail(staging != ticket["writable_staging_path"] or not receipt_rel.startswith(staging.rstrip("/") + "/"), "worker_staging_escape", "Topology receipt is not inside the ticket staging root.")
    require_timestamp(receipt["issued_at_utc"], "topology receipt issued_at_utc")
    require_timestamp(receipt["expires_at_utc"], "topology receipt expires_at_utc")
    fail(parse_utc(receipt["issued_at_utc"]) >= parse_utc(receipt["expires_at_utc"]), "topology_receipt_invalid", "Topology receipt expiry is not after issuance.")
    fail(parse_utc(receipt["expires_at_utc"]) <= dt.datetime.now(dt.timezone.utc), "topology_receipt_stale", "Topology receipt expired before ATTEMPT_START preparation.")
    worker = receipt["worker_observation"]
    require_exact(worker, ("topology", "probe_relative_path", "probe_sha256", "nonce_sha256", "worker_receipt_sha256"), "worker topology observation")
    _validate_topology_descriptor_binding(worker["topology"], root, {"worker"}, "worker topology")
    probe_rel = safe_relative(worker["probe_relative_path"], "topology probe path")
    fail(not probe_rel.startswith(staging.rstrip("/") + "/"), "worker_staging_escape", "Topology probe escaped ticket staging.")
    for key in ("probe_sha256", "nonce_sha256", "worker_receipt_sha256"):
        require_hash(worker[key], f"worker observation {key}")
    readback = receipt["readback_observation"]
    require_exact(readback, ("topology", "independent_reopen", "project_head_sha256", "ticket_sha256", "probe_sha256", "checked_at_utc"), "readback topology observation")
    _validate_topology_descriptor_binding(readback["topology"], root, {"ingest", "publisher"}, "readback topology")
    fail(readback["independent_reopen"] is not True, "host_or_ingest_readback_unavailable", "Topology receipt lacks an independent publisher reopen.")
    fail(readback["project_head_sha256"] != receipt["project_head"]["sha256"] or readback["ticket_sha256"] != ticket_pointer["sha256"] or readback["probe_sha256"] != worker["probe_sha256"], "topology_receipt_mismatch", "Readback observation differs from worker bindings.")
    require_timestamp(readback["checked_at_utc"], "readback checked_at_utc")
    fail(not isinstance(receipt["consumer_principal"], str) or not receipt["consumer_principal"], "consumer_principal_mismatch", "Topology receipt lacks the frozen long-lived consumer principal.")
    consumer = receipt["consumer_observation"]
    require_exact(consumer, ("topology", "principal", "independent_recursive_reopen", "project_tree_sha256", "directory_count", "file_count", "publisher_probe_relative_path", "publisher_probe_sha256", "checked_at_utc"), "consumer topology observation")
    _validate_topology_descriptor_binding(consumer["topology"], root, {"consumer"}, "consumer topology")
    principal_equal = consumer["principal"].casefold() == receipt["consumer_principal"].casefold() if os.name == "nt" and isinstance(consumer["principal"], str) else consumer["principal"] == receipt["consumer_principal"]
    fail(not principal_equal, "consumer_principal_mismatch", "Consumer observation came from a different OS principal.")
    fail(consumer["independent_recursive_reopen"] is not True, "consumer_readback_unavailable", "Topology receipt lacks an independent recursive consumer reopen.")
    require_hash(consumer["project_tree_sha256"], "consumer project tree hash")
    require_hash(consumer["publisher_probe_sha256"], "consumer publisher probe hash")
    fail(type(consumer["directory_count"]) is not int or consumer["directory_count"] < 1 or type(consumer["file_count"]) is not int or consumer["file_count"] < 1, "consumer_readback_unavailable", "Consumer observation has invalid project traversal counts.")
    safe_relative(consumer["publisher_probe_relative_path"], "consumer publisher probe path")
    require_timestamp(consumer["checked_at_utc"], "consumer checked_at_utc")
    return receipt


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


def preflight_v10(project: Path, ticket_path: Path, access_log: Path | None) -> dict[str, Any]:
    ticket = load_json(ticket_path)
    validate_v10_ticket(ticket, project)
    input_paths = {safe_relative(item["path"], "ticket input path") for item in ticket["input_artifacts"]}
    allowed_reads = {safe_relative(item, "allowed read") for item in ticket["allowed_reads"]}
    fail(input_paths != allowed_reads, "ticket_read_closure_failed", "v10 allowed_reads must exactly equal bound input artifacts.")
    asset_like = {rel for rel in input_paths if Path(rel).suffix.casefold() in _asset_tools().ASSET_SUFFIXES}
    if asset_like:
        head = load_json(project / "project.json")
        _, state_path = pointer(head["state"], project, "asset-aware ticket state")
        live_state = load_json(state_path)
        fail(live_state.get("asset_index") is None, "asset_index_required", "A ticket containing research assets requires a current asset index.")
        try:
            loaded_assets = _asset_tools().load_index(project, resolve_under(project, live_state["asset_index"]["path"], "asset index"))
        except Exception as exc:
            raise ResearchError(getattr(exc, "code", "asset_index_invalid"), getattr(exc, "message", str(exc))) from exc
        fail(bool(asset_like - loaded_assets["registered_paths"]), "unregistered_dependency", f"Ticket uses unregistered research assets: {sorted(asset_like - loaded_assets['registered_paths'])[:5]}")
    input_reads: list[str] = []
    staging_reads: list[str] = []
    if access_log is not None:
        log = load_json(access_log)
        require_exact(log, ("schema", "input_reads", "staging_reads"), "worker access log v2")
        fail(log["schema"] != "math-research-worker-access-log/v2", "worker_access_invalid", "Worker access log schema is not v2.")
        fail(not isinstance(log["input_reads"], list) or not isinstance(log["staging_reads"], list), "worker_access_invalid", "Worker access arrays are invalid.")
        input_reads = [safe_relative(item, "worker input read") for item in log["input_reads"]]
        fail(bool(set(input_reads) - input_paths), "worker_access_out_of_scope", "Worker reported an unbound input read; discard the return.")
        staging_root = safe_relative(ticket["writable_staging_path"], "ticket writable staging path").rstrip("/")
        staging_reads = [safe_relative(item, "worker staging read") for item in log["staging_reads"]]
        fail(
            any(item != staging_root and not item.startswith(staging_root + "/") for item in staging_reads),
            "worker_staging_escape",
            "Worker reported a staging read outside its ticket staging root; discard the return.",
        )
    return {
        "classification": "ticket_ready",
        "ticket_id": ticket["ticket_id"],
        "input_count": len(input_paths),
        "required_full_artifact_count": len(load_json(resolve_under(project, ticket["continuity_capsule"]["path"], "ticket capsule"))["required_full_artifacts"]),
        "access_log_checked": access_log is not None,
        "input_read_count": len(input_reads),
        "staging_read_count": len(staging_reads),
        "persistent_lead": ticket["persistent_lead"],
        "worker_capsule": {
            "preferred_resume_same_lead": True,
            "required_fork_turns_for_new_specialist": "none",
            "context_inputs": [ticket_path.resolve().as_posix()] + [resolve_under(project, rel, "capsule input").as_posix() for rel in sorted(input_paths)],
            "isolation_level": "protocol_only_shared_filesystem",
        },
    }


def validate_manifest(root: Path, manifest: Any) -> dict[str, Any]:
    require_exact(manifest, ("schema", "project_id", "control_generation", "entries", "created_at_utc"), "archive manifest")
    fail(manifest["schema"] != "math-research-archive-manifest/v10", "manifest_invalid", "Manifest schema is invalid.")
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
    legacy_keys = {"schema", "project_id", "control_generation", "active_run", "current_attempt", "current_ticket", "continuity_capsule", "active_route_card", "strategy_action", "counters", "evidence_items", "typed_references", "updated_at_utc"}
    optional = {"route_reset", "asset_index", "migration"}
    fail(not isinstance(state, dict) or not legacy_keys.issubset(state) or bool(set(state) - legacy_keys - optional), "schema_keys", "v10 state has missing or unexpected keys.")
    fail(state["schema"] != "math-research-state/v10", "state_invalid", "State schema is invalid.")
    require_id(state["project_id"], "state project_id")
    fail(type(state["control_generation"]) is not int or state["control_generation"] < 1, "state_invalid", "State generation is invalid.")
    require_timestamp(state["updated_at_utc"], "state updated_at_utc")
    if state.get("asset_index") is not None:
        validate_asset_index_pointer(state["asset_index"], root, state["project_id"])
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
        fail(pred["final_status"] not in ("closed", "superseded", "budget_exhausted", "route_exhausted", "superseded_by_v10_migration"), "state_invalid", "Predecessor final status is invalid.")
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
        require_exact(attempt, ("id", "ticket_id", "started_generation", "kind", "solver_result", "verifier_completion", "disposition", "lead_id", "scope_fingerprint", "checkpoint_count"), "current_attempt")
        require_id(attempt["id"], "attempt id")
        require_id(attempt["ticket_id"], "attempt ticket id")
        fail(type(attempt["started_generation"]) is not int or attempt["started_generation"] < 1, "state_invalid", "Attempt generation is invalid.")
        fail(attempt["kind"] not in ("route_discovery", "route_execution", "candidate_revision", "candidate_synthesis"), "state_invalid", "Attempt kind is invalid.")
        require_id(attempt["lead_id"], "attempt lead id")
        require_hash(attempt["scope_fingerprint"], "attempt scope fingerprint")
        fail(type(attempt["checkpoint_count"]) is not int or attempt["checkpoint_count"] < 0, "state_invalid", "Attempt checkpoint count is invalid.")
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
        validate_v10_ticket(ticket, root, expected_lifecycle=ticket_state["lifecycle"])
        fail(ticket["ticket_id"] != ticket_state["id"], "state_invalid", "Current ticket ID differs from frozen ticket.")
        if attempt is not None:
            fail(attempt["ticket_id"] != ticket_state["id"], "state_invalid", "Attempt and ticket IDs differ.")
    capsule_rel, capsule_path = pointer(state["continuity_capsule"], root, "state continuity capsule")
    capsule = validate_continuity_capsule(load_json(capsule_path), root)
    fail(capsule["project_id"] != state["project_id"] or capsule["run_id"] != run["id"], "state_invalid", "Continuity capsule identity differs from state.")
    fail(capsule["generation"] > state["control_generation"], "state_invalid", "Continuity capsule generation is from the future.")
    route_rel, route_path = pointer(state["active_route_card"], root, "state active route card")
    route = validate_route_card(load_json(route_path))
    fail(route["route_id"] not in capsule["live_routes"] and route["route_id"] not in capsule["rejected_routes"] and route["route_id"] not in capsule["quarantined_routes"], "state_invalid", "Active route card is absent from capsule route registries.")
    if state["strategy_action"] is not None:
        _, action_path = pointer(state["strategy_action"], root, "state strategy action")
        validate_strategy_action(load_json(action_path), root)
    validate_route_reset_state(state.get("route_reset"), root, state["control_generation"])
    if state.get("migration") is not None:
        fail(run["predecessor"] is None or run["predecessor"]["final_status"] != "superseded_by_v10_migration", "migration_invalid", "A migrated state requires the v8 migration predecessor status.")
        validate_incremental_migration(state["migration"], root, state)
    else:
        fail(run["predecessor"] is not None and run["predecessor"]["final_status"] == "superseded_by_v10_migration", "migration_invalid", "The v8 migration predecessor status requires a migration record.")
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


def load_v10_project(root: Path, audit_mode: str = "Auto", allowed_unmanifested: set[str] | None = None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str, list[str]]:
    project_path = root / "project.json"
    fail(not project_path.is_file(), "project_missing", "project.json is absent.")
    head_hash = sha_file(project_path)
    head = load_json(project_path)
    require_exact(head, ("schema", "project_id", "control_generation", "state", "event_tail", "archive_manifest", "last_full_audit_generation", "last_full_audit_at_utc"), "project head")
    fail(head["schema"] != "math-research-project/v10", "not_v10", "Project is not v10.")
    require_id(head["project_id"], "project_id")
    fail(type(head["control_generation"]) is not int or head["control_generation"] < 1, "project_invalid", "Head generation is invalid.")
    fail(type(head["last_full_audit_generation"]) is not int or head["last_full_audit_generation"] < 0, "project_invalid", "Full-audit generation is invalid.")
    require_timestamp(head["last_full_audit_at_utc"], "last_full_audit_at_utc")
    _, state_path = pointer(head["state"], root, "head state")
    _, event_path = pointer(head["event_tail"], root, "head event")
    manifest_rel, manifest_path = pointer(head["archive_manifest"], root, "head manifest")
    state = validate_state(root, load_json(state_path))
    if state.get("migration") is not None:
        fail(root.resolve().name != state["migration"]["successor_directory_name"], "migration_path_invalid", "Live v10 directory name differs from the migration binding.")
    manifest = validate_manifest(root, load_json(manifest_path))
    fail(state["project_id"] != head["project_id"] or manifest["project_id"] != head["project_id"], "project_invalid", "Project identity differs across head/state/manifest.")
    fail(state["control_generation"] != head["control_generation"] or manifest["control_generation"] != head["control_generation"], "project_invalid", "Generation differs across head/state/manifest.")
    event = load_json(event_path)
    require_exact(event, ("schema", "project_id", "control_generation", "event_type", "previous_event", "payload_sha256", "occurred_at_utc"), "event tail")
    fail(event["schema"] != "math-research-event/v10" or event["project_id"] != head["project_id"] or event["control_generation"] != head["control_generation"], "event_invalid", "Event tail binding is invalid.")
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
    current_paths.add(state["continuity_capsule"]["path"])
    current_paths.add(state["active_route_card"]["path"])
    if state["strategy_action"] is not None:
        current_paths.add(state["strategy_action"]["path"])
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
    result.append(state["continuity_capsule"])
    result.append(state["active_route_card"])
    if state["strategy_action"] is not None:
        result.append(state["strategy_action"])
    if state.get("asset_index") is not None:
        result.append(state["asset_index"])
    if state.get("migration") is not None:
        result.extend(state["migration"][key] for key in ("manifest", "freeze_record", "envelope_snapshot", "lineage"))
    route_reset = state.get("route_reset")
    if route_reset is not None and route_reset["status"] != "triggered":
        result.extend([route_reset["portfolio"], route_reset["selected_route"], route_reset["successor_capsule"]])
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
    new.setdefault("route_reset", None)
    attempt = new["current_attempt"]
    ticket_state = new["current_ticket"]
    pending_reset = new["route_reset"]
    if pending_reset is not None and pending_reset["status"] == "portfolio_accepted":
        required_next = "ATTEMPT_END" if attempt is not None else "ATTEMPT_START"
        fail(kind != required_next, "route_reset_sequence_invalid", "An accepted route portfolio must proceed directly to its unique successor attempt.")
    if kind == "ASSET_REGISTRY_UPDATE":
        require_exact(payload, ("schema", "asset_index", "occurred_at_utc"), "ASSET_REGISTRY_UPDATE payload")
        fail(payload["schema"] != "math-research-transition-payload/v10", "transition_invalid", "Payload schema is invalid.")
        require_timestamp(payload["occurred_at_utc"], "ASSET_REGISTRY_UPDATE occurred_at_utc")
        fail(new["active_run"]["status"] in ("superseded", "closed"), "transition_invalid", "A terminal run cannot update its asset registry.")
        validate_asset_index_pointer(payload["asset_index"], root, new["project_id"])
        new["asset_index"] = copy.deepcopy(payload["asset_index"])
    elif kind == "ATTEMPT_START":
        start_required = {"schema", "attempt_id", "attempt_kind", "ticket", "occurred_at_utc"}
        fail(not isinstance(payload, dict) or not start_required.issubset(payload) or set(payload) - start_required - {"execution_topology_receipt"}, "schema_invalid", "ATTEMPT_START payload keys are invalid.")
        fail(payload["schema"] != "math-research-transition-payload/v10", "transition_invalid", "Payload schema is invalid.")
        require_timestamp(payload["occurred_at_utc"], "ATTEMPT_START occurred_at_utc")
        fail(attempt is not None or ticket_state is None or ticket_state["lifecycle"] != "planned" or new["active_run"]["status"] != "preparing", "transition_invalid", "ATTEMPT_START requires a preparing run and planned ticket with no attempt.")
        rel, ticket_path = pointer(payload["ticket"], root, "ATTEMPT_START ticket")
        ticket = validate_v10_ticket(load_json(ticket_path), root)
        fail(ticket["ticket_id"] != ticket_state["id"] or rel != ticket_state["path"] or payload["ticket"]["sha256"] != ticket_state["sha256"], "transition_invalid", "ATTEMPT_START ticket differs from the planned current ticket.")
        aid = require_id(payload["attempt_id"], "attempt_id")
        fail(payload["attempt_kind"] not in ("route_discovery", "route_execution", "candidate_revision", "candidate_synthesis"), "transition_invalid", "Attempt kind is invalid.")
        fail(payload["attempt_kind"] != ticket["attempt_scope"]["attempt_kind"], "transition_invalid", "ATTEMPT_START kind differs from the frozen ticket scope.")
        validate_migration_predecessor_freeze(root, new)
        local = new["counters"]["run_local"]
        cumulative = new["counters"]["cumulative"]
        budgets = new["active_run"]["budgets"]
        fail(local["attempt_count"] + 1 > budgets["attempt_budget"] or local["total_round_count"] + 2 > budgets["total_round_budget"], "budget_exhausted", "ATTEMPT_START would consume the reserved terminal-audit round.")
        fail("execution_topology_receipt" not in payload, "topology_receipt_required", "ATTEMPT_START requires a current round-trip execution-topology receipt before counters change.")
        receipt_rel, receipt_path = pointer(payload["execution_topology_receipt"], root, "ATTEMPT_START execution topology receipt")
        validate_execution_topology_receipt(load_json(receipt_path), root, new, ticket, payload["ticket"], receipt_rel)
        for target in (local, cumulative):
            target["attempt_count"] += 1
            target["total_round_count"] += 1
            target["attempts_since_last_audit"] += 1
        scope_fingerprint = sha_bytes(canonical_bytes(ticket["attempt_scope"]))
        route_reset = new["route_reset"]
        if route_reset is not None and route_reset["status"] == "portfolio_accepted":
            fail(aid == route_reset["predecessor_attempt_id"], "route_reset_sequence_invalid", "Route reset successor must use a distinct attempt ID.")
            fail(ticket["route_card"] != route_reset["selected_route"] or ticket["continuity_capsule"] != route_reset["successor_capsule"], "route_reset_sequence_invalid", "Successor ticket is not bound to the accepted route and capsule.")
            successor_lead = ticket["persistent_lead"]
            fail(successor_lead["lead_id"] == route_reset["predecessor_lead_id"] or successor_lead["mode"] != "new" or successor_lead["previous_ticket_id"] is not None, "partial_reset_identity", "A semantic-reset successor must replace the predecessor lead with one fresh lead in new mode.")
            route_reset["status"] = "successor_started"
            route_reset["successor_attempt_id"] = aid
            new["active_route_card"] = copy.deepcopy(route_reset["selected_route"])
            new["continuity_capsule"] = copy.deepcopy(route_reset["successor_capsule"])
        elif route_reset is not None and route_reset["status"] in ("triggered", "successor_started"):
            fail(True, "route_reset_sequence_invalid", "A reset cannot start before portfolio acceptance or start a second successor.")
        new["current_attempt"] = {"id": aid, "ticket_id": ticket_state["id"], "started_generation": generation, "kind": payload["attempt_kind"], "solver_result": None, "verifier_completion": None, "disposition": None, "lead_id": ticket["persistent_lead"]["lead_id"], "scope_fingerprint": scope_fingerprint, "checkpoint_count": 0}
        new["typed_references"].append({"kind": "execution_topology_receipt", "path": receipt_rel, "sha256": payload["execution_topology_receipt"]["sha256"], "attempt_id": aid, "ticket_id": ticket_state["id"]})
        new["current_ticket"]["lifecycle"] = "active"
        new["active_run"]["status"] = "attempt_running"
    elif kind == "ROUTE_RESET_TRIGGER":
        require_exact(payload, ("schema", "assessment", "occurred_at_utc"), "ROUTE_RESET_TRIGGER payload")
        fail(payload["schema"] != "math-research-transition-payload/v10", "transition_invalid", "Payload schema is invalid.")
        require_timestamp(payload["occurred_at_utc"], "ROUTE_RESET_TRIGGER occurred_at_utc")
        fail(attempt is None or ticket_state is None or ticket_state["lifecycle"] != "active", "route_reset_sequence_invalid", "A route reset trigger requires an active attempt.")
        existing = new["route_reset"]
        fail(existing is not None and existing["status"] != "completed", "route_reset_sequence_invalid", "The current reset lifecycle already has an earliest trigger.")
        assessment = assess_route_reset(payload["assessment"])
        fail(not assessment["reset_required"], "route_reset_sequence_invalid", "The supplied assessment does not trigger a reset.")
        active_capsule = validate_continuity_capsule(load_json(resolve_under(root, new["continuity_capsule"]["path"], "active reset capsule")), root)
        directive = active_capsule["route_reset_directive"]
        fail(not directive["required"] or directive["trigger"] not in assessment["triggers"], "route_reset_sequence_invalid", "The trigger assessment is not bound to the active reset directive.")
        if "explicit_user_ban" in assessment["triggers"]:
            fail(not directive["forbidden_mechanism_family_ids"], "route_reset_sequence_invalid", "An explicit method ban must identify at least one forbidden mechanism family.")
        new["route_reset"] = {
            "status": "triggered",
            "trigger_generation": generation,
            "triggers": assessment["triggers"],
            "portfolio_generation": None,
            "portfolio": None,
            "predecessor_attempt_id": attempt["id"],
            "predecessor_lead_id": attempt["lead_id"],
            "selected_route": None,
            "successor_capsule": None,
            "successor_attempt_id": None,
        }
    elif kind == "ROUTE_PORTFOLIO_ACCEPT":
        require_exact(payload, ("schema", "portfolio", "selected_route", "successor_capsule", "occurred_at_utc"), "ROUTE_PORTFOLIO_ACCEPT payload")
        fail(payload["schema"] != "math-research-transition-payload/v10", "transition_invalid", "Payload schema is invalid.")
        require_timestamp(payload["occurred_at_utc"], "ROUTE_PORTFOLIO_ACCEPT occurred_at_utc")
        reset = new["route_reset"]
        fail(attempt is None or ticket_state is None or ticket_state["lifecycle"] != "active" or reset is None or reset["status"] != "triggered" or reset["predecessor_attempt_id"] != attempt["id"], "route_reset_sequence_invalid", "Portfolio acceptance requires the triggered predecessor attempt.")
        old_capsule = validate_continuity_capsule(load_json(resolve_under(root, new["continuity_capsule"]["path"], "active reset capsule")), root)
        directive = old_capsule["route_reset_directive"]
        fail(not directive["required"], "route_reset_sequence_invalid", "Portfolio acceptance requires an active reset directive in the capsule.")
        _, portfolio_path = pointer(payload["portfolio"], root, "accepted route portfolio")
        portfolio = validate_route_portfolio(load_json(portfolio_path), reset_directive=directive)
        _, route_path = pointer(payload["selected_route"], root, "selected reset route")
        selected = validate_route_card(load_json(route_path))
        matches = [card for card in portfolio["routes"] if card["route_id"] == selected["route_id"]]
        fail(len(matches) != 1 or matches[0] != selected, "route_reset_sequence_invalid", "Selected route is not the exact accepted portfolio card.")
        _, capsule_path = pointer(payload["successor_capsule"], root, "route reset successor capsule")
        successor_capsule = validate_continuity_capsule(load_json(capsule_path), root)
        fail(successor_capsule["project_id"] != new["project_id"] or successor_capsule["run_id"] != new["active_run"]["id"] or selected["route_id"] not in successor_capsule["live_routes"], "route_reset_sequence_invalid", "Successor capsule does not bind the selected route and active run.")
        verified_paths = {item["path"] for item in new["evidence_items"] if item["kind"] in ("candidate", "verified_partial", "failure_boundary")}
        validate_reset_successor_capsule(old_capsule, successor_capsule, selected, directive, generation, verified_paths)
        reset.update({
            "status": "portfolio_accepted",
            "portfolio_generation": generation,
            "portfolio": copy.deepcopy(payload["portfolio"]),
            "selected_route": copy.deepcopy(payload["selected_route"]),
            "successor_capsule": copy.deepcopy(payload["successor_capsule"]),
        })
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
        fail(completion["schema"] != "math-research-verifier-completion/v10" or completion["project_id"] != new["project_id"] or completion["run_id"] != new["active_run"]["id"] or completion["attempt_id"] != attempt["id"] or completion["ticket_id"] != ticket_state["id"], "transition_invalid", "Verifier completion identity binding failed.")
        fail(completion["verdict"] not in ("PASS", "FAIL", "INCONCLUSIVE"), "transition_invalid", "Verifier verdict is invalid.")
        require_timestamp(completion["completed_at_utc"], "verifier completion time")
        if completion["candidate"] is not None:
            pointer(completion["candidate"], root, "verified candidate")
        evidence = validate_evidence(payload["evidence_items"], root, "verifier evidence")
        for item in evidence:
            fail(item["attempt_id"] != attempt["id"] or item["ticket_id"] != ticket_state["id"], "evidence_invalid", "Evidence is not bound to the current attempt and ticket.")
        fail(bool(evidence) and completion["verdict"] != "PASS", "verification_required", "Mathematical evidence can be published only by a PASS verifier completion.")
        candidate_evidence = [item for item in evidence if item["kind"] == "candidate"]
        if completion["candidate"] is None:
            fail(bool(candidate_evidence), "transition_invalid", "Candidate evidence is not bound to the verifier completion candidate.")
        else:
            fail(len(candidate_evidence) != 1 or {"path": candidate_evidence[0]["path"], "sha256": candidate_evidence[0]["sha256"]} != completion["candidate"], "transition_invalid", "Verifier completion candidate differs from candidate evidence.")
        new["current_attempt"]["verifier_completion"] = payload["verifier_completion"]
        new["current_ticket"]["lifecycle"] = "verifier_completed"
        new["evidence_items"].extend(copy.deepcopy(evidence))
    elif kind == "ATTEMPT_END":
        require_exact(payload, ("schema", "disposition", "attempt_record", "evidence_items", "next_ticket", "occurred_at_utc"), "ATTEMPT_END payload")
        require_timestamp(payload["occurred_at_utc"], "ATTEMPT_END occurred_at_utc")
        disposition = payload["disposition"]
        fail(disposition not in DISPOSITIONS, "transition_invalid", "Attempt disposition is invalid.")
        fail(attempt is None or ticket_state is None or ticket_state["lifecycle"] not in ("active", "solver_completed", "verifier_completed"), "transition_invalid", "ATTEMPT_END requires a running attempt.")
        _, record_path = pointer(payload["attempt_record"], root, "attempt record")
        record = load_json(record_path)
        require_exact(record, ("schema", "project_id", "run_id", "attempt_id", "ticket_id", "disposition", "evidence", "verifier_completion", "completed_at_utc"), "attempt record")
        fail(record["schema"] != "math-research-attempt-record/v10" or record["project_id"] != new["project_id"] or record["run_id"] != new["active_run"]["id"] or record["attempt_id"] != attempt["id"] or record["ticket_id"] != ticket_state["id"] or record["disposition"] != disposition, "transition_invalid", "Attempt record identity/outcome binding failed.")
        validate_evidence(record["evidence"], root, "attempt record evidence")
        evidence = validate_evidence(payload["evidence_items"], root, "ATTEMPT_END evidence")
        fail(record["evidence"] != evidence, "transition_invalid", "Attempt record evidence differs from ATTEMPT_END evidence.")
        kinds = {item["kind"] for item in evidence}
        promoted = disposition in ("candidate", "no_candidate_with_evidence") or bool(kinds & {"candidate", "verified_partial", "failure_boundary"})
        if promoted:
            fail(ticket_state["lifecycle"] != "verifier_completed" or attempt["verifier_completion"] is None, "verification_required", "Promoted mathematical evidence requires an independent verifier.")
            completion = load_json(resolve_under(root, attempt["verifier_completion"]["path"], "verifier completion"))
            fail(completion["verdict"] != "PASS", "verification_required", "Promoted mathematical evidence requires a PASS verdict.")
            fail(record["verifier_completion"] != attempt["verifier_completion"], "transition_invalid", "Attempt record verifier pointer differs from state.")
            if disposition == "candidate":
                fail(completion["verdict"] != "PASS" or "candidate" not in kinds, "transition_invalid", "candidate disposition requires PASS and candidate evidence.")
            if disposition == "no_candidate_with_evidence":
                fail(completion["verdict"] != "PASS" or "verified_partial" not in kinds, "transition_invalid", "no_candidate_with_evidence requires PASS verified_partial evidence.")
        else:
            if attempt["verifier_completion"] is None:
                fail(record["verifier_completion"] is not None, "transition_invalid", "Attempt record claims a verifier completion that never occurred.")
            else:
                fail(record["verifier_completion"] != attempt["verifier_completion"], "transition_invalid", "Attempt record verifier pointer differs from state.")
        new["evidence_items"] = _dedupe_records(new["evidence_items"] + copy.deepcopy(evidence))
        new["typed_references"].append({"kind": "attempt_record", "path": payload["attempt_record"]["path"], "sha256": payload["attempt_record"]["sha256"], "attempt_id": attempt["id"], "ticket_id": ticket_state["id"]})
        new["current_attempt"]["disposition"] = disposition
        new["current_ticket"]["lifecycle"] = "closed"
        route_reset = new["route_reset"]
        if route_reset is not None and route_reset["status"] == "triggered" and route_reset["predecessor_attempt_id"] == attempt["id"]:
            fail(True, "route_reset_sequence_invalid", "The triggered predecessor cannot close before accepting a route portfolio.")
        if route_reset is not None and route_reset["status"] == "portfolio_accepted" and route_reset["predecessor_attempt_id"] == attempt["id"]:
            fail(payload["next_ticket"] is None, "route_reset_sequence_invalid", "An accepted reset portfolio requires one planned successor ticket.")
        if route_reset is not None and route_reset["status"] == "successor_started" and route_reset["successor_attempt_id"] == attempt["id"]:
            route_reset["status"] = "completed"
        new["current_attempt"] = None
        if payload["next_ticket"] is not None:
            rel, next_path = pointer(payload["next_ticket"], root, "next planned ticket")
            next_ticket = validate_v10_ticket(load_json(next_path), root)
            fail(next_ticket["ticket_id"] == ticket_state["id"], "transition_invalid", "The next ticket must have a fresh ID.")
            next_scope_fingerprint = sha_bytes(canonical_bytes(next_ticket["attempt_scope"]))
            reset_successor = route_reset is not None and route_reset["status"] == "portfolio_accepted" and route_reset["predecessor_attempt_id"] == attempt["id"]
            if reset_successor:
                fail(next_ticket["route_card"] != route_reset["selected_route"] or next_ticket["continuity_capsule"] != route_reset["successor_capsule"], "route_reset_sequence_invalid", "The planned successor ticket is not bound to the accepted route and capsule.")
                successor_lead = next_ticket["persistent_lead"]
                fail(successor_lead["lead_id"] == attempt["lead_id"] or successor_lead["mode"] != "new" or successor_lead["previous_ticket_id"] is not None, "partial_reset_identity", "A semantic-reset successor must replace the predecessor lead with one fresh lead in new mode.")
            fail(next_scope_fingerprint == attempt["scope_fingerprint"] and not reset_successor, "attempt_continuity_violation", "An unchanged bottleneck and scope must continue in the current attempt instead of opening a successor ticket.")
            new["current_ticket"] = {"id": next_ticket["ticket_id"], "path": rel, "sha256": payload["next_ticket"]["sha256"], "lifecycle": "planned"}
            new["active_run"]["status"] = "preparing"
        else:
            new["current_ticket"] = None
            new["active_run"]["status"] = "audit_due" if disposition == "candidate" else "awaiting_input"
    elif kind == "RESEARCH_CHECKPOINT":
        require_exact(payload, ("schema", "capsule", "references", "checkpoint_reason", "occurred_at_utc"), "RESEARCH_CHECKPOINT payload")
        fail(payload["schema"] != "math-research-transition-payload/v10", "transition_invalid", "Payload schema is invalid.")
        require_timestamp(payload["occurred_at_utc"], "RESEARCH_CHECKPOINT occurred_at_utc")
        fail(attempt is None or ticket_state is None or ticket_state["lifecycle"] != "active" or new["active_run"]["status"] != "attempt_running", "transition_invalid", "RESEARCH_CHECKPOINT requires an active, unpromoted solver attempt.")
        fail(payload["checkpoint_reason"] not in ("material_result", "agent_handoff", "context_compaction", "cadence_30m", "route_internal_revision"), "transition_invalid", "Checkpoint reason is invalid.")
        _, capsule_path = pointer(payload["capsule"], root, "checkpoint capsule")
        capsule = validate_continuity_capsule(load_json(capsule_path), root)
        old_capsule = validate_continuity_capsule(load_json(resolve_under(root, new["continuity_capsule"]["path"], "old continuity capsule")), root)
        fail(capsule["project_id"] != new["project_id"] or capsule["run_id"] != new["active_run"]["id"], "ticket_scope_changed", "Checkpoint capsule changes project or run identity.")
        fail(capsule["generation"] != generation, "capsule_invalid", "Checkpoint capsule generation must equal the prepared transition generation.")
        fail(capsule["target_sha256"] != old_capsule["target_sha256"], "ticket_scope_changed", "Checkpoint cannot change the frozen target.")
        active_reset = new["route_reset"]
        if active_reset is not None and active_reset["status"] == "triggered":
            fail(capsule["route_reset_directive"] != old_capsule["route_reset_directive"], "route_reset_sequence_invalid", "A triggered reset cannot rewrite its trigger or forbidden mechanism families before portfolio acceptance.")
        ticket = validate_v10_ticket(load_json(resolve_under(root, ticket_state["path"], "active ticket")), root, expected_lifecycle="active")
        active_scope_hash = sha_bytes(canonical_bytes(ticket["attempt_scope"]))
        fail(active_scope_hash != attempt["scope_fingerprint"], "ticket_scope_changed", "Checkpoint changed the active attempt scope.")
        old_claims = {item["claim_id"]: item for item in old_capsule["proof_spine"]}
        new_claims = {item["claim_id"]: item for item in capsule["proof_spine"]}
        for claim_id, prior in old_claims.items():
            if prior["status"] in ("verified", "refuted"):
                fail(new_claims.get(claim_id) != prior, "terminal_claim_regression", "RESEARCH_CHECKPOINT cannot delete, downgrade, or rewrite a terminal claim.")
        verified_paths = {item["path"] for item in new["evidence_items"] if item["kind"] in ("candidate", "verified_partial", "failure_boundary")}
        for claim in capsule["proof_spine"]:
            if claim["status"] not in ("verified", "refuted"):
                continue
            prior = old_claims.get(claim["claim_id"])
            unchanged = prior is not None and prior["status"] == claim["status"] and prior["artifact"] == claim["artifact"]
            if not unchanged:
                fail(claim["artifact"] is None or claim["artifact"]["path"] not in verified_paths, "unverified_claim_promotion", "RESEARCH_CHECKPOINT cannot promote a working claim without verified evidence.")
        refs = validate_references(payload["references"], root, "research checkpoint references")
        for item in refs:
            if item["attempt_id"] is not None:
                fail(item["attempt_id"] != attempt["id"], "reference_invalid", "Checkpoint reference attempt binding differs from current attempt.")
            if item["ticket_id"] is not None:
                fail(item["ticket_id"] != ticket_state["id"], "reference_invalid", "Checkpoint reference ticket binding differs from current ticket.")
        new["continuity_capsule"] = payload["capsule"]
        new["typed_references"] = _dedupe_records(new["typed_references"] + copy.deepcopy(refs))
        new["current_attempt"]["checkpoint_count"] += 1
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
    allowed = _payload_pointer_paths(payload)
    if kind == "ASSET_REGISTRY_UPDATE" and isinstance(payload, dict) and isinstance(payload.get("asset_index"), dict):
        raw_head = load_json(project / "project.json")
        allowed.update(item["path"] for item in asset_index_closure(payload["asset_index"], project, raw_head["project_id"]))
    head, state, manifest, old_hash, audit_notes = load_v10_project(project, audit_mode, allowed)
    generation = head["control_generation"] + 1
    new_state = apply_transition(project, state, kind, payload, generation)
    validate_state(project, new_state)
    stamp = time.time_ns()
    generation_name = f"g{generation:04d}"
    state_rel = f"state/generations/{generation_name}/state-v10.json"
    event_rel = f"events/{generation_name}-{kind.lower().replace('_', '-')}.json"
    manifest_rel = f"state/manifests/{generation_name}.json"
    stage_root = output.resolve()
    fail(stage_root == project.resolve() or project.resolve() in stage_root.parents, "stage_invalid", "Transition staging must be outside the project root.")
    stage_root.mkdir(parents=True, exist_ok=True)
    state_info = _write_stage(stage_root / state_rel, new_state, stamp)
    event = {
        "schema": "math-research-event/v10",
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
    state_pointers = _collect_state_pointers(new_state)
    if new_state.get("asset_index") is not None:
        state_pointers = [item for item in state_pointers if item != new_state["asset_index"]]
        state_pointers.extend(asset_index_closure(new_state["asset_index"], project, new_state["project_id"]))
    for ptr in state_pointers:
        rel, _ = pointer(ptr, project, "transition referenced artifact")
        if rel not in by_path:
            by_path[rel] = _entry_for(project, rel, generation)
    by_path[state_rel] = {"path": state_rel, "sha256": state_info["sha256"], "size": state_info["size"], "mtime_ns": state_info["mtime_ns"], "generation_added": generation}
    by_path[event_rel] = {"path": event_rel, "sha256": event_info["sha256"], "size": event_info["size"], "mtime_ns": event_info["mtime_ns"], "generation_added": generation}
    new_manifest = {"schema": "math-research-archive-manifest/v10", "project_id": head["project_id"], "control_generation": generation, "entries": [by_path[key] for key in sorted(by_path)], "created_at_utc": payload["occurred_at_utc"]}
    manifest_info = _write_stage(stage_root / manifest_rel, new_manifest, stamp + 2)
    full_used = "full_audit_used" in audit_notes
    new_head = {
        "schema": "math-research-project/v10",
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
        "schema": "math-research-transition-plan/v10",
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
    require_exact(spec, ("schema", "predecessor", "successor", "reason", "cumulative_counters", "initial_ticket", "initial_capsule", "initial_route_card", "occurred_at_utc"), "successor spec")
    fail(spec["schema"] != "math-research-successor-spec/v10", "successor_invalid", "Successor spec schema is invalid.")
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
    ticket = validate_v10_ticket(spec["initial_ticket"], successor)
    capsule_rel, capsule_path = pointer(spec["initial_capsule"], successor, "initial continuity capsule")
    capsule = validate_continuity_capsule(load_json(capsule_path), successor)
    route_rel, route_path = pointer(spec["initial_route_card"], successor, "initial route card")
    route = validate_route_card(load_json(route_path))
    fail(ticket["continuity_capsule"] != spec["initial_capsule"] or ticket["route_card"] != spec["initial_route_card"], "successor_invalid", "Initial ticket capsule or route card differs from the successor spec.")
    fail(capsule["project_id"] != succ["project_id"] or capsule["run_id"] != succ["run_id"], "successor_invalid", "Initial capsule identity differs from successor identity.")
    fail(route["route_id"] not in capsule["live_routes"] and route["route_id"] not in capsule["rejected_routes"] and route["route_id"] not in capsule["quarantined_routes"], "successor_invalid", "Initial route card is absent from capsule route registries.")
    ticket_rel = f"runs/{succ['run_id']}/tickets/{ticket['ticket_id']}.json"
    stage_root = output.resolve()
    fail(stage_root == successor.resolve() or successor.resolve() in stage_root.parents, "stage_invalid", "Successor staging must be outside the successor root.")
    stage_root.mkdir(parents=True, exist_ok=True)
    stamp = time.time_ns()
    ticket_info = _write_stage(stage_root / ticket_rel, ticket, stamp)
    lineage_rel = "lineage/predecessor-v10.json"
    lineage = {"schema": "math-research-predecessor/v10", "project_id": pred["project_id"], "run_id": pred["run_id"], "head_sha256": pred_hash, "final_status": pred["final_status"]}
    lineage_info = _write_stage(stage_root / lineage_rel, lineage, stamp + 1)
    state_rel = "state/generations/g0001/state-v10.json"
    state = {
        "schema": "math-research-state/v10",
        "project_id": succ["project_id"],
        "control_generation": 1,
        "active_run": {"id": succ["run_id"], "status": "preparing", "envelope_sha256": succ["envelope_sha256"], "permission_envelope_sha256": succ["permission_envelope_sha256"], "resource_envelope_sha256": succ["resource_envelope_sha256"], "predecessor": {"project_id": pred["project_id"], "run_id": pred["run_id"], "head_sha256": pred_hash, "final_status": pred["final_status"]}, "budgets": succ["budgets"]},
        "current_attempt": None,
        "current_ticket": {"id": ticket["ticket_id"], "path": ticket_rel, "sha256": ticket_info["sha256"], "lifecycle": "planned"},
        "continuity_capsule": spec["initial_capsule"],
        "active_route_card": spec["initial_route_card"],
        "strategy_action": None,
        "route_reset": None,
        "counters": {"run_local": {"attempt_count": 0, "audit_count": 0, "total_round_count": 0, "attempts_since_last_audit": 0}, "cumulative": cumulative},
        "evidence_items": [],
        "typed_references": [],
        "updated_at_utc": spec["occurred_at_utc"],
    }
    state_info = _write_stage(stage_root / state_rel, state, stamp + 2)
    event_rel = "events/g0001-run-successor.json"
    event = {"schema": "math-research-event/v10", "project_id": succ["project_id"], "control_generation": 1, "event_type": "RUN_SUCCESSOR", "previous_event": None, "payload_sha256": sha_file(spec_path), "occurred_at_utc": spec["occurred_at_utc"]}
    event_info = _write_stage(stage_root / event_rel, event, stamp + 3)
    entries: list[dict[str, Any]] = []
    for item in ticket["input_artifacts"]:
        entries.append(_entry_for(successor, item["path"], 1))
    for rel, info in ((ticket_rel, ticket_info), (lineage_rel, lineage_info), (state_rel, state_info), (event_rel, event_info)):
        entries.append({"path": rel, "sha256": info["sha256"], "size": info["size"], "mtime_ns": info["mtime_ns"], "generation_added": 1})
    entries = [dict(item) for item in {item["path"]: item for item in entries}.values()]
    manifest_rel = "state/manifests/g0001.json"
    manifest = {"schema": "math-research-archive-manifest/v10", "project_id": succ["project_id"], "control_generation": 1, "entries": sorted(entries, key=lambda item: item["path"]), "created_at_utc": spec["occurred_at_utc"]}
    manifest_info = _write_stage(stage_root / manifest_rel, manifest, stamp + 4)
    head = {"schema": "math-research-project/v10", "project_id": succ["project_id"], "control_generation": 1, "state": {"path": state_rel, "sha256": state_info["sha256"]}, "event_tail": {"path": event_rel, "sha256": event_info["sha256"]}, "archive_manifest": {"path": manifest_rel, "sha256": manifest_info["sha256"]}, "last_full_audit_generation": 1, "last_full_audit_at_utc": spec["occurred_at_utc"]}
    project_info = _write_stage(stage_root / "project.json", head, stamp + 5)
    immutable = []
    for rel, info in ((ticket_rel, ticket_info), (lineage_rel, lineage_info), (state_rel, state_info), (event_rel, event_info), (manifest_rel, manifest_info)):
        immutable.append({"target": rel, **info})
    plan = {"schema": "math-research-transition-plan/v10", "project_root": str(successor.resolve()), "expected_head_sha256": None, "expected_generation": 0, "new_generation": 1, "event_type": "RUN_SUCCESSOR", "immutable_files": immutable, "candidate_project": {"source": project_info["source"], "sha256": project_info["sha256"], "mtime_ns": project_info["mtime_ns"]}, "created_at_utc": now_utc()}
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
    fail(plan["schema"] != "math-research-transition-plan/v10", "plan_invalid", "Transition plan schema is invalid.")
    project = Path(plan["project_root"])
    project.mkdir(parents=True, exist_ok=True)
    lock = project / ".math-research-v10.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise ResearchError("writer_busy", "The cooperative v10 writer lock already exists.") from exc
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
    freeze_path = project / V8_FREEZE_REL
    if isinstance(raw, dict) and raw.get("schema") == "math-research-project/v8" and freeze_path.exists():
        fail(not freeze_path.is_file(), "migration_freeze_invalid", "The v8 migration freeze marker is not a regular file.")
        freeze = load_json(freeze_path)
        require_exact(freeze, ("schema", "migration_id", "predecessor", "successor", "migration_manifest", "occurred_at_utc"), "v8 migration freeze marker")
        fail(freeze["schema"] != "math-research-v8-freeze/v10", "migration_freeze_invalid", "The v8 migration freeze marker schema is invalid.")
        require_timestamp(freeze["occurred_at_utc"], "v8 migration freeze time")
        predecessor = require_exact(freeze["predecessor"], ("project_id", "head_sha256", "control_generation", "run_id", "run_status"), "v8 migration predecessor")
        successor = require_exact(freeze["successor"], ("project_id", "run_id", "directory_name"), "v8 migration successor")
        fail(predecessor["project_id"] != raw.get("project_id") or predecessor["head_sha256"] != sha_file(project_path) or predecessor["control_generation"] != raw.get("control_generation"), "migration_freeze_invalid", "The v8 migration freeze marker differs from the live predecessor head.")
        fail(Path(successor["directory_name"]).name != successor["directory_name"] or successor["directory_name"] in ("", ".", ".."), "migration_freeze_invalid", "The successor directory name is invalid.")
        successor_root = project.parent / successor["directory_name"]
        successor_ready = False
        successor_head_sha256 = None
        if (successor_root / "project.json").is_file():
            _, successor_state, _, successor_head_sha256, _ = load_v10_project(successor_root, audit_mode)
            fail(successor_state.get("migration") is None or successor_state["migration"]["freeze_record"]["sha256"] != sha_file(freeze_path), "migration_freeze_invalid", "The v10 successor does not bind the v8 freeze marker.")
            successor_ready = True
        return {
            "classification": "v8_migrated_frozen",
            "schema_version": 8,
            "project_id": raw["project_id"],
            "control_generation": raw["control_generation"],
            "project_sha256": sha_file(project_path),
            "migration_id": freeze["migration_id"],
            "freeze_sha256": sha_file(freeze_path),
            "successor_project": str(successor_root.resolve()),
            "successor_run_id": successor["run_id"],
            "successor_ready": successor_ready,
            "successor_head_sha256": successor_head_sha256,
            "next_action": "open_v10_successor" if successor_ready else "recover_exact_prepared_v10_migration_plan",
            "research_writes_forbidden": True,
        }
    if isinstance(raw, dict) and raw.get("schema") == "math-research-project/v10":
        head, state, _, head_hash, notes = load_v10_project(project, audit_mode)
        used = "Full" if "full_audit_used" in notes else "Fast"
        current_attempt = state["current_attempt"]
        current_ticket = state["current_ticket"]
        return {
            "classification": "v10_ready",
            "schema_version": 10,
            "project_id": head["project_id"],
            "control_generation": head["control_generation"],
            "project_sha256": head_hash,
            "run_status": state["active_run"]["status"],
            "ticket_lifecycle": None if current_ticket is None else current_ticket["lifecycle"],
            "current_ticket_id": None if current_ticket is None else current_ticket["id"],
            "current_attempt_id": None if current_attempt is None else current_attempt["id"],
            "lead_id": None if current_attempt is None else current_attempt["lead_id"],
            "checkpoint_count": 0 if current_attempt is None else current_attempt["checkpoint_count"],
            "route_reset": state.get("route_reset"),
            "audit_mode_used": used,
            "audit_notes": notes,
            "continuity_capsule": state["continuity_capsule"],
            "active_route_card": state["active_route_card"],
            "asset_index": state.get("asset_index"),
            "migration": state.get("migration"),
        }
    return {"classification": "delegate_startup_v4", "schema_version": "v3-v9", "goal_status_advisory": legacy_goal_status}


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
    pre10 = sub.add_parser("ticket-preflight-v10")
    pre10.add_argument("--project", required=True)
    pre10.add_argument("--ticket", required=True)
    pre10.add_argument("--access-log")
    capsule = sub.add_parser("continuity-validate")
    capsule.add_argument("--project", required=True)
    capsule.add_argument("--capsule", required=True)
    route = sub.add_parser("route-portfolio-validate")
    route.add_argument("--portfolio", required=True)
    route.add_argument("--capsule")
    route.add_argument("--project")
    strategy = sub.add_parser("strategy-action-validate")
    strategy.add_argument("--project", required=True)
    strategy.add_argument("--action", required=True)
    reset = sub.add_parser("route-reset-assess")
    reset.add_argument("--input", required=True)
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
        elif args.command == "ticket-preflight-v10":
            data = preflight_v10(Path(args.project), Path(args.ticket), Path(args.access_log) if args.access_log else None)
        elif args.command == "continuity-validate":
            capsule = validate_continuity_capsule(load_json(Path(args.capsule)), Path(args.project))
            data = {"classification": "continuity_capsule_valid", "project_id": capsule["project_id"], "run_id": capsule["run_id"], "proof_spine_count": len(capsule["proof_spine"]), "required_full_artifact_count": len(capsule["required_full_artifacts"]), "reset_required": capsule["route_reset_directive"]["required"]}
        elif args.command == "route-portfolio-validate":
            directive = None
            if args.capsule:
                fail(not args.project, "route_portfolio_invalid", "--project is required with --capsule.")
                directive = validate_continuity_capsule(load_json(Path(args.capsule)), Path(args.project))["route_reset_directive"]
            portfolio = validate_route_portfolio(load_json(Path(args.portfolio)), reset_directive=directive)
            data = {"classification": "route_portfolio_valid", "route_count": len(portfolio["routes"]), "semantic_reset_checked": directive is not None and directive["required"]}
        elif args.command == "strategy-action-validate":
            action = validate_strategy_action(load_json(Path(args.action)), Path(args.project))
            data = {"classification": "strategy_action_valid", "action": action["action"], "surface_reset_risk": action["surface_reset_risk"], "required_next_input_count": len(action["required_next_inputs"])}
        elif args.command == "route-reset-assess":
            data = assess_route_reset(load_json(Path(args.input)))
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
