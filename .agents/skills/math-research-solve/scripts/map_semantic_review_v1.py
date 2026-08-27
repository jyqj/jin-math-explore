#!/usr/bin/env python3
"""Fail-closed semantic review closure for v13 research maps.

This module intentionally contains both the author-side packet builder and the
host-side verifier.  A reviewer receives only the packet and ticket.  It never
receives a project root, an object store, imports, recovery material, or logs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any, Callable

try:
    from v13_common import configure_stdio
except ImportError:  # pragma: no cover - permits isolated import by other harnesses
    def configure_stdio() -> None:
        return None


PACKET_SCHEMA = "math-research-map-review-packet/v1"
TICKET_SCHEMA = "math-research-map-review-ticket/v1"
RESULT_SCHEMA = "math-research-map-review-result/v1"
CLOSURE_SCHEMA = "math-research-map-review-closure/v1"
VALIDATION_SCHEMA = "math-research-map-review-validation/v1"
REVIEWER_MODE = "fresh_subagent"
MAX_CYCLES = 3
HEX64 = re.compile(r"^[0-9a-f]{64}$")
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
FORBIDDEN_COMPONENTS = {
    "raw", "raw-object", "raw-objects", "object", "objects", "object-store",
    "imports", "import", "recovery", "recovery-tree", "restore", "logs", "log",
    ".git", "worktree", "snapshots",
}
ALLOWED_EVIDENCE_CATEGORIES = (
    "research-map-control", "visible-map-note", "objective-commitment",
    "authority-manifest", "authority-inventory-summary", "structural-validation",
    "terminal-sufficient-condition-register", "retrieval-slice",
)
EXCLUDED_EVIDENCE_CATEGORIES = (
    "raw-objects", "imports", "recovery-tree", "logs", "unrelated-project-files",
)

PACKET_FIELDS = {
    "schema", "protocol", "project", "candidate", "authority", "structural_validation",
    "evidence_boundary",
}
TICKET_FIELDS = {
    "schema", "ticket_id", "packet_sha256", "protocol_sha256", "project_id",
    "candidate_map_sha256", "visible_tree_inventory_sha256",
    "authority_manifest_sha256", "authority_inventory_sha256",
    "structural_receipt_sha256", "author_principal", "reviewer_principal",
    "reviewer_mode", "dispatch_id", "cycle", "max_cycles", "prior_result_sha256",
    "repair_lineage", "result_contract_sha256", "retrieval_request_sha256",
}
RESULT_FIELDS = {
    "schema", "ticket_id", "packet_sha256", "protocol_sha256", "project_id",
    "candidate_map_sha256", "visible_tree_inventory_sha256",
    "authority_manifest_sha256", "authority_inventory_sha256",
    "structural_receipt_sha256", "reviewer_principal", "reviewer_mode", "dispatch_id",
    "cycle", "authority_coverage", "synthesis_checks", "evidence_boundary",
    "verdict", "repairs", "unresolved",
}
CLOSURE_FIELDS = {
    "schema", "protocol_sha256", "project_id", "project_objective_sha256",
    "author_principal", "bindings", "rounds", "repair_lineage", "final_pass", "status",
}


class ReviewError(RuntimeError):
    def __init__(self, code: str, message: str, path: str = ""):
        super().__init__(message)
        self.code, self.message, self.path = code, message, path


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def document_sha256(value: Any) -> str:
    return sha256(canonical(value))


def ticket_id_for(ticket: dict[str, Any]) -> str:
    """Return the content-derived ID for every ticket field except the ID itself."""
    payload = {key: ticket[key] for key in TICKET_FIELDS if key != "ticket_id"}
    return "map-review-" + document_sha256(payload)[:24]


def load_json_bytes(raw: bytes) -> Any:
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw:
        raise ReviewError("json_encoding_invalid", "JSON must be UTF-8 without BOM and use LF", "")
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise ReviewError("json_invalid", str(exc), "") from exc


def _exact(value: Any, fields: set[str], path: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ReviewError("closed_schema_fields_invalid", f"Expected exactly {sorted(fields)}", path)
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReviewError("nonempty_string_required", "A nonempty string is required", path)
    return value


def _hash(value: Any, path: str) -> str:
    if not isinstance(value, str) or not HEX64.fullmatch(value):
        raise ReviewError("sha256_invalid", "Expected a lowercase SHA-256", path)
    return value


def _relative(value: Any, path: str, *, allow_forbidden: bool = False) -> str:
    text = _string(value, path)
    if "\\" in text or "\x00" in text:
        raise ReviewError("path_unsafe", "Use a POSIX project-relative path", path)
    rel = PurePosixPath(text)
    if rel.is_absolute() or any(part in ("", ".", "..") for part in rel.parts) or ":" in rel.parts[0]:
        raise ReviewError("path_unsafe", "Absolute and traversal paths are forbidden", path)
    if not allow_forbidden and any(part.casefold() in FORBIDDEN_COMPONENTS for part in rel.parts):
        raise ReviewError("forbidden_evidence_path", "Raw/import/recovery/log paths cannot enter a reviewer packet", path)
    return rel.as_posix()


def _default_reader(root: Path) -> Callable[[str], bytes]:
    base = root.resolve(strict=True)

    def read(rel_text: str) -> bytes:
        rel = PurePosixPath(_relative(rel_text, "binding", allow_forbidden=True))
        target = base.joinpath(*rel.parts)
        if target.is_symlink() or not target.is_file():
            raise ReviewError("binding_missing", "Bound file is missing or is a reparse point", rel_text)
        resolved = target.resolve(strict=True)
        if base not in resolved.parents:
            raise ReviewError("path_escape", "Bound file escapes project root", rel_text)
        return target.read_bytes()

    return read


def _read_json(reader: Callable[[str], bytes], path: str) -> Any:
    try:
        return load_json_bytes(reader(path))
    except ReviewError:
        raise
    except Exception as exc:
        raise ReviewError("binding_read_failed", str(exc), path) from exc


def _inventory_hash(rows: list[dict[str, Any]]) -> str:
    return document_sha256(rows)


def _visible_rows(root: Path, reader: Callable[[str], bytes], map_control_path: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    base = root.resolve(strict=True)
    rows: list[dict[str, Any]] = []
    documents: list[dict[str, Any]] = []
    control_parts = PurePosixPath(map_control_path).parts
    if len(control_parts) < 3 or control_parts[-2] != ".research":
        raise ReviewError("map_control_location_invalid", "Map control must be MAP_ROOT/.research/research-map.json", map_control_path)
    map_root = base.joinpath(*control_parts[:-2])
    candidates = [path for path in map_root.rglob("*.md") if path.is_file() and not path.is_symlink() and ".research" not in path.relative_to(map_root).parts]
    for path in sorted(candidates, key=lambda p: p.relative_to(base).as_posix().casefold()):
        rel = path.relative_to(base).as_posix()
        if any(part.casefold() in FORBIDDEN_COMPONENTS for part in PurePosixPath(rel).parts):
            continue
        raw = reader(rel)
        try:
            content = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise ReviewError("visible_note_not_utf8", str(exc), rel) from exc
        rows.append({"path": rel, "size": len(raw), "sha256": sha256(raw)})
        documents.append({"path": rel, "sha256": sha256(raw), "content": content})
    main_rel = PurePosixPath(*control_parts[:-2], "01-主研究地图.md").as_posix()
    try:
        main = reader(main_rel).decode("utf-8", errors="strict")
    except Exception as exc:
        raise ReviewError("main_map_read_failed", str(exc), main_rel) from exc
    sufficient_marker = re.compile(
        r"<!--\s*research-map-sufficient-condition-topic:v1\s+(?P<payload>\{[^\r\n]*\})\s*-->"
    )
    register_paths: set[str] = set()
    for marker in sufficient_marker.finditer(main):
        try:
            payload = json.loads(marker.group("payload"))
        except json.JSONDecodeError as exc:
            raise ReviewError("sufficient_condition_marker_invalid_json", str(exc), main_rel) from exc
        register_rel = payload.get("register_path") if isinstance(payload, dict) else None
        register_posix = PurePosixPath(str(register_rel))
        if (
            not isinstance(register_rel, str)
            or register_posix.is_absolute()
            or ".." in register_posix.parts
            or register_posix.suffix.lower() != ".json"
            or register_posix.parts[:2] != (".research", "sufficient-conditions")
        ):
            raise ReviewError("sufficient_condition_register_path_invalid", "Register path is outside the closed map location", main_rel)
        project_rel = PurePosixPath(*control_parts[:-2], *register_posix.parts).as_posix()
        register_paths.add(project_rel)
    for rel in sorted(register_paths, key=str.casefold):
        raw = reader(rel)
        try:
            content = raw.decode("utf-8", errors="strict")
            load_json_bytes(raw)
        except Exception as exc:
            raise ReviewError("sufficient_condition_register_invalid", str(exc), rel) from exc
        rows.append({"path": rel, "size": len(raw), "sha256": sha256(raw)})
        documents.append({"path": rel, "sha256": sha256(raw), "content": content})
    control_raw = reader(map_control_path)
    rows.append({"path": map_control_path, "size": len(control_raw), "sha256": sha256(control_raw)})
    rows.sort(key=lambda row: row["path"].casefold())
    return rows, documents


def _authority_entries(value: Any) -> list[dict[str, str]]:
    if isinstance(value, dict) and set(value) == {"entries"}:
        value = value["entries"]
    if not isinstance(value, list) or not value:
        raise ReviewError("authority_inventory_invalid", "Authority inventory must contain at least one entry", "authority_inventory")
    rows: list[dict[str, str]] = []
    ids: set[str] = set()
    for index, item in enumerate(value):
        path = f"authority_inventory[{index}]"
        if not isinstance(item, dict) or not {"authority_id", "kind", "sha256", "summary"} <= set(item):
            raise ReviewError("authority_entry_invalid", "Each entry needs authority_id, kind, sha256, and summary", path)
        authority_id = _string(item["authority_id"], path + ".authority_id")
        if authority_id in ids:
            raise ReviewError("authority_id_duplicate", "Authority identifiers must be unique", path)
        ids.add(authority_id)
        rows.append({
            "authority_id": authority_id,
            "kind": _string(item["kind"], path + ".kind"),
            "sha256": _hash(item["sha256"], path + ".sha256"),
            "summary": _string(item["summary"], path + ".summary"),
        })
    return sorted(rows, key=lambda row: row["authority_id"])


def _required_authority_bindings(
    head: Any,
    manifest: Any,
    map_control: Any,
    *,
    head_sha256: str,
    manifest_sha256: str,
) -> dict[str, str | None]:
    """Derive IDs and every available exact hash from authoritative objects."""
    required: dict[str, str | None] = {
        "authority-head": head_sha256,
        "authority-manifest": manifest_sha256,
    }

    def walk(node: Any, trail: tuple[str, ...] = ()) -> None:
        if isinstance(node, dict):
            if isinstance(node.get("path"), str) and HEX64.fullmatch(str(node.get("sha256", ""))):
                required["source:" + PurePosixPath(node["path"].replace("\\", "/")).as_posix()] = node["sha256"]
            for key, value in node.items():
                if not trail and key == "independent_semantic_review":
                    continue
                walk(value, trail + (str(key),))
        elif isinstance(node, list):
            for value in node:
                walk(value, trail)
        elif isinstance(node, str):
            # Evidence references are already stable authority identifiers.
            if ":" in node and trail and trail[-1] in {"evidence_refs", "source_refs", "migration_sources", "prior_map_nodes"}:
                required.setdefault(node, None)

    walk(head)
    walk(manifest)
    walk(map_control)
    if isinstance(map_control, dict):
        for collection, id_key, prefix in (
            ("milestones", "milestone_id", "milestone:"),
            ("results", "result_id", "result:"),
            ("routes", "route_id", "route:"),
        ):
            for item in map_control.get(collection, []) if isinstance(map_control.get(collection, []), list) else []:
                if isinstance(item, dict) and isinstance(item.get(id_key), str) and item[id_key].strip():
                    required[prefix + item[id_key]] = document_sha256(item)
    return required


def _check_inventory_bindings(entries: list[dict[str, str]], required: dict[str, str | None], path: str) -> None:
    by_id = {row["authority_id"]: row for row in entries}
    missing = sorted(set(required) - set(by_id))
    if missing:
        raise ReviewError("authority_inventory_incomplete", "Missing derived authority IDs: " + ", ".join(missing), path)
    stale = sorted(authority_id for authority_id, expected in required.items() if expected is not None and by_id[authority_id]["sha256"] != expected)
    if stale:
        raise ReviewError("authority_inventory_hash_mismatch", "Stale derived authority hashes: " + ", ".join(stale), path)


def _pointer_matches(head: dict[str, Any], key: str, path: str, digest: str) -> bool:
    pointer = head.get(key)
    return isinstance(pointer, dict) and pointer.get("path") == path and pointer.get("sha256") == digest


def _normalized_authority_head(head: Any) -> Any:
    if not isinstance(head, dict):
        raise ReviewError("authority_head_invalid", "Authority head must be an object", "authority_head")
    return {key: value for key, value in head.items() if key != "independent_semantic_review"}


def result_contract_sha256() -> str:
    return document_sha256({
        "schema": RESULT_SCHEMA,
        "fields": sorted(RESULT_FIELDS),
        "synthesis_roles": list(SYNTHESIS_ROLES),
        "verdicts": ["PASS", "FAIL", "INCONCLUSIVE"],
        "reviewer_mode": REVIEWER_MODE,
    })


def prepare_documents(
    project_root: Path,
    request: dict[str, Any],
    *,
    read_bytes: Callable[[str], bytes] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create a minimized packet and one immutable review ticket.

    ``request`` is host-local and is deliberately not a persisted schema.  Its
    closed field set prevents accidental whole-project disclosure.
    """
    fields = {
        "project_id", "project_objective_sha256", "author_principal", "reviewer_principal",
        "reviewer_mode", "dispatch_id", "cycle", "protocol_path", "map_control_path",
        "authority_head_path", "authority_manifest_path", "authority_inventory_path", "structural_receipt_path",
        "prior_result_path", "repair_summary", "retrieval_request_path",
    }
    _exact(request, fields, "request")
    root = Path(project_root)
    reader = read_bytes or _default_reader(root)
    cycle = request["cycle"]
    if not isinstance(cycle, int) or isinstance(cycle, bool) or not 1 <= cycle <= MAX_CYCLES:
        raise ReviewError("cycle_invalid", "cycle must be 1..3", "request.cycle")
    author = _string(request["author_principal"], "request.author_principal")
    reviewer = _string(request["reviewer_principal"], "request.reviewer_principal")
    if reviewer == author:
        raise ReviewError("reviewer_not_independent", "Reviewer principal must differ from author", "request.reviewer_principal")
    if request["reviewer_mode"] != REVIEWER_MODE:
        raise ReviewError("reviewer_mode_invalid", "Only fresh_subagent is permitted", "request.reviewer_mode")

    bindings = {
        "protocol_path": _relative(request["protocol_path"], "request.protocol_path"),
        "map_control_path": _relative(request["map_control_path"], "request.map_control_path"),
        "authority_head_path": _relative(request["authority_head_path"], "request.authority_head_path"),
        "authority_manifest_path": _relative(request["authority_manifest_path"], "request.authority_manifest_path"),
        "authority_inventory_path": _relative(request["authority_inventory_path"], "request.authority_inventory_path"),
        "structural_receipt_path": _relative(request["structural_receipt_path"], "request.structural_receipt_path"),
    }
    protocol_raw = reader(bindings["protocol_path"])
    map_raw = reader(bindings["map_control_path"])
    map_control = load_json_bytes(map_raw)
    if not isinstance(map_control, dict):
        raise ReviewError("map_control_invalid", "Map control must be an object", bindings["map_control_path"])
    project_id = _string(request["project_id"], "request.project_id")
    objective_sha = _hash(request["project_objective_sha256"], "request.project_objective_sha256")
    if map_control.get("project_id") != project_id or map_control.get("project_objective_sha256") != objective_sha:
        raise ReviewError("map_project_binding_mismatch", "Map control does not bind the requested project/objective", bindings["map_control_path"])
    head_raw = reader(bindings["authority_head_path"])
    head = load_json_bytes(head_raw)
    review_head = _normalized_authority_head(head)
    manifest_raw = reader(bindings["authority_manifest_path"])
    manifest = load_json_bytes(manifest_raw)
    inventory_raw = reader(bindings["authority_inventory_path"])
    inventory_value = load_json_bytes(inventory_raw)
    entries = _authority_entries(inventory_value)
    structural_raw = reader(bindings["structural_receipt_path"])
    structural = load_json_bytes(structural_raw)
    if not isinstance(structural, dict) or structural.get("ok") is not True or structural.get("activation_eligible") is not True:
        raise ReviewError("structural_validation_not_pass", "Structural validation must be activation-eligible", bindings["structural_receipt_path"])
    map_semantic_sha = document_sha256(map_control)
    if structural.get("control_sha256") != map_semantic_sha:
        raise ReviewError("structural_map_binding_mismatch", "Structural receipt is stale for the candidate map", bindings["structural_receipt_path"])
    if not _pointer_matches(head, "candidate_manifest", bindings["authority_manifest_path"], sha256(manifest_raw)):
        raise ReviewError("authority_manifest_pointer_mismatch", "Authority head does not bind the selected manifest", bindings["authority_head_path"])
    if not _pointer_matches(head, "research_map", bindings["map_control_path"], sha256(map_raw)):
        raise ReviewError("authority_map_pointer_mismatch", "Authority head does not bind the selected map", bindings["authority_head_path"])
    if not _pointer_matches(head, "map_validation_receipt", bindings["structural_receipt_path"], sha256(structural_raw)):
        raise ReviewError("authority_structural_pointer_mismatch", "Authority head does not bind the structural receipt", bindings["authority_head_path"])
    required_bindings = _required_authority_bindings(
        review_head,
        manifest,
        map_control,
        head_sha256=document_sha256(review_head),
        manifest_sha256=sha256(manifest_raw),
    )
    _check_inventory_bindings(entries, required_bindings, bindings["authority_inventory_path"])
    rows, documents = _visible_rows(root, reader, bindings["map_control_path"])

    retrieval_request_sha: str | None = None
    evidence_slices: list[dict[str, str]] = []
    retrieval_path = request["retrieval_request_path"]
    if retrieval_path is not None:
        retrieval_rel = _relative(retrieval_path, "request.retrieval_request_path")
        retrieval_raw = reader(retrieval_rel)
        retrieval = load_json_bytes(retrieval_raw)
        if not isinstance(retrieval, dict) or set(retrieval) != {"request_id", "ticket_scope", "slices"}:
            raise ReviewError("retrieval_request_invalid", "Retrieval request has a closed three-field shape", retrieval_rel)
        if retrieval["ticket_scope"] != request["dispatch_id"] or not isinstance(retrieval["slices"], list):
            raise ReviewError("retrieval_ticket_mismatch", "Retrieval request must bind this dispatch", retrieval_rel)
        for index, item in enumerate(retrieval["slices"]):
            ipath = f"retrieval.slices[{index}]"
            if not isinstance(item, dict) or set(item) != {"slice_id", "source_category", "content"}:
                raise ReviewError("retrieval_slice_invalid", "Retrieval slices are closed", ipath)
            category = _string(item["source_category"], ipath + ".source_category")
            if category.casefold() in FORBIDDEN_COMPONENTS or category in EXCLUDED_EVIDENCE_CATEGORIES:
                raise ReviewError("raw_evidence_disclosure_forbidden", "Raw/import/recovery/log content cannot be sent", ipath)
            content = _string(item["content"], ipath + ".content")
            evidence_slices.append({
                "slice_id": _string(item["slice_id"], ipath + ".slice_id"),
                "source_category": category,
                "sha256": sha256(content.encode("utf-8")),
                "content": content,
            })
        retrieval_request_sha = sha256(retrieval_raw)

    packet = {
        "schema": PACKET_SCHEMA,
        "protocol": {"path": bindings["protocol_path"], "sha256": sha256(protocol_raw), "content": protocol_raw.decode("utf-8", errors="strict")},
        "project": {"project_id": project_id, "project_objective_sha256": objective_sha},
        "candidate": {
            "map_control_path": bindings["map_control_path"],
            "map_control_sha256": sha256(map_raw),
            "map_control_semantic_sha256": map_semantic_sha,
            "map_control": map_control,
            "visible_tree_inventory_sha256": _inventory_hash(rows),
            "visible_tree_inventory": rows,
            "visible_documents": documents,
        },
        "authority": {
            "head_path": bindings["authority_head_path"],
            "head_sha256": document_sha256(review_head),
            "head": review_head,
            "manifest_path": bindings["authority_manifest_path"],
            "manifest_sha256": sha256(manifest_raw),
            "manifest": manifest,
            "inventory_path": bindings["authority_inventory_path"],
            "inventory_sha256": sha256(inventory_raw),
            "entries": entries,
        },
        "structural_validation": {
            "path": bindings["structural_receipt_path"],
            "sha256": sha256(structural_raw),
            "receipt": structural,
        },
        "evidence_boundary": {
            "classification": "minimized-remote",
            "allowed_categories": list(ALLOWED_EVIDENCE_CATEGORIES),
            "excluded_categories": list(EXCLUDED_EVIDENCE_CATEGORIES),
            "retrieval_request_sha256": retrieval_request_sha,
            "evidence_slices": evidence_slices,
        },
    }
    packet_sha = document_sha256(packet)

    prior_sha: str | None = None
    repair_lineage: dict[str, Any] | None = None
    if cycle == 1:
        if request["prior_result_path"] is not None or request["repair_summary"] is not None:
            raise ReviewError("unexpected_repair_lineage", "Cycle one cannot have repair lineage", "request")
    else:
        prior_rel = _relative(request["prior_result_path"], "request.prior_result_path")
        prior_raw = reader(prior_rel)
        prior = load_json_bytes(prior_raw)
        if not isinstance(prior, dict) or prior.get("schema") != RESULT_SCHEMA or prior.get("cycle") != cycle - 1:
            raise ReviewError("prior_result_invalid", "Cycle must bind the immediately preceding result", prior_rel)
        if prior.get("verdict") == "PASS":
            raise ReviewError("pass_cannot_be_repaired", "A PASS result cannot start a repair cycle", prior_rel)
        candidate_unchanged = prior.get("candidate_map_sha256") == sha256(map_raw)
        if prior.get("verdict") == "FAIL" and candidate_unchanged:
            raise ReviewError("candidate_not_changed_after_failure", "A failed candidate must change bytes before review resumes", bindings["map_control_path"])
        if prior.get("verdict") == "INCONCLUSIVE" and candidate_unchanged and (retrieval_request_sha is None or not evidence_slices):
            raise ReviewError(
                "inconclusive_without_new_evidence",
                "An unchanged inconclusive candidate requires a new retrieval request with bounded evidence slices",
                "request.retrieval_request_path",
            )
        summary = _string(request["repair_summary"], "request.repair_summary")
        prior_sha = document_sha256(prior)
        findings_sha = document_sha256({"repairs": prior.get("repairs"), "unresolved": prior.get("unresolved")})
        repair_lineage = {
            "prior_result_path": prior_rel,
            "prior_result_sha256": prior_sha,
            "from_candidate_map_sha256": prior.get("candidate_map_sha256"),
            "to_candidate_map_sha256": sha256(map_raw),
            "findings_sha256": findings_sha,
            "repair_summary": summary,
        }

    ticket = {
        "schema": TICKET_SCHEMA,
        "ticket_id": "pending",
        "packet_sha256": packet_sha,
        "protocol_sha256": packet["protocol"]["sha256"],
        "project_id": project_id,
        "candidate_map_sha256": packet["candidate"]["map_control_sha256"],
        "visible_tree_inventory_sha256": packet["candidate"]["visible_tree_inventory_sha256"],
        "authority_manifest_sha256": packet["authority"]["manifest_sha256"],
        "authority_inventory_sha256": packet["authority"]["inventory_sha256"],
        "structural_receipt_sha256": packet["structural_validation"]["sha256"],
        "author_principal": author,
        "reviewer_principal": reviewer,
        "reviewer_mode": REVIEWER_MODE,
        "dispatch_id": _string(request["dispatch_id"], "request.dispatch_id"),
        "cycle": cycle,
        "max_cycles": MAX_CYCLES,
        "prior_result_sha256": prior_sha,
        "repair_lineage": repair_lineage,
        "result_contract_sha256": result_contract_sha256(),
        "retrieval_request_sha256": retrieval_request_sha,
    }
    ticket["ticket_id"] = ticket_id_for(ticket)
    return packet, ticket


