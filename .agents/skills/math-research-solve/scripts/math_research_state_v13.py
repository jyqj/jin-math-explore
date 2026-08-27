#!/usr/bin/env python3
"""Pure fail-closed Startup and transition planner for Math Research Solve v13.

This module never writes project authority.  Goal state is a local gate only;
the Host must still make a fresh get_goal call at every authority boundary.
"""
from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any, Iterable

from v13_common import V13Error, canonical_json, configure_stdio, emit, error_result, is_sha256, load_json, objective_bytes, sha256_bytes, sha256_file

PROJECT_SCHEMA = "math-research-project/v13"
EXECUTION_SCHEMA = "math-research-execution-head/v13"
AUTHORITY_SCHEMA = "math-research-authority-head/v13"
PHASES = {
    "window_idle", "window_planning", "window_planning_blocked", "window_running",
    "attempt_closing", "window_verifying", "window_reconciling", "window_suspended",
    "source_integrity_review", "window_invalidated", "maintenance",
    "completion_pending", "terminal_audit", "project_complete",
}
ACTIVE_PHASES = {
    "window_planning", "window_planning_blocked", "window_running", "attempt_closing",
    "window_verifying", "window_reconciling", "window_suspended",
    "source_integrity_review", "window_invalidated",
}
OUTCOMES = {"candidate_found", "no_candidate", "inconclusive", "failed", "awaiting_input"}
VERDICTS = {"PASS", "FAIL", "INCONCLUSIVE"}
AUDIT_KINDS = {"quantifier_coverage", "strategy_independence", "tool_and_dependency_soundness"}
COUNTER_FIELDS = {
    "attempts_since_route_review", "internal_attempts_completed", "internal_attempts_started",
    "route_review_due", "route_reviews", "terminal_audits",
}
EXECUTION_FIELDS = {
    "schema", "generation", "phase", "migrated_project", "window_source_binding",
    "active_window", "queue", "active_attempts", "route_decisions", "route_portfolio",
    "cognition", "capsules", "verification_queue", "review_required", "counters",
    "legacy_unfinished_work", "source_invalidations", "terminal_audits", "repair_count",
    "last_transition",
}


def require(condition: bool, code: str, message: str, path: str | None = None) -> None:
    if not condition:
        raise V13Error(code, message, path)


def closed(value: Any, fields: Iterable[str], code: str, name: str) -> dict[str, Any]:
    require(isinstance(value, dict) and set(value) == set(fields), code, f"{name} fields are not closed")
    return value


def nonempty(value: Any, code: str, name: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), code, f"{name} must be a nonempty string")
    return value


def valid_hash(value: Any, code: str, name: str) -> str:
    require(is_sha256(value), code, f"{name} must be a lowercase SHA-256")
    return value


