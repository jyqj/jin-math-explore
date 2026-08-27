#!/usr/bin/env python3
"""Create, migrate, and validate math-research-map/v3 reading layers."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

HEX64 = re.compile(r"^[0-9a-f]{64}$")
WIKILINK = re.compile(r"!?(?<!\\)\[\[([^\]]+)\]\]")
MDLINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
ROUTE_FIELDS = {
    "mathematical_object",
    "objective_mechanism",
    "evidence_boundary",
    "missing_work",
    "success_failure_gate",
}
CONTROL_FILES = {
    "research-map.json",
    "asset-references.json",
    "validation-receipt.json",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_bytes(canonical(value))
    os.replace(temp, path)


def safe_rel(value: str) -> str:
    p = PurePosixPath(value.replace("\\", "/"))
    if p.is_absolute() or ".." in p.parts or any(part in ("", ".") for part in p.parts):
        raise ValueError(value)
    return p.as_posix()


def object_path(project: Path, digest: str) -> Path:
    return project / ".research/objects/sha256" / digest[:2] / digest


def project_context(project: Path) -> dict[str, Any]:
    head_path = project / "project.json"
    head = load_json(head_path)
    manifest_path = project / head["archive_manifest"]["path"]
    manifest = load_json(manifest_path)
    manifest_by_path = {e["path"]: e for e in manifest["entries"]}
    objective_path = project / head["project_objective"]["path"]
    state_path = project / head["state"]["path"]
    state = load_json(state_path)
    memory_index = load_json(project / state["memory_index"]["path"])
    memory_ids: set[str] = set()
    memory_paths: dict[str, str] = {}
    for pointer in memory_index.get("items", []):
        item = load_json(project / pointer["path"])
        memory_ids.add(item["memory_id"])
        memory_paths[pointer["path"]] = item["memory_id"]
    return {
        "head": head,
        "head_sha256": sha_file(head_path),
        "objective_sha256": sha_file(objective_path),
        "manifest_by_path": manifest_by_path,
        "memory_ids": memory_ids,
        "memory_paths": memory_paths,
    }


def issue(issues: list[dict[str, Any]], code: str, path: str = "", detail: str = "") -> None:
    item: dict[str, Any] = {"code": code}
    if path:
        item["path"] = path
    if detail:
        item["detail"] = detail
    issues.append(item)


def resolve_note_target(source: Path, raw: str, notes: dict[str, Path], stems: dict[str, list[Path]]) -> tuple[Path | None, str | None]:
    target = raw.split("|", 1)[0].split("#", 1)[0].strip().replace("\\", "/")
    if not target:
        return source, None
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
        return None, "external"
    if target.startswith("./") or "/" in target:
        candidate = (source.parent / target).resolve()
        if candidate.suffix.lower() != ".md":
            candidate = Path(str(candidate) + ".md")
        return (candidate, None) if candidate in notes else (None, "missing")
    key = Path(target).stem.casefold()
    matches = stems.get(key, [])
    if len(matches) == 1:
        return matches[0], None
    return None, "ambiguous" if len(matches) > 1 else "missing"


def validate_v3(map_root: Path, project_root: Path, *, allow_missing_receipt: bool = False) -> dict[str, Any]:
    root = map_root.resolve()
    project = project_root.resolve()
    issues: list[dict[str, Any]] = []
    hidden = root / ".research"
    control_path = hidden / "research-map.json"
    refs_path = hidden / "asset-references.json"
    receipt_path = hidden / "validation-receipt.json"
    if not root.is_dir() or not project.is_dir():
        return {"ok": False, "schema": "math-research-map-validation/v2", "issues": [{"code": "root_missing"}]}
    visible_files = [p for p in root.rglob("*") if p.is_file() and hidden not in p.parents]
    for path in visible_files:
        if path.suffix.lower() != ".md":
            issue(issues, "raw_asset_in_map", path.relative_to(root).as_posix())
    hidden_files = [p for p in hidden.rglob("*") if p.is_file()] if hidden.is_dir() else []
    for path in hidden_files:
        rel = path.relative_to(hidden).as_posix()
        if rel not in CONTROL_FILES:
            issue(issues, "raw_asset_in_map", f".research/{rel}")
    if not control_path.is_file() or not refs_path.is_file():
        issue(issues, "control_file_missing", ".research")
        return {"ok": False, "schema": "math-research-map-validation/v2", "issues": issues}
    if not receipt_path.is_file() and not allow_missing_receipt:
        issue(issues, "validation_receipt_missing", ".research/validation-receipt.json")
    try:
        control = load_json(control_path)
        refs = load_json(refs_path)
        receipt = load_json(receipt_path) if receipt_path.is_file() else None
        ctx = project_context(project)
    except Exception as exc:
        issue(issues, "control_parse_failed", detail=str(exc))
        return {"ok": False, "schema": "math-research-map-validation/v2", "issues": issues}
    if control.get("schema") != "math-research-map/v3":
        issue(issues, "map_schema_mismatch")
    if refs.get("schema") != "math-research-map-asset-references/v2":
        issue(issues, "asset_reference_schema_mismatch")
    if control.get("project_id") != ctx["head"].get("project_id"):
        issue(issues, "project_id_mismatch")
    if control.get("objective_sha256") != ctx["objective_sha256"]:
        issue(issues, "objective_binding_mismatch")
    if control.get("source_head_sha256") != ctx["head_sha256"] or refs.get("source_head_sha256") != ctx["head_sha256"]:
        issue(issues, "source_head_stale")
    if refs.get("map_id") != control.get("map_id"):
        issue(issues, "map_id_mismatch")
    if receipt is not None:
        receipt_binding = (receipt.get("map_id"), receipt.get("map_version"), receipt.get("project_id"), receipt.get("source_head_sha256"))
        expected_binding = (control.get("map_id"), control.get("map_version"), control.get("project_id"), control.get("source_head_sha256"))
        if receipt.get("schema") != "math-research-map-validation-receipt/v1" or receipt_binding != expected_binding:
            issue(issues, "validation_receipt_binding_mismatch")
        semantic_status = receipt.get("semantic_audit", {}).get("status") if isinstance(receipt.get("semantic_audit"), dict) else None
        if control.get("status") == "current" and semantic_status != "PASS":
            issue(issues, "current_without_semantic_pass")

    registered: dict[str, str] = {}
    for key, pointer in control.get("control_notes", {}).items():
        if isinstance(pointer, dict) and isinstance(pointer.get("path"), str):
            registered[pointer["path"]] = f"control:{key}"
    nodes = control.get("nodes", []) if isinstance(control.get("nodes"), list) else []
    node_ids: set[str] = set()
    for node in nodes:
        node_id = node.get("id") if isinstance(node, dict) else None
        note = node.get("note") if isinstance(node, dict) else None
        if not isinstance(node_id, str) or not node_id or node_id in node_ids:
            issue(issues, "node_id_invalid", str(node_id))
            continue
        node_ids.add(node_id)
        if isinstance(note, str):
            registered[note] = f"node:{node_id}"
    notes = {p.relative_to(root).as_posix(): p.resolve() for p in visible_files if p.suffix.lower() == ".md"}
    note_values = {v: k for k, v in notes.items()}
    stems: dict[str, list[Path]] = {}
    for path in notes.values():
        stems.setdefault(path.stem.casefold(), []).append(path)
    for rel, path in notes.items():
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            issue(issues, "blank_markdown", rel)
        if rel not in registered:
            issue(issues, "unregistered_markdown", rel)
        if len(text.strip()) < 80 and not re.search(r"^##?\s+", text, re.M):
            issue(issues, "asset_wrapper_markdown", rel)
        for raw in WIKILINK.findall(text):
            _, error = resolve_note_target(path.resolve(), raw, note_values, stems)
            if error == "missing":
                issue(issues, "wikilink_missing", rel, raw)
            elif error == "ambiguous":
                issue(issues, "wikilink_ambiguous", rel, raw)
        for raw in MDLINK.findall(text):
            target = raw.strip().split()[0].strip("<>")
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            clean = target.split("#", 1)[0]
            if Path(clean).suffix.lower() != ".md":
                issue(issues, "non_markdown_local_link", rel, raw)
            else:
                _, error = resolve_note_target(path.resolve(), clean, note_values, stems)
                if error in ("missing", "ambiguous"):
                    issue(issues, "markdown_link_unresolved", rel, raw)
    for rel, owner in registered.items():
        try:
            safe_rel(rel)
        except Exception:
            issue(issues, "unsafe_note_path", rel)
            continue
        path = root / rel
        if not path.is_file() or path.suffix.lower() != ".md":
            issue(issues, "registered_note_missing", rel, owner)

    asset_by_id: dict[str, dict[str, Any]] = {}
    for asset in refs.get("assets", []) if isinstance(refs.get("assets"), list) else []:
        aid = asset.get("asset_id") if isinstance(asset, dict) else None
        digest = asset.get("object_sha256") if isinstance(asset, dict) else None
        if not isinstance(aid, str) or not aid or aid in asset_by_id:
            issue(issues, "asset_id_invalid", str(aid))
            continue
        asset_by_id[aid] = asset
        if not isinstance(digest, str) or not HEX64.fullmatch(digest):
            issue(issues, "asset_hash_invalid", aid)
            continue
        obj = object_path(project, digest)
        if not obj.is_file():
            issue(issues, "project_object_missing", aid)
        elif sha_file(obj) != digest or obj.stat().st_size != asset.get("size"):
            issue(issues, "project_object_hash_mismatch", aid)
        obj_rel = obj.relative_to(project).as_posix()
        archived = ctx["manifest_by_path"].get(obj_rel)
        if not archived or archived.get("sha256") != digest:
            issue(issues, "project_object_unarchived", aid)
    if refs.get("asset_count") != len(asset_by_id):
        issue(issues, "asset_count_mismatch")
    ledger_memories = set(refs.get("memory_ids", [])) if isinstance(refs.get("memory_ids"), list) else set()
    if not ledger_memories.issubset(ctx["memory_ids"]):
        issue(issues, "memory_id_unresolved")
    ledger_records = set(refs.get("project_records", [])) if isinstance(refs.get("project_records"), list) else set()
    for rel in ledger_records:
        if not isinstance(rel, str) or not (project / rel).is_file() or (rel != "project.json" and rel not in ctx["manifest_by_path"]):
            issue(issues, "project_record_unresolved", str(rel))

    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str):
            continue
        node_id = node["id"]
        note = root / str(node.get("note", ""))
        if note.is_file() and node.get("note_sha256") != sha_file(note):
            issue(issues, "note_hash_mismatch", node_id)
        asset_ids = node.get("required_asset_ids")
        if not isinstance(asset_ids, list) or not all(isinstance(x, str) and x for x in asset_ids):
            issue(issues, "required_asset_ids_invalid", node_id)
            asset_ids = []
        for aid in asset_ids:
            if aid not in asset_by_id:
                issue(issues, "required_asset_unresolved", node_id, aid)
        memories = set(node.get("memory_ids", [])) if isinstance(node.get("memory_ids"), list) else set()
        for mid in memories:
            if mid not in ctx["memory_ids"]:
                issue(issues, "node_memory_unresolved", node_id, str(mid))
        records = set(node.get("project_record_refs", [])) if isinstance(node.get("project_record_refs"), list) else set()
        for rel in records:
            if rel not in ledger_records:
                issue(issues, "node_project_record_unresolved", node_id, str(rel))
        if node.get("kind") == "route":
            route = node.get("route_entry")
            fields = route.get("fields") if isinstance(route, dict) else None
            if not isinstance(fields, dict) or set(fields) != ROUTE_FIELDS:
                issue(issues, "route_context_incomplete", node_id)
                continue
            for field_name, field in fields.items():
                status = field.get("asset_status") if isinstance(field, dict) else None
                refs_list = field.get("source_refs") if isinstance(field, dict) else None
                gap = field.get("gap") if isinstance(field, dict) else None
                if status not in ("supported", "missing_from_assets") or not isinstance(refs_list, list) or not refs_list:
                    issue(issues, "route_evidence_boundary_invalid", node_id, field_name)
                    continue
                if status == "missing_from_assets" and (not isinstance(gap, str) or not gap.strip()):
                    issue(issues, "route_gap_missing", node_id, field_name)
                for source_ref in refs_list:
                    ok = False
                    if isinstance(source_ref, str) and source_ref.startswith("asset:"):
                        ok = source_ref[6:] in asset_ids
                    elif isinstance(source_ref, str) and source_ref.startswith("memory:"):
                        ok = source_ref[7:] in memories
                    elif isinstance(source_ref, str) and source_ref.startswith("project:"):
                        ok = source_ref[8:] in records
                    elif isinstance(source_ref, str) and source_ref.startswith("evidence:"):
                        ok = source_ref[9:] in set(node.get("evidence_sha256s", []))
                    if not ok:
                        issue(issues, "route_source_unresolved", node_id, str(source_ref))
    result = {
        "ok": not issues,
        "schema": "math-research-map-validation/v2",
        "map_schema": control.get("schema"),
        "map_id": control.get("map_id"),
        "map_version": control.get("map_version"),
        "project_id": control.get("project_id"),
        "source_head_sha256": control.get("source_head_sha256"),
        "note_count": len(notes),
        "asset_count": len(asset_by_id),
        "issues": issues,
    }
    return result


def migrate_v2(source: Path, project: Path, stage: Path) -> dict[str, Any]:
    if stage.exists():
        raise RuntimeError(f"Stage exists: {stage}")
    old = load_json(source / "research-map.json")
    old_refs = load_json(source / old["asset_manifest"])
    ctx = project_context(project)
    if old.get("schema") != "math-research-map/v2":
        raise RuntimeError("Source is not a v2 map")
    stage.mkdir(parents=True)
    for path in source.rglob("*.md"):
        if source / ".research" in path.parents:
            continue
        rel = path.relative_to(source)
        target = stage / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        text = path.read_text(encoding="utf-8")
        text = text.replace("`required_assets`", "`required_asset_ids`")
        text = text.replace("`99-资产清单.json`", "`.research/asset-references.json`")
        target.write_text(text, encoding="utf-8")
    old_asset_by_path = {a["path"]: a for a in old_refs["assets"]}
    object_assets: dict[str, dict[str, Any]] = {}
    path_kind: dict[str, tuple[str, str]] = {}
    all_memories: set[str] = set()
    all_records: set[str] = set()
    for rel, asset in old_asset_by_path.items():
        locator = asset.get("source_locator", "")
        if locator.startswith("source-project::"):
            project_rel = locator.split("::", 1)[1]
            if project_rel in ctx["memory_paths"]:
                mid = ctx["memory_paths"][project_rel]
                path_kind[rel] = ("memory", mid)
                all_memories.add(mid)
                continue
            digest = asset["sha256"]
            if not object_path(project, digest).is_file():
                path_kind[rel] = ("project", project_rel)
                all_records.add(project_rel)
                continue
        digest = asset["sha256"]
        obj = object_path(project, digest)
        if not obj.is_file() or sha_file(obj) != digest:
            raise RuntimeError(f"Object not available for {rel}: {digest}")
        aid = f"asset-{digest[:16]}-{sha_bytes(rel.encode('utf-8'))[:8]}"
        path_kind[rel] = ("asset", aid)
        current = object_assets.get(aid)
        if current and current["object_sha256"] != digest:
            raise RuntimeError(f"Asset ID collision: {aid}")
        object_assets[aid] = {
            "asset_id": aid,
            "display_name": Path(rel).name,
            "object_sha256": digest,
            "size": asset["size"],
            "role": asset.get("role", "research_asset"),
            "node_ids": asset.get("node_ids", []),
            "source_locator": locator,
        }

    nodes = []
    for original in old["nodes"]:
        node = json.loads(json.dumps(original, ensure_ascii=False))
        asset_ids: list[str] = []
        records = set(node.get("project_record_refs", []))
        memories = set(node.get("memory_ids", []))
        for rel in node.pop("required_assets", []):
            kind, value = path_kind[rel]
            if kind == "asset":
                asset_ids.append(value)
            elif kind == "memory":
                memories.add(value)
            else:
                records.add(value)
        node["required_asset_ids"] = sorted(set(asset_ids))
        node["memory_ids"] = sorted(memories)
        node["project_record_refs"] = sorted(records)
        if isinstance(node.get("route_entry"), dict):
            for field in node["route_entry"].get("fields", {}).values():
                converted = []
                for ref in field.get("source_refs", []):
                    if ref.startswith("asset:"):
                        kind, value = path_kind[ref[6:]]
                        converted.append(f"{kind}:{value}")
                    else:
                        converted.append(ref)
                field["source_refs"] = sorted(set(converted))
        note_path = stage / node["note"]
        node["note_sha256"] = sha_file(note_path)
        nodes.append(node)
    control_notes = old["control_notes"]
    for pointer in control_notes.values():
        pointer["sha256"] = sha_file(stage / pointer["path"])
    control = {
        "schema": "math-research-map/v3",
        "map_id": old["map_id"],
        "map_version": int(old.get("map_version", 0)) + 1,
        "project_id": ctx["head"]["project_id"],
        "project_schema": ctx["head"]["schema"],
        "objective_sha256": ctx["objective_sha256"],
        "source_head_sha256": ctx["head_sha256"],
        "status": "review_required",
        "status_reason": "v3 migration and structural validation completed; independent semantic audit is still required.",
        "control_notes": control_notes,
        "asset_references": ".research/asset-references.json",
        "active_route_ids": old.get("active_route_ids", []),
        "nodes": nodes,
    }
    refs = {
        "schema": "math-research-map-asset-references/v2",
        "map_id": control["map_id"],
        "source_head_sha256": ctx["head_sha256"],
        "asset_count": len(object_assets),
        "assets": sorted(object_assets.values(), key=lambda x: x["asset_id"]),
        "memory_ids": sorted(all_memories | {m for n in nodes for m in n.get("memory_ids", [])}),
        "project_records": sorted(all_records | {r for n in nodes for r in n.get("project_record_refs", [])}),
    }
    write_json(stage / ".research/research-map.json", control)
    write_json(stage / ".research/asset-references.json", refs)
    preliminary = validate_v3(stage, project, allow_missing_receipt=True)
    if not preliminary["ok"]:
        raise RuntimeError(json.dumps(preliminary, ensure_ascii=False, indent=2))
    receipt = {
        "schema": "math-research-map-validation-receipt/v1",
        "map_id": control["map_id"],
        "map_version": control["map_version"],
        "project_id": control["project_id"],
        "source_head_sha256": ctx["head_sha256"],
        "validated_at_utc": now_utc(),
        "structural_validation": {"ok": True, "note_count": preliminary["note_count"], "asset_count": preliminary["asset_count"]},
        "semantic_audit": {"status": "review_required", "reason": "Independent mathematical fidelity audit has not promoted this map to current."},
    }
    write_json(stage / ".research/validation-receipt.json", receipt)
    final = validate_v3(stage, project)
    if not final["ok"]:
        raise RuntimeError(json.dumps(final, ensure_ascii=False, indent=2))
    return final


def refresh_hashes(map_root: Path, project_root: Path) -> dict[str, Any]:
    root = map_root.resolve()
    project = project_root.resolve()
    control_path = root / ".research/research-map.json"
    control = load_json(control_path)
    for pointer in control.get("control_notes", {}).values():
        pointer["sha256"] = sha_file(root / pointer["path"])
    for node in control.get("nodes", []):
        node["note_sha256"] = sha_file(root / node["note"])
    write_json(control_path, control)
    receipt_path = root / ".research/validation-receipt.json"
    if receipt_path.exists():
        receipt_path.unlink()
    preliminary = validate_v3(root, project, allow_missing_receipt=True)
    if not preliminary["ok"]:
        return preliminary
    receipt = {
        "schema": "math-research-map-validation-receipt/v1",
        "map_id": control["map_id"],
        "map_version": control["map_version"],
        "project_id": control["project_id"],
        "source_head_sha256": control["source_head_sha256"],
        "validated_at_utc": now_utc(),
        "structural_validation": {"ok": True, "note_count": preliminary["note_count"], "asset_count": preliminary["asset_count"]},
        "semantic_audit": {"status": "review_required", "reason": "Independent mathematical fidelity audit has not promoted this map to current."},
    }
    write_json(receipt_path, receipt)
    return validate_v3(root, project)


def inventory(project_root: Path) -> dict[str, Any]:
    project = project_root.resolve()
    ctx = project_context(project)
    objects = [p for p in (project / ".research/objects/sha256").rglob("*") if p.is_file()]
    evidence = [p for p in (project / ".research/evidence").rglob("*") if p.is_file()]
    return {
        "ok": True,
        "schema": "math-research-map-evidence-inventory/v1",
        "project_id": ctx["head"].get("project_id"),
        "source_head_sha256": ctx["head_sha256"],
        "objective_sha256": ctx["objective_sha256"],
        "memory_count": len(ctx["memory_ids"]),
        "project_record_count": len(ctx["manifest_by_path"]),
        "object_count": len(objects),
        "evidence_record_count": len(evidence),
    }


def record_semantic_audit(map_root: Path, project_root: Path, audit_file: Path) -> dict[str, Any]:
    root = map_root.resolve()
    project = project_root.resolve()
    audit_path = audit_file.resolve()
    audit = load_json(audit_path)
    control_path = root / ".research/research-map.json"
    control = load_json(control_path)
    preliminary = validate_v3(root, project)
    if not preliminary.get("ok"):
        return preliminary
    expected = (control.get("map_id"), control.get("map_version"), control.get("project_id"), control.get("source_head_sha256"))
    received = (audit.get("map_id"), audit.get("map_version"), audit.get("project_id"), audit.get("source_head_sha256"))
    if audit.get("schema") != "math-research-map-semantic-audit/v1" or audit.get("verdict") != "PASS" or received != expected:
        return {"ok": False, "schema": "math-research-map-validation/v2", "issues": [{"code": "semantic_audit_receipt_invalid"}]}
    control["status"] = "current"
    control["status_reason"] = "Full structural, formula, link, object, binding, and independent semantic audits passed for this source head."
    write_json(control_path, control)
    receipt = {
        "schema": "math-research-map-validation-receipt/v1",
        "map_id": control["map_id"],
        "map_version": control["map_version"],
        "project_id": control["project_id"],
        "source_head_sha256": control["source_head_sha256"],
        "validated_at_utc": now_utc(),
        "structural_validation": {"ok": True, "note_count": preliminary["note_count"], "asset_count": preliminary["asset_count"]},
        "semantic_audit": {"status": "PASS", "audit_record_sha256": sha_file(audit_path), "auditor_role": audit.get("auditor_role", "independent")},
    }
    write_json(root / ".research/validation-receipt.json", receipt)
    return validate_v3(root, project)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("map_root", type=Path)
    validate.add_argument("--project-root", type=Path, required=True)
    migrate = sub.add_parser("migrate-v2")
    migrate.add_argument("map_root", type=Path)
    migrate.add_argument("--project-root", type=Path, required=True)
    migrate.add_argument("--stage-root", type=Path, required=True)
    refresh = sub.add_parser("refresh")
    refresh.add_argument("map_root", type=Path)
    refresh.add_argument("--project-root", type=Path, required=True)
    inventory_parser = sub.add_parser("inventory")
    inventory_parser.add_argument("--project-root", type=Path, required=True)
    audit_parser = sub.add_parser("record-audit")
    audit_parser.add_argument("map_root", type=Path)
    audit_parser.add_argument("--project-root", type=Path, required=True)
    audit_parser.add_argument("--audit-file", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "validate":
        result = validate_v3(args.map_root, args.project_root)
    elif args.command == "migrate-v2":
        result = migrate_v2(args.map_root.resolve(), args.project_root.resolve(), args.stage_root.resolve())
    elif args.command == "refresh":
        result = refresh_hashes(args.map_root, args.project_root)
    elif args.command == "inventory":
        result = inventory(args.project_root)
    else:
        result = record_semantic_audit(args.map_root, args.project_root, args.audit_file)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