def validate_packet_document(packet: Any) -> None:
    packet = _exact(packet, PACKET_FIELDS, "packet")
    if packet["schema"] != PACKET_SCHEMA:
        raise ReviewError("packet_schema_invalid", "Unexpected packet schema", "packet.schema")
    _exact(packet["protocol"], {"path", "sha256", "content"}, "packet.protocol")
    _relative(packet["protocol"]["path"], "packet.protocol.path")
    if sha256(_string(packet["protocol"]["content"], "packet.protocol.content").encode("utf-8")) != _hash(packet["protocol"]["sha256"], "packet.protocol.sha256"):
        raise ReviewError("protocol_hash_mismatch", "Protocol content hash mismatch", "packet.protocol")
    _exact(packet["project"], {"project_id", "project_objective_sha256"}, "packet.project")
    _string(packet["project"]["project_id"], "packet.project.project_id")
    _hash(packet["project"]["project_objective_sha256"], "packet.project.project_objective_sha256")
    candidate = _exact(packet["candidate"], {"map_control_path", "map_control_sha256", "map_control_semantic_sha256", "map_control", "visible_tree_inventory_sha256", "visible_tree_inventory", "visible_documents"}, "packet.candidate")
    _relative(candidate["map_control_path"], "packet.candidate.map_control_path")
    _hash(candidate["map_control_sha256"], "packet.candidate.map_control_sha256")
    if document_sha256(candidate["map_control"]) != _hash(candidate["map_control_semantic_sha256"], "packet.candidate.map_control_semantic_sha256"):
        raise ReviewError("map_semantic_hash_mismatch", "Map object hash mismatch", "packet.candidate.map_control")
    rows = candidate["visible_tree_inventory"]
    if not isinstance(rows, list) or _inventory_hash(rows) != _hash(candidate["visible_tree_inventory_sha256"], "packet.candidate.visible_tree_inventory_sha256"):
        raise ReviewError("visible_inventory_hash_mismatch", "Visible inventory hash mismatch", "packet.candidate.visible_tree_inventory")
    documents = candidate["visible_documents"]
    if not isinstance(documents, list):
        raise ReviewError("visible_documents_invalid", "Visible documents must be a list", "packet.candidate.visible_documents")
    row_by_path = {row.get("path"): row for row in rows if isinstance(row, dict)}
    for index, doc in enumerate(documents):
        path = f"packet.candidate.visible_documents[{index}]"
        _exact(doc, {"path", "sha256", "content"}, path)
        rel = _relative(doc["path"], path + ".path")
        raw = _string(doc["content"], path + ".content").encode("utf-8")
        if sha256(raw) != _hash(doc["sha256"], path + ".sha256") or row_by_path.get(rel, {}).get("sha256") != doc["sha256"]:
            raise ReviewError("visible_document_hash_mismatch", "Visible document is not inventory-bound", path)
    authority = _exact(packet["authority"], {"head_path", "head_sha256", "head", "manifest_path", "manifest_sha256", "manifest", "inventory_path", "inventory_sha256", "entries"}, "packet.authority")
    _relative(authority["head_path"], "packet.authority.head_path")
    _hash(authority["head_sha256"], "packet.authority.head_sha256")
    _relative(authority["manifest_path"], "packet.authority.manifest_path")
    _relative(authority["inventory_path"], "packet.authority.inventory_path")
    _hash(authority["manifest_sha256"], "packet.authority.manifest_sha256")
    _hash(authority["inventory_sha256"], "packet.authority.inventory_sha256")
    entries = _authority_entries(authority["entries"])
    if entries != authority["entries"]:
        raise ReviewError("authority_entries_not_canonical", "Authority entries must be sorted and minimized", "packet.authority.entries")
    if document_sha256(authority["head"]) != authority["head_sha256"]:
        raise ReviewError("authority_head_hash_mismatch", "Normalized authority head hash mismatch", "packet.authority.head")
    required_bindings = _required_authority_bindings(
        authority["head"], authority["manifest"], candidate["map_control"],
        head_sha256=authority["head_sha256"], manifest_sha256=authority["manifest_sha256"],
    )
    _check_inventory_bindings(entries, required_bindings, "packet.authority.entries")
    structural = _exact(packet["structural_validation"], {"path", "sha256", "receipt"}, "packet.structural_validation")
    _relative(structural["path"], "packet.structural_validation.path")
    _hash(structural["sha256"], "packet.structural_validation.sha256")
    if not isinstance(structural["receipt"], dict) or structural["receipt"].get("ok") is not True:
        raise ReviewError("structural_validation_not_pass", "Structural receipt must pass", "packet.structural_validation.receipt")
    boundary = _exact(packet["evidence_boundary"], {"classification", "allowed_categories", "excluded_categories", "retrieval_request_sha256", "evidence_slices"}, "packet.evidence_boundary")
    if boundary["classification"] != "minimized-remote" or boundary["allowed_categories"] != list(ALLOWED_EVIDENCE_CATEGORIES) or boundary["excluded_categories"] != list(EXCLUDED_EVIDENCE_CATEGORIES):
        raise ReviewError("evidence_boundary_invalid", "The minimized-remote boundary is immutable", "packet.evidence_boundary")
    if boundary["retrieval_request_sha256"] is not None:
        _hash(boundary["retrieval_request_sha256"], "packet.evidence_boundary.retrieval_request_sha256")
    if not isinstance(boundary["evidence_slices"], list):
        raise ReviewError("evidence_slices_invalid", "Evidence slices must be a list", "packet.evidence_boundary.evidence_slices")
    if boundary["retrieval_request_sha256"] is None and boundary["evidence_slices"]:
        raise ReviewError("unbound_evidence_slices", "Evidence slices require a retrieval-request binding", "packet.evidence_boundary")
    if boundary["retrieval_request_sha256"] is not None and not boundary["evidence_slices"]:
        raise ReviewError("empty_retrieval_response", "A retrieval request must provide at least one bounded evidence slice", "packet.evidence_boundary")
    for index, item in enumerate(boundary["evidence_slices"]):
        path = f"packet.evidence_boundary.evidence_slices[{index}]"
        item = _exact(item, {"slice_id", "source_category", "sha256", "content"}, path)
        _string(item["slice_id"], path + ".slice_id")
        category = _string(item["source_category"], path + ".source_category")
        if category.casefold() in FORBIDDEN_COMPONENTS or category in EXCLUDED_EVIDENCE_CATEGORIES:
            raise ReviewError("raw_evidence_disclosure_forbidden", "Raw/import/recovery/log content cannot be sent", path + ".source_category")
        content = _string(item["content"], path + ".content")
        if sha256(content.encode("utf-8")) != _hash(item["sha256"], path + ".sha256"):
            raise ReviewError("evidence_slice_hash_mismatch", "Evidence slice content does not match its hash", path)
    serialized = json.dumps(packet, ensure_ascii=False).casefold()
    for token in ('"raw-objects"', '"imports"', '"recovery-tree"', '"logs"'):
        # The immutable excluded_categories declaration is the one allowed occurrence.
        if serialized.count(token) > 1:
            raise ReviewError("forbidden_evidence_disclosure", "Forbidden evidence category appears outside the boundary declaration", "packet")


