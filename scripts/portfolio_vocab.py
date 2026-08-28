"""Closed vocabularies and shared helpers for portfolio contracts."""
from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import research_repo as core

Problem = core.Problem
PROJECT_ID = core.PROJECT_ID
SHARED_ID = core.SHARED_ID
SLUG = core.SLUG
SHA256 = core.SHA256
KNOWLEDGE_ID = re.compile(r"^K-[0-9]{4,}$")
MSC_CODE = re.compile(r"^[0-9]{2}(?:-[0-9]{2}|-XX|[A-Z](?:[0-9]{2}|xx)?)?$")
TAG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RELATION_TARGET = re.compile(r"^(?:K|P|S)-[0-9]{4,}$")

PROBLEM_ORIGINS = (
    "known_open", "likely_open_needs_audit", "internal_frontier", "missing_lemma",
    "computational_conjecture", "generalization", "optimality_question", "counterexample_search",
)
PROBLEM_CLASSES = frozenset(PROBLEM_ORIGINS)
GOAL_TYPES = (
    "existence", "nonexistence", "uniqueness", "classification", "characterization", "construction",
    "equivalence", "bound", "optimality", "asymptotic", "regularity", "convergence", "stability",
    "algorithm", "decidability", "computation", "counterexample", "formalization", "explanation", "other",
)
PORTFOLIO_ROLES = (
    "frontier_problem", "bridge_problem", "foundation_building", "method_development", "application_case",
)
CLASSIFICATION_STATUSES = ("provisional", "reviewed")
KNOWLEDGE_KINDS = (
    "definition", "notation", "theorem", "lemma", "equivalence", "method", "example", "counterexample",
    "obstruction", "computational_fact", "reference_map", "knowledge_gap",
)
KNOWLEDGE_RELATION_TYPES = (
    "generalizes", "specializes", "equivalent_to", "contrasts_with", "uses_method", "applies_to",
    "motivates", "obstructs", "discharges",
)
KNOWLEDGE_AUTHORITY_STATUSES = ("reference_only", "source_audited", "independently_verified")
FEEDBACK_EVENT_TYPES = ("none", "source_audit", "window", "verification", "terminal")
FRONTIER_MOVEMENTS = (
    "not_started", "clarified", "narrowed", "reframed", "expanded", "unchanged",
    "closed_by_proof", "closed_by_refutation",
)

TAXONOMY_FIELDS = (
    "schema", "subject_scheme", "problem_origins", "goal_types", "portfolio_roles",
    "classification_statuses", "knowledge_kinds", "knowledge_relation_types",
    "knowledge_authority_statuses", "feedback_event_types", "frontier_movements",
)
TAXONOMY_EXPECTED: dict[str, Any] = {
    "schema": "jin-math-taxonomy/v1",
    "subject_scheme": "MSC2020",
    "problem_origins": list(PROBLEM_ORIGINS),
    "goal_types": list(GOAL_TYPES),
    "portfolio_roles": list(PORTFOLIO_ROLES),
    "classification_statuses": list(CLASSIFICATION_STATUSES),
    "knowledge_kinds": list(KNOWLEDGE_KINDS),
    "knowledge_relation_types": list(KNOWLEDGE_RELATION_TYPES),
    "knowledge_authority_statuses": list(KNOWLEDGE_AUTHORITY_STATUSES),
    "feedback_event_types": list(FEEDBACK_EVENT_TYPES),
    "frontier_movements": list(FRONTIER_MOVEMENTS),
}

