"""Repository contracts for jin-math-explore.

These checks are deliberately mechanical.  They validate identity, paths,
hashes, and lifecycle compatibility; they never claim mathematical truth.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


PROJECT_ID = re.compile(r"^P-[0-9]{4,}$")
SHARED_ID = re.compile(r"^S-[0-9]{4,}$")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SHA1 = re.compile(r"^[0-9a-f]{40}$")

OBJECTIVE_FIELDS = (
    "statement",
    "domain",
    "quantifier_order",
    "assumptions",
    "evidence_standard",
    "completion_standard",
)

REGISTRY_FIELDS = (
    "schema",
    "project_id",
    "slug",
    "title",
    "problem_class",
    "operational_status",
    "mathematical_status",
    "project_path",
    "objective_sha256",
    "current_window_id",
    "dependencies",
    "source_audit",
    "last_merged_window",
)

PROBLEM_CLASSES = {
    "known_open",
    "likely_open_needs_audit",
    "internal_frontier",
    "missing_lemma",
    "computational_conjecture",
    "generalization",
    "optimality_question",
    "counterexample_search",
}
OPERATIONAL_STATUSES = {
    "candidate",
    "source_audit",
    "objective_freeze",
    "active",
    "review_gate",
    "compute_wait",
    "parked",
    "terminal_audit",
    "closed",
}
MATHEMATICAL_STATUSES = {"unknown", "open", "partial", "proof_candidate", "refuted", "complete"}
SOURCE_AUDIT_STATUSES = {"pending", "pass", "fail", "stale"}
PROJECTED_WITH_PROJECT = {"objective_freeze", "active", "review_gate", "compute_wait", "parked", "terminal_audit", "closed"}
PROJECT_ROOT_ENTRIES = {"project.json", "README.md", "研究地图", ".research"}
PROJECT_FIELDS = (
    "schema", "project_id", "created_at_utc", "objective",
    "objective_commitment_sha256", "research_authority_head",
    "execution_state_head", "generation", "project_complete",
    "pending_goal_update",
)
HANDOFF_FIELDS = (
    "schema", "problem_id", "window_id", "attempt_id", "claim_id",
    "objective_sha256", "question", "domain", "assumptions",
    "requested_evidence", "backend", "exact_input", "reproduction_command",
    "code_artifacts", "result_artifacts", "computation_record",
    "evidence_grade", "cannot_imply",
)
EVIDENCE_GRADES = {"numerical_evidence", "bounded_check", "exact_check", "proof_certificate", "formal_verification"}
VERIFICATION_FIELDS = (
    "schema", "verification_id", "problem_id", "claim_id", "candidate",
    "dependencies", "reviewer_principal", "context_isolated", "verdict",
    "checked_scope", "earliest_error", "unresolved", "cannot_imply",
)


@dataclass(frozen=True)
class Problem:
    code: str
    message: str
    path: str

    def render(self) -> str:
        return f"{self.code}: {self.path}: {self.message}"


class DuplicateKeyError(ValueError):
    pass


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_pairs_no_duplicates)


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def pretty_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative(value: str) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and "." not in path.parts


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_objective(path: Path) -> list[Problem]:
    problems: list[Problem] = []
    rel = path.as_posix()
    try:
        value = load_json(path)
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateKeyError) as exc:
        return [Problem("objective_json_invalid", str(exc), rel)]
    if not isinstance(value, dict) or tuple(value) != OBJECTIVE_FIELDS:
        problems.append(Problem("objective_fields_invalid", f"expected ordered fields {OBJECTIVE_FIELDS}", rel))
        return problems
    for key in ("statement", "domain", "quantifier_order", "evidence_standard", "completion_standard"):
        if not _nonempty(value[key]):
            problems.append(Problem("objective_value_invalid", f"{key} must be a nonempty string", rel))
    assumptions = value["assumptions"]
    if not isinstance(assumptions, list) or not all(isinstance(item, str) for item in assumptions):
        problems.append(Problem("objective_assumptions_invalid", "assumptions must be an ordered string array", rel))
    raw = path.read_bytes()
    expected = canonical_json(value)
    if raw != expected:
        problems.append(Problem("objective_not_canonical", "objective must be compact UTF-8 JSON with one final LF", rel))
    return problems


def _load_registry_entries(root: Path) -> tuple[list[dict[str, Any]], list[Problem]]:
    entries: list[dict[str, Any]] = []
    problems: list[Problem] = []
    directory = root / "registry" / "projects"
    if not directory.is_dir():
        return entries, [Problem("registry_missing", "registry/projects directory is required", "registry/projects")]
    for path in sorted(directory.glob("*.json")):
        try:
            value = load_json(path)
        except (OSError, UnicodeError, json.JSONDecodeError, DuplicateKeyError) as exc:
            problems.append(Problem("registry_json_invalid", str(exc), path.relative_to(root).as_posix()))
            continue
        if not isinstance(value, dict):
            problems.append(Problem("registry_entry_invalid", "entry must be a JSON object", path.relative_to(root).as_posix()))
            continue
        entries.append(value | {"__file__": path.relative_to(root).as_posix()})
    return entries, problems


def registry_entries(root: Path) -> list[dict[str, Any]]:
    entries, problems = _load_registry_entries(root)
    if problems:
        raise ValueError("; ".join(item.render() for item in problems))
    return entries


def validate_registry(root: Path) -> list[Problem]:
    entries, problems = _load_registry_entries(root)
    ids: dict[str, str] = {}
    for raw in entries:
        file_name = raw["__file__"]
        value = {key: item for key, item in raw.items() if key != "__file__"}
        if tuple(value) != REGISTRY_FIELDS:
            problems.append(Problem("registry_fields_invalid", f"expected ordered fields {REGISTRY_FIELDS}", file_name))
            continue
        project_id = value["project_id"]
        if not isinstance(project_id, str) or not PROJECT_ID.fullmatch(project_id):
            problems.append(Problem("project_id_invalid", "expected P- followed by at least four digits", file_name))
            continue
        if Path(file_name).stem != project_id:
            problems.append(Problem("registry_filename_mismatch", "filename must equal project_id.json", file_name))
        if project_id in ids:
            problems.append(Problem("project_id_duplicate", f"also declared in {ids[project_id]}", file_name))
        ids[project_id] = file_name
        if value["schema"] != "jin-math-project-registry/v1":
            problems.append(Problem("registry_schema_invalid", "unexpected schema", file_name))
        if not isinstance(value["slug"], str) or not SLUG.fullmatch(value["slug"]):
            problems.append(Problem("project_slug_invalid", "slug must be lowercase kebab-case", file_name))
        if not _nonempty(value["title"]):
            problems.append(Problem("project_title_invalid", "title must be nonempty", file_name))
        if value["problem_class"] not in PROBLEM_CLASSES:
            problems.append(Problem("problem_class_invalid", "unknown problem class", file_name))
        op = value["operational_status"]
        math = value["mathematical_status"]
        if op not in OPERATIONAL_STATUSES:
            problems.append(Problem("operational_status_invalid", "unknown operational status", file_name))
        if math not in MATHEMATICAL_STATUSES:
            problems.append(Problem("mathematical_status_invalid", "unknown mathematical status", file_name))
        if op == "closed" and math not in {"refuted", "complete"}:
            problems.append(Problem("closed_status_invalid", "closed projects must be refuted or complete", file_name))
        if math == "complete" and op not in {"terminal_audit", "closed"}:
            problems.append(Problem("complete_status_invalid", "complete mathematics requires terminal_audit or closed", file_name))
        dependencies = value["dependencies"]
        if not isinstance(dependencies, list) or len(dependencies) != len(set(dependencies)) or not all(isinstance(x, str) and PROJECT_ID.fullmatch(x) for x in dependencies):
            problems.append(Problem("project_dependencies_invalid", "dependencies must be unique Project IDs", file_name))
        audit = value["source_audit"]
        if not isinstance(audit, dict) or tuple(audit) != ("status", "as_of", "receipt") or audit.get("status") not in SOURCE_AUDIT_STATUSES:
            problems.append(Problem("source_audit_invalid", "source_audit has invalid closed shape/status", file_name))
        elif audit["status"] == "pass":
            if not _nonempty(audit["as_of"]) or not _nonempty(audit["receipt"]) or not safe_relative(audit["receipt"]):
                problems.append(Problem("source_audit_pass_invalid", "PASS requires date and safe receipt path", file_name))
            elif not (root / audit["receipt"]).is_file():
                problems.append(Problem("source_audit_receipt_missing", "receipt file is missing", file_name))
            else:
                try:
                    date.fromisoformat(audit["as_of"])
                except ValueError:
                    problems.append(Problem("source_audit_date_invalid", "as_of must be YYYY-MM-DD", file_name))
        elif audit["as_of"] is not None or audit["receipt"] is not None:
            problems.append(Problem("source_audit_nonpass_invalid", "non-PASS audit must not carry authority receipt", file_name))

        project_path = value["project_path"]
        objective_sha = value["objective_sha256"]
        if op in PROJECTED_WITH_PROJECT:
            expected_path = f"projects/{project_id}-{value['slug']}"
            if project_path != expected_path or not safe_relative(project_path):
                problems.append(Problem("project_path_invalid", f"expected {expected_path}", file_name))
                continue
            project_root = root / project_path
            if not project_root.is_dir():
                problems.append(Problem("project_directory_missing", "project directory is missing", project_path))
                continue
            entries_on_disk = {item.name for item in project_root.iterdir()}
            if entries_on_disk != PROJECT_ROOT_ENTRIES:
                problems.append(Problem("project_root_shape_invalid", f"expected exactly {sorted(PROJECT_ROOT_ENTRIES)}, got {sorted(entries_on_disk)}", project_path))
            objective = project_root / ".research" / "identity" / "objective-core.json"
            if not objective.is_file():
                problems.append(Problem("objective_missing", "v13 objective-core.json is missing", objective.relative_to(root).as_posix()))
            else:
                problems.extend(validate_objective(objective))
                if not isinstance(objective_sha, str) or not SHA256.fullmatch(objective_sha) or objective_sha != sha256_file(objective):
                    problems.append(Problem("objective_hash_mismatch", "registry objective_sha256 does not match objective bytes", file_name))
                else:
                    problems.extend(validate_project_shell(project_root, project_id, objective_sha))
            if op in {"active", "review_gate", "compute_wait", "terminal_audit", "closed"} and audit.get("status") != "pass":
                problems.append(Problem("active_without_source_audit", "active/terminal project requires source audit PASS", file_name))
        else:
            if project_path is not None or objective_sha is not None or value["current_window_id"] is not None or value["last_merged_window"] is not None:
                problems.append(Problem("preproject_state_invalid", "candidate/source-audit entries must not bind project state", file_name))

    for raw in entries:
        file_name = raw.get("__file__", "registry/projects")
        for dependency in raw.get("dependencies", []):
            if dependency not in ids:
                problems.append(Problem("dependency_missing", f"unknown project dependency {dependency}", file_name))
            if dependency == raw.get("project_id"):
                problems.append(Problem("dependency_self_reference", "project cannot depend on itself", file_name))
    return problems


def validate_skill_dependencies(root: Path) -> list[Problem]:
    path = root / "skill-dependencies.json"
    try:
        value = load_json(path)
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateKeyError) as exc:
        return [Problem("skill_dependencies_invalid", str(exc), "skill-dependencies.json")]
    if not isinstance(value, dict) or tuple(value) != ("schema", "dependencies") or value["schema"] != "jin-math-skill-dependencies/v1":
        return [Problem("skill_dependencies_invalid", "invalid closed manifest", "skill-dependencies.json")]
    names: set[str] = set()
    problems: list[Problem] = []
    for item in value["dependencies"]:
        if not isinstance(item, dict) or tuple(item) != ("name", "version", "package_tree_sha256", "required_for"):
            problems.append(Problem("skill_dependency_shape_invalid", "dependency has unknown/missing fields", "skill-dependencies.json"))
            continue
        if not _nonempty(item["name"]) or item["name"] in names:
            problems.append(Problem("skill_dependency_name_invalid", "dependency names must be nonempty and unique", "skill-dependencies.json"))
        names.add(item["name"])
        if not _nonempty(item["version"]) or not isinstance(item["package_tree_sha256"], str) or not SHA256.fullmatch(item["package_tree_sha256"]):
            problems.append(Problem("skill_dependency_version_invalid", "version/hash invalid", "skill-dependencies.json"))
        if not isinstance(item["required_for"], list) or not item["required_for"] or not all(_nonempty(x) for x in item["required_for"]):
            problems.append(Problem("skill_dependency_routes_invalid", "required_for must be nonempty strings", "skill-dependencies.json"))
    required = {"math-research-solve", "math-science-computation"}
    if names != required:
        problems.append(Problem("skill_dependency_set_invalid", f"expected exactly {sorted(required)}", "skill-dependencies.json"))
    return problems


def validate_shared_results(root: Path) -> list[Problem]:
    directory = root / "registry" / "shared-results"
    problems: list[Problem] = []
    known_projects = {item["project_id"] for item in registry_entries(root)}
    ids: set[str] = set()
    for path in sorted(directory.glob("*.json")):
        rel = path.relative_to(root).as_posix()
        try:
            value = load_json(path)
        except Exception as exc:
            problems.append(Problem("shared_result_json_invalid", str(exc), rel)); continue
        fields = ("schema", "shared_id", "kind", "source_project", "source_claim", "source_commit", "status", "statement", "assumptions", "scope", "evidence_refs", "cannot_imply")
        if not isinstance(value, dict) or tuple(value) != fields:
            problems.append(Problem("shared_result_fields_invalid", "invalid closed shape", rel)); continue
        shared_id = value["shared_id"]
        if not isinstance(shared_id, str) or not SHARED_ID.fullmatch(shared_id) or Path(rel).stem != shared_id or shared_id in ids:
            problems.append(Problem("shared_result_id_invalid", "ID/filename must be unique S-XXXX", rel))
        ids.add(shared_id)
        if value["schema"] != "jin-math-shared-result/v1" or value["status"] != "independently_verified":
            problems.append(Problem("shared_result_authority_invalid", "shared result must use v1 and be independently_verified", rel))
        if value["source_project"] not in known_projects:
            problems.append(Problem("shared_result_source_missing", "source project is not registered", rel))
        if not isinstance(value["source_commit"], str) or not SHA1.fullmatch(value["source_commit"]):
            problems.append(Problem("shared_result_commit_invalid", "source_commit must be a full Git SHA-1", rel))
        if not isinstance(value["evidence_refs"], list) or not value["evidence_refs"] or not isinstance(value["cannot_imply"], list) or not value["cannot_imply"]:
            problems.append(Problem("shared_result_evidence_invalid", "evidence_refs and cannot_imply are required", rel))
    return problems


def _validate_pointer(value: Any, base: Path, label: str, source: str) -> list[Problem]:
    problems: list[Problem] = []
    if not isinstance(value, dict) or tuple(value) != ("path", "sha256"):
        return [Problem("artifact_pointer_invalid", f"{label} must contain only path and sha256", source)]
    path_value = value["path"]
    digest = value["sha256"]
    if not safe_relative(path_value):
        return [Problem("artifact_path_invalid", f"{label} path must be safe and relative to Project root", source)]
    target = base / path_value
    if not target.is_file():
        problems.append(Problem("artifact_missing", f"{label} target is missing: {path_value}", source))
    elif not isinstance(digest, str) or not SHA256.fullmatch(digest) or sha256_file(target) != digest:
        problems.append(Problem("artifact_hash_mismatch", f"{label} hash differs: {path_value}", source))
    return problems


def validate_project_shell(project_root: Path, project_id: str, objective_sha256: str) -> list[Problem]:
    """Validate the repository-facing v13 head shell.

    The full state machine remains owned by $math-research-solve. This check
    prevents the registry from accepting an empty or hash-broken Project.
    """
    path = project_root / "project.json"
    source = path.as_posix()
    try:
        value = load_json(path)
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateKeyError) as exc:
        return [Problem("project_head_json_invalid", str(exc), source)]
    if not isinstance(value, dict) or tuple(value) != PROJECT_FIELDS:
        return [Problem("project_head_fields_invalid", f"expected ordered fields {PROJECT_FIELDS}", source)]
    problems: list[Problem] = []
    if path.read_bytes() != canonical_json(value):
        problems.append(Problem("project_head_not_canonical", "project.json must be canonical compact JSON", source))
    if value["schema"] != "math-research-project/v13" or value["project_id"] != project_id:
        problems.append(Problem("project_head_identity_invalid", "v13 schema or registry Project ID differs", source))
    if not _nonempty(value["created_at_utc"]):
        problems.append(Problem("project_created_at_invalid", "created_at_utc must be nonempty", source))
    if not isinstance(value["generation"], int) or isinstance(value["generation"], bool) or value["generation"] < 0:
        problems.append(Problem("project_generation_invalid", "generation must be a nonnegative integer", source))
    if not isinstance(value["project_complete"], bool) or not isinstance(value["pending_goal_update"], bool):
        problems.append(Problem("project_completion_flags_invalid", "completion flags must be booleans", source))
    objective_pointer = value["objective"]
    problems.extend(_validate_pointer(objective_pointer, project_root, "objective", source))
    if isinstance(objective_pointer, dict) and (
        objective_pointer.get("path") != ".research/identity/objective-core.json"
        or objective_pointer.get("sha256") != objective_sha256
    ):
        problems.append(Problem("project_objective_pointer_mismatch", "project.json objective pointer differs from registry/objective bytes", source))
    if value["objective_commitment_sha256"] != objective_sha256:
        problems.append(Problem("project_objective_commitment_mismatch", "objective commitment differs from registry", source))
    for field, schema in (
        ("research_authority_head", "math-research-authority-head/v13"),
        ("execution_state_head", "math-research-execution-head/v13"),
    ):
        pointer = value[field]
        pointer_problems = _validate_pointer(pointer, project_root, field, source)
        problems.extend(pointer_problems)
        if pointer_problems:
            continue
        target = project_root / pointer["path"]
        try:
            head = load_json(target)
        except Exception as exc:
            problems.append(Problem("component_head_json_invalid", f"{field}: {exc}", target.as_posix()))
            continue
        if not isinstance(head, dict) or head.get("schema") != schema or not isinstance(head.get("generation"), int):
            problems.append(Problem("component_head_schema_invalid", f"{field} must be {schema} with integer generation", target.as_posix()))
    return problems


def validate_computation_handoff(path: Path, project_root: Path) -> list[Problem]:
    source = path.as_posix()
    try:
        value = load_json(path)
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateKeyError) as exc:
        return [Problem("computation_handoff_json_invalid", str(exc), source)]
    if not isinstance(value, dict) or tuple(value) != HANDOFF_FIELDS:
        return [Problem("computation_handoff_fields_invalid", f"expected ordered fields {HANDOFF_FIELDS}", source)]
    problems: list[Problem] = []
    if value["schema"] != "jin-math-computation-handoff/v1":
        problems.append(Problem("computation_handoff_schema_invalid", "unexpected schema", source))
    if not isinstance(value["problem_id"], str) or not PROJECT_ID.fullmatch(value["problem_id"]):
        problems.append(Problem("computation_problem_id_invalid", "problem_id must be P-XXXX", source))
    for key in ("window_id", "attempt_id", "question", "domain", "reproduction_command"):
        if not _nonempty(value[key]):
            problems.append(Problem("computation_value_invalid", f"{key} must be nonempty", source))
    if value["claim_id"] is not None and not _nonempty(value["claim_id"]):
        problems.append(Problem("computation_claim_id_invalid", "claim_id must be null or nonempty", source))
    if not isinstance(value["objective_sha256"], str) or not SHA256.fullmatch(value["objective_sha256"]):
        problems.append(Problem("computation_objective_hash_invalid", "objective_sha256 invalid", source))
    else:
        objective = project_root / ".research" / "identity" / "objective-core.json"
        if not objective.is_file() or sha256_file(objective) != value["objective_sha256"]:
            problems.append(Problem("computation_objective_binding_mismatch", "handoff does not bind the current Project objective bytes", source))
    if not isinstance(value["assumptions"], list) or not all(isinstance(item, str) for item in value["assumptions"]):
        problems.append(Problem("computation_assumptions_invalid", "assumptions must be strings", source))
    if value["requested_evidence"] not in EVIDENCE_GRADES or value["evidence_grade"] not in EVIDENCE_GRADES:
        problems.append(Problem("computation_evidence_grade_invalid", "unknown requested/actual evidence grade", source))
    backend = value["backend"]
    if not isinstance(backend, dict) or tuple(backend) != ("name", "version", "interface", "inventory_snapshot_sha256"):
        problems.append(Problem("computation_backend_invalid", "backend has invalid closed shape", source))
    else:
        if not all(_nonempty(backend[key]) for key in ("name", "version", "interface")):
            problems.append(Problem("computation_backend_invalid", "backend identity must be nonempty", source))
        snapshot = backend["inventory_snapshot_sha256"]
        if snapshot is not None and (not isinstance(snapshot, str) or not SHA256.fullmatch(snapshot)):
            problems.append(Problem("computation_backend_snapshot_invalid", "inventory snapshot hash invalid", source))
    cannot = value["cannot_imply"]
    if not isinstance(cannot, list) or not cannot or not all(_nonempty(item) for item in cannot):
        problems.append(Problem("computation_nonimplication_missing", "cannot_imply must contain nonempty boundaries", source))
    for field in ("code_artifacts", "result_artifacts"):
        refs = value[field]
        if not isinstance(refs, list) or not refs:
            problems.append(Problem("computation_artifacts_missing", f"{field} must be nonempty", source))
        else:
            for index, ref in enumerate(refs):
                problems.extend(_validate_pointer(ref, project_root, f"{field}[{index}]", source))
    problems.extend(_validate_pointer(value["computation_record"], project_root, "computation_record", source))
    return problems


def validate_verification(path: Path, project_root: Path) -> list[Problem]:
    source = path.as_posix()
    try:
        value = load_json(path)
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateKeyError) as exc:
        return [Problem("verification_json_invalid", str(exc), source)]
    if not isinstance(value, dict) or tuple(value) != VERIFICATION_FIELDS:
        return [Problem("verification_fields_invalid", f"expected ordered fields {VERIFICATION_FIELDS}", source)]
    problems: list[Problem] = []
    if value["schema"] != "jin-math-verification/v1":
        problems.append(Problem("verification_schema_invalid", "unexpected schema", source))
    if not _nonempty(value["verification_id"]) or not isinstance(value["problem_id"], str) or not PROJECT_ID.fullmatch(value["problem_id"]) or not _nonempty(value["claim_id"]):
        problems.append(Problem("verification_identity_invalid", "verification/problem/claim identity invalid", source))
    problems.extend(_validate_pointer(value["candidate"], project_root, "candidate", source))
    dependencies = value["dependencies"]
    if not isinstance(dependencies, list):
        problems.append(Problem("verification_dependencies_invalid", "dependencies must be an array", source))
    else:
        seen: set[tuple[str, str]] = set()
        for index, pointer in enumerate(dependencies):
            problems.extend(_validate_pointer(pointer, project_root, f"dependencies[{index}]", source))
            if isinstance(pointer, dict):
                key = (str(pointer.get("path")), str(pointer.get("sha256")))
                if key in seen:
                    problems.append(Problem("verification_dependency_duplicate", "dependency pointers must be unique", source))
                seen.add(key)
    if not _nonempty(value["reviewer_principal"]) or value["context_isolated"] is not True:
        problems.append(Problem("verification_independence_invalid", "reviewer identity and context_isolated=true are required", source))
    verdict = value["verdict"]
    earliest = value["earliest_error"]
    unresolved = value["unresolved"]
    if verdict not in {"PASS", "FAIL", "INCONCLUSIVE"}:
        problems.append(Problem("verification_verdict_invalid", "verdict must be PASS, FAIL, or INCONCLUSIVE", source))
    elif verdict == "FAIL" and not _nonempty(earliest):
        problems.append(Problem("verification_failure_detail_missing", "FAIL requires earliest_error", source))
    elif verdict != "FAIL" and earliest is not None:
        problems.append(Problem("verification_failure_detail_invalid", "only FAIL may carry earliest_error", source))
    if not isinstance(unresolved, list) or not all(isinstance(item, str) for item in unresolved):
        problems.append(Problem("verification_unresolved_invalid", "unresolved must be a string array", source))
    elif verdict == "PASS" and unresolved:
        problems.append(Problem("verification_pass_unresolved", "PASS requires empty unresolved", source))
    elif verdict == "INCONCLUSIVE" and not unresolved:
        problems.append(Problem("verification_inconclusive_unresolved", "INCONCLUSIVE requires unresolved items", source))
    if not _nonempty(value["checked_scope"]):
        problems.append(Problem("verification_scope_invalid", "checked_scope must be nonempty", source))
    cannot = value["cannot_imply"]
    if not isinstance(cannot, list) or not cannot or not all(_nonempty(item) for item in cannot):
        problems.append(Problem("verification_nonimplication_missing", "cannot_imply must be nonempty", source))
    return problems


def validate_repository_metadata(root: Path) -> list[Problem]:
    problems: list[Problem] = []
    required_schemas = {
        "objective.schema.json",
        "project-registry.schema.json",
        "computation-handoff.schema.json",
        "verification.schema.json",
        "shared-result.schema.json",
    }
    schema_dir = root / "schemas"
    found = {path.name for path in schema_dir.glob("*.json")} if schema_dir.is_dir() else set()
    for missing in sorted(required_schemas - found):
        problems.append(Problem("schema_missing", "required machine contract is missing", f"schemas/{missing}"))
    for path in sorted(schema_dir.glob("*.json")) if schema_dir.is_dir() else []:
        try:
            value = load_json(path)
        except Exception as exc:
            problems.append(Problem("schema_json_invalid", str(exc), path.relative_to(root).as_posix()))
            continue
        if not isinstance(value, dict) or value.get("$schema") != "https://json-schema.org/draft/2020-12/schema" or not _nonempty(value.get("title")):
            problems.append(Problem("schema_header_invalid", "schema requires draft 2020-12 and a title", path.relative_to(root).as_posix()))

    skills = root / ".agents" / "skills"
    names: dict[str, str] = {}
    if not skills.is_dir():
        problems.append(Problem("repo_skills_missing", ".agents/skills is required", ".agents/skills"))
    else:
        for skill_file in sorted(skills.glob("*/SKILL.md")):
            rel = skill_file.relative_to(root).as_posix()
            text = skill_file.read_text(encoding="utf-8")
            match = re.match(r"^---\nname: ([a-z0-9-]+)\ndescription: (.+?)\n---\n", text, re.DOTALL)
            if not match:
                problems.append(Problem("skill_frontmatter_invalid", "SKILL.md requires name and description frontmatter", rel))
                continue
            name, description = match.group(1), match.group(2).strip()
            if name != skill_file.parent.name or name in names or not description:
                problems.append(Problem("skill_identity_invalid", "directory/name must match and be unique", rel))
            names[name] = rel
    return problems


def validate_repository(root: Path) -> list[Problem]:
    root = root.resolve()
    problems = []
    problems.extend(validate_repository_metadata(root))
    problems.extend(validate_skill_dependencies(root))
    problems.extend(validate_registry(root))
    if not any(item.code.startswith("registry_") for item in problems):
        problems.extend(validate_shared_results(root))
    projects = root / "projects"
    if projects.is_dir():
        for path in sorted(projects.glob("P-*/**/computation-handoff.json")):
            project_root = projects / path.relative_to(projects).parts[0]
            problems.extend(validate_computation_handoff(path, project_root))
        for path in sorted(projects.glob("P-*/**/jin-math-verification.json")):
            project_root = projects / path.relative_to(projects).parts[0]
            problems.extend(validate_verification(path, project_root))
    return sorted(problems, key=lambda item: (item.path, item.code, item.message))


def public_registry_entries(root: Path) -> list[dict[str, Any]]:
    entries = registry_entries(root)
    return [{k: v for k, v in item.items() if k != "__file__"} for item in entries]


def catalog_payload(entries: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = sorted(entries, key=lambda item: item["project_id"])
    tracked = ("active", "review_gate", "compute_wait", "terminal_audit", "closed")
    counts = {"projects": len(rows), **{status: sum(item["operational_status"] == status for item in rows) for status in tracked}}
    projected = [
        {
            "project_id": item["project_id"],
            "title": item["title"],
            "problem_class": item["problem_class"],
            "operational_status": item["operational_status"],
            "mathematical_status": item["mathematical_status"],
            "project_path": item["project_path"],
            "current_window_id": item["current_window_id"],
            "dependencies": item["dependencies"],
        }
        for item in rows
    ]
    return {"schema": "jin-math-catalog/v1", "projects": projected, "counts": counts}


def frontier_markdown(entries: Iterable[dict[str, Any]]) -> str:
    rows = sorted(entries, key=lambda item: item["project_id"])
    lines = ["# Research frontier", "", "<!-- Generated by scripts/build_catalog.py. Do not edit manually. -->", ""]
    if not rows:
        lines.append("当前尚未登记研究项目。")
    else:
        lines.extend([
            "| Project | Title | Class | Operational | Mathematical | Window |",
            "|---|---|---|---|---|---|",
        ])
        for item in rows:
            title = item["title"].replace("|", "\\|")
            window = item["current_window_id"] or "-"
            lines.append(f"| {item['project_id']} | {title} | {item['problem_class']} | {item['operational_status']} | {item['mathematical_status']} | {window} |")
    return "\n".join(lines) + "\n"