def validate_ticket_document(packet: dict[str, Any], ticket: Any) -> None:
    validate_packet_document(packet)
    ticket = _exact(ticket, TICKET_FIELDS, "ticket")
    if ticket["schema"] != TICKET_SCHEMA:
        raise ReviewError("ticket_schema_invalid", "Unexpected ticket schema", "ticket.schema")
    if ticket["ticket_id"] != ticket_id_for(ticket):
        raise ReviewError("ticket_id_binding_mismatch", "Ticket ID must bind every closed ticket field", "ticket.ticket_id")
    bindings = {
        "packet_sha256": document_sha256(packet),
        "protocol_sha256": packet["protocol"]["sha256"],
        "project_id": packet["project"]["project_id"],
        "candidate_map_sha256": packet["candidate"]["map_control_sha256"],
        "visible_tree_inventory_sha256": packet["candidate"]["visible_tree_inventory_sha256"],
        "authority_manifest_sha256": packet["authority"]["manifest_sha256"],
        "authority_inventory_sha256": packet["authority"]["inventory_sha256"],
        "structural_receipt_sha256": packet["structural_validation"]["sha256"],
        "retrieval_request_sha256": packet["evidence_boundary"]["retrieval_request_sha256"],
    }
    for key, expected in bindings.items():
        if ticket[key] != expected:
            raise ReviewError("ticket_binding_mismatch", f"Ticket does not bind packet field {key}", "ticket." + key)
    if ticket["reviewer_mode"] != REVIEWER_MODE or ticket["max_cycles"] != MAX_CYCLES:
        raise ReviewError("ticket_review_mode_invalid", "Fresh subagent and three-cycle cap are mandatory", "ticket")
    if ticket["author_principal"] == ticket["reviewer_principal"]:
        raise ReviewError("reviewer_not_independent", "Reviewer principal must differ from author", "ticket.reviewer_principal")
    if not isinstance(ticket["cycle"], int) or isinstance(ticket["cycle"], bool) or not 1 <= ticket["cycle"] <= MAX_CYCLES:
        raise ReviewError("cycle_invalid", "cycle must be 1..3", "ticket.cycle")
    _string(ticket["dispatch_id"], "ticket.dispatch_id")
    if ticket["result_contract_sha256"] != result_contract_sha256():
        raise ReviewError("result_contract_mismatch", "Reviewer output boundary is stale", "ticket.result_contract_sha256")
    if ticket["cycle"] == 1:
        if ticket["prior_result_sha256"] is not None or ticket["repair_lineage"] is not None:
            raise ReviewError("unexpected_repair_lineage", "Cycle one cannot have repair lineage", "ticket")
    else:
        _hash(ticket["prior_result_sha256"], "ticket.prior_result_sha256")
        lineage = _exact(ticket["repair_lineage"], {"prior_result_path", "prior_result_sha256", "from_candidate_map_sha256", "to_candidate_map_sha256", "findings_sha256", "repair_summary"}, "ticket.repair_lineage")
        if lineage["prior_result_sha256"] != ticket["prior_result_sha256"] or lineage["to_candidate_map_sha256"] != ticket["candidate_map_sha256"]:
            raise ReviewError("repair_lineage_invalid", "Repair lineage does not bind the prior result and current candidate", "ticket.repair_lineage")
        _relative(lineage["prior_result_path"], "ticket.repair_lineage.prior_result_path")
        _hash(lineage["findings_sha256"], "ticket.repair_lineage.findings_sha256")
        _string(lineage["repair_summary"], "ticket.repair_lineage.repair_summary")