CLASSIFICATION_FIELDS = (
    "subject", "origin", "goal_types", "object_tags", "method_tags", "portfolio_role", "status",
)
SUBJECT_FIELDS = ("scheme", "primary", "secondary")
DEPENDENCY_FIELDS = ("projects", "knowledge", "shared_results")
FEEDBACK_FIELDS = (
    "event_type", "event_id", "receipt", "frontier_movement", "verified_claims_added",
    "verified_refutations_added", "routes_eliminated", "blockers_resolved", "blockers_open",
    "verification_debt", "knowledge_debt", "next_frontier",
)
KNOWLEDGE_FIELDS = (
    "schema", "knowledge_id", "kind", "title", "classification", "statement", "assumptions", "scope",
    "conventions", "prerequisites", "relations", "authority", "source_refs", "cannot_imply",
)
KNOWLEDGE_CLASSIFICATION_FIELDS = ("subject", "object_tags", "method_tags")
RELATION_FIELDS = ("type", "target")
AUTHORITY_FIELDS = ("status", "receipt", "shared_result")
PROJECTED_WITH_PROJECT = frozenset(
    {"objective_freeze", "active", "review_gate", "compute_wait", "parked", "terminal_audit", "closed"}
)


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def string_list(value: Any, *, nonempty_items: bool = True) -> bool:
    if not isinstance(value, list):
        return False
    return all(nonempty(item) for item in value) if nonempty_items else all(isinstance(item, str) for item in value)


def unique(value: list[Any]) -> bool:
    try:
        return len(value) == len(set(value))
    except TypeError:
        return False


def msc_valid(value: Any, *, allow_unclassified: bool) -> bool:
    return bool((allow_unclassified and value == "unclassified") or (isinstance(value, str) and MSC_CODE.fullmatch(value)))


def default_classification(
    *, origin: str, primary_msc: str = "unclassified", secondary_msc: Iterable[str] = (),
    goal_types: Iterable[str] = ("other",), object_tags: Iterable[str] = (), method_tags: Iterable[str] = (),
    portfolio_role: str = "frontier_problem", status: str = "provisional",
) -> dict[str, Any]:
    return {
        "subject": {"scheme": "MSC2020", "primary": primary_msc, "secondary": list(dict.fromkeys(secondary_msc))},
        "origin": origin,
        "goal_types": list(dict.fromkeys(goal_types)),
        "object_tags": list(dict.fromkeys(object_tags)),
        "method_tags": list(dict.fromkeys(method_tags)),
        "portfolio_role": portfolio_role,
        "status": status,
    }


def default_dependencies(
    *, projects: Iterable[str] = (), knowledge: Iterable[str] = (), shared_results: Iterable[str] = (),
) -> dict[str, list[str]]:
    return {
        "projects": list(dict.fromkeys(projects)),
        "knowledge": list(dict.fromkeys(knowledge)),
        "shared_results": list(dict.fromkeys(shared_results)),
    }


def default_result_feedback() -> dict[str, Any]:
    return {
        "event_type": "none", "event_id": None, "receipt": None, "frontier_movement": "not_started",
        "verified_claims_added": 0, "verified_refutations_added": 0, "routes_eliminated": 0,
        "blockers_resolved": 0, "blockers_open": 0, "verification_debt": 0, "knowledge_debt": [],
        "next_frontier": "Complete independent source audit, classification review, and prerequisite mapping.",
    }


def validate_taxonomy(root: Path) -> list[Problem]:
    path = root / "taxonomy/facets.json"
    rel = "taxonomy/facets.json"
    try:
        value = core.load_json(path)
    except (OSError, UnicodeError, ValueError) as exc:
        return [Problem("taxonomy_invalid", str(exc), rel)]
    if not isinstance(value, dict) or tuple(value) != TAXONOMY_FIELDS:
        return [Problem("taxonomy_fields_invalid", f"expected ordered fields {TAXONOMY_FIELDS}", rel)]
    problems = [
        Problem("taxonomy_vocabulary_mismatch", f"{field} differs from the v1 closed vocabulary", rel)
        for field in TAXONOMY_FIELDS if value.get(field) != TAXONOMY_EXPECTED[field]
    ]
    if path.read_bytes() != core.pretty_json(value):
        problems.append(Problem("taxonomy_not_canonical", "taxonomy must be deterministic pretty UTF-8 JSON with one final LF", rel))
    return problems


