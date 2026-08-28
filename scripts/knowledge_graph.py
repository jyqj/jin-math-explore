"""Demand-driven mathematical knowledge-node validation and generated views."""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

import research_repo as core
from portfolio_registry import registry_entries
from portfolio_vocab import (
    AUTHORITY_FIELDS,
    KNOWLEDGE_AUTHORITY_STATUSES,
    KNOWLEDGE_CLASSIFICATION_FIELDS,
    KNOWLEDGE_FIELDS,
    KNOWLEDGE_ID,
    KNOWLEDGE_KINDS,
    KNOWLEDGE_RELATION_TYPES,
    RELATION_FIELDS,
    RELATION_TARGET,
    SHARED_ID,
    Problem,
    first_cycle,
    known_file_ids,
    nonempty,
    string_list,
    unique,
    validate_subject,
    validate_tags,
)


def _load_knowledge_nodes(root: Path) -> tuple[list[dict[str, Any]], list[Problem]]:
    directory = root / "knowledge/nodes"
    if not directory.is_dir():
        return [], [Problem("knowledge_registry_missing", "knowledge/nodes directory is required", "knowledge/nodes")]
    nodes: list[dict[str, Any]] = []
    problems: list[Problem] = []
    for path in sorted(directory.glob("*.json")):
        rel = path.relative_to(root).as_posix()
        try:
            value = core.load_json(path)
        except (OSError, UnicodeError, ValueError) as exc:
            problems.append(Problem("knowledge_json_invalid", str(exc), rel))
            continue
        if not isinstance(value, dict):
            problems.append(Problem("knowledge_node_invalid", "knowledge node must be a JSON object", rel))
            continue
        nodes.append(value | {"__file__": rel})
    return nodes, problems


def knowledge_nodes(root: Path) -> list[dict[str, Any]]:
    nodes, problems = _load_knowledge_nodes(root)
    if problems:
        raise ValueError("; ".join(item.render() for item in problems))
    return nodes


def public_knowledge_nodes(root: Path) -> list[dict[str, Any]]:
    return [{key: value for key, value in node.items() if key != "__file__"} for node in knowledge_nodes(root)]


def _validate_knowledge_classification(value: Any, source: str) -> list[Problem]:
    if not isinstance(value, dict) or tuple(value) != KNOWLEDGE_CLASSIFICATION_FIELDS:
        return [
            Problem(
                "knowledge_classification_shape_invalid",
                f"expected ordered fields {KNOWLEDGE_CLASSIFICATION_FIELDS}",
                source,
            )
        ]
    problems = validate_subject(value["subject"], source)
    problems.extend(validate_tags(value["object_tags"], "object_tags", source))
    problems.extend(validate_tags(value["method_tags"], "method_tags", source))
    return problems