def validate_result_document(packet: dict[str, Any], ticket: dict[str, Any], result: Any) -> dict[str, Any]:
    validate_ticket_document(packet, ticket)
    result = _exact(result, RESULT_FIELDS, "result")
    if result["schema"] != RESULT_SCHEMA:
        raise ReviewError("result_schema_invalid", "Unexpected result schema", "result.schema")
    for key in (
        "ticket_id", "packet_sha256", "protocol_sha256", "project_id", "candidate_map_sha256",
        "visible_tree_inventory_sha256", "authority_manifest_sha256", "authority_inventory_sha256",
        "structural_receipt_sha256", "reviewer_principal", "reviewer_mode", "dispatch_id", "cycle",
    ):
        if result[key] != ticket[key]:
            raise ReviewError("result_ticket_binding_mismatch", f"Result does not bind {key}", "result." + key)
    if result["reviewer_mode"] != REVIEWER_MODE:
        raise ReviewError("reviewer_mode_invalid", "Only fresh_subagent results are accepted", "result.reviewer_mode")
    coverage = result["authority_coverage"]
    if not isinstance(coverage, list):
        raise ReviewError("authority_coverage_invalid", "Authority coverage must be a list", "result.authority_coverage")
    expected_ids = [row["authority_id"] for row in packet["authority"]["entries"]]
    seen: list[str] = []
    for index, item in enumerate(coverage):
        path = f"result.authority_coverage[{index}]"
        _exact(item, {"authority_id", "verdict", "rationale"}, path)
        seen.append(_string(item["authority_id"], path + ".authority_id"))
        if item["verdict"] not in ("PASS", "FAIL", "INCONCLUSIVE"):
            raise ReviewError("coverage_verdict_invalid", "Unknown coverage verdict", path + ".verdict")
        _string(item["rationale"], path + ".rationale")
    if sorted(seen) != sorted(expected_ids) or len(seen) != len(set(seen)):
        raise ReviewError("authority_coverage_incomplete", "Every authority must be covered exactly once", "result.authority_coverage")
    checks = result["synthesis_checks"]
    if not isinstance(checks, list):
        raise ReviewError("synthesis_checks_invalid", "Synthesis checks must be a list", "result.synthesis_checks")
    roles: list[str] = []
    for index, item in enumerate(checks):
        path = f"result.synthesis_checks[{index}]"
        _exact(item, {"role", "verdict", "rationale"}, path)
        roles.append(_string(item["role"], path + ".role"))
        if item["verdict"] not in ("PASS", "FAIL", "INCONCLUSIVE"):
            raise ReviewError("synthesis_verdict_invalid", "Unknown synthesis verdict", path + ".verdict")
        _string(item["rationale"], path + ".rationale")
    if sorted(roles) != sorted(SYNTHESIS_ROLES) or len(roles) != len(set(roles)):
        raise ReviewError("synthesis_checks_incomplete", "All eight synthesis roles are required exactly once", "result.synthesis_checks")
    boundary = _exact(result["evidence_boundary"], {"classification", "categories_seen", "retrieval_requests"}, "result.evidence_boundary")
    if boundary["classification"] != "minimized-remote" or not isinstance(boundary["categories_seen"], list) or not isinstance(boundary["retrieval_requests"], list):
        raise ReviewError("result_evidence_boundary_invalid", "Result must attest the minimized boundary", "result.evidence_boundary")
    if not set(boundary["categories_seen"]) <= set(ALLOWED_EVIDENCE_CATEGORIES):
        raise ReviewError("forbidden_evidence_seen", "Reviewer reports forbidden evidence", "result.evidence_boundary.categories_seen")
    verdict = result["verdict"]
    if verdict not in ("PASS", "FAIL", "INCONCLUSIVE"):
        raise ReviewError("verdict_invalid", "Unknown result verdict", "result.verdict")
    if not isinstance(result["repairs"], list) or not all(isinstance(item, str) and item.strip() for item in result["repairs"]):
        raise ReviewError("repairs_invalid", "repairs must be a string list", "result.repairs")
    if not isinstance(result["unresolved"], list) or not all(isinstance(item, str) and item.strip() for item in result["unresolved"]):
        raise ReviewError("unresolved_invalid", "unresolved must be a string list", "result.unresolved")
    all_component_verdicts = [item["verdict"] for item in coverage + checks]
    if verdict == "PASS":
        if result["repairs"] or result["unresolved"] or any(item != "PASS" for item in all_component_verdicts):
            raise ReviewError("pass_has_open_findings", "PASS requires all checks PASS and no repairs/unresolved", "result")
    elif verdict == "FAIL":
        if not result["repairs"] or "FAIL" not in all_component_verdicts:
            raise ReviewError("fail_without_findings", "FAIL requires a failed check and repair findings", "result")
    else:
        if not result["unresolved"] or "INCONCLUSIVE" not in all_component_verdicts:
            raise ReviewError("inconclusive_without_open_question", "INCONCLUSIVE requires unresolved questions", "result")
    return result


