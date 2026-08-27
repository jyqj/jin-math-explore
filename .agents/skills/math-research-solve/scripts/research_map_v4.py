#!/usr/bin/env python3
"""Validate the causal control layer for math-research-map/v4."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "math-research-map/v4"
VALIDATION_SCHEMA = "math-research-map-validation/v4"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
AUTH_PREFIXES = ("memory:", "route-review:", "evidence:", "asset:", "project:")


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def refs_ok(value: Any, *, require_review: bool = False) -> bool:
    if not isinstance(value, list) or not value or not all(nonempty(x) and x.startswith(AUTH_PREFIXES) for x in value):
        return False
    return not require_review or any(x.startswith(("route-review:", "memory:")) for x in value)


def memory_refs(value: Any) -> set[str]:
    found: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for item in node.values():
                walk(item)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, str) and node.startswith("memory:"):
            found.add(node[len("memory:"):])

    walk(value)
    return found


def issue_receipt(value: Any, *, route_review_sha256: str, authoritative_memory_ids: set[str]) -> dict[str, Any]:
    issues = validate_control(value, for_attempt=True)
    if not isinstance(route_review_sha256, str) or not HEX64.fullmatch(route_review_sha256):
        issues.append({"code": "route_review_hash_invalid", "path": "route_review_sha256"})
    missing = sorted(memory_refs(value) - authoritative_memory_ids)
    for memory_id in missing:
        issues.append({"code": "map_authority_reference_missing", "path": f"memory:{memory_id}"})
    if issues:
        return {"ok": False, "schema": VALIDATION_SCHEMA, "activation_eligible": False, "issues": issues}
    return {
        "ok": True,
        "schema": VALIDATION_SCHEMA,
        "activation_eligible": True,
        "project_id": value["project_id"],
        "project_objective_sha256": value["project_objective_sha256"],
        "source_head_sha256": value["source_head_sha256"],
        "control_sha256": digest(canonical(value)),
        "route_review_sha256": route_review_sha256,
        "authoritative_memory_ids": sorted(authoritative_memory_ids),
        "issues": [],
    }


def validate_control(value: Any, *, for_attempt: bool = False) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    def issue(code: str, path: str, detail: str = "") -> None:
        item = {"code": code, "path": path}
        if detail:
            item["detail"] = detail
        issues.append(item)

    required = {"schema", "project_id", "project_objective_sha256", "source_head_sha256", "status", "milestones", "routes", "route_decision"}
    if not isinstance(value, dict) or set(value) != required:
        return [{"code": "map_fields_invalid", "path": ".research/research-map.json"}]
    if value.get("schema") != SCHEMA:
        issue("map_schema_invalid", "schema")
    if not nonempty(value.get("project_id")):
        issue("project_id_invalid", "project_id")
    for key in ("project_objective_sha256", "source_head_sha256"):
        if not isinstance(value.get(key), str) or not HEX64.fullmatch(value[key]):
            issue("hash_invalid", key)
    if value.get("status") not in ("current", "review_required", "historical"):
        issue("map_status_invalid", "status")
    if for_attempt and value.get("status") != "current":
        issue("map_not_activation_eligible", "status")

    milestones = value.get("milestones")
    if not isinstance(milestones, list):
        issue("milestones_invalid", "milestones")
        milestones = []
    seen: set[str] = set()
    milestone_keys = {"milestone_id", "conclusion", "method_overview", "parameter_definitions", "method_spine", "reusable_structures", "bottleneck_effect", "cannot_imply", "evidence_refs", "status"}
    for i, item in enumerate(milestones):
        p = f"milestones[{i}]"
        if not isinstance(item, dict) or set(item) != milestone_keys:
            issue("milestone_fields_invalid", p)
            continue
        mid = item.get("milestone_id")
        if not nonempty(mid) or mid in seen:
            issue("milestone_id_invalid", p + ".milestone_id")
        else:
            seen.add(mid)
        for key in ("conclusion", "method_spine", "bottleneck_effect", "cannot_imply"):
            if not nonempty(item.get(key)):
                issue("milestone_causality_missing", p + "." + key)
        overview = item.get("method_overview")
        if not isinstance(overview, dict) or set(overview) != {"method_family", "baseline_method", "project_modification", "high_level_mechanism"} or not all(nonempty(overview.get(key)) for key in overview):
            issue("method_overview_missing", p + ".method_overview")
        definitions = item.get("parameter_definitions")
        if not isinstance(definitions, list):
            issue("parameter_definitions_invalid", p + ".parameter_definitions")
        else:
            for j, definition in enumerate(definitions):
                if not isinstance(definition, dict) or set(definition) != {"symbol", "meaning", "frozen_value", "choice_reason", "evidence_refs"} or not all(nonempty(definition.get(key)) for key in ("symbol", "meaning", "frozen_value", "choice_reason")) or not refs_ok(definition.get("evidence_refs")):
                    issue("parameter_definition_missing", f"{p}.parameter_definitions[{j}]")
        if not isinstance(item.get("reusable_structures"), list) or not item["reusable_structures"] or not all(nonempty(x) for x in item["reusable_structures"]):
            issue("reusable_structures_missing", p + ".reusable_structures")
        if not refs_ok(item.get("evidence_refs")):
            issue("method_source_missing", p + ".evidence_refs")
        if item.get("status") not in ("verified", "bounded", "review_required"):
            issue("milestone_status_invalid", p + ".status")

    routes = value.get("routes")
    if not isinstance(routes, list) or not routes:
        issue("routes_invalid", "routes")
        routes = []
    route_keys = {"route_id", "status", "mathematical_object", "objective_mechanism", "evidence_boundary", "missing_work", "success_gate", "candidate_failure_gate", "failure_scope", "verified_route_failure_ref", "evidence_refs"}
    route_ids: set[str] = set()
    for i, item in enumerate(routes):
        p = f"routes[{i}]"
        if not isinstance(item, dict) or set(item) != route_keys:
            issue("route_fields_invalid", p)
            continue
        rid = item.get("route_id")
        if not nonempty(rid) or rid in route_ids:
            issue("route_id_invalid", p + ".route_id")
        else:
            route_ids.add(rid)
        for key in ("mathematical_object", "objective_mechanism", "evidence_boundary", "missing_work", "success_gate", "candidate_failure_gate"):
            if not nonempty(item.get(key)):
                issue("route_explanation_missing", p + "." + key)
        if item.get("failure_scope") not in ("candidate_only", "route_exact_scope"):
            issue("failure_scope_invalid", p + ".failure_scope")
        if item.get("failure_scope") == "route_exact_scope":
            ref = item.get("verified_route_failure_ref")
            if not nonempty(ref) or not ref.startswith("memory:verified-impossibility-boundary/"):
                issue("candidate_failure_expanded", p + ".verified_route_failure_ref")
        elif item.get("verified_route_failure_ref") is not None:
            issue("candidate_failure_expanded", p + ".verified_route_failure_ref")
        if not refs_ok(item.get("evidence_refs")):
            issue("route_evidence_missing", p + ".evidence_refs")

    decision = value.get("route_decision")
    decision_keys = {"selected_route_id", "why_now", "why_over_alternatives", "targeted_bottleneck", "uncertainty", "rerank_conditions", "evidence_refs"}
    if not isinstance(decision, dict) or set(decision) != decision_keys:
        issue("route_decision_fields_invalid", "route_decision")
    else:
        if decision.get("selected_route_id") not in route_ids:
            issue("selected_route_missing", "route_decision.selected_route_id")
        for key in ("why_now", "targeted_bottleneck", "uncertainty"):
            if not nonempty(decision.get(key)):
                issue("route_decision_reason_missing", "route_decision." + key)
        comparisons = decision.get("why_over_alternatives")
        if not isinstance(comparisons, list) or not comparisons:
            issue("why_over_alternatives_missing", "route_decision.why_over_alternatives")
        else:
            for i, item in enumerate(comparisons):
                if not isinstance(item, dict) or set(item) != {"route_id", "reason"} or not nonempty(item.get("route_id")) or not nonempty(item.get("reason")):
                    issue("alternative_reason_invalid", f"route_decision.why_over_alternatives[{i}]")
        if not isinstance(decision.get("rerank_conditions"), list) or not decision["rerank_conditions"] or not all(nonempty(x) for x in decision["rerank_conditions"]):
            issue("rerank_conditions_missing", "route_decision.rerank_conditions")
        if not refs_ok(decision.get("evidence_refs"), require_review=True):
            issue("route_decision_authority_missing", "route_decision.evidence_refs")
    return issues


def validate_root(root: Path, *, for_attempt: bool = False) -> dict[str, Any]:
    control_path = root.resolve() / ".research" / "research-map.json"
    if not control_path.is_file():
        return {"ok": False, "schema": VALIDATION_SCHEMA, "issues": [{"code": "map_control_missing", "path": str(control_path)}]}
    try:
        value = load(control_path)
    except Exception as exc:
        return {"ok": False, "schema": VALIDATION_SCHEMA, "issues": [{"code": "map_control_parse_failed", "path": str(control_path), "detail": str(exc)}]}
    issues = validate_control(value, for_attempt=for_attempt)
    return {"ok": not issues, "schema": VALIDATION_SCHEMA, "map_schema": value.get("schema"), "activation_eligible": not issues and value.get("status") == "current", "control_sha256": digest(canonical(value)), "issues": issues}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("map_root", type=Path)
    p.add_argument("--for-v13-attempt", action="store_true")
    args = p.parse_args(argv)
    result = validate_root(args.map_root, for_attempt=args.for_v13_attempt)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