def validate_subject(value: Any, source: str, *, reviewed_required: bool = False) -> list[Problem]:
    if not isinstance(value, dict) or tuple(value) != SUBJECT_FIELDS:
        return [Problem("subject_shape_invalid", f"expected ordered fields {SUBJECT_FIELDS}", source)]
    problems: list[Problem] = []
    if value["scheme"] != "MSC2020":
        problems.append(Problem("subject_scheme_invalid", "subject.scheme must be MSC2020", source))
    primary = value["primary"]
    if not msc_valid(primary, allow_unclassified=True):
        problems.append(Problem("subject_primary_invalid", "primary must be unclassified or a syntactically valid MSC2020 code", source))
    secondary = value["secondary"]
    if not isinstance(secondary, list) or not unique(secondary) or not all(msc_valid(x, allow_unclassified=False) for x in secondary):
        problems.append(Problem("subject_secondary_invalid", "secondary must be unique MSC2020 codes", source))
    elif primary in secondary:
        problems.append(Problem("subject_duplicate_primary", "primary must not be repeated in secondary", source))
    if reviewed_required and primary == "unclassified":
        problems.append(Problem("subject_review_missing", "Project state requires a reviewed non-placeholder primary MSC2020 code", source))
    return problems


def validate_tags(value: Any, field: str, source: str, *, required: bool = False) -> list[Problem]:
    if not isinstance(value, list) or not unique(value) or not all(isinstance(x, str) and TAG.fullmatch(x) for x in value):
        return [Problem("classification_tags_invalid", f"{field} must contain unique lowercase kebab-case tags", source)]
    return [Problem("classification_tags_missing", f"{field} must be nonempty for a reviewed Project", source)] if required and not value else []


def validate_project_classification(value: Any, source: str, *, reviewed_required: bool) -> list[Problem]:
    if not isinstance(value, dict) or tuple(value) != CLASSIFICATION_FIELDS:
        return [Problem("classification_shape_invalid", f"expected ordered fields {CLASSIFICATION_FIELDS}", source)]
    problems = validate_subject(value["subject"], source, reviewed_required=reviewed_required)
    if value["origin"] not in PROBLEM_ORIGINS:
        problems.append(Problem("classification_origin_invalid", "unknown problem origin", source))
    goals = value["goal_types"]
    if not isinstance(goals, list) or not goals or not unique(goals) or not all(x in GOAL_TYPES for x in goals):
        problems.append(Problem("classification_goals_invalid", "goal_types must be a nonempty unique registered list", source))
    elif "other" in goals and len(goals) > 1:
        problems.append(Problem("classification_goals_ambiguous", "other cannot be combined with a specific goal type", source))
    elif reviewed_required and goals == ["other"]:
        problems.append(Problem("classification_goals_unreviewed", "reviewed Project classification must name a specific mathematical goal", source))
    problems.extend(validate_tags(value["object_tags"], "object_tags", source, required=reviewed_required))
    problems.extend(validate_tags(value["method_tags"], "method_tags", source))
    if value["portfolio_role"] not in PORTFOLIO_ROLES:
        problems.append(Problem("classification_role_invalid", "unknown portfolio role", source))
    if value["status"] not in CLASSIFICATION_STATUSES:
        problems.append(Problem("classification_status_invalid", "unknown classification review status", source))
    elif reviewed_required and value["status"] != "reviewed":
        problems.append(Problem("classification_review_missing", "Project state requires classification.status=reviewed", source))
    return problems


def known_file_ids(directory: Path, pattern: re.Pattern[str]) -> set[str]:
    return {p.stem for p in directory.glob("*.json") if pattern.fullmatch(p.stem)} if directory.is_dir() else set()


def first_cycle(graph: dict[str, list[str]]) -> list[str] | None:
    visited: set[str] = set(); active: list[str] = []; active_set: set[str] = set()
    def visit(node: str) -> list[str] | None:
        visited.add(node); active.append(node); active_set.add(node)
        for target in sorted(graph.get(node, [])):
            if target not in graph:
                continue
            if target in active_set:
                return active[active.index(target):] + [target]
            if target not in visited:
                cycle = visit(target)
                if cycle:
                    return cycle
        active.pop(); active_set.remove(node); return None
    for node in sorted(graph):
        if node not in visited:
            cycle = visit(node)
            if cycle:
                return cycle
    return None
