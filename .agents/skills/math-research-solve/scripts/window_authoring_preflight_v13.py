#!/usr/bin/env python3
"""Deterministic, non-authoritative preflight for v13 window authoring artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any


ORDINARY_MAX_BYTES = 512_000
CLOSURE_MAX_BYTES = 2_097_152
TREE_MAX_BYTES = 8_388_608
CLOSURE_SCHEMA = "math-research-map-review-closure/v1"
MANIFEST_SCHEMA = "local-v13-artifact-manifest/v1"
SHA256_HEX = set("0123456789abcdef")


class PreflightError(Exception):
    def __init__(self, code: str, message: str, recovery: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.recovery = recovery


def fail(code: str, message: str, recovery: str) -> None:
    raise PreflightError(code, message, recovery)


def require(condition: bool, code: str, message: str, recovery: str) -> None:
    if not condition:
        fail(code, message, recovery)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_document(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def canonical_file(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail("json_duplicate_key", "JSON contains a duplicate key", "Regenerate the artifact from one closed object.")
        result[key] = value
    return result


def read_json(path: Path, *, require_canonical_file: bool = False) -> tuple[Any, bytes]:
    require(path.is_file() and not path.is_symlink(), "file_invalid", "Input must be a regular non-symlink file", "Provide the frozen regular file.")
    raw = path.read_bytes()
    require(not raw.startswith(b"\xef\xbb\xbf"), "utf8_bom_forbidden", "UTF-8 BOM is forbidden", "Rewrite as UTF-8 without BOM.")
    require(b"\r" not in raw, "cr_forbidden", "CR bytes are forbidden", "Rewrite with LF line endings.")
    try:
        text = raw.decode("utf-8")
        value = json.loads(text, object_pairs_hook=_pairs_no_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail("json_invalid", f"Invalid UTF-8 JSON: {type(exc).__name__}", "Regenerate valid UTF-8 JSON.")
    if require_canonical_file:
        require(raw == canonical_file(value), "json_not_canonical", "JSON is not compact canonical file form", "Serialize the parsed key order with compact separators and one final LF.")
    return value, raw


def valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= SHA256_HEX


def digest_check(packet_path: Path, ticket_path: Path) -> dict[str, Any]:
    packet, packet_raw = read_json(packet_path)
    ticket, _ = read_json(ticket_path)
    require(isinstance(ticket, dict), "ticket_invalid", "Ticket must be a JSON object", "Regenerate the closed ticket.")
    bound = ticket.get("packet_sha256")
    require(valid_sha256(bound), "ticket_packet_digest_invalid", "ticket.packet_sha256 must be lowercase SHA-256", "Regenerate the ticket from the packet document.")
    document_digest = sha256(canonical_document(packet))
    raw_digest = sha256(packet_raw)
    require(bound == document_digest, "packet_document_digest_mismatch", "ticket.packet_sha256 does not match the canonical document digest", "Recompute the recursively key-sorted compact JSON plus final-LF document digest; do not substitute the raw-file digest.")
    return {
        "ok": True,
        "check": "review-packet-digests",
        "packet_document_sha256": document_digest,
        "packet_raw_sha256": raw_digest,
        "ticket_bound_sha256": bound,
        "raw_equals_document": raw_digest == document_digest,
    }


def _resolved(path: Path) -> Path:
    return path.resolve(strict=False)


def _inside(child: Path, parent: Path) -> bool:
    return child == parent or parent in child.parents


def output_scope_check(workspace_root: Path, project_root: Path, output_root: Path) -> dict[str, Any]:
    workspace = _resolved(workspace_root)
    project = _resolved(project_root)
    output = _resolved(output_root)
    require(workspace.is_dir(), "workspace_root_invalid", "Workspace root must exist", "Provide the authorized task workspace root.")
    require(project.is_dir(), "project_root_invalid", "Project root must exist", "Provide the live research project root.")
    require(output != workspace and _inside(output, workspace), "output_outside_workspace", "Output root must be a proper descendant of the task workspace", "Choose a task-local output directory.")
    require(not _inside(output, project), "output_inside_project", "Worker output must remain outside the live research project", "Choose a task-local workspace directory and ingest only through the Host.")
    require(not _inside(project, output), "output_contains_project", "Output root must not contain the live research project", "Choose a narrower task-local output directory.")
    return {"ok": True, "check": "output-scope", "workspace_bound": True, "project_excluded": True}


def _manifest(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    value, _ = read_json(path, require_canonical_file=True)
    require(isinstance(value, dict) and set(value) == {"schema", "writes"}, "manifest_shape_invalid", "Artifact manifest must have exactly schema and writes", "Regenerate the closed local-v13 manifest.")
    require(value["schema"] == MANIFEST_SCHEMA and isinstance(value["writes"], list), "manifest_schema_invalid", "Artifact manifest schema or writes is invalid", "Use local-v13-artifact-manifest/v1 with a writes array.")
    targets: set[str] = set()
    for row in value["writes"]:
        require(isinstance(row, dict) and set(row) == {"target", "source", "immutable", "expected_old_sha256"}, "manifest_row_invalid", "Each manifest row must use the closed four-field schema", "Regenerate the manifest row.")
        target = row["target"]
        require(isinstance(target, str) and target and target not in targets, "manifest_target_invalid", "Manifest targets must be unique nonempty strings", "Deduplicate the target inventory.")
        require(isinstance(row["source"], str) and row["source"], "manifest_source_invalid", "Manifest source must be nonempty", "Bind each target to one staged source.")
        require(isinstance(row["immutable"], bool), "manifest_immutable_invalid", "Manifest immutable must be boolean", "Regenerate the row.")
        require(row["expected_old_sha256"] is None or valid_sha256(row["expected_old_sha256"]), "manifest_expected_old_invalid", "expected_old_sha256 must be null or lowercase SHA-256", "Bind the exact old alias or use null only for a new target.")
        targets.add(target)
    return value, value["writes"]


def close_manifest_check(planning_path: Path, commit_path: Path) -> dict[str, Any]:
    _, planning = _manifest(planning_path)
    _, commit = _manifest(commit_path)
    require(planning, "planning_manifest_empty", "WINDOW_CLOSE planning manifest must contain changed Markdown aliases", "Include only Markdown bytes needed for candidate-project validation.")
    for row in planning:
        require(row["target"].casefold().endswith(".md"), "planning_manifest_control_alias", "WINDOW_CLOSE planning overlay may contain only Markdown aliases", "Keep map control, receipts, ledgers, and other aliases in the formal commit manifest.")
    commit_by_target = {row["target"]: row for row in commit}
    for row in planning:
        require(commit_by_target.get(row["target"]) == row, "planning_commit_manifest_mismatch", "Every planning write must appear byte-semantically unchanged in the formal commit manifest", "Regenerate both manifests from one frozen publication inventory.")
    require(any(not row["target"].casefold().endswith(".md") for row in commit), "commit_manifest_controls_missing", "Formal WINDOW_CLOSE manifest must retain non-Markdown publication aliases", "Add the map control, receipt, or asset aliases required by the publication contract.")
    return {
        "ok": True,
        "check": "window-close-manifests",
        "planning_write_count": len(planning),
        "commit_write_count": len(commit),
        "planning_is_strict_subset": len(planning) < len(commit),
    }


def tree_check(root: Path, ordinary_max: int, closure_max: int, tree_max: int) -> dict[str, Any]:
    require(root.is_dir() and not root.is_symlink(), "tree_root_invalid", "Audit root must be a regular directory", "Provide a fresh task-local authoring tree.")
    require(0 < ordinary_max <= closure_max <= tree_max, "size_budget_invalid", "Require 0 < ordinary <= closure <= tree byte budgets", "Use artifact-class-aware positive budgets.")
    total = 0
    files = 0
    closures = 0
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().casefold()):
        require(not path.is_symlink(), "tree_reparse_forbidden", "Symlink or reparse-like entry is forbidden", "Replace it with an ordinary file or directory.")
        if path.is_dir():
            continue
        require(path.is_file(), "tree_entry_invalid", "Tree contains a non-regular entry", "Remove the unsupported entry.")
        raw = path.read_bytes()
        total += len(raw)
        files += 1
        require(not raw.startswith(b"\xef\xbb\xbf"), "tree_bom_forbidden", "Tree file contains UTF-8 BOM", "Rewrite the file without BOM.")
        require(b"\r" not in raw, "tree_cr_forbidden", "Tree file contains CR bytes", "Rewrite the file with LF line endings or a text-safe encoded wrapper.")
        limit = ordinary_max
        if path.suffix.casefold() == ".json":
            value, _ = read_json(path, require_canonical_file=True)
            if isinstance(value, dict) and value.get("schema") == CLOSURE_SCHEMA:
                limit = closure_max
                closures += 1
        require(len(raw) <= limit, "artifact_size_exceeded", "Artifact exceeds its class-specific byte budget", "Reduce the artifact or assign the documented larger class; never weaken the whole-tree audit.")
    require(files > 0, "tree_empty", "Authoring tree is empty", "Provide the frozen authoring artifacts.")
    require(total <= tree_max, "tree_size_exceeded", "Authoring tree exceeds its total byte budget", "Remove redundant diagnostics or increase the explicitly reviewed tree budget.")
    return {"ok": True, "check": "authoring-tree", "file_count": files, "byte_count": total, "closure_count": closures}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    digest = sub.add_parser("review-digests")
    digest.add_argument("--packet", required=True, type=Path)
    digest.add_argument("--ticket", required=True, type=Path)
    scope = sub.add_parser("output-scope")
    scope.add_argument("--workspace-root", required=True, type=Path)
    scope.add_argument("--project-root", required=True, type=Path)
    scope.add_argument("--output-root", required=True, type=Path)
    manifests = sub.add_parser("window-close-manifests")
    manifests.add_argument("--planning-manifest", required=True, type=Path)
    manifests.add_argument("--commit-manifest", required=True, type=Path)
    tree = sub.add_parser("authoring-tree")
    tree.add_argument("--root", required=True, type=Path)
    tree.add_argument("--ordinary-max-bytes", type=int, default=ORDINARY_MAX_BYTES)
    tree.add_argument("--closure-max-bytes", type=int, default=CLOSURE_MAX_BYTES)
    tree.add_argument("--tree-max-bytes", type=int, default=TREE_MAX_BYTES)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "review-digests":
            result = digest_check(args.packet, args.ticket)
        elif args.command == "output-scope":
            result = output_scope_check(args.workspace_root, args.project_root, args.output_root)
        elif args.command == "window-close-manifests":
            result = close_manifest_check(args.planning_manifest, args.commit_manifest)
        else:
            result = tree_check(args.root, args.ordinary_max_bytes, args.closure_max_bytes, args.tree_max_bytes)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0
    except PreflightError as exc:
        print(json.dumps({"ok": False, "error": {"code": exc.code, "message": exc.message, "recovery": exc.recovery}}, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 2


if __name__ == "__main__":
    sys.exit(main())