def validate_knowledge_nodes(root: Path) -> list[Problem]:
    root = root.resolve()
    nodes, problems = _load_knowledge_nodes(root)
    ids: dict[str, str] = {}
    project_ids = {
        item.get("project_id")
        for item in registry_entries(root)
        if isinstance(item.get("project_id"), str)
    }
    shared_ids = known_file_ids(root / "registry/shared-results", SHARED_ID)

    for raw in nodes:
        source = raw["__file__"]
        value = {key: item for key, item in raw.items() if key != "__file__"}
        if tuple(value) != KNOWLEDGE_FIELDS:
            problems.append(Problem("knowledge_fields_invalid", f"expected ordered fields {KNOWLEDGE_FIELDS}", source))
            continue
        knowledge_id = value["knowledge_id"]
        if not isinstance(knowledge_id, str) or not KNOWLEDGE_ID.fullmatch(knowledge_id):
            problems.append(Problem("knowledge_id_invalid", "expected K- followed by at least four digits", source))
            continue
        if Path(source).stem != knowledge_id:
            problems.append(Problem("knowledge_filename_mismatch", "filename must equal knowledge_id.json", source))
        if knowledge_id in ids:
            problems.append(Problem("knowledge_id_duplicate", f"also declared in {ids[knowledge_id]}", source))
        ids[knowledge_id] = source
        if value["schema"] != "jin-math-knowledge-node/v1":
            problems.append(Problem("knowledge_schema_invalid", "unexpected knowledge-node schema", source))
        if value["kind"] not in KNOWLEDGE_KINDS:
            problems.append(Problem("knowledge_kind_invalid", "unknown knowledge kind", source))
        if not nonempty(value["title"]):
            problems.append(Problem("knowledge_title_invalid", "title must be nonempty", source))
        problems.extend(_validate_knowledge_classification(value["classification"], source))
        for field in ("statement", "scope"):
            if not nonempty(value[field]):
                problems.append(Problem("knowledge_text_invalid", f"{field} must be nonempty", source))
        for field in ("assumptions", "conventions"):
            if not string_list(value[field], nonempty_items=False):
                problems.append(Problem("knowledge_list_invalid", f"{field} must be an ordered string array", source))

        prerequisites = value["prerequisites"]
        if (
            not isinstance(prerequisites, list)
            or not unique(prerequisites)
            or not all(isinstance(item, str) and KNOWLEDGE_ID.fullmatch(item) for item in prerequisites)
        ):
            problems.append(Problem("knowledge_prerequisites_invalid", "prerequisites must be unique K-XXXX IDs", source))

        relations = value["relations"]
        relation_keys: set[tuple[str, str]] = set()
        if not isinstance(relations, list):
            problems.append(Problem("knowledge_relations_invalid", "relations must be an array", source))
        else:
            for relation in relations:
                if not isinstance(relation, dict) or tuple(relation) != RELATION_FIELDS:
                    problems.append(Problem("knowledge_relation_shape_invalid", f"relation must contain {RELATION_FIELDS}", source))
                    continue
                relation_type = relation["type"]
                target = relation["target"]
                if (
                    relation_type not in KNOWLEDGE_RELATION_TYPES
                    or not isinstance(target, str)
                    or not RELATION_TARGET.fullmatch(target)
                ):
                    problems.append(Problem("knowledge_relation_invalid", "relation type/target is invalid", source))
                    continue
                key = (relation_type, target)
                if key in relation_keys:
                    problems.append(Problem("knowledge_relation_duplicate", "relation pairs must be unique", source))
                relation_keys.add(key)

        authority = value["authority"]
        if not isinstance(authority, dict) or tuple(authority) != AUTHORITY_FIELDS:
            problems.append(Problem("knowledge_authority_shape_invalid", f"expected ordered fields {AUTHORITY_FIELDS}", source))
        else:
            status = authority["status"]
            receipt = authority["receipt"]
            shared = authority["shared_result"]
            if status not in KNOWLEDGE_AUTHORITY_STATUSES:
                problems.append(Problem("knowledge_authority_status_invalid", "unknown knowledge authority status", source))
            elif status == "reference_only":
                if receipt is not None or shared is not None:
                    problems.append(
                        Problem(
                            "knowledge_reference_authority_invalid",
                            "reference_only cannot carry an authority receipt/shared result",
                            source,
                        )
                    )
            elif status == "source_audited":
                if (
                    not nonempty(receipt)
                    or not core.safe_relative(receipt)
                    or not (root / receipt).is_file()
                    or shared is not None
                ):
                    problems.append(
                        Problem(
                            "knowledge_source_authority_invalid",
                            "source_audited requires an existing receipt and no shared result",
                            source,
                        )
                    )
            elif status == "independently_verified":
                if not nonempty(receipt) or not core.safe_relative(receipt) or not (root / receipt).is_file():
                    problems.append(
                        Problem(
                            "knowledge_verified_receipt_invalid",
                            "independently_verified requires an existing receipt",
                            source,
                        )
                    )
                if not isinstance(shared, str) or not SHARED_ID.fullmatch(shared) or shared not in shared_ids:
                    problems.append(
                        Problem(
                            "knowledge_verified_shared_invalid",
                            "independently_verified requires an existing S-XXXX shared result",
                            source,
                        )
                    )

        if not string_list(value["source_refs"]) or not value["source_refs"]:
            problems.append(
                Problem(
                    "knowledge_sources_missing",
                    "source_refs must contain at least one stable source or repository locator",
                    source,
                )
            )
        if not string_list(value["cannot_imply"]) or not value["cannot_imply"]:
            problems.append(
                Problem(
                    "knowledge_nonimplication_missing",
                    "cannot_imply must contain at least one boundary",
                    source,
                )
            )

    graph: dict[str, list[str]] = {}
    for raw in nodes:
        knowledge_id = raw.get("knowledge_id")
        source = raw.get("__file__", "knowledge/nodes")
        if not isinstance(knowledge_id, str) or not KNOWLEDGE_ID.fullmatch(knowledge_id):
            continue
        prerequisites = raw.get("prerequisites")
        if isinstance(prerequisites, list):
            graph[knowledge_id] = [item for item in prerequisites if isinstance(item, str)]
            for dependency in prerequisites:
                if dependency == knowledge_id:
                    problems.append(Problem("knowledge_self_reference", "knowledge node cannot require itself", source))
                elif dependency not in ids:
                    problems.append(Problem("knowledge_prerequisite_missing", f"unknown prerequisite {dependency}", source))
        relations = raw.get("relations")
        if isinstance(relations, list):
            for relation in relations:
                if not isinstance(relation, dict):
                    continue
                target = relation.get("target")
                if not isinstance(target, str):
                    continue
                if target.startswith("K-") and target not in ids:
                    problems.append(Problem("knowledge_relation_target_missing", f"unknown knowledge target {target}", source))
                elif target.startswith("P-") and target not in project_ids:
                    problems.append(Problem("knowledge_relation_target_missing", f"unknown Project target {target}", source))
                elif target.startswith("S-") and target not in shared_ids:
                    problems.append(Problem("knowledge_relation_target_missing", f"unknown shared-result target {target}", source))
    cycle = first_cycle(graph)
    if cycle:
        problems.append(
            Problem(
                "knowledge_prerequisite_cycle",
                " -> ".join(cycle),
                ids.get(cycle[0], "knowledge/nodes"),
            )
        )
    return problems