def validate_pointer(value: Any, name: str, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    closed(value, {"path", "sha256"}, "pointer_invalid", f"{name} pointer")
    nonempty(value["path"], "pointer_invalid", f"{name}.path")
    valid_hash(value["sha256"], "pointer_invalid", f"{name}.sha256")


def validate_pointer_list(value: Any, name: str) -> None:
    require(isinstance(value, list), "pointer_list_invalid", f"{name} must be an array")
    for index, pointer in enumerate(value):
        validate_pointer(pointer, f"{name}[{index}]")


def validate_attempt_package_preflight_ref(value: Any) -> None:
    validate_pointer_list(value, "artifact_refs")
    matches = [ref for ref in value if ref["path"].endswith("/attempt-package-preflight.json")]
    require(len(matches) == 1, "attempt_package_preflight_missing", "Exactly one attempt-package preflight receipt is required before candidate freeze")


def validate_review_gate(value: Any) -> None:
    fields = {"scope", "owner_lifecycle", "blocked_transition", "dependency_closure", "release_condition", "evidence_refs"}
    closed(value, fields, "review_gate_invalid", "review_required gate")
    require(value["scope"] in {"claim", "route", "attempt", "window", "project", "source_integrity"}, "review_gate_invalid", "review scope invalid")
    nonempty(value["owner_lifecycle"], "review_gate_invalid", "owner_lifecycle")
    require(isinstance(value["blocked_transition"], list) and value["blocked_transition"] and all(isinstance(x, str) and x for x in value["blocked_transition"]), "review_gate_invalid", "blocked_transition must be nonempty")
    require(isinstance(value["dependency_closure"], list) and all(isinstance(x, str) and x for x in value["dependency_closure"]), "review_gate_invalid", "dependency_closure invalid")
    nonempty(value["release_condition"], "review_gate_invalid", "release_condition")
    require(isinstance(value["evidence_refs"], list) and all(isinstance(x, str) and x for x in value["evidence_refs"]), "review_gate_invalid", "evidence_refs invalid")


def validate_semantic_fingerprint(value: Any) -> None:
    closed(value, {"proof_object", "mechanism_family", "quantifier_strategy"}, "semantic_fingerprint_invalid", "semantic fingerprint")
    for key in value:
        nonempty(value[key], "semantic_fingerprint_invalid", key)


def validate_source_binding(value: Any, *, migrated: bool = False, objective_commitment: str | None = None) -> None:
    require(isinstance(value, dict) and value.get("kind") in {"validated_map", "genesis_objective"}, "source_binding_invalid", "window_source_binding must be a closed union")
    if value["kind"] == "validated_map":
        fields = {"kind", "map", "validation_receipt", "research_authority_head_sha256", "objective_commitment_sha256", "promoted_memory_index_sha256", "route_review_sha256"}
        closed(value, fields, "source_binding_invalid", "validated_map source")
        validate_pointer(value["map"], "map"); validate_pointer(value["validation_receipt"], "validation_receipt")
        for key in fields - {"kind", "map", "validation_receipt"}:
            valid_hash(value[key], "source_binding_invalid", key)
    else:
        require(not migrated, "genesis_forbidden_for_migration", "Migrated projects may never use genesis_objective")
        fields = {"kind", "objective_commitment_sha256", "genesis_head_sha256", "eligibility_receipt", "never_created_marker", "consumed"}
        closed(value, fields, "source_binding_invalid", "genesis source")
        valid_hash(value["objective_commitment_sha256"], "source_binding_invalid", "objective commitment")
        valid_hash(value["genesis_head_sha256"], "source_binding_invalid", "genesis head")
        validate_pointer(value["eligibility_receipt"], "genesis eligibility receipt")
        require(value["never_created_marker"] is True and isinstance(value["consumed"], bool), "genesis_binding_invalid", "Genesis requires a never-created marker and a boolean consumption flag")
    if objective_commitment is not None:
        require(value["objective_commitment_sha256"] == objective_commitment, "source_objective_mismatch", "Source objective differs")


def validate_counters(value: Any) -> None:
    closed(value, COUNTER_FIELDS, "counters_invalid", "counters")
    for key in COUNTER_FIELDS - {"route_review_due"}:
        require(isinstance(value[key], int) and not isinstance(value[key], bool) and value[key] >= 0, "counters_invalid", f"{key} invalid")
    require(isinstance(value["route_review_due"], bool), "counters_invalid", "route_review_due invalid")
    require(value["internal_attempts_completed"] <= value["internal_attempts_started"], "counters_invalid", "completed attempts exceed starts")


def validate_budget(value: Any) -> None:
    fields = {"runtime_seconds", "tool_calls", "tickets", "checkpoints", "computations", "output_bytes", "no_progress_checkpoints"}
    closed(value, fields, "budget_invalid", "budget")
    require(all(isinstance(value[k], int) and not isinstance(value[k], bool) and value[k] >= 0 for k in fields), "budget_invalid", "Budget values must be nonnegative integers")


def validate_portfolio(value: Any) -> None:
    fields = {"schema", "window_id", "source_binding_sha256", "members", "window_budget", "budget_transfer_policy"}
    closed(value, fields, "portfolio_invalid", "route portfolio")
    require(value["schema"] == "math-research-route-portfolio/v13", "portfolio_invalid", "Portfolio schema invalid")
    nonempty(value["window_id"], "portfolio_invalid", "window_id"); valid_hash(value["source_binding_sha256"], "portfolio_invalid", "source binding")
    members = value["members"]
    require(isinstance(members, list) and len(members) == 3, "portfolio_invalid", "Portfolio must have exactly three members")
    mfields = {"member_id", "route_id", "kind", "semantic_fingerprint", "bounded_question", "required_outputs", "stop_rule", "failure_boundary", "budget"}
    for member in members:
        closed(member, mfields, "portfolio_member_invalid", "portfolio member")
        for key in ("member_id", "route_id", "bounded_question", "stop_rule", "failure_boundary"):
            nonempty(member[key], "portfolio_member_invalid", key)
        require(member["kind"] in {"research", "route_discovery"}, "portfolio_member_invalid", "Member kind invalid")
        validate_semantic_fingerprint(member["semantic_fingerprint"]); validate_budget(member["budget"])
        require(isinstance(member["required_outputs"], list) and member["required_outputs"], "portfolio_member_invalid", "required_outputs missing")
    require(len({m["member_id"] for m in members}) == 3, "portfolio_duplicate", "Member IDs must differ")
    require(len({canonical_json(m["semantic_fingerprint"]) for m in members}) == 3, "portfolio_not_differentiated", "Semantic fingerprints must differ")
    validate_budget(value["window_budget"]); nonempty(value["budget_transfer_policy"], "portfolio_invalid", "budget transfer policy")


def validate_route_card(value: Any) -> None:
    fields = {"schema", "project_id", "window_id", "proposed_attempt_id", "objective_commitment_sha256", "window_source_binding_sha256", "route_decision_sha256", "evidence_standard_sha256", "semantic_fingerprint", "success_gate", "candidate_failure_gate"}
    closed(value, fields, "route_card_invalid", "route card")
    require(value["schema"] == "math-research-route-card/v13", "route_card_invalid", "Route card schema invalid")
    for key in ("project_id", "window_id", "proposed_attempt_id", "success_gate", "candidate_failure_gate"): nonempty(value[key], "route_card_invalid", key)
    for key in ("objective_commitment_sha256", "window_source_binding_sha256", "route_decision_sha256", "evidence_standard_sha256"): valid_hash(value[key], "route_card_invalid", key)
    validate_semantic_fingerprint(value["semantic_fingerprint"])


def validate_capsule(value: Any, route_card: dict[str, Any]) -> None:
    fields = {"schema", "project_id", "window_id", "proposed_attempt_id", "objective_commitment_sha256", "cognition_sha256", "selected_rendering_sha256", "route_card_sha256", "semantic_fingerprint", "local_position", "open_questions", "generation", "previous_capsule_sha256"}
    closed(value, fields, "capsule_invalid", "continuity capsule")
    require(value["schema"] == "math-research-continuity-capsule/v13" and value["project_id"] == route_card["project_id"] and value["window_id"] == route_card["window_id"] and value["proposed_attempt_id"] == route_card["proposed_attempt_id"] and value["objective_commitment_sha256"] == route_card["objective_commitment_sha256"] and value["semantic_fingerprint"] == route_card["semantic_fingerprint"], "capsule_binding_mismatch", "Capsule differs from route card")
    for key in ("cognition_sha256", "selected_rendering_sha256", "route_card_sha256"): valid_hash(value[key], "capsule_invalid", key)
    require(value["route_card_sha256"] == sha256_bytes(canonical_json(route_card)), "capsule_binding_mismatch", "Capsule route-card hash differs")
    require(isinstance(value["local_position"], str) and isinstance(value["open_questions"], list) and all(isinstance(x, str) for x in value["open_questions"]), "capsule_invalid", "Capsule local fields invalid")
    require(isinstance(value["generation"], int) and value["generation"] >= 0 and (value["previous_capsule_sha256"] is None or is_sha256(value["previous_capsule_sha256"])), "capsule_invalid", "Capsule generation/lineage invalid")


def validate_queue_item(value: Any, route_card: dict[str, Any], ticket_sha256: str) -> None:
    fields = {"schema", "window_id", "proposed_attempt_id", "solver_ticket_sha256", "status", "candidate_sha256", "dependency_sha256s", "verdict", "package_sha256"}
    closed(value, fields, "queue_item_invalid", "window queue item")
    require(value["schema"] == "math-research-window-queue-item/v13" and value["window_id"] == route_card["window_id"] and value["proposed_attempt_id"] == route_card["proposed_attempt_id"] and value["solver_ticket_sha256"] == ticket_sha256 and value["status"] == "prepared", "queue_item_invalid", "Prepared queue item binding/status invalid")
    require(value["candidate_sha256"] is None and value["dependency_sha256s"] == [] and value["verdict"] is None and value["package_sha256"] is None, "queue_item_invalid", "Prepared queue item cannot contain output")


def validate_prepare_record(value: Any, *, project_id: str, objective_commitment: str) -> None:
    fields = {"schema", "project_id", "window_id", "proposed_attempt_id", "portfolio_member_id", "objective_commitment_sha256", "source_binding_sha256", "portfolio_sha256", "route_decision", "ticket", "cognition", "selected_rendering", "route_card", "route_card_contract", "capsule", "capsule_contract", "budget", "queue_item", "queue_item_contract", "access_check", "input_check", "staging_check"}
    closed(value, fields, "prepare_record_invalid", "ATTEMPT_START_PREPARE")
    require(value["schema"] == "math-research-attempt-start-prepare/v13" and value["project_id"] == project_id and value["objective_commitment_sha256"] == objective_commitment, "prepare_identity_mismatch", "Prepare identity differs")
    for key in ("window_id", "proposed_attempt_id", "portfolio_member_id"):
        nonempty(value[key], "prepare_record_invalid", key)
    for key in ("objective_commitment_sha256", "source_binding_sha256", "portfolio_sha256"):
        valid_hash(value[key], "prepare_record_invalid", key)
    for key in ("route_decision", "ticket", "cognition", "selected_rendering", "route_card", "capsule", "queue_item"):
        validate_pointer(value[key], key)
    validate_route_card(value["route_card_contract"]); validate_capsule(value["capsule_contract"], value["route_card_contract"]); validate_queue_item(value["queue_item_contract"], value["route_card_contract"], value["ticket"]["sha256"])
    require(value["route_card"]["sha256"] == sha256_bytes(canonical_json(value["route_card_contract"])) and value["capsule"]["sha256"] == sha256_bytes(canonical_json(value["capsule_contract"])) and value["queue_item"]["sha256"] == sha256_bytes(canonical_json(value["queue_item_contract"])), "prepare_contract_hash_mismatch", "Prepare object pointers do not bind their closed contracts")
    require(value["route_card_contract"]["project_id"] == project_id and value["route_card_contract"]["window_id"] == value["window_id"] and value["route_card_contract"]["proposed_attempt_id"] == value["proposed_attempt_id"] and value["route_card_contract"]["objective_commitment_sha256"] == objective_commitment and value["route_card_contract"]["window_source_binding_sha256"] == value["source_binding_sha256"] and value["route_card_contract"]["route_decision_sha256"] == value["route_decision"]["sha256"] and value["capsule_contract"]["cognition_sha256"] == value["cognition"]["sha256"] and value["capsule_contract"]["selected_rendering_sha256"] == value["selected_rendering"]["sha256"], "prepare_contract_binding_mismatch", "Prepare contracts differ from attempt-local pointers")
    validate_budget(value["budget"])
    require(value["access_check"] is True and value["input_check"] is True and value["staging_check"] is True, "prepare_check_failed", "Prepare checks must all PASS")


def validate_active_attempt(value: Any) -> None:
    fields = {"attempt_id", "portfolio_member_id", "prepare_sha256", "source_binding_sha256", "portfolio_sha256", "route_decision_sha256", "ticket_sha256", "cognition_sha256", "selected_rendering_sha256", "route_card_sha256", "semantic_fingerprint", "evidence_standard_sha256", "activation_receipt_sha256", "status", "last_capsule_sha256", "last_verified_checkpoint", "closing", "verification", "repair_count", "package"}
    closed(value, fields, "active_attempt_invalid", "active attempt")
    for key in ("attempt_id", "portfolio_member_id"): nonempty(value[key], "active_attempt_invalid", key)
    for key in ("prepare_sha256", "source_binding_sha256", "portfolio_sha256", "route_decision_sha256", "ticket_sha256", "cognition_sha256", "selected_rendering_sha256", "route_card_sha256", "evidence_standard_sha256", "activation_receipt_sha256", "last_capsule_sha256"): valid_hash(value[key], "active_attempt_invalid", key)
    validate_semantic_fingerprint(value["semantic_fingerprint"])
    require(value["status"] in {"solver_running", "closing", "verification_queued", "verification_complete", "package_ready"}, "active_attempt_invalid", "Attempt status invalid")
    validate_pointer(value["last_verified_checkpoint"], "last verified checkpoint", nullable=True)
    require(isinstance(value["repair_count"], int) and 0 <= value["repair_count"] <= 1, "active_attempt_invalid", "Per-attempt repair count invalid")
    if value["status"] == "solver_running": require(value["closing"] is None and value["verification"] is None and value["package"] is None, "active_attempt_invalid", "Running attempt retains closing output")
    if value["status"] in {"closing", "verification_queued", "verification_complete", "package_ready"}: require(isinstance(value["closing"], dict), "active_attempt_invalid", "Closing record missing")
    if value["status"] == "verification_complete": require(isinstance(value["verification"], dict) and value["verification"].get("verdict") in VERDICTS, "active_attempt_invalid", "Verification record missing")
    if value["status"] == "package_ready": require(isinstance(value["package"], dict) and is_sha256(value["package"].get("sha256")), "active_attempt_invalid", "Ready package missing")


def validate_terminal_record(value: Any) -> None:
    require(isinstance(value, dict), "terminal_record_invalid", "Terminal record must be an object")
    if value.get("status") == "maintenance":
        require(set(value) == {"status", "origin_phase", "start"} and value["origin_phase"] in {"window_idle", "completion_pending"} and isinstance(value["start"], dict), "terminal_record_invalid", "Maintenance marker invalid")
        return
    status = value.get("status"); require(status in {"candidate_frozen", "auditing", "published"}, "terminal_record_invalid", "Terminal status invalid")
    fields = {"status", "candidate", "dependencies", "completion_candidate_sha256", "audits"}
    if status in {"auditing", "published"}: fields.add("audit_tickets")
    if status == "published": fields.update({"terminal_summary", "completion_plan"})
    closed(value, fields, "terminal_record_invalid", "terminal record")
    validate_pointer(value["candidate"], "terminal candidate"); validate_pointer_list(value["dependencies"], "terminal dependencies"); valid_hash(value["completion_candidate_sha256"], "terminal_record_invalid", "completion candidate hash")
    require(isinstance(value["audits"], dict) and set(value["audits"]) <= AUDIT_KINDS, "terminal_record_invalid", "Terminal audit set invalid")
    if status in {"auditing", "published"}:
        require(isinstance(value["audit_tickets"], dict) and set(value["audit_tickets"]) == AUDIT_KINDS, "terminal_record_invalid", "Three audit tickets required")
        for key, pointer in value["audit_tickets"].items(): validate_pointer(pointer, f"terminal ticket {key}")
        require(len({x["sha256"] for x in value["audit_tickets"].values()}) == 3, "terminal_record_invalid", "Terminal tickets must be distinct")
    for kind, result in value["audits"].items():
        fields = {"schema", "audit_kind", "ticket_sha256", "completion_candidate_sha256", "verdict", "receipt", "impact_classification", "new_math_performed"}
        closed(result, fields, "terminal_result_invalid", "terminal audit result")
        require(result["schema"] == "math-research-terminal-audit-result/v13" and result["audit_kind"] == kind and result["ticket_sha256"] == value["audit_tickets"][kind]["sha256"] and result["completion_candidate_sha256"] == value["completion_candidate_sha256"] and result["verdict"] in VERDICTS and result["new_math_performed"] is False, "terminal_result_invalid", "Terminal audit result binding invalid")
        validate_pointer(result["receipt"], "terminal audit receipt")
        require((result["verdict"] == "PASS" and result["impact_classification"] is None) or (result["verdict"] != "PASS" and result["impact_classification"] in {"coverage", "soundness"}), "terminal_result_invalid", "Terminal audit impact classification invalid")
    if status == "published": validate_pointer(value["terminal_summary"], "terminal summary"); validate_pointer(value["completion_plan"], "completion plan")


def validate_execution(execution: Any, project: dict[str, Any]) -> None:
    closed(execution, EXECUTION_FIELDS, "execution_fields_invalid", "execution head")
    require(execution["schema"] == EXECUTION_SCHEMA and execution["phase"] in PHASES, "execution_head_invalid", "Execution schema/phase invalid")
    require(isinstance(execution["generation"], int) and execution["generation"] >= 0 and isinstance(execution["migrated_project"], bool), "execution_head_invalid", "Execution identity invalid")
    for key in ("queue", "active_attempts", "route_decisions", "capsules", "verification_queue", "review_required", "legacy_unfinished_work", "source_invalidations", "terminal_audits"):
        require(isinstance(execution[key], list), "execution_head_invalid", f"{key} must be an array")
    for gate in execution["review_required"]:
        validate_review_gate(gate)
    for attempt in execution["active_attempts"]:
        validate_active_attempt(attempt)
    for terminal in execution["terminal_audits"]:
        validate_terminal_record(terminal)
    require(len({x["attempt_id"] for x in execution["active_attempts"]}) == len(execution["active_attempts"]), "active_attempt_invalid", "Active attempt IDs duplicate")
    if execution["active_attempts"]:
        require(len(execution["active_attempts"]) == 3 and len({x["activation_receipt_sha256"] for x in execution["active_attempts"]}) == 1, "window_attempt_group_invalid", "An activated window must retain exactly three attempts and one activation receipt")
    validate_counters(execution["counters"])
    require(isinstance(execution["repair_count"], int) and 0 <= execution["repair_count"] <= 3, "execution_head_invalid", "repair_count invalid")
    if execution["window_source_binding"] is not None:
        validate_source_binding(execution["window_source_binding"], migrated=execution["migrated_project"], objective_commitment=project["objective_commitment_sha256"])
    if execution["route_portfolio"] is not None:
        validate_portfolio(execution["route_portfolio"])
    inactive = {"window_idle", "completion_pending", "terminal_audit", "maintenance", "project_complete"}
    if execution["phase"] in inactive:
        require(execution["active_window"] is None and execution["window_source_binding"] is None and execution["queue"] == [] and execution["active_attempts"] == [] and execution["route_decisions"] == [] and execution["route_portfolio"] is None and execution["cognition"] is None and execution["capsules"] == [] and execution["verification_queue"] == [], "idle_pointer_leak", "Inactive phase retains active pointers")
    if project["project_complete"]:
        require(project["pending_goal_update"] is True and execution["phase"] == "project_complete", "completion_flags_invalid", "Complete project must retain pending Goal update")
    else:
        require(execution["phase"] != "project_complete", "completion_flags_invalid", "Incomplete project has terminal phase")


def _load_bound(root: Path, pointer: dict[str, str], name: str) -> dict[str, Any]:
    path = root / Path(pointer["path"])
    require(path.is_file() and sha256_file(path) == pointer["sha256"], "head_hash_mismatch", f"{name} hash mismatch")
    value = load_json(path, canonical_required=True); require(isinstance(value, dict), "head_invalid", f"{name} must be an object")
    return value


def _validate_map_review_closure(
    root: Path,
    authority: dict[str, Any],
    *,
    allow_legacy: bool,
) -> tuple[bool, str]:
    """Validate the independent map-review closure bound by an authority head.

    Old v13 authorities used a thin review receipt.  Startup may keep those
    projects readable (and an already-active window resumable), but it must not
    silently reinterpret the thin receipt as a closure PASS.
    """
    pointer = authority.get("independent_semantic_review")
    if not isinstance(pointer, dict) or set(pointer) != {"path", "sha256"}:
        if allow_legacy:
            return False, "map_review_upgrade_required"
        raise V13Error("map_review_closure_missing", "Research-map publication requires a semantic-review closure")
    validate_pointer(pointer, "map semantic review closure")
    closure = _load_bound(root, pointer, "map semantic review closure")
    if closure.get("schema") != "math-research-map-review-closure/v1":
        if allow_legacy:
            return False, "map_review_upgrade_required"
        raise V13Error("map_review_closure_invalid", "Thin or legacy semantic-review receipts cannot publish a research map")
    try:
        from map_semantic_review_v1 import validate_closure_document
    except ImportError as exc:  # fail closed when the mandatory Harness is unavailable
        raise V13Error("map_review_harness_unavailable", "Map semantic-review Harness is unavailable") from exc
    result = validate_closure_document(root, closure, expected_closure_path=pointer["path"])
    require(isinstance(result, dict) and result.get("ok") is True, "map_review_closure_invalid", "Map semantic-review closure failed validation")
    return True, "PASS"


def _require_candidate_map_review(
    root: Path,
    project: dict[str, Any],
    candidate_pointer: dict[str, Any],
    semantic_pointer: dict[str, Any] | None = None,
) -> None:
    """Require a closure only when a transition publishes new authority."""
    validate_pointer(candidate_pointer, "candidate research authority")
    if candidate_pointer == project["research_authority_head"]:
        return
    candidate = _load_bound(root, candidate_pointer, "candidate research authority")
    require(candidate.get("schema") == AUTHORITY_SCHEMA, "authority_head_invalid", "Candidate authority schema invalid")
    if semantic_pointer is not None:
        validate_pointer(semantic_pointer, "semantic review closure")
        require(semantic_pointer == candidate.get("independent_semantic_review"), "map_review_closure_mismatch", "Transition review pointer differs from candidate authority closure")
    _validate_map_review_closure(root, candidate, allow_legacy=False)


def validate_project(root: Path) -> dict[str, Any]:
    require(root.is_dir(), "project_missing", "Project root missing")
    require({p.name for p in root.iterdir()} == {"project.json", "README.md", "研究地图", ".research"}, "root_layout_invalid", "Active root must contain exactly four entries")
    project_path = root / "project.json"; project = load_json(project_path, canonical_required=True)
    ordered = ["schema", "project_id", "created_at_utc", "objective", "objective_commitment_sha256", "research_authority_head", "execution_state_head", "generation", "project_complete", "pending_goal_update"]
    require(isinstance(project, dict) and list(project) == ordered and project["schema"] == PROJECT_SCHEMA, "project_fields_invalid", "project.json schema/order invalid")
    for key in ("objective", "research_authority_head", "execution_state_head"):
        validate_pointer(project[key], key)
    objective = _load_bound(root, project["objective"], "objective"); raw = objective_bytes(objective)
    require(sha256_bytes(raw) == project["objective_commitment_sha256"] == project["objective"]["sha256"], "objective_commitment_mismatch", "Objective commitment mismatch")
    execution = _load_bound(root, project["execution_state_head"], "execution_state_head"); validate_execution(execution, project)
    authority = _load_bound(root, project["research_authority_head"], "research_authority_head")
    require(authority.get("schema") == AUTHORITY_SCHEMA, "authority_head_invalid", "Authority schema invalid")
    manifest = authority.get("candidate_manifest"); validate_pointer(manifest, "candidate_manifest")
    require(sha256_file(root / Path(manifest["path"])) == manifest["sha256"], "authority_manifest_mismatch", "Authority manifest mismatch")
    map_pointer, receipt_pointer = authority.get("research_map"), authority.get("map_validation_receipt")
    genesis_ready = map_pointer is None and receipt_pointer is None
    if genesis_ready:
        require(authority.get("map_never_created") is True and authority.get("route_review") is None and authority.get("independent_semantic_review") is None and authority.get("memory_index") == {"items": []}, "genesis_authority_invalid", "Genesis authority must prove that no map/review/memory has ever been published")
        validate_pointer(authority.get("genesis_eligibility"), "genesis eligibility")
        require(not (root / "研究地图/.research/research-map.json").exists() and not (root / "研究地图/.research/validation-receipt.json").exists(), "genesis_map_already_exists", "Genesis is forbidden after any official map bytes exist")
        map_control = None; map_receipt = {"status": "GENESIS", "semantic_review": "NOT_APPLICABLE"}
    else:
        validate_pointer(map_pointer, "research_map"); validate_pointer(receipt_pointer, "map_validation_receipt")
        map_control = _load_bound(root, map_pointer, "research_map"); map_receipt = _load_bound(root, receipt_pointer, "map_validation_receipt")
        require(map_control.get("project_objective_sha256") == project["objective_commitment_sha256"] and map_control.get("authority_manifest_sha256") == manifest["sha256"] and map_control.get("status") == "current" and "route_decision" not in map_control, "map_authority_mismatch", "Closed map binding invalid")
        assets = load_json(root / "研究地图/.research/asset-references.json", canonical_required=True)
        require(assets.get("schema") == "math-research-map-asset-references/v3" and assets.get("objective_commitment_sha256") == project["objective_commitment_sha256"] and assets.get("authority_manifest_sha256") == manifest["sha256"], "asset_binding_invalid", "Asset references invalid")
        require(assets.get("asset_count") == len(assets.get("assets", [])) and len(assets.get("memory_ids", [])) == len(authority.get("memory_index", {}).get("items", [])), "asset_inventory_invalid", "Asset or memory count mismatch")
        for rel in assets.get("project_records", []):
            require((root / Path(rel)).is_file(), "asset_project_record_missing", f"Missing project record: {rel}")
        route_review = _load_bound(root, authority["route_review"], "route_review")
        require(route_review.get("schema") == "math-research-route-review/v2" and route_review.get("new_math_performed") is False, "route_review_invalid", "Route review invalid")
        require({x.get("route_id") for x in route_review.get("routes", [])} == {x.get("route_id") for x in map_control.get("routes", [])}, "route_review_map_mismatch", "Route IDs differ")
        require(any(f"route-review:{route_review.get('review_id')}" in x.get("evidence_refs", []) for x in map_control.get("routes", [])), "route_review_reference_missing", "Map does not cite route review")
    spines: list[str] = []
    for item in authority.get("memory_index", {}).get("items", []):
        memory = _load_bound(root, item, f"memory:{item.get('memory_id')}")
        require(memory.get("schema") == "math-research-memory-item/v2" and memory.get("memory_id") == item.get("memory_id"), "memory_v2_invalid", "Memory binding invalid")
        require(memory.get("method_overview") and memory.get("method_spine") and memory.get("reusable_structures") and memory.get("cannot_imply") and memory.get("evidence_refs"), "memory_causality_missing", "Memory causality incomplete")
        spines.append(memory["method_spine"])
    require(len(set(spines)) > 1 or len(spines) <= 1, "memory_template_detected", "Generic migration memory template detected")
    if not genesis_ready:
        visible_paths = ("研究地图/00-研究地图契约.md", "研究地图/01-主研究地图.md", "研究地图/40-路线景观与重排条件.md", "研究地图/桥梁/权威状态与地图绑定.md")
        require(all((root / rel).is_file() for rel in visible_paths), "map_layout_invalid", "Official map layout incomplete")
        visible = "\n".join((root / rel).read_text(encoding="utf-8") for rel in visible_paths)
        for marker in ("map_status: review_required", "math-research-project/v12", "Startup v7", "等待你确认", "先寻找新增的全量词算术节省；如果不能"):
            require(marker not in visible, "visible_map_stale", f"Visible map retains stale marker: {marker}")
    if genesis_ready:
        semantic_pass, map_review_status = True, "NOT_APPLICABLE"
    else:
        semantic_pass, map_review_status = _validate_map_review_closure(root, authority, allow_legacy=True)
    activation = execution["phase"] == "window_idle" and not execution["review_required"] and semantic_pass and not project["project_complete"]
    status = "v13_complete_pending_goal_update" if project["project_complete"] else ("v13_ready" if semantic_pass or execution["phase"] in ACTIVE_PHASES else "map_review_upgrade_required")
    source_mode = "genesis_objective" if genesis_ready else ("validated_map" if semantic_pass else "legacy_map_upgrade_required")
    return {"ok": True, "status": status, "phase": execution["phase"], "project_id": project["project_id"], "project_head_sha256": sha256_file(project_path), "objective_commitment_sha256": project["objective_commitment_sha256"], "generation": project["generation"], "project_complete": project["project_complete"], "pending_goal_update": project["pending_goal_update"], "activation_eligible": activation, "semantic_review": map_review_status, "source_mode": source_mode}


def _payload(payload: Any, schema: str, fields: set[str], name: str) -> dict[str, Any]:
    closed(payload, fields | {"schema"}, "transition_payload_invalid", name)
    require(payload["schema"] == schema, "transition_payload_invalid", f"{name} schema invalid")
    return payload


def _attempt(execution: dict[str, Any], attempt_id: str) -> dict[str, Any]:
    matches = [x for x in execution["active_attempts"] if x.get("attempt_id") == attempt_id]
    require(len(matches) == 1, "attempt_not_active", "Attempt is not uniquely active")
    return matches[0]


def _replace(values: list[dict[str, Any]], key: str, identity: str, new: dict[str, Any]) -> list[dict[str, Any]]:
    return [new if x.get(key) == identity else x for x in values]


def _clear_active(candidate: dict[str, Any], phase: str) -> None:
    candidate.update({"phase": phase, "window_source_binding": None, "active_window": None, "queue": [], "active_attempts": [], "route_decisions": [], "route_portfolio": None, "cognition": None, "capsules": [], "verification_queue": [], "repair_count": 0})


def _gate_blocks(execution: dict[str, Any], transition: str) -> bool:
    return any("*" in gate["blocked_transition"] or transition in gate["blocked_transition"] for gate in execution["review_required"])


def _active_window(window_id: str, owner: str, ids: list[str], counters: dict[str, Any], budget: dict[str, Any]) -> dict[str, Any]:
    return {"schema": "math-research-active-window/v13", "window_id": window_id, "planning_owner": owner, "proposed_attempt_ids": ids, "counter_snapshot": counters, "budget_reservation": budget, "activation_receipt": None, "suspended_from": None, "resume_capsule": None, "source_review_return_phase": None, "reconciliation": None}


def prepare_transition(root: Path, transition: str, payload: dict[str, Any], *, goal_state: str = "active") -> dict[str, Any]:
    status = validate_project(root); project = load_json(root / "project.json", canonical_required=True)
    execution = load_json(root / Path(project["execution_state_head"]["path"]), canonical_required=True)
    require(not project["project_complete"], "project_closed", "Final head is immutable; only retry the same Goal completion call")
    require(goal_state == "active", "goal_gate_closed", "Local Goal gate is not active; it never replaces fresh get_goal")
    require(not _gate_blocks(execution, transition), "review_required", "A scoped gate blocks this transition")
    candidate = copy.deepcopy(execution); candidate["generation"] += 1; candidate["last_transition"] = transition
    authority = "execution"; candidate_research = None; candidate_project = None

    if transition == "WINDOW_PLAN":
        require(execution["phase"] == "window_idle", "transition_blocked", "WINDOW_PLAN requires window_idle")
        require(status["activation_eligible"], "map_review_upgrade_required", "Current research map lacks a valid independent semantic-review closure")
        fields = {"window_id", "planning_owner", "source_binding", "route_portfolio", "proposed_attempt_ids", "counter_snapshot", "budget_reservation"}
        _payload(payload, "math-research-window-plan/v13", fields, transition)
        validate_source_binding(payload["source_binding"], migrated=execution["migrated_project"], objective_commitment=project["objective_commitment_sha256"])
        authority_head = load_json(root / Path(project["research_authority_head"]["path"]), canonical_required=True)
        if payload["source_binding"]["kind"] == "genesis_objective":
            require(authority_head.get("map_never_created") is True and authority_head.get("research_map") is None and payload["source_binding"]["consumed"] is False and payload["source_binding"]["genesis_head_sha256"] == project["research_authority_head"]["sha256"] and payload["source_binding"]["eligibility_receipt"] == authority_head.get("genesis_eligibility"), "genesis_not_eligible", "Genesis source is not the current never-created authority")
        else:
            memory_sha = sha256_bytes(canonical_json(authority_head.get("memory_index")))
            require(payload["source_binding"]["research_authority_head_sha256"] == project["research_authority_head"]["sha256"] and payload["source_binding"]["map"] == authority_head.get("research_map") and payload["source_binding"]["validation_receipt"] == authority_head.get("map_validation_receipt") and payload["source_binding"]["promoted_memory_index_sha256"] == memory_sha and payload["source_binding"]["route_review_sha256"] == authority_head.get("route_review", {}).get("sha256"), "validated_map_not_current", "Validated-map source is not the current research authority")
        validate_portfolio(payload["route_portfolio"]); validate_counters(payload["counter_snapshot"]); validate_budget(payload["budget_reservation"])
        source_sha = sha256_bytes(canonical_json(payload["source_binding"])); ids = payload["proposed_attempt_ids"]
        require(payload["counter_snapshot"] == execution["counters"] and isinstance(ids, list) and len(ids) == 3 and len(set(ids)) == 3 and all(isinstance(x, str) and x for x in ids), "planning_invalid", "Planning counters or proposed IDs invalid")
        require(payload["route_portfolio"]["window_id"] == payload["window_id"] and payload["route_portfolio"]["source_binding_sha256"] == source_sha, "planning_binding_mismatch", "Portfolio window/source differs")
        candidate["phase"] = "window_planning"; candidate["window_source_binding"] = payload["source_binding"]; candidate["route_portfolio"] = payload["route_portfolio"]
        candidate["active_window"] = _active_window(payload["window_id"], payload["planning_owner"], ids, payload["counter_snapshot"], payload["budget_reservation"])
    elif transition in {"WINDOW_PLANNING_BLOCK", "WINDOW_PLANNING_RESUME", "WINDOW_PLANNING_SUPERSEDE"}:
        if transition == "WINDOW_PLANNING_BLOCK":
            require(execution["phase"] == "window_planning", "transition_blocked", "Planning block requires planning")
            _payload(payload, "math-research-window-planning-block/v13", {"reason", "missing_regions", "reopen_condition", "source_binding_sha256"}, transition)
            require(payload["source_binding_sha256"] == sha256_bytes(canonical_json(execution["window_source_binding"])) and isinstance(payload["missing_regions"], list) and payload["missing_regions"], "planning_block_invalid", "Block source/regions invalid")
            candidate["phase"] = "window_planning_blocked"; candidate["active_window"]["planning_block"] = copy.deepcopy(payload)
        elif transition == "WINDOW_PLANNING_RESUME":
            require(execution["phase"] == "window_planning_blocked", "transition_blocked", "Planning resume requires blocked planning")
            _payload(payload, "math-research-window-planning-resume/v13", {"source_binding_sha256", "release_evidence_refs"}, transition)
            require(payload["source_binding_sha256"] == sha256_bytes(canonical_json(execution["window_source_binding"])) and isinstance(payload["release_evidence_refs"], list) and payload["release_evidence_refs"], "planning_resume_invalid", "Resume cannot rebase source and needs evidence")
            candidate["phase"] = "window_planning"; candidate["active_window"].pop("planning_block", None)
        else:
            require(execution["phase"] in {"window_planning", "window_planning_blocked"}, "transition_blocked", "Supersede requires unactivated planning")
            _payload(payload, "math-research-window-planning-supersede/v13", {"reason", "superseded_proposed_attempt_ids", "zero_attempts_committed", "planning_closure"}, transition)
            validate_pointer(payload["planning_closure"], "planning closure")
            require(payload["superseded_proposed_attempt_ids"] == execution["active_window"]["proposed_attempt_ids"] and payload["zero_attempts_committed"] is True and execution["counters"] == execution["active_window"]["counter_snapshot"], "planning_supersede_invalid", "Supersede must close exact IDs at zero count")
            _clear_active(candidate, "window_idle")
    elif transition == "ATTEMPT_START_PREPARE":
        require(execution["phase"] == "window_planning", "transition_blocked", "Prepare requires planning")
        validate_prepare_record(payload, project_id=project["project_id"], objective_commitment=project["objective_commitment_sha256"])
        require(payload["window_id"] == execution["active_window"]["window_id"] and payload["proposed_attempt_id"] in execution["active_window"]["proposed_attempt_ids"], "prepare_binding_mismatch", "Prepare window/ID differs")
        return {"schema": "math-research-transition-plan/v13", "transition": transition, "authority": "none", "expected_project_head_sha256": status["project_head_sha256"], "expected_execution_head_sha256": project["execution_state_head"]["sha256"], "expected_research_authority_head_sha256": project["research_authority_head"]["sha256"], "payload_sha256": sha256_bytes(canonical_json(payload)), "candidate_execution_head": execution, "candidate_research_authority_head": None, "candidate_project": None, "prepare_record_sha256": sha256_bytes(canonical_json(payload))}
    elif transition == "WINDOW_ACTIVATE":
        require(execution["phase"] == "window_planning", "transition_blocked", "Activation requires planning")
        _payload(payload, "math-research-window-activate/v13", {"prepare_records", "activation_receipt"}, transition)
        prepares = payload["prepare_records"]
        require(isinstance(prepares, list) and len(prepares) == 3, "activation_requires_three", "Exactly three prepares required")
        for item in prepares: validate_prepare_record(item, project_id=project["project_id"], objective_commitment=project["objective_commitment_sha256"])
        hashes = [sha256_bytes(canonical_json(x)) for x in prepares]; source_sha = sha256_bytes(canonical_json(execution["window_source_binding"])); portfolio_sha = sha256_bytes(canonical_json(execution["route_portfolio"]))
        members = {m["member_id"]: m for m in execution["route_portfolio"]["members"]}
        require(len(set(hashes)) == 3 and {x["proposed_attempt_id"] for x in prepares} == set(execution["active_window"]["proposed_attempt_ids"]) and {x["portfolio_member_id"] for x in prepares} == set(members), "activation_group_mismatch", "Prepare group differs from planning")
        for item in prepares:
            require(item["window_id"] == execution["active_window"]["window_id"] and item["source_binding_sha256"] == source_sha and item["portfolio_sha256"] == portfolio_sha and item["budget"] == members[item["portfolio_member_id"]]["budget"] and item["route_card_contract"]["semantic_fingerprint"] == members[item["portfolio_member_id"]]["semantic_fingerprint"], "activation_binding_mismatch", "Prepare binding/budget/fingerprint differs")
        before = execution["counters"]; after = copy.deepcopy(before); after["internal_attempts_started"] += 3
        receipt = payload["activation_receipt"]; rfields = {"schema", "window_id", "expected_project_head_sha256", "expected_execution_head_sha256", "source_binding_sha256", "portfolio_sha256", "prepare_sha256s", "counter_before", "counter_after", "candidate_execution_manifest_sha256"}
        closed(receipt, rfields, "activation_receipt_invalid", "activation receipt")
        manifest = {"schema": "math-research-window-activation-manifest/v13", "expected_execution_head_sha256": project["execution_state_head"]["sha256"], "source_binding_sha256": source_sha, "portfolio_sha256": portfolio_sha, "prepare_sha256s": hashes, "counter_after": after}
        require(receipt["schema"] == "math-research-window-activation-receipt/v13" and receipt["window_id"] == execution["active_window"]["window_id"] and receipt["expected_project_head_sha256"] == status["project_head_sha256"] and receipt["expected_execution_head_sha256"] == project["execution_state_head"]["sha256"] and receipt["source_binding_sha256"] == source_sha and receipt["portfolio_sha256"] == portfolio_sha and receipt["prepare_sha256s"] == hashes and receipt["counter_before"] == before and receipt["counter_after"] == after and receipt["candidate_execution_manifest_sha256"] == sha256_bytes(canonical_json(manifest)), "activation_receipt_mismatch", "Activation receipt differs")
        candidate["phase"] = "window_running"; candidate["active_window"]["activation_receipt"] = receipt; candidate["counters"] = after
        candidate["queue"] = [copy.deepcopy(x["queue_item_contract"]) | {"object": copy.deepcopy(x["queue_item"]), "attempt_id": x["proposed_attempt_id"], "status": "solver_running"} for x in prepares]
        candidate["route_decisions"] = [copy.deepcopy(x["route_decision"]) | {"attempt_id": x["proposed_attempt_id"]} for x in prepares]
        candidate["cognition"] = [copy.deepcopy(x["cognition"]) | {"attempt_id": x["proposed_attempt_id"]} for x in prepares]
        candidate["capsules"] = [copy.deepcopy(x["capsule_contract"]) | {"object": copy.deepcopy(x["capsule"]), "attempt_id": x["proposed_attempt_id"]} for x in prepares]
        candidate["active_attempts"] = []
        for item in prepares:
            member = members[item["portfolio_member_id"]]
            candidate["active_attempts"].append({"attempt_id": item["proposed_attempt_id"], "portfolio_member_id": item["portfolio_member_id"], "prepare_sha256": sha256_bytes(canonical_json(item)), "source_binding_sha256": source_sha, "portfolio_sha256": portfolio_sha, "route_decision_sha256": item["route_decision"]["sha256"], "ticket_sha256": item["ticket"]["sha256"], "cognition_sha256": item["cognition"]["sha256"], "selected_rendering_sha256": item["selected_rendering"]["sha256"], "route_card_sha256": item["route_card"]["sha256"], "semantic_fingerprint": member["semantic_fingerprint"], "evidence_standard_sha256": item["route_card_contract"]["evidence_standard_sha256"], "activation_receipt_sha256": sha256_bytes(canonical_json(receipt)), "status": "solver_running", "last_capsule_sha256": item["capsule"]["sha256"], "last_verified_checkpoint": None, "closing": None, "verification": None, "repair_count": 0, "package": None})
        if candidate["window_source_binding"]["kind"] == "genesis_objective": candidate["window_source_binding"]["consumed"] = True
    elif transition == "CHECKPOINT":
        require(execution["phase"] in {"window_running", "attempt_closing", "window_verifying"}, "transition_blocked", "Checkpoint requires active window")
        _payload(payload, "math-research-checkpoint/v13", {"attempt_id", "frozen_bindings", "prior_capsule_sha256", "successor_capsule", "successor_capsule_contract", "last_verified_checkpoint"}, transition)
        attempt = _attempt(execution, payload["attempt_id"]); require(attempt["status"] == "solver_running", "checkpoint_after_closing", "Closing attempt cannot checkpoint")
        expected = {k: attempt[k] for k in ("source_binding_sha256", "portfolio_sha256", "route_decision_sha256", "cognition_sha256", "selected_rendering_sha256", "route_card_sha256", "semantic_fingerprint", "evidence_standard_sha256")}
        require(payload["frozen_bindings"] == expected and payload["prior_capsule_sha256"] == attempt["last_capsule_sha256"], "checkpoint_semantic_change", "Checkpoint changed frozen semantics")
        validate_pointer(payload["successor_capsule"], "successor capsule"); validate_pointer(payload["last_verified_checkpoint"], "last verified checkpoint")
        capsule = payload["successor_capsule_contract"]
        # The successor binds the original route-card hash, not this reconstruction's prose gates.
        closed(capsule, {"schema", "project_id", "window_id", "proposed_attempt_id", "objective_commitment_sha256", "cognition_sha256", "selected_rendering_sha256", "route_card_sha256", "semantic_fingerprint", "local_position", "open_questions", "generation", "previous_capsule_sha256"}, "capsule_invalid", "successor capsule")
        require(capsule["schema"] == "math-research-continuity-capsule/v13" and capsule["project_id"] == project["project_id"] and capsule["window_id"] == execution["active_window"]["window_id"] and capsule["proposed_attempt_id"] == attempt["attempt_id"] and capsule["objective_commitment_sha256"] == project["objective_commitment_sha256"] and capsule["cognition_sha256"] == attempt["cognition_sha256"] and capsule["selected_rendering_sha256"] == attempt["selected_rendering_sha256"] and capsule["route_card_sha256"] == attempt["route_card_sha256"] and capsule["semantic_fingerprint"] == attempt["semantic_fingerprint"] and capsule["previous_capsule_sha256"] == attempt["last_capsule_sha256"] and payload["successor_capsule"]["sha256"] == sha256_bytes(canonical_json(capsule)), "capsule_binding_mismatch", "Checkpoint successor capsule changed frozen bindings or lineage")
        changed = copy.deepcopy(attempt); changed["last_capsule_sha256"] = payload["successor_capsule"]["sha256"]; changed["last_verified_checkpoint"] = payload["last_verified_checkpoint"]
        candidate["active_attempts"] = _replace(candidate["active_attempts"], "attempt_id", payload["attempt_id"], changed)
        candidate["capsules"] = _replace(candidate["capsules"], "attempt_id", payload["attempt_id"], copy.deepcopy(capsule) | {"object": copy.deepcopy(payload["successor_capsule"]), "attempt_id": payload["attempt_id"]})
    elif transition in {"SEMANTIC_RESET", "ATTEMPT_CLOSE"}:
        require(execution["phase"] in {"window_running", "attempt_closing", "window_verifying", "window_invalidated"}, "transition_blocked", "Attempt close requires active window")
        fields = {"attempt_id", "closing_reason", "outcome", "candidate", "dependencies", "artifact_refs", "evidence_refs", "final_capsule", "budget_usage", "semantic_reset_directive", "cannot_imply", "reopen_conditions"}
        _payload(payload, "math-research-attempt-closing/v13", fields, transition); attempt = _attempt(execution, payload["attempt_id"])
        require(attempt["status"] == "solver_running" and payload["outcome"] in OUTCOMES, "attempt_not_closable", "Attempt status/outcome invalid")
        validate_pointer(payload["candidate"], "candidate", nullable=True); validate_pointer_list(payload["dependencies"], "dependencies"); validate_attempt_package_preflight_ref(payload["artifact_refs"]); validate_pointer(payload["final_capsule"], "final capsule"); validate_budget(payload["budget_usage"])
        require(isinstance(payload["evidence_refs"], list) and isinstance(payload["cannot_imply"], list) and payload["cannot_imply"] and isinstance(payload["reopen_conditions"], list) and payload["reopen_conditions"], "closing_invalid", "Closing evidence/boundaries invalid")
        if transition == "SEMANTIC_RESET": require(isinstance(payload["semantic_reset_directive"], dict) and payload["semantic_reset_directive"].get("successor_attempt_forbidden_in_window") is True, "semantic_reset_invalid", "Semantic reset must forbid in-window successor")
        else: require(payload["semantic_reset_directive"] is None, "semantic_reset_invalid", "Ordinary close cannot carry semantic reset")
        changed = copy.deepcopy(attempt); changed["status"] = "closing"; changed["closing"] = copy.deepcopy(payload); changed["last_capsule_sha256"] = payload["final_capsule"]["sha256"]
        candidate["active_attempts"] = _replace(candidate["active_attempts"], "attempt_id", payload["attempt_id"], changed); candidate["phase"] = "window_invalidated" if execution["phase"] == "window_invalidated" else "attempt_closing"
    elif transition == "QUEUED_PREFLIGHT_REBIND":
        require(execution["phase"] == "window_verifying", "transition_blocked", "Queued preflight rebind requires window_verifying")
        _payload(payload, "math-research-queued-preflight-rebind/v13", {"window_id", "expected_execution_head_sha256", "compatibility_reason", "rebinds"}, transition)
        require(payload["window_id"] == execution["active_window"]["window_id"] and payload["expected_execution_head_sha256"] == project["execution_state_head"]["sha256"], "queued_preflight_rebind_binding_mismatch", "Compatibility migration window/head binding differs")
        require(payload["compatibility_reason"] == "v13-attempt-package-preflight-backfill", "queued_preflight_rebind_reason_invalid", "Compatibility migration reason is not the registered one-time backfill")
        attempts = execution["active_attempts"]; queues = execution["verification_queue"]; rebinds = payload["rebinds"]
        require(len(attempts) == 3 and all(x["status"] == "verification_queued" and x["verification"] is None and x["package"] is None and x["repair_count"] == 0 for x in attempts) and execution["repair_count"] == 0, "queued_preflight_rebind_not_legacy", "Compatibility migration requires exactly three unrepaired queued legacy attempts")
        require(isinstance(rebinds, list) and len(rebinds) == 3 and {x.get("attempt_id") for x in rebinds if isinstance(x, dict)} == {x["attempt_id"] for x in attempts}, "queued_preflight_rebind_incomplete", "Compatibility migration must atomically rebind all three attempts exactly once")
        require(len(queues) == 3 and {x.get("attempt_id") for x in queues} == {x["attempt_id"] for x in attempts} and all(x.get("status") == "queued" for x in queues), "queued_preflight_rebind_queue_invalid", "Compatibility migration requires one live legacy verifier queue item per attempt")
        rebound = []
        rfields = {"attempt_id", "old_candidate_sha256", "old_dependency_sha256s", "old_verifier_ticket_sha256", "new_candidate", "new_dependencies", "new_artifact_refs", "frozen_semantics"}
        frozen_keys = ("source_binding_sha256", "portfolio_sha256", "route_decision_sha256", "cognition_sha256", "selected_rendering_sha256", "route_card_sha256", "semantic_fingerprint", "evidence_standard_sha256")
        for row in rebinds:
            closed(row, rfields, "queued_preflight_rebind_invalid", "queued preflight rebind row")
            attempt = _attempt(execution, row["attempt_id"]); queue = [x for x in queues if x.get("attempt_id") == row["attempt_id"]]
            require(len(queue) == 1 and attempt["closing"]["candidate"] is not None, "queued_preflight_rebind_queue_invalid", "Legacy candidate has no unique verifier queue item")
            old_receipts = [ref for ref in attempt["closing"]["artifact_refs"] if ref["path"].endswith("/attempt-package-preflight.json")]
            require(not old_receipts, "queued_preflight_rebind_not_legacy", "Receipt-bound or already migrated attempts cannot use compatibility rebind")
            q = queue[0]; old_dependencies = [x["sha256"] for x in attempt["closing"]["dependencies"]]
            require(row["old_candidate_sha256"] == attempt["closing"]["candidate"]["sha256"] == q["candidate_sha256"] and row["old_dependency_sha256s"] == old_dependencies == q["dependency_sha256s"] and row["old_verifier_ticket_sha256"] == q["verifier_ticket"]["sha256"], "queued_preflight_rebind_lineage_mismatch", "Legacy queue/candidate/dependency/ticket lineage differs")
            frozen = {key: attempt[key] for key in frozen_keys}
            require(row["frozen_semantics"] == frozen, "queued_preflight_rebind_semantic_change", "Compatibility migration changed frozen semantics")
            validate_pointer(row["new_candidate"], "new candidate"); validate_pointer_list(row["new_dependencies"], "new dependencies"); validate_attempt_package_preflight_ref(row["new_artifact_refs"])
            changed = copy.deepcopy(attempt); changed["status"] = "closing"; changed["verification"] = None; changed["closing"]["candidate"] = copy.deepcopy(row["new_candidate"]); changed["closing"]["dependencies"] = copy.deepcopy(row["new_dependencies"]); changed["closing"]["artifact_refs"] = copy.deepcopy(row["new_artifact_refs"])
            rebound.append(changed)
        candidate["active_attempts"] = rebound; candidate["verification_queue"] = []; candidate["phase"] = "attempt_closing"
    elif transition in {"VERIFICATION_QUEUE", "VERIFICATION_RESULT", "LIMITED_REPAIR"}:
        if transition == "VERIFICATION_QUEUE":
            require(execution["phase"] in {"attempt_closing", "window_verifying"}, "transition_blocked", "Queue requires closing")
            _payload(payload, "math-research-verification-queue/v13", {"attempt_id", "verifier_ticket", "candidate_sha256", "dependency_sha256s", "independence_mode", "consumer_principal"}, transition)
            attempt = _attempt(execution, payload["attempt_id"]); require(attempt["status"] == "closing" and attempt["closing"]["candidate"] is not None, "verification_candidate_missing", "Frozen candidate missing")
            validate_pointer(payload["verifier_ticket"], "verifier ticket")
            require(payload["candidate_sha256"] == attempt["closing"]["candidate"]["sha256"] and payload["dependency_sha256s"] == [x["sha256"] for x in attempt["closing"]["dependencies"]] and payload["independence_mode"] in {"independent_agent", "context_isolated_single_agent"} and payload["consumer_principal"] == "verifier", "verification_binding_mismatch", "Verification binding/principal invalid")
            changed = copy.deepcopy(attempt); changed["status"] = "verification_queued"; candidate["active_attempts"] = _replace(candidate["active_attempts"], "attempt_id", payload["attempt_id"], changed); candidate["verification_queue"].append(copy.deepcopy(payload) | {"status": "queued"}); candidate["phase"] = "window_verifying"
        elif transition == "VERIFICATION_RESULT":
            require(execution["phase"] == "window_verifying", "transition_blocked", "Result requires verifying")
            _payload(payload, "math-research-verification-result/v13", {"attempt_id", "verifier_ticket_sha256", "candidate_sha256", "dependency_sha256s", "verdict", "checked_scope", "earliest_error", "unresolved", "context_isolated"}, transition)
            attempt = _attempt(execution, payload["attempt_id"]); queue = [x for x in execution["verification_queue"] if x.get("attempt_id") == payload["attempt_id"]]
            require(len(queue) == 1 and attempt["status"] == "verification_queued", "verification_not_queued", "No unique verification queue item")
            q = queue[0]; require(payload["verifier_ticket_sha256"] == q["verifier_ticket"]["sha256"] and payload["candidate_sha256"] == q["candidate_sha256"] and payload["dependency_sha256s"] == q["dependency_sha256s"] and payload["verdict"] in VERDICTS and payload["context_isolated"] is True, "verification_result_invalid", "Verification result binding invalid")
            require((payload["verdict"] == "FAIL") == isinstance(payload["earliest_error"], str), "verification_result_invalid", "FAIL needs earliest_error only")
            changed = copy.deepcopy(attempt); changed["status"] = "verification_complete"; changed["verification"] = copy.deepcopy(payload); candidate["active_attempts"] = _replace(candidate["active_attempts"], "attempt_id", payload["attempt_id"], changed)
            candidate["verification_queue"] = [copy.deepcopy(x) | ({"status": "complete"} if x.get("attempt_id") == payload["attempt_id"] else {}) for x in candidate["verification_queue"]]
        else:
            require(execution["phase"] == "window_verifying", "transition_blocked", "Repair requires verifying")
            _payload(payload, "math-research-limited-repair/v13", {"attempt_id", "repair_ticket", "old_candidate_sha256", "new_candidate", "new_dependencies", "new_artifact_refs", "frozen_semantics"}, transition)
            attempt = _attempt(execution, payload["attempt_id"]); require(attempt["status"] == "verification_complete" and attempt["verification"]["verdict"] == "FAIL" and attempt["repair_count"] == 0, "repair_not_permitted", "Only one repair after FAIL")
            validate_pointer(payload["repair_ticket"], "repair ticket"); validate_pointer(payload["new_candidate"], "new candidate"); validate_pointer_list(payload["new_dependencies"], "new dependencies"); validate_attempt_package_preflight_ref(payload["new_artifact_refs"])
            frozen = {k: attempt[k] for k in ("source_binding_sha256", "portfolio_sha256", "route_decision_sha256", "semantic_fingerprint", "evidence_standard_sha256")}
            require(payload["old_candidate_sha256"] == attempt["closing"]["candidate"]["sha256"] and payload["frozen_semantics"] == frozen, "repair_semantic_change", "Repair changed candidate lineage or semantics")
            changed = copy.deepcopy(attempt); changed["status"] = "closing"; changed["repair_count"] = 1; changed["verification"] = None; changed["closing"]["candidate"] = payload["new_candidate"]; changed["closing"]["dependencies"] = payload["new_dependencies"]; changed["closing"]["artifact_refs"] = payload["new_artifact_refs"]
            candidate["active_attempts"] = _replace(candidate["active_attempts"], "attempt_id", payload["attempt_id"], changed); candidate["verification_queue"] = [x for x in candidate["verification_queue"] if x.get("attempt_id") != payload["attempt_id"]]; candidate["repair_count"] += 1; candidate["phase"] = "attempt_closing"
    elif transition == "ATTEMPT_END":
        require(execution["phase"] in {"attempt_closing", "window_verifying", "window_invalidated"}, "transition_blocked", "ATTEMPT_END requires closing/verifying/invalidated")
        _payload(payload, "math-research-attempt-end/v13", {"attempt_id", "package", "close_receipt"}, transition); attempt = _attempt(execution, payload["attempt_id"])
        require(attempt["status"] in {"closing", "verification_complete"}, "attempt_not_closable", "Attempt not closable")
        package = payload["package"]; pfields = {"schema", "attempt_id", "window_id", "source_binding_sha256", "portfolio_member_id", "route_decision_sha256", "outcome", "artifact_refs", "evidence_refs", "verification", "final_capsule", "route_delta", "result_proposals", "obstacles", "cannot_imply", "reopen_conditions", "budget_usage", "semantic_reset_directive", "source_invalidated", "promotion_eligible"}
        closed(package, pfields, "package_invalid", "reconciliation package")
        require(package["schema"] == "math-research-attempt-reconciliation-package/v13" and package["attempt_id"] == attempt["attempt_id"] and package["window_id"] == execution["active_window"]["window_id"] and package["source_binding_sha256"] == attempt["source_binding_sha256"] and package["portfolio_member_id"] == attempt["portfolio_member_id"] and package["route_decision_sha256"] == attempt["route_decision_sha256"] and package["outcome"] == attempt["closing"]["outcome"], "package_binding_mismatch", "Package binding differs")
        validate_attempt_package_preflight_ref(package["artifact_refs"]); validate_pointer(package["final_capsule"], "package capsule"); validate_budget(package["budget_usage"])
        require(package["artifact_refs"] == attempt["closing"]["artifact_refs"], "package_preflight_lineage_mismatch", "ATTEMPT_END package must preserve the frozen preflight-bound artifact refs")
        for key in ("evidence_refs", "route_delta", "result_proposals", "obstacles", "cannot_imply", "reopen_conditions"): require(isinstance(package[key], list), "package_invalid", f"{key} invalid")
        require(isinstance(package["source_invalidated"], bool) and isinstance(package["promotion_eligible"], bool), "package_invalid", "Package flags invalid")
        pass_bound = attempt["verification"] is not None and attempt["verification"]["verdict"] == "PASS" and package["verification"] == attempt["verification"]
        proposed_knowledge = bool(package["route_delta"] or package["result_proposals"])
        if pass_bound and not package["source_invalidated"]: require(proposed_knowledge, "verified_knowledge_missing", "A source-valid PASS package must preserve verified knowledge as route_delta or result_proposals")
        expected_promotion_eligible = pass_bound and not package["source_invalidated"] and proposed_knowledge
        require(package["promotion_eligible"] is expected_promotion_eligible, "promotion_eligibility_mismatch", "promotion_eligible must be derived from a source-valid bound PASS and explicit reconciliation knowledge")
        if package["source_invalidated"]: require(package["promotion_eligible"] is False, "source_invalidated_promotion", "Invalidated source cannot promote")
        if execution["phase"] == "window_invalidated": require(package["source_invalidated"] is True and package["promotion_eligible"] is False, "invalidated_window_package_invalid", "Packages closed after invalidation must be explicitly ineligible")
        if package["promotion_eligible"]: require(attempt["verification"] is not None and attempt["verification"]["verdict"] == "PASS" and package["verification"] == attempt["verification"], "promotion_without_pass", "Promotion needs bound PASS")
        receipt = payload["close_receipt"]; closed(receipt, {"schema", "attempt_id", "package_sha256", "completed_counter_before", "completed_counter_after"}, "close_receipt_invalid", "close receipt")
        before = execution["counters"]["internal_attempts_completed"]
        require(receipt["schema"] == "math-research-attempt-close-receipt/v13" and receipt["attempt_id"] == attempt["attempt_id"] and receipt["package_sha256"] == sha256_bytes(canonical_json(package)) and receipt["completed_counter_before"] == before and receipt["completed_counter_after"] == before + 1, "close_receipt_invalid", "Close receipt differs")
        changed = copy.deepcopy(attempt); changed["status"] = "package_ready"; changed["package"] = copy.deepcopy(package) | {"sha256": receipt["package_sha256"]}
        candidate["active_attempts"] = _replace(candidate["active_attempts"], "attempt_id", payload["attempt_id"], changed); candidate["queue"] = [copy.deepcopy(x) | ({"status": "package_ready"} if x.get("attempt_id") == payload["attempt_id"] else {}) for x in candidate["queue"]]; candidate["verification_queue"] = [x for x in candidate["verification_queue"] if x.get("attempt_id") != payload["attempt_id"]]
        candidate["counters"]["internal_attempts_completed"] += 1; candidate["counters"]["attempts_since_route_review"] += 1; candidate["phase"] = "window_invalidated" if execution["phase"] == "window_invalidated" else "window_verifying"
    elif transition in {"WINDOW_RECONCILE", "WINDOW_RECONCILIATION_FAIL", "WINDOW_CLOSE"}:
        packages = [x.get("package") for x in execution["active_attempts"]]
        if transition != "WINDOW_CLOSE": require(len(packages) == 3 and all(x and x.get("sha256") for x in packages) and len({x["sha256"] for x in packages}) == 3, "reconciliation_incomplete", "Three distinct packages required")
        if transition == "WINDOW_RECONCILE":
            require(execution["phase"] in {"window_running", "window_verifying", "window_reconciling"}, "transition_blocked", "Reconcile requires active complete window")
            require(not execution["source_invalidations"], "source_invalidated_reconciliation", "A source-invalidated window must use source-integrity reconciliation")
            fields = {"package_sha256s", "new_math_performed", "conflict_set", "candidate_research_authority_head", "candidate_manifest", "map_validation_receipt", "semantic_review_receipt", "reconciliation_receipt"}
            _payload(payload, "math-research-window-reconciliation/v13", fields, transition)
            require(payload["package_sha256s"] == [x["sha256"] for x in packages] and payload["new_math_performed"] is False and isinstance(payload["conflict_set"], list), "reconciliation_binding_mismatch", "Reconciliation binding/new-math invalid")
            for key in fields - {"package_sha256s", "new_math_performed", "conflict_set"}: validate_pointer(payload[key], key)
            if any(x.get("promotion_eligible") is True for x in packages): require(payload["candidate_research_authority_head"] != project["research_authority_head"], "promotable_knowledge_not_reconciled", "Promotion-eligible packages require a new research authority head with updated memory, route review, and map")
            _require_candidate_map_review(root, project, payload["candidate_research_authority_head"], payload["semantic_review_receipt"])
            candidate["phase"] = "window_reconciling"; candidate["active_window"]["reconciliation"] = copy.deepcopy(payload)
        elif transition == "WINDOW_RECONCILIATION_FAIL":
            require(execution["phase"] in {"window_running", "window_verifying", "window_reconciling"}, "transition_blocked", "Failure requires reconciliation context")
            _payload(payload, "math-research-window-reconciliation-failure/v13", {"package_sha256s", "new_math_required", "failure_receipt", "review_gate"}, transition)
            validate_pointer(payload["failure_receipt"], "failure receipt"); validate_review_gate(payload["review_gate"])
            require(payload["package_sha256s"] == [x["sha256"] for x in packages] and payload["review_gate"]["owner_lifecycle"] == "window_reconciliation", "reconciliation_failure_invalid", "Failure binding/gate invalid")
            candidate["phase"] = "window_reconciling"; candidate["review_required"].append(payload["review_gate"]); candidate["active_window"]["reconciliation_failure"] = copy.deepcopy(payload)
        else:
            require(execution["phase"] == "window_reconciling" and execution["active_window"].get("reconciliation"), "transition_blocked", "Window close needs successful reconciliation")
            _payload(payload, "math-research-window-close/v13", {"reconciliation_receipt_sha256", "candidate_research_authority_head", "candidate_execution_state_head", "queue_clear_proof", "terminal_candidate"}, transition)
            recon = execution["active_window"]["reconciliation"]; validate_pointer(payload["candidate_research_authority_head"], "candidate authority"); validate_pointer(payload["candidate_execution_state_head"], "candidate execution")
            require(payload["reconciliation_receipt_sha256"] == recon["reconciliation_receipt"]["sha256"] and payload["candidate_research_authority_head"] == recon["candidate_research_authority_head"] and payload["queue_clear_proof"] is True, "window_close_binding_mismatch", "Close binding/queue proof invalid")
            _require_candidate_map_review(root, project, payload["candidate_research_authority_head"], recon["semantic_review_receipt"])
            if payload["terminal_candidate"] is not None:
                closed(payload["terminal_candidate"], {"candidate", "dependencies", "completion_candidate_sha256"}, "terminal_candidate_invalid", "terminal candidate"); validate_pointer(payload["terminal_candidate"]["candidate"], "terminal candidate"); validate_pointer_list(payload["terminal_candidate"]["dependencies"], "terminal dependencies"); valid_hash(payload["terminal_candidate"]["completion_candidate_sha256"], "terminal_candidate_invalid", "completion candidate")
            candidate_research = payload["candidate_research_authority_head"]; _clear_active(candidate, "completion_pending" if payload["terminal_candidate"] else "window_idle")
            candidate["counters"]["route_reviews"] += 1; candidate["counters"]["attempts_since_route_review"] = 0; candidate["counters"]["route_review_due"] = False
            if payload["terminal_candidate"]: candidate["terminal_audits"] = [{"status": "candidate_frozen", **copy.deepcopy(payload["terminal_candidate"]), "audits": {}}]
            require(payload["candidate_execution_state_head"]["sha256"] == sha256_bytes(canonical_json(candidate)), "candidate_execution_binding_mismatch", "Closing project pointer does not bind candidate execution bytes")
            candidate_project = copy.deepcopy(project); candidate_project["research_authority_head"] = candidate_research; candidate_project["execution_state_head"] = payload["candidate_execution_state_head"]; candidate_project["generation"] += 1; authority = "both"
    elif transition in {"SUSPEND", "RESUME", "SOURCE_REVIEW_START", "SOURCE_REVIEW_CONFIRM", "SOURCE_INVALIDATE", "SOURCE_INTEGRITY_RECONCILE"}:
        if transition == "SUSPEND":
            require(execution["phase"] in ACTIVE_PHASES - {"window_suspended"}, "transition_blocked", "Suspend requires active work")
            _payload(payload, "math-research-window-suspend/v13", {"resume_capsule", "frozen_state_sha256", "reason"}, transition); validate_pointer(payload["resume_capsule"], "resume capsule")
            frozen = copy.deepcopy(execution); frozen["generation"] = 0; frozen["last_transition"] = ""
            require(payload["frozen_state_sha256"] == sha256_bytes(canonical_json(frozen)), "suspend_binding_mismatch", "Suspend digest differs")
            candidate["active_window"]["suspended_from"] = execution["phase"]; candidate["active_window"]["resume_capsule"] = payload["resume_capsule"]; candidate["phase"] = "window_suspended"
        elif transition == "RESUME":
            require(execution["phase"] == "window_suspended", "transition_blocked", "Resume requires suspended window")
            _payload(payload, "math-research-window-resume/v13", {"resume_capsule_sha256", "integrity_check", "frozen_bindings_unchanged"}, transition)
            require(payload["resume_capsule_sha256"] == execution["active_window"]["resume_capsule"]["sha256"] and payload["integrity_check"] is True and payload["frozen_bindings_unchanged"] is True, "resume_integrity_failed", "Resume integrity failed")
            candidate["phase"] = execution["active_window"]["suspended_from"]; candidate["active_window"]["suspended_from"] = None; candidate["active_window"]["resume_capsule"] = None
        elif transition == "SOURCE_REVIEW_START":
            require(execution["phase"] in ACTIVE_PHASES - {"source_integrity_review", "window_invalidated"}, "transition_blocked", "Source review requires active window")
            _payload(payload, "math-research-source-review-start/v13", {"source_binding_sha256", "review_ticket", "review_gate"}, transition); validate_pointer(payload["review_ticket"], "review ticket"); validate_review_gate(payload["review_gate"])
            require(payload["source_binding_sha256"] == sha256_bytes(canonical_json(execution["window_source_binding"])) and payload["review_gate"]["owner_lifecycle"] == "source_integrity_review", "source_review_invalid", "Source review binding/gate invalid")
            candidate["active_window"]["source_review_return_phase"] = execution["phase"]; candidate["phase"] = "source_integrity_review"; candidate["review_required"].append(payload["review_gate"])
        elif transition == "SOURCE_REVIEW_CONFIRM":
            require(execution["phase"] == "source_integrity_review", "transition_blocked", "Confirm requires source review")
            _payload(payload, "math-research-source-review-confirm/v13", {"review_receipt", "source_binding_sha256", "gate_release_evidence_refs"}, transition); validate_pointer(payload["review_receipt"], "review receipt")
            require(payload["source_binding_sha256"] == sha256_bytes(canonical_json(execution["window_source_binding"])) and isinstance(payload["gate_release_evidence_refs"], list) and payload["gate_release_evidence_refs"], "source_review_release_invalid", "Confirm binding/evidence invalid")
            candidate["review_required"] = [g for g in candidate["review_required"] if g["owner_lifecycle"] != "source_integrity_review"]; candidate["phase"] = execution["active_window"]["source_review_return_phase"]; candidate["active_window"]["source_review_return_phase"] = None
        elif transition == "SOURCE_INVALIDATE":
            require(execution["phase"] == "source_integrity_review", "transition_blocked", "Invalidate requires source review")
            _payload(payload, "math-research-source-invalidation/v13", {"review_receipt", "source_binding_sha256", "dependency_closure", "invalidation_id"}, transition); validate_pointer(payload["review_receipt"], "invalidation receipt")
            require(payload["source_binding_sha256"] == sha256_bytes(canonical_json(execution["window_source_binding"])) and isinstance(payload["dependency_closure"], list), "source_invalidation_invalid", "Invalidation binding/closure invalid")
            candidate["source_invalidations"].append(copy.deepcopy(payload)); candidate["phase"] = "window_invalidated"
        else:
            require(execution["phase"] == "window_invalidated", "transition_blocked", "Source reconciliation requires invalidated window")
            fields = {"new_math_performed", "candidate_research_authority_head", "candidate_execution_state_head", "withdrawals", "dependency_impact", "queue_clear_proof", "semantic_review_receipt", "close_receipt"}
            _payload(payload, "math-research-source-integrity-reconciliation/v13", fields, transition)
            packages = [x.get("package") for x in execution["active_attempts"]]
            require(len(packages) == 3 and all(x and is_sha256(x.get("sha256")) for x in packages), "source_reconciliation_incomplete", "Invalidated window must first produce three immutable closing packages")
            require(payload["new_math_performed"] is False and payload["queue_clear_proof"] is True and isinstance(payload["withdrawals"], list) and isinstance(payload["dependency_impact"], list), "source_reconciliation_invalid", "Source reconciliation invalid")
            validate_pointer(payload["candidate_research_authority_head"], "candidate authority"); validate_pointer(payload["candidate_execution_state_head"], "candidate execution"); validate_pointer(payload["semantic_review_receipt"], "semantic review"); validate_pointer(payload["close_receipt"], "close receipt")
            _require_candidate_map_review(root, project, payload["candidate_research_authority_head"], payload["semantic_review_receipt"])
            candidate_research = payload["candidate_research_authority_head"]; _clear_active(candidate, "window_idle"); candidate["review_required"] = [g for g in candidate["review_required"] if g["owner_lifecycle"] != "source_integrity_review"]
            require(payload["candidate_execution_state_head"]["sha256"] == sha256_bytes(canonical_json(candidate)), "candidate_execution_binding_mismatch", "Source close pointer does not bind candidate execution bytes")
            candidate_project = copy.deepcopy(project); candidate_project["research_authority_head"] = candidate_research; candidate_project["execution_state_head"] = payload["candidate_execution_state_head"]; candidate_project["generation"] += 1; authority = "both"
    elif transition in {"MAINTENANCE_START", "MAINTENANCE_RECONCILE", "MAINTENANCE_FAIL"}:
        if transition == "MAINTENANCE_START":
            require(execution["phase"] in {"window_idle", "completion_pending"}, "transition_blocked", "Maintenance starts only from idle/completion_pending")
            _payload(payload, "math-research-maintenance-start/v13", {"input_records", "reason", "origin_phase", "new_math_performed"}, transition); validate_pointer_list(payload["input_records"], "maintenance inputs")
            require(payload["origin_phase"] == execution["phase"] and payload["new_math_performed"] is False, "maintenance_invalid", "Maintenance origin/new-math invalid")
            candidate["phase"] = "maintenance"; candidate["terminal_audits"].append({"status": "maintenance", "origin_phase": execution["phase"], "start": copy.deepcopy(payload)})
        else:
            require(execution["phase"] == "maintenance", "transition_blocked", "Maintenance reconcile requires maintenance")
            fields = {"new_math_performed", "candidate_research_authority_head", "candidate_execution_state_head", "promotion_or_withdrawal", "dependency_impact", "semantic_review_receipt", "maintenance_receipt", "next_phase", "review_gate"}
            _payload(payload, "math-research-maintenance-reconciliation/v13", fields, transition); validate_pointer(payload["maintenance_receipt"], "maintenance receipt")
            require(payload["new_math_performed"] is False and isinstance(payload["promotion_or_withdrawal"], list) and isinstance(payload["dependency_impact"], list), "maintenance_invalid", "Maintenance decisions invalid")
            if transition == "MAINTENANCE_RECONCILE":
                require(payload["next_phase"] in {"window_idle", "completion_pending"} and payload["review_gate"] is None, "maintenance_invalid", "Successful maintenance next phase/gate invalid"); validate_pointer(payload["candidate_research_authority_head"], "candidate authority"); validate_pointer(payload["candidate_execution_state_head"], "candidate execution"); validate_pointer(payload["semantic_review_receipt"], "semantic review")
                _require_candidate_map_review(root, project, payload["candidate_research_authority_head"], payload["semantic_review_receipt"])
                candidate_research = payload["candidate_research_authority_head"]; candidate["phase"] = payload["next_phase"]
                require(payload["candidate_execution_state_head"]["sha256"] == sha256_bytes(canonical_json(candidate)), "candidate_execution_binding_mismatch", "Maintenance pointer does not bind candidate execution bytes")
                candidate_project = copy.deepcopy(project); candidate_project["research_authority_head"] = candidate_research; candidate_project["execution_state_head"] = payload["candidate_execution_state_head"]; candidate_project["generation"] += 1; authority = "both"
            else:
                require(payload["next_phase"] == "maintenance" and payload["candidate_research_authority_head"] is None and payload["candidate_execution_state_head"] is None and payload["semantic_review_receipt"] is None, "maintenance_failure_invalid", "Failed maintenance advanced authority"); validate_review_gate(payload["review_gate"]); require(payload["review_gate"]["owner_lifecycle"] == "maintenance_reconciliation", "maintenance_failure_invalid", "Maintenance gate owner invalid"); candidate["review_required"].append(payload["review_gate"])
    elif transition in {"TERMINAL_AUDIT_START", "TERMINAL_AUDIT_RESULT", "COMPLETION_PUBLISH"}:
        if transition == "TERMINAL_AUDIT_START":
            require(execution["phase"] == "completion_pending" and len(execution["terminal_audits"]) == 1 and execution["terminal_audits"][0].get("status") == "candidate_frozen", "transition_blocked", "Audit start requires frozen candidate")
            _payload(payload, "math-research-terminal-audit-start/v13", {"completion_candidate_sha256", "audit_tickets", "context_isolation"}, transition); terminal = execution["terminal_audits"][0]
            require(payload["completion_candidate_sha256"] == terminal["completion_candidate_sha256"] and isinstance(payload["audit_tickets"], dict) and set(payload["audit_tickets"]) == AUDIT_KINDS and payload["context_isolation"] is True, "terminal_audit_invalid", "Audit tickets/candidate invalid")
            for key, pointer in payload["audit_tickets"].items(): validate_pointer(pointer, f"audit ticket {key}")
            require(len({x["sha256"] for x in payload["audit_tickets"].values()}) == 3, "terminal_audit_invalid", "Audit tickets must be distinct")
            candidate["phase"] = "terminal_audit"; candidate["terminal_audits"][0]["status"] = "auditing"; candidate["terminal_audits"][0]["audit_tickets"] = copy.deepcopy(payload["audit_tickets"])
        elif transition == "TERMINAL_AUDIT_RESULT":
            require(execution["phase"] == "terminal_audit", "transition_blocked", "Audit result requires terminal_audit")
            _payload(payload, "math-research-terminal-audit-result/v13", {"audit_kind", "ticket_sha256", "completion_candidate_sha256", "verdict", "receipt", "impact_classification", "new_math_performed"}, transition); terminal = execution["terminal_audits"][0]
            require(payload["audit_kind"] in AUDIT_KINDS and payload["ticket_sha256"] == terminal["audit_tickets"][payload["audit_kind"]]["sha256"] and payload["completion_candidate_sha256"] == terminal["completion_candidate_sha256"] and payload["verdict"] in VERDICTS and payload["new_math_performed"] is False and payload["audit_kind"] not in terminal["audits"], "terminal_audit_invalid", "Audit result binding invalid"); validate_pointer(payload["receipt"], "audit receipt")
            candidate["terminal_audits"][0]["audits"][payload["audit_kind"]] = copy.deepcopy(payload); candidate["counters"]["terminal_audits"] += 1
            if payload["verdict"] != "PASS":
                require(payload["impact_classification"] in {"coverage", "soundness"}, "audit_impact_missing", "Non-PASS needs impact classification")
                if payload["impact_classification"] == "coverage": candidate["phase"] = "window_idle"; candidate["terminal_audits"] = []
                else: candidate["phase"] = "maintenance"; candidate["review_required"].append({"scope": "project", "owner_lifecycle": "maintenance_reconciliation", "blocked_transition": ["WINDOW_PLAN", "COMPLETION_PUBLISH"], "dependency_closure": [terminal["completion_candidate_sha256"]], "release_condition": "Quarantine and repair all soundness-affected authority", "evidence_refs": [payload["receipt"]["sha256"]]})
            else: require(payload["impact_classification"] is None, "audit_impact_invalid", "PASS cannot carry failure impact")
        else:
            require(execution["phase"] == "terminal_audit", "transition_blocked", "Completion requires terminal_audit")
            _payload(payload, "math-research-completion-publication/v13", {"completion_candidate_sha256", "terminal_summary", "completion_plan", "candidate_research_authority_head", "candidate_execution_state_head"}, transition); terminal = execution["terminal_audits"][0]; audits = terminal.get("audits", {})
            require(set(audits) == AUDIT_KINDS and all(audits[k]["verdict"] == "PASS" for k in AUDIT_KINDS) and payload["completion_candidate_sha256"] == terminal["completion_candidate_sha256"], "terminal_audit_incomplete", "Three PASS audits on one candidate required")
            validate_pointer(payload["terminal_summary"], "terminal summary"); validate_pointer(payload["completion_plan"], "completion plan"); validate_pointer(payload["candidate_research_authority_head"], "final authority"); validate_pointer(payload["candidate_execution_state_head"], "final execution")
            _require_candidate_map_review(root, project, payload["candidate_research_authority_head"])
            candidate["phase"] = "project_complete"; candidate["terminal_audits"][0]["status"] = "published"; candidate["terminal_audits"][0]["terminal_summary"] = payload["terminal_summary"]; candidate["terminal_audits"][0]["completion_plan"] = payload["completion_plan"]
            require(payload["candidate_execution_state_head"]["sha256"] == sha256_bytes(canonical_json(candidate)), "candidate_execution_binding_mismatch", "Final project pointer does not bind candidate execution bytes")
            candidate_research = payload["candidate_research_authority_head"]; candidate_project = copy.deepcopy(project); candidate_project["research_authority_head"] = candidate_research; candidate_project["execution_state_head"] = payload["candidate_execution_state_head"]; candidate_project["generation"] += 1; candidate_project["project_complete"] = True; candidate_project["pending_goal_update"] = True; authority = "both"
    else:
        raise V13Error("transition_unknown", f"Unknown transition {transition}")

    return {"schema": "math-research-transition-plan/v13", "transition": transition, "authority": authority, "expected_project_head_sha256": status["project_head_sha256"], "expected_execution_head_sha256": project["execution_state_head"]["sha256"], "expected_research_authority_head_sha256": project["research_authority_head"]["sha256"], "payload_sha256": sha256_bytes(canonical_json(payload)), "candidate_execution_head": candidate, "candidate_research_authority_head": candidate_research, "candidate_project": candidate_project}


def main() -> int:
    configure_stdio(); parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="command", required=True)
    startup = sub.add_parser("startup"); startup.add_argument("--project", type=Path, required=True)
    objective = sub.add_parser("objective-commitment"); objective.add_argument("--input", type=Path, required=True)
    prepare = sub.add_parser("prepare"); prepare.add_argument("--project", type=Path, required=True); prepare.add_argument("--transition", required=True); prepare.add_argument("--payload", type=Path, required=True); prepare.add_argument("--goal-state", required=True); prepare.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "startup": result = validate_project(args.project)
        elif args.command == "objective-commitment":
            value = load_json(args.input, canonical_required=True); raw = objective_bytes(value); result = {"ok": True, "objective_commitment_sha256": sha256_bytes(raw), "bytes": len(raw)}
        else:
            result = prepare_transition(args.project, args.transition, load_json(args.payload, canonical_required=True), goal_state=args.goal_state)
            args.output.write_bytes(canonical_json(result))
            result = {"ok": True, "status": "prepared", "transition": result["transition"], "authority": result["authority"], "expected_project_head_sha256": result["expected_project_head_sha256"], "expected_execution_head_sha256": result["expected_execution_head_sha256"], "expected_research_authority_head_sha256": result["expected_research_authority_head_sha256"], "payload_sha256": result["payload_sha256"], "candidate_execution_generation": result["candidate_execution_head"]["generation"], "plan_file_sha256": sha256_file(args.output)}
        return emit(result)
    except Exception as exc:
        value, code = error_result(exc); return emit(value, code)


if __name__ == "__main__":
    raise SystemExit(main())