def finalize_documents(round_documents: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]) -> dict[str, Any]:
    if not 1 <= len(round_documents) <= MAX_CYCLES:
        raise ReviewError("round_count_invalid", "A closure contains one to three rounds", "rounds")
    rounds: list[dict[str, Any]] = []
    lineages: list[dict[str, Any]] = []
    reviewers: set[str] = set()
    author: str | None = None
    project_id: str | None = None
    objective_sha: str | None = None
    protocol_sha: str | None = None
    bindings: dict[str, str] | None = None
    previous_result: dict[str, Any] | None = None
    previous_result_sha: str | None = None
    for expected_cycle, (packet, ticket, result) in enumerate(round_documents, start=1):
        validated = validate_result_document(packet, ticket, result)
        if ticket["cycle"] != expected_cycle:
            raise ReviewError("round_cycle_gap", "Rounds must be consecutive from cycle one", f"rounds[{expected_cycle - 1}]")
        if author is None:
            author = ticket["author_principal"]
            project_id = ticket["project_id"]
            objective_sha = packet["project"]["project_objective_sha256"]
            protocol_sha = ticket["protocol_sha256"]
            bindings = {
                "protocol_path": packet["protocol"]["path"],
                "map_control_path": packet["candidate"]["map_control_path"],
                "authority_head_path": packet["authority"]["head_path"],
                "authority_manifest_path": packet["authority"]["manifest_path"],
                "authority_inventory_path": packet["authority"]["inventory_path"],
                "structural_receipt_path": packet["structural_validation"]["path"],
            }
        elif ticket["author_principal"] != author or ticket["project_id"] != project_id or packet["project"]["project_objective_sha256"] != objective_sha or ticket["protocol_sha256"] != protocol_sha:
            raise ReviewError("round_campaign_binding_mismatch", "All rounds must bind one author/project/objective/protocol", f"rounds[{expected_cycle - 1}]")
        reviewer = ticket["reviewer_principal"]
        if reviewer in reviewers:
            raise ReviewError("reviewer_reused", "Every cycle requires a new reviewer principal", f"rounds[{expected_cycle - 1}].reviewer_principal")
        reviewers.add(reviewer)
        if previous_result is not None:
            if previous_result["verdict"] == "PASS":
                raise ReviewError("round_after_pass", "No round may follow PASS", f"rounds[{expected_cycle - 1}]")
            if ticket["prior_result_sha256"] != previous_result_sha:
                raise ReviewError("prior_result_binding_mismatch", "Ticket does not bind the prior exact result", f"rounds[{expected_cycle - 1}]")
            expected_findings = document_sha256({"repairs": previous_result["repairs"], "unresolved": previous_result["unresolved"]})
            lineage = ticket["repair_lineage"]
            if lineage["findings_sha256"] != expected_findings or lineage["from_candidate_map_sha256"] != previous_result["candidate_map_sha256"]:
                raise ReviewError("repair_findings_binding_mismatch", "Repair lineage does not bind immutable findings", f"rounds[{expected_cycle - 1}]")
            candidate_unchanged = lineage["from_candidate_map_sha256"] == lineage["to_candidate_map_sha256"]
            if previous_result["verdict"] == "FAIL" and candidate_unchanged:
                raise ReviewError("failed_candidate_not_changed", "A FAIL must be followed by a changed candidate", f"rounds[{expected_cycle - 1}]")
            if previous_result["verdict"] == "INCONCLUSIVE" and candidate_unchanged:
                if ticket["retrieval_request_sha256"] is None or not packet["evidence_boundary"]["evidence_slices"]:
                    raise ReviewError("inconclusive_without_new_evidence", "An unchanged inconclusive candidate requires bounded new evidence", f"rounds[{expected_cycle - 1}]")
            lineages.append(lineage)
        rounds.append({
            "cycle": expected_cycle,
            "packet_sha256": document_sha256(packet),
            "ticket_sha256": document_sha256(ticket),
            "result_sha256": document_sha256(validated),
            "candidate_map_sha256": validated["candidate_map_sha256"],
            "visible_tree_inventory_sha256": validated["visible_tree_inventory_sha256"],
            "authority_manifest_sha256": validated["authority_manifest_sha256"],
            "authority_inventory_sha256": validated["authority_inventory_sha256"],
            "structural_receipt_sha256": validated["structural_receipt_sha256"],
            "reviewer_principal": reviewer,
            "reviewer_mode": validated["reviewer_mode"],
            "dispatch_id": validated["dispatch_id"],
            "verdict": validated["verdict"],
            "authority_coverage_count": len(validated["authority_coverage"]),
            "synthesis_check_count": len(validated["synthesis_checks"]),
            "repair_count": len(validated["repairs"]),
            "unresolved_count": len(validated["unresolved"]),
            "packet": packet,
            "ticket": ticket,
            "result": validated,
        })
        previous_result = validated
        previous_result_sha = document_sha256(validated)
    if previous_result is None or previous_result["verdict"] != "PASS":
        code = "review_cycle_limit_reached" if len(rounds) == MAX_CYCLES else "final_pass_missing"
        raise ReviewError(code, "Only a final exact-candidate PASS can form a closure", "rounds")
    final = rounds[-1]
    return {
        "schema": CLOSURE_SCHEMA,
        "protocol_sha256": protocol_sha,
        "project_id": project_id,
        "project_objective_sha256": objective_sha,
        "author_principal": author,
        "bindings": bindings,
        "rounds": rounds,
        "repair_lineage": lineages,
        "final_pass": {
            "cycle": final["cycle"],
            "packet_sha256": final["packet_sha256"],
            "ticket_sha256": final["ticket_sha256"],
            "result_sha256": final["result_sha256"],
            "candidate_map_sha256": final["candidate_map_sha256"],
            "visible_tree_inventory_sha256": final["visible_tree_inventory_sha256"],
            "authority_manifest_sha256": final["authority_manifest_sha256"],
            "authority_inventory_sha256": final["authority_inventory_sha256"],
            "structural_receipt_sha256": final["structural_receipt_sha256"],
            "reviewer_principal": final["reviewer_principal"],
        },
        "status": "PASS",
    }


