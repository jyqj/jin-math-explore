#!/usr/bin/env python3
"""Validate the structural and byte-integrity contract of a research map."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import deque
from pathlib import Path
from typing import Any
from urllib.parse import unquote


HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]*\]\((<[^>]+>|[^)\s]+)(?:\s+[\"'][^)]+[\"'])?\)")
ASSET_ROOT = ".research/assets"

CONTROL_PATHS = {
    "contract": "00-研究地图契约.md",
    "main": "01-主研究地图.md",
    "evidence_rules": "02-阅读说明与证据规则.md",
    "next_routes": "40-当前候选路线与下一步.md",
    "asset_index": "90-资产索引.md",
}
NODE_PREFIXES = {
    "milestone": "10-里程碑-",
    "route": "20-路线-",
    "bridge": "25-桥梁-",
    "experiment": "30-实验-",
}
NODE_STATES = {"active", "paused", "closed", "invalidated", "historical"}
NODE_SLOTS = {
    "summary",
    "motivation",
    "scope",
    "argument",
    "computer_boundary",
    "audit",
    "limits_reopen",
}
ROUTE_ENTRY_FIELDS = {
    "mathematical_object": "数学对象：",
    "objective_mechanism": "连接最终目标的机制：",
    "evidence_boundary": "已有证据：",
    "missing_work": "尚缺内容：",
    "success_failure_gate": "下一步成败判据：",
}
ROUTE_ENTRY_ASSET_STATUSES = {"supported", "missing_from_assets"}
REQUIRED_HEADINGS = {
    "main": {"研究主线", "当前研究判断", "如何审计"},
    "evidence_rules": {"三层结构", "证据词的含义", "原始资产与解释页", "AI 启动规则"},
    "next_routes": {"恢复研究时的读取集合"},
    "asset_index": {"哈希与来源"},
}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("map_root", help="Research-map folder.")
    result.add_argument("--expected-objective-sha256")
    result.add_argument("--expected-source-head-sha256")
    result.add_argument("--expected-project-schema")
    result.add_argument("--allow-stale", action="store_true")
    return result


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path, issues: list[dict[str, str]]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # precise exception text is useful and contains no file body
        issues.append({"code": "invalid_json", "path": path.name, "detail": type(exc).__name__})
        return None


def relative_file(root: Path, value: Any, issues: list[dict[str, str]], code: str) -> Path | None:
    if not isinstance(value, str) or not value:
        issues.append({"code": code, "path": "<missing>"})
        return None
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        issues.append({"code": "path_escape", "path": value})
        return None
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        issues.append({"code": "path_escape", "path": value})
        return None
    if not resolved.is_file() or resolved.is_symlink():
        issues.append({"code": code, "path": value})
        return None
    return resolved


def heading_names(text: str) -> set[str]:
    return {match.group(2).strip() for match in HEADING.finditer(text)}


def heading_section(text: str, heading: str) -> str | None:
    matches = list(HEADING.finditer(text))
    selected = [index for index, match in enumerate(matches) if match.group(2).strip() == heading]
    if len(selected) != 1:
        return None
    index = selected[0]
    level = len(matches[index].group(1))
    start = matches[index].end()
    end = len(text)
    for later in matches[index + 1 :]:
        if len(later.group(1)) <= level:
            end = later.start()
            break
    return text[start:end]


def validate_route_entry(
    node: dict[str, Any],
    node_id: str,
    note_rel: str,
    text: str | None,
    issues: list[dict[str, str]],
) -> None:
    route_entry = node.get("route_entry")
    if not isinstance(route_entry, dict) or set(route_entry) != {"heading", "fields"}:
        issues.append({"code": "invalid_route_entry", "path": node_id})
        return

    heading = route_entry.get("heading")
    if not isinstance(heading, str) or not heading:
        issues.append({"code": "invalid_route_entry_heading", "path": node_id})
    elif text is not None:
        section = heading_section(text, heading)
        if section is None:
            issues.append({"code": "missing_or_ambiguous_route_entry_section", "path": note_rel})
        else:
            for field, label in ROUTE_ENTRY_FIELDS.items():
                if label not in section:
                    issues.append(
                        {"code": "missing_route_entry_label", "path": note_rel, "detail": field}
                    )

    fields = route_entry.get("fields")
    if not isinstance(fields, dict) or set(fields) != set(ROUTE_ENTRY_FIELDS):
        issues.append({"code": "invalid_route_entry_fields", "path": node_id})
        return

    memory_ids = (
        {value for value in node.get("memory_ids", []) if isinstance(value, str)}
        if isinstance(node.get("memory_ids"), list)
        else set()
    )
    evidence_sha256s = (
        {value for value in node.get("evidence_sha256s", []) if isinstance(value, str)}
        if isinstance(node.get("evidence_sha256s"), list)
        else set()
    )
    required_assets = (
        {value for value in node.get("required_assets", []) if isinstance(value, str)}
        if isinstance(node.get("required_assets"), list)
        else set()
    )
    bound_sources = {
        **{f"memory:{value}": value for value in memory_ids if isinstance(value, str)},
        **{f"evidence:{value}": value for value in evidence_sha256s if isinstance(value, str)},
        **{f"asset:{value}": value for value in required_assets if isinstance(value, str)},
    }

    for field in sorted(ROUTE_ENTRY_FIELDS):
        entry = fields.get(field)
        path = f"{node_id}.route_entry.{field}"
        if not isinstance(entry, dict) or set(entry) != {"asset_status", "source_refs", "gap"}:
            issues.append({"code": "invalid_route_entry_field", "path": path})
            continue
        asset_status = entry.get("asset_status")
        if asset_status not in ROUTE_ENTRY_ASSET_STATUSES:
            issues.append({"code": "invalid_route_entry_asset_status", "path": path})
        source_refs = entry.get("source_refs")
        valid_source_ref_list = (
            isinstance(source_refs, list)
            and bool(source_refs)
            and all(isinstance(value, str) and value for value in source_refs)
        )
        if not valid_source_ref_list or len(source_refs) != len(set(source_refs)):
            issues.append({"code": "invalid_route_entry_source_refs", "path": path})
        else:
            for source_ref in source_refs:
                if source_ref not in bound_sources:
                    issues.append(
                        {"code": "unbound_route_entry_source", "path": path, "detail": source_ref}
                    )
        gap = entry.get("gap")
        if not isinstance(gap, str):
            issues.append({"code": "invalid_route_entry_gap", "path": path})
        elif asset_status == "supported" and gap:
            issues.append({"code": "supported_route_entry_has_gap", "path": path})
        elif asset_status == "missing_from_assets" and not gap.strip():
            issues.append({"code": "missing_route_entry_gap", "path": path})


def read_note(path: Path, issues: list[dict[str, str]], rel: str) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        issues.append({"code": "note_not_utf8", "path": rel})
    except OSError as exc:
        issues.append({"code": "note_unreadable", "path": rel, "detail": type(exc).__name__})
    return None


def normalized_link_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    return unquote(target).strip()


def resolve_wikilink(
    root: Path,
    source: Path,
    raw: str,
    notes: dict[str, Path],
    stems: dict[str, list[str]],
) -> tuple[str | None, str | None]:
    target = raw.split("|", 1)[0].strip()
    target, _, anchor = target.partition("#")
    if not target:
        rel = source.relative_to(root).as_posix()
        return rel, anchor or None
    target = target.replace("\\", "/")
    candidates = []
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
    if len(unique) == 1:
        return unique[0], anchor or None
    return None, anchor or None


def validate_links(
    root: Path,
    notes: dict[str, Path],
    note_text: dict[str, str],
    issues: list[dict[str, str]],
) -> dict[str, set[str]]:
    stems: dict[str, list[str]] = {}
    for rel in notes:
        stems.setdefault(Path(rel).stem.casefold(), []).append(rel)
    graph: dict[str, set[str]] = {rel: set() for rel in notes}
    for rel, text in note_text.items():
        source = notes[rel]
        for match in WIKILINK.finditer(text):
            target_rel, anchor = resolve_wikilink(root, source, match.group(1), notes, stems)
            if target_rel is None:
                issues.append({"code": "broken_or_ambiguous_wikilink", "path": rel})
                continue
            graph[rel].add(target_rel)
            if anchor and anchor not in heading_names(note_text[target_rel]):
                issues.append({"code": "missing_wikilink_heading", "path": rel})
        for match in MARKDOWN_LINK.finditer(text):
            target = normalized_link_target(match.group(1))
            if not target or target.startswith(("http://", "https://", "mailto:", "obsidian://", "#")):
                continue
            target = target.split("#", 1)[0]
            candidate = (source.parent / target).resolve()
            if candidate.suffix.casefold() != ".md":
                issues.append({"code": "non_markdown_local_hyperlink", "path": rel})
                continue
            try:
                target_rel = candidate.relative_to(root).as_posix()
            except ValueError:
                issues.append({"code": "path_escape_link", "path": rel})
                continue
            if not candidate.is_file() or candidate.is_symlink():
                issues.append({"code": "broken_markdown_link", "path": rel})
                continue
            if target_rel in notes:
                graph[rel].add(target_rel)
    return graph


def validate_map(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.map_root).expanduser().resolve()
    issues: list[dict[str, str]] = []
    if not root.is_dir() or root.is_symlink():
        return {"ok": False, "schema": "math-research-map-validation/v1", "issues": [{"code": "invalid_map_root"}]}

    map_path = root / "research-map.json"
    manifest_path = root / "99-资产清单.json"
    if not map_path.is_file():
        issues.append({"code": "missing_control_file", "path": map_path.name})
    if not manifest_path.is_file():
        issues.append({"code": "missing_control_file", "path": manifest_path.name})
    if issues:
        return {"ok": False, "schema": "math-research-map-validation/v1", "issues": issues}

    data = load_json(map_path, issues)
    manifest = load_json(manifest_path, issues)
    if not isinstance(data, dict) or not isinstance(manifest, dict):
        return {"ok": False, "schema": "math-research-map-validation/v1", "issues": issues}

    if data.get("schema") != "math-research-map/v2":
        issues.append({"code": "map_schema_mismatch", "path": "research-map.json"})
    if manifest.get("schema") != "math-research-map-asset-manifest/v1":
        issues.append({"code": "manifest_schema_mismatch", "path": "99-资产清单.json"})
    for field in ("map_id", "project_id", "project_schema"):
        if not isinstance(data.get(field), str) or not data[field]:
            issues.append({"code": "missing_map_field", "path": field})
    if not isinstance(data.get("map_version"), int) or data["map_version"] < 1:
        issues.append({"code": "invalid_map_version", "path": "map_version"})
    for field in ("objective_sha256", "source_head_sha256"):
        if not isinstance(data.get(field), str) or not HEX64.fullmatch(data[field]):
            issues.append({"code": "invalid_sha256", "path": field})
    if data.get("status") not in {"current", "stale", "review_required"}:
        issues.append({"code": "invalid_map_status", "path": "status"})
    if data.get("status") != "current" and not args.allow_stale:
        issues.append({"code": "map_not_current", "path": "status"})
    expectations = (
        ("objective_sha256", args.expected_objective_sha256),
        ("source_head_sha256", args.expected_source_head_sha256),
        ("project_schema", args.expected_project_schema),
    )
    for field, expected in expectations:
        if expected is not None and data.get(field) != expected:
            issues.append({"code": "expected_binding_mismatch", "path": field})

    notes: dict[str, Path] = {}
    note_text: dict[str, str] = {}
    control = data.get("control_notes")
    if not isinstance(control, dict):
        issues.append({"code": "invalid_control_notes", "path": "control_notes"})
        control = {}
    for key, expected_path in CONTROL_PATHS.items():
        entry = control.get(key)
        if not isinstance(entry, dict) or entry.get("path") != expected_path:
            issues.append({"code": "control_path_mismatch", "path": key})
            continue
        path = relative_file(root, entry.get("path"), issues, "missing_control_note")
        expected_hash = entry.get("sha256")
        if path is None:
            continue
        if not isinstance(expected_hash, str) or not HEX64.fullmatch(expected_hash) or sha256_file(path) != expected_hash:
            issues.append({"code": "control_note_hash_mismatch", "path": expected_path})
        notes[expected_path] = path
        text = read_note(path, issues, expected_path)
        if text is not None:
            note_text[expected_path] = text
            missing = REQUIRED_HEADINGS.get(key, set()) - heading_names(text)
            for heading in sorted(missing):
                issues.append({"code": "missing_control_heading", "path": expected_path, "detail": heading})

    nodes = data.get("nodes")
    if not isinstance(nodes, list):
        issues.append({"code": "invalid_nodes", "path": "nodes"})
        nodes = []
    node_ids: set[str] = set()
    node_records: dict[str, dict[str, Any]] = {}
    for index, node in enumerate(nodes):
        label = f"nodes[{index}]"
        if not isinstance(node, dict):
            issues.append({"code": "invalid_node", "path": label})
            continue
        node_id = node.get("id")
        kind = node.get("kind")
        state = node.get("state")
        note_rel = node.get("note")
        text: str | None = None
        if not isinstance(node_id, str) or not node_id or node_id in node_ids:
            issues.append({"code": "invalid_or_duplicate_node_id", "path": label})
            continue
        node_ids.add(node_id)
        node_records[node_id] = node
        if kind not in NODE_PREFIXES:
            issues.append({"code": "invalid_node_kind", "path": node_id})
        if state not in NODE_STATES:
            issues.append({"code": "invalid_node_state", "path": node_id})
        if not isinstance(note_rel, str) or kind not in NODE_PREFIXES or not Path(note_rel).name.startswith(NODE_PREFIXES[kind]):
            issues.append({"code": "node_filename_kind_mismatch", "path": node_id})
        path = relative_file(root, note_rel, issues, "missing_node_note")
        if path is None or not isinstance(note_rel, str):
            continue
        expected_hash = node.get("note_sha256")
        if not isinstance(expected_hash, str) or not HEX64.fullmatch(expected_hash) or sha256_file(path) != expected_hash:
            issues.append({"code": "node_note_hash_mismatch", "path": note_rel})
        notes[note_rel] = path
        text = read_note(path, issues, note_rel)
        if text is not None:
            note_text[note_rel] = text
            sections = node.get("sections")
            if not isinstance(sections, dict) or set(sections) != NODE_SLOTS:
                issues.append({"code": "invalid_node_sections", "path": node_id})
            else:
                available = heading_names(text)
                for slot in sorted(NODE_SLOTS):
                    heading = sections.get(slot)
                    if not isinstance(heading, str) or heading not in available:
                        issues.append({"code": "missing_node_section", "path": note_rel, "detail": slot})
        if not isinstance(node.get("memory_ids"), list) or not all(isinstance(x, str) and x for x in node["memory_ids"]):
            issues.append({"code": "invalid_memory_ids", "path": node_id})
        evidence = node.get("evidence_sha256s")
        if not isinstance(evidence, list) or not all(isinstance(x, str) and HEX64.fullmatch(x) for x in evidence):
            issues.append({"code": "invalid_evidence_hashes", "path": node_id})
        required_assets = node.get("required_assets")
        if not isinstance(required_assets, list) or not all(isinstance(x, str) and x for x in required_assets):
            issues.append({"code": "invalid_required_assets", "path": node_id})
        if kind == "route":
            validate_route_entry(node, node_id, note_rel if isinstance(note_rel, str) else label, text, issues)
        elif "route_entry" in node:
            issues.append({"code": "route_entry_on_non_route_node", "path": node_id})

    active_routes = data.get("active_route_ids")
    if not isinstance(active_routes, list) or len(active_routes) != len(set(active_routes)):
        issues.append({"code": "invalid_active_routes", "path": "active_route_ids"})
        active_routes = []
    for node_id in active_routes:
        node = node_records.get(node_id)
        if not node or node.get("kind") != "route" or node.get("state") != "active":
            issues.append({"code": "active_route_mismatch", "path": str(node_id)})

    if data.get("asset_manifest") != "99-资产清单.json":
        issues.append({"code": "asset_manifest_path_mismatch", "path": "asset_manifest"})
    if manifest.get("map_id") != data.get("map_id"):
        issues.append({"code": "manifest_map_id_mismatch", "path": "99-资产清单.json"})
    if manifest.get("source_head_sha256") != data.get("source_head_sha256"):
        issues.append({"code": "manifest_head_mismatch", "path": "99-资产清单.json"})
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        issues.append({"code": "invalid_assets", "path": "99-资产清单.json"})
        assets = []
    listed_assets: set[str] = set()
    for index, asset in enumerate(assets):
        label = f"assets[{index}]"
        if not isinstance(asset, dict):
            issues.append({"code": "invalid_asset", "path": label})
            continue
        rel = asset.get("path")
        if not isinstance(rel, str) or not rel.startswith(ASSET_ROOT + "/") or rel in listed_assets:
            issues.append({"code": "invalid_or_duplicate_asset_path", "path": label})
            continue
        listed_assets.add(rel)
        path = relative_file(root, rel, issues, "missing_asset")
        recorded_hash = asset.get("sha256")
        source_hash = asset.get("source_sha256")
        if not isinstance(recorded_hash, str) or not HEX64.fullmatch(recorded_hash):
            issues.append({"code": "invalid_sha256", "path": rel})
        if source_hash != recorded_hash:
            issues.append({"code": "source_export_hash_mismatch", "path": rel})
        if path is not None:
            if sha256_file(path) != recorded_hash:
                issues.append({"code": "asset_hash_mismatch", "path": rel})
            if asset.get("size") != path.stat().st_size:
                issues.append({"code": "asset_size_mismatch", "path": rel})
        if not isinstance(asset.get("source_locator"), str) or not asset["source_locator"]:
            issues.append({"code": "missing_source_locator", "path": rel})
        if not isinstance(asset.get("role"), str) or not asset["role"]:
            issues.append({"code": "missing_asset_role", "path": rel})
        asset_nodes = asset.get("node_ids")
        if not isinstance(asset_nodes, list) or not asset_nodes or any(x not in node_ids for x in asset_nodes):
            issues.append({"code": "invalid_asset_node_ids", "path": rel})

    visible_asset_root = root / "assets"
    if visible_asset_root.exists():
        issues.append({"code": "visible_assets_directory_forbidden", "path": "assets"})
    asset_root = root / ASSET_ROOT
    physical_assets: set[str] = set()
    if not asset_root.is_dir() or asset_root.is_symlink():
        issues.append({"code": "missing_assets_directory", "path": ASSET_ROOT})
    else:
        for path in asset_root.rglob("*"):
            if path.is_symlink():
                issues.append({"code": "asset_symlink_forbidden", "path": path.relative_to(root).as_posix()})
            elif path.is_file():
                physical_assets.add(path.relative_to(root).as_posix())
    for rel in sorted(physical_assets - listed_assets):
        issues.append({"code": "unlisted_asset", "path": rel})
    for rel in sorted(listed_assets - physical_assets):
        issues.append({"code": "listed_asset_missing", "path": rel})
    for node_id, node in node_records.items():
        for rel in node.get("required_assets", []) if isinstance(node.get("required_assets"), list) else []:
            if rel not in listed_assets:
                issues.append({"code": "required_asset_not_manifested", "path": node_id})

    graph = validate_links(root, notes, note_text, issues)
    main_rel = CONTROL_PATHS["main"]
    reached: set[str] = set()
    if main_rel in graph:
        queue: deque[str] = deque([main_rel])
        while queue:
            current = queue.popleft()
            if current in reached:
                continue
            reached.add(current)
            queue.extend(graph.get(current, set()) - reached)
    required_reachable = set(notes) - {main_rel}
    for rel in sorted(required_reachable - reached):
        issues.append({"code": "note_unreachable_from_main", "path": rel})

    objective = data.get("objective_sha256")
    for rel in (CONTROL_PATHS["contract"], CONTROL_PATHS["main"]):
        if rel in note_text and isinstance(objective, str) and objective not in note_text[rel]:
            issues.append({"code": "objective_hash_not_visible", "path": rel})

    return {
        "ok": not issues,
        "schema": "math-research-map-validation/v1",
        "status": data.get("status"),
        "map_version": data.get("map_version"),
        "counts": {
            "control_notes": len(control),
            "nodes": len(node_ids),
            "active_routes": len(active_routes),
            "route_entries": sum(
                1
                for node in node_records.values()
                if node.get("kind") == "route" and isinstance(node.get("route_entry"), dict)
            ),
            "assets": len(listed_assets),
            "reachable_notes": len(reached),
        },
        "issues": issues,
    }


def main() -> int:
    args = parser().parse_args()
    result = validate_map(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
