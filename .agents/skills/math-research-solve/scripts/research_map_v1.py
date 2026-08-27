#!/usr/bin/env python3
"""Validate the official v13 research-map component format v1."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any
from v13_common import configure_stdio

SCHEMA = "math-research-map/v1"
VALIDATION_SCHEMA = "math-research-map-validation/v1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
AUTH_PREFIXES = ("memory:", "route-review:", "evidence:", "asset:", "project:")
RESULT_CALLOUT_TYPES = {"theorem", "proposition"}
RESULT_DIRECTORY = "研究成果"
MAIN_SURVEY = "01-主研究地图.md"
GLOSSARY_NOTE = "03-术语与记号.md"
GLOSSARY_MARKER_RE = re.compile(r"<!--\s*research-map-glossary:v1\s*-->")
GLOSSARY_LINK_RE = re.compile(
    r"\[\[(?:\./)?03-术语与记号(?:\.md)?(?:[|#][^\]]+)?\]\]"
)
GLOSSARY_FIELD_NAMES = ("定义", "在本项目中的作用", "不要混淆")
MIN_GLOSSARY_ENTRIES = 6
MIN_GLOSSARY_FIELD_CHARS = 8
TRACKED_TOPIC_SCHEMA = "research-map-tracked-topic:v1"
TRACKED_TOPIC_FIELD_NAMES = ("状态", "进度", "排序")
MIN_TRACKED_TOPIC_FIELD_CHARS = 12
TRACKED_TOPIC_MARKER_RE = re.compile(
    r"<!--\s*research-map-tracked-topic:v1\s+(?P<payload>\{[^\r\n]*\})\s*-->"
)
SUFFICIENT_TOPIC_SCHEMA = "research-map-sufficient-condition-topic:v1"
SUFFICIENT_REGISTER_SCHEMA = "math-research-sufficient-condition-register/v1"
SUFFICIENT_REGISTER_FIELDS = (
    "充分命题清单", "逻辑关系", "难度排序", "排除项", "来源覆盖",
)
MIN_SUFFICIENT_REGISTER_FIELD_CHARS = 12
SUFFICIENT_TOPIC_MARKER_RE = re.compile(
    r"<!--\s*research-map-sufficient-condition-topic:v1\s+(?P<payload>\{[^\r\n]*\})\s*-->"
)
SUFFICIENT_DEFINITION_SCHEMA = "research-map-sufficient-condition-definitions:v1"
SUFFICIENT_DEFINITION_MARKER_RE = re.compile(
    r"<!--\s*research-map-sufficient-condition-definitions:v1\s+(?P<payload>\{[^\r\n]*\})\s*-->"
)
SUFFICIENT_ENTRY_MARKER_RE = re.compile(
    r"<!--\s*research-map-sufficient-condition-entry:v1\s+(?P<payload>\{[^\r\n]*\})\s*-->"
)
SUFFICIENT_EXCLUSION_MARKER_RE = re.compile(
    r"<!--\s*research-map-sufficient-condition-exclusion:v1\s+(?P<payload>\{[^\r\n]*\})\s*-->"
)
SUFFICIENT_SOURCE_MARKER_RE = re.compile(
    r"<!--\s*research-map-sufficient-condition-source:v1\s+(?P<payload>\{[^\r\n]*\})\s*-->"
)
SYNTHESIS_ROLES = (
    "objective-context",
    "unified-method-spine",
    "historical-development",
    "route-genealogy",
    "cross-route-structure",
    "global-state",
    "frontier",
    "authority-coverage",
)
SYNTHESIS_MARKER_RE = re.compile(
    r"<!--\s*research-map-synthesis:(?P<role>[a-z0-9-]+)\s*-->"
)
SYNTHESIS_PLACEHOLDERS = (
    "todo", "tbd", "placeholder", "to be written", "待补正文", "待写正文",
    "此处略", "内容略", "占位文本",
)
MIN_SYNTHESIS_SECTION_CHARS = 160
MIN_SYNTHESIS_NOTE_CHARS = 1600
FLAT_NODE_RE = re.compile(r"^(?:研究成果-|(?:\d+-)?(?P<category>里程碑|路线|实验|桥梁)-)")
RESULT_PLACEHOLDERS = (
    "proof omitted", "proof sketch", "see the route", "see route", "see elsewhere",
    "todo", "to be proved", "证明略", "证明省略", "证明思路", "证明概要", "证明见",
    "参见路线", "见路线", "详见路线", "留待证明", "待证明", "待补",
)
CALLOUT_RE = re.compile(
    r"(?m)^>\s*\[!(?P<kind>[A-Za-z0-9_-]+)\][+-]?(?:\s+(?P<title>[^\n]*))?\n"
    r"(?P<body>(?:^>[^\n]*(?:\n|$))+)",
)
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
HEADING_RE = re.compile(r"(?m)^(?P<marks>#{1,6})\s+(?P<title>[^\n]+?)\s*$")


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


def issue_receipt(value: Any, *, route_review_sha256: str, authoritative_memory_ids: set[str], map_root: Path | None = None) -> dict[str, Any]:
    issues = validate_control(value, for_attempt=True)
    if map_root is None:
        issues.append({"code": "map_synthesis_root_required", "path": MAIN_SURVEY})
    else:
        issues.extend(validate_visible_layout(value, map_root))
        issues.extend(validate_global_synthesis(map_root))
        issues.extend(validate_project_glossary(map_root))
        issues.extend(validate_tracked_topic_sections(
            map_root,
            authority_manifest_sha256=value.get("authority_manifest_sha256") if isinstance(value, dict) else None,
        ))
        issues.extend(validate_terminal_sufficient_condition_sections(
            map_root,
            project_id=value.get("project_id") if isinstance(value, dict) else None,
            project_objective_sha256=value.get("project_objective_sha256") if isinstance(value, dict) else None,
            authority_manifest_sha256=value.get("authority_manifest_sha256") if isinstance(value, dict) else None,
            route_ids={
                item.get("route_id")
                for item in value.get("routes", [])
                if isinstance(value, dict) and isinstance(item, dict) and isinstance(item.get("route_id"), str)
            } if isinstance(value, dict) else set(),
            require_definition_card=True,
        ))
    if isinstance(value, dict) and value.get("results"):
        if map_root is None:
            issues.append({"code": "result_note_root_missing", "path": "results"})
        else:
            note_issues, _ = validate_result_notes(value, map_root)
            issues.extend(note_issues)
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
        "authority_manifest_sha256": value["authority_manifest_sha256"],
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

    def validate_overview(value: Any, path: str) -> None:
        keys = {"method_family", "baseline_method", "project_modification", "high_level_mechanism"}
        if not isinstance(value, dict) or set(value) != keys or not all(nonempty(value.get(key)) for key in keys):
            issue("method_overview_missing", path)

    def validate_definitions(value: Any, path: str) -> None:
        if not isinstance(value, list):
            issue("parameter_definitions_invalid", path)
            return
        keys = {"symbol", "meaning", "frozen_value", "choice_reason", "evidence_refs"}
        for index, definition in enumerate(value):
            current = f"{path}[{index}]"
            if (
                not isinstance(definition, dict)
                or set(definition) != keys
                or not all(nonempty(definition.get(key)) for key in ("symbol", "meaning", "frozen_value", "choice_reason"))
                or not refs_ok(definition.get("evidence_refs"))
            ):
                issue("parameter_definition_missing", current)

    required = {
        "schema", "project_id", "project_objective_sha256", "authority_manifest_sha256",
        "status", "milestones", "results", "routes",
    }
    if not isinstance(value, dict) or set(value) != required:
        return [{"code": "map_fields_invalid", "path": ".research/research-map.json"}]
    if value.get("schema") != SCHEMA:
        issue("map_schema_invalid", "schema")
    if not nonempty(value.get("project_id")):
        issue("project_id_invalid", "project_id")
    for key in ("project_objective_sha256", "authority_manifest_sha256"):
        if not isinstance(value.get(key), str) or not HEX64.fullmatch(value[key]):
            issue("hash_invalid", key)
    if value.get("status") not in ("current", "review_required", "historical"):
        issue("map_status_invalid", "status")
    if for_attempt and value.get("status") != "current":
        issue("map_not_activation_eligible", "status")

    node_ids: set[str] = set()
    milestones = value.get("milestones")
    if not isinstance(milestones, list):
        issue("milestones_invalid", "milestones")
        milestones = []
    milestone_keys = {
        "milestone_id", "conclusion", "method_overview", "parameter_definitions",
        "method_spine", "reusable_structures", "bottleneck_effect", "cannot_imply",
        "evidence_refs", "status",
    }
    for index, item in enumerate(milestones):
        path = f"milestones[{index}]"
        if not isinstance(item, dict) or set(item) != milestone_keys:
            issue("milestone_fields_invalid", path)
            continue
        node_id = item.get("milestone_id")
        if not nonempty(node_id) or node_id in node_ids:
            issue("map_node_id_invalid", path + ".milestone_id")
        else:
            node_ids.add(node_id)
        for key in ("conclusion", "method_spine", "bottleneck_effect", "cannot_imply"):
            if not nonempty(item.get(key)):
                issue("milestone_causality_missing", path + "." + key)
        validate_overview(item.get("method_overview"), path + ".method_overview")
        validate_definitions(item.get("parameter_definitions"), path + ".parameter_definitions")
        if not isinstance(item.get("reusable_structures"), list) or not item["reusable_structures"] or not all(nonempty(x) for x in item["reusable_structures"]):
            issue("reusable_structures_missing", path + ".reusable_structures")
        if not refs_ok(item.get("evidence_refs")):
            issue("method_source_missing", path + ".evidence_refs")
        if item.get("status") not in ("verified", "bounded", "review_required"):
            issue("milestone_status_invalid", path + ".status")

    results = value.get("results")
    if not isinstance(results, list):
        issue("result_registry_invalid", "results")
        results = []
    result_keys = {
        "result_id", "status", "note_path", "theorem_callout_type", "proof_heading",
        "statement", "scope", "method_overview",
        "parameter_definitions", "method_spine", "novelty_and_source",
        "relation_to_objective", "reusable_value", "cannot_imply", "evidence_refs",
    }
    for index, item in enumerate(results):
        path = f"results[{index}]"
        if not isinstance(item, dict) or set(item) != result_keys:
            issue("result_fields_invalid", path)
            continue
        node_id = item.get("result_id")
        if not nonempty(node_id) or node_id in node_ids:
            issue("map_node_id_invalid", path + ".result_id")
        else:
            node_ids.add(node_id)
        for key in (
            "note_path", "proof_heading", "statement", "scope", "method_spine", "novelty_and_source",
            "relation_to_objective", "reusable_value", "cannot_imply",
        ):
            if not nonempty(item.get(key)):
                issue("result_content_missing", path + "." + key)
        if item.get("theorem_callout_type") not in RESULT_CALLOUT_TYPES:
            issue("result_callout_type_invalid", path + ".theorem_callout_type")
        validate_overview(item.get("method_overview"), path + ".method_overview")
        validate_definitions(item.get("parameter_definitions"), path + ".parameter_definitions")
        if item.get("status") not in ("independently_verified", "verified", "conditional", "review_required"):
            issue("result_status_invalid", path + ".status")
        if not refs_ok(item.get("evidence_refs")):
            issue("result_evidence_missing", path + ".evidence_refs")

    routes = value.get("routes")
    if not isinstance(routes, list) or not routes:
        issue("routes_invalid", "routes")
        routes = []
    route_keys = {
        "route_id", "status", "mathematical_object", "objective_mechanism",
        "evidence_boundary", "missing_work", "success_gate", "candidate_failure_gate",
        "failure_scope", "verified_route_failure_ref", "evidence_refs",
    }
    route_ids: set[str] = set()
    for index, item in enumerate(routes):
        path = f"routes[{index}]"
        if not isinstance(item, dict) or set(item) != route_keys:
            issue("route_fields_invalid", path)
            continue
        route_id = item.get("route_id")
        if not nonempty(route_id) or route_id in route_ids or route_id in node_ids:
            issue("map_node_id_invalid", path + ".route_id")
        else:
            route_ids.add(route_id)
            node_ids.add(route_id)
        if item.get("status") not in ("landscape", "paused", "closed", "invalidated", "historical"):
            issue("route_status_invalid", path + ".status")
        for key in ("mathematical_object", "objective_mechanism", "evidence_boundary", "missing_work", "success_gate", "candidate_failure_gate"):
            if not nonempty(item.get(key)):
                issue("route_explanation_missing", path + "." + key)
        if item.get("failure_scope") not in ("candidate_only", "route_exact_scope"):
            issue("failure_scope_invalid", path + ".failure_scope")
        if item.get("failure_scope") == "route_exact_scope":
            ref = item.get("verified_route_failure_ref")
            if not nonempty(ref) or not ref.startswith("memory:verified-impossibility-boundary/"):
                issue("candidate_failure_expanded", path + ".verified_route_failure_ref")
        elif item.get("verified_route_failure_ref") is not None:
            issue("candidate_failure_expanded", path + ".verified_route_failure_ref")
        if not refs_ok(item.get("evidence_refs")):
            issue("route_evidence_missing", path + ".evidence_refs")

    return issues


def _result_note_path(map_root: Path, relative: Any) -> Path | None:
    if not nonempty(relative):
        return None
    posix = PurePosixPath(relative.replace("\\", "/"))
    if posix.is_absolute() or not posix.parts or ".." in posix.parts or posix.suffix.lower() != ".md":
        return None
    root = map_root.resolve()
    path = (root / Path(*posix.parts)).resolve()
    if root not in path.parents or path.is_symlink():
        return None
    return path


def validate_visible_layout(value: Any, map_root: Path) -> list[dict[str, str]]:
    """Enforce grouped visible nodes without changing the map-control schema."""
    issues: list[dict[str, str]] = []
    root = map_root.resolve()
    if root.is_dir():
        for child in sorted(root.iterdir(), key=lambda item: item.name):
            if not child.is_file() or child.suffix.lower() != ".md":
                continue
            match = FLAT_NODE_RE.match(child.name)
            if match:
                category = RESULT_DIRECTORY if child.name.startswith("研究成果-") else str(match.group("category"))
                issues.append({
                    "code": "map_node_not_grouped",
                    "path": child.name,
                    "detail": f"Move this note under {category}/ and update all links and controls.",
                })
    results = value.get("results", []) if isinstance(value, dict) else []
    if isinstance(results, list):
        for index, item in enumerate(results):
            if not isinstance(item, dict) or not nonempty(item.get("note_path")):
                continue
            posix = PurePosixPath(str(item["note_path"]).replace("\\", "/"))
            if not posix.parts or posix.parts[0] != RESULT_DIRECTORY:
                issues.append({
                    "code": "result_note_directory_invalid",
                    "path": f"results[{index}].note_path",
                    "detail": f"Result notes must be stored under {RESULT_DIRECTORY}/.",
                })
    return issues


def _plain_callout(body: str) -> str:
    return "\n".join(re.sub(r"^>\s?", "", line) for line in body.splitlines()).strip()


def sufficient_definition_digest(title: str, raw_body: str) -> str:
    """Hash the visible shared-definition card under one stable text normalization."""
    normalized_title = re.sub(r"\s+", " ", title).strip()
    normalized_body = _plain_callout(raw_body).strip()
    return digest((normalized_title + "\n" + normalized_body + "\n").encode("utf-8"))


def _record_heading_before(text: str, marker_start: int) -> str | None:
    """Return an immediately preceding level-three title, ignoring blank lines only."""
    matches = [match for match in HEADING_RE.finditer(text, 0, marker_start) if match.group("marks") == "###"]
    if not matches:
        return None
    heading = matches[-1]
    if text[heading.end():marker_start].strip():
        return None
    return heading.group("title").strip()


def _markdown_note_index(root: Path) -> tuple[dict[str, Path], dict[str, list[str]]]:
    notes: dict[str, Path] = {}
    stems: dict[str, list[str]] = {}
    for path in root.rglob("*.md"):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(root).as_posix()
        notes[rel] = path
        stems.setdefault(path.stem.casefold(), []).append(rel)
    return notes, stems


def _resolve_wikilink(
    root: Path,
    source: Path,
    raw: str,
    notes: dict[str, Path],
    stems: dict[str, list[str]],
) -> tuple[str | None, str | None, str | None]:
    target = raw.split("|", 1)[0].strip()
    target, _, anchor = target.partition("#")
    if not target:
        rel = source.relative_to(root).as_posix()
        return rel, anchor or None, None
    target = target.replace("\\", "/")
    candidates: list[str] = []
    for base in (source.parent, root):
        candidate = (base / target).with_suffix(".md") if not Path(target).suffix else base / target
        try:
            rel = candidate.resolve().relative_to(root).as_posix()
        except ValueError:
            continue
        if rel in notes:
            candidates.append(rel)
    if not candidates and "/" not in target:
        candidates.extend(stems.get(Path(target).stem.casefold(), []))
    unique = sorted(set(candidates))
    if len(unique) != 1:
        return None, anchor or None, "missing_or_ambiguous"
    rel = unique[0]
    if anchor:
        target_text = notes[rel].read_text(encoding="utf-8")
        headings = {match.group("title").strip() for match in HEADING_RE.finditer(target_text)}
        block_ids = set(re.findall(r"(?m)^\s*\^(?P<id>[A-Za-z0-9-]+)\s*$", target_text))
        if anchor.startswith("^"):
            if anchor[1:] not in block_ids:
                return rel, anchor, "anchor_missing"
        elif anchor not in headings:
            return rel, anchor, "anchor_missing"
    return rel, anchor or None, None


def _visible_field(segment: str, name: str) -> str | None:
    match = re.search(rf"(?m)^-\s*\*\*{re.escape(name)}：\*\*\s*(?P<value>.+)$", segment)
    return match.group("value").strip() if match else None


def _contains_placeholder(text: str) -> bool:
    lowered = text.casefold()
    return any(item.casefold() in lowered for item in RESULT_PLACEHOLDERS)


def validate_global_synthesis(map_root: Path) -> list[dict[str, str]]:
    """Validate publication-time structure of the global narrative without judging its mathematics."""
    issues: list[dict[str, str]] = []
    path = map_root.resolve() / MAIN_SURVEY
    if not path.is_file() or path.is_symlink():
        return [{
            "code": "global_synthesis_main_missing",
            "path": MAIN_SURVEY,
            "detail": "Create the self-contained main research survey before publication.",
        }]
    try:
        note = path.read_text(encoding="utf-8")
    except Exception as exc:
        return [{"code": "global_synthesis_read_failed", "path": MAIN_SURVEY, "detail": str(exc)}]

    headings = list(re.finditer(r"(?m)^##\s+[^\n]+\s*$", note))
    role_sections: dict[str, list[tuple[str, str]]] = {role: [] for role in SYNTHESIS_ROLES}
    unknown_roles: set[str] = set()
    for index, heading in enumerate(headings):
        stop = headings[index + 1].start() if index + 1 < len(headings) else len(note)
        section = note[heading.end():stop]
        title = heading.group(0).removeprefix("##").strip()
        for marker in SYNTHESIS_MARKER_RE.finditer(section):
            role = marker.group("role")
            if role in role_sections:
                role_sections[role].append((title, section))
            else:
                unknown_roles.add(role)

    all_markers = list(SYNTHESIS_MARKER_RE.finditer(note))
    section_markers = sum(len(items) for items in role_sections.values()) + len(unknown_roles)
    if len(all_markers) != section_markers:
        issues.append({
            "code": "global_synthesis_marker_outside_section",
            "path": MAIN_SURVEY,
            "detail": "Place every synthesis marker inside one level-two section.",
        })
    for role in sorted(unknown_roles):
        issues.append({
            "code": "global_synthesis_role_unknown",
            "path": MAIN_SURVEY,
            "detail": role,
        })
    for role, sections in role_sections.items():
        if not sections:
            issues.append({
                "code": "global_synthesis_role_missing",
                "path": MAIN_SURVEY,
                "detail": role,
            })
            continue
        if len(sections) != 1:
            issues.append({
                "code": "global_synthesis_role_duplicate",
                "path": MAIN_SURVEY,
                "detail": role,
            })
            continue
        title, section = sections[0]
        prose = SYNTHESIS_MARKER_RE.sub("", section)
        compact = re.sub(r"\s+", "", prose)
        if len(compact) < MIN_SYNTHESIS_SECTION_CHARS:
            issues.append({
                "code": "global_synthesis_role_too_short",
                "path": f"{MAIN_SURVEY}##{title}",
                "detail": f"{role} requires at least {MIN_SYNTHESIS_SECTION_CHARS} non-whitespace characters.",
            })
        lowered = prose.casefold()
        if any(token.casefold() in lowered for token in SYNTHESIS_PLACEHOLDERS):
            issues.append({
                "code": "global_synthesis_placeholder",
                "path": f"{MAIN_SURVEY}##{title}",
                "detail": role,
            })
    compact_note = re.sub(r"\s+", "", SYNTHESIS_MARKER_RE.sub("", note))
    if len(compact_note) < MIN_SYNTHESIS_NOTE_CHARS:
        issues.append({
            "code": "global_synthesis_note_too_short",
            "path": MAIN_SURVEY,
            "detail": f"The main survey requires at least {MIN_SYNTHESIS_NOTE_CHARS} non-whitespace characters.",
        })
    return issues


def validate_project_glossary(map_root: Path) -> list[dict[str, str]]:
    """Validate the publication-time project glossary without judging coverage semantics."""
    issues: list[dict[str, str]] = []
    root = map_root.resolve()
    glossary_path = root / GLOSSARY_NOTE
    main_path = root / MAIN_SURVEY
    if not glossary_path.is_file() or glossary_path.is_symlink():
        return [{
            "code": "project_glossary_missing",
            "path": GLOSSARY_NOTE,
            "detail": "Create the project-specific terminology and notation glossary before publication.",
        }]
    try:
        glossary = glossary_path.read_text(encoding="utf-8")
    except Exception as exc:
        return [{"code": "project_glossary_read_failed", "path": GLOSSARY_NOTE, "detail": str(exc)}]

    marker_count = len(GLOSSARY_MARKER_RE.findall(glossary))
    if marker_count != 1:
        issues.append({
            "code": "project_glossary_marker_invalid",
            "path": GLOSSARY_NOTE,
            "detail": "The glossary must contain exactly one research-map-glossary:v1 marker.",
        })

    try:
        main = main_path.read_text(encoding="utf-8")
    except Exception:
        main = ""
    if not GLOSSARY_LINK_RE.search(main):
        issues.append({
            "code": "project_glossary_main_link_missing",
            "path": MAIN_SURVEY,
            "detail": f"Link {GLOSSARY_NOTE} from the main survey.",
        })

    headings = list(re.finditer(r"(?m)^###\s+[^\n]+\s*$", glossary))
    if len(headings) < MIN_GLOSSARY_ENTRIES:
        issues.append({
            "code": "project_glossary_too_few_entries",
            "path": GLOSSARY_NOTE,
            "detail": f"Provide at least {MIN_GLOSSARY_ENTRIES} substantive glossary entries.",
        })
    field_patterns = {
        name: re.compile(rf"(?m)^-\s*\*\*{re.escape(name)}：\*\*\s*(?P<value>.+)$")
        for name in GLOSSARY_FIELD_NAMES
    }
    for index, heading in enumerate(headings):
        stop = headings[index + 1].start() if index + 1 < len(headings) else len(glossary)
        section = glossary[heading.end():stop]
        title = heading.group(0).removeprefix("###").strip()
        for name, pattern in field_patterns.items():
            match = pattern.search(section)
            if match is None:
                issues.append({
                    "code": "project_glossary_field_missing",
                    "path": f"{GLOSSARY_NOTE}###{title}",
                    "detail": name,
                })
                continue
            compact = re.sub(r"\s+", "", match.group("value"))
            if len(compact) < MIN_GLOSSARY_FIELD_CHARS or any(
                token.casefold() in match.group("value").casefold()
                for token in SYNTHESIS_PLACEHOLDERS
            ):
                issues.append({
                    "code": "project_glossary_field_not_substantive",
                    "path": f"{GLOSSARY_NOTE}###{title}",
                    "detail": name,
                })
    return issues


def validate_tracked_topic_sections(
    map_root: Path,
    *,
    authority_manifest_sha256: str | None,
) -> list[dict[str, str]]:
    """Validate durable tracked-topic sections without judging their mathematics."""
    root = map_root.resolve()
    main_path = root / MAIN_SURVEY
    try:
        note = main_path.read_text(encoding="utf-8")
    except Exception as exc:
        return [{"code": "tracked_topic_main_read_failed", "path": MAIN_SURVEY, "detail": str(exc)}]

    issues: list[dict[str, str]] = []
    headings = list(re.finditer(r"(?m)^##\s+(?P<title>[^\n]+)\s*$", note))
    sections = [
        (heading.start(), headings[index + 1].start() if index + 1 < len(headings) else len(note), heading.group("title").strip())
        for index, heading in enumerate(headings)
    ]
    seen_ids: set[str] = set()
    field_patterns = {
        name: re.compile(rf"(?m)^-\s*\*\*{re.escape(name)}：\*\*\s*(?P<value>.+)$")
        for name in TRACKED_TOPIC_FIELD_NAMES
    }

    for marker in TRACKED_TOPIC_MARKER_RE.finditer(note):
        containing = next((section for section in sections if section[0] <= marker.start() < section[1]), None)
        if containing is None:
            issues.append({
                "code": "tracked_topic_marker_outside_level_two_section",
                "path": MAIN_SURVEY,
                "detail": "Place every tracked-topic marker inside one level-two section.",
            })
            continue
        start, stop, title = containing
        section_text = note[start:stop]
        try:
            payload = json.loads(marker.group("payload"))
        except json.JSONDecodeError as exc:
            issues.append({
                "code": "tracked_topic_marker_invalid_json",
                "path": f"{MAIN_SURVEY}##{title}",
                "detail": str(exc),
            })
            continue
        if not isinstance(payload, dict) or set(payload) != {"topic_id", "authority_manifest_sha256"}:
            issues.append({
                "code": "tracked_topic_marker_fields_invalid",
                "path": f"{MAIN_SURVEY}##{title}",
                "detail": "Marker fields must be exactly topic_id and authority_manifest_sha256.",
            })
            continue
        topic_id = payload.get("topic_id")
        manifest_sha = payload.get("authority_manifest_sha256")
        if not isinstance(topic_id, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", topic_id):
            issues.append({
                "code": "tracked_topic_id_invalid",
                "path": f"{MAIN_SURVEY}##{title}",
                "detail": "topic_id must be stable lowercase kebab-case.",
            })
        elif topic_id in seen_ids:
            issues.append({
                "code": "tracked_topic_id_duplicate",
                "path": f"{MAIN_SURVEY}##{title}",
                "detail": topic_id,
            })
        else:
            seen_ids.add(topic_id)
        if not isinstance(manifest_sha, str) or not HEX64.fullmatch(manifest_sha):
            issues.append({
                "code": "tracked_topic_manifest_hash_invalid",
                "path": f"{MAIN_SURVEY}##{title}",
                "detail": "authority_manifest_sha256 must be 64 lowercase hex characters.",
            })
        elif manifest_sha != authority_manifest_sha256:
            issues.append({
                "code": "tracked_topic_manifest_binding_stale",
                "path": f"{MAIN_SURVEY}##{title}",
                "detail": "Refresh the tracked topic against the candidate authority manifest.",
            })
        for name, pattern in field_patterns.items():
            field = pattern.search(section_text)
            if field is None:
                issues.append({
                    "code": "tracked_topic_field_missing",
                    "path": f"{MAIN_SURVEY}##{title}",
                    "detail": name,
                })
                continue
            value = field.group("value")
            compact = re.sub(r"\s+", "", value)
            if len(compact) < MIN_TRACKED_TOPIC_FIELD_CHARS or any(
                token.casefold() in value.casefold() for token in SYNTHESIS_PLACEHOLDERS
            ):
                issues.append({
                    "code": "tracked_topic_field_not_substantive",
                    "path": f"{MAIN_SURVEY}##{title}",
                    "detail": name,
                })
    return issues


def _directed_cycle(graph: dict[str, set[str]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(target) for target in graph.get(node, set())):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in graph)


def _marker_topic_ids(note: str) -> set[str]:
    found: set[str] = set()
    for marker in SUFFICIENT_TOPIC_MARKER_RE.finditer(note):
        try:
            payload = json.loads(marker.group("payload"))
        except json.JSONDecodeError:
            continue
        topic_id = payload.get("topic_id") if isinstance(payload, dict) else None
        if isinstance(topic_id, str):
            found.add(topic_id)
    return found


def validate_sufficient_condition_downgrade(previous_map_root: Path, candidate_map_root: Path) -> list[dict[str, str]]:
    """Reject removal of a previously registered sufficient-condition obligation."""
    try:
        previous = (previous_map_root.resolve() / MAIN_SURVEY).read_text(encoding="utf-8")
        candidate = (candidate_map_root.resolve() / MAIN_SURVEY).read_text(encoding="utf-8")
    except Exception as exc:
        return [{
            "code": "sufficient_condition_prior_map_read_failed",
            "path": MAIN_SURVEY,
            "detail": str(exc),
        }]
    removed = sorted(_marker_topic_ids(previous) - _marker_topic_ids(candidate))
    return [{
        "code": "sufficient_condition_obligation_downgraded",
        "path": MAIN_SURVEY,
        "detail": topic_id,
    } for topic_id in removed]


def validate_terminal_sufficient_condition_sections(
    map_root: Path,
    *,
    project_id: str | None,
    project_objective_sha256: str | None,
    authority_manifest_sha256: str | None,
    route_ids: set[str],
    require_definition_card: bool = False,
) -> list[dict[str, str]]:
    """Validate hash-bound terminal sufficient-condition registers and visible coverage."""
    root = map_root.resolve()
    main_path = root / MAIN_SURVEY
    try:
        note = main_path.read_text(encoding="utf-8")
    except Exception as exc:
        return [{"code": "sufficient_condition_main_read_failed", "path": MAIN_SURVEY, "detail": str(exc)}]

    issues: list[dict[str, str]] = []
    notes, note_stems = _markdown_note_index(root)
    headings = list(re.finditer(r"(?m)^##\s+(?P<title>[^\n]+)\s*$", note))
    sections = [
        (heading.start(), headings[index + 1].start() if index + 1 < len(headings) else len(note), heading.group("title").strip())
        for index, heading in enumerate(headings)
    ]
    tracked_topics: dict[str, str] = {}
    for marker in TRACKED_TOPIC_MARKER_RE.finditer(note):
        try:
            payload = json.loads(marker.group("payload"))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and isinstance(payload.get("topic_id"), str):
            tracked_topics[payload["topic_id"]] = str(payload.get("authority_manifest_sha256", ""))

    seen_topics: set[str] = set()
    visible_field_patterns = {
        name: re.compile(rf"(?m)^-\s*\*\*{re.escape(name)}：\*\*\s*(?P<value>.+)$")
        for name in SUFFICIENT_REGISTER_FIELDS
    }
    condition_keys = {
        "condition_id", "statement", "objective_implication", "terminality", "kind",
        "closed_prerequisites", "open_obligations", "route_ids", "evidence_refs",
        "difficulty_disposition",
    }
    logical_relation_keys = {"source_id", "relation", "target_id", "rationale", "evidence_refs"}
    difficulty_relation_keys = {"source_id", "relation", "target_id", "basis", "evidence_refs"}
    exclusion_keys = {"candidate_id", "description", "exclusion_reason", "evidence_refs"}
    source_coverage_keys = {
        "source_id", "source_kind", "candidate_summary", "disposition",
        "target_ids", "route_ids", "evidence_refs", "rationale",
    }
    root_keys = {
        "schema", "topic_id", "project_id", "project_objective_sha256",
        "authority_manifest_sha256", "coverage_claim", "difficulty_basis",
        "conditions", "logical_relations", "difficulty_relations", "exclusions",
        "candidate_source_coverage",
    }

    for marker in SUFFICIENT_TOPIC_MARKER_RE.finditer(note):
        containing = next((section for section in sections if section[0] <= marker.start() < section[1]), None)
        if containing is None:
            issues.append({
                "code": "sufficient_condition_marker_outside_level_two_section",
                "path": MAIN_SURVEY,
                "detail": "Place the sufficient-condition marker inside one level-two section.",
            })
            continue
        start, stop, title = containing
        section_path = f"{MAIN_SURVEY}##{title}"
        section_text = note[start:stop]
        try:
            payload = json.loads(marker.group("payload"))
        except json.JSONDecodeError as exc:
            issues.append({"code": "sufficient_condition_marker_invalid_json", "path": section_path, "detail": str(exc)})
            continue
        marker_keys = {"topic_id", "authority_manifest_sha256", "register_path", "register_sha256"}
        if not isinstance(payload, dict) or set(payload) != marker_keys:
            issues.append({
                "code": "sufficient_condition_marker_fields_invalid",
                "path": section_path,
                "detail": "Marker fields must be exactly topic_id, authority_manifest_sha256, register_path, and register_sha256.",
            })
            continue
        topic_id = payload.get("topic_id")
        manifest_sha = payload.get("authority_manifest_sha256")
        register_rel = payload.get("register_path")
        register_sha = payload.get("register_sha256")
        if not isinstance(topic_id, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", topic_id):
            issues.append({"code": "sufficient_condition_topic_id_invalid", "path": section_path})
            continue
        if topic_id in seen_topics:
            issues.append({"code": "sufficient_condition_topic_id_duplicate", "path": section_path, "detail": topic_id})
            continue
        seen_topics.add(topic_id)
        if tracked_topics.get(topic_id) != manifest_sha:
            issues.append({
                "code": "sufficient_condition_tracked_topic_binding_missing",
                "path": section_path,
                "detail": "Register the same topic_id and manifest hash with research-map-tracked-topic:v1.",
            })
        if not isinstance(manifest_sha, str) or not HEX64.fullmatch(manifest_sha) or manifest_sha != authority_manifest_sha256:
            issues.append({"code": "sufficient_condition_manifest_binding_stale", "path": section_path})
        if not isinstance(register_sha, str) or not HEX64.fullmatch(register_sha):
            issues.append({"code": "sufficient_condition_register_hash_invalid", "path": section_path})
        expected_rel = PurePosixPath(".research", "sufficient-conditions", f"{topic_id}.json")
        if not isinstance(register_rel, str) or PurePosixPath(register_rel) != expected_rel:
            issues.append({
                "code": "sufficient_condition_register_path_invalid",
                "path": section_path,
                "detail": expected_rel.as_posix(),
            })
            continue
        register_path = root.joinpath(*expected_rel.parts)
        if not register_path.is_file() or register_path.is_symlink():
            issues.append({"code": "sufficient_condition_register_missing", "path": expected_rel.as_posix()})
            continue
        raw = register_path.read_bytes()
        if digest(raw) != register_sha:
            issues.append({"code": "sufficient_condition_register_hash_stale", "path": expected_rel.as_posix()})
            continue
        try:
            register = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            issues.append({"code": "sufficient_condition_register_parse_failed", "path": expected_rel.as_posix(), "detail": str(exc)})
            continue
        if raw != canonical(register):
            issues.append({"code": "sufficient_condition_register_not_canonical", "path": expected_rel.as_posix()})
        if not isinstance(register, dict) or set(register) != root_keys:
            issues.append({"code": "sufficient_condition_register_fields_invalid", "path": expected_rel.as_posix()})
            continue
        if register.get("schema") != SUFFICIENT_REGISTER_SCHEMA:
            issues.append({"code": "sufficient_condition_register_schema_invalid", "path": expected_rel.as_posix()})
        for key, expected in (
            ("topic_id", topic_id),
            ("project_id", project_id),
            ("project_objective_sha256", project_objective_sha256),
            ("authority_manifest_sha256", authority_manifest_sha256),
        ):
            if register.get(key) != expected:
                issues.append({"code": "sufficient_condition_register_binding_stale", "path": f"{expected_rel.as_posix()}.{key}"})
        for key in ("coverage_claim", "difficulty_basis"):
            if not nonempty(register.get(key)) or len(re.sub(r"\s+", "", str(register.get(key)))) < MIN_SUFFICIENT_REGISTER_FIELD_CHARS:
                issues.append({"code": "sufficient_condition_register_explanation_missing", "path": f"{expected_rel.as_posix()}.{key}"})

        definition_markers = list(SUFFICIENT_DEFINITION_MARKER_RE.finditer(section_text))
        if require_definition_card or definition_markers:
            if not definition_markers:
                issues.append({"code": "sufficient_condition_definition_card_missing", "path": section_path})
            elif len(definition_markers) != 1:
                issues.append({"code": "sufficient_condition_definition_card_duplicate", "path": section_path})
            else:
                definition_marker = definition_markers[0]
                try:
                    definition_payload = json.loads(definition_marker.group("payload"))
                except json.JSONDecodeError:
                    definition_payload = None
                definition_keys = {"topic_id", "definition_id", "definition_sha256"}
                if not isinstance(definition_payload, dict) or set(definition_payload) != definition_keys:
                    issues.append({"code": "sufficient_condition_definition_marker_invalid", "path": section_path})
                else:
                    definition_id = definition_payload.get("definition_id")
                    definition_sha = definition_payload.get("definition_sha256")
                    if definition_payload.get("topic_id") != topic_id:
                        issues.append({"code": "sufficient_condition_definition_topic_mismatch", "path": section_path})
                    if not isinstance(definition_id, str) or not re.fullmatch(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", definition_id):
                        issues.append({"code": "sufficient_condition_definition_id_invalid", "path": section_path})
                    if not isinstance(definition_sha, str) or not HEX64.fullmatch(definition_sha):
                        issues.append({"code": "sufficient_condition_definition_hash_invalid", "path": section_path})
                    topic_marker_end = marker.end() - start
                    if section_text[topic_marker_end:definition_marker.start()].strip():
                        issues.append({"code": "sufficient_condition_definition_marker_not_immediate", "path": section_path})
                    definition_boundaries = [
                        candidate.start()
                        for pattern in (SUFFICIENT_ENTRY_MARKER_RE, SUFFICIENT_EXCLUSION_MARKER_RE, SUFFICIENT_SOURCE_MARKER_RE)
                        for candidate in pattern.finditer(section_text)
                        if candidate.start() > definition_marker.start()
                    ]
                    definition_stop = min(definition_boundaries, default=len(section_text))
                    definition_segment = section_text[definition_marker.end():definition_stop]
                    definition_callouts = [
                        match for match in CALLOUT_RE.finditer(definition_segment)
                        if match.group("kind").casefold() == "definition"
                    ]
                    if len(definition_callouts) != 1:
                        issues.append({"code": "sufficient_condition_definition_callout_missing", "path": section_path})
                    else:
                        definition_callout = definition_callouts[0]
                        if definition_segment[:definition_callout.start()].strip():
                            issues.append({"code": "sufficient_condition_definition_callout_not_immediate", "path": section_path})
                        definition_title = re.sub(r"\s+", " ", str(definition_callout.group("title") or "")).strip()
                        if not definition_title or definition_title.casefold() in {"定义", "符号", "definition", "notation"}:
                            issues.append({"code": "sufficient_condition_definition_title_missing", "path": section_path})
                        definition_body = definition_callout.group("body")
                        if "<!--" in definition_body or "-->" in definition_body or "%%" in definition_body:
                            issues.append({"code": "sufficient_condition_definition_hidden_text", "path": section_path})
                        if len(re.sub(r"\s+", "", _plain_callout(definition_body))) < 80:
                            issues.append({"code": "sufficient_condition_definition_not_substantive", "path": section_path})
                        if isinstance(definition_sha, str) and HEX64.fullmatch(definition_sha):
                            actual_definition_sha = sufficient_definition_digest(definition_title, definition_body)
                            if actual_definition_sha != definition_sha:
                                issues.append({"code": "sufficient_condition_definition_hash_stale", "path": section_path})

        conditions = register.get("conditions")
        if not isinstance(conditions, list) or not conditions:
            issues.append({"code": "sufficient_condition_inventory_missing", "path": f"{expected_rel.as_posix()}.conditions"})
            conditions = []
        condition_ids: set[str] = set()
        direct_ids: set[str] = set()
        ranked_ids: set[str] = set()
        condition_route_ids: set[str] = set()
        actionable_route_ids: set[str] = set()
        condition_kinds: dict[str, str] = {}
        condition_routes_by_id: dict[str, set[str]] = {}
        conditions_by_id: dict[str, dict[str, Any]] = {}
        normalized_statements: set[str] = set()
        for index, condition in enumerate(conditions):
            cpath = f"{expected_rel.as_posix()}.conditions[{index}]"
            if not isinstance(condition, dict) or set(condition) != condition_keys:
                issues.append({"code": "sufficient_condition_fields_invalid", "path": cpath})
                continue
            condition_id = condition.get("condition_id")
            if not isinstance(condition_id, str) or not re.fullmatch(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", condition_id) or condition_id in condition_ids:
                issues.append({"code": "sufficient_condition_id_invalid", "path": cpath + ".condition_id"})
                continue
            condition_ids.add(condition_id)
            conditions_by_id[condition_id] = condition
            for key in ("statement", "objective_implication"):
                if not nonempty(condition.get(key)):
                    issues.append({"code": "sufficient_condition_explanation_missing", "path": cpath + "." + key})
            normalized_statement = re.sub(r"\s+", "", str(condition.get("statement", "")).casefold())
            if normalized_statement in normalized_statements:
                issues.append({"code": "sufficient_condition_duplicate_statement", "path": cpath + ".statement"})
            normalized_statements.add(normalized_statement)
            terminality = condition.get("terminality")
            if terminality not in {"direct", "via_registered_condition"}:
                issues.append({"code": "terminal_condition_not_terminal", "path": cpath + ".terminality"})
            elif terminality == "direct":
                direct_ids.add(condition_id)
            kind = condition.get("kind")
            if kind not in {"criterion", "actionable"}:
                issues.append({"code": "sufficient_condition_kind_invalid", "path": cpath + ".kind"})
            else:
                condition_kinds[condition_id] = kind
            for key in ("closed_prerequisites", "open_obligations"):
                if not isinstance(condition.get(key), list) or not all(nonempty(item) for item in condition.get(key, [])):
                    issues.append({"code": "sufficient_condition_obligations_invalid", "path": cpath + "." + key})
            condition_routes = condition.get("route_ids")
            if not isinstance(condition_routes, list) or not all(nonempty(item) for item in condition_routes):
                issues.append({"code": "sufficient_condition_route_ids_invalid", "path": cpath + ".route_ids"})
            else:
                condition_routes_by_id[condition_id] = set(condition_routes)
                for route_id in condition_routes:
                    if route_id not in route_ids:
                        issues.append({"code": "sufficient_condition_route_id_unknown", "path": cpath + ".route_ids", "detail": route_id})
                    else:
                        condition_route_ids.add(route_id)
                        if kind == "actionable":
                            actionable_route_ids.add(route_id)
            if not refs_ok(condition.get("evidence_refs")):
                issues.append({"code": "sufficient_condition_evidence_missing", "path": cpath + ".evidence_refs"})
            disposition = condition.get("difficulty_disposition")
            if not isinstance(disposition, dict) or set(disposition) != {"status", "rationale"} or not nonempty(disposition.get("rationale")):
                issues.append({"code": "terminal_condition_difficulty_uncovered", "path": cpath + ".difficulty_disposition"})
            else:
                expected_status = "criterion_scale" if kind == "criterion" else "ranked"
                if disposition.get("status") != expected_status:
                    issues.append({"code": "terminal_condition_difficulty_uncovered", "path": cpath + ".difficulty_disposition.status"})
                if disposition.get("status") == "ranked":
                    ranked_ids.add(condition_id)

        logical_relations = register.get("logical_relations")
        if not isinstance(logical_relations, list):
            issues.append({"code": "sufficient_condition_logical_relations_invalid", "path": f"{expected_rel.as_posix()}.logical_relations"})
            logical_relations = []
        implication_graph = {condition_id: set() for condition_id in condition_ids}
        for index, relation in enumerate(logical_relations):
            rpath = f"{expected_rel.as_posix()}.logical_relations[{index}]"
            if not isinstance(relation, dict) or set(relation) != logical_relation_keys:
                issues.append({"code": "sufficient_condition_relation_fields_invalid", "path": rpath})
                continue
            source, target = relation.get("source_id"), relation.get("target_id")
            if source not in condition_ids or target not in condition_ids:
                issues.append({"code": "sufficient_condition_relation_dangling", "path": rpath})
                continue
            if source == target or relation.get("relation") not in {"implies", "equivalent_to", "incomparable_with"}:
                issues.append({"code": "sufficient_condition_relation_invalid", "path": rpath})
                continue
            if not nonempty(relation.get("rationale")) or not refs_ok(relation.get("evidence_refs")):
                issues.append({"code": "sufficient_condition_relation_evidence_missing", "path": rpath})
            if relation["relation"] == "implies":
                implication_graph[source].add(target)
        if _directed_cycle(implication_graph):
            issues.append({"code": "sufficient_condition_implication_cycle", "path": f"{expected_rel.as_posix()}.logical_relations"})

        def reaches_direct(start_id: str) -> bool:
            pending = [start_id]
            visited: set[str] = set()
            while pending:
                current = pending.pop()
                if current in direct_ids:
                    return True
                if current in visited:
                    continue
                visited.add(current)
                pending.extend(implication_graph.get(current, set()))
            return False

        for index, condition in enumerate(conditions):
            if isinstance(condition, dict) and condition.get("terminality") == "via_registered_condition":
                condition_id = condition.get("condition_id")
                if isinstance(condition_id, str) and not reaches_direct(condition_id):
                    issues.append({"code": "terminal_condition_not_terminal", "path": f"{expected_rel.as_posix()}.conditions[{index}].terminality"})

        difficulty_relations = register.get("difficulty_relations")
        if not isinstance(difficulty_relations, list):
            issues.append({"code": "sufficient_condition_difficulty_relations_invalid", "path": f"{expected_rel.as_posix()}.difficulty_relations"})
            difficulty_relations = []
        difficulty_graph = {condition_id: set() for condition_id in ranked_ids}
        difficulty_covered: set[str] = set()
        for index, relation in enumerate(difficulty_relations):
            rpath = f"{expected_rel.as_posix()}.difficulty_relations[{index}]"
            if not isinstance(relation, dict) or set(relation) != difficulty_relation_keys:
                issues.append({"code": "sufficient_condition_difficulty_relation_fields_invalid", "path": rpath})
                continue
            source, target = relation.get("source_id"), relation.get("target_id")
            if source not in ranked_ids or target not in ranked_ids or source == target:
                issues.append({"code": "sufficient_condition_difficulty_relation_dangling", "path": rpath})
                continue
            relation_kind = relation.get("relation")
            if relation_kind not in {"easier_than", "harder_than", "incomparable_with"}:
                issues.append({"code": "sufficient_condition_difficulty_relation_invalid", "path": rpath})
                continue
            difficulty_covered.update((source, target))
            if not nonempty(relation.get("basis")) or not refs_ok(relation.get("evidence_refs")):
                issues.append({"code": "sufficient_condition_difficulty_evidence_missing", "path": rpath})
            if relation_kind == "easier_than":
                difficulty_graph[source].add(target)
            elif relation_kind == "harder_than":
                difficulty_graph[target].add(source)
        if _directed_cycle(difficulty_graph):
            issues.append({"code": "sufficient_condition_difficulty_cycle", "path": f"{expected_rel.as_posix()}.difficulty_relations"})
        if len(ranked_ids) > 1:
            for condition_id in sorted(ranked_ids - difficulty_covered):
                issues.append({"code": "terminal_condition_difficulty_uncovered", "path": f"{expected_rel.as_posix()}.conditions", "detail": condition_id})

        exclusions = register.get("exclusions")
        if not isinstance(exclusions, list):
            issues.append({"code": "sufficient_condition_exclusions_invalid", "path": f"{expected_rel.as_posix()}.exclusions"})
            exclusions = []
        exclusion_ids: set[str] = set()
        for index, exclusion in enumerate(exclusions):
            xpath = f"{expected_rel.as_posix()}.exclusions[{index}]"
            if not isinstance(exclusion, dict) or set(exclusion) != exclusion_keys:
                issues.append({"code": "sufficient_condition_exclusion_fields_invalid", "path": xpath})
                continue
            candidate_id = exclusion.get("candidate_id")
            if not isinstance(candidate_id, str) or not re.fullmatch(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", candidate_id) or candidate_id in exclusion_ids:
                issues.append({"code": "sufficient_condition_exclusion_id_invalid", "path": xpath + ".candidate_id"})
                continue
            exclusion_ids.add(candidate_id)
            if not nonempty(exclusion.get("description")) or not nonempty(exclusion.get("exclusion_reason")):
                issues.append({"code": "sufficient_condition_exclusion_explanation_missing", "path": xpath})
            if not refs_ok(exclusion.get("evidence_refs")):
                issues.append({"code": "sufficient_condition_exclusion_evidence_missing", "path": xpath + ".evidence_refs"})

        source_coverage = register.get("candidate_source_coverage")
        if not isinstance(source_coverage, list) or not source_coverage:
            issues.append({"code": "sufficient_condition_source_coverage_missing", "path": f"{expected_rel.as_posix()}.candidate_source_coverage"})
            source_coverage = []
        source_ids: set[str] = set()
        covered_route_ids: set[str] = set()
        for index, source in enumerate(source_coverage):
            spath = f"{expected_rel.as_posix()}.candidate_source_coverage[{index}]"
            if not isinstance(source, dict) or set(source) != source_coverage_keys:
                issues.append({"code": "sufficient_condition_source_fields_invalid", "path": spath})
                continue
            source_id = source.get("source_id")
            if not isinstance(source_id, str) or not re.fullmatch(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", source_id) or source_id in source_ids:
                issues.append({"code": "sufficient_condition_source_id_invalid", "path": spath + ".source_id"})
                continue
            source_ids.add(source_id)
            source_kind = source.get("source_kind")
            if source_kind not in {"route_success_gate", "route_review", "authority_claim", "visible_map_claim"}:
                issues.append({"code": "sufficient_condition_source_kind_invalid", "path": spath + ".source_kind"})
            if not nonempty(source.get("candidate_summary")) or not nonempty(source.get("rationale")):
                issues.append({"code": "sufficient_condition_source_explanation_missing", "path": spath})
            if not refs_ok(source.get("evidence_refs")):
                issues.append({"code": "sufficient_condition_source_evidence_missing", "path": spath + ".evidence_refs"})
            source_routes = source.get("route_ids")
            if not isinstance(source_routes, list) or not all(nonempty(item) for item in source_routes):
                issues.append({"code": "sufficient_condition_source_route_ids_invalid", "path": spath + ".route_ids"})
                source_routes = []
            for route_id in source_routes:
                if route_id not in route_ids:
                    issues.append({"code": "sufficient_condition_source_route_id_unknown", "path": spath + ".route_ids", "detail": route_id})
                else:
                    covered_route_ids.add(route_id)
            if source_kind in {"route_success_gate", "route_review"} and not source_routes:
                issues.append({"code": "sufficient_condition_route_source_unbound", "path": spath + ".route_ids"})
            disposition = source.get("disposition")
            target_ids = source.get("target_ids")
            if not isinstance(target_ids, list) or not target_ids or not all(nonempty(item) for item in target_ids):
                issues.append({"code": "sufficient_condition_source_targets_invalid", "path": spath + ".target_ids"})
                continue
            if disposition in {"condition", "equivalent_to_condition"}:
                if any(target_id not in condition_ids for target_id in target_ids):
                    issues.append({"code": "sufficient_condition_source_target_dangling", "path": spath + ".target_ids"})
                elif source_kind in {"route_success_gate", "route_review"}:
                    for route_id in source_routes:
                        if not any(
                            condition_kinds.get(target_id) == "actionable"
                            and route_id in condition_routes_by_id.get(target_id, set())
                            for target_id in target_ids
                        ):
                            issues.append({
                                "code": "sufficient_condition_route_source_not_actionable",
                                "path": spath + ".target_ids",
                                "detail": route_id,
                            })
            elif disposition == "exclusion":
                if any(target_id not in exclusion_ids for target_id in target_ids):
                    issues.append({"code": "sufficient_condition_source_target_dangling", "path": spath + ".target_ids"})
            else:
                issues.append({"code": "sufficient_condition_source_disposition_invalid", "path": spath + ".disposition"})
        for route_id in sorted(route_ids - covered_route_ids):
            issues.append({"code": "sufficient_condition_route_source_uncovered", "path": f"{expected_rel.as_posix()}.candidate_source_coverage", "detail": route_id})
        for route_id in sorted(route_ids - actionable_route_ids):
            issues.append({"code": "sufficient_condition_route_terminal_uncovered", "path": f"{expected_rel.as_posix()}.conditions", "detail": route_id})

        for name, pattern in visible_field_patterns.items():
            match = pattern.search(section_text)
            if match is None or len(re.sub(r"\s+", "", match.group("value") if match else "")) < MIN_SUFFICIENT_REGISTER_FIELD_CHARS:
                issues.append({"code": "sufficient_condition_visible_field_missing", "path": section_path, "detail": name})
        visible_condition_ids: list[str] = []
        entry_markers = list(SUFFICIENT_ENTRY_MARKER_RE.finditer(section_text))
        boundary_starts = sorted(
            [match.start() for match in entry_markers]
            + [match.start() for match in SUFFICIENT_EXCLUSION_MARKER_RE.finditer(section_text)]
            + [match.start() for match in SUFFICIENT_SOURCE_MARKER_RE.finditer(section_text)]
            + [len(section_text)]
        )
        for entry_marker in entry_markers:
            try:
                entry_payload = json.loads(entry_marker.group("payload"))
            except json.JSONDecodeError:
                entry_payload = None
            if not isinstance(entry_payload, dict) or set(entry_payload) != {"condition_id"} or not isinstance(entry_payload.get("condition_id"), str):
                issues.append({"code": "sufficient_condition_visible_entry_invalid", "path": section_path})
            else:
                visible_id = entry_payload["condition_id"]
                visible_condition_ids.append(visible_id)
                condition = conditions_by_id.get(visible_id)
                entry_heading = _record_heading_before(section_text, entry_marker.start())
                if entry_heading is None or re.match(rf"^{re.escape(visible_id)}(?:\s|[:：—-])", entry_heading) is None:
                    issues.append({"code": "sufficient_condition_entry_marker_position_invalid", "path": section_path, "detail": visible_id})
                stop_at = next((value for value in boundary_starts if value > entry_marker.start()), len(section_text))
                segment = section_text[entry_marker.end():stop_at]
                callouts = [match for match in CALLOUT_RE.finditer(segment) if match.group("kind").casefold() == "proposition"]
                if len(callouts) != 1:
                    issues.append({"code": "sufficient_condition_visible_callout_missing", "path": section_path, "detail": visible_id})
                elif condition is not None:
                    callout = callouts[0]
                    if segment[:callout.start()].strip():
                        issues.append({"code": "sufficient_condition_visible_callout_not_immediate", "path": section_path, "detail": visible_id})
                    title = re.sub(r"\s+", " ", str(callout.group("title") or "")).strip()
                    placeholder_titles = {"命题", "充分命题", "研究目标", "proposition", "statement", "research target"}
                    if not title or title.casefold() == visible_id.casefold() or title.casefold() in placeholder_titles:
                        issues.append({"code": "sufficient_condition_visible_callout_title_missing", "path": section_path, "detail": visible_id})
                    raw_body = callout.group("body")
                    if "<!--" in raw_body or "-->" in raw_body or "%%" in raw_body:
                        issues.append({"code": "sufficient_condition_visible_callout_hidden_text", "path": section_path, "detail": visible_id})
                    visible_body = re.sub(r"<!--[\s\S]*?-->", "", raw_body)
                    visible_body = re.sub(r"%%[\s\S]*?%%", "", visible_body)
                    body = re.sub(r"\s+", "", _plain_callout(visible_body).casefold())
                    for key in ("statement", "objective_implication"):
                        expected = re.sub(r"\s+", "", str(condition.get(key, "")).casefold())
                        if expected and expected not in body:
                            issues.append({"code": "sufficient_condition_visible_callout_body_mismatch", "path": section_path, "detail": f"{visible_id}.{key}"})
        if sorted(visible_condition_ids) != sorted(condition_ids) or len(visible_condition_ids) != len(set(visible_condition_ids)):
            issues.append({"code": "sufficient_condition_visible_inventory_mismatch", "path": section_path})
        visible_exclusion_ids: list[str] = []
        for exclusion_marker in SUFFICIENT_EXCLUSION_MARKER_RE.finditer(section_text):
            try:
                exclusion_payload = json.loads(exclusion_marker.group("payload"))
            except json.JSONDecodeError:
                exclusion_payload = None
            if not isinstance(exclusion_payload, dict) or set(exclusion_payload) != {"candidate_id"} or not isinstance(exclusion_payload.get("candidate_id"), str):
                issues.append({"code": "sufficient_condition_visible_exclusion_invalid", "path": section_path})
            else:
                candidate_id = exclusion_payload["candidate_id"]
                visible_exclusion_ids.append(candidate_id)
                exclusion_heading = _record_heading_before(section_text, exclusion_marker.start())
                if exclusion_heading != f"排除：{candidate_id}":
                    issues.append({"code": "sufficient_condition_exclusion_marker_position_invalid", "path": section_path, "detail": candidate_id})
                stop_at = next((value for value in boundary_starts if value > exclusion_marker.start()), len(section_text))
                segment = section_text[exclusion_marker.end():stop_at]
                exclusion = next((row for row in exclusions if isinstance(row, dict) and row.get("candidate_id") == candidate_id), None)
                required_fields = ("被排除候选", "排除范围", "路线保留", "路线", "证据", "失败边界", "对应终端命题")
                values = {name: _visible_field(segment, name) for name in required_fields}
                for name, value in values.items():
                    if not nonempty(value):
                        issues.append({"code": "sufficient_condition_exclusion_visible_field_missing", "path": section_path, "detail": f"{candidate_id}.{name}"})
                if nonempty(values.get("被排除候选")) and candidate_id not in str(values["被排除候选"]):
                    issues.append({"code": "sufficient_condition_exclusion_scope_mismatch", "path": section_path, "detail": candidate_id})
                if nonempty(values.get("排除范围")) and len(re.sub(r"\s+", "", str(values["排除范围"]))) < MIN_SUFFICIENT_REGISTER_FIELD_CHARS:
                    issues.append({"code": "sufficient_condition_exclusion_scope_missing", "path": section_path, "detail": candidate_id})
                if nonempty(values.get("路线保留")) and not re.match(r"^(?:是|否)(?:\b|[，。；：:])", str(values["路线保留"])):
                    issues.append({"code": "sufficient_condition_exclusion_route_retention_missing", "path": section_path, "detail": candidate_id})
                for field_name in ("路线", "证据", "失败边界", "对应终端命题"):
                    links = WIKILINK_RE.findall(str(values.get(field_name) or ""))
                    if not links:
                        issues.append({"code": "sufficient_condition_exclusion_link_missing", "path": section_path, "detail": f"{candidate_id}.{field_name}"})
                        continue
                    resolved_links: list[tuple[str, str | None]] = []
                    for raw_link in links:
                        rel, anchor, error = _resolve_wikilink(root, main_path, raw_link, notes, note_stems)
                        if error == "missing_or_ambiguous":
                            issues.append({"code": "sufficient_condition_visible_link_missing_or_ambiguous", "path": section_path, "detail": raw_link})
                        elif error == "anchor_missing":
                            issues.append({"code": "sufficient_condition_visible_link_anchor_missing", "path": section_path, "detail": raw_link})
                        elif rel is not None:
                            resolved_links.append((rel, anchor))
                    if field_name in {"失败边界", "对应终端命题"} and resolved_links and not any(anchor for _, anchor in resolved_links):
                        issues.append({"code": "sufficient_condition_visible_link_anchor_required", "path": section_path, "detail": f"{candidate_id}.{field_name}"})
                    if field_name == "对应终端命题" and resolved_links:
                        anchors = {anchor for _, anchor in resolved_links if anchor}
                        if not any(any(re.match(rf"^{re.escape(condition_id)}(?:\s|[:：—-])", anchor) for condition_id in condition_ids) for anchor in anchors):
                            issues.append({"code": "sufficient_condition_exclusion_terminal_link_mismatch", "path": section_path, "detail": candidate_id})
        if sorted(visible_exclusion_ids) != sorted(exclusion_ids) or len(visible_exclusion_ids) != len(set(visible_exclusion_ids)):
            issues.append({"code": "sufficient_condition_visible_exclusions_mismatch", "path": section_path})
        visible_source_ids: list[str] = []
        for source_marker in SUFFICIENT_SOURCE_MARKER_RE.finditer(section_text):
            try:
                source_payload = json.loads(source_marker.group("payload"))
            except json.JSONDecodeError:
                source_payload = None
            if not isinstance(source_payload, dict) or set(source_payload) != {"source_id"} or not isinstance(source_payload.get("source_id"), str):
                issues.append({"code": "sufficient_condition_visible_source_invalid", "path": section_path})
            else:
                source_id = source_payload["source_id"]
                visible_source_ids.append(source_id)
                source_heading = _record_heading_before(section_text, source_marker.start())
                if source_heading != f"来源：{source_id}":
                    issues.append({"code": "sufficient_condition_source_marker_position_invalid", "path": section_path, "detail": source_id})
                stop_at = next((value for value in boundary_starts if value > source_marker.start()), len(section_text))
                segment = section_text[source_marker.end():stop_at]
                source = next((row for row in source_coverage if isinstance(row, dict) and row.get("source_id") == source_id), None)
                required_fields = ("路线", "证据", "失败边界", "对应终端命题", "登记处置")
                values = {name: _visible_field(segment, name) for name in required_fields}
                for name, value in values.items():
                    if not nonempty(value):
                        issues.append({"code": "sufficient_condition_source_visible_field_missing", "path": section_path, "detail": f"{source_id}.{name}"})
                resolved_by_field: dict[str, list[tuple[str, str | None]]] = {}
                for field_name in ("路线", "证据", "失败边界", "对应终端命题"):
                    links = WIKILINK_RE.findall(str(values.get(field_name) or ""))
                    if not links:
                        issues.append({"code": "sufficient_condition_source_link_missing", "path": section_path, "detail": f"{source_id}.{field_name}"})
                        resolved_by_field[field_name] = []
                        continue
                    resolved_links: list[tuple[str, str | None]] = []
                    for raw_link in links:
                        rel, anchor, error = _resolve_wikilink(root, main_path, raw_link, notes, note_stems)
                        if error == "missing_or_ambiguous":
                            issues.append({"code": "sufficient_condition_visible_link_missing_or_ambiguous", "path": section_path, "detail": raw_link})
                        elif error == "anchor_missing":
                            issues.append({"code": "sufficient_condition_visible_link_anchor_missing", "path": section_path, "detail": raw_link})
                        elif rel is not None:
                            resolved_links.append((rel, anchor))
                    resolved_by_field[field_name] = resolved_links
                    if field_name in {"失败边界", "对应终端命题"} and resolved_links and not any(anchor for _, anchor in resolved_links):
                        issues.append({"code": "sufficient_condition_visible_link_anchor_required", "path": section_path, "detail": f"{source_id}.{field_name}"})
                if source is not None:
                    disposition_text = str(values.get("登记处置") or "")
                    expected_tokens = [str(source.get("disposition") or "")] + [str(item) for item in source.get("target_ids", [])]
                    if any(token and token not in disposition_text for token in expected_tokens):
                        issues.append({"code": "sufficient_condition_source_disposition_mismatch", "path": section_path, "detail": source_id})
                    route_text = "\n".join(
                        notes[rel].read_text(encoding="utf-8")
                        for rel, _ in resolved_by_field.get("路线", [])
                    )
                    if any(route_id not in route_text for route_id in source.get("route_ids", [])):
                        issues.append({"code": "sufficient_condition_source_route_link_mismatch", "path": section_path, "detail": source_id})
                    terminal_anchors = {anchor for _, anchor in resolved_by_field.get("对应终端命题", []) if anchor}
                    target_condition_ids = {
                        target_id for target_id in source.get("target_ids", []) if target_id in condition_ids
                    }
                    if target_condition_ids and any(
                        not any(re.match(rf"^{re.escape(target_id)}(?:\s|[:：—-])", anchor) for anchor in terminal_anchors)
                        for target_id in target_condition_ids
                    ):
                        issues.append({"code": "sufficient_condition_source_terminal_link_mismatch", "path": section_path, "detail": source_id})
        if sorted(visible_source_ids) != sorted(source_ids) or len(visible_source_ids) != len(set(visible_source_ids)):
            issues.append({"code": "sufficient_condition_visible_sources_mismatch", "path": section_path})

    return issues


def validate_result_notes(value: Any, map_root: Path, *, for_export: bool = False) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    issues: list[dict[str, str]] = []
    bindings: list[dict[str, str]] = []
    results = value.get("results", []) if isinstance(value, dict) else []
    if not isinstance(results, list):
        return issues, bindings
    seen_paths: set[str] = set()
    for index, item in enumerate(results):
        base = f"results[{index}]"
        if not isinstance(item, dict):
            continue
        result_id = item.get("result_id") if nonempty(item.get("result_id")) else base
        relative = item.get("note_path")
        path = _result_note_path(map_root, relative)
        if path is None:
            issues.append({"code": "result_note_path_invalid", "path": base + ".note_path"})
            continue
        normalized = PurePosixPath(str(relative).replace("\\", "/")).as_posix()
        if normalized in seen_paths:
            issues.append({"code": "result_note_path_duplicate", "path": base + ".note_path"})
            continue
        seen_paths.add(normalized)
        if not path.is_file():
            issues.append({"code": "result_note_missing", "path": normalized})
            continue
        try:
            note = path.read_text(encoding="utf-8")
        except Exception as exc:
            issues.append({"code": "result_note_read_failed", "path": normalized, "detail": str(exc)})
            continue
        expected_kind = item.get("theorem_callout_type")
        matches = [match for match in CALLOUT_RE.finditer(note) if match.group("kind").casefold() == str(expected_kind).casefold()]
        if not matches:
            issues.append({"code": "result_theorem_callout_missing", "path": normalized})
            continue
        theorem = _plain_callout(matches[0].group("body"))
        if not theorem.strip() or _contains_placeholder(theorem):
            issues.append({"code": "result_theorem_not_substantive", "path": normalized})
        heading = item.get("proof_heading")
        heading_re = re.compile(rf"(?m)^##\s+{re.escape(str(heading).strip())}\s*$") if nonempty(heading) else None
        proof_match = heading_re.search(note, matches[0].end()) if heading_re else None
        if proof_match is None:
            issues.append({"code": "result_proof_missing", "path": normalized})
        else:
            next_heading = re.search(r"(?m)^##\s+", note[proof_match.end():])
            stop = proof_match.end() + next_heading.start() if next_heading else len(note)
            proof = note[proof_match.end():stop].strip()
            if len(proof) < 300:
                issues.append({"code": "result_proof_too_short", "path": normalized})
            if _contains_placeholder(proof):
                issues.append({"code": "result_proof_delegated", "path": normalized})
        if for_export and item.get("status") not in {"verified", "independently_verified"}:
            issues.append({"code": "result_not_exportable", "path": base + ".status"})
        bindings.append({"result_id": str(result_id), "note_path": normalized, "sha256": digest(path.read_bytes())})
    return issues, bindings


def validate_root(
    root: Path,
    *,
    for_attempt: bool = False,
    for_export: bool = False,
    for_publication: bool = False,
    previous_map_root: Path | None = None,
) -> dict[str, Any]:
    control_path = root.resolve() / ".research" / "research-map.json"
    if not control_path.is_file():
        return {"ok": False, "schema": VALIDATION_SCHEMA, "issues": [{"code": "map_control_missing", "path": str(control_path)}]}
    try:
        value = load(control_path)
    except Exception as exc:
        return {"ok": False, "schema": VALIDATION_SCHEMA, "issues": [{"code": "map_control_parse_failed", "path": str(control_path), "detail": str(exc)}]}
    issues = validate_control(value, for_attempt=for_attempt)
    if for_attempt:
        try:
            project_root = root.resolve().parent
            project = load(project_root / "project.json")
            authority_pointer = project["research_authority_head"]
            authority_path = project_root / Path(authority_pointer["path"])
            authority_raw = authority_path.read_bytes()
            if digest(authority_raw) != authority_pointer["sha256"]:
                raise ValueError("authority pointer mismatch")
            authority = json.loads(authority_raw.decode("utf-8"))
            closure_pointer = authority["independent_semantic_review"]
            closure_path = project_root / Path(closure_pointer["path"])
            closure_raw = closure_path.read_bytes()
            if digest(closure_raw) != closure_pointer["sha256"]:
                raise ValueError("closure pointer mismatch")
            closure = json.loads(closure_raw.decode("utf-8"))
            if closure.get("schema") != "math-research-map-review-closure/v1":
                raise ValueError("thin semantic-review receipt")
            from map_semantic_review_v1 import validate_closure_document
            checked = validate_closure_document(project_root, closure, expected_closure_path=closure_pointer["path"])
            if not isinstance(checked, dict) or checked.get("ok") is not True:
                raise ValueError("closure validation failed")
        except Exception as exc:
            issues.append({"code": "map_review_upgrade_required", "path": ".research/map-review/closure.json", "detail": str(exc)})
    issues.extend(validate_visible_layout(value, root))
    if for_publication:
        issues.extend(validate_global_synthesis(root))
        issues.extend(validate_project_glossary(root))
        issues.extend(validate_tracked_topic_sections(
            root,
            authority_manifest_sha256=value.get("authority_manifest_sha256") if isinstance(value, dict) else None,
        ))
        issues.extend(validate_terminal_sufficient_condition_sections(
            root,
            project_id=value.get("project_id") if isinstance(value, dict) else None,
            project_objective_sha256=value.get("project_objective_sha256") if isinstance(value, dict) else None,
            authority_manifest_sha256=value.get("authority_manifest_sha256") if isinstance(value, dict) else None,
            route_ids={
                item.get("route_id")
                for item in value.get("routes", [])
                if isinstance(value, dict) and isinstance(item, dict) and isinstance(item.get("route_id"), str)
            } if isinstance(value, dict) else set(),
            require_definition_card=True,
        ))
        if previous_map_root is not None:
            issues.extend(validate_sufficient_condition_downgrade(previous_map_root, root))
    result_issues, result_notes = validate_result_notes(value, root, for_export=for_export)
    issues.extend(result_issues)
    return {
        "ok": not issues,
        "schema": VALIDATION_SCHEMA,
        "map_schema": value.get("schema"),
        "activation_eligible": not issues and value.get("status") == "current",
        "control_sha256": digest(canonical(value)),
        "result_notes": result_notes,
        "issues": issues,
    }


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("map_root", type=Path)
    parser.add_argument("--for-v13-attempt", action="store_true")
    parser.add_argument("--for-result-export", action="store_true")
    parser.add_argument("--for-publication", action="store_true")
    parser.add_argument("--previous-map-root", type=Path)
    args = parser.parse_args(argv)
    result = validate_root(
        args.map_root,
        for_attempt=args.for_v13_attempt,
        for_export=args.for_result_export,
        for_publication=args.for_publication,
        previous_map_root=args.previous_map_root,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