def validate_closure_document(
    project_root: Path,
    closure: dict[str, Any],
    *,
    read_bytes: Callable[[str], bytes] | None = None,
    expected_closure_path: str | None = None,
) -> dict[str, Any]:
    """Recompute a closure against a live tree or a staged-overlay reader."""
    issues: list[dict[str, str]] = []

    def issue(code: str, path: str, detail: str = "") -> None:
        row = {"code": code, "path": path}
        if detail:
            row["detail"] = detail
        issues.append(row)

    try:
        closure = _exact(closure, CLOSURE_FIELDS, "closure")
        if closure["schema"] != CLOSURE_SCHEMA or closure["status"] != "PASS":
            raise ReviewError("closure_schema_or_status_invalid", "Closure must be v1 PASS", "closure")
        _hash(closure["protocol_sha256"], "closure.protocol_sha256")
        _hash(closure["project_objective_sha256"], "closure.project_objective_sha256")
        _string(closure["project_id"], "closure.project_id")
        _string(closure["author_principal"], "closure.author_principal")
        bindings = _exact(closure["bindings"], {"protocol_path", "map_control_path", "authority_head_path", "authority_manifest_path", "authority_inventory_path", "structural_receipt_path"}, "closure.bindings")
        for key, value in bindings.items():
            _relative(value, "closure.bindings." + key)
        if expected_closure_path is not None:
            _relative(expected_closure_path, "expected_closure_path")
        rounds = closure["rounds"]
        if not isinstance(rounds, list) or not 1 <= len(rounds) <= MAX_CYCLES:
            raise ReviewError("round_count_invalid", "Closure must contain one to three rounds", "closure.rounds")
        round_fields = {"cycle", "packet_sha256", "ticket_sha256", "result_sha256", "candidate_map_sha256", "visible_tree_inventory_sha256", "authority_manifest_sha256", "authority_inventory_sha256", "structural_receipt_sha256", "reviewer_principal", "reviewer_mode", "dispatch_id", "verdict", "authority_coverage_count", "synthesis_check_count", "repair_count", "unresolved_count", "packet", "ticket", "result"}
        reviewers: set[str] = set()
        for index, row in enumerate(rounds):
            _exact(row, round_fields, f"closure.rounds[{index}]")
            if row["cycle"] != index + 1 or row["reviewer_mode"] != REVIEWER_MODE or row["reviewer_principal"] == closure["author_principal"] or row["reviewer_principal"] in reviewers:
                raise ReviewError("closure_round_independence_invalid", "Cycles are ordered and use unique fresh reviewers", f"closure.rounds[{index}]")
            reviewers.add(row["reviewer_principal"])
            for key in ("packet_sha256", "ticket_sha256", "result_sha256", "candidate_map_sha256", "visible_tree_inventory_sha256", "authority_manifest_sha256", "authority_inventory_sha256", "structural_receipt_sha256"):
                _hash(row[key], f"closure.rounds[{index}].{key}")
            if row["synthesis_check_count"] != len(SYNTHESIS_ROLES) or not isinstance(row["authority_coverage_count"], int) or row["authority_coverage_count"] < 1:
                raise ReviewError("closure_round_coverage_invalid", "Round summary must attest full checks", f"closure.rounds[{index}]")
            validated_result = validate_result_document(row["packet"], row["ticket"], row["result"])
            if document_sha256(row["packet"]) != row["packet_sha256"] or document_sha256(row["ticket"]) != row["ticket_sha256"] or document_sha256(validated_result) != row["result_sha256"]:
                raise ReviewError("closure_round_artifact_hash_mismatch", "Embedded round artifacts do not match their hashes", f"closure.rounds[{index}]")
            for key in ("candidate_map_sha256", "visible_tree_inventory_sha256", "authority_manifest_sha256", "authority_inventory_sha256", "structural_receipt_sha256", "reviewer_principal", "reviewer_mode", "dispatch_id", "verdict"):
                if validated_result[key] != row[key]:
                    raise ReviewError("closure_round_summary_mismatch", "Round summary does not match embedded result", f"closure.rounds[{index}].{key}")
            if index < len(rounds) - 1 and row["verdict"] not in ("FAIL", "INCONCLUSIVE"):
                raise ReviewError("closure_intermediate_verdict_invalid", "Only failed/inconclusive rounds may precede another", f"closure.rounds[{index}].verdict")
        last = rounds[-1]
        if last["verdict"] != "PASS" or last["repair_count"] or last["unresolved_count"]:
            raise ReviewError("closure_final_pass_invalid", "Final round must be a clean PASS", "closure.rounds")
        lineages = closure["repair_lineage"]
        if not isinstance(lineages, list) or len(lineages) != len(rounds) - 1:
            raise ReviewError("closure_repair_lineage_count_invalid", "Each adjustment must have one lineage", "closure.repair_lineage")
        for index, lineage in enumerate(lineages):
            _exact(lineage, {"prior_result_path", "prior_result_sha256", "from_candidate_map_sha256", "to_candidate_map_sha256", "findings_sha256", "repair_summary"}, f"closure.repair_lineage[{index}]")
            if lineage["from_candidate_map_sha256"] != rounds[index]["candidate_map_sha256"] or lineage["to_candidate_map_sha256"] != rounds[index + 1]["candidate_map_sha256"]:
                raise ReviewError("closure_repair_lineage_invalid", "Lineage must connect adjacent candidates", f"closure.repair_lineage[{index}]")
            candidate_unchanged = lineage["from_candidate_map_sha256"] == lineage["to_candidate_map_sha256"]
            if rounds[index]["verdict"] == "FAIL" and candidate_unchanged:
                raise ReviewError("closure_failed_candidate_not_changed", "A FAIL lineage must change the candidate", f"closure.repair_lineage[{index}]")
            if rounds[index]["verdict"] == "INCONCLUSIVE" and candidate_unchanged:
                next_ticket = rounds[index + 1]["ticket"]
                next_packet = rounds[index + 1]["packet"]
                if next_ticket["retrieval_request_sha256"] is None or not next_packet["evidence_boundary"]["evidence_slices"]:
                    raise ReviewError("closure_inconclusive_without_new_evidence", "An unchanged inconclusive candidate requires bounded new evidence", f"closure.repair_lineage[{index}]")
        final = _exact(closure["final_pass"], {"cycle", "packet_sha256", "ticket_sha256", "result_sha256", "candidate_map_sha256", "visible_tree_inventory_sha256", "authority_manifest_sha256", "authority_inventory_sha256", "structural_receipt_sha256", "reviewer_principal"}, "closure.final_pass")
        for key in final:
            if key in last and final[key] != last[key]:
                raise ReviewError("closure_final_pass_binding_mismatch", "final_pass must repeat the exact last round", "closure.final_pass." + key)

        reader = read_bytes or _default_reader(Path(project_root))
        protocol_raw = reader(bindings["protocol_path"])
        map_raw = reader(bindings["map_control_path"])
        map_control = load_json_bytes(map_raw)
        head_raw = reader(bindings["authority_head_path"])
        head = load_json_bytes(head_raw)
        manifest_raw = reader(bindings["authority_manifest_path"])
        manifest = load_json_bytes(manifest_raw)
        inventory_raw = reader(bindings["authority_inventory_path"])
        structural_raw = reader(bindings["structural_receipt_path"])
        structural = load_json_bytes(structural_raw)
        current_rows, _ = _visible_rows(Path(project_root), reader, bindings["map_control_path"])
        current = {
            "protocol_sha256": sha256(protocol_raw),
            "candidate_map_sha256": sha256(map_raw),
            "visible_tree_inventory_sha256": _inventory_hash(current_rows),
            "authority_manifest_sha256": sha256(manifest_raw),
            "authority_inventory_sha256": sha256(inventory_raw),
            "structural_receipt_sha256": sha256(structural_raw),
        }
        if current["protocol_sha256"] != closure["protocol_sha256"]:
            issue("closure_protocol_stale", bindings["protocol_path"])
        for key in ("candidate_map_sha256", "visible_tree_inventory_sha256", "authority_manifest_sha256", "authority_inventory_sha256", "structural_receipt_sha256"):
            if current[key] != final[key]:
                issue("closure_binding_stale", key)
        if not isinstance(map_control, dict) or map_control.get("project_id") != closure["project_id"] or map_control.get("project_objective_sha256") != closure["project_objective_sha256"]:
            issue("closure_project_binding_mismatch", bindings["map_control_path"])
        if not isinstance(structural, dict) or structural.get("ok") is not True or structural.get("activation_eligible") is not True or structural.get("control_sha256") != document_sha256(map_control):
            issue("closure_structural_receipt_invalid", bindings["structural_receipt_path"])
        inventory_entries = _authority_entries(load_json_bytes(inventory_raw))
        normalized_head = _normalized_authority_head(head)
        if not _pointer_matches(head, "candidate_manifest", bindings["authority_manifest_path"], sha256(manifest_raw)):
            issue("closure_authority_manifest_pointer_mismatch", bindings["authority_head_path"])
        if not _pointer_matches(head, "research_map", bindings["map_control_path"], sha256(map_raw)):
            issue("closure_authority_map_pointer_mismatch", bindings["authority_head_path"])
        if not _pointer_matches(head, "map_validation_receipt", bindings["structural_receipt_path"], sha256(structural_raw)):
            issue("closure_authority_structural_pointer_mismatch", bindings["authority_head_path"])
        try:
            _check_inventory_bindings(
                inventory_entries,
                _required_authority_bindings(normalized_head, manifest, map_control, head_sha256=document_sha256(normalized_head), manifest_sha256=sha256(manifest_raw)),
                bindings["authority_inventory_path"],
            )
        except ReviewError as exc:
            issue(exc.code, exc.path, exc.message)
    except ReviewError as exc:
        issue(exc.code, exc.path, exc.message)
    except Exception as exc:  # fail closed at integration boundary
        issue("closure_validation_internal_error", "closure", f"{type(exc).__name__}: {exc}")
    return {
        "ok": not issues,
        "schema": VALIDATION_SCHEMA,
        "activation_eligible": not issues,
        "final_candidate_map_sha256": closure.get("final_pass", {}).get("candidate_map_sha256") if isinstance(closure, dict) else None,
        "final_cycle": closure.get("final_pass", {}).get("cycle") if isinstance(closure, dict) else None,
        "issues": issues,
    }