def catalog_payload(
    entries: Iterable[dict[str, Any]],
    knowledge_nodes: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    rows = sorted(entries, key=lambda item: item["project_id"])
    nodes = sorted(knowledge_nodes, key=lambda item: item["knowledge_id"])
    tracked = ("active", "review_gate", "compute_wait", "terminal_audit", "closed")
    counts: dict[str, int] = {
        "projects": len(rows),
        **{status: sum(item["operational_status"] == status for item in rows) for status in tracked},
    }
    projected = [
        {
            "project_id": item["project_id"],
            "title": item["title"],
            "classification": item["classification"],
            "operational_status": item["operational_status"],
            "mathematical_status": item["mathematical_status"],
            "project_path": item["project_path"],
            "current_window_id": item["current_window_id"],
            "dependencies": item["dependencies"],
            "result_feedback": item["result_feedback"],
        }
        for item in rows
    ]
    payload: dict[str, Any] = {"schema": "jin-math-catalog/v1", "projects": projected, "counts": counts}
    if nodes:
        payload["knowledge_nodes"] = [
            {
                "knowledge_id": item["knowledge_id"],
                "kind": item["kind"],
                "title": item["title"],
                "classification": item["classification"],
                "prerequisites": item["prerequisites"],
                "relations": item["relations"],
                "authority_status": item["authority"]["status"],
            }
            for item in nodes
        ]
        counts["knowledge_nodes"] = len(nodes)
    return payload


def _markdown_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def frontier_markdown(
    entries: Iterable[dict[str, Any]],
    knowledge_nodes: Iterable[dict[str, Any]] = (),
) -> str:
    rows = sorted(entries, key=lambda item: item["project_id"])
    nodes = sorted(knowledge_nodes, key=lambda item: item["knowledge_id"])
    lines = ["# Research frontier", "", "<!-- Generated by scripts/build_catalog.py. Do not edit manually. -->", ""]
    if not rows:
        lines.append("当前尚未登记研究项目。")
    else:
        lines.extend(
            [
                "| Project | Title | MSC | Origin | Goals | Role | Operational | Mathematical | Feedback | Window |",
                "|---|---|---|---|---|---|---|---|---|---|",
            ]
        )
        for item in rows:
            classification = item["classification"]
            primary = classification["subject"]["primary"]
            goals = ", ".join(classification["goal_types"])
            feedback = item["result_feedback"]["frontier_movement"]
            window = item["current_window_id"] or "-"
            lines.append(
                "| {project} | {title} | {msc} | {origin} | {goals} | {role} | {operational} | {mathematical} | {feedback} | {window} |".format(
                    project=item["project_id"],
                    title=_markdown_escape(item["title"]),
                    msc=primary,
                    origin=classification["origin"],
                    goals=_markdown_escape(goals),
                    role=classification["portfolio_role"],
                    operational=item["operational_status"],
                    mathematical=item["mathematical_status"],
                    feedback=feedback,
                    window=window,
                )
            )
    if nodes:
        lines.extend(
            [
                "",
                "## Knowledge network",
                "",
                "| Node | Kind | Title | MSC | Authority | Prerequisites |",
                "|---|---|---|---|---|---|",
            ]
        )
        for node in nodes:
            prerequisites = ", ".join(node["prerequisites"]) or "-"
            lines.append(
                f"| {node['knowledge_id']} | {node['kind']} | {_markdown_escape(node['title'])} | "
                f"{node['classification']['subject']['primary']} | {node['authority']['status']} | "
                f"{_markdown_escape(prerequisites)} |"
            )
    return "\n".join(lines) + "\n"
