"""Project registry v2 validation and typed portfolio dependencies."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import research_repo as core
from portfolio_vocab import (
    DEPENDENCY_FIELDS, FEEDBACK_EVENT_TYPES, FEEDBACK_FIELDS, FRONTIER_MOVEMENTS, KNOWLEDGE_ID,
    PROJECTED_WITH_PROJECT, PROJECT_ID, SHA256, SHARED_ID, Problem, first_cycle, known_file_ids,
    nonempty, string_list, unique, validate_project_classification,
)

REGISTRY_FIELDS = (
    "schema", "project_id", "slug", "title", "classification", "operational_status",
    "mathematical_status", "project_path", "objective_sha256", "current_window_id",
    "dependencies", "source_audit", "last_merged_window", "result_feedback",
)


def _load_entries(root: Path) -> tuple[list[dict[str, Any]], list[Problem]]:
    directory = root / "registry/projects"
    if not directory.is_dir():
        return [], [Problem("registry_missing", "registry/projects directory is required", "registry/projects")]
    entries: list[dict[str, Any]] = []; problems: list[Problem] = []
    for path in sorted(directory.glob("*.json")):
        rel = path.relative_to(root).as_posix()
        try:
            value = core.load_json(path)
        except (OSError, UnicodeError, ValueError) as exc:
            problems.append(Problem("registry_json_invalid", str(exc), rel)); continue
        if not isinstance(value, dict):
            problems.append(Problem("registry_entry_invalid", "entry must be a JSON object", rel)); continue
        entries.append(value | {"__file__": rel})
    return entries, problems


def registry_entries(root: Path) -> list[dict[str, Any]]:
    entries, problems = _load_entries(root)
    if problems:
        raise ValueError("; ".join(item.render() for item in problems))
    return entries


def public_registry_entries(root: Path) -> list[dict[str, Any]]:
    return [{k: v for k, v in item.items() if k != "__file__"} for item in registry_entries(root)]


def _validate_dependencies(value: Any, source: str) -> list[Problem]:
    if not isinstance(value, dict) or tuple(value) != DEPENDENCY_FIELDS:
        return [Problem("dependency_shape_invalid", f"expected ordered fields {DEPENDENCY_FIELDS}", source)]
    problems: list[Problem] = []
    for field, pattern in {"projects": PROJECT_ID, "knowledge": KNOWLEDGE_ID, "shared_results": SHARED_ID}.items():
        items = value[field]
        if not isinstance(items, list) or not unique(items) or not all(isinstance(x, str) and pattern.fullmatch(x) for x in items):
            problems.append(Problem("dependency_values_invalid", f"dependencies.{field} must contain unique valid IDs", source))
    return problems


def _nonnegative_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _validate_feedback(
    value: Any, source: str, *, root: Path, source_audit: Any, last_window: Any,
    operational_status: Any, mathematical_status: Any,
) -> list[Problem]:
    if not isinstance(value, dict) or tuple(value) != FEEDBACK_FIELDS:
        return [Problem("feedback_shape_invalid", f"expected ordered fields {FEEDBACK_FIELDS}", source)]
    problems: list[Problem] = []
    event_type = value["event_type"]; movement = value["frontier_movement"]
    if event_type not in FEEDBACK_EVENT_TYPES:
        problems.append(Problem("feedback_event_invalid", "unknown feedback event_type", source))
    if movement not in FRONTIER_MOVEMENTS:
        problems.append(Problem("feedback_movement_invalid", "unknown frontier_movement", source))
    counts = (
        "verified_claims_added", "verified_refutations_added", "routes_eliminated", "blockers_resolved",
        "blockers_open", "verification_debt",
    )
    for field in counts:
        if not _nonnegative_integer(value[field]):
            problems.append(Problem("feedback_count_invalid", f"{field} must be a nonnegative integer", source))
    debt = value["knowledge_debt"]
    if not string_list(debt) or not unique(debt):
        problems.append(Problem("feedback_knowledge_debt_invalid", "knowledge_debt must be unique nonempty strings", source))
    if not nonempty(value["next_frontier"]):
        problems.append(Problem("feedback_next_frontier_invalid", "next_frontier must be nonempty", source))

    event_id = value["event_id"]; receipt = value["receipt"]
    if event_type == "none":
        if event_id is not None or receipt is not None or movement != "not_started":
            problems.append(Problem("feedback_none_invalid", "none event requires null identity/receipt and not_started movement", source))
        if any(value[field] != 0 for field in counts):
            problems.append(Problem("feedback_none_counts_invalid", "none event cannot report completed-result counts or debt", source))
    else:
        if not nonempty(event_id):
            problems.append(Problem("feedback_event_id_missing", "audited feedback event requires event_id", source))
        if movement == "not_started":
            problems.append(Problem("feedback_event_movement_invalid", "audited feedback event cannot remain not_started", source))
        if not nonempty(receipt) or not core.safe_relative(receipt):
            problems.append(Problem("feedback_receipt_invalid", "audited feedback event requires a safe repository-relative receipt", source))
        elif not (root / receipt).is_file():
            problems.append(Problem("feedback_receipt_missing", "feedback receipt file is missing", source))
    if last_window is not None and event_type == "none":
        problems.append(Problem("feedback_missing_after_window", "a merged window requires an audited feedback event", source))
    if event_type == "window" and event_id != last_window:
        problems.append(Problem("feedback_window_binding_invalid", "window feedback event_id must equal last_merged_window", source))
    if event_type == "source_audit" and isinstance(source_audit, dict) and source_audit.get("status") == "pass" and receipt != source_audit.get("receipt"):
        problems.append(Problem("feedback_source_binding_invalid", "source_audit feedback must bind the source-audit receipt", source))
    if event_type == "terminal" and (
        operational_status not in {"terminal_audit", "closed"} or mathematical_status not in {"complete", "refuted"}
    ):
        problems.append(Problem("feedback_terminal_state_invalid", "terminal feedback requires terminal/closed and complete/refuted state", source))
    if movement == "closed_by_proof" and mathematical_status != "complete":
        problems.append(Problem("feedback_proof_close_invalid", "closed_by_proof requires mathematical_status=complete", source))
    if movement == "closed_by_refutation" and mathematical_status != "refuted":
        problems.append(Problem("feedback_refutation_close_invalid", "closed_by_refutation requires mathematical_status=refuted", source))
    return problems


def validate_registry(root: Path) -> list[Problem]:
    root = root.resolve()
    entries, problems = _load_entries(root)
    ids: dict[str, str] = {}
    known_knowledge = known_file_ids(root / "knowledge/nodes", KNOWLEDGE_ID)
    known_shared = known_file_ids(root / "registry/shared-results", SHARED_ID)

    for raw in entries:
        source = raw["__file__"]
        value = {k: v for k, v in raw.items() if k != "__file__"}
        if tuple(value) != REGISTRY_FIELDS:
            problems.append(Problem("registry_fields_invalid", f"expected ordered fields {REGISTRY_FIELDS}", source)); continue
        project_id = value["project_id"]
        if not isinstance(project_id, str) or not PROJECT_ID.fullmatch(project_id):
            problems.append(Problem("project_id_invalid", "expected P- followed by at least four digits", source)); continue
        if Path(source).stem != project_id:
            problems.append(Problem("registry_filename_mismatch", "filename must equal project_id.json", source))
        if project_id in ids:
            problems.append(Problem("project_id_duplicate", f"also declared in {ids[project_id]}", source))
        ids[project_id] = source
        if value["schema"] != "jin-math-project-registry/v2":
            problems.append(Problem("registry_schema_invalid", "registry entries must use jin-math-project-registry/v2", source))
        if not isinstance(value["slug"], str) or not core.SLUG.fullmatch(value["slug"]):
            problems.append(Problem("project_slug_invalid", "slug must be lowercase kebab-case", source))
        if not nonempty(value["title"]):
            problems.append(Problem("project_title_invalid", "title must be nonempty", source))

        op = value["operational_status"]; math = value["mathematical_status"]
        if op not in core.OPERATIONAL_STATUSES:
            problems.append(Problem("operational_status_invalid", "unknown operational status", source))
        if math not in core.MATHEMATICAL_STATUSES:
            problems.append(Problem("mathematical_status_invalid", "unknown mathematical status", source))
        problems.extend(validate_project_classification(value["classification"], source, reviewed_required=op in PROJECTED_WITH_PROJECT))
        problems.extend(_validate_dependencies(value["dependencies"], source))
        if op == "closed" and math not in {"refuted", "complete"}:
            problems.append(Problem("closed_status_invalid", "closed projects must be refuted or complete", source))
        if math == "complete" and op not in {"terminal_audit", "closed"}:
            problems.append(Problem("complete_status_invalid", "complete mathematics requires terminal_audit or closed", source))

        current_window = value["current_window_id"]; last_window = value["last_merged_window"]
        if current_window is not None and not nonempty(current_window):
            problems.append(Problem("current_window_invalid", "current_window_id must be null or nonempty", source))
        if last_window is not None and not nonempty(last_window):
            problems.append(Problem("last_window_invalid", "last_merged_window must be null or nonempty", source))

        audit = value["source_audit"]
        if not isinstance(audit, dict) or tuple(audit) != ("status", "as_of", "receipt") or audit.get("status") not in core.SOURCE_AUDIT_STATUSES:
            problems.append(Problem("source_audit_invalid", "source_audit has invalid closed shape/status", source))
        elif audit["status"] == "pass":
            if not nonempty(audit["as_of"]) or not nonempty(audit["receipt"]) or not core.safe_relative(audit["receipt"]):
                problems.append(Problem("source_audit_pass_invalid", "PASS requires date and safe receipt path", source))
            elif not (root / audit["receipt"]).is_file():
                problems.append(Problem("source_audit_receipt_missing", "receipt file is missing", source))
            else:
                try:
                    date.fromisoformat(audit["as_of"])
                except ValueError:
                    problems.append(Problem("source_audit_date_invalid", "as_of must be YYYY-MM-DD", source))
        elif audit["as_of"] is not None or audit["receipt"] is not None:
            problems.append(Problem("source_audit_nonpass_invalid", "non-PASS audit must not carry authority receipt", source))

        project_path = value["project_path"]; objective_sha = value["objective_sha256"]
        if op in PROJECTED_WITH_PROJECT:
            expected = f"projects/{project_id}--{value['slug']}"
            if project_path != expected or not core.safe_relative(project_path):
                problems.append(Problem("project_path_invalid", f"expected {expected}", source))
            else:
                project_root = root / project_path
                if not project_root.is_dir():
                    problems.append(Problem("project_directory_missing", "project directory is missing", project_path))
                else:
                    disk = {item.name for item in project_root.iterdir()}
                    if disk != core.PROJECT_ROOT_ENTRIES:
                        problems.append(Problem("project_root_shape_invalid", f"expected exactly {sorted(core.PROJECT_ROOT_ENTRIES)}, got {sorted(disk)}", project_path))
                    objective = project_root / ".research/identity/objective-core.json"
                    if not objective.is_file():
                        problems.append(Problem("objective_missing", "v13 objective-core.json is missing", objective.relative_to(root).as_posix()))
                    else:
                        problems.extend(core.validate_objective(objective))
                        if not isinstance(objective_sha, str) or not SHA256.fullmatch(objective_sha) or objective_sha != core.sha256_file(objective):
                            problems.append(Problem("objective_hash_mismatch", "registry objective_sha256 does not match objective bytes", source))
                        else:
                            problems.extend(core.validate_project_shell(project_root, project_id, objective_sha))
            requires_pass = op in {"active", "review_gate", "compute_wait", "terminal_audit", "closed"}
            if requires_pass and (not isinstance(audit, dict) or audit.get("status") != "pass"):
                problems.append(Problem("active_without_source_audit", "active/terminal project requires source audit PASS", source))
        elif project_path is not None or objective_sha is not None or current_window is not None or last_window is not None:
            problems.append(Problem("preproject_state_invalid", "candidate/source-audit entries must not bind Project state", source))

        problems.extend(_validate_feedback(
            value["result_feedback"], source, root=root, source_audit=audit, last_window=last_window,
            operational_status=op, mathematical_status=math,
        ))

    graph: dict[str, list[str]] = {}
    for raw in entries:
        project_id = raw.get("project_id"); source = raw.get("__file__", "registry/projects")
        deps = raw.get("dependencies")
        if not isinstance(project_id, str) or not PROJECT_ID.fullmatch(project_id) or not isinstance(deps, dict):
            continue
        pdeps = deps.get("projects", []); kdeps = deps.get("knowledge", []); sdeps = deps.get("shared_results", [])
        if isinstance(pdeps, list):
            graph[project_id] = [x for x in pdeps if isinstance(x, str)]
            for dependency in pdeps:
                if dependency == project_id:
                    problems.append(Problem("dependency_self_reference", "Project cannot depend on itself", source))
                elif dependency not in ids:
                    problems.append(Problem("dependency_missing", f"unknown Project dependency {dependency}", source))
        if isinstance(kdeps, list):
            for dependency in kdeps:
                if dependency not in known_knowledge:
                    problems.append(Problem("knowledge_dependency_missing", f"unknown knowledge dependency {dependency}", source))
        if isinstance(sdeps, list):
            for dependency in sdeps:
                if dependency not in known_shared:
                    problems.append(Problem("shared_dependency_missing", f"unknown shared-result dependency {dependency}", source))
    cycle = first_cycle(graph)
    if cycle:
        problems.append(Problem("project_dependency_cycle", " -> ".join(cycle), ids.get(cycle[0], "registry/projects")))
    return problems