def build_test_closure(
    project_root: Path,
    *,
    author_principal: str = "fixture-author",
    reviewer_principal: str = "fixture-fresh-reviewer-1",
    dispatch_id: str = "fixture-dispatch-1",
    closure_path: str = ".research/map-review/closure.json",
) -> dict[str, Any]:
    """Build one honest PASS closure for local deterministic fixtures.

    This helper is deliberately unsuitable as a production review substitute:
    the principal names are fixture-only and the generated result states that
    it is a deterministic fixture.  Production callers must dispatch an actual
    fresh subagent and use ``prepare_documents``/``finalize_documents``.
    """
    root = Path(project_root).resolve(strict=True)
    project = load_json_bytes((root / "project.json").read_bytes())
    authority_ref = project["research_authority_head"]
    authority = load_json_bytes((root / authority_ref["path"]).read_bytes())
    map_path = authority["research_map"]["path"]
    manifest_path = authority["candidate_manifest"]["path"]
    receipt_path = authority["map_validation_receipt"]["path"]
    map_control = load_json_bytes((root / map_path).read_bytes())
    if map_control.get("project_id") != project.get("project_id"):
        raise ReviewError("fixture_map_project_id_missing", "Fixture map must bind project_id before closure construction", map_path)
    review_dir = root / ".research" / "map-review"
    review_dir.mkdir(parents=True, exist_ok=True)
    protocol_rel = ".research/map-review/protocol-v1.txt"
    inventory_rel = ".research/map-review/authority-inventory.json"
    packet_rel = ".research/map-review/packet-1.json"
    ticket_rel = ".research/map-review/ticket-1.json"
    result_rel = ".research/map-review/result-1.json"
    (root / protocol_rel).write_text("map_semantic_review/v1 fixture protocol\n", encoding="utf-8", newline="\n")
    manifest = load_json_bytes((root / manifest_path).read_bytes())
    structural = {
        "schema": "math-research-map-validation/v1",
        "ok": True,
        "activation_eligible": True,
        "control_sha256": document_sha256(map_control),
        "issues": [],
    }
    (root / receipt_path).write_bytes(canonical(structural))
    authority["candidate_manifest"] = {"path": manifest_path, "sha256": sha256((root / manifest_path).read_bytes())}
    authority["research_map"] = {"path": map_path, "sha256": sha256((root / map_path).read_bytes())}
    authority["map_validation_receipt"] = {"path": receipt_path, "sha256": sha256((root / receipt_path).read_bytes())}
    (root / authority_ref["path"]).write_bytes(canonical(authority))
    project["research_authority_head"] = {"path": authority_ref["path"], "sha256": sha256((root / authority_ref["path"]).read_bytes())}
    (root / "project.json").write_bytes(canonical(project))
    normalized_head = _normalized_authority_head(authority)
    required = _required_authority_bindings(
        normalized_head,
        manifest,
        map_control,
        head_sha256=document_sha256(normalized_head),
        manifest_sha256=sha256((root / manifest_path).read_bytes()),
    )
    inventory_entries = [{
        "authority_id": authority_id,
        "kind": authority_id.split(":", 1)[0],
        "sha256": expected or sha256(authority_id.encode("utf-8")),
        "summary": "Deterministic fixture authority summary for " + authority_id,
    } for authority_id, expected in sorted(required.items())]
    (root / inventory_rel).write_bytes(canonical({"entries": inventory_entries}))
    request = {
        "project_id": project["project_id"],
        "project_objective_sha256": project["objective_commitment_sha256"],
        "author_principal": author_principal,
        "reviewer_principal": reviewer_principal,
        "reviewer_mode": REVIEWER_MODE,
        "dispatch_id": dispatch_id,
        "cycle": 1,
        "protocol_path": protocol_rel,
        "map_control_path": map_path,
        "authority_head_path": authority_ref["path"],
        "authority_manifest_path": manifest_path,
        "authority_inventory_path": inventory_rel,
        "structural_receipt_path": receipt_path,
        "prior_result_path": None,
        "repair_summary": None,
        "retrieval_request_path": None,
    }
    packet, ticket = prepare_documents(root, request)
    rationale = "Deterministic fixture attestation; not promotion evidence."
    result = {
        "schema": RESULT_SCHEMA,
        "ticket_id": ticket["ticket_id"],
        "packet_sha256": ticket["packet_sha256"],
        "protocol_sha256": ticket["protocol_sha256"],
        "project_id": ticket["project_id"],
        "candidate_map_sha256": ticket["candidate_map_sha256"],
        "visible_tree_inventory_sha256": ticket["visible_tree_inventory_sha256"],
        "authority_manifest_sha256": ticket["authority_manifest_sha256"],
        "authority_inventory_sha256": ticket["authority_inventory_sha256"],
        "structural_receipt_sha256": ticket["structural_receipt_sha256"],
        "reviewer_principal": ticket["reviewer_principal"],
        "reviewer_mode": ticket["reviewer_mode"],
        "dispatch_id": ticket["dispatch_id"],
        "cycle": ticket["cycle"],
        "authority_coverage": [{"authority_id": row["authority_id"], "verdict": "PASS", "rationale": rationale} for row in packet["authority"]["entries"]],
        "synthesis_checks": [{"role": role, "verdict": "PASS", "rationale": rationale} for role in SYNTHESIS_ROLES],
        "evidence_boundary": {"classification": "minimized-remote", "categories_seen": ["research-map-control", "visible-map-note", "authority-inventory-summary", "structural-validation"], "retrieval_requests": []},
        "verdict": "PASS",
        "repairs": [],
        "unresolved": [],
    }
    closure = finalize_documents([(packet, ticket, result)])
    (root / packet_rel).write_bytes(canonical(packet))
    (root / ticket_rel).write_bytes(canonical(ticket))
    (root / result_rel).write_bytes(canonical(result))
    destination = root.joinpath(*PurePosixPath(_relative(closure_path, "closure_path")).parts)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(canonical(closure))
    authority["independent_semantic_review"] = {"path": closure_path, "sha256": sha256(destination.read_bytes())}
    (root / authority_ref["path"]).write_bytes(canonical(authority))
    project["research_authority_head"] = {"path": authority_ref["path"], "sha256": sha256((root / authority_ref["path"]).read_bytes())}
    (root / "project.json").write_bytes(canonical(project))
    return closure


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))


