#!/usr/bin/env python3
"""Math Research Solve v12: compact projects with lossless object storage.

The module is standard-library only.  It provides deterministic project
construction, read-only startup, generated human views, private export, and
journaled batch migration.  A product Goal is still the mutation authority;
the permanent mathematical objective is an immutable hash-bound object.
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
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


PROJECT_SCHEMA = "math-research-project/v12"
STATE_SCHEMA = "math-research-state/v12"
OBJECTIVE_SCHEMA = "math-research-project-objective/v1"
MEMORY_SCHEMA = "math-research-memory-index/v12"
MEMORY_ITEM_SCHEMA = "math-research-memory-item/v12"
TREE_SCHEMA = "math-research-imported-tree/v12"
MANIFEST_SCHEMA = "math-research-archive-manifest/v12"
VIEW_SCHEMA = "math-research-generated-views/v12"
MIGRATION_PLAN_SCHEMA = "math-research-layout-migration-plan/v12"
MIGRATION_JOURNAL_SCHEMA = "math-research-layout-migration-journal/v12"
EXPORT_SCHEMA = "math-research-private-export/v12"

HEX64 = re.compile(r"^[0-9a-f]{64}$")
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
ROOT_VIEW_FILES = (
    "README.md",
    "当前状态.md",
    "已验证结论.md",
    "障碍与失败.md",
    "下一步路线.md",
)
ROOT_ENTRIES = set(ROOT_VIEW_FILES) | {"project.json", ".research"}
RESEARCH_DIRS = {
    "state",
    "memory",
    "runs",
    "evidence",
    "intakes",
    "imported-projects",
    "objects",
}
TASK_KINDS = {
    "research",
    "external_intake",
    "verification",
    "strategy_review",
    "project_maintenance",
    "export",
}
MEMORY_CLASSES = {
    "verified_fact",
    "verified_refutation",
    "verified_impossibility_boundary",
    "bounded_negative",
    "unresolved_obstacle",
    "reproduction_blocked",
    "conditional_result",
    "open_bridge",
    "known_pitfall",
}
FAILURE_CLASSES = {"verified_refutation", "verified_impossibility_boundary"}
OBSTACLE_CLASSES = {"unresolved_obstacle", "reproduction_blocked"}
TRUST_STATES = {
    "registered_unverified",
    "recorded",
    "reproduced",
    "independently_verified",
    "promoted",
    "superseded",
}


class ResearchError(Exception):
    def __init__(self, code: str, message: str, recovery: str | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.recovery = recovery or "Preserve source bytes and repair the stated invariant before retrying."


def fail(condition: bool, code: str, message: str) -> None:
    if condition:
        raise ResearchError(code, message)


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        fail(key in out, "duplicate_json_key", f"Duplicate JSON key: {key}")
        out[key] = value
    return out


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicates)
    except ResearchError:
        raise
    except Exception as exc:
        raise ResearchError("json_invalid", f"Invalid JSON {path}: {exc}") from exc


def write_bytes_atomic(path: Path, data: bytes, *, replace: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fail(path.exists() and not replace, "destination_exists", f"Refusing to replace immutable path: {path}")
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def write_json(path: Path, value: Any, *, replace: bool = False) -> None:
    write_bytes_atomic(path, canonical_bytes(value), replace=replace)


def require_id(value: Any, label: str) -> str:
    fail(not isinstance(value, str) or SAFE_ID.fullmatch(value) is None, "id_invalid", f"Invalid {label}: {value!r}")
    return value


def require_sha(value: Any, label: str) -> str:
    fail(not isinstance(value, str) or HEX64.fullmatch(value) is None, "hash_invalid", f"Invalid {label} hash.")
    return value


def safe_rel(value: Any, label: str) -> str:
    fail(not isinstance(value, str) or not value, "path_invalid", f"{label} must be nonempty.")
    fail("\x00" in value, "path_invalid", f"NUL in {label}.")
    path = PurePosixPath(value.replace("\\", "/"))
    fail(path.is_absolute() or ".." in path.parts or any(part in ("", ".") for part in path.parts), "path_escape", f"Unsafe {label}: {value}")
    fail(bool(re.match(r"^[A-Za-z]:", value)), "path_escape", f"Drive-qualified {label}: {value}")
    return path.as_posix()


def ptr(root: Path, value: Any, label: str) -> Path:
    fail(not isinstance(value, dict) or set(value) != {"path", "sha256"}, "pointer_invalid", f"{label} must be path/hash.")
    rel = safe_rel(value["path"], f"{label} path")
    expected = require_sha(value["sha256"], label)
    path = root / Path(rel)
    fail(not path.is_file(), "pointer_missing", f"{label} missing: {rel}")
    fail(sha_file(path) != expected, "pointer_hash_mismatch", f"{label} hash mismatch: {rel}")
    return path


def pointer_for(path: Path, root: Path) -> dict[str, str]:
    return {"path": path.relative_to(root).as_posix(), "sha256": sha_file(path)}


def is_reparse_point(path: Path) -> bool:
    """Reject symlinks and Windows reparse points without following them."""
    if path.is_symlink():
        return True
    try:
        return bool(path.lstat().st_file_attributes & 0x400)
    except (AttributeError, OSError):
        return False


def tree_inventory(root: Path) -> list[dict[str, Any]]:
    fail(not root.is_dir(), "source_missing", f"Source directory is absent: {root}")
    entries: list[dict[str, Any]] = []
    folded: dict[str, str] = {}
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix().casefold()):
        rel = path.relative_to(root).as_posix()
        key = rel.casefold()
        if key in folded and folded[key] != rel:
            raise ResearchError("case_collision", f"Case-colliding source paths: {folded[key]} and {rel}")
        folded[key] = rel
        fail(is_reparse_point(path), "reparse_point_rejected", f"Linked/reparse path is not accepted: {rel}")
        if path.is_file():
            stat = path.stat()
            entries.append({"path": rel, "sha256": sha_file(path), "size": stat.st_size})
    return entries


def tree_hash(entries: Iterable[dict[str, Any]]) -> str:
    return sha_bytes(canonical_bytes(list(entries)))


def validate_objective(value: Any, project_id: str) -> dict[str, Any]:
    required = {
        "schema", "project_id", "statement", "domain", "quantifier_order",
        "assumptions", "evidence_standard", "completion_standard", "created_at_utc",
    }
    fail(not isinstance(value, dict) or set(value) != required, "objective_invalid", "Objective keys are invalid.")
    fail(value["schema"] != OBJECTIVE_SCHEMA or value["project_id"] != project_id, "objective_invalid", "Objective identity mismatch.")
    for key in ("statement", "domain", "quantifier_order", "evidence_standard", "completion_standard", "created_at_utc"):
        fail(not isinstance(value[key], str) or not value[key].strip(), "objective_invalid", f"Objective {key} must be nonempty.")
    fail(not isinstance(value["assumptions"], list) or not all(isinstance(x, str) and x for x in value["assumptions"]), "objective_invalid", "Objective assumptions are invalid.")
    return value


def validate_evidence(value: Any, *, required_pass: bool) -> list[dict[str, Any]]:
    fail(not isinstance(value, list), "memory_invalid", "Evidence must be an array.")
    checked: list[dict[str, Any]] = []
    for item in value:
        required = {"role", "locator", "sha256", "verifier_verdict"}
        fail(not isinstance(item, dict) or set(item) != required, "memory_invalid", "Evidence keys are invalid.")
        fail(not all(isinstance(item[k], str) and item[k] for k in ("role", "locator")), "memory_invalid", "Evidence role/locator must be nonempty.")
        require_sha(item["sha256"], "evidence")
        fail(item["verifier_verdict"] not in ("PASS", "FAIL", "INCONCLUSIVE", "NOT_APPLICABLE"), "memory_invalid", "Bad verifier verdict.")
        if required_pass:
            fail(item["verifier_verdict"] != "PASS", "verification_required", "Mathematical exclusion requires verifier PASS evidence.")
        checked.append(item)
    if required_pass:
        fail(not checked, "verification_required", "Mathematical exclusion requires evidence.")
    return checked


def validate_memory_item(value: Any, project_id: str, objective_sha: str) -> dict[str, Any]:
    required = {
        "schema", "project_id", "project_objective_sha256", "memory_id", "classification",
        "statement", "scope", "origin", "trust_state", "evidence", "permits",
        "does_not_imply", "reopen_condition", "tool_requirements", "exclusion_authorized",
        "exclusion_scope", "created_at_utc",
    }
    fail(not isinstance(value, dict) or set(value) != required, "memory_invalid", "Memory item keys are invalid.")
    fail(value["schema"] != MEMORY_ITEM_SCHEMA or value["project_id"] != project_id or value["project_objective_sha256"] != objective_sha, "memory_invalid", "Memory identity mismatch.")
    require_id(value["memory_id"], "memory_id")
    classification = value["classification"]
    fail(classification not in MEMORY_CLASSES, "memory_invalid", f"Unknown memory classification: {classification}")
    fail(value["trust_state"] not in TRUST_STATES, "memory_invalid", "Unknown memory trust state.")
    for key in ("statement", "scope", "reopen_condition", "created_at_utc"):
        fail(not isinstance(value[key], str) or not value[key].strip(), "memory_invalid", f"Memory {key} must be nonempty.")
    for key in ("permits", "does_not_imply", "tool_requirements"):
        fail(not isinstance(value[key], list) or not all(isinstance(x, str) and x for x in value[key]), "memory_invalid", f"Memory {key} must be a string array.")
    fail(not isinstance(value["origin"], dict) or not isinstance(value["origin"].get("kind"), str), "memory_invalid", "Memory origin is invalid.")
    exclusion = classification in FAILURE_CLASSES or classification == "bounded_negative"
    fail(value["exclusion_authorized"] is not exclusion, "memory_scope_invalid", "Exclusion flag does not match classification.")
    if exclusion:
        fail(not isinstance(value["exclusion_scope"], str) or not value["exclusion_scope"].strip(), "memory_scope_invalid", "Exclusion requires an exact scope.")
        fail(value["trust_state"] != "promoted", "verification_required", "Exclusion memory must be promoted.")
        validate_evidence(value["evidence"], required_pass=True)
    else:
        fail(value["exclusion_scope"] is not None, "memory_scope_invalid", "Obstacle/non-exclusion memory cannot carry an exclusion scope.")
        validate_evidence(value["evidence"], required_pass=False)
    if classification in OBSTACLE_CLASSES:
        fail(value["exclusion_authorized"] is not False, "obstacle_misclassified", "An obstacle cannot exclude a route.")
    return value


def validate_memory_index(root: Path, value: Any, project_id: str, objective_sha: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    required = {"schema", "project_id", "project_objective_sha256", "items", "latest_route_review", "updated_at_utc"}
    fail(not isinstance(value, dict) or set(value) != required, "memory_invalid", "Memory index keys are invalid.")
    fail(value["schema"] != MEMORY_SCHEMA or value["project_id"] != project_id or value["project_objective_sha256"] != objective_sha, "memory_invalid", "Memory index identity mismatch.")
    fail(not isinstance(value["items"], list), "memory_invalid", "Memory index items are invalid.")
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item_ptr in value["items"]:
        item_path = ptr(root, item_ptr, "memory item")
        item = validate_memory_item(load_json(item_path), project_id, objective_sha)
        fail(item["memory_id"] in seen, "memory_invalid", "Duplicate memory ID.")
        seen.add(item["memory_id"])
        items.append(item)
    return value, items


def object_path(project: Path, digest: str) -> Path:
    require_sha(digest, "object")
    return project / ".research" / "objects" / "sha256" / digest[:2] / digest


def ingest_file(project: Path, source: Path, expected: dict[str, Any]) -> None:
    digest = require_sha(expected["sha256"], "source")
    fail(source.stat().st_size != expected["size"] or sha_file(source) != digest, "source_changed", f"Source changed: {source}")
    target = object_path(project, digest)
    if target.exists():
        fail(not target.is_file() or target.stat().st_size != expected["size"] or sha_file(target) != digest, "object_collision", f"Object collision: {digest}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    fail(sha_file(target) != digest, "object_write_mismatch", f"Object write mismatch: {digest}")


def render_views(project_id: str, objective: dict[str, Any], state: dict[str, Any], memory_items: list[dict[str, Any]]) -> dict[str, str]:
    counters = state["counters"]
    complete_text = "已完成" if state["project_complete"] else "未完成"
    title = state["display_name"]
    grouped = {key: [] for key in MEMORY_CLASSES}
    for item in memory_items:
        grouped[item["classification"]].append(item)

    def bullets(items: list[dict[str, Any]], *, include_scope: bool = True) -> str:
        if not items:
            return "- 暂无。"
        out: list[str] = []
        for item in sorted(items, key=lambda x: x["memory_id"]):
            scope = f"（范围：{item['scope']}）" if include_scope else ""
            out.append(f"- {item['statement']}{scope}")
            if item["does_not_imply"]:
                out.append("  - 不能推出：" + "；".join(item["does_not_imply"]))
            out.append("  - 重开条件：" + item["reopen_condition"])
        return "\n".join(out)

    readme = (
        f"# {title}\n\n"
        f"本目录是项目 `{project_id}` 的唯一长期入口。项目状态：**{complete_text}**。\n\n"
        f"## 永久终极目标\n\n{objective['statement']}\n\n"
        f"完成标准：{objective['completion_standard']}\n\n"
        "普通任务、导入、整理、核验、导出或产品 Goal 都不能覆盖这个目标；语义变化必须新建或分叉项目。\n\n"
        "## 阅读顺序\n\n"
        "1. [[当前状态]]\n2. [[已验证结论]]\n3. [[障碍与失败]]\n4. [[下一步路线]]\n\n"
        "机器档案保存在隐藏目录 `.research/`。根层 Markdown 是自动生成视图，不作为权威状态手工编辑。\n"
    )
    current = (
        f"# 当前状态\n\n- 项目：{title}\n- 状态：{complete_text}\n"
        f"- 当前任务：{state['current_task'] or '无'}\n- 当前 Run：{state['active_run'] or '无'}\n"
        f"- 累计内部 attempt：{counters['internal_attempts_completed']}\n"
        f"- 距上次路线复盘：{counters['attempts_since_route_review']}\n"
        f"- 是否必须复盘：{'是' if counters['route_review_due'] else '否'}\n"
        f"- 可恢复旧进度：{'是' if state['legacy_resume_capsules'] else '否'}\n\n"
        "当前任务授权与永久终极目标彼此独立。\n"
    )
    conclusions = (
        "# 已验证结论\n\n## 已验证事实\n\n" + bullets(grouped["verified_fact"]) +
        "\n\n## 条件性结果\n\n" + bullets(grouped["conditional_result"]) +
        "\n\n所有结论只能在记录的精确范围内使用。\n"
    )
    obstacles = (
        "# 障碍与失败\n\n"
        "“失败”只表示已有反例或严格不可能性证明；没有找到证明、缺少工具或计算未完成只属于障碍。\n\n"
        "## 已证明证伪或不可能\n\n" + bullets(grouped["verified_refutation"] + grouped["verified_impossibility_boundary"]) +
        "\n\n## 有限域负结果\n\n" + bullets(grouped["bounded_negative"]) +
        "\n\n## 尚未克服的障碍\n\n" + bullets(grouped["unresolved_obstacle"] + grouped["open_bridge"] + grouped["known_pitfall"]) +
        "\n\n## 复现与工具阻塞\n\n" + bullets(grouped["reproduction_blocked"]) + "\n"
    )
    review = state["route_review"]
    routes = review.get("ranked_routes", [])
    if routes:
        route_lines = []
        for index, route in enumerate(routes, 1):
            route_lines.append(f"{index}. {route['title']} — {route['reason']}（重开/推进条件：{route['reopen_condition']}）")
        route_text = "\n".join(route_lines)
    else:
        route_text = "暂无活动路线；项目已经完成或等待新的明确任务。"
    next_routes = (
        "# 下一步路线\n\n"
        f"本页来自第 {review['review_number']} 次路线复盘；复盘不创造新数学。\n\n"
        "## 排序结果\n\n" + route_text + "\n\n"
        "下一轮必须同时参考已验证结论、严格失败、有限负结果、暂时障碍、工具阻塞和重开条件。\n"
    )
    return {
        "README.md": readme,
        "当前状态.md": current,
        "已验证结论.md": conclusions,
        "障碍与失败.md": obstacles,
        "下一步路线.md": next_routes,
    }


def build_manifest(project: Path) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    manifest_rel = ".research/state/manifest.json"
    for path in sorted((p for p in (project / ".research").rglob("*") if p.is_file()), key=lambda p: p.relative_to(project).as_posix().casefold()):
        rel = path.relative_to(project).as_posix()
        if rel == manifest_rel:
            continue
        entries.append({"path": rel, "sha256": sha_file(path), "size": path.stat().st_size})
    return {"schema": MANIFEST_SCHEMA, "entries": entries}


def build_project(project: Path, spec: dict[str, Any], created: str) -> dict[str, Any]:
    fail(project.exists(), "destination_exists", f"Staged project already exists: {project}")
    project.mkdir(parents=True)
    for name in RESEARCH_DIRS:
        (project / ".research" / name).mkdir(parents=True, exist_ok=False)
    project_id = require_id(spec.get("project_id"), "project_id")
    display_name = spec.get("display_name")
    fail(not isinstance(display_name, str) or not display_name, "spec_invalid", "display_name is required.")
    objective = copy.deepcopy(spec.get("objective"))
    validate_objective(objective, project_id)
    objective_path = project / ".research" / "state" / "objective.json"
    write_json(objective_path, objective)
    objective_sha = sha_file(objective_path)

    imported_ptrs: list[dict[str, str]] = []
    source_receipts: list[dict[str, Any]] = []
    for source_spec in spec.get("sources", []):
        source_id = require_id(source_spec.get("source_id"), "source_id")
        source_root = Path(source_spec.get("path", "")).resolve()
        entries = tree_inventory(source_root)
        expected_tree = source_spec.get("expected_tree_sha256")
        if expected_tree:
            fail(tree_hash(entries) != expected_tree, "source_tree_mismatch", f"Source tree mismatch: {source_id}")
        for entry in entries:
            ingest_file(project, source_root / Path(entry["path"]), entry)
        tree = {
            "schema": TREE_SCHEMA,
            "project_id": project_id,
            "source_id": source_id,
            "source_path_at_import": str(source_root),
            "tree_sha256": tree_hash(entries),
            "entries": entries,
            "imported_at_utc": created,
        }
        tree_path = project / ".research" / "imported-projects" / f"{source_id}.json"
        write_json(tree_path, tree)
        imported_ptrs.append(pointer_for(tree_path, project))
        source_receipts.append({"source_id": source_id, "path": str(source_root), "tree_sha256": tree["tree_sha256"], "file_count": len(entries)})

    memory_ptrs: list[dict[str, str]] = []
    memory_items: list[dict[str, Any]] = []
    for raw in spec.get("memory_items", []):
        item = copy.deepcopy(raw)
        item["schema"] = MEMORY_ITEM_SCHEMA
        item["project_id"] = project_id
        item["project_objective_sha256"] = objective_sha
        item.setdefault("created_at_utc", created)
        validate_memory_item(item, project_id, objective_sha)
        item_path = project / ".research" / "memory" / "items" / f"{item['memory_id']}.json"
        write_json(item_path, item)
        memory_ptrs.append(pointer_for(item_path, project))
        memory_items.append(item)

    review = copy.deepcopy(spec.get("route_review", {}))
    review.setdefault("review_number", 1)
    review.setdefault("new_math_performed", False)
    review.setdefault("ranked_routes", [])
    fail(review["new_math_performed"] is not False, "route_review_invalid", "Migration review cannot create mathematics.")
    review_path = project / ".research" / "memory" / "route-review.json"
    write_json(review_path, review)
    memory_index = {
        "schema": MEMORY_SCHEMA,
        "project_id": project_id,
        "project_objective_sha256": objective_sha,
        "items": memory_ptrs,
        "latest_route_review": pointer_for(review_path, project),
        "updated_at_utc": created,
    }
    memory_path = project / ".research" / "memory" / "index.json"
    write_json(memory_path, memory_index)

    counters = copy.deepcopy(spec.get("counters", {}))
    required_counters = {
        "internal_attempts_started", "internal_attempts_completed", "terminal_audits",
        "route_reviews", "attempts_since_route_review", "route_review_due",
    }
    fail(set(counters) != required_counters, "counter_invalid", "Counter keys are invalid.")
    fail(counters["internal_attempts_completed"] > counters["internal_attempts_started"], "counter_invalid", "Completed attempts exceed starts.")
    fail(counters["attempts_since_route_review"] >= 3 and not counters["route_review_due"], "route_review_gate_invalid", "Three attempts require route review.")
    terminal_evidence = copy.deepcopy(spec.get("terminal_evidence", []))
    project_complete = spec.get("project_complete") is True
    if project_complete:
        validate_evidence(terminal_evidence, required_pass=True)
    else:
        fail(bool(terminal_evidence), "completion_invalid", "Incomplete project cannot carry terminal completion evidence.")

    resume_capsules = copy.deepcopy(spec.get("legacy_resume_capsules", []))
    state = {
        "schema": STATE_SCHEMA,
        "project_id": project_id,
        "display_name": display_name,
        "project_objective": pointer_for(objective_path, project),
        "project_complete": project_complete,
        "current_task": None,
        "active_run": None,
        "current_attempt": None,
        "counters": counters,
        "memory_index": pointer_for(memory_path, project),
        "route_review": review,
        "legacy_resume_capsules": resume_capsules,
        "imported_projects": imported_ptrs,
        "terminal_evidence": terminal_evidence,
        "updated_at_utc": created,
    }
    state_path = project / ".research" / "state" / "current.json"
    write_json(state_path, state)
    event = {
        "schema": "math-research-event/v12",
        "project_id": project_id,
        "control_generation": 1,
        "event_type": "MIGRATION_COMPLETE" if spec.get("sources") else "PROJECT_GENESIS",
        "project_objective_sha256": objective_sha,
        "created_at_utc": created,
    }
    event_path = project / ".research" / "state" / "event-g0001.json"
    write_json(event_path, event)
    views = render_views(project_id, objective, state, memory_items)
    for name, content in views.items():
        write_bytes_atomic(project / name, content.encode("utf-8"))
    view_record = {
        "schema": VIEW_SCHEMA,
        "project_id": project_id,
        "control_generation": 1,
        "views": {name: sha_file(project / name) for name in ROOT_VIEW_FILES},
    }
    view_path = project / ".research" / "state" / "views.json"
    write_json(view_path, view_record)
    migration = {
        "schema": "math-research-migration-record/v12",
        "project_id": project_id,
        "sources": source_receipts,
        "non_counting_consolidation_review": True,
        "legacy_goal_bindings_obsolete": True,
        "created_at_utc": created,
    }
    migration_path = project / ".research" / "state" / "migration.json"
    write_json(migration_path, migration)
    write_json(project / ".research" / "runs" / "index.json", {"schema": "math-research-run-index/v12", "runs": [], "legacy_resume_capsules": resume_capsules})
    write_json(project / ".research" / "evidence" / "index.json", {"schema": "math-research-evidence-index/v12", "terminal_evidence": terminal_evidence})
    write_json(project / ".research" / "intakes" / "index.json", {"schema": "math-research-intake-index/v12", "intakes": spec.get("intakes", [])})
    manifest_path = project / ".research" / "state" / "manifest.json"
    write_json(manifest_path, build_manifest(project))
    head = {
        "schema": PROJECT_SCHEMA,
        "project_id": project_id,
        "control_generation": 1,
        "project_objective": pointer_for(objective_path, project),
        "state": pointer_for(state_path, project),
        "event_tail": pointer_for(event_path, project),
        "archive_manifest": pointer_for(manifest_path, project),
        "generated_views": pointer_for(view_path, project),
        "updated_at_utc": created,
    }
    write_json(project / "project.json", head)
    return {"project_id": project_id, "project_sha256": sha_file(project / "project.json"), "sources": source_receipts}


def _validate_tree_objects(project: Path, tree: dict[str, Any], *, full: bool) -> None:
    fail(tree.get("schema") != TREE_SCHEMA, "tree_invalid", "Imported tree schema is invalid.")
    entries = tree.get("entries")
    fail(not isinstance(entries, list) or tree_hash(entries) != tree.get("tree_sha256"), "tree_invalid", "Imported tree hash mismatch.")
    for entry in entries:
        rel = safe_rel(entry.get("path"), "imported tree path")
        digest = require_sha(entry.get("sha256"), "imported tree")
        fail(not isinstance(entry.get("size"), int) or entry["size"] < 0, "tree_invalid", f"Bad size: {rel}")
        obj = object_path(project, digest)
        fail(not obj.is_file(), "object_missing", f"Missing object {digest} for {rel}")
        if full:
            fail(obj.stat().st_size != entry["size"] or sha_file(obj) != digest, "object_hash_mismatch", f"Object mismatch: {digest}")


def startup(project: Path, *, full: bool = False) -> dict[str, Any]:
    head_path = project / "project.json"
    fail(not head_path.is_file(), "project_missing", f"project.json is absent: {project}")
    head = load_json(head_path)
    if head.get("schema") != PROJECT_SCHEMA:
        return {"classification": "delegate_startup_v6", "schema": head.get("schema"), "project_sha256": sha_file(head_path)}
    required = {"schema", "project_id", "control_generation", "project_objective", "state", "event_tail", "archive_manifest", "generated_views", "updated_at_utc"}
    fail(set(head) != required, "project_invalid", "v12 project head keys are invalid.")
    project_id = require_id(head["project_id"], "project_id")
    objective_path = ptr(project, head["project_objective"], "objective")
    objective = validate_objective(load_json(objective_path), project_id)
    state_path = ptr(project, head["state"], "state")
    state = load_json(state_path)
    state_keys = {
        "schema", "project_id", "display_name", "project_objective", "project_complete",
        "current_task", "active_run", "current_attempt", "counters", "memory_index",
        "route_review", "legacy_resume_capsules", "imported_projects", "terminal_evidence",
        "updated_at_utc",
    }
    fail(set(state) != state_keys or state.get("schema") != STATE_SCHEMA or state.get("project_id") != project_id, "state_invalid", "State keys or identity mismatch.")
    fail(state.get("project_objective") != head["project_objective"], "objective_changed", "State objective differs from immutable head.")
    ptr(project, head["event_tail"], "event tail")
    manifest_path = ptr(project, head["archive_manifest"], "manifest")
    view_path = ptr(project, head["generated_views"], "view record")
    view_record = load_json(view_path)
    memory_path = ptr(project, state["memory_index"], "memory index")
    _, memory_items = validate_memory_index(project, load_json(memory_path), project_id, head["project_objective"]["sha256"])
    counters = state.get("counters")
    fail(not isinstance(counters, dict) or counters.get("internal_attempts_completed", 0) > counters.get("internal_attempts_started", -1), "counter_invalid", "Counters are invalid.")
    fail(counters.get("attempts_since_route_review", 0) >= 3 and not counters.get("route_review_due"), "route_review_gate_invalid", "Route review gate is invalid.")
    expected_views = render_views(project_id, objective, state, memory_items)
    drift: list[str] = []
    for name, content in expected_views.items():
        path = project / name
        expected_sha = sha_bytes(content.encode("utf-8"))
        if not path.is_file() or sha_file(path) != expected_sha or view_record.get("views", {}).get(name) != expected_sha:
            drift.append(name)
    root_names = {p.name for p in project.iterdir()}
    fail(root_names != ROOT_ENTRIES, "root_layout_invalid", f"Root entries differ from v12 layout: {sorted(root_names ^ ROOT_ENTRIES)}")
    research_names = {p.name for p in (project / ".research").iterdir() if p.is_dir()}
    fail(research_names != RESEARCH_DIRS, "research_layout_invalid", f".research directories differ: {sorted(research_names ^ RESEARCH_DIRS)}")
    manifest = load_json(manifest_path)
    fail(manifest.get("schema") != MANIFEST_SCHEMA or not isinstance(manifest.get("entries"), list), "manifest_invalid", "Manifest is invalid.")
    allowed_files: set[str] = {entry["path"] for entry in manifest["entries"]}
    allowed_files.add(manifest_path.relative_to(project).as_posix())
    actual_files = {p.relative_to(project).as_posix() for p in (project / ".research").rglob("*") if p.is_file()}
    fail(actual_files != allowed_files, "manifest_coverage_invalid", f"Manifest coverage differs: {len(actual_files ^ allowed_files)} path(s).")
    for entry in manifest["entries"]:
        rel = safe_rel(entry.get("path"), "manifest path")
        path = project / Path(rel)
        fail(not path.is_file(), "manifest_missing_file", f"Manifest file missing: {rel}")
        if full:
            fail(path.stat().st_size != entry.get("size") or sha_file(path) != entry.get("sha256"), "archive_hash_mismatch", f"Manifest mismatch: {rel}")
    for tree_ptr in state.get("imported_projects", []):
        _validate_tree_objects(project, load_json(ptr(project, tree_ptr, "imported project")), full=full)
    classification = "v12_view_drift" if drift else "v12_ready"
    return {
        "classification": classification,
        "schema_version": 12,
        "project_id": project_id,
        "project_sha256": sha_file(head_path),
        "control_generation": head["control_generation"],
        "project_complete": state["project_complete"],
        "objective": objective["completion_standard"],
        "counters": counters,
        "memory_entry_count": len(memory_items),
        "route_review_due": counters["route_review_due"],
        "current_task": state["current_task"],
        "active_run": state["active_run"],
        "legacy_resume_available": bool(state["legacy_resume_capsules"]),
        "view_drift": drift,
        "audit_mode_used": "Full" if full else "Auto",
    }


def repair_views(project: Path, goal_status: str) -> dict[str, Any]:
    fail(goal_status != "active", "goal_gate", "Generated-view repair requires a fresh active Goal.")
    head = load_json(project / "project.json")
    fail(head.get("schema") != PROJECT_SCHEMA, "project_invalid", "Not a v12 project.")
    project_id = head["project_id"]
    objective = load_json(ptr(project, head["project_objective"], "objective"))
    state = load_json(ptr(project, head["state"], "state"))
    _, items = validate_memory_index(project, load_json(ptr(project, state["memory_index"], "memory index")), project_id, head["project_objective"]["sha256"])
    views = render_views(project_id, objective, state, items)
    for name, content in views.items():
        write_bytes_atomic(project / name, content.encode("utf-8"), replace=True)
    view_path = ptr(project, head["generated_views"], "view record")
    view_record = load_json(view_path)
    fail(view_record.get("views") != {name: sha_file(project / name) for name in ROOT_VIEW_FILES}, "view_record_invalid", "View record does not match deterministic views.")
    return {"repaired": list(ROOT_VIEW_FILES), "project_sha256": sha_file(project / "project.json")}


def restore_tree(project: Path, source_id: str, output: Path) -> dict[str, Any]:
    fail(output.exists(), "destination_exists", f"Restore destination exists: {output}")
    tree_path = project / ".research" / "imported-projects" / f"{require_id(source_id, 'source_id')}.json"
    tree = load_json(tree_path)
    _validate_tree_objects(project, tree, full=True)
    output.mkdir(parents=True)
    for entry in tree["entries"]:
        target = output / Path(safe_rel(entry["path"], "restore path"))
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(object_path(project, entry["sha256"]), target)
    rebuilt = tree_inventory(output)
    fail(tree_hash(rebuilt) != tree["tree_sha256"], "restore_mismatch", "Restored tree hash mismatch.")
    return {"source_id": source_id, "tree_sha256": tree["tree_sha256"], "file_count": len(rebuilt)}


def prepare_batch(spec_path: Path, output: Path) -> dict[str, Any]:
    fail(output.exists() and any(output.iterdir()), "stage_not_empty", f"Stage is not empty: {output}")
    spec = load_json(spec_path)
    fail(not isinstance(spec, dict) or set(spec) != {"schema", "projects", "created_at_utc"} or spec["schema"] != "math-research-batch-migration-spec/v12", "spec_invalid", "Batch migration spec is invalid.")
    fail(not isinstance(spec["projects"], list) or not spec["projects"], "spec_invalid", "Batch requires projects.")
    output.mkdir(parents=True, exist_ok=True)
    projects_root = output / "projects"
    projects_root.mkdir()
    seen_targets: set[str] = set()
    built: list[dict[str, Any]] = []
    for project_spec in spec["projects"]:
        source_root = Path(project_spec["current_root"]).resolve()
        target_root = Path(project_spec["target_root"]).resolve()
        target_key = str(target_root).casefold()
        fail(target_key in seen_targets, "target_collision", f"Duplicate target: {target_root}")
        seen_targets.add(target_key)
        fail(not source_root.is_dir(), "source_missing", f"Current root missing: {source_root}")
        source_inventory = tree_inventory(source_root)
        fail(tree_hash(source_inventory) != project_spec["expected_current_tree_sha256"], "source_tree_mismatch", f"Current tree changed: {source_root}")
        staged = projects_root / project_spec["project_id"]
        result = build_project(staged, project_spec, spec["created_at_utc"])
        check = startup(staged, full=True)
        fail(check["classification"] != "v12_ready", "staged_project_invalid", f"Staged project failed startup: {project_spec['project_id']}")
        built.append({
            "project_id": project_spec["project_id"],
            "current_root": str(source_root),
            "target_root": str(target_root),
            "expected_current_tree_sha256": project_spec["expected_current_tree_sha256"],
            "staged_root": str(staged.resolve()),
            "staged_tree_sha256": tree_hash(tree_inventory(staged)),
            "project_sha256": result["project_sha256"],
        })
    plan = {"schema": MIGRATION_PLAN_SCHEMA, "projects": built, "created_at_utc": spec["created_at_utc"]}
    plan_path = output / "migration-plan.json"
    write_json(plan_path, plan)
    return {"plan_path": str(plan_path.resolve()), "plan_sha256": sha_file(plan_path), "project_count": len(built)}


def _same_volume(a: Path, b: Path) -> bool:
    return a.resolve().drive.casefold() == b.resolve().drive.casefold()


def commit_batch(plan_path: Path, expected_plan_sha: str, goal_status: str) -> dict[str, Any]:
    fail(goal_status != "active", "goal_gate", "Batch migration commit requires a fresh active Goal.")
    fail(sha_file(plan_path) != require_sha(expected_plan_sha, "plan"), "plan_hash_mismatch", "Migration plan hash mismatch.")
    plan = load_json(plan_path)
    fail(plan.get("schema") != MIGRATION_PLAN_SCHEMA, "plan_invalid", "Migration plan schema is invalid.")
    stage = plan_path.parent
    recovery = stage / "recovery"
    fail(recovery.exists(), "recovery_exists", "Recovery directory already exists.")
    recovery.mkdir()
    journal_path = stage / "commit-journal.json"
    journal = {"schema": MIGRATION_JOURNAL_SCHEMA, "plan_sha256": expected_plan_sha, "status": "moving", "moves": [], "created_at_utc": now_utc()}
    write_json(journal_path, journal)
    installed: list[dict[str, Any]] = []
    try:
        for entry in plan["projects"]:
            current = Path(entry["current_root"])
            target = Path(entry["target_root"])
            staged = Path(entry["staged_root"])
            fail(not _same_volume(current, stage) or not _same_volume(target, stage), "cross_volume", "Batch migration requires same-volume moves.")
            fail(tree_hash(tree_inventory(current)) != entry["expected_current_tree_sha256"], "source_tree_mismatch", f"Source changed before commit: {current}")
            fail(tree_hash(tree_inventory(staged)) != entry["staged_tree_sha256"], "stage_changed", f"Stage changed before commit: {staged}")
            startup(staged, full=True)
            if target != current:
                fail(target.exists(), "target_exists", f"Renamed target already exists: {target}")
            backup = recovery / entry["project_id"]
            shutil.move(str(current), str(backup))
            move_state = {"current": current, "target": target, "backup": backup, "new_installed": False}
            installed.append(move_state)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(staged), str(target))
            move_state["new_installed"] = True
            journal["moves"].append({"project_id": entry["project_id"], "current_root": str(current), "target_root": str(target), "backup_root": str(backup), "completed": True})
            write_json(journal_path, journal, replace=True)
            check = startup(target, full=True)
            fail(check["classification"] != "v12_ready", "post_commit_invalid", f"Installed project failed Full Startup: {target}")
        journal["status"] = "committed"
        journal["completed_at_utc"] = now_utc()
        write_json(journal_path, journal, replace=True)
        return {"project_count": len(installed), "journal": str(journal_path), "status": "committed", "targets": [str(x["target"]) for x in installed]}
    except Exception:
        for move_state in reversed(installed):
            current = move_state["current"]
            target = move_state["target"]
            backup = move_state["backup"]
            rejected = recovery / (backup.name + "-rejected-v12")
            if move_state["new_installed"] and target.exists() and not rejected.exists():
                shutil.move(str(target), str(rejected))
            if backup.exists() and not current.exists():
                current.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(backup), str(current))
        journal["status"] = "failed_rolled_back"
        journal["failed_at_utc"] = now_utc()
        write_json(journal_path, journal, replace=True)
        raise


def rollback_batch(journal_path: Path, goal_status: str) -> dict[str, Any]:
    fail(goal_status != "active", "goal_gate", "Rollback requires a fresh active Goal.")
    journal = load_json(journal_path)
    fail(journal.get("schema") != MIGRATION_JOURNAL_SCHEMA or journal.get("status") != "committed", "journal_invalid", "Only a committed batch can be rolled back.")
    rollback_root = journal_path.parent / "rollback-v12"
    fail(rollback_root.exists(), "destination_exists", "Rollback staging already exists.")
    rollback_root.mkdir()
    restored = []
    for move in reversed(journal["moves"]):
        current = Path(move["current_root"])
        target = Path(move["target_root"])
        backup = Path(move["backup_root"])
        fail(not target.is_dir() or not backup.is_dir() or current.exists(), "rollback_conflict", f"Rollback conflict for {move['project_id']}")
        rejected = rollback_root / move["project_id"]
        shutil.move(str(target), str(rejected))
        current.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(backup), str(current))
        restored.append(move["project_id"])
    journal["status"] = "rolled_back"
    journal["rolled_back_at_utc"] = now_utc()
    write_json(journal_path, journal, replace=True)
    return {"restored": restored, "rejected_v12_root": str(rollback_root)}


def export_project(project: Path, profile: str, output: Path) -> dict[str, Any]:
    check = startup(project, full=True)
    fail(check["classification"] != "v12_ready", "project_invalid", "Project must pass Full Startup before export.")
    fail(output.exists(), "destination_exists", f"Export destination exists: {output}")
    fail(profile not in ("intermediate", "final", "full-private"), "profile_invalid", "Unknown export profile.")
    if profile == "final":
        fail(not check["project_complete"], "project_not_complete", "Final export requires project_complete=true.")
    output.mkdir(parents=True)
    if profile == "full-private":
        shutil.copytree(project, output / "project", dirs_exist_ok=False)
    else:
        for name in ROOT_VIEW_FILES + ("project.json",):
            shutil.copyfile(project / name, output / name)
        state = load_json(ptr(project, load_json(project / "project.json")["state"], "state"))
        if profile == "final":
            write_json(output / "TERMINAL_EVIDENCE.json", {"terminal_evidence": state["terminal_evidence"]})
    files = tree_inventory(output)
    record = {"schema": EXPORT_SCHEMA, "profile": profile, "source_project_sha256": check["project_sha256"], "entries": files, "created_at_utc": now_utc()}
    write_json(output / "EXPORT_MANIFEST.json", record)
    return {"profile": profile, "output": str(output.resolve()), "file_count": len(files) + 1}


def simulate_transition(state: dict[str, Any], kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(state)
    counters = out["counters"]
    if kind == "TASK_START":
        fail(out["current_task"] is not None, "task_active", "A task is already active.")
        fail(payload.get("task_kind") not in TASK_KINDS, "task_kind_invalid", "Unsupported task kind.")
        fail(payload.get("project_objective_sha256") != out["project_objective"]["sha256"], "objective_changed", "Task cannot replace the permanent objective.")
        out["current_task"] = {"task_id": require_id(payload.get("task_id"), "task_id"), "task_kind": payload["task_kind"]}
    elif kind == "TASK_END":
        fail(out["current_task"] is None, "task_missing", "No active task.")
        fail(out["active_run"] is not None, "run_active", "End Run before task.")
        out["current_task"] = None
    elif kind == "RUN_START":
        fail(out["current_task"] is None, "task_missing", "Run requires a task.")
        fail(out["active_run"] is not None, "run_active", "Run already active.")
        run_id = require_id(payload.get("run_id"), "run_id")
        out["active_run"] = {"run_id": run_id, "path": f".research/runs/{run_id}"}
    elif kind == "RUN_END":
        fail(out["active_run"] is None, "run_missing", "No active Run.")
        fail(out.get("current_attempt") is not None, "attempt_active", "Attempt still active.")
        out["active_run"] = None
    elif kind == "ATTEMPT_START":
        fail(out["current_task"] is None or out["current_task"]["task_kind"] != "research", "research_task_required", "Attempt requires research task.")
        fail(out["active_run"] is None, "run_required", "Attempt requires Run.")
        fail(out.get("current_attempt") is not None, "attempt_active", "Attempt already active.")
        fail(counters["route_review_due"], "route_review_required", "Complete route review first.")
        counters["internal_attempts_started"] += 1
        out["current_attempt"] = require_id(payload.get("attempt_id"), "attempt_id")
    elif kind == "ATTEMPT_END":
        fail(out.get("current_attempt") is None, "attempt_missing", "No active attempt.")
        counters["internal_attempts_completed"] += 1
        counters["attempts_since_route_review"] += 1
        out["current_attempt"] = None
        counters["route_review_due"] = counters["attempts_since_route_review"] >= 3
    elif kind == "ROUTE_REVIEW_COMPLETE":
        fail(not counters["route_review_due"], "route_review_not_due", "Route review is not due.")
        fail(payload.get("new_math_performed") is not False, "route_review_new_math", "Route review cannot create mathematics.")
        counters["route_reviews"] += 1
        counters["attempts_since_route_review"] = 0
        counters["route_review_due"] = False
    else:
        raise ResearchError("transition_invalid", f"Unsupported transition: {kind}")
    return out


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("startup")
    s.add_argument("--project", required=True)
    s.add_argument("--full", action="store_true")
    b = sub.add_parser("prepare-batch")
    b.add_argument("--spec", required=True)
    b.add_argument("--output", required=True)
    c = sub.add_parser("commit-batch")
    c.add_argument("--plan", required=True)
    c.add_argument("--expected-plan-sha256", required=True)
    c.add_argument("--goal-status", required=True)
    r = sub.add_parser("rollback-batch")
    r.add_argument("--journal", required=True)
    r.add_argument("--goal-status", required=True)
    v = sub.add_parser("repair-views")
    v.add_argument("--project", required=True)
    v.add_argument("--goal-status", required=True)
    t = sub.add_parser("restore-tree")
    t.add_argument("--project", required=True)
    t.add_argument("--source-id", required=True)
    t.add_argument("--output", required=True)
    e = sub.add_parser("export")
    e.add_argument("--project", required=True)
    e.add_argument("--profile", required=True)
    e.add_argument("--output", required=True)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "startup":
            data = startup(Path(args.project), full=args.full)
        elif args.command == "prepare-batch":
            data = prepare_batch(Path(args.spec), Path(args.output))
        elif args.command == "commit-batch":
            data = commit_batch(Path(args.plan), args.expected_plan_sha256, args.goal_status)
        elif args.command == "rollback-batch":
            data = rollback_batch(Path(args.journal), args.goal_status)
        elif args.command == "repair-views":
            data = repair_views(Path(args.project), args.goal_status)
        elif args.command == "restore-tree":
            data = restore_tree(Path(args.project), args.source_id, Path(args.output))
        else:
            data = export_project(Path(args.project), args.profile, Path(args.output))
        print(json.dumps({"ok": True, "data": data}, ensure_ascii=False, indent=2))
        return 0
    except ResearchError as exc:
        print(json.dumps({"ok": False, "error": {"code": exc.code, "message": exc.message, "recovery": exc.recovery}}, ensure_ascii=False, indent=2))
        return 2
    except Exception as exc:
        print(json.dumps({"ok": False, "error": {"code": "internal_error", "message": f"{type(exc).__name__}: {exc}", "recovery": "Preserve the stage and journal before retrying."}}, ensure_ascii=False, indent=2))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