def _load(path: Path) -> Any:
    return load_json_bytes(path.read_bytes())


def _round_spec(text: str) -> tuple[Path, Path, Path]:
    parts = text.split("|")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("round must be PACKET|TICKET|RESULT")
    return Path(parts[0]), Path(parts[1]), Path(parts[2])


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--project-root", type=Path, required=True)
    prepare.add_argument("--request", type=Path, required=True)
    prepare.add_argument("--packet-out", type=Path, required=True)
    prepare.add_argument("--ticket-out", type=Path, required=True)
    check = sub.add_parser("validate-result")
    check.add_argument("--packet", type=Path, required=True)
    check.add_argument("--ticket", type=Path, required=True)
    check.add_argument("--result", type=Path, required=True)
    finalize = sub.add_parser("finalize")
    finalize.add_argument("--round", action="append", type=_round_spec, required=True)
    finalize.add_argument("--closure-out", type=Path, required=True)
    closure = sub.add_parser("validate-closure")
    closure.add_argument("--project-root", type=Path, required=True)
    closure.add_argument("--closure", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            packet, ticket = prepare_documents(args.project_root, _load(args.request))
            _write_json(args.packet_out, packet)
            _write_json(args.ticket_out, ticket)
            result = {"ok": True, "packet_sha256": document_sha256(packet), "ticket_sha256": document_sha256(ticket)}
        elif args.command == "validate-result":
            validated = validate_result_document(_load(args.packet), _load(args.ticket), _load(args.result))
            result = {"ok": True, "verdict": validated["verdict"], "result_sha256": document_sha256(validated)}
        elif args.command == "finalize":
            documents = [(_load(p), _load(t), _load(r)) for p, t, r in args.round]
            output = finalize_documents(documents)
            _write_json(args.closure_out, output)
            result = {"ok": True, "closure_sha256": document_sha256(output), "final_cycle": output["final_pass"]["cycle"]}
        else:
            result = validate_closure_document(args.project_root, _load(args.closure))
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result["ok"] else 2
    except ReviewError as exc:
        print(json.dumps({"ok": False, "error": {"code": exc.code, "message": exc.message, "path": exc.path}}, ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
